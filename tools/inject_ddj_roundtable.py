#!/usr/bin/env python3
"""三本《道德经》详情页（290/297/311）挂「圆桌」入口：三位智能体彼此接话。幂等。用法：python3 tools/inject_ddj_roundtable.py"""
import json, re, html
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
MARK = "<!-- ddj-roundtable v1 -->"
AG = json.loads((ROOT / "public/books/agents.json").read_text(encoding="utf-8"))["agents"]
T = {290: "普通人都能懂的老子", 297: "道德经SDE解构导论", 311: "道德经的缝隙与填补"}
OLD = re.compile(r"\n?" + re.escape(MARK) + r".*?</div>\n<!-- /ddj-roundtable -->", re.S)
for me in T:
    others = [n for n in T if n != me]
    links = " · ".join('<a href="/books/m/%d/agent/">%s（《%s》）</a>' % (n, html.escape(AG[str(n)]["name"]), html.escape(T[n])) for n in others)
    blk = (MARK + '\n<div class="ddj-rt" style="margin:.8rem 0 0;padding:12px 16px;border:1px dashed #E0A58A;border-radius:12px;background:#12161B;color:#E6E4DE;font-size:.88rem;line-height:1.8">'
           '<b style="color:#E0A58A">三本《道德经》圆桌</b>　这三本书各有一位智能体，彼此互为对方的 RAG，还能互相接话：在「%s」的每一答下面，点「请 X 接话」，另一位会读到刚才的话，从自己那本书里同意、补充或反对。同桌：%s。</div>\n<!-- /ddj-roundtable -->'
           % (html.escape(AG[str(me)]["name"]), links))
    p = ROOT / ("public/books/m/%d/index.html" % me)
    h = p.read_text(encoding="utf-8")
    h = OLD.sub("", h)
    m = re.search(r'<a class="ssh-e".*?</a>', h, re.S)
    assert m, p
    h = h[:m.end()] + "\n" + blk + h[m.end():]
    p.write_text(h, encoding="utf-8"); print("ok", p)
