#!/usr/bin/env python3
"""第 290 号封面与封底：藏青渐变底、细点阵、金色光晕与刻度环；主图是一支毛笔牵出一根金线，
线的尽头是一只风筝（教人松手的人，一直握着笔），地上一株毫末之芽，下有水纹。

用法：python3 cover.py --fonts /tmp/fonts --out /tmp/laozi-build
产物：cover-print.pdf / back-print.pdf（170×240）、cover-reader.pdf / back-reader.pdf（190×250）、
      cover.jpg / backcover.jpg（1004×1418，站上用）
"""
import argparse
import math
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0B1830', '#1B3158', '#142746'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#58BDCA', '#EFE8D6', '#9FB0C8'
ISBN = '979-8-90690-245-0'

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


def art(W, H, uid):
    """主图：毛笔—金线—风筝，毫末之芽，水纹。坐标按 0.1 mm。"""
    s = W / 1700  # 以 170 mm 宽为基准缩放
    cx, cy, r = W * 0.57, H * 0.525, 520 * s
    out = [rings(cx, cy, r).replace('{uid}', uid)]
    # 远处的小星点
    for (fx, fy, rr, op) in [(.80, .30, 3.2, .7), (.88, .44, 2.2, .5), (.72, .22, 2, .45), (.93, .60, 2.6, .4),
                             (.47, .36, 1.8, .35), (.64, .70, 2, .3), (.86, .74, 1.6, .35)]:
        out.append('<circle cx="%.0f" cy="%.0f" r="%.1f" fill="%s" fill-opacity="%.2f"/>' % (W * fx, H * fy, rr * s * 1.4, GOLD2, op))
    # 风筝
    kx, ky = W * 0.70, H * 0.395
    top, side, bot = 170 * s, 118 * s, 250 * s
    tilt = -14
    kite = f"""
<g transform="rotate({tilt} {kx:.0f} {ky:.0f})">
 <path d="M{kx:.0f} {ky-top:.0f} L{kx+side:.0f} {ky:.0f} L{kx:.0f} {ky+bot:.0f} L{kx-side:.0f} {ky:.0f} Z" fill="url(#kite{uid})" stroke="{GOLD2}" stroke-width="{3.2*s:.1f}"/>
 <path d="M{kx:.0f} {ky-top:.0f} L{kx+side:.0f} {ky:.0f} L{kx:.0f} {ky:.0f} Z" fill="{NAVY_MID}" fill-opacity=".16"/>
 <path d="M{kx:.0f} {ky:.0f} L{kx-side:.0f} {ky:.0f} L{kx:.0f} {ky+bot:.0f} Z" fill="{NAVY_MID}" fill-opacity=".12"/>
 <line x1="{kx:.0f}" y1="{ky-top:.0f}" x2="{kx:.0f}" y2="{ky+bot:.0f}" stroke="#8A6A2E" stroke-width="{2.2*s:.1f}"/>
 <path d="M{kx-side:.0f} {ky:.0f} Q{kx:.0f} {ky-40*s:.0f} {kx+side:.0f} {ky:.0f}" fill="none" stroke="#8A6A2E" stroke-width="{2.2*s:.1f}"/>
 <circle cx="{kx:.0f}" cy="{ky:.0f}" r="{8*s:.1f}" fill="{NAVY_TOP}" stroke="{GOLD2}" stroke-width="{1.6*s:.1f}"/>
</g>"""
    out.append(kite)
    # 风筝尾巴：两条 S 形飘带，缀小蝴蝶结
    rad = math.radians(tilt)
    tx, ty = kx - bot * math.sin(rad), ky + bot * math.cos(rad)
    tails = []
    for k, (col, dx, amp, op) in enumerate([(CREAM, 1.0, 1.0, .85), (CYAN, 0.8, 1.25, .75)]):
        p0 = (tx, ty); p3 = (tx + 330 * s * dx, ty + 470 * s)
        p1 = (tx + 160 * s * amp, ty + 120 * s); p2 = (tx - 60 * s * amp, ty + 330 * s)
        tails.append('<path d="M%.0f %.0f C%.0f %.0f %.0f %.0f %.0f %.0f" fill="none" stroke="%s" stroke-opacity="%.2f" stroke-width="%.1f" stroke-linecap="round"/>'
                     % (*p0, *p1, *p2, *p3, col, op, (2.6 - k * .6) * s))
        for t in (.25, .5, .75, .95):
            bx, by = bez(p0, p1, p2, p3, t)
            w = (16 - 7 * t) * s
            tails.append('<path d="M%.1f %.1f l%.1f %.1f l0 %.1f Z M%.1f %.1f l%.1f %.1f l0 %.1f Z" fill="%s" fill-opacity="%.2f"/>'
                         % (bx, by, -w, -w * .55, w * 1.1, bx, by, w, -w * .55, w * 1.1, col if k == 0 else CYAN, op))
    out.append(''.join(tails))
    # 毛笔
    bx0, by0 = W * 0.235, H * 0.585      # 笔杆顶端
    ang = math.radians(12)               # 向右下略倾
    Lh = 380 * s
    hx, hy = bx0 + Lh * math.sin(ang), by0 + Lh * math.cos(ang)   # 笔杆底端（笔斗）
    wd = 25 * s
    ux, uy = math.cos(ang), -math.sin(ang)
    handle = 'M%.1f %.1f L%.1f %.1f L%.1f %.1f L%.1f %.1f Z' % (
        bx0 - ux * wd / 2, by0 - uy * wd / 2, bx0 + ux * wd / 2, by0 + uy * wd / 2,
        hx + ux * wd / 2, hy + uy * wd / 2, hx - ux * wd / 2, hy - uy * wd / 2)
    brush = [f'<path d="{handle}" fill="url(#handle{uid})" stroke="#8A6A2E" stroke-width="{1.2*s:.1f}"/>']
    # 竹节
    for t in (.2, .55):
        nx_, ny_ = bx0 + (hx - bx0) * t, by0 + (hy - by0) * t
        brush.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#8A6A2E" stroke-width="%.1f"/>'
                     % (nx_ - ux * wd / 2, ny_ - uy * wd / 2, nx_ + ux * wd / 2, ny_ + uy * wd / 2, 2 * s))
    # 挂绳圈
    brush.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="%s" stroke-width="%.1f"/>' % (
        bx0 - math.sin(ang) * 14 * s, by0 - math.cos(ang) * 14 * s, 9 * s, GOLD, 1.8 * s))
    # 笔斗（金箍）
    fx2, fy2 = hx + 34 * s * math.sin(ang), hy + 34 * s * math.cos(ang)
    wf = 33 * s
    brush.append('<path d="M%.1f %.1f L%.1f %.1f L%.1f %.1f L%.1f %.1f Z" fill="%s"/>' % (
        hx - ux * wd / 2, hy - uy * wd / 2, hx + ux * wd / 2, hy + uy * wd / 2,
        fx2 + ux * wf / 2, fy2 + uy * wf / 2, fx2 - ux * wf / 2, fy2 - uy * wf / 2, GOLD))
    # 笔头：水滴形，墨色，金边
    tipx, tipy = fx2 + 150 * s * math.sin(ang), fy2 + 150 * s * math.cos(ang)
    c1 = (fx2 + ux * wf * .9 + 40 * s * math.sin(ang), fy2 + uy * wf * .9 + 40 * s * math.cos(ang))
    c2 = (fx2 - ux * wf * .9 + 40 * s * math.sin(ang), fy2 - uy * wf * .9 + 40 * s * math.cos(ang))
    brush.append('<path d="M%.1f %.1f Q%.1f %.1f %.1f %.1f Q%.1f %.1f %.1f %.1f Z" fill="#0A1224" stroke="%s" stroke-width="%.1f"/>' % (
        fx2 + ux * wf / 2, fy2 + uy * wf / 2, c1[0], c1[1], tipx, tipy, c2[0], c2[1], fx2 - ux * wf / 2, fy2 - uy * wf / 2, GOLD2, 1.8 * s))
    brush.append('<path d="M%.1f %.1f Q%.1f %.1f %.1f %.1f" fill="none" stroke="%s" stroke-opacity=".6" stroke-width="%.1f"/>' % (
        fx2 + ux * wf * .15, fy2 + uy * wf * .15, c1[0] - ux * wf * .3, c1[1] - uy * wf * .3, tipx, tipy, GOLD, 1.2 * s))
    out.append(''.join(brush))
    # 从笔尖出来的一笔：先在纸上一顿一转（粗），再细成金线，一路升到风筝
    k_ang = math.radians(tilt)
    bridle = (kx, ky)   # 风筝线系在十字中心
    p0 = (tipx, tipy)
    p1 = (tipx + 60 * s, tipy + 95 * s)
    p2 = (tipx + 250 * s, tipy + 60 * s)
    p3 = (tipx + 300 * s, tipy - 30 * s)
    stroke_pts = [bez(p0, p1, p2, p3, i / 60) for i in range(61)]
    out.append('<path d="%s" fill="%s" fill-opacity=".92"/>' % (tapered(stroke_pts, 26 * s, 3.2 * s, 1.3), GOLD))
    q0 = p3
    q1 = (p3[0] + 150 * s, p3[1] - 260 * s)
    q2 = (bridle[0] - 250 * s, bridle[1] + 330 * s)
    q3 = bridle
    line_pts = [bez(q0, q1, q2, q3, i / 80) for i in range(81)]
    out.append('<path d="%s" fill="url(#line%s)"/>' % (tapered(line_pts, 3.4 * s, 1.5 * s, 1.0), uid))
    # 毫末之芽
    sx, sy = W * 0.63, H * 0.852
    out.append(f"""<g stroke="{CYAN}" stroke-width="{2.4*s:.1f}" fill="none" stroke-linecap="round">
 <path d="M{sx:.0f} {sy:.0f} C{sx+4*s:.0f} {sy-30*s:.0f} {sx-6*s:.0f} {sy-52*s:.0f} {sx+2*s:.0f} {sy-70*s:.0f}"/></g>
 <path d="M{sx+2*s:.0f} {sy-66*s:.0f} C{sx+34*s:.0f} {sy-92*s:.0f} {sx+58*s:.0f} {sy-74*s:.0f} {sx+62*s:.0f} {sy-60*s:.0f} C{sx+40*s:.0f} {sy-50*s:.0f} {sx+18*s:.0f} {sy-52*s:.0f} {sx+2*s:.0f} {sy-66*s:.0f} Z" fill="{CYAN}" fill-opacity=".85"/>
 <path d="M{sx:.0f} {sy-52*s:.0f} C{sx-26*s:.0f} {sy-72*s:.0f} {sx-48*s:.0f} {sy-60*s:.0f} {sx-52*s:.0f} {sy-48*s:.0f} C{sx-34*s:.0f} {sy-40*s:.0f} {sx-14*s:.0f} {sy-42*s:.0f} {sx:.0f} {sy-52*s:.0f} Z" fill="{CYAN}" fill-opacity=".6"/>
 <ellipse cx="{sx:.0f}" cy="{sy+3*s:.0f}" rx="{46*s:.0f}" ry="{5*s:.0f}" fill="{GOLD}" fill-opacity=".25"/>""")
    # 水纹
    waves = []
    for k, (yy, op, amp) in enumerate([(.885, .30, 10), (.905, .20, 8), (.925, .13, 6)]):
        y0 = H * yy
        d = 'M0 %.0f' % y0
        n = 9
        for i in range(n):
            x1 = W * (i + .5) / n; x2 = W * (i + 1) / n
            d += ' Q%.0f %.0f %.0f %.0f' % (x1, y0 + (amp if i % 2 else -amp) * s * 2, x2, y0)
        waves.append('<path d="%s" fill="none" stroke="%s" stroke-opacity="%.2f" stroke-width="%.1f"/>' % (d, CYAN if k % 2 == 0 else GOLD, op, 1.8 * s))
    out.append(''.join(waves))
    return ''.join(out)


