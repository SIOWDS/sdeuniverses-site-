#!/usr/bin/env python3
"""第 497 号《释经学的典范革命》封面与封底（由第 427 号改来，220 系列版式）：主图「缝里结晶」——石版裂开一道缝，缝里长出晶体，一缕气吹过。
用法：python3 cover.py --fonts /home/claude/fonts --out <dir>
"""
import argparse
import math
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0B1830', '#1B3158', '#142746'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#58BDCA', '#EFE8D6', '#9FB0C8'
ISBN = '979-8-90690-497-3'

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
    """主图「缝里结晶」：左下一块刻着字行的石版，斜斜裂开一道缝；缝里透出光，光往上长成一簇金色晶体，
    一缕气从右上吹下来绕过晶体——同一节经文，对不上的缝，结晶出新的符号，此刻还在发生。"""
    import random
    rnd = random.Random(498)
    s = W / 1700
    out = [f"""<defs>
 <radialGradient id="glow{uid}" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{CYAN}" stop-opacity=".55"/>
  <stop offset=".45" stop-color="{CYAN}" stop-opacity=".14"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient>
 <radialGradient id="gold{uid}" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{GOLD2}" stop-opacity=".95"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></radialGradient>
 <linearGradient id="cry{uid}" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="{GOLD}" stop-opacity=".95"/><stop offset=".6" stop-color="{GOLD2}" stop-opacity=".9"/><stop offset="1" stop-color="{CREAM}" stop-opacity=".95"/></linearGradient>
 <linearGradient id="stone{uid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#34507C"/><stop offset="1" stop-color="#1A2F57"/></linearGradient>
</defs>"""]
    # 石版：两块，中间一道斜缝
    x0, y0, x1, y1 = W * 0.42, H * 0.58, W * 0.92, H * 0.86
    cx0, cy0, cx1, cy1 = W * 0.64, y0, W * 0.71, y1          # 缝的上下端
    crack = [(cx0, cy0)]
    for k in range(1, 9):
        t = k / 9
        crack.append((cx0 + (cx1 - cx0) * t + rnd.uniform(-14, 14) * s, cy0 + (cy1 - cy0) * t))
    crack.append((cx1, cy1))
    left = [(x0, y0), (cx0 - 6 * s, y0)] + [(x - 6 * s, y) for x, y in crack[1:-1]] + [(cx1 - 6 * s, y1), (x0, y1)]
    right = [(cx0 + 6 * s, y0), (x1, y0), (x1, y1), (cx1 + 6 * s, y1)] + [(x + 6 * s, y) for x, y in crack[::-1][1:-1]]
    for poly in (left, right):
        d = 'M' + ' L'.join('%.0f %.0f' % q for q in poly) + ' Z'
        out.append(f'<path d="{d}" fill="url(#stone{uid})" stroke="{GOLD}" stroke-opacity=".55" stroke-width="{2*s:.1f}"/>')
    # 石版上的字行（细金线），左右各一列，被缝截断
    for i in range(9):
        yy = y0 + (y1 - y0) * (i + 1) / 10.5
        out.append(f'<line x1="{x0 + 26*s:.0f}" y1="{yy:.0f}" x2="{cx0 - 30*s + (cx1-cx0)*(i+1)/10.5:.0f}" y2="{yy:.0f}" stroke="{CREAM}" stroke-opacity=".22" stroke-width="{3*s:.1f}" stroke-dasharray="{18*s:.0f} {7*s:.0f}"/>')
        out.append(f'<line x1="{cx0 + 30*s + (cx1-cx0)*(i+1)/10.5:.0f}" y1="{yy:.0f}" x2="{x1 - 26*s:.0f}" y2="{yy:.0f}" stroke="{CREAM}" stroke-opacity=".22" stroke-width="{3*s:.1f}" stroke-dasharray="{18*s:.0f} {7*s:.0f}"/>')
    # 缝里的光
    out.append('<path d="M' + ' L'.join('%.0f %.0f' % q for q in crack) + f'" fill="none" stroke="{GOLD2}" stroke-width="{5*s:.1f}" stroke-opacity=".9"/>')
    out.append(f'<circle cx="{cx0:.0f}" cy="{cy0:.0f}" r="{260*s:.0f}" fill="url(#glow{uid})"/>')
    out.append(f'<circle cx="{cx0:.0f}" cy="{cy0:.0f}" r="{120*s:.0f}" fill="url(#gold{uid})" fill-opacity=".35"/>')
    # 晶体：从缝口往上长的一簇棱柱（细长六边形），越往上越亮
    for k in range(13):
        ang = -90 + rnd.uniform(-38, 38) + (k - 6) * 3
        ln = rnd.uniform(120, 360) * s * (1.15 if abs(k - 6) < 3 else 0.85)
        wd = rnd.uniform(18, 34) * s
        bx, by = cx0 + rnd.uniform(-30, 30) * s, cy0 + rnd.uniform(-6, 10) * s
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        nx, ny = -sa, ca
        tip = (bx + ca * ln, by + sa * ln)
        mid1 = (bx + ca * ln * .82 + nx * wd / 2, by + sa * ln * .82 + ny * wd / 2)
        mid2 = (bx + ca * ln * .82 - nx * wd / 2, by + sa * ln * .82 - ny * wd / 2)
        b1 = (bx + nx * wd / 2, by + ny * wd / 2); b2 = (bx - nx * wd / 2, by - ny * wd / 2)
        d = 'M%.0f %.0f L%.0f %.0f L%.0f %.0f L%.0f %.0f L%.0f %.0f Z' % (b1 + mid1 + tip + mid2 + b2)
        out.append(f'<path d="{d}" fill="url(#cry{uid})" fill-opacity="{rnd.uniform(.55, .9):.2f}" stroke="{CREAM}" stroke-opacity=".7" stroke-width="{1.4*s:.1f}"/>')
        out.append(f'<line x1="{bx:.0f}" y1="{by:.0f}" x2="{tip[0]:.0f}" y2="{tip[1]:.0f}" stroke="{CREAM}" stroke-opacity=".45" stroke-width="{1*s:.1f}"/>')
    # 一缕气：从右上吹下，绕过晶体顶端
    for j, (op, off) in enumerate([(.55, 0), (.32, 26), (.2, 52)]):
        p0 = (W * 1.02, H * 0.12 + off * s); p1 = (W * 0.86, H * 0.16 + off * s); p2 = (W * 0.98, H * 0.40 + off * s); p3 = (cx0 + 60 * s, H * 0.33 + off * s)
        pts = [bez(p0, p1, p2, p3, t / 40) for t in range(41)]
        out.append(f'<path d="{tapered(pts, 9*s, 1.2*s)}" fill="{CYAN}" fill-opacity="{op:.2f}"/>')
    # 星点
    for _ in range(90):
        out.append(f'<circle cx="{rnd.uniform(0, W):.0f}" cy="{rnd.uniform(H*0.06, H*0.55):.0f}" r="{rnd.uniform(.8, 2.2)*s:.1f}" fill="{CREAM}" fill-opacity="{rnd.uniform(.12, .45):.2f}"/>')
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 497 号</div>
<div class="t"><div class="pre">S D E 释 经 学</div><div class="big">释经学的<br>典范革命</div>
<div class="sub">从发现学到发生学</div><div class="rule"></div></div>
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
<div class="q">发现学读圣经，问“神说了什么”；<br>发生学读圣经，问“神与人之间发生了什么，此刻还在发生什么”。</div><div class="by">——本书判词</div><div class="rule"></div>
<div class="bl"><p>同一节经文，在发现学里是一份记录，在发生学里是一段发生史。两千年的释经学多半在做一件事：把神已经说完的话，准确地取出来。它稳，可考，能防随意，本书先把这些长处写足。</p>
<p>可是一节经文，常常是两样东西对不上时留下的刻痕：理念与现实，现实与自我。本书从“起初”读到“我将一切都更新了”，六十六卷，一卷一章，看每一卷的那条缝在哪里，结晶出了什么，今天又在读的人身上逼出了什么。</p>
<p>它也写清边界：缝要事先从经文里指认，读法要能被检验，发生学不等于怎么读都行。</p></div>
<div class="gold">经文每次被读，都又发生一次。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 497 号 · 十编七十四章 · 约 50 万字<br>定价 US$23.00</div>
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
