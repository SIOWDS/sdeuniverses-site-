#!/usr/bin/env python3
"""第 607 号《SDE思想大全》封面与封底：沿用作者提供的 assets/cover.png、back.png（1339×1890，深蓝底），不重绘。
  cover.jpg / backcover.jpg：原画面转 JPG（质量 92），站上详情页与全文页用；
  cover-print.pdf / back-print.pdf（170×240 mm，与原图同比例，铺满）；
  cover-reader.pdf / back-reader.pdf（190×250 mm：原图按页高放入，左右两侧用图像最外一列像素横向延伸补足，画面不动）。
  全部为位图页（站上翻页器的矢量模式画不出渐变，位图最稳）。
用法：python3 cover.py --out <dir>      （--fonts 参数保留以兼容 build 的调用，不使用）
"""
import argparse
import io
from pathlib import Path

HERE = Path(__file__).resolve().parent


def page_pdf(img, w_mm, h_mm, out):
    import pymupdf
    buf = io.BytesIO(); img.save(buf, 'JPEG', quality=93, subsampling=0)
    doc = pymupdf.open()
    W, H = w_mm / 25.4 * 72, h_mm / 25.4 * 72
    pg = doc.new_page(width=W, height=H)
    pg.insert_image(pg.rect, stream=buf.getvalue())
    doc.save(str(out), deflate=True)


def stretch_to(img, ratio):
    """宽高比补到 ratio（宽/高）：两侧用最外一列像素横向延伸。"""
    from PIL import Image
    w, h = img.size
    nw = round(h * ratio)
    if nw <= w:
        return img
    pad = nw - w; l = pad // 2; r = pad - l
    out = Image.new('RGB', (nw, h))
    out.paste(img, (l, 0))
    out.paste(img.crop((0, 0, 1, h)).resize((l, h)), (0, 0))
    out.paste(img.crop((w - 1, 0, w, h)).resize((r, h)), (l + w, 0))
    return out


def main():
    from PIL import Image
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--fonts', type=Path)
    ap.add_argument('--src', type=Path, default=HERE / 'assets')
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    for name, jpg, tag in (('cover', 'cover.jpg', 'cover'), ('back', 'backcover.jpg', 'back')):
        im = Image.open(a.src / (name + '.png')).convert('RGB')
        im.save(a.out / jpg, 'JPEG', quality=92, subsampling=0)
        page_pdf(im, 170, 240, a.out / ('%s-print.pdf' % tag))
        page_pdf(stretch_to(im, 190 / 250), 190, 250, a.out / ('%s-reader.pdf' % tag))
    print('covers ok')


if __name__ == '__main__':
    main()
