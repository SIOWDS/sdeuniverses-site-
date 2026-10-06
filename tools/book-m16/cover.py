#!/usr/bin/env python3
"""第 16 号封面与封底：cover/ 下由系列 make_cover.py 生成的 SVG（封底已去掉右上装饰圆，免与判词相叠），
渲染成高清图后排成印刷版 170×240、阅读版 190×250 的单页 PDF，另出站上用的 JPG。

用法：python3 cover.py --out /tmp/edu-build
"""
import argparse
import io
from pathlib import Path

import cairosvg
import pymupdf
from PIL import Image

MM = 72 / 25.4
HERE = Path(__file__).parent / 'cover'


def render(svg, w):
    png = cairosvg.svg2png(bytestring=svg.read_text().encode(), output_width=w, output_height=round(w * 240 / 170))
    return Image.open(io.BytesIO(png)).convert('RGB')


def fit(img, W, H):
    """按高放满，左右用边列拉伸补齐（底色是渐变藏青，看不出接缝）。"""
    ph = img.height; pw = round(ph * W / H)
    canvas = Image.new('RGB', (pw, ph)); x0 = (pw - img.width) // 2
    if x0 > 0:
        canvas.paste(img.crop((0, 0, 1, ph)).resize((x0, ph)), (0, 0))
        canvas.paste(img.crop((img.width - 1, 0, img.width, ph)).resize((pw - x0 - img.width, ph)), (x0 + img.width, 0))
    canvas.paste(img, (max(x0, 0), 0))
    return canvas


def page_pdf(img, W, H, out):
    doc = pymupdf.open(); pg = doc.new_page(width=W * MM, height=H * MM)
    buf = io.BytesIO(); img.save(buf, 'JPEG', quality=92)
    pg.insert_image(pg.rect, stream=buf.getvalue()); doc.save(str(out), garbage=4, deflate=True)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
    front, back = render(HERE / 'pg-front.svg', 1800), render(HERE / 'pg-back.svg', 1800)
    for name, img in (('cover', front), ('back', back)):
        page_pdf(img, 170, 240, a.out / f'{name}-print.pdf')
        page_pdf(fit(img, 190, 250), 190, 250, a.out / f'{name}-reader.pdf')
    for name, img in (('cover', front), ('backcover', back)):
        img.resize((1004, round(1004 * img.height / img.width)), Image.LANCZOS).save(
            a.out / f'{name}.jpg', 'JPEG', quality=88, optimize=True, progressive=True)
    print('covers ok', a.out)


if __name__ == '__main__':
    main()
