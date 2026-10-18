#!/usr/bin/env python3
"""第 356 号封面与封底：科幻 + AI 画面，少字。
主图由代码绘制：一颗由节点与连线织成的“AI 神经球”悬在透视网格地面之上，球上最亮的那一个金色节点，
就是全书说的“最先被量成数的那一角价值”；两条轨道上三颗小星（青、金、洋红）对应动能、内能、势能。
辉光用多级高斯模糊叠加，直接出位图，再由 weasyprint 叠上矢量文字。

用法：python3 cover.py --out /home/claude/b356
产物：cover-print.pdf / back-print.pdf（170×240）、cover-reader.pdf / back-reader.pdf（190×250）、
      cover.jpg / backcover.jpg（1004 宽，站上用）
"""
import argparse
import math
import random
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ISBN = '979-8-90690-517-8'
CREAM, GOLD2, DIM = '#EFE8D6', '#E3C77E', '#9FB0C8'

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




def blur(img, r):
    return img.filter(ImageFilter.GaussianBlur(r))


def arr(img):
    return np.asarray(img, dtype=np.float32) / 255.0


def make_art(W, H, kind='front', seed=356):
    rnd = random.Random(seed)
    npr = np.random.RandomState(seed)
    u = W / 2000.0
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    X, Y = xx / W, yy / H
    # ── 底：深空渐变 + 两团色雾 ──
    base = np.zeros((H, W, 3), np.float32)
    top, bot = np.array([3, 5, 15]) / 255., np.array([9, 15, 44]) / 255.
    base += top + (bot - top) * Y[..., None]
    def fog(cx, cy, rx, ry, col, k):
        d = ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2
        return np.exp(-d)[..., None] * (np.array(col) / 255.) * k
    cy_s = 0.40 if kind == 'front' else 0.22
    base += fog(.5, cy_s, .55, .30, (30, 70, 190), .55)
    base += fog(.5, .72, .8, .10, (150, 40, 190), .45)
    base += fog(.12, .15, .35, .25, (70, 30, 150), .25)
    base += fog(.92, .55, .30, .30, (20, 110, 150), .22)

    sharp = Image.new('RGB', (W, H), (0, 0, 0))
    d = ImageDraw.Draw(sharp)
    gold = Image.new('RGB', (W, H), (0, 0, 0))
    g = ImageDraw.Draw(gold)

    # ── 星点 ──
    for _ in range(900):
        x, y = rnd.random() * W, rnd.random() * H * 0.78
        b = rnd.random() ** 3
        r = (0.6 + 2.2 * b) * u
        c = int(70 + 185 * b)
        tint = rnd.choice([(c, c, c), (int(c * .7), int(c * .9), c), (c, int(c * .8), int(c * .95))])
        d.ellipse([x - r, y - r, x + r, y + r], fill=tint)

    # ── 数据流：两侧竖向虚线列 ──
    yh = H * 0.72
    for side in (0, 1):
        for k in range(15):
            x = (0.035 + k * 0.021) * W if side == 0 else W - (0.035 + k * 0.021) * W
            if kind == 'front' and 0.30 * W < x < 0.70 * W:
                continue
            y = rnd.random() * H * 0.2
            while y < yh - 20 * u:
                ln = (6 + rnd.random() * 40) * u
                fade = 1 - (y / yh) ** 1.5 * 0.8
                a = (0.10 + 0.55 * rnd.random()) * fade * (1 - k / 22.)
                d.line([x, y, x, y + ln], fill=(int(60 * a * 2.4), int(200 * a * 1.6), int(255 * a * 1.6)), width=max(1, int(2 * u)))
                y += ln + (10 + rnd.random() * 70) * u

    # ── 透视网格地面 ──
    vx = W * 0.5
    for i in range(-26, 27):
        xb = vx + i * 0.19 * W
        a = max(0.0, 1 - abs(i) / 26.) ** 0.7
        col = (int(150 * a), int(70 * a), int(255 * a))
        d.line([vx + i * 0.004 * W, yh, xb, H], fill=col, width=max(1, int(2.2 * u)))
    for t in np.linspace(0.0, 1, 18)[1:]:
        y = yh + (H - yh) * (t ** 2.4)
        a = 0.25 + 0.75 * (1 - t)
        d.line([0, y, W, y], fill=(int(120 * a), int(90 * a), int(255 * a)), width=max(1, int((1.4 + 2.2 * t) * u)))
    # 地平线亮带
    d.line([0, yh, W, yh], fill=(120, 210, 255), width=max(2, int(3 * u)))

    if kind == 'front':
        cx, cy, R = W * 0.5, H * 0.405, W * 0.285
        # 光柱：球底到地面
        beam = np.zeros((H, W), np.float32)
        ys = np.arange(int(cy + R * 0.8), int(yh + (H - yh) * 0.18))
        for y in ys:
            t = max(0.0, (y - (cy + R * 0.8)) / max(1, (yh + (H - yh) * 0.18) - (cy + R * 0.8)))
            half = (0.035 + 0.55 * t ** 1.4) * R
            x0, x1 = int(cx - half), int(cx + half)
            beam[y, max(0, x0):min(W, x1)] = (0.55 * (1 - t) ** 0.8 + 0.05)
        beam_img = Image.fromarray((np.clip(beam, 0, 1) * 255).astype(np.uint8))
        beam_rgb = np.stack([beam * 0.20, beam * 0.62, beam * 1.0], -1)
        # 地面涟漪
        for k, rr in enumerate([0.22, 0.42, 0.68, 0.98]):
            ry = rr * R * 0.16
            a = 0.9 - k * 0.2
            d.ellipse([cx - rr * R * 1.05, yh + (H - yh) * 0.12 - ry, cx + rr * R * 1.05, yh + (H - yh) * 0.12 + ry],
                      outline=(int(90 * a), int(220 * a), int(255 * a)), width=max(1, int(3 * u)))
        # ── 神经球 ──
        N = 230
        i = np.arange(N)
        yv = 1 - 2 * (i + .5) / N
        rv = np.sqrt(1 - yv ** 2)
        th = i * math.pi * (3 - math.sqrt(5))
        P = np.stack([rv * np.cos(th), yv, rv * np.sin(th)], 1)
        ax, ay = math.radians(-18), math.radians(32)
        Rx = np.array([[1, 0, 0], [0, math.cos(ax), -math.sin(ax)], [0, math.sin(ax), math.cos(ax)]])
        Ry = np.array([[math.cos(ay), 0, math.sin(ay)], [0, 1, 0], [-math.sin(ay), 0, math.cos(ay)]])
        P = P @ Rx.T @ Ry.T
        px, py, pz = cx + P[:, 0] * R, cy + P[:, 1] * R, P[:, 2]
        D = np.linalg.norm(P[:, None, :] - P[None, :, :], axis=2)
        edges = set()
        for a_ in range(N):
            for b_ in np.argsort(D[a_])[1:4]:
                edges.add((min(a_, int(b_)), max(a_, int(b_))))
        for a_, b_ in edges:
            z = (pz[a_] + pz[b_]) / 2
            al = 0.12 + 0.88 * (z + 1) / 2
            d.line([px[a_], py[a_], px[b_], py[b_]], fill=(int(70 * al), int(215 * al), int(255 * al)), width=max(1, int((1.2 + 1.6 * al) * u)))
        order = np.argsort(pz)
        for a_ in order:
            al = 0.18 + 0.82 * (pz[a_] + 1) / 2
            r = (2.2 + 4.4 * al) * u
            d.ellipse([px[a_] - r, py[a_] - r, px[a_] + r, py[a_] + r], fill=(int(190 * al + 40), int(240 * al + 15), 255))
        # 最亮的金节点：右上前方
        score = P[:, 0] * 0.7 - P[:, 1] * 0.6 + P[:, 2] * 1.1
        gi = int(np.argmax(score))
        gx, gy = px[gi], py[gi]
        for rr, al in [(70, .20), (44, .35), (26, .6), (13, 1.0)]:
            r = rr * u
            g.ellipse([gx - r, gy - r, gx + r, gy + r], fill=(int(255 * al), int(205 * al), int(110 * al)))
        for L_, w_ in [(300, 3), (190, 2)]:
            g.line([gx - L_ * u, gy, gx + L_ * u, gy], fill=(255, 215, 130), width=max(1, int(w_ * u)))
            g.line([gx, gy - L_ * .7 * u, gx, gy + L_ * .7 * u], fill=(255, 215, 130), width=max(1, int(w_ * u)))
        # 从金节点引出一条细线到画面右上（像被“点名”）
        g.line([gx, gy, gx + 0.20 * W, gy - 0.085 * H], fill=(230, 190, 110), width=max(1, int(2 * u)))
        g.ellipse([gx + 0.20 * W - 6 * u, gy - 0.085 * H - 6 * u, gx + 0.20 * W + 6 * u, gy - 0.085 * H + 6 * u], outline=(255, 215, 130), width=max(1, int(2 * u)))
        # 轨道 + 三颗星
        def orbit(rx, ry, rot, col, sat_col, ang, ticks=True):
            pts = []
            for k in range(361):
                t = math.radians(k)
                x, y = rx * math.cos(t), ry * math.sin(t)
                pts.append((cx + x * math.cos(rot) - y * math.sin(rot), cy + x * math.sin(rot) + y * math.cos(rot)))
            d.line(pts, fill=col, width=max(1, int(2.2 * u)))
            if ticks:
                for k in range(0, 360, 6):
                    t = math.radians(k); x, y = rx * math.cos(t), ry * math.sin(t)
                    x2, y2 = (rx * 1.02) * math.cos(t), (ry * 1.02 * 1.0) * math.sin(t)
                    def rt(a, b): return (cx + a * math.cos(rot) - b * math.sin(rot), cy + a * math.sin(rot) + b * math.cos(rot))
                    d.line([rt(x, y), rt(x2 * 1.01, y2 * 1.01)], fill=col, width=max(1, int(1.6 * u)))
            t = math.radians(ang); x, y = rx * math.cos(t), ry * math.sin(t)
            sx_, sy_ = cx + x * math.cos(rot) - y * math.sin(rot), cy + x * math.sin(rot) + y * math.cos(rot)
            return sx_, sy_
        s1 = orbit(R * 1.52, R * 0.42, math.radians(-16), (40, 120, 170), (80, 230, 255), 212)
        s2 = orbit(R * 1.32, R * 0.30, math.radians(22), (110, 60, 160), (255, 90, 200), 38)
        s3 = orbit(R * 1.78, R * 0.55, math.radians(-8), (90, 80, 60), (255, 200, 90), 322, ticks=False)
        sats = [(s1, (90, 235, 255), 20), (s2, (255, 100, 210), 17), (s3, (255, 210, 110), 15)]
        for (sx_, sy_), col, rr in sats:
            for k, al in [(3.4, .12), (2.2, .3), (1.3, .7), (.7, 1.0)]:
                r = rr * k * u * .6
                g.ellipse([sx_ - r, sy_ - r, sx_ + r, sy_ + r], fill=tuple(int(c * al) for c in col))
        # 球心光
        core = np.exp(-(((X * W - cx) ** 2 + (Y * H - cy) ** 2) / (R * 0.95) ** 2))
        base += core[..., None] * np.array([40, 120, 255]) / 255. * 0.55
        base += (beam_rgb * 0.8)
    else:
        # 封底：只留一个被截断的大球体轮廓与光雾，保持同一世界观但不抢字
        cx, cy, R = W * 0.88, H * 0.20, W * 0.34
        N = 150
        i = np.arange(N); yv = 1 - 2 * (i + .5) / N; rv = np.sqrt(1 - yv ** 2); th = i * math.pi * (3 - math.sqrt(5))
        P = np.stack([rv * np.cos(th), yv, rv * np.sin(th)], 1)
        px, py, pz = cx + P[:, 0] * R, cy + P[:, 1] * R, P[:, 2]
        Dm = np.linalg.norm(P[:, None, :] - P[None, :, :], axis=2)
        for a_ in range(N):
            for b_ in np.argsort(Dm[a_])[1:4]:
                z = (pz[a_] + pz[b_]) / 2; al = (0.10 + 0.5 * (z + 1) / 2)
                d.line([px[a_], py[a_], px[b_], py[b_]], fill=(int(70 * al), int(215 * al), int(255 * al)), width=max(1, int(1.6 * u)))
        for a_ in range(N):
            al = 0.15 + 0.5 * (pz[a_] + 1) / 2; r = (2 + 3 * al) * u
            d.ellipse([px[a_] - r, py[a_] - r, px[a_] + r, py[a_] + r], fill=(int(160 * al + 30), int(230 * al + 20), 255))
        core = np.exp(-(((X * W - cx) ** 2 + (Y * H - cy) ** 2) / (R * 1.1) ** 2))
        base += core[..., None] * np.array([40, 110, 240]) / 255. * 0.4

    # ── 合成：锐层 + 多级辉光 ──
    S = arr(sharp); Gd = arr(gold)
    glow = arr(blur(sharp, 4 * u)) * 0.9 + arr(blur(sharp, 14 * u)) * 1.1 + arr(blur(sharp, 42 * u)) * 1.4
    gglow = arr(blur(gold, 6 * u)) * 1.2 + arr(blur(gold, 24 * u)) * 1.6 + arr(blur(gold, 70 * u)) * 1.8
    add = S * 1.0 + glow + Gd + gglow
    out = 1 - (1 - np.clip(base, 0, 1)) * (1 - np.clip(add, 0, 1))
    # 暗角 + 底部压暗（给作者行留底）
    dd = ((X - .5) / .75) ** 2 + ((Y - .5) / .8) ** 2
    out *= (1 - 0.55 * np.clip(dd, 0, 1.2) ** 1.3)[..., None]
    out *= (1 - 0.65 * np.clip((Y - .86) / .14, 0, 1) ** 1.2)[..., None]
    if kind == 'back':
        out *= 0.72
    out += npr.normal(0, 0.006, out.shape).astype(np.float32)  # 抗色带
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))


