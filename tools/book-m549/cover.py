#!/usr/bin/env python3
"""第 549 号《今天的善为何很难发生了？》（王德生 著）封面与封底（工具链承自第 547 号，藏青底、金青奶白三色，220 系列版式）：
主图：河边石阶，岸上三人站着；最下一级有人蹲下伸手，水里升起另一只手，两手之间一圈金环。全部纯色，不用渐变。
用法：python3 cover.py --fonts /usr/share/fonts/opentype/noto --out <dir>
"""
import argparse
import math
import os
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0C1A34', '#1B3158', '#16294A'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#7FA7C9', '#EFE8D6', '#A9B6C8'
ISBN = '979-8-90690-551-2'
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
    """主图（第 549 号）：河边的石阶。岸上三个人站着没动；最下一级有人蹲下，伸出一只手；
    水里升起另一只手。两只手之间留一道缝，缝上一圈金环——善在这里发生。全部纯色，不用渐变。"""
    import random
    rnd = random.Random(549)
    s = W / 1700
    out = []
    x0 = W * 0.08
    ytop, hstep, wstep, nstep = H * 0.47, 90 * s, 150 * s, 4
    yw = ytop + hstep * nstep            # 水面
    yb = H * 0.735                       # 水底
    # 水：淡青块＋波纹
    out.append(f'<rect x="0" y="{yw:.0f}" width="{W}" height="{yb - yw:.0f}" fill="{CYAN}" fill-opacity=".10"/>')
    for k in range(7):
        y0 = yw + 30 * s + (yb - yw - 50 * s) * k / 6
        d = 'M0 %.0f' % y0
        n = 8
        for i in range(n):
            d += ' Q%.0f %.0f %.0f %.0f' % (W * (i + .5) / n, y0 + (9 if (i + k) % 2 else -9) * s, W * (i + 1) / n, y0 + rnd.uniform(-2, 2) * s)
        out.append(f'<path d="{d}" fill="none" stroke="{CYAN}" stroke-opacity="{.42 - .04 * k:.2f}" stroke-width="{2.6*s:.1f}" stroke-linecap="round"/>')
    # 石阶：一级一级通到水里
    d = 'M0 %.0f L%.0f %.0f' % (ytop, x0, ytop)
    for k in range(nstep):
        d += ' L%.0f %.0f L%.0f %.0f' % (x0 + (k + 1) * wstep, ytop + k * hstep, x0 + (k + 1) * wstep, ytop + (k + 1) * hstep)
    d += ' L%.0f %.0f L0 %.0f Z' % (x0 + nstep * wstep, yb, yb)
    out.append(f'<path d="{d}" fill="{CREAM}" fill-opacity=".14" stroke="{GOLD}" stroke-opacity=".55" stroke-width="{2.4*s:.1f}" stroke-linejoin="round"/>')
    # 岸上的三个人：站着，淡色
    for k, xx in enumerate((x0 - 70 * s, x0 + 10 * s, x0 + 92 * s)):
        yy = ytop if xx < x0 + 8 * s else ytop
        hh = (112, 124, 106)[k] * s
        out.append(f'<circle cx="{xx + 22*s:.0f}" cy="{yy - hh - 16*s:.0f}" r="{17*s:.0f}" fill="{DIM}" fill-opacity=".55"/>')
        out.append(f'<path d="M{xx + 8*s:.0f} {yy:.0f} L{xx + 2*s:.0f} {yy - hh + 18*s:.0f} Q{xx + 4*s:.0f} {yy - hh:.0f} {xx + 22*s:.0f} {yy - hh:.0f} Q{xx + 40*s:.0f} {yy - hh:.0f} {xx + 42*s:.0f} {yy - hh + 18*s:.0f} L{xx + 36*s:.0f} {yy:.0f} Z" fill="{DIM}" fill-opacity=".45"/>')
    # 最下一级：蹲下的人，伸出手
    sx, sy = x0 + (nstep - 1) * wstep + 40 * s, ytop + (nstep - 1) * hstep   # 那一级的台面
    out.append(f'<circle cx="{sx + 30*s:.0f}" cy="{sy - 128*s:.0f}" r="{22*s:.0f}" fill="{GOLD2}"/>')
    out.append(f'<path d="{tapered([(sx - 4*s, sy - 4*s), (sx + 6*s, sy - 60*s), (sx + 26*s, sy - 100*s)], 40 * s, 26 * s)}" fill="{GOLD2}"/>')
    out.append(f'<path d="{tapered([(sx - 2*s, sy - 6*s), (sx + 46*s, sy - 30*s), (sx + 56*s, sy - 2*s)], 18 * s, 13 * s)}" fill="{GOLD2}"/>')
    hx, hy = sx + 210 * s, yw - 78 * s                                         # 岸上的手
    out.append(f'<path d="{tapered([(sx + 30*s, sy - 92*s), (sx + 110*s, sy - 70*s), (hx - 14*s, hy - 8*s)], 15 * s, 10 * s)}" fill="{GOLD2}"/>')
    out.append(f'<circle cx="{hx:.0f}" cy="{hy:.0f}" r="{13*s:.0f}" fill="{GOLD2}"/>')
    wx, wy = hx + 58 * s, hy + 26 * s                                          # 水里的手
    ex = wx + 46 * s
    out.append(f'<path d="{tapered([(ex, yw + 30*s), (ex - 8*s, yw - 4*s), (wx + 6*s, wy + 10*s)], 18 * s, 12 * s)}" fill="{CREAM}"/>')
    out.append(f'<circle cx="{wx:.0f}" cy="{wy:.0f}" r="{12*s:.0f}" fill="{CREAM}"/>')
    for k, (rx, ry) in enumerate(((54, 12), (92, 20), (134, 28))):            # 水圈
        out.append(f'<ellipse cx="{ex:.0f}" cy="{yw + 22*s:.0f}" rx="{rx*s:.0f}" ry="{ry*s:.0f}" fill="none" stroke="{CREAM}" stroke-opacity="{.6 - .17*k:.2f}" stroke-width="{2.4*s:.1f}"/>')
    # 缝：两只手之间一圈金环
    gx, gy = (hx + wx) / 2, (hy + wy) / 2
    out.append(f'<circle cx="{gx:.0f}" cy="{gy:.0f}" r="{44*s:.0f}" fill="none" stroke="{GOLD2}" stroke-width="{3.6*s:.1f}"/>')
    out.append(f'<circle cx="{gx:.0f}" cy="{gy:.0f}" r="{72*s:.0f}" fill="none" stroke="{GOLD2}" stroke-opacity=".32" stroke-width="{2.2*s:.1f}"/>')
    out.append(f'<circle cx="{gx:.0f}" cy="{gy:.0f}" r="{6*s:.0f}" fill="{GOLD2}"/>')
    # 对岸：远处一排楼
    for k in range(9):
        bw = rnd.uniform(70, 120) * s; bh = rnd.uniform(90, 210) * s
        bx = W * 0.52 + k * 88 * s
        if bx + bw > W: break
        out.append(f'<rect x="{bx:.0f}" y="{H*0.56 - bh:.0f}" width="{bw:.0f}" height="{bh:.0f}" fill="{NAVY_TOP}" fill-opacity=".65"/>')
        for r in range(int(bh // (30 * s)) - 1):
            if rnd.random() < .35:
                out.append(f'<rect x="{bx + 14*s:.0f}" y="{H*0.56 - bh + (16 + 30*r)*s:.0f}" width="{10*s:.0f}" height="{12*s:.0f}" fill="{GOLD2}" fill-opacity=".55"/>')
    out.append(f'<line x1="{W*0.50:.0f}" y1="{H*0.56:.0f}" x2="{W:.0f}" y2="{H*0.56:.0f}" stroke="{GOLD}" stroke-opacity=".35" stroke-width="{2*s:.1f}"/>')
    # 标注：三道堵
    ty = yb + 66 * s
    x1 = W * 0.92
    for xx, anc, big, small, col in ((x0, 'start', '缝', '逻辑吃掉自由律', CYAN), (W * 0.5, 'middle', '人', '人人算最小亏损', GOLD2), (x1, 'end', '落地', '评估挪到了前面', CREAM)):
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 549 号</div>
<div class="t"><div class="pre">善的发生学 · 三道堵</div><div class="big big2" style="font-size:{33*s:.1f}pt">今天的善，<br>为何很难发生了？</div>
<div class="sub">善的发生学与<br>技术世界里的三道堵</div><div class="rule"></div></div>
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
<div class="q">今天善难发生，<br>不是人心坏了。</div><div class="by">——本书第三章</div><div class="rule"></div>
<div class="bl"><p>老人落水，岸上站着十个人，没有一个跳下去。不是谁的心冷了。本书说，善不是装在心里、碰到事情拿出来用的东西；善是发生，是在人和人之间一来一回走出来的。</p>
<p>今天的善难发生，是三道堵：逻辑吃掉了自由律，事事有流程，没有缝；人人计算势能的最小亏损，场里没有人；事事先作理性评估，善还没走就被算完，没有落地。三道堵也是一把刀，用来重读孟子、荀子、康德、朱熹与阳明。</p>
<p>全书序、六编十七章、结语，从河边、楼道、公交车、外卖这些日常小事讲起，讲善的三个号位（客体善、善行、主体善），讲三道堵怎样相撞、合拢，再讲六条路径与几把钥匙怎样让善重新走起来，最后写这本书自己会怎样错。</p>
<p>这是一部研究性专著：核心问题与主干判断由王德生口述提出，正文由 AI（Claude）协作撰写并经质检回改；书中的人物与场景是构想，推翻条件尚待检验，没有独立学术评审。</p></div>
<div class="gold">善，是发生学。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 549 号 · 序、六编十七章、结语 · 约 {WAN} 万字<br>ISBN 979-8-90690-551-2 · 定价 US$20.00</div>
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
