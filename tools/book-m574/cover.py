#!/usr/bin/env python3
"""《腐败与癌症》修订版封面与封底（220 系列版式：藏青底、金青奶白三色，全部矢量、纯色）。
主图：一只断开的金环（断路模板）居中，从缺口复印出两串越来越小的同款断环，一串走向上方的层级网格（组织），一串走向下方的细胞群（身体）；
左侧几道奶白的价值流涌进环里，右侧意义的虚线没有接上。
用法：python3 cover.py --fonts /usr/share/fonts/opentype/noto --out <dir>
"""
import argparse
import math
import os
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0C1A34', '#1B3158', '#16294A'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#7FA7C9', '#EFE8D6', '#A9B6C8'
ISBN = '978-1-970820-36-2'
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


def ring(cx, cy, r, w, col, op=1.0, gap=52, rot=0):
    """断环：一段缺口的圆弧，缺口朝右（rot 旋转），两端各一个圆点。"""
    a0, a1 = math.radians(rot + gap / 2), math.radians(rot + 360 - gap / 2)
    x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
    x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
    return (f'<path d="M{x0:.1f} {y0:.1f} A{r:.1f} {r:.1f} 0 1 1 {x1:.1f} {y1:.1f}" fill="none" stroke="{col}" stroke-opacity="{op:.2f}" stroke-width="{w:.1f}" stroke-linecap="round"/>'
            f'<circle cx="{x0:.1f}" cy="{y0:.1f}" r="{w*0.9:.1f}" fill="{col}" fill-opacity="{op:.2f}"/><circle cx="{x1:.1f}" cy="{y1:.1f}" r="{w*0.9:.1f}" fill="{col}" fill-opacity="{op:.2f}"/>')


