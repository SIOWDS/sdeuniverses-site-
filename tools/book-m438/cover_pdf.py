#!/usr/bin/env python3
"""第 438 号：封面封底来自著者定稿图 cover.png / back.png（900×1270，已含书号、ISBN、条形码、定价），不用 503 的 cover.py 内置插画。
产出（都写到 --out）：
  cover-print.pdf、back-print.pdf     170×240 mm 整页铺满（图宽高比 0.7087，页 0.7083，按页宽等比放，上下各差 0.05 mm，不拉伸）
  cover-reader.pdf、back-reader.pdf   190×250 mm：图按页高等比居中，两侧按图左缘逐行取色补满（底色是纯竖向渐变，左右同色，接缝不可见）
  cover.jpg、backcover.jpg            900×1270 原样转 JPEG（网页封面用）
用法：python3 cover_pdf.py --src /home/claude/book4/cover --out /home/claude/b438
"""
import argparse, io
from pathlib import Path
from PIL import Image
import pymupdf

ap = argparse.ArgumentParser(); ap.add_argument('--src', type=Path, required=True); ap.add_argument('--out', type=Path, required=True)
a = ap.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
MM = 72 / 25.4


def png_bytes(im):
    b = io.BytesIO(); im.save(b, 'PNG'); return b.getvalue()


def page_pdf(path, wmm, hmm, im, fit):
    doc = pymupdf.open(); pg = doc.new_page(width=wmm * MM, height=hmm * MM)
    W, H = wmm * MM, hmm * MM
    iw, ih = im.size
    if fit == 'width':
        w = W; h = W * ih / iw
    else:
        h = H; w = H * iw / ih
    x, y = (W - w) / 2, (H - h) / 2
    pg.insert_image(pymupdf.Rect(x, y, x + w, y + h), stream=png_bytes(im))
    doc.save(str(path), garbage=4, deflate=True)


def reader_canvas(im, wmm=190, hmm=250, px=1520):
    """整页画布：图按高度等比缩放居中，两侧逐行取图左缘 x=2 的颜色。"""
    cw, ch = px, round(px * hmm / wmm)
    s = ch / im.height
    iw = round(im.width * s)
    r = im.resize((iw, ch), Image.LANCZOS)
    can = Image.new('RGB', (cw, ch))
    edge = im.resize((1, ch), Image.BILINEAR) if False else None
    col = [im.getpixel((2, min(im.height - 1, int(y / s)))) for y in range(ch)]
    px_ = can.load()
    for y in range(ch):
        c = col[y]
        for x in range(cw):
            px_[x, y] = c
    can.paste(r, ((cw - iw) // 2, 0))
    return can


for src, tag, jpg in [('cover.png', 'cover', 'cover.jpg'), ('back.png', 'back', 'backcover.jpg')]:
    im = Image.open(a.src / src).convert('RGB')
    assert im.size == (900, 1270), im.size
    im.save(a.out / jpg, quality=92, optimize=True)
    page_pdf(a.out / f'{tag}-print.pdf', 170, 240, im, 'width')
    page_pdf(a.out / f'{tag}-reader.pdf', 190, 250, reader_canvas(im), 'width')
    print(tag, 'ok')
