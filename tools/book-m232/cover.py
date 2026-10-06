#!/usr/bin/env python3
"""第 232 号《SDE红学》封面与封底：沿用作者书稿自带的封面设计（酒红上幅、米白下幅、飘落的花瓣、朱文「情」印），
按印刷尺寸重画成矢量，补上专著编号、ISBN 条码与定价。

用法：python3 cover.py --fonts /usr/share/fonts --out <out>
产物：cover-print.pdf / back-print.pdf（170×240）、cover-reader.pdf / back-reader.pdf（190×250）、
      cover.jpg / backcover.jpg（1004 宽，站上用）
"""
import argparse
import random
import re
from pathlib import Path

RED, RED2, CREAM, INK, GOLD, PINK = '#7A1F26', '#8E2B33', '#F1E9DA', '#2A2622', '#C9A46A', '#D9A0A0'
ISBN = '979-8-90690-683-0'
NO = 232

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


def petals(W, H, split, seed, n_top=9, n_bot=9, edge=False):
    """飘落的花瓣：上幅用浅色（金、粉），下幅用红。避开中间的文字带。"""
    rnd = random.Random(seed)
    out = []

    def one(x, y, size, rot, fill, op):
        out.append(f'<path transform="translate({x:.0f} {y:.0f}) rotate({rot:.0f}) scale({size:.2f})" '
                   f'd="M0 -30 C14 -14 12 14 0 30 C-9 12 -11 -12 0 -30 Z" fill="{fill}" fill-opacity="{op:.2f}"/>')
    for i in range(n_top):
        side = i % 2
        x = rnd.uniform(.08, .24) * W if side else rnd.uniform(.76, .92) * W
        y = rnd.uniform(.10, .92) * split
        one(x, y, rnd.uniform(.9, 1.5) * W / 1700, rnd.uniform(-60, 60), rnd.choice([GOLD, PINK, '#E3C58E']), rnd.uniform(.75, .95))
    for i in range(n_bot):
        side = i % 2
        if edge:   # 封底：只落在版心外的两条边上，不压文字与条码
            x = rnd.uniform(.055, .125) * W if side else rnd.uniform(.875, .945) * W
            y = split + rnd.uniform(.08, .62) * (H - split)
        else:
            x = rnd.uniform(.08, .28) * W if side else rnd.uniform(.72, .92) * W
            y = split + rnd.uniform(.06, .78) * (H - split)
        one(x, y, rnd.uniform(1.0, 1.6) * W / 1700, rnd.uniform(-70, 70), rnd.choice([RED, RED2, '#A8343C']), rnd.uniform(.8, .95))
    return ''.join(out)


