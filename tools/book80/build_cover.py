# -*- coding: utf-8 -*-
"""《判断的危机》封面 · 第二版"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1240, 1750
BG = (10, 16, 26); GRID = (18, 30, 44)
MINT = (126, 232, 206); TEAL = (58, 178, 186)
GREEN = (74, 200, 140); GREEN2 = (46, 150, 116)
GOLD = (214, 158, 74); DIM = (128, 146, 164); DIM2 = (86, 102, 118)
PAPER = (222, 232, 238)

SER = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
SERR = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc'
SAN = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
MONO = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
IDX = 2


def f(path, size, idx=IDX): return ImageFont.truetype(path, size, index=idx)
def fm(size): return ImageFont.truetype(MONO, size)


def bg_layer():
    im = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(im)
    for x in range(0, W, 31): d.line([(x, 0), (x, H)], fill=GRID)
    for y in range(0, H, 31): d.line([(0, y), (W, y)], fill=GRID)
    glow = Image.new('RGB', (W, H), BG); gd = ImageDraw.Draw(glow)
    gd.ellipse([-460, -560, 760, 520], fill=(16, 46, 58))
    gd.ellipse([W - 340, H - 700, W + 420, H + 160], fill=(30, 22, 16))
    return Image.blend(im, glow.filter(ImageFilter.GaussianBlur(190)), 0.62)


def grad_text(im, xy, text, font, c1, c2):
    mask = Image.new('L', im.size, 0)
    ImageDraw.Draw(mask).text(xy, text, font=font, fill=255)
    b = mask.getbbox()
    grad = Image.new('RGB', im.size, c1); gd = ImageDraw.Draw(grad)
    for x in range(b[0], b[2] + 1):
        t = (x - b[0]) / max(1, b[2] - b[0])
        gd.line([(x, 0), (x, im.size[1])],
                fill=tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)))
    im.paste(grad, (0, 0), mask)


def bar(im, x, y, w, h, c1, c2):
    r = h // 2
    lay = Image.new('RGB', (w, h), c1); ld = ImageDraw.Draw(lay)
    for i in range(w):
        t = i / max(1, w - 1)
        ld.line([(i, 0), (i, h)], fill=tuple(int(c1[k] + (c2[k] - c1[k]) * t) for k in range(3)))
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=255)
    g = Image.new('RGB', im.size, (0, 0, 0)); gm = Image.new('L', im.size, 0)
    gm.paste(mask, (x, y)); g.paste(lay, (x, y), mask)
    g = g.filter(ImageFilter.GaussianBlur(11))
    base = im.copy(); glow = base.copy()
    glow.paste(g, (0, 0), gm.filter(ImageFilter.GaussianBlur(13)))
    im.paste(Image.blend(base, glow, 0.55), (0, 0))
    im.paste(lay, (x, y), mask)


ROWS = [('01', '未阅率', 0.93), ('02', '暗基线抬升度', 0.88), ('03', '饱和关占比', 0.96),
        ('04', '认领占比', 0.90), ('05', '辨认转嫁比', 0.85), ('06', '无量期占比', 0.94),
        ('07', '著作层并项率', 0.89), ('08', '有效种类留存率', 0.92),
        ('09', '无验收期占比', 0.87), ('10', '停 养 率', None)]


def build_front():
    im = bg_layer(); d = ImageDraw.Draw(im); L = 118
    grad_text(im, (L, 232), '判断的危机', f(SER, 112), MINT, TEAL)
    d.line([(L, 384), (L + 196, 384)], fill=GOLD, width=5)
    d.text((L, 430), '它不会发出任何警报', font=f(SERR, 41), fill=PAPER)
    d.text((L, 490), '生成成本归零之后，谁还在辨认', font=f(SERR, 41), fill=PAPER)
    d.text((L, 560), 'THE CRISIS OF JUDGMENT', font=fm(22), fill=DIM)

    top = 640
    d.text((L, top), 'READOUT', font=fm(19), fill=DIM)
    d.text((L + 600, top), 'STATUS', font=fm(19), fill=DIM)
    d.line([(L, top + 34), (W - L, top + 34)], fill=(40, 58, 76), width=2)
    y = top + 74; bx = L + 290; bw = 430
    for code, name, v in ROWS:
        d.text((L, y + 2), code, font=fm(18), fill=DIM2)
        d.text((L + 54, y - 4), name, font=f(SAN, 25), fill=(196, 212, 224) if v else DIM)
        if v is not None:
            bar(im, bx, y, int(bw * v), 22, GREEN, TEAL)
            d.text((bx + bw + 30, y), '正常', font=f(SAN, 22), fill=GREEN2)
        else:
            for xx in range(bx, bx + bw, 13):
                d.line([(xx, y + 11), (xx + 6, y + 11)], fill=(52, 66, 82), width=2)
            d.rectangle([bx, y, bx + 2, y + 21], fill=(70, 86, 102))
            d.rectangle([bx + bw - 2, y, bx + bw, y + 21], fill=(70, 86, 102))
            d.text((bx + bw + 30, y), '无人测量', font=f(SAN, 22), fill=GOLD)
        y += 52

    cy = y + 30
    d.text((L, cy), '十项读数，九项全绿。', font=f(SERR, 27), fill=(178, 196, 210))
    d.text((L, cy + 44), '第十项没有颜色——因为没有任何机构在测它。',
           font=f(SERR, 27), fill=(178, 196, 210))
    d.line([(L, cy + 100), (W - L, cy + 100)], fill=(34, 50, 66), width=1)
    d.text((L, cy + 118), 'w = u / (1 - u)', font=fm(21), fill=GOLD)
    d.text((L + 232, cy + 120), '十项读数已被五条关系式锁在一起，必须同时成立。',
           font=f(SAN, 21), fill=(132, 150, 166))

    d.text((L, H - 226), '王德生　＋　Claude　著', font=f(SER, 38), fill=PAPER)
    d.text((L, H - 150), '德麦国际出版社', font=f(SAN, 26), fill=DIM)
    t = '专著第 80 号'
    d.text((W - L - d.textlength(t, font=f(SAN, 26)), H - 150), t, font=f(SAN, 26), fill=DIM)
    return im


front = build_front()
front.save('/home/claude/book80/cover.jpg', quality=94)
print('cover.jpg', front.size)

SPINE = 96
FULL_W = W * 2 + SPINE
full = Image.new('RGB', (FULL_W, H), BG)
back = bg_layer(); d = ImageDraw.Draw(back); L = 118
d.text((L, 175), '母 题', font=f(SER, 34), fill=GOLD)
yy = 240
for s in ['判断力无人生产、无账可记，', '只由低效活动顺带养成；', '它消失时不发生任何事件。']:
    d.text((L, yy), s, font=f(SERR, 40), fill=PAPER); yy += 60
d.line([(L, yy + 22), (L + 196, yy + 22)], fill=GOLD, width=4)
yy += 74
PARA = ['做出一件东西的成本降到了接近于零。',
        '而认出它算不算数的成本，一分钱没有降。',
        '',
        '本书由学科通融专栏十篇连续研究编成，另新写',
        '导论、枢纽章、合章与结论。十章分别指认判定',
        '这一端上一个从未被单独生产的量：没有人打开过',
        '的那种否决、由弃物合成的标准、拦不下人却撤不掉',
        '的关口、为证明「是你做的」而追加的那一层、被整体',
        '转嫁的辨认负担、被计为损耗的首读时距、失去下界',
        '的计数单位、被当作背景的分辨力、不产出可验收',
        '之物的那段时间，以及一类没有供给方的能力。',
        '',
        '全书的兑现物是结论给出的十项体检读数——每一项',
        '都能从既有日志算出，且与该行业现行主要指标正交：',
        '主要指标全绿时，它可以很难看。',
        '',
        '合章再用五条从定义推出的关系把十项锁成一张可',
        '互相否证的网。其中最干净的一条说：首读时距与',
        '未阅率不是两件事，是同一个拥堵参数的两种读法。',
        '',
        '第四、七、八章各附一节「换一组学科再问一遍」，',
        '三次换组都改动了原章的处方或读数。']
for s in PARA:
    d.text((L, yy), s, font=f(SERR, 26), fill=(176, 194, 208)); yy += 42
d.text((L, H - 226), '王德生　＋　Claude　著', font=f(SER, 32), fill=PAPER)
d.text((L, H - 160), '德麦国际出版社 · SDE UNIVERSES', font=f(SAN, 24), fill=DIM)
d.text((L, H - 108), 'THE CRISIS OF JUDGMENT', font=fm(20), fill=DIM2)

full.paste(back, (0, 0))
full.paste(front, (W + SPINE, 0))
sd = ImageDraw.Draw(full)
sd.rectangle([W, 0, W + SPINE, H], fill=(13, 21, 33))
sd.line([(W, 0), (W, H)], fill=(30, 44, 60), width=2)
sd.line([(W + SPINE, 0), (W + SPINE, H)], fill=(30, 44, 60), width=2)


def stack(text, y0, font, fill, gap=6):
    y = y0
    for c in text:
        w = sd.textlength(c, font=font)
        sd.text((W + (SPINE - w) / 2, y), c, font=font, fill=fill)
        y += font.size + gap
    return y


yy = stack('判断的危机', 150, f(SER, 46), MINT, 10)
yy = stack('王德生', yy + 56, f(SAN, 22), DIM, 3)
sp2 = Image.new('RGB', (170, 34), (13, 21, 33))
ImageDraw.Draw(sp2).text((2, 2), '+ Claude', font=fm(22), fill=DIM)
full.paste(sp2.rotate(-90, expand=True), (W + (SPINE - 34) // 2, int(yy) + 14))
stack('德麦国际出版社', H - 380, f(SAN, 22), DIM, 3)
full.save('/home/claude/book80/cover-full.jpg', quality=93)
print('cover-full.jpg', full.size)
