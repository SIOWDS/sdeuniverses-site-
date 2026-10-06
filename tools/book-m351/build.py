#!/usr/bin/env python3
"""第 351 号《AI时代大学毕业生的核心竞争力——大学如何读？》成书：Markdown 分卷稿 → 印刷版／阅读版 PDF ＋ 全文网页。

版式照第 220 号（经第 259、290、274 号实测，脚本由第 274 号庄子卷改来；补代码块＝定位卡）：暖纸内页、藏青标题、浅金大号章码、金色「第 N 章」、
金短线、◆ 金菱形小节、带走的话与小账米底金线框、章末金菱形、编首页金色花饰圆章与导语。

用法：
  python3 build.py --fonts /home/claude/fonts --out /home/claude/bk351
产物：
  <out>/daxue-ruhe-du-print.pdf   170×240 mm，含封面封底
  <out>/daxue-ruhe-du-reader.pdf  190×250 mm，含封面封底
  <out>/text.html         全文网页（放到 public/books/m/351/text/index.html）
  <out>/toc-reader.json   翻页器目录（read.html 用）
依赖：weasyprint 70、pymupdf；封面封底由 cover.py 先生成（<out>/cover-*.pdf、back-*.pdf）。
"""
import argparse
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / 'src'
PARTS = [('p1', ['c01', 'c02']), ('p2', ['c03', 'c04', 'c05']), ('p3', ['c06', 'c07', 'c08']),
         ('p4', ['c09', 'c10', 'c11']), ('p5', ['c12']), ('p6', ['c13', 'c14', 'c15', 'c16'])]
FILES = ['00-front', '02-zixu', '03-daolun'] + [x for p, cs in PARTS for x in [p] + cs] + ['90-jieyu', '91-fangfa', '92-yanjiu', '93-refs', '94-shuoming']
SLUG = 'daxue-ruhe-du'
META = dict(
    title='AI时代大学毕业生的核心竞争力', name='AI时代大学毕业生的核心竞争力',
    subtitle='大学如何读？', author='王德生', no=351,
    isbn='979-8-90690-661-8', price='US$21.00', version='20261006a',
    publisher='德麦国际出版社', publisher_en='Demai International Press',
)
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
    for raw in text.splitlines():
        line = raw.rstrip()
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
        else:
            res.append((k, b))
    return res


def inline(s):
    s = re.sub(r'(?<=[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]) (?=[A-Za-z0-9$])|(?<=[A-Za-z0-9%$.)]) (?=[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef])', '\u2009', s)
    s = html.escape(s, quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?!\*)', r'<em>\1</em>', s)
    return s


def table_html(rows, cls='tb'):
    cells = [[c.strip() for c in r.strip().strip('|').split('|')] for r in rows]
    cells = [r for r in cells if not all(re.fullmatch(r':?-{2,}:?', c) for c in r)]
    head, body = cells[0], cells[1:]
    ncol = len(head)
    h = ['<div class="tw%s"><table class="%s c%d"><thead><tr>' % (' long' if len(body) > 8 or sum(len(c) for r in cells for c in r) > 700 else '', cls, ncol)]
    h += ['<th>%s</th>' % inline(c) for c in head]
    h.append('</tr></thead><tbody>')
    for r in body:
        h.append('<tr>' + ''.join('<td>%s</td>' % inline(c) for c in r) + '</tr>')
    h.append('</tbody></table></div>')
    return ''.join(h)


def quote_html(lines):
    lines = [l for l in lines]
    first = lines[0].strip() if lines else ''
    rest = [l for l in lines[1:] if l.strip()]
    if first == '**带走的话**':
        return '<div class="takeaway"><span class="lab">带走的话</span>%s</div>' % ''.join(
            '<p>%s</p>' % inline(l) for l in rest)
    if first == '**小账**':
        ps = []
        for l in rest:
            m = re.match(r'^([^：]{2,8})：(.*)$', l)
            ps.append('<p><span class="lk">%s：</span>%s</p>' % (inline(m[1]), inline(m[2])) if m else '<p>%s</p>' % inline(l))
        return '<div class="ledger"><span class="lab">小　账</span>%s</div>' % ''.join(ps)
    body = [l for l in lines if l.strip()]
    if len(body) == 1 and re.fullmatch(r'\*\*.+\*\*', body[0].strip()):
        return '<div class="pull"><p>%s</p></div>' % inline(body[0].strip()[2:-2])
    return '<blockquote class="verdict">%s</blockquote>' % ''.join('<p>%s</p>' % inline(l) for l in body)


