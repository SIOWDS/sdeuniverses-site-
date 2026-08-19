#!/usr/bin/env python3
# 读母文骨架：标题/副标题/摘要/各级小标题+每节首句。给伴读文写作用。
import sys, re, html, os
slug = sys.argv[1]
base = sys.argv[2].strip("/") if len(sys.argv) > 2 else "column"
p = f"public/{base}/{slug}/index.html"
h = open(p, encoding="utf-8", errors="replace").read()
h = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", "", h, flags=re.S)
def txt(x): return html.unescape(re.sub(r"<[^>]+>", "", x)).strip()
t = re.search(r"<title>(.*?)</title>", h, re.S)
print("TITLE:", txt(t.group(1)) if t else "")
for cls in ["art-eyebrow", "eyebrow", "art-subtitle", "art-sub", "art-meta", "meta"]:
    m = re.search(r'class="[^"]*%s[^"]*"[^>]*>(.*?)</' % cls, h, re.S)
    if m: print(cls.upper() + ":", txt(m.group(1))[:200])
m = re.search(r'class="(abs|abstract|abstract-box|absbox)[^"]*"[^>]*>(.*?)</div>', h, re.S)
if m: print("ABSTRACT:", txt(m.group(2))[:700])
print("---- 结构 ----")
for m in re.finditer(r"<(h2|h3)\b[^>]*>(.*?)</\1>", h, re.S):
    lvl = "  " if m.group(1) == "h3" else ""
    head = txt(m.group(2))
    tail = h[m.end():m.end()+2200]
    ps = re.findall(r"<p\b[^>]*>(.*?)</p>", tail, re.S)
    first = txt(ps[0])[:160] if ps else ""
    print(f"{lvl}{m.group(1)} {head}\n{lvl}    · {first}")
