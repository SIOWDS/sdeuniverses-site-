#!/usr/bin/env python3
"""第 523 号《陈晓艳谈「懂」》：封面封底用著者给定的图（不另做、封面不写「王德生指导」），
铺成 build.py 要的四个单页 PDF，并拷成站上用的 cover.jpg、backcover.jpg。
印刷版 170×240 mm 与原图同比例，直接铺满；阅读版 190×250 mm 按宽铺满、上下居中裁去少许。
用法：python3 covers.py --src <放 cover-front.jpg、cover-back.jpg 的目录> --out /home/claude/b523
"""
import argparse, shutil
from pathlib import Path
import pymupdf

MM = 72 / 25.4


def page(img, out, wmm, hmm):
    doc = pymupdf.open()
    W, H = wmm * MM, hmm * MM
    pg = doc.new_page(width=W, height=H)
    pix = pymupdf.Pixmap(str(img))
    ih = W * pix.height / pix.width          # 按宽铺满后的高
    top = (H - ih) / 2
    pg.insert_image(pymupdf.Rect(0, top, W, top + ih), filename=str(img), keep_proportion=False)
    doc.save(str(out))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--src', type=Path, required=True); ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
    f, b = a.src / 'cover-front.jpg', a.src / 'cover-back.jpg'
    for tag, (w, h) in {'print': (170, 240), 'reader': (190, 250)}.items():
        page(f, a.out / f'cover-{tag}.pdf', w, h)
        page(b, a.out / f'back-{tag}.pdf', w, h)
    shutil.copy(f, a.out / 'cover.jpg'); shutil.copy(b, a.out / 'backcover.jpg')
    print('covers ok')


if __name__ == '__main__':
    main()
