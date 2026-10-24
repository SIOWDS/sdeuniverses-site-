#!/usr/bin/env python3
"""第 418 号《用进身上的品牌》：书目 catalog.json、站点地图、/today/ 新书卡（读者页、学习包、智能体由 build_unit.py 与 m418 配置另出）。"""
import datetime, json, re, subprocess
from pathlib import Path
SITE = Path(__file__).resolve().parents[2] / 'public'
NO, V, SLUG = 418, '20261024a', 'brand-semiotics'
T, SUB = '用进身上的品牌', '溢价、直播与消费空虚的符号学'
ISBN = '979-8-90690-101-9'; AG = '上身'
DESC = '好品牌不是被记住，是被用进身上。全书把品牌当作一个符号，问它在理念、现实、自我三界怎样立住，再顺着溢价、直播带货、三种崩法、越买越空走一遍，最后给做品牌的人与买东西的人各备一张体检卡。第七编关于 AI 时代的部分是推演，带〔待核〕的数字不当事实。'
ZH = '被记住的是名字，被用进身上的是日子。品牌指向商品的真善美与内能动能势能，经三个“最少”纠缠发生；溢价是连接度的价格，直播把“零不顺”催成成交窗口，崩塌与越买越空各有可看的阈值。九编二十五章，附品牌三界体检十二问与消费者三问卡。含阅读、学习包与智能体“上身”。'
EN = 'What is remembered is a name; what is used into the body is a day. A brand, read as a symbol, points at a good’s truth, goodness and beauty and its internal, kinetic and potential energy, tied together by three “least” constraints. Premium is the price of connectedness; live commerce turns “zero friction” into a closing window. Nine parts, 25 chapters, with a learning pack and the book agent “Shangshen”.'
pages = int(re.search(r'Pages:\s+(\d+)', subprocess.run(['pdfinfo', str(SITE/f'books/m/{NO}/{SLUG}-print.pdf')], capture_output=True, text=True).stdout).group(1))
han = len(re.findall(r'[一-鿿]', (Path(__file__).parent/'chapters.md').read_text()))
cp = SITE/'books/catalog.json'; data = json.loads(cp.read_text()); books = data['books']
assert not any(str(b.get('number')) == str(NO) for b in books), 'number taken'
assert not any((b.get('isbn') or '').replace('-', '') == ISBN.replace('-', '') for b in books), 'ISBN dup'
d = ISBN.replace('-', ''); s = sum(int(c)*(1 if i % 2 == 0 else 3) for i, c in enumerate(d[:12])); assert (10-s % 10) % 10 == int(d[12]), 'check digit'
url = f'https://sdeuniverses.com/books/m/{NO}/'; now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
e = dict(id=f'm-{NO}', number=NO, title=T, subtitle=SUB, authors=['王德生'], category='core', description=DESC,
  detailUrl=url, readUrl=url+'read.html', readMode='full', readLabel='友好阅读 · 在线翻页',
  pdfUrl=url+f'{SLUG}-reader.pdf?v={V}', printPdfUrl=url+f'{SLUG}-print.pdf?v={V}',
  coverUrl=url+f'cover.jpg?v={V}', backcoverUrl=url+f'backcover.jpg?v={V}', flipUrl=url+'read.html', chapterUrl=url+'text/', openness='full',
  price='US$20', priceUsd=20, currency='USD', priceLabel='US$20', edition='2026年10月第1版', pdfPages=pages, publishedAt=now,
  publisher='德麦国际出版社', publisherEnglish='Demai International Press', isbn=d,
  agentUrl=url+'agent/dialogue.html', agentName=AG, agentLabel='智能问对 · '+AG,
  learnUrl=url+'agent/learning.html', learningUrl=url+'agent/learning.html', learnLabel='学习包 · 25个学习单元',
  learningPackUrl=url+f'downloads/{SLUG}-learning-v1.0.pdf',
  publicationUnit={'id': f'm-{NO}', 'type': 'reading-learning-dialogue', 'revision': '20261024-m418-unit-v1'})
books.insert(0, e); data['updated'] = now[:10]
cp.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
sm = SITE/'sitemap.xml'; t = sm.read_text()
for u in [url, url+'text/', url+'read.html']:
    if f'<loc>{u}</loc>' not in t:
        assert '</urlset>' in t; t = t.replace('</urlset>', f'<url><loc>{u}</loc><lastmod>{now[:10]}</lastmod></url>\n</urlset>')
sm.write_text(t)
tp = SITE/'today/index.html'; h = tp.read_text(); i = h.index('★ 新书 · 德麦国际专著第'); a0 = h.rindex('<a href="/books/m/', 0, i)
card = (f'<a href="/books/m/{NO}/" style="display:block;text-decoration:none;margin-bottom:16px"><div style="border:1px solid rgba(217,180,92,0.85);border-radius:3px;background:linear-gradient(135deg,rgba(14,31,49,0.98),rgba(9,18,30,0.98));padding:34px 32px;box-shadow:0 0 0 1px rgba(217,180,92,0.16) inset,0 0 40px rgba(217,180,92,0.10)">'
  f'<div class="zh-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ 新书 · 德麦国际专著第 {NO} 号 · 约 {han/10000:.0f} 万字 · {pages} 页 · US$ 20</div>'
  f'<div class="en-only" style="font-size:12.5px;letter-spacing:0.18em;color:#D9B45C;margin-bottom:14px">★ NEW BOOK · DEMAI MONOGRAPH No.{NO} · ~{han:,} CHARS · {pages} PP · US$ 20</div>'
  f'<h3 class="zh-only" style="color:#F1EBDC;font-size:25px;line-height:1.5;margin:0 0 14px">{T}——{SUB}</h3>'
  f'<h3 class="en-only" style="color:#F1EBDC;font-size:23px;line-height:1.5;margin:0 0 14px">Brands Worn Into the Body: A Semiotics of Premium, Live Commerce and Consumer Emptiness</h3>'
  f'<p class="zh-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">{ZH}</p>'
  f'<p class="en-only" style="color:#C9BCA6;font-size:15px;line-height:1.95;margin:0">{EN}</p></div></a>')
tp.write_text(h[:a0]+card+h[a0:]); print('ok', pages, han)
