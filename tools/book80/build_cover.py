# -*- coding: utf-8 -*-
"""《判断的危机》封面 · 简化版（现代 + 科技感，去掉条形图）"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1240, 1750
BG = (8, 12, 20)
MINT = (126, 232, 206); TEAL = (56, 176, 190)
GOLD = (214, 158, 74); DIM = (122, 140, 158); DIM2 = (76, 92, 108)
PAPER = (226, 234, 240)

SER = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
SERR = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc'
SAN = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
MONO = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
IDX = 2


def f(p, s, i=IDX): return ImageFont.truetype(p, s, index=i)
def fm(s): return ImageFont.truetype(MONO, s)


def base():
    im = Image.new('RGB', (W, H), BG)
    g = Image.new('RGB', (W, H), BG); gd = ImageDraw.Draw(g)
    gd.ellipse([-500, -700, 900, 500], fill=(14, 44, 56))
    gd.ellipse([W - 250, H - 520, W + 500, H + 240], fill=(24, 20, 14))
    return Image.blend(im, g.filter(ImageFilter.GaussianBlur(230)), 0.68)


def grad_text(im, xy, text, font, c1, c2):
    m = Image.new('L', im.size, 0)
    ImageDraw.Draw(m).text(xy, text, font=font, fill=255)
    b = m.getbbox()
    gr = Image.new('RGB', im.size, c1); gd = ImageDraw.Draw(gr)
    for x in range(b[0], b[2] + 1):
        t = (x - b[0]) / max(1, b[2] - b[0])
        gd.line([(x, 0), (x, im.size[1])],
                fill=tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)))
    im.paste(gr, (0, 0), m)


def scanfield(im, x0, y0, width, height, n, gap_index):
    step = width / (n - 1)
    lay = Image.new('RGB', im.size, (0, 0, 0))
    mask = Image.new('L', im.size, 0)
    ld = ImageDraw.Draw(lay); md = ImageDraw.Draw(mask)
    for i in range(n):
        if i == gap_index:
            continue
        x = int(x0 + i * step)
        t = i / (n - 1)
        col = tuple(int(MINT[k] + (TEAL[k] - MINT[k]) * t) for k in range(3))
        ld.rounded_rectangle([x, y0, x + 5, y0 + height], radius=3, fill=col)
        md.rounded_rectangle([x, y0, x + 5, y0 + height], radius=3, fill=255)
    tmp = Image.new('RGB', im.size, (0, 0, 0))
    tmp.paste(lay, (0, 0), mask)
    glow = im.copy()
    glow.paste(tmp.filter(ImageFilter.GaussianBlur(22)), (0, 0),
               mask.filter(ImageFilter.GaussianBlur(26)))
    im.paste(Image.blend(im, glow, 0.85), (0, 0))
    im.paste(lay, (0, 0), mask)
    gx = int(x0 + gap_index * step) + 2
    d = ImageDraw.Draw(im)
    for yy in range(y0 - 24, y0 + height + 24, 14):
        d.line([(gx, yy), (gx, yy + 7)], fill=GOLD, width=2)
    d.line([(gx - 13, y0 - 38), (gx + 13, y0 - 38)], fill=GOLD, width=2)
    d.line([(gx - 13, y0 + height + 38), (gx + 13, y0 + height + 38)], fill=GOLD, width=2)
    return gx


def front():
    im = base(); L = 118
    grad_text(im, (L, 262), '判断的危机', f(SER, 118), MINT, TEAL)
    d = ImageDraw.Draw(im)
    d.line([(L, 428), (L + 210, 428)], fill=GOLD, width=5)
    d.text((L, 476), '它不会发出任何警报', font=f(SERR, 40), fill=PAPER)
    d.text((L, 542), 'THE CRISIS OF JUDGMENT', font=fm(21), fill=DIM2)

    gx = scanfield(im, L, 800, W - 2 * L - 6, 210, 34, 25)
    d = ImageDraw.Draw(im)
    d.text((gx - 46, 800 + 210 + 64), '未测量', font=f(SAN, 22), fill=GOLD)

    d.text((L, 1180), '所有读数都是绿的。', font=f(SERR, 30), fill=(196, 212, 224))
    d.text((L, 1236), '因为最要紧的那一项，没有装表。', font=f(SERR, 30), fill=(196, 212, 224))

    d.text((L, H - 238), '王德生　＋　Claude　著', font=f(SER, 37), fill=PAPER)
    d.text((L, H - 158), '德麦国际出版社', font=f(SAN, 25), fill=DIM)
    t = '专著第 80 号'
    d.text((W - L - d.textlength(t, font=f(SAN, 25)), H - 158), t, font=f(SAN, 25), fill=DIM)
    return im


fr = front()
fr.save('/home/claude/book80/cover.jpg', quality=95)
print('cover.jpg', fr.size)

SPINE = 96
full = Image.new('RGB', (W * 2 + SPINE, H), BG)
bk = base(); d = ImageDraw.Draw(bk); L = 118
d.text((L, 190), '母 题', font=f(SER, 32), fill=GOLD)
y = 252
for s in ['判断力无人生产、无账可记，', '只由低效活动顺带养成；', '它消失时不发生任何事件。']:
    d.text((L, y), s, font=f(SERR, 39), fill=PAPER); y += 60
d.line([(L, y + 24), (L + 210, y + 24)], fill=GOLD, width=4)
y += 82
for s in ['做出一件东西的成本降到了接近于零。',
          '而认出它算不算数的成本，一分钱没有降。',
          '',
          '本书由「学科通融」专栏十篇连续研究编成，另新写',
          '前言、导读、导论、枢纽章、合章、结语与附录。',
          '十章分别指认判定这一端上一个从未被单独生产的量：',
          '没有人打开过的那种否决、由弃物合成的标准、',
          '拦不下人却撤不掉的关口、为证明「是你做的」而',
          '追加的那一层、被整体转嫁的辨认负担、被计为损耗',
          '的首读时距、失去下界的计数单位、被当作背景的',
          '分辨力、不产出可验收之物的那段时间，以及一类',
          '没有供给方的能力。',
          '',
          '合章用五条从定义推出的关系把十项读数锁成一张',
          '可互相否证的网。其中最干净的一条说：首读时距',
          '与未阅率不是两件事，是同一个拥堵参数的两种读法。',
          '',
          '全书的兑现物是结语给出的十项体检读数——每一项',
          '都能从既有日志算出，且与该行业现行主要指标正交：',
          '主要指标全绿时，它可以很难看。']:
    d.text((L, y), s, font=f(SERR, 25), fill=(172, 190, 206)); y += 43
d.text((L, H - 238), '王德生　＋　Claude　著', font=f(SER, 31), fill=PAPER)
d.text((L, H - 172), '德麦国际出版社 · SDE UNIVERSES', font=f(SAN, 23), fill=DIM)
d.text((L, H - 118), 'THE CRISIS OF JUDGMENT', font=fm(19), fill=DIM2)

full.paste(bk, (0, 0)); full.paste(fr, (W + SPINE, 0))
sd = ImageDraw.Draw(full)
sd.rectangle([W, 0, W + SPINE, H], fill=(11, 17, 27))
sd.line([(W, 0), (W, H)], fill=(28, 42, 58), width=2)
sd.line([(W + SPINE, 0), (W + SPINE, H)], fill=(28, 42, 58), width=2)


def stack(text, y0, font, fill, gap=6):
    y = y0
    for c in text:
        w = sd.textlength(c, font=font)
        sd.text((W + (SPINE - w) / 2, y), c, font=font, fill=fill)
        y += font.size + gap
    return y


yy = stack('判断的危机', 150, f(SER, 46), MINT, 10)
yy = stack('王德生', yy + 56, f(SAN, 22), DIM, 3)
sp = Image.new('RGB', (170, 34), (11, 17, 27))
ImageDraw.Draw(sp).text((2, 2), '+ Claude', font=fm(22), fill=DIM)
full.paste(sp.rotate(-90, expand=True), (W + (SPINE - 34) // 2, int(yy) + 14))
stack('德麦国际出版社', H - 380, f(SAN, 22), DIM, 3)
full.save('/home/claude/book80/cover-full.jpg', quality=93)
print('cover-full.jpg', full.size)
