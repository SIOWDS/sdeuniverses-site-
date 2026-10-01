#!/usr/bin/env python3
"""第 274 号封面与封底：用作者来稿 DOCX 里的两张图（藏青底、金色蝴蝶与枝条，已含 ISBN 条码），
排成印刷版 170×240、阅读版 190×250 两种开本的单页 PDF，另出站上用的 JPG。

来稿图 1800×2540，宽高比 0.709，正合 170×240；阅读版 190×250 更宽，
图按高度放满、居中，左右两条用图边那一列像素拉宽补齐（底色是渐变藏青，看不出接缝），不裁掉条码与字。

用法：python3 cover.py SOURCE.docx --out /tmp/zhuangzi-build
"""
import argparse
import io
import zipfile
from pathlib import Path

import pymupdf
from PIL import Image

MM = 72 / 25.4


def fit(img, W, H, px_per_mm=1800 / 170):
    """把图放进 W×H mm 的页面：按高放满，左右用边列拉伸补齐。"""
    ph = round(H * px_per_mm)
    pw = round(W * px_per_mm)
    s = img.resize((round(img.width * ph / img.height), ph), Image.LANCZOS)
    canvas = Image.new('RGB', (pw, ph))
    x0 = (pw - s.width) // 2
    if x0 > 0:
        canvas.paste(s.crop((0, 0, 1, ph)).resize((x0, ph)), (0, 0))
        canvas.paste(s.crop((s.width - 1, 0, s.width, ph)).resize((pw - x0 - s.width, ph)), (x0 + s.width, 0))
    canvas.paste(s, (x0, 0))
    return canvas


def page_pdf(img, W, H, out):
    doc = pymupdf.open()
    pg = doc.new_page(width=W * MM, height=H * MM)
    buf = io.BytesIO(); img.save(buf, 'JPEG', quality=92)
    pg.insert_image(pg.rect, stream=buf.getvalue())
    doc.save(str(out), garbage=4, deflate=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('docx', type=Path)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(a.docx) as z:
        front = Image.open(io.BytesIO(z.read('word/media/image1.png'))).convert('RGB')
        back = Image.open(io.BytesIO(z.read('word/media/image2.png'))).convert('RGB')
    for name, img in (('cover', front), ('back', back)):
        page_pdf(fit(img, 170, 240), 170, 240, a.out / f'{name}-print.pdf')
        page_pdf(fit(img, 190, 250), 190, 250, a.out / f'{name}-reader.pdf')
    web = {'cover': front, 'backcover': back}
    for name, img in web.items():
        im = img.resize((1004, round(1004 * img.height / img.width)), Image.LANCZOS)
        im.save(a.out / f'{name}.jpg', 'JPEG', quality=88, optimize=True, progressive=True)
    print('covers ok', a.out)


if __name__ == '__main__':
    main()
