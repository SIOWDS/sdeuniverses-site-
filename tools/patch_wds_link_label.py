#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修：模式条上的 🔗 链接键是个没名字的空框

病因：文案 `lnkBtn` 在词典里写了，`title` 也设了，**但从来没有一处把它写进 textContent**。
研究键有 rsPaint、并排键有 duPaint、工序键有 paintTool，唯独链接键漏了一个 paint。
于是它渲染成一颗空的椭圆，读者只看见"一个没有名字的框"。

顺手加一条通用守门断言（这次真正的教训）：**模式条上每一颗按钮都必须有字**。
逐颗写断言是补不完的——下次再加一颗按钮，同样会漏。
"""
P = "/home/claude/site/public/wds-mode.js"
S = "/home/claude/site/tools/sim_wds_mode_v2.js"


def sub1(txt, old, new, why):
    n = txt.count(old)
    assert n == 1, "锚点应恰好出现一次，实际 %d 次：%s（%s）" % (n, old[:70], why)
    return txt.replace(old, new, 1)


h = open(P, encoding="utf-8").read()
o0 = len(h)

# ── 给链接键一个 paint，和别的按钮一样 ──
h = sub1(
    h,
    '  if (lnkBtn) {\n'
    '    lnkBtn.title = t("lnkTip");\n'
    '    lnkBtn.onclick = function () {',
    '  function lnkPaint() {\n'
    '    if (!lnkBtn) return;\n'
    '    lnkBtn.textContent = t("lnkBtn");     // 漏了这一行，它就是一颗没名字的空框\n'
    '    lnkBtn.title = t("lnkTip");\n'
    '  }\n'
    '  lnkPaint();\n'
    '  if (lnkBtn) {\n'
    '    lnkBtn.onclick = function () {',
    "lnkPaint",
)
# 切语言时跟着刷（与 rsPaint/duPaint 同排）
h = sub1(
    h,
    '    try { rsPaint(); cvPaint(); compPaint(); duPaint(); pjPaint(); } catch (e) {}',
    '    try { rsPaint(); lnkPaint(); cvPaint(); compPaint(); duPaint(); pjPaint(); } catch (e) {}',
    "切语言刷链接键",
)
open(P, "w", encoding="utf-8").write(h)
print("wds-mode.js: %d → %d bytes（%+d）" % (o0, len(h), len(h) - o0))

# ── 通用守门断言：模式条上不许有没名字的按钮 ──
s = open(S, encoding="utf-8").read()
s = sub1(
    s,
    'ok(!!layer.querySelector(".wdsm-attbtn"), "附件按钮存在（借 .wdsm-mode 样式但无 data-k，不参与档位互斥）");',
    'ok(!!layer.querySelector(".wdsm-attbtn"), "附件按钮存在（借 .wdsm-mode 样式但无 data-k，不参与档位互斥）");\n'
    '// 通用守门：模式条上**每一颗按钮都必须有字**。\n'
    '// 逐颗写断言是补不完的——链接键当初就是这么漏成一颗空框的（文案定义了，没人写进 DOM）。\n'
    '{\n'
    '  const blank = layer.querySelectorAll(".wdsm-mode").filter((b) => !String(b.textContent || "").trim());\n'
    '  ok(blank.length === 0, "模式条上没有没名字的按钮，实得空按钮 " + blank.length + " 颗（className：" + blank.map((b) => b.className).join(" / ") + "）");\n'
    '}',
    "通用空按钮断言",
)
open(S, "w", encoding="utf-8").write(s)
print("sim 已加通用断言")
