#!/usr/bin/env python3
"""精选本网页正文：book.json → public/books/m/48/text/（目录页 + 48 个分篇页）"""
import json, re, html
from pathlib import Path
from bs4 import BeautifulSoup

SITE = Path('/home/user/sdeuniverses-site-/public/books/m/48')
QB = SITE / 'quanben/text'
book = json.load(open('book.json'))
outline = json.load(open('outline.json'))['print']
V = '20260930p'
AUTH = '王德生、刘春华'


def cjk(s):
    return len(re.findall(r'[一-鿿]', s))


def folio(title_start):
    for o in outline:
        if o['t'].replace('　', '').startswith(title_start.replace('　', '')):
            return o['g'] - 4
    return None


# 页面样式直接沿用全本网页版
tpl = (QB / '06/index.html').read_text()
CSS = tpl[tpl.index('<style>'):tpl.index('</style>')] + '''
article table{width:100%;border-collapse:collapse;font-size:14.5px;line-height:1.7;margin:22px 0 26px}
@media(max-width:560px){article table{display:block;overflow-x:auto}}
article th{background:#2A3A5E;color:#fff;font-weight:700;text-align:left;padding:8px 10px;white-space:nowrap}
article td{border-bottom:1px solid var(--border);padding:8px 10px;vertical-align:top}
article tbody tr:nth-child(even) td{background:rgba(94,71,16,0.05)}
article td:first-child{font-weight:700;color:var(--accent)}
article p.num{padding-left:1.6em;text-indent:-1.6em}
article p.dash{text-indent:0;color:var(--muted);letter-spacing:.04em;margin-top:-6px}
article p.tcap{text-indent:0;margin:26px 0 0}
article h2{font-size:22px;margin:52px 0 18px}
</style>'''
TAIL = '''<script>window.WDS_READ={selector:"article"};</script>
<script src="/taste/wds-companion/wds-read.js?v=20260817c" defer></script>
<script src="/wds-mode.js?v=20261004d" defer></script>
<script src="/assets/sde-talk.js?v=20260817c" data-pv="1" defer></script>
</body>
</html>
'''

NOTE_HTML = ['<p>' + html.escape(p) + '</p>' for p in [
    '《三律心理学——意识、人格与学习的本体论革命》全本原分上下两册，六编三十二篇，约七十万字。本书是它的精选本，约二十万字，仍为德麦国际专著第 48 号。',
    '精选依三条原则。',
    '第一，结构不动。全书“立基—破旧—立新—拓展—应用—升华”的六编弧线，以及各编的编序与编结，全部保留；六编的主线一条不缺。',
    '第二，每篇只取承重的部分。原稿多由系列长文汇成，同一论点常在几篇文字里反复展开。精选本取论证最完整的一篇，舍去重复的展开；向经济学、物理学、营销与企业管理延伸的外篇，以及“实体发生学”一篇，留在全本。',
    '第三，文字一仍其旧。正文的论断、例证与行文都不改动。编辑只做选篇、删节、章次重排，接回排版时断开的段落，删去原稿篇内的旧章号；编序与编结中提到未选篇目之处，作了最小的相应改动。',
]] + ['<p>全本仍在本站开放阅读，供需要完整论证与全部外篇的读者查考：<a href="/books/m/48/quanben/">《三律心理学》七十万字全本 →</a></p>']

# ---------------------------------------------------------------- 分篇清单
pages = []  # dict(slug, kicker, title, html, group, idx, pdf_title)
def add(kicker, title, frags, group, idx, pdf_title=None):
    pages.append(dict(slug=f'{len(pages) + 1:02d}', kicker=kicker, title=title, html=frags, group=group, idx=idx,
                      pdf_title=pdf_title or title))

add('卷首', '精选本说明', NOTE_HTML, 'front', '—')
for f in book['front']:
    add('卷首', f['title'], f['html'], 'front', '—', '导读' if f['title'] == '全书导读' else f['title'])
