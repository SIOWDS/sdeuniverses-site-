#!/usr/bin/env python3
"""第 474 号《AI时代的焦虑：主体性如何重生》（王德生 著；由第 553 号 publish.py 改来）：
装进 public/books/m/474/（两版 PDF、Word、封面封底、全文网页、矢量翻页器、详情页）、书目、站点地图、/today/ 新书卡；
并更新书号预留档 .publish/volume-reservations/474.json（该号已预留：在原档上更新，保留原有字段，不另起号；写之前查号、查 ISBN、验校验位）。
定价、书号、ISBN、版本一律取 meta.py（定价只改 meta.PRICE_USD 一处）。
翻页器用 tools/build_flip_reader.py one 生成。
可重跑：重跑时只替换本书自己的条目（catalog 里 m-474、/today/ 里本书那张卡、站点地图里本书几条），不碰别的书。
用法（仓库根目录）：python3 tools/book-m474/publish.py --build /tmp/b474 --content tools/book-m474/content.json --ms tools/book-m474/book.md
"""
import argparse, datetime, glob, json, re, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa: E402
REPO = HERE.resolve().parents[1]
SITE = REPO / 'public'
NO, V, SLUG, T, SUB, ISBN, AUTHORS = M.NO, M.V, M.SLUG, M.TITLE, M.SUBTITLE, M.ISBN, M.AUTHORS
PRICE, PRICE_USD = M.PRICE, M.PRICE_USD


def check_digit_ok(isbn):
    d = re.sub(r'\D', '', isbn)
    s = sum(int(c) * (3 if i % 2 else 1) for i, c in enumerate(d[:12]))
    return len(d) == 13 and int(d[12]) == (10 - s % 10) % 10


def reserve(han, chapters):
    rdir = REPO / '.publish' / 'volume-reservations'
    path = rdir / f'{NO}.json'
    prev = json.loads(path.read_text()) if path.exists() else {}
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
    vols = [int(d.get('volume') or d.get('number')) for d in others if str(d.get('volume') or d.get('number') or '').isdigit()]
    _cat = json.loads((SITE / 'books' / 'catalog.json').read_text())
    pub = [int(x['number']) for x in _cat['books'] if isinstance(x, dict) and isinstance(x.get('number'), int) and x['number'] != NO]   # 稀疏检出里目录不全，按书目算
    d = dict(prev)   # 第 474 号：在已有预留档上更新（保留 scale、原 authorization 等），不另起号
    d.update({'volume': NO, 'title': T, 'subtitle': SUB, 'authors': AUTHORS, 'isbn': ISBN, 'isbnNormalized': nisbn,
         'isbnStatus': 'site-allocated-checksum-valid', 'priceUsd': PRICE_USD, 'status': 'published', 'date': M.DATE,
         'reservationAuthorization': prev.get('authorization', ''),
         'authorization': '王德生出版令（2026-11-02）：排版按第 220、302 号版式，封面封底用已定稿（带定价 %s），三位一体（阅读、学习包、智能体）上站。《%s》为德麦国际专著第 %d 号，ISBN %s（校验位已核），定价 %s；副题“%s”；署名“王德生 著”。' % (PRICE, T, NO, ISBN, PRICE, SUB),
         'availabilityCheck': {'maxPublishedCatalogNumber': max(pub), 'maxReservedVolume': max(vols), 'volumeAbsent': True,
                               'isbnAbsentInCatalogAndReservations': True, 'checkDigit': int(nisbn[-1])},
         'tier': M.TIER,
         'manuscript': {'chapters': chapters, 'bodyHanzi': han, 'state': '已上站'},
         'publishedAt': M.DATE, 'detailUrl': f'https://sdeuniverses.com/books/m/{NO}/'})
    path.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
    return d


