#!/usr/bin/env python3
"""第 501 号《道德经SDE新解——普通人都能明白的》：一条命令装进 public/books/m/501/（PDF、封面、全文网页、翻页器、详情页）、书目、站点地图、/today/ 新书卡。
用法：
  python3 tools/book-m501/publish.py [--agent 摸丝] [--build /home/claude/b501] [--ms 全稿.md] [--units 81] [--dry]
  智能体名也可用环境变量 AGENT_NAME；学习单元数用 LEARN_UNITS。
  --dry：只做全部断言，并把将写的文件放到 <build>/dry/ ，不动站点。
"""
import argparse, datetime, json, os, re, shutil, subprocess
from pathlib import Path

HERE = Path(__file__).parent
SITE = HERE.resolve().parents[1] / 'public'
NO = 501
V = '20261020a'
SLUG = 'daodejing-sde'
T, SUB = '道德经SDE新解', '普通人都能明白的'
ISBN = '979-8-90690-167-5'
PRICE = 25
T_EN = 'The Daodejing, Re-read with SDE: A Version for Everyone'
ZH_JUDGE = '回去的路，是另一条路。根是一块一直被写的土，不是埋着的老物件。'


def pages_of(pdf):
    o = subprocess.run(['pdfinfo', str(pdf)], capture_output=True, text=True).stdout
    return int(re.search(r'Pages:\s+(\d+)', o).group(1))


