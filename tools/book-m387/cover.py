#!/usr/bin/env python3
"""第 387 号封面与封底（220 系列藏青金色，主图改为飘舞的五线谱丝带与音符）：藏青渐变底、细点阵、金色光晕与刻度环；
主图是楼顶一只木槽里正在长出来的豆苗，左边远处一座城门，一串金色脚印从城门走到苗前。

用法：python3 cover.py --fonts /home/claude/fonts --out /home/claude/mengzi/build
产物：cover-print.pdf / back-print.pdf（170×240）、cover-reader.pdf / back-reader.pdf（190×250）、
      cover.jpg / backcover.jpg（1004×1418，站上用）
"""
import argparse
import math
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0B1830', '#1B3158', '#142746'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#58BDCA', '#EFE8D6', '#9FB0C8'
ISBN = '979-8-90690-928-2'

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


def staff_path(W, H):
    """一条 S 形飘带的中线：从右下卷起，绕到左侧甩出一个大弧，再掠过中部，扬向右上。避开左上标题区与左下署名区。"""
    P = [((1.08 * W, .97 * H), (.70 * W, 1.03 * H), (.22 * W, .93 * H), (.24 * W, .72 * H)),
         ((.24 * W, .72 * H), (.26 * W, .54 * H), (.80 * W, .66 * H), (.74 * W, .47 * H)),
         ((.74 * W, .47 * H), (.69 * W, .31 * H), (.40 * W, .44 * H), (.58 * W, .31 * H)),
         ((.58 * W, .31 * H), (.72 * W, .22 * H), (.92 * W, .30 * H), (1.08 * W, .14 * H))]
    pts = []
    for seg in P:
        for i in range(50):
            pts.append(bez(*seg, i / 50))
    pts.append(P[-1][3])
    return pts


