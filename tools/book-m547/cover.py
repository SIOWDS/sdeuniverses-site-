#!/usr/bin/env python3
"""第 547 号《岸上讲，田里耕》（王德生 著）封面与封底（工具链承自第 545、536、532 号，藏青底、金青奶白三色，220 系列版式）：
主图：岸上一个人在讲（青色话弧），田里一个人在耕（金色垄）；一条金色虚线从田里升起，落进话弧，碰出一圈亮环，环里长出两片芽。全部纯色，不用渐变。
用法：python3 cover.py --fonts /usr/share/fonts/opentype/noto --out <dir>
"""
import argparse
import math
import os
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0C1A34', '#1B3158', '#16294A'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#7FA7C9', '#EFE8D6', '#A9B6C8'
ISBN = '979-8-90690-549-9'
WAN = os.environ.get('WAN', '19')

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


def background(W, H, uid, split=0.365):
    """纯色底：三条横带拼出上深下浅（不用渐变——翻页器矢量模式画不出 PDF 渐变）。"""
    dots = []
    step = 44
    for yy in range(22, H, step):
        for xx in range(22 + (yy // step % 2) * 22, W, step):
            dots.append('<circle cx="%d" cy="%d" r="1.7"/>' % (xx, yy))
    return (f'<rect width="{W}" height="{H}" fill="{NAVY_TOP}"/>'
            f'<rect y="{H*split:.0f}" width="{W}" height="{H*(1-split):.0f}" fill="{NAVY_MID}"/>'
            f'<rect y="{H*0.80:.0f}" width="{W}" height="{H*0.20:.0f}" fill="{NAVY_LOW}"/>'
            f'<g fill="{DIM}" fill-opacity=".10">{"".join(dots)}</g>')


def art(W, H, uid):
    """主图（第 547 号）：岸与田。"""
    import random
    rnd = random.Random(547)
    s = W / 1700
    out = []
    yb = H * 0.505                      # 岸线
    yf = H * 0.735                      # 田底
    x0, x1 = W * 0.10, W * 0.90
    # 岸：一道缓坡的土埂（奶白淡块）
    bank = 'M%.0f %.0f Q%.0f %.0f %.0f %.0f Q%.0f %.0f %.0f %.0f L%.0f %.0f L%.0f %.0f Z' % (
        x0, yb + 36 * s, W * 0.30, yb - 34 * s, W * 0.52, yb - 6 * s, W * 0.74, yb + 20 * s, x1, yb + 2 * s, x1, yb + 70 * s, x0, yb + 70 * s)
    out.append(f'<path d="{bank}" fill="{CREAM}" fill-opacity=".16" stroke="{GOLD}" stroke-opacity=".5" stroke-width="{2.4*s:.1f}"/>')
    # 田：垄线（金），一垄一垄起伏
    out.append(f'<rect x="{x0:.0f}" y="{yb + 70*s:.0f}" width="{x1 - x0:.0f}" height="{yf - yb - 70*s:.0f}" fill="{CREAM}" fill-opacity=".07" stroke="{GOLD}" stroke-opacity=".30" stroke-width="{2*s:.1f}"/>')
    nrow = 9
    for k in range(nrow):
        y0 = yb + 70 * s + (yf - yb - 70 * s) * (k + .6) / (nrow + .2)
        d = 'M%.0f %.0f' % (x0 + 10 * s, y0)
        n = 6
        for i in range(n):
            xm = x0 + (x1 - x0) * (i + .5) / n; xe = x0 + (x1 - x0) * (i + 1) / n
            d += ' Q%.0f %.0f %.0f %.0f' % (xm, y0 + (11 if (i + k) % 2 else -11) * s, xe, y0 + rnd.uniform(-2, 2) * s)
        out.append(f'<path d="{d}" fill="none" stroke="{GOLD2}" stroke-opacity="{.30 + .04 * (k % 3):.2f}" stroke-width="{3.2*s:.1f}" stroke-linecap="round"/>')
    for _ in range(120):                # 田里的颗粒
        x = rnd.uniform(x0 + 14 * s, x1 - 14 * s); y = rnd.uniform(yb + 90 * s, yf - 10 * s)
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rnd.uniform(1.8, 4.6)*s:.1f}" fill="{rnd.choice([GOLD2, CREAM, CYAN])}" fill-opacity="{rnd.uniform(.3, .75):.2f}"/>')
    # 岸上的人：圆头＋长衫，面向右上，青色话弧
    px, py = W * 0.30, yb - 40 * s
    out.append(f'<circle cx="{px:.0f}" cy="{py - 150*s:.0f}" r="{24*s:.0f}" fill="{CREAM}"/>')
    out.append(f'<path d="M{px - 30*s:.0f} {py:.0f} L{px - 14*s:.0f} {py - 118*s:.0f} L{px + 14*s:.0f} {py - 118*s:.0f} L{px + 30*s:.0f} {py:.0f} Z" fill="{CREAM}" fill-opacity=".92"/>')
    ax, ay = px + 40 * s, py - 150 * s
    for k, r in enumerate((60, 100, 142, 186)):
        out.append(f'<path d="M{ax + r*s*math.cos(math.radians(-62)):.0f} {ay + r*s*math.sin(math.radians(-62)):.0f} '
                   f'A{r*s:.0f} {r*s:.0f} 0 0 1 {ax + r*s*math.cos(math.radians(24)):.0f} {ay + r*s*math.sin(math.radians(24)):.0f}" '
                   f'fill="none" stroke="{CYAN}" stroke-opacity="{.85 - k*.15:.2f}" stroke-width="{5*s:.1f}" stroke-linecap="round"/>')
    # 田里的人：弯腰，一条长锄
    fx, fy = W * 0.62, yb + 150 * s
    out.append(f'<circle cx="{fx + 46*s:.0f}" cy="{fy - 56*s:.0f}" r="{21*s:.0f}" fill="{GOLD2}"/>')
    out.append(f'<path d="{tapered([(fx - 40*s, fy + 74*s), (fx - 8*s, fy + 6*s), (fx + 30*s, fy - 36*s)], 34 * s, 22 * s)}" fill="{GOLD2}"/>')
    out.append(f'<path d="{tapered([(fx - 30*s, fy + 74*s), (fx - 24*s, fy + 120*s)], 14 * s, 11 * s)}" fill="{GOLD2}"/>')
    out.append(f'<path d="{tapered([(fx, fy + 70*s), (fx + 14*s, fy + 120*s)], 14 * s, 11 * s)}" fill="{GOLD2}"/>')
    out.append(f'<line x1="{fx + 62*s:.0f}" y1="{fy - 40*s:.0f}" x2="{fx + 128*s:.0f}" y2="{fy + 112*s:.0f}" stroke="{CREAM}" stroke-width="{6*s:.1f}" stroke-linecap="round"/>')
    out.append(f'<path d="M{fx + 108*s:.0f} {fy + 116*s:.0f} L{fx + 150*s:.0f} {fy + 104*s:.0f} L{fx + 132*s:.0f} {fy + 140*s:.0f} Z" fill="{CREAM}"/>')
    # 碰：金色虚线从田里升起，穿过岸，落进话弧，碰出一圈亮环，环里两片芽
    hx, hy = fx + 134 * s, fy + 90 * s
    cx_, cy_ = ax + 124 * s, ay - 40 * s
    out.append(f'<path d="M{hx:.0f} {hy:.0f} C{hx + 60*s:.0f} {yb:.0f} {cx_ + 40*s:.0f} {cy_ + 360*s:.0f} {cx_:.0f} {cy_:.0f}" fill="none" stroke="{GOLD2}" stroke-width="{4*s:.1f}" stroke-dasharray="{12*s:.0f} {10*s:.0f}" stroke-linecap="round"/>')
    out.append(f'<circle cx="{cx_:.0f}" cy="{cy_:.0f}" r="{58*s:.0f}" fill="{NAVY_TOP}" fill-opacity=".55" stroke="{GOLD2}" stroke-width="{4*s:.1f}"/>')
    out.append(f'<circle cx="{cx_:.0f}" cy="{cy_:.0f}" r="{82*s:.0f}" fill="none" stroke="{GOLD2}" stroke-opacity=".35" stroke-width="{2.4*s:.1f}"/>')
    out.append(f'<path d="M{cx_:.0f} {cy_ + 30*s:.0f} L{cx_:.0f} {cy_ - 6*s:.0f}" stroke="{CREAM}" stroke-width="{5*s:.1f}" stroke-linecap="round"/>')
    out.append(f'<path d="M{cx_:.0f} {cy_ - 6*s:.0f} Q{cx_ - 40*s:.0f} {cy_ - 14*s:.0f} {cx_ - 34*s:.0f} {cy_ - 46*s:.0f} Q{cx_ - 6*s:.0f} {cy_ - 40*s:.0f} {cx_:.0f} {cy_ - 6*s:.0f} Z" fill="{CREAM}"/>')
    out.append(f'<path d="M{cx_:.0f} {cy_ - 6*s:.0f} Q{cx_ + 40*s:.0f} {cy_ - 14*s:.0f} {cx_ + 34*s:.0f} {cy_ - 46*s:.0f} Q{cx_ + 6*s:.0f} {cy_ - 40*s:.0f} {cx_:.0f} {cy_ - 6*s:.0f} Z" fill="{CYAN}"/>')
    # 标注
    ty = yf + 66 * s
    for xx, anc, big, small, col in ((x0, 'start', '岸上 · 讲', '理念', CYAN), (W * 0.5, 'middle', '碰', '不是加', GOLD2), (x1, 'end', '田里 · 耕', '现实', CREAM)):
        out.append(f'<text x="{xx:.0f}" y="{ty:.0f}" font-size="{36*s:.0f}" text-anchor="{anc}" font-family="Noto Serif CJK SC" font-weight="700" fill="{col}" letter-spacing="{4*s:.0f}">{big}</text>')
        out.append(f'<text x="{xx:.0f}" y="{ty + 40*s:.0f}" font-size="{20*s:.0f}" text-anchor="{anc}" font-family="Noto Sans CJK SC" fill="{DIM}" letter-spacing="{3*s:.0f}">{small}</text>')
    for _ in range(50):
        out.append(f'<circle cx="{rnd.uniform(0, W):.0f}" cy="{rnd.uniform(H*0.30, H*0.355):.0f}" r="{rnd.uniform(.8, 2.2)*s:.1f}" fill="{CREAM}" fill-opacity="{rnd.uniform(.12, .40):.2f}"/>')
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 547 号</div>
<div class="t"><div class="pre">复合思考主体 · 你的田</div><div class="big big2" style="font-size:{44*s:.1f}pt">岸上讲，<br>田里耕</div>
<div class="sub">你的经验，是<br>AI时代最稀缺的东西</div><div class="rule"></div></div>
<div class="b"><div class="au">王德生　著</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div>
</div></div></body></html>"""


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
           f'{background(W, H, "b", split=0.66)}{emb}{"".join(waves)}{bc}</svg>')
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
<div class="c"><div class="lab">核 心 问 题</div>
<div class="q">AI 在岸上讲耕田。<br>耕田的人，在田里。</div><div class="by">——本书序章</div><div class="rule"></div>
<div class="bl"><p>有人担心，AI 会让人变蠢。本书说，这句担心量错了：它量的是单独的人，而今天做事的，是人和 AI 一起。人让出一部分思考，同时被推上一层；这一层，是人和 AI 碰出来的，不是相加出来的。</p>
<p>岸上的 AI 讲得很全，可它没踩过你的田。田里那点说不清的东西，手上的分寸、耳朵里的响动、一眼看出不对，碰上岸上的讲，才碰得出新的。没有田的人，讲得再多，多半只是转述。</p>
<p>全书序章、四编八章、结语，从做饭、种菜、修东西这些日常小事讲起，用触觉、听觉、视觉三种感觉讲清 S·D·E，再讲碰撞怎样发生、人怎样守住自己的田。每章末有“带走的话”“小账”和一条“这一章怎样算错”。</p>
<p>这是一部研究性专著：核心思想由王德生提出，正文由 AI（Claude）协作撰写并经审读回改；书中的人物与场景是构想，所列判错条件尚待检验，没有独立学术评审，也没有用户试验。</p></div>
<div class="gold">AI时代最值钱的，是那一块别人没踩过的、你自己的田。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 547 号 · 序章四编八章结语 · 约 {WAN} 万字<br>ISBN 979-8-90690-549-9 · 定价 US$20.00</div>
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
