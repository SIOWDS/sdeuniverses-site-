#!/usr/bin/env python3
"""把 build.py / cover.py 的产物装进 public/books/m/36/：PDF、封面、全文网页、翻页器、详情页、书目、站点地图。（2026 年 1 月已出版的旧书补上站，不挂 /today/ 新书卡）

用法：python3 publish.py --build /home/claude/bookwork/build
（由第 231 号 tools/book-m231/publish.py 改来；第 36 号原只有介绍页与三篇文章精选，此次换成全书，三篇文章保留在 articles/ 下）
"""
import argparse
import datetime
import json
import re
import shutil
from pathlib import Path

HERE = Path(__file__).parent
SITE = HERE.resolve().parents[1] / 'public'
NO = 36
V = '20261006a'
SLUG = 'human-gpt-super-composite'
T, SUB = '人—GPT超级复合智能体', 'SIO本体论下的三体对话与文明实践'
ISBN = '978-1-970820-32-4'


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--build', type=Path, required=True)
    b = ap.parse_args().build
    d = SITE / 'books' / 'm' / str(NO)
    (d / 'text').mkdir(parents=True, exist_ok=True)
    for f in [f'{SLUG}-print.pdf', f'{SLUG}-reader.pdf', 'cover.jpg', 'backcover.jpg']:
        shutil.copy(b / f, d / f)
    shutil.copy(b / 'text.html', d / 'text' / 'index.html')
    # 翻页器：照第 259 号的矢量翻页器，只换书名、PDF 与目录
    tpl = (SITE / 'books' / 'm' / '259' / 'read.html').read_text()
    toc = json.loads((b / 'toc-reader.json').read_text())
    import pymupdf as _p
    _n = len(_p.open(str(b / f'{SLUG}-reader.pdf')))
    toc['toc'] = [{'t': '封面', 'p': '', 'g': 1, 'l': 1}] + toc['toc'] + [{'t': '封底', 'p': '', 'g': _n, 'l': 1}]
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
    assert 'm/259' not in tpl and '谈尼采视角主义' not in tpl, [l for l in tpl.splitlines() if 'm/259' in l][:3]
    (d / 'read.html').write_text(tpl)
    # 书籍详情页
    import pymupdf
    pages = len(pymupdf.open(str(b / f'{SLUG}-print.pdf')))
    han = int(float(re.search(r'约 ([\d.]+) 万汉字', (HERE / 'front' / '00-前置.md').read_text())[1]) * 10000)
    shutil.copy(HERE / 'keypoints.json', d / 'keypoints.json')
    det = (HERE / 'detail.html').read_text()
    det = det.replace('__V__', V).replace('__PAGES__', str(pages)).replace('__WAN__', '%.0f' % (han / 10000))
    assert '__' not in det.replace('__agentproxy', '')
    (d / 'index.html').write_text(det)
    # 书目：先查重（铁律 14）
    cat_p = SITE / 'books' / 'catalog.json'
    data = json.loads(cat_p.read_text())
    books = data['books']
    old = [x for x in books if str(x.get('number')) == str(NO)]   # 重排再版：沿用首次上线时间
    pos = next((i for i, x in enumerate(books) if str(x.get('number')) == str(NO)), 0)
    books[:] = [x for x in books if str(x.get('number')) != str(NO)]
    assert not ISBN or not any((x.get('isbn') or '').replace('-', '') == ISBN.replace('-', '') for x in books), 'ISBN 重号'
    url = f'https://sdeuniverses.com/books/m/{NO}/'
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    entry = dict(id=f'm-{NO}', number=NO, title=T, subtitle=SUB, authors=['王德生', '秦衡峰'], category=(old[0].get('category') if old else 'ai'), articlesUrl=url + 'articles/01/',
                 description='关于生成式 AI 的讨论卡在「人 vs GPT」与「GPT 只是工具」两种叙事里，本书给出第三个起点：智能不是某个人或某个模型的属性，而是人、GPT 与具体场域在三体对话中生成的整体。上编用 SIO 本体论重写存在、GPT 与智能体；中编追踪人—GPT 关系从工具期、伙伴期到复合萌芽期的发生；下编落到教师—学生—GPT 的三体课堂与医生—病人—GPT 的三体对话医疗。三编七篇，全书公开。',
                 detailUrl=url, readUrl=url + 'read.html', readMode='full', readLabel='友好阅读 · 在线翻页',
                 pdfUrl=url + f'{SLUG}-reader.pdf?v={V}', printPdfUrl=url + f'{SLUG}-print.pdf?v={V}',
                 coverUrl=url + f'cover.jpg?v={V}', backcoverUrl=url + f'backcover.jpg?v={V}',
                 flipUrl=url + 'read.html', chapterUrl=url + 'text/', openness='full',
                 price='US$45.00', priceUsd=45, currency='USD', priceLabel='US$45.00', edition='2026年1月第1版',
                 pdfPages=pages, publishedAt=now, publisher='德麦国际出版社', publisherEnglish='Demai International Press')
    if ISBN:
        entry['isbn'] = ISBN.replace('-', '')
    if old:
        entry['publishedAt'] = old[0]['publishedAt']
    books.insert(pos, entry)
    data['updated'] = now[:10]
    cat_p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    # 智能体名字
    ag_p = SITE / 'books' / 'agents.json'
    ag = json.loads(ag_p.read_text())
    assert not any(v.get('name') == '新流' for k, v in ag['agents'].items() if k != str(NO))
    ag['agents'][str(NO)] = {
        'name': '新流', 'epithet': '汇进老河的那一股理念之流',
        'intro': '我从《人—GPT超级复合智能体》里来。带一堂你想重写的课、一次没说清的看病，或者你自己和 GPT 相处的一段经历来：我陪你看它停在工具期、伙伴期还是已经开始复合，也陪你拆这本书自己最经不起追问的地方。',
        'starts': {'read': '为什么说 GPT 是“发动机而不是河床”？意义三律各管什么？',
                   'apply': '我是一名老师，想把一堂课改成教师—学生—GPT 的三体课堂，第一步做什么？',
                   'cut': '“智能体 = 三律正常运行的整体”这个定义，最容易被什么反例击穿？',
                   'clash': '把这本书和克拉克的延展心智、哈钦斯的分布式认知撞一撞，真正的分歧落在哪里？'}}
    ag_p.write_text(json.dumps(ag, ensure_ascii=False, indent=1) + '\n')
    # 站点地图
    sm = SITE / 'sitemap.xml'; t = sm.read_text()
    for u in [url, url + 'text/', url + 'read.html']:
        if '<loc>%s</loc>' % u not in t:
            assert '</urlset>' in t
            t = t.replace('</urlset>', '<url><loc>%s</loc><lastmod>%s</lastmod></url>\n</urlset>' % (u, now[:10]))
    sm.write_text(t)
    print('published to', d, 'pages', pages, 'han', han)


if __name__ == '__main__':
    main()
