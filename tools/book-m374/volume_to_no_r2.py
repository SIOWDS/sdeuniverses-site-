#!/usr/bin/env python3
"""第 374 号：把 PDF 里所有“第 374 卷”改成“第 374 号”（全书与学习包）。书中引文里的“第七卷”等不动；不改版面。
用法：volume_to_no_r2.py                     在 Actions 里跑，读写 R2
      volume_to_no_r2.py --local IN OUT COUNT  本地改一份并核对，不碰 R2"""
import collections
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

import pymupdf
import weasyprint

BUCKET = 'sdeuniverses-pdf'
TARGETS = {
    'books/m/374/downloads/chemistry-history-v1.1.pdf': ('5d6d2236fb490e64cfb98f6a501fb4bc', 495),
    'books/m/374/downloads/chemistry-learning-v1.0.pdf': ('ba90a7b1ee779f9e1dc294b799b244c0', 1),
}


def glyph_pdf(size, color, tmp, cache={}):
    """一个只含“号”字的小页，返回文档和字的基线原点。"""
    key = (size, color)
    if key not in cache:
        path = Path(tmp) / f'g{len(cache)}.pdf'
        html = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><style>
@page{{size:30pt 30pt;margin:0}} html,body{{margin:0;background:transparent}}
div{{position:absolute;left:5pt;top:5pt;font:400 {size}pt/1.2 'Noto Serif CJK SC';color:#{color:06x}}}
</style></head><body><div>号</div></body></html>"""
        weasyprint.HTML(string=html).write_pdf(str(path))
        doc = pymupdf.open(path)
        origin = None
        for b in doc[0].get_text('rawdict')['blocks']:
            for l in b.get('lines', []):
                for s in l['spans']:
                    for c in s['chars']:
                        if c['c'] == '号':
                            origin = c['origin']
        assert origin, 'glyph'
        cache[key] = (doc, origin)
    return cache[key]


def hits(page):
    out = []
    for b in page.get_text('rawdict')['blocks']:
        for l in b.get('lines', []):
            chars = [(c, s) for s in l['spans'] for c in s['chars']]
            for k, (c, s) in enumerate(chars):
                if c['c'] == '卷':
                    pre = ''.join(x[0]['c'] for x in chars[:k]).replace(' ', '').replace('　', '')
                    if pre.endswith('374'):
                        out.append((c, s))
    return out


def convert(src, out, expected):
    d = pymupdf.open(src)
    toc = d.get_toc()
    n = 0
    with tempfile.TemporaryDirectory() as tmp:
        for page in d:
            found = hits(page)
            if not found:
                continue
            for c, s in found:
                x0, y0, x1, y1 = c['bbox']
                page.add_redact_annot(pymupdf.Rect(x0 + .8, y0 + 1, x1 - .8, y1 - 1), fill=False)
            page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE, graphics=pymupdf.PDF_REDACT_LINE_ART_NONE,
                                  text=pymupdf.PDF_REDACT_TEXT_REMOVE)
            for c, s in found:
                g, (ox, oy) = glyph_pdf(s['size'], s['color'], tmp)
                tx, ty = c['origin']
                page.show_pdf_page(pymupdf.Rect(tx - ox, ty - oy, tx - ox + 30, ty - oy + 30), g, 0, overlay=True)
                n += 1
        assert n == expected, (n, expected)
        m = d.metadata
        for k in ('subject', 'title', 'keywords'):
            if m.get(k):
                m[k] = m[k].replace('第374卷', '第374号').replace('第 374 卷', '第 374 号')
        d.set_metadata(m)
        if toc:
            d.set_toc(toc)
        d.save(out, garbage=3, deflate=True)
    d.close()


def check(src, out, expected):
    a, b = pymupdf.open(src), pymupdf.open(out)
    assert len(a) == len(b)
    total = 0
    for i in range(len(a)):
        ca = collections.Counter(''.join(a[i].get_text().split()))
        cb = collections.Counter(''.join(b[i].get_text().split()))
        k = ca['卷'] - cb['卷']
        total += k
        ca['卷'] -= k
        ca['号'] += k
        assert +ca == +cb, (i, (ca - cb), (cb - ca))
        assert not hits(b[i]), i
    assert total == expected, total
    assert a.get_toc() == b.get_toc()
    assert '卷' not in (b.metadata.get('subject') or '')
    return len(b)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--local':
        convert(sys.argv[2], sys.argv[3], int(sys.argv[4]))
        print('pages', check(sys.argv[2], sys.argv[3], int(sys.argv[4])))
        return
    import boto3
    os.environ.setdefault('AWS_REQUEST_CHECKSUM_CALCULATION', 'when_required')
    os.environ.setdefault('AWS_RESPONSE_CHECKSUM_VALIDATION', 'when_required')
    c = boto3.client('s3', endpoint_url='https://d3ea22f828ce19cf113a457ceba2c930.r2.cloudflarestorage.com', region_name='auto')
    work = Path(os.environ.get('RUNNER_TEMP', '/tmp')) / 'm374'
    work.mkdir(parents=True, exist_ok=True)
    built = {}
    for i, (key, (md5, count)) in enumerate(TARGETS.items()):
        src, out = work / f'cur{i}.pdf', work / f'new{i}.pdf'
        c.download_file(BUCKET, key, str(src))
        assert hashlib.md5(src.read_bytes()).hexdigest() == md5, key
        convert(str(src), str(out), count)
        built[key] = (out, check(str(src), str(out), count))
    res = {}
    for key, (out, pages) in built.items():
        raw = out.read_bytes()
        m = hashlib.md5(raw).hexdigest()
        c.put_object(Bucket=BUCKET, Key=key, Body=raw, ContentType='application/pdf', CacheControl='public, max-age=3600')
        h = c.head_object(Bucket=BUCKET, Key=key)
        assert h['ContentLength'] == len(raw) and h['ETag'].strip('"') == m, key
        res[key] = {'bytes': len(raw), 'md5': m, 'pages': pages}
    Path('m374-r2-result.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print('R2 OK', res)


if __name__ == '__main__':
    main()
