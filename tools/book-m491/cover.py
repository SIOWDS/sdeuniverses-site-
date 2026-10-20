#!/usr/bin/env python3
"""第 491 号《SDE平台：慧店的诞生》封面与封底（由第 503 号改来，220 系列版式）：主图是一片地上的许多口井，地下水脉相连，远处一座越来越淡的水塔。
用法：python3 cover.py --fonts /home/claude/fonts --out <dir>
"""
import argparse
import math
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0B1830', '#1B3158', '#142746'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#58BDCA', '#EFE8D6', '#9FB0C8'
ISBN = '979-8-90690-150-7'

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
    """主图：一片起伏的地，地上散着许多口井，井与井之间有地下虚线水脉相连（谱系、地下水图）；
    中右一口大井泛着青色水光，井架上一道金色的提绳；左上远处一座细线勾的水塔，几根管子伸下来，越伸越淡。"""
    import random
    rnd = random.Random(491)
    s = W / 1700
    out = [f"""<defs>
 <radialGradient id="glow{uid}" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{CYAN}" stop-opacity=".55"/>
  <stop offset=".45" stop-color="{CYAN}" stop-opacity=".16"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient>
 <radialGradient id="gold{uid}" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{GOLD2}" stop-opacity=".9"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></radialGradient>
 <linearGradient id="fade{uid}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{CREAM}" stop-opacity=".5"/><stop offset="1" stop-color="{CREAM}" stop-opacity="0"/></linearGradient>
</defs>"""]
    for k in range(14):
        y0 = H * (0.50 + k * 0.032)
        amp = (18 + k * 3) * s
        ph = rnd.uniform(0, 6.28)
        pts = []
        for i in range(41):
            x = W * i / 40
            y = y0 + amp * math.sin(i / 40 * 6.28 * 1.3 + ph) + amp * 0.4 * math.sin(i / 40 * 6.28 * 3.1 + ph * 2)
            pts.append((x, y))
        d = 'M' + ' L'.join('%.0f %.0f' % q for q in pts)
        out.append(f'<path d="{d}" fill="none" stroke="{GOLD}" stroke-opacity="{.10 + .012*k:.3f}" stroke-width="{1.3*s:.1f}"/>')
    wells = []
    tries = 0
    while len(wells) < 26 and tries < 6000:
        tries += 1
        x = rnd.uniform(W * 0.06, W * 0.95); y = rnd.uniform(H * 0.56, H * 0.94)
        r = (14 + (y - H * 0.55) / (H * 0.38) * 26) * s
        if all(math.hypot(x - a2, (y - b2) * 2.2) > (r + rr) * 2.6 for a2, b2, rr in wells) and not (W*0.46 < x < W*0.88 and H*0.58 < y < H*0.84):
            wells.append((x, y, r))
    main = (W * 0.66, H * 0.71, 74 * s)
    allw = wells + [main]
    for i, (x, y, r) in enumerate(allw):
        near = sorted(range(len(allw)), key=lambda j: math.hypot(allw[j][0] - x, allw[j][1] - y))[1:3]
        for j in near:
            x2, y2, _ = allw[j]
            mx, my = (x + x2) / 2, max(y, y2) + 40 * s
            out.append(f'<path d="M{x:.0f} {y:.0f} Q{mx:.0f} {my:.0f} {x2:.0f} {y2:.0f}" fill="none" stroke="{CYAN}" stroke-opacity=".30" stroke-width="{1.3*s:.1f}" stroke-dasharray="{3*s:.1f} {8*s:.1f}"/>')
    for x, y, r in wells:
        out.append(f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{r*2.4:.0f}" ry="{r*1.1:.0f}" fill="url(#glow{uid})" fill-opacity=".5"/>')
        out.append(f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{r:.0f}" ry="{r*.45:.0f}" fill="#0A1528" stroke="{GOLD2}" stroke-opacity=".75" stroke-width="{1.6*s:.1f}"/>')
        out.append(f'<ellipse cx="{x:.0f}" cy="{y + r*.06:.0f}" rx="{r*.62:.0f}" ry="{r*.25:.0f}" fill="none" stroke="{CYAN}" stroke-opacity=".7" stroke-width="{1.2*s:.1f}"/>')
    x, y, r = main
    out.append(f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{r*4.4:.0f}" ry="{r*2.2:.0f}" fill="url(#glow{uid})"/>')
    for rr, op in [(1.9, .14), (1.5, .26)]:
        out.append(f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{r*rr:.0f}" ry="{r*rr*.45:.0f}" fill="none" stroke="{CYAN}" stroke-opacity="{op}" stroke-width="{1.6*s:.1f}"/>')
    out.append(f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{r:.0f}" ry="{r*.45:.0f}" fill="#081224" stroke="{GOLD2}" stroke-width="{4*s:.1f}"/>')
    out.append(f'<ellipse cx="{x:.0f}" cy="{y + 4*s:.0f}" rx="{r*.7:.0f}" ry="{r*.28:.0f}" fill="{CYAN}" fill-opacity=".55"/>')
    out.append(f'<ellipse cx="{x - r*.2:.0f}" cy="{y:.0f}" rx="{r*.22:.0f}" ry="{r*.07:.0f}" fill="#E8FBFF" fill-opacity=".85"/>')
    lx, rx2, top = x - r * 1.05, x + r * 1.05, y - r * 2.3
    out.append(f'<line x1="{lx:.0f}" y1="{y:.0f}" x2="{x - r*.25:.0f}" y2="{top:.0f}" stroke="{CREAM}" stroke-opacity=".8" stroke-width="{3*s:.1f}" stroke-linecap="round"/>')
    out.append(f'<line x1="{rx2:.0f}" y1="{y:.0f}" x2="{x + r*.25:.0f}" y2="{top:.0f}" stroke="{CREAM}" stroke-opacity=".8" stroke-width="{3*s:.1f}" stroke-linecap="round"/>')
    out.append(f'<line x1="{x - r*.4:.0f}" y1="{top:.0f}" x2="{x + r*.4:.0f}" y2="{top:.0f}" stroke="{CREAM}" stroke-width="{3.4*s:.1f}" stroke-linecap="round"/>')
    out.append(f'<line x1="{x:.0f}" y1="{top:.0f}" x2="{x:.0f}" y2="{y - r*.05:.0f}" stroke="{GOLD2}" stroke-width="{2.2*s:.1f}"/>')
    out.append(f'<rect x="{x - 9*s:.0f}" y="{y - r*.95:.0f}" width="{18*s:.0f}" height="{20*s:.0f}" rx="{3*s:.0f}" fill="{GOLD}"/>')
    out.append(f'<circle cx="{x:.0f}" cy="{y - r*1.2:.0f}" r="{120*s:.0f}" fill="url(#gold{uid})" fill-opacity=".18"/>')
    tx, ty = W * 0.20, H * 0.47
    out.append(f'<g stroke="{CREAM}" stroke-opacity=".35" stroke-width="{2*s:.1f}" fill="none">'
               f'<rect x="{tx - 46*s:.0f}" y="{ty - 150*s:.0f}" width="{92*s:.0f}" height="{56*s:.0f}" rx="{8*s:.0f}"/>'
               f'<line x1="{tx - 38*s:.0f}" y1="{ty - 94*s:.0f}" x2="{tx - 56*s:.0f}" y2="{ty:.0f}"/>'
               f'<line x1="{tx + 38*s:.0f}" y1="{ty - 94*s:.0f}" x2="{tx + 56*s:.0f}" y2="{ty:.0f}"/>'
               f'<line x1="{tx - 47*s:.0f}" y1="{ty - 50*s:.0f}" x2="{tx + 47*s:.0f}" y2="{ty - 50*s:.0f}"/></g>')
    for k in range(4):
        ex = W * (0.34 + k * 0.16); ey = H * (0.57 + 0.02 * k)
        out.append(f'<path d="M{tx:.0f} {ty:.0f} Q{(tx+ex)/2:.0f} {ty + 20*s:.0f} {ex:.0f} {ey:.0f}" fill="none" stroke="url(#fade{uid})" stroke-width="{1.6*s:.1f}" stroke-dasharray="{10*s:.1f} {6*s:.1f}"/>')
    for _ in range(90):
        out.append(f'<circle cx="{rnd.uniform(0, W):.0f}" cy="{rnd.uniform(H*0.32, H*0.5):.0f}" r="{rnd.uniform(.8, 2.2)*s:.1f}" fill="{CREAM}" fill-opacity="{rnd.uniform(.15, .5):.2f}"/>')
    return ''.join(out)


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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 491 号</div>
<div class="t"><div class="pre">SDE 平台</div><div class="big big2">慧店的<br>诞生</div>
<div class="sub">让天下没有难发生的知识</div><div class="rule"></div></div>
<div class="b"><div class="au">王德生　著</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div>
</div></body></html>"""


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
           f'{background(W, H, "b")}{emb}{"".join(waves)}{bc}</svg>')
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
<div class="c"><div class="lab">判 词</div>
<div class="q">知识不能再批发，<br>只能在每一个部落里<br>重新发生。</div><div class="by">——本书判词</div><div class="rule"></div>
<div class="bl"><p>一位中学老师发现，班上的孩子越来越不像一个班；一个修电动车的小伙子手机里有四十多个骑手群，各有各的规矩。指南对每个人都对，对谁都不够。</p>
<p>本书说：从许多人身上抽出来的那个「大家都一样」正在消失，人群碎成了部落。公共知识像自来水，送到了却不合用；未来的知识要在每块地上打井——人与 AI 结成复合体，开一家家「慧店」，以专著集合体为底座，服务一个个部落。SDE 平台服务千千万万家慧店。</p>
<p>新的规矩只有六个字：局部宣称，有检验。</p></div>
<div class="gold">让天下没有难发生的知识。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 491 号 · 八编四十八章 · 约 20 万字<br>定价 US$20.00</div>
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
