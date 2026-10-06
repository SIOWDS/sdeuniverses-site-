#!/usr/bin/env python3
"""第 36 号《人—GPT超级复合智能体》封面与封底。

站上原有的正式封面只有 300 像素宽的立体样书图，初稿内附的封面是单作者旧版、封底条码与定价皆不对，都不能上印刷尺寸。
这里按正式封面的意思（深绿底、电路纹、一条无限纽带、纽带下人—SIO—机三环）重画成矢量，
著者照正式封面署「王德生　秦衡峰」，封底补专著编号、ISBN 条码与定价。拿到正式封面的高清原图后可直接替换。

用法：python3 cover.py --out <out>
产物：cover-print.pdf / back-print.pdf（170×240）、cover-reader.pdf / back-reader.pdf（190×250）、cover.jpg / backcover.jpg
"""
import argparse
import math
import random
import re
from pathlib import Path

ISBN = '978-1-970820-32-4'
NO = 36
G0, G1, G2 = '#0B3B2E', '#11533F', '#1B6B50'
CREAM, GOLD, MINT = '#F4F1E4', '#E4C77A', '#8FE3C0'

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


def barcode(x, y, s):
    d, bits = ean13_bits(ISBN)
    mw, h = 3.3 * s, 190 * s
    rects = []
    for i, b in enumerate(bits):
        if b == '1':
            guard = i < 3 or 45 <= i < 50 or i >= 92
            rects.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#111"/>' % (x + 22 * s + i * mw, y + 40 * s, mw + .2, h + (18 * s if guard else 0)))
    bw = 95 * mw + 44 * s
    yb = y + 40 * s + h + 36 * s
    txt = (f'<text x="{x + bw/2:.0f}" y="{y + 30*s:.0f}" font-size="{19*s:.0f}" text-anchor="middle" font-family="Noto Sans CJK SC" fill="#111">ISBN {ISBN}</text>'
           f'<text x="{x + 8*s:.0f}" y="{yb:.0f}" font-size="{26*s:.0f}" font-family="Noto Serif CJK SC" fill="#111">{d[0]}</text>'
           f'<text x="{x + 22*s + 24*mw:.0f}" y="{yb:.0f}" font-size="{26*s:.0f}" text-anchor="middle" letter-spacing="{9*s:.0f}" font-family="Noto Serif CJK SC" fill="#111">{d[1:7]}</text>'
           f'<text x="{x + 22*s + 71*mw:.0f}" y="{yb:.0f}" font-size="{26*s:.0f}" text-anchor="middle" letter-spacing="{9*s:.0f}" font-family="Noto Serif CJK SC" fill="#111">{d[7:]}</text>')
    return f'<rect x="{x:.0f}" y="{y:.0f}" width="{bw:.0f}" height="{h + 110*s:.0f}" fill="#fff"/>' + ''.join(rects) + txt


def mix(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]; b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return '#%02X%02X%02X' % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def ramp(t):
    """沿纽带一圈的颜色：珊瑚红 → 金 → 薄荷绿 → 青 → 回到珊瑚红。"""
    stops = ['#F0705A', '#F2B84B', '#9BE08A', '#4FD1C5', '#6FB7F0', '#F0705A']
    x = (t % 1) * (len(stops) - 1)
    i = int(x)
    return mix(stops[i], stops[min(i + 1, len(stops) - 1)], x - i)


