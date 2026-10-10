#!/usr/bin/env python3
"""每本专著自己的智能体：生成 /books/m/N/agent/ 页、/books/agent/ 名录，并把详情页入口换成书自己的名字。

2026-10-03 王德生令：不是一个「书生」智能体，而是每本书一个独特名字的智能体，带它自己提前打造的碰撞库
（RAG，见 tools/build_book_rag.py）——出版的价值就此典范转移。

数据：
  public/books/agents.json      每本书的名字、称号、自我介绍、四道门的开门问题（名字全站唯一，起名在这里改）
  public/books/m/N/rag.json     这本书的专属碰撞库（build_book_rag.py 生成）
共用程序：public/books/agent/app.js + app.css（一套代码，人格与碰撞库按书各自加载）

新书上站：在 agents.json 里给它起名 → 跑 build_book_rag.py N → 跑本脚本（build_bookshelf.py 会自动调用本脚本）。
没起名的书会在输出里点名提醒，暂用「书生」兜底。
用法：python3 tools/build_book_agents.py
"""
import html, io, json, os, re
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, "public")
V = "20261003d"
BODY = io.open(os.path.join(ROOT, "tools", "book_agent_body.html"), encoding="utf-8").read()
cat = json.load(io.open(os.path.join(PUB, "books", "catalog.json"), encoding="utf-8"))
reg = json.load(io.open(os.path.join(PUB, "books", "agents.json"), encoding="utf-8"))["agents"]
CATS = cat["categories"]
esc = lambda s: html.escape(str(s or ""), quote=True)


def has_text(b):
    n = b.get("number")
    return n and (b.get("textUrl") or b.get("chapterUrl") or os.path.exists(os.path.join(PUB, "books", "m", str(n), "text", "index.html")))


books = [b for b in cat["books"] if has_text(b) and os.path.exists(os.path.join(PUB, "books", "m", str(b["number"]), "index.html"))]
unnamed, made = [], 0
for b in books:
    n = b["number"]
    a = reg.get(str(n))
    if not a:
        unnamed.append(n)
        a = {"name": "书生", "epithet": "这本书的智能体", "intro": ""}
    rag = os.path.exists(os.path.join(PUB, "books", "m", str(n), "rag.json"))
    desc = a.get("intro") or ("《%s》的智能体：读懂、用上、拆开、对撞、写出。" % b["title"])
    page = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>%(name)s · 《%(title)s》的智能体 | 德麦国际专著第 %(n)s 号</title>
