#!/usr/bin/env python3
"""第 527 号《子本打造法》（王德生著）封面与封底（工具链承自第 431 号，藏青底、金青奶白三色，220 系列版式）：主图是一本翻开的母本垂下九道线，落成九枚各不相同的子本，再以虚线回流母本。
用法：python3 cover.py --fonts /home/claude/fonts --out <dir>
"""
import argparse
import math
import os
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0C1A34', '#1B3158', '#16294A'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#7FA7C9', '#EFE8D6', '#A9B6C8'
ISBN = '979-8-90690-527-7'
WAN = os.environ.get('WAN', '20')

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


def foot(x, y, k, rot, fill, op, uid):
    """一枚脚印：前掌、足弓、脚跟与五个趾点；整枚一个透明度，叠起来时重合处才显出来。"""
    toes = [(-36, -136, 13), (-13, -150, 12), (10, -152, 11), (31, -144, 10), (48, -128, 9)]
    t = ''.join('<circle cx="%d" cy="%d" r="%d"/>' % c for c in toes)
    return (f'<g transform="translate({x:.0f} {y:.0f}) rotate({rot}) scale({k:.3f})" fill="{fill}" opacity="{op}">'
            f'<path d="M -50 -66 C -52 -112 -22 -124 8 -122 C 40 -120 58 -96 54 -56 C 50 -24 34 -8 30 18 C 28 40 40 58 40 80 C 40 114 18 130 -6 130 C -32 130 -42 108 -38 78 C -34 52 -26 36 -32 12 C -38 -10 -48 -34 -50 -66 Z"/>{t}</g>')


