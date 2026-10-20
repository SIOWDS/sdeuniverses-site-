#!/usr/bin/env python3
"""第 503 号《爱的箴言新解》封面与封底（由第 488 号改来，220 系列版式）：主图是一颗由场线织成的心——心形场线是场（势能），心里被金线连起的光点是定态（内能），点间弹起的虚线弧是波（动能），心尖下一张绷紧的网，心顶一颗暖金色的实底。
用法：python3 cover.py --fonts /home/claude/fonts --out <dir>
"""
import argparse
import math
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0B1830', '#1B3158', '#142746'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#58BDCA', '#EFE8D6', '#9FB0C8'
ISBN = '979-8-90690-175-0'

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
    """主图：一颗由场线织成的心——一圈圈心形场线（场·势能），心里许多站住的小光点（定态·内能）
    被金线连起来，点与点之间有弹起的虚线弧（波·动能）；心尖下是一张绷紧的网，心顶上一颗金色的实底。
    四周飘着暖色的小光点与花瓣，整幅画是暖的。"""
    import random
    rnd = random.Random(503)
    s = W / 1700
    cx, cy = W * 0.56, H * 0.60
    k = 27 * s
    out = [f"""<defs>
 <radialGradient id="warm{uid}" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{ROSE2}" stop-opacity=".75"/>
  <stop offset=".35" stop-color="{ROSE}" stop-opacity=".34"/><stop offset=".7" stop-color="{GOLD}" stop-opacity=".08"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></radialGradient>
 <radialGradient id="core{uid}" cx=".5" cy=".45" r=".55"><stop offset="0" stop-color="#FFF6E6"/><stop offset=".55" stop-color="{WARM}"/><stop offset="1" stop-color="{GOLD}"/></radialGradient>
 <radialGradient id="dot{uid}" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#FFF4E8" stop-opacity="1"/><stop offset="1" stop-color="{ROSE}" stop-opacity="0"/></radialGradient>
</defs>""",
           f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{760*s:.0f}" fill="url(#warm{uid})"/>']
    # 心形场线：由内到外
    for i, (sc, op, wd, col) in enumerate([(0.42, .30, 1.2, ROSE2), (0.58, .38, 1.4, ROSE), (0.72, .45, 1.6, GOLD2),
                                          (0.86, .65, 2.2, GOLD2), (1.0, .95, 4.2, WARM), (1.13, .32, 1.4, GOLD), (1.27, .16, 1.1, GOLD)]):
        pts = heart_pts(cx, cy, k * sc)
        d = 'M' + ' L'.join('%.1f %.1f' % p for p in pts) + ' Z'
        if i == 4:
            out.append(f'<path d="{d}" fill="{ROSE}" fill-opacity=".10"/>')
        dash = '' if i in (3, 4) else f' stroke-dasharray="{2*s:.1f} {9*s:.1f}"' if i > 4 else ''
        out.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-opacity="{op}" stroke-width="{wd*s:.1f}" stroke-linecap="round"{dash}/>')
    # 心里的点（定态）与金线（连接）
    nodes = []
    big = heart_pts(cx, cy, k * 0.80, 400)
    xs = [p[0] for p in big]; ys = [p[1] for p in big]
    def inside(x, y):
        # 用射线法判断点是否在心形内
        c = False
        for a, b in zip(big, big[1:]):
            if (a[1] > y) != (b[1] > y) and x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1] + 1e-9) + a[0]:
                c = not c
        return c
    while len(nodes) < 46:
        x = rnd.uniform(min(xs), max(xs)); y = rnd.uniform(min(ys), max(ys))
        if inside(x, y) and all(math.hypot(x - a, y - b) > 56 * s for a, b in nodes):
            nodes.append((x, y))
    links = set()
    for i, (x, y) in enumerate(nodes):
        near = sorted(range(len(nodes)), key=lambda j: math.hypot(nodes[j][0] - x, nodes[j][1] - y))[1:4]
        for j in near: links.add(tuple(sorted((i, j))))
    for i, j in links:
        (x1, y1), (x2, y2) = nodes[i], nodes[j]
        out.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{GOLD2}" stroke-opacity=".42" stroke-width="{1.5*s:.1f}"/>')
    # 波：几道弹起的虚线弧
    for i, j in list(links)[::5]:
        (x1, y1), (x2, y2) = nodes[i], nodes[j]
        mx, my = (x1 + x2) / 2, min(y1, y2) - 70 * s
        out.append(f'<path d="M{x1:.0f} {y1:.0f} Q{mx:.0f} {my:.0f} {x2:.0f} {y2:.0f}" fill="none" stroke="{ROSE2}" stroke-opacity=".7" stroke-width="{2*s:.1f}" stroke-dasharray="{1.5*s:.1f} {8*s:.1f}" stroke-linecap="round"/>')
    for x, y in nodes:
        r0 = rnd.uniform(5, 9) * s
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r0*3.2:.1f}" fill="url(#dot{uid})" fill-opacity=".55"/>')
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r0:.1f}" fill="#FFF3E2"/>')
    # 心尖下的网（场的托）
    tip = heart_pts(cx, cy, k)[120]
    x0, x1, ny = cx - 440 * s, cx + 440 * s, tip[1] + 50 * s
    for kk, (op, d) in enumerate([(.9, 1.0), (.45, .65), (.25, .35)]):
        out.append(f'<path d="M{x0:.0f} {ny:.0f} Q{cx:.0f} {ny + 70*s*d:.0f} {x1:.0f} {ny:.0f}" fill="none" stroke="{GOLD2 if kk==0 else GOLD}" stroke-opacity="{op}" stroke-width="{(3.6 if kk==0 else 1.4)*s:.1f}" stroke-linecap="round"/>')
    # 心顶上的实底：一颗暖金色的球
    top = (cx, cy - 13.2 * k + 30 * s)
    top = (cx, cy - 4.0 * k)
    for rr, op in [(150, .10), (104, .20), (70, .38)]:
        out.append(f'<circle cx="{top[0]:.0f}" cy="{top[1]:.0f}" r="{rr*s:.0f}" fill="none" stroke="{WARM}" stroke-opacity="{op}" stroke-width="{1.8*s:.1f}"/>')
    out.append(f'<circle cx="{top[0]:.0f}" cy="{top[1]:.0f}" r="{110*s:.0f}" fill="url(#dot{uid})" fill-opacity=".45"/>')
    out.append(f'<circle cx="{top[0]:.0f}" cy="{top[1]:.0f}" r="{40*s:.0f}" fill="url(#core{uid})"/>')
    # 四周的暖光点与花瓣
    for _ in range(130):
        a = rnd.uniform(0, 2 * math.pi); rr = rnd.uniform(560, 900) * s
        x = cx + rr * math.cos(a); y = cy + rr * math.sin(a) * 0.95
        if not (0 < x < W and H * 0.30 < y < H * 0.93): continue
        if (x < W * 0.38 and y > H * 0.80) or (x < W * 0.50 and y < H * 0.34): continue
        if rnd.random() < .5:
            ang = rnd.uniform(0, 180); L = rnd.uniform(10, 18) * s
            out.append(f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{L:.1f}" ry="{L*0.48:.1f}" transform="rotate({ang:.0f} {x:.0f} {y:.0f})" fill="{rnd.choice([ROSE, ROSE2, '#F0B3B5'])}" fill-opacity="{rnd.uniform(.45,.85):.2f}"/>')
        else:
            out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rnd.uniform(1.6,4.2)*s:.1f}" fill="{rnd.choice([WARM, ROSE2, CREAM])}" fill-opacity="{rnd.uniform(.35,.85):.2f}"/>')
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 503 号</div>
<div class="t"><div class="pre">普通人都能明白的</div><div class="big big2">爱的箴言<br>新解</div>
<div class="sub">信是内能，望是动能，爱是势能</div><div class="rule"></div></div>
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
<div class="q">信是站住的，望是走动的，<br>爱是托住二者的那片场——<br>所以最大的是爱。</div><div class="by">——本书判词</div><div class="rule"></div>
<div class="bl"><p>腊月二十九，高铁晚点四个小时，一家人在出站口等。等的那几个小时里，有人站得住，有人坐不住，有人把大家托在一起。</p>
<p>本书把《哥林多前书》第 13 章里的信、望、爱，从三种德目读成一片土：信是土的定态，是内能；望是土的波，是动能；爱是托住二者的场，是势能。它们不是带来的，是每顺利走过一段苦难之路，显露就回写一层、加厚一层；拒绝回写，土就焊死，那就是石心。</p>
<p>不护教，也不反教。写给每一个读过这一章、却没读懂它的人。</p></div>
<div class="gold">望立次序，信接实底，爱守结构。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 503 号 · 十编五十一章 · 约 23 万字<br>定价 US$23.40</div>
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
