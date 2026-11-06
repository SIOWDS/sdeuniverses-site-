#!/usr/bin/env python3
"""第 600 号《AI大模型巴别塔的倒塌》（王德生 著）封面与封底（承第 552 号 cover.py；深蓝底、奶白书名、金色副题、金色光环，纯色扁平插图，不用渐变；规格见 popular-philosophy-monograph-format/references/cover-spec.md）：
主图：三层的塔（青、金、奶白三种纯色块）中部一道斜裂缝，塔脚下一只小手托起一粒发芽的种子。
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
    """主图（第 600 号）：一座三层的塔，三层三种纯色块（青＝大学、金＝出版、奶白＝AGI）叠起，塔身中部一道斜裂缝；
    塔脚下一只小手托起一粒发芽的种子。身后五层金色光环。全部纯色扁平，不用渐变；原创图形，不画任何真实人物。"""
    s = W / 1700
    out = []
    cx = W * 0.56
    ground = H * 0.865
    # 光环：五层同心描边，由宽而淡到细而亮
    hy = H * 0.60
    for r, w, op in [(655, 30, .06), (610, 20, .10), (565, 12, .18), (525, 6, .34), (490, 3, .70)]:
        out.append(f'<circle cx="{cx:.0f}" cy="{hy:.0f}" r="{r*s:.0f}" fill="none" stroke="{GOLD}" stroke-opacity="{op}" stroke-width="{w*s:.1f}"/>')
    # 地：三层纯色带
    for y0, h, col in [(ground, H * 0.026, '#2E4A57'), (ground + H * 0.026, H * 0.024, '#24404D'), (ground + H * 0.050, H * 0.030, '#1B3542')]:
        out.append(f'<rect x="0" y="{y0:.0f}" width="{W}" height="{h:.0f}" fill="{col}"/>')
    # 塔：三层梯形，自下而上 青／金／奶白
    TIER_H = 250 * s
    tiers = [(CYAN, 300 * s, 262 * s), (GOLD2, 252 * s, 214 * s), (CREAM, 204 * s, 164 * s)]
    y = ground
    ys = []
    for col, hw0, hw1 in tiers:
        y1 = y - TIER_H
        out.append(f'<path d="M{cx-hw0:.0f} {y:.0f} L{cx+hw0:.0f} {y:.0f} L{cx+hw1:.0f} {y1:.0f} L{cx-hw1:.0f} {y1:.0f} Z" fill="{col}"/>')
        # 层与层之间一道深色细缝；窗
        out.append(f'<rect x="{cx-hw1-6*s:.0f}" y="{y1-4*s:.0f}" width="{2*hw1+12*s:.0f}" height="{8*s:.0f}" fill="{NAVY_TOP}"/>')
        n = 4
        for k in range(n):
            wx = cx - hw1 * 0.72 + k * (hw1 * 1.44) / (n - 1)
            out.append(f'<path d="M{wx-16*s:.0f} {y-62*s:.0f} L{wx-16*s:.0f} {y-122*s:.0f} Q{wx:.0f} {y-152*s:.0f} {wx+16*s:.0f} {y-122*s:.0f} L{wx+16*s:.0f} {y-62*s:.0f} Z" fill="{NAVY_TOP}" fill-opacity=".78"/>')
        ys.append((y, y1)); y = y1
    top = y
    # 顶：小小的尖顶，像还没来得及封好的屋脊
    out.append(f'<path d="M{cx-164*s:.0f} {top:.0f} L{cx:.0f} {top-120*s:.0f} L{cx+164*s:.0f} {top:.0f} Z" fill="{CLAY}"/>')
    # 斜裂缝：从第三层右上角斜下穿过第二层，深色锯齿
    pts = [(cx + 120*s, top - 8*s), (cx + 80*s, top + 70*s), (cx + 112*s, top + 120*s), (cx + 28*s, top + 220*s),
           (cx + 52*s, top + 292*s), (cx - 40*s, top + 392*s), (cx - 30*s, top + 440*s)]
    left = ' L'.join('%.0f %.0f' % (x - (14 if i % 2 else 7) * s, yy) for i, (x, yy) in enumerate(pts))
    right = ' L'.join('%.0f %.0f' % (x + (13 if i % 2 else 8) * s, yy) for i, (x, yy) in reversed(list(enumerate(pts))))
    out.append(f'<path d="M{left} L{right} Z" fill="{NAVY_TOP}"/>')
    # 掉落的几块砖
    for bx, by, bw, bh, col, rot in [(cx + 190*s, top + 330*s, 40*s, 24*s, CREAM, 14), (cx + 238*s, top + 420*s, 34*s, 20*s, GOLD2, -18),
                                      (cx - 215*s, top + 360*s, 36*s, 22*s, CYAN, -9)]:
        out.append(f'<rect x="{bx:.0f}" y="{by:.0f}" width="{bw:.0f}" height="{bh:.0f}" fill="{col}" transform="rotate({rot} {bx+bw/2:.0f} {by+bh/2:.0f})"/>')
    # 塔脚下的小手托着发芽的种子（手在塔右侧，自右缘伸进来，掌心向上）
    hx, hy0 = cx - 520 * s, ground - 40 * s
    hand = []
    hand.append(f'<rect x="{hx-250*s:.0f}" y="{hy0+8*s:.0f}" width="{250*s:.0f}" height="{58*s:.0f}" rx="{29*s:.0f}" fill="{CLAY}" transform="rotate(-6 {hx:.0f} {hy0:.0f})"/>')   # 前臂
    hand.append(f'<rect x="{hx-12*s:.0f}" y="{hy0-14*s:.0f}" width="{176*s:.0f}" height="{66*s:.0f}" rx="{30*s:.0f}" fill="{CLAY}"/>')   # 掌
    for k in range(4):   # 四指，微微上翘
        fx = hx + (30 + k * 36) * s
        hand.append(f'<rect x="{fx:.0f}" y="{hy0-44*s - k%2*0:.0f}" width="{28*s:.0f}" height="{70*s:.0f}" rx="{14*s:.0f}" fill="{CLAY}" transform="rotate(8 {fx+14*s:.0f} {hy0:.0f})"/>')
    hand.append(f'<rect x="{hx-28*s:.0f}" y="{hy0-60*s:.0f}" width="{30*s:.0f}" height="{76*s:.0f}" rx="{15*s:.0f}" fill="{CLAY}" transform="rotate(-26 {hx:.0f} {hy0:.0f})"/>')  # 拇指
    hs = list(hand)
    # 种子与嫩芽
    sx, sy = hx + 92 * s, hy0 - 52 * s
    hs.append(f'<ellipse cx="{sx:.0f}" cy="{sy:.0f}" rx="{22*s:.0f}" ry="{15*s:.0f}" fill="{GOLD2}"/>')
    hs.append(f'<path d="M{sx:.0f} {sy-10*s:.0f} C{sx-4*s:.0f} {sy-60*s:.0f} {sx+6*s:.0f} {sy-90*s:.0f} {sx:.0f} {sy-120*s:.0f}" fill="none" stroke="{CYAN}" stroke-width="{7*s:.1f}" stroke-linecap="round"/>')
    hs.append(f'<path d="M{sx:.0f} {sy-92*s:.0f} C{sx-26*s:.0f} {sy-126*s:.0f} {sx-64*s:.0f} {sy-118*s:.0f} {sx-72*s:.0f} {sy-104*s:.0f} C{sx-52*s:.0f} {sy-86*s:.0f} {sx-24*s:.0f} {sy-84*s:.0f} {sx:.0f} {sy-92*s:.0f} Z" fill="{CYAN}"/>')
    hs.append(f'<path d="M{sx:.0f} {sy-112*s:.0f} C{sx+24*s:.0f} {sy-156*s:.0f} {sx+62*s:.0f} {sy-150*s:.0f} {sx+72*s:.0f} {sy-136*s:.0f} C{sx+52*s:.0f} {sy-116*s:.0f} {sx+24*s:.0f} {sy-108*s:.0f} {sx:.0f} {sy-112*s:.0f} Z" fill="{CYAN}"/>')
    xm = hx - 37 * s
    out.append(f'<g transform="translate({1475*s - xm:.0f} 0) translate({xm:.0f} 0) scale(-1 1) translate({-xm:.0f} 0)">' + ''.join(hs) + '</g>')
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
<div class="t"><div class="big big2" style="font-size:{50*s:.1f}pt;line-height:1.3;letter-spacing:.08em;margin-top:{12*s:.1f}mm">AI大模型<br>巴别塔的倒塌</div>
<div class="sub" style="font-size:{12*s:.1f}pt;margin-top:{6*s:.1f}mm">统一性的最大赢家，<br>成了同一性谱系的接生婆</div><div class="rule"></div></div>
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
.c{{position:absolute;left:{17*s:.1f}mm;top:{30*s:.1f}mm;width:{122*s:.1f}mm;color:{CREAM}}}
.lab{{font:700 {7.4*s:.1f}pt 'Noto Sans CJK SC';color:{GOLD2};letter-spacing:.5em}}
.q{{font:700 {14.6*s:.1f}pt/1.8 'Noto Serif CJK SC';color:#F7F1E3;margin:{4*s:.1f}mm 0 {2*s:.1f}mm;letter-spacing:.04em}}
.by{{font:400 {8.2*s:.1f}pt 'Noto Serif CJK SC';color:{DIM}}}
.rule{{width:{14*s:.1f}mm;border-top:.9pt solid {GOLD};margin:{7*s:.1f}mm 0 {6*s:.1f}mm}}
.bl p{{font:400 {9.6*s:.1f}pt/2.0 'Noto Serif CJK SC';color:{CREAM};opacity:.9;margin:0 0 {2.6*s:.1f}mm;text-align:left}}
.gold{{font:700 {10.5*s:.1f}pt 'Noto Serif CJK SC';color:{GOLD2};margin-top:{6*s:.1f}mm;letter-spacing:.06em}}
.f{{position:absolute;left:{17*s:.1f}mm;bottom:{17*s:.1f}mm;font:400 {7.2*s:.1f}pt/1.85 'Noto Sans CJK SC';color:{DIM}}}
.f b{{color:{CREAM};font-weight:700;letter-spacing:.12em}}
</style></head><body><div class="pg">{svg}
<div class="c">
<div class="q">统一性的最大赢家，<br>成了同一性谱系的接生婆：<br>塔建到顶，不是被谁推倒的，<br>是自己倒的。<br>倒下的地方，长出一个个不同的人。</div><div class="rule"></div>
<div class="bl"><p>全书讲三座塔——大学、出版、AGI——怎样一层层建起来：话要统一，知识要统一，答案也要统一。大模型把统一性推到了极限，塔顶封顶的那一天，三座塔和三把尺子——智商、智慧、图灵测试——一起失去了作数的地方。塔倒之后并不是一片空白：被统一压下去的“不同”，正等着长成各自的谱系。而这一次，统一性的最大赢家，把接生的手递了过来。</p></div>
<div class="gold">塔建成之日，就是塔倒之时。　　——本书</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 {M.NO} 号 · 约 {WAN} 万字<br>ISBN {M.ISBN} · 定价 {M.PRICE}</div>
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
