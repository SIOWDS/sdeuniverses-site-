# -*- coding: utf-8 -*-
"""封面：两条完全重合的曲线，它们分开的那一点在纸的外面。"""
import math, os
from PIL import Image, ImageDraw, ImageFont

os.chdir('/home/claude/b90')
W, H = 1240, 1750
SPINE = 96
BG = (10, 18, 30)
GRID = (20, 34, 52)
MINT = (140, 232, 200)
CYAN = (96, 190, 220)
GOLD = (201, 162, 39)
GREY = (150, 168, 186)

SERIF = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
SANS = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
MONO = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'


def f(p, s, idx=2):
    return ImageFont.truetype(p, s, index=idx) if p.endswith('.ttc') else ImageFont.truetype(p, s)


def grad_text(base, xy, text, font, c1, c2, anchor=None):
    tmp = Image.new('L', base.size, 0)
    ImageDraw.Draw(tmp).text(xy, text, font=font, fill=255, anchor=anchor)
    bbox = tmp.getbbox()
    if not bbox:
        return
    g = Image.new('RGB', base.size, c1)
    dg = ImageDraw.Draw(g)
    x0, y0, x1, y1 = bbox
    for x in range(x0, x1 + 1):
        t = (x - x0) / max(1, x1 - x0)
        dg.line([(x, y0), (x, y1)],
                fill=tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)))
    base.paste(g, (0, 0), tmp)


