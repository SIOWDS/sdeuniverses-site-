#!/usr/bin/env python3
"""《真的能摸着石头过河吗？》封面封底（照第 220、302 号：藏青渐变、细点阵、金环、扁平插画；封底白字判词、金句、条码）。
主图：一条河的剖面。左边几块奶白的石头，一个人站在最后一块上，一只脚探向前方；前方河底没有石头，只有一圈圈搅动的漩涡，
米粒在里面化开；再往前，是一块金色虚线的石头，还没有垫出来。
"""
import argparse
import math
import os
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0B1830', '#1B3158', '#142746'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#58BDCA', '#EFE8D6', '#9FB0C8'
ISBN = '979-8-90690-977-0'
NO = '第 487 号'
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


def stone(cx, base, w, h, fill=CREAM, op=1):
    """一块平顶的石头。"""
    return (f'<path d="M{cx - w/2:.0f} {base:.0f} C{cx - w/2:.0f} {base - h*.62:.0f} {cx - w*.34:.0f} {base - h:.0f} {cx - w*.10:.0f} {base - h:.0f} '
            f'L{cx + w*.16:.0f} {base - h:.0f} C{cx + w*.38:.0f} {base - h:.0f} {cx + w/2:.0f} {base - h*.56:.0f} {cx + w/2:.0f} {base:.0f} Z" '
            f'fill="{fill}" fill-opacity="{op}"/>')


