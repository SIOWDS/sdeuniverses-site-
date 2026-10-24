#!/usr/bin/env python3
"""第 420 号《一句话是怎么活起来的》封面与封底（由第 419 号 cover.py 改来，220 系列版式：藏青底、细点阵、大号书名、金色副题、金环内的扁平主图、白色大字判词、右下条码）；
全图只用纯色、不用渐变。主图取全书总比喻「一句话办成一件事」：一只奶油色的对话气泡，里面一行长短不一的「词」（一个金色的岗位），
气泡顶上长出一棵两片叶的小苗；右下一只青色小气泡打着勾在回话（对方接住了）；左上一盏小灯刚亮。画面里不写字。
用法：python3 cover.py --fonts /home/claude/fonts --out <dir>
"""
import argparse
import math
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0B1830', '#1B3158', '#142746'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#58BDCA', '#EFE8D6', '#9FB0C8'
ISBN = '979-8-90690-600-7'

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


def background(W, H, uid):
    dots = []
    step = 44
    for yy in range(22, H, step):
        for xx in range(22 + (yy // step % 2) * 22, W, step):
            dots.append('<circle cx="%d" cy="%d" r="1.7"/>' % (xx, yy))
    return f"""
<rect width="{W}" height="{H}" fill="{NAVY_MID}"/>
<g fill="{DIM}" fill-opacity=".10">{''.join(dots)}</g>"""



def ring(cx, cy, r, uid):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r*1.08:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".14" stroke-width="10"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{GOLD}" stroke-opacity=".62" stroke-width="3.4"/>')


LEAF, LEAF2, STEM, INK = '#7CC47F', '#5FAF6A', '#4E9A5B', '#1B3158'


def art(W, H, uid):
    """主图：一句话办成一件事。奶油色对话气泡里一行长短不一的「词」（其中一个是金色的岗位），
    气泡顶上长出一棵两片叶的小苗；右下一只青色小气泡在回话；左上一盏小灯刚亮。全部纯色。"""
    s = W / 1700
    cx, cy, r = 1150, 1590, 640
    o = [ring(cx * s, cy * s, r * s, uid)]
    g = [f'<g transform="scale({s})">']
    # 小灯：灯亮了
    g.append(f'<circle cx="780" cy="1080" r="44" fill="{GOLD2}"/>')
    for ang in range(0, 360, 45):
        a = math.radians(ang)
        g.append(f'<line x1="{780 + 70*math.cos(a):.0f}" y1="{1080 + 70*math.sin(a):.0f}" x2="{780 + 100*math.cos(a):.0f}" y2="{1080 + 100*math.sin(a):.0f}" '
                 f'stroke="{GOLD2}" stroke-width="12" stroke-linecap="round"/>')
    # 小苗：从气泡顶上长出来
    g.append(f'<path d="M1120 1528 C1120 1430 1098 1350 1124 1236" fill="none" stroke="{STEM}" stroke-width="24" stroke-linecap="round"/>')
    g.append(f'<path d="M1114 1352 C1036 1352 976 1300 960 1222 C1040 1216 1102 1264 1114 1352 Z" fill="{LEAF}"/>')
    g.append(f'<path d="M1126 1268 C1206 1258 1278 1194 1294 1108 C1206 1106 1136 1170 1126 1268 Z" fill="{LEAF2}"/>')
    # 主气泡（一句话）与尾巴
    g.append(f'<path d="M930 1868 L846 1996 L1046 1872 Z" fill="{CREAM}"/>')
    g.append(f'<rect x="800" y="1520" width="640" height="370" rx="96" fill="{CREAM}"/>')
    # 气泡里的一行「词」：长短不一，中间一个金色的岗位
    for x, w, col in [(880, 150, INK), (1052, 96, GOLD), (1170, 186, INK)]:
        g.append(f'<rect x="{x}" y="1672" width="{w}" height="40" rx="20" fill="{col}"/>')
    g.append(f'<rect x="880" y="1752" width="230" height="40" rx="20" fill="{INK}" fill-opacity=".35"/>')
    # 回话的小气泡：对方接住了
    g.append(f'<path d="M1584 1952 L1660 2030 L1540 1958 Z" fill="{CYAN}"/>')
    g.append(f'<rect x="1446" y="1820" width="214" height="140" rx="56" fill="{CYAN}"/>')
    g.append(f'<path d="M1500 1892 L1538 1926 L1606 1858" fill="none" stroke="{CREAM}" stroke-width="20" stroke-linecap="round" stroke-linejoin="round"/>')
    g.append('</g>')
    g.append(f'<line x1="{760 * s:.0f}" y1="{2085 * s:.0f}" x2="{W - 60 * s:.0f}" y2="{2085 * s:.0f}" stroke="{DIM}" stroke-opacity=".45" stroke-width="{2.4 * s:.1f}"/>')
    dots = ''.join(f'<circle cx="{(560 + i * 40) * s:.0f}" cy="{(1930 - i * 55) * s:.0f}" r="{(15 - i * 2.4) * s:.1f}" fill="{GOLD}" fill-opacity="{.95 - i * .17:.2f}"/>' for i in range(5))
    return ''.join(o) + ''.join(g) + dots


def barcode(x, y, s):
    if not re.search(r'\d{13}', re.sub(r'\D', '', ISBN) or ''):
        return (f'<rect x="{x:.0f}" y="{y:.0f}" width="{520*s:.0f}" height="{300*s:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".6" stroke-width="{2*s:.1f}" stroke-dasharray="{8*s:.0f} {8*s:.0f}"/>'
                f'<text x="{x + 260*s:.0f}" y="{y + 170*s:.0f}" font-size="{34*s:.0f}" text-anchor="middle" font-family="Noto Sans CJK SC" fill="{CREAM}" fill-opacity=".8">ISBN · 定价　待填</text>'), 520*s
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
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page{{size:{Wmm}mm {Hmm}mm;margin:0}} body{{margin:0}}
.pg{{position:relative;width:{Wmm}mm;height:{Hmm}mm;overflow:hidden}}
.pg svg{{position:absolute;left:0;top:0}}
.t{{position:absolute;left:{11.5*s:.1f}mm;top:{38*s:.1f}mm;color:{CREAM}}}
.big{{font:700 {54*s:.1f}pt/1.22 'Noto Serif CJK SC';letter-spacing:.06em;color:#F7F1E3;margin:0 0 {5*s:.1f}mm {-1*s:.1f}mm}}
.sub{{font:500 {13.4*s:.1f}pt/1.75 'Noto Sans CJK SC';color:{GOLD2};letter-spacing:.04em;margin-left:{1*s:.1f}mm}}
.no{{position:absolute;right:{15*s:.1f}mm;top:{15*s:.1f}mm;font:400 {6.6*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.2em;text-align:right}}
.au{{position:absolute;left:{11.5*s:.1f}mm;top:{201*s:.1f}mm;font:400 {17*s:.1f}pt 'Noto Sans CJK SC';color:{CREAM};letter-spacing:.3em}}
.auline{{position:absolute;left:{11.5*s:.1f}mm;top:{196*s:.1f}mm;width:{47*s:.1f}mm;border-top:.9pt solid {DIM};opacity:.6}}
.adv{{position:absolute;left:{11.5*s:.1f}mm;top:{209.5*s:.1f}mm;font:400 {9.6*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.3em}}
.ph{{position:absolute;left:{11.5*s:.1f}mm;top:{219*s:.1f}mm;font:600 {11.2*s:.1f}pt 'Noto Sans CJK SC';color:{CREAM};letter-spacing:.14em}}
.pe{{position:absolute;left:{11.5*s:.1f}mm;top:{226*s:.1f}mm;font:400 {7.8*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.16em}}
</style></head><body><div class="pg">{svg}
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 420 号</div>
<div class="t"><div class="big">一句话是<br>怎么活起来的</div><div class="sub">普通人都能懂的英语语法</div></div>
<div class="auline"></div><div class="au">麦子　著</div><div class="adv">王德生　指导</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div>
</div></body></html>"""


def back(Wmm, Hmm, F):
    W, H = Wmm * 10, Hmm * 10
    s = Wmm / 170
    cx, cy, r = W * 0.80, H * 0.185, 480 * s
    ringsvg = (f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r*1.08:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".14" stroke-width="{10*s:.1f}"/>'
               f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".62" stroke-width="{3.4*s:.1f}"/>')
    bc, bw = barcode(W - 170 * s - 380 * s, H - 150 * s - 300 * s, s)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{Wmm}mm" height="{Hmm}mm">'
           f'{background(W, H, "b")}{ringsvg}{bc}</svg>')
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page{{size:{Wmm}mm {Hmm}mm;margin:0}} body{{margin:0}}
.pg{{position:relative;width:{Wmm}mm;height:{Hmm}mm;overflow:hidden}}
.pg svg{{position:absolute;left:0;top:0}}
.c{{position:absolute;left:{13*s:.1f}mm;top:{20*s:.1f}mm;width:{130*s:.1f}mm;color:{CREAM}}}
.q{{font:600 {15.2*s:.1f}pt/1.95 'Noto Sans CJK SC';color:#FFFFFF;margin:0 0 {9*s:.1f}mm}}
.bl p{{font:400 {10.6*s:.1f}pt/1.95 'Noto Sans CJK SC';color:#EDE7D8;margin:0 0 {3.6*s:.1f}mm}}
.gold{{font:500 {11.6*s:.1f}pt/1.8 'Noto Sans CJK SC';color:{GOLD2};margin-top:{9*s:.1f}mm}}
.gold span{{margin-left:{9*s:.1f}mm}}
.f{{position:absolute;left:{13*s:.1f}mm;bottom:{16*s:.1f}mm;font:400 {8.6*s:.1f}pt/2.1 'Noto Sans CJK SC';color:#D6DCE8;border-top:.9pt solid {DIM};padding-top:{4*s:.1f}mm;width:{82*s:.1f}mm}}
</style></head><body><div class="pg">{svg}
<div class="c"><div class="q">早上七点，Get up!<br>她翻了个身。<br>Are you still sleeping?<br>她一下坐了起来。</div>
<div class="bl"><p>背熟了八大词类，<br>被人问路时还是一句也说不出。<br>不是你笨，也不是你不够努力，<br>是顺序反了。</p>
<p>先有要办的事，再有说话的过程，<br>句子才活起来；<br>词性只是句子里的岗位。<br>跟着小雨和妈妈走一个学年，<br>二十个卡住的地方，长出二十盏灯。</p>
<p>写给初中生，<br>也写给陪孩子学英语的妈妈。</p></div>
<div class="gold">先有句子，后有词性。<span>——本书</span></div></div>
<div class="f">德麦国际出版社 · Demai International Press<br>德麦国际专著第 420 号<br>定价：US$20.00</div>
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