<meta name="description" content="%(desc)s">
<meta name="sde-page-kind" content="tool">
<meta name="book-agent" content="%(name)s"><meta name="book_no" content="%(n)s">
<link rel="canonical" href="https://sdeuniverses.com/books/m/%(n)s/agent/">
<meta property="og:title" content="%(name)s · 《%(title)s》的智能体">
<meta property="og:description" content="%(desc)s">
%(og)s<link rel="stylesheet" href="/books/agent/app.css?v=%(v)s">
</head>
<body>
%(body)s<script>window.BOOK_AGENT={no:%(n)s};</script>
<script src="/books/agent/app.js?v=%(v)s" defer></script>
</body></html>
""" % {"name": esc(a["name"]), "title": esc(b["title"]), "n": n, "desc": esc(desc), "v": V, "body": BODY,
       "og": ('<meta property="og:image" content="%s">\n' % esc(b["coverUrl"])) if b.get("coverUrl") else ""}
    d = os.path.join(PUB, "books", "m", str(n), "agent")
    os.makedirs(d, exist_ok=True)
    agent_path = os.path.join(d, "index.html")
    if n == 265 and os.path.exists(agent_path) and '<meta name="sde-dedicated-agent" content="m265-unit-v1">' in io.open(agent_path, encoding="utf-8").read():
        made += 1
        continue  # preserve volume 265's 42-unit source loader and evidence contract
    if n == 271 and os.path.exists(agent_path) and '<meta name="sde-dedicated-agent" content="m271-unit-v1">' in io.open(agent_path, encoding="utf-8").read():
        made += 1
        continue  # preserve this edition's 51-unit source loader; the directory still lists book 271
    io.open(agent_path, "w", encoding="utf-8").write(page)
    made += 1

# —— 名录 /books/agent/ ——（带 ?m=N 的旧链接跳到那本书自己的智能体页）
groups = defaultdict(list)
for b in books:
    groups[b.get("category", "")].append(b)
cards = ""
for k, label in CATS.items():
    bs = sorted(groups.get(k, []), key=lambda x: -x["number"])
    if not bs:
        continue
    cards += '<section><h2>%s<span>%d</span></h2><div class="g">' % (esc(label), len(bs))
    for b in bs:
        a = reg.get(str(b["number"]), {"name": "书生", "epithet": "这本书的智能体"})
        cards += ('<a class="c" href="/books/m/%d/agent/"><b>%s</b><i>%s</i><span>《%s》 · 第 %d 号</span></a>'
                  % (b["number"], esc(a["name"]), esc(a.get("epithet", "")), esc(b["title"]), b["number"]))
    cards += "</div></section>"
idx = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>专著智能体名录 · 每本书一个名字 | 德麦国际</title>
<meta name="description" content="德麦国际的每一本专著都有一个自己名字的智能体，带着为它提前打造的碰撞库：读懂、用上、拆开、对撞、写出。">
<link rel="canonical" href="https://sdeuniverses.com/books/agent/">
<script>(function(){var m=new URLSearchParams(location.search).get("m");if(m&&/^\\d+$/.test(m))location.replace("/books/m/"+m+"/agent/");})();</script>
<style>
:root{--bg:#0B0E12;--bg2:#11161B;--fg:#E6E4DE;--dim:#8C949C;--gold:#D9A441;--line:#232A31}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font-family:"PingFang SC","Microsoft YaHei","Noto Sans CJK SC",sans-serif}
a{color:var(--gold);text-decoration:none}
.w{max-width:1180px;margin:0 auto;padding:28px 16px 60px}
.cr{font-size:12.5px;color:var(--dim)}.cr a{color:var(--dim)}
h1{font-family:"Noto Serif CJK SC","Songti SC",serif;font-size:30px;margin:18px 0 8px;letter-spacing:.04em}
.lead{color:#CFCBC2;line-height:1.9;max-width:760px;font-size:15px;margin:0 0 6px}
.n{color:var(--dim);font-size:13px;margin-bottom:22px}
h2{font-size:15px;color:var(--gold);letter-spacing:.1em;margin:30px 0 10px;font-weight:600}
h2 span{color:var(--dim);font-weight:400;margin-left:8px;font-size:12.5px}
.g{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px}
.c{display:flex;flex-direction:column;gap:3px;background:var(--bg2);border:1px solid var(--line);border-radius:10px;padding:12px 14px;color:var(--fg)}
.c:hover{border-color:var(--gold)}
.c b{font-family:"Noto Serif CJK SC","Songti SC",serif;font-size:21px;color:var(--gold);letter-spacing:.12em;font-weight:600}
.c i{font-style:normal;font-size:12.5px;color:#CFCBC2}
.c span{font-size:12px;color:var(--dim);line-height:1.6}
</style></head><body><div class="w">
<div class="cr"><a href="/browse/">SDE Universes</a> · <a href="/books/">专著书架</a> · 专著智能体名录</div>
<h1>每本书，一个名字</h1>
<p class="lead">德麦国际的每一本专著，都有一个从它自己身上长出来的智能体。它逐字读过这本书，带着一套为这本书提前打造的碰撞库——从站上其他专著与文章里检索出来、与本书各章最相撞的段落——陪你读懂它、用上它、拆开它、拿它去对撞，再把碰出来的新思想写成论文，甚至一部新专著。</p>
<div class="n">共 %(cnt)d 位 · 名字取自各书的核心意象，全站唯一</div>
%(cards)s
</div></body></html>
""" % {"cnt": len(books), "cards": cards}
io.open(os.path.join(PUB, "books", "agent", "index.html"), "w", encoding="utf-8").write(idx)
print("已生成 %d 本书的智能体页；名录 1 页" % made + ("；未起名（暂用「书生」）：%s" % unnamed if unnamed else ""))
