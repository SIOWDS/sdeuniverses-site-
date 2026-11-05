#!/usr/bin/env python3
"""第 438 号学习包 PDF 改署名：第 1 页换新封面、「原书作者」一行改为胡志英，PDF 属性同改；其余页不动。
用法：python3 patch_learning_pdf.py <旧.pdf> <cover.png> <新.pdf>"""
import sys
import pymupdf

src, cover, out = sys.argv[1:4]
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
d = pymupdf.open(src)
p = d[0]
p.replace_image(p.get_images()[0][0], filename=cover)
OLD = '原书作者：王德生'
NEW = '原书作者：胡志英　指导老师：王德生'
hit = None
for b in p.get_text('dict')['blocks']:
    for line in b.get('lines', []):
        text = ''.join(s['text'] for s in line['spans'])
        if OLD in text:
            hit = line
assert hit, 'author line not found'
span = hit['spans'][0]
box = pymupdf.Rect(hit['bbox'])
print('author line', span['font'], span['size'], span['color'], box)
p.add_redact_annot(box)
p.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE, graphics=pymupdf.PDF_REDACT_LINE_ART_NONE)
col = pymupdf.sRGB_to_pdf(span['color'])
p.insert_font(fontname='nsans', fontfile=FONT)
p.insert_text(span['origin'], NEW, fontname='nsans', fontsize=span['size'], color=col)
meta = dict(d.metadata)
meta['author'] = '胡志英（原书）；配套学习设计'
d.set_metadata(meta)
d.save(out, garbage=3, deflate=True)
