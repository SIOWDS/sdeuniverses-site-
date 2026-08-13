# -*- coding: utf-8 -*-
"""《答案随时可得之后》上站为专著第 81 号 · 完整体例版"""
import os, re, shutil, html as H

SITE = '/home/claude/site/public'
SRC = '/home/claude/book81'
NO, TITLE = '81', '答案随时可得之后'
PDF = TITLE + '.pdf'
DST = os.path.join(SITE, 'books/m/' + NO)
SUB = '论知识不是存量，及重新推出它的那一段为何不入账'
PAGES_N, WAN = '229 页', '约 17.9 万汉字'

os.makedirs(DST, exist_ok=True)
for f in (PDF, 'cover.jpg', 'cover-full.jpg'):
    shutil.copy(f'{SRC}/{f}', f'{DST}/{f}')

if not os.path.exists(f'{DST}/read.html'):
    r = open(f'{SITE}/books/m/80/read.html', encoding='utf-8').read()
    r = (r.replace('/books/m/80/', f'/books/m/{NO}/')
          .replace('判断的危机.pdf', PDF)
          .replace('判断的危机', TITLE).replace('第 80 号', f'第 {NO} 号'))
    open(f'{DST}/read.html', 'w', encoding='utf-8').write(r)

TXT = os.path.join(DST, 'text')
shutil.rmtree(TXT, ignore_errors=True)
os.makedirs(TXT, exist_ok=True)
raw = open(f'{SRC}/manuscript.md', encoding='utf-8').read()
raw = re.sub(r'\*\*(.+?)\*\*', r'\1', raw).replace('**', '')
blocks = [b.strip() for b in raw.split('\n\n') if b.strip()]

SLUG = {'出版信息': 'pub', '作者介绍': 'au', '前言': 'qy', '导读': 'dd', '导论': 'dl',
        '十二种读法': 'tj', '枢纽章': 'sn', '合章': 'hz', '参考文献': 'ref'}

pages, cur, ci, bi = [], None, 0, 0
started = False
for b in blocks:
    m = re.match(r'^(#{1,2}) (.+)$', b.split('\n')[0]) if b.startswith('#') else None
    if m and len(m.group(1)) <= 2:
        t = m.group(2).strip()
        if t == TITLE:          # 书名页，跳过
            cur = None; continue
        started = True
        flat = t.replace('　', '').replace(' ', '')
        key = re.split(r'[·]', flat)[0].strip()
        if re.match(r'^第[一二三四]编', t):
            bi += 1; slug = 'b%d' % bi
        elif re.match(r'^第[一二三四五六七八九十]+章', t):
            ci += 1; slug = 'c%02d' % ci
        elif t.startswith('结'):
            slug = 'jy'
        elif t.startswith('后'):
            slug = 'hj'
        elif t.startswith('封'):
            slug = 'fd'
        elif flat.startswith('附录'):
            slug = {'一': 'ap1', '二': 'ap2', '三': 'ap3'}[flat[2]]
        else:
            slug = SLUG.get(key, 'x%d' % len(pages))
        cur = (slug, t, []); pages.append(cur)
    elif cur is not None and started:
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
h3{font-size:15.5px;color:#B9C4CE;margin:22px 0 8px;font-weight:700}
.meta{color:var(--dim);font-size:13.5px;margin-bottom:24px}
p{margin:0 0 15px;text-align:justify}
blockquote{margin:16px 0;padding:12px 16px;border-left:3px solid var(--gold);
background:var(--card);color:#DCD8CE}
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
        if b.startswith('#### '):
            body.append('<h3>%s</h3>' % H.escape(b[5:].strip()))
        elif b.startswith('### '):
            body.append('<h2>%s</h2>' % H.escape(b[4:].strip()))
        elif b.startswith('> '):
            q = ' '.join(l.lstrip('> ').strip() for l in b.split('\n'))
            body.append('<blockquote><p>%s</p></blockquote>' % H.escape(q))
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

toc = []
for slug, title, _ in pages:
    cls = 'bian' if re.match(r'^b\d$', slug) else ('chap' if slug.startswith('c') else '')
    toc.append('<a class="%s" href="/books/m/%s/text/%s/">%s</a>' % (cls, NO, slug, H.escape(title)))
idx = (f'<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">'
       f'<meta name="viewport" content="width=device-width,initial-scale=1">'
       f'<title>{TITLE} · 网页版全书 · 德麦国际专著第 {NO} 号</title>'
       f'<meta name="description" content="{SUB}。王德生＋Claude 著。网页版全书目录。">{CSS}</head><body>'
       f'{BAR}<div class="wrap"><h1>{TITLE}</h1>'
       f'<div class="meta">{SUB} · 王德生 ＋ Claude 著 · 十二种读法·前言·导读·导论·四编十章·枢纽章·合章·结语·参考文献·三附录·后记 · {WAN} · {PAGES_N} · 德麦国际专著第 {NO} 号</div>'
       f'<div class="toc">{"".join(toc)}</div>'
       f'<div class="foot">© 德麦国际出版社 · 王德生 ＋ Claude《{TITLE}》</div></div></body></html>')
open(os.path.join(TXT, 'index.html'), 'w', encoding='utf-8').write(idx)
print('text 页数', len(pages), [p[0] for p in pages])
