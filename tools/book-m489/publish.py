#!/usr/bin/env python3
"""第 489 号《学习如何发生》（阳涌子本）：装进 public/books/m/489/（PDF、封面、全文网页、翻页器、详情页）、书目、站点地图、/today/ 新书卡。
由 tools/book-m415/publish.py 改来。用法（仓库根目录）：python3 tools/book-m489/publish.py --build /home/claude/typeset/yy/build
"""
import argparse, datetime, json, re, shutil
from pathlib import Path

HERE = Path(__file__).parent
SITE = HERE.resolve().parents[1] / 'public'
NO = 489
V = '20261022m489'
SLUG = 'xuexi-ruhe-fasheng-yy'
T, SUB = '学习如何发生', 'SDE 三方程的教育思考与实践（阳涌子本）'
FULL = T + '：' + SUB
ISBN = '979-8-90690-643-4'


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--build', type=Path, required=True)
    b = ap.parse_args().build
    d = SITE / 'books' / 'm' / str(NO)
    assert not (d / 'index.html').exists(), f'{NO} 号目录已存在'
    (d / 'text').mkdir(parents=True, exist_ok=True)
    shutil.copy(b / f'{SLUG}-print.pdf', d / f'{SLUG}-print.pdf')
    shutil.copy(b / f'{SLUG}-reader.pdf', d / f'{SLUG}-reader.pdf')
    shutil.copy(b / 'cover.jpg', d / 'cover.jpg')
    shutil.copy(b / 'backcover.jpg', d / 'backcover.jpg')
    shutil.copy(b / 'text.html', d / 'text' / 'index.html')

    # 翻页器：照第 259 号矢量翻页器（同第 406 号做法），只换书名、PDF 与目录（目录取阅读版 PDF 书签）
    import pymupdf
    rd = pymupdf.open(str(b / f'{SLUG}-reader.pdf')); npg = len(rd)
    bm = rd.get_toc()
    first = next(p for l, t, p in bm if t.startswith('导论'))   # 导论页＝正文第 1 页
    offset = first
    toc = [{'t': '封面', 'p': '', 'g': 1, 'l': 1}]
    for l, t, p in bm:
        t = t.strip()
        if t.startswith('◆'): continue
        lv = 1 if l == 1 else 2
        pp = str(p - offset + 1) if p >= offset else ''
        toc.append({'t': t, 'p': pp, 'g': p, 'l': lv})
    toc.append({'t': '封底', 'p': '', 'g': npg, 'l': 1})
    tpl = (SITE / 'books' / 'm' / '259' / 'read.html').read_text()
    rep = [
        ('友好阅读 · 在线翻页 · 谈尼采视角主义的错误 | SDE Universes', f'友好阅读 · 在线翻页 · {FULL} | SDE Universes'),
        ('《谈尼采视角主义的错误》在线翻页阅读', f'《{FULL}》在线翻页阅读'),
        ('https://sdeuniverses.com/books/m/259/read.html', f'https://sdeuniverses.com/books/m/{NO}/read.html'),
        ('<span class="ttl">谈尼采视角主义的错误</span><span class="sub hideS">视角是选出来的，还是长出来的</span>',
         f'<span class="ttl">{T}</span><span class="sub hideS">{SUB}</span>'),
        ('<a href="/books/m/259/"', f'<a href="/books/m/{NO}/"'),
        ("title: '谈尼采视角主义的错误',", f"title: '{FULL}',"),
        ("msg('正在载入《谈尼采视角主义的错误》…');", f"msg('正在载入《{FULL}》…');"),
    ]
    for a, c in rep:
        assert a in tpl, a[:50]
        tpl = tpl.replace(a, c)
    cfg = {'pdf': f'/books/m/{NO}/{SLUG}-reader.pdf?v={V}', 'key': f'books-m-{NO}-v1', 'offset': offset}
    tpl = re.sub(r'<script type="application/json" id="cfg">.*?</script>',
                 lambda m: '<script type="application/json" id="cfg">%s</script>' % json.dumps(cfg, ensure_ascii=False), tpl, flags=re.S)
    tpl = re.sub(r'<script type="application/json" id="toc">.*?</script>',
                 lambda m: '<script type="application/json" id="toc">%s</script>' % json.dumps(toc, ensure_ascii=False), tpl, flags=re.S)
    assert 'm/259' not in tpl and '谈尼采' not in tpl
    (d / 'read.html').write_text(tpl)

    pages = len(pymupdf.open(str(b / f'{SLUG}-print.pdf')))
    han = len(re.findall(r'[\u4e00-\u9fff]', (b / 'text.html').read_text()))
    det = (HERE / 'detail.html').read_text()
    det = det.replace('__V__', V).replace('__PAGES__', str(pages)).replace('__WAN__', '%.1f' % (han / 10000)).replace('__RPAGES__', str(npg))
    assert '__' not in det
    (d / 'index.html').write_text(det)

    cat_p = SITE / 'books' / 'catalog.json'
    data = json.loads(cat_p.read_text())
    books = data['books']
    assert not any(str(x.get('number')) == str(NO) for x in books), f'{NO} 号已被占用'
    assert not any((x.get('isbn') or '').replace('-', '') == ISBN.replace('-', '') for x in books), 'ISBN 重号'
    url = f'https://sdeuniverses.com/books/m/{NO}/'
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    entry = dict(id=f'm-{NO}', number=NO, title=FULL, subtitle='阳涌子本 · 思想母本：第 51 号《SDE三方程导论》', authors=['王德生'], category='edu',
                 description='学生学习的动力从哪里来？学生怎样学会系统性地思考？以王德生《SDE 三方程导论》（第 51 号）为思想母本，为一位数学教育者从他的两个问题出发重写的整本个体子本。两张底牌：动力不是一箱油，是被接住的落差；系统思考是三句追问——它在什么条件里经过哪些尝试长成这样、下一步往哪里走、它又反过来改变了什么。以初中数学课堂为主场景，四部二十四章：动力、系统思考、回写与学校、可检验的研究。王德生思想母本，阳涌子本；书中人物与课堂场景均为构造。',
                 detailUrl=url, readUrl=url + 'read.html', readMode='full', readLabel='友好阅读 · 在线翻页',
                 pdfUrl=url + f'{SLUG}-reader.pdf?v={V}', printPdfUrl=url + f'{SLUG}-print.pdf?v={V}',
                 coverUrl=url + f'cover.jpg?v={V}', backcoverUrl=url + f'backcover.jpg?v={V}',
                 flipUrl=url + 'read.html', chapterUrl=url + 'text/', openness='full',
                 price='US$20.00', priceUsd=20, currency='USD', priceLabel='US$20.00', edition='2026年10月第1版',
                 pdfPages=npg, printPdfPages=pages, publishedAt=now, publisher='德麦国际出版社', publisherEnglish='Demai International Press',
                 isbn=ISBN.replace('-', ''),
                 agentUrl=url + 'agent/dialogue.html', agentName='天平', agentLabel='智能问对 · 天平',
                 learnUrl=url + 'agent/learning.html', learningUrl=url + 'agent/learning.html', learnLabel='学习包 · 24个学习单元',
                 learningPackUrl=url + f'downloads/{SLUG}-learning-v1.0.pdf',
                 publicationUnit={'id': f'm-{NO}', 'type': 'reading-learning-dialogue', 'revision': '20261022-m489-unit-v1'})
    books.insert(0, entry)
    data['updated'] = now[:10]
    cat_p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

    sm = SITE / 'sitemap.xml'; t = sm.read_text()
    for u in [url, url + 'text/', url + 'read.html']:
        if '<loc>%s</loc>' % u not in t:
            t = t.replace('</urlset>', '<url><loc>%s</loc><lastmod>%s</lastmod></url>\n</urlset>' % (u, now[:10]))
    sm.write_text(t)

    tp = SITE / 'today' / 'index.html'; h = tp.read_text()
    i = h.index('★ 新书 · 德麦国际专著第')
    a0 = h.rindex('<a href="/books/m/', 0, i)
    card = ('<a href="/books/m/%d/" style="display:block;text-decoration:none;margin-bottom:16px"><div style="border:1px solid rgba(217,180,92,0.85);border-radius:3px;background:linear-gradient(135deg,rgba(14,31,49,0.98),rgba(9,18,30,0.98));padding:34px 32px;box-shadow:0 0 0 1px rgba(217,180,92,0.16) inset,0 0 40px rgba(217,180,92,0.10)">'
            '<div class="zh-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ 新书 · 德麦国际专著第 %d 号 · 约 %.1f 万字 · %d 页 · US$ 20.00</div>'
            '<div class="en-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ NEW BOOK · DEMAI MONOGRAPH No.%d · ~%s CHARS · %d PP · US$ 20.00</div>'
            '<h3 class="zh-only" style="color:#F1EBDC;font-size:25px;line-height:1.5;margin:0 0 14px">学习如何发生：SDE 三方程的教育思考与实践（阳涌子本）</h3>'
            '<h3 class="en-only" style="color:#F1EBDC;font-size:23px;line-height:1.5;margin:0 0 14px">How Learning Happens: The Three SDE Equations in Education (A Reader’s Edition for Yang Yong)</h3>'
            '<p class="zh-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">王德生思想母本，阳涌子本。母本—子本阅读新典范的第一本个体子本：以第 51 号《SDE 三方程导论》为母本，为一位数学教育者从他的两个问题重写整本书——动力不是一箱油，是被接住的落差；系统思考是三句追问。含阅读、学习包、智能体三位一体出版单元。</p>'
            '<p class="en-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">Built on Wang Desheng’s Monograph No. 51 and rewritten for one reader’s two questions: where the drive to learn comes from, and how students learn to think in systems.</p></div></a>'
            % (NO, NO, han / 10000, pages, NO, format(han, ','), pages))
    h = h[:a0] + card + h[a0:]
    tp.write_text(h)
    print('published to', d, 'print pages', pages, 'reader pages', npg, 'offset', offset, 'han', han, 'toc', len(toc))


if __name__ == '__main__':
    main()
