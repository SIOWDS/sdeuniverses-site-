#!/usr/bin/env python3
"""第 215 号封面与封底（照第 290 号的 220 系列版式）：藏青渐变底、细点阵、金色光晕与刻度环；
主图是楼顶一只木槽里正在长出来的豆苗，左边远处一座城门，一串金色脚印从城门走到苗前。

用法：python3 cover.py --fonts /home/claude/fonts --out /home/claude/mengzi/build
产物：cover-print.pdf / back-print.pdf（170×240）、cover-reader.pdf / back-reader.pdf（190×250）、
      cover.jpg / backcover.jpg（1004×1418，站上用）
"""
import argparse
import math
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0B1830', '#1B3158', '#142746'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#58BDCA', '#EFE8D6', '#9FB0C8'
ISBN = '979-8-90690-220-7'

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
    """主图：楼顶一只木槽，槽里一株豆苗正长出来；左边远处一座城门，一串金色脚印从城门走到苗前。
    （判语：他教的是找回心，他靠的是走出去；判词：长出来的，被记成了找回来的。）坐标按 0.1 mm。"""
    s = W / 1700
    cx, cy, r = W * 0.60, H * 0.53, 520 * s
    out = [rings(cx, cy, r).replace('{uid}', uid)]
    for (fx, fy, rr, op) in [(.82, .30, 3.2, .7), (.90, .44, 2.2, .5), (.74, .22, 2, .45), (.93, .62, 2.6, .4),
                             (.50, .34, 1.8, .35), (.68, .70, 2, .3), (.86, .72, 1.6, .35)]:
        out.append('<circle cx="%.0f" cy="%.0f" r="%.1f" fill="%s" fill-opacity="%.2f"/>' % (W * fx, H * fy, rr * s * 1.4, GOLD2, op))
    # 远处城门（左中）：城墙、门洞三个、城楼
    gx, gy, gw, gh = W * 0.10, H * 0.50, 330 * s, 110 * s
    gate = [f'<rect x="{gx:.0f}" y="{gy:.0f}" width="{gw:.0f}" height="{gh:.0f}" fill="{CREAM}" fill-opacity=".20"/>',
            f'<rect x="{gx:.0f}" y="{gy:.0f}" width="{gw:.0f}" height="{gh:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".75" stroke-width="{2*s:.1f}"/>']
    for k in range(5):
        bx = gx + k * gw / 5 + 6 * s
        gate.append(f'<rect x="{bx:.0f}" y="{gy-16*s:.0f}" width="{gw/5-12*s:.0f}" height="{16*s:.0f}" fill="{GOLD}" fill-opacity=".55"/>')
    for k, ww in enumerate((48, 64, 48)):
        ax = gx + gw * (0.2 + 0.3 * k)
        aw = ww * s
        gate.append(f'<path d="M{ax-aw/2:.0f} {gy+gh:.0f} L{ax-aw/2:.0f} {gy+gh-38*s:.0f} A{aw/2:.0f} {aw/2:.0f} 0 0 1 {ax+aw/2:.0f} {gy+gh-38*s:.0f} L{ax+aw/2:.0f} {gy+gh:.0f} Z" fill="{NAVY_TOP}"/>')
    tx, ty, tw = gx + gw / 2, gy - 16 * s, 150 * s
    gate.append(f'<rect x="{tx-tw/2+14*s:.0f}" y="{ty-62*s:.0f}" width="{tw-28*s:.0f}" height="{46*s:.0f}" fill="{CREAM}" fill-opacity=".22" stroke="{GOLD}" stroke-opacity=".7" stroke-width="{1.6*s:.1f}"/>')
    gate.append(f'<path d="M{tx-tw/2-20*s:.0f} {ty-58*s:.0f} Q{tx:.0f} {ty-104*s:.0f} {tx+tw/2+20*s:.0f} {ty-58*s:.0f} L{tx+tw/2-6*s:.0f} {ty-74*s:.0f} Q{tx:.0f} {ty-112*s:.0f} {tx-tw/2+6*s:.0f} {ty-74*s:.0f} Z" fill="{GOLD}" fill-opacity=".85"/>')
    out.append(''.join(gate))
    # 脚印：从城门中门洞出来，一路弯到木槽前（由小而大，近大远小）
    p0 = (gx + gw * 0.5, gy + gh + 10 * s)
    p1 = (gx + gw * 0.55, H * 0.70)
    p2 = (W * 0.20, H * 0.80)
    p3 = (W * 0.36, H * 0.86)
    for i in range(14):
        tt = i / 13
        x, y = bez(p0, p1, p2, p3, tt)
        x2, y2 = bez(p0, p1, p2, p3, min(tt + .01, 1))
        ang = math.degrees(math.atan2(y2 - y, x2 - x)) + 90
        sc = (0.45 + 0.75 * tt) * s
        off = (10 if i % 2 else -10) * sc
        out.append('<g transform="translate(%.1f %.1f) rotate(%.1f) translate(%.1f 0)">'
                   '<ellipse cx="0" cy="0" rx="%.1f" ry="%.1f" fill="%s" fill-opacity="%.2f"/>'
                   '<circle cx="0" cy="%.1f" r="%.1f" fill="%s" fill-opacity="%.2f"/></g>'
                   % (x, y, ang, off, 7 * sc, 12 * sc, GOLD2, .35 + .5 * tt, -17 * sc, 5 * sc, GOLD2, .35 + .5 * tt))
    # 木槽
    tx0, tx1, ty0, ty1 = W * 0.40, W * 0.88, H * 0.785, H * 0.845
    out.append(f'<rect x="{tx0:.0f}" y="{ty0:.0f}" width="{tx1-tx0:.0f}" height="{ty1-ty0:.0f}" fill="#6E5428"/>')
    out.append(f'<rect x="{tx0-10*s:.0f}" y="{ty0-12*s:.0f}" width="{tx1-tx0+20*s:.0f}" height="{14*s:.0f}" fill="{GOLD}"/>')
    for k in range(1, 4):
        yy = ty0 + (ty1 - ty0) * k / 4
        out.append(f'<line x1="{tx0:.0f}" y1="{yy:.0f}" x2="{tx1:.0f}" y2="{yy:.0f}" stroke="#4E3B1C" stroke-width="{1.6*s:.1f}"/>')
    out.append(f'<rect x="{tx0:.0f}" y="{ty0:.0f}" width="{tx1-tx0:.0f}" height="{ty1-ty0:.0f}" fill="none" stroke="#B89A5E" stroke-width="{2*s:.1f}"/>')
    # 土面上几颗小芽（同一槽，高矮不一）
    for fx, hh in ((.47, 40), (.53, 26), (.80, 34), (.85, 22)):
        sx = W * fx; sy = ty0 - 12 * s
        out.append(f'<path d="M{sx:.0f} {sy:.0f} C{sx+3*s:.0f} {sy-hh*s*.5:.0f} {sx-3*s:.0f} {sy-hh*s*.8:.0f} {sx:.0f} {sy-hh*s:.0f}" fill="none" stroke="{CYAN}" stroke-opacity=".8" stroke-width="{2.2*s:.1f}" stroke-linecap="round"/>')
        out.append(f'<ellipse cx="{sx-7*s:.0f}" cy="{sy-hh*s:.0f}" rx="{8*s:.0f}" ry="{4*s:.0f}" fill="{CYAN}" fill-opacity=".75"/>'
                   f'<ellipse cx="{sx+7*s:.0f}" cy="{sy-hh*s:.0f}" rx="{8*s:.0f}" ry="{4*s:.0f}" fill="{CYAN}" fill-opacity=".75"/>')
    # 主苗
    bx, by = W * 0.64, ty0 - 12 * s
    top = (W * 0.62, H * 0.47)
    stem = [bez((bx, by), (bx + 40 * s, by - 260 * s), (top[0] - 50 * s, top[1] + 260 * s), top, i / 60) for i in range(61)]
    out.append('<path d="%s" fill="%s"/>' % (tapered(stem, 16 * s, 6 * s, 1.0), CYAN))
    # 子叶（低处，奶白）
    cyy = by - 150 * s
    cxx = bez((bx, by), (bx + 40 * s, by - 260 * s), (top[0] - 50 * s, top[1] + 260 * s), top, .28)[0]
    out.append(f'<path d="M{cxx:.0f} {cyy:.0f} C{cxx-40*s:.0f} {cyy-50*s:.0f} {cxx-120*s:.0f} {cyy-30*s:.0f} {cxx-130*s:.0f} {cyy+5*s:.0f} C{cxx-90*s:.0f} {cyy+30*s:.0f} {cxx-30*s:.0f} {cyy+25*s:.0f} {cxx:.0f} {cyy:.0f} Z" fill="{CREAM}" fill-opacity=".92"/>')
    out.append(f'<path d="M{cxx:.0f} {cyy:.0f} C{cxx+40*s:.0f} {cyy-50*s:.0f} {cxx+120*s:.0f} {cyy-30*s:.0f} {cxx+130*s:.0f} {cyy+5*s:.0f} C{cxx+90*s:.0f} {cyy+30*s:.0f} {cxx+30*s:.0f} {cyy+25*s:.0f} {cxx:.0f} {cyy:.0f} Z" fill="{CREAM}" fill-opacity=".80"/>')
    # 真叶（高处，青色心形，带金色叶脉）
    lx, ly = top
    def leaf(dirx, size, rot):
        L = size * s
        return (f'<g transform="rotate({rot} {lx:.0f} {ly:.0f})">'
                f'<path d="M{lx:.0f} {ly:.0f} C{lx+dirx*L*.35:.0f} {ly-L*.55:.0f} {lx+dirx*L*.95:.0f} {ly-L*.55:.0f} {lx+dirx*L*1.1:.0f} {ly-L*.05:.0f} '
                f'C{lx+dirx*L*.85:.0f} {ly+L*.35:.0f} {lx+dirx*L*.35:.0f} {ly+L*.30:.0f} {lx:.0f} {ly:.0f} Z" fill="{CYAN}" fill-opacity=".88" stroke="{GOLD2}" stroke-width="{1.6*s:.1f}"/>'
                f'<path d="M{lx:.0f} {ly:.0f} Q{lx+dirx*L*.55:.0f} {ly-L*.12:.0f} {lx+dirx*L*1.0:.0f} {ly-L*.06:.0f}" fill="none" stroke="{GOLD2}" stroke-opacity=".8" stroke-width="{1.4*s:.1f}"/></g>')
    out.append(leaf(-1, 190, 18))
    out.append(leaf(1, 210, -14))
    # 顶芽：一点金
    out.append(f'<path d="M{lx:.0f} {ly-4*s:.0f} C{lx-14*s:.0f} {ly-40*s:.0f} {lx+4*s:.0f} {ly-70*s:.0f} {lx+10*s:.0f} {ly-78*s:.0f} C{lx+16*s:.0f} {ly-50*s:.0f} {lx+12*s:.0f} {ly-24*s:.0f} {lx:.0f} {ly-4*s:.0f} Z" fill="{GOLD2}"/>')
    # 一根细竹签与刻度（看得见的回写物）
    kx = W * 0.74
    out.append(f'<line x1="{kx:.0f}" y1="{ty0-12*s:.0f}" x2="{kx:.0f}" y2="{H*0.60:.0f}" stroke="{CREAM}" stroke-opacity=".55" stroke-width="{3*s:.1f}"/>')
    for k in range(6):
        yy = ty0 - 12 * s - k * (ty0 - 12 * s - H * 0.60) / 6
        out.append(f'<line x1="{kx:.0f}" y1="{yy:.0f}" x2="{kx+14*s:.0f}" y2="{yy:.0f}" stroke="{GOLD}" stroke-opacity=".7" stroke-width="{1.6*s:.1f}"/>')
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
    return f"""@font-face{{font-family:BS;src:url(file://{F}/NotoSerifSC-Regular.otf);font-weight:400}}
@font-face{{font-family:BS;src:url(file://{F}/NotoSerifSC-Bold.otf);font-weight:700}}
@font-face{{font-family:BH;src:url(file://{F}/NotoSansSC-Regular.otf);font-weight:400}}
@font-face{{font-family:BH;src:url(file://{F}/NotoSansSC-Bold.otf);font-weight:700}}"""


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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 215 号</div>
<div class="t"><div class="pre">普通人都能懂的</div><div class="big">孟子</div>
<div class="sub">一颗种子、一畦豆苗，<br>与 SDE 的解构</div><div class="rule"></div></div>
<div class="b"><div class="au">王德生　著</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div>
</div></body></html>"""


def back(Wmm, Hmm, F):
    W, H = Wmm * 10, Hmm * 10
    s = Wmm / 170
    # 右上小徽：环＋一株小苗
    ex, ey, er = W * 0.84, H * 0.085, 70 * s
    emb = f"""<circle cx="{ex:.0f}" cy="{ey:.0f}" r="{er:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".6" stroke-width="{2*s:.1f}"/>
