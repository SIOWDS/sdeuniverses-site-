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
NO = 326
V = '20261012a'
SLUG = 'wo-yao-zhiqian'
T, SUB = '“我要”之前没有我：欲望发生学与弗洛伊德学派的解构', '欲望发生学专著'
ISBN = '979-8-90690-778-3'


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--build', type=Path, required=True)
    b = ap.parse_args().build
    d = SITE / 'books' / 'm' / str(NO)
    assert not (d / 'index.html').exists(), f'{NO} 号目录已存在'
    (d / 'text').mkdir(parents=True, exist_ok=True)
    for f in ['cover.jpg', 'backcover.jpg']:  # PDF 走 R2，不进 git
        shutil.copy(b / f, d / f)
    shutil.copy(b / 'text.html', d / 'text' / 'index.html')
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
    cfg = {'pdf': f'/students/wang-desheng/{SLUG}/m{NO}/{SLUG}-reader-v1.pdf', 'key': f'books-m-{NO}-v1', 'offset': toc['offset']}
    tpl = re.sub(r'<script type="application/json" id="cfg">.*?</script>',
                 lambda m: '<script type="application/json" id="cfg">%s</script>' % json.dumps(cfg, ensure_ascii=False), tpl, flags=re.S)
    tpl = re.sub(r'<script type="application/json" id="toc">.*?</script>',
                 lambda m: '<script type="application/json" id="toc">%s</script>' % json.dumps(toc['toc'], ensure_ascii=False), tpl, flags=re.S)
    assert 'm/259' not in tpl and '谈尼采' not in tpl, [l[:200] for l in tpl.splitlines() if 'm/259' in l or '尼采' in l][:5]
    (d / 'read.html').write_text(tpl)
    # 书籍详情页
    import pymupdf
    pages = len(pymupdf.open(str(b / f'{SLUG}-print.pdf')))
    files = sorted(str(x.relative_to(HERE)) for x in HERE.glob('front/*.md')) + sorted(str(x.relative_to(HERE)) for x in (HERE / 'parts').glob('*.md')) + sorted(str(x.relative_to(HERE)) for x in HERE.glob('back/*.md'))
    han = sum(len(re.findall(r'[一-鿿]', (HERE / f).read_text())) for f in files)
    det = (HERE / 'detail.html').read_text()
    det = det.replace('__V__', V).replace('__PAGES__', str(pages)).replace('__WAN__', '%.0f' % (han / 10000))
    assert '__' not in det.replace('__agentproxy', '')
    (d / 'index.html').write_text(det)
    # 书目：先查重（铁律 14）
    cat_p = SITE / 'books' / 'catalog.json'
    data = json.loads(cat_p.read_text())
    books = data['books']
    assert not any(str(x.get('number')) == str(NO) for x in books), f'{NO} 号已被占用'
    assert not ISBN or not any((x.get('isbn') or '').replace('-', '') == ISBN.replace('-', '') for x in books), 'ISBN 重号'
    url = f'https://sdeuniverses.com/books/m/{NO}/'
    R2 = f'https://sdeuniverses.com/students/wang-desheng/{SLUG}/m{NO}/'
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    entry = dict(id=f'm-{NO}', number=NO, title=T, subtitle=SUB, authors=['王德生'], category='core',
                 description='弗洛伊德学派看见了欲望的全部 D 现象（张力、压抑、改道、对象替代），却把它们安放在一个先在的主体上。欲望发生学把次序倒过来：幸福律的张力临界时，分布、场、美三号位侧重显影，回写出一个“我”。全书先立论，再逐家解构弗洛伊德、荣格、阿德勒、克莱因、赖希、拉康、弗洛姆、霍妮、马尔库塞，以德勒兹与加塔利为对照，最后落到怎样把一次“要”转换成一个会长大的“我”。七编三十章。',
                 detailUrl=url, readUrl=url + 'read.html', readMode='full', readLabel='友好阅读 · 在线翻页',
                 pdfUrl=R2 + f'{SLUG}-reader-v1.pdf?v={V}', readPdfUrl=R2 + f'{SLUG}-reader-v1.pdf?v={V}', printPdfUrl=R2 + f'{SLUG}-v1.0.pdf?v={V}',
                 coverUrl=url + f'cover.jpg?v={V}', backcoverUrl=url + f'backcover.jpg?v={V}',
                 flipUrl=url + 'read.html', chapterUrl=url + 'text/', openness='full',
                 price='US$20', priceUsd=20, currency='USD', priceLabel='US$20', edition='2026年10月第1版',
                 pdfPages=pages, publishedAt=now, publisher='德麦国际出版社', publisherEnglish='Demai International Press')
    if ISBN:
        entry['isbn'] = ISBN.replace('-', '')
    books.insert(0, entry)
    data['updated'] = now[:10]
    cat_p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    # 站点地图
    sm = SITE / 'sitemap.xml'; t = sm.read_text()
    for u in [url, url + 'text/', url + 'read.html']:
        if '<loc>%s</loc>' % u not in t:
            assert '</urlset>' in t
            t = t.replace('</urlset>', '<url><loc>%s</loc><lastmod>%s</lastmod></url>\n</urlset>' % (u, now[:10]))
    sm.write_text(t)
    # /today/ 新书卡：插在第一张「★ 新书」卡之前
    tp = SITE / 'today' / 'index.html'; h = tp.read_text()
    i = h.index('★ 新书 · 德麦国际专著第')
    a0 = h.rindex('<a href="/books/m/', 0, i)
    card = ('<a href="/books/m/%d/" style="display:block;text-decoration:none;margin-bottom:16px"><div style="border:1px solid rgba(217,180,92,0.85);border-radius:3px;background:linear-gradient(135deg,rgba(14,31,49,0.98),rgba(9,18,30,0.98));padding:34px 32px;box-shadow:0 0 0 1px rgba(217,180,92,0.16) inset,0 0 40px rgba(217,180,92,0.10)">'
            '<div class="zh-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ 新书 · 德麦国际专著第 %d 号 · 约 %.0f 万字 · %d 页 · US$ 20</div>'
            '<div class="en-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ NEW BOOK · DEMAI MONOGRAPH No.%d · ~%s CHARS · %d PP · US$ 20</div>'
            '<h3 class="zh-only" style="color:#F1EBDC;font-size:25px;line-height:1.5;margin:0 0 14px">“我要”之前没有我：欲望发生学与弗洛伊德学派的解构</h3>'
            '<h3 class="en-only" style="color:#F1EBDC;font-size:23px;line-height:1.5;margin:0 0 14px">Before “I Want”, There Is No I: The Genesis of Desire and a Deconstruction of the Freudian School</h3>'
            '<p class="zh-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">王德生著。小孩喊“我要冰淇淋”之前，并没有一个“要冰淇淋的他”在等着。欲望是张力临界时的一次发生，“我”是这次发生的产物。全书逐家解构弗洛伊德学派“主体发出欲望”的理论，落到怎样把一次“要”转换成一个会长大的“我”。</p>'
            '<p class="en-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">By Wang Desheng. Before a child cries “I want ice cream”, there is no one waiting to want it. Desire is an event at the threshold of tension, and the “I” is its product. The book takes apart the Freudian idea of a subject that emits desire.</p></div></a>'
            % (NO, NO, han / 10000, pages, NO, format(han, ','), pages))
    h = h[:a0] + card + h[a0:]
    tp.write_text(h)
    print('published to', d, 'pages', pages, 'han', han)


if __name__ == '__main__':
    main()
