#!/usr/bin/env python3
"""第 427 号《范畴的SDE解构入门》封面与封底（由第 491 号改来，220 系列版式）：主图「花沉为壤」——一朵花的花瓣落下，一层层沉成地层。
用法：python3 cover.py --fonts /home/claude/fonts --out <dir>
"""
import argparse
import math
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0B1830', '#1B3158', '#142746'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#58BDCA', '#EFE8D6', '#9FB0C8'
ISBN = '979-8-90690-838-4'

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
    """主图「花沉为壤」：右上一朵发光的花，花瓣一片片落下；下半是一层层起伏的地层，越深越薄、越平；
    落下的花瓣在地层里被压成扁扁的透镜，最深处隐约压着三张旧表格的格线（十格、十二格、三格）。"""
    import random
    rnd = random.Random(427)
    s = W / 1700
    fx, fy = W * 0.73, H * 0.30
    out = [f"""<defs>
 <radialGradient id="glow{uid}" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{CYAN}" stop-opacity=".55"/>
  <stop offset=".45" stop-color="{CYAN}" stop-opacity=".14"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient>
 <radialGradient id="gold{uid}" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{GOLD2}" stop-opacity=".95"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></radialGradient>
 <linearGradient id="pet{uid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{CREAM}" stop-opacity=".95"/><stop offset="1" stop-color="{GOLD}" stop-opacity=".8"/></linearGradient>
</defs>"""]
    # 地层：自上而下，越深越薄越平
    top = H * 0.56
    layers = []
    y = top
    for k in range(11):
        th = (95 - k * 6.5) * s
        amp = (34 - k * 2.8) * s
        ph = rnd.uniform(0, 6.28)
        pts = []
        for i in range(61):
            x = W * i / 60
            yy = y + amp * math.sin(i / 60 * 6.28 * 1.1 + ph) + amp * .35 * math.sin(i / 60 * 6.28 * 2.7 + ph * 1.7)
            pts.append((x, yy))
        layers.append(pts)
        y += th
    layers.append([(W * i / 60, H + 10) for i in range(61)])
    for k in range(len(layers) - 1):
        a, b = layers[k], layers[k + 1]
        d = 'M' + ' L'.join('%.0f %.0f' % q for q in a) + ' L' + ' L'.join('%.0f %.0f' % q for q in b[::-1]) + ' Z'
        fill = '#0E2040' if k % 2 else '#132A4E'
        out.append(f'<path d="{d}" fill="{fill}" fill-opacity="{.55 + .035*k:.2f}"/>')
        out.append('<path d="M' + ' L'.join('%.0f %.0f' % q for q in a) + f'" fill="none" stroke="{GOLD}" stroke-opacity="{.62 - .04*k:.2f}" stroke-width="{(2.2 - .12*k)*s:.1f}"/>')
    # 地层里被压扁的花瓣：越深越扁、越淡
    for k in range(len(layers) - 2):
        a, b = layers[k], layers[k + 1]
        for _ in range(7 - k // 2):
            i = rnd.randint(2, 58)
            x = a[i][0] + rnd.uniform(-8, 8) * s
            yy = (a[i][1] + b[i][1]) / 2
            rx = (30 - k * 1.2) * s; ry = max((11 - k * 1.0) * s, 2.2 * s)
            ang = rnd.uniform(-9, 9)
            out.append(f'<ellipse cx="{x:.0f}" cy="{yy:.0f}" rx="{rx:.0f}" ry="{ry:.1f}" transform="rotate({ang:.0f} {x:.0f} {yy:.0f})" fill="url(#pet{uid})" fill-opacity="{.75 - .06*k:.2f}"/>')
    # 最深处三张旧表的格线
    gy = H * 0.885
    for gx, cols in [(W * 0.38, 10), (W * 0.60, 12), (W * 0.82, 3)]:
        cw = (22 if cols > 3 else 40) * s; ch = 26 * s
        wtot = cw * (cols if cols != 12 else 6); rows = 1 if cols != 12 else 2
        g = [f'<rect x="{gx:.0f}" y="{gy:.0f}" width="{wtot:.0f}" height="{ch*rows:.0f}"/>']
        for c in range(1, int(wtot / cw)):
            g.append(f'<line x1="{gx + c*cw:.0f}" y1="{gy:.0f}" x2="{gx + c*cw:.0f}" y2="{gy + ch*rows:.0f}"/>')
        if rows == 2:
            g.append(f'<line x1="{gx:.0f}" y1="{gy + ch:.0f}" x2="{gx + wtot:.0f}" y2="{gy + ch:.0f}"/>')
        out.append(f'<g fill="none" stroke="{CREAM}" stroke-opacity=".22" stroke-width="{1.4*s:.1f}">' + ''.join(g) + '</g>')
    # 花：光晕、八片瓣、花心
    out.append(f'<circle cx="{fx:.0f}" cy="{fy:.0f}" r="{330*s:.0f}" fill="url(#glow{uid})"/>')
    out.append(f'<circle cx="{fx:.0f}" cy="{fy:.0f}" r="{150*s:.0f}" fill="url(#gold{uid})" fill-opacity=".22"/>')
    for k in range(8):
        ang = k * 45 + 10
        out.append(f'<ellipse cx="{fx:.0f}" cy="{fy - 92*s:.0f}" rx="{38*s:.0f}" ry="{92*s:.0f}" transform="rotate({ang} {fx:.0f} {fy:.0f})" fill="url(#pet{uid})" fill-opacity="{.78 if k % 2 else .62}" stroke="{GOLD2}" stroke-opacity=".7" stroke-width="{1.4*s:.1f}"/>')
    out.append(f'<circle cx="{fx:.0f}" cy="{fy:.0f}" r="{34*s:.0f}" fill="{CYAN}" fill-opacity=".85"/>')
    out.append(f'<circle cx="{fx:.0f}" cy="{fy:.0f}" r="{16*s:.0f}" fill="#E8FBFF"/>')
    # 花茎：细线一路伸进地层
    out.append(f'<path d="M{fx:.0f} {fy + 40*s:.0f} C{fx - 30*s:.0f} {fy + 300*s:.0f} {fx + 40*s:.0f} {top - 120*s:.0f} {fx - 10*s:.0f} {top + 60*s:.0f}" fill="none" stroke="{CREAM}" stroke-opacity=".55" stroke-width="{3*s:.1f}"/>')
    # 正在落下的花瓣：从花到地面，越近地面越扁
    for i in range(26):
        t = rnd.uniform(0, 1)
        x = fx + rnd.uniform(-420, 260) * s * (0.4 + t)
        yy = fy + 140 * s + t * (top - fy - 160 * s)
        rx = 20 * s; ry = (14 - 7 * t) * s
        ang = rnd.uniform(0, 180)
        out.append(f'<ellipse cx="{x:.0f}" cy="{yy:.0f}" rx="{rx:.0f}" ry="{ry:.1f}" transform="rotate({ang:.0f} {x:.0f} {yy:.0f})" fill="url(#pet{uid})" fill-opacity="{.85 - .35*t:.2f}"/>')
    for _ in range(80):
        out.append(f'<circle cx="{rnd.uniform(0, W):.0f}" cy="{rnd.uniform(H*0.08, H*0.5):.0f}" r="{rnd.uniform(.8, 2.2)*s:.1f}" fill="{CREAM}" fill-opacity="{rnd.uniform(.12, .45):.2f}"/>')
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 427 号</div>
<div class="t"><div class="pre">范 畴 论 的 发 生 学</div><div class="big">范畴的<br><span style="font-size:.62em;letter-spacing:.06em">SDE解构入门</span></div>
<div class="sub">慢到被当成发现的发生</div><div class="rule"></div></div>
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
<div class="q">范畴是特征纠缠粒子化之后，<br>经长久回写沉淀下来的 S。</div><div class="by">——本书定义</div><div class="rule"></div>
<div class="bl"><p>整理衣柜的人都知道：按季节分、按颜色分还是按场合分，决定了明天早上先找什么。哲学把最底下那一层分法叫作范畴。亚里士多德说它在存在里，康德说它在心里，皮尔斯说它在现象的成色里。三家相去甚远，却都默认范畴本身没有来历。</p>
<p>本书用 SDE 的三大方程、123原理与六路径，逐家接住、逐家诊断，再拿能量与信息两个几十年里就长成的基础概念作证据：范畴是发生的，只是它沉得太深、太慢，人站在它上面思考，于是把它当成了被发现的框。</p>
<p>慢不等于随便改：范畴能改，但要靠真矛盾逼出来。</p></div>
<div class="gold">花沉为壤。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 427 号 · 导论与四部二十章 · 约 25 万字<br>定价 US$20.00</div>
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
