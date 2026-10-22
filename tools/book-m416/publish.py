#!/usr/bin/env python3
"""第 416 号《收口——AI 时代谁来结这一笔账》（工具由第 478 号改来）：装进 public/books/m/416/（PDF、封面、全文网页、翻页器、详情页）、书目、站点地图、/today/ 新书卡。
用法：python3 tools/book-m416/publish.py --build /home/claude/typeset/shoukou/build --agent 交班 --ms /home/claude/typeset/shoukou/unit_ms.md
"""
import argparse, datetime, json, re, shutil, subprocess
from pathlib import Path

HERE = Path(__file__).parent
SITE = HERE.resolve().parents[1] / 'public'
NO = 416
V = '20261022c'
SLUG = 'shoukou'
T, SUB = '收口', 'AI 时代谁来结这一笔账'
ISBN = '979-8-90690-416-4'


def pages_of(pdf):
    o = subprocess.run(['pdfinfo', str(pdf)], capture_output=True, text=True).stdout
    return int(re.search(r'Pages:\s+(\d+)', o).group(1))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--build', type=Path, required=True); ap.add_argument('--agent', required=True); ap.add_argument('--ms', required=True)
    A = ap.parse_args(); b = A.build; AG = A.agent
    d = SITE / 'books' / 'm' / str(NO)
    assert not (d / 'index.html').exists(), f'{NO} 号目录已存在'
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
    det = det.replace('__V__', V).replace('__PAGES__', str(pages)).replace('__WAN__', '28')
    assert '__' not in det.replace('__agentproxy', '')
    (d / 'index.html').write_text(det)
    cat_p = SITE / 'books' / 'catalog.json'
    data = json.loads(cat_p.read_text())
    books = data['books']
    assert not any(str(x.get('number')) == str(NO) for x in books), f'{NO} 号已被占用'
    assert not any((x.get('isbn') or '').replace('-', '') == ISBN.replace('-', '') for x in books), 'ISBN 重号'
    url = f'https://sdeuniverses.com/books/m/{NO}/'
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    entry = dict(id=f'm-{NO}', number=NO, title=T, subtitle=SUB, authors=['王德生'], category='ai',
                 description='夜里十一点，一家人里有三个在按同一种按钮：重新生成。作文、海报、一句没事，按一下不花钱，也不欠谁；可是最后一步谁走、错了谁买单、尺子谁能改回来？本书从德麦国际书架教育、健康、事业三类挑出十部专著两两碰撞，提出母题「收口」：AI 把开口变得几乎免费，在少数被法规点名的高风险场合之外，却几乎没有给收口留下位置。收口三件（收尾、认账、改尺）加收口时距；四格中的靶格是空重开；读数是收口率与写进率；第八编推出收口产业的十个新行业（初判）。第 46 章在公开记录上真跑两条，把本书的话改小；第 47 章押四条赌注到 2029 年底。王德生著；九编四十八章；含阅读、学习包、智能体三位一体。',
                 detailUrl=url, readUrl=url + 'read.html', readMode='full', readLabel='友好阅读 · 在线翻页',
                 pdfUrl=url + f'{SLUG}-reader.pdf?v={V}', printPdfUrl=url + f'{SLUG}-print.pdf?v={V}',
                 coverUrl=url + f'cover.jpg?v={V}', backcoverUrl=url + f'backcover.jpg?v={V}',
                 flipUrl=url + 'read.html', chapterUrl=url + 'text/', openness='full',
                 price='US$23.00', priceUsd=23, currency='USD', priceLabel='US$23.00', edition='2026年10月第1版',
                 pdfPages=pages, publishedAt=now, publisher='德麦国际出版社', publisherEnglish='Demai International Press',
                 isbn=ISBN.replace('-', ''),
                 agentUrl=url + 'agent/dialogue.html', agentName=AG, agentLabel='智能问对 · ' + AG,
                 learnUrl=url + 'agent/learning.html', learningUrl=url + 'agent/learning.html', learnLabel='学习包 · 48个学习单元',
                 learningPackUrl=url + f'downloads/{SLUG}-learning-v1.0.pdf',
                 publicationUnit={'id': f'm-{NO}', 'type': 'reading-learning-dialogue', 'revision': '20261022-m416-unit-v1'})
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
            '<div class="zh-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ 新书 · 德麦国际专著第 %d 号 · 约 %.0f 万字 · %d 页 · US$ 23.00</div>'
            '<div class="en-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ NEW BOOK · DEMAI MONOGRAPH No.%d · ~%s CHARS · %d PP · US$ 23.00</div>'
            '<h3 class="zh-only" style="color:#F1EBDC;font-size:25px;line-height:1.5;margin:0 0 14px">收口——AI 时代谁来结这一笔账</h3>'
            '<h3 class="en-only" style="color:#F1EBDC;font-size:23px;line-height:1.5;margin:0 0 14px">Closing: Who Settles the Account in the Age of AI</h3>'
            '<p class="zh-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">王德生著。教育、健康、事业十部专著两两碰撞：AI 把开口变得几乎免费，却几乎没有给收口留下位置。收口三件、空重开、收口率，与 AI 时代的收口产业。含阅读、学习包、智能体三位一体出版单元。</p>'
            '<p class="en-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">By Wang Desheng. Ten monographs on education, health and work collide: AI makes opening nearly free yet leaves almost no registered place for closing.</p></div></a>'
            % (NO, NO, han / 10000, pages, NO, format(han, ','), pages))
    h = h[:a0] + card + h[a0:]
    tp.write_text(h)
    print('published to', d, 'pages', pages, 'han', han)


if __name__ == '__main__':
    main()
