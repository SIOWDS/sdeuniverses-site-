# -*- coding: utf-8 -*-
"""《谁来陪伴我？》上站为专著第 92 号"""
import os, re, shutil, html as H

SITE = '/home/claude/site/public'
SRC = '/home/claude/b90'
NO, TITLE = '92', '谁来陪伴我？'
PDFNAME = '谁来陪伴我.pdf'
DST = os.path.join(SITE, 'books/m/' + NO)
SUB = 'AI 时代的婚姻困境'
PAGES_N, WAN = '135 页', '约 7.6 万汉字'
ISBN = '979-8-90690-040-1'

os.makedirs(DST, exist_ok=True)
shutil.copy(f'{SRC}/{PDFNAME}', f'{DST}/{PDFNAME}')
for f in ('cover.jpg', 'cover-full.jpg'):
    shutil.copy(f'{SRC}/{f}', f'{DST}/{f}')

# ---- read.html 抄 84 号 ----
r = open(f'{SITE}/books/m/84/read.html', encoding='utf-8').read()
old_pdf = set(re.findall(r'[^"\'/>]+\.pdf', r))
r = r.replace('/books/m/84/', f'/books/m/{NO}/').replace('第 84 号', f'第 {NO} 号')
for op in old_pdf:
    r = r.replace(op, PDFNAME)
r = r.replace('越顺利，越没有你的位置', TITLE).replace('越顺利越没有你的位置', TITLE)
open(f'{DST}/read.html', 'w', encoding='utf-8').write(r)

# ---- text/ 分页 ----
TXT = os.path.join(DST, 'text')
shutil.rmtree(TXT, ignore_errors=True)
os.makedirs(TXT, exist_ok=True)
raw = open(f'{SRC}/manuscript.md', encoding='utf-8').read()
raw = re.sub(r'\*\*(.+?)\*\*', r'\1', raw).replace('**', '')
blocks = [b.strip() for b in raw.split('\n\n') if b.strip()]

SLUG = {'出版信息': 'pub', '作者介绍': 'au', '前言': 'qy', '导读': 'dd', '导论': 'dl',
        '枢纽章': 'sn', '合章': 'hz', '参考书目': 'ref', '结语': 'jy',
        '全书十句': 'sj', '后记': 'hj', '封底': 'fd'}

pages, cur, ci, bi = [], None, 0, 0
for b in blocks:
    head = None
    if b.startswith('## '):
        head = b.split('\n')[0][3:].strip()
    elif b.startswith('# ') and b[2:3] == '第':
        head = b.split('\n')[0][2:].strip()
    elif b.startswith('# '):
        continue                      # 书名页，跳过
    if head is not None:
        flat = head.replace('　', '').replace(' ', '')
        if re.match(r'^第[一二三四]编', flat):
            bi += 1; slug = 'b%d' % bi
        elif re.match(r'^第[一二三四五六七八九十]+章', flat):
            ci += 1; slug = 'c%02d' % ci
        elif flat.startswith('附录'):
            slug = {'一': 'ap1', '二': 'ap2', '三': 'ap3'}[flat[2]]
        else:
            slug = None
            for k, v in SLUG.items():
                if flat.startswith(k):
                    slug = v; break
            if slug is None:
                slug = 'x%d' % len(pages)
        rest = b.split('\n', 1)[1].strip() if '\n' in b else ''
        cur = (slug, head, [rest] if rest else [])
        pages.append(cur)
    elif cur is not None:
        cur[2].append(b)

