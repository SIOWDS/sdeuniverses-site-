#!/usr/bin/env python3
"""第 300 号《圣经中女子智慧的缝隙和补缺》封面与封底（由第 230 号 cover.py 改来；主图换成九格被面与一根金针）（照第 340 号／220 系列版式：藏青渐变底、细点阵、金色光晕与刻度环）；
主图是一只白底青花杯，杯下三个人影——孩子、做瓷的师傅、喝了五十年茶的老人——各有一道不同颜色的视线，
分别落在杯把、釉面上一点缩釉、杯口的茶渍上。同一只杯子，三种看法。

用法：python3 cover.py --fonts /usr/share/fonts --out /home/claude/bookwork/build
产物：cover-print.pdf / back-print.pdf（170×240）、cover-reader.pdf / back-reader.pdf（190×250）、
      cover.jpg / backcover.jpg（1004×1418，站上用）
"""
import argparse
import math
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0B1830', '#1B3158', '#142746'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#58BDCA', '#EFE8D6', '#9FB0C8'
ISBN = '979-8-90690-620-5'
CORAL = '#E8997A'
BLUE, BLUE2 = '#2C5AA6', '#8FB2E0'

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


def person(kind, x, y, col, uid):
    """简笔人影（站在地上，脚在 (x, y)）。返回 (svg, 眼睛位置)。"""
    c = CREAM
    if kind == 'child':
        body = (f'<path d="M{x-30} {y-128} Q{x-38} {y-70} {x-26} {y-48} L{x+26} {y-48} Q{x+38} {y-70} {x+30} {y-128} Z" fill="{c}"/>'
                f'<rect x="{x-17}" y="{y-50}" width="11" height="46" rx="4" fill="{c}"/><rect x="{x+6}" y="{y-50}" width="11" height="46" rx="4" fill="{c}"/>'
                f'<line x1="{x+26}" y1="{y-118}" x2="{x+58}" y2="{y-168}" stroke="{c}" stroke-width="12" stroke-linecap="round"/>'
                f'<circle cx="{x}" cy="{y-158}" r="27" fill="{c}"/>'
                f'<path d="M{x-27} {y-162} Q{x} {y-196} {x+27} {y-162} Q{x} {y-176} {x-27} {y-162} Z" fill="{col}"/>')
        eye = (x + 8, y - 160)
    elif kind == 'old':
        body = (f'<path d="M{x-34} {y-232} Q{x-58} {y-150} {x-38} {y-52} L{x+34} {y-52} Q{x+52} {y-150} {x+22} {y-222} Z" fill="{c}"/>'
                f'<rect x="{x-24}" y="{y-56}" width="15" height="52" rx="5" fill="{c}"/><rect x="{x+8}" y="{y-56}" width="15" height="52" rx="5" fill="{c}"/>'
                f'<line x1="{x+30}" y1="{y-170}" x2="{x+78}" y2="{y-150}" stroke="{c}" stroke-width="13" stroke-linecap="round"/>'
                f'<line x1="{x+78}" y1="{y-156}" x2="{x+82}" y2="{y+2}" stroke="{GOLD}" stroke-width="9" stroke-linecap="round"/>'
                f'<circle cx="{x-12}" cy="{y-262}" r="31" fill="{c}"/>'
                f'<path d="M{x-40} {y-268} Q{x-12} {y-306} {x+16} {y-268} Q{x-12} {y-280} {x-40} {y-268} Z" fill="{DIM}"/>')
        eye = (x - 2, y - 262)
    else:
        body = (f'<path d="M{x-40} {y-240} Q{x-52} {y-150} {x-40} {y-52} L{x+40} {y-52} Q{x+52} {y-150} {x+40} {y-240} Z" fill="{c}"/>'
                f'<path d="M{x-30} {y-200} L{x+30} {y-200} L{x+36} {y-60} L{x-36} {y-60} Z" fill="{col}" fill-opacity=".55"/>'
                f'<rect x="{x-28}" y="{y-56}" width="17" height="52" rx="5" fill="{c}"/><rect x="{x+11}" y="{y-56}" width="17" height="52" rx="5" fill="{c}"/>'
                f'<line x1="{x+36}" y1="{y-210}" x2="{x+78}" y2="{y-262}" stroke="{c}" stroke-width="14" stroke-linecap="round"/>'
                f'<circle cx="{x+88}" cy="{y-276}" r="19" fill="none" stroke="{GOLD2}" stroke-width="5"/>'
                f'<circle cx="{x}" cy="{y-272}" r="30" fill="{c}"/>'
                f'<path d="M{x-31} {y-282} L{x+31} {y-282} L{x+27} {y-306} Q{x} {y-318} {x-27} {y-306} Z" fill="{DIM}"/>')
        eye = (x + 12, y - 270)
    return f'<g stroke="{col}" stroke-width="3.2" stroke-opacity=".9">{body}</g>', eye


