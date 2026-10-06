#!/usr/bin/env python3
"""把 build.py / cover.py 的产物装进 public/books/m/4/：PDF、封面、全文网页、翻页器。

用法：python3 publish.py --build /tmp/edu-build
"""
import argparse
import json
import re
import shutil
from pathlib import Path

SITE = Path(__file__).resolve().parents[2] / 'public'
NO = 4
V = '20261006a'
T, SUB = 'SDE发生学', '结构、差异与特征纠缠的本体论革命'


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--build', type=Path, required=True)
    b = ap.parse_args().build
    d = SITE / 'books' / 'm' / str(NO)
    (d / 'text').mkdir(parents=True, exist_ok=True)
    for f in ['sde-genealogics-print.pdf', 'sde-genealogics.pdf', 'cover.jpg', 'backcover.jpg']:
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
    cfg = {'pdf': f'/books/m/{NO}/sde-genealogics.pdf?v={V}', 'key': f'books-m-{NO}-v1', 'offset': toc['offset']}
    tpl = re.sub(r'<script type="application/json" id="cfg">.*?</script>',
                 '<script type="application/json" id="cfg">%s</script>' % json.dumps(cfg, ensure_ascii=False), tpl, flags=re.S)
    tpl = re.sub(r'<script type="application/json" id="toc">.*?</script>',
                 lambda m: '<script type="application/json" id="toc">%s</script>' % json.dumps(toc['toc'], ensure_ascii=False), tpl, flags=re.S)
    assert '/18/' not in tpl and '中国教育改革' not in tpl and 'zhongguo' not in tpl
    (d / 'read.html').write_text(tpl)
    # 书籍详情页
    import pymupdf
    pages = len(pymupdf.open(str(b / 'sde-genealogics-print.pdf')))
    han = sum(len(re.findall(r'[一-鿿]', (Path(__file__).parent / f).read_text()))
              for f in ['front/00-前置.md'] + sorted(str(x.relative_to(Path(__file__).parent)) for x in (Path(__file__).parent / 'parts').glob('*.md'))
              + ['back/01-结语.md', 'back/10-附录.md'])
    shutil.copy(b / 'cover.jpg', d / 'cover.jpg'); shutil.copy(b / 'backcover.jpg', d / 'backcover.jpg')
    det = (Path(__file__).parent / 'detail.html').read_text()
    from front import part_stats, CNP
    vols = ''.join('<li><b>第%s篇</b>　%s%s</li>' % (CNP[x['k']], x['title'], '（%d 章）' % x['ch'] if x['ch'] else '（六节）') for x in part_stats())
    det = det.replace('__VOLS__', vols).replace('__V__', V).replace('__PAGES__', str(pages)).replace('__WAN__', '%.0f' % (han / 10000))
    assert '__' not in det.replace('__agentproxy', '')
    (d / 'index.html').write_text(det)
    # 书目
    cat_p = SITE / 'books' / 'catalog.json'
    data = json.loads(cat_p.read_text())
    books = data['books']
    old = next((x for x in books if x['id'] == f'm-{NO}'), None)
    url = f'https://sdeuniverses.com/books/m/{NO}/'
    entry = dict(old or {})
    entry.update(dict(id=f'm-{NO}', number=NO, title=T, subtitle=SUB, authors=['王德生'], category='core',
                 description='稳定不是起点，而是差异洪流与特征纠缠共同压出的阶段性成果。十篇文章合成一部专著：先讲 SDE 发生学为什么必然出现，再立底盘、写引擎、给出回写的闭环，最后把同一台发动机用到思想创新、欲望、抑郁、无为与慢性病上。十篇五十九章，约 %d 万字。' % round(han / 10000),
                 detailUrl=url, readUrl=url + 'read.html', readMode='full', readLabel='友好阅读 · 在线翻页',
                 pdfUrl=url + f'sde-genealogics.pdf?v={V}', printPdfUrl=url + f'sde-genealogics-print.pdf?v={V}',
                 coverUrl=url + f'cover.jpg?v={V}', backcoverUrl=url + f'backcover.jpg?v={V}', isbn='9781970820317',
                 flipUrl=url + 'read.html', chapterUrl=url + 'text/', openness='full', price='待填', currency='USD',
                 priceLabel='待填', edition='2026年1月成稿 · 2026年10月统稿上线版', pdfPages=pages,
                 publisher='德麦国际出版社', publisherEnglish='Demai International Press'))
    entry.pop('priceUsd', None)
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