def front_html(Wmm, Hmm, img):
    s = Wmm / 170
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page{{size:{Wmm}mm {Hmm}mm;margin:0}} body{{margin:0}}
.pg{{position:relative;width:{Wmm}mm;height:{Hmm}mm;overflow:hidden;background:#05070f}}
.pg img{{position:absolute;left:0;top:0;width:{Wmm}mm;height:{Hmm}mm}}
.t{{position:absolute;left:{17*s:.1f}mm;right:{17*s:.1f}mm;top:{19*s:.1f}mm;text-align:center}}
.big{{font:700 {33*s:.1f}pt/1.25 'Noto Serif CJK SC';letter-spacing:.12em;color:#F4F7FF;white-space:nowrap}}
.line{{width:{26*s:.1f}mm;border-top:1.1pt solid #E3C77E;margin:{5*s:.1f}mm auto 0}}
.no{{position:absolute;right:{15*s:.1f}mm;top:{9*s:.1f}mm;font:400 {6.4*s:.1f}pt 'Noto Sans CJK SC';color:#8FB4D8;letter-spacing:.3em}}
.b{{position:absolute;left:0;right:0;bottom:{14*s:.1f}mm;text-align:center}}
.au{{font:400 {12*s:.1f}pt 'Noto Serif CJK SC';color:#EFE8D6;letter-spacing:.5em;margin-right:-.5em}}
.ph{{font:700 {7.6*s:.1f}pt 'Noto Sans CJK SC';color:#E3C77E;letter-spacing:.4em;margin-top:{4*s:.1f}mm;margin-right:-.4em}}
</style></head><body><div class="pg"><img src="{img}">
<div class="no">SDE UNIVERSES · NO.356</div>
<div class="t"><div class="big">管理学学派解构入门</div><div class="line"></div></div>
<div class="b"><div class="au">胡敏　著</div><div class="ph">德麦国际出版社</div></div>
</div></body></html>"""


def back_html(Wmm, Hmm, img):
    s = Wmm / 170
    W, H = Wmm * 10, Hmm * 10
    bc, bw = barcode(W - 170 * s - 380 * s, H - 150 * s - 300 * s, s)
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{Wmm}mm" height="{Hmm}mm" style="position:absolute;left:0;top:0">{bc}</svg>'
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page{{size:{Wmm}mm {Hmm}mm;margin:0}} body{{margin:0}}
.pg{{position:relative;width:{Wmm}mm;height:{Hmm}mm;overflow:hidden;background:#05070f}}
.pg img{{position:absolute;left:0;top:0;width:{Wmm}mm;height:{Hmm}mm}}
.c{{position:absolute;left:{17*s:.1f}mm;top:{56*s:.1f}mm;width:{118*s:.1f}mm}}
.q{{font:700 {17*s:.1f}pt/1.85 'Noto Serif CJK SC';color:#F4F7FF;letter-spacing:.05em}}
.rule{{width:{16*s:.1f}mm;border-top:1.1pt solid #E3C77E;margin:{9*s:.1f}mm 0 {8*s:.1f}mm}}
.gold{{font:700 {10.4*s:.1f}pt/1.95 'Noto Serif CJK SC';color:#E3C77E;letter-spacing:.06em}}
.f{{position:absolute;left:{17*s:.1f}mm;bottom:{17*s:.1f}mm;font:400 {7.2*s:.1f}pt/1.9 'Noto Sans CJK SC';color:{DIM}}}
.f b{{color:{CREAM};font-weight:700;letter-spacing:.12em}}
</style></head><body><div class="pg"><img src="{img}">
<div class="c"><div class="q">每个管理学派，<br>都是“预设的人”<br>乘“预设的事”；<br>抓手一旦当家，<br>就把自己锁成了起点。</div><div class="rule"></div>
<div class="gold">动能被数会变形，<br>内能被盘会仪式化，<br>势能被兑会塌缩。</div></div>
{svg}
<div class="f"><b>德麦国际出版社</b> · Demai International Press<br>德麦国际专著第 356 号 · US$20.00</div>
</div></body></html>"""


def main():
    import weasyprint
    import pymupdf
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    for tag, (w, h) in {'print': (170, 240), 'reader': (190, 250)}.items():
        W = 2000; H = round(W * h / w)
        for kind in ('front', 'back'):
            im = make_art(W, H, kind)
            p = a.out / f'art-{kind}-{tag}.jpg'
            im.save(p, quality=90, subsampling=0)
            html = front_html(w, h, p.as_uri()) if kind == 'front' else back_html(w, h, p.as_uri())
            name = 'cover' if kind == 'front' else 'back'
            weasyprint.HTML(string=html, base_url=str(a.out)).write_pdf(str(a.out / f'{name}-{tag}.pdf'))
    for src, dst in [('cover-print.pdf', 'cover.jpg'), ('back-print.pdf', 'backcover.jpg')]:
        pg = pymupdf.open(str(a.out / src))[0]
        zoom = 1004 / pg.rect.width
        pg.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom)).save(str(a.out / dst), jpg_quality=90)
    print('covers ok')


if __name__ == '__main__':
    main()
