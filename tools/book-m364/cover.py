#!/usr/bin/env python3
"""《AI赋能了谁？》封面与封底（工具由第 403 号改来，照第 220 号系列版式）：藏青渐变底、细点阵、金色光晕与刻度环；
主图是一只姿态仪：天与地的分界斜着，机翼标志却觉得自己是平的（仪表区）；右上两块小仪表的指针打架；
台下一串奶白的脚印走着走着，变成了两道金色的车辙（汽车没有赋能双腿）。
"""
import argparse
import os
import math
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0B1830', '#1B3158', '#142746'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#58BDCA', '#EFE8D6', '#9FB0C8'
ISBN = '979-8-90690-975-6'
WAN = os.environ.get('WAN', '20')
NO = '第 364 号'
PRICE = 'US$23.00'

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
<defs>
 <linearGradient id="bg{uid}" x1="0" y1="0" x2="0.35" y2="1">
  <stop offset="0" stop-color="{NAVY_TOP}"/><stop offset=".58" stop-color="{NAVY_MID}"/><stop offset="1" stop-color="{NAVY_LOW}"/></linearGradient>
 <radialGradient id="halo{uid}" cx=".5" cy=".5" r=".5">
  <stop offset="0" stop-color="{GOLD2}" stop-opacity=".30"/><stop offset=".45" stop-color="{GOLD}" stop-opacity=".12"/>
  <stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></radialGradient>
 <linearGradient id="kite{uid}" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="{CREAM}" stop-opacity=".95"/><stop offset="1" stop-color="{GOLD}" stop-opacity=".85"/></linearGradient>
 <linearGradient id="handle{uid}" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#B89A5E"/><stop offset=".45" stop-color="{CREAM}"/><stop offset="1" stop-color="#A88C55"/></linearGradient>
 <linearGradient id="line{uid}" x1="0" y1="1" x2="1" y2="0">
  <stop offset="0" stop-color="{GOLD}"/><stop offset="1" stop-color="{GOLD2}"/></linearGradient>
</defs>
<rect width="{W}" height="{H}" fill="url(#bg{uid})"/>
<g fill="{DIM}" fill-opacity=".10">{''.join(dots)}</g>"""


def rings(cx, cy, r):
    ticks = []
    for k in range(72):
        a = k * math.pi * 2 / 72
        r1 = r * (1.035 if k % 6 else 1.06)
        ticks.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (
            cx + r * math.cos(a), cy + r * math.sin(a), cx + r1 * math.cos(a), cy + r1 * math.sin(a)))
    return f"""
