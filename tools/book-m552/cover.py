#!/usr/bin/env python3
"""第 552 号《陶哲轩如何才能与大模型公司和解与合作呢？》（王德生 著）封面与封底（工具链承自第 551 号；靛青底，金、青绿、陶红点缀，220 系列版式）：
主图：回写派生树——三层土上一根主干，在共同祖先处分三支、再分叉；左支两片叶梢沿金色虚线回到共同祖先，旁标 g；右支挂一颗陶红的反面果子，另起新的一支。全部纯色，不用渐变。
用法：python3 cover.py --fonts /usr/share/fonts/opentype/noto --out <dir>
"""
import argparse
import math
import os
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#121E36', '#1A2B48', '#16253F'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#6FB9B0', '#EFE8D6', '#A3B8BC'
CLAY = '#D98E73'
import sys
sys.path.insert(0, str(Path(__file__).parent))
import meta as M  # noqa: E402
ISBN = M.ISBN
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
    """主图（第 552 号）：回写派生树。底下三层土（回写一层层堆成的土壤），一根主干从土里长出，
    在共同祖先处分成三支，各支再分叉，节点即一代代回写；左支两片叶梢沿金色虚线回到共同祖先，旁标 g（共同祖先深度）；
    右支一处分叉上挂一颗陶红的“反面果子”，从那里另起一支。全部纯色扁平，不用渐变。"""
    import random
    rnd = random.Random(552)
    s = W / 1700
    out = []
    cx = W * 0.57
    ground = H * 0.865
    gens = [ground, H * 0.775, H * 0.685, H * 0.600, H * 0.515]
    # 土壤：三层纯色带
    for k, (y0, h, col, op) in enumerate([(ground, H * 0.026, '#2E4A57', 1), (ground + H * 0.026, H * 0.024, '#24404D', 1),
                                         (ground + H * 0.050, H * 0.030, '#1B3542', 1)]):
        out.append(f'<rect x="0" y="{y0:.0f}" width="{W}" height="{h:.0f}" fill="{col}" fill-opacity="{op}"/>')
    for _ in range(70):
        out.append(f'<circle cx="{rnd.uniform(0, W):.0f}" cy="{rnd.uniform(ground + 8*s, ground + H*0.075):.0f}" '
                   f'r="{rnd.uniform(1.5, 4.5)*s:.1f}" fill="{rnd.choice([GOLD, CLAY, CREAM])}" fill-opacity="{rnd.uniform(.15, .45):.2f}"/>')
    # 树：节点 (x, y, 代) 与父子边
    nodes = {'r': (cx, gens[1], 1)}
    edges = [((cx, ground), (cx, gens[1]), 0)]
    dx2 = [-0.235 * W, 0.0, 0.195 * W]
    for i, d2 in enumerate(dx2):
        k2 = 'b%d' % i
        nodes[k2] = (cx + d2, gens[2], 2); edges.append((nodes['r'][:2], nodes[k2][:2], 1))
        for j, d3 in enumerate((-0.085 * W, 0.085 * W)):
            if i == 1 and j == 0:
                continue
            k3 = '%s%d' % (k2, j)
            nodes[k3] = (nodes[k2][0] + d3, gens[3], 3); edges.append((nodes[k2][:2], nodes[k3][:2], 2))
            for m, d4 in enumerate((-0.042 * W, 0.042 * W)):
                if (i, j, m) in ((2, 1, 1),):
                    continue
                k4 = '%s%d' % (k3, m)
                nodes[k4] = (nodes[k3][0] + d4, gens[4], 4); edges.append((nodes[k3][:2], nodes[k4][:2], 3))
    widths = [15, 10, 6.5, 4.2]
    cols = [GOLD2, GOLD2, CREAM, CYAN]
    for (p0, p1, g) in edges:
        d = f'M{p0[0]:.0f} {p0[1]:.0f} C{p0[0]:.0f} {p0[1] - (p0[1]-p1[1])*0.55:.0f} {p1[0]:.0f} {p1[1] + (p0[1]-p1[1])*0.45:.0f} {p1[0]:.0f} {p1[1]:.0f}'
        out.append(f'<path d="{d}" fill="none" stroke="{cols[g]}" stroke-opacity=".9" stroke-width="{widths[g]*s:.1f}" stroke-linecap="round"/>')
    # 反面果子：右支 b21 节点上方另起一支（陶红）
    fx, fy, _ = nodes['b21']
    nx, ny = fx + 0.035 * W, gens[4] - H * 0.045
    out.append(f'<path d="M{fx:.0f} {fy:.0f} C{fx + 30*s:.0f} {fy - 90*s:.0f} {nx - 40*s:.0f} {ny + 80*s:.0f} {nx:.0f} {ny:.0f}" fill="none" stroke="{CLAY}" stroke-width="{4.2*s:.1f}" stroke-linecap="round" stroke-dasharray="{14*s:.0f} {9*s:.0f}"/>')
    out.append(f'<circle cx="{nx:.0f}" cy="{ny:.0f}" r="{13*s:.0f}" fill="{NAVY_TOP}" stroke="{CLAY}" stroke-width="{3*s:.1f}"/>')
    out.append(f'<circle cx="{fx + 26*s:.0f}" cy="{fy - 40*s:.0f}" r="{19*s:.0f}" fill="{CLAY}"/>')
    out.append(f'<path d="M{fx + 26*s:.0f} {fy - 59*s:.0f} q{6*s:.0f} {-14*s:.0f} {18*s:.0f} {-16*s:.0f}" fill="none" stroke="{GOLD2}" stroke-width="{3*s:.1f}"/>')
    # 节点
    for k, (x, y, g) in nodes.items():
        r = {1: 21, 2: 15, 3: 11, 4: 9}[g] * s
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.0f}" fill="{NAVY_TOP}" stroke="{cols[min(g, 3)]}" stroke-width="{3*s:.1f}"/>')
    # 叶梢的果子
    for k, (x, y, g) in nodes.items():
        if g == 4:
            out.append(f'<circle cx="{x:.0f}" cy="{y - 26*s:.0f}" r="{7*s:.0f}" fill="{GOLD}" fill-opacity=".85"/>')
    # g：左支两片叶梢沿金色虚线回到共同祖先 b0
    ax, ay, _ = nodes['b0']
    out.append(f'<circle cx="{ax:.0f}" cy="{ay:.0f}" r="{27*s:.0f}" fill="none" stroke="{GOLD}" stroke-width="{3*s:.1f}"/>')
    for leaf in ('b000', 'b011'):
        lx, ly, _ = nodes[leaf]
        out.append(f'<path d="M{lx:.0f} {ly:.0f} L{lx:.0f} {ay:.0f} L{ax:.0f} {ay:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".7" stroke-width="{2.2*s:.1f}" stroke-dasharray="{8*s:.0f} {8*s:.0f}"/>')
    bx = nodes['b000'][0] - 60 * s
    out.append(f'<path d="M{bx + 18*s:.0f} {gens[4]:.0f} L{bx:.0f} {gens[4]:.0f} L{bx:.0f} {ay:.0f} L{bx + 18*s:.0f} {ay:.0f}" fill="none" stroke="{GOLD2}" stroke-width="{2.6*s:.1f}"/>')
    out.append(f'<text x="{bx - 16*s:.0f}" y="{(gens[4] + ay)/2 + 14*s:.0f}" font-size="{40*s:.0f}" text-anchor="end" font-family="Noto Serif CJK SC" font-weight="700" fill="{GOLD2}">g</text>')
    # 小注
    out.append(f'<text x="{W*0.92:.0f}" y="{ground - 26*s:.0f}" font-size="{19*s:.0f}" text-anchor="end" font-family="Noto Sans CJK SC" fill="{DIM}" letter-spacing="{3*s:.0f}">回写派生树</text>')
    out.append(f'<text x="{nx:.0f}" y="{ny - 26*s:.0f}" font-size="{18*s:.0f}" text-anchor="middle" font-family="Noto Sans CJK SC" fill="{CLAY}" letter-spacing="{2*s:.0f}">反面果子 · 新的一支</text>')
    for _ in range(40):
        out.append(f'<circle cx="{rnd.uniform(0, W):.0f}" cy="{rnd.uniform(H*0.44, H*0.47):.0f}" r="{rnd.uniform(.8, 2.2)*s:.1f}" fill="{CREAM}" fill-opacity="{rnd.uniform(.10, .32):.2f}"/>')
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 {M.NO} 号</div>
<div class="t"><div class="pre">AI 撞果子 · 人织谱</div><div class="big big2" style="font-size:{33*s:.1f}pt;line-height:1.36">陶哲轩如何才能<br>与大模型公司<br>和解与合作呢？</div>
<div class="sub">{M.SUBTITLE}</div><div class="rule"></div></div>
<div class="b"><div class="au">{M.AUTHOR}　著</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div>
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
<div class="q">和解不是谈判，<br>是赛道变多。</div><div class="by">——本书结语</div><div class="rule"></div>
<div class="bl"><p>2026 年秋天，菲尔兹奖得主们发出联名宣言，陶哲轩把一次放出的七百多道 AI 证明说成“有毒废料”，许多人把这读成“数学家反 AI”。核对原话以后，问题反而更清楚：陶哲轩不反对 AI，大模型公司也不反对数学；双方谈不拢，是因为挤在统一性数学的同一条跑道上，抢同一颗果子。</p>
<p>本书用 SDE 发生学换一个眼光：数学是 E2 之场，是特征纠缠之间的连接、次序与结构；场结构在一代代回写中分枝成谱，同一性因此有了程度，可以沿回写派生树数出共同祖先的深度 g，在搬一条规律之前先量。AI 在一支里千倍推导，撞出反面果子；人把果子接住，织成谱系的新分叉。</p>
<p>全书前言、四编十四章、结语与四个附录：从宣言与内卷讲起，立起三种同一性、回写派生树与反面果子，设计在形式库、学骑车、细胞、土壤上先测 g 再测 d 的对赌，最后画出陶哲轩与大模型公司各自可走的路线图。</p>
<p>这是一部研究性专著：核心问题、SDE 框架与全书母题由王德生提出，正文由 AI（Claude）协作撰写，经分章质检与统稿；书中人物与场景是构想，第 9–12 章的测量是研究设计，没有实测数据，没有独立学术评审。</p></div>
<div class="gold">AI 撞果子，人织谱。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 {M.NO} 号 · 前言、四编十四章、结语、附录 · 约 {WAN} 万字<br>ISBN {M.ISBN} · 定价 {M.PRICE}</div>
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
