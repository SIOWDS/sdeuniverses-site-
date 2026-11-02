#!/usr/bin/env python3
"""第 555 号《让经验长成思想》（阳涌 著）封面与封底（工具链承自第 554 号；靛青底，金、青绿点缀，220 系列版式）：
主图：洗碗盆剖面——清水、落下的颗粒、盆底沉淀层、自沉淀长出的晶体。全部纯色，不用渐变。
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
    """主图（第 555 号）：洗碗盆的剖面——上层清水（清洗），水中落下的颗粒，盆底一层层沉淀，最上一层长出一枚晶体（显露）。纯色，不用渐变与裁剪。"""
    s = W / 1700
    out = []
    cx, hw = W * 0.5, W * 0.40
    rim, D = H * 0.515, H * 0.30
    N = 160
    def prof(x):
        u = max(-1.0, min(1.0, (x - cx) / hw))
        return rim + D * (1 - abs(u) ** 3.2) ** 0.55
    xs = [cx - hw + 2 * hw * k / N for k in range(N + 1)]
    # 盆内的水（清洗）
    water_top = rim + D * 0.06
    pts = [(x, prof(x)) for x in xs if prof(x) > water_top]
    d = 'M%.1f %.1f ' % (pts[0][0], water_top) + ' '.join('L%.1f %.1f' % q for q in pts) + ' L%.1f %.1f Z' % (pts[-1][0], water_top)
    out.append(f'<path d="{d}" fill="{CYAN}" fill-opacity=".10"/>')
    # 水面细纹
    for k, (yy, op) in enumerate([(water_top, .55), (water_top + 14 * s, .25)]):
        x0, x1 = pts[0][0] + 6 * s, pts[-1][0] - 6 * s
        dd = 'M%.0f %.0f' % (x0, yy)
        segs = 10
        for i in range(segs):
            xa = x0 + (x1 - x0) * (i + .5) / segs; xb = x0 + (x1 - x0) * (i + 1) / segs
            dd += ' Q%.0f %.0f %.0f %.0f' % (xa, yy + (6 if i % 2 else -6) * s, xb, yy)
        out.append(f'<path d="{dd}" fill="none" stroke="{CYAN}" stroke-opacity="{op}" stroke-width="{2*s:.1f}"/>')
    # 冲洗的水流（自上而下的几道细线）
    for k, fx in enumerate((0.30, 0.38, 0.62, 0.70)):
        x = W * fx
        out.append(f'<line x1="{x:.0f}" y1="{rim - H*0.09:.0f}" x2="{x:.0f}" y2="{water_top + 40*s:.0f}" stroke="{CYAN}" stroke-opacity="{.35 - .05*k:.2f}" stroke-width="{(3 - .4*k)*s:.1f}" stroke-linecap="round" stroke-dasharray="{18*s:.0f} {12*s:.0f}"/>')
    # 沉淀层（自下而上）
    levels = [(D * 0.80, CLAY, .55), (D * 0.70, GOLD, .55), (D * 0.61, DIM, .35), (D * 0.53, GOLD2, .60), (D * 0.46, GOLD, .35)]
    import math as _m
    prev = None
    bands = []
    for i, (dep, col, op) in enumerate(levels):
        amp = (5 + 2 * i) * s
        def top(x, dep=dep, amp=amp, i=i):
            return rim + dep + amp * _m.sin((x - cx) / (70 * s) + i * 1.3)
        seg = [x for x in xs if prof(x) > top(x)]
        if len(seg) < 3:
            continue
        up = [(x, top(x)) for x in seg]
        lo = [(x, prof(x)) for x in reversed(seg)]
        dd = 'M' + ' L'.join('%.1f %.1f' % q for q in up + lo) + ' Z'
        bands.append(f'<path d="{dd}" fill="{col}" fill-opacity="{op}"/>')
        bands.append('<path d="M' + ' L'.join('%.1f %.1f' % q for q in up) + f'" fill="none" stroke="{CREAM}" stroke-opacity=".25" stroke-width="{1.4*s:.1f}"/>')
    out += bands
    # 正在落下的颗粒
    import random as _r
    rnd = _r.Random(555)
    for k in range(46):
        x = cx + (rnd.random() * 2 - 1) * hw * 0.78
        y = water_top + 30 * s + rnd.random() * (D * 0.40 - 40 * s)
        r = (2.2 + rnd.random() * 4.2) * s
        col = (GOLD2, CREAM, GOLD, CLAY)[k % 4]
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="{col}" fill-opacity="{.45 + .4*rnd.random():.2f}"/>')
    # 晶体（显露）：自最上一层长出的六棱柱
    bx = cx + hw * 0.18
    by = rim + D * 0.46 + 4 * s
    cw, ch = 34 * s, 170 * s
    body = [(bx - cw, by), (bx - cw, by - ch), (bx, by - ch - 34 * s), (bx + cw, by - ch), (bx + cw, by)]
    out.append('<path d="M' + ' L'.join('%.1f %.1f' % q for q in body) + f' Z" fill="{GOLD}"/>')
    out.append(f'<path d="M{bx:.1f} {by:.1f} L{bx:.1f} {by - ch:.1f} L{bx + cw:.1f} {by - ch:.1f} L{bx + cw:.1f} {by:.1f} Z" fill="{GOLD2}"/>')
    out.append(f'<path d="M{bx - cw:.1f} {by - ch:.1f} L{bx:.1f} {by - ch - 34*s:.1f} L{bx + cw:.1f} {by - ch:.1f} L{bx:.1f} {by - ch:.1f} Z" fill="#F7E6B0"/>')
    sm = [(bx - cw - 46 * s, by), (bx - cw - 46 * s, by - 80 * s), (bx - cw - 30 * s, by - 98 * s), (bx - cw - 14 * s, by - 80 * s), (bx - cw - 14 * s, by)]
    out.append('<path d="M' + ' L'.join('%.1f %.1f' % q for q in sm) + f' Z" fill="{GOLD}" fill-opacity=".75"/>')
    for t in (-150, -115, -65, -30):
        rr = 70 * s
        x1 = bx + _m.cos(_m.radians(t)) * (60 * s); y1 = by - ch - 20 * s + _m.sin(_m.radians(t)) * (60 * s)
        x2 = bx + _m.cos(_m.radians(t)) * (60 * s + rr); y2 = by - ch - 20 * s + _m.sin(_m.radians(t)) * (60 * s + rr)
        out.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{GOLD2}" stroke-opacity=".55" stroke-width="{2.2*s:.1f}" stroke-linecap="round"/>')
    # 盆的轮廓
    edge = [(x, prof(x)) for x in xs]
    out.append('<path d="M' + ' L'.join('%.1f %.1f' % q for q in edge) + f'" fill="none" stroke="{CREAM}" stroke-opacity=".85" stroke-width="{3.2*s:.1f}" stroke-linejoin="round"/>')
    out.append(f'<line x1="{cx - hw - 26*s:.0f}" y1="{rim:.0f}" x2="{cx - hw + 10*s:.0f}" y2="{rim:.0f}" stroke="{CREAM}" stroke-opacity=".85" stroke-width="{3.2*s:.1f}" stroke-linecap="round"/>')
    out.append(f'<line x1="{cx + hw - 10*s:.0f}" y1="{rim:.0f}" x2="{cx + hw + 26*s:.0f}" y2="{rim:.0f}" stroke="{CREAM}" stroke-opacity=".85" stroke-width="{3.2*s:.1f}" stroke-linecap="round"/>')
    # 标注
    lab = lambda x, y, t, col, anc='start': out.append(f'<text x="{x:.0f}" y="{y:.0f}" font-size="{26*s:.0f}" text-anchor="{anc}" font-family="Noto Sans CJK SC" fill="{col}" letter-spacing="{4*s:.0f}">{t}</text>')
    lab(cx + hw + 26 * s, rim - 20 * s, '清洗', CYAN, 'end')
    lab(cx - hw * 0.62, rim + D * 0.30, '沉淀', GOLD2)
    lab(bx + cw + 22 * s, by - ch + 10 * s, '显露', '#F7E6B0')
    out.append(f'<text x="{cx:.0f}" y="{rim + D + 70*s:.0f}" font-size="{18*s:.0f}" text-anchor="middle" font-family="Noto Sans CJK SC" fill="{DIM}" letter-spacing="{4*s:.0f}">混沌碰撞 · 自组织 · 涌现</text>')
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
<div class="t"><div class="pre">经验 · 沉淀 · 思想</div><div class="big big2" style="font-size:{40*s:.1f}pt;line-height:1.36">让经验<br>长成思想</div>
<div class="sub">{M.SUBTITLE}</div><div class="rule"></div></div>
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
<div class="c"><div class="lab">核 心 问 题</div>
<div class="q">思想是经验的差异没有被清洗掉，<br>而留下来的沉淀显露。</div><div class="by">——本书原理</div><div class="rule"></div>
<div class="bl"><p>一件事做完，碗洗干净了，题做对了，会开完了——过程里冒出来的差异，大多跟着被冲走。完成、熟练、标准化、提炼，都是清洗；清洗让我们交得了差、组织得起来，也让思想越来越没有来处。</p>
<p>本书的原理：思想不是被提炼出来的，是经验里没被洗掉的差异沉淀下来、显露出来的。它是特征律“混沌碰撞—自组织—涌现”在经验上的翻译：特征是差异稳定运行的结晶。判据是两个独立读数——复现与存留。</p>
<p>由此有三个反常识的判断：把沉淀写成谁用都一样的要点，是又洗了一遍；条件恒定下越熟练，沉淀越少；只交终稿的 AI 是最强的清洗机，留下来路的 AI 却是最强的沉淀器。提炼是多对一的压缩，差异将来会在哪里撞出结晶，压缩当时无法预知——所以要点替代不了原始沉淀。</p>
<p>全书前言、导论、五编十八章、结语与附录；第十八章写明七条判决预测、与最强对手分叉的设计和撤回条件。学术专著：全书原理由王德生提出，阳涌著，正文由 AI（Claude）协作撰写，经统稿与三审；场景为设想，无实测数据，无独立学术评审。</p></div>
<div class="gold">请留着盆底那一层。</div></div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 {M.NO} 号 · 前言、导论、五编十八章、结语、附录 · 约 {WAN} 万字<br>ISBN {M.ISBN} · 定价 {M.PRICE}</div>
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
