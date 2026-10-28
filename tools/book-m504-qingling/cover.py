#!/usr/bin/env python3
"""第 504 号《被清零的不是博士》（王德生著）封面与封底（照前一本的工具改来，藏青底、金青奶白三色，220 系列版式）：主图是金环里一架上半截碎成光点的金梯子，梯脚长出一条向右横展的奶白谱系。
用法：python3 cover.py --fonts /home/claude/fonts --out <dir>
"""
import argparse
import math
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0C1A34', '#1B3158', '#16294A'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#7FA7C9', '#EFE8D6', '#A9B6C8'
ISBN = '979-8-90690-504-8'

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


def arrowhead(x, y, ang, sz, col):
    a1, a2 = ang + 2.6, ang - 2.6
    return '<path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f Z" fill="%s"/>' % (
        x, y, x + sz * math.cos(a1), y + sz * math.sin(a1), x + sz * math.cos(a2), y + sz * math.sin(a2), col)


def art(W, H, uid):
    """主图（第 504 号）：金环里，左边一架金色的梯子，上半截的横档一级级淡去、碎成光点；
    梯脚处长出一条向右横展的谱系，奶白枝干粗细不一，节点有大有小，青色虚线把几处节点接上（接口）。
    环下标「统一 阶梯 → 同一 谱系」。"""
    import random
    rnd = random.Random(504)
    s = W / 1700
    cx, cy, r = W * 0.56, H * 0.60, 470 * s
    out = [f"""<defs>
 <radialGradient id="glow{uid}" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{GOLD2}" stop-opacity=".22"/>
  <stop offset=".5" stop-color="{GOLD}" stop-opacity=".07"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></radialGradient>
</defs>"""]
    out.append(rings(cx, cy, r).replace('{uid}', uid))
    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r*0.95:.0f}" fill="url(#glow{uid})"/>')
    bx, by = cx - 250 * s, cy + 300 * s
    tx, ty = cx - 150 * s, cy - 360 * s
    half = 62 * s

    def lerp(t):
        return bx + (tx - bx) * t, by + (ty - by) * t
    for side in (-1, 1):
        steps = 40
        for i in range(steps):
            t0, t1 = i / steps, (i + 1) / steps
            x0, y0 = lerp(t0); x1, y1 = lerp(t1)
            op = 0.95 if t1 < 0.5 else max(0.0, 0.95 - (t1 - 0.5) * 2.2)
            if op <= 0.02:
                continue
            out.append(f'<line x1="{x0+side*half:.1f}" y1="{y0:.1f}" x2="{x1+side*half:.1f}" y2="{y1:.1f}" stroke="{GOLD}" stroke-opacity="{op:.2f}" stroke-width="{9*s:.1f}" stroke-linecap="round"/>')
    for k in range(1, 12):
        t = k / 12
        x, y = lerp(t)
        if t < 0.5:
            out.append(f'<line x1="{x-half:.1f}" y1="{y:.1f}" x2="{x+half:.1f}" y2="{y:.1f}" stroke="{GOLD2}" stroke-width="{7*s:.1f}" stroke-linecap="round"/>')
        else:
            n = int(14 * (1 - t) + 3)
            for j in range(n):
                u = rnd.uniform(-1, 1)
                dx, dy = rnd.uniform(-30, 30) * s * (t - .4) * 3, rnd.uniform(-26, 26) * s * (t - .4) * 3
                out.append(f'<circle cx="{x+u*half+dx:.1f}" cy="{y+dy:.1f}" r="{rnd.uniform(2.5,6)*s*(1.2-t):.1f}" fill="{GOLD2}" fill-opacity="{max(.12, 1.1-t):.2f}"/>')
    root = (bx + 40 * s, by - 10 * s)
    nodes = []

    def branch(x0, y0, ang, length, w, depth):
        if depth == 0 or length < 40 * s:
            return
        p1 = (x0 + length * 0.35 * math.cos(ang + .25), y0 + length * 0.35 * math.sin(ang + .25))
        p2 = (x0 + length * 0.7 * math.cos(ang - .15), y0 + length * 0.7 * math.sin(ang - .15))
        x1, y1 = x0 + length * math.cos(ang), y0 + length * math.sin(ang)
        pts = [bez((x0, y0), p1, p2, (x1, y1), i / 24) for i in range(25)]
        out.append(f'<path d="{tapered(pts, w, w * .55)}" fill="{CREAM}" fill-opacity="{.55 + .1 * depth:.2f}"/>')
        nodes.append((x1, y1, depth))
        k = 2 if depth > 1 else 1
        for j in range(k + (1 if depth == 3 else 0)):
            na = ang + rnd.uniform(-.75, .75)
            branch(x1, y1, max(-1.2, min(0.45, na)), length * rnd.uniform(.55, .75), w * .62, depth - 1)
    for a0 in (-0.95, -0.50, -0.12, 0.22):
        branch(root[0], root[1], a0, 285 * s, 15 * s, 4)
    for (x, y, d) in nodes:
        rr = (3 + 3.2 * d + rnd.uniform(0, 3)) * s
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rr:.1f}" fill="{CREAM}"/>')
        if d >= 3:
            out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rr*1.9:.1f}" fill="none" stroke="{CREAM}" stroke-opacity=".35" stroke-width="{1.8*s:.1f}"/>')
    sel = sorted(nodes, key=lambda q: q[0])[::3]
    for (x0, y0, _), (x1, y1, _) in zip(sel, sel[1:]):
        out.append(f'<line x1="{x0:.0f}" y1="{y0:.0f}" x2="{x1:.0f}" y2="{y1:.0f}" stroke="{CYAN}" stroke-opacity=".45" stroke-width="{2*s:.1f}" stroke-dasharray="{6*s:.0f} {6*s:.0f}"/>')
    out.append(f'<circle cx="{root[0]:.0f}" cy="{root[1]:.0f}" r="{16*s:.0f}" fill="{GOLD2}"/>')
    base = cy + r * 0.86
    xl, xr = cx - 260 * s, cx + 260 * s
    for (x, lab, cap, col) in [(xl, '统一', '阶梯', GOLD), (xr, '同一', '谱系', CREAM)]:
        out.append(f'<circle cx="{x:.0f}" cy="{base:.0f}" r="{9*s:.0f}" fill="{col}"/>')
        out.append(f'<text x="{x:.0f}" y="{base + 56*s:.0f}" font-size="{38*s:.0f}" text-anchor="middle" font-family="Noto Serif CJK SC" font-weight="700" fill="{CREAM}" fill-opacity=".92">{lab}</text>')
        out.append(f'<text x="{x:.0f}" y="{base + 104*s:.0f}" font-size="{26*s:.0f}" text-anchor="middle" font-family="Noto Sans CJK SC" fill="{GOLD2}" fill-opacity=".85" letter-spacing="{6*s:.0f}">{cap}</text>')
    out.append(f'<line x1="{xl + 40*s:.0f}" y1="{base:.0f}" x2="{xr - 40*s:.0f}" y2="{base:.0f}" stroke="{GOLD}" stroke-opacity=".55" stroke-width="{1.6*s:.1f}"/>')
    out.append(arrowhead(xr - 40 * s, base, 0, 16 * s, GOLD))
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 504 号</div>
<div class="t"><div class="big" style="font-size:{36*s:.1f}pt;line-height:1.32;letter-spacing:.1em">被清零的<br>不是博士</div>
<div class="sub" style="font-size:{12*s:.1f}pt">AI时代博士生的困境与出路</div><div class="sub" style="color:{DIM}">从统一性到同一性谱系</div><div class="rule"></div></div>
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
<div class="q">被清零的不是博士，<br>是那条人人都走的路。</div><div class="by">——本书判词</div><div class="rule"></div>
<div class="bl"><p>凌晨刷到“全球博士生职业生涯一夜清零”，心里一沉的人，不全是因为信了它，是因为它说中了心里早就有的那点不安。本书说：大模型吃进全人类的公共知识，吐出公共知识的最优平均，它最先打穿的，是价值寄存在统一的训练、尺度与阶梯上的那些位置。</p>
<p>死守统一，是和不会累的机器赛跑；散成碎片，是集市散了各卖各的，谁也接不上谁。出路在第三条：看清你在同一性谱系的哪一层——高同一性层是接口，变薄层正被机器接管，近零层是只属于你的来路——再把来路一寸寸长出来。个人与制度，各担一半。</p>
<p>四编十三章，外加导论、结语与后记。</p></div>
<div class="gold">你的来路，接在哪一个问题上？</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 504 号 · 四编十三章 · 约 20 万字<br>ISBN 979-8-90690-504-8 · 定价 US$20.00</div>
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
