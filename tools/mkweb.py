#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mkweb.py —— 《课堂的智慧》网页版全书（第三读）
把 out/book_clean.md 按一级标题切成一页一节，生成 /books/m/57/text/ 下的页面与索引。
段落与表格都是真段真表，不从 PDF 抽行。
"""
import re, os, json, html

MD = '/home/claude/ktzh/out/book_clean.md'
OUT = '/home/claude/site/public/books/m/57/text'
BOOK = '/books/m/57'

CSS = """
:root{--bg:#0B0E12;--panel:#111820;--ink:#E7E3DB;--mute:#8C97A3;--cy:#5FD3E0;--am:#FFC24A;--line:#1E2730}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:"Noto Serif SC","Songti SC",Georgia,serif;line-height:1.95;-webkit-text-size-adjust:100%}
::selection{background:rgba(95,211,224,.28)}
a{color:var(--cy);text-decoration:none}
nav.top{position:sticky;top:0;z-index:9;background:rgba(11,14,18,.93);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.topin{max-width:820px;margin:0 auto;padding:12px 22px;display:flex;gap:18px;flex-wrap:wrap;font-size:13.5px}
.wrap{max-width:820px;margin:0 auto;padding:34px 22px 90px}
.kicker{font-size:11px;letter-spacing:.34em;color:var(--cy);margin-bottom:14px}
h1.bt{font-size:clamp(26px,4.6vw,40px);font-weight:800;letter-spacing:.06em;line-height:1.4}
.sub{color:var(--mute);margin-top:10px;font-size:15px}
.cmeta{color:var(--mute);font-size:13px;margin-top:14px;letter-spacing:.03em}
.acts{display:flex;gap:10px;flex-wrap:wrap;margin:26px 0 6px}
.btn{display:inline-block;padding:10px 20px;border:1px solid var(--line);border-radius:3px;font-size:14px;background:var(--panel)}
.btn.pri{background:var(--cy);color:#08252A;border-color:var(--cy);font-weight:700}
.intro{color:var(--mute);font-size:14.5px;margin-top:22px;line-height:2}
.grp{margin:34px 0 8px;font-size:12px;letter-spacing:.26em;color:var(--am)}
a.row{display:flex;gap:14px;align-items:baseline;padding:11px 4px;border-bottom:1px solid var(--line);color:var(--ink)}
a.row:hover{background:rgba(95,211,224,.06)}
a.row .n{width:34px;color:var(--cy);font-size:13px;flex:none}
a.row .ti{flex:1}
a.row .wc{color:var(--mute);font-size:12.5px;flex:none}
h1.ct{font-size:clamp(22px,3.6vw,31px);font-weight:800;line-height:1.5;margin:6px 0 22px;letter-spacing:.04em}
h2{font-size:clamp(17px,2.4vw,20px);font-weight:700;margin:38px 0 10px;letter-spacing:.03em;color:#F2EFE8}
h3{font-size:16px;font-weight:700;margin:26px 0 8px;color:#F2EFE8}
p{margin:0 0 15px;text-align:justify}
blockquote{margin:20px 0;padding:14px 18px;background:var(--panel);border-left:2px solid var(--am);color:#DCD7CE;font-size:15px}
blockquote p:last-child{margin:0}
ul{margin:0 0 15px 22px}li{margin:0 0 7px}
table{width:100%;border-collapse:collapse;margin:20px 0;font-size:13.5px;display:block;overflow-x:auto}
th,td{border:1px solid var(--line);padding:8px 10px;vertical-align:top;text-align:left}
th{background:#16202A;color:var(--cy);font-weight:700;white-space:nowrap}
hr{border:0;border-top:1px solid var(--line);margin:30px 0}
.pager{display:flex;justify-content:space-between;gap:14px;margin-top:52px;padding-top:20px;border-top:1px solid var(--line);font-size:14px}
.foot{margin-top:34px;color:var(--mute);font-size:12.5px}
b,strong{color:#FFF6E6}
"""


def esc(s):
    return html.escape(s, quote=False)


def inline(s):
    s = esc(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'\[\[(.+?)\]\]', r'\1', s)
    s = s.replace('&lt;br&gt;', '<br>')
    return s


def md2html(md):
    out, i, lines = [], 0, md.split('\n')
    while i < len(lines):
        l = lines[i].rstrip()
        if not l.strip():
            i += 1; continue
        if re.fullmatch(r'-{3,}', l.strip()):
            out.append('<hr>'); i += 1; continue
        m = re.match(r'^### (.+)$', l)
        if m:
            out.append(f'<h3>{inline(m.group(1))}</h3>'); i += 1; continue
        m = re.match(r'^## (.+)$', l)
        if m:
            out.append(f'<h2>{inline(m.group(1))}</h2>'); i += 1; continue
        if l.startswith('|') and i + 1 < len(lines) and re.match(r'^\|[\s:\-|]+\|$', lines[i + 1]):
            blk = []
            while i < len(lines) and lines[i].startswith('|'):
                blk.append(lines[i]); i += 1
            rows = [r.split('|')[1:-1] for r in blk if not re.match(r'^\|[\s:\-|]+\|$', r)]
            t = ['<table>']
            for ri, cells in enumerate(rows):
                tag = 'th' if ri == 0 else 'td'
                t.append('<tr>' + ''.join(f'<{tag}>{inline(c.strip())}</{tag}>' for c in cells) + '</tr>')
            t.append('</table>')
            out.append(''.join(t)); continue
        if l.startswith('> '):
            q = []
            while i < len(lines) and (lines[i].startswith('> ') or lines[i].strip() == '>'):
                if lines[i].strip() != '>':
                    q.append(f'<p>{inline(lines[i][2:])}</p>')
                i += 1
            out.append('<blockquote>' + ''.join(q) + '</blockquote>'); continue
        if l.startswith('- '):
            u = []
            while i < len(lines) and lines[i].startswith('- '):
                u.append(f'<li>{inline(lines[i][2:])}</li>'); i += 1
            out.append('<ul>' + ''.join(u) + '</ul>'); continue
        out.append(f'<p>{inline(l)}</p>'); i += 1
    return '\n'.join(out)


def slugify(title, n):
    t = title.strip()
    m = re.match(r'^第([一二三四五六七八九十]+)章', t)
    if m:
        CN = '一二三四五六七八九十'
        x = m.group(1)
        if x == '十': v = 10
        elif x.startswith('十'): v = 10 + CN.index(x[1]) + 1
        elif '十' in x:
            a, b = x.split('十'); v = (CN.index(a) + 1) * 10 + (CN.index(b) + 1 if b else 0)
        else: v = CN.index(x) + 1
        return 'c%02d' % v
    key = {'前　言': 'qy', '导　论': 'dl', '结　语': 'jy', '后　记': 'hj'}
    for k, v in key.items():
        if t.startswith(k):
            return v
    if t.startswith('附录'):
        cn = '一二三四五六七'
        return 'ap%d' % (cn.index(t[2]) + 1)
    if t.startswith('第') and '编小结' in t:
        return 'b%ds' % ('一二三四'.index(t[1]) + 1)
    if t.startswith('第') and '编' in t[:3]:
        return 'b%d' % ('一二三四'.index(t[1]) + 1)
    if t.startswith('作者简介'):
        return 'au'
    return 'x%02d' % n


def page(title, body, prev, nxt, wc):
    p = f'<a href="../{prev[0]}/">← {esc(prev[1])}</a>' if prev else '<span></span>'
    n = f'<a href="../{nxt[0]}/">{esc(nxt[1])} →</a>' if nxt else '<span></span>'
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · 课堂的智慧 | 阳涌</title>
<meta name="description" content="{esc(title)}——阳涌《课堂的智慧》网页版全书。">
<style>{CSS}</style></head><body>
<nav class="top"><div class="topin"><a href="/browse/">SDE Universes</a><a href="{BOOK}/">← 专著导读页</a><a href="../">全书目录</a><a href="{BOOK}/read.html">翻书版</a></div></nav>
<div class="wrap">
<h1 class="ct">{esc(title)}</h1>
{body}
<div class="pager">{p}{n}</div>
<div class="foot">《课堂的智慧》· 阳涌 著 · 德麦国际出版社 · ISBN 978-1-970820-95-9 · 本页 {wc:,} 字 · <a href="/students/yang-yong/classroom-wisdom/">阳涌学员专栏</a></div>
</div></body></html>'''


def main():
    md = open(MD, encoding='utf-8').read()
    hs = [(m.start(), m.group(1).strip()) for m in re.finditer(r'^# (.+)$', md, re.M)]
    secs = []
    for i, (p, t) in enumerate(hs):
        e = hs[i + 1][0] if i + 1 < len(hs) else len(md)
        body = md[p:e].split('\n', 1)[1]
        if t == '课堂的智慧':
            continue
        secs.append((t, body))

    slugs, seen = [], {}
    for k, (t, b) in enumerate(secs, 1):
        s = slugify(t, k)
        while s in seen:
            s += 'b'
        seen[s] = 1
        slugs.append(s)

    os.makedirs(OUT, exist_ok=True)
    nav = []
    for k, ((t, b), s) in enumerate(zip(secs, slugs)):
        wc = len(re.findall(r'[\u4e00-\u9fff]', b))
        prev = (slugs[k - 1], secs[k - 1][0]) if k else None
        nxt = (slugs[k + 1], secs[k + 1][0]) if k + 1 < len(secs) else None
        os.makedirs(f'{OUT}/{s}', exist_ok=True)
        open(f'{OUT}/{s}/index.html', 'w', encoding='utf-8').write(
            page(t, md2html(b), prev, nxt, wc))
        nav.append((s, t, wc))

    # 索引
    tot = sum(w for _, _, w in nav)
    rows, grp = [], None
    for s, t, w in nav:
        g = ('卷首' if s in ('qy', 'dl') else
             '第一编 · 对象' if s in ('b1', 'c01', 'c02', 'c03', 'b1s') else
             '第二编 · 运行' if s in ('b2', 'c04', 'c05', 'c06', 'b2s') else
             '第三编 · 动力' if s in ('b3', 'c07', 'c08', 'c09', 'b3s') else
             '第四编 · 合论' if s in ('b4', 'c10', 'c11', 'c12', 'c13') else
             '卷末' if s in ('jy', 'hj', 'au') else '附录')
        if g != grp:
            rows.append(f'<div class="grp">{g}</div>'); grp = g
        num = re.match(r'^第([一二三四五六七八九十]+)章', t)
        n = num.group(1) if num else '—'
        rows.append(f'<a class="row" href="{s}/"><span class="n">{n}</span>'
                    f'<span class="ti">{esc(t)}</span><span class="wc">{w:,} 字</span></a>')

    idx = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>全书目录 · 课堂的智慧 | 阳涌</title>
<meta name="description" content="阳涌《课堂的智慧》网页版全书目录：四编十三章、七附录，约 {tot//10000} 万字，可检索、可选句、手机可长读。">
<style>{CSS}</style></head><body>
<nav class="top"><div class="topin"><a href="/browse/">SDE Universes</a><a href="{BOOK}/">← 专著导读页</a><a href="/students/yang-yong/classroom-wisdom/">阳涌学员专栏</a></div></nav>
<div class="wrap">
<header>
<div class="kicker">德麦国际出版社 · 专著第 57 号 · 网页排版版</div>
<h1 class="bt">课堂的智慧</h1>
<div class="sub">课堂内生对象、运行条件与失效动力的可证伪理论纲领</div>
<div class="cmeta">阳涌 著 · 前言·导论·四编十三章·结语·后记·七附录 · 约 {tot:,} 字 · ISBN 978-1-970820-95-9</div>
<div class="acts"><a class="btn pri" href="qy/">从头读起 →</a><a class="btn" href="{BOOK}/read.html">翻书版（260 页）</a><a class="btn" href="{BOOK}/Classroom-Wisdom.pdf">下载 PDF</a></div>
<p class="intro">这是《课堂的智慧》的<b>网页排版版</b>：正文由源文重新排版为可检索、可选句、可在手机上长读的网页，段落与表格均为真段真表，不是从 PDF 抽出来的行。与另两种读法的分别是——<b>翻书版</b>保留纸书页码与版式，适合引用与核对；<b>网页版</b>适合通读、检索与选句发问；<b>三章精读</b>是从书里抽出的三篇独立长文。</p>
</header>
{''.join(rows)}
<div class="foot">全书 {len(nav)} 个条目 · 约 {tot:,} 汉字 · 本书按<b>一部专著抵十篇论文</b>计入 <a href="/students/yang-yong/works/">阳涌作品集</a>。</div>
</div></body></html>'''
    open(f'{OUT}/index.html', 'w', encoding='utf-8').write(idx)
    print(f'网页版全书：{len(nav)} 页 · {tot:,} 汉字 → {OUT}')
    print('  ' + ' '.join(s for s, _, _ in nav))


main()
