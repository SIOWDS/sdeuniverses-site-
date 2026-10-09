#!/usr/bin/env python3
"""为每本专著生成 public/books/m/N/unit.json —— 三位一体出版单元的身份与组件清单。
只记录事实：有没有 学习包(learn.json)、有没有智能体页、有没有原文；不声称学习效果。"""
import io, json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, "public")
cat = json.load(io.open(os.path.join(PUB, "books", "catalog.json"), encoding="utf-8"))
ags = json.load(io.open(os.path.join(PUB, "books", "agents.json"), encoding="utf-8"))["agents"]
n_all = n_full = 0
for b in cat["books"]:
    n = b.get("number")
    if not n: continue
    d = os.path.join(PUB, "books", "m", str(n))
    if not os.path.isdir(d): continue
    has = lambda *p: os.path.exists(os.path.join(d, *p))
    learn = None
    if has("learn.json"):
        L = json.load(io.open(os.path.join(d, "learn.json"), encoding="utf-8"))
        learn = {"url": "/books/learn/?b=%d" % n, "dataUrl": "/books/m/%d/learn.json" % n, "problems": len(L.get("problems", []))}
    reading = {"url": b.get("readUrl") or b.get("textUrl") or ("/books/m/%d/text/" % n)} if (has("text", "index.html") or has("read.html")) else None
    agent = {"url": "/books/m/%d/agent/" % n, "name": (ags.get(str(n)) or ags.get(n) or {}).get("name", "书生")} if has("agent", "index.html") else None
    u = {"schemaVersion": "1.0", "unitId": "m%d" % n, "volumeNumber": n, "title": b.get("title"), "authors": b.get("authors", []),
         "components": {"reading": reading, "learning": learn, "dialogue": agent},
         "complete": bool(reading and learn and agent),
         "note": "学习包缺失时只列事实，不自动生成题目；题目必须逐本读原文后设计。"}
    io.open(os.path.join(d, "unit.json"), "w", encoding="utf-8").write(json.dumps(u, ensure_ascii=False, indent=1) + "\n")
    n_all += 1; n_full += u["complete"]
print("单元清单 %d 本；三项齐全 %d 本" % (n_all, n_full))
