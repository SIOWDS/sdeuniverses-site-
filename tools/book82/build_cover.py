# -*- coding: utf-8 -*-
"""《答案随时可得之后》封面 · 两条剖面线：平的那条在这张表上得分更高"""
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


# 二十格覆盖型量表；平线恰在及格线上，锐线三峰二坑，两坑落在格里
PROFILE = [0, 0, 0, 0, 0, 2.10, 0, -1.15, 0, 0, 2.35, 0, 0, -1.05, 0, 0, 1.95, 0, 0, 0]


def field(im, x0, y0, width, height):
    """height 为及格线上下各自的半幅"""
    n = len(PROFILE)
    step = width / (n - 1)
    base_y = y0 + height          # 及格线
    d = ImageDraw.Draw(im)

    # 格线
    for i in range(n):
        x = int(x0 + i * step)
        d.line([(x, y0 - 18), (x, base_y + height + 18)], fill=(26, 38, 52), width=1)

    # 及格线（金色虚线）
    for xx in range(int(x0), int(x0 + width), 16):
        d.line([(xx, base_y), (xx + 8, base_y)], fill=(96, 74, 40), width=2)

    # 平线：均浅者 —— 每格恰好及格
    lay = Image.new('RGB', im.size, (0, 0, 0)); mask = Image.new('L', im.size, 0)
    ld = ImageDraw.Draw(lay); md = ImageDraw.Draw(mask)
    ld.line([(x0, base_y - 3), (x0 + width, base_y - 3)], fill=TEAL, width=6)
    md.line([(x0, base_y - 3), (x0 + width, base_y - 3)], fill=255, width=6)

    # 锐线：深学者 —— 三峰二坑
    pts = []
    for i, v in enumerate(PROFILE):
        pts.append((x0 + i * step, base_y - 3 - v * (height / 2.6)))
    ld.line(pts, fill=MINT, width=6, joint='curve')
    md.line(pts, fill=255, width=6, joint='curve')

    tmp = Image.new('RGB', im.size, (0, 0, 0)); tmp.paste(lay, (0, 0), mask)
    glow = im.copy()
    glow.paste(tmp.filter(ImageFilter.GaussianBlur(20)), (0, 0),
               mask.filter(ImageFilter.GaussianBlur(24)))
    im.paste(Image.blend(im, glow, 0.85), (0, 0))
    im.paste(lay, (0, 0), mask)

    # 两个坑：标金色「扣一格」
    d = ImageDraw.Draw(im)
    for i, v in enumerate(PROFILE):
        if v < 0:
            x = int(x0 + i * step)
            yb = base_y - 3 - v * (height / 2.6)
            d.rectangle([x - step / 2 + 3, base_y, x + step / 2 - 3, yb],
                        outline=GOLD, width=2)
    return base_y


def front():
    im = base(); L = 118
    grad_text(im, (L, 246), '答案随时', f(SER, 112), MINT, TEAL)
    grad_text(im, (L, 386), '可得之后', f(SER, 112), MINT, TEAL)
    d = ImageDraw.Draw(im)
    d.line([(L, 546), (L + 210, 546)], fill=GOLD, width=5)
    d.text((L, 592), '论知识不是存量，及重新推出它的那一段为何不入账',
           font=f(SERR, 30), fill=PAPER)
    d.text((L, 648), 'AFTER THE ANSWER IS ALWAYS AVAILABLE', font=fm(19), fill=DIM2)

    base_y = field(im, L, 860, W - 2 * L - 6, 130)
    d = ImageDraw.Draw(im)
    d.text((L, base_y + 168), '两条线在这张表上，', font=f(SERR, 30), fill=(196, 212, 224))
    d.text((L, base_y + 224), '平的那条得分更高。', font=f(SERR, 30), fill=(196, 212, 224))

    d.text((L, H - 238), '王德生　＋　Claude　著', font=f(SER, 37), fill=PAPER)
    d.text((L, H - 158), '德麦国际出版社', font=f(SAN, 25), fill=DIM)
    t = '专著第 81 号'
    d.text((W - L - d.textlength(t, font=f(SAN, 25)), H - 158), t, font=f(SAN, 25), fill=DIM)
    return im


fr = front()
fr.save('/home/claude/book81/cover.jpg', quality=95)
print('cover.jpg', fr.size)

SPINE = 96
full = Image.new('RGB', (W * 2 + SPINE, H), BG)
bk = base(); d = ImageDraw.Draw(bk); L = 118
d.text((L, 176), '母 题', font=f(SER, 32), fill=GOLD)
y = 238
for s in ['知识不是被持有的存量，', '是每次被重新推出来的事件。', '贬值的不是知识，是「拥有」这本账。']:
    d.text((L, y), s, font=f(SERR, 37), fill=PAPER); y += 58
d.line([(L, y + 22), (L + 210, y + 22)], fill=GOLD, width=4)
y += 78
for s in ['一份合格产物随时可以从外部取到之后，被取消的',
          '不是知识，是重新推出知识的那一段；而那一段里',
          '长出来的全部东西，现行的记账法一栏也没有。',
          '',
          '本书十章由十个互不相同的学科组撞出来，写作时',
          '彼此不知情，说的却是同一句话——凡进入产物的',
          '都留下，凡不进入产物的都在退，而只有前者被记录。',
          '',
          '术后单腿跳远的距离比是百分之九十七，同一次测量',
          '里膝关节做功比是百分之六十九；八百七十九个职业',
          '中，自动化程度与决策频次相关 0.042，与决策自由度',
          '相关 −0.199。步骤留下，岔路删除。',
          '',
          '枢纽章只引入一个参数——可及性——推出七条关系，',
          '并造出全书唯一一样新东西：均浅，一种既无峰亦无坑',
          '的知识分布，它的锐度不是低，是没有定义。由它推出',
          '的判断是：在任何覆盖型量表上，衡量知识的通行办法',
          '会给损失的那一方加分。',
          '',
          '合章把十项读数锁进七条关系，并给出五条可以一起',
          '推翻它们的方式——最后一条针对的不是任何一章，',
          '而是把这十章装成一本书这个动作本身。']:
    d.text((L, y), s, font=f(SERR, 24), fill=(172, 190, 206)); y += 41
d.text((L, H - 238), '王德生　＋　Claude　著', font=f(SER, 31), fill=PAPER)
d.text((L, H - 172), '德麦国际出版社 · SDE UNIVERSES', font=f(SAN, 23), fill=DIM)
d.text((L, H - 118), 'AFTER THE ANSWER IS ALWAYS AVAILABLE', font=fm(17), fill=DIM2)

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


yy = stack('答案随时可得之后', 130, f(SER, 44), MINT, 8)
yy = stack('王德生', yy + 48, f(SAN, 22), DIM, 3)
sp = Image.new('RGB', (170, 34), (11, 17, 27))
ImageDraw.Draw(sp).text((2, 2), '+ Claude', font=fm(22), fill=DIM)
full.paste(sp.rotate(-90, expand=True), (W + (SPINE - 34) // 2, int(yy) + 14))
stack('德麦国际出版社', H - 380, f(SAN, 22), DIM, 3)
full.save('/home/claude/book81/cover-full.jpg', quality=93)
print('cover-full.jpg', full.size)
