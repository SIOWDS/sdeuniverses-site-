#!/usr/bin/env python3
"""第 551 号《AI时代的职业教育出路：技术的同一性谱系》（王德生 著）封面与封底（工具链承自第 549 号；藏青墨绿底，金、青绿、陶红点缀，220 系列版式）：
主图：一条金色的地板线（正规统一指导）；线上并排长出六条路径，每条三个节点，自下而上依次写着该路径的 S、D、E 次序；同层节点之间一道细虚线（对照、互底）。全部纯色，不用渐变。
用法：python3 cover.py --fonts /usr/share/fonts/opentype/noto --out <dir>
"""
import argparse
import math
import os
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0A1F2B', '#123847', '#0E2C3A'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#6FB9B0', '#EFE8D6', '#A3B8BC'
CLAY = '#D98E73'
ISBN = '979-8-90690-553-6'
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
    """主图（第 551 号）：地板与六条路径。金色地板线之上并排六条路径（沉淀、倒逼、锚定、进入、原型、再创），
    每条三个节点自下而上依次是该路径的 S/D/E 次序；相邻两条同层节点之间一道细线。全部纯色，不用渐变。"""
    import random
    rnd = random.Random(551)
    s = W / 1700
    out = []
    floor = H * 0.745
    gap = H * 0.105
    x_l, x_r = W * 0.13, W * 0.87
    paths = [('E', 'D', 'S', CYAN), ('D', 'E', 'S', GOLD2), ('E', 'S', 'D', CLAY),
             ('S', 'E', 'D', CREAM), ('D', 'S', 'E', CYAN), ('S', 'D', 'E', GOLD2)]
    names = ['沉淀', '倒逼', '锚定', '进入', '原型', '再创']
    xs = [x_l + (x_r - x_l) * k / 5 for k in range(6)]
    # 背景：谱位的淡点阵（并存的位置）
    for yy in range(int(floor - gap * 3.3), int(floor), int(34 * s)):
        for xx in range(int(x_l - 60 * s), int(x_r + 70 * s), int(34 * s)):
            out.append(f'<circle cx="{xx}" cy="{yy}" r="{1.5*s:.1f}" fill="{CREAM}" fill-opacity=".10"/>')
    # 同层节点之间的细线（对照、互底）
    for lv in range(3):
        y = floor - gap * (lv + 1)
        pts = ' '.join(f'{x + 10*s*math.sin(lv*1.7 + k):.0f},{y:.0f}' for k, x in enumerate(xs))
        out.append(f'<polyline points="{pts}" fill="none" stroke="{GOLD}" stroke-opacity=".28" stroke-width="{1.8*s:.1f}" stroke-dasharray="{6*s:.0f} {7*s:.0f}"/>')
    # 六条路径
    for k, (a1, a2, a3, col) in enumerate(paths):
        x = xs[k]
        nodes = []
        for lv, ch in enumerate((a1, a2, a3)):
            nodes.append((x + 10 * s * math.sin(lv * 1.7 + k), floor - gap * (lv + 1), ch))
        d = f'M{x:.0f} {floor:.0f}'
        prev = (x, floor)
        for (nx, ny, _) in nodes:
            d += f' C{prev[0]:.0f} {prev[1] - gap*0.5:.0f} {nx:.0f} {ny + gap*0.5:.0f} {nx:.0f} {ny:.0f}'
            prev = (nx, ny)
        out.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-opacity=".85" stroke-width="{3.4*s:.1f}" stroke-linecap="round"/>')
        for lv, (nx, ny, ch) in enumerate(nodes):
            r = 31 * s
            out.append(f'<circle cx="{nx:.0f}" cy="{ny:.0f}" r="{r:.0f}" fill="{NAVY_TOP}" stroke="{col}" stroke-width="{3*s:.1f}"/>')
            out.append(f'<text x="{nx:.0f}" y="{ny + 11*s:.0f}" font-size="{31*s:.0f}" text-anchor="middle" font-family="Noto Serif CJK SC" font-weight="700" fill="{col}">{ch}</text>')
        out.append(f'<text x="{x:.0f}" y="{floor + 64*s:.0f}" font-size="{28*s:.0f}" text-anchor="middle" font-family="Noto Serif CJK SC" font-weight="700" fill="{col}" letter-spacing="{3*s:.0f}">{names[k]}</text>')
    # 地板
    out.append(f'<rect x="0" y="{floor:.0f}" width="{W}" height="{9*s:.0f}" fill="{GOLD2}"/>')
    out.append(f'<rect x="0" y="{floor + 9*s:.0f}" width="{W}" height="{H*0.815 - floor:.0f}" fill="{GOLD}" fill-opacity=".10"/>')
    ty = floor + 158 * s
    out.append(f'<text x="{W*0.08:.0f}" y="{ty:.0f}" font-size="{30*s:.0f}" font-family="Noto Serif CJK SC" font-weight="700" fill="{GOLD2}" letter-spacing="{4*s:.0f}">地板</text>')
    out.append(f'<text x="{W*0.08:.0f}" y="{ty + 38*s:.0f}" font-size="{19*s:.0f}" font-family="Noto Sans CJK SC" fill="{DIM}" letter-spacing="{3*s:.0f}">统一指导留作地板</text>')
    out.append(f'<text x="{W*0.92:.0f}" y="{ty:.0f}" font-size="{30*s:.0f}" text-anchor="end" font-family="Noto Serif CJK SC" font-weight="700" fill="{CREAM}" letter-spacing="{4*s:.0f}">谱</text>')
    out.append(f'<text x="{W*0.92:.0f}" y="{ty + 38*s:.0f}" font-size="{19*s:.0f}" text-anchor="end" font-family="Noto Sans CJK SC" fill="{DIM}" letter-spacing="{3*s:.0f}">可对照　可追溯　可协同</text>')
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 551 号</div>
<div class="t"><div class="pre">六路径 · 同一性谱系</div><div class="big big2" style="font-size:{33*s:.1f}pt">AI时代的<br>职业教育出路</div>
<div class="sub">技术的同一性谱系<br><span style="font-size:{8.6*s:.1f}pt;color:{DIM}">基于SDE技术发生智能体的路径同一性发生学</span></div><div class="rule"></div></div>
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
<div class="q">学一门手艺，<br>学的不是一条路。</div><div class="by">——本书导读</div><div class="rule"></div>
<div class="bl"><p>设想幼儿园里三十个孩子学系鞋带，用的是同一首口诀，走的却是三条路：一个先泡在绳子里，一个先有非系不可的事，一个先看懂了结的样子。正规统一指导记下了一条路，其余的路走通了，也无处可记。</p>
<p>本书说，技术就是六路径：统一性技术把六路径压成一条起手次序；技术的同一性谱系，是六路径各自再按显露、差异序列、纠缠三维的分量具体化，长成一张谱，每个位置可对照、可追溯、可协同，并且互为留底。职教被叫作二等，不是技术低，是拿“点”的尺去量“路”。</p>
<p>全书前言、导读、八编三十六章、结语与四个附录：从手、耳、眼讲技术长在什么土里，讲谱位、家谱、乐谱与互底，讲“SDE技术发生智能体”怎样替一个人选起手（算法是设想，尚无实现），再落到十三个行业、学校、企业、协会与政策，最后立下十二条带失败标准的预言。</p>
<p>这是一部研究性专著：核心问题与主干判断由王德生提出，正文由 AI（Claude）协作撰写并经质检回改；书中的人物与场景是构想，算法与预言均未检验，没有独立学术评审。</p></div>
<div class="gold">药方是换尺子，不靠升格。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 551 号 · 前言、八编三十六章、结语、附录 · 约 {WAN} 万字<br>ISBN 979-8-90690-553-6 · 定价 US$20.00</div>
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
