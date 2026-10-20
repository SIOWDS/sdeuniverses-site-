#!/usr/bin/env python3
"""第 501 号《道德经SDE新解》封面与封底（由第 486 号 cover.py 改来，220 系列版式）。
主图原创：「一根不断的线」——一团连着的细丝，一处被一只手攥住拉直（统），另一处自然盘绕垂着（一）；金、奶白、青三色。
用法：python3 cover.py --out /home/claude/b501
产物：cover-print.pdf / back-print.pdf（170×240）、cover-reader.pdf / back-reader.pdf（190×250）、cover.jpg / backcover.jpg（1004×1418）
"""
import argparse
import math
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0B1830', '#1B3158', '#142746'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#58BDCA', '#EFE8D6', '#9FB0C8'
ISBN = '979-8-90690-167-5'
import random

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


def smooth(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def catmull(pts, per=24):
    out = []
    P = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(per):
            t = k / per
            t2, t3 = t * t, t * t * t
            out.append((0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
                        0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)))
    out.append(pts[-1])
    return out


def resample(poly, step):
    """按弧长等距重采样，返回 [(x, y, s)]。"""
    out = [(poly[0][0], poly[0][1], 0.0)]
    acc, last = 0.0, poly[0]
    carry = 0.0
    for p in poly[1:]:
        d = math.hypot(p[0] - last[0], p[1] - last[1])
        while carry + d >= step and d > 0:
            f = (step - carry) / d
            last = (last[0] + (p[0] - last[0]) * f, last[1] + (p[1] - last[1]) * f)
            acc += step
            out.append((last[0], last[1], acc))
            d = math.hypot(p[0] - last[0], p[1] - last[1]); carry = 0.0
        carry += d; last = p
    return out


def capsule(cx, cy, w, h, fill, stroke, sw, extra=''):
    return f'<rect x="{cx - w/2:.1f}" y="{cy - h/2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{w/2:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'


