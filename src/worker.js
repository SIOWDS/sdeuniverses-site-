// SDE Universes site worker: visit counter + static assets
export class VisitCounter {
  constructor(ctx, env) {
    this.ctx = ctx;
  }
  async fetch(request) {
    let total = (await this.ctx.storage.get("total")) || 0;
    if (request.method === "POST") {
      total += 1;
      await this.ctx.storage.put("total", total);
    }
    return new Response(JSON.stringify({ total }), {
      headers: {
        "content-type": "application/json",
        "cache-control": "no-store",
      },
    });
  }
}

// ===== Tier2 智能问答·按 IP 限流（站方出 Key，必须防刷爆）=====
export class AskLimiter {
  constructor(ctx, env) { this.ctx = ctx; }
  async fetch(request) {
    const now = Date.now();
    const WINDOW = 60000, PER_WINDOW = 8;   // 每 IP 每分钟 ≤ 8 次
    const DAY = 86400000, PER_DAY = 60;      // 每 IP 每天 ≤ 60 次
    let hits = (await this.ctx.storage.get("hits")) || [];
    hits = hits.filter((t) => now - t < DAY);
    const inWindow = hits.filter((t) => now - t < WINDOW).length;
    const inDay = hits.length;
    let ok = true, reason = "";
    if (inWindow >= PER_WINDOW) { ok = false; reason = "rate"; }
    else if (inDay >= PER_DAY) { ok = false; reason = "day"; }
    if (ok) { hits.push(now); await this.ctx.storage.put("hits", hits); }
    return new Response(JSON.stringify({ ok, reason, inWindow, inDay }), {
      headers: { "content-type": "application/json" },
    });
  }
}

// ===== 密钥保险箱·服务端存基底 Key（页面设置，免进 Cloudflare）=====
// 纪律：key 只写入、只在 Worker 内部（op:get）读取用于调用基底；绝不经任何公开路由回传浏览器。
export class ConfigVault {
  constructor(ctx, env) { this.ctx = ctx; }
  async _hash(s) {
    const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode("sde-admin-v1:" + s));
    return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
  }
  async fetch(request) {
    const body = await request.json().catch(() => ({}));
    const op = body.op;
    if (op === "get") { // 仅 Worker 内部调用（DO 不对公网暴露）
      return Response.json({ key: (await this.ctx.storage.get("key")) || "" });
    }
    if (op === "status") {
      const key = (await this.ctx.storage.get("key")) || "";
      const adminHash = (await this.ctx.storage.get("adminHash")) || "";
      return Response.json({ configured: !!key, hasAdmin: !!adminHash });
    }
    if (op === "getReflect") { // 深度档·按基底缓存的《从发现到发生》心得（内部调用）
      return Response.json({ reflect: (await this.ctx.storage.get("reflect:" + (body.vendor || ""))) || "" });
    }
    if (op === "setReflect") {
      await this.ctx.storage.put("reflect:" + (body.vendor || ""), String(body.reflect || ""));
      return Response.json({ ok: true });
    }
    if (op === "clearReflect") { // 重写心得：清掉缓存，下次深度提问重写
      const stored = (await this.ctx.storage.get("adminHash")) || "";
      if (!stored || (await this._hash(String(body.pass || ""))) !== stored) return Response.json({ ok: false, msg: "管理口令不正确。" });
      const v = String(body.vendor || "");
      if (v === "all") {
        await this.ctx.storage.delete("reflect:glm");
        await this.ctx.storage.delete("reflect:ds");
        return Response.json({ ok: true, msg: "已清空全部基底的心得，下次深度提问将重写。" });
      }
      await this.ctx.storage.delete("reflect:" + v);
      return Response.json({ ok: true, msg: "已清空 " + (v || "?") + " 的心得，下次深度提问将重写。" });
    }
    if (op === "set") {
      const pass = String(body.pass || ""), key = String(body.key || "");
      if (pass.length < 4) return Response.json({ ok: false, msg: "管理口令太短（至少 4 位）。" });
      if (key.length < 8) return Response.json({ ok: false, msg: "密钥格式无效。" });
      const stored = (await this.ctx.storage.get("adminHash")) || "";
      const h = await this._hash(pass);
      if (!stored) { // 首次：设定管理口令 + 密钥
        await this.ctx.storage.put("adminHash", h);
        await this.ctx.storage.put("key", key);
        return Response.json({ ok: true, msg: "已启用。首次口令即管理口令，请牢记。" });
      }
      if (h !== stored) return Response.json({ ok: false, msg: "管理口令不正确。" });
      await this.ctx.storage.put("key", key);
      return Response.json({ ok: true, msg: "密钥已更新。" });
    }
    return Response.json({ ok: false, msg: "unknown op" });
  }
}

