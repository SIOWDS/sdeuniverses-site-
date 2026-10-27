#!/usr/bin/env python3
"""第 473 号《还清了钱，没还清位置》（《愧》文学版）改稿、改名后重新上站：
替换封面、PDF、全文网页、翻页器（目录与书名），按新模板重写详情页，更新书目条目、/today/ 卡片与预留档里的书名和页数。
用法（仓库根目录）：python3 tools/book-m473/republish.py --build /home/claude/b473 --content tools/book-m473/content.json --ms tools/book-m473/book.md
之后跑 register.py、gen_config.py、build_unit_473s.py、learning_pdf.py、build_bookshelf.py。
"""
import argparse, html as _h, json, re, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa: E402
SITE = HERE.resolve().parents[1] / 'public'
D = SITE / 'books' / 'm' / str(M.NO)
OLD_TITLES = ['愧（文学版）', '愧']


def pages_of(pdf):
    o = subprocess.run(['pdfinfo', str(pdf)], capture_output=True, text=True).stdout
    return int(re.search(r'Pages:\s+(\d+)', o).group(1))


ap = argparse.ArgumentParser()
ap.add_argument('--build', type=Path, required=True); ap.add_argument('--content', type=Path, required=True); ap.add_argument('--ms', required=True)
A = ap.parse_args(); b = A.build; CT = json.loads(A.content.read_text()); AG = CT['agent']['name']
for f in (f'{M.SLUG}-print.pdf', f'{M.SLUG}-reader.pdf', 'cover.jpg', 'backcover.jpg'):
    shutil.copy(b / f, D / f)
shutil.copy(b / 'text.html', D / 'text' / 'index.html')
pages = pages_of(D / f'{M.SLUG}-print.pdf')
han = len(re.findall(r'[一-鿿]', Path(A.ms).read_text()))

# 翻页器：目录、偏移、书名
toc = json.loads((b / 'toc-reader.json').read_text())
rp = D / 'read.html'; t = rp.read_text()
cfg = json.loads(re.search(r'<script type="application/json" id="cfg">(.*?)</script>', t, re.S).group(1))
cfg['offset'] = toc['offset']; cfg['pdf'] = f'/books/m/{M.NO}/{M.SLUG}-reader.pdf?v={M.V}'
t = re.sub(r'<script type="application/json" id="cfg">.*?</script>', lambda m: '<script type="application/json" id="cfg">%s</script>' % json.dumps(cfg, ensure_ascii=False), t, flags=re.S)
t = re.sub(r'<script type="application/json" id="toc">.*?</script>', lambda m: '<script type="application/json" id="toc">%s</script>' % json.dumps(toc['toc'], ensure_ascii=False), t, flags=re.S)
t = t.replace('友好阅读 · 在线翻页 · 愧 |', f'友好阅读 · 在线翻页 · {M.TITLE} |').replace('《愧》在线翻页阅读', f'《{M.TITLE}》在线翻页阅读')
t = t.replace('<span class="ttl">愧</span>', f'<span class="ttl">{M.TITLE}</span>').replace("title: '愧',", f"title: '{M.TITLE}',").replace("msg('正在载入《愧》…');", f"msg('正在载入《{M.TITLE}》…');")
rp.write_text(t)

# 详情页：按模板重写，再把三位一体单元块放回
old = (D / 'index.html').read_text()
S0, E0 = '<!-- UNIT_START -->', '<!-- UNIT_END -->'
unit = re.search(re.escape(S0) + '.*?' + re.escape(E0), old, re.S)
det = (HERE / 'detail.html').read_text()
cards = ''.join('<div class="card"><b>%s</b><span>%s</span></div>' % (_h.escape(c['t']), _h.escape(c['x'])) for c in CT['loadBearing'])
det = (det.replace('__AGENT__', AG).replace('__V__', M.V).replace('__PAGES__', str(pages)).replace('__WAN__', '%.0f' % (han / 10000))
       .replace('__LINE__', _h.escape(CT['detailLine'])).replace('__INTRO__', _h.escape(CT['detailIntro'])).replace('__CARDS__', cards)
       .replace('__DESC_SHORT__', _h.escape(CT['detailLine'], quote=True)).replace('__PRICE_NUM__', '%.2f' % M.PRICE_USD).replace('__PRICE__', M.PRICE))
assert '__' not in det.replace('__agentproxy', '')
if unit:
    assert '<div class="btns">' in det
    det = det.replace('<div class="btns">', unit.group(0) + '<div class="btns">', 1)
(D / 'index.html').write_text(det)

# 书目条目
cp = SITE / 'books' / 'catalog.json'; data = json.loads(cp.read_text())
for e in data['books']:
    if e.get('number') == M.NO:
        e.update(title=M.TITLE, subtitle=M.SUBTITLE, titleEn=CT['titleEn'], description=CT['description'], pdfPages=pages,
                 pdfUrl=f'https://sdeuniverses.com/books/m/{M.NO}/{M.SLUG}-reader.pdf?v={M.V}',
                 printPdfUrl=f'https://sdeuniverses.com/books/m/{M.NO}/{M.SLUG}-print.pdf?v={M.V}',
                 coverUrl=f'https://sdeuniverses.com/books/m/{M.NO}/cover.jpg?v={M.V}', backcoverUrl=f'https://sdeuniverses.com/books/m/{M.NO}/backcover.jpg?v={M.V}')
cp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

# /today/ 卡片
tp = SITE / 'today' / 'index.html'; h = tp.read_text()
i = h.find('★ 新书 · 德麦国际专著第 %d 号' % M.NO)
if i >= 0:
    a0 = h.rindex('<a href="/books/m/', 0, i); a1 = h.index('</a>', i) + 4
    card = h[a0:a1]
    card2 = re.sub(r'(<h3 class="zh-only"[^>]*>).*?(</h3>)', lambda m: m.group(1) + M.TITLE + m.group(2), card, count=1, flags=re.S)
    card2 = re.sub(r'(<h3 class="en-only"[^>]*>).*?(</h3>)', lambda m: m.group(1) + CT['titleEn'] + m.group(2), card2, count=1, flags=re.S)
    card2 = re.sub(r'(<p class="zh-only"[^>]*>).*?(</p>)', lambda m: m.group(1) + CT['todayZh'] + m.group(2), card2, count=1, flags=re.S)
    card2 = re.sub(r'· \d+ 页 ·', '· %d 页 ·' % pages, card2).replace(' PP ·', ' PP ·')
    h = h[:a0] + card2 + h[a1:]
    tp.write_text(h)

# 预留档
rv = HERE.resolve().parents[1] / '.publish' / 'volume-reservations' / f'{M.NO}.json'
d = json.loads(rv.read_text()); d['title'] = M.TITLE; d['subtitle'] = M.SUBTITLE
d.setdefault('manuscript', {})['bodyHanzi'] = han
d['retitled'] = '2026-10-27 用户令：给文学版重生一个吸引人的书名；原题「愧——一次只走了两步的发生（文学版）」改为「%s——%s」。' % (M.TITLE, M.SUBTITLE)
rv.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
print('republished', M.NO, M.TITLE, 'pages', pages, 'han', han)
