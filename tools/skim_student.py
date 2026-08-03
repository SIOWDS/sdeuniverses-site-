#!/usr/bin/env python3
# 读学员母文骨架：标题/副标题/摘要/各级小标题+每节首句。写配套读物前先跑它。
import sys, re, html, os
author, slug = sys.argv[1], sys.argv[2]
FIRST = int(sys.argv[3]) if len(sys.argv) > 3 else 70
p = f"public/students/{author}/{slug}/index.html"
h = open(p, encoding="utf-8", errors="replace").read()
h = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", "", h, flags=re.S)
def txt(x): return re.sub(r"\s+", "", html.unescape(re.sub(r"<[^>]+>", "", x))).strip()
for cls, lab in [("art-title", "标题"), ("art-subtitle", "副题")]:
    m = re.search(r'class="[^"]*%s[^"]*"[^>]*>(.*?)</' % cls, h, re.S)
    if m: print(lab + "：" + txt(m.group(1)))
m = re.search(r'<div[^>]*class="[^"]*abstract[^"]*"[^>]*>(.*?)</div>', h, re.S)
if not m:
    m2 = re.search(r"<h2[^>]*>\s*摘要\s*</h2>(.*?)(?=<h2|<div class=\"keywords)", h, re.S)
    m = m2
if m: print("摘要：" + txt(m.group(1))[:600])
print("---- 结构 ----")
for m in re.finditer(r"<(h2|h3)\b[^>]*>(.*?)</\1>", h, re.S):
    head = txt(m.group(2))
    if head in ("摘要", "关键词"): continue
    lvl = "  " if m.group(1) == "h3" else ""
    tail = h[m.end():m.end() + 3000]
    ps = re.findall(r"<p\b[^>]*>(.*?)</p>", tail, re.S)
    first = txt(ps[0])[:FIRST] if ps else ""
    print(f"{lvl}{head}｜{first}")
