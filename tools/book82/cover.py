# -*- coding: utf-8 -*-
"""《山路会自己长回去》封面 —— 一条山路从左到右被两侧植被向中间合拢，
路牌、里程碑与维护记录全在；只有脚印没了。"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random, math

W, H = 1240, 1750
BG = (10, 16, 14)
MOSS = (94, 168, 118); MOSS2 = (52, 108, 78)
PATH = (206, 190, 156); PATH2 = (150, 134, 104)
GOLD = (216, 168, 84); DIM = (128, 146, 132); DIM2 = (74, 92, 80)
PAPER = (228, 236, 228)

SER = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
SERR = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc'
SAN = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
MONO = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
IDX = 2
def f(p, s, i=IDX): return ImageFont.truetype(p, s, index=i)
def fm(s): return ImageFont.truetype(MONO, s)

random.seed(82)

def base():
    im = Image.new('RGB', (W, H), BG)
    g = Image.new('RGB', (W, H), BG); gd = ImageDraw.Draw(g)
    gd.ellipse([-400, -600, 1000, 600], fill=(16, 46, 34))
    gd.ellipse([W-300, H-560, W+460, H+200], fill=(30, 26, 14))
    return Image.blend(im, g.filter(ImageFilter.GaussianBlur(230)), 0.66)


def trail(im, x0, y0, w, h):
    """一条自上而下的山路：上端宽而清晰，下端被两侧植被合拢到几乎不见。"""
    d = ImageDraw.Draw(im, 'RGBA')
    N = 260
    pts = []
    for i in range(N + 1):
        t = i / N
        y = y0 + h * t
        x = x0 + w * 0.5 + math.sin(t * 3.1 + 0.4) * w * 0.16 + math.sin(t * 7.3) * w * 0.04
        # 路面宽度：t=0 处最宽，t=1 处趋近 0（植被合拢）
        half = w * 0.150 * (1.0 - t) ** 1.55 + 1.2
        pts.append((x, y, half))

    # 路面
    for i in range(N):
        x, y, hw = pts[i]; x2, y2, hw2 = pts[i + 1]
        t = i / N
        a = int(232 * (1 - t) ** 0.75) + 12
        c1 = tuple(int(PATH[k] * (1 - t * .35) + PATH2[k] * (t * .35)) for k in range(3))
        d.polygon([(x - hw, y), (x + hw, y), (x2 + hw2, y2), (x2 - hw2, y2)], fill=c1 + (a,))

    # 两侧植被，向中间伸
    for i in range(0, N, 2):
        x, y, hw = pts[i]
        t = i / N
        grow = w * 0.155 * (t ** 1.25)          # 侵入量随 t 增大
        for side in (-1, 1):
            n = int(3 + 9 * t)
            for k in range(n):
                px = x + side * (hw + random.uniform(-6, grow * random.uniform(0.15, 1.15)))
                py = y + random.uniform(-7, 7)
                r = random.uniform(1.6, 5.4) * (0.55 + t)
                cc = MOSS if random.random() < 0.45 + t * .3 else MOSS2
                aa = int(70 + 150 * t)
                d.ellipse([px - r, py - r, px + r, py + r], fill=cc + (aa,))

    # 脚印：只在上段有，且越往下越稀，最后完全消失
    for i in range(6, int(N * 0.42), 9):
        x, y, hw = pts[i]
        t = i / N
        if random.random() > (1 - t * 2.3):
            continue
        for side in (-1, 1):
            px = x + side * hw * 0.34
            a = int(150 * (1 - t * 2.2))
            if a <= 6: continue
            d.ellipse([px - 3.4, y - 5.6, px + 3.4, y + 5.6], fill=(66, 54, 40, a))

    # 路牌（上、中、下三块，全都在，最后一块底下已无路）
    for t, label in ((0.10, 'KM 0'), (0.52, 'KM 7'), (0.90, 'KM 14')):
        i = int(t * N); x, y, hw = pts[i]
        sx = x + w * 0.20
        d.line([(sx, y), (sx, y - 40)], fill=DIM + (200,), width=3)
        d.rounded_rectangle([sx - 4, y - 62, sx + 62, y - 36], 4,
                            fill=(20, 30, 24, 235), outline=GOLD + (190,), width=2)
        d.text((sx + 5, y - 57), label, font=fm(15), fill=GOLD)

    # 底部：路已消失处的一条虚线，标"地图上这里仍是路"
    xe, ye, _ = pts[-1]
    for k in range(0, 118, 14):
        d.line([(xe - 58 + k, ye + 20), (xe - 58 + k + 7, ye + 20)], fill=DIM2 + (210,), width=2)
    return pts


def front():
    im = base()
    d = ImageDraw.Draw(im, 'RGBA')

    d.text((88, 96), 'SDE UNIVERSES', font=f(SAN, 21), fill=DIM2)
    d.text((88, 130), '专著第 82 号', font=f(SERR, 19), fill=DIM2)

    trail(im, 88, 232, 1064, 690)

    d.text((88, 952), '地图上，这条路还在。', font=f(SERR, 25), fill=DIM)
    d.text((88, 992), '路牌还在，维护预算还在。只有脚印没了。', font=f(SERR, 25), fill=DIM)

    d.line([(88, 1064), (1152, 1064)], fill=(46, 74, 58), width=2)

    y = 1112
    for line, sz in (('山路会自己', 92), ('长回去', 92)):
        d.text((88, y), line, font=f(SER, sz), fill=PAPER)
        y += sz + 18

    d.text((90, y + 22), '十件必须由本人反复做才存在的事', font=f(SERR, 31), fill=MOSS)

    d.line([(88, 1520), (300, 1520)], fill=GOLD, width=3)
    d.text((88, 1552), '王德生　＋　Claude', font=f(SERR, 34), fill=PAPER)
    d.text((88, 1606), '据学员专栏十位作者的十篇论文编成', font=f(SERR, 22), fill=DIM)
    d.text((88, 1652), '德麦国际出版社 · 新加坡', font=f(SERR, 20), fill=DIM2)
    return im


im = front()
im.save('/home/claude/sl/out/cover.jpg', quality=94)
print('front ok')

# ---------------- 封底 ----------------
SPINE = 74
full = Image.new('RGB', (W * 2 + SPINE, H), BG)
back = base()
d = ImageDraw.Draw(back, 'RGBA')

d.text((88, 120), '山路会自己长回去', font=f(SER, 44), fill=PAPER)
d.text((88, 186), '十件必须由本人反复做才存在的事', font=f(SERR, 24), fill=MOSS)
d.line([(88, 240), (1152, 240)], fill=(46, 74, 58), width=2)


def wrap(text, font, maxw, d):
    out, cur = [], ''
    for ch in text:
        if d.textlength(cur + ch, font=font) > maxw and cur:
            out.append(cur); cur = ch
        else:
            cur += ch
    if cur: out.append(cur)
    return out


BLURB = [
 '十位互不相识的作者，十个相隔很远的题域：人机协作、育儿与临床里的理解、阅读现象学、比较认知、中医辨证、语感、组织理论、法学教育、艺术生态、伦理人类学。',
 '十篇文章不是选出来的，是按预先写死的协议抽出来的——抽样框、随机种子与三条成功标准，全部写在读到它们之前。',
 '其中九篇在说同一件事，而它们互不知情：凡真正承重的那样东西，都不是谁拥有的属性，而是一次必须由本人反复付代价执行的动作；一旦被压成可以调用的完成品，读数照常甚至更好，而它已经不在了。',
 '第十篇站到了对面：那些被误认为死掉的硬壳，不是残余，是唯一能跨越肉身死亡的骨骼。',
 '本书的那一刀落在两者之间——沉淀下来的那一层，是被后来的人重新踩过，还是被供着？两种状态在所有常规读数上一模一样，而分开它们所需要的那个东西，恰恰是正在减少的那一个。',
]
y = 292
fb = f(SERR, 23)
for para in BLURB:
    for ln in wrap(para, fb, 1050, d):
        d.text((88, y), ln, font=fb, fill=(206, 218, 208)); y += 38
    y += 16

d.line([(88, y + 10), (1152, y + 10)], fill=(46, 74, 58), width=2)
y += 44
for q in ('一句可以带走的判据：',
          '你们那套手册，上一次因为一线的一次失败而被改写，',
          '是什么时候？改的是谁？'):
    d.text((88, y), q, font=f(SERR, 26), fill=GOLD if q.startswith('一句') else PAPER)
    y += 44

d.text((88, H - 300), '分类：认识论 / 组织理论 / 教育 / 知识管理', font=f(SERR, 20), fill=DIM2)
d.text((88, H - 262), 'ISBN 979-8-90690-015-9', font=fm(24), fill=PAPER)
d.text((88, H - 224), 'US$15.90', font=fm(22), fill=DIM)
d.text((88, H - 178), '德麦国际有限公司 · 新加坡 · SDE Universes', font=f(SERR, 20), fill=DIM2)

# 条码面板
bx, by = 800, H - 300
d.rounded_rectangle([bx, by, bx + 352, by + 150], 10, fill=(238, 242, 236))
code = '9798906900159'
px = bx + 26
for i, c in enumerate(code):
    wgt = 3 if int(c) % 3 else 2
    for k in range(4):
        d.rectangle([px, by + 20, px + wgt, by + 108], fill=(12, 16, 14))
        px += wgt + (2 + int(c) % 3)
d.text((bx + 62, by + 116), '9 798906 900159', font=fm(21), fill=(12, 16, 14))

back.save('/home/claude/sl/out/cover-back.jpg', quality=94)

sp = Image.new('RGB', (SPINE, H), (12, 20, 16))
ds = ImageDraw.Draw(sp)


def stack(dr, text, y0, font, fill, gap=5):
    y = y0
    for ch in text:
        b = dr.textbbox((0, 0), ch, font=font)
        dr.text(((SPINE - (b[2] - b[0])) / 2 - b[0], y), ch, font=font, fill=fill)
        y += (b[3] - b[1]) + gap
    return y


ye = stack(ds, '山路会自己长回去', 250, f(SER, 40), PAPER)
stack(ds, '王德生 ＋ Claude', ye + 70, f(SERR, 24), DIM)
ds.text((22, H - 130), '82', font=fm(30), fill=GOLD)

full.paste(back, (0, 0)); full.paste(sp, (W, 0)); full.paste(im, (W + SPINE, 0))
full.save('/home/claude/sl/out/cover-full.jpg', quality=93)
print('full ok', full.size)
