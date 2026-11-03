#!/usr/bin/env python3
"""第 571 号《医患复合体状态发生学——病不在病人身上，也不在医生眼里》（王德生 著）封面与封底（工具链承自上一号，藏青底、金青奶白三色，220 系列版式）：
主图：拉大锯——两个人一推一拉一把大锯，锯口在圆木正中，锯末从锯口落下；锯口正上方一张挂号单（总钥匙「挂号那一刻」）。
全部矢量绘制、纯色，不用照片、不用渐变。封面不写「王德生指导」。
用法：python3 cover.py --fonts /usr/share/fonts/opentype/noto --out <dir>
"""
import argparse
import math
import os
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0C1A34', '#1B3158', '#16294A'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#7FA7C9', '#EFE8D6', '#A9B6C8'
ISBN = '979-8-90690-590-1'
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


def person(x, base, s, facing, lean, col):
    """一个拉锯的人：身体前倾，双手握住锯柄（握点由调用方给出）。facing=1 朝右，-1 朝左。返回 (svg, 手的位置)。"""
    f = facing
    hip = (x, base - 92 * s)
    sh = (x + f * lean * s, base - 168 * s)
    head = (sh[0] + f * 8 * s, sh[1] - 26 * s)
    hand = (sh[0] + f * 62 * s, base - 150 * s)
    elbow = (sh[0] + f * 22 * s, sh[1] + 38 * s)
    knee_f = (x + f * 30 * s, base - 46 * s)
    foot_f = (x + f * 46 * s, base)
    knee_b = (x - f * 16 * s, base - 44 * s)
    foot_b = (x - f * 44 * s, base)
    sw = 9 * s
    path = ('M%.0f %.0f L%.0f %.0f L%.0f %.0f ' % (foot_f + knee_f + hip) +
            'M%.0f %.0f L%.0f %.0f L%.0f %.0f ' % (foot_b + knee_b + hip) +
            'M%.0f %.0f L%.0f %.0f ' % (hip + sh) +
            'M%.0f %.0f L%.0f %.0f L%.0f %.0f' % (sh + elbow + hand))
    out = (f'<path d="{path}" stroke="{col}" stroke-width="{sw:.1f}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
           f'<circle cx="{head[0]:.0f}" cy="{head[1]:.0f}" r="{17*s:.0f}" fill="{col}"/>')
    return out, hand


