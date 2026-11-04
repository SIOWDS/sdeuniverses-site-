#!/usr/bin/env python3
"""《为何会想生孩子？》封面封底（照第 220、302 号：藏青渐变、细点阵、金环、扁平插画；封底白字判词、金句、条码）。
主图：短纤维散着，往右捻成三股绳，三股是三条流。
"""
import argparse
import math
import os
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0B1830', '#1B3158', '#142746'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#58BDCA', '#EFE8D6', '#9FB0C8'
ISBN = '979-8-90690-980-0'
NO = '第 515 号'
PRICE = 'US$20.00'

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


def background(W, H, uid):
    dots = []
    step = 44
    for yy in range(22, H, step):
        for xx in range(22 + (yy // step % 2) * 22, W, step):
            dots.append('<circle cx="%d" cy="%d" r="1.7"/>' % (xx, yy))
    return f"""
<defs>
 <linearGradient id="bg{uid}" x1="0" y1="0" x2="0.2" y2="1">
  <stop offset="0" stop-color="{NAVY_TOP}"/><stop offset=".58" stop-color="{NAVY_MID}"/><stop offset="1" stop-color="{NAVY_LOW}"/></linearGradient>
 <radialGradient id="halo{uid}" cx=".5" cy=".5" r=".5">
  <stop offset="0" stop-color="{GOLD2}" stop-opacity=".16"/><stop offset=".62" stop-color="{GOLD}" stop-opacity=".07"/>
  <stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></radialGradient>
 <linearGradient id="water{uid}" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#2A6C88" stop-opacity=".62"/><stop offset="1" stop-color="#10284A" stop-opacity=".92"/></linearGradient>
</defs>
<rect width="{W}" height="{H}" fill="url(#bg{uid})"/>
<g fill="{DIM}" fill-opacity=".10">{''.join(dots)}</g>"""


def art(W, H, uid):
    """一股绳：左边短纤维散着，往右捻成三股；三股是三条流，一根奶白、一根金、一根青，彼此压着走。"""
    import random
    s = W / 1700
    cx, cy, r = W * 0.625, H * 0.578, 590 * s
    out = [f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r*1.28:.0f}" fill="url(#halo{uid})"/>',
           f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".62" stroke-width="{4.5*s:.1f}"/>',
           f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r*1.035:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".20" stroke-width="{2*s:.1f}"/>',
           f'<defs><clipPath id="cl{uid}"><circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r - 3*s:.0f}"/></clipPath></defs>']
    g = [f'<g clip-path="url(#cl{uid})">']
    rnd = random.Random(500)
    cols = [CREAM, GOLD2, CYAN]
    x1 = cx + r * 1.02
    ropeL = cx - r * .42

    def centre(u, k):
        x = ropeL + (x1 - ropeL) * u
        amp = r * (.15 - .05 * u)
        ph = 2 * math.pi * (2.7 * u) + k * 2 * math.pi / 3
        return x, cy + amp * math.sin(ph) + r * .02, math.cos(ph)
    for k in range(3):
        for i in range(34):
            sx = cx - r * 1.0 + rnd.random() * r * .62
            spread = (ropeL + r * .12 - sx) / (r * .72)
            yy = cy + (k - 1) * r * .11 * spread * 1.6 + (rnd.random() - .5) * r * .46 * spread
            ln = r * (.14 + rnd.random() * .15)
            ey = yy + (cy + (k - 1) * r * .08 - yy) * .40
            cx1 = sx + ln * .5
            cy1 = yy + (rnd.random() - .5) * r * .07
            g.append(f'<path d="M{sx:.0f} {yy:.0f} Q{cx1:.0f} {cy1:.0f} {sx + ln:.0f} {ey:.0f}" fill="none" stroke="{cols[k]}" stroke-opacity="{.45 + rnd.random()*.45:.2f}" stroke-width="{(3.2 + rnd.random()*2.6)*s:.1f}" stroke-linecap="round"/>')
    segs = []
    N = 170
    for k in range(3):
        for i in range(N):
            a_ = centre(i / N, k); b_ = centre((i + 1) / N, k)
            segs.append(((a_[2] + b_[2]) / 2, k, a_, b_))
    segs.sort(key=lambda z: z[0])
    wd = 40 * s
    for d, k, a_, b_ in segs:
        shade = .62 + .38 * (d + 1) / 2
        g.append(f'<path d="M{a_[0]:.1f} {a_[1]:.1f} L{b_[0]:.1f} {b_[1]:.1f}" stroke="#0B1830" stroke-width="{wd + 5*s:.1f}" stroke-linecap="round" fill="none" stroke-opacity="{.38 if d > 0 else 0}"/>')
        g.append(f'<path d="M{a_[0]:.1f} {a_[1]:.1f} L{b_[0]:.1f} {b_[1]:.1f}" stroke="{cols[k]}" stroke-width="{wd:.1f}" stroke-linecap="round" fill="none" stroke-opacity="{shade:.2f}"/>')
    for i in range(190):
        u = rnd.random(); k = rnd.randrange(3)
        x, y, d = centre(u, k)
        if d < .15:
            continue
        ln = r * (.03 + rnd.random() * .05)
        yy = y + (rnd.random() - .5) * wd * .7
        g.append(f'<path d="M{x:.0f} {yy:.0f} l{ln:.0f} {ln * (.35 if rnd.random() < .5 else -.35):.0f}" stroke="#0B1830" stroke-opacity=".22" stroke-width="{1.8*s:.1f}" stroke-linecap="round"/>')
    g.append('</g>')
    out += g
    return ''.join(out)


def barcode(x, y, s):
    d, bits = ean13_bits(ISBN)
    mw = 4.0 * s
    h = 230 * s
    rects = []
    for i, b in enumerate(bits):
        if b == '1':
            rects.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#111"/>' % (x + 28 * s + i * mw, y + 46 * s, mw + .2, h))
    bw = 95 * mw + 56 * s
    bh = h + 110 * s
    txt = (f'<text x="{x + bw/2:.0f}" y="{y + 33*s:.0f}" font-size="{23*s:.0f}" text-anchor="middle" font-family="Noto Sans CJK SC" fill="#111">ISBN {ISBN}</text>'
           f'<text x="{x + bw/2:.0f}" y="{y + 46*s + h + 42*s:.0f}" font-size="{28*s:.0f}" text-anchor="middle" letter-spacing="{4*s:.0f}" font-family="Noto Sans CJK SC" fill="#111">{d}</text>')
    return (f'<rect x="{x:.0f}" y="{y:.0f}" width="{bw:.0f}" height="{bh:.0f}" fill="#fff"/>' + ''.join(rects) + txt), bw, bh


def front(Wmm, Hmm):
    W, H = Wmm * 10, Hmm * 10
    s = Wmm / 170
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{Wmm}mm" height="{Hmm}mm">{background(W, H, "f")}{art(W, H, "f")}</svg>'
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page{{size:{Wmm}mm {Hmm}mm;margin:0}} body{{margin:0}}
.pg{{position:relative;width:{Wmm}mm;height:{Hmm}mm;overflow:hidden}}
.pg svg{{position:absolute;left:0;top:0}}
.t{{position:absolute;left:{11.5*s:.1f}mm;top:{24*s:.1f}mm;color:{CREAM}}}
.pre{{font:700 {30*s:.1f}pt/1.2 'Noto Serif CJK SC';color:#F3ECD9;letter-spacing:.04em}}
.big{{font:900 {46*s:.1f}pt/1.25 'Noto Serif CJK SC';letter-spacing:.015em;color:#F3ECD9;margin:{1.5*s:.1f}mm 0 {7*s:.1f}mm {-.5*s:.1f}mm;white-space:nowrap}}
.sub{{font:500 {13*s:.1f}pt/1.6 'Noto Sans CJK SC';color:{GOLD2};letter-spacing:.03em}}
.b{{position:absolute;left:{11.5*s:.1f}mm;bottom:{10*s:.1f}mm}}
.rl{{width:{47*s:.1f}mm;border-top:.6pt solid {DIM};opacity:.8;margin-bottom:{4.5*s:.1f}mm}}
.au{{font:500 {16*s:.1f}pt 'Noto Sans CJK SC';color:{CREAM};letter-spacing:.14em}}
.ph{{font:500 {11.5*s:.1f}pt 'Noto Sans CJK SC';color:{CREAM};letter-spacing:.12em;margin-top:{7.5*s:.1f}mm}}
.pe{{font:400 {7.8*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.14em;margin-top:{.9*s:.1f}mm}}
</style></head><body><div class="pg">{svg}
<div class="t"><div class="pre">为何会想</div><div class="big">生孩子？</div></div>
<div class="b"><div class="rl"></div><div class="au">王德生　著</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div>
</div></body></html>"""


def back(Wmm, Hmm):
    W, H = Wmm * 10, Hmm * 10
    s = Wmm / 170
    rx, ry, rr = W * .80, H * .20, 480 * s
    ring = (f'<circle cx="{rx:.0f}" cy="{ry:.0f}" r="{rr:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".62" stroke-width="{4.5*s:.1f}"/>'
            f'<circle cx="{rx:.0f}" cy="{ry:.0f}" r="{rr*1.04:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".20" stroke-width="{2*s:.1f}"/>')
    bx = W - 110 * s - 436 * s
    bc, bw, bh = barcode(bx, H - 74 * s - 340 * s, s)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{Wmm}mm" height="{Hmm}mm">'
           f'{background(W, H, "b")}{ring}{bc}</svg>')
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page{{size:{Wmm}mm {Hmm}mm;margin:0}} body{{margin:0}}
.pg{{position:relative;width:{Wmm}mm;height:{Hmm}mm;overflow:hidden}}
.pg svg{{position:absolute;left:0;top:0}}
.c{{position:absolute;left:{13.3*s:.1f}mm;top:{21*s:.1f}mm;width:{118*s:.1f}mm;color:{CREAM}}}
.q{{font:700 {15*s:.1f}pt/1.82 'Noto Sans CJK SC';color:#FBF8F0;letter-spacing:.02em}}
.bl{{margin-top:{9*s:.1f}mm}}
.bl p{{font:400 {10.8*s:.1f}pt/1.95 'Noto Sans CJK SC';color:{CREAM};opacity:.93;margin:0;text-align:left}}
.gold{{font:700 {11*s:.1f}pt/1.8 'Noto Sans CJK SC';color:{GOLD2};margin-top:{9*s:.1f}mm;letter-spacing:.02em}}
.f{{position:absolute;left:{13.3*s:.1f}mm;bottom:{9*s:.1f}mm;font:400 {9*s:.1f}pt/2.05 'Noto Sans CJK SC';color:{CREAM};opacity:.9}}
.rl{{width:{68*s:.1f}mm;border-top:.6pt solid {DIM};margin-bottom:{3*s:.1f}mm}}
</style></head><body><div class="pg">{svg}
<div class="c"><div class="q">人口不是人数。<br>想生不想生，<br>是创造、自由、幸福三条流，<br>落在理念、现实、自我<br>三界上的权重组合。</div>
<div class="bl"><p>人口的书多半在数人，这本书问那一愣：</p><p>你想要几个孩子？这个数字是怎么来的？</p><p>从马尔萨斯只算了一格讲起，走过三条流和三界，</p><p>看这份想漏在哪一次转界、停在哪一步；</p><p>再走一遍中国、伊斯兰世界、西方、非洲、东亚。</p><p>它不劝生，也不劝不生。四条律都是候选，</p><p>每条都写了怎样算输，对它不利的材料都留在书里。</p></div>
<div class="gold">绳子变细，不等于断了。　　——本书</div></div>
<div class="f"><div class="rl"></div>德麦国际出版社 · Demai International Press<br>德麦国际专著{NO}<br>定价：{PRICE}</div>
</div></body></html>"""


def main():
    import pymupdf
    import weasyprint
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    for tag, (w, h) in {'print': (170, 240), 'reader': (190, 250)}.items():
        weasyprint.HTML(string=front(w, h)).write_pdf(str(a.out / f'cover-{tag}.pdf'))
        weasyprint.HTML(string=back(w, h)).write_pdf(str(a.out / f'back-{tag}.pdf'))
    for src, dst in [('cover-print.pdf', 'cover.jpg'), ('back-print.pdf', 'backcover.jpg')]:
        pg = pymupdf.open(str(a.out / src))[0]
        pix = pg.get_pixmap(matrix=pymupdf.Matrix(1004 / pg.rect.width, 1004 / pg.rect.width))
        pix.save(str(a.out / dst), jpg_quality=90)
    print('covers ok')


if __name__ == '__main__':
    main()