// ===== Tier2 智能问答·站内 RAG =====
const _ENC = new TextEncoder();
function _sseBytes(o) { return _ENC.encode("data: " + JSON.stringify(o) + "\n\n"); }
function _sseResp(objs) {
  const body = objs.map((o) => "data: " + JSON.stringify(o) + "\n\n").join("") + "data: [DONE]\n\n";
  return new Response(body, { headers: { "content-type": "text/event-stream; charset=utf-8", "cache-control": "no-store", "access-control-allow-origin": "*" } });
}
function _cors() { return { "access-control-allow-origin": "*", "access-control-allow-methods": "POST, OPTIONS", "access-control-allow-headers": "content-type" }; }

let CORPUS = null; // 模块级缓存：isolate 内复用，避免每次问答重载 ~6MB 索引
async function loadCorpus(env, url) {
  if (CORPUS) return CORPUS;
  const man = await (await env.ASSETS.fetch(new Request(new URL("/search/manifest.json", url)))).json();
  const secLabel = {};
  man.sections.forEach((s) => { secLabel[s.key] = s.label; });
  const chunks = [];
  for (const s of man.sections) {
    try {
      const sh = await (await env.ASSETS.fetch(new Request(new URL("/search/shard-" + s.key + ".json", url)))).json();
      for (const c of sh.chunks) chunks.push(c);
    } catch (e) { /* 单片失败不阻断 */ }
  }
  CORPUS = { docs: man.docs, secLabel, chunks };
  return CORPUS;
}
function retrieve(corpus, q, k, expTerms) {
  const terms = q.toLowerCase().split(/\s+/).filter(Boolean);
  const zh = q.replace(/[^\u4e00-\u9fff]/g, "");
  const grams = [];
  for (let i = 0; i + 2 <= zh.length; i++) grams.push(zh.slice(i, i + 2)); // 中文无空格→补 bigram 提召回
  const baseKeys = terms.concat(grams).filter((v, i, a) => v && a.indexOf(v) === i);
  const exp = (expTerms || []).map((t) => t.toLowerCase()).filter((v, i, a) => v && v.length >= 2 && a.indexOf(v) === i && baseKeys.indexOf(v) < 0); // SDE 词义扩展词
  const scored = [];
  for (const ck of corpus.chunks) {
    const tl = ck.t.toLowerCase();
    let sc = 0;
    for (const key of baseKeys) { const n = tl.split(key).length - 1; if (n) sc += n; }
    for (const key of exp) { const n = tl.split(key).length - 1; if (n) sc += n * 1.2; } // SDE 义命中略加权
    if (q && ck.t.indexOf(q) >= 0) sc += 8;
    if (sc > 0) scored.push({ sc, ck });
  }
  scored.sort((a, b) => b.sc - a.sc);
  const perDoc = {}, picked = [];
  for (const s of scored) {
    const d = s.ck.d;
    perDoc[d] = perDoc[d] || 0;
    if (perDoc[d] >= 2) continue;          // 每篇最多取 2 段，保证来源多样
    perDoc[d]++; picked.push(s.ck);
    if (picked.length >= k) break;
  }
  return picked;
}

