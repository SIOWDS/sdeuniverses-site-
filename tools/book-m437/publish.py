#!/usr/bin/env python3
"""第 437 号《被替代的从来不是人——论AI替代的虚幻》（王德生著；由第 527 号 publish.py 改来）：
装进 public/books/m/437/（PDF、封面、全文网页、翻页器、详情页）、书目、站点地图、/today/ 新书卡；
并写书号预留档 .publish/volume-reservations/437.json（铁律14：写之前查号、查 ISBN、验校验位）。
用法（仓库根目录）：python3 tools/book-m437/publish.py --build /home/claude/b437 --content tools/book-m437/content.json --ms tools/book-m437/book.md
"""
import argparse, datetime, glob, json, re, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa: E402
SITE = HERE.resolve().parents[1] / 'public'
NO, V, SLUG, T, SUB, ISBN, AUTHORS = M.NO, M.V, M.SLUG, M.TITLE, M.SUBTITLE, M.ISBN, M.AUTHORS
PRICE, PRICE_USD = M.PRICE, M.PRICE_USD


def check_digit_ok(isbn):
    d = re.sub(r'\D', '', isbn)
    s = sum(int(c) * (3 if i % 2 else 1) for i, c in enumerate(d[:12]))
    return len(d) == 13 and int(d[12]) == (10 - s % 10) % 10


