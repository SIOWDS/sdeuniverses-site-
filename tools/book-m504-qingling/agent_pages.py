#!/usr/bin/env python3
"""第 504 号：只为本书生成 /books/m/504/agent/ 页，并把本书一张卡插进 /books/agent/ 名录（数目同步加一）。
做法照 tools/build_book_agents.py 的模板，但不重写其他书的页面（本次是稀疏检出，不能全量重建）。
用法（仓库根目录）：python3 tools/book-m504-qingling/agent_pages.py
"""
import html, json, re
from pathlib import Path

NO = 504
V = '20261003d'
PUB = Path('public')
cat = json.loads((PUB / 'books/catalog.json').read_text())
reg = json.loads((PUB / 'books/agents.json').read_text())['agents']
b = [x for x in cat['books'] if x.get('number') == NO][0]
a = reg[str(NO)]
esc = lambda s: html.escape(str(s or ''), quote=True)
BODY = Path('tools/book_agent_body.html').read_text()
desc = a.get('intro') or ('《%s》的智能体：读懂、用上、拆开、对撞、写出。' % b['title'])
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
""" % {'name': esc(a['name']), 'title': esc(b['title']), 'n': NO, 'desc': esc(desc), 'v': V, 'body': BODY,
       'og': ('<meta property="og:image" content="%s">\n' % esc(b['coverUrl'])) if b.get('coverUrl') else ''}
d = PUB / ('books/m/%d/agent' % NO); d.mkdir(parents=True, exist_ok=True)
(d / 'index.html').write_text(page)

# 名录：插一张卡，总数与本类数目各加一（幂等：已有本书卡则不动）
ip = PUB / 'books/agent/index.html'; t = ip.read_text()
if 'href="/books/m/%d/agent/"' % NO not in t:
    label = cat['categories'][b['category']]
    card = ('<a class="c" href="/books/m/%d/agent/"><b>%s</b><i>%s</i><span>《%s》 · 第 %d 号</span></a>'
            % (NO, esc(a['name']), esc(a.get('epithet', '')), esc(b['title']), NO))
    m = re.search(r'<section><h2>%s<span>(\d+)</span></h2><div class="g">(.*?)</div></section>' % re.escape(esc(label)), t, re.S)
    assert m, label
    cards = re.findall(r'<a class="c" href="/books/m/(\d+)/agent/">.*?</a>', m.group(2), re.S)
    raw = re.findall(r'<a class="c" href="/books/m/\d+/agent/">.*?</a>', m.group(2), re.S)
    pos = next((i for i, n in enumerate(cards) if int(n) < NO), len(cards))
    raw.insert(pos, card)
    new = '<section><h2>%s<span>%d</span></h2><div class="g">%s</div></section>' % (esc(label), int(m.group(1)) + 1, ''.join(raw))
    t = t[:m.start()] + new + t[m.end():]
    n0 = int(re.search(r'共 (\d+) 位', t).group(1))
    t = t.replace('共 %d 位' % n0, '共 %d 位' % (n0 + 1), 1)
    ip.write_text(t)
    print('directory: +1 card in', label)
print('agent page ok', a['name'])
