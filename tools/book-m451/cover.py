#!/usr/bin/env python3
"""第 628 号《发生的时差》封面与封底（220 系列版式）：主图是金圆环里的 H 形档位板、一根正在换档的变速杆和一只小钟。
用法：python3 cover.py --fonts /home/claude/fonts --out <dir>
"""
import argparse
import math
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#14244A', '#1A2D57', '#16284E'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#58BDCA', '#EFE8D6', '#9FB0C8'
ISBN = '979-8-90690-451-5'

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
"""


def rings(cx, cy, r):
    ticks = []
    for k in range(72):
        a = k * math.pi * 2 / 72
        r1 = r * (1.035 if k % 6 else 1.06)
        ticks.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (
            cx + r * math.cos(a), cy + r * math.sin(a), cx + r1 * math.cos(a), cy + r1 * math.sin(a)))
    return f"""
<circle cx="{cx}" cy="{cy}" r="{r*1.55:.0f}" fill="url(#halo{{uid}})"/>
<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{GOLD}" stroke-opacity=".55" stroke-width="2.2"/>
<circle cx="{cx}" cy="{cy}" r="{r*1.10:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".22" stroke-width="1.2"/>
<circle cx="{cx}" cy="{cy}" r="{r*0.62:.0f}" fill="none" stroke="{CYAN}" stroke-opacity=".16" stroke-width="1.2" stroke-dasharray="3 9"/>
<g stroke="{GOLD}" stroke-opacity=".45" stroke-width="1.6">{''.join(ticks)}</g>"""


ROSE, ROSE2, WARM = '#E8A3A0', '#F6C9B8', '#F3D9A4'


def heart_pts(cx, cy, k, n=240):
    pts = []
    for i in range(n + 1):
        t = 2 * math.pi * i / n
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + x * k, cy - y * k))
    return pts


def art(W, H, uid):
    """主图（220/302 平面风）：一只细金大圆环里，一块 H 形档位板，奶白色变速杆正从一档往另一档推；
    左边一只金边小钟，两根青色指针一长一短；变速杆球头外一串由大到小的金点，像档位刚刚换过。"""
    s = W / 1700
    cx, cy, R = W * 0.60, H * 0.68, 470 * s
    o = [f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{R:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".75" stroke-width="{3.2*s:.1f}"/>']
    # 档位板
    px, py, pw, ph = cx - 300 * s, cy + 120 * s, 600 * s, 230 * s
    o.append(f'<rect x="{px:.0f}" y="{py:.0f}" width="{pw:.0f}" height="{ph:.0f}" rx="{26*s:.0f}" fill="#8C7344"/>')
    o.append(f'<rect x="{px:.0f}" y="{py - 26*s:.0f}" width="{pw:.0f}" height="{ph:.0f}" rx="{26*s:.0f}" fill="{GOLD}"/>')
    gy0, gy1, gm = py + 14 * s, py + ph - 66 * s, py - 26 * s + ph / 2
    xs = [cx - 190 * s, cx, cx + 190 * s]
    sl = f'stroke="#3B3020" stroke-width="{22*s:.0f}" stroke-linecap="round"'
    o.append(f'<line x1="{xs[0]:.0f}" y1="{gm:.0f}" x2="{xs[2]:.0f}" y2="{gm:.0f}" {sl}/>')
    for x in xs:
        o.append(f'<line x1="{x:.0f}" y1="{gy0:.0f}" x2="{x:.0f}" y2="{gy1:.0f}" {sl}/>')
    # 变速杆：从中缝偏上处立起，略向右倾
    bx, by = xs[1], gy0 + 4 * s
    tx, ty = cx + 110 * s, cy - 330 * s
    o.append(f'<ellipse cx="{bx:.0f}" cy="{by + 8*s:.0f}" rx="{58*s:.0f}" ry="{20*s:.0f}" fill="#3B3020" fill-opacity=".55"/>')
    o.append(f'<line x1="{bx:.0f}" y1="{by:.0f}" x2="{tx:.0f}" y2="{ty:.0f}" stroke="{CREAM}" stroke-width="{30*s:.0f}" stroke-linecap="round"/>')
    o.append(f'<circle cx="{tx:.0f}" cy="{ty:.0f}" r="{78*s:.0f}" fill="{CREAM}"/>')
    o.append(f'<circle cx="{tx:.0f}" cy="{ty:.0f}" r="{30*s:.0f}" fill="{GOLD}"/>')
    # 换档的轨迹：金点由小到大
    for k in range(6):
        ang = math.radians(-150 + k * 17)
        r2 = 150 * s
        o.append(f'<circle cx="{tx + r2*math.cos(ang):.0f}" cy="{ty + r2*math.sin(ang) + 40*s:.0f}" r="{(5 + k*2.6)*s:.1f}" fill="{GOLD2}" fill-opacity="{.35 + k*.12:.2f}"/>')
    # 左侧小钟：金边，两根青针，一长一短
    kx, ky, kr = cx - 330 * s, cy - 40 * s, 112 * s
    o.append(f'<circle cx="{kx:.0f}" cy="{ky:.0f}" r="{kr:.0f}" fill="#13284A" stroke="{GOLD}" stroke-width="{12*s:.0f}"/>')
    for k in range(12):
        a2 = k * math.pi / 6
        o.append(f'<circle cx="{kx + kr*.74*math.cos(a2):.0f}" cy="{ky + kr*.74*math.sin(a2):.0f}" r="{(6 if k % 3 == 0 else 3.4)*s:.1f}" fill="{CREAM}" fill-opacity=".8"/>')
    o.append(f'<line x1="{kx:.0f}" y1="{ky:.0f}" x2="{kx + kr*.6*math.cos(math.radians(-130)):.0f}" y2="{ky + kr*.6*math.sin(math.radians(-130)):.0f}" stroke="{CYAN}" stroke-width="{14*s:.0f}" stroke-linecap="round"/>')
    o.append(f'<line x1="{kx:.0f}" y1="{ky:.0f}" x2="{kx + kr*.42*math.cos(math.radians(20)):.0f}" y2="{ky + kr*.42*math.sin(math.radians(20)):.0f}" stroke="{CYAN}" stroke-width="{18*s:.0f}" stroke-linecap="round"/>')
    o.append(f'<circle cx="{kx:.0f}" cy="{ky:.0f}" r="{14*s:.0f}" fill="{GOLD2}"/>')
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
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{Wmm}mm" height="{Hmm}mm">{background(W, H, "f")}{art(W, H, "f")}'
    svg += f'<line x1="{W*.52:.0f}" y1="{H*.858:.0f}" x2="{W*.975:.0f}" y2="{H*.858:.0f}" stroke="{DIM}" stroke-opacity=".45" stroke-width="{1.6*s:.1f}"/>'
    svg += f'<line x1="{W*.07:.0f}" y1="{H*.818:.0f}" x2="{W*.34:.0f}" y2="{H*.818:.0f}" stroke="{DIM}" stroke-opacity=".45" stroke-width="{1.6*s:.1f}"/></svg>'
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page{{size:{Wmm}mm {Hmm}mm;margin:0}} body{{margin:0}}
.pg{{position:relative;width:{Wmm}mm;height:{Hmm}mm;overflow:hidden}}
.pg svg{{position:absolute;left:0;top:0}}
.t{{position:absolute;left:{12*s:.1f}mm;top:{30*s:.1f}mm;color:{CREAM}}}
.pre{{font:700 {15*s:.1f}pt 'Noto Serif CJK SC';letter-spacing:.06em;color:#F7F1E3}}
.big{{font:700 {44*s:.1f}pt/1.2 'Noto Serif CJK SC';letter-spacing:.06em;color:#F7F1E3;margin:{3*s:.1f}mm 0 {7*s:.1f}mm {-1*s:.1f}mm}}
.sub{{font:400 {9.6*s:.1f}pt/1.75 'Noto Sans CJK SC';color:{GOLD2};letter-spacing:.04em}}
.au{{position:absolute;left:{12*s:.1f}mm;top:{208*s/170*170*Hmm/240:.1f}mm}}
.au{{position:absolute;left:{12*s:.1f}mm;top:{Hmm*.84:.1f}mm;font:400 {12.5*s:.1f}pt 'Noto Serif CJK SC';color:#F7F1E3;letter-spacing:.3em}}
.au2{{position:absolute;left:{12*s:.1f}mm;top:{Hmm*.84+8*s:.1f}mm;font:400 {8.2*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.22em}}
.b{{position:absolute;left:{12*s:.1f}mm;bottom:{11*s:.1f}mm}}
.ph{{font:700 {9.6*s:.1f}pt 'Noto Sans CJK SC';color:#F7F1E3;letter-spacing:.12em}}
.pe{{font:400 {6.2*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.14em;margin-top:{1.2*s:.1f}mm}}
</style></head><body><div class="pg">{svg}
<div class="t"><div class="pre">普通人都能懂的快慢之学</div><div class="big">发生的时差</div>
<div class="sub">不怕慢，怕卡档——一本讲换档的书</div></div>
<div class="au">王德生　著</div><div class="au2">WDS博士　立题与裁定</div>
<div class="b"><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div>
</div></body></html>"""


