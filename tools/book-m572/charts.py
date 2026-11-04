#!/usr/bin/env python3
"""第 572 号：把第 26 章的十张缠图（/home/claude/klife/run/charts/*.png，RGBA）铺白底压成 jpg，放进
public/books/m/572/text/charts/<slug>.jpg（全文网页用相对路径 charts/…，build.py 排 PDF 时也从这里取），每张须 < 300KB。
用法（仓库根目录）：python3 tools/book-m572/charts.py"""
import sys
from pathlib import Path
from PIL import Image
sys.path.insert(0, 'tools/book-m572')
import meta as M  # noqa: E402
out = Path('public/books/m/%d/text/charts' % M.NO)
out.mkdir(parents=True, exist_ok=True)
for nm, sl in M.CHARTS:
    im = Image.open(Path(M.CHARTS_DIR) / (nm + '.png')).convert('RGBA')
    bg = Image.new('RGB', im.size, (255, 255, 255))
    bg.paste(im, mask=im.split()[3])
    p = out / (sl + '.jpg')
    for q in (88, 82, 75, 68):
        bg.save(p, 'JPEG', quality=q, optimize=True, progressive=True)
        if p.stat().st_size < 300 * 1024:
            break
    assert p.stat().st_size < 300 * 1024, p
    print(nm, p, bg.size, p.stat().st_size)
