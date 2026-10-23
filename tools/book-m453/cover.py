#!/usr/bin/env python3
"""第 453 号《爱在创造中成全》封面与封底（沿用 220 系列版式骨架：书名在左上、署名出版在左下、封底判词＋简介＋条码；
配色与图案为本书原创）。主图是“同一性谱系”：九道水平的地层，最上面一层整齐划一（同），往下一层比一层不同（异）；
一根细线贯穿其间，越往下越粗（最薄的核心，在回流里变厚）；线顶长出一枝新芽（创造中长出来的新东西）。
用法：python3 cover.py --fonts <dir> --out <dir>
"""
import argparse
import math
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import meta453 as M

BG_TOP, BG_MID, BG_LOW = '#0A1F18', '#133428', '#0E2A20'
GOLD, GOLD2, CREAM, DIM = '#C9A857', '#E6CB82', '#F1EAD6', '#A8B9AD'
COPPER, SAGE, TEAL, ROSE = '#D8956B', '#9FC48A', '#6FB5A6', '#E3B1A0'
ISBN = M.ISBN

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




def background(W, H, uid):
    dots = []
    step = 46
    for yy in range(23, H, step):
        for xx in range(23 + (yy // step % 2) * 23, W, step):
            dots.append('<circle cx="%d" cy="%d" r="1.6"/>' % (xx, yy))
    return f"""
<defs>
 <linearGradient id="bg{uid}" x1="0" y1="0" x2="0.3" y2="1">
  <stop offset="0" stop-color="{BG_TOP}"/><stop offset=".55" stop-color="{BG_MID}"/><stop offset="1" stop-color="{BG_LOW}"/></linearGradient>
 <radialGradient id="halo{uid}" cx=".5" cy=".5" r=".5">
  <stop offset="0" stop-color="{GOLD2}" stop-opacity=".30"/><stop offset=".5" stop-color="{GOLD}" stop-opacity=".10"/>
  <stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></radialGradient>
 <linearGradient id="core{uid}" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="{SAGE}"/><stop offset=".5" stop-color="{GOLD2}"/><stop offset="1" stop-color="{GOLD}"/></linearGradient>
</defs>
<rect width="{W}" height="{H}" fill="url(#bg{uid})"/>
<g fill="{DIM}" fill-opacity=".09">{''.join(dots)}</g>"""


def branch(out, rnd, x, y, ang, length, depth, s, tips):
    """一枝新芽：递归分叉，越往末梢越细，末梢落一颗暖光点。"""
    x2 = x + length * math.cos(ang); y2 = y + length * math.sin(ang)
    bend = rnd.uniform(-0.18, 0.18) * length
    cx_, cy_ = (x + x2) / 2 + bend * math.sin(ang), (y + y2) / 2 - bend * math.cos(ang)
    w = max(1.4, depth * 2.6) * s
    col = SAGE if depth >= 3 else GOLD2
    out.append(f'<path d="M{x:.0f} {y:.0f} Q{cx_:.0f} {cy_:.0f} {x2:.0f} {y2:.0f}" fill="none" stroke="{col}" stroke-opacity=".92" stroke-width="{w:.1f}" stroke-linecap="round"/>')
    if depth <= 2 and rnd.random() < .7:   # 叶片
        a = ang + rnd.choice([-1, 1]) * 1.0
        L = rnd.uniform(26, 40) * s
        out.append(f'<ellipse cx="{x2 + L*0.5*math.cos(a):.0f}" cy="{y2 + L*0.5*math.sin(a):.0f}" rx="{L*0.55:.1f}" ry="{L*0.24:.1f}" transform="rotate({math.degrees(a):.0f} {x2 + L*0.5*math.cos(a):.0f} {y2 + L*0.5*math.sin(a):.0f})" fill="{SAGE}" fill-opacity=".7"/>')
    if depth == 0:
        tips.append((x2, y2)); return
    n = 2 if depth > 1 else rnd.choice([1, 2])
    for k in range(n):
        da = rnd.uniform(0.38, 0.62) * (1 if (k == 0) else -1) if n == 2 else rnd.uniform(-0.3, 0.3)
        branch(out, rnd, x2, y2, ang + da, length * rnd.uniform(.66, .78), depth - 1, s, tips)


def art(W, H, uid):
    rnd = random.Random(453)
    s = W / 1700
    cx = W * 0.70
    y_top, y_bot = H * 0.40, H * 0.775
    out = [f'<circle cx="{cx:.0f}" cy="{H*0.40:.0f}" r="{620*s:.0f}" fill="url(#halo{uid})"/>']
    # 九道地层：越往下越不同
    n = 9
    band_y = [H * 0.52 + k * (H * 0.032) for k in range(n)]
    palette = [GOLD2, COPPER, SAGE, CREAM, TEAL, ROSE]
    x_lo, x_hi = W * 0.09, W * 0.95
    for k, y in enumerate(band_y):
        t = k / (n - 1)               # 0 同 → 1 异
        x = x_lo
        L0 = 46 * s
        while x < x_hi:
            L = L0 * (1 + rnd.uniform(-1, 1) * 0.75 * t)
            gap = 13 * s * (1 + rnd.uniform(-1, 1) * 0.9 * t)
            yy = y + rnd.uniform(-1, 1) * 9 * s * t
            if abs((x + L / 2) - cx) > 20 * s:
                if rnd.random() < 0.12 + 0.55 * t:
                    col = rnd.choice(palette)
                else:
                    col = GOLD2
                op = 0.9 - 0.15 * t
                out.append(f'<line x1="{x:.0f}" y1="{yy:.0f}" x2="{x + L:.0f}" y2="{yy:.0f}" stroke="{col}" stroke-opacity="{op:.2f}" stroke-width="{5.2*s:.1f}" stroke-linecap="round"/>')
            x += L + gap
    # 贯穿的最薄的核心：越往下越粗
    pts = [(cx, y_bot + (y_top - y_bot) * i / 60) for i in range(61)]   # 自下而上
    out.append(f'<path d="{tapered(pts, 15*s, 3*s, 1.0)}" fill="url(#core{uid})" fill-opacity=".98"/>')
    out.append(f'<line x1="{cx:.0f}" y1="{y_top:.0f}" x2="{cx:.0f}" y2="{y_bot:.0f}" stroke="{GOLD2}" stroke-opacity=".22" stroke-width="{34*s:.0f}" stroke-linecap="round"/>')
    # 底线
    out.append(f'<line x1="{W*0.09:.0f}" y1="{y_bot + 40*s:.0f}" x2="{W*0.95:.0f}" y2="{y_bot + 40*s:.0f}" stroke="{GOLD}" stroke-opacity=".5" stroke-width="{1.6*s:.1f}"/>')
    # 新芽
    tips = []
    branch(out, rnd, cx, y_top, -math.pi / 2, 130 * s, 4, s, tips)
    for x, y in tips:
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{26*s:.0f}" fill="{GOLD2}" fill-opacity=".18"/>')
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{7*s:.1f}" fill="#FFF3D6"/>')
    # 四周零星的暖光点
    for _ in range(70):
        x = rnd.uniform(W * 0.45, W * 0.98); y = rnd.uniform(H * 0.14, H * 0.50)
        if (x - cx) ** 2 / (330 * s) ** 2 + (y - H * 0.30) ** 2 / (300 * s) ** 2 < 1: continue
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rnd.uniform(1.4, 3.6)*s:.1f}" fill="{rnd.choice([GOLD2, CREAM, ROSE])}" fill-opacity="{rnd.uniform(.3, .75):.2f}"/>')
    return ''.join(out)



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
.big{{font:700 {35*s:.1f}pt/1.25 'Noto Serif CJK SC';letter-spacing:.08em;color:#F7F1E3;margin:{3*s:.1f}mm 0 {3*s:.1f}mm {-1*s:.1f}mm}}
.sub{{font:400 {10.2*s:.1f}pt/1.8 'Noto Serif CJK SC';color:{GOLD2};letter-spacing:.03em;width:{104*s:.1f}mm}}
.rule{{width:{16*s:.1f}mm;border-top:.9pt solid {GOLD};margin-top:{5*s:.1f}mm}}
.b{{position:absolute;left:{17*s:.1f}mm;bottom:{17*s:.1f}mm}}
.au{{font:400 {12.5*s:.1f}pt 'Noto Serif CJK SC';color:{CREAM};letter-spacing:.28em}}
.ph{{font:700 {8.4*s:.1f}pt 'Noto Sans CJK SC';color:{GOLD2};letter-spacing:.3em;margin-top:{6*s:.1f}mm}}
.pe{{font:400 {6.6*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.08em;margin-top:{.8*s:.1f}mm}}
.no{{position:absolute;right:{15*s:.1f}mm;top:{16*s:.1f}mm;font:400 {6.6*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.2em;text-align:right}}
</style></head><body><div class="pg">{svg}
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 {M.NO} 号</div>
<div class="t"><div class="pre">普通人都能读的</div><div class="big">{M.TITLE}</div>
<div class="sub">{M.SUBTITLE}</div><div class="rule"></div></div>
<div class="b"><div class="au">{M.AUTHOR}　著</div><div class="ph">{M.PUBLISHER}</div><div class="pe">{M.PUBLISHER_EN}</div></div>
</div></body></html>"""


def back(Wmm, Hmm, F):
    W, H = Wmm * 10, Hmm * 10
    s = Wmm / 170
    # 右上小徽：一根芯线，两侧由整齐渐到参差的小横道
    ex, ey = W * 0.865, H * 0.075
    rows = []
    for k in range(5):
        yy = ey - 36 * s + k * 18 * s
        j = k * 3.2 * s
        rows.append(f'<line x1="{ex-44*s:.0f}" y1="{yy:.0f}" x2="{ex-10*s - j:.0f}" y2="{yy + (k%2)*j*0.4:.0f}" stroke="{GOLD}" stroke-width="{3*s:.1f}" stroke-linecap="round" stroke-dasharray="{(14 - k*2)*s:.0f} {(5 + k*2)*s:.0f}"/>')
        rows.append(f'<line x1="{ex+10*s + j:.0f}" y1="{yy:.0f}" x2="{ex+44*s:.0f}" y2="{yy - (k%2)*j*0.4:.0f}" stroke="{GOLD}" stroke-width="{3*s:.1f}" stroke-linecap="round" stroke-dasharray="{(14 - k*2)*s:.0f} {(5 + k*2)*s:.0f}"/>')
    emb = (f'<circle cx="{ex:.0f}" cy="{ey:.0f}" r="{70*s:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".5" stroke-width="{2*s:.1f}"/>' + ''.join(rows) +
           f'<line x1="{ex:.0f}" y1="{ey-52*s:.0f}" x2="{ex:.0f}" y2="{ey+44*s:.0f}" stroke="{SAGE}" stroke-width="{4.5*s:.1f}" stroke-linecap="round"/>'
           f'<circle cx="{ex:.0f}" cy="{ey-58*s:.0f}" r="{7*s:.1f}" fill="{GOLD2}"/>')
    waves = []
    for k, (yy, op) in enumerate([(.955, .16), (.972, .09)]):
        y0 = H * yy
        waves.append(f'<line x1="0" y1="{y0:.0f}" x2="{W}" y2="{y0:.0f}" stroke="{GOLD}" stroke-opacity="{op}" stroke-width="{1.6*s:.1f}"/>')
    bc, bw = barcode(W - 170 * s - 380 * s, H - 150 * s - 300 * s, s)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{Wmm}mm" height="{Hmm}mm">'
           f'{background(W, H, "b")}{emb}{"".join(waves)}{bc}</svg>')
    wan = round(M.total_hanzi() / 10000)
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{fontface(F)}
@page{{size:{Wmm}mm {Hmm}mm;margin:0}} body{{margin:0}}
.pg{{position:relative;width:{Wmm}mm;height:{Hmm}mm;overflow:hidden}}
.pg svg{{position:absolute;left:0;top:0}}
.c{{position:absolute;left:{17*s:.1f}mm;top:{24*s:.1f}mm;width:{128*s:.1f}mm;color:{CREAM}}}
.lab{{font:700 {7.4*s:.1f}pt 'Noto Sans CJK SC';color:{GOLD2};letter-spacing:.5em}}
.q{{font:700 {15*s:.1f}pt/1.8 'Noto Serif CJK SC';color:#F7F1E3;margin:{4*s:.1f}mm 0 {2*s:.1f}mm;letter-spacing:.03em}}
.by{{font:400 {8.2*s:.1f}pt 'Noto Serif CJK SC';color:{DIM}}}
.rule{{width:{14*s:.1f}mm;border-top:.9pt solid {GOLD};margin:{6*s:.1f}mm 0 {5*s:.1f}mm}}
.bl p{{font:400 {9.3*s:.1f}pt/1.95 'Noto Serif CJK SC';color:{CREAM};opacity:.9;margin:0 0 {3.2*s:.1f}mm;text-align:left}}
.gold{{font:700 {10.2*s:.1f}pt/1.7 'Noto Serif CJK SC';color:{GOLD2};margin-top:{5*s:.1f}mm;letter-spacing:.05em}}
.f{{position:absolute;left:{17*s:.1f}mm;bottom:{17*s:.1f}mm;font:400 {7.2*s:.1f}pt/1.85 'Noto Sans CJK SC';color:{DIM}}}
.f b{{color:{CREAM};font-weight:700;letter-spacing:.12em}}
</style></head><body><div class="pg">{svg}
<div class="c"><div class="lab">判 词</div>
<div class="q">爱不在冲突里放弃，在冲突里创造：<br>把统一性升维为同一性谱系，<br>爱在这新创造里涌现。</div><div class="by">——本书判词</div><div class="rule"></div>
<div class="bl"><p>湖南的丈夫和苏州的妻子，三年里菜里没有放过辣椒。丈夫说“没事，我什么都吃”，直到妻子在他的外套口袋里翻出一张火锅店的小票。</p>
<p>忍耐有两种：一种把力气耗掉，一种把力气存起来，存成新的东西。今天处理矛盾最常听到的话，多包容、再忍忍、放下就好，有很大一部分是虚幻的解法：暂时平息，很快复发，级别升高。真正解决问题的，是带着忍耐和坚持的创造：把“大家都一样”的统一性，升维为同一性谱系，有的层必须同，有的层可以异。</p>
<p>全书从林前 13 章出发，逐句读爱的箴言，回望旧约几千年的忍耐，读耶稣的神迹与饭桌，再走回婚姻、亲子、照料、内心、职场、教会和有机器参与的时代。按经文所记是事实来读，神学上的争议不判，难读的地方标明“待验”。写给每一个被劝过“忍一忍”的人。</p></div>
<div class="gold">恒久忍耐，是为了让新的东西有时间长出来。</div></div>
<div class="f"><b>{M.PUBLISHER}</b> · {M.PUBLISHER_EN}<br>德麦国际专著第 {M.NO} 号 · 七部五十三章 · 约 {wan} 万字<br>定价 {M.PRICE}</div>
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
