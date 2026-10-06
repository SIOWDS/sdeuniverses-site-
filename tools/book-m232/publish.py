#!/usr/bin/env python3
"""把 build.py / cover.py 的产物装进 public/books/m/232/：PDF、封面、全文网页、翻页器、详情页、核心要点、智能体名字、
书目（顶替旧的 /books/redology/ 试读条目）、旧地址跳转、导读文章里的入口、站点地图、/today/ 新书卡。

用法：python3 publish.py --build <out>
（由第 340 号 tools/book-m340/publish.py 改来；2026-10-06 王德生令：卷号取站内空位＝232，试读改为全读。）
"""
import argparse
import datetime
import json
import re
import shutil
from pathlib import Path

HERE = Path(__file__).parent
SITE = HERE.resolve().parents[1] / 'public'
NO = 232
V = '20261006a'
SLUG = 'sde-redology'
T, SUB = 'SDE红学', '情悲发生学与空化解释学'
ISBN = '979-8-90690-683-0'
DESC = ('不问《红楼梦》“是什么”，而问它“如何自己发生”。前八十回是情悲发生学：创造、自由、幸福得一样便锁死另两样，情越真的人输得越尽；'
        '后四十回是空化解释学：把情与空不结算的张力从世俗与归空两头焊死。上篇三十七章讲原理、与八派红学交锋并作接续试焊，中篇细读十八个名场面，'
        '下篇把“情，不肯被空收编”带进教育、健康与商业。')
OLD = ('<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8"><title>SDE红学 · 已编为专著第 232 号</title>'
       '<link rel="canonical" href="https://sdeuniverses.com/books/m/232/%s"><meta http-equiv="refresh" content="0; url=/books/m/232/%s">'
       '<meta name="robots" content="noindex"></head><body><p>《SDE红学》已编为德麦国际专著第 232 号，全书公开，'
       '<a href="/books/m/232/%s">请到新地址阅读</a>。</p></body></html>\n')


