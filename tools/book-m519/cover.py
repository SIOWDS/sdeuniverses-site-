#!/usr/bin/env python3
"""第 519 号《一张全绿的体检单》（胡敏著）封面与封底（由第 459 号改来，换成深绿底；第 459 号由第 405 号改来，220 系列版式）：主图是金环里一张三栏化验单——刻痕、标准、日子三栏横格对不齐，栏界两道发光的缝。
用法：python3 cover.py --fonts /home/claude/fonts --out <dir>
"""
import argparse
import math
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0A231C', '#17402F', '#123528'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#7FD3A1', '#EFE8D6', '#A6C2B4'
ISBN = '979-8-90690-519-2'

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


ROSE, ROSE2, WARM = '#E8A3A0', '#F6C9B8', '#F3D9A4'


def heart_pts(cx, cy, k, n=240):
    pts = []
    for i in range(n + 1):
        t = 2 * math.pi * i / n
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + x * k, cy - y * k))
    return pts


def art(W, H, uid):
    """主图（第 459 号）：金环里斜放一张米色化验单，纸上三栏——左栏「刻痕」金色短刻度、中栏「标准」青色区间带、
    右栏「日子」米白手写起伏线；三栏的横格到了栏界处没有对齐，栏与栏之间留一道发光的细缝（缝在纸上被指认出来）。
    纸后横过一条淡青的起伏线，到纸边断开。环下三点标「刻痕 · 标准 · 日子」。"""
    import random
    rnd = random.Random(519)
    s = W / 1700
    cx, cy, r = W * 0.56, H * 0.62, 470 * s
    out = [f"""<defs>
 <radialGradient id="glow{uid}" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{CYAN}" stop-opacity=".55"/>
  <stop offset=".45" stop-color="{CYAN}" stop-opacity=".14"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient>
 <linearGradient id="paper{uid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F6F0E0"/><stop offset="1" stop-color="#E6DCC4"/></linearGradient>
 <linearGradient id="seam{uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{CYAN}" stop-opacity="0"/>
  <stop offset=".5" stop-color="{CYAN}" stop-opacity=".95"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></linearGradient>
</defs>"""]
    out.append(rings(cx, cy, r).replace('{uid}', uid))
    # 纸后一条淡青起伏线（像一道读数），从环左边进来，到纸边断开，右侧再出来时错开了相位
    def wave(x0, x1, y0, ph, amp):
        pts = []
        x = x0
        while x <= x1:
            pts.append('%.0f %.0f' % (x, y0 + amp * math.sin((x - x0) / (38 * s) + ph)))
            x += 6 * s
        return 'M' + ' L'.join(pts)
    pw, ph = r * 1.02, r * 1.30
    px0, py0 = cx - pw / 2, cy - ph / 2 - r * 0.05
    out.append(f'<path d="{wave(cx - r*1.45, px0 - 10*s, cy + r*0.10, 0, 14*s)}" fill="none" stroke="{CYAN}" stroke-opacity=".45" stroke-width="{2.2*s:.1f}"/>')
    out.append(f'<path d="{wave(px0 + pw + 10*s, cx + r*1.45, cy + r*0.10, 2.2, 14*s)}" fill="none" stroke="{CYAN}" stroke-opacity=".45" stroke-width="{2.2*s:.1f}"/>')
    g = [f'<g transform="rotate(-6 {cx:.0f} {cy:.0f})">']
    # 纸影与纸
    g.append(f'<rect x="{px0 + 14*s:.0f}" y="{py0 + 18*s:.0f}" width="{pw:.0f}" height="{ph:.0f}" rx="{6*s:.0f}" fill="#000" fill-opacity=".28"/>')
    g.append(f'<rect x="{px0:.0f}" y="{py0:.0f}" width="{pw:.0f}" height="{ph:.0f}" rx="{6*s:.0f}" fill="url(#paper{uid})"/>')
    # 抬头两行细字条
    for k, wfrac in enumerate([0.55, 0.36]):
        g.append(f'<rect x="{px0 + 40*s:.0f}" y="{py0 + (44 + k*26)*s:.0f}" width="{pw*wfrac:.0f}" height="{9*s:.0f}" rx="{4*s:.0f}" fill="#1B3158" fill-opacity="{.55 - k*.2:.2f}"/>')
    top = py0 + 112 * s
    bot = py0 + ph - 46 * s
    cw = (pw - 80 * s) / 3
    xs = [px0 + 40 * s + i * cw for i in range(4)]
    g.append(f'<line x1="{xs[0]:.0f}" y1="{top - 10*s:.0f}" x2="{xs[3]:.0f}" y2="{top - 10*s:.0f}" stroke="#1B3158" stroke-opacity=".5" stroke-width="{2*s:.1f}"/>')
    # 三栏各自的横格：行距各不相同，所以到了栏界就对不齐
    rows = [(46, 0), (52, 10), (40, 22)]
    cols = ['#B08A3C', '#2E8F9C', '#7A6E58']
    for ci in range(3):
        step, off = rows[ci]
        y = top + off * s
        while y < bot:
            g.append(f'<line x1="{xs[ci] + 10*s:.0f}" y1="{y:.0f}" x2="{xs[ci+1] - 10*s:.0f}" y2="{y:.0f}" stroke="{cols[ci]}" stroke-opacity=".28" stroke-width="{1.4*s:.1f}"/>')
            y += step * s
    # 左栏：刻痕——金色短刻度条（长短不一）
    y = top + 12 * s
    while y < bot - 10 * s:
        ln = rnd.uniform(.25, .85) * (cw - 30 * s)
        g.append(f'<rect x="{xs[0] + 14*s:.0f}" y="{y:.0f}" width="{ln:.0f}" height="{10*s:.0f}" rx="{3*s:.0f}" fill="{GOLD}" fill-opacity=".85"/>')
        y += 46 * s
    # 中栏：标准——青色区间带（参考范围），一条细线落在带外
    y = top + 18 * s
    k = 0
    while y < bot - 10 * s:
        a0 = xs[1] + 16 * s + rnd.uniform(0, 12) * s
        a1 = xs[2] - 16 * s - rnd.uniform(0, 12) * s
        g.append(f'<rect x="{a0:.0f}" y="{y:.0f}" width="{a1 - a0:.0f}" height="{12*s:.0f}" rx="{6*s:.0f}" fill="{CYAN}" fill-opacity=".22"/>')
        mx = a0 + (a1 - a0) * (rnd.uniform(.2, .8))
        g.append(f'<circle cx="{mx:.0f}" cy="{y + 6*s:.0f}" r="{5*s:.1f}" fill="#2E8F9C"/>')
        y += 52 * s; k += 1
    # 右栏：日子——米白底上的手写起伏线（深一点的暖灰，像笔迹）
    y = top + 30 * s
    while y < bot - 10 * s:
        pts = []
        x = xs[2] + 16 * s
        ph0 = rnd.uniform(0, 6)
        while x < xs[3] - 16 * s:
            pts.append('%.0f %.0f' % (x, y + 5 * s * math.sin((x - xs[2]) / (9 * s) + ph0)))
            x += 4 * s
        g.append(f'<path d="M{" L".join(pts)}" fill="none" stroke="#5E5240" stroke-opacity=".75" stroke-width="{2.2*s:.1f}" stroke-linecap="round"/>')
        y += 40 * s
    # 两道发光的缝（栏界）
    for xx in xs[1:3]:
        g.append(f'<rect x="{xx - 4*s:.0f}" y="{top - 4*s:.0f}" width="{8*s:.0f}" height="{bot - top + 8*s:.0f}" fill="url(#seam{uid})" fill-opacity=".85"/>')
        g.append(f'<line x1="{xx:.0f}" y1="{top:.0f}" x2="{xx:.0f}" y2="{bot:.0f}" stroke="#FFFFFF" stroke-opacity=".75" stroke-width="{1.2*s:.1f}"/>')
    g.append('</g>')
    out.append(''.join(g))
    # 环下三点与标签
    base = cy + r * 0.86
    for (x, lab, col) in [(cx - r * 0.42, '刻痕', GOLD2), (cx, '标准', CYAN), (cx + r * 0.42, '日子', CREAM)]:
        out.append(f'<circle cx="{x:.0f}" cy="{base:.0f}" r="{9*s:.0f}" fill="{col}"/>')
        out.append(f'<text x="{x:.0f}" y="{base + 52*s:.0f}" font-size="{30*s:.0f}" text-anchor="middle" font-family="Noto Sans CJK SC" fill="{CREAM}" fill-opacity=".88" letter-spacing="{6*s:.0f}">{lab}</text>')
    out.append(f'<line x1="{cx - r*0.62:.0f}" y1="{base:.0f}" x2="{cx + r*0.62:.0f}" y2="{base:.0f}" stroke="{GOLD}" stroke-opacity=".45" stroke-width="{1.4*s:.1f}"/>')
    for _ in range(70):
        out.append(f'<circle cx="{rnd.uniform(0, W):.0f}" cy="{rnd.uniform(H*0.30, H*0.42):.0f}" r="{rnd.uniform(.8, 2.2)*s:.1f}" fill="{CREAM}" fill-opacity="{rnd.uniform(.12, .45):.2f}"/>')
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 519 号</div>
<div class="t"><div class="pre">SDE 符号学 · 医疗符号学</div><div class="big big2">一张全绿的<br>体检单</div>
<div class="sub">刻痕、标准与日子为什么总对不上</div><div class="rule"></div></div>
<div class="b"><div class="au">胡敏　著</div><div class="pe" style="letter-spacing:.2em;margin-top:1.6mm">王德生　指导</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div>
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
.bl p{{font:400 {8.8*s:.1f}pt/1.9 'Noto Serif CJK SC';color:{CREAM};opacity:.9;margin:0 0 {2.6*s:.1f}mm;text-align:left}}
.gold{{font:700 {10.5*s:.1f}pt 'Noto Serif CJK SC';color:{GOLD2};margin-top:{6*s:.1f}mm;letter-spacing:.06em}}
.f{{position:absolute;left:{17*s:.1f}mm;bottom:{17*s:.1f}mm;font:400 {7.2*s:.1f}pt/1.85 'Noto Sans CJK SC';color:{DIM}}}
.f b{{color:{CREAM};font-weight:700;letter-spacing:.12em}}
</style></head><body><div class="pg">{svg}
<div class="c"><div class="lab">开 篇</div>
<div class="q">单子全绿，<br>她的下午却没有地方放。</div><div class="by">——前言</div><div class="rule"></div>
<div class="bl"><p>新加坡一所小学的行政人员蔡淑贞，体检报告每一项都在参考范围里，医生说“没有问题”。可是半年来，每天下午她都觉得不对劲。单子没有错，她也没有说谎——两句话，能不能同时是真的？</p>
<p>一张体检单上同时说着三种话：测得值是身体在仪器里留下的刻痕，参考范围与指南是医学约定的标准，“我哪里不舒服”是病人的日子。三种话各有凭据，却未必在一次门诊里相遇。本书从一个数字的来路、一条界线的挪动、一个病名怎样凝成偶像与石心，一直讲到一张三栏对账单，怎样让未说完的问题有记录、有人接、有下一次。</p>
<p>本书不给任何诊断与治疗建议，具体病情请遵医嘱。第二十一章写下三场能让本书认错的检验：如果对账没有带来事前约定的改善，作者先改自己。</p></div>
<div class="gold">没有答案时，也不能把人删掉。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 519 号 · 八编二十二章 · 约 25 万字<br>ISBN 979-8-90690-519-2 · 定价 US$20.00</div>
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
