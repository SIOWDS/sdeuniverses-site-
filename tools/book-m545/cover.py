#!/usr/bin/env python3
"""第 545 号《AI时代什么知识最值钱？》（王德生 著）封面与封底（工具链承自第 536、532 号，藏青底、金青奶白三色，220 系列版式）：
主图是一棵树立在剖开的土里：果子是 S，树是 D，土（根、层、颗粒）是 E，土画得比树深、比树密；虚线弧是回写。全部纯色，不用渐变。
用法：python3 cover.py --fonts /home/claude/fonts --out <dir>
"""
import argparse
import math
import os
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0C1A34', '#1B3158', '#16294A'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#7FA7C9', '#EFE8D6', '#A9B6C8'
ISBN = '979-8-90690-546-8'
WAN = os.environ.get('WAN', '24')

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
    """主图（第 545 号）：一棵树立在一方剖开的土里——树梢的果子是 S（显露），树干与枝是 D（差异序列），
    土里的根、层、颗粒是 E（特征纠缠）：土画得比树深、比树密。落叶与落果沿虚线弧落回土里（回写）。
    土里三色颗粒：金＝三界，青＝信息，奶白＝能量。全部纯色，不用渐变。"""
    import random
    rnd = random.Random(545)
    s = W / 1700
    cx = W * 0.5
    yg = H * 0.56                      # 地面线
    yb = H * 0.735                      # 土层底
    x0, x1 = W * 0.12, W * 0.88
    out = []
    # 土的剖面：底色块＋三道起伏的层线
    out.append(f'<rect x="{x0:.0f}" y="{yg:.0f}" width="{x1 - x0:.0f}" height="{yb - yg:.0f}" fill="{CREAM}" fill-opacity=".07" stroke="{GOLD}" stroke-opacity=".35" stroke-width="{2*s:.1f}"/>')
    for k, fy in enumerate((0.30, 0.58, 0.82)):
        y0 = yg + (yb - yg) * fy
        d = 'M%.0f %.0f' % (x0, y0)
        n = 8
        for i in range(n):
            xm = x0 + (x1 - x0) * (i + .5) / n; xe = x0 + (x1 - x0) * (i + 1) / n
            d += ' Q%.0f %.0f %.0f %.0f' % (xm, y0 + (14 if i % 2 else -14) * s * (1 + k * .3), xe, y0)
        out.append(f'<path d="{d}" fill="none" stroke="{CREAM}" stroke-opacity="{.30 - k*.06:.2f}" stroke-width="{2.4*s:.1f}"/>')
    # 土里的颗粒：三界（金）·信息（青）·能量（奶白）
    cols = [GOLD2, CYAN, CREAM]
    for _ in range(190):
        x = rnd.uniform(x0 + 14 * s, x1 - 14 * s); y = rnd.uniform(yg + 14 * s, yb - 14 * s)
        c = rnd.choice(cols)
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rnd.uniform(2.2, 6.5)*s:.1f}" fill="{c}" fill-opacity="{rnd.uniform(.35, .85):.2f}"/>')
    # 根：递归分叉，青色，越分越细
    def root(x, y, ang, ln, w, depth):
        if depth == 0 or ln < 18 * s:
            return
        pts = []
        steps = 8
        a = ang
        px, py = x, y
        for i in range(steps + 1):
            pts.append((px, py))
            a += rnd.uniform(-.22, .22)
            px += math.cos(a) * ln / steps; py += math.sin(a) * ln / steps
            py = min(py, yb - 8 * s); px = max(x0 + 8 * s, min(x1 - 8 * s, px))
        out.append(f'<path d="{tapered(pts, w, max(w*.35, 1.4*s))}" fill="{CYAN}" fill-opacity="{.35 + .12*depth:.2f}"/>')
        ex, ey = pts[-1]
        for da in (-.65, .55):
            root(ex, ey, a + da + rnd.uniform(-.2, .2), ln * .72, w * .62, depth - 1)
        if depth >= 4:
            mx, my = pts[len(pts)//2]
            root(mx, my, ang + rnd.choice((-1, 1)) * 1.0, ln * .5, w * .5, depth - 2)
    for k, ang in enumerate((math.pi/2 - .95, math.pi/2 - .4, math.pi/2 + .05, math.pi/2 + .5, math.pi/2 + 1.0)):
        root(cx + (k - 2) * 6 * s, yg + 4 * s, ang, 150 * s, 15 * s, 5)
    # 树：树干＋枝，金色
    K = 1.35
    tp = [(cx, yg + 3 * s), (cx + 8 * s * K, yg - 70 * s * K), (cx - 6 * s * K, yg - 150 * s * K), (cx + 4 * s * K, yg - 222 * s * K)]
    trunk = [bez(tp[0], tp[1], tp[2], tp[3], i / 20) for i in range(21)]
    out.append(f'<path d="{tapered(trunk, 34 * s, 12 * s)}" fill="{GOLD}" fill-opacity=".92"/>')
    top = trunk[-1]
    branches = [(-1, 150, 120), (1, 160, 115), (-1, 105, 175), (1, 100, 170), (-1, 60, 220), (1, 55, 215)]
    fruits = []
    for side, dx, dy in branches:
        by_ = top[1] + 150 * s - dy * s * 0.0 - (dy - 100) * s * .55
        sx, sy = trunk[int(20 * (1 - (dy - 55) / 200))] if True else top
        ex, ey = sx + side * dx * s * K, sy - dy * .5 * s * K
        bp = [bez((sx, sy), (sx + side * 40 * s, sy - 10 * s), (ex - side * 40 * s, ey + 25 * s), (ex, ey), i / 14) for i in range(15)]
        out.append(f'<path d="{tapered(bp, 12 * s, 4 * s)}" fill="{GOLD}" fill-opacity=".9"/>')
        fruits.append((ex, ey))
    fruits.append((top[0], top[1] - 24 * s))
    # 果子（S）：奶白圆，亮边
    for (fx, fy) in fruits:
        out.append(f'<circle cx="{fx:.0f}" cy="{fy:.0f}" r="{19*s:.0f}" fill="{CREAM}" fill-opacity=".92"/>')
        out.append(f'<circle cx="{fx:.0f}" cy="{fy:.0f}" r="{27*s:.0f}" fill="none" stroke="{CREAM}" stroke-opacity=".28" stroke-width="{2*s:.1f}"/>')
    # 回写：几条虚线弧，从果子落回土里，尾端有小箭头
    for k, (fx, fy) in enumerate(fruits[:5]):
        tx = fx + (-1 if k % 2 else 1) * rnd.uniform(70, 150) * s
        ty = yg + rnd.uniform(70, 150) * s
        mx, my = (fx + tx) / 2 + (-1 if k % 2 else 1) * 70 * s, (fy + ty) / 2 - 20 * s
        out.append(f'<path d="M{fx:.0f} {fy + 30*s:.0f} Q{mx:.0f} {my:.0f} {tx:.0f} {ty:.0f}" fill="none" stroke="{GOLD2}" stroke-opacity=".65" stroke-width="{2.6*s:.1f}" stroke-dasharray="{10*s:.0f} {9*s:.0f}"/>')
        out.append(f'<circle cx="{tx:.0f}" cy="{ty:.0f}" r="{6*s:.1f}" fill="{GOLD2}"/>')
    # 地面线
    out.append(f'<line x1="{x0 - 30*s:.0f}" y1="{yg:.0f}" x2="{x1 + 30*s:.0f}" y2="{yg:.0f}" stroke="{GOLD2}" stroke-width="{4*s:.1f}" stroke-linecap="round"/>')
    # 标注
    ty = yb + 66 * s
    for xx, anc, big, small, col in ((x0, 'start', '果子 · S', '显露', CREAM), (cx, 'middle', '树 · D', '差异序列', GOLD2), (x1, 'end', '土 · E', '特征纠缠', CYAN)):
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 545 号</div>
<div class="t"><div class="pre">知识经济 · 同一性谱系知识</div><div class="big big2" style="font-size:{33*s:.1f}pt">AI时代<br>什么知识<br>最值钱？</div>
<div class="sub">知识经济在<br>E 的土壤里出生</div><div class="rule"></div></div>
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
<div class="q">AI 能把露水收尽。<br>它收不走的，在土里。</div><div class="by">——本书序言</div><div class="rule"></div>
<div class="bl"><p>AI 时代，会写的、会算的、会查的，越来越不稀缺。人一生真正依靠的，是一块沉了很多年的土：习惯、分寸、信任、对自己的看法。本书把这块土叫做 E（特征纠缠），把它和显露出来的果子 S、一次次重来的路径 D 放在一起看，追问：什么知识，才是 AI 时代最值钱的？</p>
<p>全书五篇二十章，从一位阿姨的存折和一位大叔的账本讲起，经土壤与回写，看统一性科学怎样把 E 简化、数学怎样成了 E 的最大统一，再落到四种最值钱的 E 知识：划型、在场读型、加厚、迁移；最后说，知识经济为什么要在 E 的土壤里才出生，主体性经济是什么样子。</p>
<p>这是一部研究性专著：核心思想由王德生提出，正文由 AI（Claude）协作撰写并经三审修订；书中的人物与场景多为构想，所列判错条件与预测尚待检验，没有独立学术评审，也没有用户试验。</p></div>
<div class="gold">真正的知识经济，来源于 E 的同一性谱系化。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 545 号 · 五篇二十章 · 约 {WAN} 万字<br>ISBN 979-8-90690-546-8 · 定价 US$20.00</div>
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