def art(W, H, uid):
    s = W / 1700
    cx, cy, r = W * 0.625, H * 0.578, 590 * s
    out = [f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r*1.28:.0f}" fill="url(#halo{uid})"/>',
           f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".62" stroke-width="{4.5*s:.1f}"/>',
           f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r*1.035:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".20" stroke-width="{2*s:.1f}"/>',
           f'<defs><clipPath id="cl{uid}"><circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r - 3*s:.0f}"/></clipPath></defs>']
    wl = cy - r * 0.06  # 水面
    bed = cy + r * 0.72  # 河床
    g = [f'<g clip-path="url(#cl{uid})">']
    # 水体
    d = f'M{cx - r*1.1:.0f} {wl:.0f}'
    for i in range(10):
        x0 = cx - r * 1.1 + i * r * .22
        d += f' q{r*.055:.0f} {(-10 if i % 2 else 10)*s:.0f} {r*.11:.0f} 0 t{r*.11:.0f} 0'
    d += f' L{cx + r*1.1:.0f} {cy + r*1.1:.0f} L{cx - r*1.1:.0f} {cy + r*1.1:.0f} Z'
    g.append(f'<path d="{d}" fill="url(#water{uid})"/>')
    # 几道水纹
    for k, (yy, x0, x1, op) in enumerate([(.10, -.95, -.15, .28), (.17, .42, .95, .24), (.28, -.92, -.40, .18)]):
        yv = cy + r * yy
        g.append(f'<path d="M{cx + r*x0:.0f} {yv:.0f} q{r*.09:.0f} {-9*s:.0f} {r*.18:.0f} 0 t{r*.18:.0f} 0 t{r*.18:.0f} 0" fill="none" stroke="{CREAM}" stroke-opacity="{op}" stroke-width="{3*s:.1f}" stroke-linecap="round"/>')
    # 河床
    g.append(f'<path d="M{cx - r*1.1:.0f} {bed - r*.04:.0f} C{cx - r*.6:.0f} {bed + r*.02:.0f} {cx - r*.1:.0f} {bed + r*.06:.0f} {cx + r*.3:.0f} {bed + r*.03:.0f} S{cx + r*.9:.0f} {bed - r*.03:.0f} {cx + r*1.1:.0f} {bed - r*.04:.0f} L{cx + r*1.1:.0f} {cy + r*1.1:.0f} L{cx - r*1.1:.0f} {cy + r*1.1:.0f} Z" fill="#0C1B33" fill-opacity=".95"/>')
    # 三块实的石头，由低到高、出水
    tops = [(-.74, .40, .50), (-.46, .38, .68), (-.17, .36, .84)]
    for dx, w, h in tops:
        x = cx + r * dx
        g.append(stone(x, bed + r * .04, r * w, r * h))
        # 石面暗部
        g.append(f'<path d="M{x - r*w*.46:.0f} {bed + r*.04:.0f} C{x - r*w*.4:.0f} {bed - r*h*.26:.0f} {x + r*w*.1:.0f} {bed - r*h*.34:.0f} {x + r*w*.5:.0f} {bed - r*h*.18:.0f} L{x + r*w*.5:.0f} {bed + r*.04:.0f} Z" fill="#CDBF9F" fill-opacity=".55"/>')
    # 漩涡：河底没有石头，米粒化开
    vx, vy = cx + r * .27, bed - r * .23
    for k, (rr, op) in enumerate([(.26, .55), (.19, .70), (.12, .85), (.06, 1)]):
        a0 = k * 1.1
        pts = []
        for t in range(0, 66):
            th = a0 + t / 65 * math.pi * 1.55
            pts.append((vx + r * rr * math.cos(th), vy + r * rr * .46 * math.sin(th)))
        g.append('<path d="M' + ' L'.join('%.1f %.1f' % p for p in pts) + f'" fill="none" stroke="{GOLD2}" stroke-opacity="{op}" stroke-width="{4.5*s:.1f}" stroke-linecap="round"/>')
    for k, (dx, dy, rad, op) in enumerate([(-.30, -.20, 6.5, .9), (-.17, -.27, 5.5, .75), (-.02, -.31, 4.5, .6), (.15, -.26, 4, .45), (.29, -.17, 3, .35)]):
        g.append(f'<ellipse cx="{vx + r*dx:.0f}" cy="{vy + r*dy:.0f}" rx="{rad*s*2:.1f}" ry="{rad*s*1.2:.1f}" fill="{CREAM}" fill-opacity="{op}"/>')
    # 虚线的石头：还没垫出来
    sx = cx + r * .73
    w, h = r * .36, r * .56
    base = bed + r * .01
    g.append(f'<path d="M{sx - w/2:.0f} {base:.0f} C{sx - w/2:.0f} {base - h*.62:.0f} {sx - w*.34:.0f} {base - h:.0f} {sx - w*.10:.0f} {base - h:.0f} L{sx + w*.16:.0f} {base - h:.0f} C{sx + w*.38:.0f} {base - h:.0f} {sx + w/2:.0f} {base - h*.56:.0f} {sx + w/2:.0f} {base:.0f}" fill="none" stroke="{GOLD2}" stroke-width="{4.5*s:.1f}" stroke-dasharray="{14*s:.0f} {11*s:.0f}" stroke-linecap="round"/>')
    g.append('</g>')
    out += g
    # 水面亮线（压在石头之后、人之前）
    # 人：站在第三块石头上，一只脚探出去
    top = bed + r * .04 - r * .84
    fx = cx + r * (-.17)
    hip = (fx + r * .01, top - r * .25)
    sh = (fx + r * .05, top - r * .50)
    head = (fx + r * .075, top - r * .615)
    st = 17 * s
    p = [f'<g stroke="{CREAM}" stroke-width="{st:.1f}" stroke-linecap="round" stroke-linejoin="round" fill="none">',
         f'<path d="M{hip[0]:.0f} {hip[1]:.0f} L{sh[0]:.0f} {sh[1]:.0f}"/>',
         f'<path d="M{hip[0]:.0f} {hip[1]:.0f} L{fx - r*.015:.0f} {top - r*.012:.0f}"/>',
         f'<path d="M{hip[0]:.0f} {hip[1]:.0f} L{fx + r*.135:.0f} {top - r*.12:.0f} L{fx + r*.245:.0f} {top + r*.055:.0f}"/>',
         f'<path d="M{sh[0] - r*.005:.0f} {sh[1] + r*.035:.0f} L{fx - r*.10:.0f} {top - r*.36:.0f}"/>',
         f'<path d="M{sh[0] + r*.005:.0f} {sh[1] + r*.035:.0f} L{fx + r*.20:.0f} {top - r*.43:.0f}"/></g>',
         f'<circle cx="{head[0]:.0f}" cy="{head[1]:.0f}" r="{r*.052:.0f}" fill="{GOLD2}"/>']
    out += p
    # 探脚处的一圈水波
    fxx, fy = fx + r * .245, wl
    out.append(f'<ellipse cx="{fxx:.0f}" cy="{fy + r*.01:.0f}" rx="{r*.085:.0f}" ry="{r*.016:.0f}" fill="none" stroke="{CYAN}" stroke-opacity=".85" stroke-width="{3*s:.1f}"/>')
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
.pre{{font:700 {26*s:.1f}pt/1.2 'Noto Serif CJK SC';color:#F3ECD9;letter-spacing:.04em}}
.big{{font:900 {38.5*s:.1f}pt/1.25 'Noto Serif CJK SC';letter-spacing:.015em;color:#F3ECD9;margin:{1.5*s:.1f}mm 0 {7*s:.1f}mm {-.5*s:.1f}mm;white-space:nowrap}}
.sub{{font:500 {13*s:.1f}pt/1.6 'Noto Sans CJK SC';color:{GOLD2};letter-spacing:.03em}}
.b{{position:absolute;left:{11.5*s:.1f}mm;bottom:{10*s:.1f}mm}}
.rl{{width:{47*s:.1f}mm;border-top:.6pt solid {DIM};opacity:.8;margin-bottom:{4.5*s:.1f}mm}}
.au{{font:500 {16*s:.1f}pt 'Noto Sans CJK SC';color:{CREAM};letter-spacing:.14em}}
.ph{{font:500 {11.5*s:.1f}pt 'Noto Sans CJK SC';color:{CREAM};letter-spacing:.12em;margin-top:{7.5*s:.1f}mm}}
.pe{{font:400 {7.8*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.14em;margin-top:{.9*s:.1f}mm}}
</style></head><body><div class="pg">{svg}
<div class="t"><div class="pre">真的能</div><div class="big">摸着石头过河吗？</div>
<div class="sub">马克思主义哲学复杂性发生学</div></div>
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
<div class="c"><div class="q">马哲的复杂，<br>不是思想丰富，<br>也不是文本多义，<br>而是化粒之后，<br>各家外补粒子的残局。</div>
<div class="bl"><p>人人都说摸着石头过河，很少有人先问：</p><p>河里有石头吗？书上为什么没有路？</p><p>这本书从恩格斯反对什么问起，一家一家看</p><p>十几种马克思主义怎样从粥里捞米、争一个名额；</p><p>再回到河边，分开能摸的河、要垫的河、</p><p>和退不回来的河，最后量一量作者自己这一派。</p><p>它是一个假说，并写明了自己的五条死法。</p></div>
<div class="gold">要的不是一锅粥，是一桌菜。　　——本书</div></div>
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
