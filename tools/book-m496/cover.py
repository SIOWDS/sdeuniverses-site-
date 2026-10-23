#!/usr/bin/env python3
"""第 496 号《化冲突》封面与封底（照第 220、302 号气质：藏青渐变底、细点阵、大号书名、金色副题、金环内的扁平主图、白色大字判词、右下条码）；
主图是一口锅、三个碗：三条线从三个碗里升起，在锅里汇合，又从锅口分开；每个碗里都有自己的颜色，也有一粒邻碗的颜色。画面里没有人，也没有指挥的手。
用法：python3 cover.py --fonts /home/claude/fonts --out <dir>
"""
import argparse
import math
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0B1830', '#1B3158', '#142746'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#58BDCA', '#EFE8D6', '#9FB0C8'
ISBN = '979-8-90690-821-6'

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


def background(W, H, uid):
    dots = []
    step = 44
    for yy in range(22, H, step):
        for xx in range(22 + (yy // step % 2) * 22, W, step):
            dots.append('<circle cx="%d" cy="%d" r="1.7"/>' % (xx, yy))
    return f"""
<defs>
 <linearGradient id="bg{uid}" x1="0" y1="0" x2="0.35" y2="1">
  <stop offset="0" stop-color="{NAVY_TOP}"/><stop offset=".58" stop-color="{NAVY_MID}"/><stop offset="1" stop-color="{NAVY_LOW}"/></linearGradient>
 <radialGradient id="halo{uid}" cx=".5" cy=".5" r=".5">
  <stop offset="0" stop-color="{GOLD2}" stop-opacity=".30"/><stop offset=".45" stop-color="{GOLD}" stop-opacity=".12"/>
  <stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></radialGradient>
 <linearGradient id="kite{uid}" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="{CREAM}" stop-opacity=".95"/><stop offset="1" stop-color="{GOLD}" stop-opacity=".85"/></linearGradient>
 <linearGradient id="handle{uid}" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#B89A5E"/><stop offset=".45" stop-color="{CREAM}"/><stop offset="1" stop-color="#A88C55"/></linearGradient>
 <linearGradient id="line{uid}" x1="0" y1="1" x2="1" y2="0">
  <stop offset="0" stop-color="{GOLD}"/><stop offset="1" stop-color="{GOLD2}"/></linearGradient>
</defs>
<rect width="{W}" height="{H}" fill="url(#bg{uid})"/>
<g fill="{DIM}" fill-opacity=".10">{''.join(dots)}</g>"""



def ring(cx, cy, r, uid):
    return (f'<defs><radialGradient id="rg{uid}" cx=".5" cy=".5" r=".5"><stop offset=".86" stop-color="{GOLD}" stop-opacity="0"/>'
            f'<stop offset=".97" stop-color="{GOLD2}" stop-opacity=".16"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></radialGradient></defs>'
            f'<circle cx="{cx}" cy="{cy}" r="{r*1.08:.0f}" fill="url(#rg{uid})"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{GOLD}" stroke-opacity=".62" stroke-width="3.4"/>')


BOWLS = [(560, '#F3EAD6', '#D9C79B'), (860, '#E3C77E', '#B89A4E'), (1160, '#58BDCA', '#3A8E9A')]


def art(W, H, uid):
    """主图：一口锅，三个碗。三条线从三个碗里升起、在锅里汇合，又从锅口分开；每个碗里都有自己的颜色，也有一粒邻碗的颜色。
    画面里没有人，也没有指挥的手。"""
    s = W / 1700
    cx, cy, r = 1150, 1500, 640
    o = [ring(cx * s, cy * s, r * s, uid)]
    g = [f'<g transform="scale({s}) translate(140,-40)">']
    # 三条线：碗 → 锅底（汇合）
    for (bx, c1, c2), col in zip(BOWLS, ['#F3EAD6', '#E3C77E', '#58BDCA']):
        g.append(f'<path d="M{bx} 1880 C{bx} 1740 860 1740 860 1600" fill="none" stroke="{col}" stroke-opacity=".9" stroke-width="7" stroke-linecap="round"/>')
    # 锅
    g.append('<path d="M690 1318 L1030 1318 Q1056 1318 1054 1346 L1036 1500 Q1026 1590 936 1590 L784 1590 Q694 1590 684 1500 L666 1346 Q664 1318 690 1318 Z" fill="#F3EAD6"/>')
    g.append('<rect x="636" y="1360" width="50" height="62" rx="25" fill="none" stroke="#D9C79B" stroke-width="12"/><rect x="1034" y="1360" width="50" height="62" rx="25" fill="none" stroke="#D9C79B" stroke-width="12"/>')
    g.append('<rect x="676" y="1282" width="368" height="40" rx="14" fill="#D9C79B"/><circle cx="860" cy="1262" r="20" fill="#E3C77E"/>')
    g.append('<path d="M700 1420 L1020 1420" stroke="#D9C79B" stroke-width="10" stroke-linecap="round"/>')
    # 三缕热气：从锅口分开
    for dx, col, (ex, ey) in [(-60, '#F3EAD6', (610, 1010)), (0, '#E3C77E', (860, 960)), (60, '#58BDCA', (1110, 1010))]:
        x0 = 860 + dx
        g.append(f'<path d="M{x0} 1236 C{x0} 1160 {(x0 + ex) / 2} 1130 {ex} {ey}" fill="none" stroke="{col}" stroke-opacity=".9" stroke-width="7" stroke-linecap="round"/>')
        g.append(f'<circle cx="{ex}" cy="{ey}" r="15" fill="{col}"/>')
    # 三个碗
    for k, (bx, c1, c2) in enumerate(BOWLS):
        g.append(f'<path d="M{bx - 135} 1880 L{bx + 135} 1880 A135 105 0 0 1 {bx - 135} 1880 Z" fill="{c1}"/>')
        g.append(f'<rect x="{bx - 62}" y="1976" width="124" height="22" rx="8" fill="{c2}"/>')
        g.append(f'<rect x="{bx - 150}" y="1868" width="300" height="20" rx="10" fill="{c2}"/>')
        other = BOWLS[(k + 1) % 3][1]
        for j, (dx, dy, cc) in enumerate([(-72, 0, c1), (-24, -16, c1), (26, -4, c1), (74, -12, other)]):
            g.append(f'<circle cx="{bx + dx}" cy="{1846 + dy}" r="17" fill="{cc}" stroke="#16253d" stroke-width="3"/>')
    g.append('</g>')
    # 台面线与远处的点
    g.append(f'<line x1="{760 * s:.0f}" y1="{2045 * s:.0f}" x2="{W - 60 * s:.0f}" y2="{2045 * s:.0f}" stroke="{DIM}" stroke-opacity=".45" stroke-width="{2.4 * s:.1f}"/>')
    dots = ''.join(f'<circle cx="{(1560 + i * 40) * s:.0f}" cy="{(1930 - i * 55) * s:.0f}" r="{(15 - i * 2.4) * s:.1f}" fill="{GOLD}" fill-opacity="{.95 - i * .17:.2f}"/>' for i in range(5))
    return ''.join(o) + ''.join(g) + dots


def barcode(x, y, s):
    if not re.search(r'\d{13}', re.sub(r'\D', '', ISBN) or ''):
        return (f'<rect x="{x:.0f}" y="{y:.0f}" width="{520*s:.0f}" height="{300*s:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".6" stroke-width="{2*s:.1f}" stroke-dasharray="{8*s:.0f} {8*s:.0f}"/>'
                f'<text x="{x + 260*s:.0f}" y="{y + 170*s:.0f}" font-size="{34*s:.0f}" text-anchor="middle" font-family="Noto Sans CJK SC" fill="{CREAM}" fill-opacity=".8">ISBN · 定价　待填</text>'), 520*s
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
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page{{size:{Wmm}mm {Hmm}mm;margin:0}} body{{margin:0}}
.pg{{position:relative;width:{Wmm}mm;height:{Hmm}mm;overflow:hidden}}
.pg svg{{position:absolute;left:0;top:0}}
.t{{position:absolute;left:{11.5*s:.1f}mm;top:{38*s:.1f}mm;color:{CREAM}}}
.big{{font:700 {96*s:.1f}pt/1.15 'Noto Serif CJK SC';letter-spacing:.06em;color:#F7F1E3;margin:0 0 {5*s:.1f}mm {-1*s:.1f}mm}}
.sub{{font:500 {13.4*s:.1f}pt/1.75 'Noto Sans CJK SC';color:{GOLD2};letter-spacing:.04em;margin-left:{1*s:.1f}mm}}
.no{{position:absolute;right:{15*s:.1f}mm;top:{15*s:.1f}mm;font:400 {6.6*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.2em;text-align:right}}
.au{{position:absolute;left:{11.5*s:.1f}mm;top:{201*s:.1f}mm;font:400 {17*s:.1f}pt 'Noto Sans CJK SC';color:{CREAM};letter-spacing:.3em}}
.auline{{position:absolute;left:{11.5*s:.1f}mm;top:{196*s:.1f}mm;width:{47*s:.1f}mm;border-top:.9pt solid {DIM};opacity:.6}}
.ph{{position:absolute;left:{11.5*s:.1f}mm;top:{217*s:.1f}mm;font:600 {11.2*s:.1f}pt 'Noto Sans CJK SC';color:{CREAM};letter-spacing:.14em}}
.pe{{position:absolute;left:{11.5*s:.1f}mm;top:{224*s:.1f}mm;font:400 {7.8*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.16em}}
</style></head><body><div class="pg">{svg}
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 496 号</div>
<div class="t"><div class="big">化冲突</div><div class="sub">谱系社会的新知识发生器</div></div>
<div class="auline"></div><div class="au">王德生　著</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div>
</div></body></html>"""


def back(Wmm, Hmm, F):
    W, H = Wmm * 10, Hmm * 10
    s = Wmm / 170
    cx, cy, r = W * 0.80, H * 0.185, 480 * s
    ringsvg = (f'<defs><radialGradient id="rgb" cx=".5" cy=".5" r=".5"><stop offset=".88" stop-color="{GOLD}" stop-opacity="0"/><stop offset=".97" stop-color="{GOLD2}" stop-opacity=".16"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></radialGradient></defs>'
               f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r*1.08:.0f}" fill="url(#rgb)"/><circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".62" stroke-width="{3.4*s:.1f}"/>')
    bc, bw = barcode(W - 170 * s - 380 * s, H - 150 * s - 300 * s, s)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{Wmm}mm" height="{Hmm}mm">'
           f'{background(W, H, "b")}{ringsvg}{bc}</svg>')
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page{{size:{Wmm}mm {Hmm}mm;margin:0}} body{{margin:0}}
.pg{{position:relative;width:{Wmm}mm;height:{Hmm}mm;overflow:hidden}}
.pg svg{{position:absolute;left:0;top:0}}
.c{{position:absolute;left:{13*s:.1f}mm;top:{20*s:.1f}mm;width:{130*s:.1f}mm;color:{CREAM}}}
.q{{font:600 {15.2*s:.1f}pt/1.95 'Noto Sans CJK SC';color:#FFFFFF;margin:0 0 {9*s:.1f}mm}}
.bl p{{font:400 {10.6*s:.1f}pt/1.95 'Noto Sans CJK SC';color:#EDE7D8;margin:0 0 {3.6*s:.1f}mm}}
.gold{{font:500 {11.6*s:.1f}pt/1.8 'Noto Sans CJK SC';color:{GOLD2};margin-top:{9*s:.1f}mm}}
.gold span{{margin-left:{9*s:.1f}mm}}
.f{{position:absolute;left:{13*s:.1f}mm;bottom:{16*s:.1f}mm;font:400 {8.6*s:.1f}pt/2.1 'Noto Sans CJK SC';color:#D6DCE8;border-top:.9pt solid {DIM};padding-top:{4*s:.1f}mm;width:{82*s:.1f}mm}}
</style></head><body><div class="pg">{svg}
<div class="c"><div class="q">谱系化之后，<br>冲突来得比化得快。<br>化它，不靠一个人拍板，<br>也不靠一套规则压平。</div>
<div class="bl"><p>一盘辣椒炒肉，<br>阿乐吃的是辣，小满怕辣，<br>外婆只吃得下炒软的。<br>三个人坐在一张桌上，<br>怎样才算和谐，而不是凑合？</p>
<p>本书给一个能被检验的答案：<br>在场、有差、认得；<br>再给一台当场生出新做法的发生器：<br>拆、筛、重做、认。</p>
<p>从家里的餐桌到班级、诊室和职场，<br>每一章都写明了怎样算错。</p></div>
<div class="gold">不设指挥，也要合上。<span>——本书</span></div></div>
<div class="f">德麦国际出版社 · Demai International Press<br>德麦国际专著第 496 号<br>定价：US$23.00</div>
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
