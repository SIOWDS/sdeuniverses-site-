#!/usr/bin/env python3
"""第 374 号加封面封底：在 Actions 里取 R2 上的现行 PDF，前加封面、封二，后加封三、封底，核过再写回 R2（PDF 不进 git）。
用法：publish_r2_pdf.py                在 Actions 里跑，读写 R2
      publish_r2_pdf.py --local OLD OUT  本地合成并核对，不碰 R2"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pymupdf

HERE = Path(__file__).resolve().parent
KEY = 'books/m/374/downloads/chemistry-history-v1.1.pdf'
BUCKET = 'sdeuniverses-pdf'
OLD_MD5 = 'b9aae395db5b4ff8dc573f33056d5513'
OLD_PAGES = 494
FRONT, BACK = 2, 2


def merge(old, cover_dir, out):
    assert hashlib.md5(Path(old).read_bytes()).hexdigest() == OLD_MD5, 'R2 上不是预期的旧版'
    d = pymupdf.open(old)
    assert len(d) == OLD_PAGES
    toc = d.get_toc(simple=False)
    old_labels = d.get_page_labels()
    w, h = d[0].rect.width, d[0].rect.height
    # 先加后面、再加前面：书签和书内跳转都按页对象指，不受影响
    d.new_page(-1, width=w, height=h)
    with pymupdf.open(cover_dir / 'back-print.pdf') as b:
        d.insert_pdf(b)
    d.new_page(0, width=w, height=h)
    with pymupdf.open(cover_dir / 'cover-print.pdf') as c:
        d.insert_pdf(c, start_at=0)
    assert len(d) == OLD_PAGES + FRONT + BACK
    shifted = [[e[0], e[1], e[2] + FRONT, *e[3:]] for e in toc]
    d.set_toc([[e[0], e[1], e[2]] for e in shifted])
    assert not old_labels
    d.set_page_labels([])   # 旧版没有页码标签；封面 PDF 带进来的要清掉
    d.save(out, garbage=3, deflate=True)
    d.close()


def check(old, out):
    a, b = pymupdf.open(old), pymupdf.open(out)
    assert len(b) == OLD_PAGES + FRONT + BACK
    first = b[0].get_text()
    for t in ('化学思想史', '从物质同一性到化学世界的创造', '胡志英', '德麦国际出版社', '第 3 7 4 号', 'NH3', '反应进程'):
        assert t in first, t
    assert '王德生' not in first and '王德生' not in b[len(b) - 1].get_text()
    assert not b[1].get_text().strip() and not b[len(b) - 2].get_text().strip()
    assert '979-8-90690-588-8' in b[len(b) - 1].get_text()
    for i in range(OLD_PAGES):
        assert a[i].get_text() == b[i + FRONT].get_text(), i
    ta, tb = a.get_toc(), b.get_toc()
    assert len(ta) == len(tb) and all(x[1] == y[1] and x[2] + FRONT == y[2] for x, y in zip(ta, tb))
    return len(b)


def covers(out_dir):
    subprocess.run([sys.executable, str(HERE / 'cover.py'), '--out', str(out_dir)], check=True)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--local':
        old, out = sys.argv[2], sys.argv[3]
        cdir = Path(out).parent / 'covers'
        covers(cdir)
        merge(old, cdir, out)
        print('pages', check(old, out))
        return
    import boto3
    os.environ.setdefault('AWS_REQUEST_CHECKSUM_CALCULATION', 'when_required')
    os.environ.setdefault('AWS_RESPONSE_CHECKSUM_VALIDATION', 'when_required')
    c = boto3.client('s3', endpoint_url='https://d3ea22f828ce19cf113a457ceba2c930.r2.cloudflarestorage.com', region_name='auto')
    work = Path(os.environ.get('RUNNER_TEMP', '/tmp')) / 'm374'
    work.mkdir(parents=True, exist_ok=True)
    old, out = work / 'old.pdf', work / 'new.pdf'
    c.download_file(BUCKET, KEY, str(old))
    covers(work)
    merge(old, work, out)
    pages = check(old, out)
    raw = out.read_bytes()
    md5 = hashlib.md5(raw).hexdigest()
    c.put_object(Bucket=BUCKET, Key=KEY, Body=raw, ContentType='application/pdf', CacheControl='public, max-age=3600')
    h = c.head_object(Bucket=BUCKET, Key=KEY)
    assert h['ContentLength'] == len(raw) and h['ETag'].strip('"') == md5
    res = {'key': KEY, 'bytes': len(raw), 'md5': md5, 'pages': pages}
    Path('m374-r2-result.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print('R2 OK', res)


if __name__ == '__main__':
    main()
