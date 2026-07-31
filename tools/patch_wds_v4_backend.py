#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""问WDS 第三批 · 后端补丁（src/worker.js）

四件事：
  ① 看图（vision）——/api/wds/chat 收 imgs（data URL），按家切到视觉档型号，
     型号改名/下线时沿备用名自动降档；这家不能看图就如实说，不装作看过。
  ② 本场账本（compaction）——收 comp，作为「前情账本」插在历史原文之前。
  ③ 深度研究——/api/wds/chat 收 rs（第 i/n 步），改口径与预算；
     新端点 /api/wds/research 管 plan（拆题，非流式 JSON）与 final（总判断，流式）。
  ④ 顺手修死型号：Kimi 深度档写的是 kimi-k3，而 Kimi 平台的模型表里根本没有这个名字
     （现存 kimi-k2.7-code / kimi-k2.6 / kimi-k2.5），照旧发过去必 400。

纪律：每处 replace 前先 assert 锚点在、且只出现一次。
"""
import re
import sys

P = "/home/claude/site/src/worker.js"
h = open(P, encoding="utf-8").read()
orig = h


def sub1(old, new, why):
    global h
    n = h.count(old)
    assert n == 1, "锚点应恰好出现一次，实际 %d 次：%s（%s）" % (n, old[:70], why)
    h = h.replace(old, new, 1)


# ── ① 修 Kimi 死型号 ──────────────────────────────────────────────
sub1(
    'const WDS_TOP_MODEL = { deepseek: "deepseek-v4-pro", zhipu: "glm-5", kimi: "kimi-k3", qwen: "qwen3.7-max", minimax: "MiniMax-M3" };',
    '// ⚠️ kimi 深度档一度写成 kimi-k3 —— Kimi 平台的模型表里**没有**这个名字（2026-07-31 实查：\n'
    '//    现存 kimi-k2.7-code / kimi-k2.7-code-highspeed / kimi-k2.6 / kimi-k2.5；下线的是 kimi-k2-*-preview 那一批）。\n'
    '//    发一个不存在的型号＝这家深度档一直在 400。改回 k2.6（Kimi 自己标的"迄今最智能"）。\n'
    'const WDS_TOP_MODEL = { deepseek: "deepseek-v4-pro", zhipu: "glm-5", kimi: "kimi-k2.6", qwen: "qwen3.7-max", minimax: "MiniMax-M3" };',
    "kimi 深度档型号",
)

# ── ② 视觉档表 + 阶梯 ─────────────────────────────────────────────
sub1(
    '// 前端短码 ↔ 基底键。未知一律落 zhipu（老前端只发 ds/其它两种值，这样不会断）。',
    '// ── 看图（视觉档）。**只有这三家**在本站的转发口径下能直接吃图；DeepSeek / MiniMax 走不了，\n'
    '//    读者选了它们又传图，我们如实说一句「这家看不了图」，绝不拿 OCR 出来的字冒充"它看过了"。\n'
    '//    每家给一个备用名：型号改名/下线时沿着阶梯自动退一格，而不是整条看图功能一起哑掉。\n'
    '//    默认核对于 2026-07-31。读者仍可在设置里覆盖（payload.vmodel）。\n'
    'const WDS_VISION = {\n'
    '  zhipu: ["glm-5v", "glm-4.6v"],\n'
    '  qwen: ["qwen-vl-max", "qwen3-vl-plus"],\n'
    '  kimi: ["kimi-k2.6", "moonshot-v1-32k-vision-preview"],\n'
    '};\n'
    'function wdsVisionLadder(vd, want) {\n'
    '  const base = WDS_VISION[vd] || [];\n'
    '  const w = String(want || "").trim();\n'
    '  if (w && w.length <= 60 && /^[A-Za-z0-9._:\\/-]+$/.test(w)) return [w].concat(base);\n'
    '  return base.slice();\n'
    '}\n'
    '// 图片钳位：4 张、总计 6MB base64。**必须校验 data URL 的形状**——这串是要原样转给上游的，\n'
    '// 不校验就等于把读者传来的任意字符串塞进上游请求体。\n'
    'const WDS_IMG_MAX = 4, WDS_IMG_BYTES = 6 * 1024 * 1024;\n'
    'function wdsPickImgs(list) {\n'
    '  const out = [];\n'
    '  if (!Array.isArray(list)) return out;\n'
    '  let tot = 0;\n'
    '  for (const im of list.slice(0, WDS_IMG_MAX)) {\n'
    '    const d = String((im && im.d) || "");\n'
    '    if (!/^data:image\\/(png|jpeg|jpg|webp|gif|bmp);base64,[A-Za-z0-9+/=\\s]+$/.test(d)) continue;\n'
    '    if (tot + d.length > WDS_IMG_BYTES) break;\n'
    '    tot += d.length;\n'
    '    out.push({ n: String((im && im.n) || "图片").slice(0, 80), d: d.replace(/\\s+/g, "") });\n'
    '  }\n'
    '  return out;\n'
    '}\n'
    '// 前端短码 ↔ 基底键。未知一律落 zhipu（老前端只发 ds/其它两种值，这样不会断）。',
    "视觉档表",
)

# ── ③ 研究步的 system 块 ──────────────────────────────────────────
sub1(
    'function WDS_CHAT_SYS(reflect, SDEM, siteCtx, webCtx, deep, docCtx, about, lang, docNote, tool) {',
    '// RESEARCH_STEP：深度研究的一步。它和普通问答的差别不在"更用力"，而在**它只负责一节**——\n'
    '// 所以要把《怎么答》第 5 条的"两三段以内"当场解除，同时把"别写总结"钉死（总判断是最后一步的活，\n'
    '// 每一步都写一遍总结，合起来就是六段废话）。\n'
    'function wdsResearchSys(rs) {\n'
    '  if (!rs) return "";\n'
    '  return "\\n\\n【你正在做一次深度研究 · 第 " + rs.i + "/" + rs.n + " 步】"\n'
    '    + "\\n总题：" + rs.topic\n'
    '    + "\\n这一步只负责：" + rs.t\n'
    '    + (rs.done ? ("\\n前面几步已经写过（只列小标题，别重复它们的内容、别再下一遍同样的判断）：\\n" + rs.done) : "")\n'
    '    + "\\n写法：**解除《怎么答》第 5 条的\\"两三段以内\\"**，这一节写 1200–2000 字；开门见山进判断，"\n'
    '    + "不要开场白、不要\\"本节将\\"、不要在末尾总结全篇（总判断是最后一步的活）。"\n'
    '    + "\\n每提到一篇站内文章就写成可点链接；凡是\\"据资料/据搜索\\"的说法都要落到具体出处。"\n'
    '    + "\\n这一步若没有可靠依据，就直说这一步查不到、说清缺的是哪一类证据——**不要拿泛论把这一节填满**。";\n'
    '}\n'
    'function WDS_CHAT_SYS(reflect, SDEM, siteCtx, webCtx, deep, docCtx, about, lang, docNote, tool, rs) {',
    "研究步 system 块",
)
sub1(
    '    + wdsToolSys(tool)\n',
    '    + wdsToolSys(tool)\n    + wdsResearchSys(rs)\n',
    "研究步块挂进 system",
)

# ── ④ /api/wds/chat：收 imgs / comp / rs ─────────────────────────
sub1(
    '      const tool = WDS_TOOL_KEYS.indexOf(String(b.tool || "")) >= 0 ? String(b.tool) : "";\n'
    '      const VC = { url: WDS_VENDORS[vd].url, model: wdsPickModel(vd, umodel, deep), name: WDS_VENDORS[vd].name, top: deep ? 1 : 0 };',
    '      const tool = WDS_TOOL_KEYS.indexOf(String(b.tool || "")) >= 0 ? String(b.tool) : "";\n'
    '      // COMPACTION：本场更早的对话已在读者本机压成一份「账本」（只留判断/否决/分离线/悬案）。\n'
    '      // 它替代的是被裁掉的原文，所以位置在历史之前、且必须**标明它是账本不是原文**——\n'
    '      // 否则它会照着账本复述，把压缩过的结论当成自己刚说过的话。\n'
    '      const comp = String(b.comp || "").slice(0, 8000);\n'
    '      // RESEARCH：深度研究的一步。走同一条产线（检索/联网/流式/时钟全都现成），只换口径与预算。\n'
    '      const rsRaw = (b.rs && typeof b.rs === "object") ? b.rs : null;\n'
    '      const rs = rsRaw ? {\n'
    '        i: Math.max(1, Math.min(12, parseInt(rsRaw.i, 10) || 1)),\n'
    '        n: Math.max(1, Math.min(12, parseInt(rsRaw.n, 10) || 1)),\n'
    '        t: String(rsRaw.t || "").slice(0, 200),\n'
    '        topic: String(rsRaw.topic || "").slice(0, 300),\n'
    '        done: String(rsRaw.done || "").slice(0, 3000),\n'
    '      } : null;\n'
    '      // VISION：读者带来的图。**图不进附件那条文字线**——附件线走的是 OCR 出来的字，\n'
    '      // 那是"读它印了什么"，不是"看它长什么样"（图表的形状、版式、手写、白板上的箭头，OCR 一个都给不出）。\n'
    '      const imgs = wdsPickImgs(b.imgs);\n'
    '      const visLadder = imgs.length ? wdsVisionLadder(vd, String(b.vmodel || "")) : [];\n'
    '      const canSee = imgs.length > 0 && visLadder.length > 0;\n'
    '      // 看图时一律卸掉满功率档：视觉档型号多半没有思考开关，且这一步的活是"看清"不是"想久"。\n'
    '      const VC = canSee\n'
    '        ? { url: WDS_VENDORS[vd].url, model: visLadder[0], name: WDS_VENDORS[vd].name, top: 0 }\n'
    '        : { url: WDS_VENDORS[vd].url, model: wdsPickModel(vd, umodel, deep), name: WDS_VENDORS[vd].name, top: deep ? 1 : 0 };',
    "chat 入参：imgs/comp/rs",
)

# 出流后：如实告知看不了图
sub1(
    '            if (qCut > 0) controller.enqueue(_sseBytes({ t: "note", v: "你这一问超过 "',
    '            if (imgs.length && !canSee) controller.enqueue(_sseBytes({ t: "note", v: "你传了 " + imgs.length + " 张图，但你现在选的这家基底在本站的接口下看不了图（能看图的是 智谱 GLM / 千问 Qwen / Kimi）。这一轮它**没有看到图**，只能就你的文字作答——要它真看图，去顶栏换一家。" }));\n'
    '            else if (canSee) controller.enqueue(_sseBytes({ t: "note", v: "已把 " + imgs.length + " 张图直接交给 " + VC.name + " 的视觉档（" + VC.model + "）看——不是文字识别。" }));\n'
    '            if (qCut > 0) controller.enqueue(_sseBytes({ t: "note", v: "你这一问超过 "',
    "看图提示",
)

# 近邻/检索：研究步照常检索；但 system 拼装处要把 rs 传进去
sub1(
    '            const sys = WDS_CHAT_SYS(reflect, SDEM, (nbrCtx ? nbrCtx + "\\n" : "") + ctxText, webCtx, deep, docCtx, about, lang, docNote, tool);',
    '            const sys = WDS_CHAT_SYS(reflect, SDEM, (nbrCtx ? nbrCtx + "\\n" : "") + ctxText, webCtx, deep, docCtx, about, lang, docNote, tool, rs);',
    "system 传 rs",
)

# 账本插在历史之前
sub1(
    '            const packed = packReadHistory(history, histBudget, WDS_CHAT_PERMSG,\n'
    '              (n) => "（本场更早的 " + n + " 条发言因长度省略；这是同一场持续对话，请接着往下谈。）");\n'
    '            for (const m of packed) messages.push(m);',
    '            if (comp) messages.push({\n'
    '              role: "user",\n'
    '              content: "【本场前情账本】以下不是原文，是这场对话更早那些轮次压出来的账本（只留下：已落下的判断、已否决的路线、已划的分离线、还悬着的问题）。"\n'
    '                + "把它当成已经发生过的事实接着往下谈；**不要复述它**，也不要假装记得账本里没写的细节。\\n" + comp,\n'
    '            });\n'
    '            const packed = packReadHistory(history, histBudget, WDS_CHAT_PERMSG,\n'
    '              (n) => "（本场更早的 " + n + " 条发言因长度省略；这是同一场持续对话，请接着往下谈。）");\n'
    '            for (const m of packed) messages.push(m);',
    "账本插入",
)

# 当轮 user 消息：看图时改成 content 数组
sub1(
    '            messages.push({\n'
    '              role: "user",\n'
    '              content: q + UMEM + (askLen\n'
    '                ? ("\\n\\n（本轮特别要求：读者要的是长篇，约 " + askLen + " 字。解除《怎么答》第 5 条的\\"两三段以内\\"，按这个长度写足；"\n'
    '                   + "别在心里反复打草稿，边想边落笔——写不完读者会点「继续」。）")\n'
    '                : ""),\n'
    '            });',
    '            const uText = q + UMEM + (askLen\n'
    '              ? ("\\n\\n（本轮特别要求：读者要的是长篇，约 " + askLen + " 字。解除《怎么答》第 5 条的\\"两三段以内\\"，按这个长度写足；"\n'
    '                 + "别在心里反复打草稿，边想边落笔——写不完读者会点「继续」。）")\n'
    '              : "");\n'
    '            // 看图时当轮 user 是 content 数组（各家都吃 OpenAI 那套 image_url/data URL）。\n'
    '            // 图放在文字**之后**：先让它知道要看什么，再给它看。\n'
    '            messages.push({\n'
    '              role: "user",\n'
    '              content: canSee\n'
    '                ? [{ type: "text", text: uText + "\\n\\n（上面这 " + imgs.length + " 张图是读者刚传的：" + imgs.map((im) => im.n).join("、")\n'
    '                    + "。请直接看图作答；图里看不清的地方就说看不清，不要猜。）" }]\n'
    '                    .concat(imgs.map((im) => ({ type: "image_url", image_url: { url: im.d } })))\n'
    '                : uText,\n'
    '            });',
    "当轮 user 消息（看图走数组）",
)

# 预算 & 时钟：研究步单独一档
sub1(
    '            const tokWant = askLen\n'
    '              ? Math.min(32000, Math.max(6000, Math.round(askLen * 1.8)))   // 中文近似 1 字 1 token，留一点余量\n'
    '              : (deep ? 6000 : (tool ? 4000 : 2600));',
    '            // 预算按"这一步该产出多长"给（老通则）：研究的一节 1200–2000 字 → 4000；满功率档仍死守 6000（≤8000 是硬约束）。\n'
    '            const tokWant = askLen\n'
    '              ? Math.min(32000, Math.max(6000, Math.round(askLen * 1.8)))   // 中文近似 1 字 1 token，留一点余量\n'
    '              : (rs ? (deep ? 6000 : 4000) : (deep ? 6000 : (tool ? 4000 : 2600)));',
    "研究步预算",
)

# 视觉档型号阶梯：上游 400/404 说型号不认时退一格重发
sub1(
    '            let upstream;\n'
    '            try {\n'
    '              upstream = await fetch(VC.url, { method: "POST", headers: { "content-type": "application/json", authorization: "Bearer " + KEY }, body: JSON.stringify(wdsTopBody(VC, { model: VC.model, stream: true, max_tokens: tokWant, messages })), signal: clk.signal });\n'
    '            } catch (e) {',
    '            let upstream;\n'
    '            try {\n'
    '              // 视觉档型号会改名/下线：认不出就沿备用名退一格重发一次（只在看图这条路上，且只退到列表用完）。\n'
    '              for (let vi = 0; ; vi++) {\n'
    '                upstream = await fetch(VC.url, { method: "POST", headers: { "content-type": "application/json", authorization: "Bearer " + KEY }, body: JSON.stringify(wdsTopBody(VC, { model: VC.model, stream: true, max_tokens: tokWant, messages })), signal: clk.signal });\n'
    '                if (upstream.ok || !canSee || vi + 1 >= visLadder.length) break;\n'
    '                if (upstream.status !== 400 && upstream.status !== 404) break;\n'
    '                let et = ""; try { et = (await upstream.clone().text()).slice(0, 300); } catch (e2) {}\n'
    '                if (!/model|not\\s*found|不存在|无效|invalid/i.test(et)) break;\n'
    '                VC.model = visLadder[vi + 1];\n'
    '                controller.enqueue(_sseBytes({ t: "note", v: "视觉档型号换成了 " + VC.model + "（上一个这家已经不认了）。" }));\n'
    '              }\n'
    '            } catch (e) {',
    "视觉型号阶梯",
)

# 研究步不出追问建议（那是给读者接着聊用的，研究流程里是噪音）
sub1(
    '            if (outText.length > 150) {\n'
    '              const fVC = { url: WDS_VENDORS[vd].url, model: WDS_VENDORS[vd].model };',
    '            if (outText.length > 150 && !rs) {\n'
    '              const fVC = { url: WDS_VENDORS[vd].url, model: WDS_VENDORS[vd].model };',
    "研究步不出追问",
)

# ── ⑤ /api/wds/summarize 加 mode=ledger ─────────────────────────
sub1(
    '      const mode = b.mode === "l2" ? "l2" : (b.mode === "long" ? "long" : "l1");',
    '      const mode = b.mode === "l2" ? "l2" : (b.mode === "long" ? "long" : (b.mode === "ledger" ? "ledger" : "l1"));',
    "summarize mode=ledger",
)
sub1(
    '      const sys = mode === "long"\n',
    '      // LEDGER：问WDS 的本场压缩。压缩的口径不是"聊了什么"，而是"落下了哪几条"——\n'
    '      // 摘要式的压缩会把判断磨成概述（"讨论了教育问题"），下一轮它就只剩一团雾；\n'
    '      // 账本式的压缩留下的是能被反驳的句子，接着谈才接得上。\n'
    '      const sys = mode === "ledger"\n'
    '        ? "你在为一场持续对话维护一份【账本】。下面是这场对话较早的一段原文。把它压成账本，**只留四类**，其余全部丢掉：\\n"\n'
    '          + "1. 已经落下的判断 —— 一条一句，要是能被反驳的那种句子，不是\\"讨论了X\\"这种概述；\\n"\n'
    '          + "2. 已经否决的路线 —— 连同否决的理由；\\n"\n'
    '          + "3. 已经划出的分离线 —— 这个说法与最近的既有说法差在哪；\\n"\n'
    '          + "4. 还悬着的问题 / 这场里新起的名字。\\n"\n'
    '          + "格式：四个小标题，每条一行、前面加「- 」。总量 400 字以内。不要寒暄、不要写\\"读者问/WDS答\\"、不要写概述句。"\n'
    '          + "某一类在这段里根本没有，就写「（无）」——**不要凑**。"\n'
    '        : mode === "long"\n',
    "ledger 提示语",
)
sub1(
    '        const out = await llmText(VC, KEY, sys, text, mode === "l1" ? 500 : 900);',
    '        const out = await llmText(VC, KEY, sys, text, mode === "l1" ? 500 : 900);   // ledger 走 900：四类小标题装得下，且远在"结构化短输出必须有界"那条线内',
    "ledger 预算",
)

# ── ⑥ 新端点 /api/wds/research ───────────────────────────────────
RESEARCH = r'''    // ── 深度研究 /api/wds/research ─────────────────────────────────────────
    // 分两个 mode，**中间那几步不在这里**：每一步都走 /api/wds/chat（带 rs 字段），
    // 因为检索/联网/流式/心跳/时钟/限流那一整套已经在那条产线上跑熟了，重写一份只会多一份 bug。
    //   mode=plan  —— 拆题。结构化 JSON，**必须非满功率＋有界预算**（老教训：满功率写 JSON 必崩）。非流式。
    //   mode=final —— 总判断。流式（先出流后干活＋心跳＋时钟），只吃各步正文，不再检索。
    if (url.pathname === "/api/wds/research") {
      if (request.method === "OPTIONS") return new Response(null, { headers: _cors() });
      if (request.method !== "POST") return new Response("Method Not Allowed", { status: 405 });
      let b = {}; try { b = await request.json(); } catch (e) {}
      const vd = wdsVendorOf(b.vendor);
      const KEY = String(b.key || "").trim();
      const lang = b.lang === "en" ? "en" : "zh";
      const q = String(b.q || "").trim().slice(0, 4000);
      const mode = b.mode === "final" ? "final" : "plan";
      if (KEY.length < 8) {
        if (mode === "plan") return Response.json({ ok: false, code: "need_key", msg: "深度研究用你自己的 API Key 运行（在设置里填入，只存在你的浏览器本地）。" }, { status: 200, headers: _cors() });
        return _sseResp([{ t: "error", v: "深度研究用你自己的 API Key 运行。", code: "need_key" }]);
      }
      const LANG = lang === "en" ? "\n\nWrite in English." : "";
      if (mode === "plan") {
        if (!q) return Response.json({ ok: false, msg: "先给一个要研究的题目。" }, { status: 200, headers: _cors() });
        const want = Math.max(3, Math.min(6, parseInt(b.n, 10) || 4));
        // 非满功率（结构化输出的铁律）＋ 有界预算 ＋ 短时限：拆题是配菜，卡住就该空手回来。
        const VC = { url: WDS_VENDORS[vd].url, model: wdsPickModel(vd, String(b.model || ""), 0), name: WDS_VENDORS[vd].name };
        const sys = "你在替 WDS（王德生的 AI 分身、SDE 本体论老师）为一次深度研究拆题。"
          + "读者给一个题目，你把它拆成 " + want + " 个**依次推进**的取证步骤——不是把题目换几种说法，而是每一步都去查一类不同的东西、"
          + "且后一步要能站在前一步的结论上。最后一步之后会另有一次总判断，所以**不要留一步叫\"总结\"**。"
          + "每一步要能被单独拿去做一次全站检索＋联网检索，所以写成一个具体的问句，别写成名词短语。"
          + "\n只输出 JSON，形如："
          + "{\"title\":\"这次研究的标题（一句，不超过 24 字）\",\"steps\":[{\"t\":\"第一步要查清的具体问句\",\"why\":\"为什么这一步必须在前面（一句）\"}]}"
          + "\n不要 Markdown 代码围栏，不要任何解释文字。" + LANG;
        try {
          const out = await llmText(VC, KEY, sys, "题目：" + q, 3000, 60000);
          const j = looseJSON(out || "");
          const steps = (j && Array.isArray(j.steps) ? j.steps : [])
            .map((s) => ({ t: String((s && s.t) || "").trim().slice(0, 200), why: String((s && s.why) || "").trim().slice(0, 200) }))
            .filter((s) => s.t).slice(0, 6);
          if (!steps.length) return Response.json({ ok: false, msg: "拆题没成——再点一次，或把题目说得更具体些。" }, { status: 200, headers: _cors() });
          return Response.json({ ok: true, title: String((j && j.title) || q).slice(0, 80), steps }, { status: 200, headers: _cors() });
        } catch (e) {
          return Response.json({ ok: false, msg: "拆题出错：" + (e && e.message) }, { status: 200, headers: _cors() });
        }
      }
      // ── mode=final：总判断 ──
      const secs = (Array.isArray(b.secs) ? b.secs : []).slice(0, 8).map((s) => ({
        t: String((s && s.t) || "").slice(0, 200),
        body: String((s && s.body) || "").slice(0, 4000),   // 只吃各步的前 4000 字：总判断要的是它们的落点，不是全文重读
      })).filter((s) => s.body);
      if (!secs.length) return _sseResp([{ t: "error", v: "没有可用的分步正文，写不了总判断。" }]);
      const deep = b.mode2 === "deep" || !!b.deep;
      const VC = deep ? wdsTopVC(vd) : { url: WDS_VENDORS[vd].url, model: wdsPickModel(vd, String(b.model || ""), 0), name: WDS_VENDORS[vd].name };
      const ip = request.headers.get("cf-connecting-ip") || "unknown";
      try {
        const lim = env.ASK_LIMITER.get(env.ASK_LIMITER.idFromName(wdsBucket("chat", ip, KEY)));
        const lr = await (await lim.fetch(new Request("https://limiter.internal/?w=" + WDS_PER_MIN + "&d=" + WDS_PER_DAY))).json();
        if (!lr.ok) return _sseResp([{ t: "error", v: lr.reason === "day" ? "这把 Key 今天的额度用完了，明天再来。" : "太快啦，过十几秒再来。" }]);
      } catch (e) {}
      const stream = new ReadableStream({
        async start(controller) {
          let _hb = null;
          const fin = () => { if (_hb) clearInterval(_hb); try { controller.enqueue(_ENC.encode("data: [DONE]\n\n")); controller.close(); } catch (e) {} };
          const _st = { t0: Date.now(), think: 0, out: 0, stage: "写总判断" };
          _hb = wdsBeat(controller, _st);
          try {
            let reflect = ""; try { reflect = await ensureReflect(env, url, wdsShort(vd), VC, KEY); } catch (e) {}
            const sys = "你是 WDS，王德生的 AI 分身、SDE 本体论老师。一次深度研究的各分步已经写完，现在只剩最后一件活：**下总判断**。"
              + (reflect ? ("\n\n【SDE 内化心得·思考底盘（别复述、别提\"心得\"二字）】\n" + reflect) : "")
              + "\n\n【总判断怎么写】"
              + "\n1. 开头一句就是结论——这次研究把什么问题从哪儿挪到了哪儿。不许有\"本文/本次研究将\"这类开场。"
              + "\n2. 然后写三件事，各一段："
              + "\n   · **撞出来的那一条**：把各步单独看不出、合起来才成立的那个判断说出来。这是这份报告存在的理由；写不出来就老实说各步之间没撞出新东西。"
              + "\n   · **各步之间打架的地方**：哪两步的结论互相矛盾、矛盾在哪一层。不要和稀泥。"
              + "\n   · **这次没查到的**：缺的是哪一类证据、要往哪儿再查一步。"
              + "\n3. 最后给一条可被反驳的判断，并写明它的证伪条件（什么情况出现就说明它错了）。"
              + "\n4. 全程说人话，不堆术语；1000 字上下；不要重复各步已经写过的细节。" + LANG;
            const usr = "研究题目：" + q + "\n\n【各分步的正文（节选）】\n"
              + secs.map((s, i) => "── 第 " + (i + 1) + " 步 · " + s.t + " ──\n" + s.body).join("\n\n");
            const clk = wdsClock(CHAT_FIRST_MS, CHAT_TOTAL_MS);
            let upstream;
            try {
              upstream = await wdsFetchMax(VC, KEY, [{ role: "system", content: sys }, { role: "user", content: usr }], true, deep ? 6000 : 4000, clk.signal);
            } catch (e) {
              clk.stop();
              controller.enqueue(_sseBytes({ t: "error", v: (clk.cut ? clk.why("基底") : ("接不上基底：" + (e && e.message))) }));
              return fin();
            }
            if (!upstream.ok) {
              const errtxt = (await upstream.text()).slice(0, 300);
              if (upstream.status === 401 || upstream.status === 402 || upstream.status === 429) { controller.enqueue(_sseBytes({ t: "error", v: "你的 Key 用不了（" + upstream.status + "）。", code: "bad_key" })); return fin(); }
              controller.enqueue(_sseBytes({ t: "error", v: "基底返回错误 " + upstream.status + "：" + errtxt })); return fin();
            }
            const reader = upstream.body.getReader();
            const dec = new TextDecoder();
            let buf = "", outText = "";
            try {
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
                  if (d.reasoning_content) { clk.firstFrame(); _st.think += d.reasoning_content.length; controller.enqueue(_sseBytes({ t: "think", v: d.reasoning_content })); }
                  if (d.content) { clk.firstFrame(); _st.out += d.content.length; outText += d.content; controller.enqueue(_sseBytes({ t: "token", v: d.content })); }
                }
              }
            } catch (e) {
              const why = clk.cut ? clk.why("总判断") : ("流中断：" + (e && e.message));
              if (outText) controller.enqueue(_sseBytes({ t: "note", v: why + "——已写出的部分保留着。" }));
              else controller.enqueue(_sseBytes({ t: "error", v: why }));
            }
            clk.stop();
          } catch (e) {
            controller.enqueue(_sseBytes({ t: "error", v: "总判断出错：" + (e && e.message) }));
          }
          fin();
        },
      });
      return new Response(stream, { headers: { ..._cors(), "content-type": "text/event-stream; charset=utf-8", "cache-control": "no-store" } });
    }
'''
sub1(
    '    // /api/wds/asr：语音转文字。读者在浏览器里录音、编成 16k 单声道 WAV，这里转发给 GLM-ASR。',
    RESEARCH + '    // /api/wds/asr：语音转文字。读者在浏览器里录音、编成 16k 单声道 WAV，这里转发给 GLM-ASR。',
    "research 端点",
)

open(P, "w", encoding="utf-8").write(h)
print("worker.js: %d → %d bytes（+%d）" % (len(orig), len(h), len(h) - len(orig)))