def sub1(path, pairs):
    h = path.read_text()
    for a, c in pairs:
        assert a in h, (path, a[:40])
        h = h.replace(a, c)
    path.write_text(h)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--build', type=Path, required=True)
    b = ap.parse_args().build
    d = SITE / 'books' / 'm' / str(NO)
    assert not (d / 'index.html').exists(), f'{NO} 号目录已存在'
    (d / 'text').mkdir(parents=True, exist_ok=True)
    for f in [f'{SLUG}-print.pdf', f'{SLUG}-reader.pdf', 'cover.jpg', 'backcover.jpg']:
        shutil.copy(b / f, d / f)
    shutil.copy(b / 'text.html', d / 'text' / 'index.html')
    shutil.copy(HERE / 'keypoints.json', d / 'keypoints.json')
    # 翻页器：照第 259 号的矢量翻页器，只换书名、PDF 与目录
    import pymupdf
    tpl = (SITE / 'books' / 'm' / '259' / 'read.html').read_text()
    toc = json.loads((b / 'toc-reader.json').read_text())
    n = len(pymupdf.open(str(b / f'{SLUG}-reader.pdf')))
    toc['toc'] = [{'t': '封面', 'p': '', 'g': 1, 'l': 1}] + toc['toc'] + [{'t': '封底', 'p': '', 'g': n, 'l': 1}]
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
    assert 'm/259' not in tpl and '尼采' not in tpl, [l for l in tpl.splitlines() if 'm/259' in l or '尼采' in l][:3]
    (d / 'read.html').write_text(tpl)
    # 书籍详情页
    pages = len(pymupdf.open(str(b / f'{SLUG}-print.pdf')))
    han = len(re.findall(r'[一-鿿]', (HERE / 'manuscript.md').read_text()))
    det = (HERE / 'detail.html').read_text()
    det = det.replace('__V__', V).replace('__PAGES__', str(pages)).replace('__WAN__', '%.0f' % (han / 10000))
    assert '__' not in det
    (d / 'index.html').write_text(det)
    # 书目：查重后顶替旧的 redology 试读条目（同一本书只留一条）
    cat_p = SITE / 'books' / 'catalog.json'
    data = json.loads(cat_p.read_text())
    books = data['books']
    assert not any(str(x.get('number')) == str(NO) for x in books), f'{NO} 号已被占用'
    assert not any((x.get('isbn') or '').replace('-', '') == ISBN.replace('-', '') for x in books), 'ISBN 重号'
    old = [x for x in books if x.get('id') == 'redology']
    assert len(old) == 1
    books.remove(old[0])
    url = f'https://sdeuniverses.com/books/m/{NO}/'
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    entry = dict(id=f'm-{NO}', number=NO, title=T, subtitle=SUB, authors=['王德生'], category=old[0]['category'],
                 description=DESC, detailUrl=url, readUrl=url + 'read.html', readMode='full', readLabel='友好阅读 · 在线翻页',
                 pdfUrl=url + f'{SLUG}-reader.pdf?v={V}', printPdfUrl=url + f'{SLUG}-print.pdf?v={V}',
                 coverUrl=url + f'cover.jpg?v={V}', backcoverUrl=url + f'backcover.jpg?v={V}', isbn=ISBN.replace('-', ''),
                 flipUrl=url + 'read.html', chapterUrl=url + 'text/', openness='full',
                 price='US$20.00', priceUsd=20, currency='USD', priceLabel='US$20.00', edition='2026年10月第1版',
                 pdfPages=pages, publishedAt=now, publisher='德麦国际出版社', publisherEnglish='Demai International Press')
    books.insert(0, entry)
    data['updated'] = now[:10]
    cat_p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    # 智能体名字
    ag_p = SITE / 'books' / 'agents.json'
    ag = json.loads(ag_p.read_text())
    assert str(NO) not in ag['agents'] and not any(v.get('name') == '情根' for v in ag['agents'].values())
    ag['agents'][str(NO)] = {
        'name': '情根', 'epithet': '守在青埂峰下，看情怎样不肯被空收编',
        'intro': '我从《SDE红学》里来。带一个你放不下的红楼人物、一个读到落泪的场面，或者你对后四十回的一口不平气来：我陪你看那条命是怎样在那座宅子里一寸寸发生的，也陪你拆这本书自己最经不起追问的几处。',
        'starts': {'read': '为什么说“白茫茫大地真干净”是悲，不是解脱？“情与空对峙不解”到底指什么？',
                   'apply': '我是一名老师，班上有个像香菱那样“能学就是造化”的孩子，却被分数压着，用这本书怎么看？',
                   'cut': '“情越真，输越尽”这条脊梁，十二钗里哪一个最难贴上去？凤姐和迎春算不算反例？',
                   'clash': '把这本书和王国维《红楼梦评论》的“解脱”说、胡适的自传说撞一撞，真正的分歧落在哪一点？'}}
    ag_p.write_text(json.dumps(ag, ensure_ascii=False, indent=1) + '\n')
    # 旧地址跳转（导读页与试读翻页器都并入第 232 号）
    (SITE / 'books' / 'redology' / 'index.html').write_text(OLD % ('', '', ''))
    (SITE / 'books' / 'redology' / 'read.html').write_text(OLD % ('read.html', 'read.html', 'read.html'))
    # 导读文章里的入口：试读 → 全读
    pdf = f'/books/m/{NO}/{SLUG}-reader.pdf?v={V}'
    sub1(SITE / 'column' / 'redology-intro' / 'index.html', [
        ('（上·下篇合集，约16万字），王德生著，德麦国际出版社 2026 年 7 月第 1 版。试读版（288页）现已上线，可在线一页页阅读。',
         '（上·中·下篇全集，约 21 万字），王德生著，德麦国际专著第 232 号，2026 年 10 月第 1 版。全书已公开，可在线一页页阅读。'),
        ('href="/books/redology/read.html"', f'href="/books/m/{NO}/read.html"'),
        ('<a class="btn ghost" href="/books/redology/">专著导读页</a>', f'<a class="btn ghost" href="/books/m/{NO}/">专著详情页</a>'),
        ('<a class="btn ghost" href="/books/redology/SDE-Redology-Preview.pdf" target="_blank">下载试读版</a>',
         f'<a class="btn ghost" href="{pdf}" target="_blank">下载全书 PDF</a>'),
    ])
    sub1(SITE / 'column' / 'redology-twelve' / 'index.html', [
        ('288 页试读版开放一页页在线阅读。', '全书已公开（德麦国际专著第 232 号），可一页页在线阅读。'),
        ('href="/books/redology/read.html"', f'href="/books/m/{NO}/read.html"'),
        ('href="/books/redology/"', f'href="/books/m/{NO}/"'),
    ])
    sub1(SITE / 'column' / 'redology-daiyu' / 'index.html', [
        ('288 页试读版开放一页页在线阅读。', '全书已公开（德麦国际专著第 232 号），<a href="/books/m/%d/read.html">可一页页在线阅读</a>。' % NO)])
    for f in ['overview/index.html', 'books/m/45/index.html', 'sites/read/reviews/index.html']:
        sub1(SITE / f, [('href="/books/redology/"', f'href="/books/m/{NO}/"')])
    # 站点地图
    sm = SITE / 'sitemap.xml'; t = sm.read_text()
    t = re.sub(r'\s*<url>\s*<loc>https://sdeuniverses\.com/books/redology/[^<]*</loc>.*?</url>', '', t, flags=re.S)
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
            '<div class="zh-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ 新书 · 德麦国际专著第 %d 号 · 约 %.0f 万字 · %d 页 · US$ 20.00 · 全书公开</div>'
            '<div class="en-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ NEW BOOK · DEMAI MONOGRAPH No.%d · ~%s CHARS · %d PP · US$ 20.00 · FULL TEXT OPEN</div>'
            '<h3 class="zh-only" style="color:#F1EBDC;font-size:25px;line-height:1.5;margin:0 0 14px">SDE红学——情悲发生学与空化解释学</h3>'
            '<h3 class="en-only" style="color:#F1EBDC;font-size:23px;line-height:1.5;margin:0 0 14px">SDE Redology — How Feeling and Sorrow Come About, and How They Are Explained Away</h3>'
            '<p class="zh-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">王德生著，上·中·下篇全集。不问《红楼梦》“是什么”，而问它“如何自己发生”：前八十回是情悲发生学，创造、自由、幸福得一样便锁死另两样，情越真的人输得越尽；后四十回是空化解释学，把情与空不结算的张力从两头焊死。上篇三十七章，中篇细读十八个名场面，下篇把“情，不肯被空收编”带进教育、健康与商业。原 288 页试读版现改为全书公开。</p>'
            '<p class="en-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">By Wang Desheng; all three parts in one volume. It asks not what Dream of the Red Chamber “is” but how it comes about: the first eighty chapters let feeling and sorrow happen, while the last forty settle the account from both ends. Part One has 37 chapters, Part Two reads 18 famous scenes closely, Part Three carries the argument into education, health and business. The former 288-page preview is now the full book, open to read.</p></div></a>'
            % (NO, NO, han / 10000, pages, NO, format(han, ','), pages))
    h = h[:a0] + card + h[a0:]
    tp.write_text(h)
    print('published to', d, 'pages', pages, 'han', han)


if __name__ == '__main__':
    main()
