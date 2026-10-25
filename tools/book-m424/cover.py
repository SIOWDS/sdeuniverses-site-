#!/usr/bin/env python3
"""第 424 号《三律医学入门》封面与封底（由第 512 号 cover.py 改来）。原第 512 号说明：（220 系列版式，由第 421 号 cover.py 改来；原拟第 507 号，改号第 512 号）。
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
ISBN = '979-8-90690-029-6'

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
    """三律之环：金色光环里三个互相咬合的圆环——特征律（金，环内一枚同心指纹）、自由律（青，环内三条分岔的小路）、
    幸福律（奶白，环内一道起伏后放平的波）；一道脉搏线从左向右穿过三环，在中心跳起一次后归于平缓。全部纯色。"""
    s = W / 1700
    out = []
    base = mix(NAVY_TOP, NAVY_LOW, .6)
    cx, cy = W * 0.58, H * 0.47
    out.append(halo(cx, cy, 480 * s, s))
    R = 205 * s
    d = 125 * s
    C = [(cx, cy - d), (cx - d * 0.95, cy + d * 0.62), (cx + d * 0.95, cy + d * 0.62)]
    cols = [GOLD, CYAN, mix(CREAM, GOLD, .15)]
    fills = [mix(base, GOLD, .10), mix(base, CYAN, .10), mix(base, CREAM, .07)]
    for (x, y), f in zip(C, fills):
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{R:.0f}" fill="{f}"/>')
    for (x, y), c in zip(C, cols):
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{R:.0f}" fill="none" stroke="{c}" stroke-width="{7*s:.1f}"/>')
    # 特征律：同心指纹（几道不闭合的同心弧）
    x, y = C[0][0], C[0][1] - 40 * s
    for k, r in enumerate((18, 34, 50, 66)):
        r *= s
        a0, a1 = math.radians(200 + k * 8), math.radians(520 - k * 10)
        p0 = (x + r * math.cos(a0), y + r * math.sin(a0)); p1 = (x + r * math.cos(a1), y + r * math.sin(a1))
        large = 1 if (a1 - a0) > math.pi else 0
        out.append(f'<path d="M{p0[0]:.0f} {p0[1]:.0f} A{r:.0f} {r:.0f} 0 {large} 1 {p1[0]:.0f} {p1[1]:.0f}" fill="none" stroke="{GOLD2}" stroke-width="{4.2*s:.1f}" stroke-linecap="round"/>')
    out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{6*s:.0f}" fill="{GOLD2}"/>')
    # 自由律：一条路分成三条
    x, y = C[1][0] - 55 * s, C[1][1] + 30 * s
    st = mix(base, CYAN, .85)
    out.append(f'<path d="M{x - 40*s:.0f} {y + 40*s:.0f} L{x:.0f} {y:.0f}" stroke="{st}" stroke-width="{5*s:.1f}" stroke-linecap="round" fill="none"/>')
    for ex, ey in ((70, -70), (85, -10), (60, 45)):
        out.append(f'<path d="M{x:.0f} {y:.0f} Q{x + ex*0.45*s:.0f} {y + ey*0.1*s:.0f} {x + ex*s:.0f} {y + ey*s:.0f}" stroke="{st}" stroke-width="{4.2*s:.1f}" stroke-linecap="round" fill="none"/>')
        out.append(f'<circle cx="{x + ex*s:.0f}" cy="{y + ey*s:.0f}" r="{7*s:.0f}" fill="{CYAN}"/>')
    # 幸福律：一道起伏的波，最后放平
    x0, y0 = C[2][0] - 20 * s, C[2][1] + 40 * s
    dpath = f'M{x0:.0f} {y0:.0f}'
    amps = (38, 30, 20, 10, 3)
    for i, a in enumerate(amps):
        xa, xb = x0 + (i * 34 + 17) * s, x0 + (i + 1) * 34 * s
        dpath += f' Q{xa:.0f} {y0 + (-a if i % 2 == 0 else a) * s:.0f} {xb:.0f} {y0:.0f}'
    out.append(f'<path d="{dpath}" fill="none" stroke="{CREAM}" stroke-width="{4.6*s:.1f}" stroke-linecap="round"/>')
    # 脉搏线：从画面左缘进入，穿过三环中心，跳起一次，归于平缓
    py = cy + 10 * s
    pts = [(W * 0.12, py), (cx - 330 * s, py), (cx - 60 * s, py), (cx - 30 * s, py - 30 * s), (cx - 5 * s, py + 25 * s),
           (cx + 20 * s, py - 120 * s), (cx + 50 * s, py + 70 * s), (cx + 75 * s, py), (cx + 360 * s, py), (W * 0.98, py)]
    dd = 'M' + ' L'.join('%.0f %.0f' % p for p in pts)
    out.append(f'<path d="{dd}" fill="none" stroke="{base}" stroke-width="{14*s:.1f}" stroke-linejoin="round" stroke-linecap="round"/>')
    out.append(f'<path d="{dd}" fill="none" stroke="{GOLD2}" stroke-width="{5*s:.1f}" stroke-linejoin="round" stroke-linecap="round"/>')
    out.append(f'<circle cx="{cx + 20*s:.0f}" cy="{py - 120*s:.0f}" r="{9*s:.0f}" fill="#FFF8E6"/>')
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
<div class="t"><div class="big">三律医学入门</div>
<div class="sub">重构生命、健康与医学的意义结构</div><div class="rule"></div></div>
<div class="b"><div class="au">王德生　秦莉　著</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div>
</div></body></html>"""


