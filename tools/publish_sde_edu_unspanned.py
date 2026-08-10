#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 /home/claude/edu/paper.md 生成 /sde-education/unspanned-capability/index.html
模板取自同栏 discovery-to-genesis（三读骨架、样式、脚本原样复用）。"""
import html
import io
import os
import re
import sys

ROOT = '/home/claude/site/public/sde-education'
TPL = os.path.join(ROOT, 'discovery-to-genesis/index.html')
SRC = '/home/claude/edu/paper.md'
SLUG = 'unspanned-capability'
OUT = os.path.join(ROOT, SLUG, 'index.html')
PDF = f'/sde-education/pdf/{SLUG}.pdf'

TITLE = '它读不出来的，它也造不出来'
SUB = '论教育的产物不是能力而是不可分辨性，及一套判定装置的边界如何同时切出一类它在原则上长不出来的能力'
DESC = ('工程学、生物学与艺术学各持一条互不相容的强主张，而三家共同假定「学到了什么」是人身上的属性。'
        '本文提出：教育的产物是不可分辨性；一套判定口径装上的那一刻，同时切出一类它既读不出也造不出的能力。'
        '含两次预注册真跑与五条对本文不利的结果。')


# ── markdown → html ────────────────────────────────────────
def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = t.replace('\\|', '|')
    return t


def md2html(md):
    lines = md.split('\n')
    out, i, sec = [], 0, 0
    toc = []
    while i < len(lines):
        ln = lines[i]
        if ln.startswith('## '):
            sec += 1
            t = ln[3:].strip()
            aid = f'c{sec}'
            toc.append((aid, t))
            out.append(f'<h2 id="{aid}">{inline(t)}</h2>')
            i += 1
        elif ln.startswith('### '):
            out.append(f'<h3>{inline(ln[4:].strip())}</h3>')
            i += 1
        elif ln.startswith('|'):
            tbl = []
            while i < len(lines) and lines[i].startswith('|'):
                tbl.append(lines[i])
                i += 1
            rows = [[c.strip() for c in r.strip().strip('|').split('|')] for r in tbl
                    if not re.match(r'^\|[\s\-:|]+\|$', r)]
            if rows:
                h = '<table class="tbl"><thead><tr>' + ''.join(
                    f'<th>{inline(c)}</th>' for c in rows[0]) + '</tr></thead><tbody>'
                for r in rows[1:]:
                    h += '<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>'
                out.append(h + '</tbody></table>')
        elif re.match(r'^\d+\.\s', ln) or ln.startswith('- '):
            ordered = bool(re.match(r'^\d+\.\s', ln))
            items = []
            while i < len(lines) and (re.match(r'^\d+\.\s', lines[i]) or lines[i].startswith('- ')
                                      or (lines[i].startswith('    ') and items)):
                s2 = lines[i]
                if s2.startswith('    ') and items:
                    items[-1] += ' ' + s2.strip()
                else:
                    items.append(re.sub(r'^(\d+\.|-)\s+', '', s2))
                i += 1
            tag = 'ol' if ordered else 'ul'
            out.append(f'<{tag}>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + f'</{tag}>')
        elif ln.startswith('> '):
            blk = []
            while i < len(lines) and lines[i].startswith('> '):
                blk.append(lines[i][2:])
                i += 1
            out.append('<blockquote class="formula">' + inline(' '.join(blk)) + '</blockquote>')
        elif ln.strip() == '':
            i += 1
        else:
            para = [ln]
            i += 1
            while i < len(lines) and lines[i].strip() and not re.match(
                    r'^(#{2,3} |\||- |\d+\.\s|> )', lines[i]):
                para.append(lines[i])
                i += 1
            out.append('<p>' + inline(' '.join(para)) + '</p>')
    return '\n'.join(out), toc


def main():
    md = io.open(SRC, encoding='utf-8').read()
    body = md.split('**关键词**：', 1)[1]
    kw = body.split('\n', 1)[0].strip()
    rest = body.split('\n', 1)[1]
    # 英文块单独取出，放进正文末尾之前
    abstract = re.search(r'## 摘 要\n\n(.+?)\n\n\*\*关键词\*\*', md, re.S).group(1).strip()

    art, toc = md2html(rest)
    zh = len(re.findall(r'[\u4e00-\u9fff]', md))
    nref = len(re.findall(r'^\d+\. [A-Z]', md, re.M))

    tpl = io.open(TPL, encoding='utf-8').read()

    def cut(a, b):
        i, j = tpl.index(a), tpl.index(b)
        return tpl[:i], tpl[i:j + len(b)], tpl[j + len(b):]

    h = tpl
    # 头部
    h = h.replace(
        '<title>教育：从发现到发生的革命——传道模式的八环链，与它的八处裂缝 | SDE教育学 | SDE Universes</title>',
        f'<title>{TITLE}——{SUB} | SDE教育学 | SDE Universes</title>')
    h = re.sub(r'<meta name="description" content="[^"]*">',
               f'<meta name="description" content="{DESC}">', h, count=1)
    h = h.replace('<div class="eyebrow"><a href="/sde-education/">SDE教育学入门</a> · 第一讲</div>',
                  '<div class="eyebrow"><a href="/sde-education/">SDE教育学</a> · 论文</div>')
    h = h.replace('<h1 class="art-title">教育：从发现到发生的革命</h1>',
                  f'<h1 class="art-title">{TITLE}</h1>')
    h = h.replace('<p class="art-sub">传道模式的八环链，与它的八处裂缝</p>',
                  f'<p class="art-sub">{SUB}</p>')
    h = re.sub(r'<div class="art-meta">.*?</div>',
               f'<div class="art-meta">王德生 · 德麦国际 SDE 学派 · SDE教育学 · 2026年8月10日 · '
               f'约 {zh:,} 字 · {nref} 条参考文献 · 三种阅读模式</div>', h, count=1, flags=re.S)

    # 摘要 / 关键词 / 目录 / 正文
    a, _, c = cut('<div class="abs">', '</div></div>')
    newabs = f'<div class="abs"><div class="l">摘 要</div><p>{inline(abstract)}</p></div>'
    h_a = h[:h.index('<div class="abs">')]
    h_c = h[h.index('<div class="kw">'):]
    h = h_a + newabs + '\n  ' + h_c

    h = re.sub(r'<div class="kw">.*?</div>', f'<div class="kw">关键词：{kw}</div>', h, count=1, flags=re.S)

    toc_html = '<div class="toc"><div class="l">目 录</div>' + '\n'.join(
        f'<a href="#{i}">{inline(t)}</a>' for i, t in toc) + '</div>'
    i0 = h.index('<div class="toc">')
    i1 = h.index('<article>')
    h = h[:i0] + toc_html + '\n  ' + h[i1:]

    j0 = h.index('<article>')
    j1 = h.index('</article>') + len('</article>')
    h = h[:j0] + '<article>\n' + art + '\n</article>' + h[j1:]

    # PDF 路径（并修掉模板里 PDF_URL 被第二次 var 覆盖的老 bug）
    h = h.replace('/sde-education/pdf/discovery-to-genesis.pdf', PDF)
    h = h.replace('var PDF_URL="/education/ai-era/pdf/adjudication-outsourcing.pdf";\n', '')

    # 页脚导航
    h = re.sub(r'<div class="cl">.*?</div>',
               '<div class="cl"><a href="/sde-education/">← SDE教育学</a>'
               '<a href="/sde-education/discovery-to-genesis/">第一讲 · 从发现到发生</a>'
               '<a href="/education/">教育发生学</a><a href="/">首页</a></div>',
               h, count=1, flags=re.S)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    io.open(OUT, 'w', encoding='utf-8').write(h)
    print(f'写出 {OUT}  {len(h):,} 字节 · 正文 {zh:,} 汉字 · {len(toc)} 节 · {nref} 条文献')


if __name__ == '__main__':
    main()
