#!/usr/bin/env python3
"""第 421 号《光的科学之外》封面与封底（220 系列版式，由第 407 号 cover.py 改来）。
只用纯色：深蓝底由纯色横带拼成（不用任何渐变），奶白书名、金色副题、金色光环。
主图取全书总比喻：左上方一个很小的亮点射出几道笔直的细光线（视觉、点）；右下方一把撑开的伞，
伞面下几圈互相重叠的同心弧（触与听、重叠、伞模型）。原创简单图形。
用法：python3 cover.py --fonts /home/claude/fonts --out <dir>
"""
import argparse
import math
import re
from pathlib import Path

NAVY_TOP, NAVY_LOW = '#0B1830', '#16294A'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#58BDCA', '#EFE8D6', '#9FB0C8'
ISBN = '979-8-90690-027-2'

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


def mix(a, b, t):
    """两种纯色按比例调成一种纯色（不用透明度，免得叠出发白）。"""
    a = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return '#%02X%02X%02X' % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def background(W, H):
    """深蓝纯色横带：28 条，自上而下由深到稍浅，每条都是纯色。"""
    n = 28
    out = []
    for k in range(n):
        y0 = H * k / n
        t = (k / (n - 1)) ** 1.2
        # 每条横带一直铺到底，后一条盖住前一条的下半，带与带之间不留缝
        out.append('<rect x="0" y="%.1f" width="%d" height="%.1f" fill="%s"/>' % (y0, W, H - y0, mix(NAVY_TOP, NAVY_LOW, t)))
    dots = []
    step = 44
    for yy in range(22, H, step):
        for xx in range(22 + (yy // step % 2) * 22, W, step):
            dots.append('<circle cx="%d" cy="%d" r="1.7"/>' % (xx, yy))
    out.append('<g fill="%s">%s</g>' % (mix(NAVY_TOP, DIM, .14), ''.join(dots)))
    return ''.join(out)


def halo(cx, cy, r, s):
    """金色光环：几圈纯色同心圆＋刻度。"""
    base = mix(NAVY_TOP, NAVY_LOW, .6)
    ticks = []
    for k in range(72):
        a = k * math.pi * 2 / 72
        r1 = r * (1.035 if k % 6 else 1.065)
        ticks.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (
            cx + r * math.cos(a), cy + r * math.sin(a), cx + r1 * math.cos(a), cy + r1 * math.sin(a)))
    return (f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r*1.20:.0f}" fill="{mix(base, GOLD, .035)}"/>'
            f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r*1.00:.0f}" fill="{mix(base, GOLD, .065)}"/>'
            f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r*1.20:.0f}" fill="none" stroke="{mix(base, GOLD, .35)}" stroke-width="{1.3*s:.1f}"/>'
            f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r:.0f}" fill="none" stroke="{mix(base, GOLD, .75)}" stroke-width="{2.4*s:.1f}"/>'
            f'<g stroke="{mix(base, GOLD, .6)}" stroke-width="{1.6*s:.1f}">{"".join(ticks)}</g>')