def back(Wmm, Hmm):
    W, H = Wmm * 10, Hmm * 10
    s = Wmm / 170
    base = mix(NAVY_TOP, NAVY_LOW, .1)
    # 右上小徽：三个咬合的小环
    ex, ey, er = W * 0.84, H * 0.085, 70 * s
    emb = (f'<circle cx="{ex:.0f}" cy="{ey:.0f}" r="{er*1.18:.0f}" fill="none" stroke="{mix(base, GOLD, .3)}" stroke-width="{1.2*s:.1f}"/>'
           f'<circle cx="{ex:.0f}" cy="{ey:.0f}" r="{er:.0f}" fill="none" stroke="{mix(base, GOLD, .65)}" stroke-width="{2*s:.1f}"/>')
    rr, dd = 24 * s, 15 * s
    for (dx, dy), c in zip(((0, -dd), (-dd * .95, dd * .62), (dd * .95, dd * .62)), (GOLD, CYAN, CREAM)):
        emb += f'<circle cx="{ex + dx:.0f}" cy="{ey + dy:.0f}" r="{rr:.0f}" fill="none" stroke="{c}" stroke-width="{2.4*s:.1f}"/>'
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
<div class="c"><div class="lab">本 书 之 问</div>
<div class="q">医学不是技术之战，<br>而是意义之问。<br>健康不是数据平稳，<br>而是意义有序。</div><div class="by">——本书</div><div class="rule"></div>
<div class="bl"><p>体检单上一个箭头也没有，人却越来越累——为什么？本书以 SIO 主客互动本体论与意义三律为钥匙：任何活着的结构，都要认得出「我是谁」（特征律），有路可走、换得开（自由律），张力积起来能放下（幸福律）。三律停摆，病就从那里长出来。</p>
<p>从三医分工到三高翻案，从器官病谱、互动医学到抑郁与癌症的三律读法，全书六编四十二章，把医学的目光从「杀、压、控」移向「归律」。本书是医学哲学著作，不替代任何诊疗。</p></div>
<div class="gold">我还认得出我自己吗？我还有别的路可走吗？<br>我积下的那些张力，有地方放下吗？<span>——随身三问</span></div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 424 号<br>US$50.00</div>
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
