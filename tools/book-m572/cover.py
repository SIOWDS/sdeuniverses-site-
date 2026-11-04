#!/usr/bin/env python3
"""第 572 号《K线人生——跃迁无法设计，只能接住》（段君毅　王德生 著）封面与封底（工具链承自第 571 号，藏青底、金青奶白三色，220 系列版式）：
主图：几条K线缠成的洪流——三条速度各异的线互相缠绕向前，挤进一团碰撞，旧线断成虚线散去，一条新线从碰撞里陡然升起，下面一道托弧（接住）。
全部矢量绘制、纯色，不用照片、不用渐变。封面不写「指导」字样，作者栏写「段君毅　王德生　著」。
用法：python3 cover.py --fonts /usr/share/fonts/opentype/noto --out <dir>
"""
import argparse
import math
import os
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0C1A34', '#1B3158', '#16294A'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#7FA7C9', '#EFE8D6', '#A9B6C8'
ISBN = '979-8-90690-591-8'
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
    """主图（第 572 号）：几条K线缠成的洪流，旧结构死去处碰撞，一条新线从碰撞里冒出来，下面一只托住它的弧。
    左半：三条速度各异的线（金＝创造、青＝自由、奶白＝幸福）互相缠绕向前，线上点缀小阴阳烛；
    中右：三条线挤进一团碰撞（短促的乱线），旧线从这里断成虚线、往下散去；
    碰撞上方：一条新线陡然升起，带几根更大的阳烛；碰撞下方一道金色托弧（接住）。全部纯色，不用渐变。"""
    import random
    rnd = random.Random(572)
    s = W / 1700
    out = []
    base = H * 0.60
    # 价格图的淡网格
    for k in range(7):
        yy = H * 0.44 + k * H * 0.05
        out.append(f'<line x1="{W*0.05:.0f}" y1="{yy:.0f}" x2="{W*0.95:.0f}" y2="{yy:.0f}" stroke="{DIM}" stroke-opacity=".10" stroke-width="{1.4*s:.1f}"/>')
    for k in range(10):
        xx = W * 0.05 + k * W * 0.1
        out.append(f'<line x1="{xx:.0f}" y1="{H*0.42:.0f}" x2="{xx:.0f}" y2="{H*0.76:.0f}" stroke="{DIM}" stroke-opacity=".06" stroke-width="{1.2*s:.1f}"/>')
    kx = W * 0.60          # 碰撞点
    ky = base - 40 * s
    x0 = W * 0.05
    cols = (GOLD2, CYAN, CREAM)
    speeds = (1.0, 1.45, 0.75)
    amps = (95, 72, 105)
    lines = []
    for i in range(3):
        pts = []
        n = 90
        for j in range(n + 1):
            t = j / n
            x = x0 + (kx - x0) * t
            ph = i * 2.1
            env = (1 - t) ** 1.2 * 0.85 + 0.15
            y = base + 30 * s * (1 - t) - 70 * s * t + amps[i] * s * env * math.sin(t * math.pi * 3.2 * speeds[i] + ph)
            # 末端收进碰撞点
            w = max(0, (t - 0.82) / 0.18)
            y = y * (1 - w) + ky * w
            x = x * (1 - w) + kx * w
            pts.append((x, y))
        lines.append(pts)
    # 先画线，后画烛
    for i, pts in enumerate(lines):
        d = 'M' + ' L'.join('%.1f %.1f' % p for p in pts)
        out.append(f'<path d="{d}" fill="none" stroke="{cols[i]}" stroke-width="{(8 if i == 0 else 6.5)*s:.1f}" stroke-linecap="round" stroke-linejoin="round" stroke-opacity=".95"/>')
    for i, pts in enumerate(lines):
        for j in range(6 + i * 3, 74, 11 + i * 2):
            x, y = pts[j]
            up = pts[j + 1][1] < pts[j - 1][1]
            bh = (16 + rnd.uniform(0, 14)) * s
            bw = 11 * s
            out.append(f'<line x1="{x:.0f}" y1="{y-bh-12*s:.0f}" x2="{x:.0f}" y2="{y+bh*0.3+12*s:.0f}" stroke="{cols[i]}" stroke-width="{2*s:.1f}"/>')
            if up:
                out.append(f'<rect x="{x-bw/2:.0f}" y="{y-bh:.0f}" width="{bw:.0f}" height="{bh*1.3:.0f}" fill="{NAVY_TOP}" stroke="{cols[i]}" stroke-width="{2.4*s:.1f}"/>')
            else:
                out.append(f'<rect x="{x-bw/2:.0f}" y="{y-bh:.0f}" width="{bw:.0f}" height="{bh*1.3:.0f}" fill="{cols[i]}"/>')
    # 旧线：碰撞之后断成虚线，往下散开
    for i, (dx, dy) in enumerate(((260, 120), (300, 190), (230, 250))):
        out.append(f'<path d="M{kx+18*s:.0f} {ky+10*s:.0f} Q{kx+dx*0.5*s:.0f} {ky+dy*0.2*s:.0f} {kx+dx*s:.0f} {ky+dy*s:.0f}" fill="none" stroke="{cols[i]}" stroke-opacity=".38" stroke-width="{4*s:.1f}" stroke-dasharray="{10*s:.0f} {12*s:.0f}" stroke-linecap="round"/>')
    # 碰撞：一团短促的乱线
    for k in range(56):
        a = rnd.uniform(0, 2 * math.pi); r = rnd.uniform(6, 66) * s; l = rnd.uniform(18, 50) * s
        x1, y1 = kx + r * math.cos(a), ky + r * math.sin(a) * 0.8
        b = a + rnd.uniform(-2.2, 2.2)
        out.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x1+l*math.cos(b):.0f}" y2="{y1+l*math.sin(b):.0f}" stroke="{cols[k % 3]}" stroke-opacity="{rnd.uniform(.45, .9):.2f}" stroke-width="{rnd.uniform(2, 4)*s:.1f}" stroke-linecap="round"/>')
    out.append(f'<circle cx="{kx:.0f}" cy="{ky:.0f}" r="{86*s:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".35" stroke-width="{2*s:.1f}" stroke-dasharray="{4*s:.0f} {6*s:.0f}"/>')
    # 托弧：接住
    out.append(f'<path d="M{kx-125*s:.0f} {ky+52*s:.0f} Q{kx:.0f} {ky+205*s:.0f} {kx+125*s:.0f} {ky+52*s:.0f}" fill="none" stroke="{GOLD}" stroke-width="{7*s:.1f}" stroke-linecap="round"/>')
    for sx in (-1, 1):
        out.append(f'<circle cx="{kx+sx*125*s:.0f}" cy="{ky+52*s:.0f}" r="{7*s:.1f}" fill="{GOLD}"/>')
    # 新线：从碰撞里陡然升起
    nx0, ny0 = kx + 10 * s, ky - 30 * s
    nx1, ny1 = W * 0.93, H * 0.37
    pts = []
    for j in range(41):
        t = j / 40
        x = nx0 + (nx1 - nx0) * t
        y = ny0 + (ny1 - ny0) * (t ** 1.35) + 12 * s * math.sin(t * math.pi * 4) * (1 - t)
        pts.append((x, y))
    d = 'M' + ' L'.join('%.1f %.1f' % p for p in pts)
    out.append(f'<path d="{d}" fill="none" stroke="#F7F1E3" stroke-width="{10*s:.1f}" stroke-linecap="round" stroke-linejoin="round"/>')
    for j in (10, 18, 26, 34):
        x, y = pts[j]
        bh = (34 + j) * s; bw = 18 * s
        out.append(f'<line x1="{x:.0f}" y1="{y-bh*0.8-14*s:.0f}" x2="{x:.0f}" y2="{y+bh*0.5+14*s:.0f}" stroke="{GOLD2}" stroke-width="{2.6*s:.1f}"/>')
        out.append(f'<rect x="{x-bw/2:.0f}" y="{y-bh*0.8:.0f}" width="{bw:.0f}" height="{bh*1.3:.0f}" fill="{NAVY_TOP}" stroke="{GOLD2}" stroke-width="{3*s:.1f}"/>')
    x, y = pts[-1]
    out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{11*s:.0f}" fill="{GOLD2}"/>')
    # 注脚三行
    ty2 = H * 0.775
    for xx, anc, big, small, col in ((W * 0.08, 'start', '1 到 N', '三条线轮流领头', GOLD2), (W * 0.5, 'middle', '碰撞', '旧结构死去，几条线撞在一起', CREAM), (W * 0.92, 'end', '0 到 1', '一条新线，只能接住', CYAN)):
        out.append(f'<text x="{xx:.0f}" y="{ty2:.0f}" font-size="{36*s:.0f}" text-anchor="{anc}" font-family="Noto Serif CJK SC" font-weight="700" fill="{col}" letter-spacing="{4*s:.0f}">{big}</text>')
        out.append(f'<text x="{xx:.0f}" y="{ty2 + 40*s:.0f}" font-size="{20*s:.0f}" text-anchor="{anc}" font-family="Noto Sans CJK SC" fill="{DIM}" letter-spacing="{3*s:.0f}">{small}</text>')
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 572 号</div>
<div class="t"><div class="pre">从一根线到一束线</div><div class="big">K线人生</div>
<div class="sub">跃迁无法设计，只能接住</div><div class="rule"></div></div>
<div class="b"><div class="au">段君毅　王德生　著</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div>
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
           f'{background(W, H, "b", split=0.715)}{emb}{"".join(waves)}{bc}</svg>')
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
<div class="c"><div class="lab">母 题</div>
<div class="q">人生不是一张K线图，<br>而是几条K线缠成的洪流。<br>跃迁无法设计，<br>能设计的只是让碰撞发生，<br>并且接得住它。</div><div class="by">——本书母题</div><div class="rule"></div>
<div class="bl"><p>段君毅的原书把交易员的冷静带进人生：人生有结构，结构有惯性，惯性有周期，周期可以被识别。本书留下这前半，翻转后半——跃迁不能设计。</p>
<p>人生不是一根线，而是几条速度各异、互相缠绕的线。创造、自由、幸福三条线轮流领头，再陡的上涨也只是1到N；旧结构死去，几条线在混沌里相撞，底子里的种子才可能长成一条新线。</p>
<p>下跌也分四种：真回撤、复权跌、发生跌、耗散跌。把后三种错认成第一种，在跃迁关口退回原位，是本书最想帮你避开的错。</p>
<p>十人回溯检验先写规则、后看史料：一条判断被撤回，一条不成立，都照实写进第26章。普通人案例均为构造；本书不预言涨跌，不给投资建议。</p></div>
<div class="gold">跃迁无法设计，只能接住。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 572 号 · 前言、八编二十七章、尾声、附录 · 约 {WAN} 万字<br>ISBN 979-8-90690-591-8 · 定价 US$20.00</div>
</div></div></body></html>"""


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