def offset_lines(pts, s, gap=24):
    n = len(pts); lines = [[] for _ in range(5)]; frames = []
    for i, (x, y) in enumerate(pts):
        a = pts[max(i - 1, 0)]; b = pts[min(i + 1, n - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]; ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln, dx / ln
        t = i / (n - 1)
        spread = gap * s * (0.22 + 1.35 * abs(math.sin(math.pi * (t * 3.4 + .1))) ** 1.3)   # 丝带拧转：线距时宽时窄，窄处像侧过身
        frames.append((x, y, nx, ny, math.degrees(math.atan2(dy, dx)), spread))
        for k in range(5):
            lines[k].append((x + nx * (k - 2) * spread, y + ny * (k - 2) * spread))
    return lines, frames


def note_svg(x, y, size, rot, col, kind):
    """一枚音符：椭圆符头＋符干＋符尾（kind=1 八分，2 十六分，0 四分）；整体按 rot 倾斜。"""
    r = size
    head = f'<ellipse cx="0" cy="0" rx="{r*1.28:.1f}" ry="{r*.92:.1f}" transform="rotate(-24)" fill="{col}"/>'
    sx = r * 1.12
    stem = f'<line x1="{sx:.1f}" y1="{-r*.25:.1f}" x2="{sx:.1f}" y2="{-r*5.4:.1f}" stroke="{col}" stroke-width="{r*.34:.1f}" stroke-linecap="round"/>'
    flag = ''
    for j in range(kind):
        yy = -r * 5.4 + j * r * 1.1
        flag += (f'<path d="M{sx:.1f} {yy:.1f} C{sx+r*1.6:.1f} {yy+r*.5:.1f} {sx+r*2.4:.1f} {yy+r*1.6:.1f} {sx+r*1.4:.1f} {yy+r*3.0:.1f} '
                 f'C{sx+r*1.9:.1f} {yy+r*1.6:.1f} {sx+r*.9:.1f} {yy+r*1.0:.1f} {sx:.1f} {yy+r*1.1:.1f} Z" fill="{col}"/>')
    return f'<g transform="translate({x:.1f} {y:.1f}) rotate({rot:.1f})">{head}{stem}{flag}</g>'


def art(W, H, uid):
    s = W / 1700
    out = []
    # 背后一圈淡淡的光晕与刻度环（沿用丛书的金色环），偏右上
    out.append(rings(W * .72, H * .50, 300 * s).replace('{uid}', uid))
    for r_, op_ in [(170, .30), (235, .20), (300, .12)]:   # 从环心向外扩开的声波弧
        out.append(f'<path d="M{W*.72+r_*s*math.cos(math.radians(-60)):.0f} {H*.50+r_*s*math.sin(math.radians(-60)):.0f} A{r_*s:.0f} {r_*s:.0f} 0 0 1 {W*.72+r_*s*math.cos(math.radians(40)):.0f} {H*.50+r_*s*math.sin(math.radians(40)):.0f}" fill="none" stroke="{CYAN}" stroke-opacity="{op_}" stroke-width="{3*s:.1f}" stroke-linecap="round"/>')
    pts = staff_path(W, H)
    lines, frames = offset_lines(pts, s)
    n = len(pts)
    # 丝带：五条谱线，由粗到细、由亮到暗；线间淡金填充让它像一条有宽度的飘带
    ribbon = lines[0] + lines[4][::-1]
    out.append('<path d="M' + ' L'.join('%.1f %.1f' % p for p in ribbon) + f' Z" fill="{GOLD}" fill-opacity=".07"/>')
    for k, ln in enumerate(lines):
        for seg in range(0, n - 1, 6):
            sub = ln[seg:seg + 7]
            if len(sub) < 2: continue
            t = seg / n
            op = .25 + .65 * math.sin(math.pi * min(1, t * 1.05)) ** 1.2
            col = GOLD2 if k in (0, 4) else GOLD
            wd = (3.4 - abs(k - 2) * .5) * s * (0.55 + 0.9 * math.sin(math.pi * t))
            out.append('<polyline points="%s" fill="none" stroke="%s" stroke-opacity="%.2f" stroke-width="%.2f" stroke-linecap="round"/>' % (
                ' '.join('%.1f,%.1f' % p for p in sub), col, op, wd))
    # 舞动的音符：位置沿丝带，落在不同谱线上，朝向跟着丝带的切线再加一点“扭”
    plan = [(.04, 2, 3.0, 1, CREAM, 24), (.10, 0, 2.5, 0, GOLD2, -26), (.17, 4, 3.4, 2, CREAM, 30), (.24, 1, 2.6, 1, CYAN, -20),
            (.31, 3, 3.2, 0, GOLD2, 36), (.38, 0, 2.4, 2, CREAM, -32), (.45, 4, 3.5, 1, GOLD2, 22), (.52, 2, 2.7, 0, CYAN, -38),
            (.59, 1, 3.3, 2, CREAM, 28), (.66, 3, 2.5, 1, GOLD2, -24), (.73, 0, 3.4, 0, CREAM, 34), (.80, 4, 2.8, 2, CYAN, -30),
            (.87, 2, 3.2, 1, GOLD2, 20), (.94, 1, 2.6, 0, CREAM, -36)]
    for t, k, sz, kind, col, wig in plan:
        i = min(n - 1, int(t * (n - 1)))
        x, y, nx, ny, ang, sp = frames[i]
        px, py = lines[k][i]
        if (px < .56 * W and py < .30 * H) or (px < .40 * W and py > .86 * H) or py > .94 * H or px > .97 * W or py < .04 * H: continue
        # 离开谱线一点点，像跳起来
        lift = (18 + 24 * math.sin(t * 17)) * s
        px += nx * lift * (1 if k >= 2 else -1); py += ny * lift * (1 if k >= 2 else -1)
        out.append(f'<circle cx="{px:.0f}" cy="{py:.0f}" r="{sz*9*s:.0f}" fill="{col}" fill-opacity=".10"/>')
        out.append(note_svg(px, py, sz * 6.2 * s, wig + ang * .12, col, kind))
        # 音符身后拖一小段运动轨迹
        out.append(f'<path d="M{px-nx*60*s-60*s*math.cos(math.radians(ang)):.0f} {py-ny*60*s-60*s*math.sin(math.radians(ang)):.0f} Q{px-30*s*math.cos(math.radians(ang)):.0f} {py-30*s*math.sin(math.radians(ang))-26*s:.0f} {px:.0f} {py:.0f}" fill="none" stroke="{col}" stroke-opacity=".28" stroke-width="{2.2*s:.1f}" stroke-dasharray="{8*s:.0f} {9*s:.0f}" stroke-linecap="round"/>')
    # 飘出来的小光点
    for k in range(42):
        t = (k * 0.0237 + .02) % 1
        i = min(n - 1, int(t * (n - 1))); x, y, nx, ny, ang, sp = frames[i]
        d = (60 + (k * 53) % 170) * s * (1 if k % 2 else -1)
        out.append(f'<circle cx="{x+nx*d:.0f}" cy="{y+ny*d:.0f}" r="{(2.2+(k%4))*s:.1f}" fill="{CREAM if k%3 else CYAN}" fill-opacity="{.25+.08*(k%4):.2f}"/>')
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
.t{{position:absolute;left:{17*s:.1f}mm;top:{19*s:.1f}mm;color:{CREAM}}}
.big{{font:700 {50*s:.1f}pt/1.18 'Noto Serif CJK SC';letter-spacing:.06em;color:#F7F1E3;margin:0 0 {2*s:.1f}mm {-1*s:.1f}mm;text-shadow:0 0 {6*s:.1f}mm rgba(11,24,48,.9)}}
.en{{font:400 {8.2*s:.1f}pt 'Liberation Serif';letter-spacing:.34em;color:{GOLD2};text-transform:uppercase}}
.rule{{width:{16*s:.1f}mm;border-top:.9pt solid {GOLD};margin-top:{5*s:.1f}mm}}
.b{{position:absolute;left:{17*s:.1f}mm;bottom:{16*s:.1f}mm}}
.au{{font:400 {13*s:.1f}pt 'Noto Serif CJK SC';color:{CREAM};letter-spacing:.34em}}
.pe{{font:400 {6.8*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.12em;margin-top:{3*s:.1f}mm}}
.no{{position:absolute;right:{15*s:.1f}mm;top:{16*s:.1f}mm;font:400 {6.8*s:.1f}pt 'Noto Sans CJK SC';color:{DIM};letter-spacing:.22em;text-align:right}}
</style></head><body><div class="pg">{svg}
<div class="no">No. 387</div>
<div class="t"><div class="big">好听<br>是谁的？</div><div class="rule"></div></div>
<div class="b"><div class="au">胡敏</div><div class="pe">DEMAI INTERNATIONAL PRESS</div></div>
</div></body></html>"""


def back(Wmm, Hmm, F):
    W, H = Wmm * 10, Hmm * 10
    s = Wmm / 170
    # 封底：丝带的尾巴再飘一次（只画谱线与三两个音符），其余留白
    pts = []
    seg = ((-.05 * W, .22 * H), (.25 * W, .30 * H), (.60 * W, .10 * H), (1.05 * W, .20 * H))
    for i in range(80): pts.append(bez(*seg, i / 80))
    lines, frames = offset_lines(pts, s, gap=13)
    wav = []
    for k, ln in enumerate(lines):
        wav.append('<polyline points="%s" fill="none" stroke="%s" stroke-opacity="%.2f" stroke-width="%.2f" stroke-linecap="round"/>' % (
            ' '.join('%.1f,%.1f' % p for p in ln), GOLD, .22 + .1 * (k in (0, 4)), 2.4 * s))
    for t, k, sz, kind, col, wig in [(.22, 1, 2.0, 1, CREAM, -20), (.45, 3, 2.4, 0, GOLD2, 24), (.74, 2, 2.2, 2, CYAN, -30)]:
        i = int(t * 79); x, y, nx, ny, ang, sp = frames[i]
        wav.append(note_svg(lines[k][i][0], lines[k][i][1] - 26 * s, sz * 6 * s, wig, col, kind))
    bc, bw = barcode(W - 170 * s - 380 * s, H - 150 * s - 300 * s, s)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{Wmm}mm" height="{Hmm}mm">'
           f'{background(W, H, "b")}{"".join(wav)}{bc}</svg>')
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{fontface(F)}
@page{{size:{Wmm}mm {Hmm}mm;margin:0}} body{{margin:0}}
.pg{{position:relative;width:{Wmm}mm;height:{Hmm}mm;overflow:hidden}}
.pg svg{{position:absolute;left:0;top:0}}
.c{{position:absolute;left:{17*s:.1f}mm;top:{70*s:.1f}mm;width:{128*s:.1f}mm;color:{CREAM}}}
.q{{font:700 {19*s:.1f}pt/1.7 'Noto Serif CJK SC';color:#F7F1E3;letter-spacing:.06em}}
.rule{{width:{14*s:.1f}mm;border-top:.9pt solid {GOLD};margin:{8*s:.1f}mm 0 0}}
.f{{position:absolute;left:{17*s:.1f}mm;bottom:{17*s:.1f}mm;font:400 {7.2*s:.1f}pt/1.85 'Noto Sans CJK SC';color:{DIM};letter-spacing:.06em}}
.f b{{color:{CREAM};font-weight:700;letter-spacing:.14em}}
</style></head><body><div class="pg">{svg}
<div class="c"><div class="q">谁能唱它，<br>它就是谁的。</div><div class="rule"></div></div>
<div class="f"><b>DEMAI INTERNATIONAL PRESS</b><br>No. 387 · US$20.00</div>
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
