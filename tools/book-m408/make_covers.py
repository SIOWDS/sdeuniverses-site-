"""把封面、封底 JPG 做成单页 PDF（170×240 mm），供 build.py 嵌入。用法：python3 make_covers.py <cover.jpg> <backcover.jpg> <out>"""
import sys, pymupdf
from pathlib import Path
cv, bk, out = sys.argv[1], sys.argv[2], Path(sys.argv[3]); out.mkdir(parents=True, exist_ok=True)
W, H = 170 / 25.4 * 72, 240 / 25.4 * 72
for src, names in [(cv, ['cover-print.pdf', 'cover-reader.pdf']), (bk, ['back-print.pdf', 'back-reader.pdf'])]:
    for n in names:
        d = pymupdf.open(); pg = d.new_page(width=W, height=H); pg.insert_image(pg.rect, filename=src, keep_proportion=False); d.save(str(out / n))
print('ok')