for p in book['parts']:
    pk = f"{p['label']} · {p['title']}"
    add(pk, '编序', p['xu'], p['label'], '序', f"{p['label']}　{p['title']}")
    for c in p['chapters']:
        add(pk + f" · 第 {c['no']} 章", c['title'], c['html'], p['label'], str(c['no']), f"第 {c['no']} 章　{c['title']}")
    add(pk, '本编结语', p['jie'], p['label'], '结', None)
for f in book['back']:
    add('卷尾', f['title'], f['html'], 'back', '—')

# 本编结语在 PDF 里接在该编末章之后，页码取末章起页
for i, pg in enumerate(pages):
    pg['chars'] = sum(cjk(BeautifulSoup(x, 'html.parser').get_text()) for x in pg['html'])
    pg['folio'] = folio(pg['pdf_title']) if pg['title'] != '本编结语' else None


def page_html(i):
    pg = pages[i]
    prev = pages[i - 1] if i > 0 else None
    nxt = pages[i + 1] if i + 1 < len(pages) else None
    meta = f"约 {pg['chars']:,} 字" + (f" · 纸书第 {pg['folio']} 页起" if pg['folio'] else '') + f' · {AUTH} 著'
    desc = f"《三律心理学——意识、人格与学习的本体论革命》（精选本）{pg['kicker']} · {pg['title']}。{AUTH} 著，德麦国际出版社。"
    pager = '<div class="pager">\n'
    pager += (f'<a href="/books/m/48/text/{prev["slug"]}/"><span class="pl">上 一 篇</span><span class="pn">{html.escape(prev["title"])}</span></a>\n'
              if prev else '<a href="/books/m/48/"><span class="pl">导 读 页</span><span class="pn">返回本书导读页</span></a>\n')
    pager += '<a href="/books/m/48/text/"><span class="pl">目 录</span><span class="pn">返回全书目录</span></a>\n'
    if nxt:
        pager += (f'<a href="/books/m/48/text/{nxt["slug"]}/" style="text-align:right"><span class="pl">下 一 篇</span>'
                  f'<span class="pn">{html.escape(nxt["title"])}</span></a>\n')
    pager += '</div>'
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(pg["title"])} · 三律心理学 | {AUTH}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="https://sdeuniverses.com/books/m/48/text/{pg["slug"]}/">
{CSS}
</head>
<body>
<nav class="top"><div class="wrap">
  <a class="nav-logo" href="/books/m/48/text/">三律心理学 · 目录</a>
  <a class="nav-back" href="/books/m/48/">← 专著导读页</a>
</div></nav>

<div class="wrap">
<header class="chead">
<div class="kicker">{html.escape(pg["kicker"])}</div>
<h1 class="t">{html.escape(pg["title"])}</h1>
<div class="cmeta">{meta}</div>
</header>
<article>
{chr(10).join(pg["html"])}
</article>
{pager}
</div>
<!-- 读者讨论区+阅读计数 · sde-talk v3 (Google实名) -->

