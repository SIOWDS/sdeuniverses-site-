#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""问WDS 第三批 · 补丁四（两处收尾）

① histPack 不再直接读模块作用域的 COMP，改成收一个 from 参数。
   起因：tools/sim_wds_chat_upgrade.js 是把单个函数从源码里抠出来单独 eval 的，
   函数一旦伸手去够模块作用域的变量，那种模拟当场 ReferenceError。
   顺带 histPack 变回一个纯函数（历史 + 起点 → 打包结果），本来就该是这样。

② 修一条**失效已久**的断言（不是本次改坏的，改动前就在 FAIL）：
   sim_wds_sde_tools.js 里守「满功率档 max_tokens ≤ 8000」的正则，
   在早先加入 askLen 长文档之后就再也匹配不上了，于是这条硬约束的守门人空转到今天。
   顺手把 WDS_CHAT_SYS 的签名断言更新为带 rs 的新签名。
"""
FP = "/home/claude/site/public/wds-mode.js"
TP = "/home/claude/site/tools/sim_wds_sde_tools.js"


def sub1(txt, old, new, why):
    n = txt.count(old)
    assert n == 1, "锚点应恰好出现一次，实际 %d 次：%s（%s）" % (n, old[:60], why)
    return txt.replace(old, new, 1)


# ── ① histPack 解耦 ──
h = open(FP, encoding="utf-8").read()
h = sub1(
    h,
    "  function histPack() {\n"
    "    var out = [], total = 0, i;\n"
    "    // 已经压进账本的那几轮不再上送原文（账本走 payload.comp）\n"
    "    var from = (COMP && COMP.text && COMP.upto <= history.length) ? COMP.upto : 0;\n"
    "    for (i = from; i < history.length; i++) {",
    "  // from＝从第几条开始带（已压进账本的那几轮不再上送原文，账本走 payload.comp）。\n"
    "  // 刻意收成参数而不是伸手够 COMP：这个函数会被单独抠出来做模拟，够外面的变量就跑不起来。\n"
    "  function histPack(from) {\n"
    "    var out = [], total = 0, i;\n"
    "    for (i = (from || 0); i < history.length; i++) {",
    "histPack 收参数",
)
h = sub1(
    h,
    "    var payload = { q: q, history: histPack(), umem: memRecall(q),",
    "    var payload = { q: q, history: histPack(compFrom()), umem: memRecall(q),",
    "send 传 compFrom",
)
h = sub1(
    h,
    "  function compReset() { COMP.text = \"\"; COMP.upto = 0; COMP.busy = false; COMP.turns = 0; compPaint(); }",
    "  function compReset() { COMP.text = \"\"; COMP.upto = 0; COMP.busy = false; COMP.turns = 0; compPaint(); }\n"
    "  // 账本有效时才跳过前面那几轮；账本没压出来就当没压过（绝不能因为指针动了而静默丢原文）\n"
    "  function compFrom() { return (COMP.text && COMP.upto <= history.length) ? COMP.upto : 0; }",
    "compFrom",
)
open(FP, "w", encoding="utf-8").write(h)
print("wds-mode.js 已改")

# ── ② 修断言 ──
s = open(TP, encoding="utf-8").read()
s = sub1(
    s,
    'ok(/function WDS_CHAT_SYS\\(reflect, SDEM, siteCtx, webCtx, deep, docCtx, about, lang, docNote, tool\\)/.test(W),\n'
    '   "WDS_CHAT_SYS 收 tool");',
    'ok(/function WDS_CHAT_SYS\\(reflect, SDEM, siteCtx, webCtx, deep, docCtx, about, lang, docNote, tool(?:, rs)?\\)/.test(W),\n'
    '   "WDS_CHAT_SYS 收 tool");',
    "签名断言容纳 rs",
)
s = sub1(
    s,
    'const mt = W.match(/max_tokens: deep \\? (\\d+) : \\(tool \\? (\\d+) : (\\d+)\\)/);\n'
    'ok(!!mt, "chat 的 max_tokens 三分支存在");\n'
    'ok(mt && +mt[1] <= 8000, "满功率档 ≤ 8000（这是硬约束不是可调参数），实得 " + (mt ? mt[1] : "?"));\n'
    'ok(mt && +mt[2] > +mt[3] && +mt[2] <= 12000, "工序档比闲聊宽但仍有界，实得 " + (mt ? mt[2] + " vs " + mt[3] : "?"));',
    '// 这条守的是全站最贵的那个教训：满功率档的 max_tokens 一旦调大，思考就跑过平台时长上限、\n'
    '// 被杀在思考阶段——流干净结束、正文 0 字、不报任何错。正则写死了行文形状，早先加 askLen 长文档时\n'
    '// 就已经匹配不上、空转至今；改成先揪出 tokWant 那一整段表达式，再从里面挑数字。\n'
    'const twSeg = W.slice(W.indexOf("const tokWant = askLen"), W.indexOf("const clk = wdsClock(CHAT_FIRST_MS"));\n'
    'const mt = twSeg.match(/deep \\? (\\d+) : \\(tool \\? (\\d+) : (\\d+)\\)/);\n'
    'ok(!!mt, "chat 的 max_tokens 三分支存在（深度/工序/闲聊）");\n'
    'ok(mt && +mt[1] <= 8000, "满功率档 ≤ 8000（这是硬约束不是可调参数），实得 " + (mt ? mt[1] : "?"));\n'
    'ok(mt && +mt[2] > +mt[3] && +mt[2] <= 12000, "工序档比闲聊宽但仍有界，实得 " + (mt ? mt[2] + " vs " + mt[3] : "?"));\n'
    'const bigs = (twSeg.match(/\\b(\\d{4,6})\\b/g) || []).map(Number).filter((n) => n > 8000 && n !== 32000);\n'
    'ok(bigs.length === 0, "tokWant 段里没有 8000 以上的裸预算（32000 是长文档档的天花板，另有出处），实得 " + bigs.join("/"));',
    "修满功率预算断言",
)
open(TP, "w", encoding="utf-8").write(s)
print("sim_wds_sde_tools.js 已改")
