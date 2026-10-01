#!/usr/bin/env python3
"""第 274 号《逍遥是怎样长出来的》：作者来稿 DOCX → 分编 Markdown 底稿（机械规范化一遍）。

只做不改意思的机械工作：拆分前置／八编／结语／后置；引号统一为「」『』；数字与汉字间加半角空格；
章号交叉引用改阿拉伯数字（第三十章 → 第 30 章）；◆ 小节题统一为「◆ 一、」；本章小账改系列小账块。
文字打磨在此之后逐编人工进行，打磨稿直接覆盖本脚本的产物（勿再运行，免得冲掉打磨）。

用法：python3 convert.py SOURCE.docx OUTDIR
"""
import re
import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

CNUM = {'〇': 0, '零': 0, '一': 1, '二': 2, '两': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}


def cn2int(s):
    if not s:
        return None
    if '十' not in s:
        if len(s) == 1 and s in CNUM:
            return CNUM[s]
        return None
    a, _, b = s.partition('十')
    if a and a not in CNUM or b and b not in CNUM:
        return None
    return (CNUM[a] if a else 1) * 10 + (CNUM[b] if b else 0)


CN = '[一二三四五六七八九十两]{1,3}'


def chap_refs(t):
    # 第三十至三十三章、第十九、二十章、第七至十一章、第五、十二至十七章
    def rep(m):
        inner = m.group(1)
        parts = re.split(r'([至、—])', inner)
        out = []
        for p in parts:
            if p in '至、—':
                out.append(p)
            else:
                n = cn2int(p)
                if n is None:
                    return m.group(0)
                out.append(str(n))
        return '第 ' + ''.join(out) + ' 章'
    return re.sub(r'第((?:%s)(?:[至、—](?:%s))*)章' % (CN, CN), rep, t)


def years(t):
    def rep(m):
        return ''.join(str(CNUM[c]) for c in m.group(1)) + '年'
    return re.sub(r'([〇一二三四五六七八九]{4})年', rep, t)


def quotes(t):
    t = t.replace('⁠', '')
    # 只把包着汉字的弯引号换成直角引号；纯外文篇名保留“”
    def dq(m):
        inner = m.group(1)
        return '「%s」' % inner if re.search(r'[一-鿿]', inner) else m.group(0)
    t = re.sub(r'“([^“”]*)”', dq, t)
    t = re.sub(r'‘([^‘’]*)’', lambda m: '『%s』' % m.group(1) if re.search(r'[一-鿿]', m.group(1)) else m.group(0), t)
    # 「」里的「」改『』
    out, depth = [], 0
    for ch in t:
        if ch == '「':
            out.append('「' if depth % 2 == 0 else '『'); depth += 1
        elif ch == '」':
            depth -= 1; out.append('」' if depth % 2 == 0 else '』')
        else:
            out.append(ch)
    return ''.join(out)


def spacing(t):
    t = re.sub(r'([一-鿿])([0-9A-Za-z])', r'\1 \2', t)
    t = re.sub(r'([0-9A-Za-z%])([一-鿿])', r'\1 \2', t)
    return t


def norm(t):
    t = t.replace('\n', '').strip()
    t = years(t)
    t = chap_refs(t)
    t = quotes(t)
    t = spacing(t)
    t = t.replace('【', '〔').replace('】', '〕')
    return t


def sec_title(t):
    t = t.lstrip('◆').strip()
    m = re.match(r'^([一二三四五六七八九十]+)[　 ]+(.*)$', t)
    return '### ◆ %s、%s' % (m[1], m[2]) if m else '### ◆ ' + t


def ledger(lines):
    out = ['> **小账**', '>']
    for i, l in enumerate(lines):
        m = re.match(r'^(.{3,14}?)？(.*)$', l)
        lab = ['松开了什么', '还须查什么'][min(i, 1)]
        body = m[2].strip() if m else l
        out += ['> %s：%s' % (lab, body), '>']
    return '\n'.join(out[:-1])


def main():
    src, outdir = Path(sys.argv[1]), Path(sys.argv[2])
    d = Document(src)
    items = []
    for el in d.element.body:
        if el.tag == qn('w:p'):
            p = Paragraph(el, d)
            items.append((p.style.name, p.text))
        elif el.tag == qn('w:tbl'):
            items.append(('TABLE', Table(el, d)))
    files = {}
    cur = None
    buf = []
    pend_part = None
    summary = []
    chapno = None

    def start(name):
        nonlocal cur
        cur = name
        files.setdefault(name, [])

    def emit(s):
        files[cur].append(s)

    def flush_summary():
        nonlocal summary
        if summary:
            emit(ledger(summary)); summary = []

    started = False
    for style, t in items:
        if style == 'TABLE':
            rows = [[norm(c.text) for c in r.cells] for r in t.rows]
            emit('| 字段 | 内容 |\n|---|---|\n' + '\n'.join('| %s | %s |' % (a, b) for a, b in rows))
            continue
        t = t.strip()
        if style == 'FrontTitle' and t == '出版信息':
            started = True
            start('front/00-前置.md')
            emit('## 出版信息')
            continue
        if not started or not t:
            continue
        if style in ('BookTOC', 'ChapterNumeral'):
            continue
        if style == 'FrontTitle':
            if t == '目录':
                cur = None
                continue
            emit('---\n\n## ' + norm(t)); continue
        if cur is None and style != 'Heading 1':
            continue
        if style == 'PartLabel':
            flush_summary()
            pend_part = t.replace(' ', ''); continue
        if style == 'ChapterLabel':
            m = re.match(r'第\s*(\d+)\s*章', t)
            if m:
                flush_summary(); chapno = int(m[1])
            continue
        if style == 'Heading 1':
            flush_summary()
            t = t.replace('\n', '')
            if t.startswith('导论'):
                start('front/00-前置.md'); emit('---\n\n## ' + norm(t)); continue
            if pend_part:
                n = '一二三四五六七八'.index(pend_part[1]) + 1
                start('parts/%02d-%s.md' % (n, pend_part)); emit('# %s　%s' % (pend_part, norm(t)))
                pend_part = None; continue
            if chapno is not None:
                emit('\n---\n\n## 第 %d 章　%s' % (chapno, norm(t))); chapno = None; continue
            if t.startswith('结语'):
                start('back/09-结语.md'); emit('# ' + norm(t)); continue
            if t.startswith('参考书目'):
                start('back/10-后置.md'); emit('# 参考书目'); continue
            if t.startswith('附录'):
                emit('\n---\n\n# 附录\n\n<!-- 原题：%s -->' % norm(t)); continue
            if t.startswith('后记'):
                emit('\n---\n\n# 后记　' + norm(t.split('：', 1)[1])); continue
            emit('# ' + norm(t)); continue
        if style == 'Heading 2':
            flush_summary(); emit(sec_title(norm(t))); continue
        if style == 'SummaryHeading':
            flush_summary(); continue
        if style == 'SummaryBody':
            summary.append(norm(t)); continue
        if style == 'SourceNote':
            s = norm(t)
            if not s.startswith('〔'):
                s = '〔%s〕' % s
            emit(s); continue
        if style == 'Colophon' and re.match(r'^\d+\.', t):
            emit(norm(t)); continue
        emit(norm(t))
    flush_summary()
    for name, chunks in files.items():
        p = outdir / name
        p.parent.mkdir(parents=True, exist_ok=True)
        text = '\n\n'.join(chunks)
        text = re.sub(r'\n{3,}', '\n\n', text).strip() + '\n'
        p.write_text(text)
        print(len(re.findall(r'[一-鿿]', text)), name)


if __name__ == '__main__':
    main()