def pages_of(pdf):
    o = subprocess.run(['pdfinfo', str(pdf)], capture_output=True, text=True).stdout
    return int(re.search(r'Pages:\s+(\d+)', o).group(1))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--build', type=Path, required=True); ap.add_argument('--content', type=Path, required=True); ap.add_argument('--ms', required=True)
    A = ap.parse_args(); b = A.build; CT = json.loads(A.content.read_text()); AG = CT['agent']['name']
    d = SITE / 'books' / 'm' / str(NO)
    cat_p = SITE / 'books' / 'catalog.json'
    data = json.loads(cat_p.read_text())
    others = [x for x in data['books'] if x.get('id') != f'm-{NO}']
    # 铁律14：编号与 ISBN 查重（不算本书自己的旧条目）
    assert not any(str(x.get('number')) == str(NO) for x in others), f'catalog 已有 {NO} 号'
    assert not any((x.get('isbn') or '').replace('-', '') == ISBN.replace('-', '') for x in others), 'catalog 已有此 ISBN'
    _ms = Path(A.ms).read_text()
    # 第 474 号：对外“约 N 万字”按含标点字数（meta.wan，与出版信息页一致）；预留档另记正文汉字数
    han = M.body_han(HERE)
    wan = M.wan(HERE)
    reserve(han, len(re.findall(r'^## 第 ?\d+ ?章　', _ms, re.M)))
    (d / 'text').mkdir(parents=True, exist_ok=True)
    for f in (f'{SLUG}-print.pdf', f'{SLUG}-reader.pdf', f'{SLUG}.docx', 'cover.jpg', 'backcover.jpg'):
        shutil.copy(b / f, d / f)
    shutil.copy(b / 'text.html', d / 'text' / 'index.html')
    # 矢量翻页器（站内统一生成器）
    toc = json.loads((b / 'toc-reader.json').read_text())   # 只取 offset 与总页数
    subprocess.run([sys.executable, str(REPO / 'tools/build_flip_reader.py'), 'one', '--read', str(d / 'read.html'),
                    '--pdf', f'/books/m/{NO}/{SLUG}-reader.pdf?v={V}', '--title', T,
                    '--sub', f'{M.AUTHOR} 著 · 德麦国际专著第 {NO} 号',
                    '--detail', f'/books/m/{NO}/', '--offset', str(toc['offset']), '--key', f'books-m-{NO}-v1'], check=True)
    rd = (d / 'read.html').read_text()
    m_ = re.search(r'(<script type="application/json" id="toc">)(.*?)(</script>)', rd, flags=re.S)
    assert m_, 'flip reader has no toc json'
    tl = json.loads(m_[2].replace('<\\/', '</'))
    if not tl or tl[0].get('t') != '封面':
        tl.insert(0, {'t': '封面', 'p': '', 'g': 1, 'l': 1})
    if tl[-1].get('t') != '封底':
        tl.append({'t': '封底', 'p': '', 'g': pages_of(b / f'{SLUG}-reader.pdf'), 'l': 1})
    rd2 = rd[:m_.start(2)] + json.dumps(tl, ensure_ascii=False).replace('</', '<\\/') + rd[m_.end(2):]
    (d / 'read.html').write_text(rd2)
    pages = pages_of(b / f'{SLUG}-print.pdf')
    det = (HERE / 'detail.html').read_text()
    import html as _h
    cards = ''.join('<div class="card"><b>%s</b><span>%s</span></div>' % (_h.escape(c['t']), _h.escape(c['x'])) for c in CT['loadBearing'])
    ld = {'@context': 'https://schema.org', '@type': 'Book', 'name': T + '：' + SUB, 'alternateName': CT['titleEn'],
          'author': [{'@type': 'Person', 'name': a} for a in AUTHORS], 'isbn': ISBN.replace('-', ''), 'bookFormat': 'https://schema.org/EBook',
          'inLanguage': 'zh-CN', 'publisher': {'@type': 'Organization', 'name': '德麦国际出版社 Demai International Press'},
          'url': f'https://sdeuniverses.com/books/m/{NO}/', 'image': f'https://sdeuniverses.com/books/m/{NO}/cover.jpg?v={V}',
          'numberOfPages': str(pages), 'datePublished': M.DATE, 'offers': {'@type': 'Offer', 'price': '%.2f' % PRICE_USD, 'priceCurrency': 'USD'}}
    rep = {'__LDJSON__': json.dumps(ld, ensure_ascii=False).replace('</', '<\\/'), '__AGENT__': _h.escape(AG), '__V__': V, '__PAGES__': str(pages),
           '__WAN__': str(wan), '__LINE__': _h.escape(CT['detailLine']), '__INTRO__': _h.escape(CT['detailIntro']), '__CARDS__': cards,
           '__NLB__': {18: '十八', 8: '八'}.get(len(CT['loadBearing']), str(len(CT['loadBearing']))),
           '__DESC_SHORT__': _h.escape(CT['detailLine'], quote=True), '__PRICE__': PRICE, '__TITLE__': _h.escape(T), '__SUB__': _h.escape(SUB),
           '__NO__': str(NO), '__ISBN__': ISBN, '__AUTHOR__': M.AUTHOR, '__AUTHORSHIP__': _h.escape(M.AUTHORSHIP), '__EDITION__': M.EDITION_SP,
           '__VERDICT__': _h.escape(M.VERDICT), '__SLUG__': SLUG, '__UNITS__': str(len(CT['tasks']))}
    for k_, v_ in rep.items():
        det = det.replace(k_, v_)

    def _struct():
        li = ['<li><b>前置</b>　出版信息 · 题词 · 作者介绍 · 前言 · 导读 · 导论</li>']
        for f in sorted((HERE / 'parts').glob('*.md')):
            tx = f.read_text()
            pt = tx.split('\n', 1)[0].lstrip('# ').strip()
            chs = re.findall(r'^## 第 ?(\d+) ?章　(.*)$', tx, re.M)
            li.append('<li><b>%s</b>（第 %s—%s 章）<span class="chs">%s</span></li>' % (
                _h.escape(pt), chs[0][0], chs[-1][0], ' · '.join('第%s章 %s' % (n, _h.escape(c)) for n, c in chs)))
        li.append('<li><b>后置</b>　结语 · 附录一至五 · 参考书目 · 后记</li>')
        return '<ol class="vols">\n%s\n</ol>' % '\n'.join(li)
    det = det.replace('__STRUCT__', _struct())
    assert not re.search(r'__[A-Z_]+__', det), re.findall(r'__[A-Z_]+__', det)
    (d / 'index.html').write_text(det)
    url = f'https://sdeuniverses.com/books/m/{NO}/'
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    old = next((x for x in data['books'] if x.get('id') == f'm-{NO}'), None)
    pubat = old['publishedAt'] if old else now
    entry = dict(id=f'm-{NO}', number=NO, title=T, subtitle=SUB, authors=AUTHORS, category=M.CATEGORY, titleEn=CT['titleEn'],
                 description=CT['description'],
                 detailUrl=url, readUrl=url + 'read.html', readMode='full', readLabel='友好阅读 · 在线翻页',
                 pdfUrl=url + f'{SLUG}-reader.pdf?v={V}', printPdfUrl=url + f'{SLUG}-print.pdf?v={V}', docxUrl=url + f'{SLUG}.docx?v={V}',
                 coverUrl=url + f'cover.jpg?v={V}', backcoverUrl=url + f'backcover.jpg?v={V}',
                 flipUrl=url + 'read.html', chapterUrl=url + 'text/', openness='full',
                 price=PRICE, priceUsd=int(PRICE_USD) if PRICE_USD == int(PRICE_USD) else PRICE_USD, currency='USD', priceLabel=PRICE, edition=M.EDITION,
                 pdfPages=pages_of(b / f'{SLUG}-reader.pdf'), printPdfPages=pages, publishedAt=pubat, publisher='德麦国际出版社', publisherEnglish='Demai International Press',
                 isbn=ISBN.replace('-', ''), isbnDisplay=ISBN, isbnStatus='site-allocated-checksum-valid',
                 agentUrl=url + 'agent/dialogue.html', agentName=AG, agentLabel='智能问对 · ' + AG,
                 learnUrl=url + 'agent/learning.html', learningUrl=url + 'agent/learning.html', learnLabel='学习包 · %d个学习单元' % len(CT['tasks']),
                 learningPackUrl=url + f'learning-pack.pdf?v={V}', learningPackDocxUrl=url + f'learning-pack.docx?v={V}',
                 tier=M.TIER['tier'], citeOk=True,
                 publicationUnit={'id': f'm-{NO}', 'type': 'reading-learning-dialogue', 'revision': M.UNIT_REV})
    data['books'] = [entry] + others
    data['updated'] = now[:10]
    cat_p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    sm = SITE / 'sitemap.xml'; t = sm.read_text()
    for u in [url, url + 'text/', url + 'read.html', url + 'agent/', url + 'agent/learning.html', url + 'agent/dialogue.html']:
        if '<loc>%s</loc>' % u not in t:
            assert '</urlset>' in t
            t = t.replace('</urlset>', '<url><loc>%s</loc><lastmod>%s</lastmod></url>\n</urlset>' % (u, now[:10]))
    sm.write_text(t)
    tp = SITE / 'today' / 'index.html'; h = tp.read_text()
    S0, E0 = '<!-- M%d_TODAY_START -->' % NO, '<!-- M%d_TODAY_END -->' % NO
    h = re.sub(re.escape(S0) + '.*?' + re.escape(E0), '', h, flags=re.S)
    i = h.index('★ 新书 · 德麦国际专著第')
    a0 = h.rindex('<a href="/books/m/', 0, i)
    card = S0 + ('<a href="/books/m/%d/" style="display:block;text-decoration:none;margin-bottom:16px"><div style="border:1px solid rgba(217,180,92,0.85);border-radius:3px;background:linear-gradient(135deg,rgba(14,31,49,0.98),rgba(9,18,30,0.98));padding:34px 32px;box-shadow:0 0 0 1px rgba(217,180,92,0.16) inset,0 0 40px rgba(217,180,92,0.10)">'
            '<div class="zh-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ 新书 · 德麦国际专著第 %d 号 · 约 %d 万字 · %d 页 · __PRICE__</div>'
            '<div class="en-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ NEW BOOK · DEMAI MONOGRAPH No.%d · ~%s CHARS · %d PP · __PRICE__</div>'
            '<h3 class="zh-only" style="color:#F1EBDC;font-size:25px;line-height:1.5;margin:0 0 14px">__TITLE__</h3>'
            '<h3 class="en-only" style="color:#F1EBDC;font-size:23px;line-height:1.5;margin:0 0 14px">%s</h3>'
            '<p class="zh-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">%s</p>'
            '<p class="en-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">%s</p></div></a>'
            % (NO, NO, wan, pages, NO, format(wan * 10000, ','), pages, CT['titleEn'], CT['todayZh'], CT['todayEn'])).replace('__PRICE__', PRICE).replace('__TITLE__', '%s：%s' % (T, SUB)) + E0
    h = h[:a0] + card + h[a0:]
    tp.write_text(h)
    print('published to', d, 'pages', pages, 'han', han)


if __name__ == '__main__':
    main()
