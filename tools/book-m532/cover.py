#!/usr/bin/env python3
"""第 532 号《SDE 语感学》（胡志英 著，王德生 指导）封面与封底（工具链承自第 529 号，藏青底、金青奶白三色，220 系列版式）：
主图是一句话（一行字格）穿过一个场（大圆，场心垫一块九宫），在说歪的那一格，扶正的路向下散开——
一条被场收成金色实线，其余是青色虚线。下标「句 × 场」。全部纯色，不用渐变。
用法：python3 cover.py --fonts /home/claude/fonts --out <dir>
"""
import argparse
import math
import os
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0C1A34', '#1B3158', '#16294A'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#7FA7C9', '#EFE8D6', '#A9B6C8'
ISBN = '979-8-90690-532-1'
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
    """主图（第 532 号）：一句话（一行字格）穿过一个场（大圆与九宫）；在说歪的那一格，扶正的路从一点散开——
    有的场里路收成一条（金实线），有的场里散成几条（青色细线）。下标「句 × 场」。全部纯色。"""
    import random
    rnd = random.Random(532)
    s = W / 1700
    cx, cy, r = W * 0.56, H * 0.575, 450 * s
    out = []
    # 场：三道同心圆＋刻度
    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r:.0f}" fill="{CREAM}" fill-opacity=".035" stroke="{GOLD}" stroke-opacity=".55" stroke-width="{2.2*s:.1f}"/>')
    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r*1.1:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".22" stroke-width="{1.2*s:.1f}"/>')
    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r*0.64:.0f}" fill="none" stroke="{CYAN}" stroke-opacity=".22" stroke-width="{1.2*s:.1f}" stroke-dasharray="3 9"/>')
    ticks = []
    for k in range(72):
        t = k * math.pi * 2 / 72
        r1 = r * (1.035 if k % 6 else 1.06)
        ticks.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (cx + r * math.cos(t), cy + r * math.sin(t), cx + r1 * math.cos(t), cy + r1 * math.sin(t)))
    out.append(f'<g stroke="{GOLD}" stroke-opacity=".45" stroke-width="{1.6*s:.1f}">{"".join(ticks)}</g>')
    # 九宫：场心一块 3×3 的格（九种语感），淡淡地垫在句子下面
    g = 64 * s
    gx, gy = cx - 1.5 * g, cy - 1.5 * g - 140 * s
    cols = [GOLD2, CREAM, CYAN]
    for i in range(3):
        for j in range(3):
            op = .16 if (i, j) not in ((1, 0), (0, 2)) else .55   # 场感、分寸感两格亮一些
            out.append(f'<rect x="{gx + j*g + 4*s:.0f}" y="{gy + i*g + 4*s:.0f}" width="{g - 8*s:.0f}" height="{g - 8*s:.0f}" rx="{5*s:.0f}" fill="{cols[i]}" fill-opacity="{op}"/>')
    # 句：一行十个字格，从左边场外进来，从右边场外出去
    n, cw = 10, 92 * s
    y0 = cy + 40 * s
    x0 = cx - n * cw / 2
    bad = 6
    for k in range(n):
        x = x0 + k * cw
        col = CREAM if k != bad else GOLD2
        out.append(f'<rect x="{x + 8*s:.0f}" y="{y0 - 38*s:.0f}" width="{cw - 16*s:.0f}" height="{76*s:.0f}" rx="{4*s:.0f}" fill="{NAVY_LOW}" stroke="{col}" stroke-opacity="{.95 if k == bad else .7}" stroke-width="{(3.4 if k == bad else 2.2)*s:.1f}"/>')
        if k != bad:
            out.append(f'<line x1="{x + 26*s:.0f}" y1="{y0:.0f}" x2="{x + cw - 26*s:.0f}" y2="{y0:.0f}" stroke="{CREAM}" stroke-opacity=".55" stroke-width="{3*s:.1f}" stroke-linecap="round"/>')
    out.append(f'<line x1="{x0 - 120*s:.0f}" y1="{y0:.0f}" x2="{x0:.0f}" y2="{y0:.0f}" stroke="{CREAM}" stroke-opacity=".5" stroke-width="{2*s:.1f}" stroke-dasharray="6 8"/>')
    out.append(f'<line x1="{x0 + n*cw:.0f}" y1="{y0:.0f}" x2="{x0 + n*cw + 120*s:.0f}" y2="{y0:.0f}" stroke="{CREAM}" stroke-opacity=".5" stroke-width="{2*s:.1f}" stroke-dasharray="6 8"/>')
    # 说歪的那一格：问号般的小点
    bx = x0 + bad * cw + cw / 2
    out.append(f'<circle cx="{bx:.0f}" cy="{y0:.0f}" r="{9*s:.0f}" fill="{GOLD2}"/>')
    # 扶正的路：向下散成四条（青），其中一条被场收成实线（金）
    sx, sy = bx, y0 + 40 * s
    ends = [(-230, 220), (-80, 250), (80, 250), (230, 220)]
    for i, (dx, dy) in enumerate(ends):
        ex, ey = sx + dx * s, sy + dy * s
        c1 = (sx + dx * s * .1, sy + dy * s * .55)
        if i == 1:
            out.append(f'<path d="M {sx:.0f} {sy:.0f} Q {c1[0]:.0f} {c1[1]:.0f} {ex:.0f} {ey:.0f}" fill="none" stroke="{GOLD}" stroke-width="{5*s:.1f}" stroke-linecap="round"/>')
            out.append(f'<circle cx="{ex:.0f}" cy="{ey:.0f}" r="{11*s:.0f}" fill="{GOLD}"/>')
        else:
            out.append(f'<path d="M {sx:.0f} {sy:.0f} Q {c1[0]:.0f} {c1[1]:.0f} {ex:.0f} {ey:.0f}" fill="none" stroke="{CYAN}" stroke-opacity=".8" stroke-width="{2.4*s:.1f}" stroke-dasharray="10 9" stroke-linecap="round"/>')
            out.append(f'<circle cx="{ex:.0f}" cy="{ey:.0f}" r="{8*s:.0f}" fill="{NAVY_LOW}" stroke="{CYAN}" stroke-width="{2.4*s:.1f}"/>')
    # 底部标：句 × 场
    base = cy + r * 0.84
    out.append(f'<line x1="{cx - 380*s:.0f}" y1="{base:.0f}" x2="{cx + 380*s:.0f}" y2="{base:.0f}" stroke="{GOLD}" stroke-opacity=".45" stroke-width="{1.4*s:.1f}"/>')
    for (x, lab, cap, col) in [(cx - 230 * s, '句', '这一句话', CREAM), (cx, '×', '', GOLD2), (cx + 230 * s, '场', '落在这个场里', CYAN)]:
        out.append(f'<text x="{x:.0f}" y="{base + 70*s:.0f}" font-size="{(52 if lab != "×" else 44)*s:.0f}" text-anchor="middle" font-family="Noto Serif CJK SC" font-weight="700" fill="{col}" fill-opacity=".95">{lab}</text>')
        if cap:
            out.append(f'<text x="{x:.0f}" y="{base + 116*s:.0f}" font-size="{25*s:.0f}" text-anchor="middle" font-family="Noto Sans CJK SC" fill="{GOLD2}" fill-opacity=".85" letter-spacing="{4*s:.0f}">{cap}</text>')
    for _ in range(60):
        out.append(f'<circle cx="{rnd.uniform(0, W):.0f}" cy="{rnd.uniform(H*0.30, H*0.355):.0f}" r="{rnd.uniform(.8, 2.2)*s:.1f}" fill="{CREAM}" fill-opacity="{rnd.uniform(.12, .45):.2f}"/>')
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 532 号</div>
<div class="t"><div class="pre">语言学 · 九问</div><div class="big" style="font-size:{46*s:.1f}pt">SDE<br>语感学</div>
<div class="sub">语言学的一个新典范</div><div class="rule"></div></div>
<div class="b"><div class="au">胡志英　著</div><div class="pe" style="font-size:{8*s:.1f}pt;color:{CREAM};letter-spacing:.24em;margin-top:{1.6*s:.1f}mm">王德生　指导</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div>
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
<div class="c"><div class="lab">判 词</div>
<div class="q">语感不是一个人拥有的<br>能力或知识，<br>而是「句×场」的运行读数。</div><div class="by">——本书判词</div><div class="rule"></div>
<div class="bl"><p>一个五岁的孩子在饭桌上说错了一句话，一桌大人笑了。谁都听得出不对，谁都说不出是哪一条规则不许这样说。同一句话印到考卷上，就成了要画红圈的错。</p>
<p>这本书把语感从一个人身上拿下来，放回一句话落在一个场里的那场运行：它读的是这句话在这个场里还剩多少路要修、要怎样修；它长在回写里，不长在输入里。九问分三篇——语感读的是什么，怎样运行，为何如此——每一问请四位全球近邻作对手，先把对方说到最强，再用一件小事裁决。</p>
<p>全书的实验都是预注册，写明了出现什么局面自己就算错；书中的每一个读数，都只作研究工具，不拿来给学生打分。</p></div>
<div class="gold">那一笑，读的是什么？</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 532 号 · 前篇与九问九章 · 约 {WAN} 万字<br>ISBN 979-8-90690-532-1 · 定价 US$25.00</div>
</div>
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
