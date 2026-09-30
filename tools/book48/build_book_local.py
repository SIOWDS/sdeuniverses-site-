#!/usr/bin/env python3
"""系列成书：Markdown 全稿 → 印刷版／阅读友好版 PDF（WeasyPrint）

用法：
  python build_book.py 全稿.md [--out 书名] [--preset current|peirce|schopenhauer]
                       [--edition print|reader|both] [--cover 封面.jpg] [--backcover 封底.jpg]
                       [--paper '#FCFAF4'] [--html-only] [--dump-css series.css]

预设（参数全表见 references/layout.md 第三节）：
  current       现行：拉康卷（第 201 号）、罗素卷（第 165 号）
  peirce        标杆：皮尔斯卷（第 133 号）；霞鹜文楷没装时退到楷体、宋体
  schopenhauer  叔本华卷（第 152 号）

稿件约定见 references/layout.md 第七节。要点：
  --- 元数据块 ---（title pretitle name subtitle author executor series_no isbn price words edition finished
                    statement（可多行） copyright runhead publisher trim）
  # 前言　副题 / # 导读 / # 导论　副题 / # 结语　副题 / # 参考书目 / # 附录 / # 附录一　题 / # 后记 / # 作者介绍
  # 第一编　编题（其后段落排在编首页）   # 上篇　题
  ## 第 1 章　章题   或   ## 第一章　章题
  ### ◆ 一、小节题（◆ 可省）
  【带走的话】…  【小账】…（连续几行并成一盒）  【想一想】…  【编序】…
  > 引语（整段加粗 = 判词块）   | 表 | 格 |   - 列表   1. 条目   **加粗**  *斜体*

目录分两遍排：第一遍找每个标题落在哪一页，第二遍把真页码写进目录。页码由脚本逐页写定，
与目录用同一个算法，不会出现拉康卷现行 PDF 那种目录页码全为「1」的情况。
"""
import argparse
import json as _json
import os as _os
TIGHT = _json.loads(_os.environ.get('TIGHT', '{}'))
import html
import re
import string
import sys
from pathlib import Path

SERIF = '"Noto Serif CJK SC", "Source Han Serif SC", "Songti SC", "SimSun", serif'
SANS = '"Noto Sans CJK SC", "Source Han Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif'
KAI = '"LXGW WenKai", "LXGW WenKai GB", "Kaiti SC", "STKaiti", "KaiTi", ' + SERIF

PRESETS = {
    'current': dict(
        name='现行（拉康卷、罗素卷）', paper='#FFFFFF', ink='#26241F', navy='#1F3A5F', gold='#B08A3C',
        muted='#9A917E', folio='#8A8578', part_ink='#4A463D', ledger_bg='#F4EFE3', ledger_ink='#5A554A',
        verdict_bg='#F6F1E4', rule_line='#D8CFBB', cp_line='#E4DCCB',
        body=10.3, lh=1.86, gap=0.5, margin=(20, 17, 19.5, 19),
        head_size=18, head_weight=700, head_ink='navy', head_spacing='0.7em', head_top=8,
        sub_font='serif', sub_size=10.3, rule_w=12, rule_h=0.9,
        sec_family='serif', sec_weight=700, sec_size=10.9,
        chap_style='label', chap_num='arabic', chap_label=9.8, chap_title=16, chap_top=6,
        part_label=10.5, part_title=19.1, part_top=62, bianxu_size=9.6, bianxu_font='serif',
        folio_pos='center', front='arabic', title_style='left', cp_style='table'),
    'peirce': dict(
        name='标杆（皮尔斯卷）', paper='#FAF6EC', ink='#2C2A27', navy='#23384F', gold='#A98541',
        muted='#8A8378', folio='#8A8378', part_ink='#4A4640', ledger_bg='#F2EBDB', ledger_ink='#5A554A',
        verdict_bg='#F2EBDB', rule_line='#C9BFAE', cp_line='#C9BFAE',
        body=10.8, lh=1.95, gap=0.55, margin=(22, 25, 22, 25),
        head_size=22, head_weight=700, head_ink='navy', head_spacing='0', head_top=12,
        sub_font='kai', sub_size=12.5, rule_w=18, rule_h=1.0,
        sec_family='sans', sec_weight=500, sec_size=11.4,
        chap_style='label', chap_num='chinese', chap_label=9.5, chap_title=17.5, chap_top=8,
        part_label=12, part_title=21, part_top=52, bianxu_size=10.6, bianxu_font='kai',
        folio_pos='outer', front='arabic', title_style='left', cp_style='box'),
    'schopenhauer': dict(
        name='叔本华卷', paper='#FFFFFF', ink='#1B1B1B', navy='#14283F', gold='#B8892F',
        muted='#9A948A', folio='#8A857C', part_ink='#444444', ledger_bg='#F4EFE3', ledger_ink='#555555',
        verdict_bg='#F4EFE3', rule_line='#D8D2C4', cp_line='#D8D2C4',
        body=10.8, lh=1.85, gap=0.3, margin=(20, 16, 20, 22),
        head_size=19, head_weight=900, head_ink='ink', head_spacing='0', head_top=10,
        sub_font='serif', sub_size=12, rule_w=20, rule_h=1.1,
        sec_family='sans', sec_weight=700, sec_size=11.2,
        chap_style='number', chap_num='chinese', chap_label=21, chap_title=11, chap_top=12,
        part_label=11, part_title=21, part_top=52, bianxu_size=10, bianxu_font='serif',
        folio_pos='left', front='roman', title_style='center', cp_style='colon'),
}
READER = dict(W=190, H=250, body=12.4, lh=2.0, margin=(20, 19, 20, 20))

