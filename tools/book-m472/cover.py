#!/usr/bin/env python3
"""第 472 号《书：洪流结出的粒子》（王德生著）封面与封底（由第 467 号改来，220 系列版式）：主图是洪流凝成一颗粒子，粒子下一座小园（假山、曲廊）。
用法：python3 cover.py --fonts /home/claude/fonts --out <dir>
"""
import argparse
import math
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0C1A34', '#1B3158', '#16294A'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#7FA7C9', '#EFE8D6', '#A9B6C8'
ISBN = '979-8-90690-472-0'

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


def flow_line(x0, y0, cx, cy, k, W, s, rnd):
    """一条从左侧洪流里流向粒子的流线：起点散在左边，越近粒子越收拢，绕粒子半圈后消失。"""
    pts = []
    n = 90
    amp = rnd.uniform(18, 46) * s
    ph = rnd.uniform(0, math.pi * 2)
    for i in range(n + 1):
        t = i / n
        e = t ** 1.7
        x = x0 + (cx - x0) * e
        y = y0 + (cy - y0) * e + amp * (1 - e) * math.sin(ph + t * 7.5)
        pts.append((x, y))
    return pts


def art(W, H, uid):
    """主图（第 472 号）：洪流结出的粒子。左下一片由流线组成的洪流，越往前越收拢，
    凝成右上一颗金色粒子；粒子外三道环是三化（整体化、稳定化、独立化）；粒子下方一座小园：假山、一道曲廊。"""
    import random
    rnd = random.Random(472)
    s = W / 1700
    cx, cy, r = W * 0.60, H * 0.56, 300 * s
    out = [f"""<defs>
 <radialGradient id="pt{uid}" cx=".38" cy=".34" r=".7"><stop offset="0" stop-color="#FFF6DA"/>
  <stop offset=".35" stop-color="{GOLD2}"/><stop offset="1" stop-color="#8E7232"/></radialGradient>
 <radialGradient id="glow{uid}" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{GOLD2}" stop-opacity=".34"/>
  <stop offset=".5" stop-color="{GOLD}" stop-opacity=".09"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></radialGradient>
</defs>"""]
    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r*2.3:.0f}" fill="url(#glow{uid})"/>')
    # 洪流：四十条流线从左侧散开处流向粒子
    pr = r * 0.30
    for k in range(46):
        y0 = H * rnd.uniform(0.40, 0.98)
        x0 = -W * rnd.uniform(0.02, 0.12)
        tx = cx + pr * 1.05 * math.cos(math.radians(rnd.uniform(120, 240)))
        ty = cy + pr * 1.05 * math.sin(math.radians(rnd.uniform(120, 240)))
        pts = flow_line(x0, y0, tx, ty, k, W, s, rnd)
        d = 'M' + ' L'.join('%.1f %.1f' % q for q in pts)
        col = CYAN if k % 3 == 0 else (GOLD if k % 3 == 1 else CREAM)
        op = rnd.uniform(.16, .46)
        out.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-opacity="{op:.2f}" stroke-width="{rnd.uniform(1.4, 3.6)*s:.1f}" stroke-linecap="round"/>')
    # 三化：三道环（实、虚点、细）
    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r*0.62:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".75" stroke-width="{3.2*s:.1f}"/>')
    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r*0.86:.0f}" fill="none" stroke="{GOLD2}" stroke-opacity=".45" stroke-width="{2*s:.1f}" stroke-dasharray="{4*s:.0f} {11*s:.0f}"/>')
    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r*1.10:.0f}" fill="none" stroke="{CREAM}" stroke-opacity=".22" stroke-width="{1.3*s:.1f}"/>')
    ticks = []
    for kk in range(60):
        a = kk * math.pi * 2 / 60
        r1 = r * (1.13 if kk % 5 else 1.17)
        ticks.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (cx + r * 1.10 * math.cos(a), cy + r * 1.10 * math.sin(a), cx + r1 * math.cos(a), cy + r1 * math.sin(a)))
    out.append(f'<g stroke="{GOLD}" stroke-opacity=".40" stroke-width="{1.4*s:.1f}">{"".join(ticks)}</g>')
    # 粒子
    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{pr:.0f}" fill="url(#pt{uid})"/>')
    out.append(f'<circle cx="{cx - pr*0.32:.0f}" cy="{cy - pr*0.34:.0f}" r="{pr*0.18:.0f}" fill="#FFFBEF" fill-opacity=".75"/>')
    # 三环上三点与标签
    for ang, lab in [(-90, '整体化'), (30, '稳定化'), (150, '独立化')]:
        a = math.radians(ang)
        px, py = cx + r * 0.62 * math.cos(a), cy + r * 0.62 * math.sin(a)
        out.append(f'<circle cx="{px:.0f}" cy="{py:.0f}" r="{9*s:.0f}" fill="{GOLD2}"/>')
    # 园林：粒子下方一座小园——假山（层叠石）、一道曲廊、一池水线
    gx, gy = cx, cy + r * 1.62
    g0 = len(out)
    def P(pts):
        return 'M' + ' '.join(('%s %.0f %.0f' % (c, gx + x * s, gy + y * s)) if c else ('%.0f %.0f' % (gx + x * s, gy + y * s)) for c, x, y in pts) + ' Z'
    # 太湖石：瘦、漏、透——一块竖立的石，腰细，顶上歪出一块，身上三个洞
    rock = P([('', -170, 0), ('Q', -182, -40), ('', -150, -62), ('Q', -128, -86), ('', -146, -118), ('Q', -170, -150), ('', -138, -190),
              ('Q', -112, -232), ('', -70, -214), ('Q', -40, -200), ('', -58, -170), ('Q', -76, -146), ('', -52, -120), ('Q', -24, -96), ('', -44, -62),
              ('Q', -66, -36), ('', -36, -14), ('Q', -20, 0), ('', -40, 0)])
    rock = rock.replace(' Q', ' Q').replace('Q ', 'Q')
    out.append(f'<path d="{rock}" fill="{NAVY_LOW}" stroke="{GOLD}" stroke-opacity=".8" stroke-width="{2.4*s:.1f}" stroke-linejoin="round"/>')
    for hx, hy, hr in [(-104, -178, 11), (-118, -104, 8), (-74, -60, 7), (-96, -142, 5)]:
        out.append(f'<circle cx="{gx + hx*s:.0f}" cy="{gy + hy*s:.0f}" r="{hr*s:.0f}" fill="none" stroke="{GOLD2}" stroke-opacity=".7" stroke-width="{1.6*s:.1f}"/>')
    # 曲廊：一条折线廊，廊顶一条，柱子数根
    lang = [(gx + 30*s, gy - 30*s), (gx + 110*s, gy - 30*s), (gx + 150*s, gy - 62*s), (gx + 230*s, gy - 62*s), (gx + 270*s, gy - 30*s)]
    d = 'M' + ' L'.join('%.0f %.0f' % q for q in lang)
    out.append(f'<path d="{d}" fill="none" stroke="{GOLD2}" stroke-width="{4*s:.1f}" stroke-linejoin="round"/>')
    d2 = 'M' + ' L'.join('%.0f %.0f' % (x, y + 34*s) for x, y in lang)
    out.append(f'<path d="{d2}" fill="none" stroke="{GOLD}" stroke-opacity=".6" stroke-width="{2*s:.1f}" stroke-linejoin="round"/>')
    for x, y in lang:
        out.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x:.0f}" y2="{y + 34*s:.0f}" stroke="{GOLD}" stroke-opacity=".7" stroke-width="{1.8*s:.1f}"/>')
    for k in range(3):
        yy = gy + (14 + k * 12) * s
        out.append(f'<path d="M {gx - 280*s:.0f} {yy:.0f} Q {gx - 140*s:.0f} {yy - 7*s:.0f} {gx:.0f} {yy:.0f} T {gx + 290*s:.0f} {yy:.0f}" fill="none" stroke="{CYAN}" stroke-opacity="{.45 - k*.12:.2f}" stroke-width="{1.6*s:.1f}"/>')
    garden = ''.join(out[g0:]); del out[g0:]
    out.append(f'<g transform="translate({gx:.0f} {gy:.0f}) scale(1.4) translate({-gx:.0f} {-gy:.0f})">{garden}</g>')
    for _ in range(70):
        out.append(f'<circle cx="{rnd.uniform(W*0.35, W):.0f}" cy="{rnd.uniform(H*0.30, H*0.42):.0f}" r="{rnd.uniform(.8, 2.2)*s:.1f}" fill="{CREAM}" fill-opacity="{rnd.uniform(.12, .45):.2f}"/>')
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 472 号</div>
<div class="t"><div class="pre">普通人都能明白的</div><div class="big" style="font-size:{70*s:.1f}pt">书</div>
<div class="sub">洪流结出的粒子</div><div class="rule"></div></div>
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
<div class="q">书＝SDE 洪流聚合体运行的粒子化：<br>整体化、稳定化、独立化。</div><div class="by">——王德生口述 · 本书母题</div><div class="rule"></div>
<div class="bl"><p>林外婆抽屉里压着一本太外婆留下的菜谱本，字清清楚楚，照着做了几十年，鱼总差一口气。「少许」是多少，太外婆的手知道，纸不知道。常说书是装知识的容器；本书说，书不是容器，是一场洪流结出的粒子：有头有尾，冻住不变，离得开原来的地方，三样各得一份，也各付一份。</p>
<p>一座山不是书，一座园林是山的成书。粒子落在哪条感觉通道，就是哪一种书：眼睛读的光书，耳朵听的音书，指尖与全身读的触之书、身之书，行在人身上的气书。西方把宝押在光书，印度押在音书，中华押在气书；而 AI 只能读光书，别的通道的书到了机器那里，都先被光化。</p>
<p>五篇十五章，从一本菜谱本、一座拙政园、一杯年夜饭前的酒，走到圆明园的残石与今天的机器。读书，是让粒子在你自己的洪流里重新入流。</p></div>
<div class="gold">它是从哪一场洪流里来的？</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 472 号 · 五篇十五章 · 约 38 万字<br>ISBN 979-8-90690-472-0 · 定价 US$25.00</div>
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
