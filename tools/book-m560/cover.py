#!/usr/bin/env python3
"""第 560 号《文学的同一性谱系——后现代之后，从卡夫卡到残雪》（王德生 著）封面与封底（工具链承自第 550 号，藏青底、金青奶白三色，220 系列版式）：
主图：一只轮子、一个奔跑的人、一条三圈的思考跑道（张力·转换·释放）。全部纯色，不用渐变。封面不写「王德生指导」。
用法：python3 cover.py --fonts /usr/share/fonts/opentype/noto --out <dir>
"""
import argparse
import math
import os
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0C1A34', '#1B3158', '#16294A'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#7FA7C9', '#EFE8D6', '#A9B6C8'
ISBN = '979-8-90690-569-7'
WAN = os.environ.get('WAN', '25')

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
    """主图（第 560 号）：意义的搬家。
    左：一扇高大的拱门（统一性），门开着一道缝却够不着，门前一个小小的人；
    中：一条由左向右展开的谱系曲线，七个节点由大到小、由一到多（卡夫卡至残雪），节点之间虚线回写；
    右：许多彼此交叠、像而不同的小圆环（家族近似、各处新发生的同一性）。全部纯色，不用渐变。"""
    import random
    rnd = random.Random(560)
    s = W / 1700
    out = []
    base = H * 0.60
    # 左：拱门
    dx, dw, dh = W * 0.06, 230 * s, 470 * s
    top = base - dh
    out.append(f'<path d="M{dx:.0f} {base:.0f} L{dx:.0f} {top + dw/2:.0f} A {dw/2:.0f} {dw/2:.0f} 0 0 1 {dx + dw:.0f} {top + dw/2:.0f} L{dx + dw:.0f} {base:.0f} Z" fill="{NAVY_TOP}" stroke="{GOLD2}" stroke-width="{4*s:.1f}"/>')
    out.append(f'<path d="M{dx + dw*0.5:.0f} {base:.0f} L{dx + dw*0.5:.0f} {top + dw*0.55:.0f}" stroke="{GOLD}" stroke-opacity=".9" stroke-width="{2.4*s:.1f}"/>')
    out.append(f'<path d="M{dx + dw*0.5:.0f} {base:.0f} L{dx + dw*0.5 + 26*s:.0f} {base - 6*s:.0f} L{dx + dw*0.5 + 26*s:.0f} {top + dw*0.6:.0f} L{dx + dw*0.5:.0f} {top + dw*0.55:.0f} Z" fill="{GOLD2}" fill-opacity=".85"/>')
    out.append(f'<line x1="0" y1="{base:.0f}" x2="{dx + dw + 80*s:.0f}" y2="{base:.0f}" stroke="{GOLD2}" stroke-opacity=".6" stroke-width="{2.4*s:.1f}"/>')
    # 门前的小人
    hx = dx + dw + 46 * s
    out.append(f'<circle cx="{hx:.0f}" cy="{base - 66*s:.0f}" r="{9*s:.0f}" fill="{CREAM}"/>')
    out.append(f'<path d="M{hx:.0f} {base - 56*s:.0f} L{hx - 2*s:.0f} {base - 22*s:.0f} M{hx - 2*s:.0f} {base - 22*s:.0f} L{hx - 12*s:.0f} {base:.0f} M{hx - 2*s:.0f} {base - 22*s:.0f} L{hx + 9*s:.0f} {base:.0f} M{hx:.0f} {base - 46*s:.0f} L{hx - 14*s:.0f} {base - 30*s:.0f}" stroke="{CREAM}" stroke-width="{3.2*s:.1f}" fill="none" stroke-linecap="round"/>')
    # 中：谱系曲线
    p0, p1, p2, p3 = (dx + dw + 120*s, base - 120*s), (W*0.40, base - 420*s), (W*0.62, base + 40*s), (W*0.88, base - 300*s)
    pts = [bez(p0, p1, p2, p3, k / 80) for k in range(81)]
    out.append('<path d="M' + ' L'.join('%.1f %.1f' % q for q in pts) + f'" fill="none" stroke="{GOLD}" stroke-opacity=".55" stroke-width="{3*s:.1f}" stroke-dasharray="{14*s:.0f} {10*s:.0f}"/>')
    names = ['卡夫卡', '贝克特', '罗伯-格里耶', '博尔赫斯', '卡尔维诺', '马尔克斯', '残雪']
    for i, nm in enumerate(names):
        x, y = bez(p0, p1, p2, p3, 0.04 + i * 0.152)
        r = (40 - i * 4.2) * s
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.0f}" fill="{NAVY_MID}" stroke="{GOLD2 if i < 3 else CYAN}" stroke-width="{3*s:.1f}"/>')
        for k in range(i):   # 越往后，新发生的小同一性越多
            a = rnd.uniform(math.pi * 1.05, math.pi * 1.95); d = r + rnd.uniform(14, 40) * s
            out.append(f'<circle cx="{x + d*math.cos(a):.0f}" cy="{y + d*math.sin(a):.0f}" r="{rnd.uniform(4, 9)*s:.1f}" fill="{CREAM}" fill-opacity="{rnd.uniform(.45, .9):.2f}"/>')
        out.append(f'<text x="{x:.0f}" y="{y + r + 34*s:.0f}" font-size="{19*s:.0f}" text-anchor="middle" font-family="Noto Sans CJK SC" fill="{DIM}" letter-spacing="{2*s:.0f}">{nm}</text>')
    # 右：家族近似的交叠圆环
    cx0, cy0 = W * 0.86, base - 80 * s
    cols = [GOLD2, CYAN, CREAM]
    for k in range(26):
        out.append(f'<circle cx="{cx0 + rnd.uniform(-150, 150)*s:.0f}" cy="{cy0 + rnd.uniform(-60, 150)*s:.0f}" r="{rnd.uniform(16, 44)*s:.0f}" fill="none" stroke="{cols[k % 3]}" stroke-opacity="{rnd.uniform(.35, .8):.2f}" stroke-width="{rnd.uniform(1.6, 3.2)*s:.1f}"/>')
    # 注脚三行
    ty2 = base + 300 * s
    for xx, anc, big, small, col in ((W * 0.08, 'start', '门', '统一性还在，只是够不着', GOLD2), (W * 0.42, 'start', '谱', '意义没有消失，只是搬了家', CYAN), (W * 0.92, 'end', '字', '同一性在各处新发生', CREAM)):
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 560 号</div>
<div class="t"><div class="pre">普通人都能明白的</div><div class="big">文学的同一性谱系</div>
<div class="sub">后现代之后，从卡夫卡到残雪</div><div class="rule"></div></div>
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
<div class="c"><div class="lab">核 心 命 题</div>
<div class="q">文学的后现代的救赎，<br>应该是文学的同一性谱系。</div><div class="by">——王德生口述</div><div class="rule"></div>
<div class="bl"><p>后现代拆掉了统一性：没有中心，没有宏大叙事，没有唯一正确的读法。拆是对的，可它停在了半路，把「统一性碎了」读成了「意义没了」，于是只剩反讽、游戏与虚无。</p>
<p>本书说，意义没有消失，只是搬了家：从公共的统一性，搬到谱系上各处新发生的同一性。卡夫卡的门还在却够不着；贝克特只剩等待；罗伯-格里耶拿掉人只剩物；博尔赫斯把统一性推到无穷；卡尔维诺让意义在读的时候发生；马尔克斯写出一个部落、一个家族的同一性；残雪站到谱系的另一端，意义只在一个自我、一场梦里新发生。七位作家排开，正好是这次搬家的全程。</p>
<p>AI 已经能批量写出通顺、合规、人人看得懂的文字，统一性退成了水和电。文学剩下的价值，在谱系上：一个人、一个部落的字，怎样发生。</p>
<p>母题由王德生口述提出；正文由 AI（Claude）协作撰写并经三审；仍受版权保护的作品一律转述；书中读者与场景多为构想，没有独立学术评审。</p></div>
<div class="gold">后现代不是终点，是搬家的中途。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 560 号 · 前言、三编十三章、结语 · 约 {WAN} 万字<br>ISBN 979-8-90690-569-7 · 定价 US$20.00</div>
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
