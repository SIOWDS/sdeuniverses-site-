#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 /home/claude/edu 下四篇同题论文生成 /sde-education/<slug>/ 页面。
模板取自同栏 discovery-to-genesis。"""
import html
import io
import os
import re

ROOT = '/home/claude/site/public/sde-education'
TPL = os.path.join(ROOT, 'discovery-to-genesis/index.html')
SRC = '/home/claude/edu'

PAPERS = [
    dict(md='paper.md', slug='unspanned-capability',
         title='它读不出来的，它也造不出来',
         sub='论教育的产物不是能力而是不可分辨性，及一套判定装置的边界如何同时切出一类它在原则上长不出来的能力',
         kw='不可分辨性；未张成能力；张成重合率；判定装置；空无课程；教育本体',
         desc='工程学、生物学与艺术学三家共同假定「学到了什么」是人身上的属性。本文提出：教育的产物是不可分辨性；一套判定口径装上的那一刻，同时切出一类它既读不出也造不出的能力。含两次预注册真跑与五条对本文不利的结果。'),
    dict(md='那道题还没有被出出来_教育是什么.md', slug='unasked-question',
         title='那道题还没有被出出来',
         sub='论教育的产物是一批由做法之差定义、而尚未被任何人出出来的题目，及为什么一份全对的记录几乎排除不掉任何做法',
         kw='界题；分法未定率；做法集合；等价类；混合策略模型；教育本体',
         desc='符号学、逻辑学与数学三家共同假定「学会了」是学习者的一项属性。本文提出：教育是与已有表现相容的做法集合的收缩，而收缩到哪一支只在尚未被出出来的那批题上显形。含分数减法 Q 矩阵的完整实算与四条形式命题。'),
    dict(md='同许__教育是什么.md', slug='tongxu-indiscernible-family',
         title='同许：教育不是能力的传递、轨道的分岔，也不是位置的分配',
         sub='论一族在既有尺子上分不开的进程，及其分离视界',
         kw='同许；带宽；同许率；分离视界；差别阈限；口径',
         desc='混沌学、舞蹈学与地理学三家共同假定教育的成果是一样有归属的东西。本文提出：教育是对同许族的一次改形。含两份公开学生成绩数据上的预注册真跑，三条假设两条被判伪，五处不利结果原样写入。'),
    dict(md='教育是什么_不计的那一遍.md', slug='uncounted-run',
         title='不计的那一遍',
         sub='论教育由一批必须不进任何账的重复构成，而三套计数装置各自都记得平',
         kw='不计遍；零计比；首计序；计数装置；无酬劳动核算；教育本体',
         desc='戏剧学、经济学与法律学三家共同假定「一次教育发生了没有」在原则上可裁定。本文提出：教育是一批必须不进任何账才承担构成功能的重复，与三套计数装置之间的存量差。含 8,400 个公开拉取请求的预注册真跑，两条假设均未命中。'),
]


def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'(?<![\w*])\*([^*\n]+?)\*(?![\w*])', r'<i>\1</i>', t)
    return t.replace('\\|', '|')


def md2html(md):
    lines, out, i, sec, toc = md.split('\n'), [], 0, 0, []
    while i < len(lines):
        ln = lines[i]
        m = re.match(r'^(#{2,3}) (.+)$', ln)
        if m and len(m.group(1)) == 2:
            sec += 1
            t = m.group(2).strip()
            toc.append((f'c{sec}', t))
            out.append(f'<h2 id="c{sec}">{inline(t)}</h2>')
            i += 1
            continue
        if m:
            out.append(f'<h3>{inline(m.group(2).strip())}</h3>')
            i += 1
            continue
        # 《同许》用 **整行粗体** 当节标题
        m2 = re.match(r'^\*\*([一二三四五六七八九十]{1,3}[　 ].{2,42})\*\*\s*$', ln)
        if m2:
            sec += 1
            t = m2.group(1).strip()
            toc.append((f'c{sec}', t))
            out.append(f'<h2 id="c{sec}">{inline(t)}</h2>')
            i += 1
            continue
        m3 = re.match(r'^\*\*(摘要|摘 要|关键词|参考文献|注 释|注释)\*\*\s*$', ln)
        if m3:
            sec += 1
            toc.append((f'c{sec}', m3.group(1)))
            out.append(f'<h2 id="c{sec}">{inline(m3.group(1))}</h2>')
            i += 1
            continue
        if ln.startswith('|'):
            tbl = []
            while i < len(lines) and lines[i].startswith('|'):
                tbl.append(lines[i]); i += 1
            rows = [[c.strip() for c in r.strip().strip('|').split('|')] for r in tbl
                    if not re.match(r'^\|[\s\-:|]+\|$', r)]
            if rows:
                h = '<table class="tbl"><thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in rows[0]) + '</tr></thead><tbody>'
                for r in rows[1:]:
                    h += '<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>'
                out.append(h + '</tbody></table>')
            continue
        if re.match(r'^\d+\.\s', ln) or ln.startswith('- '):
            ordered = bool(re.match(r'^\d+\.\s', ln))
            items = []
            while i < len(lines) and (re.match(r'^\d+\.\s', lines[i]) or lines[i].startswith('- ')
                                      or (lines[i].startswith('    ') and items)):
                if lines[i].startswith('    ') and items:
                    items[-1] += ' ' + lines[i].strip()
                else:
                    items.append(re.sub(r'^(\d+\.|-)\s+', '', lines[i]))
                i += 1
            tag = 'ol' if ordered else 'ul'
            out.append(f'<{tag}>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + f'</{tag}>')
            continue
        if ln.startswith('>'):
            blk = []
            while i < len(lines) and lines[i].startswith('>'):
                blk.append(lines[i].lstrip('>').strip()); i += 1
            paras, cur = [], []
            for x in blk:
                if x:
                    cur.append(x)
                elif cur:
                    paras.append(' '.join(cur)); cur = []
            if cur:
                paras.append(' '.join(cur))
            if len(paras) == 1 and len(paras[0]) < 160:
                out.append('<blockquote class="formula">' + inline(paras[0]) + '</blockquote>')
            else:
                out.append('<div class="refs-body">' + ''.join(
                    f'<p>{inline(x)}</p>' for x in paras) + '</div>')
            continue
        if not ln.strip():
            i += 1
            continue
        para = [ln]; i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r'^(#{2,3} |\||- |\d+\.\s|> |\*\*[一二三四五六七八九十]{1,3}[　 ])', lines[i]):
            para.append(lines[i]); i += 1
        out.append('<p>' + inline(' '.join(para)) + '</p>')
    return '\n'.join(out), toc


def build(p, tpl):
    md = io.open(os.path.join(SRC, p['md']), encoding='utf-8').read()
    zh = len(re.findall(r'[\u4e00-\u9fff]', md))
    nref = len(re.findall(r'^\d+\. [A-Z\u4e00-\u9fff]', md, re.M))
    nref = max(nref, len(re.findall(
        r'^>?\s*[A-Z\u4e00-\u9fff][^\n]{4,160}\((?:19|20)\d\d[a-z]?\)[.,]', md, re.M)))
    # 摘要：第一段中文摘要
    mm = re.search(r'(?:## 摘 要|\*\*摘要\*\*|\*\*摘 要\*\*)\s*\n+(.+?)\n', md)
    abstract = mm.group(1).strip() if mm else ''
    # 正文：从摘要之后开始，去掉重复的标题行
    body = md
    for cut in ['**关键词**：', '关键词　', '> 关键词']:
        if cut in body:
            body = body.split(cut, 1)[1]
            body = body.split('\n', 1)[1] if '\n' in body else body
            break
    art, toc = md2html(body)

    h = tpl
    h = re.sub(r'<title>.*?</title>', f'<title>{p["title"]} | SDE教育学 | SDE Universes</title>', h, count=1, flags=re.S)
    h = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{p["desc"]}">', h, count=1)
    h = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{p["title"]} | SDE教育学">', h, count=1)
    h = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{p["desc"][:110]}">', h, count=1)
    h = h.replace('https://sdeuniverses.com/sde-education/discovery-to-genesis/', f'https://sdeuniverses.com/sde-education/{p["slug"]}/')
    h = h.replace('<div class="eyebrow"><a href="/sde-education/">SDE教育学入门</a> · 第一讲</div>',
                  '<div class="eyebrow"><a href="/sde-education/">SDE教育学</a> · 同题四篇</div>')
    h = h.replace('<h1 class="art-title">教育：从发现到发生的革命</h1>', f'<h1 class="art-title">{p["title"]}</h1>')
    h = h.replace('<p class="art-sub">传道模式的八环链，与它的八处裂缝</p>', f'<p class="art-sub">{p["sub"]}</p>')
    h = re.sub(r'<div class="art-meta">.*?</div>',
               f'<div class="art-meta">王德生 · 德麦国际 SDE 学派 · SDE教育学 · 2026年8月10日 · 约 {zh:,} 字 · {nref} 条参考文献 · 三种阅读模式</div>',
               h, count=1, flags=re.S)
    i0 = h.index('<div class="abs">')
    i1 = h.index('<div class="kw">')
    h = h[:i0] + f'<div class="abs"><div class="l">摘 要</div><p>{inline(abstract)}</p></div>\n  ' + h[i1:]
    h = re.sub(r'<div class="kw">.*?</div>', f'<div class="kw">关键词：{p["kw"]}</div>', h, count=1, flags=re.S)
    toc_html = '<div class="toc"><div class="l">目 录</div>' + '\n'.join(f'<a href="#{a}">{inline(t)}</a>' for a, t in toc) + '</div>'
    h = h[:h.index('<div class="toc">')] + toc_html + '\n  ' + h[h.index('<article>'):]
    h = h[:h.index('<article>')] + '<article>\n' + art + '\n</article>' + h[h.index('</article>') + len('</article>'):]
    h = h.replace('/sde-education/pdf/discovery-to-genesis.pdf', f'/sde-education/pdf/{p["slug"]}.pdf')
    h = h.replace('var PDF_URL="/education/ai-era/pdf/adjudication-outsourcing.pdf";\n', '')
    sibs = ''.join(f'<a href="/sde-education/{q["slug"]}/">{q["title"][:12]}</a>' for q in PAPERS if q['slug'] != p['slug'])
    h = re.sub(r'<div class="cl">.*?</div>',
               f'<div class="cl"><a href="/sde-education/">← SDE教育学</a>{sibs}<a href="/">首页</a></div>',
               h, count=1, flags=re.S)
    out = os.path.join(ROOT, p['slug'], 'index.html')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    io.open(out, 'w', encoding='utf-8').write(h)
    print(f'  ✓ {p["slug"]:<28} {zh:>6} 汉字 · {len(toc):>2} 节 · {nref:>2} 文献 · {len(h):,} 字符')
    return zh, len(toc), nref


if __name__ == '__main__':
    tpl = io.open(TPL, encoding='utf-8').read()
    for p in PAPERS:
        build(p, tpl)
