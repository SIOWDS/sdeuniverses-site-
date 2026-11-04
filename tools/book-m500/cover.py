#!/usr/bin/env python3
"""《AI是加速你的落地》封面封底（照第 220、302 号：藏青渐变、细点阵、金环、扁平插画；封底白字判词）。
主图：人站在地上，头旁一颗青色的 AI，连成一个思维体；金弧落到地上生出新苗，青色虚线把现实的回答写回去，走完一轮。
"""
import argparse
import math
import os
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0B1830', '#1B3158', '#142746'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#58BDCA', '#EFE8D6', '#9FB0C8'
ISBN = '979-8-90690-978-7'
NO = '第 500 号'
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
  <stop offset="0" stop-color="#8A6E3A" stop-opacity=".78"/><stop offset="1" stop-color="#3A2E1C" stop-opacity=".95"/></linearGradient>
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
    gy = cy + r * .42  # 地面
    g = [f'<g clip-path="url(#cl{uid})">']
    # 地：一层深土，几道田垄
    g.append(f'<path d="M{cx-r*1.1:.0f} {gy:.0f} C{cx-r*.5:.0f} {gy-r*.035:.0f} {cx+r*.4:.0f} {gy+r*.035:.0f} {cx+r*1.1:.0f} {gy-r*.01:.0f} L{cx+r*1.1:.0f} {cy+r*1.1:.0f} L{cx-r*1.1:.0f} {cy+r*1.1:.0f} Z" fill="url(#water{uid})"/>')
    g.append(f'<path d="M{cx-r*1.1:.0f} {gy:.0f} C{cx-r*.5:.0f} {gy-r*.035:.0f} {cx+r*.4:.0f} {gy+r*.035:.0f} {cx+r*1.1:.0f} {gy-r*.01:.0f}" fill="none" stroke="{GOLD2}" stroke-width="{5*s:.1f}"/>')
    for k, (yy, op) in enumerate([(.10, .34), (.20, .26), (.31, .19), (.43, .13)]):
        g.append(f'<path d="M{cx-r*1.0:.0f} {gy+r*yy:.0f} Q{cx:.0f} {gy+r*(yy+.05):.0f} {cx+r*1.0:.0f} {gy+r*yy:.0f}" fill="none" stroke="{CREAM}" stroke-opacity="{op}" stroke-width="{3*s:.1f}"/>')
    g.append('</g>')
    out += g
    # 人：站在地上，头旁一颗青色的 AI，两条弧把它们连成一个思维体
    fx = cx - r * .47
    hip = (fx, gy - r * .30)
    sh = (fx + r * .01, gy - r * .54)
    head = (fx + r * .015, gy - r * .655)
    st = 17 * s
    out += [f'<g stroke="{CREAM}" stroke-width="{st:.1f}" stroke-linecap="round" stroke-linejoin="round" fill="none">',
            f'<path d="M{hip[0]:.0f} {hip[1]:.0f} L{sh[0]:.0f} {sh[1]:.0f}"/>',
            f'<path d="M{hip[0]:.0f} {hip[1]:.0f} L{fx - r*.075:.0f} {gy - r*.01:.0f}"/>',
            f'<path d="M{hip[0]:.0f} {hip[1]:.0f} L{fx + r*.085:.0f} {gy - r*.01:.0f}"/>',
            f'<path d="M{sh[0]:.0f} {sh[1] + r*.035:.0f} L{fx - r*.10:.0f} {gy - r*.33:.0f}"/>',
            f'<path d="M{sh[0]:.0f} {sh[1] + r*.035:.0f} L{fx + r*.12:.0f} {gy - r*.40:.0f}"/></g>',
            f'<circle cx="{head[0]:.0f}" cy="{head[1]:.0f}" r="{r*.056:.0f}" fill="{GOLD2}"/>']
    ax, ay = head[0] + r * .31, head[1] - r * .10
    out.append(f'<path d="M{head[0]:.0f} {head[1]:.0f} Q{(head[0]+ax)/2:.0f} {head[1]-r*.24:.0f} {ax:.0f} {ay:.0f}" fill="none" stroke="{GOLD2}" stroke-width="{4*s:.1f}"/>')
    out.append(f'<path d="M{head[0]:.0f} {head[1]:.0f} Q{(head[0]+ax)/2:.0f} {head[1]+r*.10:.0f} {ax:.0f} {ay:.0f}" fill="none" stroke="{CYAN}" stroke-width="{4*s:.1f}"/>')
    out.append(f'<circle cx="{ax:.0f}" cy="{ay:.0f}" r="{r*.05:.0f}" fill="{CYAN}"/>')
    out.append(f'<circle cx="{ax:.0f}" cy="{ay:.0f}" r="{r*.085:.0f}" fill="none" stroke="{CYAN}" stroke-opacity=".45" stroke-width="{2.5*s:.1f}"/>')
    # 一轮：从思维体落到地上（实线金弧，带箭头），现实回答写回（青色虚线）
    lx, ly = cx + r * .55, gy - r * .005
    out.append(f'<path d="M{ax + r*.09:.0f} {ay - r*.03:.0f} C{cx + r*.12:.0f} {ay - r*.42:.0f} {lx + r*.02:.0f} {ay - r*.22:.0f} {lx:.0f} {ly - r*.075:.0f}" fill="none" stroke="{GOLD2}" stroke-width="{7*s:.1f}" stroke-linecap="round"/>')
    out.append(f'<path d="M{lx - r*.05:.0f} {ly - r*.125:.0f} L{lx:.0f} {ly - r*.045:.0f} L{lx + r*.052:.0f} {ly - r*.12:.0f}" fill="none" stroke="{GOLD2}" stroke-width="{7*s:.1f}" stroke-linecap="round" stroke-linejoin="round"/>')
    out.append(f'<path d="M{lx - r*.10:.0f} {ly - r*.04:.0f} C{lx - r*.35:.0f} {ly - r*.20:.0f} {ax + r*.22:.0f} {ay + r*.26:.0f} {ax + r*.075:.0f} {ay + r*.08:.0f}" fill="none" stroke="{CYAN}" stroke-opacity=".9" stroke-width="{4.5*s:.1f}" stroke-dasharray="{15*s:.0f} {12*s:.0f}" stroke-linecap="round"/>')
    # 落点：一株新苗
    px = lx + r * .17
    out.append(f'<path d="M{px:.0f} {ly:.0f} L{px:.0f} {ly - r*.15:.0f}" stroke="{CREAM}" stroke-width="{6*s:.1f}" stroke-linecap="round"/>')
    out.append(f'<path d="M{px:.0f} {ly - r*.12:.0f} C{px - r*.10:.0f} {ly - r*.16:.0f} {px - r*.10:.0f} {ly - r*.24:.0f} {px - r*.10:.0f} {ly - r*.24:.0f} C{px - r*.03:.0f} {ly - r*.24:.0f} {px:.0f} {ly - r*.18:.0f} {px:.0f} {ly - r*.12:.0f} Z" fill="{GOLD2}"/>')
    out.append(f'<path d="M{px:.0f} {ly - r*.09:.0f} C{px + r*.10:.0f} {ly - r*.13:.0f} {px + r*.10:.0f} {ly - r*.21:.0f} {px + r*.10:.0f} {ly - r*.21:.0f} C{px + r*.03:.0f} {ly - r*.21:.0f} {px:.0f} {ly - r*.15:.0f} {px:.0f} {ly - r*.09:.0f} Z" fill="{GOLD2}"/>')
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
<div class="t"><div class="pre">AI是加速</div><div class="big">你的落地</div>
<div class="sub">人-AI复合思考体的价值与意义</div></div>
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
<div class="c"><div class="q">AI是加速你的落地，<br>而不是代替你落地。<br>人与人的竞争，落在谁有新思想，<br>谁能更快把它变成<br>经得起现实回答的实践方案。</div>
<div class="bl"><p>很多人问：AI 到底能不能落地？这个问法丢了主语。</p><p>上午有想法，下午实验室就能从十个方案里选最可能的去做；灵感还热，书已成稿。千倍万倍要分三本账来算，现实回答得多快，决定加速的上限。这本书把判断说足，也写明它自己怎样会错。</p></div>
<div class="gold">地是你的。　　——本书</div></div>
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
