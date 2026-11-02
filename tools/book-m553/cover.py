#!/usr/bin/env python3
"""第 553 号《AI时代出版典范的革命》（王德生 著）封面与封底（工具链承自第 551 号；靛青底，金、青绿、陶红点缀，220 系列版式）：
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
    """主图（第 553 号）：一排一模一样的灰蓝楼房（人人同版的公共平台），旁边一座自己的小屋亮着一盏金灯；
    灯火沿一条金色虚线，一户一户接力到更远处几座亮起一扇窗的小屋（分享）。全部纯色扁平，不用渐变。"""
    import random
    rnd = random.Random(553)
    s = W / 1700
    out = []
    ground = H * 0.80
    # 地面三层纯色带
    for y0, h, col in [(ground, H * 0.026, '#2E4A57'), (ground + H * 0.026, H * 0.024, '#24404D'), (ground + H * 0.050, H * 0.030, '#1B3542')]:
        out.append(f'<rect x="0" y="{y0:.0f}" width="{W}" height="{h:.0f}" fill="{col}"/>')
    # 左：七座一模一样的楼，窗全暗
    bw, bh, gap = 92 * s, 250 * s, 14 * s
    x0 = W * 0.06
    for i in range(7):
        x = x0 + i * (bw + gap)
        out.append(f'<rect x="{x:.0f}" y="{ground - bh:.0f}" width="{bw:.0f}" height="{bh:.0f}" fill="#223650" stroke="#34506E" stroke-width="{2*s:.1f}"/>')
        for r in range(4):
            for c in range(2):
                out.append(f'<rect x="{x + 16*s + c*38*s:.0f}" y="{ground - bh + 22*s + r*56*s:.0f}" width="{24*s:.0f}" height="{30*s:.0f}" fill="#2D4766"/>')
    out.append(f'<text x="{x0 + 3.5*(bw+gap) - gap/2:.0f}" y="{ground - bh - 26*s:.0f}" font-size="{20*s:.0f}" text-anchor="middle" font-family="Noto Sans CJK SC" fill="{DIM}" letter-spacing="{4*s:.0f}">人人同版</text>')
    # 中右：自己的小屋（奶白墙、金色坡顶、一扇亮窗）
    hx, hw, hh = W * 0.665, 250 * s, 300 * s
    hy = ground - hh
    out.append(f'<rect x="{hx:.0f}" y="{hy:.0f}" width="{hw:.0f}" height="{hh:.0f}" fill="{CREAM}"/>')
    out.append(f'<path d="M{hx - 26*s:.0f} {hy:.0f} L{hx + hw/2:.0f} {hy - 150*s:.0f} L{hx + hw + 26*s:.0f} {hy:.0f} Z" fill="{GOLD}"/>')
    out.append(f'<rect x="{hx + hw*0.14:.0f}" y="{hy + 52*s:.0f}" width="{hw*0.72:.0f}" height="{124*s:.0f}" fill="{GOLD2}"/>')
    out.append(f'<rect x="{hx + hw/2 - 3*s:.0f}" y="{hy + 52*s:.0f}" width="{6*s:.0f}" height="{124*s:.0f}" fill="{CREAM}"/>')
    out.append(f'<rect x="{hx + hw*0.14:.0f}" y="{hy + 108*s:.0f}" width="{hw*0.72:.0f}" height="{6*s:.0f}" fill="{CREAM}"/>')
    out.append(f'<rect x="{hx + hw/2 - 28*s:.0f}" y="{ground - 96*s:.0f}" width="{56*s:.0f}" height="{96*s:.0f}" fill="#8C6B2E"/>')
    # 灯光的同心圈（纯色描边，由宽而淡）
    lx, ly = hx + hw / 2, hy + 114 * s
    for r, op in [(330, .08), (260, .12), (195, .20), (140, .30)]:
        out.append(f'<circle cx="{lx:.0f}" cy="{ly:.0f}" r="{r*s:.0f}" fill="none" stroke="{GOLD2}" stroke-opacity="{op}" stroke-width="{2.4*s:.1f}"/>')
    out.append(f'<text x="{lx:.0f}" y="{hy - 190*s:.0f}" font-size="{20*s:.0f}" text-anchor="middle" font-family="Noto Sans CJK SC" fill="{GOLD2}" letter-spacing="{4*s:.0f}">自己的灯</text>')
    # 接力：三座越来越远、越来越小的小屋，各亮一扇窗；金色虚线相连
    pts = [(W * 0.915, ground - 120 * s, 0.50), (W * 0.545, H * 0.52, 0.30), (W * 0.80, H * 0.43, 0.24)]
    prev = (lx, ly)
    for (px, py, k) in pts:
        top = py - 100 * s * k * 2
        out.append(f'<path d="M{prev[0]:.0f} {prev[1]:.0f} Q{(prev[0]+px)/2:.0f} {min(prev[1], py) - 140*s:.0f} {px:.0f} {py - 30*s:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".75" stroke-width="{3.2*s:.1f}" stroke-dasharray="{12*s:.0f} {10*s:.0f}" stroke-linecap="round"/>')
        w, h = 120 * s * k * 2, 120 * s * k * 2
        out.append(f'<rect x="{px - w/2:.0f}" y="{py - h/2:.0f}" width="{w:.0f}" height="{h:.0f}" fill="{CREAM}" fill-opacity=".92"/>')
        out.append(f'<path d="M{px - w/2 - 8*s:.0f} {py - h/2:.0f} L{px:.0f} {py - h/2 - 46*s*k*2:.0f} L{px + w/2 + 8*s:.0f} {py - h/2:.0f} Z" fill="{GOLD}"/>')
        out.append(f'<rect x="{px - w*0.2:.0f}" y="{py - h*0.22:.0f}" width="{w*0.4:.0f}" height="{h*0.38:.0f}" fill="{GOLD2}"/>')
        prev = (px, py - h * 0.03)
    # 零星的火星
    for _ in range(46):
        out.append(f'<circle cx="{rnd.uniform(W*0.45, W):.0f}" cy="{rnd.uniform(H*0.30, ground - 60*s):.0f}" r="{rnd.uniform(1.2, 3.4)*s:.1f}" fill="{rnd.choice([GOLD2, CREAM])}" fill-opacity="{rnd.uniform(.12, .5):.2f}"/>')
    out.append(f'<text x="{W*0.92:.0f}" y="{ground + 44*s:.0f}" font-size="{19*s:.0f}" text-anchor="end" font-family="Noto Sans CJK SC" fill="{DIM}" letter-spacing="{3*s:.0f}">星星之火 · 一户一户接力</text>')
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
<div class="t"><div class="pre">出版：知识的发生，而不是发现</div><div class="big big2" style="font-size:{36*s:.1f}pt;line-height:1.36">AI时代<br>出版典范的革命</div>
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
<div class="q">出版：知识的发生，<br>而不是发现。</div><div class="by">——王德生</div><div class="rule"></div>
<div class="bl"><p>一份报纸每天登一道菜谱，一万人读到同一道菜；一间厨房让人进来学做菜，你走时带走的是你自己的做法。本书说，出版正经历从前者到后者的典范转移：从发现到发生，从公共平台到个人的、复合体的、部落性的知识发生系统。</p>
<p>人和 AI 把“结论”的生产变得几乎不要钱，投稿、编辑、出版三头内卷。出路是知识的典范转移：同一性谱系知识需要的不是更大的广场，而是一个能让它在自己的条件下一代一代发生的地方。统一性知识的出版平台不会消失，它们会降级、降价，成为基础设施。</p>
<p>全书导论、六编二十四章、结语：先拆旧典范，再讲读者怎样从消费走到进入，传播怎样靠分享而不靠大流量，作者与系统怎样建造，最后说风险与边界。主线是一条有条件的因果链：若谱系知识成为知识经济的主流领地，出版就要从公布发现变成托管发生。</p>
<p>这是一部研究性专著：核心命题由王德生口述提出，正文由 AI（Claude）协作撰写，经三审与统稿；书中人物与场景是构想，没有实测数据，没有独立学术评审。作者主持的 SDE 平台是全书的活样本，做到的与没做到的都如实写出。</p></div>
<div class="gold">点一盏灯，星星之火。</div></div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 {M.NO} 号 · 前言、导论、六编二十四章、结语、附录 · 约 {WAN} 万字<br>ISBN {M.ISBN} · 定价 {M.PRICE}</div>
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
