#!/usr/bin/env python3
"""第 602 号《难得糊涂：原创力的人格根基》（王德生 著）封面与封底（由第 599 号 cover.py 改来；深蓝底、奶白书名、金色副题、金色光环，
纯色扁平插图，不用渐变；规格见 popular-philosophy-monograph-format/references/cover-spec.md）：
主图取全书总比喻：一口盖着盖子的汤锅，锅下一小簇文火；盖沿逸出两缕细汽。
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
    """主图（第 602 号）：盖着盖子的汤锅（奶白锅身、金色锅盖与把手），锅下三瓣小小的文火（陶红、金、奶白），
    盖沿逸出两缕细汽；身后五层金色光环。全部纯色扁平，不用渐变；原创图形。"""
    s = W / 1700
    cx, cy = W * 0.5, H * 0.62
    out = []
    for rr, w, op in [(655, 30, .06), (610, 20, .10), (565, 12, .18), (525, 6, .34), (490, 3, .70)]:
        out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{rr*s:.0f}" fill="none" stroke="{GOLD}" stroke-opacity="{op}" stroke-width="{w*s:.1f}"/>')
    pw, ph = 330 * s, 250 * s          # 锅身半宽、高
    top = cy - 60 * s                  # 锅口
    bot = top + ph
    # 两侧把手
    for sx in (-1, 1):
        x0 = cx + sx * pw
        out.append(f'<rect x="{min(x0, x0 + sx*70*s):.0f}" y="{top + 40*s:.0f}" width="{70*s:.0f}" height="{30*s:.0f}" rx="{15*s:.0f}" fill="{GOLD}"/>')
    # 锅身：上宽下略收、底角圆
    body = (f'M{cx-pw:.0f} {top:.0f} L{cx+pw:.0f} {top:.0f} L{cx+pw-18*s:.0f} {bot-50*s:.0f} '
            f'Q{cx+pw-24*s:.0f} {bot:.0f} {cx+pw-80*s:.0f} {bot:.0f} L{cx-pw+80*s:.0f} {bot:.0f} '
            f'Q{cx-pw+24*s:.0f} {bot:.0f} {cx-pw+18*s:.0f} {bot-50*s:.0f} Z')
    out.append(f'<path d="{body}" fill="{CREAM}"/>')
    out.append(f'<rect x="{cx-pw+12*s:.0f}" y="{top + 105*s:.0f}" width="{2*pw-24*s:.0f}" height="{14*s:.0f}" fill="{CYAN}" fill-opacity=".85"/>')
    # 锅沿
    out.append(f'<rect x="{cx-pw-14*s:.0f}" y="{top-16*s:.0f}" width="{2*pw+28*s:.0f}" height="{24*s:.0f}" rx="{10*s:.0f}" fill="{GOLD2}"/>')
    # 锅盖：扁拱形 + 盖钮
    lid_y = top - 18 * s
    out.append(f'<path d="M{cx-pw-4*s:.0f} {lid_y:.0f} Q{cx:.0f} {lid_y-150*s:.0f} {cx+pw+4*s:.0f} {lid_y:.0f} Z" fill="{GOLD}"/>')
    out.append(f'<rect x="{cx-34*s:.0f}" y="{lid_y-108*s:.0f}" width="{68*s:.0f}" height="{36*s:.0f}" rx="{14*s:.0f}" fill="{GOLD2}"/>')
    # 两缕细汽（盖沿逸出）
    for sx in (-1, 1):
        x = cx + sx * (pw - 40 * s)
        y0 = lid_y - 30 * s
        d = (f'M{x:.0f} {y0:.0f} C{x+sx*30*s:.0f} {y0-60*s:.0f} {x-sx*30*s:.0f} {y0-110*s:.0f} {x+sx*10*s:.0f} {y0-170*s:.0f}')
        out.append(f'<path d="{d}" fill="none" stroke="{CREAM}" stroke-opacity=".55" stroke-width="{9*s:.1f}" stroke-linecap="round"/>')
    # 文火：三瓣小火苗
    fy = bot + 120 * s
    def flame(x, h, w, col):
        return (f'<path d="M{x:.0f} {fy-h:.0f} C{x+w*.9:.0f} {fy-h*.55:.0f} {x+w:.0f} {fy-h*.15:.0f} {x:.0f} {fy:.0f} '
                f'C{x-w:.0f} {fy-h*.15:.0f} {x-w*.9:.0f} {fy-h*.55:.0f} {x:.0f} {fy-h:.0f} Z" fill="{col}"/>')
    out.append(flame(cx - 62 * s, 70 * s, 26 * s, CLAY))
    out.append(flame(cx + 62 * s, 70 * s, 26 * s, CLAY))
    out.append(flame(cx, 100 * s, 36 * s, GOLD2))
    out.append(flame(cx, 52 * s, 18 * s, CREAM))
    # 灶沿：一道细线
    out.append(f'<rect x="{cx-200*s:.0f}" y="{fy+8*s:.0f}" width="{400*s:.0f}" height="{10*s:.0f}" rx="{5*s:.0f}" fill="{DIM}" fill-opacity=".45"/>')
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
<div class="t"><div class="big" style="font-size:{50*s:.1f}pt;letter-spacing:.18em;margin-top:{10*s:.1f}mm">难得糊涂</div>
<div class="sub" style="font-size:{13*s:.1f}pt;margin-top:{4*s:.1f}mm;letter-spacing:.16em">原创力的人格根基</div><div class="rule"></div></div>
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
.c{{position:absolute;left:{17*s:.1f}mm;top:{30*s:.1f}mm;width:{122*s:.1f}mm;color:{CREAM}}}
.lab{{font:700 {7.4*s:.1f}pt 'Noto Sans CJK SC';color:{GOLD2};letter-spacing:.5em}}
.q{{font:700 {13.2*s:.1f}pt/1.85 'Noto Serif CJK SC';color:#F7F1E3;margin:{4*s:.1f}mm 0 {2*s:.1f}mm;letter-spacing:.04em}}
.by{{font:400 {8.2*s:.1f}pt 'Noto Serif CJK SC';color:{DIM}}}
.rule{{width:{14*s:.1f}mm;border-top:.9pt solid {GOLD};margin:{7*s:.1f}mm 0 {6*s:.1f}mm}}
.bl p{{font:400 {9.6*s:.1f}pt/2.0 'Noto Serif CJK SC';color:{CREAM};opacity:.9;margin:0 0 {2.6*s:.1f}mm;text-align:left}}
.gold{{font:700 {10.5*s:.1f}pt 'Noto Serif CJK SC';color:{GOLD2};margin-top:{6*s:.1f}mm;letter-spacing:.06em}}
.f{{position:absolute;left:{17*s:.1f}mm;bottom:{17*s:.1f}mm;font:400 {7.2*s:.1f}pt/1.85 'Noto Sans CJK SC';color:{DIM}}}
.f b{{color:{CREAM};font-weight:700;letter-spacing:.12em}}
</style></head><body><div class="pg">{svg}
<div class="c">
<div class="lab">全书一句话</div>
<div class="q">糊涂不是少了清楚，而是让一件事暂时不进入“定死了”的状态，留在“还没定”和“正在成形”里熬；熬出的是创造新秩序的能力。</div><div class="rule"></div>
<div class="bl"><p>“难得糊涂”四个字，几乎每个中国人都见过。本书把它当真：糊涂不是装傻、不是拖延、不是接纳一切，而是有火的不定论——火在，事情在往前走，只是不让它提前凝固。聪明在已有秩序里又快又稳地展开和搬家；糊涂熬出的，是造出原本没有的秩序的本事。全书十编二十八章：先说糊涂是什么、怎样被秩序独大扼杀，再分讲先后、样子、关系三种糊涂怎样熬，问熬出什么，最后放到人与 AI 之间，放进教育、健康、事业、婚姻、科研五个领域。</p></div>
<div class="gold">由聪明转入糊涂更难。　　——郑板桥</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 {M.NO} 号 · 约 {WAN} 万字<br>ISBN {M.ISBN} · 定价 {M.PRICE}</div>
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
