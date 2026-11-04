#!/usr/bin/env python3
"""第 483 号《K线人生——跃迁无法设计，只能接住》（段君毅　王德生 著）封面与封底（工具链承自第 571 号，藏青底、金青奶白三色，220 系列版式）：
主图：几条K线缠成的洪流——三条速度各异的线互相缠绕向前，挤进一团碰撞，旧线断成虚线散去，一条新线从碰撞里陡然升起，下面一道托弧（接住）。
全部矢量绘制、纯色，不用照片、不用渐变。封面不写「指导」字样，作者栏写「段君毅　王德生　著」。
用法：python3 cover.py --fonts /usr/share/fonts/opentype/noto --out <dir>
"""
import argparse
import math
import os
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0C1A34', '#1B3158', '#16294A'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#7FA7C9', '#EFE8D6', '#A9B6C8'
ISBN = '979-8-90690-979-4'
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
    """主图（第 511 号）：左下饭桌与灯（见一面），信沿虚线穿过暗处，飞向右上虚线勾出的未见之物。全部矢量、纯色。"""
    s = W / 1700
    out = []
    # 暗处的同心虚弧：场
    tx, ty = W * 0.27, H * 0.735      # 桌心
    for k, r_ in enumerate((190, 290, 400, 520)):
        out.append(f'<circle cx="{tx:.0f}" cy="{ty:.0f}" r="{r_*s:.0f}" fill="none" stroke="{DIM}" stroke-opacity="{.20-.035*k:.2f}" stroke-width="{2*s:.1f}" stroke-dasharray="{4*s:.0f} {11*s:.0f}"/>')
    # 灯：吊线、灯罩、光锥（纯色半透明）
    ly = ty - 215 * s
    out.append(f'<polygon points="{tx-44*s:.0f},{ly:.0f} {tx+44*s:.0f},{ly:.0f} {tx+225*s:.0f},{ty:.0f} {tx-225*s:.0f},{ty:.0f}" fill="{GOLD2}" fill-opacity=".13"/>')
    out.append(f'<line x1="{tx:.0f}" y1="{ly-150*s:.0f}" x2="{tx:.0f}" y2="{ly-44*s:.0f}" stroke="{CREAM}" stroke-width="{2.6*s:.1f}"/>')
    out.append(f'<path d="M{tx-58*s:.0f} {ly:.0f} Q{tx:.0f} {ly-92*s:.0f} {tx+58*s:.0f} {ly:.0f} Z" fill="{GOLD2}"/>')
    # 桌面与两张相对的椅子（两个人的位置空着）
    out.append(f'<ellipse cx="{tx:.0f}" cy="{ty:.0f}" rx="{232*s:.0f}" ry="{50*s:.0f}" fill="{NAVY_TOP}" stroke="{CREAM}" stroke-width="{5*s:.1f}"/>')
    for sg in (-1, 1):
        cx_ = tx + sg * 318 * s
        out.append(f'<path d="M{cx_:.0f} {ty-74*s:.0f} L{cx_:.0f} {ty+98*s:.0f} M{cx_:.0f} {ty+34*s:.0f} L{cx_-sg*62*s:.0f} {ty+34*s:.0f} L{cx_-sg*62*s:.0f} {ty+98*s:.0f}" fill="none" stroke="{CREAM}" stroke-opacity=".82" stroke-width="{5*s:.1f}" stroke-linecap="round" stroke-linejoin="round"/>')
    out.append(f'<line x1="{tx:.0f}" y1="{ty+50*s:.0f}" x2="{tx:.0f}" y2="{ty+132*s:.0f}" stroke="{CREAM}" stroke-opacity=".82" stroke-width="{5*s:.1f}" stroke-linecap="round"/>')
    # 未见之物：虚线大圆，里面的小核只画一半的轮廓
    ux, uy, ur = W * 0.765, H * 0.40, 168 * s
    out.append(f'<circle cx="{ux:.0f}" cy="{uy:.0f}" r="{ur:.0f}" fill="none" stroke="{GOLD2}" stroke-width="{4*s:.1f}" stroke-dasharray="{20*s:.0f} {15*s:.0f}"/>')
    out.append(f'<circle cx="{ux:.0f}" cy="{uy:.0f}" r="{ur*1.32:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".30" stroke-width="{1.8*s:.1f}" stroke-dasharray="{5*s:.0f} {12*s:.0f}"/>')
    out.append(f'<path d="M{ux:.0f} {uy-52*s:.0f} A{52*s:.0f} {52*s:.0f} 0 0 1 {ux:.0f} {uy+52*s:.0f}" fill="none" stroke="{CYAN}" stroke-width="{4*s:.1f}" stroke-linecap="round"/>')
    out.append(f'<path d="M{ux:.0f} {uy-52*s:.0f} A{52*s:.0f} {52*s:.0f} 0 0 0 {ux:.0f} {uy+52*s:.0f}" fill="none" stroke="{CYAN}" stroke-opacity=".45" stroke-width="{3*s:.1f}" stroke-dasharray="{6*s:.0f} {9*s:.0f}"/>')
    # 信的航迹：从桌上升起，金色虚线，进入未见之物
    x0, y0 = tx + 34 * s, ty - 40 * s
    c1, c2 = (W * 0.34, H * 0.47), (W * 0.52, H * 0.60)
    x3, y3 = ux - ur * 0.70, uy + ur * 0.70
    out.append(f'<path d="M{x0:.0f} {y0:.0f} C{c1[0]:.0f} {c1[1]:.0f} {c2[0]:.0f} {c2[1]:.0f} {x3:.0f} {y3:.0f}" fill="none" stroke="{GOLD2}" stroke-width="{3.6*s:.1f}" stroke-dasharray="{15*s:.0f} {11*s:.0f}" stroke-linecap="round"/>')
    # 信：航迹上的一封信（奶白信封、金封缘），略微上仰
    t_ = 0.63
    bx = (1-t_)**3*x0 + 3*(1-t_)**2*t_*c1[0] + 3*(1-t_)*t_**2*c2[0] + t_**3*x3
    by = (1-t_)**3*y0 + 3*(1-t_)**2*t_*c1[1] + 3*(1-t_)*t_**2*c2[1] + t_**3*y3
    ew, eh = 124 * s, 82 * s
    out.append(f'<g transform="translate({bx:.0f} {by:.0f}) rotate(-24)"><rect x="{-ew/2-10*s:.0f}" y="{-eh/2-10*s:.0f}" width="{ew+20*s:.0f}" height="{eh+20*s:.0f}" fill="{NAVY_MID}"/>'
               f'<rect x="{-ew/2:.0f}" y="{-eh/2:.0f}" width="{ew:.0f}" height="{eh:.0f}" fill="{CREAM}" rx="{3*s:.0f}"/>'
               f'<path d="M{-ew/2:.0f} {-eh/2:.0f} L0 {6*s:.0f} L{ew/2:.0f} {-eh/2:.0f}" fill="none" stroke="{GOLD}" stroke-width="{4*s:.1f}" stroke-linejoin="round"/></g>')
    # 注脚：各贴着自己的图
    for xx, yy, anc, big, small, col in ((W * 0.535, ty - 8 * s, 'start', '见一面', '是没信先付账', CREAM), (ux, uy + ur * 1.32 + 62 * s, 'middle', '未见面', '放心是信结的账', GOLD2)):
        out.append(f'<text x="{xx:.0f}" y="{yy:.0f}" font-size="{36*s:.0f}" text-anchor="{anc}" font-family="Noto Serif CJK SC" font-weight="700" fill="{col}" letter-spacing="{4*s:.0f}">{big}</text>')
        out.append(f'<text x="{xx:.0f}" y="{yy + 40*s:.0f}" font-size="{20*s:.0f}" text-anchor="{anc}" font-family="Noto Sans CJK SC" fill="{DIM}" letter-spacing="{3*s:.0f}">{small}</text>')
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 511 号</div>
<div class="t"><div class="big">见面才放心吗？</div>
<div class="sub">科学需要未见面之信</div><div class="rule"></div></div>
<div class="b"><div class="au">王德生　著</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div></div></body></html>"""


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
           f'{background(W, H, "b", split=0.715)}{emb}{"".join(waves)}{bc}</svg>')
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
<div class="c"><div class="lab">母 题</div>
<div class="q">科学需要未见面之信。<br>放心是信结的账；<br>见一面，是没信先付账。</div><div class="by">—— 本书定音句</div><div class="rule"></div>
<div class="bl"><p>中国人信一个人，常常不从他写的东西开始，要见一面才放心。这一面，见到的多半是一幅图像和一个场。本书把信分成三种：见面之信快而不准，实践之信准而太迟，理念之信依据理念的运行，快，而且当下可核对。</p>
<p>从一张饭桌写到一张信用卡，从爱因斯坦那篇没有引文的论文写到李约瑟之问，再写到和大模型见一面。方程写的都是看不见的东西，你得先信，才知道去实践什么。未来的创新，多半是还未见面的科学。</p>
<p>全书没有做统计调查，书中的老陆、叶川都是构想的人物；每章写明怎样算错，结语把本书自己的路标列了出来。</p>
<div class="gold">理念之信是发生的，所以可以学会。</div></div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 511 号 · 七编四十一章 · 约 {WAN} 万字<br>ISBN 979-8-90690-979-4 · 定价 US$20.00</div>
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
