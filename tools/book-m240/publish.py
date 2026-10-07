#!/usr/bin/env python3
"""第 240 号《从因材施教到超材创造》上站：照第 351 号 publish.py 改来。
用法：python3 publish.py --build /home/claude/b240/out   （out 里需有 text.html、toc-reader.json、cover.jpg、backcover.jpg、两个 PDF）"""
import argparse, datetime, json, re, shutil
from pathlib import Path
import pymupdf

HERE = Path(__file__).parent
SITE = HERE.resolve().parents[1] / 'public'
NO = 240
V = '20261007a'
SLUG = 'super-material-education'
T, SUB = '从因材施教到超材创造', 'AI时代的新教育使命'
ISBN = '979-8-90690-864-3'
WAN = 20


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--build', type=Path, required=True)
    b = ap.parse_args().build
    d = SITE / 'books' / 'm' / str(NO)
    assert not (d / 'index.html').exists(), f'{NO} 号目录已存在'
    cat_p = SITE / 'books' / 'catalog.json'
    data = json.loads(cat_p.read_text()); books = data['books']
    assert not any(str(x.get('number')) == str(NO) for x in books), f'{NO} 号已被占用'
    assert not any((x.get('isbn') or '').replace('-', '') == ISBN.replace('-', '') for x in books), 'ISBN 重号'
    (d / 'text').mkdir(parents=True, exist_ok=True)
    for f in [f'{SLUG}-print.pdf', f'{SLUG}-reader.pdf', 'cover.jpg', 'backcover.jpg']:
        shutil.copy(b / f, d / f)
    shutil.copy(b / 'text.html', d / 'text' / 'index.html')
    # 翻页器：照第 259 号模板，换书名、PDF 与目录
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
    pages = len(pymupdf.open(str(b / f'{SLUG}-print.pdf')))
    det = (HERE / 'detail.html').read_text().replace('__V__', V).replace('__PAGES__', str(pages)).replace('__WAN__', str(WAN))
    assert '__' not in det.replace('__agentproxy', '')
    (d / 'index.html').write_text(det)
    url = f'https://sdeuniverses.com/books/m/{NO}/'
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    entry = dict(id=f'm-{NO}', number=NO, title=T, subtitle=SUB, authors=['王德生'], category='edu',
                 description='看清一个孩子是块什么料，机器做得越来越好。如果“看清材、养成器”机器都能做，教育还剩什么是人的事？本书的回答是超材：因材施教是发现学的教育，AI 正在把它做到极致；教育的新使命，是设计让新的材能够长出来的结构，设计土，不设计孩子。全书五编四十章，从旧使命的伟大与终点，到0到1的真问题，到材的发生，到人、AI、问题三要素的结构设计，再到设计的边界与家庭、学校、社会的新分工；书中案例均为模拟。',
                 detailUrl=url, readUrl=url + 'read.html', readMode='full', readLabel='友好阅读 · 在线翻页',
                 pdfUrl=url + f'{SLUG}-reader.pdf?v={V}', printPdfUrl=url + f'{SLUG}-print.pdf?v={V}',
                 coverUrl=url + f'cover.jpg?v={V}', backcoverUrl=url + f'backcover.jpg?v={V}',
                 flipUrl=url + 'read.html', chapterUrl=url + 'text/', openness='full',
                 price='US$20.00', priceUsd=20, currency='USD', priceLabel='US$20.00', edition='2026年10月第1版',
                 pdfPages=pages, publishedAt=now, publisher='德麦国际出版社', publisherEnglish='Demai International Press',
                 isbn=ISBN.replace('-', ''))
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
            '<div class="zh-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ 新书 · 德麦国际专著第 %d 号 · 约 %d 万字 · %d 页 · US$ 20.00</div>'
            '<div class="en-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ NEW BOOK · DEMAI MONOGRAPH No.%d · ~200,000 CHARS · %d PP · US$ 20.00</div>'
            '<h3 class="zh-only" style="color:#F1EBDC;font-size:25px;line-height:1.5;margin:0 0 14px">从因材施教到超材创造：AI时代的新教育使命</h3>'
            '<h3 class="en-only" style="color:#F1EBDC;font-size:23px;line-height:1.5;margin:0 0 14px">From Fitting Teaching to the Material\'s Nature to Creating Super-Materials: The New Mission of Education in the AI Era</h3>'
            '<p class="zh-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">王德生著。机器越来越会看清每个孩子是块什么料，教育还剩什么是人的事？本书的回答是超材：教育的新使命，是设计让新的材能够长出来的结构，设计土，不设计孩子。五编四十章，书中案例均为模拟。</p>'
            '<p class="en-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">By Wang Desheng. Machines are ever better at seeing what each child is made of; what is left for people in education? The book answers: super-materials. Education\'s new mission is to design the structures in which new talent can grow. Five parts, forty chapters; all cases are simulated.</p></div></a>'
            % (NO, NO, WAN, pages, NO, pages))
    h = h[:a0] + card + h[a0:]
    tp.write_text(h)
    print('published to', d, 'pages', pages)


if __name__ == '__main__':
    main()
