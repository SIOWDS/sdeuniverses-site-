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
    """主图（第 608 号）：一把扇形声束从探头打向下方；扇区里一团纯色灰阶亮点、几层回声弧线；
    亮点旁一条金色小回箭（线索一步步冒出来，又放回病人身上）。全部纯色几何，不画器官、人物、品牌。"""
    s = W / 1700
    ax, ay = W * 0.5, H * 0.455          # 探头位置（扇尖）
    Rr = 800 * s
    half = math.radians(40)
    base = math.pi / 2
    def P(r, a):
        return ax + r * math.cos(a), ay + r * math.sin(a)
    out = []
    # 探头：一块圆角金属块
    pw, ph = 170 * s, 62 * s
    out.append(f'<rect x="{ax-pw/2:.0f}" y="{ay-ph-6*s:.0f}" width="{pw:.0f}" height="{ph:.0f}" rx="{20*s:.0f}" fill="{CREAM}"/>')
    out.append(f'<rect x="{ax-pw/2+14*s:.0f}" y="{ay-ph+18*s:.0f}" width="{pw-28*s:.0f}" height="{8*s:.0f}" rx="{4*s:.0f}" fill="{NAVY_TOP}" fill-opacity=".5"/>')
    # 扇区底色（纯色半透明）+ 扇区边
    a0, a1 = base - half, base + half
    p0, p1 = P(Rr, a0), P(Rr, a1)
    sector = f'M{ax:.0f} {ay:.0f} L{p0[0]:.0f} {p0[1]:.0f} A{Rr:.0f} {Rr:.0f} 0 0 1 {p1[0]:.0f} {p1[1]:.0f} Z'
    out.append(f'<path d="{sector}" fill="{CYAN}" fill-opacity=".10"/>')
    out.append(f'<path d="{sector}" fill="none" stroke="{CYAN}" stroke-opacity=".7" stroke-width="{4*s:.1f}" stroke-linejoin="round"/>')
    # 声束扫描线（细）
    for k in range(1, 8):
        a = a0 + (a1 - a0) * k / 8
        q = P(Rr, a)
        out.append(f'<line x1="{ax:.0f}" y1="{ay:.0f}" x2="{q[0]:.0f}" y2="{q[1]:.0f}" stroke="{CYAN}" stroke-opacity=".16" stroke-width="{2*s:.1f}"/>')
    # 回声弧线（几层）
    for r, op, w in [(250, .30, 3), (400, .38, 3.5), (540, .46, 4), (680, .30, 3)]:
        pa, pb = P(r * s, a0 + .02), P(r * s, a1 - .02)
        out.append(f'<path d="M{pa[0]:.0f} {pa[1]:.0f} A{r*s:.0f} {r*s:.0f} 0 0 1 {pb[0]:.0f} {pb[1]:.0f}" fill="none" stroke="{GOLD2}" stroke-opacity="{op}" stroke-width="{w*s:.1f}" stroke-linecap="round" stroke-dasharray="{26*s:.0f} {16*s:.0f}"/>')
    # 灰阶亮点团：同心纯色圆，由暗到亮；中心偏左下一点
    fx, fy = P(470 * s, base + .13)
    for r, col in [(120, '#2D4560'), (92, '#44607A'), (66, '#6A8598'), (42, '#A3B8BC'), (22, CREAM)]:
        out.append(f'<circle cx="{fx:.0f}" cy="{fy:.0f}" r="{r*s:.0f}" fill="{col}"/>')
    # 零散小亮点（散斑）
    for (rr, da, rad, col) in [(330, -.22, 11, '#6A8598'), (360, .30, 9, '#44607A'), (590, -.30, 12, '#6A8598'),
                               (610, .05, 8, '#A3B8BC'), (520, .33, 10, '#44607A'), (300, .12, 8, '#6A8598'),
                               (640, .37, 9, '#44607A'), (440, -.40, 8, '#44607A')]:
        x, y = P(rr * s, base + da)
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rad*s:.0f}" fill="{col}"/>')
    # 金色小回箭：从亮点右侧出发，绕一个小圈，箭头指回亮点
    c0 = (fx + 170 * s, fy - 10 * s)
    pts = [bez((fx + 70 * s, fy - 80 * s), (fx + 330 * s, fy - 230 * s), (fx + 380 * s, fy + 190 * s), (fx + 90 * s, fy + 70 * s), k / 40) for k in range(41)]
    d = 'M' + ' L'.join('%.1f %.1f' % q for q in pts)
    out.append(f'<path d="{d}" fill="none" stroke="{GOLD2}" stroke-width="{9*s:.1f}" stroke-linecap="round"/>')
    ex, ey = pts[-1]; qx, qy = pts[-5]
    ang = math.atan2(ey - qy, ex - qx); hl = 38 * s
    h1 = (ex - hl * math.cos(ang - .5), ey - hl * math.sin(ang - .5))
    h2 = (ex - hl * math.cos(ang + .5), ey - hl * math.sin(ang + .5))
    out.append(f'<path d="M{h1[0]:.1f} {h1[1]:.1f} L{ex:.1f} {ey:.1f} L{h2[0]:.1f} {h2[1]:.1f}" fill="none" stroke="{GOLD2}" stroke-width="{9*s:.1f}" stroke-linecap="round" stroke-linejoin="round"/>')
    # 起点金点
    out.append(f'<circle cx="{pts[0][0]:.0f}" cy="{pts[0][1]:.0f}" r="{12*s:.0f}" fill="{GOLD}"/>')
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
<div class="t"><div class="big">彩超医生会被<br>AI替代吗？</div>
<div class="sub">{M.SUBTITLE}</div><div class="rule"></div><div class="sm">{M.COVER_SMALL}</div></div>
<div class="b"><div class="au">{M.AUTHOR}　著</div><div class="ad">{M.ADVISOR}　指导</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div>
</div></body></html>"""


def back(Wmm, Hmm, F):
    W, H = Wmm * 10, Hmm * 10
    s = Wmm / 170
    # 右上小徽：一小段扇形
    ex, ey = W * 0.84, H * 0.06
    r = 120 * s
    a0, a1 = math.radians(50), math.radians(130)
    p0 = (ex + r * math.cos(a0), ey + r * math.sin(a0)); p1 = (ex + r * math.cos(a1), ey + r * math.sin(a1))
    emb = (f'<path d="M{ex:.0f} {ey:.0f} L{p0[0]:.0f} {p0[1]:.0f} A{r:.0f} {r:.0f} 0 0 1 {p1[0]:.0f} {p1[1]:.0f} Z" fill="{CYAN}" fill-opacity=".14" stroke="{GOLD}" stroke-opacity=".7" stroke-width="{2.5*s:.1f}" stroke-linejoin="round"/>'
           f'<circle cx="{ex:.0f}" cy="{ey+r*0.62:.0f}" r="{9*s:.1f}" fill="{CREAM}"/><circle cx="{ex:.0f}" cy="{ey:.0f}" r="{8*s:.1f}" fill="{GOLD}"/>')
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
<div class="q">会被替代的，不是彩超医生，<br>而是只看图下结论的单点做法。</div><div class="rule"></div>
<div class="bl"><p>本书讲线索怎样随着扫查一步步冒出来，又怎样被放回病人的全部其他情况里去定位。</p>
<p>本书讲医生与AI各自守住哪一格，哪一格是责任与信任，至今还没有发生。</p>
<p>本书不开诊断标准，不列数据，不给结论清单。</p></div>
<div class="gold">本书不作诊断，不替代医生判断。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 {M.NO} 号 · {M.AUTHOR}　著 · {M.ADVISOR}　指导<br>ISBN {M.ISBN} · 定价 {M.PRICE}</div>
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
