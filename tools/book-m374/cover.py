#!/usr/bin/env python3
"""第 374 号《化学思想史》（胡志英 著）封面与封底：藏青纯色底，细线画曲颈瓶蒸馏、合成氨反应式、反应进程图和苯环。
用法：python3 cover.py --out <dir>
"""
import argparse
import math
import re
from pathlib import Path

NAVY = '#14264A'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#7FA7C9', '#EFE8D6', '#A9B6C8'
ISBN = '979-8-90690-588-8'
Wmm, Hmm = 170, 240

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


def barcode(x, y):
    d, bits = ean13_bits(ISBN)
    mw, h = 3.3, 190
    rects = []
    for i, b in enumerate(bits):
        if b == '1':
            guard = i < 3 or 45 <= i < 50 or i >= 92
            rects.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#111"/>'
                         % (x + 22 + i * mw, y + 40, mw + .2, h + (18 if guard else 0)))
    bw = 95 * mw + 44
    ty = y + 40 + h + 36
    txt = (f'<text x="{x + bw/2:.0f}" y="{y + 30:.0f}" font-size="19" text-anchor="middle" font-family="Noto Sans CJK SC" fill="#111">ISBN {ISBN}</text>'
           f'<text x="{x + 8:.0f}" y="{ty:.0f}" font-size="26" font-family="Noto Serif CJK SC" fill="#111">{d[0]}</text>'
           f'<text x="{x + 22 + 24*mw:.0f}" y="{ty:.0f}" font-size="26" text-anchor="middle" letter-spacing="9" font-family="Noto Serif CJK SC" fill="#111">{d[1:7]}</text>'
           f'<text x="{x + 22 + 71*mw:.0f}" y="{ty:.0f}" font-size="26" text-anchor="middle" letter-spacing="9" font-family="Noto Serif CJK SC" fill="#111">{d[7:]}</text>')
    return f'<rect x="{x:.0f}" y="{y:.0f}" width="{bw:.0f}" height="{h + 110:.0f}" fill="#fff"/>' + ''.join(rects) + txt


def ring(cx, cy, r):
    """一枚细线苯环：六边形加内圆。"""
    pts = ' '.join('%.1f,%.1f' % (cx + r * math.cos(math.radians(60 * k - 90)),
                                  cy + r * math.sin(math.radians(60 * k - 90))) for k in range(6))
    return (f'<polygon points="{pts}" fill="none" stroke="{GOLD}" stroke-width="3" stroke-linejoin="round"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r*0.58:.1f}" fill="none" stroke="{GOLD}" stroke-width="3"/>')


def line(d, color=CREAM, w=3, extra=''):
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round" {extra}/>'


def distillation():
    """曲颈瓶蒸馏：酒精灯、三脚架、曲颈瓶、接收瓶。一律细线，液面用一个淡蓝。"""
    o = []
    # 三脚架与酒精灯
    o.append(line('M270 1625 L595 1625 M320 1625 L280 1860 M545 1625 L585 1860', DIM))
    o.append(line('M350 1860 L510 1860 L490 1790 L370 1790 Z', CREAM))
    o.append(line('M430 1790 L430 1762', CREAM))
    o.append(f'<path d="M430 1668 C462 1710 458 1752 430 1762 C402 1752 398 1710 430 1668 Z" fill="{GOLD2}"/>')
    # 曲颈瓶：先铺液面，再描外形
    o.append(f'<path d="M287.3 1510 A150 150 0 0 0 578.1 1510 Z" fill="{CYAN}" fill-opacity=".5"/>')
    o.append(f'<path d="M322 1372 A150 150 0 1 0 578 1436 L1032 1584 L1044 1558 L610 1330 C530 1268 392 1270 322 1372 Z" fill="none" stroke="{CREAM}" stroke-width="3" stroke-linejoin="round"/>')
    # 接收瓶（锥形瓶）
    o.append(f'<path d="M975 1720 L900 1826 Q884 1860 924 1860 L1190 1860 Q1230 1860 1214 1826 L1139 1720 Z" fill="{CYAN}" fill-opacity=".5"/>')
    o.append(line('M1022 1500 L1092 1500 M1032 1500 L1032 1640 L900 1826 Q884 1860 924 1860 L1190 1860 Q1230 1860 1214 1826 L1082 1640 L1082 1500', CREAM))
    o.append(f'<circle cx="1057" cy="1612" r="7" fill="{GOLD2}"/>')
    return ''.join(o)