// ===== 深度档·两次内功提智 =====
let NEIGONG = null; // 完整 SDE 内功先验（模块级缓存，isolate 内复用）
async function loadNeigong(env, url) {
  if (NEIGONG) return NEIGONG;
  try {
    const t = await (await env.ASSETS.fetch(new Request(new URL("/taste/assets/sde-neigong.txt", url)))).text();
    if (t && t.length > 5000) NEIGONG = t;
  } catch (e) {}
  return NEIGONG || "";
}
const REFLECT_PROMPT = "请用你自己的话，写一篇《从发现到发生》的内化心得（约 5000 字，要写透、写充分）：不要复述方法条目，而是把“追问任何事物是如何发生的（而不是如何被发现的）”这套思维方式，用你自己的理解完整内化一遍；并诚实检视你平时回答问题的默认惯性（例如急于给结论、罗列要点、停在表层描述、把现成关系当起点），说明用这套“发生”的眼光重新看，你该在哪里改变。这篇心得只写给你自己看，写完你就完成了一次自我提智。切记：全文用平实现代汉语，绝不出现“显露/差异/纠缠/发生学/SDE”等任何术语标签。";
// 第一次提智：让基底带着完整内功、亲手写心得；按基底缓存，只写一次，之后所有深度提问复用
async function ensureReflect(env, url, vendor, VC, KEY) {
  try {
    const cv = env.CONFIG_VAULT.get(env.CONFIG_VAULT.idFromName("global"));
    const r = await (await cv.fetch(new Request("https://cfg.internal/", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ op: "getReflect", vendor }) }))).json();
    if (r.reflect && r.reflect.length > 500) return r.reflect;
  } catch (e) {}
  const neigong = await loadNeigong(env, url);
  if (!neigong) return "";
  let text = "";
  try {
    const resp = await fetch(VC.url, {
      method: "POST",
      headers: { "content-type": "application/json", authorization: "Bearer " + KEY },
      body: JSON.stringify({ model: VC.model, stream: false, max_tokens: 6000, messages: [{ role: "system", content: neigong }, { role: "user", content: REFLECT_PROMPT }] }),
    });
    if (resp.ok) { const j = await resp.json(); text = (j.choices && j.choices[0] && j.choices[0].message && j.choices[0].message.content) || ""; }
  } catch (e) {}
  if (text && text.length > 500) {
    try {
      const cv = env.CONFIG_VAULT.get(env.CONFIG_VAULT.idFromName("global"));
      await cv.fetch(new Request("https://cfg.internal/", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ op: "setReflect", vendor, reflect: text }) }));
    } catch (e) {}
  }
  return text;
}

// 非流式单维调用（四步法的 Q1/Q2/Q3 用；思考关，控延迟）
async function llmText(VC, KEY, sys, usr, maxTok) {
  try {
    const resp = await fetch(VC.url, {
      method: "POST",
      headers: { "content-type": "application/json", authorization: "Bearer " + KEY },
      body: JSON.stringify({ model: VC.model, stream: false, max_tokens: maxTok, messages: [{ role: "system", content: sys }, { role: "user", content: usr }] }),
    });
    if (!resp.ok) return "";
    const j = await resp.json();
    return (j.choices && j.choices[0] && j.choices[0].message && j.choices[0].message.content) || "";
  } catch (e) { return ""; }
}

// ===== SDE 词义查询扩展：把访客问题翻成 SDE 术语，再拿去召回（检索侧提智，对称于答题侧内功）=====
const SDE_LEXICON = "你是 SDE（显露·差异·纠缠 / Show-Difference-Entanglement 本体论）术语解析器。SDE 核心词表：\n"
  + "· 三维：S=显露(结构/可辨认单位/稳定核心/显影/结构显露态)；D=差异(过程/差异序列/张力/路径/演化/发生)；E=纠缠(环境/特征纠缠/三界/信息/能量)。\n"
  + "· 三界(E1)：现实界、理念界、自我界。信息三模态(E2)：符号/逻辑/信息。能量三态(E3)：真/善/美。\n"
  + "· SIO 27宫格：O=一号位=客体，I=二号位=互动，S=三号位=主体(最后才显影/最后才亮)；C⊗M⊗V=内容⊗方法⊗价值。\n"
  + "· 核心概念：发生(相对于发现)、显影、名是指针、特征纠缠、中心位轮转、意义三律(特征律/自由律/幸福律)、三大方程 S=F(D,E)/D=G(S,E)/E=H(S,D)、六路径、123原理、底盘与回写、成熟态与退化谱系、解构、裂缝、约束性发生、反身的发生不可自我封顶。\n"
  + "任务：把用户问题解析成一串【最能帮助在 SDE 语料里检索到相关内容】的具体术语——包括它触及的维度(S/D/E)、相关核心概念、可能落在的三界或宫格位、以及同义/近义的 SDE 说法。只输出术语本身，用顿号分隔，8–20 个，不要解释、不要整句、不要泛词（如“事物/问题/研究”）。";
async function sdeExpandQuery(VC, KEY, q) {
  const out = await llmText(VC, KEY, SDE_LEXICON, "用户问题：" + q + "\n\n请只输出 SDE 检索术语（顿号分隔）：", 300);
  if (!out) return [];
  return out.replace(/\n/g, "、").split(/[、,，;；\s]+/).map((s) => s.trim()).filter((s) => s.length >= 2 && s.length <= 12).slice(0, 24);
}

