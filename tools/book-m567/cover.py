#!/usr/bin/env python3
"""第 567 号《一颗心，一阵心，一片心》（王德生 著）封面与封底（工具链承自第 566 号；靛青底，金、青绿点缀，220 系列版式）：
主图：水面上的一颗石子、一圈波纹、一整片水（粒子心、波心、场心）。全部纯色，不用渐变。
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
    """主图（第 567 号《一颗心，一阵心，一片心》）：水面上的一颗石子、一圈波纹、一整片水。
    一颗金色石子正落到水面（粒子心），以它为心起一圈圈青绿波纹往外传（波心），
    底下是一整片铺开的水，横纹平平地铺到两边（场心）；水面映着石子的倒影——平下来的水还照得见。全部纯色，不用渐变。"""
    s = W / 1700
    out = []
    cx, y0 = W * 0.58, H * 0.655          # 石子落点所在的水面
    # ── 场心：一整片水，横纹铺满整个宽度，越往下越密、越淡 ──
    out.append(f'<rect x="0" y="{y0:.0f}" width="{W}" height="{H*0.80 - y0:.0f}" fill="{CYAN}" fill-opacity=".07"/>')
    yy, k = y0 + 16 * s, 0
    while yy < H * 0.795:
        op = max(.05, .30 - .022 * k)
        x0 = W * (0.02 + 0.01 * (k % 3)); x1 = W * (0.98 - 0.012 * ((k + 1) % 3))
        out.append(f'<line x1="{x0:.0f}" y1="{yy:.0f}" x2="{x1:.0f}" y2="{yy:.0f}" stroke="{CREAM}" stroke-opacity="{op:.2f}" stroke-width="{1.6*s:.1f}"/>')
        yy += (14 + 2.2 * k) * s; k += 1
    # 水面线
    out.append(f'<line x1="0" y1="{y0:.0f}" x2="{W}" y2="{y0:.0f}" stroke="{CREAM}" stroke-opacity=".55" stroke-width="{2.4*s:.1f}"/>')
    # ── 波心：一圈圈波纹（透视成扁椭圆），由内到外渐淡 ──
    for i in range(1, 9):
        rx = 80 * s * i ** 1.05; ry = rx * 0.21
        op = max(.12, .9 - .1 * i)
        sw = max(1.4, 5.2 - .45 * i) * s
        out.append(f'<ellipse cx="{cx:.0f}" cy="{y0:.0f}" rx="{rx:.0f}" ry="{ry:.0f}" fill="none" stroke="{CYAN if i % 2 else GOLD2}" stroke-opacity="{op:.2f}" stroke-width="{sw:.1f}"/>')
    # ── 粒子心：一颗金色石子，正落到水面；上方几点落下的轨迹 ──
    r = 46 * s
    sy = y0 - r * 0.55
    for j, (dy, rr, op) in enumerate([(210, 7, .22), (150, 9, .36), (98, 12, .55)]):
        out.append(f'<circle cx="{cx:.0f}" cy="{sy - dy*s:.0f}" r="{rr*s:.1f}" fill="{GOLD2}" fill-opacity="{op}"/>')
    out.append(f'<ellipse cx="{cx:.0f}" cy="{sy:.0f}" rx="{r*1.12:.0f}" ry="{r:.0f}" fill="{GOLD}"/>')
    out.append(f'<ellipse cx="{cx - r*.32:.0f}" cy="{sy - r*.34:.0f}" rx="{r*.34:.0f}" ry="{r*.2:.0f}" fill="{GOLD2}" fill-opacity=".85"/>')
    # 水下倒影：平下来的水还照得见
    out.append(f'<ellipse cx="{cx:.0f}" cy="{y0 + r*1.25:.0f}" rx="{r*1.0:.0f}" ry="{r*.42:.0f}" fill="{GOLD}" fill-opacity=".22"/>')
    # 溅起的几滴
    for ang, dist, rr in ((-150, 70, 6), (-125, 92, 4.5), (-55, 88, 5), (-30, 66, 6.5)):
        a = math.radians(ang)
        out.append(f'<circle cx="{cx + math.cos(a)*dist*s:.0f}" cy="{y0 + math.sin(a)*dist*s*.6:.0f}" r="{rr*s:.1f}" fill="{CREAM}" fill-opacity=".7"/>')
    # ── 三个名字 ──
    lab = lambda x, y, t, anchor='start', col=DIM: (f'<text x="{x:.0f}" y="{y:.0f}" font-size="{27*s:.0f}" text-anchor="{anchor}" '
                                                  f'font-family="Noto Sans CJK SC" fill="{col}" letter-spacing="{4*s:.0f}">{t}</text>')
    out.append(f'<line x1="{cx + r*1.3:.0f}" y1="{sy - r*.4:.0f}" x2="{cx + 150*s:.0f}" y2="{sy - 95*s:.0f}" stroke="{GOLD2}" stroke-opacity=".7" stroke-width="{1.6*s:.1f}"/>')
    out.append(lab(cx + 158 * s, sy - 100 * s, '一颗 · 粒子心', col=GOLD2))
    out.append(lab(W * 0.05, y0 - 70 * s, '一阵 · 波心', col=CYAN))
    out.append(lab(W * 0.94, H * 0.775, '一片 · 场心', anchor='end', col=CREAM))
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
<div class="t"><div class="pre">三书缝隙集 · SDE 发生学</div><div class="big big2">{M.TITLE.replace("，", "，<br>")}</div>
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
<div class="q">心是洪流的显露；<br>健康的心，是三种心之间转得动。</div><div class="by">——本书母题</div><div class="rule"></div>
<div class="bl"><p>一个孩子说心是一颗，像一颗糖；一个说心是一阵，像一阵风；一个说心是一片，像下过雪的操场。汉语早就把心分好了：一颗心，一阵心，一片心。本书说，这是心的三种状态——粒子心、波心、场心。</p>
<p>詹姆斯看见了一颗宾我和一阵意识之流，弗洛伊德抓住了卡在场里的碎粒，华生只认可以数的那一颗；圣经、心经、儒家与庄子各守住一种心。每一家看准的，都只是一种；三部名著都没写三种心怎样转。</p>
<p>本书立三心转换律：场凝成一颗，有自凝，也有点成——点成的那一颗是假粒子；一颗在有回应的共鸣里化成一阵；一阵复平成一片，有止水、死水、乱水。五条判死条款，写在看材料之前。</p></div>
<div class="gold">转得动，就好。</div></div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 {M.NO} 号 · 前言、导论、八编四十章、结语、附录 · 约 {WAN} 万字<br>ISBN {M.ISBN} · 定价 {M.PRICE}</div>
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
