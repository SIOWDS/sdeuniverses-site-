#!/usr/bin/env python3
"""第 428 号《这把不算：玩的发生学》（柴翱著，王德生指导；由第 423 号 publish.py 改来）：
装进 public/books/m/428/（PDF、封面、全文网页、翻页器、详情页）、书目、站点地图、/today/ 新书卡，
并把书号预留档 .publish/volume-reservations/428.json 改为 published（照 513.json）。
用法（仓库根目录）：python3 tools/book-m428/publish.py --build /home/claude/bk428 --content tools/book-m428/content.json --ms tools/book-m428/book.md
"""
import argparse, datetime, json, re, shutil, subprocess
from pathlib import Path

HERE = Path(__file__).parent
SITE = HERE.resolve().parents[1] / 'public'
NO = 428
V = '20261025b'
SLUG = 'zhebabusuan'
T, SUB = '这把不算', '玩的发生学'
ISBN = '979-8-90690-428-7'
AUTHORS = ['柴翱']
AUTHOR_NOTE = '柴翱著，王德生指导'


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
    _rp = SITE.parent / '.publish' / 'volume-reservations' / f'{NO}.json'
    _res = json.loads(_rp.read_text())
    assert _res['title'] == T and _res['isbnNormalized'] == ISBN.replace('-', ''), '预留档不是本书'
    _d = re.sub(r'\D', '', ISBN); assert int(_d[12]) == (10 - sum(int(c) * (3 if i % 2 else 1) for i, c in enumerate(_d[:12])) % 10) % 10, 'ISBN 校验位不对'
    (d / 'text').mkdir(parents=True, exist_ok=True)
    shutil.copy(b / f'{SLUG}-print.pdf', d / f'{SLUG}-print.pdf')
    shutil.copy(b / f'{SLUG}-reader.pdf', d / f'{SLUG}-reader.pdf')
    shutil.copy(b / 'cover.jpg', d / 'cover.jpg')
    shutil.copy(b / 'backcover.jpg', d / 'backcover.jpg')
    shutil.copy(b / 'text.html', d / 'text' / 'index.html')
    toc = {'offset': int(json.loads((b / 'build_report.json').read_text())['reader_offset']), 'pages': pages_of(b / f'{SLUG}-reader.pdf')}
    subprocess.run(['python3', str(HERE.parents[0] / 'build_flip_reader.py'), 'one', '--read', str(d / 'read.html'),
                    '--pdf', f'/books/m/{NO}/{SLUG}-reader.pdf?v={V}', '--title', T, '--sub', SUB, '--detail', f'/books/m/{NO}/',
                    '--offset', str(toc['offset']), '--key', f'books-m-{NO}-v1'], check=True)
    rd = (d / 'read.html').read_text()
    m = re.search(r'(<script type="application/json" id="toc">)(.*?)(</script>)', rd, flags=re.S)
    tl = json.loads(m.group(2))
    if not tl or tl[0].get('t') != '封面':
        tl.insert(0, {"t": "封面", "p": "", "g": 1, "l": 1})
        tl.append({"t": "封底", "p": "", "g": toc['pages'], "l": 1})
    rd = rd[:m.start(2)] + json.dumps(tl, ensure_ascii=False) + rd[m.end(2):]
    (d / 'read.html').write_text(rd)
    pages = pages_of(b / f'{SLUG}-print.pdf')
    han = len(re.findall(r'[一-鿿]', Path(A.ms).read_text()))
    det = (HERE / 'detail.html').read_text()
    import html as _h
    cards = ''.join('<div class="card"><b>%s</b><span>%s</span></div>' % (_h.escape(c['t']), _h.escape(c['x'])) for c in CT['loadBearing'])
    det = (det.replace('__AGENT__', AG).replace('__V__', V).replace('__PAGES__', str(pages)).replace('__WAN__', '%.0f' % (han / 10000))
           .replace('__LINE__', _h.escape(CT['detailLine'])).replace('__INTRO__', _h.escape(CT['detailIntro'])).replace('__CARDS__', cards)
           .replace('__DESC_SHORT__', _h.escape(CT['detailLine'], quote=True)))
    assert '__' not in det.replace('__agentproxy', '')
    (d / 'index.html').write_text(det)
    cat_p = SITE / 'books' / 'catalog.json'
    data = json.loads(cat_p.read_text())
    books = data['books']
    assert not any(str(x.get('number')) == str(NO) for x in books), f'{NO} 号已被占用'
    assert not any((x.get('isbn') or '').replace('-', '') == ISBN.replace('-', '') for x in books), 'ISBN 重号'
    url = f'https://sdeuniverses.com/books/m/{NO}/'
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    entry = dict(id=f'm-{NO}', number=NO, title=T, subtitle=SUB, authors=AUTHORS, authorNote=AUTHOR_NOTE, category='edu',
                 titleEn=CT['titleEn'], description=CT['description'],
                 detailUrl=url, readUrl=url + 'read.html', readMode='full', readLabel='友好阅读 · 在线翻页',
                 pdfUrl=url + f'{SLUG}-reader.pdf?v={V}', printPdfUrl=url + f'{SLUG}-print.pdf?v={V}',
                 coverUrl=url + f'cover.jpg?v={V}', backcoverUrl=url + f'backcover.jpg?v={V}',
                 flipUrl=url + 'read.html', chapterUrl=url + 'text/', openness='full',
                 price='US$20.00', priceUsd=20, currency='USD', priceLabel='US$20.00', edition='2026年10月第1版',
                 pdfPages=pages_of(b / f'{SLUG}-reader.pdf'), printPdfPages=pages, publishedAt=now, publisher='德麦国际出版社', publisherEnglish='Demai International Press',
                 isbn=ISBN.replace('-', ''),
                 agentUrl=url + 'agent/dialogue.html', agentName=AG, agentLabel='智能问对 · ' + AG,
                 learnUrl=url + 'agent/learning.html', learningUrl=url + 'agent/learning.html', learnLabel='学习包 · 12个学习单元',
                 learningPackUrl=url + f'downloads/{SLUG}-learning-v1.0.pdf',
                 publicationUnit={'id': f'm-{NO}', 'type': 'reading-learning-dialogue', 'revision': '20261025-m428-unit-v1'})
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
            '<div class="zh-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ 新书 · 德麦国际专著第 %d 号 · 约 %.0f 万字 · %d 页 · US$20.00</div>'
            '<div class="en-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ NEW BOOK · DEMAI MONOGRAPH No.%d · ~%s CHARS · %d PP · US$20.00</div>'
            '<h3 class="zh-only" style="color:#F1EBDC;font-size:25px;line-height:1.5;margin:0 0 14px">这把不算——玩的发生学</h3>'
            '<h3 class="en-only" style="color:#F1EBDC;font-size:23px;line-height:1.5;margin:0 0 14px">%s</h3>'
            '<p class="zh-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">%s</p>'
            '<p class="en-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">%s</p></div></a>'
            % (NO, NO, han / 10000, pages, NO, format(round(han, -3), ','), pages, CT['titleEn'], CT['todayZh'], CT['todayEn']))
    h = h[:a0] + card + h[a0:]
    tp.write_text(h)
    _res.update(status='published', publishedAt=now[:10], detailUrl=url)
    _res.setdefault('manuscript', {})['state'] = '已上站'
    _res['manuscript']['bodyHanzi'] = han
    _rp.write_text(json.dumps(_res, ensure_ascii=False, indent=2) + '\n')
    print('published to', d, 'pages', pages, 'han', han)


if __name__ == '__main__':
    main()
