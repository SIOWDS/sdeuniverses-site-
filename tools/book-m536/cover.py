#!/usr/bin/env python3
"""第 536 号《AI时代普通人的知识发生机会》（王德生 著）封面与封底（工具链承自第 532 号，藏青底、金青奶白三色，220 系列版式）：
主图是一句话（一行字格）穿过一个场（大圆，场心垫一块九宫），在说歪的那一格，扶正的路向下散开——
一条被场收成金色实线，其余是青色虚线。下标「句 × 场」。全部纯色，不用渐变。
用法：python3 cover.py --fonts /home/claude/fonts --out <dir>
"""
import argparse
import math
import os
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0C1A34', '#1B3158', '#16294A'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#7FA7C9', '#EFE8D6', '#A9B6C8'
ISBN = '979-8-90690-536-9'
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


def art(W, H, uid):
    """主图（第 536 号）：一块田的剖面。地面上三丛草依次是「长、割、再长」；地下从左边板结的密格，
    过渡到右边松散的土粒；一条金色回写弧从右端的地下转回左端——这一轮留下的变化，参与下一轮的条件。全部纯色。"""
    import random
    rnd = random.Random(536)
    s = W / 1700
    gy = H * 0.585                       # 地面线
    x0, x1 = W * 0.10, W * 0.92
    out = []
    # 地下：左边板结（密而齐的小方格），右边松软（疏而散的圆粒），中间渐变成散
    for k in range(900):
        t = rnd.random()
        x = x0 + t * (x1 - x0)
        y = gy + 30 * s + rnd.random() * (H * 0.165)
        if rnd.random() < 0.82 - 0.62 * t:
            gx = round((x - x0) / (26 * s)) * 26 * s + x0
            gyy = round((y - gy) / (26 * s)) * 26 * s + gy
            out.append(f'<rect x="{gx:.0f}" y="{gyy:.0f}" width="{17*s:.0f}" height="{17*s:.0f}" fill="{CREAM}" fill-opacity="{.10 + .10*(1-t):.2f}"/>')
        elif rnd.random() < 0.18 + 0.5 * t:
            out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rnd.uniform(3, 7)*s:.1f}" fill="{GOLD2 if rnd.random() < .25 else CREAM}" fill-opacity="{rnd.uniform(.18, .45):.2f}"/>')
    # 地面线
    out.append(f'<line x1="{x0 - 40*s:.0f}" y1="{gy:.0f}" x2="{x1 + 40*s:.0f}" y2="{gy:.0f}" stroke="{GOLD}" stroke-opacity=".75" stroke-width="{3*s:.1f}"/>')

    def clump(cx, hmax, cut=False, n=11, seed=0):
        r2 = random.Random(seed)
        g = []
        for i in range(n):
            dx = (i - (n - 1) / 2) * 13 * s
            h = (hmax * r2.uniform(.6, 1.0)) if not cut else 34 * s
            lean = r2.uniform(-.35, .35) + dx / (90 * s) * .25
            ex, ey = cx + dx + lean * h, gy - h
            c1x, c1y = cx + dx + lean * h * .25, gy - h * .55
            col = CYAN if not cut else CREAM
            g.append(f'<path d="M {cx+dx:.0f} {gy:.0f} Q {c1x:.0f} {c1y:.0f} {ex:.0f} {ey:.0f}" fill="none" stroke="{col}" stroke-opacity="{.85 if not cut else .7}" stroke-width="{(4.2 if not cut else 3.6)*s:.1f}" stroke-linecap="round"/>')
            if cut:
                g.append(f'<line x1="{ex - 6*s:.0f}" y1="{ey:.0f}" x2="{ex + 6*s:.0f}" y2="{ey:.0f}" stroke="{GOLD2}" stroke-width="{2.4*s:.1f}"/>')
        # 根：往下几条细线，再长那丛的根更深更散
        for i in range(7):
            dx = (i - 3) * 16 * s
            depth = r2.uniform(.45, 1.0) * (150 if not cut else 120) * s * (1.6 if seed == 3 else 1)
            g.append(f'<path d="M {cx+dx*.3:.0f} {gy:.0f} Q {cx+dx:.0f} {gy+depth*.5:.0f} {cx+dx*1.4:.0f} {gy+depth:.0f}" fill="none" stroke="{GOLD2}" stroke-opacity=".45" stroke-width="{1.8*s:.1f}"/>')
        return ''.join(g)
    xs = [W * 0.25, W * 0.51, W * 0.77]
    out.append(clump(xs[0], 250 * s, seed=1))
    out.append(clump(xs[1], 0, cut=True, seed=2))
    out.append(clump(xs[2], 290 * s, n=14, seed=3))
    # 镰刀一道：割的那一丛上方一条金色弧
    out.append(f'<path d="M {xs[1]-90*s:.0f} {gy-70*s:.0f} Q {xs[1]:.0f} {gy-120*s:.0f} {xs[1]+90*s:.0f} {gy-70*s:.0f}" fill="none" stroke="{GOLD}" stroke-width="{3.4*s:.1f}" stroke-dasharray="14 10" stroke-linecap="round"/>')
    # 回写弧：从右端地下转回左端地下
    ay = gy + H * 0.15
    out.append(f'<path d="M {xs[2]:.0f} {gy + 70*s:.0f} C {xs[2] + 120*s:.0f} {ay + 60*s:.0f}, {xs[0] - 120*s:.0f} {ay + 60*s:.0f}, {xs[0]:.0f} {gy + 70*s:.0f}" fill="none" stroke="{GOLD}" stroke-width="{4.4*s:.1f}" stroke-linecap="round"/>')
    ax, ay2 = xs[0], gy + 70 * s
    out.append(f'<path d="M {ax:.0f} {ay2:.0f} l {-16*s:.0f} {30*s:.0f} M {ax:.0f} {ay2:.0f} l {20*s:.0f} {26*s:.0f}" stroke="{GOLD}" stroke-width="{4.4*s:.1f}" stroke-linecap="round"/>')
    # 地上标字：长 · 割 · 再长
    for x, lab in zip(xs, ['长', '割', '再长']):
        out.append(f'<text x="{x:.0f}" y="{gy - 330*s:.0f}" font-size="{44*s:.0f}" text-anchor="middle" font-family="Noto Serif CJK SC" font-weight="700" fill="{CREAM}" fill-opacity=".92">{lab}</text>')
    out.append(f'<text x="{(xs[0]+xs[2])/2:.0f}" y="{ay + 150*s:.0f}" font-size="{25*s:.0f}" text-anchor="middle" font-family="Noto Sans CJK SC" fill="{GOLD2}" fill-opacity=".9" letter-spacing="{4*s:.0f}">板结　→　松软　·　回写</text>')
    for _ in range(50):
        out.append(f'<circle cx="{rnd.uniform(0, W):.0f}" cy="{rnd.uniform(H*0.30, H*0.355):.0f}" r="{rnd.uniform(.8, 2.2)*s:.1f}" fill="{CREAM}" fill-opacity="{rnd.uniform(.12, .40):.2f}"/>')
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 536 号</div>
<div class="t"><div class="pre">知识发生 · 农业与日常</div><div class="big big2" style="font-size:{33*s:.1f}pt">AI时代<br>普通人的<br>知识发生机会</div>
<div class="sub">从农业与日常生活经验，<br>到教育、健康、事业的知识母本与同一性谱系</div><div class="rule"></div></div>
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
<div class="c"><div class="lab">田 间 原 型</div>
<div class="q">草长了一年，割过几次，<br>又长起来，<br>原本板结的土变得松软了。</div><div class="by">——王德生的田间经验</div><div class="rule"></div>
<div class="bl"><p>这一轮发生留下的变化，参与塑造下一轮发生的条件——本书把它叫作回写。一个农民可能不这样叫它，一个厨师也不会在端出一盘菜时先报告差异序列；可他们的实践里有顺序、选择、限度、失败与再试，有值得提取的关系。</p>
<p>本书讨论普通人的真实经验怎样与 SDE 知识发生智能体相遇，经过拆解、比较、跨域类通与独立检验，成为可以修订的候选知识母本，并在教育、健康、事业里长出共享程度不同的分支。书中写明每一处类通能搬什么、不能搬什么，什么情况下就错了。</p>
<p>除作者的田间原型外，书中人物与场景都是构想；书里不作诊断，不替孩子代笔，不保证收入。</p></div>
<div class="gold">草割了，还会再长。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 536 号 · 十六编九十六章 · 约 {WAN} 万字<br>ISBN 979-8-90690-536-9 · 定价 US$20.00</div>
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