def barcode(x, y, s):
    d, bits = ean13_bits(ISBN)
    mw = 3.3 * s  # 模块宽
    h = 190 * s
    rects = []
    for i, b in enumerate(bits):
        if b == '1':
            guard = i < 3 or 45 <= i < 50 or i >= 92
            rects.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#111"/>' % (x + 22 * s + i * mw, y + 40 * s, mw + .2, h + (18 * s if guard else 0)))
    bw = 95 * mw + 44 * s
    txt = (f'<text x="{x + bw/2:.0f}" y="{y + 30*s:.0f}" font-size="{19*s:.0f}" text-anchor="middle" font-family="BH" fill="#111">ISBN {ISBN}</text>'
           f'<text x="{x + 8*s:.0f}" y="{y + 40*s + h + 36*s:.0f}" font-size="{26*s:.0f}" font-family="BS" fill="#111">{d[0]}</text>'
           f'<text x="{x + 22*s + 3*mw + 21*mw:.0f}" y="{y + 40*s + h + 36*s:.0f}" font-size="{26*s:.0f}" text-anchor="middle" letter-spacing="{9*s:.0f}" font-family="BS" fill="#111">{d[1:7]}</text>'
           f'<text x="{x + 22*s + 50*mw + 21*mw:.0f}" y="{y + 40*s + h + 36*s:.0f}" font-size="{26*s:.0f}" text-anchor="middle" letter-spacing="{9*s:.0f}" font-family="BS" fill="#111">{d[7:]}</text>')
    return (f'<rect x="{x:.0f}" y="{y:.0f}" width="{bw:.0f}" height="{h + 110*s:.0f}" fill="#fff"/>' + ''.join(rects) + txt), bw


