#!/usr/bin/env python3
"""Build the /books/m/125/ page set for 《番茄炒蛋是谁发现的？》 from the full manuscript."""
import re, json, html, subprocess, pathlib

SITE = pathlib.Path('/home/claude/site')
SRC = pathlib.Path('/mnt/user-data/outputs/番茄炒蛋是谁发现的_专著全本.md').read_text(encoding='utf-8')
NO = 125
ISBN = '979-8-90690-095-1'
TITLE = '番茄炒蛋是谁发现的？'
SUB = '一台引擎，三扇门：知识、技术、艺术的发生学'
TIER_REASON = 'Q3第一刀：全文为主张层——三扇门与三种验法的承重区分、"验法造出看法"、五条承重命题与各自的作废条件、与赖尔/波兰尼/杜威/西蒙东的分离线；且为方法论的家常入门，靠传播才有生态，按六条边界裁定应公开'
BASE = f'/books/m/{NO}'
OUT = SITE / f'public/books/m/{NO}'

HEAD = '''<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="tier" content="L0">
<meta name="tier_set_at" content="统稿">
<meta name="tier_reason" content="{reason}">
<meta name="cite_ok" content="true">
<meta name="source" content="自撰">
<meta name="isbn" content="{isbn}">
<meta name="book_no" content="{no}">
<style>
:root{{--bg:#0B0E12;--fg:#E6E4DE;--dim:#8C949C;--gold:#D9A441;--line:#232A31;--card:#11161B}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.95 "Noto Serif CJK SC","Songti SC",Georgia,serif}}
a{{color:var(--gold);text-decoration:none}}a:hover{{text-decoration:underline}}
.bar{{position:sticky;top:0;background:rgba(11,14,18,.96);border-bottom:1px solid var(--line);padding:10px 18px;display:flex;gap:14px;flex-wrap:wrap;align-items:center;font-size:13px;z-index:9}}
.wrap{{max-width:760px;margin:0 auto;padding:34px 20px 90px}}
h1{{font-size:27px;line-height:1.5;margin:.2em 0 .1em}}
h2{{font-size:21px;margin:1.7em 0 .6em;color:var(--fg)}}
h3{{font-size:17px;margin:1.5em 0 .5em;color:var(--gold);font-weight:600}}
p{{margin:.85em 0;text-align:justify}}
.meta{{color:var(--dim);font-size:13.5px;margin:.4em 0 1.8em;line-height:1.75}}
blockquote{{margin:1.2em 0;padding:.7em 1.1em;border-left:3px solid var(--gold);background:var(--card);color:var(--dim)}}
ul{{padding-left:1.4em}}li{{margin:.3em 0}}
hr{{border:0;border-top:1px solid var(--line);margin:2.2em 0}}
table{{border-collapse:collapse;width:100%;margin:1.3em 0;font-size:14px}}
th,td{{border:1px solid var(--line);padding:7px 9px;text-align:left;vertical-align:top}}
th{{background:var(--card);color:var(--gold);font-weight:600}}
.nav{{display:flex;justify-content:space-between;gap:14px;margin-top:3.2em;padding-top:1.3em;border-top:1px solid var(--line);font-size:14px}}
.foot{{margin-top:2.4em;color:var(--dim);font-size:12px;text-align:center}}
.toc a{{display:block;padding:7px 0;border-bottom:1px solid var(--line)}}
.ptx{{margin:1.8em 0 .5em;color:var(--gold);font-size:14px;letter-spacing:.08em}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:4px;padding:16px 18px;margin:1.3em 0}}
.card h3{{margin-top:0}}
.pill{{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:2px 10px;font-size:12px;color:var(--dim);margin:0 6px 6px 0}}
.cover{{width:100%;max-width:300px;border:1px solid var(--line);border-radius:3px;display:block;margin:0 auto 1.6em}}
</style>
</head><body><div class="bar"><a href="{base}/">← 专著首页</a><a href="{base}/text/">目录</a><a href="/books/">专著栏目</a></div>
'''

FOOT = f'<div class="foot">《{TITLE}——{SUB}》· 王德生 著 · 德麦国际专著第 {NO} 号 · ISBN {ISBN}</div>'

def md2html(md):
    """Small markdown -> html for the body of one unit."""
    out, i = [], 0
    lines = md.split('\n')
    while i < len(lines):
        l = lines[i]
        if not l.strip(): i += 1; continue
        if l.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')]); i += 1
            head = rows[0]; body = rows[2:] if len(rows) > 2 else []
            t = '<table><thead><tr>' + ''.join(f'<th>{inl(c)}</th>' for c in head) + '</tr></thead><tbody>'
            for r in body: t += '<tr>' + ''.join(f'<td>{inl(c)}</td>' for c in r) + '</tr>'
            out.append(t + '</tbody></table>'); continue
        if l.startswith('### '): out.append(f'<h3>{inl(l[4:])}</h3>'); i += 1; continue
        if l.startswith('## '): out.append(f'<h3>{inl(l[3:])}</h3>'); i += 1; continue
        if l.startswith('# '): out.append(f'<h2>{inl(l[2:])}</h2>'); i += 1; continue
        if l.strip() == '---': out.append('<hr />'); i += 1; continue
        if l.startswith('> '): out.append(f'<blockquote><p>{inl(l[2:])}</p></blockquote>'); i += 1; continue
        if l.startswith('- '):
            items = []
            while i < len(lines) and lines[i].startswith('- '):
                items.append(f'<li>{inl(lines[i][2:])}</li>'); i += 1
            out.append('<ul>' + ''.join(items) + '</ul>'); continue
        out.append(f'<p>{inl(l)}</p>'); i += 1
    return '\n'.join(out)

