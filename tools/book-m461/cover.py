#!/usr/bin/env python3
"""第 458 号《科学共同体的退位和出版典范转移》（王德生著）封面与封底（由第 520 号改来，藏青底，220 系列版式）：主图是金环里一座城门——左段城墙完好、门洞里站着守门人，右段城墙塌成几截，青色的路从塌口穿进去；塌口外悬一杆秤。
用法：python3 cover.py --fonts /home/claude/fonts --out <dir>
"""
import argparse
import math
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0C1A34', '#1B3158', '#16294A'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#7FA7C9', '#EFE8D6', '#A9B6C8'
ISBN = '979-8-90690-458-4'

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
    """主图（第 458 号）：金环里一座城门。左墙完好带垛口，门楼、拱门，门洞里一个守门人；右墙塌成几截碎块，
    两条青色虚线的路从塌口外绕进城里；塌口上方悬一杆秤（系统认证）。环下三点标「共同体 · 系统 · 部落」。"""
    import random
    rnd = random.Random(458)
    s = W / 1700
    cx, cy, r = W * 0.56, H * 0.60, 470 * s
    out = [rings(cx, cy, r).replace('{uid}', uid)]
    g = lambda x, y: (cx + x * s, cy + y * s)
    def P(pts):
        return ' '.join('%.0f,%.0f' % g(x, y) for x, y in pts)
    gy = 210  # 地面
    out.append(f'<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" stroke="{CREAM}" stroke-opacity=".55" stroke-width="%.1f"/>' % (*g(-400, gy), *g(400, gy), 4*s))
    # 左墙＋垛口
    out.append(f'<polyline points="{P([(-380,gy),(-380,-20),(-150,-20),(-150,gy)])}" fill="none" stroke="{GOLD2}" stroke-width="{14*s:.0f}" stroke-linejoin="round"/>')
    for k in range(4):
        x0 = -380 + k * 60
        out.append(f'<polyline points="{P([(x0,-20),(x0,-58),(x0+32,-58),(x0+32,-20)])}" fill="none" stroke="{GOLD2}" stroke-width="{10*s:.0f}" stroke-linejoin="round"/>')
    # 门楼
    out.append(f'<polyline points="{P([(-150,gy),(-150,-110),(150,-110),(150,gy)])}" fill="none" stroke="{GOLD2}" stroke-width="{16*s:.0f}" stroke-linejoin="round"/>')
    out.append(f'<polyline points="{P([(-190,-110),(0,-215),(190,-110)])}" fill="none" stroke="{GOLD2}" stroke-width="{16*s:.0f}" stroke-linejoin="round"/>')
    # 拱门
    ax0, ay0 = g(-70, gy); ax1, ay1 = g(-70, 40); bx1, by1 = g(70, 40); bx0, by0 = g(70, gy)
    out.append(f'<path d="M {ax0:.0f} {ay0:.0f} L {ax1:.0f} {ay1:.0f} A {70*s:.0f} {70*s:.0f} 0 0 1 {bx1:.0f} {by1:.0f} L {bx0:.0f} {by0:.0f}" fill="none" stroke="{CREAM}" stroke-width="{10*s:.0f}"/>')
    hx, hy = g(0, 95)
    out.append(f'<circle cx="{hx:.0f}" cy="{hy:.0f}" r="{17*s:.0f}" fill="{CREAM}"/>')
    out.append(f'<line x1="{hx:.0f}" y1="{hy+20*s:.0f}" x2="{hx:.0f}" y2="{hy+95*s:.0f}" stroke="{CREAM}" stroke-width="{11*s:.0f}" stroke-linecap="round"/>')
    # 右墙：完好一小段，然后塌
    out.append(f'<polyline points="{P([(150,gy),(150,-20),(215,-20),(232,30)])}" fill="none" stroke="{GOLD2}" stroke-width="{14*s:.0f}" stroke-linejoin="round"/>')
    out.append(f'<polyline points="{P([(262,gy),(270,95),(300,120)])}" fill="none" stroke="{GOLD}" stroke-opacity=".75" stroke-width="{11*s:.0f}" stroke-linejoin="round"/>')
    out.append(f'<polyline points="{P([(340,gy),(334,160),(368,168)])}" fill="none" stroke="{GOLD}" stroke-opacity=".55" stroke-width="{9*s:.0f}" stroke-linejoin="round"/>')
    for (x, y, w, h, rot) in [(232, 188, 26, 18, 14), (300, 194, 22, 15, -18), (372, 196, 18, 12, 6), (318, 176, 14, 10, 30)]:
        X, Y = g(x, y)
        out.append(f'<rect x="{X:.0f}" y="{Y:.0f}" width="{w*s:.0f}" height="{h*s:.0f}" fill="{GOLD}" fill-opacity=".6" transform="rotate({rot} {X:.0f} {Y:.0f})"/>')
    # 路：从塌口外穿进来
    for (pts, op, wd) in [([(470, 250), (400, 236), (330, 222), (270, 198), (220, 150)], .95, 9), ([(470, 290), (390, 272), (310, 250), (250, 228), (190, 200)], .7, 7)]:
        d = 'M %.0f %.0f ' % g(*pts[0]) + ' '.join('L %.0f %.0f' % g(x, y) for x, y in pts[1:])
        out.append(f'<path d="{d}" fill="none" stroke="{CYAN}" stroke-opacity="{op}" stroke-width="{wd*s:.0f}" stroke-dasharray="{4*s:.0f} {22*s:.0f}" stroke-linecap="round"/>')
    # 秤
    kx, ky = g(300, -150)
    sw = 6 * s
    out.append(f'<g fill="none" stroke="{CREAM}" stroke-width="{sw:.1f}" stroke-linecap="round" stroke-linejoin="round">'
               f'<line x1="{kx:.0f}" y1="{ky-62*s:.0f}" x2="{kx:.0f}" y2="{ky+62*s:.0f}"/>'
               f'<line x1="{kx-85*s:.0f}" y1="{ky-40*s:.0f}" x2="{kx+85*s:.0f}" y2="{ky-40*s:.0f}"/>'
               f'<path d="M {kx-85*s:.0f} {ky-40*s:.0f} L {kx-112*s:.0f} {ky+12*s:.0f} L {kx-58*s:.0f} {ky+12*s:.0f} Z"/>'
               f'<path d="M {kx+85*s:.0f} {ky-40*s:.0f} L {kx+58*s:.0f} {ky+12*s:.0f} L {kx+112*s:.0f} {ky+12*s:.0f} Z"/>'
               f'<line x1="{kx-32*s:.0f}" y1="{ky+62*s:.0f}" x2="{kx+32*s:.0f}" y2="{ky+62*s:.0f}"/></g>')
    base = cy + r * 0.86
    for (x, lab, col) in [(cx - r * 0.42, '共同体', GOLD2), (cx, '系统', CREAM), (cx + r * 0.42, '部落', CYAN)]:
        out.append(f'<circle cx="{x:.0f}" cy="{base:.0f}" r="{9*s:.0f}" fill="{col}"/>')
        out.append(f'<text x="{x:.0f}" y="{base + 52*s:.0f}" font-size="{30*s:.0f}" text-anchor="middle" font-family="Noto Sans CJK SC" fill="{CREAM}" fill-opacity=".88" letter-spacing="{6*s:.0f}">{lab}</text>')
    out.append(f'<line x1="{cx - r*0.62:.0f}" y1="{base:.0f}" x2="{cx + r*0.62:.0f}" y2="{base:.0f}" stroke="{GOLD}" stroke-opacity=".45" stroke-width="{1.4*s:.1f}"/>')
    for _ in range(60):
        out.append(f'<circle cx="{rnd.uniform(0, W):.0f}" cy="{rnd.uniform(H*0.30, H*0.40):.0f}" r="{rnd.uniform(.8, 2.2)*s:.1f}" fill="{CREAM}" fill-opacity="{rnd.uniform(.12, .45):.2f}"/>')
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 458 号</div>
<div class="t"><div class="pre">AI 时代的科研认证</div><div class="big" style="font-size:{33*s:.1f}pt">科学共同体的退位</div>
<div class="sub" style="font-size:{14*s:.1f}pt">和出版典范转移</div><div class="rule"></div></div>
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
.bl p{{font:400 {8.8*s:.1f}pt/1.9 'Noto Serif CJK SC';color:{CREAM};opacity:.9;margin:0 0 {2.6*s:.1f}mm;text-align:left}}
.gold{{font:700 {10.5*s:.1f}pt 'Noto Serif CJK SC';color:{GOLD2};margin-top:{6*s:.1f}mm;letter-spacing:.06em}}
.f{{position:absolute;left:{17*s:.1f}mm;bottom:{17*s:.1f}mm;font:400 {7.2*s:.1f}pt/1.85 'Noto Sans CJK SC';color:{DIM}}}
.f b{{color:{CREAM};font-weight:700;letter-spacing:.12em}}
</style></head><body><div class="pg">{svg}
<div class="c"><div class="lab">判 词</div>
<div class="q" style="font-size:{13.2*s:.1f}pt">认证没有消失，它搬了家：<br>统一性的知识交给系统，<br>同一性谱系的知识交给用它的群体；<br>夹在中间、靠一群人点头的科学共同体，<br>先反扑，再退位。</div><div class="by">——前言</div><div class="rule"></div>
<div class="bl"><p>论文为什么一定要发期刊？因为期刊在一个门洞里捆了五件事：登记谁先想到，分发给人看到，存档以后查得到，替读者先筛一遍，再给职称和经费记账。</p>
<p>AI 让前几件几乎不再花钱，却让「凭什么信这一篇」变得前所未有地稀缺。数学、工程这类统一性的知识，正在交给形式化证明、可复跑流水线和运行记录去点头，像高铁的安全不靠乘客投票；同一性谱系的知识，只能在用它的一群人手里被认下来。夹在中间的同行评审，先是反扑——拒收未核查的稿子、不许 AI 署名、一年禁投——再是退位。</p>
<p>本书从一封拒稿信、1665 年的两份刊物、一杆菜市场的秤讲起，也老实摊开自己：一本在城门外出版的书，认证这一环还欠着。</p></div>
<div class="gold">谁在点头？</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 458 号 · 五篇三十六章 · 约 22 万字<br>ISBN 979-8-90690-458-4 · 定价 US$20.00</div>
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
