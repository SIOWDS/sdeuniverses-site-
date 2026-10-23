#!/usr/bin/env python3
"""第 453 号《爱在创造中成全》：装进 public/books/m/453/（PDF、封面、全文网页、翻页器、详情页）、书目、站点地图、/today/ 新书卡。
由第 503 号 publish.py 改来；书籍常量一律取自 meta453.py（ISBN 暂定，改那一处即可）。

用法（仓库根目录）：
  python3 tools/book-m453/publish.py --build <build453目录> --content tools/book-m453/content.json --ms <全稿.md或任一含全书汉字的md>
可选：
  --site <dir>   指向别处的 public 目录做干跑（默认是本仓库的 public/）。
  --unit         同时挂入学习包/智能问对入口（默认不挂：本版尚未建 agent/ 与 unit/）。
注意：本脚本会写 public/、catalog.json、sitemap.xml、today/index.html——上站由主会话统一执行，作者审定 ISBN 后再跑。
"""
import argparse, datetime, json, re, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta453 as M

SITE = HERE.resolve().parents[1] / 'public'
NO = M.NO
V = M.VERSION
SLUG = M.SLUG
T, SUB = M.TITLE, M.SUBTITLE
ISBN = M.ISBN


def pages_of(pdf):
    o = subprocess.run(['pdfinfo', str(pdf)], capture_output=True, text=True).stdout
    return int(re.search(r'Pages:\s+(\d+)', o).group(1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--build', type=Path, required=True)
    ap.add_argument('--content', type=Path, required=True)
    ap.add_argument('--ms', required=True, help='含全书汉字的 md（取汉字数用，如 S/book.md）')
    ap.add_argument('--site', type=Path, default=SITE)
    ap.add_argument('--unit', action='store_true')
    A = ap.parse_args()
    site = A.site
    b = A.build
    CT = json.loads(A.content.read_text(encoding='utf-8'))
    d = site / 'books' / 'm' / str(NO)
    assert not (d / 'index.html').exists(), f'{NO} 号目录已存在'
    (d / 'text').mkdir(parents=True, exist_ok=True)
    for f in (f'{SLUG}-print.pdf', f'{SLUG}-reader.pdf', 'cover.jpg', 'backcover.jpg'):
        shutil.copy(b / f, d / f)
    shutil.copy(b / 'text.html', d / 'text' / 'index.html')
    tpl = (site / 'books' / 'm' / '259' / 'read.html').read_text(encoding='utf-8')
    toc = json.loads((b / 'toc-reader.json').read_text(encoding='utf-8'))
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
    (d / 'read.html').write_text(tpl, encoding='utf-8')
    pages = pages_of(b / f'{SLUG}-print.pdf')
    han = len(re.findall(r'[一-鿿]', Path(A.ms).read_text(encoding='utf-8')))
    wan = '%.0f' % (han / 10000)
    det = (HERE / 'detail.html').read_text(encoding='utf-8')
    unit_btns = unit_sec = ''
    if A.unit:
        unit_btns = (f'      <a class="btn" href="/books/m/{NO}/agent/learning.html">学习包 · {M.NCHAP} 个学习单元</a>\n'
                     f'      <a class="btn" href="/books/m/{NO}/agent/dialogue.html">智能问对 · {M.AGENT_NAME}</a>\n')
        unit_sec = (f'<h2>三位一体</h2>\n<p>本书同时是一个出版单元：全文阅读、{M.NCHAP} 章学习任务（学习包）、专属智能体「{M.AGENT_NAME}」的对话。'
                    f'入口见上方按钮，或到<a href="/books/m/{NO}/agent/">智能体页</a>。</p>\n')
    det = (det.replace('__UNIT_BTNS__', unit_btns).replace('__UNIT_SECTION__', unit_sec)
              .replace('__V__', V).replace('__PAGES__', str(pages)).replace('__WAN__', wan)
              .replace('__SLUG__', SLUG).replace('__ISBN_PLAIN__', ISBN.replace('-', ''))
              .replace('__PRICE_NUM__', '%.2f' % M.PRICE_USD))
    for k, v in M.placeholders().items():
        if k != '__WAN__':
            det = det.replace(k, v)
    assert '__' not in det.replace('__agentproxy', ''), re.findall(r'__\w+__', det)
    (d / 'index.html').write_text(det, encoding='utf-8')
    cat_p = site / 'books' / 'catalog.json'
    data = json.loads(cat_p.read_text(encoding='utf-8'))
    books = data['books']
    assert not any(str(x.get('number')) == str(NO) for x in books), f'{NO} 号已被占用'
    assert not any((x.get('isbn') or '').replace('-', '') == ISBN.replace('-', '') for x in books), 'ISBN 重号'
    if A.unit:
        assert not any(x.get('agentName') == M.AGENT_NAME for x in books), '智能体名已被占用'
    url = f'https://sdeuniverses.com/books/m/{NO}/'
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    desc = CT['description'].replace('__WAN__', wan)
    entry = dict(id=f'm-{NO}', number=NO, title=T, subtitle=SUB, authors=[M.AUTHOR], category='core',
                 description=desc,
                 detailUrl=url, readUrl=url + 'read.html', readMode='full', readLabel='友好阅读 · 在线翻页',
                 pdfUrl=url + f'{SLUG}-reader.pdf?v={V}', printPdfUrl=url + f'{SLUG}-print.pdf?v={V}',
                 coverUrl=url + f'cover.jpg?v={V}', backcoverUrl=url + f'backcover.jpg?v={V}',
                 flipUrl=url + 'read.html', chapterUrl=url + 'text/', openness='full',
                 price=M.PRICE, priceUsd=M.PRICE_USD, currency='USD', priceLabel=M.PRICE, edition=M.EDITION,
                 pdfPages=pages, publishedAt=now, publisher=M.PUBLISHER, publisherEnglish=M.PUBLISHER_EN,
                 isbn=ISBN.replace('-', ''))
    if A.unit:
        entry.update(agentUrl=url + 'agent/dialogue.html', agentName=M.AGENT_NAME, agentLabel='智能问对 · ' + M.AGENT_NAME,
                     learnUrl=url + 'agent/learning.html', learningUrl=url + 'agent/learning.html', learnLabel=f'学习包 · {M.NCHAP}个学习单元',
                     learningPackUrl=url + f'downloads/{SLUG}-learning-v1.0.pdf',
                     publicationUnit={'id': f'm-{NO}', 'type': 'reading-learning-dialogue', 'revision': M.UNIT_REV})
    books.insert(0, entry)
    data['updated'] = now[:10]
    cat_p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    sm = site / 'sitemap.xml'; t = sm.read_text(encoding='utf-8')
    for u in [url, url + 'text/', url + 'read.html']:
        if '<loc>%s</loc>' % u not in t:
            assert '</urlset>' in t
            t = t.replace('</urlset>', '<url><loc>%s</loc><lastmod>%s</lastmod></url>\n</urlset>' % (u, now[:10]))
    sm.write_text(t, encoding='utf-8')
    tp = site / 'today' / 'index.html'; h = tp.read_text(encoding='utf-8')
    i = h.index('★ 新书 · 德麦国际专著第')
    a0 = h.rindex('<a href="/books/m/', 0, i)
    price_sp = M.PRICE.replace('US$', 'US$ ')
    card = ('<a href="/books/m/%d/" style="display:block;text-decoration:none;margin-bottom:16px"><div style="border:1px solid rgba(217,180,92,0.85);border-radius:3px;background:linear-gradient(135deg,rgba(14,31,49,0.98),rgba(9,18,30,0.98));padding:34px 32px;box-shadow:0 0 0 1px rgba(217,180,92,0.16) inset,0 0 40px rgba(217,180,92,0.10)">'
            '<div class="zh-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ 新书 · 德麦国际专著第 %d 号 · 约 %s 万字 · %d 页 · %s</div>'
            '<div class="en-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ NEW BOOK · DEMAI MONOGRAPH No.%d · ~%s CHARS · %d PP · %s</div>'
            '<h3 class="zh-only" style="color:#F1EBDC;font-size:25px;line-height:1.5;margin:0 0 14px">%s——%s</h3>'
            '<h3 class="en-only" style="color:#F1EBDC;font-size:23px;line-height:1.5;margin:0 0 14px">%s</h3>'
            '<p class="zh-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">%s</p>'
            '<p class="en-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">%s</p></div></a>'
            % (NO, NO, wan, pages, price_sp, NO, format(han, ','), pages, price_sp, T, SUB, CT['titleEn'], CT['todayZh'], CT['todayEn']))
    h = h[:a0] + card + h[a0:]
    tp.write_text(h, encoding='utf-8')
    print('published to', d, 'pages', pages, 'han', han)


if __name__ == '__main__':
    main()
