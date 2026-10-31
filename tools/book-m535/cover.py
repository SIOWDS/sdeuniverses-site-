#!/usr/bin/env python3
"""第 535 号《SDE思想入门》（王德生　阳涌　著）封面与封底（工具链承自第 532 号，220 系列版式；配色换成墨绿底、金·青绿·奶白三色）：
主图是三大感觉——摸、听、看——三个圆两两相交缠在一起，交汇处一点金。下标「摸 · 听 · 看」。全部纯色，不用渐变。
用法：python3 cover.py --fonts /home/claude/fonts --out <dir>
"""
import argparse
import math
import os
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0E2621', '#1B4038', '#15342D'   # 墨绿三带（变量名沿用）
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E6CB85', '#86C2B0', '#F0EADA', '#A8BDB4'
import sys as _sys
_sys.path.insert(0, str(Path(__file__).parent))
import meta as M  # noqa: E402
ISBN = M.ISBN
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
    """主图（第 535 号）：三大感觉——摸、听、看——三个圆两两相交、缠在一起（三维不可分）；
    左圆里一把钥匙（触），右圆里一串由疏到密的声波（听），下圆里一道一层层亮起的地平线（看）；
    三圆交汇处一点金。下标「摸 · 听 · 看」。全部纯色。"""
    import random
    rnd = random.Random(535)
    s = W / 1700
    cx, cy, R = W * 0.56, H * 0.565, 250 * s
    cs = [(cx - 0.62 * R, cy - 0.36 * R, CREAM), (cx + 0.62 * R, cy - 0.36 * R, CYAN), (cx, cy + 0.72 * R, GOLD2)]
    out = []
    # 外圈：一道淡金环与刻度
    rr = R * 2.05
    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{rr:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".30" stroke-width="{1.4*s:.1f}"/>')
    ticks = []
    for k in range(60):
        t = k * math.pi * 2 / 60
        r1 = rr * (1.03 if k % 5 else 1.055)
        ticks.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (cx + rr * math.cos(t), cy + rr * math.sin(t), cx + r1 * math.cos(t), cy + r1 * math.sin(t)))
    out.append(f'<g stroke="{GOLD}" stroke-opacity=".40" stroke-width="{1.5*s:.1f}">{"".join(ticks)}</g>')
    # 三个圆：两两相交
    for x, y, col in cs:
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{R:.0f}" fill="{col}" fill-opacity=".05" stroke="{col}" stroke-opacity=".75" stroke-width="{2.6*s:.1f}"/>')
    # 触：左圆里一把钥匙
    kx, ky = cs[0][0] - 0.30 * R, cs[0][1] - 0.12 * R
    out.append(f'<circle cx="{kx:.0f}" cy="{ky:.0f}" r="{38*s:.0f}" fill="none" stroke="{CREAM}" stroke-width="{7*s:.1f}"/>')
    out.append(f'<line x1="{kx + 38*s:.0f}" y1="{ky:.0f}" x2="{kx + 190*s:.0f}" y2="{ky:.0f}" stroke="{CREAM}" stroke-width="{9*s:.1f}" stroke-linecap="round"/>')
    for dx, h in ((120, 34), (150, 22), (178, 30)):
        out.append(f'<line x1="{kx + dx*s:.0f}" y1="{ky:.0f}" x2="{kx + dx*s:.0f}" y2="{ky + h*s:.0f}" stroke="{CREAM}" stroke-width="{8*s:.1f}" stroke-linecap="round"/>')
    # 听：右圆里由疏到密、由低到高的声波
    hx, hy = cs[1][0] - 0.55 * R, cs[1][1] - 0.10 * R
    d, x = 'M %.0f %.0f' % (hx, hy), hx
    for i in range(14):
        wv = (34 - i * 1.7) * s
        amp = (10 + i * 2.6) * s
        d += ' q %.1f %.1f %.1f 0' % (wv / 2, -amp if i % 2 == 0 else amp, wv)
        x += wv
    out.append(f'<path d="{d}" fill="none" stroke="{CYAN}" stroke-width="{4.2*s:.1f}" stroke-linecap="round"/>')
    # 看：下圆里一层层亮起的地平线
    vx, vy = cs[2][0], cs[2][1] + 0.05 * R
    for i, op in enumerate((.25, .45, .65, .9)):
        w = (150 + i * 40) * s
        out.append(f'<line x1="{vx - w:.0f}" y1="{vy - i*18*s:.0f}" x2="{vx + w:.0f}" y2="{vy - i*18*s:.0f}" stroke="{GOLD2}" stroke-opacity="{op}" stroke-width="{3.2*s:.1f}" stroke-linecap="round"/>')
    out.append(f'<path d="M {vx - 70*s:.0f} {vy - 72*s:.0f} A {70*s:.0f} {70*s:.0f} 0 0 1 {vx + 70*s:.0f} {vy - 72*s:.0f}" fill="none" stroke="{GOLD2}" stroke-width="{4*s:.1f}"/>')
    # 三圆交汇处一点金
    ox, oy = cx, cy - 0.02 * R
    out.append(f'<circle cx="{ox:.0f}" cy="{oy:.0f}" r="{14*s:.0f}" fill="{GOLD}"/>')
    out.append(f'<circle cx="{ox:.0f}" cy="{oy:.0f}" r="{30*s:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".5" stroke-width="{1.6*s:.1f}"/>')
    # 底部标：摸 · 听 · 看
    base = cy + R * 2.0
    out.append(f'<line x1="{cx - 380*s:.0f}" y1="{base:.0f}" x2="{cx + 380*s:.0f}" y2="{base:.0f}" stroke="{GOLD}" stroke-opacity=".45" stroke-width="{1.4*s:.1f}"/>')
    for (x, lab, cap, col) in [(cx - 250 * s, '摸', '一只手', CREAM), (cx, '听', '一只耳', CYAN), (cx + 250 * s, '看', '一双眼', GOLD2)]:
        out.append(f'<text x="{x:.0f}" y="{base + 70*s:.0f}" font-size="{50*s:.0f}" text-anchor="middle" font-family="Noto Serif CJK SC" font-weight="700" fill="{col}" fill-opacity=".95">{lab}</text>')
        out.append(f'<text x="{x:.0f}" y="{base + 114*s:.0f}" font-size="{24*s:.0f}" text-anchor="middle" font-family="Noto Sans CJK SC" fill="{GOLD2}" fill-opacity=".85" letter-spacing="{4*s:.0f}">{cap}</text>')
    for _ in range(60):
        out.append(f'<circle cx="{rnd.uniform(0, W):.0f}" cy="{rnd.uniform(H*0.30, H*0.355):.0f}" r="{rnd.uniform(.8, 2.2)*s:.1f}" fill="{CREAM}" fill-opacity="{rnd.uniform(.12, .45):.2f}"/>')
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 {M.NO} 号</div>
<div class="t"><div class="pre">四篇 · 十四讲</div><div class="big" style="font-size:{46*s:.1f}pt">SDE<br>思想入门</div>
<div class="sub">{M.SUBTITLE}</div><div class="rule"></div></div>
<div class="b"><div class="au">{M.BYLINE}</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div>
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
<div class="c"><div class="lab">一 句 话</div>
<div class="q">世界不是摆在那里等你去拿的，<br>它在发生；你在其中，<br>也正在发生；<br>凡是正在发生的，都可以改。</div><div class="by">——本书前言</div><div class="rule"></div>
<div class="bl"><p>一个孩子说"我就是不爱写作文"，一个店主说"这条街就是做不起生意"，一个妈妈说"我脾气就是急"。三句话都把一件正在发生的事，说成了一样本来就在那里、不会动的东西。</p>
<p>这本书交给你一双能看见"正在发生"的眼睛：从摸钥匙、听水壶、看天亮三件小事认出显露、差异序列、纠缠，再拿到三件工具——一件事是什么、从哪里下手、凭什么会动——落到带孩子、做事业、和 AI 打交道、过好一个家里去。</p>
<p>每一讲都写明自己在什么情况下就错了；查出来是反的，请相信你查到的，而不是这本书。</p></div>
<div class="gold">它是怎样一层层显出来的？</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 {M.NO} 号 · 四篇十四讲 · 约 {WAN} 万字<br>ISBN {M.ISBN} · 定价 {M.PRICE}</div>
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