def inl(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    return s

# ---- split the manuscript into units ----
units = []   # (slug, kind, label, group, body)
blocks = re.split(r'\n(?=# )', SRC)
group = None
chap_n = 0
for b in blocks:
    m = re.match(r'# (.+)', b)
    if not m: continue
    h1 = m.group(1).strip()
    body = b
    if h1.startswith('番茄炒蛋是谁发现的'): continue
    if h1 == '版权信息':
        units.append(('fm0', 'front', '版权信息', '卷前', body)); continue
    if h1 == '作者介绍':
        units.append(('fm1', 'front', '作者介绍', '卷前', body)); continue
    if h1 == '前言':
        units.append(('fm2', 'front', '前言', '卷前', body)); continue
    if h1.startswith('导读'):
        units.append(('fm3', 'front', h1, '卷前', body)); continue
    if h1.startswith('导论'):
        units.append(('intro', 'intro', h1, '导论', body)); continue
    if h1.startswith('参考书目'):
        units.append(('ref', 'back', '参考书目', '卷后', body)); continue
    if h1.startswith('附录'):
        # split appendices by ## 附
        parts = re.split(r'\n(?=## 附)', body)
        lead = parts[0]
        for k, p in enumerate(parts[1:], 1):
            t = re.match(r'## (.+)', p).group(1).strip()
            units.append((f'ap{k}', 'appendix', t, '附录', p))
        continue
    if h1.startswith('卷'):
        group = h1
        vol_no = ['一','二','三','四','五','六','七','八','九'].index(h1[1]) + 1
        # volume preface + its chapters
        segs = re.split(r'\n(?=## 第)', body)
        head_seg = segs[0]
        units.append((f'b{vol_no}', 'volpref', f'卷序·{h1}', h1, head_seg))
        for s in segs[1:]:
            t = re.match(r'## (.+)', s).group(1).strip()
            chap_n += 1
            units.append((f'c{chap_n:02d}', 'chapter', t, h1, s))
        continue

# chapters that live in files whose H1 is a volume are handled; catch stray '## 第N章' blocks at top level
print('units:', len(units), 'chapters:', sum(1 for u in units if u[1] == 'chapter'))

# ---- write unit pages ----
OUT.mkdir(parents=True, exist_ok=True)
for idx, (slug, kind, label, grp, body) in enumerate(units):
    prev = units[idx-1] if idx else None
    nxt = units[idx+1] if idx+1 < len(units) else None
    inner = md2html(re.sub(r'^# .+\n', '', body, count=1) if kind in ('front','intro','back') else re.sub(r'^## .+\n', '', body, count=1) if kind in ('chapter','appendix') else body)
    title_h = f'<h2>{html.escape(label)}</h2>'
    if kind == 'volpref':
        inner = md2html(re.sub(r'^# .+\n', '', body, count=1))
    crumb = f'<p class="ptx">{html.escape(grp)}</p>' if grp else ''
    nav = '<div class="nav">'
    nav += f'<a href="{BASE}/text/{prev[0]}/">← {html.escape(prev[2])}</a>' if prev else f'<a href="{BASE}/text/">← 目录</a>'
    nav += f'<a href="{BASE}/text/{nxt[0]}/">{html.escape(nxt[2])} →</a>' if nxt else f'<a href="{BASE}/">全书首页 →</a>'
    nav += '</div>'
    page = HEAD.format(title=f'{html.escape(label)} · {TITLE} · 德麦国际专著第 {NO} 号',
                       desc=f'{html.escape(label)}——《{TITLE}：{SUB}》，王德生著，德麦国际专著第 {NO} 号。',
                       reason=html.escape(TIER_REASON, quote=True), isbn=ISBN, no=NO, base=BASE)
    page += f'<div class="wrap">{crumb}{title_h}\n<hr />\n{inner}\n<hr />\n{nav}{FOOT}</div></body></html>\n'
    d = OUT / 'text' / slug; d.mkdir(parents=True, exist_ok=True)
    (d / 'index.html').write_text(page, encoding='utf-8')

# ---- TOC ----
toc = []
last_grp = None
for slug, kind, label, grp, _ in units:
    if grp != last_grp:
        toc.append(f'<p class="ptx">{html.escape(grp)}</p>'); last_grp = grp
    toc.append(f'<a href="{BASE}/text/{slug}/">{html.escape(label)}</a>')
page = HEAD.format(title=f'网页版全书 · 目录 · {TITLE} · 德麦国际专著第 {NO} 号',
                   desc=f'《{TITLE}》网页版全书目录，共 {len(units)} 个单元。',
                   reason=html.escape(TIER_REASON, quote=True), isbn=ISBN, no=NO, base=BASE)
page += (f'<div class="wrap"><h1>{TITLE}</h1><p class="meta">{SUB} · 王德生 著 · 德麦国际专著第 {NO} 号 · '
         f'网页版全书，共 {len(units)} 个单元（A5 印本 278 页）</p><div class="toc">' + ''.join(toc) + f'</div>{FOOT}</div></body></html>\n')
(OUT / 'text').mkdir(parents=True, exist_ok=True)
(OUT / 'text' / 'index.html').write_text(page, encoding='utf-8')
print('text pages written')