def render(blocks, bib=False):
    h = []
    for k, b in blocks:
        if k == 'p':
            t = b[0]
            if t.startswith('【表】'):
                h.append('<div class="tcap">%s</div>' % inline(t[3:].strip()))
            elif t.startswith('【路线】'):
                h.append('<div class="route"><span>路线</span>%s</div>' % inline(t[4:].strip()))
            elif re.fullmatch(r'〔[^〔〕]*〕', t):
                h.append('<p class="srcnote">%s</p>' % inline(t))
            else:
                h.append('<p%s>%s</p>' % (' class="bib"' if bib else '', inline(t)))
        elif k == 'h3':
            t = b[0]
            if t.startswith('◆'):
                tt = t.lstrip('◆ ').strip()
                h.append('<h3 class="sec%s"><span class="dia">◆</span>%s</h3>' % (' pb' if '核心概念总表' in tt else '', inline(tt)))
            else:
                h.append('<h3 class="sec">%s</h3>' % inline(t))
        elif k in ('h2', 'h4'):
            h.append('<h4 class="subhead">%s</h4>' % inline(b[0]))
        elif k == 'quote':
            h.append(quote_html(b))
        elif k == 'table':
            h.append(table_html(b))
        elif k == 'ul':
            h.append('<ul class="ls">%s</ul>' % ''.join('<li>%s</li>' % inline(x) for x in b))
        elif k == 'ol':
            if bib:
                h.append(''.join('<p class="bib"><span class="bn">%s.</span> %s</p>' % (re.match(r'^(\d+)\. ', x)[1], inline(re.sub(r'^\d+\. ', '', x))) for x in b))
            else:
                start = int(re.match(r'^(\d+)\. ', b[0])[1])
                h.append('<ol class="ls"%s>%s</ol>' % (' start="%d"' % start if start != 1 else '',
                                                       ''.join('<li>%s</li>' % inline(re.sub(r'^\d+\. ', '', x)) for x in b)))
        elif k == 'orn':
            h.append('<div class="orn">◆</div>')
        elif k == 'pre':
            ls = [x.strip() for x in b if x.strip()]
            h.append('<div class="card"><span class="lab">%s</span>%s</div>' % (inline(ls[0]), ''.join('<p>%s</p>' % inline(x) for x in ls[1:])))
    return '\n'.join(h)


def with_endmark(inner):
    """章末「带走的话＋小账＋◆」绑成一块，禁止拆页——否则会掉出只有一个 ◆ 或只有小账的孤页。"""
    end = '<div class="endmark">◆</div>'
    m = re.search(r'(<div class="takeaway">.*?</div>)\s*(<div class="ledger">.*?</div>)\s*$', inner, re.S)
    if m:
        return inner[:m.start()] + '<div class="chapend">' + m.group(0) + end + '</div>'
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
    return ' '.join(label)


def read_blocks(name):
    return blocks_of((SRC / (name + '.md')).read_text())


