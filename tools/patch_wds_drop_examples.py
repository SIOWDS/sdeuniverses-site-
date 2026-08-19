#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""去掉首屏那四个示例问题（用户 2026-07-31 指定）

只动"渲染"这一处，不删词条也不删容器：
  · `egs` 词条（中英各四条）留着——将来想换个形式再用，不必从头写；
  · `.wdsm-egs` 容器留着，只是不再往里塞东西（删容器要连样式、选择器、模拟一起改，
    收益为零，还多三处可能改错的地方）。
"""
P = "/home/claude/site/public/wds-mode.js"
h = open(P, encoding="utf-8").read()
orig = h


def sub1(old, new, why):
    global h
    n = h.count(old)
    assert n == 1, "锚点应恰好出现一次，实际 %d 次：%s（%s）" % (n, old[:70], why)
    h = h.replace(old, new, 1)


sub1(
    '    egsEl.innerHTML = "";\n'
    '    t("egs").forEach(function (x) { var b = el("button", "wdsm-eg", x); b.onclick = function () { inEl.value = x; send(); }; egsEl.appendChild(b); });',
    '    // 首屏不再铺示例问题（2026-07-31 用户指定去掉）。词条 egs 与容器 .wdsm-egs 都留着，\n'
    '    // 将来想换个形式再用不必从头写；这里只是不再往里塞东西。\n'
    '    egsEl.innerHTML = "";',
    "不再铺示例问题",
)

open(P, "w", encoding="utf-8").write(h)
print("wds-mode.js: %d → %d bytes（%+d）" % (len(orig), len(h), len(h) - len(orig)))

# 模拟里那条「英文示例问题已重铺」跟着改：现在该断言的是"确实不铺了"
S = "/home/claude/site/tools/sim_wds_mode_v2.js"
s = open(S, encoding="utf-8").read()
old = '  ok(layer.querySelectorAll(".wdsm-eg").length === 4, "英文示例问题已重铺");'
new = '  ok(layer.querySelectorAll(".wdsm-eg").length === 0, "首屏不铺示例问题（切语言也不会把它们铺回来），实得 " + layer.querySelectorAll(".wdsm-eg").length);'
assert s.count(old) == 1
open(S, "w", encoding="utf-8").write(s.replace(old, new, 1))
print("sim 断言已改")
