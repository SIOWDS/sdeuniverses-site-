#!/usr/bin/env python3
"""第 372 号《社会学学派解构入门》PDF 打磨重排（2026-10-17，王德生令：逐页打磨、美化、合并过短段落、减少页数）。

原统稿 Markdown 未入库，本脚本以站上全文网页 public/books/m/372/text/index.html 为底本重排：
  · 合并过短段落（≤SHORT 字的普通段：优先并入下一段，下一段是列举/字段时并入上一段）；
  · 「王德生说：」并进其后的引文框，做成框内小标；
  · 「命题卡（…）」及其后的字段段落收成一张卡片；
  · 附录七的空壳嵌套列表摊平；编序重复的标签去重；
  · 表格可跨页、表头重复；标题与下文不拆；孤行寡行至少两行。
用法：
  python3 tools/book-m372/build.py --out <目录> [--old-reader <旧阅读版PDF>]
产物：<out>/print.pdf（170×240，无封面）与 <out>/reader.pdf（190×250，封面封底取自旧阅读版首末页）。
"""
import argparse
import copy
import re
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'public/books/m/372/text/index.html'
SHORT = 34          # 「太短」的段落：一行放得下
CJ = '一-鿿　-〿＀-￯'

TITLE = '社会学学派解构入门'
FULL = '社会学学派解构入门——普通人都能读懂的'

PUBINFO = [
    ('书名', '《社会学学派解构入门——普通人都能读懂的》'),
    ('著者', '王德生'),
    ('执笔', '复合主体：王德生立题、给出全书口径与裁定，Claude 执笔与统稿'),
    ('出版', '德麦国际出版社（Demai International Press）· 新加坡'),
    ('编号', '德麦国际专著第 372 号'),
    ('ISBN', '979-8-90690-558-1'),
    ('定价', 'US$20'),
    ('开本', '{size}'),
    ('字数', '约 39 万字'),
    ('版次', '2026 年 10 月第 1 版（2026 年 10 月 17 日修订排印）'),
]
PUBNOTES = [
    'AI 协作声明：本书的学科诊断、社会的 SDE 定义、三句判词、出路主张与各项裁定由王德生给出；文字在其指令下由 AI（Claude）协作成稿与统稿，并经其审定。本书以第 321 号《社会科学学派的SDE解构与思想创新》为纲，与第 319 号经济学卷、第 320 号法学卷、第 360 号政治学卷、第 361 号语言学卷配套。书中槐荫里小区的人物、业主群与电梯议事场景均为作者构想，不是真人真事。凡标“按本书的读法”之处，是作者的建模判断，不是学界公认的事实；凡标〔待核〕之处，出处或细节尚未逐条核对，全书汇总于附录七。涉及国家政策的章节只描述公开条文与事件，不作评判。',
    '全书结构：出版信息、作者介绍、前言、导读、目录；导论；上编十编六十四章（第 1—64 章）；下编导论、二十章（第 65—84 章）与下编结语；结语、参考书目、附录七件。',
    '版权所有，侵权必究。',
]

FIELD = re.compile(r'^[^，。：；“”（）\s]{1,10}[：:]')
ENUM = re.compile(r'^(第[一二三四五六七八九十]+[，、：]|[①-⑳]|[一二三四五六七八九十]+[、，]|\d+[.、）)])')


# ───────────────────────── 段落整理 ─────────────────────────
def plain_p(t):
    return isinstance(t, Tag) and t.name == 'p' and not t.get('class')


def txt(t):
    return re.sub(r'\s+', '', t.get_text())


def is_short(t):
    return plain_p(t) and 0 < len(txt(t)) <= SHORT and not t.find('br')


def siblings(node):
    return [c for c in node.children if not (isinstance(c, NavigableString) and not c.strip())]


def append_into(dst, src, front=False):
    kids = list(src.contents)
    if front:
        for k in reversed(kids):
            dst.insert(0, k.extract() if isinstance(k, Tag) else NavigableString(str(k)))
    else:
        for k in kids:
            dst.append(k.extract() if isinstance(k, Tag) else NavigableString(str(k)))
    src.decompose()


