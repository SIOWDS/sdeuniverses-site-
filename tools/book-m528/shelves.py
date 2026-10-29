#!/usr/bin/env python3
"""第 528 号：把本书挂上三处书架（books/、monographs/、sites/read/library/）、全部智能体页（books/agent/），
并写本书的智能体入口页 books/m/528/agent/index.html（照第 527 号同名页）。在 publish.py、build_unit_528.py、register.py 之后运行。
用法（仓库根目录）：python3 tools/book-m528/shelves.py
"""
import html as H, json, re, sys
from pathlib import Path
HERE = Path(__file__).parent; sys.path.insert(0, str(HERE))
import meta as M  # noqa
SITE = HERE.resolve().parents[1] / 'public'
NO, T = M.NO, M.TITLE
cat = json.loads((SITE / 'books/catalog.json').read_text())['books']
e = [x for x in cat if str(x.get('number')) == str(NO)][0]
CT = json.loads((HERE / 'content.json').read_text())
AG, EPI = CT['agent']['name'], CT['agentEpithet']
LABEL = '教育与学习'
U = e['detailUrl']; esc = lambda s: H.escape(s, quote=True)
desc = e['description']
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
    s=esc(' '.join([T, ' '.join(e['authors']), LABEL, desc, e['isbn'], str(NO)])), on=e['publishedAt'], u=U, cov=e['coverUrl'],
    lab=LABEL, by=esc('、'.join(e['authors'])), d=esc(desc), ll=esc(e['learnLabel']), ag=esc(AG), pdf=e['pdfUrl'])
for f in ('books/index.html', 'monographs/index.html', 'sites/read/library/index.html'):
    p = SITE / f; h = p.read_text()
    assert 'data-publication-unit="m-%d"' % NO not in h, f + ' 已有本书'
    n = int(re.search(r'<strong>(\d+)</strong>部图书', h).group(1))
    assert h.count('<article class="book"') == n, (f, n)
    h = h.replace('<strong>%d</strong>部图书' % n, '<strong>%d</strong>部图书' % (n + 1), 1)
    old = 'aria-live="polite">%d 部</span>' % n; assert old in h; h = h.replace(old, 'aria-live="polite">%d 部</span>' % (n + 1), 1)
    k = h.index('<div id="book-grid" class="book-grid">') + len('<div id="book-grid" class="book-grid">')
    h = h[:k] + art + h[k:]
    p.write_text(h); print(f, n, '->', n + 1)
# all-agents page
p = SITE / 'books/agent/index.html'; h = p.read_text()
assert '/books/m/%d/agent/' % NO not in h
m = re.search(r'共 (\d+) 位', h); tot = int(m.group(1)); h = h.replace(m.group(0), '共 %d 位' % (tot + 1), 1)
m = re.search(r'<section><h2>%s<span>(\d+)</span></h2><div class="g">' % LABEL, h); assert m
card = '<a class="c" href="/books/m/%d/agent/"><b>%s</b><i>%s</i><span>《%s》 · 第 %d 号</span></a>' % (NO, esc(AG), esc(EPI), esc(T), NO)
h = h[:m.start()] + '<section><h2>%s<span>%d</span></h2><div class="g">' % (LABEL, int(m.group(1)) + 1) + card + h[m.end():]
p.write_text(h); print('agents page', tot, '->', tot + 1)
# book agent entry page
tpl = (SITE / 'books/m/527/agent/index.html').read_text()
intro = CT['agentIntro']
reps = [('九问 · 《子本打造法》的智能体', '%s · 《%s》的智能体' % (AG, T)), ('德麦国际专著第 527 号', '德麦国际专著第 %d 号' % NO),
        ('<meta name="book-agent" content="九问"><meta name="book_no" content="527">', '<meta name="book-agent" content="%s"><meta name="book_no" content="%d">' % (esc(AG), NO)),
        ('https://sdeuniverses.com/books/m/527/agent/', U + 'agent/'), ('window.BOOK_AGENT={no:527};', 'window.BOOK_AGENT={no:%d};' % NO)]
for a, b in reps:
    assert a in tpl, a; tpl = tpl.replace(a, b)
tpl = re.sub(r'<meta name="description" content="[^"]*">', '<meta name="description" content="%s">' % esc(intro[:150]), tpl)
tpl = re.sub(r'<meta property="og:description" content="[^"]*">', '<meta property="og:description" content="%s">' % esc(intro[:150]), tpl)
tpl = re.sub(r'<meta property="og:image" content="[^"]*">', '<meta property="og:image" content="%s">' % e['coverUrl'], tpl)
assert '527' not in tpl and '子本打造法' not in tpl and '九问 ·' not in tpl.split('<title>')[1][:20], [l for l in tpl.splitlines() if '527' in l]
(SITE / ('books/m/%d/agent/index.html' % NO)).write_text(tpl); print('agent index ok')
