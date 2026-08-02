#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建 /taste/confluence/index.html。

页面骨架在 tools/confluence/confluence.template.html，多厂商基底引擎（API_URLS→buildPayload、
streamChat/callOverseas、Markdown→docx 三件套）从金点子发生器整块取来注入——
一处维护，两页同步。改了发生器的引擎，重跑本脚本即可。

用法：python3 tools/build_confluence_page.py
"""
import datetime
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "public", "taste", "idea-generator", "index.html")
TPL = os.path.join(ROOT, "tools", "confluence", "confluence.template.html")
OUT = os.path.join(ROOT, "public", "taste", "confluence", "index.html")


def slice_between(h, start_mark, end_mark, name):
    i = h.find(start_mark)
    assert i >= 0, "找不到起点：" + name
    j = h.find(end_mark, i + len(start_mark))
    assert j > i, "找不到终点：" + name
    return h[i:j].rstrip() + "\n"


def main():
    h = open(SRC, encoding="utf-8").read()

    vendors = slice_between(h, "// 多厂商 API 地址", "// 示例问题", "vendors")
    stream = slice_between(h, "async function streamChat",
                           "// 主流程：两边并行", "stream")
    md = slice_between(h, "function mdInlineTokens",
                       "// —— Markdown 文本 → HTML", "md")

    i = h.find('id="modelSel"')
    a = h.rfind("<select", 0, i)
    b = h.find("</select>", i)
    assert a > 0 and b > a, "找不到基底选择器"
    modelsel = h[a:b + 9]

    # 注入的块必须自带这些标识，缺了说明上游改了名字，宁可炸也别静默产出半截页面
    for needle, blk, nm in [
        ("const API_URLS", vendors, "vendors"),
        ("function buildPayload", vendors, "vendors"),
        ("async function callOverseas", stream, "stream"),
        ("function mdParas", md, "md"),
        ('value="ds:pro"', modelsel, "modelsel"),
    ]:
        assert needle in blk, "注入块 %s 里少了 %s——上游改了写法，先核对再构建" % (nm, needle)

    t = open(TPL, encoding="utf-8").read()
    tag = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    for mark, val in [("/*@VENDORS@*/", vendors), ("/*@STREAM@*/", stream),
                      ("/*@MD@*/", md), ("<!--@MODELSEL@-->", modelsel),
                      ("@BUILDTAG@", tag + "·通融v1")]:
        assert mark in t, "模板里少了占位符 " + mark
        t = t.replace(mark, val, 1)

    # 外借代码的依赖自检：抄来的块里调用、而页面又没定义的函数 —— 踩过 escTxt 那一次
    borrowed = vendors + "\n" + stream + "\n" + md
    # 先剥注释与字符串，否则 CSS 里的 rgba( 、提示语里的 tokens( 会被当成函数调用
    code = re.sub(r"/\*.*?\*/", " ", borrowed, flags=re.S)
    code = re.sub(r"//[^\n]*", " ", code)
    code = re.sub(r"'(?:\\.|[^'\\])*'", "''", code)
    code = re.sub(r'"(?:\\.|[^"\\])*"', '""', code)
    code = re.sub(r"`(?:\\.|[^`\\])*`", "``", code)
    # 正则字面量也要剥（/__([^_]+)__/ 里的 __ 会被当成函数名）
    code = re.sub(r"(?<![\w)\]])/(?:\\.|\[[^\]]*\]|[^/\\\n])+/[gimsuy]*", " RE ", code)
    called = set(re.findall(r"(?<![.\w$])([A-Za-z_$][\w$]*)\s*\(", code))
    defined = set(re.findall(r"function\s+([A-Za-z_$][\w$]*)\s*\(", t)) \
        | set(re.findall(r"(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=", t))
    for grp in re.findall(r"(?:const|let|var)\s*\{([^}]*)\}\s*=", t):   # 解构出来的（docx 那几个）
        defined |= {x.strip().split(':')[-1].strip() for x in grp.split(',') if x.strip()}
    builtin = {
        "if", "for", "while", "switch", "catch", "return", "typeof", "function", "new",
        "String", "Number", "Boolean", "Object", "Array", "Math", "JSON", "Date", "Promise",
        "Error", "RegExp", "Set", "Map", "parseInt", "parseFloat", "isNaN", "fetch", "atob",
        "setTimeout", "setInterval", "clearTimeout", "clearInterval", "encodeURIComponent",
        "decodeURIComponent", "TextDecoder", "TextEncoder", "AbortController", "Blob", "URL",
        "requestAnimationFrame", "structuredClone", "queueMicrotask",
    }
    missing = sorted(x for x in called if x not in defined and x not in builtin)
    assert not missing, ("抄来的引擎块用到了页面没定义的函数：%s —— 把它们一并抄过来，"
                         "否则只在少见分支（如空响应）才炸" % ", ".join(missing))

    # 标签配对自检（div/script/style/select 开闭数一致）
    for tagname in ["div", "script", "style", "select", "textarea"]:
        o = len(re.findall(r"<%s[\s>]" % tagname, t))
        c = len(re.findall(r"</%s>" % tagname, t))
        assert o == c, "标签不配对：%s 开 %d 闭 %d" % (tagname, o, c)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(t)
    print("built:", os.path.relpath(OUT, ROOT), len(t), "字符  build tag", tag)
    return 0


if __name__ == "__main__":
    sys.exit(main())