def build_sections():
    """返回 [(kind, id, toc_title, level, html)]；kind: cp/front/main/part/chapter/back。"""
    secs, n = [], 0

    def sid():
        nonlocal n
        n += 1
        return 's%d' % n

    def front_like(kind, title, bl, lvl=1, bib=False, endmark=False):
        name, _, sub = title.partition('　')
        head = '<h1 class="fs-title">%s</h1>%s<div class="rule"></div>' % (
            name, '<div class="fs-sub">%s</div>' % inline(sub) if sub else '')
        body = render(bl, bib=bib)
        if endmark:
            body = with_endmark(body)
        secs.append((kind, sid(), name + ('　' + sub if sub else ''), lvl, head + body))

    # ── 前置：出版信息、作者介绍、内容提要 ──
    front = read_blocks('00-front')
    groups, cur = [], None
    for k, b in front:
        if k == 'h2':
            cur = [b[0], []]; groups.append(cur)
        elif cur is not None and k != 'hr':
            cur[1].append((k, b))
    han = sum(len(HAN.findall((SRC / (f + '.md')).read_text())) for f in FILES)
    for title, bl in groups:
        if title == '出版信息':
            rows = [b for k, b in bl if k == 'table'][0]
            notes = [b[0] for k, b in bl if k == 'p']
            cells = [[c.strip() for c in r.strip().strip('|').split('|')] for r in rows][2:]
            tb = ''.join('<tr><th>%s</th><td>%s</td></tr>' % (inline(a), inline(c.replace('__WAN__', '%.0f' % (han / 10000)))) for a, c in cells)
            nt = ''.join('<p%s>%s</p>' % (' class="cp-right"' if '侵权必究' in x else '', inline(x)) for x in notes)
            secs.append(('cp', sid(), '出版信息', 0,
                         '<div class="cp-title">出 版 信 息</div><table class="cp">%s</table><div class="cp-notes">%s</div>' % (tb, nt)))
        else:
            front_like('front', title, bl)
    # ── 自序、导论 ──
    for f, kind in (('02-zixu', 'front'), ('03-daolun', 'main')):
        bl = read_blocks(f)
        front_like(kind, bl[0][1][0], bl[1:], endmark=(kind == 'main'))
    # ── 六部十六章 ──
    for pf, chs in PARTS:
        bl = read_blocks(pf)
        m = re.match(r'^(.+?)　(.*)$', bl[0][1][0])
        route, intro = '', []
        for k, b in bl[1:]:
            if k == 'p' and b[0].startswith('【路线】'):
                route = b[0][4:].strip()
            elif k == 'p':
                intro.append('<p class="bianxu">%s</p>' % inline(b[0]))
            elif k == 'quote':
                intro.append(quote_html(b))
        secs.append(('part', sid(), '%s　%s' % (m[1], m[2]), 1,
                     '%s<div class="part-label">%s</div><h1 class="part-title">%s</h1><div class="rule"></div>'
                     '%s<div class="daoyu">导　语</div><div class="part-intro">%s</div>'
                     % (EMB, spaced(m[1]), inline(m[2]),
                        '<div class="route2">%s</div>' % inline(route) if route else '', ''.join(intro))))
        for cf in chs:
            cb = read_blocks(cf)
            cm = re.match(r'^(.+?)　(.*)$', cb[0][1][0])
            body = [x for x in cb[1:] if x[0] != 'hr']
            lab = cm[1]
            nm = re.fullmatch(r'第([一二三四五六七八九十百〇]+)章', lab)
            num = cn2int(nm[1])
            secs.append(('chapter', sid(), '%s　%s' % (lab, cm[2]), 2,
                         '<div class="chapnum">%02d</div><div class="chap-label">%s</div>'
                         '<h2 class="chap-title">%s</h2><div class="rule"></div>%s'
                         % (num, lab, inline(cm[2]), with_endmark(render(body)))))
    # ── 结语与附录 ──
    bl = read_blocks('90-jieyu')
    front_like('back', bl[0][1][0], bl[1:], endmark=True)
    for f in ('91-fangfa', '92-yanjiu'):
        bl = read_blocks(f)
        front_like('back', bl[0][1][0], bl[1:], lvl=1)
    bl = read_blocks('93-refs')
    front_like('back', bl[0][1][0], [x for x in bl[1:]], bib=True)
    bl = read_blocks('94-shuoming')
    front_like('back', bl[0][1][0], bl[1:])
    return secs


