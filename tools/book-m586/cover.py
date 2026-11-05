#!/usr/bin/env python3
"""第 586 号《你没交给企业的那一半》（贝芳 著）封面与封底（工具链承自第 582 号，深青底、金青奶白三色，220 系列版式）：
主图：一条金线把画面分成两半——左边是一面整齐的格子墙（交出去的秩序），右边是一小块地，地上一株正在长的苗，
上方散着几点金色（没处放的混沌）。全部纯色，不用渐变。封面封底不写指导者（站上口径）。
用法：python3 cover.py --fonts /usr/share/fonts/opentype/noto --out <dir>
"""
import argparse
import math
import os
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0E2A2B', '#1A3E3C', '#153433'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#7FA7C9', '#EFE8D6', '#A9B6C8'
ISBN = '979-8-90690-610-6'
WAN = os.environ.get('WAN', '20')

L = ['0001101', '0011001', '0010011', '0111101', '0100011', '0110001', '0101111', '0111011', '0110111', '0001011']
G = ['0100111', '0110011', '0011011', '0100001', '0011101', '0111001', '0000101', '0010001', '0001001', '0010111']
R = ['1110010', '1100110', '1101100', '1000010', '1011100', '1001110', '1010000', '1000100', '1001000', '1110100']
PAR = ['LLLLLL', 'LLGLGG', 'LLGGLG', 'LLGGGL', 'LGLLGG', 'LGGLLG', 'LGGGLL', 'LGLGLG', 'LGLGGL', 'LGGLGL']


def ean13_bits(isbn):
    d = re.sub(r'\D', '', isbn)
    s = sum(int(c) * (3 if i % 2 else 1) for i, c in enumerate(d[:12]))
    assert int(d[12]) == (10 - s % 10) % 10, 'ISBN 校验位不对'
    bits = '101'
    for i, c in enumerate(d[1:7]):
        bits += (L if PAR[int(d[0])][i] == 'L' else G)[int(c)]
    bits += '01010' + ''.join(R[int(c)] for c in d[7:]) + '101'
    return d, bits


def bez(p0, p1, p2, p3, t):
    u = 1 - t
    return (u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
            u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1])