def circuits(W, H, seed, keep):
    """电路纹：从四边伸进来的折线，端点一个小圆；keep(x, y) 为假的地方不画。"""
    rnd = random.Random(seed)
    out = []
    for i in range(46):
        side = rnd.choice('LRTB')
        if side in 'LR':
            y = rnd.uniform(.04, .96) * H; x0 = 0 if side == 'L' else W
            ln = rnd.uniform(.08, .26) * W * (1 if side == 'L' else -1)
            dy = rnd.choice([-1, 1]) * rnd.uniform(.02, .06) * H
            pts = [(x0, y), (x0 + ln, y), (x0 + ln + abs(dy) * (1 if side == 'L' else -1), y + dy)]
        else:
            x = rnd.uniform(.05, .95) * W; y0 = 0 if side == 'T' else H
            ln = rnd.uniform(.04, .13) * H * (1 if side == 'T' else -1)
            dx = rnd.choice([-1, 1]) * rnd.uniform(.03, .08) * W
            pts = [(x, y0), (x, y0 + ln), (x + dx, y0 + ln + abs(dx) * (1 if side == 'T' else -1))]
        if not keep(*pts[-1]):
            continue
        d = 'M' + ' L'.join('%.0f %.0f' % p for p in pts)
        out.append(f'<path d="{d}" fill="none" stroke="{MINT}" stroke-opacity=".16" stroke-width="{W/700:.1f}"/>'
                   f'<circle cx="{pts[-1][0]:.0f}" cy="{pts[-1][1]:.0f}" r="{W/260:.1f}" fill="{MINT}" fill-opacity=".28"/>')
    return ''.join(out)


def sparks(W, H, seed, cx, cy, rad, n=150):
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        a = rnd.uniform(0, 2 * math.pi); r = rad * rnd.random() ** .6
        x, y = cx + r * math.cos(a) * 1.25, cy + r * math.sin(a)
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rnd.uniform(.5, 2.4) * W / 1700:.1f}" fill="{rnd.choice(["#FFFFFF", MINT, GOLD, "#BFEFFF"])}" fill-opacity="{rnd.uniform(.25, .9):.2f}"/>')
    return ''.join(out)


def knot(cx, cy, a, sw):
    """一条无限纽带（双纽线），分段着色；先铺宽而淡的光晕，再画带子，最后一道高光。"""
    N = 240
    P = []
    for i in range(N + 1):
        t = 2 * math.pi * i / N
        den = 1 + math.sin(t) ** 2
        x, y = a * math.cos(t) / den, a * math.sin(t) * math.cos(t) / den * 1.25
        ang = math.radians(-14)
        P.append((cx + x * math.cos(ang) - y * math.sin(ang), cy + x * math.sin(ang) + y * math.cos(ang)))
    out = []
    for w, op in ((sw * 3.4, .05), (sw * 2.3, .08), (sw * 1.55, .12)):
        for i in range(0, N, 2):
            out.append('<path d="M%.1f %.1f L%.1f %.1f L%.1f %.1f" fill="none" stroke="%s" stroke-opacity="%.2f" stroke-width="%.1f" stroke-linecap="round"/>'
                       % (*P[i], *P[i + 1], *P[min(i + 2, N)], ramp(i / N), op, w))
    order = list(range(N // 2, N)) + list(range(0, N // 2))   # 后半圈压在前半圈上，交叉处有上下
    for i in order:
        out.append('<path d="M%.1f %.1f L%.1f %.1f" fill="none" stroke="%s" stroke-width="%.1f" stroke-linecap="round"/>' % (*P[i], *P[i + 1], ramp(i / N), sw))
    hl = [P[i] for i in order] + [P[order[0]]]
    out.append('<path d="M%s" fill="none" stroke="#FFFFFF" stroke-opacity=".45" stroke-width="%.1f" stroke-linejoin="round"/>' % (' L'.join('%.1f %.1f' % q for q in hl), sw * .14))
    return ''.join(out)


def ring(cx, cy, r, col, inner):
    return (f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r*1.22:.0f}" fill="{col}" fill-opacity=".07"/>'
            f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r:.0f}" fill="{G0}" fill-opacity=".72" stroke="{col}" stroke-width="{r*.055:.1f}"/>'
            f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r*.86:.0f}" fill="none" stroke="{col}" stroke-opacity=".35" stroke-width="{r*.02:.1f}"/>{inner}')


def person(cx, cy, r, col):
    return (f'<circle cx="{cx:.0f}" cy="{cy - r*.24:.0f}" r="{r*.24:.0f}" fill="{col}"/>'
            f'<path d="M{cx - r*.52:.0f} {cy + r*.58:.0f} C{cx - r*.5:.0f} {cy + r*.05:.0f} {cx + r*.5:.0f} {cy + r*.05:.0f} {cx + r*.52:.0f} {cy + r*.58:.0f} Z" fill="{col}"/>')