def cup(cx, uid):
    """白底青花杯：左边是杯把，杯口内壁右侧有一圈茶渍，正面有一点缩釉。"""
    top, bot, hw = 1030, 1420, 300
    body = (f'M{cx-hw} {top} C{cx-hw-10} {top+170} {cx-250} {bot-40} {cx-170} {bot} '
            f'L{cx+170} {bot} C{cx+250} {bot-40} {cx+hw+10} {top+170} {cx+hw} {top} Z')
    petals = ''.join(
        f'<ellipse cx="{cx}" cy="{1235-44}" rx="19" ry="44" fill="{BLUE if k % 2 == 0 else BLUE2}" fill-opacity=".92" transform="rotate({k*45} {cx} 1235)"/>'
        for k in range(8))
    leaves = ''
    for sgn in (-1, 1):
        leaves += (f'<path d="M{cx+sgn*92} 1236 C{cx+sgn*150} 1180 {cx+sgn*210} 1190 {cx+sgn*222} 1245 C{cx+sgn*228} 1285 {cx+sgn*186} 1296 {cx+sgn*172} 1268" '
                   f'fill="none" stroke="{BLUE}" stroke-width="8" stroke-linecap="round"/>'
                   f'<path d="M{cx+sgn*98} 1262 C{cx+sgn*140} 1300 {cx+sgn*190} 1332 {cx+sgn*214} 1344" fill="none" stroke="{BLUE}" stroke-width="7" stroke-linecap="round"/>')
    return f"""
<defs>
 <linearGradient id="cupg{uid}" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#CFC8B3"/><stop offset=".22" stop-color="#FBF8EF"/><stop offset=".6" stop-color="#F2EDDF"/><stop offset="1" stop-color="#C6BEA8"/></linearGradient>
 <linearGradient id="inn{uid}" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#B7C3D4"/><stop offset="1" stop-color="#E9EEF5"/></linearGradient>
 <clipPath id="cl{uid}"><path d="{body}"/></clipPath>
</defs>
<ellipse cx="{cx}" cy="{bot+58}" rx="400" ry="34" fill="#000" fill-opacity=".38"/>
<ellipse cx="{cx}" cy="{bot+34}" rx="372" ry="38" fill="#D9D2BE"/><ellipse cx="{cx}" cy="{bot+26}" rx="372" ry="38" fill="#F4EFE1"/>
<ellipse cx="{cx}" cy="{bot+26}" rx="316" ry="26" fill="none" stroke="{BLUE}" stroke-width="5" stroke-opacity=".8"/>
<path d="M{cx-300} {top+70} C{cx-460} {top+30} {cx-470} {top+290} {cx-246} {top+320}" fill="none" stroke="#C9BF9E" stroke-width="46" stroke-linecap="round"/>
<path d="M{cx-300} {top+70} C{cx-460} {top+30} {cx-470} {top+290} {cx-246} {top+320}" fill="none" stroke="#F8F4E8" stroke-width="36" stroke-linecap="round"/>
<path d="M{cx-300} {top+70} C{cx-460} {top+30} {cx-470} {top+290} {cx-246} {top+320}" fill="none" stroke="{BLUE}" stroke-width="5" stroke-linecap="round" stroke-opacity=".75"/>
<path d="{body}" fill="url(#cupg{uid})"/>
<g clip-path="url(#cl{uid})">
 <path d="M{cx-hw} {top+48} Q{cx} {top+120} {cx+hw} {top+48}" fill="none" stroke="{BLUE}" stroke-width="9"/>
 <path d="M{cx-hw} {top+72} Q{cx} {top+144} {cx+hw} {top+72}" fill="none" stroke="{BLUE}" stroke-width="4"/>
 <path d="M{cx-200} {bot-44} Q{cx} {bot+8} {cx+200} {bot-44}" fill="none" stroke="{BLUE}" stroke-width="9"/>
 <circle cx="{cx}" cy="1235" r="86" fill="#FBF8EF" fill-opacity=".9"/>
 {petals}{leaves}
 <circle cx="{cx}" cy="1235" r="21" fill="#F6D98F" stroke="{BLUE}" stroke-width="5"/>
</g>
<ellipse cx="{cx}" cy="{top}" rx="{hw}" ry="48" fill="#FBF8EF" stroke="#C9BF9E" stroke-width="4"/>
<ellipse cx="{cx}" cy="{top+4}" rx="{hw-30}" ry="36" fill="url(#inn{uid})"/>
<path d="M{cx+110} {top+24} Q{cx+190} {top+22} {cx+240} {top-6}" fill="none" stroke="#8A5A2E" stroke-width="9" stroke-linecap="round" stroke-opacity=".8"/>
<ellipse cx="{cx}" cy="{top}" rx="{hw}" ry="48" fill="none" stroke="{BLUE}" stroke-width="5" stroke-opacity=".8"/>
<circle cx="{cx+100}" cy="1332" r="7" fill="#7A6A52"/><circle cx="{cx+98}" cy="1330" r="3" fill="#FBF8EF"/>"""


