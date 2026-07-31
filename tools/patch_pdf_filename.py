# -*- coding: utf-8 -*-
"""打印框的建议文件名带上时间戳（幂等）。

病：`doc()` 把同一个字符串既当封面大标题、又当 `<title>`，而 `<title>` 就是
Chrome「另存为 PDF」的建议文件名。标题固定是「与 WDS 的对话」⇒ **每导一次都撞同名**，
读者每次都被逼进"是否替换"那一步；而那一步成不成（文件被 PDF 阅读器占着、同步盘锁着…）
**网页一行都碰不到**。

修：把"封面标题"和"文件名"拆成两件事。新增 `o.file`（只进 `<title>`，不进封面），
ChatSDE 传 `ChatSDE-与WDS的对话-20260801-0713` 这样带时间戳的名字 ⇒ 天然不撞名，
也就不需要覆盖。与 Markdown 存盘（早就带 stampName）口径拉齐。
"""
import io, sys

P = "public/assets/wds-pdf.js"
h = io.open(P, encoding="utf-8").read()
orig = h
if "o.file" not in h:
    OLD = '''    var title = String(o.title || "对话记录");'''
    NEW = '''    var title = String(o.title || "对话记录");
    // ⚠️ `<title>` 就是打印框「另存为 PDF」的**建议文件名**，而封面上那行大标题是给人看的。
    //    两者共用一个字符串，等于每次导出都建议同一个名字 → 每次都撞名 → 每次都要人去点"替换"，
    //    而替换成不成功不归网页管。所以文件名单独一路，调用方可传时间戳。
    var file = String(o.file || title);'''
    assert OLD in h
    h = h.replace(OLD, NEW, 1)
    OLD2 = '''    h += "<title>" + esc(title) + "</title>";'''
    NEW2 = '''    h += "<title>" + esc(file) + "</title>";'''
    assert OLD2 in h
    h = h.replace(OLD2, NEW2, 1)
    h = h.replace('  var VERSION = 3;   // v3：版心宽按 @page 的 178mm 折算，不再问 1px 的 iframe 要',
                  '  var VERSION = 4;   // v4：文件名与封面标题分家（o.file 进 <title> ＝ 打印框的建议文件名）\n  // v3：版心宽按 @page 的 178mm 折算，不再问 1px 的 iframe 要', 1)
    io.open(P, "w", encoding="utf-8").write(h)

P2 = "public/wds-mode.js"
h2 = io.open(P2, encoding="utf-8").read()
o2 = h2
if 'file: "ChatSDE-"' not in h2:
    A = '''        title: t("convoTitle"),'''
    assert A in h2
    h2 = h2.replace(A, '''        title: t("convoTitle"),
        // 建议文件名带时间戳：每场对话各存一份，不必再去跟"是否替换同名文件"较劲
        file: "ChatSDE-" + safeName(t("convoTitle")) + "-" + stampName(),''', 1)
h2 = h2.replace('  var PDF_WANT = 3;                 // v3 起：版心宽按 @page 折算（v2：等字体、缩超宽公式）见 /assets/wds-pdf.js',
                '  var PDF_WANT = 4;                 // v4 起：建议文件名带时间戳（v3：版心宽按 @page 折算）见 /assets/wds-pdf.js', 1)
if h2 != o2:
    io.open(P2, "w", encoding="utf-8").write(h2)

if h == orig and h2 == o2:
    print("已是最新"); sys.exit(0)
print("patched")