CSS = """<style>
:root{--bg:#0A1220;--fg:#E6EDF4;--dim:#8CA0B4;--gold:#C9A227;--mint:#8CE8C8;--line:#1C2E42;--card:#111C2C}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.95 "Noto Serif CJK SC","Songti SC",Georgia,serif}
a{color:var(--gold);text-decoration:none}a:hover{text-decoration:underline}
.bar{position:sticky;top:0;background:rgba(10,18,32,.94);backdrop-filter:blur(8px);
border-bottom:1px solid var(--line);padding:11px 20px;display:flex;gap:16px;flex-wrap:wrap;
font-size:13.5px;align-items:center}
.wrap{max-width:760px;margin:0 auto;padding:30px 22px 70px}
h1{font-size:25px;line-height:1.5;margin:14px 0 6px;font-weight:700;color:var(--mint)}
h2{font-size:18px;color:var(--gold);margin:34px 0 10px;font-weight:700;
border-top:1px solid var(--line);padding-top:16px}
h3{font-size:15.5px;color:#B5C6D6;margin:22px 0 8px;font-weight:700}
.meta{color:var(--dim);font-size:13.5px;margin-bottom:24px}
p{margin:0 0 15px;text-align:justify}
blockquote{margin:16px 0;padding:12px 16px;border-left:3px solid var(--gold);
background:var(--card);color:#E4DECE}
blockquote p{margin:0}
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
       f'<a href="/books/m/{NO}/{PDFNAME}">⬇ 下载</a>'
       f'<span style="color:var(--dim)">德麦国际专著第 {NO} 号</span></div>')


def md_table(b):
    rows = []
    for line in b.split('\n'):
        line = line.strip()
        if not line.startswith('|'):
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        if all(set(c) <= set('-: ') for c in cells):
            continue
        rows.append(cells)
    if not rows:
        return ''
    out = ['<table>']
    for i, rr in enumerate(rows):
        tag = 'th' if i == 0 else 'td'
        out.append('<tr>' + ''.join(f'<{tag}>{H.escape(c)}</{tag}>' for c in rr) + '</tr>')
    out.append('</table>')
    return '\n'.join(out)


def page_html(title, body, prev=None, nxt=None, desc=''):
    nav = '<div class="nav2">'
    nav += f'<a href="/books/m/{NO}/text/{prev[0]}/">‹ {H.escape(prev[1])}</a>' if prev else '<span></span>'
    nav += f'<a href="/books/m/{NO}/text/{nxt[0]}/">{H.escape(nxt[1])} ›</a>' if nxt else '<span></span>'
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
        if b.startswith('#### '):
            body.append('<h3>%s</h3>' % H.escape(b[5:].strip()))
        elif b.startswith('### '):
            body.append('<h2>%s</h2>' % H.escape(b[4:].strip()))
        elif b.startswith('> '):
            q = ' '.join(l.lstrip('> ').strip() for l in b.split('\n'))
            body.append('<blockquote><p>%s</p></blockquote>' % H.escape(q))
        elif b.startswith('|'):
            body.append(md_table(b))
        elif b.startswith('- ') or b.startswith('1. '):
            for line in b.split('\n'):
                body.append('<p>%s</p>' % H.escape(re.sub(r'^(- |\d+\. )', '· ', line.strip())))
        elif b.startswith('---'):
            continue
        else:
            body.append('<p>%s</p>' % H.escape(b.replace('\n', '')))
    desc = re.sub(r'<[^>]+>', '', ''.join(body))[:150]
    prev = (pages[i - 1][0], pages[i - 1][1][:14]) if i > 0 else None
    nxt = (pages[i + 1][0], pages[i + 1][1][:14]) if i < len(pages) - 1 else None
    d = os.path.join(TXT, slug)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(
        page_html(title, '\n'.join(body), prev, nxt, desc))

toc = []
for slug, title, _ in pages:
    cls = 'bian' if re.match(r'^b\d$', slug) else ('chap' if re.match(r'^c\d\d$', slug) else '')
    toc.append('<a class="%s" href="/books/m/%s/text/%s/">%s</a>' % (cls, NO, slug, H.escape(title)))
idx = (f'<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">'
       f'<meta name="viewport" content="width=device-width,initial-scale=1">'
       f'<title>{TITLE} · 网页版全书 · 德麦国际专著第 {NO} 号</title>'
       f'<meta name="description" content="{SUB}。王德生＋Claude 编著，据十位作者的十篇论文全部重写。网页版全书目录。">{CSS}</head><body>'
       f'{BAR}<div class="wrap"><h1>{TITLE}</h1>'
       f'<div class="meta">{SUB} · 王德生 ＋ Claude 编著 · 前言·导读·导论·四编十章·枢纽章·合章·结语·参考书目·三附录·全书十句·后记 · {WAN} · {PAGES_N} · ISBN {ISBN} · 德麦国际专著第 {NO} 号</div>'
       f'<div class="toc">{"".join(toc)}</div>'
       f'<div class="foot">© 德麦国际出版社 · 王德生 ＋ Claude《{TITLE}》</div></div></body></html>')
open(os.path.join(TXT, 'index.html'), 'w', encoding='utf-8').write(idx)
print('text 页数', len(pages))
print([p[0] for p in pages])
assert not any(p[0].startswith('x') for p in pages), '有部件没分到 slug'
