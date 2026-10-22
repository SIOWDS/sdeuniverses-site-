# -*- coding: utf-8 -*-
"""书七全文网页（public/books/m/406/text/index.html），照第 320 号全文页的骨架与样式。"""
import re, json, html, sys, glob, os
SITE = '/home/claude/sdeuniverses-site-/public'
B7 = '/home/claude/book7'
NO = 406; V = '20261022a'; SLUG = 'yi-fuhao-bianhua'
OUT = sys.argv[1]
ref = open(SITE + '/books/m/320/text/index.html', encoding='utf-8').read()
head = ref[:ref.index('<body>')]
head = re.sub(r'<title>.*?</title>', '<title>长文网页阅读 · 易：符号的变化，不是符号的发生 · 德麦国际专著第 406 号</title>', head, flags=re.S)
head = head.replace('/books/m/320/', '/books/m/406/').replace('第 320 号', '第 406 号').replace('法学学派解构入门', '易：符号的变化，不是符号的发生')
assert '320' not in re.sub(r'<style.*?</style>', '', head, flags=re.S), [m.group(0) for m in re.finditer('.{30}320.{30}', head)][:3]
tail_script = ref[ref.rindex('<script>'):].replace('bk320', 'bk406')

PARTS = {int(k): v for k, v in json.load(open(B7 + '/layout/parts.json', encoding='utf-8')).items()}
Q = {}
for f in sorted(glob.glob(B7 + '/review3/questions-*.json')):
    Q.update({int(k): v for k, v in json.load(open(f, encoding='utf-8')).items()})
META = json.load(open(B7 + '/layout/meta.json', encoding='utf-8'))

def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    return re.sub(r'`([^`]+)`', r'\1', s)

def table(lines):
    rows = [[c.strip() for c in l.strip().strip('|').split('|')] for l in lines if not re.match(r'^\|[\s:|-]+\|?$', l.strip())]
    if not rows: return ''
    h = '<div class="tw"><table><thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in rows[0]) + '</tr></thead><tbody>'
    for r in rows[1:]: h += '<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>'
    return h + '</tbody></table></div>'

def body(md):
    out, tbl, lst, olst, quote = [], [], [], [], []
    mode = None; titled = False
    def flush():
        nonlocal tbl, lst, olst, quote
        if tbl: out.append(table(tbl)); tbl = []
        if lst: out.append('<ul>' + ''.join(f'<li>{inline(x)}</li>' for x in lst) + '</ul>'); lst = []
        if olst: out.append('<ol>' + ''.join(f'<li>{inline(x)}</li>' for x in olst) + '</ol>'); olst = []
        if quote: out.append('<blockquote>' + ''.join(f'<p>{inline(x)}</p>' for x in quote) + '</blockquote>'); quote = []
    def close():
        nonlocal mode
        flush()
        if mode: out.append('</div>'); mode = None
    for raw in md.split('\n'):
        s = raw.strip()
        if s.startswith('```') or re.match(r'^〔本章(约|参考)', s): continue
        if s.startswith('## ') and not titled: titled = True; continue
        if s.startswith('|'):
            if lst or olst or quote: flush()
            tbl.append(s); continue
        elif tbl: flush()
        if not s or re.fullmatch(r'[-*]{3,}', s):
            if quote: flush()
            continue
        m = re.match(r'^#{2,4}\s+(.*)', s)
        if m:
            close(); t = m.group(1).replace('**', ''); mm = re.match(r'^◆\s*(.*)', t)
            out.append(f'<h2 class="sec"><span class="dia">◆</span>{inline(mm.group(1))}</h2>' if mm else f'<h2 class="sec">{inline(t)}</h2>')
            continue
        if s.startswith('**带走的话'):
            close(); t = re.sub(r'^\*\*带走的话[：:]\*\*\s*', '', s)
            out.append(f'<p class="takeaway"><span class="tk-l">带走的话</span><br><strong>{inline(t)}</strong></p>'); continue
        if s.startswith('**两行小账') or s.startswith('**想一想'):
            close(); mode = 1
            out.append('<div class="ledger"><span class="lt">%s</span>' % ('两行小账' if '两行' in s else '想一想')); continue
        m = re.match(r'^>\s?(.*)', s)
        if m:
            if lst or olst: flush()
            quote.append(m.group(1)); continue
        m = re.match(r'^[-*·]\s+(.*)', s)
        if m:
            if olst or quote: flush()
            lst.append(m.group(1)); continue
        m = re.match(r'^(\d+)[.、．]\s*(.*)', s)
        if m:
            if lst or quote: flush()
            olst.append(m.group(2)); continue
        flush()
        if mode: close()
        out.append(f'<p>{inline(s)}</p>')
    close()
    return '\n'.join(out)