def art(W, H, uid):
    import random
    rnd = random.Random(2026)
    s = W / 1700
    out = []
    # 淡网格
    for k in range(8):
        yy = H * 0.40 + k * H * 0.05
        out.append(f'<line x1="{W*0.05:.0f}" y1="{yy:.0f}" x2="{W*0.95:.0f}" y2="{yy:.0f}" stroke="{DIM}" stroke-opacity=".07" stroke-width="{1.2*s:.1f}"/>')
    cx, cy, R = W * 0.34, H * 0.575, 170 * s
    # 价值流：左侧几道奶白曲线涌进环
    for i in range(5):
        y0 = cy - 150 * s + i * 75 * s
        out.append(f'<path d="M{W*0.03:.0f} {y0:.0f} C{W*0.12:.0f} {y0:.0f} {cx-R*1.6:.0f} {cy+(i-2)*30*s:.0f} {cx-R*0.95:.0f} {cy+(i-2)*22*s:.0f}" fill="none" stroke="{CREAM}" stroke-opacity="{.55-i*.06:.2f}" stroke-width="{(5-i*.5)*s:.1f}" stroke-linecap="round"/>')
    # 主环（断路模板）
    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{R*1.32:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".22" stroke-width="{2*s:.1f}" stroke-dasharray="{5*s:.0f} {8*s:.0f}"/>')
    out.append(ring(cx, cy, R, 16 * s, GOLD2, 1.0, gap=48))
    out.append(f'<path d="M{cx:.0f} {cy-46*s:.0f} L{cx+34*s:.0f} {cy:.0f} L{cx:.0f} {cy+46*s:.0f} L{cx-34*s:.0f} {cy:.0f} Z" fill="none" stroke="{CREAM}" stroke-width="{5*s:.1f}"/>')
    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{9*s:.0f}" fill="{GOLD2}"/>')
    # 意义输出：右侧虚线，没有接上
    gx = cx + R * 1.02
    out.append(f'<path d="M{gx+30*s:.0f} {cy:.0f} L{gx+150*s:.0f} {cy:.0f}" stroke="{CYAN}" stroke-opacity=".45" stroke-width="{4*s:.1f}" stroke-dasharray="{6*s:.0f} {14*s:.0f}" stroke-linecap="round"/>')
    # 复印：两路越来越小的断环
    def path_pts(p0, p1, p2, n):
        pts = []
        for j in range(n):
            t = (j + 1) / (n + 0.6)
            x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
            y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
            pts.append((x, y, t))
        return pts
    up = path_pts((gx, cy - 20 * s), (W * 0.62, H * 0.43), (W * 0.76, H * 0.41), 6)
    dn = path_pts((gx, cy + 20 * s), (W * 0.62, H * 0.70), (W * 0.76, H * 0.70), 6)
    for pts, col in ((up, CREAM), (dn, CYAN)):
        for x, y, t in pts:
            r = R * (0.34 - 0.2 * t)
            out.append(ring(x, y, r, (7 - 3 * t) * s, GOLD2, 0.95 - 0.45 * t, gap=48, rot=rnd.uniform(-12, 12)))
    # 上方：层级网格（组织）
    ox, oy = W * 0.86, H * 0.40
    nodes = [(ox, oy - 120 * s)] + [(ox + dx * s, oy - 30 * s) for dx in (-90, 0, 90)] + [(ox + dx * s, oy + 60 * s) for dx in (-140, -70, 0, 70, 140)]
    for a, b in [(0, 1), (0, 2), (0, 3), (1, 4), (1, 5), (2, 6), (3, 7), (3, 8), (2, 5), (2, 7)]:
        out.append(f'<line x1="{nodes[a][0]:.0f}" y1="{nodes[a][1]:.0f}" x2="{nodes[b][0]:.0f}" y2="{nodes[b][1]:.0f}" stroke="{CREAM}" stroke-opacity=".55" stroke-width="{2.6*s:.1f}"/>')
    for x, y in nodes:
        out.append(f'<rect x="{x-14*s:.0f}" y="{y-11*s:.0f}" width="{28*s:.0f}" height="{22*s:.0f}" fill="{NAVY_TOP}" stroke="{CREAM}" stroke-width="{2.6*s:.1f}"/>')
    # 下方：细胞群（身体）
    bx, by = W * 0.86, H * 0.71
    for k in range(9):
        a = k * 2.4; rr = (0 if k == 0 else 70 + (k % 3) * 18) * s
        x, y = bx + rr * math.cos(a), by + rr * math.sin(a) * 0.75
        r0 = (30 - (k % 3) * 5) * s
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r0:.0f}" fill="{NAVY_TOP}" stroke="{CYAN}" stroke-width="{2.6*s:.1f}" stroke-opacity=".85"/>')
        out.append(f'<circle cx="{x+4*s:.0f}" cy="{y-3*s:.0f}" r="{r0*0.32:.0f}" fill="{CYAN}" fill-opacity=".6"/>')
    # 注脚三行
    ty2 = H * 0.785
    for xx, anc, big, small, col in ((W * 0.08, 'start', '模板', '真正被复制的东西', GOLD2), (W * 0.5, 'middle', '断路', '价值进来，意义不出', CREAM), (W * 0.92, 'end', '免疫', '拆模板 · 修通路 · 建免疫', CYAN)):
        out.append(f'<text x="{xx:.0f}" y="{ty2:.0f}" font-size="{36*s:.0f}" text-anchor="{anc}" font-family="Noto Serif CJK SC" font-weight="700" fill="{col}" letter-spacing="{4*s:.0f}">{big}</text>')
        out.append(f'<text x="{xx:.0f}" y="{ty2 + 40*s:.0f}" font-size="{20*s:.0f}" text-anchor="{anc}" font-family="Noto Sans CJK SC" fill="{DIM}" letter-spacing="{3*s:.0f}">{small}</text>')
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 574 号</div>
<div class="t"><div class="pre">同一种病，两种尺度</div><div class="big">腐败与癌症</div>
<div class="sub">三律发生学视角下的同构病理学</div><div class="rule"></div></div>
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
           f'{background(W, H, "b", split=0.715)}{emb}{"".join(waves)}{bc}</svg>')
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
<div class="c"><div class="lab">结 论</div>
<div class="q">真正复制的不是人，<br>不是细胞，<br>而是模板。</div><div class="by">——本书结论</div><div class="rule"></div>
<div class="bl"><p>越抓越合规，越治越复发；越加码越迁移，越精准越分叉。反腐与治癌在同一条规律面前反复受挫。本书的回答是：腐败与癌症是同一种发生学病理在不同尺度上的投影。</p>
<p>真正被复制的不是坏人、坏细胞、坏通路，而是「价值→意义」通路断裂之后的断路模板。越违背意义三律，越省力、越容易复制——这叫 Easy Copies。</p>
<p>全书十一篇：先立意义三律与三模态的哲学底座，再写腐败度、合法无监督化与科学的「我」，再到 SIO 癌症学、细胞复制、异质性、增生与小我夺权，最后落在拆模板、修通路、建免疫的工程闭环。</p>
<p>医学哲学与治理哲学著作，不构成诊断、治疗或用药建议。</p></div>
<div class="gold">拆模板 · 修通路 · 建免疫</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 574 号 · 修订版 · 十一篇 · 约 {WAN} 万字<br>ISBN 978-1-970820-36-2 · 定价 US$47.00</div></div></body></html>"""


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
