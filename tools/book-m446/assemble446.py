#!/usr/bin/env python3
"""第 446 号《法律是谁？》：装进 public/books/m/446/（封面、PDF、全文网页、翻页器、详情页），并挂接书目。
用法：python3 tools/book-m446/assemble446.py --text /tmp/w446/bk/text.html --pdfdir <含两版 PDF 与封面的目录>
不做 git 操作。重复运行安全（书目条目已存在则替换）。"""
import argparse, datetime, json, re, shutil, subprocess, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import content446 as CT
SITE = HERE.resolve().parents[1] / 'public'
NO = 446; V = '20261020a'; SLUG = 'falv-shi-shei'
T, SUB = '法律是谁？', '普通人都能明白的法律'
ISBN = '979-8-90690-177-4'
AG = CT.AGENT['name']
D = SITE / 'books' / 'm' / str(NO)

def pages_of(pdf):
    o = subprocess.run(['pdfinfo', str(pdf)], capture_output=True, text=True).stdout
    return int(re.search(r'Pages:\s+(\d+)', o).group(1))

def toc_from_pdf(pdf):
    """用 PDF 书签（无则用目录页）算翻页器目录。返回 (toc, offset)。"""
    import pypdf
    r = pypdf.PdfReader(str(pdf))
    ol = r.outline
    flat = []
    def walk(o, lv):
        for x in o:
            if isinstance(x, list): walk(x, lv + 1)
            else: flat.append((lv, x.title, r.get_destination_page_number(x) + 1))
    walk(ol, 1)
    return flat

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--text', type=Path, required=True); ap.add_argument('--pdfdir', type=Path, required=True)
    ap.add_argument('--toc', type=Path, required=True, help='toc-reader.json（由 mktoc446.py 生成）')
    ap.add_argument('--ms', type=Path, required=True)
    A = ap.parse_args(); b = A.pdfdir
    (D / 'text').mkdir(parents=True, exist_ok=True)
    shutil.copy(b / f'{SLUG}-print.pdf', D / f'{SLUG}-print.pdf')
    shutil.copy(b / f'{SLUG}-reader.pdf', D / f'{SLUG}-reader.pdf')
    shutil.copy(b / 'cover-front.jpg', D / 'cover.jpg')
    shutil.copy(b / 'cover-back.jpg', D / 'backcover.jpg')
    shutil.copy(A.text, D / 'text' / 'index.html')
    tpl = (SITE / 'books' / 'm' / '259' / 'read.html').read_text()
    toc = json.loads(A.toc.read_text())
    rep = [
        ('友好阅读 · 在线翻页 · 谈尼采视角主义的错误 | SDE Universes', f'友好阅读 · 在线翻页 · {T} | SDE Universes'),
        ('《谈尼采视角主义的错误》在线翻页阅读', f'《{T}》在线翻页阅读'),
        ('https://sdeuniverses.com/books/m/259/read.html', f'https://sdeuniverses.com/books/m/{NO}/read.html'),
        ('<span class="ttl">谈尼采视角主义的错误</span><span class="sub hideS">视角是选出来的，还是长出来的</span>', f'<span class="ttl">{T}</span><span class="sub hideS">{SUB}</span>'),
        ('<a href="/books/m/259/"', f'<a href="/books/m/{NO}/"'),
        ("title: '谈尼采视角主义的错误',", f"title: '{T}',"),
        ("msg('正在载入《谈尼采视角主义的错误》…');", f"msg('正在载入《{T}》…');"),
    ]
    for a, c in rep:
        assert a in tpl, a[:50]
        tpl = tpl.replace(a, c)
    cfg = {'pdf': f'/books/m/{NO}/{SLUG}-reader.pdf?v={V}', 'key': f'books-m-{NO}-v1', 'offset': toc['offset']}
    tpl = re.sub(r'<script type="application/json" id="cfg">.*?</script>', lambda m: '<script type="application/json" id="cfg">%s</script>' % json.dumps(cfg, ensure_ascii=False), tpl, flags=re.S)
    tpl = re.sub(r'<script type="application/json" id="toc">.*?</script>', lambda m: '<script type="application/json" id="toc">%s</script>' % json.dumps(toc['toc'], ensure_ascii=False), tpl, flags=re.S)
    assert 'm/259' not in tpl and '尼采' not in tpl
    (D / 'read.html').write_text(tpl)
    pages = pages_of(b / f'{SLUG}-print.pdf')
    han = len(re.findall(r'[一-鿿]', A.ms.read_text()))
    det = (HERE / 'detail.html').read_text()
    det = det.replace('__AGENT__', AG).replace('__V__', V).replace('__PAGES__', str(pages)).replace('__WAN__', '%.0f' % (han / 10000))
    assert '__' not in det.replace('__agentproxy', '')
    (D / 'index.html').write_text(det)
    # 书目
    cat_p = SITE / 'books' / 'catalog.json'
    data = json.loads(cat_p.read_text()); books = data['books']
    books[:] = [x for x in books if str(x.get('number')) != str(NO)]
    assert not any((x.get('isbn') or '').replace('-', '') == ISBN.replace('-', '') for x in books), 'ISBN 重号'
    url = f'https://sdeuniverses.com/books/m/{NO}/'
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    entry = dict(id=f'm-{NO}', number=NO, title=T, subtitle=SUB, authors=['高鹏'], advisor='王德生', category='culture', description=CT.DESC,
                 detailUrl=url, readUrl=url + 'read.html', readMode='full', readLabel='友好阅读 · 在线翻页',
                 pdfUrl=url + f'{SLUG}-reader.pdf?v={V}', printPdfUrl=url + f'{SLUG}-print.pdf?v={V}',
                 coverUrl=url + f'cover.jpg?v={V}', backcoverUrl=url + f'backcover.jpg?v={V}',
                 flipUrl=url + 'read.html', chapterUrl=url + 'text/', openness='full',
                 price='US$20.00', priceUsd=20, currency='USD', priceLabel='US$20.00', edition='2026年10月第1版',
                 pdfPages=pages, publishedAt=now, publisher='德麦国际出版社', publisherEnglish='Demai International Press',
                 isbn=ISBN.replace('-', ''),
                 agentUrl=url + 'agent/dialogue.html', agentName=AG, agentLabel='智能问对 · ' + AG,
                 learnUrl=url + 'agent/learning.html', learningUrl=url + 'agent/learning.html', learnLabel='学习包 · 38个学习单元',
                 learningPackUrl=url + f'downloads/{SLUG}-learning-v1.0.pdf',
                 publicationUnit={'id': f'm-{NO}', 'type': 'reading-learning-dialogue', 'revision': '20261020-m446-unit-v1'})
    books.insert(0, entry)
    data['updated'] = now[:10]
    cat_p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    # agents.json
    ag_p = SITE / 'books' / 'agents.json'
    ag = json.loads(ag_p.read_text())
    ag['agents'][str(NO)] = {'name': AG, 'epithet': CT.AGENT['epithet'], 'intro': CT.AGENT['intro'], 'starts': CT.AGENT['starts']}
    assert sum(1 for v in ag['agents'].values() if v['name'] == AG) == 1, '智能体名重名'
    ag['agents'] = dict(sorted(ag['agents'].items(), key=lambda kv: int(kv[0]))) if False else ag['agents']
    ag['updated'] = ag['updatedAt'] = now[:10]
    ag_p.write_text(json.dumps(ag, ensure_ascii=False, indent=2) + '\n')
    # keypoints
    kp = dict(no=NO, title='法律是谁？——普通人都能明白的法律', built='2026-10-20', items=[dict(t=t, x=x, ch=ch) for t, x, ch in CT.KEYPOINTS])
    (D / 'keypoints.json').write_text(json.dumps(kp, ensure_ascii=False, indent=2) + '\n')
    # sitemap
    sm = SITE / 'sitemap.xml'; t = sm.read_text()
    for u in [url, url + 'text/', url + 'read.html']:
        if '<loc>%s</loc>' % u not in t:
            t = t.replace('</urlset>', '<url><loc>%s</loc><lastmod>%s</lastmod></url>\n</urlset>' % (u, now[:10]))
    sm.write_text(t)
    # today 新书卡
    tp = SITE / 'today' / 'index.html'; h = tp.read_text()
    if f'href="/books/m/{NO}/"' not in h:
        i = h.index('★ 新书 · 德麦国际专著第'); a0 = h.rindex('<a href="/books/m/', 0, i)
        card = ('<a href="/books/m/%d/" style="display:block;text-decoration:none;margin-bottom:16px"><div style="border:1px solid rgba(217,180,92,0.85);border-radius:3px;background:linear-gradient(135deg,rgba(14,31,49,0.98),rgba(9,18,30,0.98));padding:34px 32px;box-shadow:0 0 0 1px rgba(217,180,92,0.16) inset,0 0 40px rgba(217,180,92,0.10)">'
                '<div class="zh-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ 新书 · 德麦国际专著第 %d 号 · 约 %.0f 万字 · %d 页 · US$ 20.00</div>'
                '<div class="en-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ NEW BOOK · DEMAI MONOGRAPH No.%d · ~%s CHARS · %d PP · US$ 20.00</div>'
                '<h3 class="zh-only" style="color:#F1EBDC;font-size:25px;line-height:1.5;margin:0 0 14px">法律是谁？——普通人都能明白的法律</h3>'
                '<h3 class="en-only" style="color:#F1EBDC;font-size:23px;line-height:1.5;margin:0 0 14px">Who Is Law? Law Explained for Everyone</h3>'
                '<p class="zh-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">%s</p>'
                '<p class="en-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">%s</p></div></a>'
                % (NO, NO, han / 10000, pages, NO, format(han, ','), pages, CT.TODAY_ZH, CT.TODAY_EN))
        tp.write_text(h[:a0] + card + h[a0:])
    print('assembled', D, 'pages', pages, 'han', han)

if __name__ == '__main__':
    main()
