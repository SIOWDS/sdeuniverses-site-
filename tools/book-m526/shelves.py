#!/usr/bin/env python3
"""第 526 号：把本书挂上三处书架（books/、monographs/、sites/read/library/）。可重跑：已有本书的条目先取下再挂。
在 publish.py、build_unit_526.py、register.py 之后跑。用法（仓库根目录）：python3 tools/book-m526/shelves.py"""
import html as H, json, re, sys
from pathlib import Path
HERE = Path(__file__).parent; sys.path.insert(0, str(HERE))
import meta as M  # noqa
SITE = HERE.resolve().parents[1] / 'public'
NO, T = M.NO, M.TITLE
e = [x for x in json.loads((SITE / 'books/catalog.json').read_text())['books'] if x.get('number') == NO][0]
AG = json.loads((HERE / 'content.json').read_text())['agent']['name']
LABEL = '文明与社会'
U = e['detailUrl']; esc = lambda s: H.escape(s, quote=True)
desc = e['description']; by = '、'.join(e['authors'])
art = ('<article class="book" data-publication-unit="m-{n}" data-id="m-{n}" data-title="{t}" data-number="{n}" data-category="{c}" data-reading="full" data-authors="{au}" data-search="{s}" data-flip="true" data-online="{on}">'
       '<div class="book-main"><a class="cover" href="{u}" tabindex="-1" aria-hidden="true"><img src="{cov}" alt="" width="92" height="134" loading="lazy" decoding="async"><span class="no-cover" hidden>{t}</span></a>'
       '<div class="book-copy"><p class="book-tag"><span>{lab}</span><span class="ordinal">#{n}</span></p><h3><a href="{u}">{t}</a></h3><p class="byline">{by}</p><p class="description">{d}</p></div></div>'
       '<div class="book-meta"><span class="reading-state full">全文可读</span><span class="format">网页 / PDF</span></div>'
       '<div class="book-actions publication-unit-actions" role="group" aria-label="阅读、学习、智能问对"><p class="publication-unit-label">三位一体出版单元</p>'
       '<a class="read-button" data-unit-action="read" href="{u}read.html" aria-label="{t}：阅读 · 在线翻页">阅读 · 在线翻页</a>'
       '<a class="learn-link" data-unit-action="learn" href="{u}agent/learning.html" aria-label="{t}：{ll}">{ll}</a>'
       '<a class="agent-link" data-unit-action="agent" href="{u}agent/dialogue.html" aria-label="{t}：智能问对 · {ag}">智能问对 · {ag}</a>'
       '<div class="unit-secondary"><a class="detail-button chapter-link" href="{u}text/" aria-label="{t}：章节阅读">章节阅读</a><a class="detail-button" href="{u}" aria-label="{t}：书籍详情">详情</a>'
       '<a class="pdf-link" href="{pdf}" aria-label="{t}：PDF">PDF ↗</a></div></div></article>').format(
    n=NO, t=esc(T), c=e['category'], au=esc(json.dumps(e['authors'], ensure_ascii=False)),
    s=esc(' '.join([T, by, LABEL, desc, e['isbn'], str(NO)])), on=e['publishedAt'], u=U, cov=e['coverUrl'],
    lab=LABEL, by=esc(by), d=esc(desc), ll=esc(e['learnLabel']), ag=esc(AG), pdf=e['pdfUrl'])
GRID = '<div id="book-grid" class="book-grid">'
for f in ('books/index.html', 'monographs/index.html', 'sites/read/library/index.html'):
    p = SITE / f; h = p.read_text()
    h = re.sub(r'<article class="book" data-publication-unit="m-%d".*?</article>' % NO, '', h, flags=re.S)
    n = h.count('<article class="book"')
    h = re.sub(r'<strong>\d+</strong>部图书', '<strong>%d</strong>部图书' % (n + 1), h, count=1)
    h = re.sub(r'aria-live="polite">\d+ 部</span>', 'aria-live="polite">%d 部</span>' % (n + 1), h, count=1)
    assert h.count(GRID) == 1, f
    k = h.index(GRID) + len(GRID)
    h = h[:k] + art + h[k:]
    p.write_text(h); print(f, n, '->', n + 1)
