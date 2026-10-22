#!/usr/bin/env python3
"""《教育的产品是结晶》封面与封底（工具由第 364 号改来，照第 220 号系列版式）：藏青渐变底、细点阵、金色光晕与刻度环；
主图是五段账：散落的特征点（在场）被细线连起（建立），中央结成金色六棱晶体（粒子化），一角熔开、旁边又长出新晶（熔开再结晶）。
"""
import argparse
import os
import math
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0B1830', '#1B3158', '#142746'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#58BDCA', '#EFE8D6', '#9FB0C8'
ISBN = '979-8-90690-409-6'
WAN = os.environ.get('WAN', '20')
NO = '第 409 号'
PRICE = 'US$23.00'

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
    """主图：五段账。左下散落的奶白特征点（在场），被青色细线连起来（建立）；
    中央结成一颗金色六棱晶体（粒子化）；右上一角熔开成虚线，旁边又长出一颗新晶（熔开再结晶）。"""
    s = W / 1700
    cx, cy, r = W * 0.58, H * 0.60, 520 * s
    u = r / 450
    out = [rings(cx, cy, r).replace('{uid}', uid)]
    out.append(f'''<defs><linearGradient id="cr{uid}" x1="0" y1="0" x2="1" y2="1">
 <stop offset="0" stop-color="{GOLD2}" stop-opacity=".95"/><stop offset=".55" stop-color="{GOLD}" stop-opacity=".85"/>
 <stop offset="1" stop-color="#8E6E2E" stop-opacity=".9"/></linearGradient>
 <linearGradient id="cr2{uid}" x1="1" y1="0" x2="0" y2="1">
 <stop offset="0" stop-color="{CREAM}" stop-opacity=".55"/><stop offset="1" stop-color="{GOLD}" stop-opacity=".25"/></linearGradient></defs>''')
    import random
    rnd = random.Random(409)
    # 在场：散落的点（左下，越往晶体越密）
    pts = []
    for k in range(46):
        a = rnd.uniform(math.radians(95), math.radians(235))
        d = rnd.uniform(1.05, 1.95) * r
        x, y = cx + d * math.cos(a), cy + d * math.sin(a) * 0.78
        if 0 < x < W and 0 < y < H * 0.97:
            pts.append((x, y))
    # 建立：最近邻连线（青色细线，越靠近晶体越亮）
    lines = []
    for i, (x, y) in enumerate(pts):
        near = sorted(((math.hypot(x - a, y - b), j) for j, (a, b) in enumerate(pts) if j != i))[:2]
        for dd, j in near:
            if dd < r * 0.42:
                a, b = pts[j]
                op = max(.10, .55 - math.hypot((x + a) / 2 - cx, (y + b) / 2 - cy) / (r * 4.2))
                lines.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{a:.0f}" y2="{b:.0f}" stroke="{CYAN}" stroke-opacity="{op:.2f}" stroke-width="{2.2*s:.1f}"/>')
    # 几条线从点群伸向晶体
    for (x, y) in sorted(pts, key=lambda p: math.hypot(p[0] - cx, p[1] - cy))[:7]:
        lines.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{cx - r*0.18:.0f}" y2="{cy + r*0.10:.0f}" stroke="{GOLD2}" stroke-opacity=".28" stroke-width="{1.8*s:.1f}" stroke-dasharray="{6*s:.0f} {7*s:.0f}"/>')
    out += lines
    for (x, y) in pts:
        rr = rnd.uniform(3.5, 7.5) * s
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rr:.1f}" fill="{CREAM}" fill-opacity="{rnd.uniform(.45, .9):.2f}"/>')
    # 粒子化：六棱晶体（正六边形 + 立体棱面）
    R = 255 * u
    hexp = [(cx + R * math.cos(math.radians(60 * k - 90)), cy + R * math.sin(math.radians(60 * k - 90))) for k in range(6)]
    poly = ' '.join('%.0f,%.0f' % p for p in hexp)
    out.append(f'<polygon points="{poly}" fill="url(#cr{uid})" stroke="{GOLD2}" stroke-width="{4*s:.1f}" stroke-linejoin="round"/>')
    inner = [(cx + R * 0.48 * math.cos(math.radians(60 * k - 90)), cy + R * 0.48 * math.sin(math.radians(60 * k - 90))) for k in range(6)]
    out.append(f'<polygon points="{" ".join("%.0f,%.0f" % p for p in inner)}" fill="url(#cr2{uid})" stroke="{CREAM}" stroke-opacity=".65" stroke-width="{2.4*s:.1f}"/>')
    for (a, b), (c, d) in zip(hexp, inner):
        out.append(f'<line x1="{a:.0f}" y1="{b:.0f}" x2="{c:.0f}" y2="{d:.0f}" stroke="{CREAM}" stroke-opacity=".55" stroke-width="{2.2*s:.1f}"/>')
    # 棱面高光
    out.append(f'<polygon points="{hexp[5][0]:.0f},{hexp[5][1]:.0f} {hexp[0][0]:.0f},{hexp[0][1]:.0f} {inner[0][0]:.0f},{inner[0][1]:.0f} {inner[5][0]:.0f},{inner[5][1]:.0f}" fill="{CREAM}" fill-opacity=".28"/>')
    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{R*0.06:.0f}" fill="{CREAM}" fill-opacity=".9"/>')
    # 熔开：右上一角裂开（虚线轮廓）＋ 新晶长出
    a0 = hexp[1]
    fx, fy = a0[0] + R * 0.34, a0[1] - R * 0.30
    out.append(f'<path d="M{hexp[0][0]*.5 + a0[0]*.5:.0f} {hexp[0][1]*.5 + a0[1]*.5:.0f} L{fx:.0f} {fy:.0f} L{a0[0]*.5 + hexp[2][0]*.5:.0f} {a0[1]*.5 + hexp[2][1]*.5:.0f}" fill="none" stroke="{GOLD2}" stroke-opacity=".75" stroke-width="{3*s:.1f}" stroke-dasharray="{9*s:.0f} {8*s:.0f}"/>')
    nx, ny, nR = cx + R * 1.72, cy - R * 1.08, R * 0.30
    nh = [(nx + nR * math.cos(math.radians(60 * k - 90)), ny + nR * math.sin(math.radians(60 * k - 90))) for k in range(6)]
    out.append(f'<polygon points="{" ".join("%.0f,%.0f" % p for p in nh)}" fill="url(#cr{uid})" fill-opacity=".9" stroke="{GOLD2}" stroke-width="{3*s:.1f}"/>')
    for p in nh:
        out.append(f'<line x1="{nx:.0f}" y1="{ny:.0f}" x2="{p[0]:.0f}" y2="{p[1]:.0f}" stroke="{CREAM}" stroke-opacity=".45" stroke-width="{1.6*s:.1f}"/>')
    for k in range(9):
        t = k / 8
        x = fx + (nx - nR * 0.9 - fx) * t
        y = fy + (ny + nR * 0.6 - fy) * t - math.sin(t * math.pi) * R * 0.18
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{(2.5 + 3*t)*s:.1f}" fill="{GOLD2}" fill-opacity="{.25 + .6*t:.2f}"/>')
    # 底部五个小刻记：在场 · 建立 · 维持 · 粒子化 · 熔开再结晶
    by = cy + R * 1.62
    for k in range(5):
        x = cx - R * 1.30 + k * R * 0.65
        out.append(f'<circle cx="{x:.0f}" cy="{by:.0f}" r="{(5 + 2.2*k)*s:.1f}" fill="{CREAM if k < 3 else GOLD2}" fill-opacity="{.35 + .14*k:.2f}"/>')
        if k < 4:
            out.append(f'<line x1="{x + 14*s:.0f}" y1="{by:.0f}" x2="{x + R*0.65 - 16*s:.0f}" y2="{by:.0f}" stroke="{GOLD}" stroke-opacity=".45" stroke-width="{2*s:.1f}"/>')
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · {NO}</div>
<div class="t"><div class="pre">学了，为什么没学会</div><div class="big big2">教育的产品是结晶</div>
<div class="sub">AI 时代，为什么学了却没学会</div><div class="rule"></div></div>
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
<div class="q">教育的产品<br>不是答案，<br>是结晶。</div><div class="by">——本书判词</div><div class="rule"></div>
<div class="bl"><p>作业全对，第二天的小测一道也写不出；题刷了三年，换个问法就卡住；培训听得频频点头，回到岗位照旧。AI 一键给出答案的时代，“都会”和“会了”之间的那道缝，越来越宽。</p>
<p>本书说：学习是特征纠缠的建立，记忆是它的维持，学会是它的粒子化——一个符号在你身上发生了。答案可以转手，纠缠不能代建。它要有对不上、有托得住的场、有学的人自己付的力气。</p>
<p>从看懂型、背住型、刷熟型三种假会，到学不进的三个入口，再到课堂、作业、评价怎样重新排布；第 21 章写明本书在什么情况下算错。</p></div>
<div class="gold">学习是建立，记忆是维持，学会是粒子化。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著 {NO} · 八编二十二章 · 约 {WAN} 万字<br>定价 {PRICE}</div>
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
