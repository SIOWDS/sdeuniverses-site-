#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""问WDS 第三批 · 附件模块补丁（public/assets/wds-attach.js）

图片原来一律先跑本机 OCR 再当文字附件。OCR 给的是"这张图印了什么字"，
给不出"这张图长什么样"——图表的形状、版式、手写、白板上的箭头，一个都留不下。
改成：图片直接留 data URL 交给视觉档；OCR 降级成**按需退路**（当前基底看不了图时才点）。
副作用是快了很多：贴一张图不用再等十几秒 OCR。
"""
P = "/home/claude/site/public/assets/wds-attach.js"
h = open(P, encoding="utf-8").read()
orig = h


def sub1(old, new, why):
    global h
    n = h.count(old)
    assert n == 1, "锚点应恰好出现一次，实际 %d 次：%s（%s）" % (n, old[:60], why)
    h = h.replace(old, new, 1)


sub1(
    "  function ocrImage(file, prog) {",
    "  // 图片读成 data URL：这串会原样发给视觉档（本站不留存、也不经过本站）\n"
    "  function readDataURL(file) {\n"
    "    return new Promise(function (res, rej) {\n"
    "      var r = new FileReader();\n"
    "      r.onload = function () { res(String(r.result || \"\")); };\n"
    "      r.onerror = function () { rej(new Error(\"图片读不出来\")); };\n"
    "      r.readAsDataURL(file);\n"
    "    });\n"
    "  }\n"
    "  // 按需 OCR：传 data URL 即可（tesseract 认这个），用在\"这家基底看不了图\"的退路上\n"
    "  function ocrDataUrl(d) {\n"
    "    return needTess().then(function (T) {\n"
    "      return T.recognize(d, \"chi_sim+eng\").then(function (r) { return ((r && r.data && r.data.text) || \"\").trim(); });\n"
    "    });\n"
    "  }\n"
    "  function ocrImage(file, prog) {",
    "data URL 与按需 OCR",
)

sub1(
    "    else if (/\\.(png|jpe?g|webp|bmp|gif)$/.test(low)) P = ocrImage(file, prog).then(function (t) { return { text: t, note: \"图片 · 本机 OCR\" }; });",
    "    else if (/\\.(png|jpe?g|webp|bmp|gif)$/.test(low)) P = readDataURL(file).then(function (d) { return { text: \"\", note: \"图片\", img: d }; });",
    "图片改走 data URL",
)

sub1(
    "    return P.then(function (r) {\n"
    "      var t = clean(r.text);\n"
    "      if (!t) throw new Error(\"这个文件里没读出文字\");",
    "    return P.then(function (r) {\n"
    "      var t = clean(r.text);\n"
    "      // 图片没有文字是正常的（它本来就不是拿来读字的），不能按\"读不出文字\"退回\n"
    "      if (r.img) return { name: name, text: t, note: r.note || \"图片\", img: r.img };\n"
    "      if (!t) throw new Error(\"这个文件里没读出文字\");",
    "图片不按空文本退回",
)

sub1(
    "  var API = { pick: pick, parseFile: parseFile, MAX_CHARS: MAX_CHARS, chunk: chunk, selectChunks: selectChunks };",
    "  var API = { pick: pick, parseFile: parseFile, MAX_CHARS: MAX_CHARS, chunk: chunk, selectChunks: selectChunks, ocrDataUrl: ocrDataUrl };",
    "导出 ocrDataUrl",
)

sub1(
    '    inp.accept = ".txt,.md,.markdown,.csv,.json,.log,.docx,.pdf,.png,.jpg,.jpeg,.webp,.bmp";',
    '    inp.accept = ".txt,.md,.markdown,.csv,.json,.log,.docx,.pdf,.png,.jpg,.jpeg,.webp,.bmp,.gif";',
    "选择框接受 gif",
)

open(P, "w", encoding="utf-8").write(h)
print("wds-attach.js: %d → %d bytes（+%d）" % (len(orig), len(h), len(h) - len(orig)))
