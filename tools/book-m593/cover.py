#!/usr/bin/env python3
"""《抓不住的人》封面与封底（工具链承自第 586 号，220 系列版式；全部纯色，不用渐变——翻页器矢量模式画不出 PDF 渐变）：
主图：几圈合不拢的弧线像一只握不紧的手势，三条缠在一起、由细到粗的线从缺口滑出去（泥鳅的抽象），下面是水纹。不画任何具体角色。
书号、ISBN、定价、题名都取自 meta.py；字数取自 han.json。封面、封底不写指导者。
用法：python3 cover.py --fonts /usr/share/fonts/opentype/noto --out <dir>
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa: E402

INK, DEEP, LOW = '#0B2230', '#123241', '#0E2936'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E8CE88', '#6FB3BE', '#EFE8D6', '#A9BAC4'
ISBN = M.ISBN
WAN = '%.0f' % (M.body_han(HERE) / 10000)

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


def ribbon(pts, width):
    """沿折线画一条宽度随位置变化的带子，返回多边形 path。width(t) 给出 t∈[0,1] 处的宽度。"""
    left, right = [], []
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        a = pts[max(i - 1, 0)]; b = pts[min(i + 1, n - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln, dx / ln
        w = width(i / (n - 1))
        left.append((x + nx * w / 2, y + ny * w / 2)); right.append((x - nx * w / 2, y - ny * w / 2))
    return 'M' + ' L'.join('%.1f %.1f' % p for p in left + right[::-1]) + ' Z'


def background(W, H, split=0.34):
    dots = []
    step = 44
    for yy in range(22, H, step):
        for xx in range(22 + (yy // step % 2) * 22, W, step):
            dots.append('<circle cx="%d" cy="%d" r="1.6"/>' % (xx, yy))
    return (f'<rect width="{W}" height="{H}" fill="{INK}"/>'
            f'<rect y="{H*split:.0f}" width="{W}" height="{H*(1-split):.0f}" fill="{DEEP}"/>'
            f'<rect y="{H*0.82:.0f}" width="{W}" height="{H*0.18:.0f}" fill="{LOW}"/>'
            f'<g fill="{DIM}" fill-opacity=".08">{"".join(dots)}</g>')


def water(W, H, s, y0s):
    o = []
    for k, (yy, op, amp, seg) in enumerate(y0s):
        y0 = H * yy; d = 'M0 %.0f' % y0
        for i in range(seg):
            d += ' Q%.0f %.0f %.0f %.0f' % (W * (i + .5) / seg, y0 + (amp if i % 2 else -amp) * s, W * (i + 1) / seg, y0)
        o.append('<path d="%s" fill="none" stroke="%s" stroke-opacity="%.2f" stroke-width="%.1f"/>' % (d, CYAN, op, 2.4 * s))
    return ''.join(o)


def art(W, H):
    s = W / 1700
    o = []
    # 水纹：横贯下半幅
    o.append(water(W, H, s, [(.60, .10, 16, 7), (.665, .14, 20, 6), (.73, .18, 24, 7), (.795, .22, 18, 6), (.855, .16, 26, 5), (.905, .12, 18, 6), (.95, .08, 14, 7)]))
    # 合不拢的弧：开口朝右上，线从缺口滑出
    cx, cy = W * .40, H * .635
    gap0, gap1 = math.radians(-62), math.radians(6)   # 缺口的角度范围
    for k, r in enumerate([250, 340, 430, 520, 610]):
        r *= s
        a0, a1 = gap1 + .03 * k, gap0 + 2 * math.pi - .03 * k
        x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
        x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
        o.append(f'<path d="M{x0:.0f} {y0:.0f} A{r:.0f} {r:.0f} 0 1 1 {x1:.0f} {y1:.0f}" fill="none" stroke="{CREAM}" stroke-opacity="{.42 - k*.06:.2f}" stroke-width="{(7 - k)*s:.1f}" stroke-linecap="round"/>')
    # 三条缠在一起的序列：沿同一条脊线绞着走，从圈内滑向缺口之外，线头在外
    p0, p1, p2, p3 = (W * .20, H * .735), (W * .42, H * .80), (W * .50, H * .50), (W * .93, H * .395)
    strands = [(CYAN, .72, 0.0, 15, 60 * s), (CREAM, .85, 2.1, 17, 56 * s), (GOLD2, 1, 4.2, 40, 74 * s)]
    N = 160
    for col, op, phase, wmax, amp in strands:
        pts = []
        for i in range(N + 1):
            t = i / N
            x, y = bez(p0, p1, p2, p3, t)
            xa, ya = bez(p0, p1, p2, p3, max(t - .01, 0)); xb, yb = bez(p0, p1, p2, p3, min(t + .01, 1))
            dx, dy = xb - xa, yb - ya; ln = math.hypot(dx, dy) or 1
            nx, ny = -dy / ln, dx / ln
            off = amp * math.sin(2 * math.pi * 2.6 * t + phase) * (1 - t) ** .75   # 越往外绞得越紧，到线头合成一条
            pts.append((x + nx * off, y + ny * off))
        wm = wmax * s
        d = ribbon(pts, lambda t: 2.5 * s + wm * (t ** 1.5) * (1 - max(0, t - .93) / .07 * .75))
        o.append(f'<path d="{d}" fill="{col}" fill-opacity="{op}"/>')
    # 滑出去之后的几点水花
    for (fx, fy, r, op) in [(.955, .372, 7, .9), (.925, .345, 4.5, .7), (.965, .335, 3, .55), (.885, .360, 3.2, .5)]:
        o.append(f'<circle cx="{W*fx:.0f}" cy="{H*fy:.0f}" r="{r*s:.1f}" fill="{GOLD2}" fill-opacity="{op}"/>')
    return ''.join(o)


def barcode(x, y, s):
    d, bits = ean13_bits(ISBN)
    mw = 3.3 * s
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


def front(Wmm, Hmm):
    W, H = Wmm * 10, Hmm * 10
    s = Wmm / 170
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{Wmm}mm" height="{Hmm}mm">{background(W, H)}{art(W, H)}</svg>'
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page{{size:{Wmm}mm {Hmm}mm;margin:0}} body{{margin:0}}
.pg{{position:relative;width:{Wmm}mm;height:{Hmm}mm;overflow:hidden}}
.pg svg{{position:absolute;left:0;top:0}}
.t{{position:absolute;left:{16*s:.1f}mm;top:{27*s:.1f}mm;color:{CREAM}}}
.big{{font:700 {67*s:.1f}pt/1.12 'Noto Serif CJK SC';letter-spacing:.035em;color:#F7F1E3;margin:0 0 {4.5*s:.1f}mm {-1*s:.1f}mm;white-space:nowrap}}
.sub{{font:400 {15*s:.1f}pt/1.6 'Noto Serif CJK SC';color:{GOLD2};letter-spacing:.14em}}
.rule{{width:{16*s:.1f}mm;border-top:.9pt solid {GOLD};margin-top:{5*s:.1f}mm}}
.b{{position:absolute;left:{16*s:.1f}mm;bottom:{14*s:.1f}mm}}
.au{{font:400 {13.5*s:.1f}pt 'Noto Serif CJK SC';color:{CREAM};letter-spacing:.28em}}
.ph{{font:700 {8.4*s:.1f}pt 'Noto Sans CJK SC';color:{GOLD2};letter-spacing:.3em;margin-top:{5*s:.1f}mm}}
.pe{{font:400 {6.6*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.08em;margin-top:{.8*s:.1f}mm}}
.no{{position:absolute;right:{15*s:.1f}mm;top:{13*s:.1f}mm;font:400 {6.6*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.2em;text-align:right}}
</style></head><body><div class="pg">{svg}
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 {M.NO} 号</div>
<div class="t"><div class="big">{M.TITLE}</div>
<div class="sub">{M.SUBTITLE}</div><div class="rule"></div></div>
<div class="b"><div class="au">{M.AUTHOR}　著</div><div class="ph">{M.PUBLISHER}</div><div class="pe">{M.PUBLISHER_EN}</div></div>
</div></body></html>"""


