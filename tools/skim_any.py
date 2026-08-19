#!/usr/bin/env python3
# 读母文骨架：标题/摘要/关键词/各级小标题(+可选每节首句)。给配套读物写作用。
# 用法: python3 tools/skim_any.py <base> <slug> [--full]
#   base 例: column | students/zhang-qiong
import sys, re, html, os

base, slug = sys.argv[1].strip("/"), sys.argv[2]
full = "--full" in sys.argv
p = os.path.join("public", *base.split("/"), slug, "index.html")
h = open(p, encoding="utf-8", errors="replace").read()
h = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", "", h, flags=re.S)


def txt(x):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", x))).strip()


m = re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S)
print("== TITLE:", txt(m.group(1)) if m else slug)
for cls in ["art-subtitle", "art-sub", "sub", "lead"]:
    m = re.search(r'class="[^"]*%s[^"]*"[^>]*>(.*?)</' % cls, h, re.S)
    if m and txt(m.group(1)):
        print("SUB:", txt(m.group(1))[:220]); break
m = re.search(r'class="(?:abs|abstract|absbox|deck)[^"]*"[^>]*>(.*?)</div>', h, re.S)
if m:
    print("ABS:", txt(m.group(1))[:900])
m = re.search(r'class="(?:kw|keywords)"[^>]*>(.*?)</', h, re.S)
if m:
    print("KW:", txt(m.group(1))[:200])
print("---- 结构 ----")
for m in re.finditer(r"<(h2|h3)\b[^>]*>(.*?)</\1>", h, re.S):
    lvl = "   " if m.group(1) == "h3" else ""
    print(f"{lvl}{txt(m.group(2))}")
    if full:
        ps = re.findall(r"<p\b[^>]*>(.*?)</p>", h[m.end():m.end() + 2500], re.S)
        if ps:
            print(f"{lvl}   · {txt(ps[0])[:150]}")