def art(W, H, uid):
    """主图（第 571 号）：拉大锯。
    一根横放的圆木架在两只木马上；左右两人各握一头锯柄，一推一拉；锯条斜插进圆木正中，锯口在中间，
    锯末从锯口两边落下——锯口不是哪一头锯出来的。左边的人着金色（医生位），右边的人着青色（病人位）；
    圆木上方一张挂号单（总钥匙「挂号那一刻」）。全部纯色，不用渐变。"""
    s = W / 1700
    out = []
    base = H * 0.665
    cx = W * 0.5
    # 地面
    out.append(f'<line x1="{W*0.04:.0f}" y1="{base:.0f}" x2="{W*0.96:.0f}" y2="{base:.0f}" stroke="{GOLD2}" stroke-opacity=".55" stroke-width="{2.4*s:.1f}"/>')
    # 木马（两只 X 形支架）
    lr = 46 * s
    ly = base - 163 * s + 26 * s + 46 * s - 8 * s   # 锯条落在圆木顶上，齿咬进去一点
    for hx in (cx - 220 * s, cx + 220 * s):
        out.append(f'<path d="M{hx-60*s:.0f} {base:.0f} L{hx+40*s:.0f} {ly+10*s:.0f} M{hx+60*s:.0f} {base:.0f} L{hx-40*s:.0f} {ly+10*s:.0f}" stroke="{DIM}" stroke-width="{8*s:.1f}" stroke-linecap="round"/>')
    # 圆木：左右两段，中间是锯口
    x0, x1 = cx - 360 * s, cx + 360 * s
    gap = 7 * s
    out.append(f'<rect x="{x0:.0f}" y="{ly-lr:.0f}" width="{cx-gap-x0:.0f}" height="{2*lr:.0f}" fill="{NAVY_LOW}" stroke="{GOLD2}" stroke-width="{3*s:.1f}"/>')
    out.append(f'<rect x="{cx+gap:.0f}" y="{ly-lr:.0f}" width="{x1-cx-gap:.0f}" height="{2*lr:.0f}" fill="{NAVY_LOW}" stroke="{GOLD2}" stroke-width="{3*s:.1f}"/>')
    # 端面年轮
    for ex in (x0, x1):
        out.append(f'<ellipse cx="{ex:.0f}" cy="{ly:.0f}" rx="{18*s:.0f}" ry="{lr:.0f}" fill="{NAVY_MID}" stroke="{GOLD2}" stroke-width="{3*s:.1f}"/>')
        for r in (0.66, 0.36):
            out.append(f'<ellipse cx="{ex:.0f}" cy="{ly:.0f}" rx="{18*s*r:.0f}" ry="{lr*r:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".6" stroke-width="{1.6*s:.1f}"/>')
    # 木纹
    for k, yy in enumerate((-0.45, -0.1, 0.3)):
        out.append(f'<path d="M{x0+30*s:.0f} {ly+yy*lr:.0f} Q{(x0+cx)/2:.0f} {ly+yy*lr+(10 if k%2 else -10)*s:.0f} {cx-24*s:.0f} {ly+yy*lr:.0f} M{cx+24*s:.0f} {ly+yy*lr:.0f} Q{(x1+cx)/2:.0f} {ly+yy*lr+(-10 if k%2 else 10)*s:.0f} {x1-30*s:.0f} {ly+yy*lr:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".28" stroke-width="{1.6*s:.1f}"/>')
    # 锯口里一道亮缝
    out.append(f'<rect x="{cx-gap:.0f}" y="{ly-lr:.0f}" width="{2*gap:.0f}" height="{2*lr:.0f}" fill="{GOLD2}" fill-opacity=".85"/>')
    # 两个人
    pl, hl = person(cx - 565 * s, base, s, 1, 34, GOLD2)
    pr, hr = person(cx + 565 * s, base, s, -1, 18, CYAN)
    # 锯条：两头锯柄握在两人手里，锯条压在锯口上
    blade_h = 26 * s
    sy = hl[1] - blade_h * 0.5
    bl, br = (hl[0], sy), (hr[0], sy)
    n = 44
    blade = f'M{bl[0]:.0f} {sy:.0f} L{br[0]:.0f} {sy:.0f} L{br[0]:.0f} {sy+blade_h:.0f} '
    pts = []
    for i in range(n, 0, -1):
        xa = bl[0] + (br[0] - bl[0]) * i / n; xm = bl[0] + (br[0] - bl[0]) * (i - .5) / n
        pts.append('L%.0f %.0f L%.0f %.0f' % (xa, sy + blade_h, xm, sy + blade_h + 10 * s))
    blade += ' '.join(pts) + f' L{bl[0]:.0f} {sy+blade_h:.0f} Z'
    out.append(f'<path d="{blade}" fill="{CREAM}" fill-opacity=".92" stroke="{DIM}" stroke-width="{1.2*s:.1f}"/>')
    # 两头锯柄（竖把），被手握住
    for bx in (bl[0], br[0]):
        out.append(f'<line x1="{bx:.0f}" y1="{sy-34*s:.0f}" x2="{bx:.0f}" y2="{sy+blade_h+30*s:.0f}" stroke="{GOLD}" stroke-width="{15*s:.1f}" stroke-linecap="round"/>')
    out.append(pl); out.append(pr)
    # 推拉箭头
    for x_, d_ in ((cx - 450 * s, -1), (cx + 450 * s, 1)):
        y_ = sy - 70 * s
        out.append(f'<path d="M{x_-60*s:.0f} {y_:.0f} L{x_+60*s:.0f} {y_:.0f} M{x_+d_*60*s:.0f} {y_:.0f} L{x_+d_*42*s:.0f} {y_-12*s:.0f} M{x_+d_*60*s:.0f} {y_:.0f} L{x_+d_*42*s:.0f} {y_+12*s:.0f} M{x_-d_*60*s:.0f} {y_:.0f} L{x_-d_*42*s:.0f} {y_-12*s:.0f} M{x_-d_*60*s:.0f} {y_:.0f} L{x_-d_*42*s:.0f} {y_+12*s:.0f}" stroke="{DIM}" stroke-opacity=".7" stroke-width="{2.6*s:.1f}" fill="none" stroke-linecap="round"/>')
    # 锯末：从锯口两边落下
    import random
    rnd = random.Random(571)
    for k in range(46):
        x = cx + rnd.uniform(-34, 34) * s
        y = ly + lr + rnd.uniform(6, 60) * s
        r = rnd.uniform(2, 5.2) * s
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="{GOLD2}" fill-opacity="{rnd.uniform(.35, .9):.2f}"/>')
    # 挂号单：圆木上方、锯口正上，一张小票
    tw, th = 150 * s, 196 * s
    tx, ty = cx - tw / 2, sy - 290 * s
    out.append(f'<rect x="{tx:.0f}" y="{ty:.0f}" width="{tw:.0f}" height="{th:.0f}" rx="{5*s:.0f}" fill="{CREAM}" transform="rotate(-4 {cx:.0f} {ty+th/2:.0f})"/>')
    g = f'<g transform="rotate(-4 {cx:.0f} {ty+th/2:.0f})">'
    g += f'<text x="{cx:.0f}" y="{ty+40*s:.0f}" font-size="{25*s:.0f}" text-anchor="middle" font-family="Noto Serif CJK SC" font-weight="700" fill="{NAVY_TOP}" letter-spacing="{4*s:.0f}">挂号单</text>'
    g += f'<line x1="{tx+16*s:.0f}" y1="{ty+56*s:.0f}" x2="{tx+tw-16*s:.0f}" y2="{ty+56*s:.0f}" stroke="{NAVY_MID}" stroke-width="{1.6*s:.1f}" stroke-dasharray="{5*s:.0f} {4*s:.0f}"/>'
    for i, (lab, w_) in enumerate((('科室', .55), ('医生', .5), ('病人', .6), ('病名', .4))):
        yy = ty + (86 + i * 30) * s
        g += f'<text x="{tx+18*s:.0f}" y="{yy:.0f}" font-size="{15*s:.0f}" font-family="Noto Sans CJK SC" fill="{NAVY_MID}">{lab}</text>'
        g += f'<line x1="{tx+64*s:.0f}" y1="{yy-4*s:.0f}" x2="{tx+64*s+(tw-82*s)*w_:.0f}" y2="{yy-4*s:.0f}" stroke="{GOLD}" stroke-width="{4*s:.1f}" stroke-linecap="round"/>'
    g += '</g>'
    out.append(g)
    # 挂号单到锯口：一条虚线
    out.append(f'<line x1="{cx:.0f}" y1="{ty+th+8*s:.0f}" x2="{cx:.0f}" y2="{sy-14*s:.0f}" stroke="{GOLD2}" stroke-opacity=".7" stroke-width="{2*s:.1f}" stroke-dasharray="{6*s:.0f} {6*s:.0f}"/>')
    scene = ''.join(out)
    k = 1.3
    out = [f'<g transform="translate({cx:.0f} {base:.0f}) scale({k}) translate({-cx:.0f} {-base:.0f})">{scene}</g>']
    # 注脚三行
    ty2 = base + 120 * s
    for xx, anc, big, small, col in ((W * 0.08, 'start', '医', '医生位：锯的这一头', GOLD2), (W * 0.5, 'middle', '锯口', '病在这里，不在哪一头', CREAM), (W * 0.92, 'end', '患', '病人位：锯的那一头', CYAN)):
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 571 号</div>
<div class="t"><div class="pre">普通人都能明白的</div><div class="big big2">医患复合体<br>状态发生学</div>
<div class="sub">病不在病人身上，也不在医生眼里</div><div class="rule"></div></div>
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
<div class="c"><div class="lab">核 心 命 题</div>
<div class="q">医学研究的不是人的病，<br>而是医患复合体的状态发生；<br>诊断不是发现的终点，<br>而是状态发生的开端。</div><div class="by">——王德生口述</div><div class="rule"></div>
<div class="bl"><p>人们总说：病人生病了，医生看病。本书说：在诊室里真正生病的，是「医生—病人」这个互动复合体。病不在病人身上，也不在医生眼里，在两个人一推一拉的那道锯口上。</p>
<p>挂号那一刻，病人位、医生位、科室和病名才一起露面；诊断不是真相到手的终点，是复合体第一次有了形状。之后是一锅粥、悬着、定型三种状态的转换：定型靠一锅粥和悬着活着，最好的痊愈是复合体散开、不再被需要。</p>
<p>量子力学把观察者请到了台前，观察者仍是发现学；本书连观察者一起拆掉。复合体生病不等于没人负责：追到那只手，也追到锯口卡住的那一维。</p>
<p>母题与四条承重命题由王德生口述；正文由 AI（Claude）执笔，经统稿与三审；书中人物均为虚构；只谈理解，不给诊疗用药建议；没有独立学术评审。</p></div>
<div class="gold">病不在哪一头，在锯口上。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 571 号 · 前言、导读、导论、四编十六章、结语 · 约 {WAN} 万字<br>ISBN 979-8-90690-590-1 · 定价 US$20.00</div>
</div></div></body></html>"""


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
