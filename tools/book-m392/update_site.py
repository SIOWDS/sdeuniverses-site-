#!/usr/bin/env python3
"""把 build.py / cover.py 的产物装进 public/books/m/215/：PDF、封面、全文网页、翻页器、详情页、书目、站点地图、/today/ 新书卡。

用法：python3 publish.py --build /home/claude/mengzi/build
（由第 274 号 tools/book-zhuangzi/publish.py 改来）
"""
import argparse
import datetime
import json
import re
import shutil
from pathlib import Path

HERE = Path(__file__).parent
SITE = HERE.resolve().parents[1] / 'public'
NO = 392
V = '20261014b'
SLUG = 'sde-ai-haixiao'
T, SUB = 'SDE ⊗ AI', '海啸的启明星、头狼、仆人'
ISBN = '979-8-90690-822-3'


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--build', type=Path, required=True)
    b = ap.parse_args().build
    d = SITE / 'books' / 'm' / str(NO)
    assert (d / 'index.html').exists(), f'{NO} 号目录不存在'
    (d / 'text').mkdir(parents=True, exist_ok=True)
    for f in [f'{SLUG}-print.pdf', f'{SLUG}-reader.pdf', 'cover.jpg', 'backcover.jpg']:
        shutil.copy(b / f, d / f)
    shutil.copy(b / 'text.html', d / 'text' / 'index.html')
    shutil.copy(b / 'cover.jpg', d / 'cover.jpg'); shutil.copy(b / 'backcover.jpg', d / 'backcover.jpg')
    # 翻页器：照第 259 号的矢量翻页器，只换书名、PDF 与目录
    tpl = (SITE / 'books' / 'm' / '259' / 'read.html').read_text()
    toc = json.loads((b / 'toc-reader.json').read_text())
    import pymupdf as _p
    _n = len(_p.open(str(b / f'{SLUG}-reader.pdf')))
    toc['toc'] = [{'t': '封面', 'p': '', 'g': 1, 'l': 1}] + toc['toc'] + [{'t': '封底', 'p': '', 'g': _n, 'l': 1}]
    rep = [
        ('友好阅读 · 在线翻页 · 谈尼采视角主义的错误 | SDE Universes', f'友好阅读 · 在线翻页 · {T} | SDE Universes'),
        ('《谈尼采视角主义的错误》在线翻页阅读', f'《{T}》在线翻页阅读'),
        ('https://sdeuniverses.com/books/m/259/read.html', f'https://sdeuniverses.com/books/m/{NO}/read.html'),
        ('<span class="ttl">谈尼采视角主义的错误</span><span class="sub hideS">视角是选出来的，还是长出来的</span>',
         f'<span class="ttl">{T}</span><span class="sub hideS">{SUB}</span>'),
        ('<a href="/books/m/259/"', f'<a href="/books/m/{NO}/"'),
        ("title: '谈尼采视角主义的错误',", f"title: '{T}',"),
        ("msg('正在载入《谈尼采视角主义的错误》…');", f"msg('正在载入《{T}》…');"),
    ]
    for a, c in rep:
        assert a in tpl, a[:50]
        tpl = tpl.replace(a, c)
    cfg = {'pdf': f'/books/m/{NO}/{SLUG}-reader.pdf?v={V}', 'key': f'books-m-{NO}-v1', 'offset': toc['offset']}
    tpl = re.sub(r'<script type="application/json" id="cfg">.*?</script>',
                 lambda m: '<script type="application/json" id="cfg">%s</script>' % json.dumps(cfg, ensure_ascii=False), tpl, flags=re.S)
    tpl = re.sub(r'<script type="application/json" id="toc">.*?</script>',
                 lambda m: '<script type="application/json" id="toc">%s</script>' % json.dumps(toc['toc'], ensure_ascii=False), tpl, flags=re.S)
    assert 'm/259' not in tpl and '谈尼采' not in tpl, [l[:200] for l in tpl.splitlines() if 'm/259' in l or '尼采' in l][:5]
    (d / 'read.html').write_text(tpl)
    # 书籍详情页
    import pymupdf
    pages = len(pymupdf.open(str(b / f'{SLUG}-print.pdf')))
    files = ['front/00-前置.md', 'front/01-导论.md'] + sorted(str(x.relative_to(HERE)) for x in (HERE / 'parts').glob('*.md')) + ['back/09-结语.md', 'back/10-后置.md']
    han = sum(len(re.findall(r'[一-鿿]', (HERE / f).read_text())) for f in files)
    det = (HERE / 'detail.html').read_text()
    det = det.replace('__V__', V).replace('__PAGES__', str(pages)).replace('__WAN__', '%.0f' % (han / 10000))
    assert '__' not in det.replace('__agentproxy', '')
    (d / 'index.html').write_text(det)
    # 书目：更新现有条目（页数、版本参数），不新增
    cat_p = SITE / 'books' / 'catalog.json'
    data = json.loads(cat_p.read_text())
    e = [x for x in data['books'] if str(x.get('number')) == str(NO)][0]
    for k in ('pdfUrl', 'printPdfUrl', 'coverUrl', 'backcoverUrl'):
        e[k] = re.sub(r'\?v=[0-9a-z]+', '?v=' + V, e[k])
    e['pdfPages'] = pages
    cat_p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    tp = SITE / 'today' / 'index.html'; h = tp.read_text()
    k = h.index('德麦国际专著第 %d 号 · 约' % NO)
    seg_end = h.index('</div>', k)
    seg = h[k:seg_end]
    seg2 = re.sub(r'(\d+) 页', '%d 页' % pages, seg, count=1)
    h = h[:k] + seg2 + h[seg_end:]
    seg_en = h.index('DEMAI MONOGRAPH No.%d' % NO)
    e2 = h.index('</div>', seg_en)
    s3 = re.sub(r'(\d+) PP', '%d PP' % pages, h[seg_en:e2], count=1)
    h = h[:seg_en] + s3 + h[e2:]
    tp.write_text(h)
    print('published to', d, 'pages', pages, 'han', han)


if __name__ == '__main__':
    main()
