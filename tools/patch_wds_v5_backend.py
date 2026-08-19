#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""问WDS 第二梯队 · 后端（src/worker.js）

① /api/wds/readurl —— 贴一个链接就把这一篇读进来（不调基底、不烧 Key，只抓正文）
② 结构图工序 map —— 产出一个 mermaid 块，正好落进第三批做好的画布里渲染

readurl 的安全边界（这是把 Worker 变成取物工具，必须写清楚）：
  · 只认 http/https；内网地址、localhost、本站自身一律拒（自请求回环实测直接 522）
  · 只收 HTML/纯文本，原始体积封顶、抽出的正文封顶
  · 不带任何凭证、不透传请求头、不回传原始字节，只回抽出来的文字
  · 走限流器（它不烧读者的 Key，所以更要防被人当免费代理刷）
"""
P = "/home/claude/site/src/worker.js"
h = open(P, encoding="utf-8").read()
orig = h


def sub1(old, new, why):
    global h
    n = h.count(old)
    assert n == 1, "锚点应恰好出现一次，实际 %d 次：%s（%s）" % (n, old[:70], why)
    h = h.replace(old, new, 1)


# ── ① 结构图工序 ──
sub1(
    'const WDS_TOOL_KEYS = ["iq", "three", "motif", "nbr", "rename", "gap", "collide", "grid", "nine"];',
    'const WDS_TOOL_KEYS = ["iq", "three", "motif", "nbr", "rename", "gap", "collide", "grid", "nine", "map"];',
    "工序白名单加 map",
)
sub1(
    "const WDS_TOOLS = {\n",
    "const WDS_TOOLS = {\n"
    '  // 结构图：画出来，不是描述。产出一个 mermaid 块——前端画布会直接把它渲染成图。\n'
    '  // 三条硬规矩都是渲染踩出来的：节点名带括号/引号/分号会让 mermaid 当场解析失败；\n'
    '  // 无名箭头等于没画（一堆方框连线，读者看不出关系）；节点过多就是没抓住主干。\n'
    '  map: "【本轮工序 · 结构图】把这一问里的结构**画出来**，不要用文字描述它。"\n'
    '    + "\\n输出两段，顺序不能反："\n'
    '    + "\\n① 一个 mermaid 围栏代码块（```mermaid 开头）。有方向、有先后、有依赖的用 `flowchart TD`；只是分层归类的用 `mindmap`。"\n'
    '    + "\\n   · 每个节点文字不超过 12 字；**节点文字里不许出现圆括号、引号、分号、冒号**（会让图当场渲染不出来）。"\n'
    '    + "\\n   · 每条边都要写关系动词（`A -->|约束| B`、`B -->|反过来锁死| A`），不要画一堆无名箭头——无名箭头等于没画。"\n'
    '    + "\\n   · 最多 18 个节点。画不下说明你还没抓住主干，那就重挑主干，不要塞。"\n'
    '    + "\\n② 图下面三到五句话：这张图最承重的是哪一条边；哪一条是你不确定的；抽掉哪个节点整张图就散。"\n'
    '    + "\\n这一问本来就没有结构可画，就直说没有——**不要硬凑一张好看的图**，凑出来的结构图比没有更误导人。",\n\n',
    "map 工序正文",
)

# ── ② /api/wds/readurl ──
READURL = r'''    // ── 贴链接读全文 /api/wds/readurl ───────────────────────────────────────
    // 联网搜索解决的是"去找几条"，这个解决的是"就读这一篇"。不调基底、不烧任何 Key，只抓正文。
    // 【安全边界】它把 Worker 变成了一个取物工具，所以每一条都要守：
    //   只认 http/https · 内网与本站自身一律拒（自请求回环实测 522）· 只收 HTML/纯文本 ·
    //   原始体积与抽出正文双封顶 · 不带凭证不透传头不回原始字节 · 走限流（它不烧读者 Key，更要防被当免费代理刷）。
    if (url.pathname === "/api/wds/readurl") {
      if (request.method === "OPTIONS") return new Response(null, { headers: _cors() });
      if (request.method !== "POST") return new Response("Method Not Allowed", { status: 405 });
      let b = {}; try { b = await request.json(); } catch (e) {}
      const J = (o, st) => Response.json(o, { status: st || 200, headers: _cors() });
      const raw = String(b.u || "").trim();
      if (!/^https?:\/\//i.test(raw)) return J({ ok: false, msg: "只认 http:// 或 https:// 开头的网址。" });
      let U;
      try { U = new URL(raw); } catch (e) { return J({ ok: false, msg: "这个网址解析不了。" }); }
      const host = U.hostname.toLowerCase();
      // 内网/环回/链路本地/本站自身：一个都不许取
      const blocked = host === "localhost" || host === "0.0.0.0" || host === "[::1]" || host === "::1"
        || /\.(local|internal|localdomain)$/.test(host)
        || /^127\./.test(host) || /^10\./.test(host) || /^192\.168\./.test(host)
        || /^169\.254\./.test(host) || /^172\.(1[6-9]|2[0-9]|3[01])\./.test(host)
        || host === url.hostname.toLowerCase();
      if (blocked) return J({ ok: false, msg: "这个地址不给取（内网地址、本机地址、或本站自己）。" });
      const ip = request.headers.get("cf-connecting-ip") || "unknown";
      try {
        const lim = env.ASK_LIMITER.get(env.ASK_LIMITER.idFromName(wdsBucket("readurl", ip, "")));
        const lr = await (await lim.fetch(new Request("https://limiter.internal/?w=10&d=120"))).json();
        if (!lr.ok) return J({ ok: false, msg: lr.reason === "day" ? "今天取链接的次数用完了，明天再来。" : "取得太快啦，过十几秒再来。" });
      } catch (e) {}
      const ac = new AbortController();
      const tm = setTimeout(() => { try { ac.abort(); } catch (e) {} }, 15000);
      let r;
      try {
        r = await fetch(U.toString(), {
          method: "GET",
          redirect: "follow",
          signal: ac.signal,
          headers: {
            // 只给一个像浏览器的身份，**不带任何凭证、不透传读者的请求头**
            "user-agent": "Mozilla/5.0 (compatible; SDEUniversesReader/1.0; +https://sdeuniverses.com)",
            "accept": "text/html,application/xhtml+xml,text/plain;q=0.9",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
          },
        });
      } catch (e) {
        clearTimeout(tm);
        return J({ ok: false, msg: "取不到这一页：" + ((e && e.name === "AbortError") ? "15 秒还没响应（已掐断）" : (e && e.message)) });
      }
      clearTimeout(tm);
      if (!r.ok) return J({ ok: false, msg: "对方返回 " + r.status + "（多半是要登录、或者不让程序取）。" });
      const ct = String(r.headers.get("content-type") || "").toLowerCase();
      if (ct.indexOf("text/html") < 0 && ct.indexOf("text/plain") < 0 && ct.indexOf("xhtml") < 0) {
        return J({ ok: false, msg: "这一页不是网页正文（" + (ct.split(";")[0] || "未知类型") + "）。PDF/Word 请下载后用「＋」当附件传，那样是在你自己机器上解析的。" });
      }
      let html = "";
      try { html = (await r.text()).slice(0, 3 * 1024 * 1024); } catch (e) { return J({ ok: false, msg: "这一页读不出文字。" }); }
      const out = wdsHtmlText(html);
      if (!out.text || out.text.length < 60) return J({ ok: false, msg: "这一页抽不出正文（多半正文是脚本渲染出来的）。可以把正文复制下来贴进提问框。" });
      return J({ ok: true, url: U.toString(), title: out.title || U.hostname, text: out.text, note: "网页 · " + U.hostname });
    }
'''
sub1(
    "    // /api/wds/asr：语音转文字。读者在浏览器里录音、编成 16k 单声道 WAV，这里转发给 GLM-ASR。",
    READURL + "    // /api/wds/asr：语音转文字。读者在浏览器里录音、编成 16k 单声道 WAV，这里转发给 GLM-ASR。",
    "readurl 端点",
)

# 正文抽取器（放在 webBlock 附近，属于同一族"把外面的东西变成可读材料"）
sub1(
    "function webBlock(items) {",
    "// 从 HTML 里抽正文。刻意用最笨的办法：先剔掉整块非正文标签，再把标签抹掉。\n"
    "// 不追求完美——追求的是「抽出来的一定是这一页的字，而不是脚本和样式」。\n"
    "// 抽不出来就让上层如实说抽不出来，别拿导航栏和页脚冒充正文。\n"
    "function wdsHtmlText(html) {\n"
    "  const s0 = String(html || \"\");\n"
    "  let title = \"\";\n"
    "  const mt = s0.match(/<title[^>]*>([\\s\\S]{0,200}?)<\\/title>/i);\n"
    "  if (mt) title = mt[1].replace(/\\s+/g, \" \").trim();\n"
    "  let s = s0\n"
    "    .replace(/<!--[\\s\\S]*?-->/g, \" \")\n"
    "    .replace(/<(script|style|noscript|svg|canvas|iframe|template|form|select|button)[\\s\\S]*?<\\/\\1>/gi, \" \")\n"
    "    .replace(/<(nav|header|footer|aside)[\\s\\S]*?<\\/\\1>/gi, \" \");\n"
    "  // 块级标签换行，行内标签直接去掉——不这样整页会挤成一行，读者与基底都读不出段落\n"
    "  s = s.replace(/<\\/(p|div|section|article|li|tr|h[1-6]|blockquote|pre)>/gi, \"\\n\")\n"
    "       .replace(/<br\\s*\\/?>/gi, \"\\n\")\n"
    "       .replace(/<[^>]+>/g, \" \");\n"
    "  s = s.replace(/&nbsp;/g, \" \").replace(/&amp;/g, \"&\").replace(/&lt;/g, \"<\").replace(/&gt;/g, \">\")\n"
    "       .replace(/&quot;/g, '\"').replace(/&#39;/g, \"'\").replace(/&mdash;/g, \"—\").replace(/&hellip;/g, \"…\")\n"
    "       .replace(/&#(\\d{2,5});/g, (m, d) => { try { return String.fromCharCode(parseInt(d, 10)); } catch (e) { return \" \"; } });\n"
    "  s = s.replace(/[ \\t\\u00a0]+/g, \" \").replace(/\\n[ \\t]+/g, \"\\n\").replace(/\\n{3,}/g, \"\\n\\n\").trim();\n"
    "  return { title, text: s.slice(0, 120000) };\n"
    "}\n"
    "function webBlock(items) {",
    "HTML 正文抽取器",
)

open(P, "w", encoding="utf-8").write(h)
print("worker.js: %d → %d bytes（+%d）" % (len(orig), len(h), len(h) - len(orig)))
