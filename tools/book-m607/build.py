#!/usr/bin/env python3
"""第 607 号《SDE思想大全》（王德生 著；工具链承自第 605 号）成书：统稿 book.md ＋ notes.json（来源注）→ 印刷版／阅读版 PDF ＋ 全文网页。

版式照第 220 号、第 302 号：暖纸内页、藏青标题、浅金大号章码、金色「第 N 章」、金短线、◆ 金菱形小节、
章末金菱形、编首页金色花饰圆章与「编序」；各章末附「来源注」（小号字）。
与第 605 号的不同：全书 21 编 115 章，按「编」分块并行排版（每编从右页起，各块独立排版后按页数接页码）；
前置依次为书名页、出版信息、作者介绍、总导论（罗马页码）、目录；正文从第一编起；后置为总合论。

用法：
  python3 cover.py --out <out>            # 封面封底（沿用作者提供的图）
  python3 build.py --fonts /usr/share/fonts/opentype/noto --out <out> [--only print|reader|web]
产物：<out>/sde-compendium-print.pdf（170×240）、-reader.pdf（190×250）、text.html、toc-reader.json、toc-print.json
依赖：weasyprint、pymupdf。
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
import meta as M  # noqa: E402
BOOK_MD = ROOT / 'book.md'
NOTES = json.loads((ROOT / 'notes.json').read_text(encoding='utf-8'))
STRUCT = json.loads((ROOT / 'structure.json').read_text(encoding='utf-8'))
SLUG = M.SLUG
META = dict(
    title=M.TITLE, name=M.TITLE,
    subtitle=M.SUBTITLE, author=M.AUTHOR, advisor=M.ADVISOR, no=M.NO,
    isbn=M.ISBN, price=M.PRICE, version=M.V,
    publisher=M.PUBLISHER, publisher_en=M.PUBLISHER_EN,
)
EPIGRAPH = ''
GROUP_START = {}   # 编首页 sid → 「第一部分　本体论」，目录里先排一行部分标题
HAN = re.compile(r'[一-鿿]')
CN = '零一二三四五六七八九十'


# ───────────────────────── 解析 ─────────────────────────
def blocks_of(text):
    """把 Markdown 切成块：h1/h2/h3/p/quote/table/ul/ol/hr/orn。"""
    out, buf, kind = [], [], None

    def flush():
        nonlocal buf, kind
        if buf:
            out.append((kind, buf))
        buf, kind = [], None

    infence = False
    informula = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if informula is not None:
            if line.strip() == '\\]':
                out.append(('formula', informula)); informula = None
            else:
                informula.append(line.strip())
            continue
        if line.strip() == '\\[':
            flush(); informula = []; continue
        if line.strip().startswith('```'):
            if infence:
                out.append(('pre', buf)); buf, kind = [], None; infence = False
            else:
                flush(); infence = True
            continue
        if infence:
            buf.append(raw.rstrip()); continue
        if not line.strip():
            flush()
            continue
        if line.startswith('> ') or line == '>':
            if kind != 'quote':
                flush(); kind = 'quote'
            buf.append(line[2:] if line.startswith('> ') else '')
            continue
        if line.startswith('|'):
            if kind != 'table':
                flush(); kind = 'table'
            buf.append(line)
            continue
        m = re.match(r'^(#{1,4}) (.*)$', line)
        if m:
            flush(); out.append(('h%d' % len(m[1]), [m[2].strip()])); continue
        if line.startswith('◆ '):
            flush(); out.append(('h3', [line.strip()])); continue
        if line.strip() == '---':
            flush(); out.append(('hr', [])); continue
        if line.strip() == '◆':
            flush(); out.append(('orn', [])); continue
        if re.match(r'^- ', line):
            if kind != 'ul':
                flush(); kind = 'ul'
            buf.append(line[2:]); continue
        if re.match(r'^\d+\. ', line):
            if kind != 'ol':
                flush(); kind = 'ol'
            buf.append(line); continue
        if kind in ('ul', 'ol', 'quote', 'table'):
            flush()
        kind = kind or 'p'
        buf.append(line.strip())
    flush()
    # 连续的普通行合成一段
    res = []
    for k, b in out:
        if k == 'p':
            res.append(('p', [''.join(b)]))
        elif k == 'ol' and res and res[-1][0] == 'ol' and int(re.match(r'\d+', b[0])[0]) == int(re.match(r'\d+', res[-1][1][-1])[0]) + 1:
            res[-1][1].extend(b)   # 空行隔开的编号项并回一张表：否则 WeasyPrint 不认 start，全排成「1.」
        elif k == 'ul' and res and res[-1][0] == 'ul':
            res[-1][1].extend(b)
        else:
            res.append((k, list(b)))
    return res


def inline(s):
    s = s.replace('AI for Science', 'AI\u00a0for\u00a0Science')
    s = re.sub(r'([。！？；：，、」』）]\*{0,2}) +(?=[\u4e00-\u9fff「『（])', r'\1', s)   # 中文标点后的空格（粗体句后常见）会撑出一块空白
    s = re.sub(r'(?<=[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]) (?=[A-Za-z0-9$])|(?<=[A-Za-z0-9%$.)]) (?=[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef])', '\u2009', s)
    s = html.escape(s, quote=False)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?!\*)', r'<em>\1</em>', s)
    return s


def _dw(s):
    """单元格的显示宽度（以一个汉字宽为 1）。"""
    s = re.sub(r'\*\*|(?<!\w)\*(?=\S)|(?<=\S)\*(?!\w)', '', s)
    return sum(1.0 if ord(c) > 0x2E7F or 0xFF00 <= ord(c) <= 0xFFEF else 0.56 for c in s)


def col_widths(head, body, total=43.0, pad=0.95):
    """逐步挪宽度、把全表行数压到最少；每列不窄于「最长外文词」和「表头两行放得下」。返回 (百分比, 估计行数)。"""
    import math
    n = len(head)
    rows = [head] + [r + [''] * (n - len(r)) for r in body]
    T = total - n * pad
    mins = []
    for i in range(n):
        tok = max([0.56 * len(t) for r in rows for t in re.findall(r'[A-Za-z0-9_.\-–—/%$+·≥≤]+', r[i])] or [0])
        mins.append(max(min(tok, 13.0), math.ceil(_dw(head[i]) / 2), min(max(_dw(r[i]) for r in rows), 3.0), 2.0))
    if sum(mins) > T:
        k = T / sum(mins); mins = [m * k for m in mins]
    weight = [math.sqrt(max(sum(_dw(r[i]) for r in rows) / len(rows), 1)) for i in range(n)]
    free = T - sum(mins)
    w = [mins[i] + free * weight[i] / sum(weight) for i in range(n)]

    def lines(wd):
        tot = lead = 0
        for r in rows:
            ls = [max(1, math.ceil(_dw(r[i]) / wd[i])) for i in range(n)]
            tot += max(ls); lead += sum(ls)
        return (tot, lead)
    best, step = lines(w), 0.5
    for _ in range(400):
        moved = False
        for i in range(n):
            for j in range(n):
                if i == j or w[j] - step < mins[j]:
                    continue
                w[i] += step; w[j] -= step
                c = lines(w)
                if c < best:
                    best, moved = c, True
                else:
                    w[i] -= step; w[j] += step
        if not moved:
            break
    return [(w[i] + pad) / total * 100 for i in range(n)], best[0]


def table_html(rows, cls='tb'):
    cells = [[c.strip() for c in r.strip().strip('|').split('|')] for r in rows]
    cells = [r for r in cells if not all(re.fullmatch(r':?-{2,}:?', c) for c in r)]
    head, body = cells[0], cells[1:]
    # 单元格里的竖线（如 |r|<0.1）被当成了分栏：多出来的格并回去，首尾两栏不动
    for r in body:
        while len(r) > len(head):
            r[1:len(r) - len(head) + 2] = ['|'.join(r[1:len(r) - len(head) + 2])]
    if len(head) >= 6:
        cls += ' w5'
    if len(body) > 20:
        cls += ' dense'
    pct, est = col_widths(head, body)
    n = len(head)
    ctr = [bool(body) and all(_dw(r[i]) <= 3 for r in body if len(r) > i) and _dw(head[i]) <= 6 for i in range(n)]
    h = ['<div class="tw%s"><table class="%s"><colgroup>%s</colgroup><thead><tr>'
         % (' short' if est <= 7 else '', cls, ''.join('<col style="width:%.2f%%">' % x for x in pct))]
    h += ['<th%s>%s</th>' % (' class="ctr"' if ctr[i] else '', inline(c)) for i, c in enumerate(head)]
    h.append('</tr></thead><tbody>')
    for r in body:
        h.append('<tr>' + ''.join('<td%s>%s</td>' % (' class="ctr"' if i < n and ctr[i] else '', inline(c)) for i, c in enumerate(r)) + '</tr>')
    h.append('</tbody></table></div>')
    return ''.join(h)


def fig_board(b):
    """第 1 章白板图：字符画改成排好的框与箭头，字一个不动。"""
    return ('<div class="fig board"><p class="note">（外圈：一个大圆，围住下面所有）</p>'
            '<div class="node top">缝隙创新法</div><div class="stem">▲<br>│</div>'
            '<div class="row"><span class="node">二阶碰撞法</span><span class="ar">◄──</span>'
            '<span class="node core">SDE思想创新法</span><span class="ar">──►</span><span class="node">九宫透镜法</span></div></div>')


def fig_grid(b):
    """第 39 章九宫占位图：原来的字符表（在比例字体里对不齐）改成真正的九宫表，字一个不动。"""
    ls = [x.strip() for x in b if x.strip()]
    heads = ls[0].split()
    rows = []
    for k in range(0, 9, 3):
        cs = [re.split(r'\s{2,}', re.sub(r'^D\d\s+', '', ls[1 + k + t])) for t in range(3)]
        label = ls[1 + k].split()[0]
        rows.append((label, [(re.sub(r'^\[|\]$', '', cs[0][i]), cs[1][i], cs[2][i]) for i in range(3)]))
    h = ['<div class="fig ninegrid"><table><thead><tr><th></th>%s</tr></thead><tbody>' % ''.join('<th>%s</th>' % x for x in heads)]
    for lab, cc in rows:
        tds = []
        for tag, l2, l3 in cc:
            kind = 'g' if '正位' in tag else ('a' if ' 甲 ' in tag else 'b')
            empty = ' empty' if '空' in l2 else ''
            tds.append('<td class="%s%s"><b>%s</b><span>%s</span><i>%s</i></td>' % (kind, empty, html.escape(tag), html.escape(l2), html.escape(l3)))
        h.append('<tr><th>%s</th>%s</tr>' % (lab, ''.join(tds)))
    h.append('</tbody></table></div>')
    return ''.join(h)


def tex_html(t):
    t = t.strip().rstrip(',.')
    t = re.sub(r'_\{([^}]*)\}', r'<sub>\1</sub>', t)
    t = re.sub(r'_(\w)', r'<sub>\1</sub>', t)
    t = t.replace('\\lor', ' ∨ ').replace('\\land', ' ∧ ').replace('=', ' ＝ ')
    t = re.sub(r'(?<![<>/\w])([a-z])(?=<sub>|[ (])', r'<i>\1</i>', t)
    t = re.sub(r'\(1-', '(1−', t)
    return t


def formula_html(lines):
    eqs = []
    for l in lines:
        for part in l.split('\\qquad'):
            if part.strip():
                eqs.append(part)
    return '<div class="formula">%s</div>' % ''.join('<p>%s</p>' % tex_html(e) for e in eqs)


def quote_html(lines):
    lines = [l for l in lines]
    first = lines[0].strip() if lines else ''
    rest = [l for l in lines[1:] if l.strip()]
    if first == '**带走的话**':
        def tk(l):
            m = re.match(r'^(- |(\d+)\. )(.*)$', l.strip())
            if not m:
                return '<p>%s</p>' % inline(l)
            return '<p class="li"><span class="tm">%s</span>%s</p>' % ('%s.' % m[2] if m[2] else '·', inline(m[3]))
        return '<div class="takeaway"><span class="lab">带走的话</span>%s</div>' % ''.join(tk(l) for l in rest)
    if first == '**小账**':
        ps = []
        for l in rest:
            m = re.match(r'^(.{2,30}？)——(.*)$', l)
            m2 = None if m else re.match(r'^([^：]{2,20})：(.*)$', l)
            ps.append('<p><span class="lk">%s</span>%s</p>' % (inline(m[1]), inline(m[2])) if m else
                      ('<p><span class="lk">%s：</span>%s</p>' % (inline(m2[1]), inline(m2[2])) if m2 else '<p>%s</p>' % inline(l)))
        return '<div class="ledger"><span class="lab">小　账</span>%s</div>' % ''.join(ps)
    if first == '**九格卡**':
        ps = []
        for l in rest:
            m = re.match(r'^([^：]{2,24})：(.*)$', l)
            ps.append('<p><span class="lk">%s：</span>%s</p>' % (inline(m[1]), inline(m[2])) if m else '<p>%s</p>' % inline(l))
        return '<div class="ledger nine"><span class="lab">九格卡</span>%s</div>' % ''.join(ps)
    if first == '**本章判错句**' or first == '**判错句**':
        return '<div class="judge"><span class="lab">本章判错句</span>%s</div>' % ''.join('<p>%s</p>' % inline(l) for l in rest)
    if first == '**章旨**':
        return '<p class="chap-lead">%s</p>' % ''.join(inline(l) for l in rest)
    if first == '**想一想**':
        return '<div class="wonder"><span class="lab">想一想</span>%s</div>' % ''.join('<p>%s</p>' % inline(l) for l in rest)
    body = [l for l in lines if l.strip()]
    if first == '**这一章的问题**':
        return '<div class="qbox"><span class="lab">这一章的问题</span>%s</div>' % ''.join('<p>%s</p>' % inline(l) for l in rest)
    mq = re.match(r'^\*\*这一章的问题\*\*：(.*)$', first)
    if mq:
        return '<div class="qbox"><span class="lab">这一章的问题</span><p>%s</p></div>' % inline(mq[1])
    if len(body) == 1 and re.fullmatch(r'\*\*.+\*\*', body[0].strip()):
        return '<div class="pull"><p>%s</p></div>' % inline(body[0].strip()[2:-2])
    return '<blockquote class="verdict%s">%s</blockquote>' % (' long' if sum(len(l) for l in body) > 260 else '', ''.join('<p>%s</p>' % inline(l) for l in body))


def render(blocks, bib=False):
    h = []
    # 个别章的「带走的话」写成了普通段＋列表：排成和别章一样的方框（字不动）
    merged, i_ = [], 0
    while i_ < len(blocks):
        k_, b_ = blocks[i_]
        if k_ == 'p' and b_[0] == '**带走的话**' and i_ + 1 < len(blocks) and blocks[i_ + 1][0] == 'ul':
            merged.append(('quote', [b_[0]] + ['- ' + x for x in blocks[i_ + 1][1]]))
            i_ += 2
            continue
        merged.append(blocks[i_])
        i_ += 1
    for k, b in merged:
        if k == 'h3' and b[0].endswith('参考文献'):
            bib = True
            h.append('<h3 class="sec bibhead">%s</h3>' % inline(b[0]))
            continue
        if k == 'p':
            t = b[0]
            if re.fullmatch(r'〔[^〔〕]*〕', t):
                h.append('<p class="srcnote">%s</p>' % inline(t))
            else:
                if bib and t.startswith('核读与使用范围'):
                    h.append('<p class="bib sc">%s</p>' % inline(t))
                else:
                    h.append('<p%s>%s</p>' % (' class="bib"' if bib else '', inline(t)))
        elif k == 'h3':
            t = b[0]
            if t.startswith('◆'):
                h.append('<h3 class="sec"><span class="dia">◆</span>%s</h3>' % inline(t.lstrip('◆ ').strip()))
            else:
                h.append('<h3 class="sec">%s</h3>' % inline(t))
        elif k == 'h2':
            h.append('<h3 class="subhead">%s</h3>' % inline(b[0]))
        elif k == 'h4':
            h.append('<h4 class="ssec">%s</h4>' % inline(b[0]))
        elif k == 'quote':
            h.append(quote_html(b))
        elif k == 'table':
            h.append(table_html(b))
        elif k == 'ul':
            if bib:
                h.append(''.join('<p class="bib">%s</p>' % inline(x) for x in b))
            else:
                h.append('<ul class="ls">%s</ul>' % ''.join('<li>%s</li>' % inline(x) for x in b))
        elif k == 'ol':
            if bib:
                h.append(''.join('<p class="bib"><span class="bn">%s.</span> %s</p>' % (re.match(r'^(\d+)\. ', x)[1], inline(re.sub(r'^\d+\. ', '', x))) for x in b))
            else:
                start = int(re.match(r'^(\d+)\. ', b[0])[1])
                h.append('<ol class="ls"%s>%s</ol>' % (' start="%d"' % start if start != 1 else '',
                                                       ''.join('<li>%s</li>' % inline(re.sub(r'^\d+\. ', '', x)) for x in b)))
        elif k == 'formula':
            h.append(formula_html(b))
        elif k == 'orn':
            h.append('<div class="orn">◆</div>')
        elif k == 'pre':
            if any('外圈：一个大圆' in x for x in b):
                h.append(fig_board(b)); continue
            if b and b[0].split() == ['S1', 'S2', 'S3']:
                h.append(fig_grid(b)); continue
            ls_ = [x for x in b if x.strip()]

            def _p(x):
                head = re.fullmatch(r'【.*】|母题卡（空组版）|第n(\+1)?轮', x.strip())
                st = ' style="padding-left:%.1fem"' % ((len(x) - len(x.lstrip(' '))) * 0.5) if x.startswith(' ') else ''
                return '<p class="%s"%s>%s</p>' % ('hd' if head else 'ln', st, re.sub(r'\s{2,}', '　', html.escape(x.strip(), quote=False)))
            h.append('<div class="card code%s">%s</div>' % (' long' if len(ls_) > 12 else '', ''.join(_p(x) for x in ls_)))
    return '\n'.join(h)


def with_endmark(inner):
    """章末「带走的话＋小账＋◆」绑成一块，禁止拆页——否则会掉出只有一个 ◆ 或只有小账的孤页。"""
    end = '<div class="endmark">◆</div>'
    m = re.search(r'(?:<div class="(?:ledger nine|takeaway|judge|wonder|ledger)">.*?</div>\s*)+$', inner, re.S)
    if m:
        pre = re.sub(r'<p>((?:(?!<p[ >]).)*</p>\s*)$', r'<p class="keepnext">\1', inner[:m.start()], flags=re.S)
        pre = re.sub(r'<(ol|ul) class="ls"((?:(?!<(?:ol|ul) ).)*</\1>\s*)$', r'<\1 class="ls keepnext"\2', pre, flags=re.S)
        n_ = len(re.sub(r'<[^>]+>', '', m.group(0)))
        return pre + '<div class="chapend%s">' % (' open' if n_ > 300 else '') + m.group(0) + end + '</div>'
    # 章末没有方框的：末段至少带 5 行过页，不留两三行的尾页
    inner = re.sub(r'<p>((?:(?!<p[ >]).)*</p>\s*)$', r'<p class="tailp">\1', inner, flags=re.S)
    return inner + end


EMB = ('<svg class="emb" viewBox="0 0 40 40"><circle cx="20" cy="20" r="13" fill="none" stroke="#B08A3C" stroke-width="1.3"/>'
       '<line x1="20" y1="3" x2="20" y2="37" stroke="#B08A3C" stroke-width="0.9"/><line x1="3" y1="20" x2="37" y2="20" stroke="#B08A3C" stroke-width="0.9"/>'
       '<path d="M20 12 L24.5 18 L20 27 L15.5 18 Z" fill="none" stroke="#1F3A5F" stroke-width="1.1"/>'
       '<circle cx="20" cy="18" r="1.6" fill="#B08A3C"/><circle cx="12.5" cy="28" r="1.5" fill="#58A9B5"/></svg>')


def cn2int(s):
    d = {'〇': 0, '零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
    if '百' in s:
        h, _, r = s.partition('百')
        v = d[h] * 100 if h else 100
        if not r:
            return v
        if '十' in r:
            a, _, b = r.partition('十')
            return v + (d[a] if a else 1) * 10 + (d[b] if b else 0)
        return v + (d[r[-1]] if r else 0)
    if '十' in s:
        a, _, b = s.partition('十')
        return (d[a] if a else 1) * 10 + (d[b] if b else 0)
    return d[s]


def spaced(label):
    return label if '（' in label else ' '.join(label)


def notes_html(stem):
    n = NOTES.get(stem)
    if not n or not n['paras']:
        return ''
    h = ['<div class="srcblock"><h4 class="srchead">%s</h4>' % inline(n['title'] or '来源注')]
    for p in n['paras']:
        p = re.sub(r'^- ', '', p)
        hang = bool(re.match(r'^(〔\d+〕|\[\d+\])', p))
        h.append('<p class="sn%s">%s</p>' % ('' if hang else ' cont', inline(p)))
    h.append('</div>')
    return ''.join(h)


def build_sections():
    """返回 [(kind, id, toc_title, level, html)]；kind: front/main/part/chapter/back/cp。"""
    secs, n = [], 0

    def sid():
        nonlocal n
        n += 1
        return 's%d' % n

    # ── 出版信息（由 meta 生成）──
    han = M.body_han(ROOT)
    rows = [('书名', '《%s》' % M.TITLE), ('副题', M.SUBTITLE), ('英文书名', M.TITLE_EN), ('著者', M.AUTHOR),
            ('执笔', '王德生著；正文由 AI（Claude）协作统稿与审校'),
            ('出版', '%s（%s）· 新加坡' % (M.PUBLISHER, M.PUBLISHER_EN)),
            ('编号', '德麦国际专著第 %d 号' % M.NO), ('ISBN', M.ISBN), ('定价', M.PRICE),
            ('开本', '170 mm × 240 mm'),
            ('字数', '约 %.1f 万字（总导论、二十一编一百一十五章与总合论正文 %s 个汉字）' % (han / 10000, format(han, ','))),
            ('版次', M.EDITION_SP), ('完稿', '2026 年 11 月 7 日')]
    notes = ['AI 协作声明：本书由王德生著；正文由 AI（Claude）协作统稿与审校，经初审、复审、思想审校与终审。本书未经独立学术评审。',
             '本书以显露、差异序列与特征纠缠为共同线索，依次展开本体论、方法论与思想创新论，全书包括总导论、二十一编一百一十五章及总合论。构造情境、模拟分析、待检假说与已有证据保持各自身份；书中的构造情境是为论证设置的，不是调查记录，也不对应真实记录。各章末的来源注保留实际读取范围及其限制。',
             '版权所有，侵权必究。']
    tb = ''.join('<tr><th>%s</th><td>%s</td></tr>' % (inline(a), inline(c)) for a, c in rows)
    nt = ''.join('<p%s>%s</p>' % (' class="cp-right"' if '侵权必究' in x else '', inline(x)) for x in notes)
    secs.append(('cp', sid(), '出版信息', 0,
                 '<div class="cp-title">出 版 信 息</div><table class="cp">%s</table><div class="cp-notes">%s</div>' % (tb, nt)))

    text = BOOK_MD.read_text(encoding='utf-8')
    tops, cur = [], None
    for k, b in blocks_of(text):
        if k == 'h1':
            cur = [b[0], []]; tops.append(cur)
        elif cur is not None and k != 'hr':
            cur[1].append((k, b))
    dom_of = {p['n']: p['domain'] for p in STRUCT['parts']}
    first_of_dom = {}
    for g in STRUCT['groups']:
        first_of_dom[g['parts'][0]] = g
    gnum = {g['name']: i + 1 for i, g in enumerate(STRUCT['groups'])}
    for title, bl in tops:
        name, _, sub = title.partition('　')
        if name == '作者介绍':
            secs.append(('front', sid(), name, 1, '<h1 class="fs-title">%s</h1><div class="rule"></div>%s' % (name, render(bl))))
        elif name == '总导论':
            csid = sid()
            nb = notes_html('intro_anchor')
            secs.append(('front', csid, name + '　' + sub, 1,
                         '<h1 class="fs-title">%s</h1><div class="fs-sub">%s</div><div class="rule"></div>%s' % (name, inline(sub), with_endmark(render(bl)) + nb)))
        elif name == '总合论':
            nb = notes_html('conclusion')
            secs.append(('back', sid(), name + '　' + sub, 1,
                         '<h1 class="fs-title">%s</h1><div class="fs-sub">%s</div><div class="rule"></div>%s' % (name, inline(sub), with_endmark(render(bl)) + nb)))
        else:
            m = re.match(r'^第([一二三四五六七八九十]+)编$', name)
            assert m, name
            pn = cn2int(m[1])
            intro, i = [], 0
            while i < len(bl) and bl[i][0] != 'h2':
                if bl[i][0] == 'p' and bl[i][1][0] != '**编序**':
                    intro.append('<p class="bianxu">%s</p>' % inline(bl[i][1][0]))
                i += 1
            dom = dom_of[pn]
            grp = '第%s部分　%s' % (CN[gnum[dom]], dom)
            part_i = len(secs)
            psid = sid()
            if pn in first_of_dom:
                GROUP_START[psid] = grp
            kicker = '%s · %s' % (name, sub)
            secs.append(['part', psid, '%s　%s' % (name, sub), 1,
                         '%s<div class="grp">%s</div><div class="part-label">%s</div><h1 class="part-title" data-h="%s">%s</h1><div class="rule"></div>'
                         '%s@@PARTTOC@@'
                         % (EMB.replace('#1F3A5F', '#FBF8F0'), grp, spaced(name), html.escape(kicker), inline(sub),
                            ('<div class="daoyu">编　序</div><div class="part-intro">%s</div>' % ''.join(intro)) if intro else '')])
            ptoc = []
            while i < len(bl):
                t = bl[i][1][0]
                cm = re.match(r'^(.+?)　(.*)$', t)
                j = i + 1
                while j < len(bl) and bl[j][0] != 'h2':
                    j += 1
                body = [x for x in bl[i + 1:j] if x[0] != 'hr']
                lab = cm[1]
                nm = re.fullmatch(r'第 ?(\d+) ?章', lab)
                num = int(nm[1])
                csid = sid()
                ptoc.append('<li><span class="n">%s</span><span class="t">%s</span><span class="pg">@@PG:%s@@</span></li>' % (lab, inline(cm[2]), csid))
                secs.append(('chapter', csid, '%s　%s' % (lab, cm[2]), 2,
                             '<div class="chap-kicker">%s</div><div class="chapnum">%02d</div><div class="chap-label">%s</div>'
                             '<h2 class="chap-title" data-h="%s">%s</h2><div class="rule"></div>%s%s'
                             % (html.escape(kicker), num, lab, html.escape(lab + ' · ' + cm[2]), inline(cm[2]),
                                with_endmark(render(body)), notes_html('ch%03d' % num))))
                i = j
            secs[part_i][4] = secs[part_i][4].replace('@@PARTTOC@@', '<ul class="part-toc">%s</ul>' % ''.join(ptoc))
            secs[part_i] = tuple(secs[part_i])
    return secs


# ───────────────────────── 印刷 CSS ─────────────────────────
def print_css(fonts, W, H, body_pt, lh, margin, fol='decimal'):
    t, o, b, i = margin
    F = fonts.resolve()
    return f"""
