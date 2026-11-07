#!/usr/bin/env python3
"""第 569 号《SDE思想创新法导论》（王德生 著）封面与封底（工具链承自第 564 号；靛青底，金、青绿点缀，220 系列版式）：
主图：一棵树的叶子落下，入土沉成一层层土，最底一层是金色的「本」；金色回箭——追认。全部纯色，不用渐变。
封面不写「指导」一类字样（本书是合著）。
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
WAN = os.environ.get('WAN', '29')

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
    """主图（第 604 号）：三个互相咬合的圆——混沌态、介生态、秩序态，同时在场；中心金圆「发生」；
    外圈金环上一段回箭＝回写。全部纯色，不用渐变。"""
    s = W / 1700
    cx, cy = W * 0.5, H * 0.665
    r, d = 255 * s, 150 * s
    out = []
    R = 560 * s
    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{R*1.07:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".18" stroke-width="{2*s:.1f}"/>')
    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{R:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".5" stroke-width="{3*s:.1f}"/>')
    # 回写：外圈上一段金色回箭（从右侧绕到上方，指回中心的方向）
    t0, t1 = math.radians(-20), math.radians(-150)
    pts = [(cx + R * math.cos(t0 + (t1 - t0) * k / 40), cy + R * math.sin(t0 + (t1 - t0) * k / 40)) for k in range(41)]
    out.append('<path d="M' + ' L'.join('%.1f %.1f' % q for q in pts) + f'" fill="none" stroke="{GOLD2}" stroke-width="{8*s:.1f}" stroke-linecap="round"/>')
    ex, ey = pts[-1]; px, py = pts[-4]
    ang = math.atan2(ey - py, ex - px); hl = 30 * s
    h1 = (ex - hl * math.cos(ang - .45), ey - hl * math.sin(ang - .45)); h2 = (ex - hl * math.cos(ang + .45), ey - hl * math.sin(ang + .45))
    out.append(f'<path d="M{h1[0]:.1f} {h1[1]:.1f} L{ex:.1f} {ey:.1f} L{h2[0]:.1f} {h2[1]:.1f}" fill="none" stroke="{GOLD2}" stroke-width="{8*s:.1f}" stroke-linecap="round" stroke-linejoin="round"/>')
    mx, my = cx + (R + 62 * s) * math.cos(math.radians(-85)), cy + (R + 62 * s) * math.sin(math.radians(-85))
    out.append(f'<text x="{mx:.0f}" y="{my:.0f}" font-size="{30*s:.0f}" text-anchor="middle" font-family="Noto Sans CJK SC" fill="{GOLD2}" letter-spacing="{14*s:.0f}">回写</text>')
    # 三个圆：秩序态在上，介生态右下，混沌态左下
    spec = [('秩序态', '站稳，可命名', -90, CREAM), ('介生态', '冒头，又沉下', 30, GOLD2), ('混沌态', '涌动的差异', 150, CYAN)]
    for name, sub, ang, col in spec:
        t = math.radians(ang)
        x, y = cx + d * math.cos(t), cy + d * math.sin(t)
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.0f}" fill="{col}" fill-opacity=".13" stroke="{col}" stroke-width="{5*s:.1f}"/>')
    for name, sub, ang, col in spec:
        t = math.radians(ang)
        lx, ly = cx + (d + r * 0.62) * math.cos(t), cy + (d + r * 0.62) * math.sin(t)
        out.append(f'<text x="{lx:.0f}" y="{ly:.0f}" font-size="{46*s:.0f}" text-anchor="middle" font-family="Noto Serif CJK SC" font-weight="700" fill="#F7F1E3" letter-spacing="{5*s:.0f}">{name}</text>')
        out.append(f'<text x="{lx:.0f}" y="{ly + 40*s:.0f}" font-size="{23*s:.0f}" text-anchor="middle" font-family="Noto Sans CJK SC" fill="{col}" letter-spacing="{3*s:.0f}">{sub}</text>')
    rc = 76 * s
    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{rc:.0f}" fill="{GOLD}"/>')
    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{rc*0.88:.0f}" fill="none" stroke="{NAVY_TOP}" stroke-opacity=".35" stroke-width="{2*s:.1f}"/>')
    out.append(f'<text x="{cx:.0f}" y="{cy + 15*s:.0f}" font-size="{44*s:.0f}" text-anchor="middle" font-family="Noto Serif CJK SC" font-weight="700" fill="{NAVY_TOP}" letter-spacing="{4*s:.0f}">发生</text>')
    # 左下角：九格小图（3 已发生 / 3 正在发生 / 3 未发生，只示意，不标判断）
    gx, gy, cell = W * 0.80, H * 0.875, 34 * s
    tones = [GOLD2, CYAN, DIM, CYAN, GOLD2, DIM, GOLD2, DIM, CYAN]
    for i in range(9):
        rx, ry = gx + (i % 3) * (cell + 8 * s), gy + (i // 3) * (cell + 8 * s)
        filled = i in (0, 4, 6, 1, 3, 8)
        out.append(f'<rect x="{rx:.0f}" y="{ry:.0f}" width="{cell:.0f}" height="{cell:.0f}" rx="{4*s:.0f}" fill="{tones[i] if filled else "none"}" fill-opacity=".75" stroke="{tones[i]}" stroke-width="{2*s:.1f}" stroke-opacity=".8"/>')
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
.big2{{font-size:{34*s:.1f}pt;line-height:1.3;letter-spacing:.06em;margin-top:0}}
.sub{{font:400 {10.6*s:.1f}pt/1.75 'Noto Serif CJK SC';color:{GOLD2};letter-spacing:.04em}}
.rule{{width:{16*s:.1f}mm;border-top:.9pt solid {GOLD};margin-top:{5*s:.1f}mm}}
.b{{position:absolute;left:{17*s:.1f}mm;bottom:{17*s:.1f}mm}}
.au{{font:400 {12.5*s:.1f}pt 'Noto Serif CJK SC';color:{CREAM};letter-spacing:.28em}}
.ph{{font:700 {8.4*s:.1f}pt 'Noto Sans CJK SC';color:{GOLD2};letter-spacing:.3em;margin-top:{6*s:.1f}mm}}
.pe{{font:400 {6.6*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.08em;margin-top:{.8*s:.1f}mm}}
.no{{position:absolute;right:{15*s:.1f}mm;top:{16*s:.1f}mm;font:400 {6.6*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.2em;text-align:right}}
</style></head><body><div class="pg">{svg}
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 {M.NO} 号</div>
<div class="t"><div class="pre">SDE 事实论 · 专著</div><div class="big">事实胜于雄辩</div><div class="big big2">真的还是假的？</div>
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
<div class="q">事实不是被说出来的，<br>是发生的。</div><div class="by">——本书母题</div><div class="rule"></div>
<div class="bl"><p>「事实胜于雄辩」，是真的还是假的？先要问：这个“事实”指哪一种。是说出来的，是摆着的，还是发生的。</p>
<p>前两种，胜的是排序，不是事实。第三种才是真事实，但它的“胜”不是出场赢了，而是通过回写，改了往后每个人开口时的起点。</p>
<p>全书把这句话放进九种条件，一格一格审：有的已经发生，有的正在发生，有的根本还没有发生。</p>
<p>然后走进课堂、诊室、职场、会议室和法庭，看这句老话在五个领域里会怎样出错、又怎样站得住。</p></div>
<div class="gold">真的还是假的？看你说的是哪一种事实。</div></div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 {M.NO} 号 · 前言、导读、八编二十六章、结语 · 约 {WAN} 万字<br>ISBN {M.ISBN} · 定价 {M.PRICE}</div>
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