# ───────────────────────── 印刷 CSS ─────────────────────────
def print_css(fonts, W, H, body_pt, lh, margin, fol='decimal'):
    t, o, b, i = margin
    F = fonts.resolve()
    return f"""
@page{{size:{W}mm {H}mm;margin:{t}mm {o}mm {b}mm {i}mm;background:#FBF8F0;
  @top-left{{content:none}} @top-right{{content:none}}}}
@page :left{{margin-left:{o}mm;margin-right:{i}mm;
  @top-left{{content:string(book);font:6.8pt 'Noto Sans CJK SC';color:#9A917E;vertical-align:bottom;padding-bottom:4mm}}
  @bottom-left{{content:counter(page,{fol});font:7.6pt 'Noto Serif CJK SC';color:#8A8578}}}}
@page :right{{
  @top-right{{content:string(chap);font:6.8pt 'Noto Sans CJK SC';color:#9A917E;vertical-align:bottom;padding-bottom:4mm}}
  @bottom-right{{content:counter(page,{fol});font:7.6pt 'Noto Serif CJK SC';color:#8A8578}}}}
@page :blank{{@top-left{{content:none}} @top-right{{content:none}} @bottom-left{{content:none}} @bottom-right{{content:none}}}}
@page clean{{@top-left{{content:none}} @top-right{{content:none}} @bottom-left{{content:none}} @bottom-right{{content:none}}}}
@page opener:left{{@top-left{{content:none}}}}
@page opener:right{{@top-right{{content:none}}}}
body{{font-family:'Noto Serif CJK SC';font-size:{body_pt}pt;line-height:{lh};color:#2A2824;margin:0;string-set:book "{META['title']}"}}
p{{margin:0 0 .42em;text-indent:2em;text-align:justify;orphans:2;widows:2}}
strong{{color:#1F3A5F;font-weight:700}}
em{{font-style:italic}}
.clean{{page:clean}}
section.tight p{{line-height:1.78}}
section{{break-before:page}}
section.part,section.front-sec,section.back-sec,section.toc{{page:opener}}
section.part{{break-before:right;text-align:center;padding-top:26mm}}
.emb{{width:15mm;height:15mm;display:block;margin:0 auto 7mm}}
.part-label{{font:700 9.5pt 'Noto Sans CJK SC';color:#B08A3C;letter-spacing:.9em;margin-bottom:5mm;text-indent:.9em}}
.part-title{{font:700 18.5pt/1.5 'Noto Serif CJK SC';color:#1F3A5F;margin:0 12mm 4mm;string-set:chap content()}}
.part .rule{{margin:0 auto 9mm}}
.daoyu{{font:700 8.5pt 'Noto Sans CJK SC';color:#B08A3C;letter-spacing:.6em;margin-bottom:5mm}}
.part-intro{{text-align:left}}
.part-intro p{{font-size:{body_pt*0.93:.2f}pt;color:#4A463D}}
.rule{{width:13mm;border-top:.9pt solid #B08A3C;margin:3mm 0 7mm}}
.chapnum{{font:300 34pt/1 'Noto Serif CJK SC';color:#D9C39A;margin-top:6mm;letter-spacing:.02em}}
.chap-label{{font:700 8.4pt 'Noto Sans CJK SC';color:#B08A3C;margin:2mm 0 1.5mm;letter-spacing:.08em}}
.chap-title{{font:700 16pt/1.45 'Noto Serif CJK SC';color:#1F3A5F;margin:0;string-set:chap content();bookmark-level:2;bookmark-label:content()}}
.fs-title{{font:700 18pt/1.4 'Noto Serif CJK SC';color:#1F3A5F;margin:14mm 0 1mm;letter-spacing:.12em;string-set:chap content();bookmark-level:1;bookmark-label:content()}}
.fs-title.appx{{bookmark-level:2;font-size:15pt;letter-spacing:.06em}}
.part-title{{bookmark-level:1;bookmark-label:content()}}
.fs-sub{{font:400 10.4pt 'Noto Serif CJK SC';color:#B08A3C;margin-top:1.5mm}}
h3.sec{{font:700 {body_pt*1.03:.2f}pt/1.6 'Noto Sans CJK SC';color:#1F3A5F;margin:5.5mm 0 2.4mm;break-after:avoid}}
h3.sec.pb{{break-before:page;margin-top:0}}
h3.sec .dia{{color:#B08A3C;font-size:.78em;margin-right:.45em;vertical-align:.08em}}
h4.subhead{{font:700 {body_pt*1.0:.2f}pt/1.6 'Noto Serif CJK SC';color:#1F3A5F;margin:4.5mm 0 1.8mm;break-after:avoid;border-bottom:.4pt solid #D8CFBB;padding-bottom:.6mm}}
.tcap{{font:700 {body_pt*0.84:.2f}pt/1.5 'Noto Sans CJK SC';color:#B08A3C;margin:4mm 0 1.2mm;break-after:avoid}}
.route2{{font:400 {body_pt*0.9:.2f}pt 'Noto Sans CJK SC';color:#8A8578;letter-spacing:.08em;margin:0 0 6mm}}
.card .lab{{display:block;font:700 7.2pt 'Noto Sans CJK SC';color:#B08A3C;letter-spacing:.3em;margin-bottom:1.2mm}}
.tw.long{{break-inside:auto}} table.tb{{break-inside:auto}} table.tb tr{{break-inside:avoid}} table.tb thead{{display:table-header-group}}
table.tb.c6,table.tb.c7{{font-size:{body_pt*0.72:.2f}pt;line-height:1.5}}
table.tb.c6 th,table.tb.c7 th{{font-size:{body_pt*0.72:.2f}pt;padding:1.1mm 1.2mm}}
table.tb.c6 td,table.tb.c7 td{{padding:1.1mm 1.2mm}}
.endmark{{break-before:avoid}}
.takeaway{{background:#F6F1E4;border-left:1.6pt solid #B08A3C;padding:2.6mm 4mm 2.8mm;margin:6mm 0 3.5mm;break-inside:avoid}}
.takeaway .lab{{display:block;font:700 7.2pt 'Noto Sans CJK SC';color:#B08A3C;letter-spacing:.5em;margin-bottom:1.4mm}}
.takeaway p{{text-indent:0;margin:0;font-weight:700;color:#1F3A5F;font-size:{body_pt*1.02:.2f}pt}}
.ledger{{background:#F4EFE3;border-left:1.6pt solid #D8CFBB;padding:2.4mm 4mm 2.6mm;margin:3mm 0 2mm;break-inside:avoid}}
.ledger .lab{{display:block;font:700 7.2pt 'Noto Sans CJK SC';color:#5A554A;letter-spacing:.3em;margin-bottom:1.2mm}}
.ledger p{{text-indent:0;margin:0 0 .6mm;font-size:{body_pt*0.86:.2f}pt;line-height:1.75;color:#5A554A}}
.ledger .lk{{color:#1F3A5F;font-weight:700}}
.chapend{{break-inside:avoid}}
.endmark{{text-align:center;color:#B08A3C;font-size:8pt;margin-top:6mm}}
.orn{{text-align:center;color:#B08A3C;font-size:7.5pt;margin:3mm 0}}
.pull{{margin:5mm 6%;padding:3mm 0;border-top:.8pt solid #B08A3C;border-bottom:.8pt solid #B08A3C;text-align:center;break-inside:avoid}}
.pull p{{text-indent:0;text-align:center;font-weight:700;color:#1F3A5F;font-size:{body_pt*1.12:.2f}pt;margin:0}}
blockquote.verdict{{background:#F6F1E4;border-left:1.6pt solid #B08A3C;margin:4mm 0;padding:2.6mm 4mm;break-inside:avoid}}
blockquote.verdict p{{text-indent:0;margin:0;font-weight:700;color:#1F3A5F}}
.tw{{margin:3.5mm 0;break-inside:avoid}}
table.tb{{width:100%;border-collapse:collapse;font-size:{body_pt*0.8:.2f}pt;line-height:1.6}}
table.tb th{{background:#1F3A5F;color:#FBF8F0;font:700 {body_pt*0.8:.2f}pt/1.6 'Noto Sans CJK SC';padding:1.4mm 1.6mm;text-align:left}}
table.tb td{{border-bottom:.5pt solid #E4DCCB;padding:1.3mm 1.6mm;vertical-align:top}}
table.tb tr:nth-child(even) td{{background:#F6F1E4}}
ul.ls,ol.ls{{margin:1mm 0 2.5mm;padding-left:2.2em}} ul.ls li,ol.ls li{{margin:.4mm 0}}
p.bib{{text-indent:-2em;padding-left:2em;font-size:{body_pt*0.88:.2f}pt;line-height:1.75;margin-bottom:1.2mm;text-align:left}}
p.bib .bn{{color:#B08A3C}}
.card{{background:#F6F1E4;border:.6pt solid #D8CFBB;border-left:1.6pt solid #1F3A5F;padding:2.6mm 4mm;margin:4mm 0;break-inside:avoid}}
.card p{{text-indent:0;margin:0 0 .5mm;font:{body_pt*0.86:.2f}pt/1.75 'Noto Sans CJK SC';color:#2A2824;text-align:left}}
p.srcnote{{text-indent:0;font:{body_pt*0.8:.2f}pt/1.7 'Noto Sans CJK SC';color:#8A8578;margin:1mm 0 2.6mm}}
.titlepage .big2{{font:700 30pt/1.35 'Noto Serif CJK SC';color:#1F3A5F;margin:2mm 0 5mm;letter-spacing:.1em}}
/* 书名页 */
section.clean,section.epi{{page:clean}}
.titlepage{{page:clean;padding-top:34mm}}
.titlepage .pre{{font:400 12pt 'Noto Serif CJK SC';color:#1F3A5F;letter-spacing:.3em}}
.titlepage .big{{font:700 29pt/1.35 'Noto Serif CJK SC';color:#1F3A5F;margin:3mm 0 5mm;letter-spacing:.08em}}
.titlepage .sub{{font:400 10.5pt/1.7 'Noto Serif CJK SC';color:#B08A3C}}
.titlepage .rule{{margin:6mm 0 0}}
.titlepage .au{{margin-top:36mm;font:400 11pt 'Noto Serif CJK SC';color:#2A2824;letter-spacing:.2em}}
.titlepage .pub{{position:absolute;bottom:0;font:700 8.5pt 'Noto Sans CJK SC';color:#1F3A5F;letter-spacing:.35em}}
.titlepage .pub span{{display:block;font:400 6.8pt 'Noto Sans CJK SC';color:#8A8578;letter-spacing:.08em;margin-top:1mm}}
/* 出版信息 */
.cp-title{{font:700 11pt 'Noto Sans CJK SC';color:#1F3A5F;letter-spacing:.8em;text-align:center;margin:6mm 0 5mm}}
table.cp{{width:100%;border-collapse:collapse;font-size:8.4pt;line-height:1.6}}
table.cp th{{font:400 7.8pt 'Noto Sans CJK SC';color:#8A8578;text-align:left;width:17mm;padding:1.5mm 2mm;vertical-align:top}}
table.cp td{{padding:1.5mm 2mm;color:#2A2824}}
table.cp tr:nth-child(odd){{background:#F4EFE3}}
.cp-notes{{margin-top:5mm}}
.cp-notes p{{text-indent:0;font-size:7.2pt;line-height:1.7;color:#5A554A;margin-bottom:1.3mm}}
.cp-right{{margin-top:3mm!important;letter-spacing:.2em}}
/* 题辞 */
.epi{{page:clean;padding-top:60mm;text-align:center}}
.epi p{{text-indent:0;text-align:center;font-size:11.5pt;line-height:2.1;color:#1F3A5F}}
.epi .by{{font-size:8.6pt;color:#8A8578;margin-top:5mm}}
/* 目录 */
.toc h1{{font:700 18pt 'Noto Serif CJK SC';color:#1F3A5F;letter-spacing:.4em;margin:6mm 0 1mm}}
.toc ul{{list-style:none;padding:0;margin:4mm 0 0}}
.toc li{{display:flex;font-size:{body_pt*0.82:.2f}pt;line-height:1.5}}
.toc li a{{color:inherit;text-decoration:none}}
.toc li .t{{flex:1}}
.toc li .pg{{color:#8A8578;font-family:'Noto Serif CJK SC';min-width:9mm;text-align:right}}
.toc li.p{{font-weight:700;color:#1F3A5F;margin-top:1.8mm}}
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
        li.append('<li class="%s"><span class="t"><a href="#%s">%s</a></span><span class="pg">%s</span></li>'
                  % (cls, sid, inline(title), pgs))
    return '<section class="toc front-sec"><h1>目录</h1><div class="rule"></div><ul>%s</ul></section>' % ''.join(li)


TITLEPAGE = f"""<div class="titlepage"><div class="pre">德麦国际专著 · 第 351 号</div><div class="big">AI时代大学毕业生<br>的核心竞争力</div>
<div class="sub">{META['subtitle']}</div><div class="rule"></div><div class="au">{META['author']}　　著</div>
<div class="pub">{META['publisher']}<span>{META['publisher_en']} · Singapore</span></div></div>"""
EPIGRAPH = ''


def html_doc(css, inner):
    return ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><style>%s</style></head><body>%s</body></html>'
            % (css, inner))


def sec_html(kind, sid, title, lvl, body):
    cls = {'part': 'part', 'chapter': 'chapter'}.get(kind, 'front-sec' if kind in ('front', 'main', 'cp') else 'back-sec')
    if title.startswith('第十二章'):
        cls += ' tight'
    return '<section class="%s" id="%s">%s</section>' % (cls, sid, body)


def render_pdf(secs, css_args, fonts, out, cover, back, raster_cover=False):
    import weasyprint
    import pymupdf
    css = print_css(fonts, *css_args)
    css_front = print_css(fonts, *css_args, fol='lower-roman')
    # 第 1 遍：正文（导论起），拿每节的页码
    main_idx = next(i for i, s in enumerate(secs) if s[0] in ('main', 'part'))
    front, main = secs[:main_idx], secs[main_idx:]
    main_html = ''.join(sec_html(*s) for s in main)
    # 导论不要求右页起，但正文第 1 页放在右页：前置页数补成偶数
    mdoc = weasyprint.HTML(string=html_doc(css, main_html), base_url=str(ROOT)).render()
    pages = {}
    for pno, pg in enumerate(mdoc.pages, 1):
        for a in pg.anchors:
            if re.fullmatch(r's\d+', a) and a not in pages:
                pages[a] = pno
    # 前置：书名页、出版信息、题辞、作者介绍、前言、导读、目录（罗马页码）
    roman_ids = set()

    def build_front(pages_front):
        inner = TITLEPAGE
        for s in front:
            if s[0] == 'cp':
                inner += '<section class="front-sec clean" id="%s">%s</section>' % (s[1], s[4])
                inner += EPIGRAPH
        for s in front:
            if s[0] != 'cp':
                inner += sec_html(*s)
        allp = dict(pages); allp.update(pages_front)
        inner += toc_block(secs, allp, roman_ids)
        return weasyprint.HTML(string=html_doc(css_front, inner), base_url=str(ROOT)).render()

    fdoc = build_front({})
    pf = {}
    for pno, pg in enumerate(fdoc.pages, 1):
        for a in pg.anchors:
            if re.fullmatch(r's\d+', a) and a not in pf:
                pf[a] = pno; roman_ids.add(a)
    fdoc = build_front(pf)
    fbytes = fdoc.write_pdf()
    mbytes = mdoc.write_pdf()
    book = pymupdf.open()

    def add_cover(src):
        c = pymupdf.open(str(src))
        if raster_cover:   # 阅读版给翻页器用：pdf.js 矢量模式不支持渐变，封面封底嵌高清图
            pg = c[0]
            pix = pg.get_pixmap(matrix=pymupdf.Matrix(2400 / pg.rect.width, 2400 / pg.rect.width))
            np = book.new_page(width=pg.rect.width, height=pg.rect.height)
            np.insert_image(np.rect, stream=pix.tobytes('jpeg', jpg_quality=90))
        else:
            book.insert_pdf(c)
    add_cover(cover)
    book.new_page(width=book[0].rect.width, height=book[0].rect.height)  # 封二
    f = pymupdf.open(stream=fbytes, filetype='pdf')
    book.insert_pdf(f)
    if len(f) % 2:
        book.new_page(width=f[0].rect.width, height=f[0].rect.height)
    main_start = len(book) + 1
    m = pymupdf.open(stream=mbytes, filetype='pdf')
    book.insert_pdf(m)
    if len(book) % 2:
        book.new_page(width=m[0].rect.width, height=m[0].rect.height)
    book.new_page(width=m[0].rect.width, height=m[0].rect.height)  # 封三
    add_cover(back)
    # 书签与翻页器目录
    toc, flip = [], []
    front_off = 2  # 封面、封二
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
    # 书签层级必须从 1 起、逐级不跳
    fixed, prev = [], 0
    for L, t, g in toc:
        L = min(L, prev + 1); fixed.append([L, t, g]); prev = L
    book.set_toc(fixed)
    book.set_metadata({'title': META['title'] + '——' + META['subtitle'], 'author': META['author'],
                       'subject': '德麦国际专著第 %d 号 · ISBN %s' % (META['no'], META['isbn']),
                       'creator': 'WeasyPrint 70.0', 'producer': 'WeasyPrint 70.0 + PyMuPDF'})
    book.save(str(out), garbage=4, deflate=True)
    return flip, main_start


# ───────────────────────── 网页全文 ─────────────────────────
WEB_CSS_FILE = Path('/home/claude/site/public/books/m/259/text/index.html')


def web_page(secs):
    src = WEB_CSS_FILE.read_text()
    style = re.search(r'<style>(.*?)</style>', src, re.S).group(1)
    style += """