def art(W, H, uid):
    """主图（第 527 号）：上方一枚金色母本（翻开的书），九道细线垂下，落到下方九枚子本——
    每枚子本是一个小环，环心的点位置、颜色各不相同（同一个判断，在不同的人身上长出不同的样子）；
    每枚子本又有一道青色虚线弯回母本（回流）。环下标「母本 · 九问 · 子本」。"""
    import random
    rnd = random.Random(527)
    s = W / 1700
    cx, cy, r = W * 0.55, H * 0.60, 470 * s
    out = [f"""<defs>
 <radialGradient id="glow{uid}" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{GOLD2}" stop-opacity=".24"/>
  <stop offset=".5" stop-color="{GOLD}" stop-opacity=".07"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></radialGradient>
 <linearGradient id="page{uid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{GOLD2}"/><stop offset="1" stop-color="{GOLD}"/></linearGradient>
</defs>"""]
    out.append(rings(cx, cy, r).replace('{uid}', uid))
    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r*0.95:.0f}" fill="url(#glow{uid})"/>')
    bx, by = cx, cy - 300 * s
    bw, bh = 150 * s, 104 * s
    for sg, op in ((-1, 1), (1, .86)):
        out.append(f'<path d="M {bx:.0f} {by-bh/2+10*s:.0f} C {bx+sg*50*s:.0f} {by-bh/2-14*s:.0f} {bx+sg*(bw-20*s):.0f} {by-bh/2-14*s:.0f} {bx+sg*bw:.0f} {by-bh/2:.0f} '
                   f'L {bx+sg*bw:.0f} {by+bh/2:.0f} C {bx+sg*(bw-20*s):.0f} {by+bh/2-14*s:.0f} {bx+sg*50*s:.0f} {by+bh/2-14*s:.0f} {bx:.0f} {by+bh/2+10*s:.0f} Z" fill="url(#page{uid})" fill-opacity="{op}"/>')
    out.append(f'<line x1="{bx:.0f}" y1="{by-bh/2+10*s:.0f}" x2="{bx:.0f}" y2="{by+bh/2+10*s:.0f}" stroke="{NAVY_MID}" stroke-width="{3*s:.1f}"/>')
    for k in range(3):
        yy = by - bh / 4 + k * bh / 4
        for sg in (-1, 1):
            out.append(f'<line x1="{bx+sg*28*s:.0f}" y1="{yy:.0f}" x2="{bx+sg*(bw-30*s):.0f}" y2="{yy-6*s:.0f}" stroke="{NAVY_MID}" stroke-opacity=".55" stroke-width="{2.2*s:.1f}"/>')
    n = 9
    span = 820 * s
    ky = cy + 130 * s
    kids = []
    for i in range(n):
        x = cx - span / 2 + span * i / (n - 1)
        y = ky + (40 * s if i % 2 else 0) + rnd.uniform(-14, 14) * s
        kids.append((x, y))
    cols = [CYAN, GOLD2, CREAM]
    for i, (x, y) in enumerate(kids):
        sx = bx + (i - 4) * 26 * s
        sy = by + bh / 2 + 12 * s
        mid = (sx + (x - sx) * .3, sy + 150 * s)
        out.append(f'<path d="M {sx:.0f} {sy:.0f} C {mid[0]:.0f} {mid[1]:.0f} {x:.0f} {y-200*s:.0f} {x:.0f} {y-38*s:.0f}" fill="none" stroke="{CREAM}" stroke-opacity=".5" stroke-width="{2.2*s:.1f}"/>')
        if i in (0, 2, 6, 8):
            side = -1 if x < cx else 1
            rx = x + side * 90 * s
            out.append(f'<path d="M {x+side*34*s:.0f} {y:.0f} C {rx:.0f} {y-160*s:.0f} {bx+side*(bw+110*s):.0f} {by+40*s:.0f} {bx+side*(bw+4*s):.0f} {by:.0f}" fill="none" stroke="{CYAN}" stroke-opacity=".38" stroke-width="{1.6*s:.1f}" stroke-dasharray="{6*s:.0f} {9*s:.0f}"/>')
    for i, (x, y) in enumerate(kids):
        rr = 34 * s
        c = cols[i % 3]
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rr:.0f}" fill="{NAVY_LOW}" stroke="{c}" stroke-opacity=".9" stroke-width="{2.4*s:.1f}"/>')
        a = rnd.uniform(0, 2 * math.pi); d = rnd.uniform(0, 14) * s
        out.append(f'<circle cx="{x+d*math.cos(a):.0f}" cy="{y+d*math.sin(a):.0f}" r="{rnd.uniform(8, 14)*s:.1f}" fill="{c}" fill-opacity="{rnd.uniform(.6, 1):.2f}"/>')
    base = cy + r * 0.86
    for (x, lab, cap, col) in [(cx - 330 * s, '母本', '给出判断', GOLD2), (cx, '九问', '找回 D 与 E', CREAM), (cx + 330 * s, '子本', '再长一遍', CYAN)]:
        out.append(f'<circle cx="{x:.0f}" cy="{base:.0f}" r="{9*s:.0f}" fill="{col}"/>')
        out.append(f'<text x="{x:.0f}" y="{base + 56*s:.0f}" font-size="{40*s:.0f}" text-anchor="middle" font-family="Noto Serif CJK SC" font-weight="700" fill="{CREAM}" fill-opacity=".92" letter-spacing="{6*s:.0f}">{lab}</text>')
        out.append(f'<text x="{x:.0f}" y="{base + 104*s:.0f}" font-size="{26*s:.0f}" text-anchor="middle" font-family="Noto Sans CJK SC" fill="{GOLD2}" fill-opacity=".85" letter-spacing="{4*s:.0f}">{cap}</text>')
    out.append(f'<line x1="{cx - 410*s:.0f}" y1="{base:.0f}" x2="{cx + 410*s:.0f}" y2="{base:.0f}" stroke="{GOLD}" stroke-opacity=".45" stroke-width="{1.4*s:.1f}"/>')
    for _ in range(60):
        out.append(f'<circle cx="{rnd.uniform(0, W):.0f}" cy="{rnd.uniform(H*0.30, H*0.40):.0f}" r="{rnd.uniform(.8, 2.2)*s:.1f}" fill="{CREAM}" fill-opacity="{rnd.uniform(.12, .45):.2f}"/>')
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 527 号</div>
<div class="t"><div class="pre">母本 · 九问 · 子本</div><div class="big" style="font-size:{46*s:.1f}pt">子本打造法</div>
<div class="sub">从母本到每个人的学术专著</div><div class="rule"></div></div>
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
<div class="q">母本给出判断，<br>子本找回生成这些判断的 D 与 E——<br>同一个判断，在你身上再长一遍。</div><div class="by">——导论、第 3 章、结语</div><div class="rule"></div>
<div class="bl"><p>AI 让一本书几十分钟就能写完。可是批量生成的书多半没有母本，只有一个人人可取的套路，每一本都是同一个模板换了皮：这是复本。只把母本的案例换成读者的、走向原封不动，也不算数：这是翻译。</p>
<p>子本是另一种书。它从一部学术母本出发，先找出九个核心抽象判断，再应用成读者能对照、能反驳的九个具体判断，然后用九问去追问：在你自己的生活里，是什么样的 D 与 E 生成了这个判断。答案由读者自己说出来，子本的大纲和整本书都从这些回答里长出来。</p>
<p>三编九章，讲子本是什么、怎样发生、怎样成书与生长，写明六道工序、四道质检闸门和三条禁令，也写明在什么情况下这套做法算错。</p></div>
<div class="gold">这是你的书吗？</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 527 号 · 三编九章 · 约 {WAN} 万字<br>ISBN 979-8-90690-527-7 · 定价 US$20.00</div>
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
