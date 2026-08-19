# -*- coding: utf-8 -*-
"""把「导出为 PDF」从「✎ 成文 · PPT」下拉里搬到顶栏，变成一个独立按钮。

用户的话：「应该放在成文的外面，就是输出PDF，即将整个对话内容打印为PDF就行。」
——它跟成文不是一回事：成文要调基底重新锻一篇，PDF 只是把眼前这场对话原样印出来，
零调用、零等待。埋在「成文 · PPT」下拉里既不好找，也把它说成了成文的一个子功能。

幂等。
"""
import io, sys

P = "public/wds-mode.js"
h = io.open(P, encoding="utf-8").read()
if "wdsm-pdfbtn'" in h:
    print("already patched"); sys.exit(0)

def rep(old, new, what):
    global h
    assert h.count(old) == 1, "锚点不唯一/找不到：" + what + " (count=%d)" % h.count(old)
    h = h.replace(old, new)

# ── 1. 从下拉菜单里撤掉 ──
rep("""    var pf = el("button", "wdsm-pdfbtn-installed");
    pf.appendChild(document.createTextNode(t("mPdf")));
    pf.appendChild(el("span", "sub", t("mPdfS")));
    pf.onclick = function () { if (menu.parentNode) menu.parentNode.removeChild(menu); exportPdf(); };
    menu.appendChild(pf);
""", "", "撤掉菜单项")

# ── 2. 顶栏加按钮（紧挨成文，导出这一族在一处）──
rep('''        "<button class='wdsm-tbtn wdsm-distbtn'></button>" +\n''',
    '''        "<button class='wdsm-tbtn wdsm-distbtn'></button>" +\n'''
    '''        "<button class='wdsm-tbtn wdsm-pdfbtn'></button>" +\n''',
    "顶栏按钮")

# ── 3. 文案：菜单项那两条改成顶栏那两条 ──
rep('      mPdf: "\\u2913 导出为 PDF", mPdfS: "排成印刷稿，在打印框里选「另存为 PDF」",\n',
    '      bPdf: "\\u2913 PDF", bPdfT: "把整场对话排成印刷稿并打印——在打印框里把「目标」选成「另存为 PDF」，即可存成文件",\n',
    "zh 文案")
rep('      mPdf: "\\u2913 Export as PDF", mPdfS: "Typeset for print — pick \\u201cSave as PDF\\u201d in the print dialog",\n',
    '      bPdf: "\\u2913 PDF", bPdfT: "Typeset this whole chat for print \\u2014 set Destination to \\u201cSave as PDF\\u201d in the dialog to keep the file",\n',
    "en 文案")

# ── 4. 语言刷新时贴文字与 title ──
rep('    q(".wdsm-distbtn").textContent = t("bDistill");\n',
    '    q(".wdsm-distbtn").textContent = t("bDistill");\n'
    '    try { var pb = q(".wdsm-pdfbtn"); pb.textContent = t("bPdf"); pb.title = t("bPdfT"); } catch (e) {}\n',
    "applyLang")

# ── 5. 绑事件（挨着成文按钮那一处）──
rep("  layer.querySelector(\".wdsm-distbtn\").onclick = function (ev) {\n",
    "  try { layer.querySelector(\".wdsm-pdfbtn\").onclick = function () { exportPdf(); }; } catch (e) {}\n"
    "  layer.querySelector(\".wdsm-distbtn\").onclick = function (ev) {\n",
    "绑事件")

io.open(P, "wb").write(h.encode("utf-8"))
print("patched", P)