def reserve(site_root, han, chapters):
    """铁律14：编号未占、ISBN 去连字符不与已有书相同、校验位对，才写预留档。"""
    rdir = site_root / '.publish' / 'volume-reservations'
    path = rdir / f'{NO}.json'
    nisbn = ISBN.replace('-', '')
    assert check_digit_ok(ISBN), 'ISBN 校验位不对'
    others = []
    for f in glob.glob(str(rdir / '*.json')):
        if Path(f).name == f'{NO}.json':
            continue
        d = json.loads(Path(f).read_text())
        others.append(d)
        assert str(d.get('volume') or d.get('number')) != str(NO), f'预留档 {f} 已占 {NO} 号'
        assert (d.get('isbnNormalized') or (d.get('isbn') or '')).replace('-', '') != nisbn, f'预留档 {f} 已用此 ISBN'
    if path.exists():
        d = json.loads(path.read_text())
        assert d['title'] == T and d['isbnNormalized'] == nisbn, '预留档不是本书'
        d.update(status='published', publishedAt=M.DATE, detailUrl=f'https://sdeuniverses.com/books/m/{NO}/',
                 manuscript={'chapters': chapters, 'bodyHanzi': han, 'state': '已上站'})
        path.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
        return d
    vols = [int(d.get('volume') or d.get('number')) for d in others if str(d.get('volume') or d.get('number') or '').isdigit()]
    pub = [int(x.name) for x in (site_root / 'public/books/m').iterdir() if x.name.isdigit()]
    d = {'volume': NO, 'title': T, 'subtitle': SUB, 'authors': AUTHORS, 'isbn': ISBN, 'isbnNormalized': nisbn,
         'isbnStatus': 'site-allocated-checksum-valid', 'priceUsd': PRICE_USD, 'status': 'published', 'date': M.DATE,
         'authorization': '用户（WDS博士）令：写一本专著批评和解构工具替代论，副题「论AI替代的虚幻」，大纲充分吸收站内相关专著，署名王德生；按出版流程三审，书号与 ISBN 从站上现算，定价 US$20.00（2026-10-29 用户定）；排版成 PDF、做三位一体再上站。',
         'availabilityCheck': {'maxPublishedDirectory': max(pub), 'maxReservedVolume': max(vols), 'volumeAbsent': True,
                               'isbnAbsentInCatalogAndReservations': True, 'checkDigit': int(nisbn[-1]),
                               'note': '437 号在最新 main 的书目、books/m 目录与预留档中均为空号，是 500 以内最小空号；979-8-90690 号段的 437 位已被第 199 号占用，照第 430、434、435 号先例取号段内最小空位 049，校验位 4；校验位检验不等于登记机关验证。'},
         'manuscript': {'chapters': chapters, 'bodyHanzi': han, 'state': '已上站'},
         'publishedAt': M.DATE, 'detailUrl': f'https://sdeuniverses.com/books/m/{NO}/'}
    path.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
    return d


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
    _ms = Path(A.ms).read_text()
    reserve(SITE.parent, len(re.findall(r'[一-鿿]', _ms)), len(re.findall(r'^## 第 ?\d+ ?章　', _ms, re.M)))
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
         f'<span class="ttl">{T}</span><span class="sub hideS">{M.EPIGRAPH}</span>'),
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
    han = len(re.findall(r'[一-鿿]', _ms))
    det = (HERE / 'detail.html').read_text()
    import html as _h
    cards = ''.join('<div class="card"><b>%s</b><span>%s</span></div>' % (_h.escape(c['t']), _h.escape(c['x'])) for c in CT['loadBearing'])
    det = (det.replace('__AGENT__', AG).replace('__V__', V).replace('__PAGES__', str(pages)).replace('__WAN__', '%.0f' % (han / 10000))
           .replace('__LINE__', _h.escape(CT['detailLine'])).replace('__INTRO__', _h.escape(CT['detailIntro'])).replace('__CARDS__', cards)
           .replace('__DESC_SHORT__', _h.escape(CT['detailLine'], quote=True)).replace('__PRICE_NUM__', '%.2f' % PRICE_USD).replace('__PRICE__', PRICE))
    def _struct():
        li = ['<li><b>前置</b>　出版信息 · 作者介绍 · 导论　%s</li>' % _h.escape((HERE / 'front/01-导论.md').read_text().split('\n', 1)[0].split('　', 1)[1])]
        for f in sorted((HERE / 'parts').glob('0*.md')):
            tx = f.read_text()
            pt = tx.split('\n', 1)[0].lstrip('# ').strip()
            chs = re.findall(r'^## (第(\d+)章)　(.*)$', tx, re.M)
            li.append('<li><b>%s</b>（第 %s—%s 章）<span class="chs">%s</span></li>' % (_h.escape(pt), chs[0][1], chs[-1][1], ' · '.join('%s %s' % (a, _h.escape(c)) for a, _, c in chs)))
        jy = (HERE / 'back/11-结语.md').read_text().split('\n', 1)[0].lstrip('# ').strip()
        li.append('<li><b>后置</b>　%s · 参考书目 · 后记</li>' % _h.escape(jy))
        return '<ol class="vols">\n%s\n</ol>' % '\n'.join(li)
    det = det.replace('__STRUCT__', _struct())
    assert '__' not in det.replace('__agentproxy', '')
    (d / 'index.html').write_text(det)
    cat_p = SITE / 'books' / 'catalog.json'
    data = json.loads(cat_p.read_text())
    books = data['books']
    assert not any(str(x.get('number')) == str(NO) for x in books), f'{NO} 号已被占用'
    assert not any((x.get('isbn') or '').replace('-', '') == ISBN.replace('-', '') for x in books), 'ISBN 重号'
    url = f'https://sdeuniverses.com/books/m/{NO}/'
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    entry = dict(id=f'm-{NO}', number=NO, title=T, subtitle=SUB, authors=AUTHORS, category=M.CATEGORY, titleEn=CT['titleEn'],
                 description=CT['description'],
                 detailUrl=url, readUrl=url + 'read.html', readMode='full', readLabel='友好阅读 · 在线翻页',
                 pdfUrl=url + f'{SLUG}-reader.pdf?v={V}', printPdfUrl=url + f'{SLUG}-print.pdf?v={V}',
                 coverUrl=url + f'cover.jpg?v={V}', backcoverUrl=url + f'backcover.jpg?v={V}',
                 flipUrl=url + 'read.html', chapterUrl=url + 'text/', openness='full',
                 price=PRICE, priceUsd=int(PRICE_USD) if PRICE_USD == int(PRICE_USD) else PRICE_USD, currency='USD', priceLabel=PRICE, edition=M.EDITION,
                 pdfPages=pages, publishedAt=now, publisher='德麦国际出版社', publisherEnglish='Demai International Press',
                 isbn=ISBN.replace('-', ''),
                 agentUrl=url + 'agent/dialogue.html', agentName=AG, agentLabel='智能问对 · ' + AG,
                 learnUrl=url + 'agent/learning.html', learningUrl=url + 'agent/learning.html', learnLabel='学习包 · %d个学习单元' % len(CT['tasks']),
                 learningPackUrl=url + f'downloads/{SLUG}-learning-v1.0.pdf',
                 publicationUnit={'id': f'm-{NO}', 'type': 'reading-learning-dialogue', 'revision': M.UNIT_REV})
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
            '<div class="zh-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ 新书 · 德麦国际专著第 %d 号 · 约 %.0f 万字 · %d 页 · __PRICE__</div>'
            '<div class="en-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ NEW BOOK · DEMAI MONOGRAPH No.%d · ~%s CHARS · %d PP · __PRICE__</div>'
            '<h3 class="zh-only" style="color:#F1EBDC;font-size:25px;line-height:1.5;margin:0 0 14px">__TITLE__</h3>'
            '<h3 class="en-only" style="color:#F1EBDC;font-size:23px;line-height:1.5;margin:0 0 14px">%s</h3>'
            '<p class="zh-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">%s</p>'
            '<p class="en-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">%s</p></div></a>'
            % (NO, NO, han / 10000, pages, NO, format(round(han, -3), ','), pages, CT['titleEn'], CT['todayZh'], CT['todayEn'])).replace('__PRICE__', PRICE).replace('__TITLE__', T)
    h = h[:a0] + card + h[a0:]
    tp.write_text(h)
    print('published to', d, 'pages', pages, 'han', han)


if __name__ == '__main__':
    main()
