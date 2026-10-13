#!/usr/bin/env python3
"""第 309 号《躺平的SDE解构》封面与封底（照第 394、359 号的 220 系列版式）：藏青渐变底、细点阵、金色光晕与刻度环；
主图是一只转速表，指针停在最低一格：怠速。

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
ISBN = '979-8-90690-817-9'

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
    """主图：一只转速表，指针停在最低一格（怠速）；表盘里三道细环是 123 引擎的三环，都在转，只是幅度压到最低；
    左下几团淡淡的白气（排气管还在吐气，车没熄火）；右下一个 H 形挡位，挡把停在空挡，一道虚线指向一挡。"""
    s = W / 1700
    cx, cy, r = W * 0.60, H * 0.585, 470 * s
    u = r / 450
    out = [rings(cx, cy, r).replace('{uid}', uid)]
    a0, a1 = math.radians(225), math.radians(-45)
    R0 = r * 0.86
    for k in range(0, 41):
        t = k / 40
        a = a0 + (a1 - a0) * t
        big = k % 5 == 0
        r1, r2 = R0 * (0.86 if big else 0.92), R0
        col = '#D8826A' if t > 0.78 else (CREAM if big else GOLD)
        out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-opacity="%.2f" stroke-width="%.1f"/>' % (
            cx + r1 * math.cos(a), cy - r1 * math.sin(a), cx + r2 * math.cos(a), cy - r2 * math.sin(a), col, .9 if big else .55, (4.2 if big else 2) * s))
        if big:
            rt = R0 * 0.72
            out.append('<text x="%.1f" y="%.1f" font-size="%.0f" font-family="Noto Sans CJK SC" fill="%s" fill-opacity=".85" text-anchor="middle" dominant-baseline="middle">%d</text>' % (
                cx + rt * math.cos(a), cy - rt * math.sin(a), 34 * s, CREAM, k // 5))
    def arc(rr, t0, t1):
        p0 = (cx + rr * math.cos(a0 + (a1 - a0) * t0), cy - rr * math.sin(a0 + (a1 - a0) * t0))
        p1 = (cx + rr * math.cos(a0 + (a1 - a0) * t1), cy - rr * math.sin(a0 + (a1 - a0) * t1))
        large = 1 if (t1 - t0) * 270 > 180 else 0
        return 'M%.1f %.1f A%.1f %.1f 0 %d 1 %.1f %.1f' % (p0[0], p0[1], rr, rr, large, p1[0], p1[1])
    out.append(f'<path d="{arc(R0*1.04, 0.16, 1.0)}" fill="none" stroke="{GOLD}" stroke-opacity=".18" stroke-width="{6*s:.1f}"/>')
    out.append(f'<path d="{arc(R0*1.04, 0.0, 0.16)}" fill="none" stroke="{CYAN}" stroke-opacity=".8" stroke-width="{10*s:.1f}" stroke-linecap="round"/>')
    for k, (rr, ang, col) in enumerate([(150 * u, 30, GOLD2), (112 * u, 150, CYAN), (76 * u, 270, CREAM)]):
        out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{rr:.0f}" fill="none" stroke="{col}" stroke-opacity=".22" stroke-width="{2*s:.1f}"/>')
        b0, b1 = math.radians(ang), math.radians(ang + 26)
        out.append('<path d="M%.1f %.1f A%.1f %.1f 0 0 1 %.1f %.1f" fill="none" stroke="%s" stroke-opacity=".9" stroke-width="%.1f" stroke-linecap="round"/>' % (
            cx + rr * math.cos(b0), cy + rr * math.sin(b0), rr, rr, cx + rr * math.cos(b1), cy + rr * math.sin(b1), col, 5 * s))
    t = 0.10
    a = a0 + (a1 - a0) * t
    tip = (cx + R0 * 0.95 * math.cos(a), cy - R0 * 0.95 * math.sin(a))
    pts = [(cx + (tip[0] - cx) * q, cy + (tip[1] - cy) * q) for q in [i / 14 for i in range(15)]]
    out.append(f'<path d="{tapered(pts, 16*s, 2*s)}" fill="{GOLD2}"/>')
    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{30*u:.0f}" fill="{NAVY_TOP}" stroke="{GOLD2}" stroke-width="{4*s:.1f}"/><circle cx="{cx:.0f}" cy="{cy:.0f}" r="{9*u:.0f}" fill="{GOLD2}"/>')
    out.append(f'<text x="{cx:.0f}" y="{cy+215*u:.0f}" font-size="{24*s:.0f}" font-family="Noto Sans CJK SC" fill="{DIM}" text-anchor="middle" letter-spacing="{6*s:.0f}">×1000 r/min</text>')
    ex, ey = cx - 520 * u, cy + 420 * u
    for k in range(6):
        rr = (26 + k * 14) * u
        out.append(f'<circle cx="{ex - k*18*u:.0f}" cy="{ey - k*70*u:.0f}" r="{rr:.0f}" fill="{CREAM}" fill-opacity="{.22 - k*.03:.3f}"/>')
    out.append(f'<rect x="{ex+10*u:.0f}" y="{ey+16*u:.0f}" width="{90*u:.0f}" height="{22*u:.0f}" rx="{8*u:.0f}" fill="{GOLD}" fill-opacity=".7"/>')
    hx, hy, hw = cx + 380 * u, cy + 470 * u, 150 * u
    g = []
    for i in range(3):
        x = hx + i * hw / 2
        g.append(f'<line x1="{x:.0f}" y1="{hy-hw*.55:.0f}" x2="{x:.0f}" y2="{hy+hw*.55:.0f}"/>')
    g.append(f'<line x1="{hx:.0f}" y1="{hy:.0f}" x2="{hx+hw:.0f}" y2="{hy:.0f}"/>')
    out.append(f'<g stroke="{CREAM}" stroke-opacity=".55" stroke-width="{6*s:.1f}" stroke-linecap="round">' + ''.join(g) + '</g>')
    for lab, x, y in [('1', hx, hy - hw * .55), ('2', hx, hy + hw * .55), ('3', hx + hw / 2, hy - hw * .55), ('4', hx + hw / 2, hy + hw * .55), ('5', hx + hw, hy - hw * .55), ('R', hx + hw, hy + hw * .55)]:
        dy = -26 * u if y < hy else 44 * u
        out.append(f'<text x="{x:.0f}" y="{y+dy:.0f}" font-size="{26*s:.0f}" font-family="Noto Sans CJK SC" fill="{GOLD2 if lab=="1" else DIM}" text-anchor="middle">{lab}</text>')
    kx, ky = hx + hw / 2, hy
    out.append(f'<path d="M{kx-12*u:.0f} {ky-16*u:.0f} Q{hx+18*u:.0f} {hy-12*u:.0f} {hx:.0f} {hy-hw*.42:.0f}" fill="none" stroke="{GOLD2}" stroke-width="{3*s:.1f}" stroke-dasharray="{9*s:.1f} {8*s:.1f}"/>')
    out.append(f'<circle cx="{kx:.0f}" cy="{ky:.0f}" r="{30*u:.0f}" fill="url(#kite{uid})" stroke="{GOLD}" stroke-width="{3*s:.1f}"/>')
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 309 号</div>
<div class="t"><div class="pre">普通人都能懂的</div><div class="big">躺平的<br>SDE解构</div>
<div class="sub">一台怠速的发动机</div><div class="rule"></div></div>
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
<div class="q">躺平是 123 引擎的怠速：<br>它看见了空转的徒劳，<br>松开了油门，保住了不熄火；<br>可是它把「不熄火」，<br>当成了「在走路」。</div><div class="by">——本书</div><div class="rule"></div>
<div class="bl"><p>路边停着一辆车，排气管吐着白气，发动机低低地响着。车没熄火，也没往前走。很多人说这是懒，说这一代人欲望低。这些话都只看见车没动，没听见发动机还在响。</p>
<p>本书说，躺平不是「一个人」的选择，是一种运行态：两头较劲推不动第三头，回写落进了几颗词，往路上送的劲收到只够不熄火，三维九子都停在维持存在的最低一层。它有三种来路：油门踩死之后，挂不上挡，方向盘和油门打架。</p>
<p>五编四十四章，从一个帖子讲到大学生、企业家、中年与家庭，从竹林、陶渊明讲到安静辞职。怠速是三病里唯一不断环的，所以解冻不是重新点火，是挂挡、松离合、给油。</p></div>
<div class="gold">不熄火，不等于在走路。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 309 号 · 五编四十四章 · 约 20 万字<br>定价 US$20.00</div>
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
