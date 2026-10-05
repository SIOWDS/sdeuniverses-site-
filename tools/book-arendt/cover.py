#!/usr/bin/env python3
"""第 284 号封面与封底：藏青底、细点阵、金色光晕与刻度环；主图是一扇门，门缝漏出一道光，
落在地上，散成六条路。

用法：python3 cover.py --fonts /tmp/fonts --out /tmp/laozi-build
产物：cover-print.pdf / back-print.pdf（170×240）、cover-reader.pdf / back-reader.pdf（190×250）、
      cover.jpg / backcover.jpg（1004×1418，站上用）
"""
import argparse
import math
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0B1830', '#1B3158', '#142746'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#58BDCA', '#EFE8D6', '#9FB0C8'
ISBN = '979-8-90690-899-5'

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
    """主图：一台打字机，滚筒上夹着一张几乎空白的纸，只有一行标题和两行题词；纸上方留一圈光。"""
    s = W / 1700
    cx, cy, r = W * 0.57, H * 0.585, 520 * s
    out = [rings(cx, cy, r).replace('{uid}', uid)]
    DOOR = '#0A1428'
    # 纸
    px0, px1, ptop, pbot = cx - 170 * s, cx + 170 * s, cy - 470 * s, cy - 60 * s
    out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" fill-opacity=".97"/>' % (px0, ptop, px1 - px0, pbot - ptop, CREAM))
    out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#1F3A5F"/>' % (cx - 70 * s, ptop + 62 * s, 140 * s, 15 * s))
    for k, w in enumerate((200, 150)):
        out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#1F3A5F" fill-opacity=".45"/>' % (cx - w / 2 * s, ptop + 120 * s + k * 30 * s, w * s, 7 * s))
    out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>' % (cx - 14 * s, ptop + 215 * s, 28 * s, 5 * s, GOLD))
    # 滚筒
    out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%.1f" fill="%s" stroke="%s" stroke-width="%.1f"/>' % (cx - 270 * s, cy - 92 * s, 540 * s, 56 * s, 28 * s, DOOR, GOLD2, 2.4 * s))
    for dx in (-292, 292):
        out.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" stroke="%s" stroke-width="%.1f"/>' % (cx + dx * s, cy - 64 * s, 26 * s, '#142746', GOLD, 2.4 * s))
    # 机身
    body = 'M%.1f %.1f L%.1f %.1f L%.1f %.1f L%.1f %.1f Z' % (cx - 300 * s, cy - 36 * s, cx + 300 * s, cy - 36 * s, cx + 360 * s, cy + 250 * s, cx - 360 * s, cy + 250 * s)
    out.append('<path d="%s" fill="%s" stroke="%s" stroke-opacity=".8" stroke-width="%.1f"/>' % (body, DOOR, GOLD, 2.4 * s))
    # 键
    for row, (n, y, x0, gap) in enumerate([(9, 70, -220, 55), (8, 130, -195, 55), (7, 190, -165, 55)]):
        for i in range(n):
            out.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="%s" stroke-opacity=".75" stroke-width="%.1f"/>' % (cx + (x0 + i * gap) * s, cy + y * s, 19 * s, GOLD2 if (i + row) % 3 else CYAN, 2 * s))
    out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%.1f" fill="none" stroke="%s" stroke-opacity=".6" stroke-width="%.1f"/>' % (cx - 120 * s, cy + 215 * s, 240 * s, 22 * s, 11 * s, GOLD, 2 * s))
    out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-opacity=".5" stroke-width="%.1f"/>' % (cx - 420 * s, cy + 262 * s, cx + 420 * s, cy + 262 * s, GOLD, 2 * s))
    return ''.join(out)


def barcode(x, y, s):
    d, bits = ean13_bits(ISBN)
    mw = 3.3 * s  # 模块宽
    h = 190 * s
    rects = []
    for i, b in enumerate(bits):
        if b == '1':
            guard = i < 3 or 45 <= i < 50 or i >= 92
            rects.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#111"/>' % (x + 22 * s + i * mw, y + 40 * s, mw + .2, h + (18 * s if guard else 0)))
    bw = 95 * mw + 44 * s
    txt = (f'<text x="{x + bw/2:.0f}" y="{y + 30*s:.0f}" font-size="{19*s:.0f}" text-anchor="middle" font-family="BH" fill="#111">ISBN {ISBN}</text>'
           f'<text x="{x + 8*s:.0f}" y="{y + 40*s + h + 36*s:.0f}" font-size="{26*s:.0f}" font-family="BS" fill="#111">{d[0]}</text>'
           f'<text x="{x + 22*s + 3*mw + 21*mw:.0f}" y="{y + 40*s + h + 36*s:.0f}" font-size="{26*s:.0f}" text-anchor="middle" letter-spacing="{9*s:.0f}" font-family="BS" fill="#111">{d[1:7]}</text>'
           f'<text x="{x + 22*s + 50*mw + 21*mw:.0f}" y="{y + 40*s + h + 36*s:.0f}" font-size="{26*s:.0f}" text-anchor="middle" letter-spacing="{9*s:.0f}" font-family="BS" fill="#111">{d[7:]}</text>')
    return (f'<rect x="{x:.0f}" y="{y:.0f}" width="{bw:.0f}" height="{h + 110*s:.0f}" fill="#fff"/>' + ''.join(rects) + txt), bw


def fontface(F):
    return f"""@font-face{{font-family:BS;src:url(file://{F}/NotoSerifSC-Regular.ttf);font-weight:400}}
@font-face{{font-family:BS;src:url(file://{F}/NotoSerifSC-Bold.ttf);font-weight:700}}
@font-face{{font-family:BH;src:url(file://{F}/NotoSansSC-Regular.ttf);font-weight:400}}
@font-face{{font-family:BH;src:url(file://{F}/NotoSansSC-Bold.ttf);font-weight:700}}"""