def rd(f): return open(os.path.join(B7, 'out', f), encoding='utf-8').read()
def title_of(md): return re.search(r'^##\s+(.*)$', md, re.M).group(1).strip()

secs, toc = [], []
k = 0
def nid():
    global k; k += 1; return 's%d' % k
i = nid()
secs.append(f'<section class="front-sec" id="{i}"><h1 class="front-title">作者介绍</h1><div class="rule"></div>' + ''.join(f'<p>{inline(p)}</p>' for p in META['author']) + '</section>')
toc.append(('f', '作者介绍', i))
for f in ['ch00a-前言.md', 'ch00b-导读.md']:
    md = rd(f); t = title_of(md); p = t.split('　'); i = nid()
    secs.append(f'<section class="front-sec" id="{i}"><h1 class="front-title">{inline(p[0])}</h1>' + (f'<div class="fs-sub">{inline("　".join(p[1:]))}</div>' if len(p) > 1 else '') + '<div class="rule"></div>' + body(md) + '</section>')
    toc.append(('f', t, i))
for n in range(1, 23):
    if n in PARTS:
        lab, name, paras = PARTS[n]; i = nid()
        secs.append(f'<section class="part" id="{i}"><div class="part-label">{lab}</div><h1 class="part-title">{inline(name)}</h1><div class="rule"></div><div class="part-intro"><div class="bianxu">编　序</div>' + ''.join(f'<p>{inline(p)}</p>' for p in paras) + '</div></section>')
        toc.append(('p', f'{lab}　{name}', i))
    md = rd(f'ch{n:02d}.md'); t = title_of(md); ct = re.sub(r'^第\s*\d+\s*章\s*', '', t); i = nid()
    q = f'<blockquote>\n<p>这一章的问题：{inline(Q[n])}</p>\n</blockquote>' if n in Q else ''
    secs.append(f'<div class="chapter" id="{i}"><div class="chap-label">第 {n} 章</div><h2 class="chap-title">{inline(ct)}</h2><div class="rule"></div></div>{q}\n' + body(md))
    toc.append(('c', f'第 {n} 章　{ct}', i))
for f in ['ch23-结语.md', 'ch24-附录一.md', 'ch25-附录二.md', 'ch26-附录三.md', 'ch27-参考书目.md', 'ch28-后记.md']:
    md = rd(f); t = title_of(md); p = t.split('　'); i = nid()
    secs.append(f'<section class="back-sec" id="{i}"><h1 class="front-title">{inline(p[0])}</h1>' + (f'<div class="fs-sub">{inline("　".join(p[1:]))}</div>' if len(p) > 1 else '') + '<div class="rule"></div>' + body(md) + '</section>')
    toc.append(('f', t, i))

han = sum(len(re.findall(r'[一-鿿]', open(f, encoding='utf-8').read())) for f in glob.glob(B7 + '/out/*.md'))
bar = (f'<body><div id="prog"></div>\n<div class="bar"><a href="/books/m/{NO}/">← 书籍详情</a><a href="/books/m/{NO}/read.html">在线翻页</a>'
       f'<a href="/books/m/{NO}/{SLUG}-print.pdf?v={V}" target="_blank" rel="noopener">PDF</a><span class="sp"></span><button id="fs">字号</button><button id="th">夜间</button></div>\n<div class="wrap">\n')
hero = (f'<div class="hero"><img src="/books/m/{NO}/cover.jpg?v={V}" alt="封面"><h1>易</h1><p>符号的变化，不是符号的发生</p>'
        f'<p style="color:var(--dim);margin-top:.5rem">王德生 著 · 德麦国际专著第 {NO} 号 · ISBN 979-8-90690-704-2 · 约 {han/10000:.1f} 万字</p></div>\n')
tc = '<details class="toc" open><summary>目录（作者介绍 · 前言 · 导读 · 八编二十二章 · 结语 · 附录三件 · 参考书目 · 后记）</summary><ul>' + \
     ''.join(f'<li class="{c}"><a href="#{i}">{inline(t)}</a></li>' for c, t, i in toc) + '</ul></details>\n'
foot = f'<div class="foot">德麦国际出版社 · Demai International Press · <a href="/books/">专著书架</a> · <a href="/books/m/{NO}/">书籍详情</a></div>\n</div>\n'
page = head + bar + hero + tc + '\n'.join(secs) + '\n' + foot + tail_script
open(OUT, 'w', encoding='utf-8').write(page)
json.dump({'han': han, 'toc': [(c, t, i) for c, t, i in toc]}, open(B7 + '/site/text-meta.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('ok', OUT, len(page), 'han', han, 'sections', k)
