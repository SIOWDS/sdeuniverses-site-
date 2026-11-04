#!/usr/bin/env python3
"""第 576 号《AI来了，你往哪里躲？》（王德生 著）封面与封底（工具链承自第 547 号，藏青底、金青奶白三色，220 系列版式）：
主图：七间亮着灯的小屋排在地上，一圈金环悬在上空，光线落到每一间；屋外站着一个人，手里举着一张账单。全部纯色，不用渐变。
用法：python3 cover.py --fonts /usr/share/fonts/opentype/noto --out <dir>
"""
import argparse
import math
import os
import re
from pathlib import Path

NAVY_TOP, NAVY_MID, NAVY_LOW = '#0C1A34', '#1B3158', '#16294A'
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#7FA7C9', '#EFE8D6', '#A9B6C8'
ISBN = '979-8-90690-596-3'
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
    """主图（第 576 号）：七间小屋排在地上，是七个躲处；上空一圈金环，光线落到每一间，没有照不到的；
    屋外一个人转过身来，手里一页账。底下三样：材料、工具、环境。全部纯色，不用渐变。"""
    s = W / 1700
    out = []
    yg = H * 0.70                         # 地平线
    yb = H * 0.755
    gx, gy = W * 0.5, H * 0.452           # 金环圆心
    # 七间小屋：x 位置
    xs = [W * (0.085 + 0.1375 * i) for i in range(7)]
    hs = [150, 118, 168, 132, 176, 124, 158]
    ws = [112, 100, 118, 104, 120, 102, 114]
    # 光线：从环落到每一间屋顶
    for x, h in zip(xs, hs):
        out.append(f'<line x1="{gx:.0f}" y1="{gy:.0f}" x2="{x:.0f}" y2="{yg - h*s - 40*s:.0f}" stroke="{GOLD2}" stroke-opacity=".34" stroke-width="{2.2*s:.1f}"/>')
    # 金环
    for r, op, wd in ((122, .22, 2.2), (92, .46, 2.6), (62, 1, 4.2)):
        out.append(f'<circle cx="{gx:.0f}" cy="{gy:.0f}" r="{r*s:.0f}" fill="none" stroke="{GOLD2}" stroke-opacity="{op}" stroke-width="{wd*s:.1f}"/>')
    out.append(f'<circle cx="{gx:.0f}" cy="{gy:.0f}" r="{13*s:.0f}" fill="{GOLD2}"/>')
    # 地面
    out.append(f'<rect x="0" y="{yg:.0f}" width="{W}" height="{yb - yg:.0f}" fill="{NAVY_TOP}" fill-opacity=".72"/>')
    out.append(f'<line x1="0" y1="{yg:.0f}" x2="{W}" y2="{yg:.0f}" stroke="{GOLD}" stroke-opacity=".75" stroke-width="{2.6*s:.1f}"/>')
    # 小屋
    for i, (x, h, w_) in enumerate(zip(xs, hs, ws)):
        hh, ww = h * s, w_ * s
        out.append(f'<rect x="{x - ww/2:.0f}" y="{yg - hh:.0f}" width="{ww:.0f}" height="{hh:.0f}" fill="{NAVY_LOW}" stroke="{CREAM}" stroke-opacity=".62" stroke-width="{2.2*s:.1f}"/>')
        out.append(f'<path d="M{x - ww/2 - 12*s:.0f} {yg - hh:.0f} L{x:.0f} {yg - hh - 40*s:.0f} L{x + ww/2 + 12*s:.0f} {yg - hh:.0f} Z" fill="{CREAM}" fill-opacity=".9"/>')
        # 窗：亮灯
        wx, wy = x - 18 * s, yg - hh + 26 * s
        out.append(f'<rect x="{wx:.0f}" y="{wy:.0f}" width="{36*s:.0f}" height="{34*s:.0f}" fill="{GOLD2}"/>')
        out.append(f'<line x1="{x:.0f}" y1="{wy:.0f}" x2="{x:.0f}" y2="{wy + 34*s:.0f}" stroke="{NAVY_TOP}" stroke-width="{2*s:.1f}"/>')
        # 门
        out.append(f'<rect x="{x - 14*s:.0f}" y="{yg - 42*s:.0f}" width="{28*s:.0f}" height="{42*s:.0f}" fill="{NAVY_TOP}"/>')
    out.append(f'<rect x="0" y="{yb:.0f}" width="{W}" height="{H*0.80 - yb:.0f}" fill="{NAVY_MID}"/>')
    # 标注：三样
    ty = yb + 70 * s
    x0, x1 = W * 0.10, W * 0.90
    for xx, anc, big, small, col in ((x0, 'start', '材料', '你带得进去的', CYAN), (W * 0.5, 'middle', '工具', '怎样问，怎样验', GOLD2), (x1, 'end', '环境', '谁来顶你', CREAM)):
        out.append(f'<text x="{xx:.0f}" y="{ty:.0f}" font-size="{36*s:.0f}" text-anchor="{anc}" font-family="Noto Serif CJK SC" font-weight="700" fill="{col}" letter-spacing="{6*s:.0f}">{big}</text>')
        out.append(f'<text x="{xx:.0f}" y="{ty + 40*s:.0f}" font-size="{20*s:.0f}" text-anchor="{anc}" font-family="Noto Sans CJK SC" fill="{DIM}" letter-spacing="{2*s:.0f}">{small}</text>')
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
<div class="no">SDE UNIVERSES<br>德麦国际专著 · 第 576 号</div>
<div class="t"><div class="pre">不疼的淘汰</div><div class="big big2">AI来了，<br>你往哪里躲？</div>
<div class="sub">为何大部分人还没有危机感</div><div class="rule"></div></div>
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
<div class="c"><div class="lab">全 书 判 词</div>
<div class="q" style="font-size:{14.2*s:.1f}pt">人靠疼知道出事，这一次的淘汰不疼。<br>手脚能躲，大脑躲不了。<br>竞争已经是复合体之间的竞争，<br>出路是搭起自己的思想发生平台。</div><div class="rule"></div>
<div class="bl"><p>培训群里，一位老师转来一条人形机器人的短视频，笑着说：同声传译也要下岗了。能这样笑，说明这场危机还没有被算到自己头上。AI 已经这样厉害，消息天天在耳边响，为什么大多数人的日子没有变？</p>
<p>本书的回答是：危机感不是胆量问题，它要有条件才会发生。事情卡住，看得见落差，账单寄到自己手上。AI 同时动了这三样：卡住被抹平，落差被“人人都在变好”遮住，账单被推迟、被转走，甚至寄不到本人手上。体感账一路变好，位差账可以同时变差。</p>
<p>全书五编二十八章：先查七个躲处，还没疼、历史总会留路、那是别的行业的事、我已经在用了、我比昨天强、我有编制学历分数、我都这么焦虑了；再讲为什么哪里都躲不了，竞争的到底是谁；最后讲要搭什么，思考的材料、思考的工具、思考的环境。书里专设一章摆出对自己最不利的证据，并写明什么事实出现就要撤回。</p>
<p>这是一部研究性专著：核心判断由王德生口述提出，正文由 AI（Claude）协作撰写并经三轮审校；书中人物是构想，平台效果未经独立检验，没有独立学术评审。</p></div>
<div class="gold">这半年，你多出了哪些别人拿不走、并被现实验过的判断？</div></div>
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 576 号 · 五编二十八章 · 约 {WAN} 万字<br>ISBN 979-8-90690-596-3 · 定价 US$25.00</div>
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
