#!/usr/bin/env python3
"""第 525 号《先到一步》（张琼 著）封面与封底（工具链承自第 582 号，藏青底、金青奶白三色，220 系列版式）：
主图：弯路上的脚印还没走到岔口，金色路标已先立在那里。全部纯色，不用渐变。
用法：python3 cover.py --fonts /usr/share/fonts/opentype/noto --out <dir>
"""
import argparse
import math
import os
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0C1A34', '#1B3158', '#16294A'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#7FA7C9', '#EFE8D6', '#A9B6C8'
ISBN = '979-8-90690-611-3'
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
    """主图（第 525 号）：先到一步。一行奶白脚印从左下沿弯路往上走，还没走到岔口；
    岔口上方已经先立着一只金色路标箭头，箭头指向的那条直路被它照亮成金线。脚印走过的地方，路面是自己的；
    路标前方的路面是事先画好的。下方一道金色地平线。全部纯色，不用渐变。"""
    s = W / 1700
    o = []
    wall_y, top_y = H * 0.40, H * 0.80
    o.append(f'<rect y="{wall_y:.0f}" width="{W}" height="{H-wall_y:.0f}" fill="{NAVY_MID}"/>')
    # 弯路（亲历走出的路）：一条三次曲线，奶白虚线作路肩
    P0, P1, P2, P3 = (W * 0.10, H * 0.78), (W * 0.42, H * 0.76), (W * 0.18, H * 0.58), (W * 0.52, H * 0.52)
    pts = [bez(P0, P1, P2, P3, k / 60) for k in range(61)]
    o.append('<path d="M%s" fill="none" stroke="%s" stroke-opacity=".35" stroke-width="%.1f" stroke-linecap="round"/>' % (' L'.join('%.1f %.1f' % q for q in pts), DIM, 46 * s))
    # 脚印：左右交替，只走到曲线的 70%，越往前越淡
    n = 15
    for k in range(n):
        tt = 0.04 + 0.66 * k / (n - 1)
        x, y = bez(P0, P1, P2, P3, tt)
        x2, y2 = bez(P0, P1, P2, P3, min(tt + 0.01, 1))
        ang = math.degrees(math.atan2(y2 - y, x2 - x)) + 90
        side = 1 if k % 2 else -1
        ox, oy = side * 13 * s * math.cos(math.radians(ang - 90)), side * 13 * s * math.sin(math.radians(ang - 90))
        op = 0.95 - 0.5 * k / (n - 1)
        o.append(f'<ellipse cx="{x+ox:.0f}" cy="{y+oy:.0f}" rx="{7*s:.1f}" ry="{12*s:.1f}" transform="rotate({ang:.0f} {x+ox:.0f} {y+oy:.0f})" fill="{CREAM}" fill-opacity="{op:.2f}"/>')
    # 事先画好的直路：从岔口直射右上，金线
    jx, jy = P3
    o.append(f'<line x1="{jx:.0f}" y1="{jy:.0f}" x2="{W*0.96:.0f}" y2="{H*0.43:.0f}" stroke="{GOLD}" stroke-width="{7*s:.1f}" stroke-linecap="round"/>')
    o.append(f'<line x1="{jx:.0f}" y1="{jy:.0f}" x2="{W*0.96:.0f}" y2="{H*0.43:.0f}" stroke="{GOLD2}" stroke-opacity=".25" stroke-width="{40*s:.1f}" stroke-linecap="round"/>')
    # 岔口上的路标：立柱＋金色箭头牌（先到的那一步）
    px, py0, py1 = jx + 40 * s, jy - 230 * s, jy + 6 * s
    o.append(f'<rect x="{px-5*s:.0f}" y="{py0:.0f}" width="{10*s:.0f}" height="{py1-py0:.0f}" fill="{CREAM}"/>')
    ax, ay, aw, ah = px - 10 * s, py0 + 10 * s, 250 * s, 64 * s
    o.append(f'<path d="M{ax:.0f} {ay:.0f} L{ax+aw:.0f} {ay:.0f} L{ax+aw+40*s:.0f} {ay+ah/2:.0f} L{ax+aw:.0f} {ay+ah:.0f} L{ax:.0f} {ay+ah:.0f} Z" fill="{GOLD2}"/>')
    o.append(f'<circle cx="{ax+34*s:.0f}" cy="{ay+ah/2:.0f}" r="{9*s:.0f}" fill="{NAVY_TOP}"/>')
    # 地平线
    o.append(f'<rect y="{top_y:.0f}" width="{W}" height="{18*s:.0f}" fill="{GOLD}"/>')
    o.append(f'<rect y="{top_y+18*s:.0f}" width="{W}" height="{H-top_y-18*s:.0f}" fill="{NAVY_LOW}"/>')
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 525 号</div>
<div class="t"><div class="big">先到一步</div>
<div class="sub">清晰、代理与被提前做完的发生</div><div class="rule"></div></div>
<div class="b"><div class="au">张琼　著</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div>
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
<div class="q" style="font-size:{13.2*s:.1f}pt">同样是硬东西，<br>落在亲历之后是骨骼，<br>落在亲历之前是假体。</div><div class="rule"></div>
<div class="bl"><p>手环说你睡得很好，你醒来却觉得很累；导航每个路口都比你早半秒，十年后你离了它不认路；一篇论文把田野里的困境命名得精确无误，写它的人却从未被那困境夹住过。这本书说，这些都是同一件事：清晰抢在亲历之前到场，就替人把该亲身发生的事提前做完了。它越准、越无痛、越体面，那件事就越不再发生。</p>
<p>全书四编十六章：身体里，读数先于感受；学者那里，命名先于被田野改变；制度里，格式先于“是真是假”，符号先于差异；第四编写另一极：清晰不抢先时，接续、试探、切割与沉淀怎样长成骨骼。病根不在缺少清晰，在清晰来得太早；刀口不在软硬，在先后。</p>
<p>这是一部学术专著初版：由作者十六篇论文熔铸，正文由 AI（Claude）协作重写，经统稿与三审，没有经过独立学术评审。全书写明了自己在什么情况下就错了，三条证伪纲领都还没有真跑。</p>
<div class="gold">清晰到场之前，先问一句：该亲历的人，亲历过了吗？</div></div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 525 号 · 四编十六章 · 约 {WAN} 万字<br>ISBN 979-8-90690-611-3 · 定价 US$20.00</div>
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
