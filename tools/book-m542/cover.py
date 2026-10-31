#!/usr/bin/env python3
"""第 542 号《知识同一性谱系递归发生学》封面与封底（220 系列版式，由第 512 号 cover.py 改来）。
只用纯色：深蓝底由纯色横带拼成（不用任何渐变），奶白书名、金色题词、金色光环。
主图：一张 7×5 的点阵（知识同一性的谱系空间），下方几行被逐步点亮（填充）；一条金色斜线是后来长出的新轴；
一道金色回写弧线把顶端指回起点。原创扁平图形。
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
    """谱系坐标与新轴：一张 7×5 的点阵（谱系空间），下方几行被逐步点亮（填充），一条金色斜线是后来长出的新轴，
    金色回写弧线把顶端指回起点。原创扁平图形，全部纯色。"""
    s = W / 1700
    out = []
    base = mix(NAVY_TOP, NAVY_LOW, .6)
    cx, cy = W * 0.56, H * 0.60
    out.append(halo(cx, cy, 455 * s, s))
    cols, rows = 7, 5
    gx, gy = 112 * s, 98 * s
    x0 = cx - (cols - 1) * gx / 2
    y0 = cy - (rows - 1) * gy / 2 + 30 * s
    axis = mix(base, CYAN, .30)
    # 原轴：横纵两条细线
    out.append(f'<line x1="{x0-50*s:.0f}" y1="{y0+(rows-1)*gy+46*s:.0f}" x2="{x0+(cols-1)*gx+50*s:.0f}" y2="{y0+(rows-1)*gy+46*s:.0f}" stroke="{axis}" stroke-width="{3*s:.1f}"/>')
    out.append(f'<line x1="{x0-50*s:.0f}" y1="{y0-40*s:.0f}" x2="{x0-50*s:.0f}" y2="{y0+(rows-1)*gy+46*s:.0f}" stroke="{axis}" stroke-width="{3*s:.1f}"/>')
    lit = {(r, c) for r in range(rows) for c in range(cols) if (rows - 1 - r) * 2 + (c % 3) < 7 - (r % 2)}
    new_axis = [(rows - 1, 0), (rows - 2, 1), (rows - 3, 2), (rows - 4, 3)]
    # 新轴斜线（金）
    ax = [(x0 + c * gx, y0 + r * gy) for r, c in new_axis]
    out.append(f'<line x1="{ax[0][0]-40*s:.0f}" y1="{ax[0][1]+40*s:.0f}" x2="{ax[-1][0]+(ax[-1][0]-ax[0][0])/3+30*s:.0f}" y2="{ax[-1][1]-(ax[0][1]-ax[-1][1])/3-30*s:.0f}" stroke="{GOLD2}" stroke-width="{6*s:.1f}" stroke-linecap="round"/>')
    for r in range(rows):
        for c in range(cols):
            x, y = x0 + c * gx, y0 + r * gy
            if (r, c) in new_axis:
                out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{19*s:.0f}" fill="{GOLD2}"/>')
            elif (r, c) in lit:
                out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{14*s:.0f}" fill="{mix(base, CYAN, .72)}"/>')
            else:
                out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{8*s:.0f}" fill="none" stroke="{mix(base, CYAN, .38)}" stroke-width="{2.4*s:.1f}"/>')
    # 回写弧线：自点阵右上绕出，回指左下起点
    rx, ry = x0 + (cols - 1) * gx + 90 * s, y0 - 10 * s
    sx, sy = x0 - 90 * s, y0 + (rows - 1) * gy + 10 * s
    out.append(f'<path d="M{rx:.0f} {ry:.0f} C{rx+190*s:.0f} {ry-170*s:.0f} {sx-230*s:.0f} {sy+260*s:.0f} {sx+20*s:.0f} {sy+60*s:.0f}" fill="none" stroke="{GOLD}" stroke-width="{7*s:.1f}" stroke-linecap="round"/>')
    out.append(f'<polygon points="{sx+20*s:.0f},{sy+60*s:.0f} {sx+78*s:.0f},{sy+66*s:.0f} {sx+44*s:.0f},{sy+118*s:.0f}" fill="{GOLD}"/>')
    sy2 = cy - 340 * s
    out.append(f'<circle cx="{cx:.0f}" cy="{sy2:.0f}" r="{58*s:.0f}" fill="none" stroke="{GOLD}" stroke-width="{11*s:.1f}"/>')
    out.append(f'<circle cx="{cx:.0f}" cy="{sy2:.0f}" r="{22*s:.0f}" fill="{GOLD2}"/>')
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
.big{{font:700 {34*s:.1f}pt/1.32 'Noto Serif CJK SC';letter-spacing:.07em;color:#F7F1E3;margin:0 0 {3*s:.1f}mm {-1*s:.1f}mm}}
.pre{{font:400 {8*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.3em;margin-bottom:{4*s:.1f}mm}}
.en{{font:italic 400 {9.2*s:.1f}pt/1.5 'Noto Serif CJK SC';color:{DIM};letter-spacing:.02em}}
.sub{{font:400 {13.5*s:.1f}pt/1.75 'Noto Serif CJK SC';color:{GOLD2};letter-spacing:.18em;margin-top:{3.5*s:.1f}mm}}
.rule{{width:{16*s:.1f}mm;border-top:.9pt solid {GOLD};margin-top:{4*s:.1f}mm}}
.b{{position:absolute;left:{17*s:.1f}mm;bottom:{17*s:.1f}mm}}
.au{{font:400 {12.5*s:.1f}pt 'Noto Serif CJK SC';color:{CREAM};letter-spacing:.28em}}
.ph{{font:700 {8.4*s:.1f}pt 'Noto Sans CJK SC';color:{GOLD2};letter-spacing:.3em;margin-top:{6*s:.1f}mm}}
.pe{{font:400 {6.6*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.08em;margin-top:{.8*s:.1f}mm}}
</style></head><body><div class="pg">{svg}
<div class="t"><div class="pre">德麦国际专著 · 第 {M.NO} 号</div><div class="big">知识同一性<br>谱系递归发生学</div>
<div class="en">Recursive Genesis of Knowledge-Identity Genealogies</div><div class="rule"></div><div class="sub">{M.SUBTITLE}</div></div>
<div class="b"><div class="au">{M.AUTHOR}　著</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div>
</div></body></html>"""


