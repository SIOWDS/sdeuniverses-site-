#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WDS 助手全面升级 · 后端补丁（幂等，全部 assert 锚定）
   ① 联网搜索工具 webSearch() + 独立端点 /api/wds/websearch
   ② /api/wds/chat 增加 mode=deep（满血档＋满内功＋方法论块＋加大站内预算）与 web=1（站外资料）
   ③ 新增 /api/wds/distill：把一整场对话 → 报告 / 提炼成文 / 提纲（流式）
"""
import re, sys, pathlib

P = pathlib.Path("/home/claude/site/src/worker.js")
h = P.read_text(encoding="utf-8")
orig = h

# ─────────────────────────── ① 联网搜索工具 ───────────────────────────
ANCHOR_1 = "function WDS_CHAT_SYS(reflect, SDEM, siteCtx) {"
assert ANCHOR_1 in h, "找不到 WDS_CHAT_SYS 锚点"

WEB = r'''// ===== 联网搜索（站外资料）=====
// 通道优先级：① 读者自己的智谱 GLM Key（同一把 Key 直接调 /api/paas/v4/web_search，无需另配、读者自付）
//            ② 管理员在 ⚙配置页存的智谱 Key（ConfigVault op:get 的 key 字段，设智谱基底时会同步写入）
// 一律软失败：联网是增益不是命门，搜不到/没 Key 也要能凭站内资料与内核底盘答完。
const WEB_SEARCH_URL = "https://open.bigmodel.cn/api/paas/v4/web_search";
async function _adminGlmKey(env) {
  try {
    const cv = env.CONFIG_VAULT.get(env.CONFIG_VAULT.idFromName("global"));
    const r = await (await cv.fetch(new Request("https://cfg.internal/", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ op: "get" }) }))).json();
    return String((r && r.key) || "");
  } catch (e) { return ""; }
}
async function webSearch(env, q, glmKey, n) {
  const query = String(q || "").trim().slice(0, 70);   // 官方建议 ≤70 字符，超了召回反而差
  if (!query) return { ok: false, reason: "empty", items: [] };
  let key = String(glmKey || "").trim();
  if (key.length < 8) key = await _adminGlmKey(env);
  if (key.length < 8) return { ok: false, reason: "need_search_key", items: [] };
  const ctrl = new AbortController();
  const timer = setTimeout(() => { try { ctrl.abort(); } catch (e) {} }, 20000);
  try {
    const resp = await fetch(WEB_SEARCH_URL, {
      method: "POST",
      headers: { "content-type": "application/json", authorization: "Bearer " + key },
      body: JSON.stringify({ search_query: query, search_engine: "search_std", count: Math.min(Math.max(n || 8, 3), 15) }),
      signal: ctrl.signal,
    });
    if (!resp.ok) return { ok: false, reason: resp.status === 401 || resp.status === 402 ? "bad_search_key" : ("http_" + resp.status), items: [] };
    const j = await resp.json();
    const items = (j && Array.isArray(j.search_result) ? j.search_result : []).map((r) => ({
      t: String(r.title || "").slice(0, 120),
      u: String(r.link || ""),
      s: String(r.content || "").replace(/\s+/g, " ").slice(0, 700),
      m: String(r.media || ""),
      d: String(r.publish_date || ""),
    })).filter((r) => r.u);
    return { ok: true, reason: "", items };
  } catch (e) { return { ok: false, reason: "net", items: [] }; }
  finally { clearTimeout(timer); }
}
// 把搜索结果码成给基底看的块。编号 [W1..] 与前端"站外来源"卡一一对应，便于答里挂角标。
function webBlock(items) {
  if (!items || !items.length) return "";
  let s = "";
  for (let i = 0; i < items.length; i++) {
    const it = items[i];
    s += "[W" + (i + 1) + "] " + it.t + (it.d ? "（" + it.d + "）" : "") + (it.m ? " · " + it.m : "") + "\n" + it.s + "\n" + it.u + "\n\n";
    if (s.length > 9000) break;
  }
  return s;
}
// 深度思考档的方法论明示块：三大方程 · 六路径 · 123原理 · 意义三律。
// 标准档不挂（省 token，也不必），深度档挂——要它真按工序走，而不是嘴上说 SDE。
const SDE_METHOD_BLOCK = "\n\n【深度档 · 必须真走的工序（不要复述工序名，只让答案带上工序的结果）】"
  + "\n· 三大方程：S=F(D,E)（显露由差异序列与特征纠缠决定）· D=G(S,E)· E=H(S,D)。三条都要试着代一遍，看哪一条把这件事解释得最紧。"
  + "\n· 六路径：不要只走「在 E 中经 D 成 S」这一条。六条路径各试，挑出真正发生的那条，并说明另几条为何不发生。"
  + "\n· 123原理与三界（现实界/理念界/自我界）、信息三模态（符号/逻辑/信息）、能量三态（真/善/美）：定位这件事落在哪几格，指出中心位轮转到哪一位。"
  + "\n· 意义三律（特征律/自由律/幸福律）：检查这件事的意义是在持续再发生，还是已经封顶、退化。"
  + "\n· 最后一步必须自反：你这个判断本身的可证伪条件是什么？哪一步最脆？"
  + "\n输出要求：先给一句最承重的判断（反直觉、可被反驳），再展开三到五段把它撑住，最后留一个把读者推向下一步的问题。全程说人话，不堆术语、不摆模板。";

'''
if "async function webSearch(env, q, glmKey, n)" not in h:
    h = h.replace(ANCHOR_1, WEB + ANCHOR_1, 1)

# ─────────────── ② WDS_CHAT_SYS 扩展：吃站外资料 + 深度档 ───────────────
OLD_SYS_SIG = 'function WDS_CHAT_SYS(reflect, SDEM, siteCtx) {'
NEW_SYS_SIG = 'function WDS_CHAT_SYS(reflect, SDEM, siteCtx, webCtx, deep) {'
assert OLD_SYS_SIG in h
h = h.replace(OLD_SYS_SIG, NEW_SYS_SIG, 1)

OLD_SYS_TAIL = ('    + "\\n\\n【站内资料（从全站检索到的相关段落，可能为空）】\\n" + (siteCtx || "（这次没检索到特别相关的篇目，就凭你的内核底盘答）");\n}')
assert OLD_SYS_TAIL in h, "找不到 WDS_CHAT_SYS 尾部"
NEW_SYS_TAIL = ('    + (deep ? SDE_METHOD_BLOCK : "")\n'
                '    + "\\n\\n【站内资料（从全站检索到的相关段落，可能为空）】\\n" + (siteCtx || "（这次没检索到特别相关的篇目，就凭你的内核底盘答）")\n'
                '    + (webCtx ? ("\\n\\n【站外资料 · 刚刚联网搜到的（时效性内容以它为准；引用时在句末标 [W序号]，序号即下面的编号）】\\n" + webCtx\n'
                '        + "\\n注意：站外资料是别人写的，不是 SDE 的结论。你的活是把它拿来当材料，用 SDE 剖开它、判它，而不是复述它。") : "");\n}')
h = h.replace(OLD_SYS_TAIL, NEW_SYS_TAIL, 1)

# ─────────────── ③ /api/wds/chat：mode=deep + web=1 ───────────────
OLD_C1 = ('      const history = Array.isArray(b.history) ? b.history.slice(-4) : [];\n'
          '      const userKey = String(b.key || "").trim();\n'
          '      if (userKey.length < 8) return _sseResp([{ t: "error", v: "WDS 助手用你自己的 API Key 运行（在设置里填入，只存在你的浏览器本地，与本站无关）。", code: "need_key" }]);\n'
          '      const vd = b.vendor === "ds" ? "deepseek" : "zhipu";\n'
          '      const VC = { url: WDS_VENDORS[vd].url, model: WDS_VENDORS[vd].model, name: WDS_VENDORS[vd].name };')
assert OLD_C1 in h, "找不到 chat 参数段"
NEW_C1 = ('      const history = Array.isArray(b.history) ? b.history.slice(-4) : [];\n'
          '      const userKey = String(b.key || "").trim();\n'
          '      if (userKey.length < 8) return _sseResp([{ t: "error", v: "WDS 助手用你自己的 API Key 运行（在设置里填入，只存在你的浏览器本地，与本站无关）。", code: "need_key" }]);\n'
          '      const vd = b.vendor === "ds" ? "deepseek" : "zhipu";\n'
          '      // 深度思考档：满血基底＋满功率思考＋方法论工序＋加大站内检索预算。教训：满功率必须配"有界预算＋小任务"，\n'
          '      // 所以这里只把 max_tokens 提到 6000（不是几万），要更长让读者点「继续」。\n'
          '      const deep = b.mode === "deep";\n'
          '      const wantWeb = !!b.web;                                  // 联网开关\n'
          '      const skey = String(b.skey || "").trim();                 // 读者的智谱 Key（专供联网搜索；没有就退到管理员 Key）\n'
          '      const VC = deep ? wdsTopVC(vd) : { url: WDS_VENDORS[vd].url, model: WDS_VENDORS[vd].model, name: WDS_VENDORS[vd].name };')
h = h.replace(OLD_C1, NEW_C1, 1)

# 检索预算 + 联网注入
OLD_C2 = ('              const expTerms = await sdeExpandQuery(VC, KEY, q);\n'
          '              const _lrC = await lightRetrieve(env, url, q, expTerms, 20, 1600, { pick: 18 });')
assert OLD_C2 in h, "找不到 chat 检索段"
NEW_C2 = ('              const expTerms = await sdeExpandQuery(VC, KEY, q);\n'
          '              const _lrC = await lightRetrieve(env, url, q, expTerms, deep ? 30 : 20, 1600, { pick: deep ? 28 : 18 });')
h = h.replace(OLD_C2, NEW_C2, 1)

OLD_C3 = ('                if (kb) { const r = retrieveKB(kb, corpus, q, expTerms, 24); kbBlock = r.block; for (const s of r.srcs) if (!seen[s.u]) { seen[s.u] = 1; sources.push(s); } }\n'
          '              } catch (e) {}\n'
          '              // —— 相似句补充:给 KB 腾预算(20→12,字数上限收紧)——\n'
          '              const chunkCap = kbBlock ? 7000 : 12000;\n'
          '              const hits = _lrC.hits.slice(0, kbBlock ? 12 : 20);')
assert OLD_C3 in h, "找不到 chat KB 段"
NEW_C3 = ('                if (kb) { const r = retrieveKB(kb, corpus, q, expTerms, deep ? 36 : 24); kbBlock = r.block; for (const s of r.srcs) if (!seen[s.u]) { seen[s.u] = 1; sources.push(s); } }\n'
          '              } catch (e) {}\n'
          '              // —— 相似句补充:给 KB 腾预算(20→12,字数上限收紧)；深度档整体放宽 ——\n'
          '              const chunkCap = deep ? (kbBlock ? 12000 : 18000) : (kbBlock ? 7000 : 12000);\n'
          '              const hits = _lrC.hits.slice(0, deep ? (kbBlock ? 20 : 28) : (kbBlock ? 12 : 20));')
h = h.replace(OLD_C3, NEW_C3, 1)

OLD_C4 = ('            sources = sources.slice(0, 6);\n'
          '            if (sources.length) controller.enqueue(_sseBytes({ t: "sources", v: sources })); // 出处先发前端\n'
          '            let reflect = ""; try { reflect = await ensureReflect(env, url, rvendor, VC, KEY); } catch (e) {}')
assert OLD_C4 in h, "找不到 chat sources 段"
NEW_C4 = ('            sources = sources.slice(0, deep ? 10 : 6);\n'
          '            if (sources.length) controller.enqueue(_sseBytes({ t: "sources", v: sources })); // 出处先发前端\n'
          '            // —— 联网搜索（可选）：搜到就把站外资料块并进 system，并把来源卡发给前端 ——\n'
          '            let webCtx = "";\n'
          '            if (wantWeb) {\n'
          '              const ws = await webSearch(env, q, (rvendor === "glm" ? KEY : skey), deep ? 12 : 8);\n'
          '              if (ws.ok && ws.items.length) { webCtx = webBlock(ws.items); controller.enqueue(_sseBytes({ t: "web", v: ws.items })); }\n'
          '              else controller.enqueue(_sseBytes({ t: "webfail", v: ws.reason }));\n'
          '            }\n'
          '            let reflect = ""; try { reflect = await ensureReflect(env, url, rvendor, VC, KEY); } catch (e) {}')
h = h.replace(OLD_C4, NEW_C4, 1)

OLD_C5 = '            const sys = WDS_CHAT_SYS(reflect, SDEM, ctxText);'
assert OLD_C5 in h
h = h.replace(OLD_C5, '            const sys = WDS_CHAT_SYS(reflect, SDEM, ctxText, webCtx, deep);', 1)

OLD_C6 = ('              upstream = await fetch(VC.url, { method: "POST", headers: { "content-type": "application/json", authorization: "Bearer " + KEY }, '
          'body: JSON.stringify({ model: VC.model, stream: true, max_tokens: 2600, messages }) });')
assert OLD_C6 in h, "找不到 chat upstream"
NEW_C6 = ('              upstream = await fetch(VC.url, { method: "POST", headers: { "content-type": "application/json", authorization: "Bearer " + KEY }, '
          'body: JSON.stringify(wdsTopBody(VC, { model: VC.model, stream: true, max_tokens: deep ? 6000 : 2600, messages })) });')
h = h.replace(OLD_C6, NEW_C6, 1)

# ─────────────── ④ 新端点：/api/wds/websearch 与 /api/wds/distill ───────────────
ANCHOR_2 = '    if (url.pathname === "/api/chat/clear" && request.method === "POST") {'
assert ANCHOR_2 in h, "找不到新端点插入锚点"

NEW_EPS = r'''    // /api/wds/websearch：独立的联网搜索端点（供各智能体复用；不调基底，只返回搜索结果）
    if (url.pathname === "/api/wds/websearch") {
      if (request.method === "OPTIONS") return new Response(null, { headers: _cors() });
      if (request.method !== "POST") return new Response("Method Not Allowed", { status: 405 });
      let b = {}; try { b = await request.json(); } catch (e) {}
      const r = await webSearch(env, String(b.q || ""), String(b.skey || b.key || ""), b.n);
      return Response.json(r, { headers: _cors() });
    }

    // /api/wds/distill：把一整场对话 → 报告 / 提炼成文 / 提纲（流式 SSE，先出流后干活＋心跳）
    // 这是"对话不止于对话"的出口：读者聊完，一键把这场谈话变成能存、能读、能发的东西。
    if (url.pathname === "/api/wds/distill") {
      if (request.method === "OPTIONS") return new Response(null, { headers: _cors() });
      if (request.method !== "POST") return new Response("Method Not Allowed", { status: 405 });
      let b = {}; try { b = await request.json(); } catch (e) {}
      const kind = ({ report: 1, essay: 1, outline: 1 })[b.kind] ? b.kind : "report";
      const turns = Array.isArray(b.history) ? b.history.slice(-40) : [];
      if (!turns.length) return _sseResp([{ t: "error", v: "这场还没有可成文的内容。" }]);
      const userKey = String(b.key || "").trim();
      if (userKey.length < 8) return _sseResp([{ t: "error", v: "成文用你自己的 API Key 运行（在 ⚙ Key 里填入，只存在你的浏览器本地）。", code: "need_key" }]);
      const vd = b.vendor === "ds" ? "deepseek" : "zhipu";
      const VC = wdsTopVC(vd);                 // 成文＝最费脑的一步，直接最强档
      const KEY = userKey, rvendor = ({ zhipu: "glm", deepseek: "ds" })[vd] || vd;
      const ip = request.headers.get("cf-connecting-ip") || "unknown";
      try {
        const lim = env.ASK_LIMITER.get(env.ASK_LIMITER.idFromName(wdsBucket("chat", ip, userKey)));
        const lr = await (await lim.fetch(new Request("https://limiter.internal/?w=" + WDS_PER_MIN + "&d=" + WDS_PER_DAY))).json();
        if (!lr.ok) return _sseResp([{ t: "error", v: lr.reason === "day" ? "这把 Key 今天的额度已用完，明天再来。" : "太快啦，过十几秒再来。" }]);
      } catch (e) {}

      // 把对话码成给基底看的材料。只带文本、不带任何身份信息。
      let convo = "";
      for (const m of turns) {
        const who = (m && m.role === "wds") ? "WDS" : "读者";
        const t = String((m && m.text) || "").slice(0, 4000);
        if (t) convo += "【" + who + "】" + t + "\n\n";
        if (convo.length > 40000) break;
      }
      const SPEC = {
        report: { name: "对话报告", tok: 5000, spec:
          "把这场对话整理成一份【对话报告】。结构：\n"
          + "① 一句话结论——这场谈话最承重的那个判断是什么（不是话题是什么，是判断是什么）。\n"
          + "② 谈了哪几件事——分点列出，每点一句话说清读者问的是什么、答的核心是什么。\n"
          + "③ 立起来的判断——把对话中真正成立的洞见抽出来，逐条给出，每条后面括注它靠什么撑住。\n"
          + "④ 还没解决的——哪些问题只碰了一下、哪些答案是脆的、哪一步最容易被反驳。\n"
          + "⑤ 下一步可做的——三到五条具体的、能动手的建议（读哪篇、往哪个方向追、可以写什么）。\n"
          + "用 Markdown，标题用 ##。忠于对话内容，不添加对话里没有的结论。" },
        essay: { name: "提炼成文", tok: 6000, spec:
          "把这场对话【提炼成一篇独立成立的文章】——不是对话记录的整理，是一篇读者从没看过这场对话也能读懂、也能被说服的文章。要求：\n"
          + "① 拟一个真标题（不是「关于XX的讨论」这种）。\n"
          + "② 开篇第一句就是最承重的那个判断，反直觉、可被反驳。\n"
          + "③ 正文分四到六节，每节一个小标题，逐层把那个判断撑住；把对话里零散的火花锻成连贯的论证。\n"
          + "④ 全程不出现「读者问」「我回答」「这场对话」之类痕迹，也不出现学派术语堆砌——普通人要能读懂。\n"
          + "⑤ 结尾留一个开口，不自我封顶。\n"
          + "用 Markdown，标题用 # 和 ##。约三千字。" },
        outline: { name: "写作提纲", tok: 3600, spec:
          "把这场对话变成一份【可以直接照着写的提纲】。结构：\n"
          + "① 母题：一句反直觉的判断，全篇的脊梁。\n"
          + "② 为什么这条母题立得住：三条支撑理由。\n"
          + "③ 章节提纲：六到十节，每节给出小标题＋这节要证的那一句＋要用到的材料（对话里已有的、站里可查的）。\n"
          + "④ 全篇最脆的一环在哪，怎么补。\n"
          + "用 Markdown。只给提纲，不要写正文。" },
      }[kind];

      const stream = new ReadableStream({
        async start(controller) {
          let _hb = null;
          const fin = () => { if (_hb) clearInterval(_hb); try { controller.enqueue(_ENC.encode("data: [DONE]\n\n")); controller.close(); } catch (e) {} };
          const _st = { t0: Date.now(), think: 0, out: 0 };
          _hb = wdsBeat(controller, _st);
          try {
            let reflect = ""; try { reflect = await ensureReflect(env, url, rvendor, VC, KEY); } catch (e) {}
            const sys = "你是 WDS，王德生的 AI 分身、SDE 本体论的老师。现在要把一场你与读者的谈话，锻成一件能留下来的东西。"
              + "\n\nSDE 骨架：显露 S / 差异序列 D / 特征纠缠 E；三大方程 S=F(D,E)·D=G(S,E)·E=H(S,D)；六路径；意义三律；发生学——追问事物为何如此发生，而非如何被发现。"
              + (reflect ? ("\n\n【SDE 内化心得·思考底盘（别复述、别提\"心得/内功\"）】\n" + reflect) : "")
              + "\n\n【本次任务】\n" + SPEC.spec
              + "\n\n【硬规矩】直接从正文开始，不要开场白、不要\"好的/以下是\"。判断要锋利、可被反驳，不要正确的废话。";
            let upstream;
            try {
              upstream = await fetch(VC.url, {
                method: "POST",
                headers: { "content-type": "application/json", authorization: "Bearer " + KEY },
                body: JSON.stringify(wdsTopBody(VC, { model: VC.model, stream: true, max_tokens: SPEC.tok, messages: [{ role: "system", content: sys }, { role: "user", content: "以下是这场对话的全文：\n\n" + convo + "\n———\n现在开始产出「" + SPEC.name + "」。" }] })),
              });
            } catch (e) { controller.enqueue(_sseBytes({ t: "error", v: "接不上基底：" + (e && e.message) })); return fin(); }
            if (!upstream.ok) {
              const errtxt = (await upstream.text()).slice(0, 300);
              if (upstream.status === 401 || upstream.status === 402 || upstream.status === 429) { controller.enqueue(_sseBytes({ t: "error", v: "你的 Key 用不了（" + upstream.status + "）：额度不足或填错了。", code: "bad_key" })); return fin(); }
              controller.enqueue(_sseBytes({ t: "error", v: "基底返回错误 " + upstream.status + "：" + errtxt })); return fin();
            }
            const reader = upstream.body.getReader();
            const dec = new TextDecoder();
            let buf = "";
            while (true) {
              const { done: rdone, value } = await reader.read();
              if (rdone) break;
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
                if (d.reasoning_content) { _st.think += d.reasoning_content.length; controller.enqueue(_sseBytes({ t: "think", v: d.reasoning_content })); }
                if (d.content) { _st.out += d.content.length; controller.enqueue(_sseBytes({ t: "token", v: d.content })); }
              }
            }
          } catch (e) {
            controller.enqueue(_sseBytes({ t: "error", v: "成文出错：" + (e && e.message) + "（可再试一次）" }));
          }
          fin();
        },
      });
      return new Response(stream, { headers: { ..._cors(), "content-type": "text/event-stream; charset=utf-8", "cache-control": "no-store" } });
    }

'''
if '/api/wds/distill' not in h:
    h = h.replace(ANCHOR_2, NEW_EPS + ANCHOR_2, 1)

assert h != orig, "什么都没改，中止"
P.write_text(h, encoding="utf-8")
print("worker patched OK; delta =", len(h) - len(orig), "chars")