.ledger .lk{color:var(--navy);font-weight:700}
.endmark{text-align:center;color:var(--gold);margin:2rem 0 0}
.chapnum{font-size:2.6rem;color:var(--gold);opacity:.45;line-height:1;margin-top:1rem}.chapnum.spacer{opacity:0;font-size:1rem}
.chap-label{margin:.3rem 0 .2rem}
blockquote.verdict{border-left:3px solid var(--gold)}blockquote.verdict p{color:var(--navy);font-weight:700}
.emb{width:44px;height:44px;display:block;margin:0 auto 1rem}
p.bib{text-indent:-2em;padding-left:2em;font-size:.9rem;line-height:1.8}p.bib .bn{color:var(--gold)}
p.srcnote{text-indent:0;font-size:.84rem;color:var(--dim);font-family:sans-serif}
.fs-title.appx{font-size:1.4rem}
table.cp th{background:none;color:var(--dim);font-weight:400;width:5rem}table.cp tr:nth-child(odd){background:var(--soft)}
.cp-title{text-align:center;letter-spacing:.6em;color:var(--navy);font-weight:700;margin:2rem 0 1rem}
.cp-notes p{text-indent:0;font-size:.85rem;color:var(--dim)}
.epi{text-align:center;margin:3rem 0}.epi p{text-indent:0;text-align:center;color:var(--navy)}.epi .by{color:var(--dim);font-size:.9rem}
.orn{text-align:center;color:var(--gold);font-size:.8rem}
.card{background:var(--soft);border-left:3px solid var(--navy);padding:.8rem 1rem;margin:1rem 0;border-radius:4px}.card p{text-indent:0;margin:0 0 .2rem;font-family:sans-serif;font-size:.9rem}
.part-intro p.bianxu{letter-spacing:0;font-size:1rem;font-family:inherit;text-align:justify;text-indent:2em;color:var(--ink);margin:0 0 .9em}
h3.sec .dia{margin-right:.4em}
"""
    v = META['version']
    toc = []
    for kind, sid, title, lvl, _ in secs:
        if kind == 'cp':
            continue
        cls = {'part': 'p', 'chapter': 'c'}.get(kind, 'f')
        toc.append('<li class="%s"><a href="#%s">%s</a></li>' % (cls, sid, inline(title)))
    body = []
    for s in secs:
        body.append(sec_html(*s))
        if s[0] == 'cp':
            body.append(EPIGRAPH.replace('section', 'div'))
    han = sum(len(HAN.findall((SRC / (f + '.md')).read_text())) for f in FILES)
    head = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>全文网页阅读 · {META['title']} · 德麦国际专著第 {META['no']} 号</title>
<meta name="description" content="《{META['title']}——{META['subtitle']}》全文网页版。{META['author']} 著，德麦国际专著第 {META['no']} 号，约 {han/10000:.0f} 万汉字。">
<meta name="tier" content="L0"><link rel="canonical" href="https://sdeuniverses.com/books/m/{META['no']}/text/">
<style>{style}</style></head><body><div id="prog"></div>
<div class="bar"><a href="/books/m/{META['no']}/">← 书籍详情</a><a href="/books/m/{META['no']}/read.html">在线翻页</a><a href="/books/m/{META['no']}/{SLUG}-print.pdf?v={v}" target="_blank" rel="noopener">PDF</a><span class="sp"></span><button id="fs">字号</button><button id="th">夜间</button></div>
<div class="wrap">
<div class="hero"><img src="/books/m/{META['no']}/cover.jpg?v={v}" alt="封面"><h1>{META['title']}</h1><p>{META['subtitle']}</p>
<p style="color:var(--dim);margin-top:.5rem">{META['author']} 著 · 德麦国际专著第 {META['no']} 号 · ISBN {META['isbn']} · 约 {han/10000:.0f} 万汉字</p></div>
<details class="toc" open><summary>目录（出版信息 · 作者介绍 · 内容提要 · 自序 · 导论 · 六部十六章 · 结语 · 方法附录 · 研究附录 · 参考文献）</summary><ul>{''.join(toc)}</ul></details>
"""
    tail = f"""<div class="foot">德麦国际出版社 · Demai International Press · <a href="/books/">专著书架</a> · <a href="/books/m/{META['no']}/">书籍详情</a></div>
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
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    secs = build_sections()
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
