#!/usr/bin/env python3
"""第 608 号《彩超医生会被AI替代吗？——病症符号发生学》（杨莉 著，王德生 指导）封面与封底（工具链承自第 564 号；靛青底，金、青绿点缀，220 系列版式）：
主图：扇形声束、灰阶亮点、回声弧线与金色小回箭。全部纯色，不用渐变。
封面作者行下写「王德生　指导」。
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
    """主图（第 609 号）：灶上一口锅，锅盖掀开一道缝，几缕汽；右上一只小钟，指针差一格到点。
    （尝一口汤，说“再等一会儿”——等到那个钟点为止。）全部纯色几何，不画人物、品牌。"""
    s = W / 1700
    cx = W * 0.5
    out = []
    ty = H * 0.50                      # 锅沿高度
    # 灶台
    out.append(f'<rect x="{cx-430*s:.0f}" y="{ty+520*s:.0f}" width="{860*s:.0f}" height="{34*s:.0f}" rx="{12*s:.0f}" fill="#2D4560"/>')
    for k, dx in enumerate((-250, -125, 0, 125, 250)):
        fx = cx + dx * s
        fy = ty + 505 * s
        out.append(f'<path d="M{fx:.0f} {fy-70*s:.0f} C{fx+34*s:.0f} {fy-30*s:.0f} {fx+30*s:.0f} {fy:.0f} {fx:.0f} {fy:.0f} C{fx-30*s:.0f} {fy:.0f} {fx-34*s:.0f} {fy-30*s:.0f} {fx:.0f} {fy-70*s:.0f} Z" fill="{GOLD if k % 2 == 0 else CLAY}"/>')
    # 锅耳
    out.append(f'<rect x="{cx-370*s:.0f}" y="{ty+60*s:.0f}" width="{90*s:.0f}" height="{40*s:.0f}" rx="{18*s:.0f}" fill="{CREAM}"/>')
    out.append(f'<rect x="{cx+280*s:.0f}" y="{ty+60*s:.0f}" width="{90*s:.0f}" height="{40*s:.0f}" rx="{18*s:.0f}" fill="{CREAM}"/>')
    # 锅身
    out.append(f'<rect x="{cx-300*s:.0f}" y="{ty:.0f}" width="{600*s:.0f}" height="{400*s:.0f}" rx="{90*s:.0f}" fill="{CREAM}"/>')
    out.append(f'<rect x="{cx-320*s:.0f}" y="{ty-24*s:.0f}" width="{640*s:.0f}" height="{40*s:.0f}" rx="{16*s:.0f}" fill="#DCD0B4"/>')
    out.append(f'<rect x="{cx-300*s:.0f}" y="{ty+190*s:.0f}" width="{600*s:.0f}" height="{10*s:.0f}" fill="{GOLD}" fill-opacity=".75"/>')
    # 锅盖：往上抬一道缝（绕左端转一个小角）
    out.append(f'<g transform="rotate(-7 {cx-300*s:.0f} {ty-30*s:.0f})">'
               f'<path d="M{cx-300*s:.0f} {ty-30*s:.0f} A{300*s:.0f} {160*s:.0f} 0 0 1 {cx+300*s:.0f} {ty-30*s:.0f} Z" fill="{CLAY}"/>'
               f'<circle cx="{cx:.0f}" cy="{ty-190*s:.0f}" r="{26*s:.0f}" fill="{GOLD2}"/></g>')
    # 汽：三缕
    for dx, hh, op in [(180, 420, .85), (250, 520, .6), (320, 360, .45)]:
        x0, y0 = cx + dx * s, ty - 60 * s
        pts = [bez((x0, y0), (x0 + 60 * s, y0 - hh * .3 * s), (x0 - 60 * s, y0 - hh * .65 * s), (x0 + 24 * s, y0 - hh * s), k / 30) for k in range(31)]
        out.append(f'<path d="{tapered(pts, 26 * s, 6 * s)}" fill="{CYAN}" fill-opacity="{op}"/>')
    # 小钟（右上）：差一格到点
    kx, ky, kr = cx + 430 * s, ty - 520 * s, 150 * s
    out.append(f'<circle cx="{kx:.0f}" cy="{ky:.0f}" r="{kr:.0f}" fill="{NAVY_TOP}" stroke="{GOLD2}" stroke-width="{12*s:.1f}"/>')
    for k in range(12):
        a = math.radians(k * 30 - 90)
        r1, r2 = kr * .80, kr * (.62 if k % 3 == 0 else .70)
        out.append(f'<line x1="{kx+r1*math.cos(a):.1f}" y1="{ky+r1*math.sin(a):.1f}" x2="{kx+r2*math.cos(a):.1f}" y2="{ky+r2*math.sin(a):.1f}" stroke="{CREAM}" stroke-width="{7*s if k % 3 == 0 else 4*s:.1f}" stroke-linecap="round"/>')
    # 还没走完的一格（11 点到 12 点）
    a0, a1 = math.radians(-120), math.radians(-90)
    ra = kr * .92
    p0 = (kx + ra * math.cos(a0), ky + ra * math.sin(a0)); p1 = (kx + ra * math.cos(a1), ky + ra * math.sin(a1))
    out.append(f'<path d="M{p0[0]:.1f} {p0[1]:.1f} A{ra:.1f} {ra:.1f} 0 0 1 {p1[0]:.1f} {p1[1]:.1f}" fill="none" stroke="{CLAY}" stroke-width="{16*s:.1f}" stroke-linecap="round"/>')
    ha = math.radians(-125)
    out.append(f'<line x1="{kx:.1f}" y1="{ky:.1f}" x2="{kx+kr*.58*math.cos(ha):.1f}" y2="{ky+kr*.58*math.sin(ha):.1f}" stroke="{GOLD2}" stroke-width="{10*s:.1f}" stroke-linecap="round"/>')
    out.append(f'<circle cx="{kx:.1f}" cy="{ky:.1f}" r="{12*s:.1f}" fill="{GOLD2}"/>')
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
.t{{position:absolute;left:{17*s:.1f}mm;top:{24*s:.1f}mm;color:{CREAM}}}
.big{{font:700 {38*s:.1f}pt/1.28 'Noto Serif CJK SC';letter-spacing:.08em;color:#F7F1E3;margin:0 0 {4*s:.1f}mm {-1*s:.1f}mm}}
.sub{{font:400 {15*s:.1f}pt/1.6 'Noto Serif CJK SC';color:{GOLD2};letter-spacing:.3em}}
.rule{{width:{16*s:.1f}mm;border-top:.9pt solid {GOLD};margin-top:{5*s:.1f}mm}}
.sm{{font:400 {8.4*s:.1f}pt 'Noto Sans CJK SC';color:{CREAM};letter-spacing:.3em;margin-top:{4*s:.1f}mm}}
.b{{position:absolute;left:{17*s:.1f}mm;bottom:{17*s:.1f}mm}}
.au{{font:400 {12.5*s:.1f}pt 'Noto Serif CJK SC';color:{CREAM};letter-spacing:.28em}}
.ad{{font:400 {10.5*s:.1f}pt 'Noto Serif CJK SC';color:{GOLD2};letter-spacing:.28em;margin-top:{2*s:.1f}mm}}
.ph{{font:700 {8.4*s:.1f}pt 'Noto Sans CJK SC';color:{GOLD2};letter-spacing:.3em;margin-top:{6*s:.1f}mm}}
.pe{{font:400 {6.6*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.08em;margin-top:{.8*s:.1f}mm}}
.no{{position:absolute;right:{15*s:.1f}mm;top:{12*s:.1f}mm;font:400 {6.6*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.2em;text-align:right}}
</style></head><body><div class="pg">{svg}
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 {M.NO} 号</div>
<div class="t"><div class="big">抉择需要<br>等待</div>
<div class="sub">{M.SUBTITLE}</div><div class="rule"></div><div class="sm">{M.COVER_SMALL}</div></div>
<div class="b"><div class="au">{M.AUTHOR}　著</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div>
</div></body></html>"""