async function handleAsk(request, env, url) {
  if (request.method === "OPTIONS") return new Response(null, { headers: _cors() });
  if (request.method !== "POST") return new Response("Method Not Allowed", { status: 405 });

  let body = {};
  try { body = await request.json(); } catch (e) {}
  const q = String(body.q || "").trim().slice(0, 300); // 输入硬钳位
  if (q.length < 2) return _sseResp([{ t: "error", v: "请输入一个问题（至少 2 个字）。" }]);

  // 基底二选一（默认 GLM）
  const vendor = body.vendor === "ds" ? "ds" : "glm";
  const VC = vendor === "ds"
    ? { url: "https://api.deepseek.com/v1/chat/completions", model: "deepseek-v4-pro", name: "DeepSeek" }
    : { url: "https://open.bigmodel.cn/api/paas/v4/chat/completions", model: "glm-5", name: "GLM-5" };

  // Key 两来源：用户自带(BYOK) 优先；否则系统 Key（页面保险箱 → Cloudflare secret）
  const userKey = String(body.key || "").trim();
  const byok = userKey.length >= 8;
  let KEY = userKey;
  if (!byok) {
    try {
      const cv = env.CONFIG_VAULT.get(env.CONFIG_VAULT.idFromName("global"));
      const r = await (await cv.fetch(new Request("https://cfg.internal/", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ op: "get" }) }))).json();
      KEY = r.key || "";
    } catch (e) {}
    if (!KEY) KEY = env.SDE_SEARCH_KEY || "";
  }
  if (!KEY) return _sseResp([{ t: "error", v: "智能问答尚未启用：管理员尚未配置系统密钥。你也可以在下方填入自己的 API Key 直接使用。", code: "use_own_key" }]);

  // 限流：系统 Key 与自带 Key 各用独立配额桶（自带 Key 用户自付，不与系统额度互挤）
  const ip = request.headers.get("cf-connecting-ip") || "unknown";
  try {
    const lim = env.ASK_LIMITER.get(env.ASK_LIMITER.idFromName((byok ? "byok:" : "sys:") + ip));
    const lr = await (await lim.fetch(new Request("https://limiter.internal/"))).json();
    if (!lr.ok) {
      const msg = lr.reason === "day"
        ? "今日提问次数已达上限，请明天再来，或改用「🔍 关键词检索」。"
        : "提问太频繁了，请过十几秒再试。";
      return _sseResp([{ t: "error", v: msg }]);
    }
  } catch (e) {}

  // 站内检索（按档分级喂料：深度档拿更多材料，普通档保持轻快）
  const deep = body.deep === true;
  const K = deep ? 120 : 20;              // 取多少块（深度档广撒网；retrieve 只收相关块、clamp 兜底，窄问题不会被噪声塞满）
  const CTX_MAX = deep ? 50000 : 12000;   // 《站内资料》字数上限
  const corpus = await loadCorpus(env, url);
  const expTerms = await sdeExpandQuery(VC, KEY, q); // SDE 词义扩展：问题→SDE 术语，再拿去召回
  const expStr = expTerms.join(" · ");
  const hits = retrieve(corpus, q, K, expTerms);
  const sources = [];
  const seen = {};
  let ctxText = "";
  for (const ck of hits) {
    const d = corpus.docs[ck.d];
    if (!seen[d.u]) { seen[d.u] = 1; sources.push({ u: d.u, t: d.t, b: corpus.secLabel[d.s] || d.s }); }
    ctxText += "【来源：" + d.t + "】\n" + ck.t + "\n\n";
    if (ctxText.length > CTX_MAX) break; // 上下文钳位·控成本
  }

  // ===== 深度档·四步法（S→D→E→整合，四次独立调用；对齐发生器/skill 验证的 140-145 机制）=====
  if (deep) {
    const reflect = await ensureReflect(env, url, vendor, VC, KEY);
    const neigong = await loadNeigong(env, url);
    if (reflect && neigong) {
      const ctx4 = ctxText.slice(0, 15000); // 四步各调用共用《站内资料》，钳 15000 控 4× 成本
      const usr4 = "《站内资料》\n" + (ctx4 || "（未检索到相关段落）") + "\n\n《问题》\n" + q;
      const dimSys = reflect + "\n\n———\n你带着上面这份你自己写下并已内化的心得，对下面的问题只做一个维度的展开。";
      const Q1 = "请【只从 S 维度·显露/结构】展开这个问题，先完全不碰过程与环境：它显露出哪些可辨认的结构、稳定核心、可识别的单位？与正常态或其他情况有何结构性差异？反复观察中什么保持一致？分点写透，约 600–900 字。";
      const Q2 = "请【只从 D 维度·差异/过程】展开这个问题，先完全不碰结构与环境：它在哪些差异张力里演化？经历哪些阶段转换、有什么周期节奏？被什么推动、朝什么方向减阻前进？分点写透，约 600–900 字。";
      const Q3 = "请【只从 E 维度·纠缠/环境】展开这个问题，先完全不碰结构与过程：它在三界（现实界/理念界/自我界）各是什么？在什么符号、逻辑、信息与什么能量条件下才得以发生？被什么环境纠缠、约束？分点写透，约 600–900 字。";
      const stream = new ReadableStream({
        async start(controller) {
          const st = (v) => controller.enqueue(_sseBytes({ t: "status", v }));
          controller.enqueue(_sseBytes({ t: "sources", v: sources }));
          if (expStr) controller.enqueue(_sseBytes({ t: "expand", v: expStr }));
          try {
            st("① S 维度·显露分析中…（四步法·约需数分钟，请勿关闭）");
            const sA = await llmText(VC, KEY, dimSys, usr4 + "\n\n" + Q1, 2500);
            st("② D 维度·差异分析中…");
            const dA = await llmText(VC, KEY, dimSys, usr4 + "\n\n" + Q2, 2500);
            st("③ E 维度·纠缠分析中…");
            const eA = await llmText(VC, KEY, dimSys, usr4 + "\n\n" + Q3, 2500);
            if (!sA && !dA && !eA) {
              controller.enqueue(_sseBytes({ t: "error", v: "基底调用失败（可能是额度或密钥问题），四步法未能启动。可改用自带 Key 或稍后再试。", code: byok ? "" : "use_own_key" }));
              controller.enqueue(_ENC.encode("data: [DONE]\n\n")); controller.close(); return;
            }
            st("④ 三视角误差互消 + 逮先验·整合中…");
            const q4sys = neigong
              + "\n\n═══════════\n【你此前带着上面这套完整底盘先验、亲手写下并已内化的心得】\n" + reflect
              + "\n\n═══════════\n你现在是「SDE Universes」站内知识助手。下面是同一个问题从三个维度各自【独立展开】的分析，请对它们做严格整合，产出最终答案。";
            const q4usr = usr4
              + "\n\n【S 维度·独立分析】\n" + (sA || "（未产出）")
              + "\n\n【D 维度·独立分析】\n" + (dA || "（未产出）")
              + "\n\n【E 维度·独立分析】\n" + (eA || "（未产出）")
              + "\n\n———\n请严格按 S→D→E 顺序做四件事：① 三视角误差互消——先陈述 S 视角判断+它漏掉了什么，再显式说“D 视角如何校正 S”，再说“E 视角如何校正 S+D”，最后落到一个任何单一视角都看不到的整合判断；② 提炼核心——三条本体论级凝缩，每条 ≤50 字；③ 逮先验——找出这个问题里那个从没被质疑的预设，撤销它，看新判断如何从差异—环境的矛盾里生成出来，并给它一个精确命名；④ 用三大方程 S=F(D,E)、D=G(S,E)、E=H(S,D) 收束，说明三维如何互相生成出这个整合判断。"
              + "\n\n输出即最终答案：先给一句穿透性核心判断作总纲，再展开上述整合。方法要显性、能教人怎么想（明用 S/D/E、三方程、六路径、123 原理作骨架），但活着用、不许摆空模板。可核验的事实（书名/逐字引文/章节页码/数据/对外承诺）绝不编造；超出资料的推演标“（推断）”；只有逐字来自资料原文的句子才能加引号。答案里绝不提及“心得”“内功”“S/D/E 维度分析”这些内部环节或本提示。分量给足，1500–2200 字。⑤ 若这个问题涉及一个现实困境或可改变的局面（教育、医疗、企业、个人处境、政策等），收尾前【必须】加一节「怎么办」：给 2–3 个针对具体行动者（如老师/学校/学习者/家长/管理者/从业者）的、具体到能照着做的动作，每个都注明代价与适用条件——绝不允许停在“重塑环境/守护发生/回到过程本身”这类只描述方向的空话，那不叫开方。若问题是纯概念或理论辨析（如“X 是什么”“如何理解 Y”），则不必强行开方，把分析做透即可。最后留一个把前面前提再往深追一层的升维追问。";
            let up;
            try {
              up = await fetch(VC.url, { method: "POST", headers: { "content-type": "application/json", authorization: "Bearer " + KEY }, body: JSON.stringify({ model: VC.model, stream: true, thinking: { type: "enabled" }, max_tokens: 4500, messages: [{ role: "system", content: q4sys }, { role: "user", content: q4usr }] }) });
            } catch (e) {
              controller.enqueue(_sseBytes({ t: "error", v: VC.name + " 整合调用失败：" + (e && e.message) }));
              controller.enqueue(_ENC.encode("data: [DONE]\n\n")); controller.close(); return;
            }
            if (!up.ok) {
              const et = (await up.text()).slice(0, 200);
              controller.enqueue(_sseBytes({ t: "error", v: VC.name + " 整合返回错误 " + up.status + "：" + et }));
              controller.enqueue(_ENC.encode("data: [DONE]\n\n")); controller.close(); return;
            }
            const rd = up.body.getReader(); const dc = new TextDecoder(); let bf = "";
            while (true) {
              const { done, value } = await rd.read();
              if (done) break;
              bf += dc.decode(value, { stream: true });
              let ix;
              while ((ix = bf.indexOf("\n")) >= 0) {
                const ln = bf.slice(0, ix).trim(); bf = bf.slice(ix + 1);
                if (!ln.startsWith("data:")) continue;
                const p = ln.slice(5).trim();
                if (p === "[DONE]") continue;
                let j; try { j = JSON.parse(p); } catch (e) { continue; }
                if (j.error) { controller.enqueue(_sseBytes({ t: "error", v: j.error.message || "整合流内错误" })); continue; }
                const d = (j.choices && j.choices[0] && j.choices[0].delta) || {};
                if (d.reasoning_content) controller.enqueue(_sseBytes({ t: "think", v: d.reasoning_content }));
                if (d.content) controller.enqueue(_sseBytes({ t: "token", v: d.content }));
              }
            }
          } catch (e) {
            controller.enqueue(_sseBytes({ t: "error", v: "四步法执行失败：" + (e && e.message) }));
          }
          controller.enqueue(_ENC.encode("data: [DONE]\n\n"));
          controller.close();
        },
      });
      return new Response(stream, { headers: { ..._cors(), "content-type": "text/event-stream; charset=utf-8", "cache-control": "no-store" } });
    }
  }

  // ===== 单次调用：普通档，或深度档无心得时降级 =====
  const sys = "你是「SDE Universes」站内知识助手，回答要像一位资深学者，而不是资料复述员。"
    + "【内部思考·不写进答案】收到问题和《站内资料》后，先在心里用三个视角各看一遍再互相校正：结构（它的构成、可辨认的单位、反复出现的稳定核心）、过程（它怎么演化、经历哪些阶段、被什么推动）、环境（它在什么约束/关系场里才成立）；然后用一个视角修正另一个视角的盲区，落到一个任何单一视角都看不到的整合判断。"
    + "【回答纪律】① 用平实现代汉语和读者的话作答，不要堆砌“显露/差异/纠缠”等术语（除非用户就在问 SDE 概念本身）——三视角是你的思考脚手架，不是答案骨架；② 《站内资料》是底盘但不框死你——站内没直接覆盖的，就像这位专家本人被问到那样，用他的方法结合你的知识原创作答，不要推说“未涉及”；凡超出资料的推演都标“（推断）”，而可核验的事实（书名/逐字引文/章节页码/数据/对外承诺）绝不编造。资料支撑的判断可点出处。只有逐字来自资料原文的句子才可以加引号、你自己的概括与推断一律不加引号（把自己的话套引号伪装成原文是最严重的错误）；③ 不要杜撰章节号或页码；④ 先给一句穿透性核心判断再展开；若问题涉及可改变的现实局面，收尾给 1–2 个具体可执行的动作（注明代价/适用条件），不要停在只说方向的空话；若是纯概念辨析则不必开方。结尾留一个可追问的问题，400–700 字。";
  const usr = "《站内资料》\n" + (ctxText || "（未检索到相关段落）") + "\n\n《问题》\n" + q;

  // 调基底（境内直连）。自带 Key：仅在内存中转发调用，绝不存储/记录（同 llm-proxy 纪律）
  let upstream;
  try {
    upstream = await fetch(VC.url, {
      method: "POST",
      headers: { "content-type": "application/json", authorization: "Bearer " + KEY },
      body: JSON.stringify({
        model: VC.model,
        stream: true,
        thinking: { type: "enabled" },
        max_tokens: 4000,
        messages: [{ role: "system", content: sys }, { role: "user", content: usr }],
      }),
    });
  } catch (e) {
    return _sseResp([{ t: "sources", v: sources }, { t: "error", v: VC.name + " 连接失败：" + (e && e.message) }]);
  }
  if (!upstream.ok) {
    const errtxt = (await upstream.text()).slice(0, 300);
    // 系统 Key 遇额度/鉴权问题(401/402/429) → 引导改用自带 Key
    if (!byok && (upstream.status === 401 || upstream.status === 402 || upstream.status === 429)) {
      return _sseResp([{ t: "error", v: "系统额度暂时不可用（" + VC.name + " " + upstream.status + "）。你可以在下方填入自己的 API Key 继续使用。", code: "use_own_key" }]);
    }
    return _sseResp([{ t: "sources", v: sources }, { t: "error", v: VC.name + " 返回错误 " + upstream.status + "：" + errtxt }]);
  }

  const reader = upstream.body.getReader();
  const dec = new TextDecoder();
  const stream = new ReadableStream({
    async start(controller) {
      controller.enqueue(_sseBytes({ t: "sources", v: sources })); // 先给出处，再流答案
      if (expStr) controller.enqueue(_sseBytes({ t: "expand", v: expStr }));
      let buf = "";
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buf += dec.decode(value, { stream: true });
          let idx;
          while ((idx = buf.indexOf("\n")) >= 0) {
            const line = buf.slice(0, idx).trim();
            buf = buf.slice(idx + 1);
            if (!line.startsWith("data:")) continue;
            const p = line.slice(5).trim();
            if (p === "[DONE]") continue;
            let j; try { j = JSON.parse(p); } catch (e) { continue; }
            if (j.error) { controller.enqueue(_sseBytes({ t: "error", v: j.error.message || "基底流内错误" })); continue; }
            const d = (j.choices && j.choices[0] && j.choices[0].delta) || {};
            if (d.reasoning_content) controller.enqueue(_sseBytes({ t: "think", v: d.reasoning_content }));
            if (d.content) controller.enqueue(_sseBytes({ t: "token", v: d.content }));
          }
        }
      } catch (e) {
        controller.enqueue(_sseBytes({ t: "error", v: "读取基底流失败：" + (e && e.message) }));
      }
      controller.enqueue(_ENC.encode("data: [DONE]\n\n"));
      controller.close();
    },
  });
  return new Response(stream, { headers: { ..._cors(), "content-type": "text/event-stream; charset=utf-8", "cache-control": "no-store" } });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    // /fresh：永不缓存的首页镜像，用于验证最新版本
    if (url.pathname === "/fresh") {
      const home = await env.ASSETS.fetch(new Request(new URL("/", url), request));
      const r = new Response(home.body, home);
      r.headers.set("cache-control", "no-store");
      r.headers.set("cdn-cache-control", "no-store");
      return r;
    }
    if (url.pathname === "/api/visits") {
      const id = env.COUNTER.idFromName("site-total");
      return env.COUNTER.get(id).fetch(request);
    }
    // /api/llm-proxy：境外基底(GPT/Claude/Gemini)纯转发代理。
    // 解决两件事：①浏览器 CORS 拦截 ②中国大陆无法直连境外 API。
    // 纪律：只转发、不存储、不记录任何 Key；只放行白名单里的官方 LLM 域名。
    if (url.pathname === "/api/llm-proxy") {
      // 预检
      if (request.method === "OPTIONS") {
        return new Response(null, {
          headers: {
            "access-control-allow-origin": "*",
            "access-control-allow-methods": "POST, OPTIONS",
            "access-control-allow-headers": "content-type, authorization, x-target-url",
            "access-control-max-age": "86400",
          },
        });
      }
      if (request.method !== "POST") {
        return new Response("Method Not Allowed", { status: 405 });
      }
      const target = request.headers.get("x-target-url") || "";
      // 白名单：只允许转发到这几家官方 LLM 端点，防止被当开放代理滥用
      const ALLOW = [
        "https://api.openai.com/",
        "https://api.anthropic.com/",
        "https://generativelanguage.googleapis.com/",
        "https://api.minimaxi.com/",
      ];
      const ok = ALLOW.some((p) => target.startsWith(p));
      if (!ok) {
        return new Response(
          JSON.stringify({ error: { message: "target url not allowed", type: "proxy_forbidden" } }),
          { status: 403, headers: { "content-type": "application/json", "access-control-allow-origin": "*" } }
        );
      }
      // 组装转发请求：原样带上 Authorization / Content-Type / anthropic 专用头，其余头一律不带
      const fwdHeaders = new Headers();
      const auth = request.headers.get("authorization");
      if (auth) fwdHeaders.set("authorization", auth);
      const ct = request.headers.get("content-type");
      if (ct) fwdHeaders.set("content-type", ct);
      // Anthropic 需要 x-api-key + anthropic-version；Gemini 用 URL 里的 key。这里透传常见必需头。
      const apiKey = request.headers.get("x-api-key");
      if (apiKey) fwdHeaders.set("x-api-key", apiKey);
      const av = request.headers.get("anthropic-version");
      if (av) fwdHeaders.set("anthropic-version", av);
      const adb = request.headers.get("anthropic-dangerous-direct-browser-access");
      if (adb) fwdHeaders.set("anthropic-dangerous-direct-browser-access", adb);

      let upstream;
      try {
        upstream = await fetch(target, {
          method: "POST",
          headers: fwdHeaders,
          body: request.body,
        });
      } catch (e) {
        return new Response(
          JSON.stringify({ error: { message: "upstream fetch failed: " + (e && e.message), type: "proxy_upstream_error" } }),
          { status: 502, headers: { "content-type": "application/json", "access-control-allow-origin": "*" } }
        );
      }
      // 原样回传响应体(含流式)，补上 CORS 头让浏览器可读
      const respHeaders = new Headers(upstream.headers);
      respHeaders.set("access-control-allow-origin", "*");
      respHeaders.delete("content-encoding"); // 避免二次压缩导致前端解码错乱
      return new Response(upstream.body, {
        status: upstream.status,
        statusText: upstream.statusText,
        headers: respHeaders,
      });
    }
    // /api/admin/*：页面设置基底密钥（op 由服务端固定，浏览器只能传 pass+key，无法注入 op:get 回读密钥）
    if (url.pathname === "/api/admin/setkey" && request.method === "POST") {
      const b = await request.json().catch(() => ({}));
      const cv = env.CONFIG_VAULT.get(env.CONFIG_VAULT.idFromName("global"));
      const r = await cv.fetch(new Request("https://cfg.internal/", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ op: "set", pass: b.pass, key: b.key }) }));
      return Response.json(await r.json(), { headers: { "access-control-allow-origin": "*" } });
    }
    if (url.pathname === "/api/admin/status") {
      const cv = env.CONFIG_VAULT.get(env.CONFIG_VAULT.idFromName("global"));
      const r = await cv.fetch(new Request("https://cfg.internal/", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ op: "status" }) }));
      return Response.json(await r.json(), { headers: { "access-control-allow-origin": "*" } });
    }
    // /api/ask：站内智能问答（RAG）——浏览器只发问题，Key 锁在服务端
    if (url.pathname === "/api/admin/clearreflect" && request.method === "POST") {
      const b = await request.json().catch(() => ({}));
      const cv = env.CONFIG_VAULT.get(env.CONFIG_VAULT.idFromName("global"));
      const r = await cv.fetch(new Request("https://cfg.internal/", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ op: "clearReflect", pass: b.pass, vendor: b.vendor }) }));
      return Response.json(await r.json(), { headers: { "access-control-allow-origin": "*" } });
    }
    if (url.pathname === "/api/ask") {
      return handleAsk(request, env, url);
    }
    // Everything else: serve static assets (with configured html/404 handling)
    const resp = await env.ASSETS.fetch(request);
    const ct = resp.headers.get("content-type") || "";
    if (ct.includes("text/html")) {
      const r = new Response(resp.body, resp);
      // 釜底抽薪式禁缓存：no-store = 绝不留副本；同时剥掉 ETag/Last-Modified，
      // 让浏览器无从发起 If-None-Match/If-Modified-Since 协商，边缘再也无法回 304 旧副本。
      // 这是"普通刷新即最新"的根治手段——不再依赖用户强刷或手动 Purge。
      r.headers.set("cache-control", "no-store, no-cache, must-revalidate, max-age=0");
      r.headers.set("cdn-cache-control", "no-store");
      r.headers.set("pragma", "no-cache");
      r.headers.set("expires", "0");
      r.headers.delete("etag");
      r.headers.delete("last-modified");
      // 版本可验证：每次响应盖实时时间戳，线上一眼看出服务的是不是最新版。
      r.headers.set("x-served-at", new Date().toISOString());
      return r;
    }
    return resp;
  },
};
