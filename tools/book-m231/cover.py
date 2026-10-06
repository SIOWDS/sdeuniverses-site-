#!/usr/bin/env python3
"""第 231 号封面封底：用著者原稿里附的原版封面、封底图（art/），不重画。
原图比例 0.671，内页 170×240（0.708）与阅读版 190×250（0.76）都更宽：整图等高居中，两侧用原图放大模糊后的底补足，不裁字。
用法：python3 cover.py --out <out>"""
import argparse, io
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance
import pymupdf
HERE = Path(__file__).parent

def page(img, wmm, hmm, px_h=3000):
    H = px_h; W = round(H * wmm / hmm)
    fg = img.resize((round(H * img.width / img.height), H), Image.LANCZOS)
    bg = ImageEnhance.Brightness(img.resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(60))).enhance(0.55)
    bg.paste(fg, ((W - fg.width) // 2, 0))
    return bg

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', type=Path, required=True)
    out = ap.parse_args().out; out.mkdir(parents=True, exist_ok=True)
    for name, src in (('cover', 'cover-original.jpg'), ('back', 'backcover-original.jpg')):
        img = Image.open(HERE / 'art' / src).convert('RGB')
        for tag, (w, h) in (('print', (170, 240)), ('reader', (190, 250))):
            buf = io.BytesIO(); page(img, w, h).save(buf, 'JPEG', quality=90)
            d = pymupdf.open(); pg = d.new_page(width=w * 72 / 25.4, height=h * 72 / 25.4)
            pg.insert_image(pg.rect, stream=buf.getvalue()); d.save(str(out / f'{name}-{tag}.pdf'))
        web = img if img.width <= 1200 else img.resize((1200, round(1200 * img.height / img.width)), Image.LANCZOS)
        web.save(out / ('cover.jpg' if name == 'cover' else 'backcover.jpg'), 'JPEG', quality=88)
    print('covers ok')

if __name__ == '__main__':
    main()
