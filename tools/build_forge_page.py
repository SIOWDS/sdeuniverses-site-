#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建 /taste/paradigm-forge/index.html。

页面骨架在 tools/forge/forge.template.html，多厂商基底引擎（API_URLS→buildPayload、
streamChat/callOverseas、Markdown→docx 三件套）从金点子发生器整块取来注入——
一处维护，两页同步。改了发生器的引擎，重跑本脚本即可。

用法：python3 tools/build_forge_page.py
"""
import datetime
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "public", "taste", "idea-generator", "index.html")
TPL = os.path.join(ROOT, "tools", "forge", "forge.template.html")
OUT = os.path.join(ROOT, "public", "taste", "paradigm-forge", "index.html")


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
                      ("@BUILDTAG@", tag + "·v1")]:
        assert mark in t, "模板里少了占位符 " + mark
        t = t.replace(mark, val, 1)

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
