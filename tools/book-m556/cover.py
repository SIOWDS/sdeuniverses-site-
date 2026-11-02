#!/usr/bin/env python3
"""第 556 号《不是工业革命》（王德生 著）封面与封底（工具链承自第 555 号；靛青底，金、青绿点缀，220 系列版式）：
主图：淡色齿轮（约得掉的工具）与两圆相交（人、AI），交集金色透镜是来回里诞生的复合主体。全部纯色，不用渐变。
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
    """主图（第 556 号）：左下一只淡色齿轮（约得掉的工具：工业革命）；右上两圆相交——人与 AI——相交处的金色透镜是在来回里诞生的复合主体；
    两道弧形箭头表示一来一回。纯色，不用渐变与裁剪。"""
    s = W / 1700
    out = []
    # 齿轮（工业革命）
    gx, gy, gr = W * 0.80, H * 0.875, 150 * s
    teeth = 14
    pts = []
    for k in range(teeth * 4):
        ang = 2 * math.pi * k / (teeth * 4)
        r = gr + (24 * s if (k % 4) in (1, 2) else 0)
        pts.append((gx + r * math.cos(ang), gy + r * math.sin(ang)))
    out.append('<path d="M' + ' L'.join('%.1f %.1f' % q for q in pts) + f' Z" fill="none" stroke="{DIM}" stroke-opacity=".38" stroke-width="{4*s:.1f}" stroke-linejoin="round"/>')
    out.append(f'<circle cx="{gx:.0f}" cy="{gy:.0f}" r="{gr*0.42:.0f}" fill="none" stroke="{DIM}" stroke-opacity=".30" stroke-width="{3*s:.1f}"/>')
    out.append(f'<circle cx="{gx:.0f}" cy="{gy:.0f}" r="{gr*0.12:.0f}" fill="{DIM}" fill-opacity=".30"/>')
    # 两圆：人（左）与 AI（右）
    cy = H * 0.585
    r = 250 * s
    c1, c2 = W * 0.53, W * 0.53 + r * 1.05
    out.append(f'<circle cx="{c1:.0f}" cy="{cy:.0f}" r="{r:.0f}" fill="{CREAM}" fill-opacity=".06" stroke="{CREAM}" stroke-opacity=".85" stroke-width="{3.2*s:.1f}"/>')
    out.append(f'<circle cx="{c2:.0f}" cy="{cy:.0f}" r="{r:.0f}" fill="{CYAN}" fill-opacity=".08" stroke="{CYAN}" stroke-opacity=".85" stroke-width="{3.2*s:.1f}"/>')
    # 透镜（交集）
    d = (c2 - c1) / 2
    h = math.sqrt(r * r - d * d)
    mx = (c1 + c2) / 2
    lens = (f'M{mx:.1f} {cy - h:.1f} A{r:.1f} {r:.1f} 0 0 1 {mx:.1f} {cy + h:.1f} '
            f'A{r:.1f} {r:.1f} 0 0 1 {mx:.1f} {cy - h:.1f} Z')
    out.append(f'<path d="{lens}" fill="{GOLD}" fill-opacity=".88"/>')
    out.append(f'<path d="{lens}" fill="none" stroke="{GOLD2}" stroke-width="{2.4*s:.1f}"/>')
    # 一来一回：两道弧形箭头
    for sgn, col in ((-1, GOLD2), (1, GOLD2)):
        y0 = cy + sgn * (r + 70 * s)
        x0, x1 = c1 - r * 0.15, c2 + r * 0.15
        ctrl = cy + sgn * (r + 190 * s)
        dd = f'M{x0:.0f} {y0:.0f} Q{mx:.0f} {ctrl:.0f} {x1:.0f} {y0:.0f}' if sgn < 0 else f'M{x1:.0f} {y0:.0f} Q{mx:.0f} {ctrl:.0f} {x0:.0f} {y0:.0f}'
        out.append(f'<path d="{dd}" fill="none" stroke="{col}" stroke-opacity=".75" stroke-width="{3*s:.1f}" stroke-linecap="round"/>')
        ex, ey = (x1, y0) if sgn < 0 else (x0, y0)
        dirx = 1 if sgn < 0 else -1
        ah = 22 * s
        out.append(f'<path d="M{ex:.0f} {ey:.0f} L{ex - dirx*ah:.0f} {ey - ah*0.8:.0f} M{ex:.0f} {ey:.0f} L{ex - dirx*ah*1.1:.0f} {ey + ah*0.6:.0f}" stroke="{col}" stroke-opacity=".85" stroke-width="{3*s:.1f}" stroke-linecap="round" fill="none"/>')
    lab = lambda x, y, t, col, sz=28, anc='middle', w=400: out.append(f'<text x="{x:.0f}" y="{y:.0f}" font-size="{sz*s:.0f}" text-anchor="{anc}" font-family="Noto Sans CJK SC" font-weight="{w}" fill="{col}" letter-spacing="{4*s:.0f}">{t}</text>')
    lab(c1 - r * 0.45, cy + 10 * s, '人', CREAM, 46)
    lab(c2 + r * 0.45, cy + 10 * s, 'AI', CYAN, 42)
    lab(mx, cy + 12 * s, '谁', '#16253F', 62, w=700)
    lab(mx, cy - r - 132 * s, '一来一回', GOLD2, 24)
    lab(gx - gr - 60 * s, gy + 8 * s, '约得掉的工具', DIM, 22, 'end')
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
<div class="t"><div class="pre">AI 革命 · 主体性革命</div><div class="big big2" style="font-size:{40*s:.1f}pt;line-height:1.36">不是<br>工业革命</div>
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
<div class="q">工业革命改变人能做什么，<br>AI 革命改变的是「谁」在做。</div><div class="by">——本书母题</div><div class="rule"></div>
<div class="bl"><p>蒸汽机、电、汽车，延伸的是手和腿；人还是那个人，力气大了、跑得远了。这些工具在账上约得掉：对谁都一样，不因使用而改变，所以“我切菜”可以省略刀，革命只落在产业上。</p>
<p>AI 约不掉。它会作声、会学、会回写，人和它一来一回，就有一个新的复合主体在思考。主体从先在者变为发生者——这是一次主体性革命，是存在论的问题，不是又一套新理论。</p>
<p>每一行都建在一个默认先在的“谁”上：谁咨询、谁学习、谁创造价值、谁投票、谁负责、谁看病、谁发现、谁说话、谁做事、谁创作。本书走过心理咨询、教育、经济、政治、法律、医疗、科研、出版与媒体、企业管理、艺术十个行业，每一行都先问：这一行的新主体（角色-AI）怎样诞生？再谈这一行的理论、制度与新行当。</p>
<p>全书前言、导论、十二编五十一章、附录与可证伪清单。研究性学术专著：母题由王德生提出，正文由 AI（Claude）协作撰写，经统稿与三审；人物与场景多为构想，无实测数据，无独立学术评审。</p></div>
<div class="gold">理论之前，先问「谁」。</div></div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 {M.NO} 号 · 前言、导论、十二编五十一章、附录 · 约 {WAN} 万字<br>ISBN {M.ISBN} · 定价 {M.PRICE}</div>
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
