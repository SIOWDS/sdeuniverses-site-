#!/usr/bin/env python3
"""第 512 号《班级之美：同一性谱系发生学》封面与封底（220 系列版式，由第 421 号 cover.py 改来；原拟第 507 号，改号第 512 号）。
只用纯色：深蓝底由纯色横带拼成（不用任何渐变），奶白书名、金色副题、金色光环。
主图取全书总比喻「从树到网」：一棵树的根落在一张小课桌上，枝条长开后又彼此连回、织成一张网；
网上几对小圆点之间有一来一回两道细弧（双向认出）。原创扁平图形。
用法：python3 cover.py --fonts /usr/share/fonts/opentype/noto --out <dir>
"""
import argparse
import math
import re
from pathlib import Path

NAVY_TOP, NAVY_LOW = '#0B1830', '#16294A'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#58BDCA', '#EFE8D6', '#9FB0C8'
ISBN = '979-8-90690-512-3'

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
    """从树到网：树根落在一张小课桌上，枝条长开后又彼此连回、织成一张网；
    网上几对小圆点之间有一来一回两道细弧（双向认出）。全部纯色。"""
    s = W / 1700
    out = []
    base = mix(NAVY_TOP, NAVY_LOW, .6)
    cx = W * 0.60
    deskY = H * 0.805
    out.append(halo(cx, H * 0.43, 470 * s, s))
    P = lambda dx, fy: (cx + dx * s, H * fy)
    B0 = P(0, .585)
    L1 = [P(-175, .505), P(8, .468), P(190, .512)]
    L2 = [P(-340, .445), P(-225, .383), P(-88, .352), P(92, .346), P(240, .388), P(352, .452)]
    OUT = [P(-415, .360), P(-178, .298), P(0, .268), P(186, .292), P(418, .366)]
    br = mix(base, CREAM, .80)
    net = mix(base, CYAN, .62)
    def q(p0, p1, bend, col, w):
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L = math.hypot(dx, dy) or 1
        c = (mx - dy / L * bend * L, my + dx / L * bend * L)
        return f'<path d="M{p0[0]:.0f} {p0[1]:.0f} Q{c[0]:.0f} {c[1]:.0f} {p1[0]:.0f} {p1[1]:.0f}" fill="none" stroke="{col}" stroke-width="{w:.1f}" stroke-linecap="round"/>', c
    # —— 网：外圈节点各与两片相邻的叶节点相连（枝条长开又连回），叶节点之间横向相连 ——
    lines = []
    links = [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3), (3, 3), (3, 4), (4, 4), (4, 5)]
    for o, l in links:
        lines.append(q(L2[l], OUT[o], .10 if l % 2 else -.10, net, 2.6 * s)[0])
    for k in range(len(L2) - 1):
        lines.append(q(L2[k], L2[k + 1], .16, net, 2.2 * s)[0])
    for k in range(len(OUT) - 1):
        lines.append(q(OUT[k], OUT[k + 1], .12, mix(base, CYAN, .45), 1.8 * s)[0])
    out += lines
    # —— 树：课桌上的树干、三根大枝、六根小枝 ——
    tw = 20 * s
    out.append(f'<path d="M{cx - tw:.0f} {deskY:.0f} Q{cx - tw*0.6:.0f} {H*.70:.0f} {cx - tw*0.45:.0f} {B0[1]:.0f} L{cx + tw*0.45:.0f} {B0[1]:.0f} Q{cx + tw*0.6:.0f} {H*.70:.0f} {cx + tw:.0f} {deskY:.0f} Z" fill="{br}"/>')
    for k, l in enumerate(L1):
        out.append(q(B0, l, (-.12, .04, .12)[k], br, 10 * s)[0])
    for k, l in enumerate(L2):
        out.append(q(L1[k // 2], l, -.10 if k % 2 == 0 else .10, br, 6 * s)[0])
    # 树根：在桌面上铺开几道
    for dx, ex in ((-1, -95), (-1, -55), (1, 60), (1, 100)):
        out.append(f'<path d="M{cx + dx*8*s:.0f} {deskY - 2*s:.0f} Q{cx + ex*0.45*s:.0f} {deskY - 4*s:.0f} {cx + ex*s:.0f} {deskY + 2*s:.0f}" fill="none" stroke="{br}" stroke-width="{4.5*s:.1f}" stroke-linecap="round"/>')
    # —— 课桌：桌面、桌斗、两条桌腿、横撑 ——
    dw = 250 * s
    wood = mix(GOLD, NAVY_TOP, .12)
    out.append(f'<rect x="{cx - dw:.0f}" y="{deskY:.0f}" width="{2*dw:.0f}" height="{24*s:.0f}" rx="{5*s:.0f}" fill="{GOLD}"/>')
    out.append(f'<rect x="{cx - dw + 22*s:.0f}" y="{deskY + 24*s:.0f}" width="{2*dw - 44*s:.0f}" height="{46*s:.0f}" fill="{wood}"/>')
    out.append(f'<rect x="{cx - dw + 22*s:.0f}" y="{deskY + 24*s:.0f}" width="{2*dw - 44*s:.0f}" height="{6*s:.0f}" fill="{mix(wood, NAVY_TOP, .25)}"/>')
    for lx in (cx - dw + 22 * s, cx + dw - 44 * s):
        out.append(f'<rect x="{lx:.0f}" y="{deskY + 70*s:.0f}" width="{22*s:.0f}" height="{150*s:.0f}" fill="{wood}"/>')
    out.append(f'<rect x="{cx - dw + 44*s:.0f}" y="{deskY + 175*s:.0f}" width="{2*dw - 88*s:.0f}" height="{10*s:.0f}" fill="{mix(wood, NAVY_TOP, .2)}"/>')
    # —— 节点 ——
    for x, y in L1:
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{6*s:.0f}" fill="{br}"/>')
    for x, y in L2 + OUT:
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{11*s:.0f}" fill="{base}"/>'
                   f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{7.5*s:.0f}" fill="{CREAM}"/>')
    # —— 成对的小圆点：一来一回两道细弧（双向认出） ——
    def arrow(tip, frm, col):
        dx, dy = tip[0] - frm[0], tip[1] - frm[1]
        L = math.hypot(dx, dy) or 1
        ux, uy = dx / L, dy / L
        bx, by = tip[0] - ux * 15 * s, tip[1] - uy * 15 * s
        return (f'<path d="M{tip[0]:.0f} {tip[1]:.0f} L{bx - uy*6*s:.0f} {by + ux*6*s:.0f} L{bx + uy*6*s:.0f} {by - ux*6*s:.0f} Z" fill="{col}"/>')
    def shrink(p0, p1, r):
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L = math.hypot(dx, dy) or 1
        return (p0[0] + dx / L * r, p0[1] + dy / L * r)
    pairs = [(L2[0], OUT[0]), (L2[2], L2[3]), (L2[4], OUT[3]), (L2[1], OUT[1]), (L2[5], OUT[4])]
    for a_, b_ in pairs:
        pa, pb = shrink(a_, b_, 16 * s), shrink(b_, a_, 16 * s)
        p1, c1 = q(pa, pb, .26, GOLD2, 2.2 * s)
        p2, c2 = q(pb, pa, .26, CYAN, 2.2 * s)
        out += [p1, p2, arrow(pb, c1, GOLD2), arrow(pa, c2, CYAN)]
        for x, y in (a_, b_):
            out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{12*s:.0f}" fill="{GOLD}"/><circle cx="{x:.0f}" cy="{y:.0f}" r="{5*s:.0f}" fill="#FFF8E6"/>')
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
.big{{font:700 {44*s:.1f}pt/1.2 'Noto Serif CJK SC';letter-spacing:.1em;color:#F7F1E3;margin:0 0 {4*s:.1f}mm {-1*s:.1f}mm}}
.sub{{font:400 {13.5*s:.1f}pt/1.75 'Noto Serif CJK SC';color:{GOLD2};letter-spacing:.06em}}
.rule{{width:{16*s:.1f}mm;border-top:.9pt solid {GOLD};margin-top:{5*s:.1f}mm}}
.b{{position:absolute;left:{17*s:.1f}mm;bottom:{17*s:.1f}mm}}
.au{{font:400 {12.5*s:.1f}pt 'Noto Serif CJK SC';color:{CREAM};letter-spacing:.28em}}
.ph{{font:700 {8.4*s:.1f}pt 'Noto Sans CJK SC';color:{GOLD2};letter-spacing:.3em;margin-top:{6*s:.1f}mm}}
.pe{{font:400 {6.6*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.08em;margin-top:{.8*s:.1f}mm}}
</style></head><body><div class="pg">{svg}
<div class="t"><div class="big">班级之美</div>
<div class="sub">同一性谱系发生学</div><div class="rule"></div></div>
<div class="b"><div class="au">柴翱　刘华杰　著</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div>
</div></body></html>"""


def back(Wmm, Hmm):
    W, H = Wmm * 10, Hmm * 10
    s = Wmm / 170
    base = mix(NAVY_TOP, NAVY_LOW, .1)
    # 右上小徽：一枝分成两枝，两枝又连回到一个点；两点之间一来一回
    ex, ey, er = W * 0.84, H * 0.085, 70 * s
    emb = (f'<circle cx="{ex:.0f}" cy="{ey:.0f}" r="{er*1.18:.0f}" fill="none" stroke="{mix(base, GOLD, .3)}" stroke-width="{1.2*s:.1f}"/>'
           f'<circle cx="{ex:.0f}" cy="{ey:.0f}" r="{er:.0f}" fill="none" stroke="{mix(base, GOLD, .65)}" stroke-width="{2*s:.1f}"/>')
    bx, by = ex, ey + 42 * s
    lx, ly, rx, ry, tx, ty = ex - 28 * s, ey + 2 * s, ex + 28 * s, ey + 2 * s, ex, ey - 36 * s
    for (x0, y0, x1, y1) in ((bx, by, lx, ly), (bx, by, rx, ry), (lx, ly, tx, ty), (rx, ry, tx, ty)):
        emb += f'<line x1="{x0:.0f}" y1="{y0:.0f}" x2="{x1:.0f}" y2="{y1:.0f}" stroke="{CREAM}" stroke-width="{2.2*s:.1f}" stroke-linecap="round"/>'
    emb += f'<path d="M{lx:.0f} {ly - 5*s:.0f} Q{ex:.0f} {ey - 14*s:.0f} {rx:.0f} {ry - 5*s:.0f}" fill="none" stroke="{GOLD2}" stroke-width="{1.6*s:.1f}"/>'
    emb += f'<path d="M{lx:.0f} {ly + 5*s:.0f} Q{ex:.0f} {ey + 18*s:.0f} {rx:.0f} {ry + 5*s:.0f}" fill="none" stroke="{CYAN}" stroke-width="{1.6*s:.1f}"/>'
    for x, y in ((lx, ly), (rx, ry), (tx, ty)):
        emb += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{6*s:.1f}" fill="{GOLD}"/>'
    emb += f'<rect x="{bx - 22*s:.0f}" y="{by:.0f}" width="{44*s:.0f}" height="{6*s:.0f}" fill="{GOLD}"/>'
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
.q{{font:700 {14.2*s:.1f}pt/1.8 'Noto Serif CJK SC';color:#F7F1E3;margin:{4*s:.1f}mm 0 {2*s:.1f}mm;letter-spacing:.04em}}
.by{{font:400 {8.2*s:.1f}pt 'Noto Serif CJK SC';color:{DIM}}}
.rule{{width:{14*s:.1f}mm;border-top:.9pt solid {GOLD};margin:{7*s:.1f}mm 0 {6*s:.1f}mm}}
.bl p{{font:400 {8.8*s:.1f}pt/1.9 'Noto Serif CJK SC';color:{mix('#EFE8D6', '#0B1830', .08)};margin:0 0 {2.6*s:.1f}mm;text-align:justify}}
.gold{{font:700 {10.5*s:.1f}pt 'Noto Serif CJK SC';color:{GOLD2};margin-top:{6*s:.1f}mm;letter-spacing:.04em}}
.gold span{{font-weight:400;font-size:.8em;color:{DIM};letter-spacing:0}}
.f{{position:absolute;left:{17*s:.1f}mm;bottom:{17*s:.1f}mm;font:400 {7.2*s:.1f}pt/1.85 'Noto Sans CJK SC';color:{DIM}}}
.f b{{color:{CREAM};font-weight:700;letter-spacing:.12em}}
</style></head><body><div class="pg">{svg}
<div class="c"><div class="lab">判 词</div>
<div class="q">班级之美是双向认出的谱系闭环——<br>一个孩子的知识在别人那里变了形，<br>原主认得出它变在哪里，<br>借用者说得出它从哪里来，<br>变形后的东西回流进全班底座。</div><div class="by">——本书判词</div><div class="rule"></div>
<div class="bl"><p>一间教室里，统一与多样为什么总也调和不了？本书说，统一不是多样的敌人，而是上一轮谱系死后留下的化石；班级之美，是双向认出的谱系闭环：一个孩子的那一枝在别人那里变了形，原主认得出，借用者说得出来路，变形后的东西写回全班底座。</p>
<p>课桌、课时、课程、考试、评估与师德，都可以从维持统一的装置，升维为谱系发生的创造。写给班主任、老师、家长与校长。</p></div>
<div class="gold">你的那一枝，在别人那里长成了什么？<span>——本书</span></div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 512 号<br>US$23.00</div>
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