def art(W, H, uid):
    """主图：一床三横三竖的九格被面。八格各是一块旧布；正中一格是深蓝工服布，它和左边的蓝印花之间衬着一指宽的白布条（接口）；
    右下一格空着，只有金色虚线（被拿走的那一格）。一根金针带着线，从白布条缝向空格。判词：他补的不是长处的反面，是接口。"""
    s = min(W / 1700, H / 2400)
    xo, yo = (W - 1700 * s) / 2, (H - 2400 * s) / 2
    cx, cy, a = 850, 1340, 250          # 中心与单格边长
    out = [f'<g transform="translate({xo:.1f} {yo:.1f}) scale({s:.4f})">']
    out.append(rings(cx, cy, 560).replace('{uid}', uid))
    out.append(f'<g transform="rotate(-6 {cx} {cy})">')
    x0, y0 = cx - 1.5 * a, cy - 1.5 * a
    out.append(f'<rect x="{x0+16}" y="{y0+22}" width="{3*a}" height="{3*a}" rx="10" fill="#000" fill-opacity=".35"/>')
    cols = {(0, 0): '#E9DFC6', (1, 0): CORAL, (2, 0): '#D8CDB0', (0, 1): BLUE, (1, 1): '#1E3558',
            (2, 1): '#EFE8D6', (0, 2): '#C9A857', (1, 2): '#9FC7CF'}
    for (c, r), col in cols.items():
        x, y = x0 + c * a, y0 + r * a
        out.append(f'<rect x="{x+5}" y="{y+5}" width="{a-10}" height="{a-10}" rx="6" fill="{col}"/>')
        g = []
        if (c, r) == (0, 1):       # 蓝印花：白色小花
            for u in range(3):
                for v in range(3):
                    px, py = x + 50 + u * 75, y + 50 + v * 75
                    g.append(''.join(f'<ellipse cx="{px}" cy="{py-13}" rx="6" ry="13" fill="#F4EFE1" transform="rotate({k*72} {px} {py})"/>' for k in range(5)))
                    g.append(f'<circle cx="{px}" cy="{py}" r="5" fill="{GOLD2}"/>')
        elif (c, r) == (1, 0):     # 红棉袄：小圆点
            g += [f'<circle cx="{x+40+u*57}" cy="{y+40+v*57}" r="9" fill="#F7E3D6" fill-opacity=".85"/>' for u in range(4) for v in range(4)]
        elif (c, r) == (0, 0):     # 条纹
            g += [f'<line x1="{x+12}" y1="{y+30+k*38}" x2="{x+a-12}" y2="{y+30+k*38}" stroke="#B8A47A" stroke-width="7"/>' for k in range(6)]
        elif (c, r) == (2, 0):     # 格子
            g += [f'<line x1="{x+30+k*48}" y1="{y+12}" x2="{x+30+k*48}" y2="{y+a-12}" stroke="#8E7F5C" stroke-width="5"/>' for k in range(5)]
            g += [f'<line x1="{x+12}" y1="{y+30+k*48}" x2="{x+a-12}" y2="{y+30+k*48}" stroke="#8E7F5C" stroke-width="5"/>' for k in range(5)]
        elif (c, r) == (1, 1):     # 工服：一只口袋、两粒扣
            g.append(f'<rect x="{x+70}" y="{y+70}" width="110" height="120" rx="8" fill="none" stroke="#6F8FBF" stroke-width="5" stroke-dasharray="10 8"/>')
            g += [f'<circle cx="{x+200}" cy="{y+60+k*70}" r="9" fill="#6F8FBF"/>' for k in range(2)]
        elif (c, r) == (2, 1):     # 素布：斜纹
            g += [f'<line x1="{x+12+k*40}" y1="{y+a-12}" x2="{x+12+k*40+60}" y2="{y+12}" stroke="#CFC4A6" stroke-width="5"/>' for k in range(5)]
        elif (c, r) == (0, 2):     # 金布：菱形
            g += [f'<path d="M{x+a/2} {y+40+k*30} L{x+a-40-k*30} {y+a/2} L{x+a/2} {y+a-40-k*30} L{x+40+k*30} {y+a/2} Z" fill="none" stroke="#7C6325" stroke-width="5"/>' for k in range(3)]
        elif (c, r) == (1, 2):     # 浅青：水纹
            for k in range(5):
                yy = y + 45 + k * 40
                g.append(f'<path d="M{x+14} {yy} Q{x+72} {yy-22} {x+125} {yy} T{x+a-14} {yy}" fill="none" stroke="#3E8C98" stroke-width="5"/>')
        out.append(f'<g>{"".join(g)}</g>')
        out.append(f'<rect x="{x+13}" y="{y+13}" width="{a-26}" height="{a-26}" rx="4" fill="none" stroke="#FFF" stroke-opacity=".55" stroke-width="2.4" stroke-dasharray="9 7"/>')
    # 空着的一格（右下）
    ex, ey = x0 + 2 * a, y0 + 2 * a
    out.append(f'<rect x="{ex+8}" y="{ey+8}" width="{a-16}" height="{a-16}" rx="6" fill="{NAVY_TOP}" fill-opacity=".55" stroke="{GOLD2}" stroke-width="5" stroke-dasharray="16 12"/>')
    # 接口：蓝印花与工服之间一指宽的白布条
    sx = x0 + a
    out.append(f'<rect x="{sx-13}" y="{y0+a+2}" width="26" height="{a-4}" fill="#FFFDF6"/>')
    out += [f'<line x1="{sx-13}" y1="{y0+a+18+k*22}" x2="{sx+13}" y2="{y0+a+18+k*22}" stroke="{GOLD}" stroke-width="3.4"/>' for k in range(11)]
    out.append(f'<rect x="{x0}" y="{y0}" width="{3*a}" height="{3*a}" rx="10" fill="none" stroke="{GOLD}" stroke-width="7"/>')
    out.append('</g>')
    # 金线与针：从白布条出来，绕一个弯，缝向空格
    pts = [bez((cx - 150, cy + 60), (cx - 260, cy + 520), (cx + 120, cy + 640), (cx + 300, cy + 430), k / 60) for k in range(61)]
    d = 'M' + ' L'.join('%.1f %.1f' % q for q in pts)
    out.append(f'<path d="{d}" fill="none" stroke="{GOLD2}" stroke-width="5" stroke-linecap="round" stroke-dasharray="2 13"/>')
    out.append(f'<path d="{d}" fill="none" stroke="{GOLD2}" stroke-width="1.8" stroke-opacity=".6"/>')
    nx, ny = cx + 300, cy + 430
    out.append(f'<g transform="rotate(-38 {nx} {ny})"><path d="M{nx-8} {ny} L{nx+250} {ny-5} L{nx+290} {ny} L{nx+250} {ny+5} Z" fill="url(#handle{uid})" stroke="{GOLD}" stroke-width="2"/>'
               f'<ellipse cx="{nx+16}" cy="{ny}" rx="13" ry="4" fill="{NAVY_TOP}"/></g>')
    out.append('</g>')
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
.big{{font:700 {31*s:.1f}pt/1.28 'Noto Serif CJK SC';letter-spacing:.1em;color:#F7F1E3;margin:{2*s:.1f}mm 0 {3*s:.1f}mm {-1*s:.1f}mm}}
.sub{{font:400 {10.6*s:.1f}pt/1.75 'Noto Serif CJK SC';color:{GOLD2};letter-spacing:.04em}}
.rule{{width:{16*s:.1f}mm;border-top:.9pt solid {GOLD};margin-top:{5*s:.1f}mm}}
.b{{position:absolute;left:{17*s:.1f}mm;bottom:{17*s:.1f}mm}}
.au{{font:400 {12.5*s:.1f}pt 'Noto Serif CJK SC';color:{CREAM};letter-spacing:.28em}}
.ph{{font:700 {8.4*s:.1f}pt 'Noto Sans CJK SC';color:{GOLD2};letter-spacing:.3em;margin-top:{6*s:.1f}mm}}
.pe{{font:400 {6.6*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.08em;margin-top:{.8*s:.1f}mm}}
.no{{position:absolute;right:{15*s:.1f}mm;top:{16*s:.1f}mm;font:400 {6.6*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.2em;text-align:right}}
</style></head><body><div class="pg">{svg}
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 300 号</div>
<div class="t"><div class="pre">差在入场那一步</div><div class="big">圣经中女子智慧的<br>缝隙和补缺</div>
<div class="sub">用耶稣的全丰满智慧照亮她们</div><div class="rule"></div></div>
<div class="b"><div class="au">李佳城　著</div><div class="pe" style="letter-spacing:.2em;margin-top:1.4mm">王德生　指导</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div>
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
<div class="c"><div class="lab">一 句 话</div>
<div class="q">圣经写她们，<br>差在入场那一步：<br>她多是被带进来的，<br>少是说着话进来的。</div><div class="by">——本书判词第一句</div><div class="rule"></div>
<div class="bl"><p>这本书写了两遍。头一遍，拿福音书里那个没有缝的人当尺子，一位一位量圣经里的三十多位女子：她长在哪里，缺在哪里，谁补了她。写完交人审读，才看清量出来的一定有缺，那是尺子的性质。第二遍，添了一本编码手册、同段男子的对照组和预先登记的六条预测，只凭经文去数。六条里输了三条，撤回一条。数出来的是另外三件事：差在入场那一步；在他面前，她们有一半一句话也没有；开口的，他驳回的同驳回男子的量不出差别。数很小，只照登，不说证明。</p></div>
<div class="gold">亏缺不是罪。先看她手里那一样有多重。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 300 号 · 七卷四十三章 · 约 24 万字<br>定价 US$23.00</div>
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