def oral_labels(soup, nodes):
    """「王德生说：」＋引文框 → 框内小标。"""
    n = 0
    for i, t in enumerate(nodes):
        if not plain_p(t):
            continue
        s = txt(t)
        m = re.fullmatch(r'(.{1,14}?(说|写道|口述(第.{1,3}条)?|这样说))[：:]', s)
        if not m:
            continue
        nxt = t.find_next_sibling()
        if nxt is not None and nxt.name == 'blockquote':
            lab = soup.new_tag('div', attrs={'class': 'qlab'})
            lab.string = m[1]
            nxt.insert(0, lab)
            nxt['class'] = nxt.get('class', []) + ['oral']
            t.decompose()
            n += 1
    return n


def cards(soup, container):
    """命题卡（…）＋字段段落 → 一张卡。"""
    n = 0
    for p in list(container.find_all('p', recursive=False)):
        if p.parent is None or not plain_p(p):
            continue
        s = txt(p)
        if not re.fullmatch(r'命题卡[一二三四五六七八九十]?(（[^）]{1,20}）|　.{1,30})?', p.get_text().strip().replace(' ', '')):
            continue
        box = soup.new_tag('div', attrs={'class': 'card'})
        head = soup.new_tag('div', attrs={'class': 'card-h'})
        head.string = p.get_text().strip()
        box.append(head)
        cur = p.find_next_sibling()
        p.replace_with(box)
        while cur is not None and plain_p(cur) and FIELD.match(txt(cur)):
            nxt = cur.find_next_sibling()
            m = re.match(r'^\s*([^，。：；“”（）\s]{1,10})[：:]', cur.get_text())
            row = soup.new_tag('p', attrs={'class': 'cf'})
            if m:
                k = soup.new_tag('b')
                k.string = m[1]
                row.append(k)
                # 去掉字段名，保留其余内联标记
                first = cur.contents[0]
                if isinstance(first, NavigableString) and first.lstrip().startswith(m[1]):
                    first.replace_with(NavigableString(re.sub(r'^\s*' + re.escape(m[1]) + r'[：:]', '', str(first), 1)))
                    append_into(row, cur)
                else:
                    append_into(row, cur)
            else:
                append_into(row, cur)
            box.append(row)
            cur = nxt
        n += 1
    return n


def merge_short(container):
    """合并过短段落。返回合并次数。"""
    n = 0
    changed = True
    while changed:
        changed = False
        nodes = siblings(container)
        for i, t in enumerate(nodes):
            if not is_short(t):
                continue
            prev = nodes[i - 1] if i > 0 else None
            nxt = nodes[i + 1] if i + 1 < len(nodes) else None
            s = txt(t)
            nxt_ok = plain_p(nxt) and not FIELD.match(txt(nxt)) and not ENUM.match(txt(nxt)) and not nxt.find('br')
            prev_ok = plain_p(prev) and not txt(prev).endswith(('：', ':')) and not prev.find('br')
            if FIELD.match(s) or ENUM.match(s):
                continue  # 字段行、列举项是结构，不并
            if nxt_ok:
                append_into(nxt, t, front=True); n += 1; changed = True; break
            if prev_ok and not s.endswith(('：', ':')):
                append_into(prev, t); n += 1; changed = True; break
    return n