def equation(x, y):
    """合成氨：N2 + 3H2 ⇌ 2NH3，箭头上标催化剂 Fe。"""
    f = "font-family=\"Noto Serif CJK SC\""
    big = f'{f} font-size="58" fill="{CREAM}"'
    sub = f'{f} font-size="36" fill="{CREAM}"'
    o = [f'<text x="{x}" y="{y}" {big}>N</text><text x="{x+44}" y="{y+14}" {sub}>2</text>',
         f'<text x="{x+90}" y="{y}" {big}>+</text>',
         f'<text x="{x+150}" y="{y}" {big}>3H</text><text x="{x+236}" y="{y+14}" {sub}>2</text>']
    ax0, ax1 = x + 288, x + 438
    o.append(line(f'M{ax0} {y-28} L{ax1} {y-28} L{ax1-20} {y-42}', GOLD))
    o.append(line(f'M{ax1} {y-12} L{ax0} {y-12} L{ax0+20} {y+2}', GOLD))
    o.append(f'<text x="{(ax0+ax1)//2}" y="{y-44}" text-anchor="middle" {f} font-size="30" fill="{GOLD2}">Fe</text>')
    o.append(f'<text x="{x+462}" y="{y}" {big}>2NH</text><text x="{x+586}" y="{y+14}" {sub}>3</text>')
    return ''.join(o)


def energy(x0, y0, w, h):
    """反应进程图：实线无催化，虚线有催化，能垒更低。"""
    xa, ya = x0, y0 + h
    o = [line(f'M{xa} {y0} L{xa} {ya} L{xa+w} {ya}', DIM, 2.4)]
    px = lambda t: xa + w * t
    py = lambda t: ya - h * t
    o.append(line(f'M{px(.04):.0f} {py(.46):.0f} L{px(.18):.0f} {py(.46):.0f} C{px(.34):.0f} {py(.46):.0f} {px(.36):.0f} {py(.94):.0f} {px(.5):.0f} {py(.94):.0f} '
                  f'C{px(.64):.0f} {py(.94):.0f} {px(.66):.0f} {py(.2):.0f} {px(.82):.0f} {py(.2):.0f} L{px(.96):.0f} {py(.2):.0f}', CREAM, 3))
    o.append(line(f'M{px(.18):.0f} {py(.46):.0f} C{px(.32):.0f} {py(.46):.0f} {px(.38):.0f} {py(.66):.0f} {px(.5):.0f} {py(.66):.0f} '
                  f'C{px(.62):.0f} {py(.66):.0f} {px(.68):.0f} {py(.2):.0f} {px(.82):.0f} {py(.2):.0f}', GOLD2, 3, 'stroke-dasharray="11 11"'))
    lab = f'font-family="Noto Sans CJK SC" font-size="25" fill="{DIM}"'
    o.append(f'<text x="{xa+w}" y="{ya+38}" text-anchor="end" {lab}>反应进程</text>')
    o.append(f'<text x="{xa+14}" y="{y0+18}" {lab}>能量</text>')
    return ''.join(o)


BASE = f"""@page{{size:{Wmm}mm {Hmm}mm;margin:0;background:{NAVY}}} html,body{{margin:0;background:{NAVY}}}
.pg{{position:relative;width:{Wmm}mm;height:{Hmm}mm;overflow:hidden;background:{NAVY}}}
.pg svg{{position:absolute;left:0;top:0}}"""


