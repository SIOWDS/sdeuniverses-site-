#!/usr/bin/env python3
"""把 build.py / cover.py 的产物装进 public/books/m/236/：PDF、封面、全文网页、翻页器。

用法：python3 publish.py --build /tmp/edu-build
"""
import argparse
import json
import re
import shutil
from pathlib import Path

SITE = Path(__file__).resolve().parents[2] / 'public'
NO = 238
V = '20261006a'
T, SUB = '特征律', '西方哲学解构的屠龙刀'


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--build', type=Path, required=True)
    b = ap.parse_args().build
    d = SITE / 'books' / 'm' / str(NO)
    (d / 'text').mkdir(parents=True, exist_ok=True)
    for f in ['te-zheng-lv-print.pdf', 'te-zheng-lv.pdf', 'cover.jpg', 'backcover.jpg']:
        shutil.copy(b / f, d / f)
    shutil.copy(b / 'text.html', d / 'text' / 'index.html')
    # 翻页器：照第 18 号的矢量翻页器，只换书名、PDF 与目录
    tpl = (SITE / 'books' / 'm' / '18' / 'read.html').read_text()
    toc = json.loads((b / 'toc-reader.json').read_text())
    rep = [
        ('友好阅读 · 在线翻页 · 基于GPT的中国教育改革 | SDE Universes', f'友好阅读 · 在线翻页 · {T} | SDE Universes'),
        ('《基于GPT的中国教育改革》在线翻页阅读', f'《{T}》在线翻页阅读'),
        ('https://sdeuniverses.com/books/m/18/read.html', f'https://sdeuniverses.com/books/m/{NO}/read.html'),
        ('<span class="ttl">基于GPT的中国教育改革</span><span class="sub hideS">新时代、新课堂、新未来</span>',
         f'<span class="ttl">{T}</span><span class="sub hideS">{SUB}</span>'),
        ('<a href="/books/m/18/"', f'<a href="/books/m/{NO}/"'),
        ("title: '基于GPT的中国教育改革',", f"title: '{T}',"),
        ("msg('正在载入《基于GPT的中国教育改革》…');", f"msg('正在载入《{T}》…');"),
    ]
    for a, c in rep:
        assert a in tpl, a[:50]
        tpl = tpl.replace(a, c)
    cfg = {'pdf': f'/books/m/{NO}/te-zheng-lv.pdf?v={V}', 'key': f'books-m-{NO}-v1', 'offset': toc['offset']}
    tpl = re.sub(r'<script type="application/json" id="cfg">.*?</script>',
                 '<script type="application/json" id="cfg">%s</script>' % json.dumps(cfg, ensure_ascii=False), tpl, flags=re.S)
    tpl = re.sub(r'<script type="application/json" id="toc">.*?</script>',
                 lambda m: '<script type="application/json" id="toc">%s</script>' % json.dumps(toc['toc'], ensure_ascii=False), tpl, flags=re.S)
    assert '/18/' not in tpl and '中国教育改革' not in tpl and 'zhongguo' not in tpl
    (d / 'read.html').write_text(tpl)
    # 书籍详情页
    import pymupdf
    pages = len(pymupdf.open(str(b / 'te-zheng-lv-print.pdf')))
    han = sum(len(re.findall(r'[一-鿿]', (Path(__file__).parent / f).read_text()))
              for f in ['front/00-前置.md'] + sorted(str(x.relative_to(Path(__file__).parent)) for x in (Path(__file__).parent / 'parts').glob('*.md'))
              + ['back/01-全书结论.md', 'back/02-结尾宣言.md', 'back/10-附录.md'])
    shutil.copy(b / 'cover.jpg', d / 'cover.jpg'); shutil.copy(b / 'backcover.jpg', d / 'backcover.jpg')
    det = (Path(__file__).parent / 'detail.html').read_text()
    det = det.replace('__V__', V).replace('__PAGES__', str(pages)).replace('__WAN__', '%.0f' % (han / 10000))
    assert '__' not in det.replace('__agentproxy', '')
    (d / 'index.html').write_text(det)
    # 书目
    cat_p = SITE / 'books' / 'catalog.json'
    data = json.loads(cat_p.read_text())
    books = data['books']
    assert not any(x.get('number') == NO and x['id'] != f'm-{NO}' for x in books), '238 号已被别的书占用'
    old = next((x for x in books if x['id'] == f'm-{NO}'), None)
    url = f'https://sdeuniverses.com/books/m/{NO}/'
    entry = dict(id=f'm-{NO}', number=NO, title=T, subtitle=SUB, authors=['王德生'], category='core',
                 description='特征不是发现的，而是发生的。本书以特征律为刀，解构从古希腊到后现代的西方哲学：差异存在、差异稳定、复杂性机制三个条件齐备，意识同一性必然生成。六篇论文依次拆亚里士多德、康德、黑格尔、尼采，并给出解剖西方哲学家的方法。六篇八十九章，约 18 万字。',
                 detailUrl=url, readUrl=url + 'read.html', readMode='full', readLabel='友好阅读 · 在线翻页',
                 pdfUrl=url + f'te-zheng-lv.pdf?v={V}', printPdfUrl=url + f'te-zheng-lv-print.pdf?v={V}',
                 coverUrl=url + f'cover.jpg?v={V}', backcoverUrl=url + f'backcover.jpg?v={V}', isbn='9798906906649',
                 publishedAt=old['publishedAt'] if old else __import__('datetime').datetime.now(__import__('datetime').timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                 flipUrl=url + 'read.html', chapterUrl=url + 'text/', openness='full', price='US$25.00', priceUsd=25, currency='USD',
                 priceLabel='US$25.00', edition='2025年8月成稿 · 2026年10月统稿上线版', pdfPages=pages,
                 publisher='德麦国际出版社', publisherEnglish='Demai International Press')
    if old:
        books[books.index(old)] = entry
    else:
        books.insert(0, entry)
    cat_p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    # 站点地图：三条网址直接加进 sitemap.xml
    locs = [url, url + 'text/', url + 'read.html']
    sm = SITE / 'sitemap.xml'; t = sm.read_text()
    for u in locs:
        if '<loc>%s</loc>' % u not in t:
            assert '</urlset>' in t
            t = t.replace('</urlset>', '<url><loc>%s</loc><lastmod>2026-10-06</lastmod></url>\n</urlset>' % u)
    sm.write_text(t)
    print('published to', d, 'pages', pages, 'han', han)


if __name__ == '__main__':
    main()
