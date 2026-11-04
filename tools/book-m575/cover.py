#!/usr/bin/env python3
"""第 575 号《好心为什么会作恶？》（王德生 著）封面与封底（工具链承自第 547 号，藏青底、金青奶白三色，220 系列版式）：
主图：夜里的书桌，台灯下一只小手捏着笔，一只大手从上方伸来，两手之间一圈金环。全部纯色，不用渐变。
用法：python3 cover.py --fonts /usr/share/fonts/opentype/noto --out <dir>
"""
import argparse
import math
import os
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0C1A34', '#1B3158', '#16294A'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#7FA7C9', '#EFE8D6', '#A9B6C8'
ISBN = '979-8-90690-594-9'
WAN = os.environ.get('WAN', '19')

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
    """主图（第 575 号）：夜里的书桌。台灯下摊着作业本，一只小手捏着笔；一只大手从右上方伸来，
    两只手之间留一道空，空上一圈金环——施者走通的那一刻，受者的路断在这里。全部纯色，不用渐变。"""
    import random
    rnd = random.Random(575)
    s = W / 1700
    out = []
    yd = H * 0.655                       # 桌面前沿
    yt = H * 0.50                        # 桌面后沿
    yb = H * 0.755                       # 桌板下沿
    # 灯光：两层半透明的扇形
    lx, ly = W * 0.205, H * 0.445         # 灯罩口
    for wid, op in ((1.0, .10), (.64, .12)):
        out.append(f'<path d="M{lx - 62*s:.0f} {ly:.0f} L{lx + 62*s:.0f} {ly:.0f} L{lx + 470*wid*s:.0f} {yd:.0f} L{lx - 240*wid*s:.0f} {yd:.0f} Z" fill="{GOLD2}" fill-opacity="{op}"/>')
    # 桌面与桌板
    out.append(f'<path d="M{W*0.06:.0f} {yt:.0f} L{W*0.94:.0f} {yt:.0f} L{W:.0f} {yd:.0f} L0 {yd:.0f} Z" fill="{CREAM}" fill-opacity=".13" stroke="{GOLD}" stroke-opacity=".5" stroke-width="{2.4*s:.1f}" stroke-linejoin="round"/>')
    out.append(f'<rect x="0" y="{yd:.0f}" width="{W}" height="{yb - yd:.0f}" fill="{NAVY_TOP}" fill-opacity=".7"/>')
    out.append(f'<line x1="0" y1="{yd:.0f}" x2="{W}" y2="{yd:.0f}" stroke="{GOLD}" stroke-opacity=".7" stroke-width="{2.6*s:.1f}"/>')
    # 台灯：底座、灯杆、灯罩
    bx = W * 0.135
    out.append(f'<ellipse cx="{bx:.0f}" cy="{yt + 62*s:.0f}" rx="{92*s:.0f}" ry="{20*s:.0f}" fill="{NAVY_TOP}" stroke="{GOLD}" stroke-width="{2.4*s:.1f}"/>')
    out.append(f'<path d="M{bx:.0f} {yt + 58*s:.0f} L{bx - 22*s:.0f} {ly - 150*s:.0f} L{lx - 18*s:.0f} {ly - 112*s:.0f}" fill="none" stroke="{GOLD}" stroke-width="{7*s:.1f}" stroke-linejoin="round" stroke-linecap="round"/>')
    out.append(f'<circle cx="{bx - 22*s:.0f}" cy="{ly - 150*s:.0f}" r="{9*s:.0f}" fill="{GOLD2}"/>')
    out.append(f'<path d="M{lx - 28*s:.0f} {ly - 112*s:.0f} L{lx + 28*s:.0f} {ly - 112*s:.0f} L{lx + 72*s:.0f} {ly:.0f} L{lx - 72*s:.0f} {ly:.0f} Z" fill="{GOLD}"/>')
    out.append(f'<ellipse cx="{lx:.0f}" cy="{ly + 2*s:.0f}" rx="{30*s:.0f}" ry="{8*s:.0f}" fill="#F7F1E3"/>')
    # 作业本：摊开的两页＋格线
    cx, cy = W * 0.46, (yt + yd) / 2 + 8 * s
    pw, ph = 330 * s, 118 * s
    out.append(f'<path d="M{cx:.0f} {cy - ph*.62:.0f} L{cx - pw:.0f} {cy - ph*.44:.0f} L{cx - pw*1.12:.0f} {cy + ph*.82:.0f} L{cx:.0f} {cy + ph:.0f} Z" fill="#F7F1E3"/>')
    out.append(f'<path d="M{cx:.0f} {cy - ph*.62:.0f} L{cx + pw:.0f} {cy - ph*.44:.0f} L{cx + pw*1.12:.0f} {cy + ph*.82:.0f} L{cx:.0f} {cy + ph:.0f} Z" fill="{CREAM}"/>')
    for k in range(1, 6):
        f = k / 6
        yl = cy - ph * .62 + (ph * 1.62) * f
        for sg in (-1, 1):
            xe = cx + sg * (pw + pw * .12 * f)
            ye = cy - ph * .44 + ph * 1.26 * f
            out.append(f'<line x1="{cx + sg*10*s:.0f}" y1="{yl:.0f}" x2="{xe:.0f}" y2="{ye:.0f}" stroke="{CYAN}" stroke-opacity=".55" stroke-width="{1.5*s:.1f}"/>')
    # 没写完的字：本子左页几行短划，到一半停住
    for k, (a0, a1) in enumerate(((.18, .84), (.18, .70), (.18, .46))):
        f = (k + 1.5) / 6
        yl = cy - ph * .62 + (ph * 1.62) * f - 8 * s
        xa, xb = cx - pw * (1 - a0 + .1), cx - pw * (1 - a1 + .1)
        out.append(f'<line x1="{xa:.0f}" y1="{yl + 8*s:.0f}" x2="{xb:.0f}" y2="{yl + 2*s:.0f}" stroke="{NAVY_MID}" stroke-opacity=".7" stroke-width="{3.4*s:.1f}" stroke-linecap="round" stroke-dasharray="{13*s:.0f} {7*s:.0f}"/>')
    def curve(p0, p1, p2, p3, n=26):
        return [bez(p0, p1, p2, p3, i / (n - 1)) for i in range(n)]

    def finger(x0, y0, x1, y1, wd, col):
        return f'<line x1="{x0:.0f}" y1="{y0:.0f}" x2="{x1:.0f}" y2="{y1:.0f}" stroke="{col}" stroke-width="{wd:.1f}" stroke-linecap="round"/>'
    # 小手：从下方伸进来，三根手指扣住笔杆，笔尖点在本子上
    px, py = cx + 96 * s, cy + 34 * s      # 笔尖
    qx, qy = px + 124 * s, py - 152 * s    # 笔尾
    hx, hy = px + 62 * s, py - 44 * s      # 手心
    arm = curve((hx + 150 * s, yb + 30 * s), (hx + 118 * s, yb - 70 * s), (hx + 92 * s, hy + 92 * s), (hx + 18 * s, hy + 18 * s))
    out.append(f'<path d="{tapered(arm, 66 * s, 44 * s, 1.0)}" fill="{GOLD2}"/>')
    out.append(f'<circle cx="{hx + 16*s:.0f}" cy="{hy + 16*s:.0f}" r="{34*s:.0f}" fill="{GOLD2}"/>')
    out.append(f'<rect x="0" y="{yb:.0f}" width="{W}" height="{H*0.80 - yb:.0f}" fill="{NAVY_MID}"/>')
    out.append(finger(px, py, qx, qy, 10 * s, NAVY_TOP))
    out.append(finger(px + 86 * s, py - 105 * s, qx, qy, 10 * s, CYAN))
    for k, (dx, dy) in enumerate(((-26, 4), (-13, 19), (2, 32))):
        out.append(finger(hx + 26 * s + dx * .2 * s, hy + 14 * s + dy * .2 * s, hx + dx * s, hy + dy * s - 28 * s, 16 * s, GOLD2))
    # 大手：从右上方伸来，手指张开，停在笔的上方
    ox, oy = qx + 214 * s, qy - 150 * s    # 手掌中心
    barm = curve((W + 60 * s, H * 0.30), (W * 0.93, H * 0.31), (ox + 150 * s, oy - 170 * s), (ox + 34 * s, oy - 30 * s))
    out.append(f'<path d="{tapered(barm, 118 * s, 74 * s, 1.0)}" fill="{CREAM}"/>')
    cuff = barm[20]; cuff0 = barm[18]
    out.append(finger(cuff0[0] - 34 * s, cuff0[1] - 46 * s, cuff0[0] + 44 * s, cuff0[1] + 34 * s, 13 * s, GOLD))
    out.append(f'<circle cx="{ox:.0f}" cy="{oy:.0f}" r="{58*s:.0f}" fill="{CREAM}"/>')
    for dx, dy, ln, wd in ((-.98, .20, 112, 25), (-.86, .50, 124, 26), (-.60, .80, 118, 25), (-.26, .96, 96, 23), (-.92, -.38, 84, 27)):
        out.append(finger(ox + dx * 42 * s, oy + dy * 42 * s, ox + dx * (42 + ln) * s, oy + dy * (42 + ln) * s, wd * s, CREAM))
    # 两手之间一圈金环
    gx, gy = (qx + ox - 100 * s) / 2, (qy + oy + 80 * s) / 2
    out.append(f'<circle cx="{gx:.0f}" cy="{gy:.0f}" r="{36*s:.0f}" fill="none" stroke="{GOLD2}" stroke-width="{3.6*s:.1f}"/>')
    out.append(f'<circle cx="{gx:.0f}" cy="{gy:.0f}" r="{58*s:.0f}" fill="none" stroke="{GOLD2}" stroke-opacity=".32" stroke-width="{2.2*s:.1f}"/>')
    out.append(f'<circle cx="{gx:.0f}" cy="{gy:.0f}" r="{6*s:.0f}" fill="{GOLD2}"/>')
    # 标注：三样意义
    ty = yb + 70 * s
    x0, x1 = W * 0.10, W * 0.90
    for xx, anc, big, small, col in ((x0, 'start', '创造', '他长出了什么', CYAN), (W * 0.5, 'middle', '自由', '他自己的路还通不通', GOLD2), (x1, 'end', '幸福', '这一下他自己走通了吗', CREAM)):
        out.append(f'<text x="{xx:.0f}" y="{ty:.0f}" font-size="{36*s:.0f}" text-anchor="{anc}" font-family="Noto Serif CJK SC" font-weight="700" fill="{col}" letter-spacing="{6*s:.0f}">{big}</text>')
        out.append(f'<text x="{xx:.0f}" y="{ty + 40*s:.0f}" font-size="{20*s:.0f}" text-anchor="{anc}" font-family="Noto Sans CJK SC" fill="{DIM}" letter-spacing="{2*s:.0f}">{small}</text>')
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 575 号</div>
<div class="t"><div class="pre">解构黄金定律</div><div class="big">好心为什么<br>会作恶？</div>
<div class="sub">两条黄金定律怎样从善变成恶</div><div class="rule"></div></div>
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
<div class="c"><div class="lab">全 书 判 词</div>
<div class="q" style="font-size:{14.2*s:.1f}pt">这两句话量的是欲，善恶却要对着意义判；<br>欲一旦顶替了意义，<br>施者走通的那一刻，<br>就是受者被截断的那一刻。</div><div class="rule"></div>
<div class="bl"><p>孩子写作业写累了，抬头说“妈，我好累”。妈妈想：我累的时候盼有人接过去，那就接过来。这句话有两千多年的来历，叫“己所不欲，勿施于人”，叫“你们愿意人怎样待你们，你们也要怎样待人”。接，它说对；不接，它也说对。</p>
<p>本书把这把尺子翻过来看刻度。两句话问的是你愿不愿意，读到的是欲；善恶却要对着意义判，书里取创造、自由、幸福。同一句话、同一个好心人，走到意义还没清楚的地方，欲就坐到了意义的位置上，好心替人提前结了账。</p>
<p>全书前言、导读、六编五十二章、结语、附录七件：先看两句话怎样被抬成“普遍真理”，再放回孔子和耶稣说话的当场，立起判断善恶的骨架，划出不能判的时候（电车难题就在其中），然后到作业、病房、车间、算法里看它一处处翻转，最后给两句话一个新位置，给读者动手前的五句问话。</p>
<p>这是一部研究性专著：核心判断由王德生口述提出，正文由 AI（Claude）协作撰写并经三轮审校；书中的人物与场景是构想，推翻条件尚待检验，没有独立学术评审。</p></div>
<div class="gold">下一次说“我是为你好”之前，先问这句话在回答他的什么。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 575 号 · 六编五十二章 · 约 {WAN} 万字<br>ISBN 979-8-90690-594-9 · 定价 US$25.00</div>
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