def art(W, H, uid):
    """主图「一根不断的线」。设计盒 1700×2400，按宽缩放、底边对齐。
    一束细丝（11 根，金／奶白／青）从上边直直垂下，被右侧伸来的一只手攥住（统：拉直、并排、听一只手的）；
    手以下，丝一点点松开，绕成圈，垂成弹簧状，一直垂到底边（一：相连、不断、碰一处全体都动）。"""
    rnd = random.Random(501)
    s = W / 1700
    oy = H - 2400 * s
    FX, FY = 1135.0, 1060.0            # 拳心
    # 引导线：自上边笔直落到拳，过拳后向左下松开，再垂向底边
    guide = catmull([(FX, -120), (FX, 700), (FX, FY), (FX - 6, FY + 190), (FX - 70, FY + 330), (FX - 230, FY + 440), (FX - 400, FY + 560),
                     (FX - 560, FY + 700), (FX - 480, FY + 880), (FX - 560, FY + 1040), (FX - 420, FY + 1200), (FX - 500, FY + 1380), (FX - 380, FY + 1520)], per=40)
    pts = resample(guide, 3.0)
    s_fist = next(sv for (x, y, sv) in pts if y >= FY)       # 拳所在弧长
    s_tot = pts[-1][2]
    NS = 11
    cols = [GOLD2, CREAM, CYAN, GOLD, CREAM, CYAN, GOLD2, CREAM, GOLD, CYAN, CREAM]
    strands = []
    for i in range(NS):
        off = (i - (NS - 1) / 2) / ((NS - 1) / 2)       # -1..1
        ph = rnd.uniform(0, 6.28); rr = rnd.uniform(0.85, 1.15); wob = rnd.uniform(0.6, 1.4)
        P = []
        for k, (x, y, sv) in enumerate(pts):
            # 切线与法线
            x2, y2, _ = pts[min(k + 1, len(pts) - 1)]; x1, y1, _ = pts[max(k - 1, 0)]
            tx, ty = x2 - x1, y2 - y1; ln = math.hypot(tx, ty) or 1
            tx, ty = tx / ln, ty / ln; nx, ny = -ty, tx
            rel = smooth(s_fist + 60, s_fist + 520, sv)          # 松开程度 0..1
            above = 1.0 if sv < s_fist else 0.0
            spread = (8.5 if above else 3.0 + (8.5 - 3.0) * 0) * 0 + (11.0 * (1 - rel) + 46.0 * rel) if not above else 12.0
            if sv > s_fist - 90 and sv < s_fist + 90:
                spread = 4.5 + 7.5 * smooth(0, 90, abs(sv - s_fist))
            o = off * spread
            # 盘绕：绕引导线的螺旋，半径随松开程度加大；垂下段再收一点，成弹簧
            nz = 0.78 + 0.32 * math.sin(sv * 0.0043 + 1.3) + 0.2 * math.sin(sv * 0.0121 + 0.4)
            R = (128 * rel * nz) * (1 - 0.3 * smooth(s_fist + 1500, s_tot, sv))
            w = 0.052 * (1 + 0.16 * math.sin(sv * 0.0037 + 2.0)) * (1 + 0.03 * (i - 5) / 5)
            a = (sv - s_fist - 300) * w + ph * 0.55 * rel
            cxo = R * rr * math.cos(a) * (0.62 + 0.3 * math.sin(sv * 0.005))
            cyo = R * rr * math.sin(a) * 1.0
            # 松开后各根丝各自有一点飘
            dr = rel * wob * 9 * math.sin(sv * 0.021 + ph)
            P.append((x + nx * (o + dr) + cxo, y + ny * (o + dr) + cyo))
        strands.append((cols[i], P))
    out = []
    # 光晕
    out.append(f'<circle cx="{FX}" cy="{FY}" r="360" fill="url(#halo{uid})"/>')
    out.append(f'<circle cx="{FX - 380}" cy="{FY + 760}" r="520" fill="url(#halo{uid})" opacity=".55"/>')
    # 丝：先一层宽而淡的辉，再细线
    def path(P, a, b):
        seg = P[a:b]
        return 'M' + ' L'.join('%.1f %.1f' % p for p in seg)
    for pass_ in (0, 1):
        for i, (c, P) in enumerate(strands):
            if pass_ == 0:
                out.append(f'<path d="{path(P, 0, len(P))}" fill="none" stroke="{c}" stroke-opacity=".07" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>')
            else:
                sw = 1.9 + (i % 3) * 0.55
                op = 0.62 + (i % 4) * 0.09
                out.append(f'<path d="{path(P, 0, len(P))}" fill="none" stroke="{c}" stroke-opacity="{op:.2f}" stroke-width="{sw:.1f}" stroke-linecap="round" stroke-linejoin="round"/>')
    # 一只手：局部坐标 x 沿丝（向上为 +x），y 指向手腕（向右）
    hand = []
    fing = [(-96, 70), (-34, 78), (28, 74), (88, 62)]       # (沿丝的位置, 指长)
    for k, (px, ln) in enumerate(fing):
        top = -48 + k * 2
        hand.append(capsule(px, (top + top + ln * 2) / 2 + 28, 56, ln * 2 + 12, '#18305A', CREAM, 2.6))
        hand.append(f'<path d="M{px - 18:.0f} {top + 20:.0f} Q{px:.0f} {top + 8:.0f} {px + 18:.0f} {top + 20:.0f}" fill="none" stroke="{GOLD2}" stroke-opacity=".8" stroke-width="2"/>')
    hand.append(f'<rect x="-128" y="116" width="250" height="150" rx="52" fill="#1B3768" stroke="{CREAM}" stroke-width="2.6"/>')
    hand.append(capsule(10, -66, 232, 54, '#21457C', CREAM, 2.6))                           # 拇指
    hand.append(f'<path d="M-86 -66 H100" stroke="{GOLD2}" stroke-opacity=".7" stroke-width="2"/>')
    hand.append(f'<path d="M-100 266 L-92 700 L110 700 L116 266 Z" fill="#16294C" stroke="{CREAM}" stroke-opacity=".9" stroke-width="2.4"/>')   # 手腕与袖
    hand.append(f'<path d="M-96 330 H112 M-95 352 H113" stroke="{GOLD}" stroke-width="2.4" stroke-opacity=".8"/>')
    hand.append(f'<path d="M-60 150 Q0 170 60 150" fill="none" stroke="{GOLD2}" stroke-opacity=".5" stroke-width="2"/>')
    # 手指缝里露出的丝：在指与指之间画几段短丝，让它读成「穿过去」
    for k in range(3):
        px = (fing[k][0] + fing[k + 1][0]) / 2 + 2
        hand.append(f'<line x1="{px:.0f}" y1="-40" x2="{px:.0f}" y2="-52" stroke="{CREAM}" stroke-opacity=".9" stroke-width="2.4"/>')
    out.append(f'<g transform="translate({FX} {FY}) rotate(-90)">{"".join(hand)}</g>')
    # 拳上方的一圈绷紧的短弧（受力）
    for r_, op in ((70, .55), (100, .32), (134, .18)):
        out.append(f'<path d="M{FX - r_} {FY - 150} Q{FX} {FY - 150 - r_ * 0.55} {FX + r_} {FY - 150}" fill="none" stroke="{GOLD2}" stroke-opacity="{op}" stroke-width="2"/>')
    return f'<g transform="translate(0 {oy:.1f}) scale({s:.4f})">{"".join(out)}</g>'


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
.big{{font:700 {42*s:.1f}pt/1.25 'Noto Serif CJK SC';letter-spacing:.1em;color:#F7F1E3;margin:{2*s:.1f}mm 0 {3*s:.1f}mm {-1*s:.1f}mm}}
.big2{{font-size:{34*s:.1f}pt;line-height:1.3;letter-spacing:.04em}}
.sub{{font:400 {10.6*s:.1f}pt/1.75 'Noto Serif CJK SC';color:{GOLD2};letter-spacing:.04em}}
.rule{{width:{16*s:.1f}mm;border-top:.9pt solid {GOLD};margin-top:{5*s:.1f}mm}}
.b{{position:absolute;left:{17*s:.1f}mm;bottom:{17*s:.1f}mm}}
.au{{font:400 {12.5*s:.1f}pt 'Noto Serif CJK SC';color:{CREAM};letter-spacing:.28em}}
.ph{{font:700 {8.4*s:.1f}pt 'Noto Sans CJK SC';color:{GOLD2};letter-spacing:.3em;margin-top:{6*s:.1f}mm}}
.pe{{font:400 {6.6*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.08em;margin-top:{.8*s:.1f}mm}}
.no{{position:absolute;right:{15*s:.1f}mm;top:{16*s:.1f}mm;font:400 {6.6*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.2em;text-align:right}}
</style></head><body><div class="pg">{svg}
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 501 号</div>
<div class="t"><div class="pre">普通人都能明白的</div><div class="big">道德经<br>SDE新解</div>
<div class="sub">回去的路，是另一条路。<br>根是一块一直被写的土，<br>不是埋着的老物件。</div><div class="rule"></div></div>
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
<div class="c"><div class="lab">判 语</div>
<div class="q">回去的路，<br>是另一条路。<br>根是一块一直被写的土，<br>不是埋着的老物件。</div><div class="by">——全书的一句话</div><div class="rule"></div>
<div class="bl"><p>「统」字带绞丝旁，说的是丝。一团丝，每一根都和别的连着，碰一处，全体都动，这是一；把每一根的头攥在手里，往一个方向拽，丝是拉直了，可它们不再互相连着，只是并排听一只手的，这是统。</p>
<p>本书读《道德经》，读出来的一，是摸出来的不间断。八十一章，每章把郭店、帛书、通行本的差别摆在你面前，指给你看哪个字挪了，再放进教育、健康、事业三个地方各走一遍；读不动的地方，就写读不动。</p></div>
<div class="gold">写一横，笔不提起来，手上的感觉只有一句：没断。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 501 号 · 九编八十一章 · 约 75 万字<br>定价 US$25.00</div>
</div></body></html>"""


def main():
    import weasyprint
    import pymupdf
    ap = argparse.ArgumentParser()
    ap.add_argument('--fonts', type=Path, default=Path('.'))
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