def tidy(soup):
    stats = dict(oral=0, card=0, merge=0)
    # 参考书目逐条成段，不参与合并
    for sec in soup.select('section.back-sec'):
        h1 = sec.find('h1')
        if h1 and h1.get_text(strip=True) == '参考书目':
            for i, bp in enumerate(sec.find_all('p', recursive=False)):
                if i:
                    bp['class'] = ['bib']
    # 编序标签去重
    for pi in soup.select('div.part-intro'):
        bx = pi.select('div.bianxu')
        for extra in bx[1:]:
            extra.decompose()
    # 附录里只包一层列表的空 li → 摊平
    for li in soup.find_all('li'):
        kids = siblings(li)
        if len(kids) == 1 and isinstance(kids[0], Tag) and kids[0].name in ('ul', 'ol'):
            inner = kids[0]
            for sub in list(inner.find_all('li', recursive=False)):
                li.insert_before(sub.extract())
            li.decompose()
    # 小账标签行
    for lt in soup.select('div.ledger span.lt'):
        par = lt.parent
        nb = lt.find_next_sibling()
        if nb is not None and nb.name == 'br':
            nb.decompose()
        lt.decompose()
        if par.name == 'p' and not txt(par):
            par.decompose()
    containers = set()
    for p in soup.find_all('p'):
        if p.parent is not None:
            containers.add(id(p.parent))
    seen = {}
    for p in soup.find_all('p'):
        seen.setdefault(id(p.parent), p.parent)
    for c in seen.values():
        if c.name in ('li', 'td', 'th'):
            continue
        stats['oral'] += oral_labels(soup, siblings(c))
    for c in list(seen.values()):
        if c.name in ('li', 'td', 'th', 'blockquote'):
            continue
        stats['card'] += cards(soup, c)
    for c in list(seen.values()):
        if c.name in ('li', 'td', 'th', 'blockquote'):
            continue
        try:
            stats['merge'] += merge_short(c)
        except Exception:
            pass
    return stats


# ───────────────────────── 结构切分 ─────────────────────────
def load():
    soup = BeautifulSoup(SRC.read_text(encoding='utf-8'), 'html.parser')
    wrap = soup.select_one('div.wrap')
    for x in wrap.select('nav, div.hero, details.toc, div.foot'):
        x.decompose()
    return soup, wrap


def classify(wrap, soup):
    """把顶层节点切成 [(kind, title, sub, nodes, id)]。"""
    out = []
    cur = None
    for node in siblings(wrap):
        if not isinstance(node, Tag):
            continue
        cls = node.get('class') or []
        if node.name == 'section' and 'front-sec' in cls or node.name == 'section' and 'back-sec' in cls:
            h1 = node.find('h1', class_='front-title')
            sub = node.find('div', class_='fs-sub')
            title = h1.get_text(strip=True)
            subt = sub.get_text(strip=True) if sub else ''
            for x in (h1, sub, node.find('div', class_='rule')):
                if x is not None:
                    x.extract()
            kind = 'back' if 'back-sec' in cls else 'front'
            if title in ('上编', '下编') and not txt(node):
                kind = 'half'
            cur = [kind, title, subt, [node], node.get('id')]
            out.append(cur)
        elif node.name == 'section' and 'part' in cls:
            lab = node.find('div', class_='part-label').get_text(strip=True)
            tit = node.find('div', class_='part-title').get_text(strip=True)
            intro = node.find('div', class_='part-intro')
            for bx in intro.select('div.bianxu'):
                bx.decompose()
            cur = ['part', lab, tit, [intro], node.get('id')]
            out.append(cur)
        elif node.name == 'div' and 'chapter' in cls:
            lab = node.find('div', class_='chap-label').get_text(strip=True)
            tit = node.find('h2', class_='chap-title').get_text(strip=True)
            cur = ['chapter', lab, tit, [], node.get('id')]
            out.append(cur)
        else:
            cur[3].append(node)
    return out


# ───────────────────────── 生成 HTML ─────────────────────────
def thin(h):
    h = re.sub(r'(?<=[' + CJ + r']) (?=[0-9A-Za-z$＝×→←↔#])', ' ', h)
    h = re.sub(r'(?<=[0-9A-Za-z%$）)×→←↔]) (?=[' + CJ + r'])', ' ', h)
    h = h.replace(' × ', ' × ').replace(' → ', ' → ')
    return h


def inner(nodes):
    return ''.join(str(n) for n in nodes)


def section_body(kind, nodes):
    body = inner(nodes)
    if kind in ('front', 'back') and nodes and nodes[0].name == 'section':
        body = ''.join(str(c) for c in nodes[0].contents)
    return body