CN = '零一二三四五六七八九'
CNUM = '零〇一二两三四五六七八九十百'
PART_RE = re.compile(r'^第\s*([一二三四五六七八九十百]+)\s*编[\s　:：]*(.*)$')
PIAN_RE = re.compile(r'^((?:[上中下尾]|第[一二三四五六七八九十]+)篇)[\s　:：]*(.*)$')
CHAP_RE = re.compile(r'^第\s*(\d+|[' + CNUM + r']+)\s*章[\s　:：]*(.*)$')
AUTHOR_SEC = {'作者介绍', '著者介绍'}
BIB_RE = re.compile(r'^(参考书目|参考文献|延伸阅读|书目)')
MAIN_FRONT = {'导论'}
PH = re.compile(r'⟦a:([^⟧]+)⟧')


def cn_num(n):
    if n < 10:
        return CN[n]
    if n < 20:
        return '十' + (CN[n % 10] if n % 10 else '')
    if n < 100:
        return CN[n // 10] + '十' + (CN[n % 10] if n % 10 else '')
    h, r = divmod(n, 100)
    s = CN[h] + '百'
    if r == 0:
        return s
    if r < 10:
        return s + '零' + CN[r]
    if r < 20:
        return s + '一十' + (CN[r % 10] if r % 10 else '')
    return s + cn_num(r)


def cn_to_int(s):
    if s.isdigit():
        return int(s)
    d = {c: i for i, c in enumerate(CN)}
    d.update({'〇': 0, '两': 2})
    total, cur = 0, 0
    for ch in s:
        if ch == '百':
            total += (cur or 1) * 100
            cur = 0
        elif ch == '十':
            total += (cur or 1) * 10
            cur = 0
        else:
            cur = d.get(ch, 0)
    return total + cur


def roman(n):
    out = ''
    for v, s in ((1000, 'm'), (900, 'cm'), (500, 'd'), (400, 'cd'), (100, 'c'), (90, 'xc'),
                 (50, 'l'), (40, 'xl'), (10, 'x'), (9, 'ix'), (5, 'v'), (4, 'iv'), (1, 'i')):
        while n >= v:
            out += s
            n -= v
    return out


def esc(s):
    return html.escape(s, quote=False)


def inline(s):
    s = esc(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<![*\w])\*([^\s*][^*\n]*?)\*(?![*\w])', r'<em>\1</em>', s)
    return s


def split_head(t):
    m = re.match(r'^(\S+?)[\s　]+(.+)$', t)
    return (m.group(1), m.group(2).strip()) if m else (t, '')


# ---------------------------------------------------------------- 解析

def parse(md):
    lines = md.replace('\r\n', '\n').split('\n')
    meta = {'statement': []}
    start = 0
    if lines and lines[0].strip() == '---':
        for j in range(1, len(lines)):
            if lines[j].strip() == '---':
                start = j + 1
                break
            k, sep, v = lines[j].partition(':')
            if not sep:
                continue
            k, v = k.strip(), v.strip()
            if k == 'statement':
                meta['statement'].append(v)
            elif k:
                meta[k] = v
    out, skip, pending = [], False, None
    for raw in lines[start:]:
        t = raw.strip()
        if t.startswith('【交接卡】'):
            skip = True
            continue
        if skip:
            if t.startswith('#'):
                skip = False
            else:
                continue
        if not t or t in ('---', '***', '* * *'):
            out.append(('blank', ''))
            pending = None
            continue
        m = re.match(r'^(#{1,4})\s+(.*)$', t)
        if m:
            out.append(('h%d' % len(m.group(1)), m.group(2).strip()))
            pending = None
            continue
        m = re.match(r'^【(带走的话|小账|想一想|编序|编首)】\s*(.*)$', t)
        if m:
            kind = {'带走的话': 'take', '小账': 'ledger', '想一想': 'think', '编序': 'bianxu', '编首': 'bianxu'}[m.group(1)]
            if m.group(2):
                out.append((kind, m.group(2)))
            else:
                pending = kind
            continue
        m = re.fullmatch(r'\**(带走的话|小账|想一想)\**[：:]?', t)
        if m:
            pending = {'带走的话': 'take', '小账': 'ledger', '想一想': 'think'}[m.group(1)]
            continue
        if pending:
            out.append((pending, t))
            continue
        if t.startswith('>'):
            out.append(('quote', t.lstrip('>').strip()))
        elif t.startswith('|'):
            out.append(('table', t))
        elif re.match(r'^[-•]\s+', t) or re.match(r'^\*\s+', t):
            out.append(('ul', re.sub(r'^[-•*]\s+', '', t)))
        elif re.match(r'^\d+[.、]\s*\S', t) and not re.match(r'^\d+[.、]\d', t):
            out.append(('ol', t))
        else:
            out.append(('p', t))
    return meta, out


def sectionize(blocks):
    secs, cur = [], None

    def new(**kw):
        d = dict(blocks=[], **kw)
        secs.append(d)
        return d

    for kind, t in blocks:
        if kind == 'h1':
            m1, m2, m3 = PART_RE.match(t), PIAN_RE.match(t), CHAP_RE.match(t)
            if m1:
                cur = new(kind='part', label=f'第{m1.group(1)}编', title=m1.group(2))
            elif m2:
                cur = new(kind='pian', label=m2.group(1), title=m2.group(2))
            elif m3:
                cur = new(kind='chap', num=cn_to_int(m3.group(1)), title=m3.group(2))
            else:
                title, sub = split_head(t)
                cur = new(kind='fsec', title=title, sub=sub)
        elif kind == 'h2' and CHAP_RE.match(t):
            m3 = CHAP_RE.match(t)
            cur = new(kind='chap', num=cn_to_int(m3.group(1)), title=m3.group(2))
        else:
            if cur is None:
                cur = new(kind='fsec', title='', sub='')
            if kind == 'h2':
                cur['blocks'].append(('sub', t))
            elif kind == 'h3':
                cur['blocks'].append(('sec', t))
            elif kind == 'h4':
                cur['blocks'].append(('minor', t))
            else:
                cur['blocks'].append((kind, t))
    return secs


# ---------------------------------------------------------------- 生成 HTML

def render_blocks(blocks, P, bib=False, part=False):
    out, i, n = [], 0, len(blocks)
    while i < n:
        kind, t = blocks[i]
        if kind == 'blank':
            i += 1
            continue
        if kind in ('quote', 'table', 'ul', 'ol', 'take', 'ledger', 'think'):
            grp, j = [], i
            while j < n and (blocks[j][0] == kind or (blocks[j][0] == 'blank' and kind in ('take', 'ledger', 'think')
                                                         and j + 1 < n and blocks[j + 1][0] == kind)):
                if blocks[j][0] == kind:
                    grp.append(blocks[j][1])
                j += 1
            i = j
            if kind == 'quote':
                if all(re.fullmatch(r'\*\*.+\*\*', g) for g in grp if g):
                    out.append('<div class="verdict">' + ''.join(f'<p>{inline(g)}</p>' for g in grp if g) + '</div>')
                else:
                    out.append('<blockquote>' + ''.join(f'<p>{inline(g)}</p>' for g in grp if g) + '</blockquote>')
            elif kind == 'table':
                rows = [r for r in grp if not re.match(r'^\|?\s*:?-{2,}', r)]
                cells = [[c.strip() for c in r.strip().strip('|').split('|')] for r in rows]
                if cells:
                    h = '<tr>' + ''.join(f'<th>{inline(c)}</th>' for c in cells[0]) + '</tr>'
                    b = ''.join('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>' for r in cells[1:])
                    out.append(f'<table class="tb"><thead>{h}</thead><tbody>{b}</tbody></table>')
            elif kind == 'ul':
                out.append('<ul class="ls">' + ''.join(f'<li>{inline(g)}</li>' for g in grp) + '</ul>')
            elif kind == 'ol':
                cls = 'bib' if bib else 'item'
                out.append(''.join(f'<p class="{cls}">{inline(g)}</p>' for g in grp))
            elif kind == 'take':
                out.append('<div class="takeaway"><span class="lab">带走的话</span>' +
                           ''.join(f'<p>{inline(g)}</p>' for g in grp) + '</div>')
            elif kind == 'ledger':
                out.append('<div class="ledger"><span class="lab">小账</span>' +
                           ''.join(f'<p>{inline(g)}</p>' for g in grp) + '</div>')
            else:
                out.append('<div class="think"><span class="lab">想一想</span>' +
                           ''.join(f'<p>{inline(g)}</p>' for g in grp) + '</div>')
            continue
        i += 1
        if kind == 'sec':
            t = re.sub(r'^[◆◇●■\s]+', '', t)
            out.append(f'<h3 class="sec"><span class="dia">◆</span>{inline(t)}</h3>')
        elif kind == 'sub':
            out.append(f'<h3 class="subhead">{inline(t)}</h3>')
        elif kind == 'minor':
            out.append(f'<h4 class="minor">{inline(t)}</h4>')
        elif kind in ('bianxu',) or (part and kind == 'p'):
            out.append(f'<p class="bianxu">{inline(t)}</p>')
        elif kind == 'p':
            if bib and re.match(r'^\d+[.、]', t):
                out.append(f'<p class="bib">{inline(t)}</p>')
            else:
                out.append(f'<p>{inline(t)}</p>')
    return '\n'.join(out)


def title_page(meta, P):
    pre = meta.get('pretitle', '普通人都能懂的')
    name = meta.get('name') or meta.get('title', '').replace(pre, '') or meta.get('title', '')
    sub = meta.get('subtitle', '')
    author = meta.get('author', '王德生')
    pub = meta.get('publisher_short', '德麦国际出版社')
    pub_en = meta.get('publisher_en', 'Demai International Press')
    if P['title_style'] == 'center':
        return (f'<section class="titlepage center"><div class="tp-full">{esc(pre + name)}</div>'
                f'<div class="tp-rule"></div><div class="tp-sub">{esc(sub)}</div>'
                f'<div class="tp-author">{esc("　".join(author))}　　著</div>'
                f'<div class="tp-pub">{esc(pub)}</div><div class="tp-pub-en">{esc(pub_en.upper())}</div></section>')
    shown = '　'.join(name) if len(name) == 2 else name
    return (f'<section class="titlepage"><div class="tp-pre">{esc(pre)}</div><div class="tp-name">{esc(shown)}</div>'
            f'<div class="tp-sub">{esc(sub)}</div><div class="tp-author">{esc(author)}　　著</div>'
            f'<div class="tp-pub">{esc(pub)}</div><div class="tp-pub-en">{esc(pub_en)}</div></section>')


def copyright_page(meta, P):
    t = meta.get('title', '')
    full = f'《{t}——{meta["subtitle"]}》' if meta.get('subtitle') else f'《{t}》'
    no = meta.get('series_no')
    fields = [
        ('书名', full), ('著者', meta.get('author', '王德生')), ('执笔', meta.get('executor')),
        ('出版', meta.get('publisher', '德麦国际出版社（Demai International Press）· 新加坡')),
        ('编号', f'德麦国际专著第 {no} 号' if no else '待填'), ('ISBN', meta.get('isbn', '待填')),
        ('定价', meta.get('price', '待填')), ('开本', meta.get('trim', '170 mm × 240 mm（16 开）')),
        ('字数', meta.get('words')), ('版次', meta.get('edition')), ('完稿', meta.get('finished')),
    ]
    fields = [(k, v) for k, v in fields if v]
    notes = ''.join(f'<p>{inline(s)}</p>' for s in meta.get('statement', []))
    right = meta.get('copyright', '版权所有　侵权必究')
    if P['cp_style'] == 'table':
        rows = ''.join(f'<tr><th>{k}</th><td>{inline(v)}</td></tr>' for k, v in fields)
        return (f'<section class="copyright"><div class="cp-title">出 版 信 息</div><table class="cp">{rows}</table>'
                f'<div class="cp-notes">{notes}<p class="cp-right">{esc(right)}</p></div></section>')
    if P['cp_style'] == 'box':
        spaced = lambda k: k if len(k) != 2 else k[0] + '　' + k[1]
        rows = ''.join(f'<p>{spaced(k)}：{inline(v)}</p>' for k, v in fields if k != '书名')
        return (f'<section class="copyright"><div class="cp-box"><div class="cp-bt">{esc(t)}</div>'
                f'<div class="cp-bs">——{esc(meta.get("subtitle", ""))}</div>{rows}'
                f'<div class="cp-notes">{notes}<p>{esc(right)}</p></div></div></section>')
    rows = ''.join(f'<p>{k}：{inline(v)}</p>' for k, v in fields)
    return (f'<section class="copyright colon"><div class="cp-title">出版信息</div>{rows}'
            f'<div class="cp-notes">{notes}<p>{esc(right)}</p></div></section>')


def chap_label(num, P):
    return f'第 {num} 章' if P['chap_num'] == 'arabic' else f'第{cn_num(num)}章'


def build_html(md, P, cover=None, backcover=None):
    meta, blocks = parse(md)
    secs = sectionize(blocks)
    toc, body = [], []
    ids = {'n': 0}
    state = {'toc': False, 'main': False, 'arabic': False}
    has_copyright_sec = any(s['kind'] == 'fsec' and s['title'] == '出版信息' for s in secs)
    roman_mode = P['front'] == 'roman'

    def nid(p):
        ids['n'] += 1
        return f'{p}{ids["n"]}'

    def anchor_marks(counted, main_part):
        a = ''
        if counted and not state['main']:
            state['main'] = True
            a += '<a id="main-start"></a>'
        if main_part and not state['arabic']:
            state['arabic'] = True
            a += '<a id="arabic-start"></a>'
        return a

    def insert_toc():
        if state['toc']:
            return
        state['toc'] = True
        body.append('⟦TOC⟧')

    if cover:
        body.append(f'<section class="coverpage"><img src="{Path(cover).resolve().as_uri()}" alt=""></section>')
        body.append('<section class="blankpage">&#8203;</section>')
    body.append(title_page(meta, P))
    if not has_copyright_sec:
        body.append(copyright_page(meta, P))

    for s in secs:
        k = s['kind']
        if k == 'fsec' and s['title'] == '出版信息':
            body.append(f'<section class="copyright custom"><div class="cp-title">出 版 信 息</div>'
                        f'{render_blocks(s["blocks"], P)}</section>')
            continue
        if k == 'fsec' and s['title'] in AUTHOR_SEC:
            body.append(f'<section class="author"><div class="fs-head"><h1 class="fs-title">{esc(s["title"])}</h1>'
                        f'<div class="rule"></div></div>{render_blocks(s["blocks"], P)}</section>')
            continue
        is_main = (k in ('part', 'pian', 'chap')) or (k == 'fsec' and s['title'] in MAIN_FRONT)
        if is_main:
            insert_toc()
        front_cls = ' front' if (roman_mode and not state['arabic'] and not is_main) else ''
        if k == 'fsec':
            aid = nid('f')
            title, sub = s['title'], s['sub']
            level = 'appx' if (title.startswith('附录') and len(title) > 2) else 'front'
            toc.append((level, title + ('　' + sub if sub else ''), aid))
            bib = bool(BIB_RE.match(title))
            marks = anchor_marks(True, is_main)
            head = (f'<div class="fs-head"><h1 class="fs-title">{esc(title)}</h1>'
                    + (f'<div class="fs-sub">{inline(sub)}</div>' if sub else '') + '<div class="rule"></div></div>')
            front_cls += {1: ' tight', 2: ' tight2'}.get(TIGHT.get('f' + title, 0), '')
            body.append(f'<section class="fsec{front_cls}" id="{aid}">{marks}{head}'
                        f'{render_blocks(s["blocks"], P, bib=bib)}</section>')
            if title == '导读':
                insert_toc()
        elif k in ('part', 'pian'):
            aid = nid('p')
            toc.append((k, s['label'] + '　' + s['title'], aid))
            marks = anchor_marks(True, True)
            body.append(f'<section class="{k}" id="{aid}">{marks}<div class="part-head"><div class="part-label">'
                        f'{esc(s["label"])}　</div><h1 class="part-title">{inline(s["title"])}</h1></div>'
                        f'<div class="rule"></div></section>')
            if any(k2 != 'blank' for k2, _ in s['blocks']):
                body.append(f'<section class="xu"><div class="xu-head">编　序</div>{render_blocks(s["blocks"], P)}</section>')
        else:
            aid = nid('c')
            lab = chap_label(s['num'], P)
            toc.append(('chap', lab + '　' + s['title'], aid))
            marks = anchor_marks(True, True)
            style = 'number' if P['chap_style'] == 'number' else 'label'
            style += {1: ' tight', 2: ' tight2'}.get(TIGHT.get('c%d' % s['num'], 0), '')
            body.append(f'<section class="chapter {style}" id="{aid}">{marks}<div class="chap-head">'
                        f'<div class="chap-label">{esc(lab)}　</div><h2 class="chap-title">{inline(s["title"])}</h2>'
                        f'</div><div class="rule"></div>{render_blocks(s["blocks"], P)}</section>')
    if not state['toc']:
        insert_toc()
    if backcover:
        body.append(f'<section class="coverpage back"><img src="{Path(backcover).resolve().as_uri()}" alt=""></section>')

    toc_front = ' front' if roman_mode else ''
    items = ''.join(f'<li class="{lv}"><span class="t">{inline(t)}</span><span class="d"></span>'
                    f'<span class="n">⟦a:{a}⟧</span></li>' for lv, t, a in toc)
    toc_html = (f'<section class="fsec toc{toc_front}" id="toc"><div class="fs-head"><h1 class="fs-title">目录</h1>'
                f'<div class="rule"></div></div><ul>{items}</ul></section>')
    doc = '\n'.join(body).replace('⟦TOC⟧', toc_html)
    title = meta.get('title', '')
    return meta, (f'<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><title>{esc(title)}</title>'
                  f'<meta name="author" content="{esc(meta.get("author", "王德生"))}"></head><body>{doc}</body></html>')


# ---------------------------------------------------------------- CSS

CSS_T = string.Template(r'''
@page { size: ${W}mm ${H}mm; margin: ${mt}mm ${mr}mm ${mb}mm ${ml}mm; background: ${paper}; }
@page :left { @top-left { content: "${runhead}"; font-family: ${sans}; font-size: 7.8pt; color: ${muted};
  vertical-align: bottom; padding-bottom: 4.5mm; } }
@page :right { @top-right { content: string(chaptitle); font-family: ${sans}; font-size: 7.8pt; color: ${muted};
  vertical-align: bottom; padding-bottom: 4.5mm; } }
@page part { @top-left { content: none; } @top-right { content: none; } }
@page bare { @top-left { content: none; } @top-right { content: none; } @bottom-left { content: none; }
  @bottom-center { content: none; } @bottom-right { content: none; } }
@page cover { margin: 0; @top-left { content: none; } @top-right { content: none; } @bottom-left { content: none; }
  @bottom-center { content: none; } @bottom-right { content: none; } }

html { font-family: ${serif}; font-size: ${body}pt; line-height: ${lh}; color: ${ink}; }
body { margin: 0; }
section { break-before: page; }
section.coverpage { page: cover; }
section.coverpage img { display: block; width: ${W}mm; height: ${H}mm; object-fit: cover; }
section.titlepage, section.copyright, section.author, section.blankpage { page: bare; }
section.part, section.pian { page: part; }
section.front { page: front; }
p { margin: 0 0 ${gap}em; text-indent: 2em; text-align: justify; orphans: 2; widows: 2; }
strong { color: ${navy}; font-weight: 700; }
em { font-style: normal; color: ${part_ink}; }
h1, h2, h3, h4 { bookmark-level: none; break-after: avoid; }

.fs-head { margin: ${head_top}mm 0 1.5em; }
h1.fs-title { font-size: ${head_em}em; font-weight: ${head_weight}; color: ${head_ink}; letter-spacing: ${head_spacing};
  line-height: 1.3; margin: 0; string-set: chaptitle content(); bookmark-level: 1; }
.fs-sub { font-family: ${sub_font}; font-size: ${sub_em}em; color: ${gold}; margin: .5em 0 0; line-height: 1.5; }
.rule { width: ${rule_w}mm; height: 0; border-top: ${rule_h}pt solid ${gold}; margin: .75em 0 0; }

.chap-head { margin: ${chap_top}mm 0 0; bookmark-level: 2; bookmark-label: content(); string-set: chaptitle content(); }
.chap-label { font-family: ${sans}; font-size: ${chap_label_em}em; color: ${gold}; letter-spacing: .12em; line-height: 1.4; }
h2.chap-title { font-size: ${chap_title_em}em; font-weight: 700; color: ${navy}; line-height: 1.45; margin: .3em 0 0; }
section.chapter > .rule { margin: .8em 0 1.7em; }
section.chapter.number .chap-label { font-family: ${serif}; font-weight: 900; color: ${ink}; letter-spacing: 0; line-height: 1.2; }
section.chapter.number h2.chap-title { font-family: ${sans}; font-weight: 400; color: ${gold}; margin-top: .6em; }

h3.sec { font-family: ${sec_family}; font-weight: ${sec_weight}; font-size: ${sec_em}em; color: ${navy};
  line-height: 1.5; margin: 1.45em 0 .5em; }
h3.sec .dia { color: ${gold}; font-family: ${sans}; font-size: .78em; margin-right: .45em; position: relative; top: -.08em; }
h3.subhead { font-family: ${serif}; font-weight: 700; font-size: 1.22em; color: ${navy};
  line-height: 1.5; margin: 2.1em 0 .7em; break-after: avoid; page-break-after: avoid; }
h3.subhead::before { content: ""; display: block; width: 14mm; border-top: 1pt solid ${gold}; margin-bottom: .55em; }
section.chapter > h3.subhead:first-of-type { margin-top: .6em; }
h4.minor { font-size: 1em; font-weight: 700; color: ${navy}; margin: 1em 0 .3em; break-after: avoid; page-break-after: avoid; }
h3.sec { break-after: avoid; page-break-after: avoid; }
section.tight p, section.tight li { line-height: 1.8; }
section.tight p { margin-bottom: .3em; }
section.tight2 p, section.tight2 li { line-height: 1.74; }
section.tight2 p { margin-bottom: .2em; }
section.tight2 h3.sec, section.tight2 h3.subhead { margin-top: 1.2em; }

section.part, section.pian { text-align: center; padding-top: ${part_top}mm; }
section.xu { page-break-before: always; break-before: page; }
section.xu p, section.xu li { line-height: 1.78; }
section.xu p { margin-bottom: .28em; }
section.xu .xu-head { font-family: ${sans}; font-size: .92em; color: ${gold}; letter-spacing: .5em; margin: 2mm 0 1.4em; }
section.xu .xu-head::after { content: ""; display: block; width: 12mm; border-top: 1pt solid ${gold}; margin-top: .6em; }
section.part ul.ls, section.pian ul.ls { text-align: left; font-size: .9em; line-height: 1.68; margin: .2em 0 .4em 1.5em; }
section.part p.bianxu { line-height: 1.72; margin-bottom: .32em; }
section.part > .rule { margin: .7em auto 1.3em; }
.part-head { bookmark-level: 1; bookmark-label: content(); string-set: chaptitle content(); }
.part-label { font-family: ${sans}; font-size: ${part_label_em}em; color: ${gold}; letter-spacing: .45em; }
h1.part-title { font-size: ${part_title_em}em; font-weight: 700; color: ${navy}; line-height: 1.5; margin: .8em 3mm 0; }
section.part > .rule, section.pian > .rule { margin: 1em auto 2.2em; }
p.bianxu { font-family: ${bianxu_font}; font-size: ${bianxu_em}em; color: ${part_ink}; text-align: justify;
  margin: 0 4mm .55em; text-indent: 2em; }
p.bianxu strong { color: ${navy}; }

section.titlepage { padding-top: 36mm; }
.tp-pre { font-size: 16pt; font-weight: 600; color: ${navy}; letter-spacing: .06em; }
.tp-name { font-size: 43pt; font-weight: 900; color: ${navy}; letter-spacing: .06em; line-height: 1.2; margin: .12em 0 .3em; }
.tp-sub { font-family: ${sub_font}; font-size: 10.5pt; color: ${gold}; }
.tp-author { margin-top: 56mm; font-size: 12.4pt; letter-spacing: .08em; }
.tp-pub { margin-top: 40mm; font-family: ${sans}; font-size: 9.8pt; color: ${navy}; letter-spacing: .3em; }
.tp-pub-en { font-family: ${sans}; font-size: 7.2pt; color: ${folio}; letter-spacing: .06em; margin-top: 1.2mm; }
section.titlepage.center { text-align: center; padding-top: 58mm; }
.tp-full { font-size: 26pt; font-weight: 900; color: ${ink}; letter-spacing: .04em; }
.tp-rule { width: 36mm; border-top: 1.2pt solid ${gold}; margin: 7mm auto 6mm; }
section.titlepage.center .tp-sub { font-family: ${serif}; font-size: 12pt; color: #555555; }
section.titlepage.center .tp-author { margin-top: 28mm; font-size: 12pt; }
section.titlepage.center .tp-pub { margin-top: 44mm; color: #444444; letter-spacing: .1em; font-size: 10pt; }
section.titlepage.center .tp-pub-en { color: #888888; letter-spacing: .3em; font-size: 8pt; }

section.copyright { padding-top: 6mm; font-size: 8.7pt; line-height: 1.65; }
.cp-title { text-align: center; font-size: 10.8pt; font-weight: 700; color: ${navy}; letter-spacing: .5em; margin: 0 0 5mm; }
table.cp { width: 100%; border-collapse: collapse; margin: 0 0 5mm; font-size: 8.7pt; }
table.cp th { font-family: ${sans}; font-weight: 400; color: ${folio}; width: 15mm; text-align: left; vertical-align: top;
  padding: 1.5mm 0; border-bottom: .4pt solid ${cp_line}; }
table.cp td { padding: 1.5mm 0; border-bottom: .4pt solid ${cp_line}; }
.cp-notes p { font-size: 8pt; color: ${part_ink}; text-indent: 0; margin: 0 0 .55em; line-height: 1.75; text-align: justify; }
.cp-notes p.cp-right { margin-top: 3mm; letter-spacing: .1em; }
.cp-box { margin-top: 92mm; border: .6pt solid ${cp_line}; padding: 5mm 6mm; font-family: ${sans}; font-weight: 300;
  font-size: 8pt; line-height: 1.8; color: ${part_ink}; }
.cp-box p { text-indent: 0; margin: 0; }
.cp-box .cp-bt { font-family: ${serif}; font-weight: 600; color: ${navy}; font-size: 9.5pt; }
.cp-box .cp-bs { font-family: ${serif}; margin-bottom: 2mm; }
.cp-box .cp-notes { margin-top: 3mm; }
.cp-box .cp-notes p { font-size: 7.2pt; }
section.copyright.colon .cp-title { text-align: left; font-size: 15pt; font-weight: 900; color: ${ink}; letter-spacing: 0; margin: 20mm 0 6mm; }
section.copyright.colon > p { font-size: 9.6pt; text-indent: 0; margin: 0; line-height: 2.4; }
section.copyright.colon .cp-notes { margin-top: 6mm; }
section.copyright.colon .cp-notes p { font-size: 9pt; color: #666666; }
section.copyright.custom p { text-indent: 0; }

section.toc ul { list-style: none; margin: 0; padding: 0; }
section.toc li { display: table; width: 100%; box-sizing: border-box; table-layout: auto; border-collapse: separate; margin: .22em 0; line-height: 1.55; }
section.toc li .t { display: table-cell; white-space: nowrap; padding-right: .35em; }
section.toc li .d { display: table-cell; width: 100%; border-bottom: 1pt dotted ${folio}; }
section.toc li .n { display: table-cell; white-space: nowrap; min-width: 1.8em; padding-left: .35em; text-align: right; color: ${folio}; }
section.toc li.part, section.toc li.pian { font-weight: 700; color: ${navy}; margin-top: .75em; }
section.toc li.pian { font-weight: 900; font-size: 1.05em; }
section.toc li.chap, section.toc li.appx { padding-left: 1.7em; font-size: .93em; }

.verdict { background: ${verdict_bg}; border-left: 2pt solid ${gold}; padding: .75em 1.1em; margin: 1em 0 1.1em 5mm; break-inside: avoid; }
.verdict p { text-indent: 0; margin: 0 0 .3em; font-weight: 700; color: ${navy}; }
.verdict p:last-child { margin-bottom: 0; }
blockquote { margin: 1em 0; padding: .55em .9em; background: ${verdict_bg}; border-left: 2pt solid ${gold}; color: ${ink}; break-inside: avoid; }
blockquote p { text-indent: 0; margin: 0 0 .3em; }
table.tb { width: 100%; border-collapse: collapse; font-size: .8em; line-height: 1.55; margin: .8em 0 1.1em; }
table.tb th { background: ${navy}; color: #FFFFFF; font-family: ${sans}; font-weight: 700; text-align: left; padding: .45em .55em; }
table.tb td { border-bottom: .3pt solid ${rule_line}; padding: .45em .55em; vertical-align: top; }
table.tb tbody tr:nth-child(even) td { background: #F8F5EE; }
table.tb td:first-child { font-weight: 700; color: ${navy}; }
table.tb tr { break-inside: avoid; page-break-inside: avoid; }
table.tb thead { display: table-header-group; }
ul.ls { list-style: none; margin: .5em 0 .8em 2em; padding: 0; }
ul.ls li { margin: .15em 0; }
ul.ls li::before { content: "·"; color: ${gold}; font-weight: 700; margin-left: -1em; display: inline-block; width: 1em; }
p.item, p.bib { text-indent: -1.6em; padding-left: 1.6em; margin: 0 0 .3em; text-align: left; }
p.bib { font-size: .9em; }
.takeaway { border-top: .6pt solid ${gold}; border-bottom: .6pt solid ${gold}; margin: 1.4em 0 .9em; padding: .6em 0 .65em; break-inside: avoid; }
.lab { display: block; font-family: ${sans}; font-size: .75em; letter-spacing: .3em; color: ${gold}; margin-bottom: .25em; line-height: 1.4; }
.takeaway p { text-indent: 0; margin: 0; font-weight: 700; color: ${navy}; }
.ledger { background: ${ledger_bg}; border-left: 1.6pt solid ${gold}; padding: .55em .9em .6em; margin: 0 0 1em;
  font-size: .86em; line-height: 1.75; color: ${ledger_ink}; break-inside: avoid; }
.ledger .lab { color: ${navy}; font-size: .84em; }
.ledger p { text-indent: 0; margin: 0 0 .15em; }
.think { border-top: .6pt solid ${rule_line}; padding: .55em 0 0; margin: .9em 0 1em; font-size: .95em; break-inside: avoid; }
.think p { text-indent: 0; margin: 0 0 .25em; }
''')


def build_css(P, edition, runhead):
    if edition == 'reader':
        W, H, body, lh, m = READER['W'], READER['H'], READER['body'], READER['lh'], READER['margin']
    else:
        W, H, body, lh, m = 170, 240, P['body'], P['lh'], P['margin']
    fam = {'serif': SERIF, 'sans': SANS, 'kai': KAI}
    b = P['body']
    v = dict(W=W, H=H, mt=m[0], mr=m[1], mb=m[2], ml=m[3], body=body, lh=lh, gap=P['gap'],
             serif=SERIF, sans=SANS, runhead=runhead.replace('\\', '').replace('"', '\\"'),
             head_em=round(P['head_size'] / b, 3), head_weight=P['head_weight'],
             head_ink=P[P['head_ink']], head_spacing=P['head_spacing'], head_top=P['head_top'],
             sub_font=fam[P['sub_font']], sub_em=round(P['sub_size'] / b, 3),
             rule_w=P['rule_w'], rule_h=P['rule_h'],
             sec_family=fam[P['sec_family']], sec_weight=P['sec_weight'], sec_em=round(P['sec_size'] / b, 3),
             chap_label_em=round(P['chap_label'] / b, 3), chap_title_em=round(P['chap_title'] / b, 3),
             chap_top=P['chap_top'], part_label_em=round(P['part_label'] / b, 3),
             part_title_em=round(P['part_title'] / b, 3), part_top=P['part_top'],
             bianxu_em=round(P['bianxu_size'] / b, 3), bianxu_font=fam[P['bianxu_font']])
    v.update({k: P[k] for k in ('paper', 'ink', 'navy', 'gold', 'muted', 'folio', 'part_ink', 'ledger_bg',
                                'ledger_ink', 'verdict_bg', 'rule_line', 'cp_line')})
    return CSS_T.substitute(v)


def folio_css(folios, P, npages):
    """逐页写定页码：页码与目录同一个算法。"""
    out = []
    style = f'font-family: {SERIF}; font-size: 8pt; color: {P["folio"]}; vertical-align: top; padding-top: 5.5mm;'
    for i in range(npages):
        f = folios.get(i, '')
        if not f:
            continue
        if P['folio_pos'] == 'center':
            box = 'bottom-center'
        elif P['folio_pos'] == 'left':
            box = 'bottom-left'
        else:
            box = 'bottom-right' if i % 2 == 0 else 'bottom-left'
        out.append(f'@page :nth({i + 1}) {{ @{box} {{ content: "{f}"; {style} }} }}')
    return '\n'.join(out)


def anchors(doc):
    pos = {}
    for i, pg in enumerate(doc.pages):
        for name in getattr(pg, 'anchors', {}) or {}:
            pos.setdefault(name, i)
    return pos


def folio_map(pos, npages, P):
    if P['front'] == 'roman':
        a = pos.get('arabic-start', 0)
        return {i: (roman(i + 1) if i < a else str(i + 1)) for i in range(npages)}
    s = pos.get('main-start', 0)
    return {i: str(i - s + 1) for i in range(s, npages)}


def render(html_doc, css_text, out_pdf, P, base):
    from weasyprint import CSS, HTML

    def run(h, extra=''):
        return HTML(string=h, base_url=base).render(stylesheets=[CSS(string=css_text + '\n' + extra)])

    d1 = run(PH.sub('000', html_doc))
    pos = anchors(d1)
    for _ in range(3):
        fol = folio_map(pos, len(d1.pages), P)
        filled = PH.sub(lambda m: fol.get(pos.get(m.group(1), -1), '?'), html_doc)
        d2 = run(filled, folio_css(fol, P, len(d1.pages)))
        pos2 = anchors(d2)
        if pos2 == pos and len(d2.pages) == len(d1.pages):
            break
        d1, pos = d2, pos2
    d2.write_pdf(out_pdf)
    return len(d2.pages), pos, fol


def main():
    ap = argparse.ArgumentParser(description='系列成书：Markdown → 印刷版／阅读友好版 PDF')
    ap.add_argument('src', nargs='?')
    ap.add_argument('--out', help='输出文件名前缀（默认用稿件名）')
    ap.add_argument('--preset', choices=sorted(PRESETS), default='current')
    ap.add_argument('--edition', choices=['print', 'reader', 'both'], default='print')
    ap.add_argument('--cover', help='封面图（满版）')
    ap.add_argument('--backcover', help='封底图（满版）')
    ap.add_argument('--paper', help='覆盖纸色，如 #FCFAF4（罗素卷）')
    ap.add_argument('--html-only', action='store_true', help='只输出 HTML，便于检查')
    ap.add_argument('--dump-css', metavar='PATH', help='把所选预设的印刷版 CSS 写到文件后退出')
    a = ap.parse_args()
    P = dict(PRESETS[a.preset])
    if a.paper:
        P['paper'] = a.paper
    if a.dump_css:
        Path(a.dump_css).write_text(f'/* 通俗哲学专著 · 预设 {a.preset}：{P["name"]}（印刷版 170×240）。由 build_book.py 生成。 */\n'
                                    + build_css(P, 'print', '书名'), encoding='utf-8')
        print('CSS →', a.dump_css)
        return 0
    if not a.src:
        ap.error('需要稿件路径')
    src = Path(a.src)
    md = src.read_text(encoding='utf-8')
    meta, doc = build_html(md, P, a.cover, a.backcover)
    runhead = meta.get('runhead') or meta.get('title') or src.stem
    out = a.out or str(src.with_suffix(''))
    eds = ['print', 'reader'] if a.edition == 'both' else [a.edition]
    if a.html_only:
        for ed in eds:
            p = f'{out}-{ed}.html'
            Path(p).write_text(doc.replace('</head>', f'<style>{build_css(P, ed, runhead)}</style></head>'), encoding='utf-8')
            print('HTML →', p)
        return 0
    for ed in eds:
        p = f'{out}-{ed}.pdf'
        n, pos, fol = render(doc, build_css(P, ed, runhead), p, P, str(src.resolve().parent))
        first = fol.get(pos.get('main-start', 0), '?')
        print(f'{"印刷版" if ed == "print" else "阅读友好版"} → {p}：{n} 页；预设 {P["name"]}；'
              f'页码从第 {pos.get("main-start", 0) + 1} 页（{first}）起；目录 {len(PH.findall(doc))} 条')
    return 0


if __name__ == '__main__':
    sys.exit(main())