def base(W, H, split, seed):
    lines = ''.join(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="#000" stroke-opacity=".035" stroke-width="2"/>' for y in range(0, int(split), 26))
    m = W * 0.042
    return (f'<rect width="{W}" height="{H}" fill="{CREAM}"/><rect width="{W}" height="{split:.0f}" fill="{RED}"/>'
            f'<rect y="{split*0.45:.0f}" width="{W}" height="{split*0.55:.0f}" fill="{RED2}" fill-opacity=".55"/>{lines}'
            f'{petals(W, H, split, seed)}'
            f'<rect x="{m:.0f}" y="{m:.0f}" width="{W-2*m:.0f}" height="{H-2*m:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".55" stroke-width="{W/600:.1f}"/>')


def front(Wmm, Hmm):
    W, H = Wmm * 10, Hmm * 10
    s = Wmm / 170
    split = H * 0.58
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{Wmm}mm" height="{Hmm}mm">{base(W, H, split, 7)}</svg>'
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page{{size:{Wmm}mm {Hmm}mm;margin:0}} body{{margin:0}}
.pg{{position:relative;width:{Wmm}mm;height:{Hmm}mm;overflow:hidden;text-align:center}}
.pg svg{{position:absolute;left:0;top:0}}
.a{{position:absolute;left:0;right:0}}
.ser{{top:{19*s:.1f}mm;font:400 {8.6*s:.1f}pt 'Noto Sans CJK SC';color:#EBD9B4;letter-spacing:.3em}}
.ser i{{display:block;width:{38*s:.1f}mm;border-top:.7pt solid {GOLD};opacity:.7;margin:{3.4*s:.1f}mm auto 0}}
.sde{{top:{34*s:.1f}mm;font:900 {74*s:.1f}pt/1 'Noto Sans CJK SC';color:#FBF6EA;letter-spacing:.02em}}
.hx{{top:{71*s:.1f}mm;font:500 {60*s:.1f}pt/1.15 'Noto Serif CJK SC';color:#FBF6EA;letter-spacing:.75em;text-indent:.75em}}
.ln{{top:{108.5*s:.1f}mm}} .ln i{{display:block;width:{66*s:.1f}mm;border-top:.8pt solid {GOLD};opacity:.75;margin:0 auto}}
.sub{{top:{112.5*s:.1f}mm;font:400 {15.5*s:.1f}pt 'Noto Serif CJK SC';color:#F6ECD8;letter-spacing:.3em;text-indent:.3em}}
.tag{{top:{124.5*s:.1f}mm;font:400 {8.8*s:.1f}pt 'Noto Serif CJK SC';color:#EBD9B4;letter-spacing:.08em}}
.seal{{top:{161*s:.1f}mm}} .seal b{{display:inline-block;width:{12.4*s:.1f}mm;height:{12.4*s:.1f}mm;border:{.75*s:.2f}mm solid #A8242C;border-radius:{1.4*s:.1f}mm;
  font:500 {22*s:.1f}pt/{12.4*s:.1f}mm 'Noto Serif CJK SC';color:#A8242C}}
.au{{top:{181*s:.1f}mm;font:500 {20*s:.1f}pt 'Noto Serif CJK SC';color:{INK};letter-spacing:.85em;text-indent:.85em}}
.pub{{bottom:{15*s:.1f}mm;font:400 {10.6*s:.1f}pt 'Noto Serif CJK SC';color:#5A4A3A;letter-spacing:.4em;text-indent:.4em}}
.pub i{{display:block;width:{42*s:.1f}mm;border-top:.7pt solid {GOLD};margin:0 auto {3.2*s:.1f}mm}}
.pub span{{display:block;font:400 {6.2*s:.1f}pt 'Noto Sans CJK SC';color:#8A6F55;letter-spacing:.12em;text-indent:0;margin-top:{1.4*s:.1f}mm}}
</style></head><body><div class="pg">{svg}
<div class="a ser">德麦国际 · SDE 思想体系 · 专著第 {NO} 号<i></i></div>
<div class="a sde">SDE</div><div class="a hx">红学</div><div class="a ln"><i></i></div>
<div class="a sub">情悲发生学 · 空化解释学</div><div class="a tag">—— 一部《红楼梦》的发生学重读 ——</div>
<div class="a seal"><b>情</b></div><div class="a au">王德生 著</div>
<div class="a pub"><i></i>德麦国际出版社<span>DEMAI INTERNATIONAL PRESS · SINGAPORE</span></div>
</div></body></html>"""


def back(Wmm, Hmm):
    W, H = Wmm * 10, Hmm * 10
    s = Wmm / 170
    split = H * 0.16
    bc = barcode(W - 150 * s - 358 * s, H - 150 * s - 300 * s, s)
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{Wmm}mm" height="{Hmm}mm">{base(W, H, split, 23).replace(petals(W, H, split, 23), petals(W, H, split, 23, 3, 7, edge=True))}{bc}</svg>'
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page{{size:{Wmm}mm {Hmm}mm;margin:0}} body{{margin:0}}
.pg{{position:relative;width:{Wmm}mm;height:{Hmm}mm;overflow:hidden}}
.pg svg{{position:absolute;left:0;top:0}}
.hd{{position:absolute;left:0;right:0;top:{14.5*s:.1f}mm;text-align:center;font:400 {12*s:.1f}pt 'Noto Serif CJK SC';color:#FBF6EA;letter-spacing:.5em;text-indent:.5em}}
.c{{position:absolute;left:{30*s:.1f}mm;right:{30*s:.1f}mm;top:{52*s:.1f}mm;color:{INK}}}
.lab{{font:700 {7.4*s:.1f}pt 'Noto Sans CJK SC';color:#A8242C;letter-spacing:.5em}}
.q{{font:700 {19*s:.1f}pt/1.7 'Noto Serif CJK SC';color:{RED};margin:{3.5*s:.1f}mm 0 {1.5*s:.1f}mm;letter-spacing:.08em}}
.by{{font:400 {8.2*s:.1f}pt 'Noto Serif CJK SC';color:#8A6F55}}
.rule{{width:{14*s:.1f}mm;border-top:.9pt solid {GOLD};margin:{6.5*s:.1f}mm 0 {5.5*s:.1f}mm}}
.bl p{{font:400 {8.9*s:.1f}pt/1.95 'Noto Serif CJK SC';color:{INK};margin:0 0 {2.6*s:.1f}mm;text-align:justify}}
.gold{{font:700 {10.5*s:.1f}pt 'Noto Serif CJK SC';color:{RED};margin-top:{5*s:.1f}mm;letter-spacing:.06em}}
.f{{position:absolute;left:{30*s:.1f}mm;bottom:{17*s:.1f}mm;font:400 {7.2*s:.1f}pt/1.85 'Noto Sans CJK SC';color:#6A5A4A}}
.f b{{color:{INK};font-weight:700;letter-spacing:.12em}}
</style></head><body><div class="pg">{svg}
<div class="hd">SDE 红学</div>
<div class="c"><div class="lab">一 句 话</div>
<div class="q">情，不肯被空收编。</div><div class="by">——本书题词</div><div class="rule"></div>
<div class="bl"><p>历来解红楼者，多问它“是什么”：索隐者问它藏着什么真事，考证者问它出自谁的手笔，色空论者问它归于何种了悟。本书换一个问法：它如何如此发生。</p>
<p>前八十回是一部情悲发生学：创造、自由、幸福，在那座宅子里得一样便锁死另两样，连到手的也留不住；人人如此，而情越真的人，输得越尽。后四十回是一套空化解释学：把这股敞开的张力，从世俗与归空两头焊死。</p>
<p>上篇三十七章讲这台引擎的原理与接续工程，中篇细读十八个名场面，下篇把它带进今天的教育、健康与商业。</p></div>
<div class="gold">情越真，输越尽。</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 {NO} 号 · 上中下三篇 · 约 21 万字<br>定价 US$20.00</div>
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
