# -*- coding: utf-8 -*-
"""《判断的危机》上站为专著第 80 号 · 完整体例版"""
import os, re, shutil, html as H

SITE = '/home/claude/site/public'
SRC = '/home/claude/book80'
DST = os.path.join(SITE, 'books/m/80')
PDF, NO, TITLE = '判断的危机.pdf', '80', '判断的危机'
SUB = '它不会发出任何警报——生成成本归零之后，谁还在辨认'
os.makedirs(DST, exist_ok=True)
for f in (PDF, 'cover.jpg', 'cover-full.jpg'):
    shutil.copy(f'{SRC}/{f}', f'{DST}/{f}')

# read.html（若不存在则由 78 号改）
if not os.path.exists(f'{DST}/read.html'):
    r = open(f'{SITE}/books/m/78/read.html', encoding='utf-8').read()
    r = (r.replace('/books/m/78/', '/books/m/80/')
          .replace('A-Cut-in-the-Record.pdf', PDF)
          .replace('一直没出事', TITLE).replace('第 78 号', '第 80 号'))
    open(f'{DST}/read.html', 'w', encoding='utf-8').write(r)

TXT = os.path.join(DST, 'text')
shutil.rmtree(TXT, ignore_errors=True)
os.makedirs(TXT, exist_ok=True)
raw = open(f'{SRC}/判断的危机.md', encoding='utf-8').read()
raw = re.sub(r'\*\*(.+?)\*\*', r'\1', raw).replace('**', '')
blocks = [b.strip() for b in raw.split('\n\n') if b.strip()]

SLUG = {'作者介绍': 'au', '前 言': 'qy', '导 读': 'dd', '导论': 'dl',
        '编一': 'b1', '编二': 'b2', '编三': 'b3', '编四': 'b4',
        '枢纽章': 'sn', '合章': 'hz', '结 语': 'jy', '参考文献': 'ref',
        '附录一': 'ap1', '附录二': 'ap2', '附录三': 'ap3', '后 记': 'hj', '封 底': 'fd'}
pages, cur, ci = [], None, 0
for b in blocks:
    if b.startswith('# '):
        t = b[2:].strip()
        key = t.split('·')[0].strip()
        if key.startswith('第') and '章' in key:
            ci += 1; slug = 'c%02d' % ci
        else:
            slug = SLUG.get(key, 'x%d' % len(pages))
        cur = (slug, t, []); pages.append(cur)
    elif cur:
        cur[2].append(b)

CSS = """<style>
:root{--bg:#0B0E12;--fg:#E6E4DE;--dim:#8C949C;--gold:#D9A441;--line:#232A31;--card:#11161B}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.95 "Noto Serif CJK SC","Songti SC",Georgia,serif}
a{color:var(--gold);text-decoration:none}a:hover{text-decoration:underline}
.bar{position:sticky;top:0;background:rgba(11,14,18,.94);backdrop-filter:blur(8px);
border-bottom:1px solid var(--line);padding:11px 20px;display:flex;gap:16px;flex-wrap:wrap;
font-size:13.5px;align-items:center}
.wrap{max-width:760px;margin:0 auto;padding:30px 22px 70px}
h1{font-size:25px;line-height:1.5;margin:14px 0 6px;font-weight:700}
h2{font-size:18px;color:var(--gold);margin:34px 0 10px;font-weight:700;
border-top:1px solid var(--line);padding-top:16px}
.meta{color:var(--dim);font-size:13.5px;margin-bottom:24px}
p{margin:0 0 15px;text-align:justify}
table{width:100%;border-collapse:collapse;margin:0 0 20px;font-size:13.5px}
th,td{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}
th{color:var(--gold);background:var(--card)}
.toc a{display:block;padding:9px 12px;border-bottom:1px solid var(--line);color:var(--fg)}
.toc a:hover{background:var(--card);text-decoration:none}
.toc a.bian{color:var(--gold);font-weight:600}
.toc a.chap{padding-left:30px}
.nav2{display:flex;justify-content:space-between;gap:12px;margin-top:44px;
border-top:1px solid var(--line);padding-top:18px;font-size:14px}
.foot{margin-top:50px;color:var(--dim);font-size:12.5px;text-align:center}
</style>"""
BAR = (f'<div class="bar"><a href="/books/m/{NO}/">← 专著首页</a>'
       f'<a href="/books/m/{NO}/text/">目录</a>'
       f'<a href="/books/m/{NO}/read.html">📄 在线 PDF</a>'
       f'<a href="/books/m/{NO}/{PDF}">⬇ 下载</a>'
       f'<span style="color:var(--dim)">德麦国际专著第 {NO} 号</span></div>')


def md_table(b):
    rows = []
    for line in b.split('\n'):
        line = line.strip()
        if not line.startswith('|'): continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        if all(set(c) <= set('-: ') for c in cells): continue
        rows.append(cells)
    if not rows: return ''
    out = ['<table>']
    for i, r in enumerate(rows):
        tag = 'th' if i == 0 else 'td'
        out.append('<tr>' + ''.join(f'<{tag}>{H.escape(c)}</{tag}>' for c in r) + '</tr>')
    out.append('</table>')
    return '\n'.join(out)