@page{{size:{W}mm {H}mm;margin:{t}mm {o}mm {b}mm {i}mm;background:#FBF8F0;
  @top-left{{content:none}} @top-right{{content:none}}}}
@page :left{{margin-left:{o}mm;margin-right:{i}mm;
  @top-left{{content:string(book,first-except);width:100%;text-align:left;font:{body_pt*0.62:.2f}pt 'Noto Sans CJK SC';letter-spacing:.06em;color:#7E7664;vertical-align:bottom;padding-bottom:2mm;margin-bottom:4.5mm;border-bottom:.4pt solid #D8CFBB}}
  @bottom-left{{content:counter(page,{fol});width:9mm;text-align:left;font:{body_pt*0.72:.2f}pt 'Noto Serif CJK SC';color:#6F6A5C;vertical-align:top;padding-top:1.6mm;margin-top:5mm;border-top:.8pt solid #B08A3C}}}}
@page :right{{
  @top-right{{content:string(chap,first-except);width:100%;text-align:right;font:{body_pt*0.62:.2f}pt 'Noto Sans CJK SC';letter-spacing:.06em;color:#7E7664;vertical-align:bottom;padding-bottom:2mm;margin-bottom:4.5mm;border-bottom:.4pt solid #D8CFBB}}
  @bottom-right{{content:counter(page,{fol});width:9mm;text-align:right;font:{body_pt*0.72:.2f}pt 'Noto Serif CJK SC';color:#6F6A5C;vertical-align:top;padding-top:1.6mm;margin-top:5mm;border-top:.8pt solid #B08A3C}}}}
@page :blank{{@top-left{{content:none;border:none}} @top-right{{content:none;border:none}} @bottom-left{{content:none;border:none}} @bottom-right{{content:none;border:none}}}}
@page clean{{@top-left{{content:none;border:none}} @top-right{{content:none;border:none}} @bottom-left{{content:none;border:none}} @bottom-right{{content:none;border:none}}}}
@page opener:left{{@top-left{{content:none;border:none}}}}
@page opener:right{{@top-right{{content:none;border:none}}}}
@page partpage{{background:#1F3A5F;@top-left{{content:none;border:none}} @top-right{{content:none;border:none}} @bottom-left{{content:none;border:none}} @bottom-right{{content:none;border:none}}}}
body{{font-family:'Noto Serif CJK SC','FreeSerif';font-size:{body_pt}pt;line-height:{lh};color:#2A2824;margin:0;string-set:book "{META['title']}"}}
p{{margin:0 0 .42em;text-indent:2em;text-align:justify;orphans:2;widows:2}}
strong{{color:#1F3A5F;font-weight:700}}
em{{font-style:italic}}
.clean{{page:clean}}
section{{break-before:page}}
section.part{{page:partpage;break-before:right;text-align:center;padding-top:22mm;color:#EFE8D6}}
.emb{{width:17mm;height:17mm;display:block;margin:0 auto 8mm}}
.part-label{{font:700 {body_pt*0.86:.2f}pt 'Noto Sans CJK SC';color:#D9B96E;letter-spacing:.9em;margin-bottom:5mm;text-indent:.9em}}
.part-title{{font:700 {body_pt*1.72:.2f}pt/1.5 'Noto Serif CJK SC';color:#FBF8F0;margin:0 10mm 5mm;string-set:chap attr(data-h)}}
.part .rule{{margin:0 auto 11mm;border-top-color:#D9B96E;width:18mm}}
ul.part-toc{{list-style:none;margin:0 6mm;padding:0;text-align:left}}
ul.part-toc li{{display:flex;font-size:{body_pt*0.86:.2f}pt;line-height:1.6;padding:1.35mm 0;border-bottom:.35pt solid rgba(239,232,214,.22);color:#EFE8D6}}
ul.part-toc .n{{flex:0 0 auto;width:4.6em;color:#D9B96E;font:400 {body_pt*0.74:.2f}pt/1.85 'Noto Sans CJK SC'}}
ul.part-toc .t{{flex:1}}
ul.part-toc .pg{{flex:0 0 auto;width:3em;text-align:right;color:#D9B96E}}
.daoyu{{font:700 8.5pt 'Noto Sans CJK SC';color:#B08A3C;letter-spacing:.6em;margin-bottom:5mm}}
.part-intro{{text-align:left}}
.part-intro p{{font-size:{body_pt*0.93:.2f}pt;color:#D8D1BF;text-indent:0}}
.rule{{width:15mm;border-top:1pt solid #B08A3C;margin:3.5mm 0 8mm}}
.chap-kicker{{font:400 {body_pt*0.66:.2f}pt 'Noto Sans CJK SC';color:#8A8578;letter-spacing:.14em;margin-top:0}}
.chapnum{{font:300 {body_pt*4.2:.2f}pt/1 'Noto Serif CJK SC';color:#CDB27A;margin-top:9mm;letter-spacing:.02em}}
.chap-label{{font:700 {body_pt*0.72:.2f}pt 'Noto Sans CJK SC';color:#B08A3C;margin:2.5mm 0 1.5mm;letter-spacing:.12em}}
.chap-title{{font:700 {body_pt*1.62:.2f}pt/1.42 'Noto Serif CJK SC';color:#1F3A5F;margin:0;string-set:chap attr(data-h),book "{META['title']}";bookmark-level:2;bookmark-label:content()}}
p.keepnext{{break-after:avoid}}
p.tailp{{widows:5;break-after:avoid}}
.fs-title{{font:700 {body_pt*1.62:.2f}pt/1.4 'Noto Serif CJK SC';color:#1F3A5F;margin:14mm 0 1mm;letter-spacing:.12em;string-set:chap content(),book "{META['title']}";bookmark-level:1;bookmark-label:content()}}
.fs-title.appx{{bookmark-level:2;font-size:15pt;letter-spacing:.06em}}
.part-title{{bookmark-level:1;bookmark-label:content()}}
.fs-sub{{font:400 10.4pt 'Noto Serif CJK SC';color:#B08A3C;margin-top:1.5mm}}
h3.sec{{font:700 {body_pt*1.04:.2f}pt/1.6 'Noto Sans CJK SC';color:#1F3A5F;margin:7mm 0 2.6mm;break-after:avoid}}
h3.sec .dia{{color:#B08A3C;font-size:.78em;margin-right:.45em;vertical-align:.08em}}
h3.sec.bibhead{{margin-top:9mm;padding-top:3mm;border-top:.5pt solid #D9CDB0;font-size:{body_pt*0.92:.2f}pt;color:#8A6E3A;letter-spacing:.2em}}
p.bib{{text-indent:-2em;padding-left:2em;font-size:{body_pt*0.8:.2f}pt;line-height:1.62;margin:0 0 1.1mm;text-align:left;overflow-wrap:anywhere}}
h4.ssec{{font:700 {body_pt*0.97:.2f}pt/1.6 'Noto Serif CJK SC';color:#5B4A26;margin:4mm 0 1.6mm;break-after:avoid}}
h4.ssec::before{{content:"";display:inline-block;width:2.4mm;border-top:.8pt solid #B08A3C;vertical-align:.3em;margin-right:1.6mm}}
h3.subhead{{font:700 {body_pt*1.05:.2f}pt/1.6 'Noto Serif CJK SC';color:#1F3A5F;margin:6mm 0 2.5mm;break-after:avoid}}
.takeaway{{background:#F6F1E4;border-left:1.6pt solid #B08A3C;padding:2.2mm 4mm 2.4mm;margin:4.5mm 0 3mm;break-inside:avoid}}
.takeaway .lab{{display:block;font:700 {body_pt*0.68:.2f}pt 'Noto Sans CJK SC';color:#8A6E3A;letter-spacing:.5em;margin-bottom:1.6mm}}
.takeaway p{{text-indent:0;margin:0 0 .5mm;font-weight:500;color:#1F3A5F;font-size:{body_pt*0.98:.2f}pt;line-height:1.82}}
.takeaway p strong{{font-weight:700}}
.takeaway p.li{{padding-left:1.3em;text-indent:-1.3em;margin:0 0 1mm}}
.takeaway .tm{{display:inline-block;width:1.3em;text-indent:0;color:#B08A3C}}
.card.code p{{font-size:{body_pt*0.82:.2f}pt;line-height:1.72;margin:0;text-align:left;overflow-wrap:anywhere}}
.card.code p.hd{{font-weight:700;color:#1F3A5F;margin:0 0 1mm}}
.card.code p.ln+p.hd{{margin-top:2.2mm}}
.card.long{{break-inside:auto;box-decoration-break:clone}}
.fig{{margin:4.5mm 0 5mm;break-inside:avoid}}
.fig p{{text-indent:0}}
.fig.board{{background:#F6F1E4;border:.6pt solid #D8CFBB;padding:4mm 4mm 5mm;text-align:center}}
.fig.board .note{{text-align:center;font-size:{body_pt*0.8:.2f}pt;color:#7E7664;margin:0 0 3.5mm}}
.fig.board .node{{display:inline-block;font:700 {body_pt*0.86:.2f}pt/1.5 'Noto Sans CJK SC';color:#1F3A5F;background:#FBF8F0;border:.7pt solid #B08A3C;padding:1.2mm 3mm}}
.fig.board .node.core{{background:#1F3A5F;color:#FBF8F0;border-color:#1F3A5F}}
.fig.board .stem{{color:#B08A3C;font-size:{body_pt*0.8:.2f}pt;line-height:1.15;margin:.8mm 0}}
.fig.board .row{{display:flex;justify-content:center;align-items:center}}
.fig.board .ar{{color:#B08A3C;font-size:{body_pt*0.8:.2f}pt;margin:0 1.2mm}}
.fig.ninegrid table{{width:100%;border-collapse:collapse;table-layout:fixed}}
.fig.ninegrid th{{font:700 {body_pt*0.8:.2f}pt 'Noto Sans CJK SC';color:#FBF8F0;background:#1F3A5F;padding:1.2mm;text-align:center}}
.fig.ninegrid thead th:first-child{{width:9%}}
.fig.ninegrid td{{border:.6pt solid #CFC4A8;padding:1.6mm 1.8mm;vertical-align:top;font-size:{body_pt*0.74:.2f}pt;line-height:1.55;background:#FBF8F0}}
.fig.ninegrid td b,.fig.ninegrid td span,.fig.ninegrid td i{{display:block;font-style:normal}}
.fig.ninegrid td b{{font:700 {body_pt*0.72:.2f}pt/1.5 'Noto Sans CJK SC';color:#1F3A5F;margin-bottom:.6mm}}
.fig.ninegrid td i{{color:#7E7664}}
.fig.ninegrid td.g{{background:#F1EAD6}}
.fig.ninegrid td.empty{{background:#E9F3F1;border:1.1pt solid #58A9B5}}
.fig.ninegrid td.empty span{{font-weight:700;color:#2F7C88}}
.ledger{{background:#F4EFE3;border-left:1.6pt solid #D8CFBB;padding:2mm 4mm 2.2mm;margin:3mm 0 2mm;break-inside:avoid;display:flex;gap:4mm;flex-wrap:wrap}}
.ledger .lab{{flex:0 0 100%;margin-bottom:.4mm!important}}
.ledger p{{flex:1 1 100%}}
.ledger .lab{{display:block;font:700 {body_pt*0.68:.2f}pt 'Noto Sans CJK SC';color:#5A554A;letter-spacing:.3em;margin-bottom:1.2mm}}
.ledger p{{text-indent:0;margin:0 0 .6mm;font-size:{body_pt*0.86:.2f}pt;line-height:1.75;color:#5A554A}}
.ledger .lk{{color:#1F3A5F;font-weight:700}}
.chapend{{break-inside:avoid}}
.chapend.open{{break-inside:auto}}
.chapend.open>div{{break-after:avoid}}
.chapend.open>div>p:last-child{{break-after:avoid}}
.endmark{{break-before:avoid}}
.chapend.open .takeaway{{break-inside:auto;box-decoration-break:clone}}
.chapend.open .takeaway p{{break-inside:avoid}}
.takeaway .lab{{break-after:avoid}}
ol.keepnext,ul.keepnext{{break-after:avoid}}
ol.keepnext li:last-child,ul.keepnext li:last-child{{break-after:avoid}}
.chapend .endmark{{break-before:avoid}}
.wonder{{border-left:1.6pt solid #58A9B5;padding:1.8mm 4mm;margin:2mm 0 1mm;break-inside:avoid}}
.wonder .lab{{display:block;font:700 {body_pt*0.68:.2f}pt 'Noto Sans CJK SC';color:#2F7C88;letter-spacing:.4em;margin-bottom:1mm}}
.wonder p{{text-indent:0;margin:0;font-size:{body_pt*0.93:.2f}pt;color:#4A463D}}
.ledger.nine{{display:block}}
.ledger.nine p{{margin:0 0 .5mm}}
.judge{{border-left:1.6pt solid #8A6E3A;padding:1.8mm 4mm;margin:2mm 0 1mm;break-inside:avoid}}
.judge .lab{{display:block;font:700 {body_pt*0.68:.2f}pt 'Noto Sans CJK SC';color:#8A6E3A;letter-spacing:.3em;margin-bottom:1mm}}
.judge p{{text-indent:0;margin:0;font-size:{body_pt*0.9:.2f}pt;color:#4A463D}}
.endmark{{text-align:center;color:#B08A3C;font-size:8pt;margin-top:3.5mm}}
.orn{{text-align:center;color:#B08A3C;font-size:7.5pt;margin:3mm 0}}
.pull{{margin:5mm 6%;padding:3mm 0;border-top:.8pt solid #B08A3C;border-bottom:.8pt solid #B08A3C;text-align:center;break-inside:avoid}}
.pull p{{text-indent:0;text-align:center;font-weight:700;color:#1F3A5F;font-size:{body_pt*1.12:.2f}pt;margin:0}}
/*Q*/.qbox{{background:#F7F3E8;border-left:1.6pt solid #58A9B5;padding:2.2mm 4mm;margin:2mm 0 4mm;break-inside:avoid}}
.qbox .lab{{display:block;font:700 {body_pt*0.68:.2f}pt 'Noto Sans CJK SC';color:#2F7C88;letter-spacing:.3em;margin-bottom:1mm}}
.qbox p{{text-indent:0;margin:0;font-size:{body_pt*0.93:.2f}pt;color:#4A463D}}
.chapter.t1 p,.chapter.t1 li{{line-height:{lh-0.05:.3f}}}
.chapter.t2 p,.chapter.t2 li{{line-height:{lh-0.10:.3f}}}
.chapter.t2 h3.sec{{margin-top:4.5mm}}
.chapter.t3 p,.chapter.t3 li{{line-height:{lh-0.15:.3f};margin-bottom:.3em}}
.chapter.t3 h3.sec{{margin-top:4mm}}
.chapter.t4 p,.chapter.t4 li{{line-height:{lh-0.2:.3f};margin-bottom:.25em}}
.chapter.t4 h3.sec{{margin-top:3.5mm}}
blockquote.verdict{{background:#F6F1E4;border-left:1.6pt solid #B08A3C;margin:4mm 0;padding:2.6mm 4mm;break-inside:avoid}}
blockquote.verdict p{{text-indent:0;margin:0;font-weight:700;color:#1F3A5F}}
blockquote.verdict.long{{break-inside:auto;box-decoration-break:clone}}
blockquote.verdict.long p{{font-weight:500;margin:0 0 1mm}}
blockquote.verdict.long p strong{{font-weight:700}}
.tw{{margin:3.5mm 0}}
table.tb{{width:100%;border-collapse:collapse;table-layout:fixed;font-size:{body_pt*0.8:.2f}pt;line-height:1.6;border-bottom:.8pt solid #1F3A5F}}
.tw.short{{break-inside:avoid}}
table.tb tbody tr:first-child{{break-after:avoid}}
table.tb tbody tr:last-child{{break-before:avoid}}
table.tb .ctr{{text-align:center}}
table.tb th{{background:#1F3A5F;color:#FBF8F0;font:700 {body_pt*0.78:.2f}pt/1.5 'Noto Sans CJK SC';padding:1.4mm 1.6mm;text-align:left;vertical-align:bottom}}
table.tb td{{overflow-wrap:anywhere}}
table.tb tr{{break-inside:avoid}}
table.tb.w5 td{{font-size:{body_pt*0.74:.2f}pt;line-height:1.55}}
table.tb.dense td{{padding-top:.7mm;padding-bottom:.7mm}}
table.tb td{{border-bottom:.5pt solid #E4DCCB;padding:1.3mm 1.6mm;vertical-align:top}}
table.tb tr:nth-child(even) td{{background:#F6F1E4}}
ul.ls,ol.ls{{margin:1mm 0 2.5mm;padding-left:2.2em}} ul.ls li,ol.ls li{{margin:.4mm 0}}
p.bib{{text-indent:-2em;padding-left:2em;font-size:{body_pt*0.88:.2f}pt;line-height:1.75;margin-bottom:1.2mm;text-align:left;overflow-wrap:anywhere}}
p.bib.sc{{text-indent:0;color:#6A6558;font-size:{body_pt*0.8:.2f}pt;margin-bottom:3.2mm;padding-left:2em}}
p.bib .bn{{color:#B08A3C}}
.card{{background:#F6F1E4;border:.6pt solid #D8CFBB;border-left:1.6pt solid #1F3A5F;padding:2.6mm 4mm;margin:4mm 0;break-inside:avoid}}
.card p{{text-indent:0;margin:0 0 .5mm;font:{body_pt*0.86:.2f}pt/1.75 'Noto Sans CJK SC';color:#2A2824;text-align:left}}
p.srcnote{{text-indent:0;font:{body_pt*0.8:.2f}pt/1.7 'Noto Sans CJK SC';color:#8A8578;margin:1mm 0 2.6mm}}
.titlepage .big2{{font:700 30pt/1.35 'Noto Serif CJK SC';color:#1F3A5F;margin:2mm 0 5mm;letter-spacing:.1em}}
/* 书名页 */
section.clean,section.epi{{page:clean}}
.titlepage{{page:clean;padding-top:30mm;border-left:1.6pt solid #B08A3C;padding-left:7mm;height:190mm;position:relative}}
section.epi{{break-before:page;padding-top:62mm;text-align:center}}
section.epi p{{text-indent:0;text-align:center;font:400 12.4pt/2.1 'Noto Serif CJK SC';color:#1F3A5F;letter-spacing:.12em;margin:0}}
section.epi p.by{{font:400 9.5pt 'Noto Serif CJK SC';color:#8A8578;margin-top:6mm;letter-spacing:.2em}}
p.chap-lead{{text-indent:0;text-align:left;font:400 {body_pt*0.98:.2f}pt/1.8 'Noto Serif CJK SC';color:#5A554B;margin:-1mm 0 6mm}}
.titlepage .pre{{font:400 {body_pt*0.86:.2f}pt 'Noto Sans CJK SC';color:#8A6E3A;letter-spacing:.3em}}
.titlepage .big{{font:700 40pt/1.2 'Noto Serif CJK SC';color:#1F3A5F;margin:3mm 0 5mm;letter-spacing:.12em}}
.titlepage .sub{{font:400 10.5pt/1.7 'Noto Serif CJK SC';color:#B08A3C}}
.titlepage .rule{{margin:6mm 0 0}}
.titlepage .au{{margin-top:30mm;font:400 {body_pt*1.05:.2f}pt 'Noto Serif CJK SC';color:#2A2824;letter-spacing:.2em}}
.titlepage .pub{{position:absolute;bottom:0;font:700 8.5pt 'Noto Sans CJK SC';color:#1F3A5F;letter-spacing:.35em}}
.titlepage .pub span{{display:block;font:400 6.8pt 'Noto Sans CJK SC';color:#8A8578;letter-spacing:.08em;margin-top:1mm}}
/* 出版信息 */
.cp-title{{font:700 11pt 'Noto Sans CJK SC';color:#1F3A5F;letter-spacing:.8em;text-align:center;margin:6mm 0 5mm}}
table.cp{{width:100%;border-collapse:collapse;font-size:{body_pt*0.76:.2f}pt;line-height:1.65}}
table.cp th{{font:400 {body_pt*0.7:.2f}pt/1.8 'Noto Sans CJK SC';color:#7E7664;text-align:left;width:17mm;padding:1.5mm 2mm;vertical-align:top}}
table.cp td{{padding:1.5mm 2mm;color:#2A2824}}
table.cp tr:nth-child(odd){{background:#F4EFE3}}
.cp-notes{{margin-top:5mm}}
.cp-notes p{{text-indent:0;font-size:{body_pt*0.68:.2f}pt;line-height:1.72;color:#5A554A;margin-bottom:1.3mm}}
.cp-right{{margin-top:3mm!important;letter-spacing:.2em}}
/* 题辞 */
.epi{{page:clean;padding-top:60mm;text-align:center}}
.epi p{{text-indent:0;text-align:center;font-size:11.5pt;line-height:2.1;color:#1F3A5F}}
.epi .by{{font-size:8.6pt;color:#8A8578;margin-top:5mm}}
/* 第 607 号增改 */
.grp{{font:400 {body_pt*0.74:.2f}pt 'Noto Sans CJK SC';color:#D9B96E;letter-spacing:.5em;margin:-3mm 0 3mm;text-indent:.5em}}
.formula{{margin:4mm 8%;padding:3mm 0;text-align:center;break-inside:avoid;border-top:.5pt solid #D8CFBB;border-bottom:.5pt solid #D8CFBB}}
.formula p{{text-indent:0;text-align:center;margin:0 0 1.2mm;font-size:{body_pt*1.04:.2f}pt;line-height:1.9}}
.formula sub{{font-size:.72em;line-height:0}}
code{{font-family:'DejaVu Sans Mono','Noto Sans CJK SC',monospace;font-size:.86em;overflow-wrap:anywhere}}
.srcblock{{margin-top:7mm;padding-top:2.4mm;border-top:.5pt solid #D8CFBB}}
h4.srchead{{font:700 {body_pt*0.74:.2f}pt 'Noto Sans CJK SC';color:#8A6E3A;letter-spacing:.35em;margin:0 0 1.6mm;break-after:avoid}}
p.sn{{text-indent:-2.1em;margin:0 0 1.1mm;padding-left:2.1em;text-align:left;font:{body_pt*0.74:.2f}pt/1.68 'Noto Sans CJK SC','FreeSerif';color:#8A8578;overflow-wrap:anywhere}}
p.sn.cont{{text-indent:0;padding-left:0}}
section.backm{{break-before:right}}
.toc li.g{{font:700 {body_pt*0.78:.2f}pt 'Noto Sans CJK SC';letter-spacing:.3em;color:#B08A3C;margin-top:5mm;break-after:avoid}}
/* 目录 */
.toc h1{{string-set:chap "目录",book "{META['title']}";font:700 {body_pt*1.62:.2f}pt 'Noto Serif CJK SC';color:#1F3A5F;letter-spacing:.4em;margin:10mm 0 2mm}}
.toc ul{{list-style:none;padding:0;margin:4mm 0 0}}
.toc li{{display:flex;font-size:{body_pt*0.88:.2f}pt;line-height:1.7;align-items:baseline}}
.toc li a{{color:inherit;text-decoration:none}}
.toc li .t{{flex:0 1 auto}}
.toc li::after{{content:none}}
.toc li .pg{{order:3}}
.toc li .t+.pg{{flex:1 1 auto;border:none;background:none}}
.toc li .pg{{color:#6F6A5C;font-family:'Noto Serif CJK SC';min-width:9mm;text-align:right}}
.toc li.p{{font-weight:700;color:#1F3A5F;margin-top:3.6mm;padding-bottom:.6mm;border-bottom:.5pt solid #CDB27A;break-after:avoid}}
.toc li.p .pg{{color:#1F3A5F}}
.toc li.c{{padding-left:2em;color:#2A2824}}
.toc li.f{{margin-top:1mm;color:#1F3A5F}}
.toc li.a{{padding-left:2em;color:#2A2824}}
"""


def toc_block(secs, pages, roman_ids):
    def roman(n):
        vals = [(10, 'x'), (9, 'ix'), (5, 'v'), (4, 'iv'), (1, 'i')]
        s = ''
        for v, r in vals:
            while n >= v:
                s += r; n -= v
        return s
    li = []
    for kind, sid, title, lvl, _ in secs:
        if kind == 'cp':
            continue
        cls = {'part': 'p', 'chapter': 'c'}.get(kind, 'f')
        if kind == 'back' and lvl == 2:
            cls = 'a'
        pg = pages.get(sid)
        pgs = '' if pg is None else (roman(pg) if sid in roman_ids else str(pg))
        if sid in GROUP_START:
            li.append('<li class="g"><span class="t">%s</span><span class="pg"></span></li>' % GROUP_START[sid])
        li.append('<li class="%s"><span class="t"><a href="#%s">%s</a></span><span class="pg">%s</span></li>'
                  % (cls, sid, inline(title), pgs))
    return '<section class="toc front-sec"><h1>目录</h1><div class="rule"></div><ul>%s</ul></section>' % ''.join(li)


TITLEPAGE = f"""<div class="titlepage"><div class="pre">德麦国际专著 · 第 {META['no']} 号</div><div class="big" style="font-size:34pt;line-height:1.5;letter-spacing:.12em">SDE思想大全</div><div class="sub" style="font-size:12pt">{META['subtitle']}</div><div class="rule"></div><div class="au">{META['author']}　著</div>
<div class="pub">{META['publisher']}<span>{META['publisher_en']} · Singapore</span></div></div>"""
EPIGRAPH = ''


def html_doc(css, inner):
    return ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><style>%s</style></head><body>%s</body></html>'
            % (css, inner))


TIGHT = {}


def sec_html(kind, sid, title, lvl, body):
    cls = {'part': 'part', 'chapter': 'chapter'}.get(kind, 'front-sec' if kind in ('front', 'main', 'cp') else 'backm')
    # 第 363 号：后置照第 220 号带页眉（不进 opener 页）；导论与附录各件收一档行距，免得章尾孤页
    return '<section class="%s" id="%s">%s</section>' % (cls, sid, body)



TAIL_DIR = Path(__file__).parent


def _tails_doc(doc_html, css):
    import weasyprint
    d = weasyprint.HTML(string=html_doc(css, doc_html), base_url=str(ROOT)).render()
    last = {}

    def iter_text(b):
        if type(b).__name__ == 'TextBox':
            yield b
        for c in getattr(b, 'children', []):
            yield from iter_text(c)

    def walk(b):
        el = getattr(b, 'element', None)
        if type(b).__name__ == 'LineBox' and el is not None and el.get('data-i'):
            last[int(el.get('data-i'))] = ''.join(t.text for t in iter_text(b))
            return
        for c in getattr(b, 'children', []):
            walk(c)
    for pg in d.pages:
        walk(pg._page_box)
    return d, last


def _hk(s):
    import hashlib
    return hashlib.md5(s.split('</p>')[0].encode()).hexdigest()[:12]


def fit_chunk(args):
    """一块（一编）：段尾只剩一两个字的段落，给极小负字距收回；返回 (html, levels, 页数, 锚点页)。块内行宽与页码奇偶无关，可单独排。"""
    chunk, css, base = args
    paras = re.split(r'(?=<p(?: class="(?:keepnext|li|tailp)")?>)', chunk)

    def apply(levels):
        out, idx = [paras[0]], 0
        for s in paras[1:]:
            idx += 1
            lv = levels.get(_hk(s), 0)
            head = re.match(r'<p( class="[^"]*")?>', s)
            st = ' style="letter-spacing:%.3fem"' % (-0.015 * lv) if lv else ''
            out.append('<p data-i="%d"%s%s>' % (idx, head[1] or '', st) + s[head.end():])
        return ''.join(out)
    levels = dict(base)
    hkeys = {i + 1: _hk(s) for i, s in enumerate(paras[1:])}
    for round_ in range(8):
        h = apply(levels)
        d, t = _tails_doc(re.sub(r'@@PG:s\d+@@', '888', h), css)
        bad = [i for i, s in t.items() if len(re.sub(r'\s', '', s)) <= 2]
        bad = [i for i in bad if len(re.sub(r'<[^>]+>', '', paras[i].split('</p>')[0])) > 12]
        if not bad:
            break
        changed = False
        for i in bad:
            k = hkeys[i]; cur = levels.get(k, 0)
            nxt = cur + 1 if 0 <= cur < 3 else (-1 if cur == 3 else (cur - 1 if -3 < cur < 0 else None))
            if nxt is not None:
                levels[k] = nxt; changed = True
        if not changed:
            break
    anchors = {}
    for pno, pg in enumerate(d.pages, 1):
        for a in pg.anchors:
            if re.fullmatch(r's\d+', a) and a not in anchors:
                anchors[a] = pno
    return h, levels, len(d.pages), anchors


def final_chunk(args):
    """按真实页码与偏移再排一遍，返回 PDF 字节与页数。"""
    h, css, offset, pages = args
    import weasyprint
    h = re.sub(r'@@PG:(s\d+)@@', lambda mm: str(pages.get(mm[1], '—')), h)
    css = css + '\n@page:first{counter-reset:page %d}' % offset
    d = weasyprint.HTML(string=html_doc(css, h), base_url=str(ROOT)).render()
    return d.write_pdf(), len(d.pages)


def render_pdf(secs, css_args, fonts, out, cover, back, raster_cover=False):
    import weasyprint
    import pymupdf
    from multiprocessing import Pool
    css = print_css(fonts, *css_args)
    css_front = print_css(fonts, *css_args, fol='lower-roman')
    tag = 'r' if css_args[0] == 190 else 'p'
    cache_path = TAIL_DIR / ('tail_fit_%s.json' % tag)
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    main_idx = next(i for i, s in enumerate(secs) if s[0] in ('main', 'part'))
    front = secs[:main_idx]
    main = secs[main_idx:]
    # 分块：每编（含其各章）一块；总合论等后置另成一块
    chunks, cur = [], None
    for s in main:
        if s[0] in ('part', 'back') or cur is None:
            cur = []; chunks.append(cur)
        cur.append(s)
    chunk_html = [''.join(sec_html(*s) for s in c) for c in chunks]
    with Pool(2) as pool:
        res = pool.map(fit_chunk, [(h, css, cache.get(tag, {})) for h in chunk_html], chunksize=1)
    lv = cache.setdefault(tag, {})
    for r in res:
        lv.update(r[1])
    cache_path.write_text(json.dumps(cache))
    offs, pages, off = [], {}, 1
    for r in res:
        offs.append(off)
        for a, p in r[3].items():
            pages[a] = off + p - 1
        off += r[2] + (r[2] % 2)
    with Pool(2) as pool:
        fin = pool.map(final_chunk, [(r[0], css, offs[i], pages) for i, r in enumerate(res)], chunksize=1)
    # 前置：书名页、出版信息、作者介绍、总导论、目录（罗马页码）
    roman_ids = set()

    def build_front(pages_front):
        inner = TITLEPAGE
        for s in front:
            if s[0] == 'cp':
                inner += '<section class="front-sec clean" id="%s">%s</section>' % (s[1], s[4])
        for s in front:
            if s[0] != 'cp':
                inner += sec_html(*s)
        allp = dict(pages); allp.update(pages_front)
        inner += toc_block(secs, allp, roman_ids)
        if True:
            inner = fit_chunk((inner, css_front, cache.get(tag + 'f', {})))
            cache[tag + 'f'] = inner[1]; cache_path.write_text(json.dumps(cache)); inner = inner[0]
        return weasyprint.HTML(string=html_doc(css_front, re.sub(r'@@PG:s\d+@@', '—', inner)), base_url=str(ROOT)).render()

    fdoc = build_front({})
    pf = {}
    for pno, pg in enumerate(fdoc.pages, 1):
        for a in pg.anchors:
            if re.fullmatch(r's\d+', a) and a not in pf:
                pf[a] = pno; roman_ids.add(a)
    fdoc = build_front(pf)
    pf2 = {}
    for pno, pg in enumerate(fdoc.pages, 1):
        for a in pg.anchors:
            if re.fullmatch(r's\d+', a) and a not in pf2:
                pf2[a] = pno
    assert pf2 == pf, '前置回填页码后分页变了'
    fbytes = fdoc.write_pdf()
    book = pymupdf.open()

    def blank(w, h):
        pg = book.new_page(width=w, height=h)
        pg.draw_rect(pg.rect, color=None, fill=(0xFB / 255, 0xF8 / 255, 0xF0 / 255))
        return pg

    def add_cover(src):
        c = pymupdf.open(str(src))
        if raster_cover:
            pg = c[0]
            pix = pg.get_pixmap(matrix=pymupdf.Matrix(2400 / pg.rect.width, 2400 / pg.rect.width))
            np = book.new_page(width=pg.rect.width, height=pg.rect.height)
            np.insert_image(np.rect, stream=pix.tobytes('jpeg', jpg_quality=92))
        else:
            book.insert_pdf(c)
    add_cover(cover)
    blank(book[0].rect.width, book[0].rect.height)  # 封二
    f = pymupdf.open(stream=fbytes, filetype='pdf')
    book.insert_pdf(f)
    if len(f) % 2:
        blank(f[0].rect.width, f[0].rect.height)
    main_start = len(book) + 1
    W_, H_ = f[0].rect.width, f[0].rect.height
    for pdfb, npg in fin:
        m = pymupdf.open(stream=pdfb, filetype='pdf')
        book.insert_pdf(m)
        if npg % 2:
            blank(W_, H_)
    if len(book) % 2 == 0:
        pass
    blank(W_, H_)  # 封三
    add_cover(back)
    toc, flip = [], []
    front_off = 2
    for kind, sid, title, lvl, _ in secs:
        if sid in pf:
            g = front_off + pf[sid]; p = ''
        elif sid in pages:
            g = main_start - 1 + pages[sid]; p = str(pages[sid])
        else:
            continue
        L = 1 if lvl <= 1 else 2
        toc.append([L, title.replace('　', ' '), g])
        flip.append({'t': title.replace('　', ' '), 'p': p, 'g': g, 'l': L})
    fixed, prev = [], 0
    for L, t, g in toc:
        L = min(L, prev + 1); fixed.append([L, t, g]); prev = L
    for kind, sid, *_ in secs:
        if kind == 'part' and sid in pages:
            pg = book[main_start - 2 + pages[sid]]
            r = pg.rect
            pg.draw_rect(pymupdf.Rect(r.x0 - 3, r.y0 - 3, r.x1 + 3, r.y1 + 3), color=None, fill=(0x1F / 255, 0x3A / 255, 0x5F / 255), overlay=False)
    book.set_toc(fixed)
    book.set_metadata({'title': META['title'] + '：' + META['subtitle'], 'author': META['author'] + ' 著',
                       'subject': '德麦国际专著第 %d 号 · ISBN %s' % (META['no'], META['isbn']),
                       'creator': 'WeasyPrint 70.0', 'producer': 'WeasyPrint 70.0 + PyMuPDF'})
    book.save(str(out), garbage=4, deflate=True)
    return flip, main_start


# ───────────────────────── 网页全文 ─────────────────────────
WEB_CSS_FILE = ROOT.parents[1] / 'public/books/m/259/text/index.html'
if not WEB_CSS_FILE.exists():   # 稀疏检出没有第 259 号时，借第 551 号全文网页的样式（只读）
    WEB_CSS_FILE = ROOT.parents[1] / 'public/books/m/551/text/index.html'


def web_page(secs):
    src = WEB_CSS_FILE.read_text()
    style = re.search(r'<style>(.*?)</style>', src, re.S).group(1)
    style += """
.ledger .lk{color:var(--navy);font-weight:700}
.wonder{border-left:3px solid #58A9B5;padding:.5rem 1rem;margin:1rem 0}.wonder .lab{display:block;font:700 .75rem sans-serif;color:#58A9B5;letter-spacing:.3em}.wonder p{text-indent:0;margin:.2rem 0;color:var(--dim)}
.endmark{text-align:center;color:var(--gold);margin:2rem 0 0}
.takeaway p.li{padding-left:1.3em;text-indent:-1.3em;margin:.15rem 0}.takeaway .tm{display:inline-block;width:1.3em;text-indent:0;color:var(--gold)}
.card.code p{font-family:ui-monospace,monospace,sans-serif;font-size:.85rem;margin:0}
.ledger.nine{display:block}.ledger.nine p{margin:.15rem 0}
.judge{border-left:3px solid #8A6E3A;padding:.5rem 1rem;margin:1rem 0}.judge .lab{display:block;font:700 .75rem sans-serif;color:#8A6E3A;letter-spacing:.3em}.judge p{text-indent:0;margin:.2rem 0;color:var(--dim)}
.chapnum{font-size:2.6rem;color:var(--gold);opacity:.45;line-height:1;margin-top:1rem}.chapnum.spacer{opacity:0;font-size:1rem}
.chap-label{margin:.3rem 0 .2rem}
blockquote.verdict{border-left:3px solid var(--gold)}blockquote.verdict p{color:var(--navy);font-weight:700}
.emb{width:44px;height:44px;display:block;margin:0 auto 1rem}
p.bib{text-indent:-2em;padding-left:2em;font-size:.9rem;line-height:1.8;overflow-wrap:anywhere}p.bib .bn{color:var(--gold)}p.bib.sc{text-indent:0;color:var(--dim);font-size:.84rem;margin-bottom:.9rem}
p.srcnote{text-indent:0;font-size:.84rem;color:var(--dim);font-family:sans-serif}
.fs-title.appx{font-size:1.4rem}
table.cp th{background:none;color:var(--dim);font-weight:400;width:5rem}table.cp tr:nth-child(odd){background:var(--soft)}
.cp-title{text-align:center;letter-spacing:.6em;color:var(--navy);font-weight:700;margin:2rem 0 1rem}
.cp-notes p{text-indent:0;font-size:.85rem;color:var(--dim)}
.epi{text-align:center;margin:3rem 0}.epi p{text-indent:0;text-align:center;color:var(--navy)}.epi .by{color:var(--dim);font-size:.9rem}
.orn{text-align:center;color:var(--gold);font-size:.8rem}
.grp{text-align:center;color:#D9B96E;font:.8rem sans-serif;letter-spacing:.4em;margin:-.5rem 0 .6rem}
.formula{margin:1.2rem 6%;padding:.7rem 0;text-align:center;border-top:1px solid var(--line,#ddd);border-bottom:1px solid var(--line,#ddd)}
.formula p{text-indent:0;text-align:center;margin:.2rem 0;font-size:1.08em}
.srcblock{margin-top:2rem;padding-top:.6rem;border-top:1px solid var(--line,#ddd)}
h4.srchead{font:700 .78rem sans-serif;color:var(--gold);letter-spacing:.3em;margin:0 0 .4rem}
p.sn{text-indent:-2.1em;padding-left:2.1em;font:.84rem/1.7 sans-serif;color:var(--dim);margin:.2rem 0;overflow-wrap:anywhere}p.sn.cont{text-indent:0;padding-left:0}
code{font-size:.88em;overflow-wrap:anywhere}
li.g{font-weight:700;letter-spacing:.2em;color:var(--gold);margin-top:.8rem;list-style:none}
.card{background:var(--soft);border-left:3px solid var(--navy);padding:.8rem 1rem;margin:1rem 0;border-radius:4px}.card p{text-indent:0;margin:0 0 .2rem;font-family:sans-serif;font-size:.9rem}
p.chap-lead{text-indent:0;color:var(--dim);margin:-.2rem 0 1.4rem;font-size:.98em}
.epi p.by{font-size:.9rem}
.part-intro p.bianxu{letter-spacing:0;font-size:1rem;font-family:inherit;text-align:justify;text-indent:2em;color:var(--ink);margin:0 0 .9em}
h3.sec .dia{margin-right:.4em}
h4.ssec{font-size:1.02em;color:var(--navy);margin:1.4rem 0 .5rem;font-weight:700}
h4.ssec::before{content:"";display:inline-block;width:.8em;border-top:1px solid var(--gold);vertical-align:.3em;margin-right:.45em}
"""
    v = META['version']
    toc = []
    for kind, sid, title, lvl, _ in secs:
        if kind == 'cp':
            continue
        cls = {'part': 'p', 'chapter': 'c'}.get(kind, 'f')
        if sid in GROUP_START:
            toc.append('<li class="g">%s</li>' % GROUP_START[sid])
        toc.append('<li class="%s"><a href="#%s">%s</a></li>' % (cls, sid, inline(title)))
    body = []
    for s in secs:
        body.append(sec_html(*s))
        if s[0] == 'cp':
            body.append(EPIGRAPH.replace('section', 'div'))
    han = M.body_han(ROOT)
    head = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>全文网页阅读 · {META['title']} · 德麦国际专著第 {META['no']} 号</title>
<meta name="description" content="《{META['title']}：{META['subtitle']}》全文网页版。{META['author']} 著，德麦国际专著第 {META['no']} 号，约 {han/10000:.0f} 万汉字。">
<meta name="tier" content="L0"><meta name="cite_ok" content="true"><meta name="book_no" content="{META['no']}"><link rel="canonical" href="https://sdeuniverses.com/books/m/{META['no']}/text/">
<style>{style}</style></head><body><div id="prog"></div>
<div class="bar"><a href="/books/m/{META['no']}/">← 书籍详情</a><a href="/books/m/{META['no']}/read.html">在线翻页</a><a href="/books/m/{META['no']}/{SLUG}-print.pdf?v={v}" target="_blank" rel="noopener">PDF</a><span class="sp"></span><button id="fs">字号</button><button id="th">夜间</button></div>
<div class="wrap">
<div class="hero"><img src="/books/m/{META['no']}/cover.jpg?v={v}" alt="封面"><h1>{META['title']}</h1><p>{META['subtitle']}</p>
<p style="color:var(--dim);margin-top:.5rem">{META['author']} 著 · 德麦国际专著第 {META['no']} 号 · ISBN {META['isbn']} · 约 {han/10000:.0f} 万汉字</p></div>
<details class="toc" open><summary>目录（出版信息 · 作者介绍 · 总导论 · 第一编至第二十一编 · 总合论）</summary><ul>{''.join(toc)}</ul></details>
"""
    tail = f"""<div class="foot">德麦国际出版社 · Demai International Press · <a href="/books/">专著书架</a> · <a href="/books/m/{META['no']}/">书籍详情</a> · <a href="/books/m/{META['no']}/read.html">在线翻页</a></div>
</div>
<script>
(function(){{var p=document.getElementById('prog');addEventListener('scroll',function(){{var h=document.documentElement;p.style.width=(h.scrollTop/(h.scrollHeight-h.clientHeight)*100)+'%';}},{{passive:true}});
var sizes=[16,17,18,20,22],k=2;try{{var s=localStorage.getItem('bk{META['no']}-fs');if(s)k=+s;var d=localStorage.getItem('bk{META['no']}-dark');if(d==='1')document.documentElement.classList.add('dark');}}catch(e){{}}
function ap(){{document.body.style.fontSize=sizes[k]+'px';}}ap();
document.getElementById('fs').onclick=function(){{k=(k+1)%sizes.length;ap();try{{localStorage.setItem('bk{META['no']}-fs',k)}}catch(e){{}}}};
document.getElementById('th').onclick=function(){{var on=document.documentElement.classList.toggle('dark');try{{localStorage.setItem('bk{META['no']}-dark',on?'1':'0')}}catch(e){{}}}};}})();
</script></body></html>"""
    return head + '\n'.join(body) + tail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fonts', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--only', choices=['print', 'reader', 'web'], action='append')
    ap.add_argument('--limit', type=int, default=0, help='试排：只排前若干节')
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    secs = build_sections()
    if a.limit:
        secs = secs[:a.limit]
    only = a.only or ['print', 'reader', 'web']
    if 'web' in only:
        (a.out / 'text.html').write_text(web_page(secs))
        print('web ok')
    if 'print' in only:
        flip, ms = render_pdf(secs, (170, 240, 10.3, 1.86, (20, 17, 19.5, 19)), a.fonts, a.out / f'{SLUG}-print.pdf',
                              a.out / 'cover-print.pdf', a.out / 'back-print.pdf')
        (a.out / 'toc-print.json').write_text(json.dumps({'toc': flip, 'offset': ms}, ensure_ascii=False))
        print('print ok, main starts at physical page', ms)
    if 'reader' in only:
        flip, ms = render_pdf(secs, (190, 250, 12.2, 1.95, (20, 19, 20, 20)), a.fonts, a.out / f'{SLUG}-reader.pdf',
                              a.out / 'cover-reader.pdf', a.out / 'back-reader.pdf', raster_cover=True)
        (a.out / 'toc-reader.json').write_text(json.dumps({'toc': flip, 'offset': ms}, ensure_ascii=False))
        print('reader ok, main starts at physical page', ms)


if __name__ == '__main__':
    main()
