#!/usr/bin/env python3
"""第 374 号补作者介绍：排在封二（封面背后的空白页），不增页、不动页码。
用法：add_author_bio_r2.py                在 Actions 里跑，读写 R2
      add_author_bio_r2.py --local IN OUT  本地合成并核对，不碰 R2"""
import hashlib
import json
import os
import sys
from pathlib import Path

import pymupdf
import weasyprint

KEY = 'books/m/374/downloads/chemistry-history-v1.1.pdf'
BUCKET = 'sdeuniverses-pdf'
R2_MD5 = 'e7b22a71733c350e7fc72b7ef4d402f4'
PAGES = 498
PAGE = 1  # 封二

BIO = ['胡志英（John Hu），著者，约翰英语创始人、攀阁林学院联合创始人，曾任郑州灵答英语执行校长，从事英语教育与课程创新十三年以上，长期研读并实践以乔姆斯基与克拉申为代表的语言学与语言习得理论；SDE Universes 学员，在学员专栏写作语言、认知、制度与教育方面的论文，此前著有德麦国际专著第 105 号《下一步才算数》、第 108 号《语言符号的智慧》、第 183 号《胡志英讲乔姆斯基：普通人都能懂》。',
       '王德生，博士，SIO 本体论与 SDE 发生学的创立者，新加坡德麦国际创始人。早年在湘潭大学、中国科学院学习与研究计算数学，后任新加坡南洋理工大学数学系教员；2015 年起推广三视角方法论，2024 年提出 SIO 本体论与意义三律，后凝练为 SDE 发生学。本书由他指导。']


def overlay(path, w, h):
    paras = ''.join(f'<p>{t}</p>' for t in BIO)
    html = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><style>
@page{{size:{w}pt {h}pt;margin:0}} html,body{{margin:0;background:transparent}}
.b{{position:absolute;left:48.3pt;top:60pt;width:378pt}}
h2{{font:700 22pt/1.45 'Noto Serif CJK SC';color:#1d2b4c;margin:0}}
.r{{width:32pt;border-top:1.2pt solid #b8913e;margin:15pt 0 28pt}}
p{{font:400 10.5pt/18.7pt 'Noto Serif CJK SC';color:#1f2430;margin:0 0 9pt;text-indent:2em}}
</style></head><body><div class="b"><h2>作者介绍</h2><div class="r"></div>{paras}</div></body></html>"""
    weasyprint.HTML(string=html).write_pdf(path)


def build(src, out, tmp):
    d = pymupdf.open(src)
    assert len(d) == PAGES
    pg = d[PAGE]
    assert not pg.get_text().strip(), '封二不是空白页'
    overlay(tmp, pg.rect.width, pg.rect.height)
    with pymupdf.open(tmp) as o:
        assert len(o) == 1
        pg.show_pdf_page(pg.rect, o, 0, overlay=True)
    toc = d.get_toc()
    assert toc[0][1] == '出版信息'
    d.set_toc([[1, '作者介绍', PAGE + 1]] + toc)
    d.save(out, garbage=3, deflate=True)
    d.close()


def check(src, out):
    a, b = pymupdf.open(src), pymupdf.open(out)
    assert len(b) == PAGES
    for i in range(PAGES):
        if i != PAGE:
            assert a[i].get_text() == b[i].get_text(), i
    t = b[PAGE].get_text().replace('\n', '')
    for x in ('作者介绍', '约翰英语创始人', '本书由他指导'):
        assert x in t, x
    ta, tb = a.get_toc(), b.get_toc()
    assert len(tb) == len(ta) + 1 and tb[0][1] == '作者介绍' and tb[1:] == ta
    return len(b)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--local':
        src, out = sys.argv[2], sys.argv[3]
        build(src, out, str(Path(out).with_suffix('.overlay.pdf')))
        print('pages', check(src, out))
        return
    import boto3
    os.environ.setdefault('AWS_REQUEST_CHECKSUM_CALCULATION', 'when_required')
    os.environ.setdefault('AWS_RESPONSE_CHECKSUM_VALIDATION', 'when_required')
    c = boto3.client('s3', endpoint_url='https://d3ea22f828ce19cf113a457ceba2c930.r2.cloudflarestorage.com', region_name='auto')
    work = Path(os.environ.get('RUNNER_TEMP', '/tmp')) / 'm374'
    work.mkdir(parents=True, exist_ok=True)
    src, out = work / 'cur.pdf', work / 'new.pdf'
    c.download_file(BUCKET, KEY, str(src))
    assert hashlib.md5(src.read_bytes()).hexdigest() == R2_MD5, 'R2 上不是预期的版本'
    build(str(src), str(out), str(work / 'overlay.pdf'))
    pages = check(str(src), str(out))
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