<circle cx="{ex:.0f}" cy="{ey:.0f}" r="{er*1.18:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".22" stroke-width="{1.2*s:.1f}"/>
<path d="M{ex:.0f} {ey+40*s:.0f} C{ex+4*s:.0f} {ey+10*s:.0f} {ex-4*s:.0f} {ey-10*s:.0f} {ex:.0f} {ey-24*s:.0f}" fill="none" stroke="{CYAN}" stroke-width="{3*s:.1f}" stroke-linecap="round"/>
<path d="M{ex:.0f} {ey-20*s:.0f} C{ex-10*s:.0f} {ey-40*s:.0f} {ex-36*s:.0f} {ey-38*s:.0f} {ex-40*s:.0f} {ey-24*s:.0f} C{ex-28*s:.0f} {ey-14*s:.0f} {ex-12*s:.0f} {ey-14*s:.0f} {ex:.0f} {ey-20*s:.0f} Z" fill="{CYAN}" fill-opacity=".85"/>
<path d="M{ex:.0f} {ey-20*s:.0f} C{ex+10*s:.0f} {ey-40*s:.0f} {ex+36*s:.0f} {ey-38*s:.0f} {ex+40*s:.0f} {ey-24*s:.0f} C{ex+28*s:.0f} {ey-14*s:.0f} {ex+12*s:.0f} {ey-14*s:.0f} {ex:.0f} {ey-20*s:.0f} Z" fill="{CREAM}" fill-opacity=".85"/>"""
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
<div class="c"><div class="lab">一 句 话</div>
<div class="q">学问之道无他，<br>求其放心而已矣。</div><div class="by">——《孟子·告子上》</div><div class="rule"></div>
<div class="bl"><p>两千多年前，孟子说学问只有一件事：把丢了的心找回来。可同一本书里，他满嘴都是生长的话：线头、苗、萌芽、泉、火，一路扩而充之；他还讲过那个拔苗的宋国人。</p>
<p>这本书把两种话放在一起读。他看见了善会长，却把长成什么样，先写进了种子里。于是，长出来的，被记成了找回来的。而他自己，是在一次次被君王送出城门的路上长出来的。</p>
<p>然后回到一家人的日子里：楼顶的一畦豆苗，孩子的作业和手机，乡下的奶奶，汽修店里的两个徒弟。不拔，也不荒着。</p></div>
<div class="gold">苗是长出来的，不是找回来的。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 215 号 · 九编四十四章 · 约 21 万字<br>定价 US$20.00</div>
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