def back(Wmm, Hmm, F):
    W, H = Wmm * 10, Hmm * 10
    s = Wmm / 170
    # 右上小徽：一小段扇形
    ex, ey = W * 0.84, H * 0.06
    r = 120 * s
    a0, a1 = math.radians(50), math.radians(130)
    p0 = (ex + r * math.cos(a0), ey + r * math.sin(a0)); p1 = (ex + r * math.cos(a1), ey + r * math.sin(a1))
    emb = (f'<circle cx="{ex:.0f}" cy="{ey+r*0.5:.0f}" r="{r*0.55:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".8" stroke-width="{4*s:.1f}"/>'
           f'<line x1="{ex:.0f}" y1="{ey+r*0.5:.0f}" x2="{ex-r*0.22:.0f}" y2="{ey+r*0.5-r*0.34:.0f}" stroke="{GOLD2}" stroke-width="{5*s:.1f}" stroke-linecap="round"/>'
           f'<circle cx="{ex:.0f}" cy="{ey+r*0.5:.0f}" r="{6*s:.1f}" fill="{GOLD2}"/>')
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
.q{{font:700 {15*s:.1f}pt/1.8 'Noto Serif CJK SC';color:#F7F1E3;margin:{4*s:.1f}mm 0 {2*s:.1f}mm;letter-spacing:.04em}}
.rule{{width:{14*s:.1f}mm;border-top:.9pt solid {GOLD};margin:{7*s:.1f}mm 0 {6*s:.1f}mm}}
.bl p{{font:400 {9*s:.1f}pt/1.9 'Noto Serif CJK SC';color:{CREAM};opacity:.92;margin:0 0 {3*s:.1f}mm}}
.gold{{font:700 {10*s:.1f}pt/1.8 'Noto Serif CJK SC';color:{GOLD2};margin-top:{7*s:.1f}mm;letter-spacing:.04em}}
.f{{position:absolute;left:{17*s:.1f}mm;bottom:{17*s:.1f}mm;font:400 {7.2*s:.1f}pt/1.85 'Noto Sans CJK SC';color:{DIM}}}
.f b{{color:{CREAM};font-weight:700;letter-spacing:.12em}}
</style></head><body><div class="pg">{svg}
<div class="c"><div class="lab">核 心 判 断</div>
<div class="q">有些判断，此刻只成了一半。<br>该等的，别催；不该等的，别拖。</div><div class="rule"></div>
<div class="bl"><p>本书讲医生、老师、家长、老板每天碰到的同一件事：判断还没成，却已经有人在催。</p>
<p>本书给三个问题，用来问清此刻该不该等：回得了头吗？谁在替我扛？读数赶得上吗？</p>
<p>本书不开药方，不给阈值，不替任何人做决定。</p></div>
<div class="gold">本书不作诊断，不给法律或财务建议。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 {M.NO} 号 · {M.AUTHOR}　著<br>ISBN {M.ISBN} · 定价 {M.PRICE}</div>
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
