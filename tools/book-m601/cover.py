#!/usr/bin/env python3
"""第 601 号《持续创造何以可能》（王德生 著）封面与封底（工具链承自第 550 号，藏青底、金青奶白三色，220 系列版式）：
主图：一只轮子、一个奔跑的人、一条三圈的思考跑道（张力·转换·释放）。全部纯色，不用渐变。封面不写「王德生指导」。
用法：python3 cover.py --fonts /usr/share/fonts/opentype/noto --out <dir>
"""
import argparse
import math
import os
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0C1A34', '#1B3158', '#16294A'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#7FA7C9', '#EFE8D6', '#A9B6C8'
ISBN = '979-8-90690-631-1'
WAN = os.environ.get('WAN', '30.6')

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
    """主图（第 601 号）：左，一枚金色的圆（人）；右，一块青色的圆角方（工具）；两者各伸出一道弧，在中间上方汇成一个小三角（S3·D3·E3 三点相连，复合体）；
    三角下方一条细虚线折回地面（回写）。全部纯色，不用渐变。"""
    import random
    rnd = random.Random(601)
    s = W / 1700
    out = []
    ground = H * 0.60
    out.append(f'<line x1="0" y1="{ground:.0f}" x2="{W:.0f}" y2="{ground:.0f}" stroke="{GOLD}" stroke-opacity=".45" stroke-width="{2.2*s:.1f}"/>')
    # 左：人（金色圆，外圈留缺口）
    hx, hy = W * 0.20, ground - 150 * s
    out.append(f'<circle cx="{hx:.0f}" cy="{hy:.0f}" r="{92*s:.0f}" fill="{GOLD2}"/>')
    for r, w, gap in ((130, 7, 56),):
        a0 = math.radians(-gap / 2); a1 = math.radians(gap / 2)
        x0, y0 = hx + r * s * math.cos(a1), hy + r * s * math.sin(a1)
        x1, y1 = hx + r * s * math.cos(a0), hy + r * s * math.sin(a0)
        out.append(f'<path d="M{x0:.1f} {y0:.1f} A{r*s:.0f} {r*s:.0f} 0 1 1 {x1:.1f} {y1:.1f}" fill="none" stroke="{GOLD}" stroke-width="{w*s:.1f}" stroke-linecap="round"/>')
    # 右：工具（青色圆角方）
    tx, ty, tw = W * 0.80, ground - 150 * s, 168 * s
    out.append(f'<rect x="{tx - tw/2:.0f}" y="{ty - tw/2:.0f}" width="{tw:.0f}" height="{tw:.0f}" rx="{22*s:.0f}" fill="{CYAN}"/>')
    out.append(f'<rect x="{tx - tw/2 - 26*s:.0f}" y="{ty - tw/2 - 26*s:.0f}" width="{tw + 52*s:.0f}" height="{tw + 52*s:.0f}" rx="{34*s:.0f}" fill="none" stroke="{CYAN}" stroke-opacity=".5" stroke-width="{5*s:.1f}"/>')
    # 中：复合体（三点相连的小三角）
    cx3, cy3 = W * 0.50, ground - 330 * s
    tri = [(cx3, cy3 - 70 * s), (cx3 - 80 * s, cy3 + 62 * s), (cx3 + 80 * s, cy3 + 62 * s)]
    out.append('<path d="M' + ' L'.join('%.1f %.1f' % p for p in tri) + f' Z" fill="none" stroke="{GOLD2}" stroke-width="{5*s:.1f}" stroke-linejoin="round"/>')
    for (px, py), col in zip(tri, (GOLD2, CREAM, CYAN)):
        out.append(f'<circle cx="{px:.0f}" cy="{py:.0f}" r="{18*s:.0f}" fill="{col}"/>')
    # 两道弧：人→复合体，工具→复合体
    p0 = (hx + 70 * s, hy - 70 * s); p3 = (tri[1][0] - 22 * s, tri[1][1] - 6 * s)
    pts = [bez(p0, (p0[0] + 120 * s, p0[1] - 150 * s), (p3[0] - 150 * s, p3[1] - 40 * s), p3, t / 40) for t in range(41)]
    out.append(f'<path d="{tapered(pts, 14*s, 3.4*s)}" fill="{GOLD2}"/>')
    q0 = (tx - 70 * s, ty - 70 * s); q3 = (tri[2][0] + 22 * s, tri[2][1] - 6 * s)
    pts2 = [bez(q0, (q0[0] - 120 * s, q0[1] - 150 * s), (q3[0] + 150 * s, q3[1] - 40 * s), q3, t / 40) for t in range(41)]
    out.append(f'<path d="{tapered(pts2, 14*s, 3.4*s)}" fill="{CYAN}"/>')
    # 回写：三角下方折回地面的细虚线
    r0 = (cx3, cy3 + 90 * s); r3 = (W * 0.50, ground - 6 * s)
    out.append(f'<path d="M{r0[0]:.1f} {r0[1]:.1f} L{r3[0]:.1f} {r3[1]:.1f}" fill="none" stroke="{CREAM}" stroke-opacity=".7" stroke-width="{4*s:.1f}" stroke-linecap="round" stroke-dasharray="{14*s:.0f} {12*s:.0f}"/>')
    out.append(f'<circle cx="{r3[0]:.0f}" cy="{r3[1]:.0f}" r="{8*s:.1f}" fill="{CREAM}"/>')
    ty2 = ground + 120 * s
    for xx, anc, big, small, col in ((W * 0.20, 'middle', '人', '承担目标与后果', GOLD2), (W * 0.50, 'middle', '复合体', '真·善·美 的运行状态', CREAM), (W * 0.80, 'middle', '工具', '符号·仪器·算法·AI', CYAN)):
        out.append(f'<text x="{xx:.0f}" y="{ty2:.0f}" font-size="{36*s:.0f}" text-anchor="{anc}" font-family="Noto Serif CJK SC" font-weight="700" fill="{col}" letter-spacing="{4*s:.0f}">{big}</text>')
        out.append(f'<text x="{xx:.0f}" y="{ty2 + 40*s:.0f}" font-size="{20*s:.0f}" text-anchor="{anc}" font-family="Noto Sans CJK SC" fill="{DIM}" letter-spacing="{3*s:.0f}">{small}</text>')
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 601 号</div>
<div class="t"><div class="pre">人—工具复合体的发生学</div><div class="big big2" style="font-size:{44*s:.1f}pt">高手发生学</div>
<div class="sub">从人—工具复合体到<br>人—AI思想创新工程</div><div class="rule"></div></div>
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
<div class="q">先定目标，<br>再谈优化与付出。</div><div class="by">——本书的主线</div><div class="rule"></div>
<div class="bl"><p>一个人借助工具做成了过去做不到的事，这项能力该记在谁的名下？把功劳全归个人，会遮住工具、符号和协作；全归工具，又解释不了同一套工具在不同人手里为什么相差悬殊。</p>
<p>本书换了一个问法：不问谁有资格被称为高手，而问一个能被辨认、比较和改进的人—工具复合体，怎样以最小的误差、最小的冗余、最小的亏损，做到预先定下的真、善、美，并把这一轮的成果变成下一轮的条件。</p>
<p>全书导论与十编五十章。理论规定、来源支持的陈述、本书推演、待检假说与构造情境分别标明。</p>
<p>王德生著；正文由 AI 协作整理、展开并统稿，经内部三审；没有独立的同行评审，没有调查或试验；书中的场景与数字，凡标明为构造的，是为辨析机制而设。</p></div>
<div class="gold">高手，是被研究其发生的，不是被指认的。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 601 号 · 导论、十编五十章 · 约 {WAN} 万字<br>ISBN 979-8-90690-631-1 · 定价 US$25.00</div>
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