def front():
    W, H = Wmm * 10, Hmm * 10
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{Wmm}mm" height="{Hmm}mm">'
           f'<rect width="{W}" height="{H}" fill="{NAVY}"/>{equation(170, 1090)}{energy(980, 800, 540, 390)}{distillation()}{ring(1420, 1640, 112)}</svg>')
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><style>{BASE}
.t{{position:absolute;left:17mm;top:40mm;color:{CREAM}}}
.big{{font:700 44pt/1.2 'Noto Serif CJK SC';letter-spacing:.1em;color:#F7F1E3;margin-left:-1mm}}
.sub{{font:400 13pt/1.75 'Noto Serif CJK SC';color:{GOLD2};letter-spacing:.05em;margin-top:5mm}}
.rule{{width:16mm;border-top:.9pt solid {GOLD};margin-top:7mm}}
.b{{position:absolute;left:17mm;bottom:19mm}}
.au{{font:400 14pt 'Noto Serif CJK SC';color:{CREAM};letter-spacing:.28em}}
.ph{{font:700 9.4pt 'Noto Sans CJK SC';color:{GOLD2};letter-spacing:.3em;margin-top:7mm}}
.pe{{font:400 7pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.08em;margin-top:1mm}}
.no{{position:absolute;left:17mm;top:19mm;font:400 8pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.2em}}
</style></head><body><div class="pg">{svg}
<div class="no">德麦国际专著 · 第 374 号</div>
<div class="t"><div class="big">化学思想史</div>
<div class="sub">从物质同一性到化学世界的创造</div><div class="rule"></div></div>
<div class="b"><div class="au">胡志英　著</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div>
</div></body></html>"""


def back():
    W, H = Wmm * 10, Hmm * 10
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{Wmm}mm" height="{Hmm}mm">'
           f'<rect width="{W}" height="{H}" fill="{NAVY}"/>{barcode(W - 170 - 358, H - 170 - 300)}</svg>')
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><style>{BASE}
.c{{position:absolute;left:17mm;top:26mm;width:132mm;color:{CREAM}}}
.q{{font:700 15pt/1.75 'Noto Serif CJK SC';color:#F7F1E3;letter-spacing:.04em}}
.rule{{width:14mm;border-top:.9pt solid {GOLD};margin:7mm 0 6mm}}
.c p{{font:400 9.6pt/1.95 'Noto Serif CJK SC';color:{CREAM};margin:0 0 3mm}}
.f{{position:absolute;left:17mm;bottom:17mm;font:400 7.4pt/1.85 'Noto Sans CJK SC';color:{DIM}}}
.f b{{color:{CREAM};font-weight:700;letter-spacing:.12em}}
</style></head><body><div class="pg">{svg}
<div class="c"><div class="q">两份组成相同的样品，<br>为什么不能互换？</div><div class="rule"></div>
<p>这本书从一个问题出发：化学怎样建立能够被辨认、比较、转化和交接的物质世界？物质同一性贯穿全书，酸性与催化则分别检验属性尺度和运行状态。</p>
<p>从样品与炼制、气体与元素、数量与结构，到反应、催化、合成和自动实验，全书追踪新的化学世界怎样形成，又怎样在失败和新证据面前修订。</p>
<p>本稿由 AI 协作起草、核查与统稿。书中提出的三项后续研究尚未实施，全书中心命题尚待外部独立评阅。</p></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 374 号 · 十二编六十章 · 约 30 万字<br>ISBN {ISBN} · 定价 US$20</div>
</div></body></html>"""


def main():
    import pymupdf
    import weasyprint
    from PIL import Image
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    weasyprint.HTML(string=front()).write_pdf(str(a.out / 'cover-print.pdf'))
    weasyprint.HTML(string=back()).write_pdf(str(a.out / 'back-print.pdf'))
    for src, dst in [('cover-print.pdf', 'cover.jpg'), ('back-print.pdf', 'backcover.jpg')]:
        doc = pymupdf.open(str(a.out / src))
        assert len(doc) == 1, src
        pg = doc[0]
        zoom = 1004 / pg.rect.width
        png = a.out / (dst + '.png')
        pg.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom)).save(str(png))
        im = Image.open(png).convert('RGB')
        w, h = im.size
        # 页高不是整数像素，末行会被混淡：用上一行盖掉
        im.paste(im.crop((0, h - 2, w, h - 1)), (0, h - 1))
        im.save(a.out / dst, quality=90)
        png.unlink()
    print('covers ok')


if __name__ == '__main__':
    main()
