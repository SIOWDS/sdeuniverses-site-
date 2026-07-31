#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修：画布找不到入口

原写法是「画布上没东西时就把顶栏那颗按钮藏起来，不占地方」。
听着体贴，实际是**把一个新功能藏成了不存在**——读者打开页面，顶栏没有画布、
右边也没有画布，只有当某一条回答恰好吐出一个围栏块时它才自己冒出来。
读者当然会说「好像看不见画布」。

改法：按钮常驻（有东西时后面缀个数字），点开就是空态说明——
空态本身要能告诉人「什么东西会落到这儿、怎么手动放一件进来」。
一个功能的入口不该由它自己有没有内容来决定显不显示。
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
    '    if (cvBtn) {\n'
    '      cvBtn.textContent = tx("cvOpen") + (CV.items.length ? " " + CV.items.length : "");\n'
    '      cvBtn.style.display = CV.items.length ? "" : "none";   // 没东西时不占地方\n'
    '    }',
    '    if (cvBtn) {\n'
    '      // 常驻。**不要**在画布为空时把它藏起来——那等于把功能藏成不存在，\n'
    '      // 读者永远等不到"它自己冒出来"的那一刻，只会以为没有这个东西。\n'
    '      cvBtn.textContent = tx("cvOpen") + (CV.items.length ? " " + CV.items.length : "");\n'
    '      cvBtn.title = tx("cvTip");\n'
    '      if (layer.classList.contains("cvon")) cvBtn.classList.add("on"); else cvBtn.classList.remove("on");\n'
    '    }',
    "画布按钮常驻",
)

# 空态说明写得更能照着做（读者是在"我点开了但里面什么都没有"的处境里读它）
sub1(
    'cvEmpty: "还没有东西落到画布。长产出（报告、图、网页、评分卡）会自动落这儿，也可以在任一条回答下点「⧉ 落到画布」。",',
    '      cvEmpty: "画布还是空的。会自动落到这儿的是：结构图（/结构图）、深度研究的报告、以及回答里成块的图/网页/表格/长文稿。\\n\\n想手动放一件进来：在任意一条回答下面点「⧉ 落到画布」。\\n\\n落进来之后可以切版本、预览、下载、存到本机，也可以选中其中一段让 WDS 就地改。",\n'
    '      cvTip: "画布：放长产出与图，可切版本、就地改",',
    "空态说明（中）",
)
sub1(
    'cvEmpty: "Nothing on the canvas yet. Long outputs (reports, diagrams, pages, score cards) land here automatically — or hit ⧉ under any answer.",',
    '      cvEmpty: "The canvas is empty. What lands here automatically: structure maps (/map), deep-research reports, and any diagram, page, table or long draft that comes back as a block.\\n\\nTo put something here by hand: hit \u201c⧉ To canvas\u201d under any answer.\\n\\nOnce here you can switch versions, preview, download, save locally, or select a passage and have WDS revise it in place.",\n'
    '      cvTip: "Canvas: long outputs and diagrams — versions, in-place revision",',
    "空态说明（英）",
)
# 空态是多行的，得让它按行显示
sub1(
    '    if (!it) { cvWrapEl.appendChild(el("div", "wdsm-cvempty", tx("cvEmpty"))); return; }',
    '    if (!it) {\n'
    '      var em = el("div", "wdsm-cvempty");\n'
    '      tx("cvEmpty").split("\\n\\n").forEach(function (p) { em.appendChild(el("p", null, p)); });\n'
    '      cvWrapEl.appendChild(em);\n'
    '      return;\n'
    '    }',
    "空态分段",
)

# 启动时画一次：按钮的文案与状态不该等到第一件成品出现才有
sub1(
    '    if (cvBtn) cvBtn.onclick = function () { cvShow(!layer.classList.contains("cvon")); cvPaint(); };',
    '    if (cvBtn) cvBtn.onclick = function () { cvShow(!layer.classList.contains("cvon")); cvPaint(); };\n'
    '    cvPaint();',
    "启动即画一次",
)

open(P, "w", encoding="utf-8").write(h)
print("wds-mode.js: %d → %d bytes（+%d）" % (len(orig), len(h), len(h) - len(orig)))
