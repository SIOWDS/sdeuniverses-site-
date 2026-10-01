#!/usr/bin/env python3
"""把 build.py / cover.py 的产物装进 public/books/m/263/：PDF、封面、全文网页、翻页器。

用法：python3 publish.py --build /tmp/edu-build
"""
import argparse
import json
import re
import shutil
from pathlib import Path

SITE = Path(__file__).resolve().parents[2] / 'public'
NO = 263
V = '20261001c'
T, SUB = '教育的新使命', '从「一个人全包」到「人与 AI 分层分工」'


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--build', type=Path, required=True)
    b = ap.parse_args().build
    d = SITE / 'books' / 'm' / str(NO)
    (d / 'text').mkdir(parents=True, exist_ok=True)
    for f in ['education-print.pdf', 'education-reader.pdf', 'cover.jpg', 'backcover.jpg']:
        shutil.copy(b / f, d / f)
    shutil.copy(b / 'text.html', d / 'text' / 'index.html')
    # 翻页器：照第 259 号的矢量翻页器，只换书名、PDF 与目录
    tpl = (SITE / 'books' / 'm' / '259' / 'read.html').read_text()
    toc = json.loads((b / 'toc-reader.json').read_text())
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
    cfg = {'pdf': f'/books/m/{NO}/education-reader.pdf?v={V}', 'key': f'books-m-{NO}-v1', 'offset': toc['offset']}
    tpl = re.sub(r'<script type="application/json" id="cfg">.*?</script>',
                 '<script type="application/json" id="cfg">%s</script>' % json.dumps(cfg, ensure_ascii=False), tpl, flags=re.S)
    tpl = re.sub(r'<script type="application/json" id="toc">.*?</script>',
                 lambda m: '<script type="application/json" id="toc">%s</script>' % json.dumps(toc['toc'], ensure_ascii=False), tpl, flags=re.S)
    assert '259' not in tpl.replace('#259', ''), [l for l in tpl.splitlines() if '259' in l][:3]
    (d / 'read.html').write_text(tpl)
    # 书籍详情页
    import pymupdf
    pages = len(pymupdf.open(str(b / 'education-print.pdf')))
    han = sum(len(re.findall(r'[一-鿿]', (Path(__file__).parent / f).read_text()))
              for f in ['front/00-前置.md'] + sorted(str(x.relative_to(Path(__file__).parent)) for x in (Path(__file__).parent / 'parts').glob('*.md'))
              + ['back/09-结语.md', 'back/10-后置.md'])
    shutil.copy(b / 'cover.jpg', d / 'cover.jpg'); shutil.copy(b / 'backcover.jpg', d / 'backcover.jpg')
    det = (Path(__file__).parent / 'detail.html').read_text()
    det = det.replace('__V__', V).replace('__PAGES__', str(pages)).replace('__WAN__', '%.0f' % (han / 10000))
    assert '__' not in det.replace('__agentproxy', '')
    (d / 'index.html').write_text(det)
    # 书目
    cat_p = SITE / 'books' / 'catalog.json'
    data = json.loads(cat_p.read_text())
    books = data['books']
    assert not any(x.get('number') == NO and x['id'] != f'm-{NO}' for x in books), '263 号已被别的书占用'
    old = next((x for x in books if x['id'] == f'm-{NO}'), None)
    url = f'https://sdeuniverses.com/books/m/{NO}/'
    entry = dict(id=f'm-{NO}', number=NO, title=T, authors=['王德生', '付自文', '胡志英', '李佳城'], category='edu',
                 description=SUB + '——机器都会了，学校还教什么？车来了，腿退出走路，人进入交通那一层；机器接管「想」的下面那一层，人往上走一层。讲学生—AI 复合思维体、思维颗粒度、合成与元判断，讲判断也分两层、链条停在定标准与担后果，再落到课堂、考试与老师。七篇加尾篇五十二章。',
                 detailUrl=url, readUrl=url + 'read.html', readMode='full', readLabel='友好阅读 · 在线翻页',
                 pdfUrl=url + f'education-print.pdf?v={V}', coverUrl=url + f'cover.jpg?v={V}', isbn='9798906902481',
                 publishedAt=old['publishedAt'] if old else __import__('datetime').datetime.now(__import__('datetime').timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                 flipUrl=url + 'read.html', chapterUrl=url + 'text/', openness='full')
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
            t = t.replace('</urlset>', '<url><loc>%s</loc><lastmod>2026-10-01</lastmod></url>\n</urlset>' % u)
    sm.write_text(t)
    print('published to', d, 'pages', pages, 'han', han)


if __name__ == '__main__':
    main()