def art(W, H):
    s = W / 1700
    out = []
    # 伞的位置与大小
    ux, uy, UR = W * 0.64, H * 0.665, 330 * s
    out.append(halo(ux, uy + UR * 0.18, UR * 1.32, s))
    def canopy_y(x):
        # 与下面画伞面用的同一组二次曲线：最外两片的外侧伞骨
        topx, topy = ux, uy - UR * 0.78
        xa, ya = (ux - UR, uy) if x < ux else (ux + UR, uy)
        cx_ = (xa + topx) / 2 + (xa - ux) * 0.18; cy_ = (ya + topy) / 2 - UR * 0.20
        best, by = 1e9, topy
        for i in range(201):
            tt = i / 200
            bx = (1 - tt) ** 2 * topx + 2 * (1 - tt) * tt * cx_ + tt * tt * xa
            byy = (1 - tt) ** 2 * topy + 2 * (1 - tt) * tt * cy_ + tt * tt * ya
            if abs(bx - x) < best:
                best, by = abs(bx - x), byy
        return by

    # —— 光：左上方一个很小的亮点，射出几道笔直的细光线 ——
    px, py = W * 0.15, H * 0.375
    rays = []
    for ang in (9, 17, 25, 31, 37, 43, 49):
        a = math.radians(ang)
        dx, dy = math.cos(a), math.sin(a)
        # 沿光线一步步走，走进伞面的外轮廓就停；打不到伞的只走一段
        t = None
        for st in range(1, 1400):
            qx, qy = px + dx * st * s, py + dy * st * s
            if ux - UR < qx < ux + UR and qy < uy and qy >= canopy_y(qx):
                t = st * s; break
        if t is None:
            t = 1250 * s
        rays.append((px + dx * t, py + dy * t))
    for ex, ey in rays:
        out.append(f'<line x1="{px:.0f}" y1="{py:.0f}" x2="{ex:.0f}" y2="{ey:.0f}" stroke="{mix(NAVY_LOW, CREAM, .62)}" stroke-width="{1.5*s:.1f}" stroke-linecap="round"/>')
    out.append(f'<circle cx="{px:.0f}" cy="{py:.0f}" r="{17*s:.0f}" fill="none" stroke="{GOLD}" stroke-width="{1.4*s:.1f}"/>')
    out.append(f'<circle cx="{px:.0f}" cy="{py:.0f}" r="{7*s:.0f}" fill="#FFF8E6"/>')
    for a in range(0, 360, 90):
        r0, r1 = 24 * s, 38 * s
        ca, sa = math.cos(math.radians(a + 45)), math.sin(math.radians(a + 45))
        out.append(f'<line x1="{px + r0*ca:.0f}" y1="{py + r0*sa:.0f}" x2="{px + r1*ca:.0f}" y2="{py + r1*sa:.0f}" stroke="{GOLD2}" stroke-width="{1.4*s:.1f}" stroke-linecap="round"/>')
    # —— 伞面下：几组互相重叠的同心弧（触与听） ——
    arcs = []
    groups = [(ux - UR * 0.42, uy + UR * 0.22, CYAN), (ux + UR * 0.40, uy + UR * 0.26, GOLD2), (ux - UR * 0.02, uy + UR * 0.52, CREAM)]
    base = mix(NAVY_TOP, NAVY_LOW, .6)
    for gx, gy, col in groups:
        for k, rr in enumerate((0.16, 0.30, 0.44, 0.58)):
            r_ = UR * rr
            a0, a1 = math.radians(200), math.radians(340)
            x0, y0 = gx + r_ * math.cos(a0), gy + r_ * math.sin(a0)
            x1, y1 = gx + r_ * math.cos(a1), gy + r_ * math.sin(a1)
            # 上半弧
            arcs.append(f'<path d="M{x0:.0f} {y0:.0f} A{r_:.0f} {r_:.0f} 0 0 1 {x1:.0f} {y1:.0f}" fill="none" stroke="{mix(base, col, .85 - k*.13)}" stroke-width="{(3.0 - k*0.45)*s:.1f}" stroke-linecap="round"/>')
            # 下半弧（浅一些）
            b0, b1 = math.radians(20), math.radians(160)
            x0, y0 = gx + r_ * math.cos(b0), gy + r_ * math.sin(b0)
            x1, y1 = gx + r_ * math.cos(b1), gy + r_ * math.sin(b1)
            arcs.append(f'<path d="M{x0:.0f} {y0:.0f} A{r_:.0f} {r_:.0f} 0 0 1 {x1:.0f} {y1:.0f}" fill="none" stroke="{mix(base, col, .55 - k*.1)}" stroke-width="{(2.4 - k*0.4)*s:.1f}" stroke-linecap="round"/>')
        arcs.append(f'<circle cx="{gx:.0f}" cy="{gy:.0f}" r="{6*s:.0f}" fill="{col}"/>')
    # —— 伞：伞面（扇形分片）、伞骨、伞柄 ——
    n = 6
    edge_y = uy
    top = (ux, uy - UR * 0.78)
    pts = [(ux - UR + 2 * UR * i / n, edge_y) for i in range(n + 1)]
    panels = []
    for i in range(n):
        (xa, ya), (xb, yb) = pts[i], pts[i + 1]
        col = GOLD if i % 2 == 0 else mix(GOLD, CREAM, .45)
        # 两条伞骨弧线 + 底边一个向上凹的小扇贝
        cxa = (xa + top[0]) / 2 + (xa - ux) * 0.18; cya = (ya + top[1]) / 2 - UR * 0.20
        cxb = (xb + top[0]) / 2 + (xb - ux) * 0.18; cyb = (yb + top[1]) / 2 - UR * 0.20
        mx, my = (xa + xb) / 2, ya - UR * 0.09
        panels.append(f'<path d="M{top[0]:.0f} {top[1]:.0f} Q{cxa:.0f} {cya:.0f} {xa:.0f} {ya:.0f} Q{mx:.0f} {my:.0f} {xb:.0f} {yb:.0f} Q{cxb:.0f} {cyb:.0f} {top[0]:.0f} {top[1]:.0f} Z" fill="{col}" stroke="{mix(GOLD, NAVY_TOP, .35)}" stroke-width="{2*s:.1f}" stroke-linejoin="round"/>')
    out.append(''.join(arcs))
    out.append(''.join(panels))
    out.append(f'<circle cx="{top[0]:.0f}" cy="{top[1]:.0f}" r="{9*s:.0f}" fill="{CREAM}"/>')
    out.append(f'<line x1="{top[0]:.0f}" y1="{top[1] - 34*s:.0f}" x2="{top[0]:.0f}" y2="{top[1]:.0f}" stroke="{CREAM}" stroke-width="{6*s:.1f}" stroke-linecap="round"/>')
    hy = uy + UR * 1.05
    out.append(f'<line x1="{ux:.0f}" y1="{uy - UR*0.1:.0f}" x2="{ux:.0f}" y2="{hy:.0f}" stroke="{CREAM}" stroke-width="{7*s:.1f}" stroke-linecap="round"/>')
    out.append(f'<path d="M{ux:.0f} {hy:.0f} A{38*s:.0f} {38*s:.0f} 0 0 1 {ux - 76*s:.0f} {hy:.0f}" fill="none" stroke="{CREAM}" stroke-width="{7*s:.1f}" stroke-linecap="round"/>')
    return ''.join(out)