def triad(cx, cy, r, col):
    pts = [(cx, cy - r * .46), (cx - r * .42, cy + r * .3), (cx + r * .42, cy + r * .3)]
    s = ''.join(f'<line x1="{a[0]:.0f}" y1="{a[1]:.0f}" x2="{b[0]:.0f}" y2="{b[1]:.0f}" stroke="{col}" stroke-width="{r*.05:.1f}"/>'
                for a, b in ((pts[0], pts[1]), (pts[1], pts[2]), (pts[2], pts[0])))
    s += f'<circle cx="{cx:.0f}" cy="{cy + r*.04:.0f}" r="{r*.2:.0f}" fill="none" stroke="{col}" stroke-width="{r*.045:.1f}"/>'
    return s + ''.join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r*.105:.0f}" fill="{col}"/>' for x, y in pts)


def machine(cx, cy, r, col):
    w = r * .78
    return (f'<rect x="{cx - w/2:.0f}" y="{cy - r*.3:.0f}" width="{w:.0f}" height="{r*.7:.0f}" rx="{r*.16:.0f}" fill="none" stroke="{col}" stroke-width="{r*.06:.1f}"/>'
            f'<line x1="{cx:.0f}" y1="{cy - r*.3:.0f}" x2="{cx:.0f}" y2="{cy - r*.55:.0f}" stroke="{col}" stroke-width="{r*.05:.1f}"/>'
            f'<circle cx="{cx:.0f}" cy="{cy - r*.6:.0f}" r="{r*.07:.0f}" fill="{col}"/>'
            f'<circle cx="{cx - r*.17:.0f}" cy="{cy - r*.02:.0f}" r="{r*.085:.0f}" fill="{col}"/><circle cx="{cx + r*.17:.0f}" cy="{cy - r*.02:.0f}" r="{r*.085:.0f}" fill="{col}"/>'
            f'<line x1="{cx - r*.16:.0f}" y1="{cy + r*.22:.0f}" x2="{cx + r*.16:.0f}" y2="{cy + r*.22:.0f}" stroke="{col}" stroke-width="{r*.05:.1f}"/>')


def ground(W, H):
    return (f'<defs><radialGradient id="g" cx="50%" cy="48%" r="75%"><stop offset="0" stop-color="{G2}"/><stop offset=".55" stop-color="{G1}"/><stop offset="1" stop-color="{G0}"/></radialGradient></defs>'
            f'<rect width="{W}" height="{H}" fill="url(#g)"/>')