def fontface(F):
    return f"""@font-face{{font-family:BS;src:url(file://{F}/NotoSerifSC-Regular.ttf);font-weight:400}}
@font-face{{font-family:BS;src:url(file://{F}/NotoSerifSC-Bold.ttf);font-weight:700}}
@font-face{{font-family:BH;src:url(file://{F}/NotoSansSC-Regular.ttf);font-weight:400}}
@font-face{{font-family:BH;src:url(file://{F}/NotoSansSC-Bold.ttf);font-weight:700}}"""


def front(Wmm, Hmm, F):
    W, H = Wmm * 10, Hmm * 10
    s = Wmm / 170
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{Wmm}mm" height="{Hmm}mm">{background(W, H, "f")}{art(W, H, "f")}</svg>'
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{fontface(F)}
@page{{size:{Wmm}mm {Hmm}mm;margin:0}} body{{margin:0}}
.pg{{position:relative;width:{Wmm}mm;height:{Hmm}mm;overflow:hidden}}
.pg svg{{position:absolute;left:0;top:0}}
.t{{position:absolute;left:{17*s:.1f}mm;top:{22*s:.1f}mm;color:{CREAM}}}
.pre{{font:400 {11.5*s:.1f}pt BS;letter-spacing:.32em;color:{CREAM};opacity:.92}}
.big{{font:700 {66*s:.1f}pt/1.15 BS;letter-spacing:.1em;color:#F7F1E3;margin:{2*s:.1f}mm 0 {3*s:.1f}mm {-1*s:.1f}mm}}
.sub{{font:400 {10.6*s:.1f}pt/1.75 BS;color:{GOLD2};letter-spacing:.04em}}
.rule{{width:{16*s:.1f}mm;border-top:.9pt solid {GOLD};margin-top:{5*s:.1f}mm}}
.b{{position:absolute;left:{17*s:.1f}mm;bottom:{17*s:.1f}mm}}
.au{{font:400 {12.5*s:.1f}pt BS;color:{CREAM};letter-spacing:.28em}}
.ph{{font:700 {8.4*s:.1f}pt BH;color:{GOLD2};letter-spacing:.3em;margin-top:{6*s:.1f}mm}}
.pe{{font:400 {6.6*s:.1f}pt BH;color:{DIM};letter-spacing:.08em;margin-top:{.8*s:.1f}mm}}
.no{{position:absolute;right:{15*s:.1f}mm;top:{16*s:.1f}mm;font:400 {6.6*s:.1f}pt BH;color:{DIM};letter-spacing:.2em;text-align:right}}
</style></head><body><div class="pg">{svg}
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 290 号</div>
<div class="t"><div class="pre">普通人都能懂的</div><div class="big">老子</div>
<div class="sub">一个劝人不言的人、五千个字，<br>与 SDE 的解构</div><div class="rule"></div></div>
<div class="b"><div class="au">王德生　著</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div>
</div></body></html>"""


def back(Wmm, Hmm, F):
    W, H = Wmm * 10, Hmm * 10
    s = Wmm / 170
    # 右上小徽：环＋小风筝
    ex, ey, er = W * 0.84, H * 0.085, 70 * s
    emb = f"""<circle cx="{ex:.0f}" cy="{ey:.0f}" r="{er:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".6" stroke-width="{2*s:.1f}"/>
<circle cx="{ex:.0f}" cy="{ey:.0f}" r="{er*1.18:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".22" stroke-width="{1.2*s:.1f}"/>
<path d="M{ex:.0f} {ey-34*s:.0f} L{ex+22*s:.0f} {ey-4*s:.0f} L{ex:.0f} {ey+40*s:.0f} L{ex-22*s:.0f} {ey-4*s:.0f} Z" fill="{CREAM}" fill-opacity=".85" stroke="{GOLD2}" stroke-width="{1.6*s:.1f}"/>
<path d="M{ex:.0f} {ey+40*s:.0f} C{ex+18*s:.0f} {ey+58*s:.0f} {ex-10*s:.0f} {ey+70*s:.0f} {ex+8*s:.0f} {ey+86*s:.0f}" fill="none" stroke="{CYAN}" stroke-opacity=".7" stroke-width="{1.6*s:.1f}"/>"""
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
.lab{{font:700 {7.4*s:.1f}pt BH;color:{GOLD2};letter-spacing:.5em}}
.q{{font:700 {15.5*s:.1f}pt/1.75 BS;color:#F7F1E3;margin:{4*s:.1f}mm 0 {2*s:.1f}mm;letter-spacing:.04em}}
.by{{font:400 {8.2*s:.1f}pt BS;color:{DIM}}}
.rule{{width:{14*s:.1f}mm;border-top:.9pt solid {GOLD};margin:{7*s:.1f}mm 0 {6*s:.1f}mm}}
.bl p{{font:400 {8.8*s:.1f}pt/1.9 BS;color:{CREAM};opacity:.9;margin:0 0 {2.6*s:.1f}mm;text-align:justify}}
.gold{{font:700 {10.5*s:.1f}pt BS;color:{GOLD2};margin-top:{6*s:.1f}mm;letter-spacing:.06em}}
.f{{position:absolute;left:{17*s:.1f}mm;bottom:{17*s:.1f}mm;font:400 {7.2*s:.1f}pt/1.85 BH;color:{DIM}}}
.f b{{color:{CREAM};font-weight:700;letter-spacing:.12em}}
</style></head><body><div class="pg">{svg}
<div class="c"><div class="lab">一 个 问 题</div>
<div class="q">若道老君是知者，<br>缘何自著五千文。</div><div class="by">——白居易《读老子》</div><div class="rule"></div>
<div class="bl"><p>一千二百年前，白居易读完《道德经》，笑了老子一句：说「知者不言」的人，为什么自己写了五千字？</p>
<p>本书认真对待这句玩笑。它把《道德经》当成一个人的一生来读：从郭店竹简到王弼注本，一本教人「日损」的书怎样越传越长；一个骂了一辈子「强」的人，怎样在最要紧的两句话里，给自己写下了「强」。</p>
<p>然后，把找回来的东西，用到孩子、身体和工作上：什么时候该松手，什么时候该在事情还小的时候，先伸手。</p></div>
<div class="gold">风不是你的，可你得跑。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 290 号 · 八编四十九章 · 约 20 万字<br>定价 US$20.00</div>
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
