#!/usr/bin/env python3
"""第 568 号《先难受，后痛快》（王德生、苏亚男 著）封面与封底（工具链承自第 567 号；靛青底，金、青绿点缀，220 系列版式）：
主图：一根绳子，左边打着一个紧结，往右渐渐松开、化成一道舒展的波（先结后解）。全部纯色，不用渐变。
封面不写「指导」一类字样（「王德生指导」只写在前言里）。
用法：python3 cover.py --fonts /usr/share/fonts/opentype/noto --out <dir>
"""
import argparse
import math
import os
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#121E36', '#1A2B48', '#16253F'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#6FB9B0', '#EFE8D6', '#A3B8BC'
CLAY = '#D98E73'
import sys
sys.path.insert(0, str(Path(__file__).parent))
import meta as M  # noqa: E402
ISBN = M.ISBN
WAN = os.environ.get('WAN') or ('%.0f' % (M.body_han(Path(__file__).parent) / 10000) if (Path(__file__).parent / 'han.json').exists() else '20')   # 第 568 号：默认取 han.json

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
    """主图（第 568 号《先难受，后痛快》）：一根绳子，左边打着一个紧结，往右渐渐松开，化成一道舒展的波（先结后解）。
    绳子从左边进来，在左侧绞成一个又紧又密的结（张力）；出了结，绳身还带着几道小折（转换）；
    再往右，折痕一路放开，成了一道越走越宽、越走越缓的波，波后面又荡开两三道淡淡的余波（释放）。
    绳身的捻纹左密右疏；颜色由金到青绿，一段一段换色，全部纯色，不用渐变。"""
    s = W / 1700
    out = []
    y0 = H * 0.655
    kx = W * 0.20                          # 结心
    R = 42 * s
    rw = 19 * s                            # 绳粗

    def knot_pts(n=260):
        # 三叶结的投影（结心收紧、略扁），首尾留在左下与右侧，接上绳子
        pts = []
        for i in range(n + 1):
            t = math.pi * 2 * i / n + 0.35
            x = math.sin(t) + 2 * math.sin(2 * t)
            y = math.cos(t) - 2 * math.cos(2 * t)
            pts.append((kx + R * x * 1.05, y0 + R * y * 0.86))
        return pts
    K = knot_pts()
    # 引入段：从左边缘进来，接到结的起点
    sx, sy = K[0]
    lead = [(-30 * s + (sx + 30 * s) * k / 30, y0 + 70 * s * (1 - k / 30) ** 2 + (sy - y0) * (k / 30)) for k in range(31)]
    # 引出段：从结的终点往右，先带几道小折，再化成越来越舒展的波
    ex, ey = K[-1]
    tail, x, ph = [], ex, 0.0
    x_end = W + 40 * s
    while x <= x_end:
        u = (x - ex) / (x_end - ex)               # 0 → 1
        lam = (30 + 1000 * u ** 1.7) * s          # 波长：由密到疏
        amp = (5 + 62 * min(1, u * 1.3) ** 0.9) * s * (1 - 0.25 * max(0, u - 0.8) / 0.2)
        if u < 0.12:
            amp *= 0.55 + 0.45 * math.sin(u / 0.12 * math.pi / 2)
        yy = y0 + (ey - y0) * max(0, 1 - u * 9) + amp * math.sin(ph)
        tail.append((x, yy))
        dx = 4 * s
        ph += 2 * math.pi * dx / lam
        x += dx
    # 余波：释放之后荡开的几道淡波
    for j, (dy, op) in enumerate([(70, .30), (128, .18), (178, .10)]):
        d = []
        for (x, yy) in tail[len(tail) // 3:]:
            u = (x - ex) / (x_end - ex)
            d.append('%.1f %.1f' % (x, y0 + dy * s + (yy - y0) * (0.55 - 0.12 * j) * min(1, (u - 0.33) * 3)))
        out.append(f'<path d="M{" L".join(d)}" fill="none" stroke="{CYAN}" stroke-opacity="{op}" stroke-width="{(2.6 - .6*j)*s:.1f}" stroke-linecap="round"/>')
    # 结的影子
    out.append(f'<ellipse cx="{kx:.0f}" cy="{y0 + R*3.4:.0f}" rx="{R*3.6:.0f}" ry="{R*.55:.0f}" fill="#0B1424" fill-opacity=".45"/>')

    def stroke(pts, col, w, outline=True, skip=3):
        d = 'M' + ' L'.join('%.1f %.1f' % p for p in pts)
        r = ''
        if outline and len(pts) > skip + 1:
            d2 = 'M' + ' L'.join('%.1f %.1f' % p for p in pts[skip:])
            r += f'<path d="{d2}" fill="none" stroke="{NAVY_MID}" stroke-width="{w + 9*s:.1f}" stroke-linecap="round" stroke-linejoin="round"/>'
        r += f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{w:.1f}" stroke-linecap="round" stroke-linejoin="round"/>'
        return r

    def twist(pts, every, col, w, op):
        # 捻纹：沿绳身斜画的短线，左密右疏
        r, acc = [], 0.0
        for i in range(1, len(pts) - 1):
            a, b = pts[i - 1], pts[i + 1]
            acc += math.hypot(pts[i][0] - a[0], pts[i][1] - a[1])
            if acc < every(pts[i][0]):
                continue
            acc = 0
            dx, dy = b[0] - a[0], b[1] - a[1]
            ln = math.hypot(dx, dy) or 1
            nx, ny = -dy / ln, dx / ln
            tx, ty = dx / ln, dy / ln
            h = w * 0.42
            x0, y0_ = pts[i][0] - nx * h - tx * h * .6, pts[i][1] - ny * h - ty * h * .6
            x1, y1 = pts[i][0] + nx * h + tx * h * .6, pts[i][1] + ny * h + ty * h * .6
            r.append(f'<line x1="{x0:.1f}" y1="{y0_:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{col}" stroke-opacity="{op}" stroke-width="{1.7*s:.1f}" stroke-linecap="round"/>')
        return ''.join(r)
    dense = lambda x: 9 * s
    # 引入段
    out.append(stroke(lead, GOLD, rw, outline=False))
    # 结：分六段画，后画的压住先画的，留出一道底色缝，看得出绳子的上下穿插
    seg = len(K) // 6
    for i in range(6):
        part = K[i * seg: (i + 1) * seg + 2 if i < 5 else len(K)]
        out.append(stroke(part, GOLD if i % 2 == 0 else '#BE9C4C', rw))
        out.append(twist(part, dense, '#8C6E2E', rw, .75))
    out.append(twist(lead, dense, '#8C6E2E', rw, .75))
    # 引出段：由金到青绿，一段一段换色（纯色）
    cols = [GOLD, GOLD2, '#B9C99A', '#93C2A9', CYAN, CYAN]
    n = len(tail)
    for i, c in enumerate(cols):
        a_, b_ = n * i // len(cols), n * (i + 1) // len(cols) + 1
        part = tail[max(0, a_ - 1):b_]
        w = rw * (1 - 0.42 * i / len(cols))
        out.append(stroke(part, c, w, outline=(i == 0), skip=6))
    out.append(twist(tail, lambda x: (9 + 60 * max(0, (x - ex) / (W - ex)) ** 1.3) * s, '#5E6F55', rw * .8, .45))
    # 结心的一点高光
    out.append(f'<circle cx="{kx:.0f}" cy="{y0 - R*0.2:.0f}" r="{5*s:.1f}" fill="{CREAM}" fill-opacity=".85"/>')
    # 波尾放出的几点光
    for (fx, fy, rr, op) in ((0.90, -120, 6, .8), (0.94, -165, 4.5, .6), (0.86, -190, 3.5, .45), (0.97, -95, 3, .5)):
        out.append(f'<circle cx="{W*fx:.0f}" cy="{y0 + fy*s:.0f}" r="{rr*s:.1f}" fill="{GOLD2}" fill-opacity="{op}"/>')
    # ── 三个名字 ──
    lab = lambda x, y, t, anchor='start', col=DIM: (f'<text x="{x:.0f}" y="{y:.0f}" font-size="{27*s:.0f}" text-anchor="{anchor}" '
                                                  f'font-family="Noto Sans CJK SC" fill="{col}" letter-spacing="{4*s:.0f}">{t}</text>')
    out.append(lab(kx, y0 - R * 3.2, '一个结 · 张力', anchor='middle', col=GOLD2))
    out.append(lab(W * 0.47, y0 + 150 * s, '转换', anchor='middle', col='#B9C99A'))
    out.append(lab(W * 0.94, H * 0.775, '解开 · 释放', anchor='end', col=CYAN))
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
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{Wmm}mm" height="{Hmm}mm">{background(W, H, "f", split=0.455)}{art(W, H, "f")}</svg>'
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{fontface(F)}
@page{{size:{Wmm}mm {Hmm}mm;margin:0}} body{{margin:0}}
.pg{{position:relative;width:{Wmm}mm;height:{Hmm}mm;overflow:hidden}}
.pg svg{{position:absolute;left:0;top:0}}
.t{{position:absolute;left:{17*s:.1f}mm;top:{22*s:.1f}mm;color:{CREAM}}}
.pre{{font:400 {11.5*s:.1f}pt 'Noto Serif CJK SC';letter-spacing:.32em;color:{CREAM};opacity:.92}}
.big{{font:700 {45*s:.1f}pt/1.2 'Noto Serif CJK SC';letter-spacing:.1em;color:#F7F1E3;margin:{2*s:.1f}mm 0 {3*s:.1f}mm {-1*s:.1f}mm}}
.big2{{font-size:{36*s:.1f}pt;line-height:1.32;letter-spacing:.08em}}
.sub{{font:400 {10.6*s:.1f}pt/1.75 'Noto Serif CJK SC';color:{GOLD2};letter-spacing:.04em}}
.rule{{width:{16*s:.1f}mm;border-top:.9pt solid {GOLD};margin-top:{5*s:.1f}mm}}
.b{{position:absolute;left:{17*s:.1f}mm;bottom:{17*s:.1f}mm}}
.au{{font:400 {12.5*s:.1f}pt 'Noto Serif CJK SC';color:{CREAM};letter-spacing:.28em}}
.ph{{font:700 {8.4*s:.1f}pt 'Noto Sans CJK SC';color:{GOLD2};letter-spacing:.3em;margin-top:{6*s:.1f}mm}}
.pe{{font:400 {6.6*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.08em;margin-top:{.8*s:.1f}mm}}
.no{{position:absolute;right:{15*s:.1f}mm;top:{16*s:.1f}mm;font:400 {6.6*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.2em;text-align:right}}
</style></head><body><div class="pg">{svg}
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 {M.NO} 号</div>
<div class="t"><div class="pre">SDE 发生学 · 普通人都能明白</div><div class="big">{M.TITLE.replace("，", "，<br>")}</div>
<div class="sub">{M.SUBTITLE}</div><div class="rule"></div><div class="pe" style="font-size:{8*s:.1f}pt;color:{CREAM};letter-spacing:.3em;margin-top:{4*s:.1f}mm">{M.COVER_SMALL}</div></div>
<div class="b"><div class="au">{M.AUTHOR}　著</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div>
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
<div class="c"><div class="lab">核 心 判 断</div>
<div class="q">心理健康不是没有张力，<br>是敢一次次走进去。</div><div class="by">——本书母题</div><div class="rule"></div>
<div class="bl"><p>跑到第三公里，那一堵墙来了：胸口发闷，腿像灌了水泥，「我不行」又快又干脆地冒出来。同一副身体，同一堵墙，有的日子就此停下，有的日子在墙后面接上了第二口气。分开它们的，不是墙有多高。</p>
<p>今天通行的说法，把幸福拍成一张快照，把难受记成亏欠；阿德勒把入口叫作「自卑」，把穿过叫作「超越」；心流把人留在挑战与能力刚好相当的窄道上。本书说：幸福是张力、转换、释放这一过程运行的体验，它的高度，取决于转换之前忍住并蓄起了多少张力。</p>
<p>病的根是不敢进入；进去了出不来，是卡在了某一拍。真正的心理健康，是敢一次次进入混沌、进入纠缠、进入张力，每次只比能扛的多一点，身后有托底，进去之后有出口。AI 可以做出口发生器，不能做释放售卖机。</p></div>
<div class="gold">先难受，后痛快。</div></div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 {M.NO} 号 · 前言、导论、五编十八章、结语、附录 · 约 {WAN} 万字<br>ISBN {M.ISBN} · 定价 {M.PRICE}</div>
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