<circle cx="{cx}" cy="{cy}" r="{r*1.55:.0f}" fill="url(#halo{{uid}})"/>
<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{GOLD}" stroke-opacity=".55" stroke-width="2.2"/>
<circle cx="{cx}" cy="{cy}" r="{r*1.10:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".22" stroke-width="1.2"/>
<circle cx="{cx}" cy="{cy}" r="{r*0.62:.0f}" fill="none" stroke="{CYAN}" stroke-opacity=".16" stroke-width="1.2" stroke-dasharray="3 9"/>
<g stroke="{GOLD}" stroke-opacity=".45" stroke-width="1.6">{''.join(ticks)}</g>"""


def art(W, H, uid):
    """主图：姿态仪（斜着的地平线、自以为平的机翼）、两块打架的小仪表、脚印变车辙。"""
    s = W / 1700
    cx, cy, r = W * 0.58, H * 0.60, 520 * s
    u = r / 450
    out = [rings(cx, cy, r).replace('{uid}', uid)]
    R = 330 * u
    out.append(f'<defs><clipPath id="cl{uid}"><circle cx="{cx:.0f}" cy="{cy:.0f}" r="{R:.0f}"/></clipPath></defs>')
    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{R:.0f}" fill="#13284A" fill-opacity=".62"/>')
    g = [f'<g clip-path="url(#cl{uid})"><g transform="rotate(-16 {cx:.0f} {cy:.0f}) translate(0 {R*0.10:.0f})">']
    g.append(f'<rect x="{cx - 2*R:.0f}" y="{cy - 2*R:.0f}" width="{4*R:.0f}" height="{2*R:.0f}" fill="#2B5288" fill-opacity=".78"/>')
    g.append(f'<rect x="{cx - 2*R:.0f}" y="{cy:.0f}" width="{4*R:.0f}" height="{2*R:.0f}" fill="#7A5C2A" fill-opacity=".70"/>')
    g.append(f'<line x1="{cx - 2*R:.0f}" y1="{cy:.0f}" x2="{cx + 2*R:.0f}" y2="{cy:.0f}" stroke="{CREAM}" stroke-width="{6*s:.1f}"/>')
    for k in (-3, -2, -1, 1, 2, 3):
        w = R * (0.34 if k % 2 else 0.20)
        yy = cy - k * R * 0.17
        g.append(f'<line x1="{cx - w:.0f}" y1="{yy:.0f}" x2="{cx + w:.0f}" y2="{yy:.0f}" stroke="{CREAM}" stroke-opacity=".55" stroke-width="{3*s:.1f}"/>')
    g.append('</g>')
    # 刻度弧：上沿的倾斜刻度
    for t in range(-60, 61, 10):
        a = math.radians(t - 90)
        r1, r2 = R * 0.86, R * (0.78 if t % 30 else 0.72)
        g.append(f'<line x1="{cx + r1*math.cos(a):.0f}" y1="{cy + r1*math.sin(a):.0f}" x2="{cx + r2*math.cos(a):.0f}" y2="{cy + r2*math.sin(a):.0f}" stroke="{CREAM}" stroke-opacity=".75" stroke-width="{3*s:.1f}"/>')
    g.append('</g>')
    out += g
    # 固定的机翼标志：它觉得自己是平的
    ww = R * 0.42
    out.append(f'<path d="M{cx - ww:.0f} {cy:.0f} L{cx - R*0.12:.0f} {cy:.0f} L{cx:.0f} {cy + R*0.09:.0f} L{cx + R*0.12:.0f} {cy:.0f} L{cx + ww:.0f} {cy:.0f}" fill="none" stroke="{GOLD2}" stroke-width="{11*s:.1f}" stroke-linejoin="round" stroke-linecap="round"/>')
    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{R*0.035:.0f}" fill="{GOLD2}"/>')
    # 右上两块小仪表，指针打架
    for k, (dx, dy, ang, col) in enumerate(((1.12, -0.98, -35, GOLD2), (1.12, -0.38, 55, CYAN))):
        x, y, rr = cx + R*dx, cy + R*dy, R * 0.25
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rr:.0f}" fill="#0F2240" fill-opacity=".85" stroke="{GOLD}" stroke-opacity=".7" stroke-width="{3*s:.1f}"/>')
        for t in range(0, 360, 30):
            a = math.radians(t)
            out.append(f'<line x1="{x + rr*0.80*math.cos(a):.0f}" y1="{y + rr*0.80*math.sin(a):.0f}" x2="{x + rr*0.92*math.cos(a):.0f}" y2="{y + rr*0.92*math.sin(a):.0f}" stroke="{CREAM}" stroke-opacity=".5" stroke-width="{2*s:.1f}"/>')
        a = math.radians(ang - 90)
        out.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x + rr*0.72*math.cos(a):.0f}" y2="{y + rr*0.72*math.sin(a):.0f}" stroke="{col}" stroke-width="{6*s:.1f}" stroke-linecap="round"/>')
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rr*0.09:.0f}" fill="{col}"/>')
    # 脚印走着走着，变成两道车辙
    by = cy + R * 1.33
    for k in range(5):
        x = cx - R * 1.05 + k * R * 0.22
        y = by + (R * 0.05 if k % 2 else -R * 0.05)
        out.append(f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{R*0.055:.0f}" ry="{R*0.024:.0f}" fill="{CREAM}" fill-opacity="{.35 + .12*k:.2f}"/>')
    x0 = cx - R * 0.02
    for dy, op in ((-R * 0.06, .9), (R * 0.06, .6)):
        out.append(f'<path d="M{x0:.0f} {by + dy:.0f} C{cx + R*0.5:.0f} {by + dy:.0f} {cx + R*0.9:.0f} {by + dy*1.6:.0f} {cx + R*1.25:.0f} {by + dy*2.4 - R*0.05:.0f}" fill="none" stroke="{GOLD}" stroke-opacity="{op}" stroke-width="{7*s:.1f}" stroke-linecap="round"/>')
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · {NO}</div>
<div class="t"><div class="pre">思考换了主语</div><div class="big">AI赋能了谁？</div>
<div class="sub">拆开“AI赋能大脑”的六种主流说法</div><div class="rule"></div></div>
<div class="b"><div class="au">王德生　著</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div>
</div></body></html>"""


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
           f'{background(W, H, "b")}{emb}{"".join(waves)}{bc}</svg>')
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
<div class="c"><div class="lab">判 词</div>
<div class="q">汽车没有赋能双腿，<br>AI也没有赋能大脑。<br>思考，换了主语。</div><div class="by">——本书判词</div><div class="rule"></div>
<div class="bl"><p>「汽车赋能双腿」谁听了都别扭，「AI赋能大脑」却人人顺口。可这个词先预设了一个现成的大脑，等着被加能；真正在思考的，已经是大脑与AI缠在一起的复合思考体。</p>
<p>本书拆开六种主流说法：增强论、外脑论、驾驭论、分工论、解放论、退化论。每一种先替它把话说足，再找出那一刀切在哪里，最后承认它对的那一半。最乐观的和最悲观的两派，用的是同一本按个人大脑记的账。</p>
<p>拆完之后立：复合思考体成立的条件、判断义务表，以及从飞行员仪表飞行借来的核心构念「仪表区」。凡是本书自己立的说法，都写明了怎样才算错。</p></div>
<div class="gold">先列判断，再找承担者。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著 {NO} · 五编三十八章 · 约 {WAN} 万字<br>定价 {PRICE}</div>
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