def decorate(body):
    """章内样式标记：章问、章末动用框、带走的话。"""
    body = re.sub(r'^\s*<blockquote>\s*<p>这一章的问题：(.*?)</p>\s*</blockquote>',
                  r'<div class="qbox"><span class="lab">这一章的问题</span><p>\1</p></div>', body, count=1, flags=re.S)
    body = re.sub(r'<blockquote>\s*(<p><strong>本章动用</strong>.*?)</blockquote>',
                  r'<div class="usage">\1</div>', body, flags=re.S)
    body = re.sub(r'<p class="takeaway"><span class="tk-l">带走的话</span><br/?>',
                  r'<div class="takeaway"><span class="lab">带走的话</span><p>', body)
    body = re.sub(r'(<div class="takeaway"><span class="lab">带走的话</span><p>.*?)</p>', r'\1</p></div>', body, flags=re.S)
    # 章末两件绑在一起，不拆页
    body = re.sub(r'(<div class="takeaway">.*?</div>)\s*(<div class="usage">.*?</div>)\s*$',
                  r'<div class="chapend">\1\2</div>', body, flags=re.S)
    body = body.replace('<div class="ledger">', '<div class="ledger"><span class="lab">小　账</span>')
    body = re.sub(r'<h2 class="sec"><span class="dia">◆</span>', '<h3 class="sec"><span class="dia">◆</span>', body)
    body = re.sub(r'(<h3 class="sec">.*?)</h2>', r'\1</h3>', body)
    body = re.sub(r'<h3>(.*?)</h3>', r'<h4 class="sub">\1</h4>', body)
    body = body.replace('<span class="hk">', '<span class="tbd">')
    body = re.sub(r'<td>([^<]{1,6})</td>', r'<td class="nw">\1</td>', body)
    return body


def build_html(secs, edition):
    W, H = (170, 240) if edition == 'print' else (190, 250)
    size = '%d mm × %d mm' % (W, H)
    front, main = [], []
    toc = []
    in_main = False
    for kind, title, sub, nodes, sid in secs:
        if kind == 'front' and title == '导论':
            in_main = True
        tgt = main if in_main else front
        body = decorate(section_body(kind, nodes))
        if kind == 'chapter':
            num = re.search(r'\d+', title)
            toc.append(('c', sid, '%s　%s' % (title, sub)))
            tgt.append('<section class="chapter" id="%s"><div class="chead"><div class="cnum">%02d</div>'
                       '<div class="clab">%s</div><h2 class="ctitle" data-run="%s" data-bm="%s　%s">%s</h2><div class="crule"></div></div>%s</section>'
                       % (sid, int(num[0]) if num else 0, title, sub, title, sub, sub, body))
        elif kind == 'part':
            toc.append(('p', sid, '%s　%s' % (title, sub)))
            intro = body if txt(BeautifulSoup(body, 'html.parser')) else ''
            tgt.append('<section class="part" id="%s"><div class="pinner"><div class="plab">%s</div>'
                       '<h1 class="ptitle" data-bm="%s　%s">%s</h1><div class="prule">◆</div>%s</div></section>'
                       % (sid, ' '.join(title), title, sub, sub, '<div class="pintro"><div class="plab2">编　序</div>%s</div>' % body if intro else ''))
        elif kind == 'half':
            toc.append(('h', sid, '%s　%s' % (title, sub)))
            tgt.append('<section class="half" id="%s"><div class="hinner"><h1 class="htitle" data-bm="%s　%s">%s</h1>'
                       '<div class="hsub">%s</div></div></section>' % (sid, title, sub, '　'.join(title), sub))
        else:
            cls = 'fs' + (' appxs' if title == '附录' else '') + (' bibs' if title == '参考书目' else '') + (' intro' if title == '导论' else '')
            toc.append(('f' if not in_main else 'b', sid, title + ('　' + sub if sub else '')))
            body = re.sub(r'<h2 class="chap-title appx" id="(s\d+)">(.*?)</h2>',
                          lambda m: (toc.append(('a', m[1], m[2])) or '') + '<h2 class="appx" id="%s">%s</h2>' % (m[1], m[2]), body)
            tgt.append('<section class="%s" id="%s"><h1 class="ftitle" data-bm="%s">%s</h1>%s<div class="frule"></div>%s</section>'
                       % (cls, sid, title + ('　' + sub if sub else ''), title, '<div class="fsub">%s</div>' % sub if sub else '', body))
            if title == '导读':
                tgt.append('@@TOC@@')
    # 目录
    rows = []
    for k, sid, t in toc:
        roman = ', lower-roman' if k == 'f' else ''
        rows.append('<li class="t%s"><a href="#%s"><span class="tt">%s</span></a></li>' % (k, sid, t))
    tochtml = '<section class="fs tocs" id="toc"><h1 class="ftitle">目　录</h1><div class="frule"></div><ul class="toc">%s</ul></section>' % ''.join(rows)
    front = [tochtml if x == '@@TOC@@' else x for x in front]
    title_page = ('<section class="titlepage"><div class="tp-pre">普通人都能读懂的</div><div class="tp-big">社会学<br/>学派解构入门</div>'
                  '<div class="tp-rule"></div><div class="tp-au">王德生　著</div>'
                  '<div class="tp-pub">德麦国际出版社<br/><span>DEMAI INTERNATIONAL PRESS</span></div></section>')
    cp = ''.join('<tr><th>%s</th><td>%s</td></tr>' % (a, b.format(size=size)) for a, b in PUBINFO)
    cpnotes = ''.join('<p>%s</p>' % x for x in PUBNOTES)
    pubinfo = ('<section class="pubinfo" id="pub"><h1 class="ftitle">出版信息</h1><div class="frule"></div>'
               '<table class="cp">%s</table><div class="cpn">%s</div></section>' % (cp, cpnotes))
    html = ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>%s</title>'
            '<meta name="author" content="王德生"><meta name="description" content="德麦国际专著第 372 号">'
            '<style>%s</style></head><body>'
            '<div class="frontmatter">%s%s%s</div><div class="mainmatter">%s</div></body></html>'
            % (FULL, css(edition), title_page, pubinfo, ''.join(front), ''.join(main)))
    return thin(html)


