#!/usr/bin/env python3
"""第 578 号《戒掉了，这一轮谁来办？》（王德生 著）封面与封底（工具链承自第 577 号，藏青底、金青奶白三色，220 系列版式）：
主图：打烊的五金店，九只挂钩，钥匙全在第一只上，灯下的凳子空着。全部纯色，不用渐变。
用法：python3 cover.py --fonts /usr/share/fonts/opentype/noto --out <dir>
"""
import argparse
import math
import os
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0C1A34', '#1B3158', '#16294A'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#7FA7C9', '#EFE8D6', '#A9B6C8'
ISBN = '979-8-90690-599-4'
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
    """主图（第 578 号）：打烊的五金店。墙上一排九只挂钩，八只空着，整串钥匙全挂在第一只上；
    柜台上一盏灯、一本开票簿，灯下那张凳子空着。全部纯色，不用渐变。"""
    s = W / 1700
    o = []
    # 墙与柜台
    wall_y, top_y = H * 0.40, H * 0.735
    o.append(f'<rect y="{wall_y:.0f}" width="{W}" height="{H-wall_y:.0f}" fill="{NAVY_MID}"/>')
    # 灯光：一块纯色的梯形，落到凳子上
    lx = W * 0.655
    lamp_y = H * 0.475
    o.append(f'<path d="M{lx-46*s:.0f} {lamp_y:.0f} L{lx+46*s:.0f} {lamp_y:.0f} L{lx+300*s:.0f} {top_y:.0f} L{lx-300*s:.0f} {top_y:.0f} Z" fill="{GOLD2}" fill-opacity=".13"/>')
    # 挂板
    by = H * 0.452
    o.append(f'<rect x="{W*0.075:.0f}" y="{by:.0f}" width="{W*0.85:.0f}" height="{15*s:.0f}" fill="{NAVY_TOP}"/>')
    xs = [W * (0.115 + 0.0965 * i) for i in range(9)]
    for i, x in enumerate(xs):
        o.append(f'<path d="M{x:.0f} {by+8*s:.0f} l0 {26*s:.0f} a{13*s:.0f} {13*s:.0f} 0 0 0 {26*s:.0f} 0" fill="none" stroke="{GOLD if i == 0 else DIM}" stroke-width="{6*s:.1f}" stroke-linecap="round" stroke-opacity="{1 if i == 0 else .55}"/>')
    # 第一只钩上的一串钥匙
    rx, ry = xs[0] + 13 * s, by + 80 * s
    o.append(f'<circle cx="{rx:.0f}" cy="{ry:.0f}" r="{32*s:.0f}" fill="none" stroke="{GOLD2}" stroke-width="{6*s:.1f}"/>')
    for ang in (-38, -20, -3, 14, 31):
        o.append(f'<g transform="translate({rx:.0f},{ry+28*s:.0f}) rotate({ang}) scale({s:.3f})" fill="{GOLD2}">'
                 f'<circle cx="0" cy="17" r="14"/><circle cx="0" cy="17" r="5" fill="{NAVY_MID}"/>'
                 f'<rect x="-3.5" y="29" width="7" height="86"/><rect x="3" y="94" width="14" height="7"/><rect x="3" y="107" width="10" height="7"/></g>')
    # 吊灯
    o.append(f'<line x1="{lx:.0f}" y1="{by+15*s:.0f}" x2="{lx:.0f}" y2="{lamp_y:.0f}" stroke="{DIM}" stroke-width="{3*s:.1f}"/>')
    o.append(f'<path d="M{lx-62*s:.0f} {lamp_y+24*s:.0f} Q{lx:.0f} {lamp_y-34*s:.0f} {lx+62*s:.0f} {lamp_y+24*s:.0f} Z" fill="{CREAM}"/>')
    o.append(f'<circle cx="{lx:.0f}" cy="{lamp_y+26*s:.0f}" r="{13*s:.0f}" fill="{GOLD2}"/>')
    # 空凳子（柜台后面，只露出上半）
    sx, sy = lx, H * 0.635
    o.append(f'<g fill="{CREAM}"><rect x="{sx-96*s:.0f}" y="{sy:.0f}" width="{192*s:.0f}" height="{23*s:.0f}" rx="{8*s:.0f}"/></g>')
    for dx0, dx1 in ((-74, -96), (74, 96), (-26, -32), (26, 32)):
        o.append(f'<line x1="{sx+dx0*s:.0f}" y1="{sy+23*s:.0f}" x2="{sx+dx1*s:.0f}" y2="{top_y:.0f}" stroke="{CREAM}" stroke-width="{10*s:.1f}"/>')
    o.append(f'<line x1="{sx-84*s:.0f}" y1="{sy+96*s:.0f}" x2="{sx+84*s:.0f}" y2="{sy+96*s:.0f}" stroke="{CREAM}" stroke-width="{7*s:.1f}"/>')
    # 柜台
    o.append(f'<rect y="{top_y:.0f}" width="{W}" height="{22*s:.0f}" fill="{GOLD}"/>')
    o.append(f'<rect y="{top_y+22*s:.0f}" width="{W}" height="{H-top_y-22*s:.0f}" fill="{NAVY_LOW}"/>')
    # 柜台上的开票簿和笔
    px, py = W * 0.205, top_y - 38 * s
    o.append(f'<rect x="{px:.0f}" y="{py:.0f}" width="{178*s:.0f}" height="{38*s:.0f}" fill="{CREAM}"/>')
    o.append(f'<rect x="{px:.0f}" y="{py:.0f}" width="{178*s:.0f}" height="{9*s:.0f}" fill="{CYAN}"/>')
    for k in (18, 27):
        o.append(f'<line x1="{px+14*s:.0f}" y1="{py+k*s:.0f}" x2="{px+150*s:.0f}" y2="{py+k*s:.0f}" stroke="{NAVY_MID}" stroke-opacity=".5" stroke-width="{2*s:.1f}"/>')
    o.append(f'<line x1="{px+196*s:.0f}" y1="{top_y-5*s:.0f}" x2="{px+318*s:.0f}" y2="{top_y-16*s:.0f}" stroke="{GOLD2}" stroke-width="{6*s:.1f}" stroke-linecap="round"/>')
    return ''.join(o)


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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 578 号</div>
<div class="t"><div class="big big2">戒掉了，<br>这一轮谁来办？</div>
<div class="sub">普通人都能懂的成瘾九道手续</div><div class="rule"></div></div>
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
<div class="c"><div class="lab">全 书 定 音</div>
<div class="q" style="font-size:{14.2*s:.1f}pt">撤走的是办事的人，<br>岗位还空着。</div><div class="rule"></div>
<div class="bl"><p>一个人戒了八次酒，每一次都是认真的。旁人问他为什么就是戒不掉。这本书换一个问题：那样东西撤走以后，这一轮生活由谁来办？</p>
<p>一轮生活从“有事了”到“这事算过去了”，大致要过九道手续：生下一步、开工、收件、接班、收尾、记功、结账、重开、改起点。全书用大白话和身边的故事一道一道对账。第八道专门反对这本书，第九道的检验在数据上没有通过，都照实写着。</p>
<p>这不是诊断书，也不是治疗方案。长期大量饮酒、长期服用镇静类或阿片类药物的人，请不要自己突然停下来，先找医生。这是一部研究性专著初版：由九篇长文重写，正文由 AI（Claude）协作撰写，没有经过独立学术评审，也没有经过成瘾科医生审读。</p>
<div class="gold">你们已经很努力了，也许该换一个问题来问。</div></div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 578 号 · 十一编四十五章 · 约 {WAN} 万字<br>ISBN 979-8-90690-599-4 · 定价 US$20.00</div>
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
