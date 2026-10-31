#!/usr/bin/env python3
"""第 536 号《AI时代普通人的知识发生机会》（王德生 著；由第 532 号 publish.py 改来）：
装进 public/books/m/536/（两版 PDF、Word、封面封底、全文网页、矢量翻页器、详情页）、书目、站点地图、/today/ 新书卡；
并写书号预留档 .publish/volume-reservations/536.json（铁律14：写之前查号、查 ISBN、验校验位）。
翻页器用 tools/build_flip_reader.py one 生成（不再改写第 259 号的旧模板）。
可重跑：重跑时只替换本书自己的条目（catalog 里 m-536、/today/ 里本书那张卡），不碰别的书。
用法（仓库根目录）：python3 tools/book-m536/publish.py --build <b536> --content tools/book-m536/content.json --ms tools/book-m536/book.md
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
    d = {'volume': NO, 'title': T, 'subtitle': SUB, 'authors': AUTHORS, 'isbn': ISBN, 'isbnNormalized': nisbn,
         'isbnStatus': 'site-allocated-checksum-valid', 'priceUsd': PRICE_USD, 'status': 'published', 'date': M.DATE,
         'authorization': '主编令（2026-10-31）：《AI时代普通人的知识发生机会》ISBN 与卷号从站里计算空位，定价 US$20；统稿三审后按第 220、302 号风格排版，做成三位一体出版单元（阅读、学习包、智能体）上站。书目：王德生 著，ISBN 979-8-90690-536-9，US$20.00，2026 年 11 月第 1 版。',
         'availabilityCheck': {'maxPublishedCatalogNumber': max(pub), 'maxReservedVolume': max(vols), 'volumeAbsent': True,
                               'isbnAbsentInCatalogAndReservations': True, 'checkDigit': int(nisbn[-1])},
         'tier': M.TIER,
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
    cat_p = SITE / 'books' / 'catalog.json'
    data = json.loads(cat_p.read_text())
    others = [x for x in data['books'] if x.get('id') != f'm-{NO}']
    # 铁律14：编号与 ISBN 查重（不算本书自己的旧条目）
    assert not any(str(x.get('number')) == str(NO) for x in others), f'catalog 已有 {NO} 号'
    assert not any((x.get('isbn') or '').replace('-', '') == ISBN.replace('-', '') for x in others), 'catalog 已有此 ISBN'
    _ms = Path(A.ms).read_text()
    # 第 536 号：字数按九十六章正文（剔除标题行）计，与封面、出版信息页口径一致
    han = sum(len(re.findall(r'[一-鿿]', '\n'.join(l for l in (HERE / 'parts' / f).read_text().split('\n## ', 1)[1].split('\n') if not l.lstrip().startswith('#')))) for f in sorted(x.name for x in (HERE / 'parts').glob('*.md')))
    reserve(han, len(re.findall(r'^## 第 ?\d+ ?章　', _ms, re.M)))
    (d / 'text').mkdir(parents=True, exist_ok=True)
    for f in (f'{SLUG}-print.pdf', f'{SLUG}-reader.pdf', f'{SLUG}.docx', 'cover.jpg', 'backcover.jpg'):
        shutil.copy(b / f, d / f)
    shutil.copy(b / 'text.html', d / 'text' / 'index.html')
    # 矢量翻页器（站内统一生成器）
    toc = json.loads((b / 'toc-reader.json').read_text())
    subprocess.run([sys.executable, str(REPO / 'tools/build_flip_reader.py'), 'one', '--read', str(d / 'read.html'),
                    '--pdf', f'/books/m/{NO}/{SLUG}-reader.pdf?v={V}', '--title', T,
                    '--sub', f'{M.AUTHOR} 著 · 德麦国际专著第 {NO} 号',
                    '--detail', f'/books/m/{NO}/', '--offset', str(toc['offset']), '--key', f'books-m-{NO}-v1'], check=True)
    rd = (d / 'read.html').read_text()
    # 目录用排版时记下的书签（含正文页码），比从 PDF 书签反推更准
    rd2 = re.sub(r'(<script type="application/json" id="toc">).*?(</script>)',
                 lambda m: m[1] + json.dumps(toc['toc'], ensure_ascii=False).replace('</', '<\\/') + m[2], rd, count=1, flags=re.S)
    if rd2 != rd:
        (d / 'read.html').write_text(rd2)
    pages = pages_of(b / f'{SLUG}-print.pdf')
    det = (HERE / 'detail.html').read_text()
    import html as _h
    cards = ''.join('<div class="card"><b>%s</b><span>%s</span></div>' % (_h.escape(c['t']), _h.escape(c['x'])) for c in CT['loadBearing'])
    det = (det.replace('__AGENT__', AG).replace('__V__', V).replace('__PAGES__', str(pages)).replace('__WAN__', '%.0f' % (han / 10000))
           .replace('__LINE__', _h.escape(CT['detailLine'])).replace('__INTRO__', _h.escape(CT['detailIntro'])).replace('__CARDS__', cards)
           .replace('__DESC_SHORT__', _h.escape(CT['detailLine'], quote=True)).replace('__PRICE_NUM__', '%.2f' % PRICE_USD).replace('__PRICE__', PRICE))

    def _struct():
        li = ['<li><b>前置</b>　出版信息 · 题词 · 作者介绍 · 本版说明 · 导论</li>']
        for f in sorted((HERE / 'parts').glob('*.md')):
            tx = f.read_text()
            pt = tx.split('\n', 1)[0].lstrip('# ').strip()
            chs = re.findall(r'^## 第(\d+)章　(.*)$', tx, re.M)
            li.append('<li><b>%s</b>（第 %s—%s 章）<span class="chs">%s</span></li>' % (
                _h.escape(pt), chs[0][0], chs[-1][0], ' · '.join('第%s章 %s' % (n, _h.escape(c)) for n, c in chs)))
        li.append('<li><b>后置</b>　参考书目（R01–R47）· 版本说明</li>')
        return '<ol class="vols">\n%s\n</ol>' % '\n'.join(li)
    det = det.replace('__STRUCT__', _struct())
    assert '__' not in det
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
            '<div class="zh-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ 新书 · 德麦国际专著第 %d 号 · 约 %.0f 万字 · %d 页 · __PRICE__</div>'
            '<div class="en-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ NEW BOOK · DEMAI MONOGRAPH No.%d · ~%s CHARS · %d PP · __PRICE__</div>'
            '<h3 class="zh-only" style="color:#F1EBDC;font-size:25px;line-height:1.5;margin:0 0 14px">__TITLE__</h3>'
            '<h3 class="en-only" style="color:#F1EBDC;font-size:23px;line-height:1.5;margin:0 0 14px">%s</h3>'
            '<p class="zh-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">%s</p>'
            '<p class="en-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">%s</p></div></a>'
            % (NO, NO, han / 10000, pages, NO, format(round(han, -3), ','), pages, CT['titleEn'], CT['todayZh'], CT['todayEn'])).replace('__PRICE__', PRICE).replace('__TITLE__', '%s：%s' % (T, SUB)) + E0
    h = h[:a0] + card + h[a0:]
    tp.write_text(h)
    print('published to', d, 'pages', pages, 'han', han)


if __name__ == '__main__':
    main()
