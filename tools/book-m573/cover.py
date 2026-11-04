#!/usr/bin/env python3
"""第 573 号《从聪明到智慧——行动哲学的修炼之路》（王德生　王涛 著）封面与封底（工具链承自第 571 号，藏青底、金青奶白三色，220 系列版式）：
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
ISBN = '978-1-970820-06-5'
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
    """主图（第 573 号）：左下一圈闭环（聪明），中间一方蓝图格（智能），右上三芒星环（智慧：创造、自由、幸福）；
    一条金色虚线从闭环里挣出，两次折上（两次跃迁），穿过蓝图格，进入星环。全部矢量、纯色。"""
    s = W / 1700
    out = []
    # 聪明：闭环（椭圆 + 三段箭头），奶白
    lx, ly, lrx, lry = W * 0.22, H * 0.69, 190 * s, 72 * s
    out.append(f'<ellipse cx="{lx:.0f}" cy="{ly:.0f}" rx="{lrx:.0f}" ry="{lry:.0f}" fill="none" stroke="{CREAM}" stroke-opacity=".85" stroke-width="{5*s:.1f}"/>')
    out.append(f'<ellipse cx="{lx:.0f}" cy="{ly:.0f}" rx="{lrx*1.28:.0f}" ry="{lry*1.36:.0f}" fill="none" stroke="{DIM}" stroke-opacity=".28" stroke-width="{2*s:.1f}" stroke-dasharray="{5*s:.0f} {12*s:.0f}"/>')
    for t in (20, 140, 260):
        a = math.radians(t)
        px, py = lx + lrx * math.cos(a), ly + lry * math.sin(a)
        dx, dy = -lrx * math.sin(a), lry * math.cos(a)
        n = math.hypot(dx, dy); dx, dy = dx / n, dy / n
        nx, ny = -dy, dx
        k = 22 * s
        out.append(f'<polygon points="{px+dx*k:.0f},{py+dy*k:.0f} {px-dx*k*.6+nx*k*.7:.0f},{py-dy*k*.6+ny*k*.7:.0f} {px-dx*k*.6-nx*k*.7:.0f},{py-dy*k*.6-ny*k*.7:.0f}" fill="{CREAM}"/>')
    # 智能：蓝图格（方框 + 网格 + 对角推演线），青色
    gx, gy, gs = W * 0.44, H * 0.47, 250 * s
    out.append(f'<rect x="{gx:.0f}" y="{gy:.0f}" width="{gs:.0f}" height="{gs:.0f}" fill="{NAVY_TOP}" fill-opacity=".55" stroke="{CYAN}" stroke-width="{4*s:.1f}"/>')
    for k in range(1, 5):
        out.append(f'<line x1="{gx+gs*k/5:.0f}" y1="{gy:.0f}" x2="{gx+gs*k/5:.0f}" y2="{gy+gs:.0f}" stroke="{CYAN}" stroke-opacity=".32" stroke-width="{1.6*s:.1f}"/>')
        out.append(f'<line x1="{gx:.0f}" y1="{gy+gs*k/5:.0f}" x2="{gx+gs:.0f}" y2="{gy+gs*k/5:.0f}" stroke="{CYAN}" stroke-opacity=".32" stroke-width="{1.6*s:.1f}"/>')
    out.append(f'<polyline points="{gx+gs*.1:.0f},{gy+gs*.85:.0f} {gx+gs*.4:.0f},{gy+gs*.6:.0f} {gx+gs*.6:.0f},{gy+gs*.65:.0f} {gx+gs*.9:.0f},{gy+gs*.2:.0f}" fill="none" stroke="{CYAN}" stroke-width="{3.6*s:.1f}" stroke-linejoin="round"/>')
    for fx, fy in ((.1, .85), (.4, .6), (.6, .65), (.9, .2)):
        out.append(f'<circle cx="{gx+gs*fx:.0f}" cy="{gy+gs*fy:.0f}" r="{7*s:.1f}" fill="{CREAM}"/>')
    # 智慧：三芒星环，金色
    ux, uy, ur = W * 0.80, H * 0.25, 120 * s
    out.append(f'<circle cx="{ux:.0f}" cy="{uy:.0f}" r="{ur:.0f}" fill="none" stroke="{GOLD2}" stroke-width="{4*s:.1f}"/>')
    out.append(f'<circle cx="{ux:.0f}" cy="{uy:.0f}" r="{ur*1.45:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".30" stroke-width="{1.8*s:.1f}" stroke-dasharray="{5*s:.0f} {12*s:.0f}"/>')
    for t in (-90, 30, 150):
        a = math.radians(t)
        ex, ey = ux + ur * 1.02 * math.cos(a), uy + ur * 1.02 * math.sin(a)
        out.append(f'<line x1="{ux:.0f}" y1="{uy:.0f}" x2="{ex:.0f}" y2="{ey:.0f}" stroke="{GOLD2}" stroke-width="{4*s:.1f}" stroke-linecap="round"/>')
        out.append(f'<circle cx="{ex:.0f}" cy="{ey:.0f}" r="{15*s:.1f}" fill="{GOLD2}"/>')
    out.append(f'<circle cx="{ux:.0f}" cy="{uy:.0f}" r="{24*s:.1f}" fill="{CREAM}"/>')
    # 修炼之路：从闭环挣出，两次折上（跃迁），穿过蓝图格，进入星环
    p0 = (lx + lrx * 0.92, ly - lry * 0.40)
    j1 = (gx - 80 * s, gy + gs * 0.97)
    j1b = (gx + gs * .1, gy + gs * .85)
    j2 = (gx + gs * .9, gy + gs * .2)
    j2b = (ux - ur * 1.05, uy + ur * 1.05)
    d = (f'M{p0[0]:.0f} {p0[1]:.0f} C{p0[0]+120*s:.0f} {p0[1]-30*s:.0f} {j1[0]-90*s:.0f} {j1[1]+40*s:.0f} {j1[0]:.0f} {j1[1]:.0f} '
         f'L{j1b[0]:.0f} {j1b[1]:.0f} M{j2[0]:.0f} {j2[1]:.0f} C{j2[0]+60*s:.0f} {j2[1]-30*s:.0f} {j2b[0]-70*s:.0f} {j2b[1]+50*s:.0f} {j2b[0]:.0f} {j2b[1]:.0f}')
    out.append(f'<path d="{d}" fill="none" stroke="{GOLD2}" stroke-width="{3.6*s:.1f}" stroke-dasharray="{15*s:.0f} {11*s:.0f}" stroke-linecap="round"/>')
    for (cx_, cy_) in (j1, j2):
        r_ = 17 * s
        out.append(f'<polygon points="{cx_:.0f},{cy_-r_:.0f} {cx_+r_:.0f},{cy_:.0f} {cx_:.0f},{cy_+r_:.0f} {cx_-r_:.0f},{cy_:.0f}" fill="{GOLD}" stroke="{NAVY_TOP}" stroke-width="{3*s:.1f}"/>')
    # 注脚
    notes = ((lx, ly + lry + 70 * s, 'middle', '聪明', '优化闭环 · 发展逻辑', CREAM),
             (gx + gs / 2, gy + gs + 64 * s, 'middle', '智能', '建模出题 · 形式逻辑', CYAN),
             (ux, uy + ur * 1.45 + 58 * s, 'middle', '智慧', '变权生成 · 发生逻辑', GOLD2))
    for xx, yy, anc, big, small, col in notes:
        out.append(f'<text x="{xx:.0f}" y="{yy:.0f}" font-size="{34*s:.0f}" text-anchor="{anc}" font-family="Noto Serif CJK SC" font-weight="700" fill="{col}" letter-spacing="{6*s:.0f}">{big}</text>')
        out.append(f'<text x="{xx:.0f}" y="{yy + 38*s:.0f}" font-size="{19*s:.0f}" text-anchor="{anc}" font-family="Noto Sans CJK SC" fill="{DIM}" letter-spacing="{3*s:.0f}">{small}</text>')
    for (cx_, cy_), txt, anc, dx_ in ((j1, '解题 → 出题', 'end', -30), (j2, '守规 → 变权', 'start', 30)):
        out.append(f'<text x="{cx_+dx_*s:.0f}" y="{cy_+8*s:.0f}" font-size="{20*s:.0f}" text-anchor="{anc}" font-family="Noto Sans CJK SC" fill="{GOLD2}" letter-spacing="{2*s:.0f}">{txt}</text>')
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 573 号</div>
<div class="t"><div class="big">从聪明到智慧</div>
<div class="sub">行动哲学的修炼之路</div><div class="rule"></div></div>
<div class="b"><div class="au">王德生　王涛　著</div><div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div></div></div></body></html>"""


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
<div class="q">真正的困境不是不够努力，<br>而是努力被锁死在错误层级。<br>智慧不是更会算，而是更会发生。</div><div class="by">—— 本书定音句</div><div class="rule"></div>
<div class="bl"><p>现代生活奖励聪明：执行更快、指标更紧、战术更精。可越来越多的高绩效者发现，优化得越高效，就越焦虑、越疲惫、越空洞。问题不在不够努力，而在意义层的问题被压进了路径层去解决。</p>
<p>本书把聪明、智能、智慧放回三个层级：聪明是发展逻辑的优化闭环，智能是形式逻辑的建模工艺，智慧是发生逻辑的原创与规范生成。两次跃迁——从解题到出题，从守规到变权——构成修炼之路的主脊梁。</p>
<p>每章都有训练与验收；第六编把整本书压成跃迁总表、全系统重写清单、自评量表与五张随身方法卡。</p>
<div class="gold">当努力越来越空，先换一层用力。</div></div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 573 号 · 六编二十一章 · 约 {WAN} 万字<br>ISBN 978-1-970820-06-5 · 定价 US$45.00</div>
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
