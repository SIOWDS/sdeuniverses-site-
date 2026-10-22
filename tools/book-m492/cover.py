#!/usr/bin/env python3
"""第 492 号《一店三门》封面与封底（由第 491 号改来，220 系列版式）：主图是一家开着三扇门的小店，三处门光各是奇、快、稳。
用法：python3 cover.py --fonts /home/claude/fonts --out <dir>
"""
import argparse
import math
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0B1830', '#1B3158', '#142746'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#58BDCA', '#EFE8D6', '#9FB0C8'
ISBN = '979-8-90690-152-1'

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
    """主图：一片起伏的地上，一家低檐小店开着三扇门。左门（作坊）漏出暖金与玫瑰色的星屑——奇；
    中门（实验室）射出几道青色的快线——快；右门（书房）一盏灯，光柱平稳落地——稳。
    三扇门前一条弧形小路把三处光连起来（门是双向的），地下浅浅的虚线水脉通向远处一口口小井（部落）。"""
    import random
    rnd = random.Random(492)
    s = W / 1700
    out = [f"""<defs>
 <radialGradient id="glow{uid}" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{CYAN}" stop-opacity=".55"/>
  <stop offset=".45" stop-color="{CYAN}" stop-opacity=".16"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient>
 <radialGradient id="gold{uid}" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{GOLD2}" stop-opacity=".9"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></radialGradient>
 <radialGradient id="rose{uid}" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{ROSE2}" stop-opacity=".75"/><stop offset="1" stop-color="{ROSE}" stop-opacity="0"/></radialGradient>
 <linearGradient id="beam{uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{WARM}" stop-opacity=".55"/><stop offset="1" stop-color="{WARM}" stop-opacity="0"/></linearGradient>
 <linearGradient id="door{uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#F6E7BE"/><stop offset="1" stop-color="{GOLD}"/></linearGradient>
</defs>"""]
    # 地层线
    for k in range(13):
        y0 = H * (0.70 + k * 0.024)
        amp = (10 + k * 2.4) * s
        ph = rnd.uniform(0, 6.28)
        pts = [(W * i / 40, y0 + amp * math.sin(i / 40 * 6.28 * 1.2 + ph) + amp * .35 * math.sin(i / 40 * 6.28 * 2.9 + ph * 2)) for i in range(41)]
        out.append(f'<path d="M{" L".join("%.0f %.0f" % q for q in pts)}" fill="none" stroke="{GOLD}" stroke-opacity="{.09 + .011*k:.3f}" stroke-width="{1.3*s:.1f}"/>')
    # 远处小井（部落）与地下水脉
    wells = []
    for _ in range(4000):
        if len(wells) >= 16: break
        x = rnd.uniform(W * .05, W * .95); y = rnd.uniform(H * .80, H * .95)
        r = (10 + (y - H * .80) / (H * .15) * 14) * s
        if all(math.hypot(x - a, (y - b) * 2.4) > (r + rr) * 3.2 for a, b, rr in wells) and not (W * .18 < x < W * .86 and y < H * .86) and not (x < W * .40 and y > H * .82):
            wells.append((x, y, r))
    for i, (x, y, r) in enumerate(wells):
        j = min((k for k in range(len(wells)) if k != i), key=lambda k: math.hypot(wells[k][0] - x, wells[k][1] - y))
        x2, y2, _ = wells[j]
        out.append(f'<path d="M{x:.0f} {y:.0f} Q{(x+x2)/2:.0f} {max(y,y2)+30*s:.0f} {x2:.0f} {y2:.0f}" fill="none" stroke="{CYAN}" stroke-opacity=".26" stroke-width="{1.2*s:.1f}" stroke-dasharray="{3*s:.1f} {8*s:.1f}"/>')
    for x, y, r in wells:
        out.append(f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{r*2.2:.0f}" ry="{r:.0f}" fill="url(#glow{uid})" fill-opacity=".45"/>')
        out.append(f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{r:.0f}" ry="{r*.45:.0f}" fill="#0A1528" stroke="{GOLD2}" stroke-opacity=".7" stroke-width="{1.4*s:.1f}"/>')
    # 小店
    x0, x1 = W * .14, W * .90
    base = H * .79
    wall_top = H * .60
    roof_y = H * .555
    out.append(f'<path d="M{x0 - 40*s:.0f} {wall_top:.0f} L{x0 + 20*s:.0f} {roof_y:.0f} L{x1 - 20*s:.0f} {roof_y:.0f} L{x1 + 40*s:.0f} {wall_top:.0f} Z" fill="#0E1D36" stroke="{GOLD2}" stroke-opacity=".75" stroke-width="{2.4*s:.1f}" stroke-linejoin="round"/>')
    for k in range(1, 14):
        xx = x0 + 20*s + (x1 - x0 - 40*s) * k / 14
        out.append(f'<line x1="{xx:.0f}" y1="{roof_y + 4*s:.0f}" x2="{xx + (xx - W*.52)*.06:.0f}" y2="{wall_top - 4*s:.0f}" stroke="{GOLD}" stroke-opacity=".22" stroke-width="{1.2*s:.1f}"/>')
    out.append(f'<rect x="{x0:.0f}" y="{wall_top:.0f}" width="{x1 - x0:.0f}" height="{base - wall_top:.0f}" fill="#0C1A31" stroke="{GOLD2}" stroke-opacity=".6" stroke-width="{2*s:.1f}"/>')
    # 匾：慧店
    mx = (x0 + x1) / 2
    out.append(f'<rect x="{mx - 80*s:.0f}" y="{wall_top + 14*s:.0f}" width="{160*s:.0f}" height="{46*s:.0f}" rx="{4*s:.0f}" fill="#0A1528" stroke="{GOLD}" stroke-width="{1.6*s:.1f}"/>')
    out.append(f'<text x="{mx:.0f}" y="{wall_top + 47*s:.0f}" font-size="{28*s:.0f}" text-anchor="middle" letter-spacing="{12*s:.0f}" font-family="Noto Serif CJK SC" font-weight="700" fill="{GOLD2}">慧店</text>')
    # 三扇门
    dw, dh = 150 * s, 250 * s
    doors = [(x0 + (x1 - x0) * f, k) for f, k in [(.20, 'qi'), (.50, 'kuai'), (.80, 'wen')]]
    for cx, kind in doors:
        dx, dy = cx - dw / 2, base - dh
        arch = f'M{dx:.0f} {base:.0f} L{dx:.0f} {dy + dw*.5:.0f} A{dw/2:.0f} {dw/2:.0f} 0 0 1 {dx + dw:.0f} {dy + dw*.5:.0f} L{dx + dw:.0f} {base:.0f} Z'
        if kind == 'qi':
            out.append(f'<ellipse cx="{cx:.0f}" cy="{base:.0f}" rx="{dw*1.7:.0f}" ry="{dw*.7:.0f}" fill="url(#rose{uid})" fill-opacity=".55"/>')
        elif kind == 'kuai':
            out.append(f'<ellipse cx="{cx:.0f}" cy="{base:.0f}" rx="{dw*1.9:.0f}" ry="{dw*.6:.0f}" fill="url(#glow{uid})"/>')
        else:
            out.append(f'<path d="M{dx + dw*.1:.0f} {base:.0f} L{dx - dw*.55:.0f} {base + 150*s:.0f} L{dx + dw*1.55:.0f} {base + 150*s:.0f} L{dx + dw*.9:.0f} {base:.0f} Z" fill="url(#beam{uid})"/>')
        out.append(f'<path d="{arch}" fill="url(#door{uid})" fill-opacity="{.92 if kind=="wen" else .82}" stroke="{GOLD2}" stroke-width="{2.6*s:.1f}"/>')
        if kind == 'qi':      # 星屑：一只纸鹤般的小星斜飞出门
            for _ in range(26):
                a = rnd.uniform(-2.6, -0.4); d = rnd.uniform(.25, 1.55) * dw
                px, py = cx + d * math.cos(a) * 1.3, dy + dw * .55 + d * math.sin(a) * .9
                r = rnd.uniform(1.4, 4.2) * s
                col = rnd.choice([ROSE2, WARM, CREAM, GOLD2])
                out.append(f'<path d="M{px:.0f} {py - r*2.2:.0f} L{px + r*.6:.0f} {py - r*.6:.0f} L{px + r*2.2:.0f} {py:.0f} L{px + r*.6:.0f} {py + r*.6:.0f} L{px:.0f} {py + r*2.2:.0f} L{px - r*.6:.0f} {py + r*.6:.0f} L{px - r*2.2:.0f} {py:.0f} L{px - r*.6:.0f} {py - r*.6:.0f} Z" fill="{col}" fill-opacity="{rnd.uniform(.5,.95):.2f}"/>')
            out.append(f'<path d="M{cx - 22*s:.0f} {dy + dw*.62:.0f} q{18*s:.0f} {-34*s:.0f} {44*s:.0f} {-10*s:.0f} q{-8*s:.0f} {22*s:.0f} {-44*s:.0f} {10*s:.0f}Z" fill="#0C1A31" fill-opacity=".85"/>')
        elif kind == 'kuai':  # 快线：几道青色的线从门里射出
            for k in range(7):
                a = math.radians(-160 + k * 23)
                L1, L2 = dw * .65, dw * (1.5 + .25 * (k % 3))
                out.append(f'<line x1="{cx + L1*math.cos(a):.0f}" y1="{dy + dw*.62 + L1*math.sin(a)*.7:.0f}" x2="{cx + L2*math.cos(a):.0f}" y2="{dy + dw*.62 + L2*math.sin(a)*.7:.0f}" stroke="{CYAN}" stroke-opacity=".75" stroke-width="{2.4*s:.1f}" stroke-linecap="round" stroke-dasharray="{26*s:.0f} {10*s:.0f}"/>')
            out.append(f'<circle cx="{cx:.0f}" cy="{dy + dw*.62:.0f}" r="{30*s:.0f}" fill="none" stroke="#0C1A31" stroke-width="{3*s:.1f}"/>')
            out.append(f'<ellipse cx="{cx:.0f}" cy="{dy + dw*.62:.0f}" rx="{52*s:.0f}" ry="{18*s:.0f}" fill="none" stroke="#0C1A31" stroke-width="{2*s:.1f}" transform="rotate(-28 {cx:.0f} {dy + dw*.62:.0f})"/>')
            out.append(f'<circle cx="{cx:.0f}" cy="{dy + dw*.62:.0f}" r="{7*s:.0f}" fill="#0C1A31"/>')
        else:                 # 一盏灯、一本摊开的书
            ly = dy + dw * .5
            out.append(f'<line x1="{cx:.0f}" y1="{dy + 8*s:.0f}" x2="{cx:.0f}" y2="{ly - 14*s:.0f}" stroke="#0C1A31" stroke-width="{2.4*s:.1f}"/>')
            out.append(f'<path d="M{cx - 22*s:.0f} {ly:.0f} L{cx - 12*s:.0f} {ly - 16*s:.0f} L{cx + 12*s:.0f} {ly - 16*s:.0f} L{cx + 22*s:.0f} {ly:.0f} Z" fill="#0C1A31"/>')
            by = base - 70 * s
            out.append(f'<path d="M{cx:.0f} {by:.0f} q{-26*s:.0f} {-12*s:.0f} {-52*s:.0f} {-4*s:.0f} l0 {34*s:.0f} q{26*s:.0f} {-8*s:.0f} {52*s:.0f} {4*s:.0f} q{26*s:.0f} {-12*s:.0f} {52*s:.0f} {-4*s:.0f} l0 {-34*s:.0f} q{-26*s:.0f} {-8*s:.0f} {-52*s:.0f} {4*s:.0f}Z" fill="#0C1A31" fill-opacity=".9"/>')
    # 门前弧路：三处光连起来
    (ax, _), (bx, _), (cx3, _) = doors
    out.append(f'<path d="M{ax:.0f} {base + 8*s:.0f} Q{(ax+bx)/2:.0f} {base + 70*s:.0f} {bx:.0f} {base + 8*s:.0f} Q{(bx+cx3)/2:.0f} {base + 70*s:.0f} {cx3:.0f} {base + 8*s:.0f}" fill="none" stroke="{GOLD2}" stroke-opacity=".7" stroke-width="{2*s:.1f}" stroke-dasharray="{6*s:.1f} {7*s:.1f}"/>')
    out.append(f'<path d="M{ax:.0f} {base + 8*s:.0f} Q{(ax+cx3)/2:.0f} {base + 150*s:.0f} {cx3:.0f} {base + 8*s:.0f}" fill="none" stroke="{CYAN}" stroke-opacity=".35" stroke-width="{1.4*s:.1f}" stroke-dasharray="{3*s:.1f} {8*s:.1f}"/>')
    out.append(f'<line x1="{x0 - 60*s:.0f}" y1="{base:.0f}" x2="{x1 + 60*s:.0f}" y2="{base:.0f}" stroke="{GOLD2}" stroke-opacity=".6" stroke-width="{1.6*s:.1f}"/>')
    # 夜空星点
    for _ in range(80):
        out.append(f'<circle cx="{rnd.uniform(W*.45, W):.0f}" cy="{rnd.uniform(H*.30, H*.52):.0f}" r="{rnd.uniform(.8, 2.2)*s:.1f}" fill="{CREAM}" fill-opacity="{rnd.uniform(.15, .5):.2f}"/>')
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
.doors{{font:400 {8.2*s:.1f}pt 'Noto Sans CJK SC';color:{CREAM};opacity:.78;letter-spacing:.18em;margin-top:{5*s:.1f}mm}}
.no{{position:absolute;right:{15*s:.1f}mm;top:{16*s:.1f}mm;font:400 {6.6*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.2em;text-align:right}}
</style></head><body><div class="pg">{svg}
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 492 号</div>
<div class="t"><div class="pre">慧店 · 第二卷</div><div class="big">一店三门</div>
<div class="sub">从作坊、实验室到书房，<br>每个人一生的知识发生</div><div class="rule"></div>
<div class="doors">达芬奇作坊 · 爱因斯坦实验室 · 天工开物书房</div></div>
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
<div class="q">一家店，三扇门：<br>作坊要奇，实验室要快，<br>书房要稳。</div><div class="by">——本书判词</div><div class="rule"></div>
<div class="bl"><p>十岁的小满画了一张会飞的药房，被大人一笑，第二天画就不见了；二十七岁的阿乐有个关于换电柜的怪念头，问机器，答得四平八稳，念头却凉了；六十一岁的周叔在药房干了三十四年，那一招说不清，退休以后就散了。</p>
<p>本书不问他是谁，只问他手上那件事卡在哪一步：一个刚冒头就被笑回去，一个冒了头却长不下去，一个长成了却传不出去。于是一家慧店开三扇门——达芬奇作坊把天马行空做成漫画、科幻、动画；爱因斯坦实验室把奇思几周跑成一套理念；天工开物书房把手艺写成书，再回写进技术流程。三扇门的成品，首先都给一个部落用。</p>
<p>每一扇门都配实现模型，每一个判断都写明怎样才算错。</p></div>
<div class="gold">每个人一生的知识发生，都有一扇门。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 492 号 · 七编四十二章 · 约 31 万字<br>定价 US$20.00</div>
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