def barcode(x, y, s):
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


def front(Wmm, Hmm):
    W, H = Wmm * 10, Hmm * 10
    s = Wmm / 170
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{Wmm}mm" height="{Hmm}mm">{background(W, H)}{art(W, H)}</svg>'
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page{{size:{Wmm}mm {Hmm}mm;margin:0}} body{{margin:0}}
.pg{{position:relative;width:{Wmm}mm;height:{Hmm}mm;overflow:hidden}}
.pg svg{{position:absolute;left:0;top:0}}
.t{{position:absolute;left:{17*s:.1f}mm;top:{24*s:.1f}mm;color:{CREAM}}}
.big{{font:700 {40*s:.1f}pt/1.2 'Noto Serif CJK SC';letter-spacing:.1em;color:#F7F1E3;margin:0 0 {4*s:.1f}mm {-1*s:.1f}mm}}
.sub{{font:400 {11.4*s:.1f}pt/1.75 'Noto Serif CJK SC';color:{GOLD2};letter-spacing:.06em}}
.rule{{width:{16*s:.1f}mm;border-top:.9pt solid {GOLD};margin-top:{5*s:.1f}mm}}
.b{{position:absolute;left:{17*s:.1f}mm;bottom:{17*s:.1f}mm}}
.au{{font:400 {12.5*s:.1f}pt 'Noto Serif CJK SC';color:{CREAM};letter-spacing:.28em}}
.ph{{font:700 {8.4*s:.1f}pt 'Noto Sans CJK SC';color:{GOLD2};letter-spacing:.3em;margin-top:{6*s:.1f}mm}}
.pe{{font:400 {6.6*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.08em;margin-top:{.8*s:.1f}mm}}
</style></head><body><div class="pg">{svg}
<div class="t"><div class="big">光的科学之外</div>
<div class="sub">视觉科学的代签与触觉、听觉科学的新生</div><div class="rule"></div></div>
<div class="b"><div class="au">王德生　著</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div>
</div></body></html>"""


def back(Wmm, Hmm):
    W, H = Wmm * 10, Hmm * 10
    s = Wmm / 170
    base = mix(NAVY_TOP, NAVY_LOW, .1)
    # 右上小徽：一个亮点三道光，落在一段伞弧上
    ex, ey, er = W * 0.84, H * 0.085, 70 * s
    emb = (f'<circle cx="{ex:.0f}" cy="{ey:.0f}" r="{er*1.18:.0f}" fill="none" stroke="{mix(base, GOLD, .3)}" stroke-width="{1.2*s:.1f}"/>'
           f'<circle cx="{ex:.0f}" cy="{ey:.0f}" r="{er:.0f}" fill="none" stroke="{mix(base, GOLD, .65)}" stroke-width="{2*s:.1f}"/>')
    lx, ly = ex - 36 * s, ey - 30 * s
    for a in (20, 45, 70):
        r_ = math.radians(a)
        emb += f'<line x1="{lx:.0f}" y1="{ly:.0f}" x2="{lx + 62*s*math.cos(r_):.0f}" y2="{ly + 62*s*math.sin(r_):.0f}" stroke="{CREAM}" stroke-width="{2*s:.1f}" stroke-linecap="round"/>'
    emb += f'<circle cx="{lx:.0f}" cy="{ly:.0f}" r="{6*s:.1f}" fill="#FFF8E6"/>'
    emb += f'<path d="M{ex - 34*s:.0f} {ey + 34*s:.0f} Q{ex + 4*s:.0f} {ey - 6*s:.0f} {ex + 42*s:.0f} {ey + 34*s:.0f} Z" fill="{GOLD}"/>'
    # 底部淡弧纹
    waves = []
    for k, (yy, t, amp) in enumerate([(.955, .30, 8), (.972, .18, 6)]):
        y0 = H * yy; d = 'M0 %.0f' % y0
        for i in range(9):
            d += ' Q%.0f %.0f %.0f %.0f' % (W * (i + .5) / 9, y0 + (amp if i % 2 else -amp) * s * 2, W * (i + 1) / 9, y0)
        waves.append('<path d="%s" fill="none" stroke="%s" stroke-width="%.1f"/>' % (d, mix(NAVY_LOW, CYAN, t), 1.6 * s))
    bc, bw = barcode(W - 150 * s - 360 * s, H - 150 * s - 300 * s, s)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{Wmm}mm" height="{Hmm}mm">'
           f'{background(W, H)}{emb}{"".join(waves)}{bc}</svg>')
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page{{size:{Wmm}mm {Hmm}mm;margin:0}} body{{margin:0}}
.pg{{position:relative;width:{Wmm}mm;height:{Hmm}mm;overflow:hidden}}
.pg svg{{position:absolute;left:0;top:0}}
.c{{position:absolute;left:{17*s:.1f}mm;top:{24*s:.1f}mm;width:{128*s:.1f}mm;color:{CREAM}}}
.lab{{font:700 {7.4*s:.1f}pt 'Noto Sans CJK SC';color:{GOLD2};letter-spacing:.5em}}
.q{{font:700 {15.5*s:.1f}pt/1.75 'Noto Serif CJK SC';color:#F7F1E3;margin:{4*s:.1f}mm 0 {2*s:.1f}mm;letter-spacing:.04em}}
.by{{font:400 {8.2*s:.1f}pt 'Noto Serif CJK SC';color:{DIM}}}
.rule{{width:{14*s:.1f}mm;border-top:.9pt solid {GOLD};margin:{7*s:.1f}mm 0 {6*s:.1f}mm}}
.bl p{{font:400 {8.8*s:.1f}pt/1.9 'Noto Serif CJK SC';color:{mix('#EFE8D6', '#0B1830', .08)};margin:0 0 {2.6*s:.1f}mm;text-align:justify}}
.gold{{font:700 {10.5*s:.1f}pt 'Noto Serif CJK SC';color:{GOLD2};margin-top:{6*s:.1f}mm;letter-spacing:.04em}}
.gold span{{font-weight:400;font-size:.8em;color:{DIM};letter-spacing:0}}
.f{{position:absolute;left:{17*s:.1f}mm;bottom:{17*s:.1f}mm;font:400 {7.2*s:.1f}pt/1.85 'Noto Sans CJK SC';color:{DIM}}}
.f b{{color:{CREAM};font-weight:700;letter-spacing:.12em}}
</style></head><body><div class="pg">{svg}
<div class="c"><div class="lab">判 词</div>
<div class="q">现代科学的眼睛是自己的，<br>手和耳朵<br>是方程借给它的；<br>把借来的当成世界，<br>就叫客观物理。</div><div class="by">——本书判词</div><div class="rule"></div>
<div class="bl"><p>现代科学是视觉科学：它用眼睛取得稳定的特征，图像、刻度、曲线，都是给眼睛看的。原子之间怎样推、怎样撞，声音怎样一起一伏，从没被手和耳朵亲身取得，是方程替缺席的手和耳朵代签了字。</p>
<p>本书说，数不再是没有大小的点，而是一把撑开的伞；中医需要一门新生的科学。视觉数学正被 AI 接走，触与听的纠缠要先人、后机、再回人。</p></div>
<div class="gold">眼睛是自己的，手和耳朵是方程借的。<span>——本书</span></div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 421 号<br>US$23.00</div>
</div></body></html>"""


def main():
    import weasyprint
    import pymupdf
    ap = argparse.ArgumentParser()
    ap.add_argument('--fonts', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    for tag, (w, h) in {'print': (170, 240), 'reader': (190, 250)}.items():
        weasyprint.HTML(string=front(w, h)).write_pdf(str(a.out / f'cover-{tag}.pdf'))
        weasyprint.HTML(string=back(w, h)).write_pdf(str(a.out / f'back-{tag}.pdf'))
    for src, dst in [('cover-print.pdf', 'cover.jpg'), ('back-print.pdf', 'backcover.jpg')]:
        pg = pymupdf.open(str(a.out / src))[0]
        zoom = 900 / pg.rect.width
        clip = pymupdf.Rect(0, 0, pg.rect.width, 1270 / zoom)
        pix = pg.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip)
        pix.save(str(a.out / dst), jpg_quality=90)
        print(dst, pix.width, pix.height)
    print('covers ok')


if __name__ == '__main__':
    main()