def back(Wmm, Hmm, F):
    W, H = Wmm * 10, Hmm * 10
    s = Wmm / 170
    ring = f'<circle cx="{W*.80:.0f}" cy="{H*.17:.0f}" r="{W*.235:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".75" stroke-width="{3.2*s:.1f}"/>'
    bc, bw = barcode(0, 0, s)
    box = f'<g transform="translate({W - bw - 70*s:.0f},{H - 290*s - 120*s:.0f})">{bc}</g>'
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{Wmm}mm" height="{Hmm}mm">'
           f'{background(W, H, "b")}{ring}{box}</svg>')
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page{{size:{Wmm}mm {Hmm}mm;margin:0}} body{{margin:0}}
.pg{{position:relative;width:{Wmm}mm;height:{Hmm}mm;overflow:hidden}}
.pg svg{{position:absolute;left:0;top:0}}
.c{{position:absolute;left:{14*s:.1f}mm;top:{17*s:.1f}mm;width:{118*s:.1f}mm;color:{CREAM}}}
.q{{font:700 {11.6*s:.1f}pt/1.95 'Noto Sans CJK SC';color:#F7F1E3;letter-spacing:.04em;margin:0 0 {8*s:.1f}mm}}
.bl p{{font:400 {8.2*s:.1f}pt/2.05 'Noto Sans CJK SC';color:{CREAM};opacity:.92;margin:0}}
.gold{{font:400 {8.4*s:.1f}pt 'Noto Sans CJK SC';color:{GOLD2};margin-top:{9*s:.1f}mm;letter-spacing:.04em}}
.gold span{{margin-left:{9*s:.1f}mm}}
.f{{position:absolute;left:{14*s:.1f}mm;bottom:{14*s:.1f}mm;font:400 {6.8*s:.1f}pt/2.1 'Noto Sans CJK SC';color:{CREAM};opacity:.9}}
.f:before{{content:'';display:block;width:{40*s:.1f}mm;border-top:.6pt solid {GOLD};opacity:.6;margin-bottom:{3*s:.1f}mm}}
</style></head><body><div class="pg">{svg}
<div class="c"><div class="q">快慢不同，是常事；<br>快慢的次序<br>再也换不过来，<br>才是病。</div>
<div class="bl"><p>外公开了三十一年货车，他的话是：「不怕慢，怕卡档。」</p><p>车慢一点不要紧，上坡挂低档，平路挂高档，</p><p>长下坡再挂回低档；要紧的是档还换得过来。</p><p>这本书把这句话带进身体、家、国家、老书和知识里，</p><p>一样一样问：这里谁缓得快、谁缓得慢？</p><p>这个次序，还换得过来吗？</p></div>
<div class="gold">活着，就是这个次序还换得过来。<span>——本书</span></div></div>
<div class="f">德麦国际出版社 · Demai International Press<br>德麦国际专著第 451 号<br>定价：US$23.00</div>
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
