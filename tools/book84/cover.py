# -*- coding: utf-8 -*-
"""《越顺利，越没有你的位置》封面 —— 一条信号链路自上而下逐级转手，
每一级都留下一枚回执印记；最末那一格该收信的位置，是空的（虚线框）。"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, random

W, H = 1240, 1750
BG = (12, 14, 18)
LINE = (118, 158, 190); LINE2 = (58, 82, 104)
STAMP = (196, 208, 222); DIM = (126, 136, 150); DIM2 = (72, 80, 94)
GOLD = (214, 172, 96)
PAPER = (232, 236, 242)

SER = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
SERR = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc'
SAN = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
MONO = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
IDX = 2
def f(p, s, i=IDX): return ImageFont.truetype(p, s, index=i)
def fm(s): return ImageFont.truetype(MONO, s)

random.seed(84)


def base():
    im = Image.new('RGB', (W, H), BG)
    g = Image.new('RGB', (W, H), BG); gd = ImageDraw.Draw(g)
    gd.ellipse([-360, -520, 980, 520], fill=(20, 34, 48))
    gd.ellipse([W - 280, H - 520, W + 420, H + 220], fill=(30, 24, 16))
    return Image.blend(im, g.filter(ImageFilter.GaussianBlur(230)), 0.64)


def dashed(d, x0, y0, x1, y1, fill, w=2, on=11, off=9):
    L = math.hypot(x1 - x0, y1 - y0)
    if L == 0: return
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    t = 0.0
    while t < L:
        e = min(t + on, L)
        d.line([x0 + ux * t, y0 + uy * t, x0 + ux * e, y0 + uy * e], fill=fill, width=w)
        t = e + off


def chain(im):
    """五级转手：前四级是实心回执章，第五级是空的收件格。"""
    d = ImageDraw.Draw(im, 'RGBA')
    cx = 640
    ys = [430, 560, 690, 820, 985]
    bw, bh = 300, 74
    labels = ['已 阅', '已 记 录', '已 归 档', '已 知 悉', '']
    for i, y in enumerate(ys):
        x0, x1 = cx - bw // 2, cx + bw // 2
        y0, y1 = y - bh // 2, y + bh // 2
        last = (i == len(ys) - 1)
        if not last:
            # 实心回执章：越往下越淡（信号在衰减，但记录在增加）
            a = 235 - i * 34
            d.rounded_rectangle([x0, y0, x1, y1], radius=6, outline=(*LINE, a), width=2)
            d.text((cx, y), labels[i], font=f(SAN, 25), fill=(*STAMP, a), anchor='mm')
            # 右侧回执编号
            d.text((x1 + 22, y - 11), 'RCPT-%02d' % (i + 1), font=fm(15), fill=DIM2)
        else:
            # 收件格：空的
            for (a, b, c, e) in [(x0, y0, x1, y0), (x1, y0, x1, y1),
                                 (x1, y1, x0, y1), (x0, y1, x0, y0)]:
                dashed(d, a, b, c, e, (*GOLD, 210), w=2)
            d.text((x1 + 22, y - 11), 'NO ADDRESSEE', font=fm(15), fill=GOLD)
        # 连接线
        if i < len(ys) - 1:
            ny = ys[i + 1] - bh // 2
            if i == len(ys) - 2:
                dashed(d, cx, y1, cx, ny, (*LINE2, 200), w=2)
            else:
                d.line([cx, y1, cx, ny], fill=(*LINE, 190 - i * 30), width=2)
                d.polygon([(cx, ny), (cx - 5, ny - 9), (cx + 5, ny - 9)],
                          fill=(*LINE, 190 - i * 30))
    # 顶端：信号源
    d.ellipse([cx - 7, 330 - 7, cx + 7, 330 + 7], outline=(*GOLD, 235), width=2)
    d.text((cx + 24, 320), '信号在这里产生', font=f(SERR, 19), fill=DIM)
    d.line([cx, 337, cx, ys[0] - bh // 2], fill=(*LINE, 210), width=2)
    # 空格下方的一行小字
    d.text((cx, 1052), '这一格没有名字', font=f(SERR, 20), fill=GOLD, anchor='mm')


im = base()
chain(im)
d = ImageDraw.Draw(im, 'RGBA')

d.text((88, 96), 'SDE UNIVERSES', font=f(SAN, 21), fill=DIM2)
d.text((88, 130), '专著第 84 号', font=f(SERR, 19), fill=DIM2)

d.text((88, 1128), '识别的能力还在上升，异议越来越精确。', font=f(SERR, 24), fill=DIM)
d.text((88, 1166), '失效发生在路径侧，不在判据侧。', font=f(SERR, 24), fill=DIM)

y = 1250
for line, sz in [('越顺利，', 76), ('越没有你的位置', 76)]:
    d.text((88, y), line, font=f(SER, sz), fill=PAPER)
    y += 94
d.line([90, y + 16, 300, y + 16], fill=GOLD, width=3)
d.text((90, y + 34), 'AI 时代普通人的困境与出路', font=f(SERR, 30), fill=LINE)

d.text((88, 1568), '王德生　＋　Claude', font=f(SERR, 34), fill=PAPER)
d.text((88, 1620), '据学员专栏十一位作者的十一篇论文编成', font=f(SERR, 21), fill=DIM)
d.text((88, 1664), '德麦国际出版社 · 新加坡', font=f(SERR, 20), fill=DIM2)

im.save('/home/claude/b84/out/cover.jpg', quality=94)
print('cover saved')

# ---------- 整封（封底 + 书脊 + 封面） ----------
SP = 96
FW, FH = W, H
full = Image.new('RGB', (W * 2 + SP, H), BG)
back = base()
d = ImageDraw.Draw(back, 'RGBA')
d.text((88, 120), '越顺利，越没有你的位置', font=f(SER, 40), fill=PAPER)
d.text((88, 186), 'AI 时代普通人的困境与出路', font=f(SERR, 24), fill=LINE)
d.line([88, 240, W - 88, 240], fill=(*LINE2, 220), width=2)


def wrap(text, font, maxw, dd):
    out, cur = [], ''
    for ch in text:
        if dd.textlength(cur + ch, font=font) > maxw and cur:
            out.append(cur); cur = ch
        else:
            cur += ch
    if cur: out.append(cur)
    return out


BODY = [
    '十一位互不相识的作者，十一个相隔很远的题域：公共卫生、人机协作、社会存在论、'
    '营养生成论、法哲学、团体治疗、中国思想史、人机系统审计、修复过程研究、艺术哲学、过程存在论。',
    '十章不是选出来的，是按预先写死的协议抽出来的；第十一章是编者点进来的——这一席的账，书里如实记着。',
    '十一章说的是同一件事，而它们互不知情：凡是让普通人变得更顺利的安排，'
    '都在同一个位置上取消了那个"必须由本人亲自穿越一次"的动作；而所有读数因为结果变好，一律不报警。',
    '本书的那一刀落在更靠后的地方：困境不是"感觉不到"。信号照常产生，'
    '只是寄到了一个不再有执行权的位置，然后被转成一份"已知悉"的记录。',
]
fb = f(SERR, 24)
y = 300
for para_ in BODY:
    for ln in wrap(para_, fb, W - 176, d):
        d.text((88, y), ln, font=fb, fill=(208, 216, 228)); y += 40
    y += 22

y += 30
d.text((88, y), '一句可以带走的判据：', font=f(SERR, 24), fill=DIM); y += 52
for ln in wrap('你们那儿，异议记录的数量在涨，方案实际改道的次数涨了吗？', f(SER, 28), W - 176, d):
    d.text((88, y), ln, font=f(SER, 28), fill=GOLD); y += 46

d.text((88, H - 320), '分类：人工智能与社会 / 组织理论 / 伦理学 / 认识论', font=f(SERR, 20), fill=DIM2)
d.text((88, H - 272), 'ISBN 979-8-90690-018-0', font=fm(24), fill=PAPER)
d.text((88, H - 232), 'US$21.30', font=fm(22), fill=DIM)
d.text((88, H - 182), '德麦国际有限公司 · 新加坡 · SDE Universes · 专著第 84 号',
       font=f(SERR, 20), fill=DIM2)

spine = Image.new('RGB', (SP, H), (16, 20, 26))
sd = ImageDraw.Draw(spine)
sd.line([2, 60, 2, H - 60], fill=LINE2, width=2)
sd.line([SP - 3, 60, SP - 3, H - 60], fill=LINE2, width=2)
st = Image.new('RGB', (H, SP), (16, 20, 26))
std = ImageDraw.Draw(st)
std.text((120, SP // 2), '越顺利，越没有你的位置', font=f(SER, 36), fill=PAPER, anchor='lm')
std.text((H - 120, SP // 2), '王德生 ＋ Claude', font=f(SERR, 24), fill=DIM, anchor='rm')
spine.paste(st.rotate(90, expand=True), (0, 0))

full.paste(back, (0, 0))
full.paste(spine, (W, 0))
full.paste(im, (W + SP, 0))
full.save('/home/claude/b84/out/cover-full.jpg', quality=92)
print('full cover saved')
