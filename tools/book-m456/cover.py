#!/usr/bin/env python3
"""第 456 号《慌：心之荒》（秦莉著，王德生指导；封面不写指导）封面与封底（220 系列版式，藏青底）：主图是金环里的一块心田——左边垄垄成行，往右散成荒地；一条夜路从一盏将熄的灯起，伸到岔口；环下三记「差异已到 · 承受已破 · 重组未及」。
用法：python3 cover.py --fonts /home/claude/fonts --out <dir>
"""
import argparse
import math
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0C1A34', '#1B3158', '#16294A'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#7FA7C9', '#EFE8D6', '#A9B6C8'
ISBN = '979-8-90690-456-0'

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
    """主图（第 456 号）：金环是心。环里一块心田：左边七道垄成行，越往右越断、越散、越歪，成了荒地；
    一条青色虚线的夜路，从左下一盏将熄的灯起，弯进荒里，在右上分成两岔。环下三记：
    实心金点「差异已到」、断开的金环「承受已破」、虚线空心圈「重组未及」。"""
    import random
    rnd = random.Random(456)
    s = W / 1700
    cx, cy, r = W * 0.56, H * 0.60, 470 * s
    R = r * 0.70
    out = [f"""<defs>
 <radialGradient id="glow{uid}" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{GOLD2}" stop-opacity=".22"/>
  <stop offset=".55" stop-color="{GOLD}" stop-opacity=".06"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></radialGradient>
 <radialGradient id="lamp{uid}" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{WARM}" stop-opacity=".85"/>
  <stop offset=".35" stop-color="{GOLD2}" stop-opacity=".30"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></radialGradient>
 <clipPath id="field{uid}"><circle cx="{cx:.0f}" cy="{cy:.0f}" r="{R:.0f}"/></clipPath>
</defs>"""]
    out.append(rings(cx, cy, r).replace('{uid}', uid))
    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{R:.0f}" fill="url(#glow{uid})"/>')
    g = [f'<g clip-path="url(#field{uid})" stroke-linecap="round">']
    rows = 7
    for k in range(rows):
        yy = cy - R * 0.62 + k * (R * 1.24 / (rows - 1))
        x = cx - R
        while x < cx + R:
            t = (x - (cx - R)) / (2 * R)
            seg = (260 - 220 * t ** 0.8) * s * rnd.uniform(.7, 1.15)
            gap = (6 + 70 * t ** 1.6) * s * rnd.uniform(.6, 1.4)
            jit = 34 * s * t ** 1.5
            y0 = yy + rnd.uniform(-jit, jit); y1 = y0 + rnd.uniform(-jit, jit) * 0.9
            op = .92 - .55 * t
            w = (9 - 4 * t) * s
            col = GOLD2 if t < .55 else GOLD
            g.append(f'<line x1="{x:.0f}" y1="{y0:.0f}" x2="{x + seg:.0f}" y2="{y1:.0f}" stroke="{col}" stroke-opacity="{op:.2f}" stroke-width="{w:.1f}"/>')
            x += seg + gap
        for _ in range(5):
            gx = rnd.uniform(cx + R * 0.15, cx + R * 0.95)
            gy = yy + rnd.uniform(-40, 40) * s
            g.append(f'<circle cx="{gx:.0f}" cy="{gy:.0f}" r="{rnd.uniform(2.5, 5)*s:.1f}" fill="{CREAM}" fill-opacity="{rnd.uniform(.15, .40):.2f}"/>')
    g.append('</g>')
    out.extend(g)
    lx, ly = cx - R * 0.62, cy + R * 0.58
    p0, p1, p2, p3 = (lx, ly), (cx - R * 0.10, cy + R * 0.55), (cx - R * 0.05, cy - R * 0.05), (cx + R * 0.30, cy - R * 0.22)
    pts = [bez(p0, p1, p2, p3, i / 40) for i in range(41)]
    d = 'M' + ' L'.join('%.0f %.0f' % q for q in pts)
    out.append(f'<path d="{d}" fill="none" stroke="{CYAN}" stroke-opacity=".85" stroke-width="{11*s:.0f}" stroke-linecap="round" stroke-dasharray="{26*s:.0f} {18*s:.0f}"/>')
    fx, fy = p3
    for (ex, ey) in [(cx + R * 0.70, cy - R * 0.50), (cx + R * 0.74, cy - R * 0.02)]:
        out.append(f'<path d="M {fx:.0f} {fy:.0f} Q {(fx+ex)/2:.0f} {(fy+ey)/2 - 30*s:.0f} {ex:.0f} {ey:.0f}" fill="none" stroke="{CYAN}" stroke-opacity=".40" stroke-width="{8*s:.0f}" stroke-linecap="round" stroke-dasharray="{14*s:.0f} {20*s:.0f}"/>')
    out.append(f'<circle cx="{fx:.0f}" cy="{fy:.0f}" r="{13*s:.0f}" fill="none" stroke="{CREAM}" stroke-width="{4*s:.1f}"/>')
    out.append(f'<circle cx="{lx:.0f}" cy="{ly:.0f}" r="{120*s:.0f}" fill="url(#lamp{uid})"/>')
    out.append(f'<circle cx="{lx:.0f}" cy="{ly:.0f}" r="{17*s:.0f}" fill="{WARM}" fill-opacity=".95"/>')
    out.append(f'<circle cx="{lx:.0f}" cy="{ly:.0f}" r="{30*s:.0f}" fill="none" stroke="{GOLD2}" stroke-opacity=".6" stroke-width="{3*s:.1f}" stroke-dasharray="{8*s:.0f} {10*s:.0f}"/>')
    base = cy + r * 0.88
    xs = [cx - r * 0.50, cx, cx + r * 0.50]
    labs = ['差异已到', '承受已破', '重组未及']
    out.append(f'<line x1="{cx - r*0.70:.0f}" y1="{base:.0f}" x2="{cx + r*0.70:.0f}" y2="{base:.0f}" stroke="{GOLD}" stroke-opacity=".45" stroke-width="{1.4*s:.1f}"/>')
    out.append(f'<circle cx="{xs[0]:.0f}" cy="{base:.0f}" r="{11*s:.0f}" fill="{GOLD2}"/>')
    rr = 13 * s
    out.append(f'<path d="M {xs[1] + rr*math.cos(math.radians(-60)):.1f} {base + rr*math.sin(math.radians(-60)):.1f} A {rr:.1f} {rr:.1f} 0 1 0 {xs[1] + rr*math.cos(math.radians(20)):.1f} {base + rr*math.sin(math.radians(20)):.1f}" fill="none" stroke="{GOLD2}" stroke-width="{4*s:.1f}" stroke-linecap="round"/>')
    out.append(f'<circle cx="{xs[2]:.0f}" cy="{base:.0f}" r="{12*s:.0f}" fill="none" stroke="{CREAM}" stroke-width="{3*s:.1f}" stroke-dasharray="{5*s:.1f} {5*s:.1f}"/>')
    for x, lab in zip(xs, labs):
        out.append(f'<text x="{x:.0f}" y="{base + 54*s:.0f}" font-size="{28*s:.0f}" text-anchor="middle" font-family="Noto Sans CJK SC" fill="{CREAM}" fill-opacity=".88" letter-spacing="{4*s:.0f}">{lab}</text>')
    for _ in range(70):
        out.append(f'<circle cx="{rnd.uniform(0, W):.0f}" cy="{rnd.uniform(H*0.28, H*0.40):.0f}" r="{rnd.uniform(.8, 2.2)*s:.1f}" fill="{CREAM}" fill-opacity="{rnd.uniform(.10, .40):.2f}"/>')
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 456 号</div>
<div class="t"><div class="pre">普通人都能明白的</div><div class="big" style="font-size:{70*s:.1f}pt">慌</div>
<div class="sub">心之荒</div><div class="rule"></div></div>
<div class="b"><div class="au">秦莉　著</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div>
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
<div class="c"><div class="lab">判 词</div>
<div class="q">慌不是怕得厉害，<br>是心之荒：差异已到，<br>承受已破，重组未及。</div><div class="by">——前言</div><div class="rule"></div>
<div class="bl"><p>怕总有个对象，急总有个时限，慌却常常说不出在慌什么。找不到证件的那几分钟，考场上一片空白，一个什么事也没有的周日下午，人都会慌，还会「闲得发慌」。汉字写「慌」，左边是心，右边是荒。</p>
<p>本书说的心，是一个已经成形、平日领着差异走的结构。慌，是三件事挤到了同一刻：差异还在不断发生；光（信息）和粮（能量）亏了，对付不了；心的确定性失效，领不动了。夜色降临，山路未出，光和粮都没有了，前面的路没法预估——这就是心之荒。由此分出思考、现实、自我三界之荒，看清慌怎样传开、怎样缩小一颗心，又怎样在荒里长出新心。</p>
<p>九个问题，三十六位古今中外的近邻：苏洵、谢安、项羽、司马光、程颢、韩信、吕坤，唯识与《安般守意经》，新渡户稻造、白隐、九鬼周造，勒庞、詹姆斯、蒂利希、弗洛姆，还有做实验的人。先把他们说中的写足，再走他们没走的那一步。</p></div>
<div class="gold">缺的是光，还是粮？</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 456 号 · 三篇九编五十四章 · 约 20 万字<br>ISBN 979-8-90690-456-0 · 定价 US$20.00</div>
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