# ───────────────────────── 版式 ─────────────────────────
NAVY, GOLD, CREAM, INK = '#1F3A5F', '#B08A3C', '#F6F0E1', '#222'


def css(edition):
    if edition == 'print':
        W, H, fs, lh, mt, mo, mb, mi = 170, 240, 9.9, 1.72, 17, 15, 17, 19
    else:
        W, H, fs, lh, mt, mo, mb, mi = 190, 250, 10.5, 1.74, 18, 18, 18, 20
    return f"""
@page {{ size:{W}mm {H}mm; margin:{mt}mm {mo}mm {mb}mm {mi}mm;
  @bottom-center {{ content: counter(page); font:7.6pt 'Noto Sans CJK SC'; color:#9a8b6a }} }}
@page :left {{ margin-left:{mo}mm; margin-right:{mi}mm;
  @top-left {{ content: '{TITLE}'; font:7.4pt 'Noto Sans CJK SC'; color:#8f8770; vertical-align:bottom; padding-bottom:3mm }} }}
@page :right {{ margin-left:{mi}mm; margin-right:{mo}mm;
  @top-right {{ content: string(run); font:7.4pt 'Noto Sans CJK SC'; color:#8f8770; vertical-align:bottom; padding-bottom:3mm }} }}
@page front {{ @bottom-center {{ content: counter(page, lower-roman); font:7.6pt 'Noto Sans CJK SC'; color:#9a8b6a }} }}
@page bare {{ @top-left {{content:none}} @top-right {{content:none}} @bottom-center {{content:none}} }}
html {{ font-family:'Noto Serif CJK SC',serif; font-size:{fs}pt; line-height:{lh}; color:{INK}; }}
body {{ margin:0 }}
.frontmatter {{ page:front; }}
.intro {{ page:intro; }}
@page intro:nth(1 of intro) {{ counter-reset: page 1; }}
h1, h2, h3, h4, h5, h6 {{ bookmark-level:none }}
p {{ margin:0 0 .28em; text-indent:2em; text-align:justify; orphans:2; widows:2; }}
b, strong {{ font-family:'Noto Sans CJK SC',sans-serif; font-weight:700; color:#1b2a3d; font-size:.95em }}
.tbd {{ font-family:'Noto Sans CJK SC',sans-serif; font-size:.72em; color:#a07c3a; letter-spacing:.02em }}
a {{ color:inherit; text-decoration:none }}

/* 扉页、出版信息 */
.titlepage {{ page:bare; text-align:left; padding-top:30mm; }}
.tp-pre {{ font-family:'Noto Sans CJK SC'; color:{GOLD}; letter-spacing:.3em; font-size:11pt; margin-bottom:5mm }}
.tp-big {{ font-family:'Noto Serif CJK SC'; font-weight:700; color:{NAVY}; font-size:30pt; line-height:1.35; letter-spacing:.06em }}
.tp-rule {{ width:22mm; border-top:1.4pt solid {GOLD}; margin:9mm 0 }}
.tp-au {{ font-size:13pt; letter-spacing:.2em; color:#333 }}
.tp-pub {{ margin-top:{H*0.29:.0f}mm; font-family:'Noto Sans CJK SC'; font-weight:700; color:{NAVY}; font-size:10.5pt; letter-spacing:.2em }}
.tp-pub span {{ font-weight:400; font-size:6.5pt; letter-spacing:.25em; color:#8f8770 }}
.pubinfo {{ break-before:page; }}
table.cp {{ width:100%; border-collapse:collapse; font-size:.86em; margin:2mm 0 6mm }}
table.cp th {{ background:none; width:15mm; text-align:left; color:{GOLD}; font-family:'Noto Sans CJK SC'; font-weight:400; padding:1.3mm 0; border-bottom:.4pt solid #e4dcc8; vertical-align:top }}
table.cp td {{ padding:1.3mm 0; border-bottom:.4pt solid #e4dcc8 }}
.cpn p {{ font-size:.78em; line-height:1.7; text-indent:0; color:#555; margin-bottom:2.2mm }}

/* 前置、后置标题 */
.fs, .pubinfo, .tocs {{ break-before:page; }}
.ftitle {{ font-family:'Noto Serif CJK SC'; font-weight:700; color:{NAVY}; font-size:19pt; letter-spacing:.25em; margin:6mm 0 1.5mm;
  bookmark-level:1; string-set: run content(); }}
.ftitle[data-bm], .ptitle, .htitle {{ bookmark-label:attr(data-bm) }}
.fsub {{ font-family:'Noto Sans CJK SC'; color:{GOLD}; font-size:9.6pt; letter-spacing:.06em; margin-bottom:2mm }}
.frule {{ width:16mm; border-top:1.2pt solid {GOLD}; margin:3mm 0 7mm }}
.tocs .ftitle {{ bookmark-level:1 }}
.pubinfo .ftitle {{ bookmark-level:1 }}

/* 目录 */
ul.toc {{ list-style:none; padding:0; margin:0; font-size:.86em; line-height:1.55 }}
ul.toc li {{ margin:0; break-inside:avoid }}
ul.toc a {{ display:block }}
ul.toc a::after {{ content: leader('·') target-counter(attr(href), page); color:#8f8770; font-family:'Noto Sans CJK SC'; font-size:.9em }}
ul.toc li.tf a::after {{ content: leader('·') target-counter(attr(href), page, lower-roman) }}
ul.toc li.th {{ margin-top:3.2mm; font-family:'Noto Sans CJK SC'; font-weight:700; color:{NAVY}; font-size:1.05em; break-after:avoid }}
ul.toc li.tp {{ margin-top:2.2mm; font-family:'Noto Sans CJK SC'; font-weight:700; color:{NAVY}; break-after:avoid }}
ul.toc li.tc {{ padding-left:5mm; color:#333 }}
ul.toc li.ta {{ padding-left:5mm; color:#333 }}
ul.toc li.tf, ul.toc li.tb {{ margin-top:1.4mm; font-weight:700; color:{NAVY} }}

/* 上编、下编 */
.half {{ page:bare; break-before:page; break-after:page; height:100%; display:flex; }}
.hinner {{ padding-top:38%; text-align:center; width:100% }}
.htitle {{ font-family:'Noto Serif CJK SC'; font-weight:700; color:{NAVY}; font-size:30pt; letter-spacing:.4em; margin:0; bookmark-level:1 }}
.hsub {{ font-family:'Noto Sans CJK SC'; color:{GOLD}; font-size:12pt; letter-spacing:.35em; margin-top:6mm }}

/* 编 */
.part {{ break-before:page; break-after:page; page:bare; }}
.pinner {{ padding-top:20%; text-align:center }}
.plab {{ font-family:'Noto Sans CJK SC'; color:{GOLD}; letter-spacing:.35em; font-size:10pt }}
.ptitle {{ font-family:'Noto Serif CJK SC'; font-weight:700; color:{NAVY}; font-size:21pt; line-height:1.45; margin:4mm 6mm 0; bookmark-level:1; string-set: run content() }}
.prule {{ color:{GOLD}; font-size:8pt; margin:6mm 0 8mm }}
.pintro {{ text-align:left; margin:0 2mm; padding:5mm 6mm 3mm; border-top:.6pt solid #e2d6b8; border-bottom:.6pt solid #e2d6b8 }}
.plab2 {{ font-family:'Noto Sans CJK SC'; color:{GOLD}; letter-spacing:.3em; font-size:8.6pt; text-align:center; margin-bottom:3mm }}
.pintro p {{ font-size:.93em; line-height:1.72 }}

/* 章 */
.chapter {{ break-before:page; }}
.chead {{ position:relative; margin:2mm 0 6mm; }}
.cnum {{ position:absolute; right:0; top:-6mm; font-family:'Noto Serif CJK SC'; font-weight:700; font-size:40pt; color:#efe5cc; line-height:1 }}
.clab {{ font-family:'Noto Sans CJK SC'; font-weight:700; color:{GOLD}; font-size:9pt; letter-spacing:.12em; position:relative }}
.ctitle {{ font-family:'Noto Serif CJK SC'; font-weight:700; color:{NAVY}; font-size:16.5pt; line-height:1.45; margin:2mm 0 0; padding-right:16mm;
  position:relative; bookmark-level:2; bookmark-label:attr(data-bm); string-set: run attr(data-run) }}
.crule {{ width:14mm; border-top:1.2pt solid {GOLD}; margin-top:4mm }}

h3.sec {{ font-family:'Noto Sans CJK SC'; font-weight:700; color:{NAVY}; font-size:10.4pt; line-height:1.5; margin:1.15em 0 .5em; break-after:avoid; }}
h3.sec .dia {{ color:{GOLD}; font-size:.75em; margin-right:.45em; vertical-align:.1em }}
h4.sub {{ font-family:'Noto Sans CJK SC'; font-weight:700; color:#3b4f6b; font-size:9.8pt; margin:.9em 0 .35em; break-after:avoid }}
h2.appx {{ break-before:page; font-family:'Noto Serif CJK SC'; font-weight:700; color:{NAVY}; font-size:14pt; line-height:1.5; margin:4mm 0 5mm;
  padding-bottom:3mm; border-bottom:1pt solid {GOLD}; bookmark-level:2; string-set: run content() }}

/* 框 */
.qbox {{ background:{CREAM}; border-left:2.2pt solid {GOLD}; padding:3mm 4.5mm 2.4mm; margin:0 0 5mm; break-inside:avoid }}
.qbox .lab, .ledger .lab, .takeaway .lab {{ display:block; font-family:'Noto Sans CJK SC'; color:{GOLD}; font-size:7.6pt; letter-spacing:.25em; margin-bottom:1.2mm }}
.qbox p {{ text-indent:0; color:#333; margin:0 }}
blockquote {{ margin:.55em 0 .7em; padding:2.6mm 4.5mm 2mm; background:{CREAM}; border-left:2.2pt solid {GOLD}; }}
blockquote p {{ text-indent:0; margin-bottom:.2em; color:#2d2a24 }}
blockquote .qlab {{ font-family:'Noto Sans CJK SC'; color:{GOLD}; font-size:7.6pt; letter-spacing:.2em; margin-bottom:1mm }}
.ledger {{ border:.6pt solid #dccfae; background:#fbf7ec; padding:3mm 4.5mm 2mm; margin:.7em 0 .8em; border-radius:1.2mm }}
.ledger p {{ text-indent:0; font-size:.95em; margin-bottom:.3em }}
.card {{ border:.7pt solid {NAVY}; border-radius:1.2mm; padding:0 0 1.6mm; margin:.7em 0 .9em; break-inside:avoid; }}
.card-h {{ background:{NAVY}; color:#fff; font-family:'Noto Sans CJK SC'; font-size:8.2pt; letter-spacing:.15em; padding:1.2mm 4mm; margin-bottom:1.8mm }}
.card p.cf {{ text-indent:0; margin:0 4mm .3em; font-size:.94em; padding-left:15mm; text-indent:-15mm }}
.card p.cf b {{ display:inline-block; width:14mm; margin-right:1mm; color:{GOLD}; font-size:.86em; text-indent:0 }}
.chapend {{ break-inside:avoid; margin-top:1em }}
.takeaway {{ border-top:.8pt solid {GOLD}; border-bottom:.8pt solid {GOLD}; padding:2.6mm 1mm 2mm; margin:0 0 3mm }}
.takeaway p {{ text-indent:0; line-height:1.75; margin:0 }}
.usage {{ font-size:.8em; line-height:1.65; color:#666; padding:0 1mm }}
.usage p {{ text-indent:0; margin:0 }}
.usage strong {{ color:#555 }}

/* 列表、表格 */
ul, ol {{ margin:.3em 0 .6em; padding-left:2.2em }}
li {{ margin:0 0 .15em; text-align:justify }}
li p {{ text-indent:0 }}
.tw {{ margin:.6em 0 .9em }}
table {{ width:100%; border-collapse:collapse; font-size:.82em; line-height:1.55 }}
thead {{ display:table-header-group }}
th {{ background:{NAVY}; color:#fff; font-family:'Noto Sans CJK SC'; font-weight:700; font-size:.92em; padding:1.4mm 1.8mm; text-align:left; vertical-align:bottom }}
td {{ padding:1.3mm 1.8mm; border-bottom:.4pt solid #ddd3bb; vertical-align:top; text-align:left }}
tbody tr:nth-child(even) td {{ background:#faf6ec }}
tr {{ break-inside:avoid }}
td.nw {{ white-space:nowrap; font-family:'Noto Sans CJK SC'; color:{NAVY}; font-size:.95em }}

/* 参考书目 */
.bibs p.bib {{ text-indent:-2em; padding-left:2em; font-size:.86em; line-height:1.6; margin-bottom:.35em; text-align:left }}
.bibs h4.sub {{ margin-top:1.1em }}
"""