def back(Wmm, Hmm):
    W, H = Wmm * 10, Hmm * 10
    s = Wmm / 170
    ex, ey, er = W * 0.84, H * 0.085, 70 * s
    # 右上小徽：一圈合不拢的弧，一条线从缺口出去
    a0, a1 = math.radians(6), math.radians(-62) + 2 * math.pi
    emb = (f'<path d="M{ex+er*math.cos(a0):.0f} {ey+er*math.sin(a0):.0f} A{er:.0f} {er:.0f} 0 1 1 {ex+er*math.cos(a1):.0f} {ey+er*math.sin(a1):.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".7" stroke-width="{3*s:.1f}" stroke-linecap="round"/>'
           f'<path d="M{ex-30*s:.0f} {ey+26*s:.0f} C{ex:.0f} {ey+36*s:.0f} {ex+10*s:.0f} {ey-16*s:.0f} {ex+er*1.25:.0f} {ey-er*.75:.0f}" fill="none" stroke="{CREAM}" stroke-width="{4*s:.1f}" stroke-linecap="round"/>')
    bc, bw = barcode(W - 170 * s - 380 * s, H - 150 * s - 300 * s, s)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{Wmm}mm" height="{Hmm}mm">'
           f'{background(W, H, split=0.66)}{emb}{water(W, H, s, [(.955, .18, 16, 9), (.972, .10, 12, 9)])}{bc}</svg>')
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page{{size:{Wmm}mm {Hmm}mm;margin:0}} body{{margin:0}}
.pg{{position:relative;width:{Wmm}mm;height:{Hmm}mm;overflow:hidden}}
.pg svg{{position:absolute;left:0;top:0}}
.c{{position:absolute;left:{17*s:.1f}mm;top:{24*s:.1f}mm;width:{128*s:.1f}mm;color:{CREAM}}}
.lab{{font:700 {7.4*s:.1f}pt 'Noto Sans CJK SC';color:{GOLD2};letter-spacing:.5em}}
.q{{font:700 {16*s:.1f}pt/1.75 'Noto Serif CJK SC';color:#F7F1E3;margin:{4*s:.1f}mm 0 {2*s:.1f}mm;letter-spacing:.06em}}
.rule{{width:{14*s:.1f}mm;border-top:.9pt solid {GOLD};margin:{6*s:.1f}mm 0 {5*s:.1f}mm}}
.bl p{{font:400 {8.6*s:.1f}pt/1.85 'Noto Serif CJK SC';color:{CREAM};opacity:.92;margin:0 0 {2.4*s:.1f}mm;text-align:left}}
.gold{{font:700 {10*s:.1f}pt 'Noto Serif CJK SC';color:{GOLD2};margin-top:{4.5*s:.1f}mm;letter-spacing:.04em}}
.f{{position:absolute;left:{17*s:.1f}mm;bottom:{17*s:.1f}mm;font:400 {7.2*s:.1f}pt/1.85 'Noto Sans CJK SC';color:{DIM}}}
.f b{{color:{CREAM};font-weight:700;letter-spacing:.12em}}
</style></head><body><div class="pg">{svg}
<div class="c"><div class="lab">全 书 定 音</div>
<div class="q">{M.EPIGRAPH}</div><div class="rule"></div>
<div class="bl"><p>人力资源管理为何如此挑战？常见的回答是人复杂、关系复杂，或者换了经济。这本书说，难在工具是按单一洪流造的，却要去管多元洪流：一份工作要同时对几条序列负责，由几种办法判对错，把人读成一个常数，差额就大到无法忽略。</p>
<p>四道错配由此而来：用统一性管控同一性谱系，用秩序态控制混沌态与介生态，管果子而进不了意义，抓泥鳅的手也是泥鳅。今天的“有效策略”大多是先给泥鳅抹一层灰，人抓住了，人力却停在那里。答案是不抓，推：基于体验和感知，让一条洪流推动另一条的意义之路与价值之路，方向由被推的人判；这件事要建在人—AI 复合智能体的知识发生平台上，平台也可能成为最大的一层灰。</p>
<p>这是一部研究性专著初版：化名案例都是构造的，十条“怎样算错”都未直接检验，平台效果待检，写作与审校借助 AI 协作，没有独立学术评审。它应读作一个有明确失败条件的假说。</p>
<div class="gold">张三换了领导，从 A 变成 C。先别问谁对，先问：这张表里写的是谁？</div></div></div>
<div class="f"><b>{M.PUBLISHER}</b> · {M.PUBLISHER_EN}<br>德麦国际专著第 {M.NO} 号 · 十编六十章 · 约 {WAN} 万字<br>ISBN {ISBN} · 定价 {M.PRICE}</div>
</div></body></html>"""


def main():
    import weasyprint
    import pymupdf
    ap = argparse.ArgumentParser()
    ap.add_argument('--fonts', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    for tag, (w, h) in {'print': (170, 240), 'reader': (190, 250)}.items():
        weasyprint.HTML(string=front(w, h)).write_pdf(str(a.out / f'cover-{tag}.pdf'))
        weasyprint.HTML(string=back(w, h)).write_pdf(str(a.out / f'back-{tag}.pdf'))
    for src, dst in [('cover-print.pdf', 'cover.jpg'), ('back-print.pdf', 'backcover.jpg')]:
        pg = pymupdf.open(str(a.out / src))[0]
        zoom = 1004 / pg.rect.width
        pix = pg.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
        pix.save(str(a.out / dst), jpg_quality=90)
    print('covers ok')


if __name__ == '__main__':
    main()