def back(Wmm, Hmm):
    W, H = Wmm * 10, Hmm * 10
    s = Wmm / 170
    base = mix(NAVY_TOP, NAVY_LOW, .1)
    # 右上小徽：小九宫格，对角三格金色、一道共线斜线（与封面主图呼应）
    ex, ey, er = W * 0.84, H * 0.085, 70 * s
    emb = (f'<circle cx="{ex:.0f}" cy="{ey:.0f}" r="{er*1.18:.0f}" fill="none" stroke="{mix(base, GOLD, .3)}" stroke-width="{1.2*s:.1f}"/>'
           f'<circle cx="{ex:.0f}" cy="{ey:.0f}" r="{er:.0f}" fill="none" stroke="{mix(base, GOLD, .65)}" stroke-width="{2*s:.1f}"/>')
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
<div class="c"><div class="lab">递归发生</div>
<div class="q">知识不仅在生长，<br>它还在改变自己凭什么生长。</div><div class="by">——绪论</div><div class="rule"></div>
<div class="bl"><p>工具带来的不只是效率。同行都用上同一件工具，只是在原来的比较方式里跑得更快；真正的升级，是旧领域被重新组织，一种活动成为一种服务，一种服务长出新的职业与市场。本书由此追问：当人与人工智能长期共同做研究，知识的发生方式本身会怎样变化？</p>
<p>全书九编四十一章：先以十类工具的历史对照检验“人—工具复合主体”与“模式谱系化”，再讨论知识同一性为什么是多维关系，最后给出填充、新轴与递归发生的形式模型，以及它们进入经济规模与平台制度的条件。来源台账 121 项，逐项写明读取范围；所有数值算例均为思想实验，所有实验设计均未执行。</p></div>
<div class="gold">知识的下一次增长，究竟长在哪里？<span>——绪论</span></div></div>
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
