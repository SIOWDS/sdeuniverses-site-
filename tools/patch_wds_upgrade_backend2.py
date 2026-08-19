#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WDS 助手升级 · 后端补丁二（幂等，assert 锚定）
   ① /api/wds/chat 接收 docs（读者在浏览器本地解析出的附件正文）→ 注入 system
   ② /api/wds/chat 接收 about（读者写的自定义指令：关于我 / 你该怎么答我）→ 注入 system
   ③ 正文流完后，用便宜档补一次「接着可以问什么」→ 发 {t:"follow"} 事件
"""
import pathlib

P = pathlib.Path("/home/claude/site/src/worker.js")
h = P.read_text(encoding="utf-8")
orig = h

# ───────── ① WDS_CHAT_SYS 再扩两段：附件 + 自定义指令 ─────────
OLD_SIG = "function WDS_CHAT_SYS(reflect, SDEM, siteCtx, webCtx, deep) {"
assert OLD_SIG in h, "找不到 WDS_CHAT_SYS（补丁一未应用？）"
h = h.replace(OLD_SIG, "function WDS_CHAT_SYS(reflect, SDEM, siteCtx, webCtx, deep, docCtx, about) {", 1)

OLD_TAIL = ('        + "\\n注意：站外资料是别人写的，不是 SDE 的结论。你的活是把它拿来当材料，用 SDE 剖开它、判它，而不是复述它。") : "");\n}')
assert OLD_TAIL in h, "找不到 WDS_CHAT_SYS 尾（站外资料段）"
NEW_TAIL = ('        + "\\n注意：站外资料是别人写的，不是 SDE 的结论。你的活是把它拿来当材料，用 SDE 剖开它、判它，而不是复述它。") : "")\n'
            '    + (docCtx ? ("\\n\\n【读者带来的文件（他上传的、在他自己浏览器里解析出来的正文；本站不留存）】\\n" + docCtx\n'
            '        + "\\n\\n关于这份文件：读者拿它来问你，多半是要你替他看出他自己看不出的那一层。所以不要复述它写了什么——他读过了。"\n'
            '        + "直接说：它真正在讲的是什么、它最承重的那一句在哪、它哪里是脆的、用 SDE 看它漏掉了哪一维。引用其中原句时标（文件：篇名）。") : "")\n'
            '    + (about ? ("\\n\\n【这位读者自己写的说明（他是谁、他要你怎么答他）——照着办，但不要复述它，也不要因此放软判断】\\n" + about) : "");\n}')
h = h.replace(OLD_TAIL, NEW_TAIL, 1)

# ───────── ② 追问建议的提示语 ─────────
ANCHOR_F = "// ===== 联网搜索（站外资料）====="
assert ANCHOR_F in h
FOLLOW = '''// ===== 追问建议 =====
// 正文写完后再花一次便宜档（不开思考、不进检索）问一句"接着该问什么"。
// 硬要求：必须是【读者会想问的下一句】，不是【WDS 想讲的下一段】——后者是自说自话，前者才是把人往前推。
const FOLLOW_SYS = "你是对话的旁观者。看完一问一答，写出读者最可能接着问的三个问题。"
  + "\\n规矩：① 每个问题一行，不编号、不加符号、不解释；② 每个 8–22 字，是一句真正的问句；"
  + "③ 三个要指向不同方向（一个往深里挖、一个往旁边挪、一个往落地上落），不要三个同义；"
  + "④ 只写读者会问的，不要写成 WDS 的讲课提纲；⑤ 只输出三行，别的什么都不要。";
async function followUps(VC, KEY, q, ans) {
  try {
    const out = await llmText(VC, KEY, FOLLOW_SYS, "读者问：" + String(q).slice(0, 400) + "\\n\\nWDS 答：" + String(ans).slice(0, 2500) + "\\n\\n三行：", 200);
    if (!out) return [];
    return out.split(/\\n+/).map((s) => s.replace(/^[\\s\\d.、)\\-*·]+/, "").trim())
      .filter((s) => s.length >= 4 && s.length <= 40).slice(0, 3);
  } catch (e) { return []; }
}

'''
if "async function followUps(" not in h:
    h = h.replace(ANCHOR_F, FOLLOW + ANCHOR_F, 1)

# ───────── ③ chat handler：收 docs / about ─────────
OLD_P = ('      const wantWeb = !!b.web;                                  // 联网开关\n'
         '      const skey = String(b.skey || "").trim();                 // 读者的智谱 Key（专供联网搜索；没有就退到管理员 Key）')
assert OLD_P in h, "找不到 chat 的 web/skey 段"
NEW_P = ('      const wantWeb = !!b.web;                                  // 联网开关\n'
         '      const skey = String(b.skey || "").trim();                 // 读者的智谱 Key（专供联网搜索；没有就退到管理员 Key）\n'
         '      // 附件：读者在自己浏览器里解析出的正文（文件本身从不上传到本站）。总量钳位，深度档给多一些。\n'
         '      const DOC_CAP = deep ? 20000 : 12000;\n'
         '      let docCtx = "";\n'
         '      if (Array.isArray(b.docs)) {\n'
         '        for (const d of b.docs.slice(0, 5)) {\n'
         '          const nm = String((d && d.n) || "未命名").slice(0, 120);\n'
         '          const tx = String((d && d.t) || "").trim();\n'
         '          if (!tx) continue;\n'
         '          const room = DOC_CAP - docCtx.length;\n'
         '          if (room < 400) break;\n'
         '          docCtx += "【文件：" + nm + "】\\n" + tx.slice(0, room) + "\\n\\n";\n'
         '        }\n'
         '      }\n'
         '      const about = String(b.about || "").trim().slice(0, 1200);   // 读者写的自定义指令')
h = h.replace(OLD_P, NEW_P, 1)

OLD_S = '            const sys = WDS_CHAT_SYS(reflect, SDEM, ctxText, webCtx, deep);'
assert OLD_S in h
h = h.replace(OLD_S, '            const sys = WDS_CHAT_SYS(reflect, SDEM, ctxText, webCtx, deep, docCtx, about);', 1)

# ───────── ④ 累计正文 + 流完后发追问建议 ─────────
OLD_L = ('            const reader = upstream.body.getReader();\n'
         '            const dec = new TextDecoder();\n'
         '            let buf = "";\n'
         '            while (true) {\n'
         '              const { done: rdone, value } = await reader.read();\n'
         '              if (rdone) break;\n'
         '              buf += dec.decode(value, { stream: true });\n'
         '              let idx;\n'
         '              while ((idx = buf.indexOf("\\n")) >= 0) {\n'
         '                const line = buf.slice(0, idx).trim();\n'
         '                buf = buf.slice(idx + 1);\n'
         '                if (!line.startsWith("data:")) continue;\n'
         '                const p = line.slice(5).trim();\n'
         '                if (p === "[DONE]") continue;\n'
         '                let j; try { j = JSON.parse(p); } catch (e) { continue; }\n'
         '                if (j.error) { controller.enqueue(_sseBytes({ t: "error", v: j.error.message || "基底流内错误" })); continue; }\n'
         '                const d = (j.choices && j.choices[0] && j.choices[0].delta) || {};\n'
         '                if (d.reasoning_content) { if (_st) _st.think += d.reasoning_content.length; controller.enqueue(_sseBytes({ t: "think", v: d.reasoning_content })); }\n'
         '                if (d.content) { if (_st) _st.out += d.content.length; controller.enqueue(_sseBytes({ t: "token", v: d.content })); }\n'
         '              }\n'
         '            }\n'
         '          } catch (e) {')
assert OLD_L in h, "找不到 chat 的读流循环"
NEW_L = OLD_L.replace(
    '            let buf = "";\n',
    '            let buf = "", outText = "";\n', 1
).replace(
    '                if (d.content) { if (_st) _st.out += d.content.length; controller.enqueue(_sseBytes({ t: "token", v: d.content })); }\n',
    '                if (d.content) { if (_st) _st.out += d.content.length; outText += d.content; controller.enqueue(_sseBytes({ t: "token", v: d.content })); }\n', 1
).replace(
    '            }\n          } catch (e) {',
    '            }\n'
    '            // 追问建议：正文已经吐完（读者已在读了），再花一次便宜档补三个「接着可以问什么」。\n'
    '            // 走 WDS_VENDORS 的快档而非满血档——这一步要快，慢了读者早就自己打字了；失败一律吞掉。\n'
    '            if (outText.length > 150) {\n'
    '              const fVC = { url: WDS_VENDORS[vd].url, model: WDS_VENDORS[vd].model };\n'
    '              const fs = await followUps(fVC, KEY, q, outText);\n'
    '              if (fs.length) controller.enqueue(_sseBytes({ t: "follow", v: fs }));\n'
    '            }\n'
    '          } catch (e) {', 1)
assert NEW_L != OLD_L, "读流循环替换没生效"
h = h.replace(OLD_L, NEW_L, 1)

assert h != orig, "什么都没改，中止"
P.write_text(h, encoding="utf-8")
print("worker patch 2 OK; delta =", len(h) - len(orig), "chars")