def front(Wmm, Hmm, F):
    W, H = Wmm * 10, Hmm * 10
    s = Wmm / 170
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{Wmm}mm" height="{Hmm}mm">{background(W, H, "f")}{art(W, H, "f")}</svg>'
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{fontface(F)}
@page{{size:{Wmm}mm {Hmm}mm;margin:0}} body{{margin:0}}
.pg{{position:relative;width:{Wmm}mm;height:{Hmm}mm;overflow:hidden}}
.pg svg{{position:absolute;left:0;top:0}}
.t{{position:absolute;left:{17*s:.1f}mm;top:{22*s:.1f}mm;color:{CREAM}}}
.pre{{font:400 {11.5*s:.1f}pt BS;letter-spacing:.32em;color:{CREAM};opacity:.92}}
.big{{font:700 {46*s:.1f}pt/1.25 BS;letter-spacing:.08em;color:#F7F1E3;margin:{2*s:.1f}mm 0 {3*s:.1f}mm {-1*s:.1f}mm}}
.sub{{font:400 {10.6*s:.1f}pt/1.75 BS;color:{GOLD2};letter-spacing:.04em}}
.rule{{width:{16*s:.1f}mm;border-top:.9pt solid {GOLD};margin-top:{5*s:.1f}mm}}
.b{{position:absolute;left:{17*s:.1f}mm;bottom:{17*s:.1f}mm}}
.au{{font:400 {12.5*s:.1f}pt BS;color:{CREAM};letter-spacing:.28em}}
.ph{{font:700 {8.4*s:.1f}pt BH;color:{GOLD2};letter-spacing:.3em;margin-top:{6*s:.1f}mm}}
.pe{{font:400 {6.6*s:.1f}pt BH;color:{DIM};letter-spacing:.08em;margin-top:{.8*s:.1f}mm}}
.no{{position:absolute;right:{15*s:.1f}mm;top:{16*s:.1f}mm;font:400 {6.6*s:.1f}pt BH;color:{DIM};letter-spacing:.2em;text-align:right}}
</style></head><body><div class="pg">{svg}
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 284 号</div>
<div class="t"><div class="pre">普通人都能明白的</div><div class="big">阿伦特</div>
<div class="sub">一个人、打字机上的一页纸，<br>与 SDE 的解构</div><div class="rule"></div></div>
<div class="b"><div class="au">王德生　著</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div>
</div></body></html>"""


def back(Wmm, Hmm, F):
    W, H = Wmm * 10, Hmm * 10
    s = Wmm / 170
    # 右上小徽：环＋小风筝
    ex, ey, er = W * 0.84, H * 0.085, 70 * s
    emb = f"""<circle cx="{ex:.0f}" cy="{ey:.0f}" r="{er:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".6" stroke-width="{2*s:.1f}"/>
<circle cx="{ex:.0f}" cy="{ey:.0f}" r="{er*1.18:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".22" stroke-width="{1.2*s:.1f}"/>
<rect x="{ex-30*s:.0f}" y="{ey-46*s:.0f}" width="{60*s:.0f}" height="{92*s:.0f}" fill="#0A1428" stroke="{GOLD2}" stroke-width="{1.6*s:.1f}"/>
<rect x="{ex-2.5*s:.0f}" y="{ey-46*s:.0f}" width="{5*s:.0f}" height="{92*s:.0f}" fill="{GOLD2}"/>"""
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
.lab{{font:700 {7.4*s:.1f}pt BH;color:{GOLD2};letter-spacing:.5em}}
.q{{font:700 {15.5*s:.1f}pt/1.75 BS;color:#F7F1E3;margin:{4*s:.1f}mm 0 {2*s:.1f}mm;letter-spacing:.04em}}
.by{{font:400 {8.2*s:.1f}pt BS;color:{DIM}}}
.rule{{width:{14*s:.1f}mm;border-top:.9pt solid {GOLD};margin:{7*s:.1f}mm 0 {6*s:.1f}mm}}
.bl p{{font:400 {8.8*s:.1f}pt/1.9 BS;color:{CREAM};opacity:.9;margin:0 0 {2.6*s:.1f}mm;text-align:justify}}
.gold{{font:700 {10.5*s:.1f}pt BS;color:{GOLD2};margin-top:{6*s:.1f}mm;letter-spacing:.06em}}
.f{{position:absolute;left:{17*s:.1f}mm;bottom:{17*s:.1f}mm;font:400 {7.2*s:.1f}pt/1.85 BH;color:{DIM}}}
.f b{{color:{CREAM};font-weight:700;letter-spacing:.12em}}
</style></head><body><div class="pg">{svg}
<div class="c"><div class="lab">一 页 纸</div>
<div class="q">1975 年，打字机里<br>只有一页纸。</div><div class="by">——《心智生命》第三卷“判断”</div><div class="rule"></div>
<div class="bl"><p>阿伦特去世时，打字机上只有标题和两句题词。她一生被推出桌子好几次：被拘押，失去国籍，关进营地；每一次她都先开了口，再长出新的桌子。</p>
<p>她看见每个人都是世界的新来者，随时能开头，却把开头写成一次次的奇迹。可开头为什么有时一下就来，有时一等就是一个月？电梯坏了，没人吭声；有人站出来修好，下一次，别人会不会更容易开口？</p>
<p>本书从饭桌、电梯、一封没写完的信讲起，把她讲明白，再问一个小问题：开头，怎样才能攒下来？也写明它怎样会错。</p></div>
<div class="gold">开头，能不能攒？</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 284 号 · 十一编五十四章 · 约 20 万字<br>定价 US$20.00</div>
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
