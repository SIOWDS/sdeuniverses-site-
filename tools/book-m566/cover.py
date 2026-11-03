#!/usr/bin/env python3
"""第 566 号《本末发生学》（王德生、陈晓艳 合著）封面与封底（工具链承自第 564 号；靛青底，金、青绿点缀，220 系列版式）：
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
    """主图（第 566 号《本末发生学》）：地面上一棵树（末），叶子一片片落下，落到地下沉成一层层土（本）；
    土层越往下越厚，最底一层是实金的「本」；一支金色回箭从底层折回地面——追认：「本来如此」。
    底层是表层沉出来的。全部纯色，不用渐变。"""
    import random
    rnd = random.Random(566)
    s = W / 1700
    out = []
    cx, y0 = W * 0.56, H * 0.585          # 树根所在的地面
    # ── 地下的土层：越深越厚，颜色由淡到金 ──
    bands = [(0.000, 0.030, CREAM, .10), (0.030, 0.068, CREAM, .16), (0.068, 0.115, GOLD, .28),
             (0.115, 0.172, GOLD, .46), (0.172, 0.240, GOLD, .95)]
    x0, x1 = W * 0.16, W * 0.94
    for k, (a, b, col, op) in enumerate(bands):
        ya, yb = y0 + a * H, y0 + b * H
        d = 'M%.0f %.0f' % (x0, ya)
        n = 10
        for i in range(n):
            xa = x0 + (x1 - x0) * (i + .5) / n; xb = x0 + (x1 - x0) * (i + 1) / n
            d += ' Q%.0f %.0f %.0f %.0f' % (xa, ya + (7 if (i + k) % 2 else -7) * s, xb, ya)
        d += ' L%.0f %.0f L%.0f %.0f Z' % (x1, yb, x0, yb)
        out.append(f'<path d="{d}" fill="{col}" fill-opacity="{op}"/>')
    # 土层里的沉积颗粒（越深越密）
    for k, (a, b, col, op) in enumerate(bands[:-1]):
        for _ in range(6 + 5 * k):
            px = rnd.uniform(x0 + 20 * s, x1 - 20 * s); py = y0 + rnd.uniform(a, b) * H
            out.append(f'<ellipse cx="{px:.0f}" cy="{py:.0f}" rx="{rnd.uniform(5, 10)*s:.1f}" ry="{rnd.uniform(2, 4)*s:.1f}" fill="{CREAM}" fill-opacity=".35"/>')
    yb_last = y0 + bands[-1][0] * H
    out.append(f'<text x="{x0 + 36*s:.0f}" y="{yb_last + 0.044*H:.0f}" font-size="{40*s:.0f}" font-family="Noto Serif CJK SC" font-weight="700" fill="{NAVY_TOP}" letter-spacing="{10*s:.0f}">本</text>')
    # 地面线
    out.append(f'<line x1="{x0:.0f}" y1="{y0:.0f}" x2="{x1:.0f}" y2="{y0:.0f}" stroke="{CREAM}" stroke-opacity=".55" stroke-width="{2.4*s:.1f}"/>')
    # ── 树：主干与枝（末） ──
    trunk = [(cx, y0), (cx - 6 * s, y0 - 120 * s), (cx + 4 * s, y0 - 240 * s), (cx, y0 - 330 * s)]
    pts = [trunk[0]]
    for i in range(1, len(trunk)):
        for t in range(1, 9):
            u = t / 8
            pts.append((trunk[i - 1][0] + (trunk[i][0] - trunk[i - 1][0]) * u, trunk[i - 1][1] + (trunk[i][1] - trunk[i - 1][1]) * u))
    out.append(f'<path d="{tapered(pts, 34*s, 9*s, 1.2)}" fill="{CREAM}" fill-opacity=".92"/>')
    branches = [((cx, y0 - 200 * s), (cx - 170 * s, y0 - 360 * s)), ((cx + 2 * s, y0 - 250 * s), (cx + 180 * s, y0 - 390 * s)),
                ((cx, y0 - 300 * s), (cx - 60 * s, y0 - 470 * s)), ((cx, y0 - 320 * s), (cx + 70 * s, y0 - 480 * s))]
    tips = []
    for (p, q) in branches:
        bp = [(p[0] + (q[0] - p[0]) * t / 10, p[1] + (q[1] - p[1]) * t / 10 - 18 * s * math.sin(math.pi * t / 10)) for t in range(11)]
        out.append(f'<path d="{tapered(bp, 13*s, 3*s, 1.3)}" fill="{CREAM}" fill-opacity=".85"/>')
        tips.append(q)
    # 叶（末）：枝头一簇簇
    def leaf(x, y, ang, L, col, op):
        a = math.radians(ang); dx, dy = math.cos(a) * L / 2, math.sin(a) * L / 2
        nx, ny = -math.sin(a) * L * .22, math.cos(a) * L * .22
        return (f'<path d="M{x-dx:.0f} {y-dy:.0f} Q{x+nx:.0f} {y+ny:.0f} {x+dx:.0f} {y+dy:.0f} Q{x-nx:.0f} {y-ny:.0f} {x-dx:.0f} {y-dy:.0f} Z" '
                f'fill="{col}" fill-opacity="{op}"/>')
    for (tx, ty) in tips + [(cx, y0 - 340 * s)]:
        for _ in range(9):
            out.append(leaf(tx + rnd.uniform(-70, 70) * s, ty + rnd.uniform(-55, 45) * s, rnd.uniform(0, 180), rnd.uniform(34, 48) * s,
                            rnd.choice([CYAN, CYAN, GOLD2]), rnd.choice(['.75', '.9'])))
    # 落叶：从枝头落向地面，越落越淡，入土成颗粒
    for i in range(9):
        fx = cx + rnd.uniform(-330, 330) * s
        fy = y0 - rnd.uniform(40, 260) * s
        out.append(leaf(fx, fy, rnd.uniform(0, 180), 30 * s, GOLD2, '.8'))
        for j in range(1, 6):
            out.append(f'<circle cx="{fx + rnd.uniform(-6, 6)*s:.0f}" cy="{y0 + j * 0.028 * H:.0f}" r="{(4.2 - .5*j)*s:.1f}" fill="{CREAM}" fill-opacity="{.6 - .09*j:.2f}"/>')
    # 根：伸进土层
    for ang in (-150, -115, -65, -30):
        a = math.radians(-ang)
        rp = [(cx + math.cos(a) * r * s * 1.4, y0 + math.sin(a) * r * s * .9) for r in range(0, 200, 20)]
        out.append(f'<path d="{tapered(rp, 12*s, 2*s, 1.1)}" fill="{CREAM}" fill-opacity=".55"/>')
    # ── 追认：金色回箭从底层折回地面 ──
    ax = W * 0.86
    ya, yt = y0 + 0.205 * H, y0 - 24 * s
    out.append(f'<path d="M{ax:.0f} {ya:.0f} L{ax:.0f} {yt + 30*s:.0f}" fill="none" stroke="{GOLD2}" stroke-width="{6*s:.1f}" stroke-dasharray="{18*s:.0f} {10*s:.0f}"/>')
    out.append(f'<path d="M{ax - 20*s:.0f} {yt + 34*s:.0f} L{ax:.0f} {yt:.0f} L{ax + 20*s:.0f} {yt + 34*s:.0f} Z" fill="{GOLD2}"/>')
    out.append(f'<text x="{ax + 24*s:.0f}" y="{yt - 20*s:.0f}" font-size="{24*s:.0f}" text-anchor="end" font-family="Noto Sans CJK SC" fill="{GOLD2}" letter-spacing="{4*s:.0f}">追认：「本来如此」</text>')
    out.append(f'<text x="{x0:.0f}" y="{y0 - 18*s:.0f}" font-size="{22*s:.0f}" font-family="Noto Sans CJK SC" fill="{DIM}" letter-spacing="{4*s:.0f}">做 · 沉 · 成本 · 守</text>')
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
<div class="t"><div class="pre">三书缝隙集 · SDE 发生学</div><div class="big">{M.TITLE}</div>
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
<div class="q">本是做出来的；<br>底层是表层沉出来的。</div><div class="by">——本书母题</div><div class="rule"></div>
<div class="bl"><p>外婆捏一捏你的手，说一句「底子寒」，熬一碗姜汤：底子在先，汤在后。本书并读三部把「本」说得最认真的书——《黄帝内经》的体质与正气，《论语》的仁与人心的想要，涂尔干的社会与信仰——发现三家都只给做法留了三种用处：守住本，找回本，表达本，没有一家让做法去造本。</p>
<p>三家自己的材料却都露出了反面：「脱营」的病人，欲罢不能的颜回，先哭、后怕的哀悼者。由此立本末律：做，沉，成本，守；本每变一次，新本都被说成「回到本来」。判死条款三条，写在看材料之前。</p>
<p>再把律放进身体、孩子、家与单位，放进饥饿冬天、出租车司机与免疫的研究，放进真、善、美。</p></div>
<div class="gold">务本，就是造本。</div></div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 {M.NO} 号 · 前言、导论、七编三十三章、结语 · 约 {WAN} 万字<br>ISBN {M.ISBN} · 定价 {M.PRICE}</div>
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
