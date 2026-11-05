#!/usr/bin/env python3
"""封面与封底，照第 220、302 号：藏青底、细点阵、金色环；主图是一摞书、一本虚线的“下一本”，
和一片格子里亮起的一格，人从书旁沿金点走向那一格。书号、ISBN 未配，封底不放条码。"""
import sys
from pathlib import Path
import weasyprint, pymupdf

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else '/home/claude/sde_ai_millennium/layout/out')
OUT.mkdir(parents=True, exist_ok=True)
GOLD, GOLD2, CYAN, CREAM, DIM = '#C9A857', '#E3C77E', '#3FB6C4', '#EFE8D6', '#9FB0C8'
SERIF, SANS = "'Noto Serif CJK SC'", "'Noto Sans CJK SC'"


ISBN = '979-8-90690-616-8'
L = ['0001101', '0011001', '0010011', '0111101', '0100011', '0110001', '0101111', '0111011', '0110111', '0001011']
G = ['0100111', '0110011', '0011011', '0100001', '0011101', '0111001', '0000101', '0010001', '0001001', '0010111']
R_ = ['1110010', '1100110', '1101100', '1000010', '1011100', '1001110', '1010000', '1000100', '1001000', '1110100']
PAR = ['LLLLLL', 'LLGLGG', 'LLGGLG', 'LLGGGL', 'LGLLGG', 'LGGLLG', 'LGGGLL', 'LGLGLG', 'LGLGGL', 'LGGLGL']


def barcode(x, y, s):
    d = ISBN.replace('-', '')
    assert int(d[12]) == (10 - sum(int(c) * (3 if i % 2 else 1) for i, c in enumerate(d[:12])) % 10) % 10
    bits = '101' + ''.join((L if PAR[int(d[0])][i] == 'L' else G)[int(c)] for i, c in enumerate(d[1:7])) + '01010' + ''.join(R_[int(c)] for c in d[7:]) + '101'
    mw, h = 3.3 * s, 190 * s
    rects = ''
    for i, b in enumerate(bits):
        if b == '1':
            guard = i < 3 or 45 <= i < 50 or i >= 92
            rects += '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#111"/>' % (x + 22 * s + i * mw, y + 40 * s, mw + .2, h + (18 * s if guard else 0))
    bw = 95 * mw + 44 * s
    txt = (f'<text x="{x + bw/2:.0f}" y="{y + 30*s:.0f}" font-size="{19*s:.0f}" text-anchor="middle" font-family="Noto Sans CJK SC" fill="#111">ISBN {ISBN}</text>'
           f'<text x="{x + 8*s:.0f}" y="{y + 40*s + h + 36*s:.0f}" font-size="{26*s:.0f}" font-family="Noto Sans CJK SC" fill="#111">{d[0]}</text>'
           f'<text x="{x + 22*s + 3*mw + 21*mw:.0f}" y="{y + 40*s + h + 36*s:.0f}" font-size="{26*s:.0f}" text-anchor="middle" letter-spacing="{9*s:.0f}" font-family="Noto Sans CJK SC" fill="#111">{d[1:7]}</text>'
           f'<text x="{x + 22*s + 50*mw + 21*mw:.0f}" y="{y + 40*s + h + 36*s:.0f}" font-size="{26*s:.0f}" text-anchor="middle" letter-spacing="{9*s:.0f}" font-family="Noto Sans CJK SC" fill="#111">{d[7:]}</text>')
    return f'<rect x="{x:.0f}" y="{y:.0f}" width="{bw:.0f}" height="{h + 110*s:.0f}" fill="#fff"/>' + rects + txt