def panel(w, h):
    im = Image.new('RGB', (w, h), BG)
    d = ImageDraw.Draw(im)
    for x in range(0, w, 40):
        d.line([(x, 0), (x, h)], fill=GRID)
    for y in range(0, h, 40):
        d.line([(0, y), (w, y)], fill=GRID)
    # 左上冷光晕
    glow = Image.new('RGB', (w, h), BG)
    dg = ImageDraw.Draw(glow)
    for r in range(420, 0, -14):
        a = int(16 * (1 - r / 420))
        dg.ellipse([-200 - r // 3, -240 - r // 3, -200 + r, -240 + r],
                   fill=(BG[0] + a, BG[1] + a + 3, BG[2] + a + 6))
    im = Image.blend(im, glow, 0.5)
    return im, ImageDraw.Draw(im)


# ================= 封面 =================
cov, d = panel(W, H)

fT = f(SERIF, 96)
fS = f(SANS, 30)
fs = f(SANS, 23)
fm = f(MONO, 17)
fq = f(SANS, 25)

grad_text(cov, (86, 200), '谁来陪伴我？', fT, MINT, CYAN)
d = ImageDraw.Draw(cov)
d.line([(88, 330), (270, 330)], fill=GOLD, width=3)
d.text((88, 362), 'AI 时代的婚姻困境', font=fS, fill=GREY)
d.text((88, 410), 'WHO WILL KEEP ME COMPANY', font=fm, fill=(70, 92, 112))

# ---- 图形：两条完全重合的曲线 ----
gx0, gy0, gx1, gy1 = 88, 560, W - 78, 1180
d.rectangle([gx0, gy0, gx1, gy1], outline=(28, 46, 66))
for i in range(1, 6):
    y = gy0 + (gy1 - gy0) * i / 6
    d.line([(gx0, y), (gx1, y)], fill=(20, 34, 50))


def curve(t):
    """0..1 -> 归一化高度，缓慢上升并轻微起伏"""
    return 0.72 - 0.42 * t + 0.05 * math.sin(t * 9.0) + 0.03 * math.sin(t * 21.0)


pts = []
N = 900
for i in range(N + 1):
    t = i / N
    x = gx0 + (gx1 - gx0) * t
    y = gy0 + (gy1 - gy0) * curve(t)
    pts.append((x, y))

# 两条线：完全重合（画两遍，微错位 1px 以示其为两条）
d.line(pts, fill=CYAN, width=5, joint='curve')
d.line([(x, y - 1.5) for x, y in pts], fill=MINT, width=2, joint='curve')

# 右缘：分开的那一点在纸的外面
for y in range(gy0, gy1, 16):
    d.line([(gx1, y), (gx1, y + 9)], fill=GOLD, width=3)
ax = gx1 - 150
ay = pts[-1][1] - 62
d.line([(ax, ay), (gx1 - 8, ay)], fill=GOLD, width=3)
d.polygon([(gx1 - 8, ay - 10), (gx1 + 12, ay), (gx1 - 8, ay + 10)], fill=GOLD)
d.text((ax - 6, ay - 44), '分开的那一点', font=fs, fill=GOLD)

d.text((gx0 + 6, gy1 + 14), '两条线：一条有承重存量，一条为零', font=fs, fill=GREY)

# ---- 文案 ----
d.text((88, 1252), '两条线在这张图上完全重合。', font=fq, fill=(206, 222, 236))
d.text((88, 1296), '它们分开的那一点，在纸的外面。', font=fq, fill=(206, 222, 236))

d.line([(88, 1372), (W - 78, 1372)], fill=(30, 50, 70), width=2)
d.text((88, 1400), '王德生　＋　Claude　编著', font=fS, fill=(200, 216, 230))
d.text((88, 1452), '十位作者的十条创见 · 全部重写 · 十二个量 · 一个会发散的时间',
       font=fs, fill=GREY)

d.text((88, H - 150), '德麦国际出版社　Demai International Press', font=fs, fill=(96, 120, 142))
d.text((88, H - 112), '专著第 92 号', font=fs, fill=(96, 120, 142))
d.text((240, H - 108), '·   ISBN 979-8-90690-034-0', font=fm, fill=(96, 120, 142))

cov.save('cover.jpg', quality=92)

# ================= 整封 =================
FW = W * 2 + SPINE
full, fd = panel(FW, H)
back = Image.new('RGB', (W, H))
bk, bd = panel(W, H)

bd.text((92, 150), '谁来陪伴我？', font=f(SERIF, 52), fill=(206, 222, 236))
bd.line([(92, 236), (250, 236)], fill=GOLD, width=3)
bd.text((92, 266), 'AI 时代的婚姻困境', font=fs, fill=GREY)

body = [
    ('有人陪你。', 30, MINT),
    ('困境不是没人陪你，是陪你的那个不会走。', 25, (206, 222, 236)),
    ('', 12, GREY),
    ('本书论证：一段关系里那样使它扛得住事的东西，', 21, GREY),
    ('需要一份叫「可撤性」的原料——那个人本可以不来而他来了。', 21, GREY),
    ('而当代每一项让关系变好的安排，都在改善所有读数的同时', 21, GREY),
    ('消耗这一项。', 21, GREY),
    ('', 12, GREY),
    ('读数不是失灵。', 24, MINT),
    ('读数正确地测量了一个与承重严格反向的量。', 24, MINT),
    ('', 12, GREY),
    ('于是两种在承重上完全相反的关系，在一切可观测项上', 21, GREY),
    ('完全一致；而看见它所需要的时间，正随着一切都在变好', 21, GREY),
    ('而趋于无穷。', 21, GREY),
    ('', 14, GREY),
    ('十位作者的十条创见，全部重写；十二个量，一个乘积式，', 21, GREY),
    ('一个会发散的时间。本书不给行动清单——只给二十四条', 21, GREY),
    ('判错方式，以及四个只能答成一件事、不能答成一个状态', 21, GREY),
    ('的问题。', 21, GREY),
]
y = 380
for txt, sz, col in body:
    if txt:
        bd.text((92, y), txt, font=f(SANS, sz), fill=col)
    y += int(sz * 1.75)

bd.line([(92, H - 300), (W - 92, H - 300)], fill=(30, 50, 70), width=2)
bd.text((92, H - 268), '德麦国际出版社　·　专著第 92 号', font=fs, fill=(96, 120, 142))
bd.text((92, H - 228), 'ISBN 979-8-90690-034-0', font=fm, fill=(96, 120, 142))
bd.text((92, H - 192), 'US$21.50', font=fm, fill=(96, 120, 142))

# 装饰性条码（非真 EAN13）
bx, by = W - 400, H - 250
bd.rectangle([bx - 14, by - 14, bx + 306, by + 130], fill=(232, 238, 244))
import random
random.seed(92)
x = bx
while x < bx + 300:
    w_ = random.choice([2, 2, 3, 4, 6])
    if random.random() < 0.55:
        bd.rectangle([x, by, x + w_, by + 96], fill=(12, 18, 26))
    x += w_ + random.choice([2, 3])
bd.text((bx + 18, by + 100), '9 798906 900340', font=f(MONO, 20), fill=(12, 18, 26))

full.paste(bk, (0, 0))
full.paste(cov, (W + SPINE, 0))
# 书脊
sd = ImageDraw.Draw(full)
sd.rectangle([W, 0, W + SPINE, H], fill=(8, 15, 25))
sd.line([(W, 0), (W, H)], fill=(28, 46, 66))
sd.line([(W + SPINE, 0), (W + SPINE, H)], fill=(28, 46, 66))
fsp = f(SERIF, 46)
title = '谁来陪伴我？'
sy = 190
for c in title:
    bb = sd.textbbox((0, 0), c, font=fsp)
    sd.text((W + SPINE // 2 - (bb[2] - bb[0]) // 2, sy), c, font=fsp, fill=MINT)
    sy += 58
sy += 40
for c in '王德生 ＋ Claude'.replace(' ', ''):
    bb = sd.textbbox((0, 0), c, font=f(SANS, 26))
    sd.text((W + SPINE // 2 - (bb[2] - bb[0]) // 2, sy), c, font=f(SANS, 26), fill=GREY)
    sy += 34
sd.text((W + SPINE // 2 - 10, H - 220), '92', font=f(MONO, 26), fill=GOLD)

full.save('cover-full.jpg', quality=92)
print('cover ok', cov.size, full.size)
