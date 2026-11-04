#!/usr/bin/env python3
"""第 483 号《AI时代还能守正创新吗？》（王德生 著）封面与封底（工具链承自第 571 号，藏青底、金青奶白三色，220 系列版式）：
主图：两座都在晃的桥，对岸上方一颗星；原注：新线从碰撞里陡然升起，下面一道托弧（接住）。
全部矢量绘制、纯色，不用照片、不用渐变。封面不写「指导」字样，作者栏写「段君毅　王德生　著」。
用法：python3 cover.py --fonts /usr/share/fonts/opentype/noto --out <dir>
"""
import argparse
import math
import os
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0C1A34', '#1B3158', '#16294A'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#7FA7C9', '#EFE8D6', '#A9B6C8'
ISBN = '979-8-90690-981-7'
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
    """主图（第 483 号）：两座都在晃的桥，桥下是水，风从左边吹过来，对岸上方一颗定向的星。
    两座桥都不稳，人才要抬头问对岸：哪边安全换成哪边值得。全部矢量、纯色。"""
    import random
    rnd = random.Random(573)
    s = W / 1700
    out = []
    wy = H * 0.73
    # 风：几条长弧，从左吹向右
    for k in range(7):
        y0 = H * (0.40 + k * 0.038)
        d = 'M%.0f %.0f C%.0f %.0f %.0f %.0f %.0f %.0f' % (W * 0.02, y0, W * 0.28, y0 - 34 * s, W * 0.52, y0 + 40 * s, W * (0.70 + 0.03 * (k % 3)), y0 - 8 * s)
        out.append(f'<path d="{d}" fill="none" stroke="{DIM}" stroke-opacity=".20" stroke-width="{2.2*s:.1f}" stroke-linecap="round"/>')
    # 水
    for k in range(6):
        y0 = wy + k * 26 * s
        d = 'M0 %.0f' % y0
        for i in range(10):
            d += ' Q%.0f %.0f %.0f %.0f' % (W * (i + .5) / 10, y0 + (9 if i % 2 else -9) * s, W * (i + 1) / 10, y0)
        out.append(f'<path d="{d}" fill="none" stroke="{CYAN}" stroke-opacity="{.42-.05*k:.2f}" stroke-width="{2.2*s:.1f}"/>')

    def bridge(x0, x1, top, col, tilt, seed):
        r = random.Random(seed)
        n = 16
        deck = []
        for j in range(n + 1):
            t_ = j / n
            x = x0 + (x1 - x0) * t_
            y = wy - (wy - top) * 4 * t_ * (1 - t_) + tilt * s * math.sin(t_ * math.pi * 5 + seed) + r.uniform(-7, 7) * s
            deck.append((x, y))
        # 桥板一段一段，有的错位，中间留缝
        for j in range(n):
            (x1_, y1_), (x2_, y2_) = deck[j], deck[j + 1]
            dy = r.uniform(-6, 6) * s
            out.append(f'<line x1="{x1_+5*s:.0f}" y1="{y1_+dy:.0f}" x2="{x2_-5*s:.0f}" y2="{y2_+dy:.0f}" stroke="{col}" stroke-width="{10*s:.1f}" stroke-linecap="round"/>')
        # 栏杆东倒西歪
        tops = []
        for j in range(1, n):
            x, y = deck[j]
            lean = r.uniform(-22, 22) * s
            h_ = r.uniform(48, 74) * s
            out.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x+lean:.0f}" y2="{y-h_:.0f}" stroke="{col}" stroke-opacity=".8" stroke-width="{3.4*s:.1f}" stroke-linecap="round"/>')
            tops.append((x + lean, y - h_))
        rail = 'M' + ' L'.join('%.1f %.1f' % p for p in tops)
        out.append(f'<path d="{rail}" fill="none" stroke="{col}" stroke-opacity=".55" stroke-width="{2.6*s:.1f}" stroke-dasharray="{18*s:.0f} {12*s:.0f}"/>')

    bridge(W * 0.04, W * 0.47, H * 0.62, CREAM, 9, 2)
    bridge(W * 0.53, W * 0.96, H * 0.60, GOLD2, 11, 5)
    # 对岸上方的星：方向
    sx, sy = W * 0.80, H * 0.335
    pts = []
    for i in range(8):
        a_ = math.radians(i * 45 - 90)
        rr = (64 if i % 2 == 0 else 14) * s
        pts.append('%.1f,%.1f' % (sx + rr * math.cos(a_), sy + rr * math.sin(a_)))
    out.append(f'<polygon points="{" ".join(pts)}" fill="{GOLD2}"/>')
    out.append(f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="{104*s:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".35" stroke-width="{2*s:.1f}" stroke-dasharray="{6*s:.0f} {10*s:.0f}"/>')
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 483 号</div>
<div class="t"><div class="big big2">AI时代<br>还能守正创新吗？</div>
<div class="sub">从最安全的活法到最危险的生存</div><div class="rule"></div></div>
<div class="b"><div class="au">王德生　著</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div></div></body></html>"""


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
           f'{background(W, H, "b", split=0.715)}{emb}{"".join(waves)}{bc}</svg>')
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
<div class="c"><div class="lab">定 音 句</div>
<div class="q">从前是一边安全、一边危险；<br>如今两边都危险，<br>于是选择的依据，<br>从“哪边安全”换成了“哪边值得”。</div><div class="rule"></div>
<div class="bl"><p>一个认真了三十年、从不追热点的人，也可能一直在跟风：什么问题值得做，哪些路子算正路，怎样才算做好，都是别人先定好的。这种活法从前最安全，因为做到这一步要练很多年。</p>
<p>基底正在拆掉这道门槛。可是另一边并没有变好，改写“一”的人仍然大概率失败。本书走过科学、技术、艺术，走过教育、健康、事业，回答书名之问：还能守，但守的是方向，不是别人立的“一”；还能新，但不能只新在路径，要走到“一”出问题的地方。</p>
<p>全书没有做统计调查，提出的练法尚未验证，每章写明怎样算错，第 36 章请最强的反方发言。</p>
<div class="gold">被端的是位置，不是人。</div></div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 483 号 · 前言、导言、五部三十六章、结语、附录 · 约 {WAN} 万字<br>ISBN 979-8-90690-981-7 · 定价 US$20.00</div>
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
