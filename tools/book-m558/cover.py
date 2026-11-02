#!/usr/bin/env python3
"""第 558 号《悬着才成事——秩序为什么要靠悬着活着》（王德生、胡敏 著）封面与封底（工具链承自第 550 号，藏青底、金青奶白三色，220 系列版式）：
主图：一只轮子、一个奔跑的人、一条三圈的思考跑道（张力·转换·释放）。全部纯色，不用渐变。封面不写「王德生指导」。
用法：python3 cover.py --fonts /usr/share/fonts/opentype/noto --out <dir>
"""
import argparse
import math
import os
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0C1A34', '#1B3158', '#16294A'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#7FA7C9', '#EFE8D6', '#A9B6C8'
ISBN = '979-8-90690-566-6'
WAN = os.environ.get('WAN', '25')

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
    """主图（第 558 号）：走路之所以稳，是因为每一步都在倒。
    左中：一个向前倾倒的行人，后脚还在推地，前脚悬在半空、尚未落地（两个悬着）；
    下方地面以下三层：微观的乱点（一锅粥）、介观的对流胞（正在成形）、宏观的平滑地面线（定型）。
    右：一只悬着的摆。全部纯色，不用渐变。"""
    import random
    rnd = random.Random(558)
    s = W / 1700
    out = []
    ground = H * 0.62
    # 地面线（宏观秩序）
    out.append(f'<line x1="0" y1="{ground:.0f}" x2="{W:.0f}" y2="{ground:.0f}" stroke="{GOLD2}" stroke-opacity=".8" stroke-width="{3.2*s:.1f}"/>')
    # 地面下：介观对流胞（一排圆角胞）
    cw = 120 * s
    for k in range(int(W // cw) + 1):
        x0 = k * cw
        out.append(f'<path d="M{x0+8*s:.0f} {ground+70*s:.0f} q {cw/2-8*s:.0f} {-58*s:.0f} {cw-16*s:.0f} 0 q {-(cw/2-8*s):.0f} {58*s:.0f} {-(cw-16*s):.0f} 0" fill="none" stroke="{CYAN}" stroke-opacity=".38" stroke-width="{2.2*s:.1f}"/>')
    # 再往下：微观乱点
    for _ in range(420):
        out.append(f'<circle cx="{rnd.uniform(0, W):.0f}" cy="{rnd.uniform(ground+120*s, ground+230*s):.0f}" r="{rnd.uniform(1.0, 2.8)*s:.1f}" fill="{CREAM}" fill-opacity="{rnd.uniform(.10, .45):.2f}"/>')
    # 行人：重心前倾
    px, top = W * 0.40, ground - 380 * s
    out.append(f'<circle cx="{px + 70*s:.0f}" cy="{top:.0f}" r="{30*s:.0f}" fill="{CREAM}" fill-opacity=".95"/>')
    hip = (px - 4*s, top + 180*s)
    body = [(px + 58*s, top + 42*s), (px + 28*s, top + 110*s), hip]
    out.append(f'<path d="{tapered(body, 34*s, 27*s)}" fill="{CREAM}" fill-opacity=".92"/>')
    # 后腿：脚尖还在推地
    out.append(f'<path d="{tapered([hip, (hip[0]-40*s, hip[1]+90*s), (hip[0]-96*s, ground-36*s), (hip[0]-130*s, ground-4*s)], 26*s, 12*s)}" fill="{CREAM}" fill-opacity=".88"/>')
    # 前腿：悬在半空，脚离地
    foot = (hip[0] + 150*s, ground - 62*s)
    out.append(f'<path d="{tapered([hip, (hip[0]+60*s, hip[1]+70*s), (hip[0]+120*s, ground-110*s), foot], 26*s, 12*s)}" fill="{CREAM}" fill-opacity=".88"/>')
    # 脚下的悬空：一道虚线落点
    out.append(f'<line x1="{foot[0]:.0f}" y1="{foot[1]+16*s:.0f}" x2="{foot[0]+10*s:.0f}" y2="{ground-6*s:.0f}" stroke="{GOLD2}" stroke-width="{2.4*s:.1f}" stroke-dasharray="{8*s:.0f} {8*s:.0f}"/>')
    out.append(f'<circle cx="{foot[0]+12*s:.0f}" cy="{ground:.0f}" r="{9*s:.0f}" fill="none" stroke="{GOLD2}" stroke-width="{2.4*s:.1f}"/>')
    # 双臂
    for pts in ([(px + 46*s, top + 64*s), (px + 100*s, top + 120*s), (px + 150*s, top + 110*s)],
                [(px + 40*s, top + 70*s), (px - 6*s, top + 128*s), (px - 50*s, top + 160*s)]):
        out.append(f'<path d="{tapered(pts, 17*s, 10*s)}" fill="{CREAM}" fill-opacity=".85"/>')
    # 前倾的弧（倒）
    out.append(f'<path d="M{px - 60*s:.0f} {top - 70*s:.0f} A {330*s:.0f} {330*s:.0f} 0 0 1 {px + 220*s:.0f} {top + 40*s:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".55" stroke-width="{3*s:.1f}" stroke-dasharray="{14*s:.0f} {10*s:.0f}"/>')
    # 右：悬着的摆
    ox, oy = W * 0.82, ground - 470 * s
    out.append(f'<line x1="{ox - 60*s:.0f}" y1="{oy:.0f}" x2="{ox + 60*s:.0f}" y2="{oy:.0f}" stroke="{GOLD2}" stroke-width="{5*s:.1f}"/>')
    ang = math.radians(24)
    bx, by = ox + 300*s*math.sin(ang), oy + 300*s*math.cos(ang)
    out.append(f'<line x1="{ox:.0f}" y1="{oy:.0f}" x2="{bx:.0f}" y2="{by:.0f}" stroke="{CREAM}" stroke-opacity=".8" stroke-width="{3*s:.1f}"/>')
    out.append(f'<circle cx="{bx:.0f}" cy="{by:.0f}" r="{30*s:.0f}" fill="{GOLD2}"/>')
    out.append(f'<path d="M{ox - 300*s*math.sin(ang):.0f} {oy + 300*s*math.cos(ang):.0f} A {300*s:.0f} {300*s:.0f} 0 0 0 {bx:.0f} {by:.0f}" fill="none" stroke="{CYAN}" stroke-opacity=".45" stroke-width="{2.4*s:.1f}" stroke-dasharray="{10*s:.0f} {10*s:.0f}"/>')
    # 注脚三行
    ty2 = ground + 290 * s
    for xx, anc, big, small, col in ((W * 0.10, 'start', '倒', '已经失衡，还没被接住', GOLD2), (W * 0.42, 'start', '摆', '新的支点，正在成形', CYAN), (W * 0.92, 'end', '接住', '秩序是两个悬着的交接', CREAM)):
        out.append(f'<text x="{xx:.0f}" y="{ty2:.0f}" font-size="{36*s:.0f}" text-anchor="{anc}" font-family="Noto Serif CJK SC" font-weight="700" fill="{col}" letter-spacing="{4*s:.0f}">{big}</text>')
        out.append(f'<text x="{xx:.0f}" y="{ty2 + 40*s:.0f}" font-size="{20*s:.0f}" text-anchor="{anc}" font-family="Noto Sans CJK SC" fill="{DIM}" letter-spacing="{3*s:.0f}">{small}</text>')
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 558 号</div>
<div class="t"><div class="pre">普通人都能明白的</div><div class="big">悬着才成事</div>
<div class="sub">秩序为什么要靠悬着活着</div><div class="rule"></div></div>
<div class="b"><div class="au">王德生　著</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div>
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
<div class="c"><div class="lab">核 心 命 题</div>
<div class="q">走路之所以稳，<br>是因为每一步都在倒。</div><div class="by">——王德生口述</div><div class="rule"></div>
<div class="bl"><p>一件事能成，底下总有两样东西悬着：一样已经失衡、还没被接住；一样正在成形、还没落定。秩序不是悬着的反面，秩序是这两样东西一次次交接出来的样子。物理里也是这样：宏观的秩序，是微观的混沌加上介观的自组织，合起来涌现的。</p>
<p>人为了证明一件事在起作用，会去裁定、命名、审核、认证、考核。本书说，错不在这些动作，在它们落下的时候：落在悬着正在进行的那段时间之内，就把悬着关掉了。音乐、形态、改编、修复、善、法律、AI 复核、组织、能力，九个行业，各看一遍。</p>
<p>庄子说浑沌日凿一窍，七日而死；郑板桥说，由聪明而转入糊涂更难。本书导论、三编九章、结语，每章都写明这一章怎样才算说错。</p>
<p>母题由王德生口述提出；九章以九篇德麦国际学员论文为材料，正文由 AI（Claude）协作撰写并经三审；书中人物与场景多为构想，推翻条件尚未检验，没有独立学术评审。</p></div>
<div class="gold">别在半夜验收。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 558 号 · 前言、导论、三编九章、结语、附录、后记 · 约 {WAN} 万字<br>ISBN 979-8-90690-566-6 · 定价 US$20.00</div>
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