def front(Wmm, Hmm):
    W, H = Wmm * 10, Hmm * 10
    s = Hmm / 240   # 版心随高度走：阅读版 190×250 比印刷版宽，字与位置都按高度比例放
    cx, cy = W / 2, H * .50
    a = W * .30
    r = W * .088
    yc = H * .715
    xs = [cx - W * .235, cx, cx + W * .235]
    stem = (f'<path d="M{cx:.0f} {cy + a*.18:.0f} C{cx:.0f} {cy + a*.5:.0f} {cx:.0f} {yc - r*1.6:.0f} {cx:.0f} {yc - r:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".7" stroke-width="{W/330:.1f}"/>'
            f'<path d="M{xs[0] + r:.0f} {yc:.0f} L{xs[1] - r:.0f} {yc:.0f} M{xs[1] + r:.0f} {yc:.0f} L{xs[2] - r:.0f} {yc:.0f}" stroke="{MINT}" stroke-opacity=".6" stroke-width="{W/420:.1f}"/>')
    keep = lambda x, y: abs(x - cx) > W * .36 or y < H * .07 or y > H * .9
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{Wmm}mm" height="{Hmm}mm">{ground(W, H)}'
           f'{circuits(W, H, 36, keep)}{sparks(W, H, 5, cx, cy, a * 1.15)}{stem}{knot(cx, cy, a, W * .034)}'
           f'{ring(xs[0], yc, r, "#9BE08A", person(xs[0], yc, r, "#CFF5C4"))}{ring(xs[1], yc, r * 1.06, GOLD, triad(xs[1], yc, r, "#F7E3A6"))}'
           f'{ring(xs[2], yc, r, "#6FB7F0", machine(xs[2], yc, r, "#CFE8FB"))}</svg>')
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page{{size:{Wmm}mm {Hmm}mm;margin:0}} body{{margin:0}}
.pg{{position:relative;width:{Wmm}mm;height:{Hmm}mm;overflow:hidden;text-align:center}}
.pg svg{{position:absolute;left:0;top:0}}
.a{{position:absolute;left:0;right:0}}
.ser{{top:{15*s:.1f}mm;font:400 {8.2*s:.1f}pt 'Noto Sans CJK SC';color:{MINT};letter-spacing:.3em;text-indent:.3em}}
.t1{{top:{27*s:.1f}mm;font:900 {50*s:.1f}pt/1 'Noto Sans CJK SC';color:{CREAM};letter-spacing:.04em}}
.t2{{top:{50*s:.1f}mm;font:700 {33*s:.1f}pt/1.2 'Noto Serif CJK SC';color:{CREAM};letter-spacing:.14em;text-indent:.14em}}
.ln{{top:{68.5*s:.1f}mm}} .ln i{{display:block;width:{40*s:.1f}mm;border-top:.8pt solid {GOLD};margin:0 auto}}
.sub{{top:{72*s:.1f}mm;font:400 {11.4*s:.1f}pt 'Noto Serif CJK SC';color:{GOLD};letter-spacing:.2em;text-indent:.2em}}
.lab{{top:{189.5*s:.1f}mm;font:400 {6.6*s:.1f}pt 'Noto Sans CJK SC';color:{MINT};letter-spacing:.3em}}
.lab span{{display:inline-block;width:{40*s:.1f}mm;text-indent:.3em}}
.au{{top:{203*s:.1f}mm;font:500 {15.5*s:.1f}pt 'Noto Serif CJK SC';color:{CREAM};letter-spacing:.3em;text-indent:.3em}}
.pub{{bottom:{12.5*s:.1f}mm;font:400 {9.6*s:.1f}pt 'Noto Serif CJK SC';color:{CREAM};letter-spacing:.4em;text-indent:.4em}}
.pub i{{display:block;width:{34*s:.1f}mm;border-top:.7pt solid {GOLD};margin:0 auto {2.8*s:.1f}mm}}
.pub span{{display:block;font:400 {6*s:.1f}pt 'Noto Sans CJK SC';color:{MINT};letter-spacing:.14em;text-indent:0;margin-top:{1.2*s:.1f}mm}}
</style></head><body><div class="pg">{svg}
<div class="a ser">德麦国际专著第 {NO} 号 · SIO 本体论</div>
<div class="a t1">人—GPT</div><div class="a t2">超级复合智能体</div><div class="a ln"><i></i></div>
<div class="a sub">SIO本体论下的三体对话与文明实践</div>
<div class="a lab"><span>人</span><span>主—互—客</span><span>GPT</span></div>
<div class="a au">王德生　秦衡峰　著</div>
<div class="a pub"><i></i>德麦国际出版社<span>DEMAI INTERNATIONAL PRESS · SINGAPORE</span></div>
</div></body></html>"""


def back(Wmm, Hmm):
    W, H = Wmm * 10, Hmm * 10
    s = Hmm / 240   # 版心随高度走：阅读版 190×250 比印刷版宽，字与位置都按高度比例放
    keep = lambda x, y: x < W * .12 or x > W * .88 or y < H * .1
    bc = barcode(W - 150 * s - 358 * s, H - 150 * s - 300 * s, s)
    panel = f'<rect x="{W*.115:.0f}" y="{H*.165:.0f}" width="{W*.77:.0f}" height="{H*.445:.0f}" rx="{W*.012:.0f}" fill="#0A2E24" fill-opacity=".55" stroke="{MINT}" stroke-opacity=".45" stroke-width="{W/520:.1f}"/>'
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{Wmm}mm" height="{Hmm}mm">{ground(W, H)}{circuits(W, H, 63, keep)}'
           f'{sparks(W, H, 9, W * .3, H * .735, W * .2, 60)}{knot(W * .3, H * .735, W * .125, W * .015)}{panel}{bc}</svg>')
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page{{size:{Wmm}mm {Hmm}mm;margin:0}} body{{margin:0}}
.pg{{position:relative;width:{Wmm}mm;height:{Hmm}mm;overflow:hidden}}
.pg svg{{position:absolute;left:0;top:0}}
.hd{{position:absolute;left:0;right:0;top:{17*s:.1f}mm;text-align:center;font:400 {11*s:.1f}pt 'Noto Serif CJK SC';color:{CREAM};letter-spacing:.4em;text-indent:.4em}}
.c{{position:absolute;left:{29*s:.1f}mm;right:{29*s:.1f}mm;top:{49*s:.1f}mm;color:{CREAM}}}
.lab{{font:700 {7*s:.1f}pt 'Noto Sans CJK SC';color:{GOLD};letter-spacing:.5em}}
.q{{font:700 {13.4*s:.1f}pt/1.8 'Noto Serif CJK SC';color:#FFFFFF;margin:{3*s:.1f}mm 0 0;letter-spacing:.04em}}
.rule{{width:{14*s:.1f}mm;border-top:.9pt solid {GOLD};margin:{5*s:.1f}mm 0 {4.5*s:.1f}mm}}
.bl p{{font:400 {8.6*s:.1f}pt/1.95 'Noto Serif CJK SC';color:#E9F3EC;margin:0 0 {2.2*s:.1f}mm;text-align:justify}}
.f{{position:absolute;left:{29*s:.1f}mm;bottom:{17*s:.1f}mm;font:400 {7*s:.1f}pt/1.85 'Noto Sans CJK SC';color:#CFE6DA}}
.f b{{color:{CREAM};font-weight:700;letter-spacing:.12em}}
</style></head><body><div class="pg">{svg}
<div class="hd">人—GPT超级复合智能体</div>
<div class="c"><div class="lab">一 句 话</div>
<div class="q">智能不是某个人或某个模型的聪明，而是人、GPT与具体场域在三体对话里，让特征、自由、幸福三律同时运转的整体。</div><div class="rule"></div>
<div class="bl"><p>本书用SIO本体论重写“存在”“GPT”“智能体”三个概念的根基：存在是主—互—客整体的呼吸，GPT是理念界里的意义三律引擎，智能体是三律正常运行的整体。</p>
<p>由此追踪人—GPT关系从工具期、伙伴期到复合萌芽期的发生，再落到两个原型场域——教师、学生与GPT的三体课堂，医生、病人与GPT的三体对话医疗。</p>
<p>它既不把GPT当新神，也不把它当小工具；它问的是：人怎样用工具而不被工具反噬。</p></div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 {NO} 号 · 三编七篇 · 约 25 万字<br>定价 US$45.00</div>
</div></body></html>"""


def main():
    import weasyprint
    import pymupdf
    ap = argparse.ArgumentParser()
    ap.add_argument('--fonts', type=Path, required=False)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    for tag, (w, h) in {'print': (170, 240), 'reader': (190, 250)}.items():
        weasyprint.HTML(string=front(w, h)).write_pdf(str(a.out / f'cover-{tag}.pdf'))
        weasyprint.HTML(string=back(w, h)).write_pdf(str(a.out / f'back-{tag}.pdf'))
    for src, dst in [('cover-print.pdf', 'cover.jpg'), ('back-print.pdf', 'backcover.jpg')]:
        pg = pymupdf.open(str(a.out / src))[0]
        zoom = 1004 / pg.rect.width
        pg.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom)).save(str(a.out / dst), jpg_quality=90)
    print('covers ok')


if __name__ == '__main__':
    main()