def graft_covers(reader_pdf, old_reader):
    import fitz
    new = fitz.open(reader_pdf)
    old = fitz.open(old_reader)
    out = fitz.open()
    out.insert_pdf(old, from_page=0, to_page=0)
    out.insert_pdf(new)
    out.insert_pdf(old, from_page=len(old) - 1, to_page=len(old) - 1)
    toc = new.get_toc(simple=False)
    out.set_toc([[l, t, p + 1] + ([d] if False else []) for l, t, p, *d in toc] if toc else [])
    out.set_metadata(new.metadata)
    tmp = reader_pdf + '.tmp'
    out.save(tmp, garbage=3, deflate=True)
    Path(tmp).replace(reader_pdf)


def fix_toc(path):
    """书签里的细空格换回普通空格（翻页器目录与检索用书签文字）。"""
    import fitz
    d = fitz.open(path)
    toc = [[l, t.replace('\u2009', ' '), p] for l, t, p in d.get_toc()]
    d.set_toc(toc)
    tmp = path + '.tmp'
    d.save(tmp, garbage=3, deflate=True)
    Path(tmp).replace(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--old-reader')
    ap.add_argument('--only', choices=['print', 'reader'])
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    from weasyprint import HTML
    for ed in (['print', 'reader'] if not a.only else [a.only]):
        soup, wrap = load()
        st = tidy(soup)
        secs = classify(wrap, soup)
        html = build_html(secs, ed)
        (out / ('%s.html' % ed)).write_text(html, encoding='utf-8')
        pdf = out / ('%s.pdf' % ed)
        doc = HTML(string=html, base_url=str(ROOT / 'public')).render()
        doc.metadata.title = FULL
        doc.metadata.authors = ['王德生']
        doc.write_pdf(str(pdf))
        print(ed, 'pages', len(doc.pages), st)
        if ed == 'reader' and a.old_reader:
            graft_covers(str(pdf), a.old_reader)
        fix_toc(str(pdf))


if __name__ == '__main__':
    main()
