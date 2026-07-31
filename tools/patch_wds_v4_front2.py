#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""问WDS 第三批 · 前端补丁二

补两个漏：
① 画布关掉之后没有再打开的入口——顶栏加一个「⧉ 画布」开关（带条数徽标）。
② 研究报告写完只落在卡片里，没有复制/下载/落画布的手——补一行操作按钮。
   （刻意不调 mountActs：那条线会 autoLink 整个 cell.a，会把研究卡的事件绑定洗掉。）
"""
P = "/home/claude/site/public/wds-mode.js"
h = open(P, encoding="utf-8").read()
orig = h


def sub1(old, new, why):
    global h
    n = h.count(old)
    assert n == 1, "锚点应恰好出现一次，实际 %d 次：%s（%s）" % (n, old[:60], why)
    h = h.replace(old, new, 1)


sub1(
    "\"<button class='wdsm-tbtn wdsm-distbtn'></button>\" +",
    "\"<button class='wdsm-tbtn wdsm-cvbtn'></button>\" +\n"
    "        \"<button class='wdsm-tbtn wdsm-distbtn'></button>\" +",
    "顶栏画布按钮",
)

sub1(
    "  (function () {\n"
    "    var x = cvEl && cvEl.querySelector(\".wdsm-cvx\");\n"
    "    if (x) { x.title = tx(\"cvClose\"); x.onclick = function () { cvShow(false); }; }\n"
    "  })();",
    "  var cvBtn = layer.querySelector(\".wdsm-cvbtn\");\n"
    "  (function () {\n"
    "    var x = cvEl && cvEl.querySelector(\".wdsm-cvx\");\n"
    "    if (x) { x.title = tx(\"cvClose\"); x.onclick = function () { cvShow(false); }; }\n"
    "    if (cvBtn) cvBtn.onclick = function () { cvShow(!layer.classList.contains(\"cvon\")); cvPaint(); };\n"
    "  })();",
    "画布开关接线",
)

# 画布按钮的文案与条数：cvPaint 每次重绘都刷（applyLang 也会调它）
sub1(
    "  function cvPaint() {\n    if (!cvEl) return;",
    "  function cvPaint() {\n"
    "    if (cvBtn) {\n"
    "      cvBtn.textContent = tx(\"cvOpen\") + (CV.items.length ? \" \" + CV.items.length : \"\");\n"
    "      cvBtn.style.display = CV.items.length ? \"\" : \"none\";   // 没东西时不占地方\n"
    "    }\n"
    "    if (!cvEl) return;",
    "画布按钮刷新",
)

# 研究报告底部操作行
sub1(
    "          cvAdd(\"md\", title, md);                       // 报告落画布：它是成品，不该只活在聊天流里\n"
    "          endRs(md);",
    "          cvAdd(\"md\", title, md);                       // 报告落画布：它是成品，不该只活在聊天流里\n"
    "          var row = el(\"div\", \"wdsm-acts\");\n"
    "          var c1 = el(\"button\", \"wdsm-act\", t(\"aCopy\"));\n"
    "          c1.onclick = function () { copyText(plainOf(md)); c1.textContent = t(\"aCopied\"); };\n"
    "          var c2 = el(\"button\", \"wdsm-act\", tx(\"cvDrop\"));\n"
    "          c2.onclick = function () { cvAdd(\"md\", title, md); };\n"
    "          var c3 = el(\"button\", \"wdsm-act\", \"\\u2913 .md\");\n"
    "          c3.onclick = function () { download(safeName(title) + \".md\", md); };\n"
    "          row.appendChild(c1); row.appendChild(c2); row.appendChild(c3);\n"
    "          card.appendChild(row);\n"
    "          endRs(md);",
    "研究报告操作行",
)

open(P, "w", encoding="utf-8").write(h)
print("wds-mode.js: %d → %d bytes（+%d）" % (len(orig), len(h), len(h) - len(orig)))