<footer><div class="wrap">《三律心理学》（精选本） · {AUTH} 著 · 德麦国际出版社 · <a href="/books/m/48/text/">全书目录</a> · <a href="/books/m/48/">导读页</a> · <a href="/browse/">首页</a></div></footer>
{TAIL}'''


# ---------------------------------------------------------------- 目录页
itpl = (QB / 'index.html').read_text()
ICSS = itpl[itpl.index('<style>'):itpl.index('</style>') + 8]
COLORS = {'第一编': ('#5C6BA8', '奠基：SIO 本体论与意义三律'), '第二编': ('#A8552E', '破旧：行为主义·认知主义·人本主义'),
          '第三编': ('#2E6E8F', '立新：意识的三律发生'), '第四编': ('#6E4E8F', '拓展：人格发生学与心理健康'),
          '第五编': ('#2E7D5B', '应用：学习心理学的三律革命'), '第六编': ('#A8322E', '升华：创造力的发生与回春')}


def li(pg):
    return (f'<li><a href="/books/m/48/text/{pg["slug"]}/"><span class="idx">{pg["idx"]}</span>'
            f'<span class="tt">{html.escape(pg["title"])}</span><span class="wc">{pg["chars"]:,} 字</span></a></li>')


blocks = []
fr = [p for p in pages if p['group'] == 'front']
blocks.append('<div class="part"><div class="part-h" style="background:#3E3524"><span class="pn">卷 首</span>'
              '<span class="pt">精选本说明 · 推荐语 · 作者的话 · 总序 · 导读</span></div><ol>\n' + '\n'.join(li(p) for p in fr) + '\n</ol></div>')
for part in book['parts']:
    col, pd = COLORS[part['label']]
    ps = [p for p in pages if p['group'] == part['label']]
    blocks.append(f'<div class="part"><div class="part-h" style="background:{col}"><span class="pn">{part["label"]}</span>'
                  f'<span class="pt">{html.escape(part["title"])}</span><span class="pd">{pd}</span></div><ol>\n'
                  + '\n'.join(li(p) for p in ps) + '\n</ol></div>')
bk = [p for p in pages if p['group'] == 'back']
blocks.append('<div class="part"><div class="part-h" style="background:#3E3524"><span class="pn">卷 尾</span>'
              '<span class="pt">全书总结 · 全书金句</span></div><ol>\n' + '\n'.join(li(p) for p in bk) + '\n</ol></div>')
total = sum(p['chars'] for p in pages)
index = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>全书目录 · 三律心理学（精选本） | {AUTH}</title>
<meta name="description" content="《三律心理学——意识、人格与学习的本体论革命》精选本网页版目录：六编二十九章，约 {total / 10000:.1f} 万字，{AUTH} 著，德麦国际出版社。">
<link rel="canonical" href="https://sdeuniverses.com/books/m/48/text/">
{ICSS}
</head>
<body>
<nav class="top"><div class="wrap">
  <a class="nav-logo" href="/browse/">SDE Universes</a>
  <a class="nav-back" href="/books/m/48/">← 专著导读页</a>
</div></nav>
<header class="hero">
  <div class="dom">心 理 学 · 本 体 论 革 命</div>
  <h1>三律心理学</h1>
  <div class="sub">意识、人格与学习的本体论革命 · 精选本</div>
  <div class="meta">{AUTH} 著 · 德麦国际出版社 · 六编二十九章 · 约 {total / 10000:.1f} 万字 · 网页排版版</div>
  <div class="cta">
    <a class="cta-a" href="/books/m/48/text/01/">从头读起 →</a>
    <a class="cta-b" href="/books/m/48/read.html">在线翻页阅读</a>
  </div>
</header>
<main><div class="wrap">
<div class="lede">这是《三律心理学》精选本的网页排版版。精选本从约七十万字的全本中选出约二十万字，保留全书六编的结构与各编编序、编结，每篇只取承重的部分，正文文字一仍其旧。全书二十九章，从 SIO 本体论与意义三律立基，经对行为主义、认知主义、人本主义的解构，重建意识论与人格论，再落到学习与创造力。需要完整论证与全部外篇，请读<a href="/books/m/48/quanben/text/">七十万字全本</a>。</div>
{chr(10).join(blocks)}
</div></main>
<!-- 读者讨论区+阅读计数 · sde-talk v3 (Google实名) -->
<footer><div class="wrap">《三律心理学》（精选本） · {AUTH} 著 · 德麦国际出版社（新加坡） · <a href="/books/m/48/">导读页</a> · <a href="/philosophy/#books">专著全景</a> · <a href="/browse/">首页</a></div></footer>
<script src="/wds-mode.js?v=20261004d" defer></script>
<script src="/assets/sde-talk.js?v=20260817c" data-pv="1" defer></script>
</body>
</html>
'''

out = SITE / 'text'
out.mkdir(exist_ok=True)
(out / 'index.html').write_text(index)
for i, pg in enumerate(pages):
    d = out / pg['slug']
    d.mkdir(exist_ok=True)
    (d / 'index.html').write_text(page_html(i))
json.dump([{k: v for k, v in p.items() if k != 'html'} for p in pages], open('pages.json', 'w'), ensure_ascii=False, indent=1)
print(len(pages), 'pages; total', total)
