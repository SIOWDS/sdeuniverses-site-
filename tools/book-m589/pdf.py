#!/usr/bin/env python3
"""book.json → 印刷版（170×240）与阅读版（190×250）PDF。版式照第 220 号（第 311 号 build.py 所记）：
暖纸内页、藏青标题、浅金大号章码、金色“第 N 章”、金短线、◆ 金菱形小节、米底金线框、章末金菱形、编首花饰圆章与导语。"""
import html, json, re, sys
from pathlib import Path
import weasyprint, pymupdf

ROOT = Path('/home/claude/sde_ai_millennium/layout')
OUT = ROOT / 'out'
D = json.loads((ROOT / 'book.json').read_text(encoding='utf-8'))
META, SECS = D['meta'], D['secs']
BS, BH = "'Noto Serif CJK SC'", "'Noto Sans CJK SC'"


def inline(s):
    # WeasyPrint 只在空格处撑开两端对齐，汉字与西文之间改用不可撑开的四分之一空
    s = re.sub(r'(?<=[\u4e00-\u9fff]) (?=[A-Za-z0-9])|(?<=[A-Za-z0-9]) (?=[\u4e00-\u9fff])', '\u2005', s)
    s = html.escape(s, quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(【设想与模拟[^】]*】)', r'<span class="simi">\1</span>', s)
    return s


def blocks(bl):
    h = []
    for b in bl:
        k = b['k']
        if k == 'p':
            h.append('<p>%s</p>' % inline(b['s']))
        elif k == 'dlg':
            h.append('<p class="dlg">%s</p>' % inline(b['s']))
        elif k == 'sec':
            h.append('<h3 class="sec"><span class="dia">◆</span>%s</h3>' % inline(b['s']))
        elif k == 'sub':
            h.append('<h3 class="subhead">%s</h3>' % inline(b['s']))
        elif k == 'sim':
            h.append('<p class="sim">%s</p>' % html.escape(b['s']))
        elif k == 'bib':
            h.append('<p class="bib">%s</p>' % inline(b['s']))
        elif k == 'card':
            ps = ''.join('<p><span class="lk">%s：</span>%s</p>' % (inline(a), inline(c)) if a else '<p>%s</p>' % inline(c) for a, c in b['rows'])
            h.append('<div class="ledger"><span class="lab">答 案 卡</span>%s</div>' % ps)
        elif k == 'table':
            cols = ''.join('<col style="width:%d%%">' % w for w in b['w'])
            th = ''.join('<th>%s</th>' % inline(c) for c in b['head'])
            tr = ''.join('<tr>%s</tr>' % ''.join('<td>%s</td>' % inline(c) for c in r) for r in b['rows'])
            h.append('<table class="tb"><colgroup>%s</colgroup><thead><tr>%s</tr></thead><tbody>%s</tbody></table>' % (cols, th, tr))
    return '\n'.join(h)


EMB = ('<svg class="emb" viewBox="0 0 40 40"><circle cx="20" cy="20" r="13" fill="none" stroke="#B08A3C" stroke-width="1.3"/>'
       '<line x1="20" y1="3" x2="20" y2="37" stroke="#B08A3C" stroke-width="0.9"/><line x1="3" y1="20" x2="37" y2="20" stroke="#B08A3C" stroke-width="0.9"/>'
       '<path d="M20 12 L24.5 18 L20 27 L15.5 18 Z" fill="none" stroke="#1F3A5F" stroke-width="1.1"/>'
       '<circle cx="20" cy="18" r="1.6" fill="#B08A3C"/><circle cx="12.5" cy="28" r="1.5" fill="#58A9B5"/></svg>')


def sec_html(i, s):
    sid = 's%d' % i
    k = s['kind']
    if k == 'cp':
        tb = ''.join('<tr><th>%s</th><td>%s</td></tr>' % (inline(a), inline(c)) for a, c in s['rows'])
        nt = ''.join('<p%s>%s</p>' % (' class="cp-right"' if '侵权必究' in x else '', inline(x)) for x in s['notes'])
        return '<section class="front-sec clean" id="%s"><div class="cp-title">出 版 信 息</div><table class="cp">%s</table><div class="cp-notes">%s</div></section>' % (sid, tb, nt)
    if k == 'part':
        intro = ''.join('<p>%s</p>' % inline(x) for x in s['intro'])
        return ('<section class="part" id="%s">%s<div class="part-label">%s</div><h1 class="part-title">%s</h1><div class="rule"></div>'
                '<div class="daoyu">导　语</div><div class="part-intro">%s</div></section>' % (sid, EMB, ' '.join(s['label']), inline(s['name']), intro))
    if k == 'chapter':
        return ('<section class="chapter" id="%s"><div class="chapnum">%02d</div><div class="chap-label">第 %d 章</div><h2 class="chap-title">%s</h2><div class="rule"></div>%s<div class="endmark">◆</div></section>'
                % (sid, s['num'], s['num'], inline(s['name']), blocks(s['blocks'])))
    cls = 'front-sec' if k == 'front' else 'back-sec'
    t = 'fs-title appx' if k == 'appx' else 'fs-title'
    sub = '<div class="fs-sub">%s</div>' % inline(s['sub']) if s.get('sub') else ''
    end = '<div class="endmark">◆</div>' if s.get('end') else ''
    return '<section class="%s" id="%s"><h1 class="%s">%s</h1>%s<div class="rule"></div>%s%s</section>' % (cls, sid, t, inline(s['name']), sub, blocks(s['blocks']), end)


def css(W, H, pt, lh, m, fol='decimal'):
    t, o, b, i = m
    return f"""
@page{{size:{W}mm {H}mm;margin:{t}mm {o}mm {b}mm {i}mm;background:#FBF8F0}}
@page :left{{margin-left:{o}mm;margin-right:{i}mm;
  @top-left{{content:string(book);font:6.8pt {BH};color:#9A917E;vertical-align:bottom;padding-bottom:4mm}}
  @bottom-left{{content:counter(page,{fol});font:7.6pt {BS};color:#8A8578}}}}
@page :right{{
  @top-right{{content:string(chap);font:6.8pt {BH};color:#9A917E;vertical-align:bottom;padding-bottom:4mm}}
  @bottom-right{{content:counter(page,{fol});font:7.6pt {BS};color:#8A8578}}}}
@page :blank{{@top-left{{content:none}} @top-right{{content:none}} @bottom-left{{content:none}} @bottom-right{{content:none}}}}
@page clean{{@top-left{{content:none}} @top-right{{content:none}} @bottom-left{{content:none}} @bottom-right{{content:none}}}}
@page opener:left{{@top-left{{content:none}}}}
@page opener:right{{@top-right{{content:none}}}}
body{{font-family:{BS};font-size:{pt}pt;line-height:{lh};color:#2A2824;margin:0;string-set:book "{META['title']}"}}
p{{margin:0 0 .42em;text-indent:2em;text-align:justify;orphans:2;widows:2}}
strong{{color:#1F3A5F;font-weight:700}}
p.dlg{{text-indent:0;margin-bottom:.5em}}
p.dlg strong{{font-family:{BH};font-weight:700;font-size:.94em}}
p.sim,.simi{{font-family:{BH};color:#8F7434;font-size:{pt*.8:.2f}pt}}
p.sim{{text-indent:0;margin:2mm 0 3mm;padding:1mm 0 1mm 3mm;border-left:1.2pt solid #D9C39A;line-height:1.6;text-align:left}}
.clean{{page:clean}}
section{{break-before:page}}
section.part,section.front-sec,section.back-sec,section.toc{{page:opener}}
section.chapter{{page:chapter}}
@page chapter:left{{@top-left{{content:string(book);font:6.8pt {BH};color:#9A917E;vertical-align:bottom;padding-bottom:4mm}}}}
section.part{{break-before:right;text-align:center;padding-top:26mm}}
.emb{{width:15mm;height:15mm;display:block;margin:0 auto 7mm}}
.part-label{{font:700 9.5pt {BH};color:#B08A3C;letter-spacing:.6em;margin-bottom:5mm;text-indent:.6em}}
.part-title{{font:700 18.5pt/1.5 {BS};color:#1F3A5F;margin:0 8mm 4mm;string-set:chap content();bookmark-level:1;bookmark-label:content()}}
.part .rule{{margin:0 auto 9mm}}
.daoyu{{font:700 8.5pt {BH};color:#B08A3C;letter-spacing:.6em;margin-bottom:5mm}}
.part-intro{{text-align:left}}
.part-intro p{{font-size:{pt*0.93:.2f}pt;color:#4A463D}}
.rule{{width:13mm;border-top:.9pt solid #B08A3C;margin:3mm 0 7mm}}
.chapnum{{font:300 34pt/1 {BS};color:#D9C39A;margin-top:6mm;letter-spacing:.02em}}
.chap-label{{font:700 8.4pt {BH};color:#B08A3C;margin:2mm 0 1.5mm;letter-spacing:.08em}}
.chap-title{{font:700 16pt/1.45 {BS};color:#1F3A5F;margin:0;string-set:chap content();bookmark-level:2;bookmark-label:content()}}
.fs-title{{font:700 18pt/1.4 {BS};color:#1F3A5F;margin:14mm 0 1mm;letter-spacing:.12em;string-set:chap content();bookmark-level:1;bookmark-label:content()}}
.fs-title.appx{{bookmark-level:2;font-size:15pt;letter-spacing:.06em}}
.fs-sub{{font:400 10.4pt {BS};color:#B08A3C;margin-top:1.5mm}}
h3.sec{{font:700 {pt*1.03:.2f}pt/1.6 {BH};color:#1F3A5F;margin:5.5mm 0 2.4mm;break-after:avoid}}
h3.sec .dia{{color:#B08A3C;font-size:.78em;margin-right:.45em;vertical-align:.08em}}
h3.subhead{{font:700 {pt*1.05:.2f}pt/1.6 {BS};color:#1F3A5F;margin:6mm 0 2.5mm;break-after:avoid}}
.ledger{{background:#F6F1E4;border-left:1.6pt solid #B08A3C;padding:2.8mm 4mm 2.8mm;margin:5mm 0 4mm;break-inside:avoid}}
.ledger .lab{{display:block;font:700 7.4pt {BH};color:#B08A3C;letter-spacing:.3em;margin-bottom:1.6mm}}
.ledger p{{text-indent:0;margin:0 0 1mm;font-size:{pt*0.9:.2f}pt;line-height:1.72;color:#3A372F;text-align:left}}
.ledger .lk{{color:#1F3A5F;font-weight:700;font-family:{BH};font-size:.95em}}
.endmark{{text-align:center;color:#B08A3C;font-size:8pt;margin-top:6mm}}
table.tb{{width:100%;border-collapse:collapse;font-size:{pt*0.82:.2f}pt;line-height:1.6;margin:3mm 0;table-layout:fixed}}
table.tb th{{background:#1F3A5F;color:#FBF8F0;font:700 {pt*0.82:.2f}pt/1.6 {BH};padding:1.4mm 1.6mm;text-align:left}}
table.tb td{{border-bottom:.5pt solid #E4DCCB;padding:1.3mm 1.6mm;vertical-align:top}}
table.tb tr{{break-inside:avoid}}
table.tb tbody tr:nth-child(even) td{{background:#F6F1E4}}
p.bib{{text-indent:-2em;padding-left:2em;font-size:{pt*0.88:.2f}pt;line-height:1.75;margin-bottom:1.2mm;text-align:left}}
.titlepage{{page:clean;padding-top:30mm;position:relative;height:{H-t-b-1}mm}}
.titlepage .pre2{{font:400 9pt {BH};color:#8A8578;letter-spacing:.2em;margin-bottom:6mm}}
.titlepage .pre{{font:700 19pt/1.3 {BS};color:#1F3A5F;letter-spacing:.04em}}
.titlepage .big{{font:700 {(W-o-i)/10.6*2.83:.1f}pt/1.3 {BS};color:#1F3A5F;margin:2mm 0 5mm;white-space:nowrap}}
.titlepage .sub{{font:400 {pt}pt/1.7 {BS};color:#B08A3C}}
.titlepage .rule{{margin:6mm 0 0}}
.titlepage .au{{margin-top:34mm;font:400 11pt {BS};color:#2A2824;letter-spacing:.2em}}
.titlepage .pub{{position:absolute;bottom:0;font:700 8.5pt {BH};color:#1F3A5F;letter-spacing:.35em}}
.titlepage .pub span{{display:block;font:400 6.8pt {BH};color:#8A8578;letter-spacing:.08em;margin-top:1mm}}
.cp-title{{font:700 11pt {BH};color:#1F3A5F;letter-spacing:.8em;text-align:center;margin:2mm 0 4mm}}
table.cp{{width:100%;border-collapse:collapse;font-size:8.2pt;line-height:1.55}}
table.cp th{{font:400 7.6pt {BH};color:#8A8578;text-align:left;width:15mm;padding:1.2mm 2mm;vertical-align:top}}
table.cp td{{padding:1.2mm 2mm;color:#2A2824}}
table.cp tr:nth-child(odd){{background:#F4EFE3}}
.cp-notes{{margin-top:4mm}}
.cp-notes p{{text-indent:0;font-size:7.1pt;line-height:1.65;color:#5A554A;margin-bottom:1.2mm;text-align:left}}
.cp-notes strong{{color:#1F3A5F}}
.cp-right{{margin-top:3mm!important;letter-spacing:.2em}}
.epi{{page:clean;padding-top:60mm;text-align:center}}
.epi p{{text-indent:0;text-align:center;font-size:11pt;line-height:2.1;color:#1F3A5F}}
.epi .by{{font-size:8.6pt;color:#8A8578;margin-top:5mm}}
.toc h1{{font:700 18pt {BS};color:#1F3A5F;letter-spacing:.4em;margin:10mm 0 2mm}}
.toc ul{{list-style:none;padding:0;margin:4mm 0 0}}
.toc li{{display:flex;font-size:{pt*0.88:.2f}pt;line-height:1.66}}
.toc li a{{color:inherit;text-decoration:none}}
.toc li .t{{flex:1}}
.toc li .pg{{color:#8A8578;min-width:9mm;text-align:right}}
.toc li.p{{font-weight:700;color:#1F3A5F;margin-top:2.4mm}}
.toc li.c{{padding-left:2em}}
.toc li.f{{margin-top:1mm;color:#1F3A5F}}
.toc li.a{{padding-left:2em}}
"""


def doc(c, inner):
    return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><style>%s</style></head><body>%s</body></html>' % (c, inner)


def roman(n):
    s = ''
    for v, r in [(10, 'x'), (9, 'ix'), (5, 'v'), (4, 'iv'), (1, 'i')]:
        while n >= v:
            s += r; n -= v
    return s


def anchors(d):
    p = {}
    for no, pg in enumerate(d.pages, 1):
        for a in pg.anchors:
            if re.fullmatch(r's\d+', a) and a not in p:
                p[a] = no
    return p


def toc_html(pages, rom):
    li = []
    for i, s in enumerate(SECS):
        if s['kind'] == 'cp':
            continue
        sid = 's%d' % i
        cls = {'part': 'p', 'chapter': 'c', 'appx': 'a'}.get(s['kind'], 'f')
        pg = pages.get(sid)
        pgs = '' if pg is None else (roman(pg) if sid in rom else str(pg))
        li.append('<li class="%s"><span class="t"><a href="#%s">%s</a></span><span class="pg">%s</span></li>' % (cls, sid, inline(s['title']), pgs))
    return '<section class="toc front-sec"><h1>目录</h1><div class="rule"></div><ul>%s</ul></section>' % ''.join(li)


def build(tag, W, H, pt, lh, m, raster):
    c, cf = css(W, H, pt, lh, m), css(W, H, pt, lh, m, 'lower-roman')
    mi = next(i for i, s in enumerate(SECS) if s['kind'] == 'part')
    main_html = ''.join(sec_html(i, SECS[i]) for i in range(mi, len(SECS)))
    print(tag, 'rendering main...', flush=True)
    mdoc = weasyprint.HTML(string=doc(c, main_html)).render()
    pages = anchors(mdoc)
    print(tag, 'main pages', len(mdoc.pages), flush=True)
    title = ('<div class="titlepage"><div class="pre2">德麦国际专著 · 第 %d 号</div><div class="pre">千年难题，</div><div class="big">还要等下一个理论吗？</div><div class="sub">%s</div>'
             '<div class="rule"></div><div class="au">%s　　著</div><div class="pub">%s<span>%s</span></div></div>'
             % (META['no'], html.escape(META['subtitle']), META['author'], META['publisher'], META['publisher_en']))
    epi = '<section class="epi"><p>%s</p><p class="by">%s</p></section>' % tuple(D['epigraph'])
    fr = ''.join(sec_html(i, SECS[i]) for i in range(mi) if SECS[i]['kind'] == 'cp') + epi + ''.join(sec_html(i, SECS[i]) for i in range(mi) if SECS[i]['kind'] != 'cp')
    rom = set()
    fdoc = weasyprint.HTML(string=doc(cf, title + fr + toc_html(pages, rom))).render()
    pf = anchors(fdoc)
    rom = set(pf)
    fdoc = weasyprint.HTML(string=doc(cf, title + fr + toc_html({**pages, **pf}, rom))).render()
    pf = anchors(fdoc)
    book = pymupdf.open()
    size = None

    def add_cover(src):
        co = pymupdf.open(str(src))
        pg = co[0]
        if raster:
            pix = pg.get_pixmap(matrix=pymupdf.Matrix(2400 / pg.rect.width, 2400 / pg.rect.width))
            np = book.new_page(width=pg.rect.width, height=pg.rect.height)
            np.insert_image(np.rect, stream=pix.tobytes('jpeg', jpg_quality=90))
        else:
            book.insert_pdf(co)
    add_cover(OUT / f'cover-{tag}.pdf')
    w0, h0 = book[0].rect.width, book[0].rect.height
    book.new_page(width=w0, height=h0)
    f = pymupdf.open(stream=fdoc.write_pdf(), filetype='pdf')
    book.insert_pdf(f)
    if len(f) % 2:
        book.new_page(width=w0, height=h0)
    start = len(book) + 1
    mm = pymupdf.open(stream=mdoc.write_pdf(), filetype='pdf')
    book.insert_pdf(mm)
    if len(book) % 2:
        book.new_page(width=w0, height=h0)
    book.new_page(width=w0, height=h0)
    add_cover(OUT / f'back-{tag}.pdf')
    toc, prev = [], 0
    for i, s in enumerate(SECS):
        sid = 's%d' % i
        if sid in pf:
            g = 2 + pf[sid]
        elif sid in pages:
            g = start - 1 + pages[sid]
        else:
            continue
        L = 2 if s['kind'] in ('chapter', 'appx') else 1
        L = min(L, prev + 1); prev = L
        toc.append([L, s['title'].replace('　', ' '), g])
    book.set_toc(toc)
    book.set_metadata({'title': META['title'] + '——' + META['subtitle'], 'author': META['author'], 'subject': '德麦国际专著第 %d 号 · ISBN %s' % (META['no'], META['isbn']),
                       'creator': 'WeasyPrint', 'producer': 'WeasyPrint + PyMuPDF'})
    out = OUT / ('%s-%s.pdf' % (META['slug'], tag))
    book.save(str(out), garbage=4, deflate=True)
    (OUT / f'toc-{tag}.json').write_text(json.dumps({'toc': toc, 'offset': start}, ensure_ascii=False), encoding='utf-8')
    print(tag, 'done', len(book), 'pages; main starts', start, out.stat().st_size // 1024, 'KB', flush=True)


if __name__ == '__main__':
    which = sys.argv[1:] or ['print', 'reader']
    if 'print' in which:
        build('print', 170, 240, 10.3, 1.86, (20, 17, 19.5, 19), False)
    if 'reader' in which:
        build('reader', 190, 250, 12.2, 1.95, (20, 19, 20, 20), True)
