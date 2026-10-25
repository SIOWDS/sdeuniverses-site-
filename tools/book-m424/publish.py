#!/usr/bin/env python3
"""第 424 号《三律医学入门——重构生命、健康与医学的意义结构》（王德生、秦莉著；SIO 阶段原稿修订版；由第 512 号 publish.py 改来）：
装进 public/books/m/424/（PDF、封面、全文网页、翻页器、详情页）、书目、站点地图、/today/ 新书卡。
用法（仓库根目录）：python3 tools/book-m424/publish.py --build /home/claude/bk424 --content tools/book-m424/content.json --ms tools/book-m424/book.md
"""
import argparse, datetime, json, re, shutil, subprocess
from pathlib import Path

HERE = Path(__file__).parent
SITE = HERE.resolve().parents[1] / 'public'
NO = 424
V = '20261025a'
SLUG = 'sanlv-yixue'
T, SUB = '三律医学入门', '重构生命、健康与医学的意义结构'
ISBN = '979-8-90690-029-6'
AUTHORS = ['王德生', '秦莉']


def pages_of(pdf):
    o = subprocess.run(['pdfinfo', str(pdf)], capture_output=True, text=True).stdout
    return int(re.search(r'Pages:\s+(\d+)', o).group(1))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--build', type=Path, required=True); ap.add_argument('--content', type=Path, required=True); ap.add_argument('--ms', required=True)
    A = ap.parse_args(); b = A.build; CT = json.loads(A.content.read_text()); AG = CT['agent']['name']
    d = SITE / 'books' / 'm' / str(NO)
    assert not d.exists(), f'{NO} 号目录已存在：{d}'
    _cat0 = json.loads((SITE / 'books' / 'catalog.json').read_text())['books']
    assert not any(str(x.get('number')) == str(NO) for x in _cat0), f'catalog 已有 {NO} 号'
    assert not any((x.get('isbn') or '').replace('-', '') == ISBN.replace('-', '') for x in _cat0), 'catalog 已有此 ISBN'
    _res = json.loads((SITE.parent / '.publish' / 'volume-reservations' / f'{NO}.json').read_text())
    assert _res['title'] == T and _res['isbnNormalized'] == ISBN.replace('-', ''), '预留档不是本书'
    (d / 'text').mkdir(parents=True, exist_ok=True)
    shutil.copy(b / f'{SLUG}-print.pdf', d / f'{SLUG}-print.pdf')
    shutil.copy(b / f'{SLUG}-reader.pdf', d / f'{SLUG}-reader.pdf')
    shutil.copy(b / 'cover.jpg', d / 'cover.jpg')
    shutil.copy(b / 'backcover.jpg', d / 'backcover.jpg')
    shutil.copy(b / 'text.html', d / 'text' / 'index.html')
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
    cfg = {'pdf': f'/books/m/{NO}/{SLUG}-reader.pdf?v={V}', 'key': f'books-m-{NO}-v1', 'offset': toc['offset']}
    tpl = re.sub(r'<script type="application/json" id="cfg">.*?</script>',
                 lambda m: '<script type="application/json" id="cfg">%s</script>' % json.dumps(cfg, ensure_ascii=False), tpl, flags=re.S)
    tpl = re.sub(r'<script type="application/json" id="toc">.*?</script>',
                 lambda m: '<script type="application/json" id="toc">%s</script>' % json.dumps(toc['toc'], ensure_ascii=False), tpl, flags=re.S)
    assert 'm/259' not in tpl and '谈尼采' not in tpl, [l[:200] for l in tpl.splitlines() if 'm/259' in l or '尼采' in l][:5]
    (d / 'read.html').write_text(tpl)
    pages = pages_of(b / f'{SLUG}-print.pdf')
    han = len(re.findall(r'[一-鿿]', Path(A.ms).read_text()))
    det = (HERE / 'detail.html').read_text()
    import html as _h
    cards = ''.join('<div class="card"><b>%s</b><span>%s</span></div>' % (_h.escape(c['t']), _h.escape(c['x'])) for c in CT['loadBearing'])
    det = (det.replace('__AGENT__', AG).replace('__V__', V).replace('__PAGES__', str(pages)).replace('__WAN__', '%.0f' % (han / 10000))
           .replace('__LINE__', _h.escape(CT['detailLine'])).replace('__INTRO__', _h.escape(CT['detailIntro'])).replace('__CARDS__', cards)
           .replace('__DESC_SHORT__', _h.escape(CT['detailLine'], quote=True)))
    assert '__' not in det.replace('__agentproxy', '')
    parts = []
    for f in sorted((HERE / 'parts').glob('*.md')):
        t = f.read_text()
        pt = re.search(r'^# (.+?)　(.+)$', t, re.M)
        chs = re.findall(r'^## 第 (\d+) 章　(.+)$', t, re.M)
        parts.append('<li><b>%s</b>　%s（第 %s—%s 章）<span class="chs">%s</span></li>' % (pt[1], _h.escape(pt[2]), chs[0][0], chs[-1][0], ' · '.join('第 %s 章 %s' % (a, _h.escape(b)) for a, b in chs)))
    det = det.replace('__PARTS__', '\n'.join(parts))
    assert '__' not in det.replace('__agentproxy', '')
    (d / 'index.html').write_text(det)
    cat_p = SITE / 'books' / 'catalog.json'
    data = json.loads(cat_p.read_text())
    books = data['books']
    assert not any(str(x.get('number')) == str(NO) for x in books), f'{NO} 号已被占用'
    assert not any((x.get('isbn') or '').replace('-', '') == ISBN.replace('-', '') for x in books), 'ISBN 重号'
    url = f'https://sdeuniverses.com/books/m/{NO}/'
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    entry = dict(id=f'm-{NO}', number=NO, title=T, subtitle=SUB, authors=AUTHORS, category='health',
                 description=CT['description'],
                 detailUrl=url, readUrl=url + 'read.html', readMode='full', readLabel='友好阅读 · 在线翻页',
                 pdfUrl=url + f'{SLUG}-reader.pdf?v={V}', printPdfUrl=url + f'{SLUG}-print.pdf?v={V}',
                 coverUrl=url + f'cover.jpg?v={V}', backcoverUrl=url + f'backcover.jpg?v={V}',
                 flipUrl=url + 'read.html', chapterUrl=url + 'text/', openness='full',
                 price='US$50.00', priceUsd=50, currency='USD', priceLabel='US$50.00', edition='2026年10月第1版（修订版）',
                 pdfPages=pages, publishedAt=now, publisher='德麦国际出版社', publisherEnglish='Demai International Press',
                 isbn=ISBN.replace('-', ''),
                 textUrl=url + 'text/', agentUrl=url + 'agent/', agentName=AG, agentLabel='智能问对 · ' + AG)
    books.insert(0, entry)
    data['updated'] = now[:10]
    cat_p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    sm = SITE / 'sitemap.xml'; t = sm.read_text()
    for u in [url, url + 'text/', url + 'read.html']:
        if '<loc>%s</loc>' % u not in t:
            assert '</urlset>' in t
            t = t.replace('</urlset>', '<url><loc>%s</loc><lastmod>%s</lastmod></url>\n</urlset>' % (u, now[:10]))
    sm.write_text(t)
    tp = SITE / 'today' / 'index.html'; h = tp.read_text()
    i = h.index('★ 新书 · 德麦国际专著第')
    a0 = h.rindex('<a href="/books/m/', 0, i)
    card = ('<a href="/books/m/%d/" style="display:block;text-decoration:none;margin-bottom:16px"><div style="border:1px solid rgba(217,180,92,0.85);border-radius:3px;background:linear-gradient(135deg,rgba(14,31,49,0.98),rgba(9,18,30,0.98));padding:34px 32px;box-shadow:0 0 0 1px rgba(217,180,92,0.16) inset,0 0 40px rgba(217,180,92,0.10)">'
            '<div class="zh-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ 新书 · 德麦国际专著第 %d 号 · 约 %.0f 万字 · %d 页 · US$50.00</div>'
            '<div class="en-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ NEW BOOK · DEMAI MONOGRAPH No.%d · ~%s CHARS · %d PP · US$50.00</div>'
            '<h3 class="zh-only" style="color:#F1EBDC;font-size:25px;line-height:1.5;margin:0 0 14px">三律医学入门——重构生命、健康与医学的意义结构</h3>'
            '<h3 class="en-only" style="color:#F1EBDC;font-size:23px;line-height:1.5;margin:0 0 14px">%s</h3>'
            '<p class="zh-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">%s</p>'
            '<p class="en-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">%s</p></div></a>'
            % (NO, NO, han / 10000, pages, NO, format(round(han, -3), ','), pages, CT['titleEn'], CT['todayZh'], CT['todayEn']))
    h = h[:a0] + card + h[a0:]
    tp.write_text(h)
    print('published to', d, 'pages', pages, 'han', han)


if __name__ == '__main__':
    main()
