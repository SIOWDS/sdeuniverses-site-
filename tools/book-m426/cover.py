#!/usr/bin/env python3
"""第 426 号《读人》封面与封底（220 系列版式，由第 513 号 cover.py 改来）。
只用纯色：深蓝底由纯色横带拼成（不用任何渐变），奶白书名、金色题词、金色光环。
主图：金、奶白两条水流从两侧流来，到中间各自松散成乱线（同停），两圈乱线之间长出一棵青色新芽。原创扁平图形。
用法：python3 cover.py --fonts /usr/share/fonts/opentype/noto --out <dir>
"""
import argparse
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import meta as M  # noqa: E402

NAVY_TOP, NAVY_LOW = '#0B1830', '#16294A'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#58BDCA', '#EFE8D6', '#9FB0C8'
ISBN = M.ISBN

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
    """两条水流：金色一条自左、奶白一条自右，流到中间各自松散成几圈乱线（同停）；
    两圈乱线之间长出一棵青色新芽（共有新）。外圈金色光环。全部纯色，原创扁平图形。"""
    s = W / 1700
    out = []
    base = mix(NAVY_TOP, NAVY_LOW, .6)
    cx, cy = W * 0.56, H * 0.605
    out.append(halo(cx, cy, 455 * s, s))
    import random
    random.seed(7)
    for k in range(3):
        for col, x0, dirn, yo in ((GOLD, cx - 430 * s, 1, -26), (CREAM, cx + 430 * s, -1, 26)):
            pts = []
            for i in range(61):
                t = i / 60
                x = x0 + dirn * t * 300 * s
                y = cy + (yo + k * 16 - 16) * s + math.sin(t * 7 + k) * (20 * (1 - t) + 4) * s
                pts.append('%.0f,%.0f' % (x, y))
            c = mix(base, col, .95 - k * .22)
            out.append(f'<polyline points="{' '.join(pts)}" fill="none" stroke="{c}" stroke-width="{(7 - k * 1.8) * s:.1f}" stroke-linecap="round"/>')
    for col, ox in ((GOLD, -78), (CREAM, 78)):
        for j in range(5):
            r = (16 + j * 8) * s
            a0 = random.uniform(0, 6.28)
            pts = []
            for i in range(40):
                a = a0 + i * .32
                rr = r * (1 - i / 60)
                pts.append('%.0f,%.0f' % (cx + ox * s + rr * math.cos(a), cy + (j - 2) * 15 * s + rr * math.sin(a)))
            out.append(f'<polyline points="{' '.join(pts)}" fill="none" stroke="{mix(base, col, .7)}" stroke-width="{3 * s:.1f}" stroke-linecap="round"/>')
    T = mix(base, CYAN, .95)
    out.append(f'<path d="M{cx:.0f} {cy + 70*s:.0f} C {cx - 2*s:.0f} {cy:.0f}, {cx + 14*s:.0f} {cy - 60*s:.0f}, {cx:.0f} {cy - 140*s:.0f} C {cx - 9*s:.0f} {cy - 185*s:.0f}, {cx + 24*s:.0f} {cy - 230*s:.0f}, {cx + 46*s:.0f} {cy - 242*s:.0f}" fill="none" stroke="{T}" stroke-width="{8*s:.1f}" stroke-linecap="round"/>')
    out.append(f'<path d="M{cx + 3*s:.0f} {cy - 80*s:.0f} C {cx - 36*s:.0f} {cy - 104*s:.0f}, {cx - 60*s:.0f} {cy - 140*s:.0f}, {cx - 54*s:.0f} {cy - 174*s:.0f} C {cx - 18*s:.0f} {cy - 162*s:.0f}, {cx + 6*s:.0f} {cy - 126*s:.0f}, {cx + 3*s:.0f} {cy - 80*s:.0f} Z" fill="{T}"/>')
    out.append(f'<path d="M{cx + 9*s:.0f} {cy - 162*s:.0f} C {cx + 46*s:.0f} {cy - 180*s:.0f}, {cx + 76*s:.0f} {cy - 210*s:.0f}, {cx + 82*s:.0f} {cy - 246*s:.0f} C {cx + 46*s:.0f} {cy - 244*s:.0f}, {cx + 17*s:.0f} {cy - 210*s:.0f}, {cx + 9*s:.0f} {cy - 162*s:.0f} Z" fill="{T}"/>')
    out.append(f'<circle cx="{cx:.0f}" cy="{cy + 76*s:.0f}" r="{11*s:.0f}" fill="{T}"/>')
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
.t{{position:absolute;left:{17*s:.1f}mm;top:{19*s:.1f}mm;color:{CREAM}}}
.big{{font:700 {52*s:.1f}pt/1.32 'Noto Serif CJK SC';letter-spacing:.07em;color:#F7F1E3;margin:0 0 {3*s:.1f}mm {-1*s:.1f}mm}}
.pre{{font:400 {8*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.3em;margin-bottom:{4*s:.1f}mm}}
.en{{font:italic 400 {9.2*s:.1f}pt/1.5 'Noto Serif CJK SC';color:{DIM};letter-spacing:.02em}}
.sub{{font:400 {13.5*s:.1f}pt/1.75 'Noto Serif CJK SC';color:{GOLD2};letter-spacing:.18em;margin-top:{3.5*s:.1f}mm}}
.rule{{width:{16*s:.1f}mm;border-top:.9pt solid {GOLD};margin-top:{4*s:.1f}mm}}
.b{{position:absolute;left:{17*s:.1f}mm;bottom:{17*s:.1f}mm}}
.au{{font:400 {12.5*s:.1f}pt 'Noto Serif CJK SC';color:{CREAM};letter-spacing:.28em}}
.ph{{font:700 {8.4*s:.1f}pt 'Noto Sans CJK SC';color:{GOLD2};letter-spacing:.3em;margin-top:{6*s:.1f}mm}}
.pe{{font:400 {6.6*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.08em;margin-top:{.8*s:.1f}mm}}
</style></head><body><div class="pg">{svg}
<div class="t"><div class="pre">德麦国际专著 · 第 {M.NO} 号</div><div class="big">读　人</div>
<div class="en">{M.TITLE_EN}</div><div class="rule"></div><div class="sub">{M.EPIGRAPH}</div></div>
<div class="b"><div class="au">{M.AUTHOR}　著</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div>
</div></body></html>"""


def back(Wmm, Hmm):
    W, H = Wmm * 10, Hmm * 10
    s = Wmm / 170
    base = mix(NAVY_TOP, NAVY_LOW, .1)
    # 右上小徽：金色光环与一点（与封面主图呼应）
    ex, ey, er = W * 0.84, H * 0.085, 70 * s
    emb = (f'<circle cx="{ex:.0f}" cy="{ey:.0f}" r="{er*1.18:.0f}" fill="none" stroke="{mix(base, GOLD, .3)}" stroke-width="{1.2*s:.1f}"/>'
           f'<circle cx="{ex:.0f}" cy="{ey:.0f}" r="{er:.0f}" fill="none" stroke="{mix(base, GOLD, .65)}" stroke-width="{2*s:.1f}"/>')
    emb += f'<circle cx="{ex:.0f}" cy="{ey:.0f}" r="{10*s:.0f}" fill="{GOLD}"/>'
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
<div class="c"><div class="lab">两 句 定 音</div>
<div class="q">读人，不是任何时刻都要读出意义、读出价值、读出信息。<br>读人，很多时候恰恰是要“读不出东西”；而“读不出东西”，才是“读出新东西”的根基。</div><div class="by">——本书定音句</div><div class="rule"></div>
<div class="bl"><p>常说读人就是察言观色、看人准，好像人是一本写好的书。可越是自认看人很准的人，越容易看走眼；夫妻过了几十年，一方还会说“我从来没读懂过你”。本书说：人不是一本写好的书，是三界里一直在发生的洪流；读人，是两条洪流撞在一起，价值、意义、信息在两人之间缠在一起。</p>
<p>九个问题，九编：读人是什么，三界的“读”是否同一回事，老话遮住了什么；一次读懂怎样发生，误读怎样形成，功夫怎样练成；为什么越亲近越读不懂，为什么既盼又怕被读懂，AI 能读人了人该怎样读人。全书的回答落在一处：两个人同时停住、谁也没先回来的那几秒，才是新东西出生的地方。写给父母、老师、管理者和每一个普通人。</p></div>
<div class="gold">人怕的不是被看穿，是被一个不为你乱的人看穿。<span>——第八编</span></div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 {M.NO} 号<br>{M.PRICE}</div>
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
