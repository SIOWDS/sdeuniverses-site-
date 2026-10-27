#!/usr/bin/env python3
"""第 471 号《舍不得——悬在半空的那一步》（高鹏著，王德生指导；封面封底不写指导）封面与封底（220 系列版式，藏青底）：主图是金环里一只悬在袋口上方的旧搪瓷缸，环下三记「矛盾已发生 · 推到改位 · 结算成停」。
用法：python3 cover.py --fonts /home/claude/fonts --out <dir>
"""
import argparse
import math
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0C1A34', '#1B3158', '#16294A'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#7FA7C9', '#EFE8D6', '#A9B6C8'
ISBN = '979-8-90690-471-3'

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
    """主图（第 471 号）：金环里，一只白底蓝口沿、口沿磕掉一块瓷的旧搪瓷缸悬在半空，离下方张开的袋口还有「一尺」；
    来路是一道渐淡的金弧（手已伸出、越过改位线），缸与袋口之间一段虚线标出停住的距离；
    右侧一只虚线小缸，是还没立起来的「另一处」（迁载）。环下三记：「矛盾已发生 · 推到改位 · 结算成停」。"""
    import random
    rnd = random.Random(471)
    s = W / 1700
    cx, cy, r = W * 0.56, H * 0.60, W * 0.2765
    R = r * 0.66
    out = [f"""<defs>
 <radialGradient id="glow{uid}" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{GOLD2}" stop-opacity=".20"/>
  <stop offset=".55" stop-color="{GOLD}" stop-opacity=".05"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></radialGradient>
 <radialGradient id="lamp{uid}" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{WARM}" stop-opacity=".9"/>
  <stop offset=".35" stop-color="{GOLD2}" stop-opacity=".32"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></radialGradient>
 <linearGradient id="cup{uid}" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#CFC6B2"/><stop offset=".35" stop-color="#F7F1E3"/><stop offset=".7" stop-color="#EDE5D2"/><stop offset="1" stop-color="#B9AF9A"/></linearGradient>
 <linearGradient id="bag{uid}" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#070E1C"/><stop offset="1" stop-color="#0E1A30"/></linearGradient>
</defs>"""]
    out.append(rings(cx, cy, r).replace('{uid}', uid))
    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{R*1.05:.0f}" fill="url(#glow{uid})"/>')
    # 袋口：环内下方一张开的口
    bx, by, bw, bh = cx, cy + R * 0.62, R * 0.62, R * 0.15
    out.append(f'<path d="M {bx-bw:.0f} {by:.0f} Q {bx-bw*0.9:.0f} {by+R*0.42:.0f} {bx:.0f} {by+R*0.46:.0f} Q {bx+bw*0.9:.0f} {by+R*0.42:.0f} {bx+bw:.0f} {by:.0f} Z" fill="url(#bag{uid})" fill-opacity=".85"/>')
    out.append(f'<ellipse cx="{bx:.0f}" cy="{by:.0f}" rx="{bw:.0f}" ry="{bh:.0f}" fill="#050B17" stroke="{GOLD}" stroke-opacity=".55" stroke-width="{2.4*s:.1f}"/>')
    # 缸：悬在袋口上方
    w, h = R * 0.50, R * 0.50
    ux, uy = cx - R * 0.04, cy - R * 0.42          # 口沿中心
    top, bot = uy, uy + h
    body = (f'M {ux-w/2:.1f} {top:.1f} L {ux-w/2*0.92:.1f} {bot-14*s:.1f} Q {ux-w/2*0.90:.1f} {bot:.1f} {ux-w/2*0.70:.1f} {bot:.1f} '
            f'L {ux+w/2*0.70:.1f} {bot:.1f} Q {ux+w/2*0.90:.1f} {bot:.1f} {ux+w/2*0.92:.1f} {bot-14*s:.1f} L {ux+w/2:.1f} {top:.1f} Z')
    # 把手
    out.append(f'<path d="M {ux+w/2*0.97:.1f} {top+h*0.18:.1f} C {ux+w/2+w*0.42:.1f} {top+h*0.16:.1f} {ux+w/2+w*0.42:.1f} {top+h*0.80:.1f} {ux+w/2*0.93:.1f} {top+h*0.74:.1f}" '
               f'fill="none" stroke="#DCD3BF" stroke-width="{15*s:.1f}" stroke-linecap="round"/>')
    out.append(f'<path d="{body}" fill="url(#cup{uid})"/>')
    # 褪色的花
    fx, fy = ux - w * 0.06, top + h * 0.55
    for k in range(5):
        a = math.radians(k * 72 - 90)
        out.append(f'<ellipse cx="{fx + 15*s*math.cos(a):.1f}" cy="{fy + 15*s*math.sin(a):.1f}" rx="{10*s:.1f}" ry="{6*s:.1f}" transform="rotate({k*72} {fx + 15*s*math.cos(a):.1f} {fy + 15*s*math.sin(a):.1f})" fill="{ROSE}" fill-opacity=".38"/>')
    out.append(f'<circle cx="{fx:.1f}" cy="{fy:.1f}" r="{6*s:.1f}" fill="{GOLD}" fill-opacity=".5"/>')
    out.append(f'<path d="M {fx:.1f} {fy+18*s:.1f} Q {fx-6*s:.1f} {fy+44*s:.1f} {fx+14*s:.1f} {fy+60*s:.1f}" fill="none" stroke="#7E9A86" stroke-opacity=".45" stroke-width="{3*s:.1f}"/>')
    # 握久了磨出的一块光
    out.append(f'<path d="M {ux+w*0.20:.1f} {top+h*0.16:.1f} L {ux+w*0.26:.1f} {bot-h*0.18:.1f}" stroke="#FFFFFF" stroke-opacity=".55" stroke-width="{7*s:.1f}" stroke-linecap="round"/>')
    # 蓝口沿（椭圆）与口沿上磕掉的一块瓷
    out.append(f'<ellipse cx="{ux:.1f}" cy="{top:.1f}" rx="{w/2:.1f}" ry="{w*0.13:.1f}" fill="#22344F" stroke="#3E6FA8" stroke-width="{9*s:.1f}"/>')
    out.append(f'<ellipse cx="{ux:.1f}" cy="{top+3*s:.1f}" rx="{w/2*0.82:.1f}" ry="{w*0.085:.1f}" fill="#5A4A32" fill-opacity=".55"/>')
    chx, chy = ux - w * 0.30, top + w * 0.105
    out.append(f'<path d="M {chx-14*s:.1f} {chy-6*s:.1f} Q {chx-4*s:.1f} {chy+16*s:.1f} {chx+12*s:.1f} {chy+4*s:.1f} Q {chx+6*s:.1f} {chy-6*s:.1f} {chx-14*s:.1f} {chy-6*s:.1f} Z" fill="#141414"/>')
    out.append(f'<path d="M {chx-12*s:.1f} {chy+2*s:.1f} Q {chx-2*s:.1f} {chy+12*s:.1f} {chx+10*s:.1f} {chy+5*s:.1f}" fill="none" stroke="#A0522D" stroke-opacity=".8" stroke-width="{2.4*s:.1f}"/>')
    # 来路：一道从左上方伸来的渐淡金弧（手伸出的轨迹），止于缸身
    def P(deg, rr=R):
        a = math.radians(deg)
        return cx + rr * math.cos(a), cy + rr * math.sin(a)
    trail = [P(200 + 40 * i / 40, R * (1.02 - 0.20 * i / 40)) for i in range(41)]
    out.append(f'<path d="{tapered(trail, 6*s, 26*s, 1.3)}" fill="{GOLD2}" fill-opacity=".85"/>')
    tx, ty = trail[-1]
    out.append(f'<circle cx="{tx:.0f}" cy="{ty:.0f}" r="{70*s:.0f}" fill="url(#lamp{uid})" opacity=".55"/>')
    # 停住的那一尺：缸底到袋口之间的虚线与两道刻度
    gy0, gy1 = bot + 20 * s, by - bh - 16 * s
    out.append(f'<line x1="{ux:.0f}" y1="{gy0:.0f}" x2="{ux:.0f}" y2="{gy1:.0f}" stroke="{GOLD2}" stroke-opacity=".75" stroke-width="{2.6*s:.1f}" stroke-dasharray="{6*s:.1f} {7*s:.1f}"/>')
    for yy in (gy0, gy1):
        out.append(f'<line x1="{ux-18*s:.0f}" y1="{yy:.0f}" x2="{ux+18*s:.0f}" y2="{yy:.0f}" stroke="{GOLD2}" stroke-opacity=".75" stroke-width="{2.6*s:.1f}"/>')
    # 另一处：右侧一只虚线小缸，尚未立起
    gx, gy, gw = cx + R * 0.66, cy + R * 0.05, R * 0.22
    out.append(f'<path d="M {gx-gw/2:.1f} {gy:.1f} L {gx-gw/2*0.9:.1f} {gy+gw:.1f} L {gx+gw/2*0.9:.1f} {gy+gw:.1f} L {gx+gw/2:.1f} {gy:.1f}" fill="none" stroke="{CYAN}" stroke-opacity=".55" stroke-width="{2.6*s:.1f}" stroke-dasharray="{5*s:.1f} {6*s:.1f}"/>')
    out.append(f'<ellipse cx="{gx:.1f}" cy="{gy:.1f}" rx="{gw/2:.1f}" ry="{gw*0.13:.1f}" fill="none" stroke="{CYAN}" stroke-opacity=".55" stroke-width="{2.6*s:.1f}" stroke-dasharray="{5*s:.1f} {6*s:.1f}"/>')
    out.append(f'<path d="M {ux+w*0.95:.1f} {top+h*0.30:.1f} Q {gx-gw*0.2:.1f} {top-h*0.10:.1f} {gx:.1f} {gy-gw*0.25:.1f}" fill="none" stroke="{CYAN}" stroke-opacity=".38" stroke-width="{2*s:.1f}" stroke-dasharray="{3*s:.1f} {7*s:.1f}"/>')
    base = cy + r * 0.88
    xs = [cx - r * 0.52, cx, cx + r * 0.52]
    labs = ['矛盾已发生', '推到改位', '结算成停']
    out.append(f'<line x1="{cx - r*0.74:.0f}" y1="{base:.0f}" x2="{cx + r*0.74:.0f}" y2="{base:.0f}" stroke="{GOLD}" stroke-opacity=".45" stroke-width="{1.4*s:.1f}"/>')
    out.append(f'<circle cx="{xs[0]:.0f}" cy="{base:.0f}" r="{11*s:.0f}" fill="{GOLD2}"/>')
    out.append(f'<path d="M {xs[1]-14*s:.1f} {base+8*s:.1f} L {xs[1]:.1f} {base-10*s:.1f} L {xs[1]+14*s:.1f} {base+8*s:.1f}" fill="none" stroke="{CREAM}" stroke-width="{4*s:.1f}" stroke-linecap="round" stroke-linejoin="round"/>')
    out.append(f'<line x1="{xs[2]-7*s:.1f}" y1="{base-12*s:.1f}" x2="{xs[2]-7*s:.1f}" y2="{base+12*s:.1f}" stroke="{CYAN}" stroke-width="{4.5*s:.1f}" stroke-linecap="round"/>'
               f'<line x1="{xs[2]+7*s:.1f}" y1="{base-12*s:.1f}" x2="{xs[2]+7*s:.1f}" y2="{base+12*s:.1f}" stroke="{CYAN}" stroke-width="{4.5*s:.1f}" stroke-linecap="round"/>')
    for x, lab in zip(xs, labs):
        out.append(f'<text x="{x:.0f}" y="{base + 54*s:.0f}" font-size="{27*s:.0f}" text-anchor="middle" font-family="Noto Sans CJK SC" fill="{CREAM}" fill-opacity=".88" letter-spacing="{3*s:.0f}">{lab}</text>')
    for _ in range(70):
        out.append(f'<circle cx="{rnd.uniform(0, W):.0f}" cy="{rnd.uniform(H*0.28, H*0.40):.0f}" r="{rnd.uniform(.8, 2.2)*s:.1f}" fill="{CREAM}" fill-opacity="{rnd.uniform(.10, .40):.2f}"/>')
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
.ser{{font:400 {8.4*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.18em;margin-top:{1.6*s:.1f}mm}}
.b{{position:absolute;left:{17*s:.1f}mm;bottom:{17*s:.1f}mm}}
.au{{font:400 {12.5*s:.1f}pt 'Noto Serif CJK SC';color:{CREAM};letter-spacing:.28em}}
.ph{{font:700 {8.4*s:.1f}pt 'Noto Sans CJK SC';color:{GOLD2};letter-spacing:.3em;margin-top:{6*s:.1f}mm}}
.pe{{font:400 {6.6*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.08em;margin-top:{.8*s:.1f}mm}}
.no{{position:absolute;right:{15*s:.1f}mm;top:{16*s:.1f}mm;font:400 {6.6*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.2em;text-align:right}}
</style></head><body><div class="pg">{svg}
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 471 号</div>
<div class="t"><div class="pre">九问 · 三十六位对手</div><div class="big" style="font-size:{52*s:.1f}pt">舍不得</div>
<div class="sub">悬在半空的那一步</div><div class="ser">普通人都能明白的舍不得</div><div class="rule"></div></div>
<div class="b"><div class="au">高鹏　著</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div>
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
<div class="q">舍不得不是一种情感，<br>是一次悬停；<br>舍得不是割断，是迁载。</div><div class="by">——前言</div><div class="rule"></div>
<div class="bl"><p>收拾厨房，一只磕掉了一块瓷的旧搪瓷缸伸向垃圾袋，手停在半空。该扔的答案早就有了，手却停在答案之后。我们管这一停叫舍不得，再给它找个原因：念旧，心软，放不下。本书把习惯倒过来：先不问谁在乎，先问缸身上缠着的那一束东西，除了这只缸，别处还有没有地方能把它再走一遍。</p>
<p>当「改」会使那一束东西的可再发生处归零，这一改就结算成停，这是归零结算律。由此分出三种停：形上的、路上的、土上的；三种落在现实界、理念界、自我界，共九格；悬停有三个去向：走完，欠，冻。照片、日记、展柜只让它可再看；有人接着用、接着做、接着走动，才是可再发生。</p>
<p>九个问题，三十六位对手：卡尼曼与特沃斯基、塞勒、贝尔克、鲍尔比、库恩、利科、勒温、费斯廷格、库伯勒-罗斯、山下英子、近藤麻理惠、法兰克福、海德格尔、龙树、韩炳哲……每一位先说到最强，再指出他在哪一维失明，最后摆出一个只有本书推得出、也写明了怎样会被推翻的预测。</p></div>
<div class="gold">可再看，不等于可再发生。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 471 号 · 三编九章 · 约 26 万字<br>ISBN 979-8-90690-471-3 · 定价 US$20.00</div>
</div>
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