def background(W, H, uid):
    dots = ''.join('<circle cx="%d" cy="%d" r="1.5"/>' % (x, y)
                   for y in range(22, H, 44) for x in range(22 + (y // 44 % 2) * 22, W, 44))
    return f"""<defs><linearGradient id="bg{uid}" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="#0D1A33"/><stop offset=".55" stop-color="#172A4E"/><stop offset="1" stop-color="#1C2C52"/></linearGradient>
<radialGradient id="halo{uid}" cx=".5" cy=".5" r=".5"><stop offset=".78" stop-color="{GOLD}" stop-opacity="0"/>
<stop offset=".93" stop-color="{GOLD}" stop-opacity=".13"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></radialGradient></defs>
<rect width="{W}" height="{H}" fill="url(#bg{uid})"/><g fill="{DIM}" fill-opacity=".08">{dots}</g>"""


def ring(cx, cy, r, uid):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r*1.12:.0f}" fill="url(#halo{uid})"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{GOLD}" stroke-opacity=".62" stroke-width="4"/>')


def mark(kind, x, y, c):
    """每一格里一个不同的小记号：格格不同。"""
    col = CREAM; op = .34
    if kind == 0:
        return f'<circle cx="{x}" cy="{y}" r="{c*.13:.0f}" fill="{col}" fill-opacity="{op}"/>'
    if kind == 1:
        return f'<rect x="{x-c*.22:.0f}" y="{y-c*.05:.0f}" width="{c*.44:.0f}" height="{c*.1:.0f}" fill="{col}" fill-opacity="{op}"/>'
    if kind == 2:
        return f'<path d="M{x} {y-c*.17:.0f} L{x+c*.17:.0f} {y+c*.13:.0f} L{x-c*.17:.0f} {y+c*.13:.0f} Z" fill="{col}" fill-opacity="{op}"/>'
    if kind == 3:
        return f'<circle cx="{x}" cy="{y}" r="{c*.15:.0f}" fill="none" stroke="{col}" stroke-opacity="{op+.06}" stroke-width="5"/>'
    if kind == 4:
        return (f'<rect x="{x-c*.17:.0f}" y="{y-c*.14:.0f}" width="{c*.34:.0f}" height="{c*.07:.0f}" fill="{col}" fill-opacity="{op}"/>'
                f'<rect x="{x-c*.17:.0f}" y="{y+c*.05:.0f}" width="{c*.22:.0f}" height="{c*.07:.0f}" fill="{col}" fill-opacity="{op}"/>')
    return f'<path d="M{x-c*.17:.0f} {y} Q{x} {y-c*.26:.0f} {x+c*.17:.0f} {y}" fill="none" stroke="{col}" stroke-opacity="{op+.06}" stroke-width="5"/>'


def art(W, H):
    s = W / 1700
    cx, cy, r = W * .615, H * .595, 560 * s
    o = [ring(round(cx), round(cy), round(r), 'f')]
    # 格子阵
    c, g = 112 * s, 22 * s
    n = 5
    x0 = cx - 120 * s
    y0 = cy - 380 * s
    seq = [0, 3, 1, 5, 2, 4, 1, 0, 2, 3, 5, 1, 4, 0, 3, 2, 5, 4, 1, 0, 3, 2, 0, 5, 1]
    cols, rows = 4, 4
    lit = (2, 3)
    for ri in range(rows):
        for ci in range(cols):
            x = x0 + ci * (c + g); y = y0 + ri * (c + g)
            if (ci, ri) == lit:
                o.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{c:.0f}" height="{c:.0f}" rx="{12*s:.0f}" fill="{CREAM}"/>')
                mx, my = x + c / 2, y + c / 2
                o.append(f'<path d="M{mx:.0f} {y+c*.82:.0f} L{mx:.0f} {y+c*.42:.0f}" stroke="{CYAN}" stroke-width="{8*s:.0f}" stroke-linecap="round"/>')
                o.append(f'<ellipse cx="{mx+c*.15:.0f}" cy="{y+c*.42:.0f}" rx="{c*.17:.0f}" ry="{c*.07:.0f}" fill="{CYAN}" transform="rotate(-30 {mx+c*.15:.0f} {y+c*.42:.0f})"/>')
                o.append(f'<ellipse cx="{mx-c*.15:.0f}" cy="{y+c*.55:.0f}" rx="{c*.17:.0f}" ry="{c*.07:.0f}" fill="{CYAN}" transform="rotate(30 {mx-c*.15:.0f} {y+c*.55:.0f})"/>')
                o.append(f'<circle cx="{mx:.0f}" cy="{y+c*.27:.0f}" r="{c*.1:.0f}" fill="{GOLD}"/>')
            else:
                o.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{c:.0f}" height="{c:.0f}" rx="{12*s:.0f}" fill="#0F1E3C" fill-opacity=".55" stroke="{CREAM}" stroke-opacity=".28" stroke-width="{3*s:.1f}"/>')
                o.append(mark(seq[(ri * cols + ci) % len(seq)], round(x + c / 2), round(y + c / 2), c))
    base = cy + 470 * s
    # 一摞书
    bx = cx - 600 * s
    books = [(480, 62, '#A98C4F'), (436, 56, '#C7B488'), (462, 60, '#8B7345'), (400, 54, '#E8DFC8')]
    y = base
    for w, h, col in books:
        y -= h * s
        off = (480 - w) / 2 * s
        o.append(f'<rect x="{bx+off:.0f}" y="{y:.0f}" width="{w*s:.0f}" height="{(h-6)*s:.0f}" rx="{8*s:.0f}" fill="{col}"/>')
        o.append(f'<rect x="{bx+off+36*s:.0f}" y="{y:.0f}" width="{10*s:.0f}" height="{(h-6)*s:.0f}" fill="#0F1E3C" fill-opacity=".3"/>')
    # 虚线的“下一本”
    y -= 62 * s
    o.append(f'<rect x="{bx+50*s:.0f}" y="{y:.0f}" width="{380*s:.0f}" height="{52*s:.0f}" rx="{8*s:.0f}" fill="none" stroke="{GOLD2}" stroke-opacity=".85" stroke-width="{3.4*s:.1f}" stroke-dasharray="{14*s:.0f} {11*s:.0f}"/>')
    # 人
    px, py = cx - 30 * s, base
    o.append(f'<circle cx="{px:.0f}" cy="{py-250*s:.0f}" r="{36*s:.0f}" fill="{CREAM}"/>')
    o.append(f'<path d="M{px-44*s:.0f} {py} L{px-44*s:.0f} {py-150*s:.0f} Q{px-44*s:.0f} {py-204*s:.0f} {px:.0f} {py-204*s:.0f} Q{px+44*s:.0f} {py-204*s:.0f} {px+44*s:.0f} {py-150*s:.0f} L{px+44*s:.0f} {py} Z" fill="{CREAM}"/>')
    # 金点：从人走向亮起的一格
    lx = x0 + lit[0] * (c + g) + c / 2; ly = y0 + lit[1] * (c + g) + c
    pts = []
    N = 4
    sx, sy = px + 58 * s, py - 262 * s
    ex, ey = lx, ly + 26 * s
    for i in range(N):
        tt = i / (N - 1)
        qx = (1 - tt) ** 2 * sx + 2 * (1 - tt) * tt * (sx + 110 * s) + tt * tt * ex
        qy = (1 - tt) ** 2 * sy + 2 * (1 - tt) * tt * (sy + 6 * s) + tt * tt * ey
        pts.append((qx, qy, (15 - tt * 8) * s))
    for qx, qy, rr in pts:
        o.append(f'<circle cx="{qx:.0f}" cy="{qy:.0f}" r="{rr:.0f}" fill="{GOLD}" fill-opacity=".95"/>')
    o.append(f'<line x1="{bx-40*s:.0f}" y1="{base+6*s:.0f}" x2="{W-34*s:.0f}" y2="{base+6*s:.0f}" stroke="{CREAM}" stroke-opacity=".45" stroke-width="{2.4*s:.1f}"/>')
    return ''.join(o)


def front(Wmm, Hmm):
    W, H = Wmm * 10, Hmm * 10
    s = Wmm / 170
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{Wmm}mm" height="{Hmm}mm">{background(W, H, "f")}{art(W, H)}</svg>'
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page{{size:{Wmm}mm {Hmm}mm;margin:0}} body{{margin:0}}
.pg{{position:relative;width:{Wmm}mm;height:{Hmm}mm;overflow:hidden}} .pg svg{{position:absolute;left:0;top:0}}
.t{{position:absolute;left:{11.5*s:.1f}mm;top:{24*s:.1f}mm;color:{CREAM}}}
.a{{font:700 {27*s:.1f}pt/1.2 {SERIF};color:#F4EEDF;letter-spacing:.03em}}
.b{{font:700 {31.5*s:.1f}pt/1.3 {SERIF};color:#F4EEDF;letter-spacing:.01em;margin-top:{2.5*s:.1f}mm;white-space:nowrap}}
.sub{{font:400 {10.8*s:.1f}pt/1.6 {SANS};color:{GOLD2};margin-top:{6.5*s:.1f}mm;letter-spacing:.01em;white-space:nowrap}}
.au{{position:absolute;left:{11.5*s:.1f}mm;bottom:{31*s:.1f}mm;font:400 {13.5*s:.1f}pt {SANS};color:{CREAM};letter-spacing:.14em}}
.rl{{position:absolute;left:{11.5*s:.1f}mm;bottom:{43*s:.1f}mm;width:{48*s:.1f}mm;border-top:.7pt solid {DIM};opacity:.7}}
.ph{{position:absolute;left:{11.5*s:.1f}mm;bottom:{17.5*s:.1f}mm;font:400 {10.2*s:.1f}pt {SANS};color:{CREAM};letter-spacing:.08em}}
.pe{{position:absolute;left:{11.5*s:.1f}mm;bottom:{11.5*s:.1f}mm;font:400 {6.6*s:.1f}pt {SANS};color:{DIM};letter-spacing:.14em}}
</style></head><body><div class="pg">{svg}
<div class="t"><div class="a">千年难题，</div><div class="b">还要等下一个理论吗？</div>
<div class="sub">以 SDE 为核心的人-AI 复合智能体怎样随时生成答案</div></div>
<div class="rl"></div><div class="au">王德生　著</div>
<div class="ph">德麦国际出版社</div><div class="pe">Demai International Press</div>
</div></body></html>"""


def back(Wmm, Hmm):
    W, H = Wmm * 10, Hmm * 10
    s = Wmm / 170
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{Wmm}mm" height="{Hmm}mm">'
           f'{background(W, H, "b")}{ring(round(W*.80), round(H*.10), round(370*s), "b")}{barcode(W - 90*s - 380*s, H - 120*s - 300*s, s)}</svg>')
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page{{size:{Wmm}mm {Hmm}mm;margin:0}} body{{margin:0}}
.pg{{position:relative;width:{Wmm}mm;height:{Hmm}mm;overflow:hidden}} .pg svg{{position:absolute;left:0;top:0}}
.c{{position:absolute;left:{13*s:.1f}mm;top:{21*s:.1f}mm;width:{138*s:.1f}mm;color:{CREAM}}}
.q{{font:700 {15.5*s:.1f}pt/1.72 {SANS};color:#F7F1E3;letter-spacing:.02em}}
.bl{{margin-top:{9*s:.1f}mm}} .bl p{{font:400 {9.6*s:.1f}pt/1.95 {SANS};color:{CREAM};opacity:.93;margin:0 0 {3*s:.1f}mm}}
.gold{{font:700 {10.6*s:.1f}pt {SANS};color:{GOLD2};margin-top:{9*s:.1f}mm}}
.f{{position:absolute;left:{13*s:.1f}mm;bottom:{14*s:.1f}mm;font:400 {8*s:.1f}pt/2 {SANS};color:{CREAM};opacity:.9}}
.rl{{position:absolute;left:{13*s:.1f}mm;bottom:{42*s:.1f}mm;width:{68*s:.1f}mm;border-top:.7pt solid {DIM};opacity:.7}}
</style></head><body><div class="pg">{svg}
<div class="c"><div class="q">千年难题，是理论<br>把活的压成定的。<br>解不在下一个理论里，<br>在以 SDE 为核心的<br>人-AI 复合智能体<br>逐格、此刻生成的答案里。</div>
<div class="bl"><p>严管还是放手，性善还是性恶，该不该说真话。<br>两边的证据都对，吵了两千多年。</p>
<p>本书列出十道千年难题，每题写两格设想中的现场：<br>人带来这一格，AI 跑路，SDE 定路判路，<br>生成一个走错了还能撤回的答案。</p>
<p>它不立新理论，也写明自己怎样会输：<br>四条总死法，十题的判负条件，全部未检验。</p></div>
<div class="gold">这些人是造出来的，你不是。　　——本书</div></div>
<div class="rl"></div>
<div class="f">德麦国际出版社 · Demai International Press<br>德麦国际专著第 589 号<br>定价：US$20.00</div>
</div></body></html>"""


for tag, (w, h) in {'print': (170, 240), 'reader': (190, 250)}.items():
    weasyprint.HTML(string=front(w, h)).write_pdf(str(OUT / f'cover-{tag}.pdf'))
    weasyprint.HTML(string=back(w, h)).write_pdf(str(OUT / f'back-{tag}.pdf'))
for src, dst in [('cover-print.pdf', 'cover.jpg'), ('back-print.pdf', 'backcover.jpg')]:
    pg = pymupdf.open(str(OUT / src))[0]
    z = 1004 / pg.rect.width
    pg.get_pixmap(matrix=pymupdf.Matrix(z, z)).save(str(OUT / dst), jpg_quality=90)
print('covers ok')
