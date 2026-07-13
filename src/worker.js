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
function retrieve(corpus, q, k) {
  const terms = q.toLowerCase().split(/\s+/).filter(Boolean);
  const zh = q.replace(/[^\u4e00-\u9fff]/g, "");
  const grams = [];
  for (let i = 0; i + 2 <= zh.length; i++) grams.push(zh.slice(i, i + 2)); // 中文无空格→补 bigram 提召回
  const keys = terms.concat(grams).filter((v, i, a) => v && a.indexOf(v) === i);
  const scored = [];
  for (const ck of corpus.chunks) {
    const tl = ck.t.toLowerCase();
    let sc = 0;
    for (const key of keys) { const n = tl.split(key).length - 1; if (n) sc += n; }
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

  // 站内检索
  const corpus = await loadCorpus(env, url);
  const hits = retrieve(corpus, q, 10);
  const sources = [];
  const seen = {};
  let ctxText = "";
  for (const ck of hits) {
    const d = corpus.docs[ck.d];
    if (!seen[d.u]) { seen[d.u] = 1; sources.push({ u: d.u, t: d.t, b: corpus.secLabel[d.s] || d.s }); }
    ctxText += "【来源：" + d.t + "】\n" + ck.t + "\n\n";
    if (ctxText.length > 7000) break; // 上下文钳位·控成本
  }

  const sys = "你是「SDE Universes」（德麦国际）站内知识助手。SDE = 显露(Show)·差异(Difference)·纠缠(Entanglement)本体论。"
    + "请【只依据】下面《站内资料》回答问题：资料能答就答，资料不足就直说「站内资料未涉及」，绝不编造、绝不引入资料外的说法。"
    + "回答用中文，条理清晰、简洁（一般 200–500 字），关键处可点出结论出自哪篇。不要复述本提示。";
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
        max_tokens: 2500,
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