def part_list(ms):
    """从全稿读九编：编题与章号范围。"""
    out, cur = [], None
    for ln in ms.splitlines():
        m = re.match(r'^# (第.编)　(.*)$', ln)
        if m:
            cur = [m[1], m[2], []]; out.append(cur); continue
        m = re.match(r'^## 第 (\d+) 章', ln)
        if m and cur:
            cur[2].append(int(m[1]))
    assert len(out) == 9 and sum(len(c[2]) for c in out) == 81
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--build', type=Path, default=Path('/home/claude/b501'))
    ap.add_argument('--agent', default=os.environ.get('AGENT_NAME', '摸丝'))
    ap.add_argument('--ms', type=Path, default=Path('/home/claude/huibuqu/build/全稿.md'))
    ap.add_argument('--units', default=os.environ.get('LEARN_UNITS', '81'))
    ap.add_argument('--dry', action='store_true')
    A = ap.parse_args(); b = A.build; AG = A.agent
    real = SITE / 'books' / 'm' / str(NO)
    assert not (real / 'index.html').exists() or A.dry, f'{NO} 号目录已存在'
    d = (b / 'dry' / 'm' / str(NO)) if A.dry else real
    (d / 'text').mkdir(parents=True, exist_ok=True)
    for f in (f'{SLUG}-print.pdf', f'{SLUG}-reader.pdf', 'cover.jpg', 'backcover.jpg'):
        shutil.copy(b / f, d / f)
    shutil.copy(b / 'text.html', d / 'text' / 'index.html')
    ms = A.ms.read_text()
    han = len(re.findall(r'[一-鿿]', ms)); wan = han // 10000
    pages = pages_of(b / f'{SLUG}-print.pdf')
    # ── read.html（第 259 号为模板）
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
    # ── 书页
    parts = part_list(ms)
    plist = ''.join('<li><b>%s</b>　%s（第%d—%d章）</li>' % (p, t, c[0], c[-1]) for p, t, c in parts)
    plist = '<li><b>导论</b>　导论一至四</li>' + plist + '<li><b>结卷</b>　结一至结四</li>'
    det = (HERE / 'detail.html').read_text()
    for k, v in (('__V__', V), ('__PAGES__', str(pages)), ('__WAN__', str(wan)), ('__AGENT__', AG), ('__UNITS__', str(A.units)), ('__PARTS__', plist)):
        det = det.replace(k, v)
    assert '__' not in det.replace('__agentproxy', ''), re.findall(r'__\w+__', det)
    (d / 'index.html').write_text(det)
    # ── catalog
    cat_p = SITE / 'books' / 'catalog.json'
    data = json.loads(cat_p.read_text())
    books = data['books']
    assert not any(str(x.get('number')) == str(NO) for x in books), f'{NO} 号已被占用'
    assert not any((x.get('isbn') or '').replace('-', '') == ISBN.replace('-', '') for x in books), 'ISBN 重号'
    assert not any(x.get('id') == f'm-{NO}' for x in books)
    url = f'https://sdeuniverses.com/books/m/{NO}/'
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    entry = dict(id=f'm-{NO}', number=NO, title=T, subtitle=SUB, authors=['王德生'], category='core',
                 description='「统」字带绞丝旁，说的是丝。一团丝，每一根都和别的连着，碰一处，全体都动，这是一；把每一根的头攥在手里往一个方向拽，丝是拉直了，可它们不再互相连着，这是统。本书读《道德经》，读出来的一是摸出来的不间断。八十一章，每章把郭店、帛书、通行本的差别摆出来，再放进教育、健康、事业各走一遍；读不动的地方，就写读不动。全书一句话：回去的路，是另一条路。根是一块一直被写的土，不是埋着的老物件。王德生著；导论四篇、九编八十一章、结卷四篇；含阅读、学习包、智能体三位一体。',
                 detailUrl=url, readUrl=url + 'read.html', readMode='full', readLabel='友好阅读 · 在线翻页',
                 pdfUrl=url + f'{SLUG}-reader.pdf?v={V}', printPdfUrl=url + f'{SLUG}-print.pdf?v={V}',
                 coverUrl=url + f'cover.jpg?v={V}', backcoverUrl=url + f'backcover.jpg?v={V}',
                 flipUrl=url + 'read.html', chapterUrl=url + 'text/', openness='full',
                 price='US$%d.00' % PRICE, priceUsd=PRICE, currency='USD', priceLabel='US$%d.00' % PRICE, edition='2026年10月第1版',
                 pdfPages=pages, publishedAt=now, publisher='德麦国际出版社', publisherEnglish='Demai International Press',
                 isbn=ISBN.replace('-', ''),
                 agentUrl=url + 'agent/dialogue.html', agentName=AG, agentLabel='智能问对 · ' + AG,
                 learnUrl=url + 'agent/learning.html', learningUrl=url + 'agent/learning.html', learnLabel='学习包 · %s个学习单元' % A.units,
                 learningPackUrl=url + f'downloads/{SLUG}-learning-v1.0.pdf',
                 publicationUnit={'id': f'm-{NO}', 'type': 'reading-learning-dialogue', 'revision': '20261020-m501-unit-v1'})
    books.insert(0, entry)
    data['updated'] = now[:10]
    # ── sitemap
    sm = SITE / 'sitemap.xml'; t = sm.read_text()
    for u in [url, url + 'text/', url + 'read.html']:
        if '<loc>%s</loc>' % u not in t:
            assert '</urlset>' in t
            t = t.replace('</urlset>', '<url><loc>%s</loc><lastmod>%s</lastmod></url>\n</urlset>' % (u, now[:10]))
    # ── today 新书卡
    tp = SITE / 'today' / 'index.html'; h = tp.read_text()
    assert f'/books/m/{NO}/' not in h, 'today 已有本书卡'
    i = h.index('★ 新书 · 德麦国际专著第')
    a0 = h.rindex('<a href="/books/m/', 0, i)
    card = ('<a href="/books/m/%d/" style="display:block;text-decoration:none;margin-bottom:16px"><div style="border:1px solid rgba(217,180,92,0.85);border-radius:3px;background:linear-gradient(135deg,rgba(14,31,49,0.98),rgba(9,18,30,0.98));padding:34px 32px;box-shadow:0 0 0 1px rgba(217,180,92,0.16) inset,0 0 40px rgba(217,180,92,0.10)">'
            '<div class="zh-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ 新书 · 德麦国际专著第 %d 号 · 约 %d 万字 · %d 页 · US$ %d.00</div>'
            '<div class="en-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ NEW BOOK · DEMAI MONOGRAPH No.%d · ~%s CHARS · %d PP · US$ %d.00</div>'
            '<h3 class="zh-only" style="color:#F1EBDC;font-size:25px;line-height:1.5;margin:0 0 14px">道德经SDE新解——普通人都能明白的</h3>'
            '<h3 class="en-only" style="color:#F1EBDC;font-size:23px;line-height:1.5;margin:0 0 14px">%s</h3>'
            '<p class="zh-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">王德生著。回去的路，是另一条路。根是一块一直被写的土，不是埋着的老物件。九编八十一章，每章把郭店、帛书、通行本的差别摆在你面前，读不动的地方，就写读不动。含阅读、学习包、智能体三位一体出版单元。</p>'
            '<p class="en-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">By Wang Desheng. All eighty-one chapters of the Daodejing, each laying the Guodian, Mawangdui and received texts side by side, then trying the chapter out in a classroom, a household and a small business. Where the reading cannot get through, the book says so.</p></div></a>'
            % (NO, NO, wan, pages, PRICE, NO, format(han, ','), pages, PRICE, T_EN))
    h2 = h[:a0] + card + h[a0:]
    if A.dry:
        (b / 'dry').mkdir(exist_ok=True)
        (b / 'dry' / 'catalog-entry.json').write_text(json.dumps(entry, ensure_ascii=False, indent=2))
        (b / 'dry' / 'today-card.html').write_text(card)
        print('DRY ok: files in', d, '; pages', pages, 'han', han); return
    cat_p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    sm.write_text(t)
    tp.write_text(h2)
    print('published to', d, 'pages', pages, 'han', han)


if __name__ == '__main__':
    main()
