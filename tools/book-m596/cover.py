#!/usr/bin/env python3
"""第 596 号《AI时代中华智慧的困境和出路》（王德生、胡志英 著）封面与封底（工具链承自第 594 号，藏青底、金青奶白三色，220 系列版式）：
主图：一个以几何画成的“中”字居中；左，守中而开花（一朵金线花）；右，花种（青色的种子，一粒已发芽）。全部纯色，不用渐变。
用法：python3 cover.py --fonts /usr/share/fonts/opentype/noto --out <dir>
"""
import argparse
import math
import os
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0C1A34', '#1B3158', '#16294A'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#7FA7C9', '#EFE8D6', '#A9B6C8'
ISBN = '979-8-90690-624-3'
WAN = os.environ.get('WAN', '25.8')

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
    """主图（第 596 号）：居中，一个几何画成的“中”字（口字加一竖，守中）；左，一朵金线花（开花）；右，几粒青色的种子，一粒已发芽（花种）。纯色。"""
    import random
    rnd = random.Random(596)
    s = W / 1700
    out = []
    ground = H * 0.60
    out.append(f'<line x1="0" y1="{ground:.0f}" x2="{W:.0f}" y2="{ground:.0f}" stroke="{GOLD}" stroke-opacity=".45" stroke-width="{2.2*s:.1f}"/>')
    # 中：口＋贯穿的一竖
    cx = W * 0.5
    bw, bh = 330 * s, 250 * s
    top = ground - 470 * s
    bx, by = cx - bw / 2, top + 105 * s
    out.append(f'<rect x="{bx:.0f}" y="{by:.0f}" width="{bw:.0f}" height="{bh:.0f}" rx="{8*s:.0f}" fill="none" stroke="{GOLD2}" stroke-width="{16*s:.1f}"/>')
    out.append(f'<line x1="{cx:.0f}" y1="{top:.0f}" x2="{cx:.0f}" y2="{ground:.0f}" stroke="{GOLD2}" stroke-width="{16*s:.1f}" stroke-linecap="round"/>')
    out.append(f'<circle cx="{cx:.0f}" cy="{by + bh/2:.0f}" r="{22*s:.0f}" fill="{CREAM}"/>')
    # 左：花
    fx = W * 0.20
    fy = ground - 340 * s
    out.append(f'<path d="M{fx:.0f} {ground:.0f} Q{fx - 30*s:.0f} {ground - 170*s:.0f} {fx:.0f} {fy + 36*s:.0f}" fill="none" stroke="{GOLD}" stroke-width="{7*s:.1f}" stroke-linecap="round"/>')
    out.append(f'<path d="M{fx - 8*s:.0f} {ground - 120*s:.0f} q{-70*s:.0f} {-20*s:.0f} {-96*s:.0f} {-84*s:.0f} q{70*s:.0f} {2*s:.0f} {96*s:.0f} {84*s:.0f}z" fill="none" stroke="{GOLD2}" stroke-opacity=".85" stroke-width="{4*s:.1f}" stroke-linejoin="round"/>')
    for k in range(8):
        ang = k * 45
        out.append(f'<ellipse cx="{fx:.0f}" cy="{fy - 58*s:.0f}" rx="{20*s:.0f}" ry="{58*s:.0f}" transform="rotate({ang} {fx:.0f} {fy:.0f})" fill="none" stroke="{GOLD2}" stroke-width="{4.6*s:.1f}"/>')
    out.append(f'<circle cx="{fx:.0f}" cy="{fy:.0f}" r="{19*s:.0f}" fill="{CREAM}"/>')
    # 右：花种，一粒已发芽
    for k, (px, py) in enumerate(((0.70, 0.34), (0.77, 0.43), (0.84, 0.375), (0.91, 0.47))):
        x0, y0 = W * px, H * py
        out.append(f'<path d="M{x0:.0f} {y0 - 26*s:.0f} C{x0 + 20*s:.0f} {y0 - 4*s:.0f} {x0 + 14*s:.0f} {y0 + 22*s:.0f} {x0:.0f} {y0 + 24*s:.0f} C{x0 - 14*s:.0f} {y0 + 22*s:.0f} {x0 - 20*s:.0f} {y0 - 4*s:.0f} {x0:.0f} {y0 - 26*s:.0f}z" fill="{CYAN}" fill-opacity="{.95 - .12*k:.2f}"/>')
        out.append(f'<line x1="{x0:.0f}" y1="{y0 + 40*s:.0f}" x2="{x0:.0f}" y2="{y0 + 96*s:.0f}" stroke="{CYAN}" stroke-opacity=".38" stroke-width="{2.4*s:.1f}" stroke-dasharray="{8*s:.0f} {9*s:.0f}"/>')
    sx = W * 0.80
    out.append(f'<path d="M{sx:.0f} {ground:.0f} q{-4*s:.0f} {-54*s:.0f} {4*s:.0f} {-100*s:.0f}" fill="none" stroke="{CYAN}" stroke-width="{6*s:.1f}" stroke-linecap="round"/>')
    out.append(f'<path d="M{sx + 4*s:.0f} {ground - 100*s:.0f} q{50*s:.0f} {-8*s:.0f} {66*s:.0f} {-56*s:.0f} q{-54*s:.0f} {4*s:.0f} {-66*s:.0f} {56*s:.0f}z" fill="{CYAN}" fill-opacity=".9"/>')
    out.append(f'<path d="M{sx + 2*s:.0f} {ground - 76*s:.0f} q{-46*s:.0f} {-6*s:.0f} {-58*s:.0f} {-48*s:.0f} q{46*s:.0f} {2*s:.0f} {58*s:.0f} {48*s:.0f}z" fill="{CYAN}" fill-opacity=".62"/>')
    ty2 = ground + 120 * s
    for xx, anc, big, small, col in ((W * 0.08, 'start', '守中', '维持可以共同展开的关系', GOLD2), (W * 0.5, 'middle', '开花', '既有可能性的充分展开', CREAM), (W * 0.92, 'end', '花种', '新基底的发生', CYAN)):
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 596 号</div>
<div class="t"><div class="pre">SDE 文明与发生研究</div><div class="big big2" style="font-size:{34*s:.1f}pt">AI时代<br>中华智慧的困境和出路</div>
<div class="sub">从守中开花到持续生成新花种</div><div class="rule"></div></div>
<div class="b"><div class="au">王德生　胡志英　著</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div>
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
<div class="c"><div class="lab">本 书 的 问 题</div>
<div class="q">文明的未来<br>需要持续生成。</div><div class="by">——守中而开花的智慧，如何获得持续生成新花种的能力？</div><div class="rule"></div>
<div class="bl"><p>当既有答案越来越容易获得，人怎样持续提出有价值的新问题，并使新的可能成为能够检验的共同生活？本书从一个“中”字出发，把中庸理解为守中、守正的 1 到 N 发展之道，先说清它曾经为什么有效，再看 AI 怎样改变引进、追赶与优化的条件。</p>
<p>全书用 SDE 的显露、差异序列与特征纠缠重建问题，进入教育、健康与事业三种生活，又回到普通人的知识母本、公共条件与文明责任。每一领域都按同一次序展开：旧路径的最强版本、AI 带来的变化、共同发生的方案、怎样验证。</p>
<p>全书导论、九编四十四章与结语，每章附资料说明，标明来源及其支持范围。</p>
<p>王德生立题与口径，正文由 AI（Claude）协作成稿，经统稿与三轮审读；情境多为思想实验；三领域试点尚未实施；没有独立学术评审。</p></div>
<div class="gold">守住有根据的智慧，也让新的花种能够发生。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 596 号 · 导论、九编四十四章、结语 · 约 {WAN} 万字<br>ISBN 979-8-90690-624-3 · 定价 US$20.00</div>
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
