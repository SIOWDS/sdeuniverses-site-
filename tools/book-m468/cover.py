#!/usr/bin/env python3
"""第 468 号《一看就不读》（王德生 著）封面与封底（工具链承自第 551 号；墨紫底，金、青、朱、木色点缀，220 系列版式）：
主图：一条金色的地板线（正规统一指导）；线上并排长出六条路径，每条三个节点，自下而上依次写着该路径的 S、D、E 次序；同层节点之间一道细虚线（对照、互底）。全部纯色，不用渐变。
用法：python3 cover.py --fonts /usr/share/fonts/opentype/noto --out <dir>
"""
import argparse
import math
import os
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#1E1A22', '#2A242E', '#231E27'   # 墨紫三带（纯色）
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#7CC1B5', '#EFE8D6', '#A9A2AE'
CLAY = '#D98E73'
WOOD, WOOD2, STEEL, VERM, JADE = '#8A6A4A', '#735638', '#B9C2C7', '#C0503C', '#9CC79A'
ISBN = '979-8-90690-629-8'
WAN = os.environ.get('WAN', '30')

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
    """主图（第 468 号）：刀工与纠缠。上方两股线（人、AI）一路互相缠绕（D1 碰撞）；
    落到一把刀上；刀下的砧板上，左边是生手切的粗块，向右渐渐成为均匀的细丝（S3 显露）；
    细丝上方浮起一层新点阵（E2 增量）。全部纯色，不用渐变。"""
    import random
    rnd = random.Random(468)
    s = W / 1700
    out = []
    board_y = H * 0.70          # 砧板上沿
    board_h = H * 0.055
    # 砧板（木色纯色两层）
    out.append(f'<rect x="{W*0.06:.0f}" y="{board_y:.0f}" width="{W*0.88:.0f}" height="{board_h:.0f}" rx="{10*s:.0f}" fill="{WOOD}"/>')
    out.append(f'<rect x="{W*0.06:.0f}" y="{board_y + board_h*0.62:.0f}" width="{W*0.88:.0f}" height="{board_h*0.38:.0f}" rx="{10*s:.0f}" fill="{WOOD2}"/>')
    # 切出的菜：左粗右细，越往右越匀
    x0, x1 = W * 0.10, W * 0.70
    n = 34
    for k in range(n):
        t = k / (n - 1)
        x = x0 + (x1 - x0) * (t ** 0.9)
        wid = (46 - 38 * t) * s * (1 + (1 - t) * rnd.uniform(-0.45, 0.45))
        hgt = (120 - 30 * t) * s * (1 + (1 - t) * rnd.uniform(-0.35, 0.35))
        tilt = (1 - t) * rnd.uniform(-14, 14)
        col = CREAM if k % 3 else JADE
        out.append(f'<rect x="{x:.0f}" y="{board_y - hgt:.0f}" width="{max(wid, 6*s):.0f}" height="{hgt:.0f}" rx="{3*s:.0f}" fill="{col}" fill-opacity="{0.55 + 0.4*t:.2f}" transform="rotate({tilt:.1f} {x:.0f} {board_y:.0f})"/>')
    # 刀（纯色剪影）：刀身斜立在细丝右侧
    kx, ky = W * 0.745, board_y
    blade = f'M{kx:.0f} {ky:.0f} L{kx + 175*s:.0f} {ky:.0f} L{kx + 205*s:.0f} {ky - 300*s:.0f} L{kx + 30*s:.0f} {ky - 300*s:.0f} Z'
    out.append(f'<path d="{blade}" fill="{STEEL}"/>')
    out.append(f'<path d="M{kx:.0f} {ky:.0f} L{kx + 175*s:.0f} {ky:.0f} L{kx + 178*s:.0f} {ky - 16*s:.0f} L{kx + 2*s:.0f} {ky - 16*s:.0f} Z" fill="{CREAM}" fill-opacity=".85"/>')
    out.append(f'<rect x="{kx + 70*s:.0f}" y="{ky - 470*s:.0f}" width="{70*s:.0f}" height="{175*s:.0f}" rx="{14*s:.0f}" fill="{VERM}"/>')
    # 两股纠缠的线（人：金；AI：青），自左上缠绕而下，汇到刀柄
    def strand(phase, col, op):
        pts = []
        for i in range(0, 121):
            t = i / 120
            x = W * 0.06 + (kx + 105 * s - W * 0.06) * t
            y = H * 0.44 + (ky - 470 * s - H * 0.44) * (t ** 2.2) + 46 * s * math.sin(t * 13 + phase) * (1 - 0.65 * t)
            pts.append((x, y))
        return tapered(pts, 16 * s, 6 * s), col, op
    for ph, col, op in ((0, GOLD2, .95), (math.pi, CYAN, .9)):
        d, c, o = strand(ph, col, op)
        out.append(f'<path d="{d}" fill="{c}" fill-opacity="{o}"/>')
    # 细丝上方浮起的新点阵（越往右越密）
    for _ in range(140):
        t = rnd.random() ** 0.6
        x = x0 + (x1 - x0) * t
        y = board_y - 150 * s - rnd.uniform(0, 140 * s) * (0.4 + t)
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rnd.uniform(1.6, 4.2)*s:.1f}" fill="{GOLD2 if rnd.random() < .5 else CYAN}" fill-opacity="{0.2 + 0.6*t:.2f}"/>')
    # 三条判据的标注
    ty = board_y + board_h + 74 * s
    for x, big, small, anchor, col in ((W*0.08, 'D1 碰撞', '意义三律转起来', 'start', GOLD2),
                                       (W*0.50, 'S3 显露', '刀工里的真善美', 'middle', CREAM),
                                       (W*0.92, 'E2 增量', '读完多了新东西', 'end', CYAN)):
        out.append(f'<text x="{x:.0f}" y="{ty:.0f}" font-size="{28*s:.0f}" text-anchor="{anchor}" font-family="Noto Serif CJK SC" font-weight="700" fill="{col}" letter-spacing="{3*s:.0f}">{big}</text>')
        out.append(f'<text x="{x:.0f}" y="{ty + 36*s:.0f}" font-size="{18*s:.0f}" text-anchor="{anchor}" font-family="Noto Sans CJK SC" fill="{DIM}" letter-spacing="{2*s:.0f}">{small}</text>')
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 468 号</div>
<div class="t"><div class="pre">S3 · D1 · E2</div><div class="big">一看就不读</div>
<div class="sub">AI时代，文字里还读得出人吗<br><span style="font-size:{8.6*s:.1f}pt;color:{DIM}">人-AI复合主体的三条成立判据</span></div><div class="rule"></div></div>
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
<div class="q">AI 写得再好，<br>我一看，就不读。</div><div class="by">——一句几乎人人说过的话</div><div class="rule"></div>
<div class="bl"><p>王德生给这句话起了个名字，叫“口味偏向性阅读”。可读者拒绝的到底是什么？是“AI”两个字，是文字太平整，还是读完学不到东西？</p>
<p>本书说：人与 AI 深度纠缠以后，已经很难分清是谁写的，因为复合主体诞生了。它要成立，得过三条——意义三律在双方之间转起来（D1）；生成的东西有真、善、美的显露，先显露给复合体自己，再显露给读者（S3）；复合体和读者的信息都有增加，读完能学到新东西（E2）。三条合起来，S3·D1·E2，正是“读人”的定义。</p>
<p>全书前言、序章、四编十三章、结语与三个附录：从预制菜、刀切菜、两人抬沙发过拐角讲起，讲到三大感觉的 SDE、内部验收与三审、九格判据图，最后落到最难的一件事——想法说不清是谁的，责任必须有人签字。</p>
<p>这是一部研究性专著：核心问题与三条判据由王德生提出，正文由 AI（Claude）协作撰写并经质检、统稿与三审回改；书中的人物与场景是构想，没有独立学术评审。</p></div>
<div class="gold">读者拒绝的从来不是 AI，是文字里读不出人。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 468 号 · 前言、四编十三章、结语、附录 · 约 {WAN} 万字<br>ISBN 979-8-90690-629-8 · 定价 US$20.00</div>
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
