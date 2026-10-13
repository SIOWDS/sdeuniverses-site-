#!/usr/bin/env python3
"""第 394 号封面与封底（照第 359 号的 220 系列版式）：藏青渐变底、细点阵、金色光晕与刻度环；
主图是暗室里一次闪光：左边双缝，波前一圈圈漫开，屏上一点闪亮；闪光外三层由细到粗的网格（多重网格），右下一片拼图。

用法：python3 cover.py --fonts /home/claude/fonts --out /home/claude/mengzi/build
产物：cover-print.pdf / back-print.pdf（170×240）、cover-reader.pdf / back-reader.pdf（190×250）、
      cover.jpg / backcover.jpg（1004×1418，站上用）
"""
import argparse
import math
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0B1830', '#1B3158', '#142746'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#58BDCA', '#EFE8D6', '#9FB0C8'
ISBN = '979-8-90690-814-8'

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


def background(W, H, uid):
    dots = []
    step = 44
    for yy in range(22, H, step):
        for xx in range(22 + (yy // step % 2) * 22, W, step):
            dots.append('<circle cx="%d" cy="%d" r="1.7"/>' % (xx, yy))
    return f"""
<defs>
 <linearGradient id="bg{uid}" x1="0" y1="0" x2="0.35" y2="1">
  <stop offset="0" stop-color="{NAVY_TOP}"/><stop offset=".58" stop-color="{NAVY_MID}"/><stop offset="1" stop-color="{NAVY_LOW}"/></linearGradient>
 <radialGradient id="halo{uid}" cx=".5" cy=".5" r=".5">
  <stop offset="0" stop-color="{GOLD2}" stop-opacity=".30"/><stop offset=".45" stop-color="{GOLD}" stop-opacity=".12"/>
  <stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></radialGradient>
 <linearGradient id="kite{uid}" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="{CREAM}" stop-opacity=".95"/><stop offset="1" stop-color="{GOLD}" stop-opacity=".85"/></linearGradient>
 <linearGradient id="handle{uid}" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#B89A5E"/><stop offset=".45" stop-color="{CREAM}"/><stop offset="1" stop-color="#A88C55"/></linearGradient>
 <linearGradient id="line{uid}" x1="0" y1="1" x2="1" y2="0">
  <stop offset="0" stop-color="{GOLD}"/><stop offset="1" stop-color="{GOLD2}"/></linearGradient>
</defs>
<rect width="{W}" height="{H}" fill="url(#bg{uid})"/>
<g fill="{DIM}" fill-opacity=".10">{''.join(dots)}</g>"""


def rings(cx, cy, r):
    ticks = []
    for k in range(72):
        a = k * math.pi * 2 / 72
        r1 = r * (1.035 if k % 6 else 1.06)
        ticks.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (
            cx + r * math.cos(a), cy + r * math.sin(a), cx + r1 * math.cos(a), cy + r1 * math.sin(a)))
    return f"""
<circle cx="{cx}" cy="{cy}" r="{r*1.55:.0f}" fill="url(#halo{{uid}})"/>
<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{GOLD}" stroke-opacity=".55" stroke-width="2.2"/>
<circle cx="{cx}" cy="{cy}" r="{r*1.10:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".22" stroke-width="1.2"/>
<circle cx="{cx}" cy="{cy}" r="{r*0.62:.0f}" fill="none" stroke="{CYAN}" stroke-opacity=".16" stroke-width="1.2" stroke-dasharray="3 9"/>
<g stroke="{GOLD}" stroke-opacity=".45" stroke-width="1.6">{''.join(ticks)}</g>"""


def art(W, H, uid):
    """主图：暗室里一次闪光。左边一道双缝，两组波前（青）一圈圈漫向右边的屏；屏上一点闪光（金、奶白），
    闪光四周三层网格由细到粗（多重网格：一层层稳住）；屏上淡淡的干涉条纹；右下一片拼图，稍稍错开，正要落位。"""
    s = W / 1700
    cx, cy, r = W * 0.62, H * 0.585, 500 * s
    u = r / 450
    out = [rings(cx, cy, r).replace('{uid}', uid)]
    # 屏：一道竖直的细长板，闪光在板上
    fx, fy = cx + 70 * u, cy - 10 * u
    sx = fx
    for k in range(-7, 8):
        op = .05 + .11 * (math.cos(k * 0.9) ** 2) * (1 - abs(k) / 9)
        out.append(f'<rect x="{sx-9*u:.0f}" y="{fy+k*44*u-15*u:.0f}" width="{18*u:.0f}" height="{30*u:.0f}" rx="{6*u:.0f}" fill="{CYAN}" fill-opacity="{op:.2f}"/>')
    out.append(f'<line x1="{sx:.0f}" y1="{fy-360*u:.0f}" x2="{sx:.0f}" y2="{fy+360*u:.0f}" stroke="{CREAM}" stroke-opacity=".28" stroke-width="{3*s:.1f}"/>')
    # 双缝
    bx = cx - 470 * u
    for (y0, y1) in [(cy - 400 * u, cy - 70 * u), (cy - 30 * u, cy + 30 * u), (cy + 70 * u, cy + 400 * u)]:
        out.append(f'<rect x="{bx-8*u:.0f}" y="{y0:.0f}" width="{16*u:.0f}" height="{y1-y0:.0f}" fill="{GOLD}" fill-opacity=".85"/>')
    # 波前：两组同心弧
    for sy in (cy - 50 * u, cy + 50 * u):
        for k in range(1, 9):
            rr = k * 62 * u
            op = .42 - k * .04
            out.append(f'<path d="M{bx+rr*math.cos(-1.0):.1f} {sy+rr*math.sin(-1.0):.1f} A{rr:.1f} {rr:.1f} 0 0 1 {bx+rr*math.cos(1.0):.1f} {sy+rr*math.sin(1.0):.1f}" fill="none" stroke="{CYAN}" stroke-opacity="{op:.2f}" stroke-width="{2.4*s:.1f}"/>')
    # 三层网格：细层 8×8、中层 4×4、粗层 2×2，以闪光为心
    for (half, n, col, op, sw) in [(110 * u, 8, CREAM, .32, 1.2), (220 * u, 4, CYAN, .30, 1.6), (360 * u, 2, GOLD, .40, 2.2)]:
        x0, y0 = fx - half, fy - half
        lines = []
        for i in range(n + 1):
            v = -half + 2 * half * i / n
            lines.append(f'<line x1="{fx+v:.1f}" y1="{y0:.1f}" x2="{fx+v:.1f}" y2="{y0+2*half:.1f}"/>')
            lines.append(f'<line x1="{x0:.1f}" y1="{fy+v:.1f}" x2="{x0+2*half:.1f}" y2="{fy+v:.1f}"/>')
        out.append(f'<g stroke="{col}" stroke-opacity="{op}" stroke-width="{sw*s:.1f}">' + ''.join(lines) + '</g>')
    # 闪光：八道锥形光芒 + 两圈光晕
    out.append(f'<circle cx="{fx:.0f}" cy="{fy:.0f}" r="{150*u:.0f}" fill="url(#halo{uid})"/>')
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        ln = (170 if k % 2 else 110) * u
        pts = [(fx + math.cos(a) * ln * t, fy + math.sin(a) * ln * t) for t in [i / 12 for i in range(13)]]
        out.append(f'<path d="{tapered(pts, 13*s, 0.8*s)}" fill="{GOLD2}" fill-opacity=".9"/>')
    out.append(f'<circle cx="{fx:.0f}" cy="{fy:.0f}" r="{26*u:.0f}" fill="{CREAM}"/><circle cx="{fx:.0f}" cy="{fy:.0f}" r="{44*u:.0f}" fill="none" stroke="{GOLD2}" stroke-width="{3*s:.1f}"/>')
    # 拼图一片：右下，稍错开
    px, py, ps = cx + 300 * u, cy + 300 * u, 92 * u
    d = (f'M{px:.0f} {py:.0f} h{ps*.36:.0f} a{ps*.14:.0f} {ps*.14:.0f} 0 1 1 {ps*.28:.0f} 0 h{ps*.36:.0f} '
         f'v{ps*.36:.0f} a{ps*.14:.0f} {ps*.14:.0f} 0 1 0 0 {ps*.28:.0f} v{ps*.36:.0f} '
         f'h-{ps*.36:.0f} a{ps*.14:.0f} {ps*.14:.0f} 0 1 1 -{ps*.28:.0f} 0 h-{ps*.36:.0f} Z')
    out.append(f'<g transform="rotate(-9 {px+ps/2:.0f} {py+ps/2:.0f})"><path d="{d}" fill="{CREAM}" fill-opacity=".9"/>'
               f'<path d="{d}" fill="none" stroke="{GOLD}" stroke-width="{2.5*s:.1f}" transform="translate({-24*u:.0f} {-24*u:.0f})" stroke-opacity=".7" stroke-dasharray="{10*s:.1f} {8*s:.1f}"/></g>')
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
.big{{font:700 {36*s:.1f}pt/1.25 'Noto Serif CJK SC';letter-spacing:.1em;color:#F7F1E3;margin:{2*s:.1f}mm 0 {3*s:.1f}mm {-1*s:.1f}mm}}
.sub{{font:400 {10.6*s:.1f}pt/1.75 'Noto Serif CJK SC';color:{GOLD2};letter-spacing:.04em}}
.rule{{width:{16*s:.1f}mm;border-top:.9pt solid {GOLD};margin-top:{5*s:.1f}mm}}
.b{{position:absolute;left:{17*s:.1f}mm;bottom:{17*s:.1f}mm}}
.au{{font:400 {12.5*s:.1f}pt 'Noto Serif CJK SC';color:{CREAM};letter-spacing:.28em}}
.ph{{font:700 {8.4*s:.1f}pt 'Noto Sans CJK SC';color:{GOLD2};letter-spacing:.3em;margin-top:{6*s:.1f}mm}}
.pe{{font:400 {6.6*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.08em;margin-top:{.8*s:.1f}mm}}
.no{{position:absolute;right:{15*s:.1f}mm;top:{16*s:.1f}mm;font:400 {6.6*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.2em;text-align:right}}
</style></head><body><div class="pg">{svg}
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 394 号</div>
<div class="t"><div class="pre">普通人都能明白的</div><div class="big">一次闪光<br>是谁的？</div>
<div class="sub">量子力学缺的那个本体论</div><div class="rule"></div></div>
<div class="b"><div class="au">王德生　著</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div>
</div></body></html>"""


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
           f'{background(W, H, "b")}{emb}{"".join(waves)}{bc}</svg>')
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{fontface(F)}
@page{{size:{Wmm}mm {Hmm}mm;margin:0}} body{{margin:0}}
.pg{{position:relative;width:{Wmm}mm;height:{Hmm}mm;overflow:hidden}}
.pg svg{{position:absolute;left:0;top:0}}
.c{{position:absolute;left:{17*s:.1f}mm;top:{24*s:.1f}mm;width:{128*s:.1f}mm;color:{CREAM}}}
.lab{{font:700 {7.4*s:.1f}pt 'Noto Sans CJK SC';color:{GOLD2};letter-spacing:.5em}}
.q{{font:700 {15.5*s:.1f}pt/1.75 'Noto Serif CJK SC';color:#F7F1E3;margin:{4*s:.1f}mm 0 {2*s:.1f}mm;letter-spacing:.04em}}
.by{{font:400 {8.2*s:.1f}pt 'Noto Serif CJK SC';color:{DIM}}}
.rule{{width:{14*s:.1f}mm;border-top:.9pt solid {GOLD};margin:{7*s:.1f}mm 0 {6*s:.1f}mm}}
.bl p{{font:400 {8.8*s:.1f}pt/1.9 'Noto Serif CJK SC';color:{CREAM};opacity:.9;margin:0 0 {2.6*s:.1f}mm;text-align:justify}}
.gold{{font:700 {10.5*s:.1f}pt 'Noto Serif CJK SC';color:{GOLD2};margin-top:{6*s:.1f}mm;letter-spacing:.06em}}
.f{{position:absolute;left:{17*s:.1f}mm;bottom:{17*s:.1f}mm;font:400 {7.2*s:.1f}pt/1.85 'Noto Sans CJK SC';color:{DIM}}}
.f b{{color:{CREAM};font-weight:700;letter-spacing:.12em}}
</style></head><body><div class="pg">{svg}
<div class="c"><div class="lab">判 词</div>
<div class="q">读数和它的主人<br>一起发生；<br>玻恩规则，是这场发生<br>一层层稳住之后的终点。</div><div class="by">——本书</div><div class="rule"></div>
<div class="bl"><p>一百年来，量子力学的算法从没出过错，物理学家却一直吵不完：屏上那一次闪光，到底是谁的？归光子，归仪器，还是归看的人？</p>
<p>本书说，这道题本身问歪了。属性不是挂在一个先在的东西身上，等人去发现；读数、光子、这一次测量、测到的人，一起发生出来。稳住不是一步到位，而像计算数学里的多重网格法：细层磨光、粗层求解、一圈圈回写，直到各层对上。玻恩规则里的平方，就是这一来一回留下的账。</p>
<p>八编四十七章，从量血压讲到双缝，从薛定谔的猫、维格纳的朋友讲到量子纠错，再回到一张化验单、一个孩子的「会」、一份 AI 写的综述。书里所有的说法都标明是诠释，并把可错条款登记在案。</p></div>
<div class="gold">收敛即事实；客观，是冗余回写出来的。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 394 号 · 八编四十七章 · 约 29 万字<br>定价 US$23.00</div>
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