def tapered(pts, w0, w1, power=1.6):
    """沿折线画一条由粗到细的笔触，返回多边形 path。"""
    left, right = [], []
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        a = pts[max(i - 1, 0)]; b = pts[min(i + 1, n - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln, dx / ln
        t = i / (n - 1)
        w = w1 + (w0 - w1) * (1 - t) ** power
        left.append((x + nx * w / 2, y + ny * w / 2)); right.append((x - nx * w / 2, y - ny * w / 2))
    poly = left + right[::-1]
    return 'M' + ' L'.join('%.1f %.1f' % p for p in poly) + ' Z'


def background(W, H, uid, split=0.365):
    """纯色底：三条横带拼出上深下浅（不用渐变——翻页器矢量模式画不出 PDF 渐变）。"""
    dots = []
    step = 44
    for yy in range(22, H, step):
        for xx in range(22 + (yy // step % 2) * 22, W, step):
            dots.append('<circle cx="%d" cy="%d" r="1.7"/>' % (xx, yy))
    return (f'<rect width="{W}" height="{H}" fill="{NAVY_TOP}"/>'
            f'<rect y="{H*split:.0f}" width="{W}" height="{H*(1-split):.0f}" fill="{NAVY_MID}"/>'
            f'<rect y="{H*0.80:.0f}" width="{W}" height="{H*0.20:.0f}" fill="{NAVY_LOW}"/>'
            f'<g fill="{DIM}" fill-opacity=".10">{"".join(dots)}</g>')


def art(W, H, uid):
    """主图（第 586 号）：左边一面整齐的格子墙（交出去的秩序），一条金线竖着分开两半；
    右边一小块地，一株苗正在长，上方散着几点金色（没处放的混沌）。下方是一道金色地平线。全部纯色，不用渐变。"""
    s = W / 1700
    o = []
    top, ground = H * 0.40, H * 0.78
    o.append(f'<rect y="{top:.0f}" width="{W}" height="{H-top:.0f}" fill="{NAVY_MID}"/>')
    split = W * 0.50
    # 左：格子墙（秩序）——四行六列，奶白方块整齐排列
    cols, rows = 6, 5
    gx0, gx1 = W * 0.08, split - 70 * s
    gy0, gy1 = top + 50 * s, ground - 40 * s
    cw, rh = (gx1 - gx0) / cols, (gy1 - gy0) / rows
    for r in range(rows):
        for c in range(cols):
            x, y = gx0 + c * cw, gy0 + r * rh
            o.append(f'<rect x="{x+8*s:.0f}" y="{y+8*s:.0f}" width="{cw-16*s:.0f}" height="{rh-16*s:.0f}" rx="{4*s:.0f}" fill="{CREAM}" fill-opacity="{.9 if (r+c)%5 else .55}"/>')
    # 中：金线
    o.append(f'<rect x="{split-3*s:.0f}" y="{top+20*s:.0f}" width="{6*s:.0f}" height="{ground-top-20*s:.0f}" fill="{GOLD}"/>')
    # 右：散着的金点（混沌）
    import random
    rnd = random.Random(586)
    for _ in range(26):
        x = split + 90 * s + rnd.random() * (W * 0.92 - split - 90 * s)
        y = top + 40 * s + rnd.random() * (ground - top - 330 * s)
        r = (4 + rnd.random() * 9) * s
        o.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.0f}" fill="{GOLD2}" fill-opacity="{.45 + rnd.random()*.5:.2f}"/>')
    # 右：一小块地与一株苗（介生）
    px = split + (W * 0.92 - split) * 0.52
    o.append(f'<path d="M{px-260*s:.0f} {ground:.0f} Q{px:.0f} {ground-90*s:.0f} {px+260*s:.0f} {ground:.0f} Z" fill="{GOLD}" fill-opacity=".55"/>')
    stem_top = ground - 300 * s
    o.append(f'<path d="M{px:.0f} {ground-50*s:.0f} C{px-10*s:.0f} {ground-140*s:.0f} {px+12*s:.0f} {ground-220*s:.0f} {px:.0f} {stem_top:.0f}" fill="none" stroke="{CYAN}" stroke-width="{9*s:.1f}" stroke-linecap="round"/>')
    o.append(f'<path d="M{px:.0f} {ground-150*s:.0f} C{px-60*s:.0f} {ground-170*s:.0f} {px-120*s:.0f} {ground-230*s:.0f} {px-140*s:.0f} {ground-280*s:.0f} C{px-80*s:.0f} {ground-270*s:.0f} {px-20*s:.0f} {ground-220*s:.0f} {px:.0f} {ground-150*s:.0f} Z" fill="{CYAN}"/>')
    o.append(f'<path d="M{px:.0f} {ground-215*s:.0f} C{px+55*s:.0f} {ground-235*s:.0f} {px+110*s:.0f} {ground-290*s:.0f} {px+125*s:.0f} {ground-340*s:.0f} C{px+70*s:.0f} {ground-330*s:.0f} {px+15*s:.0f} {ground-280*s:.0f} {px:.0f} {ground-215*s:.0f} Z" fill="{CYAN}" fill-opacity=".85"/>')
    o.append(f'<circle cx="{px:.0f}" cy="{stem_top-8*s:.0f}" r="{11*s:.0f}" fill="{GOLD2}"/>')
    # 地平线
    o.append(f'<rect y="{ground:.0f}" width="{W}" height="{20*s:.0f}" fill="{GOLD}"/>')
    o.append(f'<rect y="{ground+20*s:.0f}" width="{W}" height="{H-ground-20*s:.0f}" fill="{NAVY_LOW}"/>')
    return ''.join(o)


def barcode(x, y, s):
    if not re.search(r'\d{13}', re.sub(r'\D', '', ISBN) or ''):
        return '', 0
    d, bits = ean13_bits(ISBN)
    mw = 3.3 * s  # 模块宽
    h = 190 * s
    rects = []
    for i, b in enumerate(bits):
        if b == '1':
            guard = i < 3 or 45 <= i < 50 or i >= 92
            rects.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#111"/>' % (x + 22 * s + i * mw, y + 40 * s, mw + .2, h + (18 * s if guard else 0)))
    bw = 95 * mw + 44 * s
    txt = (f'<text x="{x + bw/2:.0f}" y="{y + 30*s:.0f}" font-size="{19*s:.0f}" text-anchor="middle" font-family="Noto Sans CJK SC" fill="#111">ISBN {ISBN}</text>'
           f'<text x="{x + 8*s:.0f}" y="{y + 40*s + h + 36*s:.0f}" font-size="{26*s:.0f}" font-family="Noto Serif CJK SC" fill="#111">{d[0]}</text>'
           f'<text x="{x + 22*s + 3*mw + 21*mw:.0f}" y="{y + 40*s + h + 36*s:.0f}" font-size="{26*s:.0f}" text-anchor="middle" letter-spacing="{9*s:.0f}" font-family="Noto Serif CJK SC" fill="#111">{d[1:7]}</text>'
           f'<text x="{x + 22*s + 50*mw + 21*mw:.0f}" y="{y + 40*s + h + 36*s:.0f}" font-size="{26*s:.0f}" text-anchor="middle" letter-spacing="{9*s:.0f}" font-family="Noto Serif CJK SC" fill="#111">{d[7:]}</text>')
    return (f'<rect x="{x:.0f}" y="{y:.0f}" width="{bw:.0f}" height="{h + 110*s:.0f}" fill="#fff"/>' + ''.join(rects) + txt), bw


def fontface(F):
    return ""


def front(Wmm, Hmm, F):
    W, H = Wmm * 10, Hmm * 10
    s = Wmm / 170
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{Wmm}mm" height="{Hmm}mm">{background(W, H, "f")}{art(W, H, "f")}</svg>'
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{fontface(F)}
@page{{size:{Wmm}mm {Hmm}mm;margin:0}} body{{margin:0}}
.pg{{position:relative;width:{Wmm}mm;height:{Hmm}mm;overflow:hidden}}
.pg svg{{position:absolute;left:0;top:0}}
.t{{position:absolute;left:{17*s:.1f}mm;top:{22*s:.1f}mm;color:{CREAM}}}
.pre{{font:400 {11.5*s:.1f}pt 'Noto Serif CJK SC';letter-spacing:.32em;color:{CREAM};opacity:.92}}
.big{{font:700 {45*s:.1f}pt/1.2 'Noto Serif CJK SC';letter-spacing:.1em;color:#F7F1E3;margin:{2*s:.1f}mm 0 {3*s:.1f}mm {-1*s:.1f}mm}}
.big2{{font-size:{34*s:.1f}pt;line-height:1.3;letter-spacing:.04em}}
.sub{{font:400 {10.6*s:.1f}pt/1.75 'Noto Serif CJK SC';color:{GOLD2};letter-spacing:.04em}}
.rule{{width:{16*s:.1f}mm;border-top:.9pt solid {GOLD};margin-top:{5*s:.1f}mm}}
.b{{position:absolute;left:{17*s:.1f}mm;bottom:{17*s:.1f}mm}}
.au{{font:400 {12.5*s:.1f}pt 'Noto Serif CJK SC';color:{CREAM};letter-spacing:.28em}}
.ph{{font:700 {8.4*s:.1f}pt 'Noto Sans CJK SC';color:{GOLD2};letter-spacing:.3em;margin-top:{6*s:.1f}mm}}
.pe{{font:400 {6.6*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.08em;margin-top:{.8*s:.1f}mm}}
.no{{position:absolute;right:{15*s:.1f}mm;top:{16*s:.1f}mm;font:400 {6.6*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.2em;text-align:right}}
</style></head><body><div class="pg">{svg}
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 586 号</div>
<div class="t"><div class="big" style="font-size:{38*s:.1f}pt;letter-spacing:.06em">你没交给企业的<br><span style="color:{GOLD2}">那一半</span></div>
<div class="sub">人和企业怎样共生，<br>离开时心怀感谢，对新事业充满希望</div><div class="rule"></div></div>
<div class="b"><div class="au">贝芳　著</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div>
</div></div></body></html>"""


def back(Wmm, Hmm, F):
    W, H = Wmm * 10, Hmm * 10
    s = Wmm / 170
    # 右上小徽：环＋三条边
    ex, ey, er = W * 0.84, H * 0.085, 70 * s
    spokes = ''.join(f'<line x1="{ex:.0f}" y1="{ey:.0f}" x2="{ex+44*s*math.cos(math.radians(t)):.0f}" y2="{ey+44*s*math.sin(math.radians(t)):.0f}" stroke="{GOLD}" stroke-width="{3*s:.1f}" stroke-linecap="round"/>'
                     f'<circle cx="{ex+44*s*math.cos(math.radians(t)):.0f}" cy="{ey+44*s*math.sin(math.radians(t)):.0f}" r="{7*s:.1f}" fill="{CREAM}"/>' for t in (-90, 30, 150))
    emb = f"""<circle cx="{ex:.0f}" cy="{ey:.0f}" r="{er:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".6" stroke-width="{2*s:.1f}"/>
<circle cx="{ex:.0f}" cy="{ey:.0f}" r="{er*1.18:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".22" stroke-width="{1.2*s:.1f}"/>{spokes}
<circle cx="{ex:.0f}" cy="{ey:.0f}" r="{12*s:.1f}" fill="{GOLD}"/>"""
    # 底部淡水纹
    waves = []
    for k, (yy, op, amp) in enumerate([(.955, .18, 8), (.972, .10, 6)]):
        y0 = H * yy; d = 'M0 %.0f' % y0
        for i in range(9):
            d += ' Q%.0f %.0f %.0f %.0f' % (W * (i + .5) / 9, y0 + (amp if i % 2 else -amp) * s * 2, W * (i + 1) / 9, y0)
        waves.append('<path d="%s" fill="none" stroke="%s" stroke-opacity="%.2f" stroke-width="%.1f"/>' % (d, CYAN, op, 1.6 * s))
    bc, bw = barcode(W - 170 * s - 380 * s, H - 150 * s - 300 * s, s)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{Wmm}mm" height="{Hmm}mm">'
           f'{background(W, H, "b", split=0.66)}{emb}{"".join(waves)}{bc}</svg>')
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{fontface(F)}
@page{{size:{Wmm}mm {Hmm}mm;margin:0}} body{{margin:0}}
.pg{{position:relative;width:{Wmm}mm;height:{Hmm}mm;overflow:hidden}}
.pg svg{{position:absolute;left:0;top:0}}
.c{{position:absolute;left:{17*s:.1f}mm;top:{24*s:.1f}mm;width:{128*s:.1f}mm;color:{CREAM}}}
.lab{{font:700 {7.4*s:.1f}pt 'Noto Sans CJK SC';color:{GOLD2};letter-spacing:.5em}}
.q{{font:700 {15.5*s:.1f}pt/1.75 'Noto Serif CJK SC';color:#F7F1E3;margin:{4*s:.1f}mm 0 {2*s:.1f}mm;letter-spacing:.04em}}
.by{{font:400 {8.2*s:.1f}pt 'Noto Serif CJK SC';color:{DIM}}}
.rule{{width:{14*s:.1f}mm;border-top:.9pt solid {GOLD};margin:{7*s:.1f}mm 0 {6*s:.1f}mm}}
.bl p{{font:400 {8.8*s:.1f}pt/1.9 'Noto Serif CJK SC';color:{CREAM};opacity:.9;margin:0 0 {2.6*s:.1f}mm;text-align:left}}
.gold{{font:700 {10.5*s:.1f}pt 'Noto Serif CJK SC';color:{GOLD2};margin-top:{6*s:.1f}mm;letter-spacing:.06em}}
.f{{position:absolute;left:{17*s:.1f}mm;bottom:{17*s:.1f}mm;font:400 {7.2*s:.1f}pt/1.85 'Noto Sans CJK SC';color:{DIM}}}
.f b{{color:{CREAM};font-weight:700;letter-spacing:.12em}}
</style></head><body><div class="pg">{svg}
<div class="c"><div class="lab">全 书 定 音</div>
<div class="q" style="font-size:{14.2*s:.1f}pt">你交给企业的是秩序，<br>没交出去的才是你自己的。</div><div class="rule"></div>
<div class="bl"><p>很多人决定离开企业之前，做的第一件事是整理经验。这本书说，这一步多半会落空：整理出来的，大多是企业的秩序——那些可以被指挥、被交接、被替换的做法。通用的秩序带得走，却人人都有，只能出租，长不成自己的事业。</p>
<p>没交出去的那一半，是企业没要的判断、没处放的想法，书里叫它混沌，它是原料；给混沌搭一个接得住它的地方，让它慢慢成形，书里叫它介生，事业从这里长出来。企业收下秩序，同时给员工的混沌与介生留一块地，这是共生；离开时把秩序交接干净，感谢就有了出处；没交出去的那一半随人走，并且早已在长，希望也就有了出处。</p>
<p>作者在房地产企业做了二十多年人事。这是一部研究性专著初版：书中涉及他人的场景，除作者亲历的几件事，都是标明的设想，写作与审校借助 AI 协作，没有经过独立学术评审。</p>
<div class="gold">离开那天之前，先问一句：没交出去的那一半，此刻放在哪里？</div></div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 586 号 · 五编十四章 · 约 {WAN} 万字<br>ISBN 979-8-90690-610-6 · 定价 US$20.00</div>
</div></body></html>"""


def main():
    import weasyprint
    import pymupdf
    ap = argparse.ArgumentParser()
    ap.add_argument('--fonts', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    F = a.fonts.resolve()
    for tag, (w, h) in {'print': (170, 240), 'reader': (190, 250)}.items():
        weasyprint.HTML(string=front(w, h, F)).write_pdf(str(a.out / f'cover-{tag}.pdf'))
        weasyprint.HTML(string=back(w, h, F)).write_pdf(str(a.out / f'back-{tag}.pdf'))
    for src, dst in [('cover-print.pdf', 'cover.jpg'), ('back-print.pdf', 'backcover.jpg')]:
        pg = pymupdf.open(str(a.out / src))[0]
        zoom = 1004 / pg.rect.width
        pix = pg.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
        pix.save(str(a.out / dst), jpg_quality=90)
    print('covers ok')


if __name__ == '__main__':
    main()