def page_html(title, body, prev=None, nxt=None, desc=''):
    nav = '<div class="nav2">'
    nav += f'<a href="/books/m/{NO}/text/{prev[0]}/">‹ {prev[1]}</a>' if prev else '<span></span>'
    nav += f'<a href="/books/m/{NO}/text/{nxt[0]}/">{nxt[1]} ›</a>' if nxt else '<span></span>'
    nav += '</div>'
    return (f'<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{H.escape(title)} · {TITLE} · 德麦国际专著第 {NO} 号</title>'
            f'<meta name="description" content="{H.escape(desc[:150])}">{CSS}</head><body>'
            f'{BAR}<div class="wrap"><h1>{H.escape(title)}</h1>{body}{nav}'
            f'<div class="foot">© 德麦国际出版社 · 王德生 ＋ Claude《{TITLE}》</div></div></body></html>')


for i, (slug, title, bs) in enumerate(pages):
    body = []
    for b in bs:
        if b.startswith('### '):
            body.append('<h2>%s</h2>' % H.escape(b[4:].strip()))
        elif b.startswith('|'):
            body.append(md_table(b))
        elif b.startswith('- '):
            for line in b.split('\n'):
                body.append('<p>· %s</p>' % H.escape(line[2:].strip()))
        elif b.startswith('---'):
            continue
        else:
            body.append('<p>%s</p>' % H.escape(b.replace('\n', '')))
    desc = re.sub(r'<[^>]+>', '', ''.join(body))[:150]
    prev = (pages[i - 1][0], pages[i - 1][1][:14]) if i > 0 else None
    nxt = (pages[i + 1][0], pages[i + 1][1][:14]) if i < len(pages) - 1 else None
    d = os.path.join(TXT, slug); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(
        page_html(title, '\n'.join(body), prev, nxt, desc))

# 出版信息页
pub = """<table>
<tr><th>项</th><th>内容</th></tr>
<tr><td>书名</td><td>判断的危机——它不会发出任何警报</td></tr>
<tr><td>著者</td><td>王德生 ＋ Claude</td></tr>
<tr><td>出版发行</td><td>德麦国际出版社 Demai International Press</td></tr>
<tr><td>版次</td><td>2026 年 8 月第 1 版第 1 次印刷</td></tr>
<tr><td>开本</td><td>16 开 170mm × 240mm · 332 页</td></tr>
<tr><td>字数</td><td>约 23.6 万汉字</td></tr>
<tr><td>专著编号</td><td>德麦国际专著第 80 号</td></tr>
<tr><td>ISBN</td><td>申领中</td></tr>
<tr><td>分类</td><td>人工智能 / 制度经济 / 科学社会学 / 教育评价</td></tr>
</table>
<h2>成书说明</h2>
<p>本书由「学科通融」专栏之四十四至之五十三共十篇连续研究编成，另新写前言、导读、导论、枢纽章、合章、结语与附录。十篇原刊于 sdeuniverses.com，作者王德生＋Claude；编入本书时篇名改为章名、篇际互引改为章际互引，正文未作删节。</p>
<h2>创新智商标注</h2>
<p>本书的前言、导读、导论、枢纽章的书内导入与推广、合章、结语、附录与后记由编者写作，因此按本栏规程，编者不得为本书出具认证分。全书盲评待未参与写作的一方独立完成后公布。</p>
<p>版权所有 侵权必究。本书内容可自由引用与批评，引用时请注明出处。</p>"""
d = os.path.join(TXT, 'pub'); os.makedirs(d, exist_ok=True)
open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(
    page_html('出版信息', pub, None, (pages[0][0], pages[0][1][:14]), '《判断的危机》出版信息与成书说明'))

toc = ['<a href="/books/m/%s/text/pub/">出版信息</a>' % NO]
for slug, title, _ in pages:
    cls = 'bian' if slug.startswith('b') and len(slug) == 2 else ('chap' if slug.startswith('c') else '')
    toc.append('<a class="%s" href="/books/m/%s/text/%s/">%s</a>' % (cls, NO, slug, H.escape(title)))
idx = (f'<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">'
       f'<meta name="viewport" content="width=device-width,initial-scale=1">'
       f'<title>{TITLE} · 网页版全书 · 德麦国际专著第 {NO} 号</title>'
       f'<meta name="description" content="判断的危机——它不会发出任何警报。王德生＋Claude著。网页版全书目录。">{CSS}</head><body>'
       f'{BAR}<div class="wrap"><h1>{TITLE}</h1>'
       f'<div class="meta">{SUB} · 王德生 ＋ Claude 著 · 前言·导读·导论·四编十章·枢纽章·合章·结语·参考文献·附录·后记 · 约 23.6 万字 · 332 页 · 德麦国际专著第 {NO} 号</div>'
       f'<div class="toc">{"".join(toc)}</div>'
       f'<div class="foot">© 德麦国际出版社 · 王德生 ＋ Claude《{TITLE}》</div></div></body></html>')
open(os.path.join(TXT, 'index.html'), 'w', encoding='utf-8').write(idx)
print('text 页数', len(pages) + 2, [p[0] for p in pages])
