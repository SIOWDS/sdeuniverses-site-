#!/usr/bin/env python3
"""第 527 号修订版就地更新：PDF、封面、全文网页、翻页器目录、详情页、书目条目；之后再跑 build_unit_527.py 与 register.py。
用法（仓库根目录）：python3 tools/book-m527/update.py --build /home/claude/b527
"""
import argparse, json, re, shutil, subprocess, html as _h, sys
from pathlib import Path
HERE = Path(__file__).parent; sys.path.insert(0, str(HERE))
import meta as M
SITE = HERE.resolve().parents[1] / 'public'; NO, V, SLUG = M.NO, M.V, M.SLUG
ap = argparse.ArgumentParser(); ap.add_argument('--build', type=Path, required=True); b = ap.parse_args().build
d = SITE / 'books' / 'm' / str(NO); assert d.exists()
for f in (f'{SLUG}-print.pdf', f'{SLUG}-reader.pdf', 'cover.jpg', 'backcover.jpg'): shutil.copy(b / f, d / f)
shutil.copy(b / 'text.html', d / 'text' / 'index.html')
rh = (d / 'read.html').read_text(); toc = json.loads((b / 'toc-reader.json').read_text())
cfg = {'pdf': f'/books/m/{NO}/{SLUG}-reader.pdf?v={V}', 'key': f'books-m-{NO}-v1', 'offset': toc['offset']}
rh = re.sub(r'<script type="application/json" id="cfg">.*?</script>', lambda m: '<script type="application/json" id="cfg">%s</script>' % json.dumps(cfg, ensure_ascii=False), rh, flags=re.S)
rh = re.sub(r'<script type="application/json" id="toc">.*?</script>', lambda m: '<script type="application/json" id="toc">%s</script>' % json.dumps(toc['toc'], ensure_ascii=False), rh, flags=re.S)
(d / 'read.html').write_text(rh)
CT = json.loads((HERE / 'content.json').read_text()); ms = (HERE / 'book.md').read_text()
han = len(re.findall(r'[一-鿿]', ms))
pages = int(re.search(r'Pages:\s+(\d+)', subprocess.run(['pdfinfo', str(b / f'{SLUG}-print.pdf')], capture_output=True, text=True).stdout).group(1))
cards = ''.join('<div class="card"><b>%s</b><span>%s</span></div>' % (_h.escape(c['t']), _h.escape(c['x'])) for c in CT['loadBearing'])
det = (HERE / 'detail.html').read_text()
det = (det.replace('__AGENT__', CT['agent']['name']).replace('__V__', V).replace('__PAGES__', str(pages)).replace('__WAN__', '%.0f' % (han / 10000))
       .replace('__LINE__', _h.escape(CT['detailLine'])).replace('__INTRO__', _h.escape(CT['detailIntro'])).replace('__CARDS__', cards)
       .replace('__DESC_SHORT__', _h.escape(CT['detailLine'], quote=True)).replace('__PRICE_NUM__', '%.2f' % M.PRICE_USD).replace('__PRICE__', M.PRICE))
def _struct():
    li = ['<li><b>前置</b>　出版信息 · 作者介绍 · 导论　%s</li>' % _h.escape((HERE / 'front/01-导论.md').read_text().split('\n', 1)[0].split('　', 1)[1])]
    for f in sorted((HERE / 'parts').glob('0*.md')):
        tx = f.read_text(); pt = tx.split('\n', 1)[0].lstrip('# ').strip()
        chs = re.findall(r'^## (第(\d+)章)　(.*)$', tx, re.M)
        li.append('<li><b>%s</b>（第 %s—%s 章）<span class="chs">%s</span></li>' % (_h.escape(pt), chs[0][1], chs[-1][1], ' · '.join('%s %s' % (a, _h.escape(c)) for a, _, c in chs)))
    jy = (HERE / 'back/11-结语.md').read_text().split('\n', 1)[0].lstrip('# ').strip()
    li.append('<li><b>后置</b>　%s · 参考书目 · 附录一至六 · 后记</li>' % _h.escape(jy))
    return '<ol class="vols">\n%s\n</ol>' % '\n'.join(li)
det = det.replace('__STRUCT__', _struct())
assert '__' not in det.replace('__agentproxy', '')
(d / 'index.html').write_text(det)
cp = SITE / 'books' / 'catalog.json'; data = json.loads(cp.read_text())
e = [x for x in data['books'] if str(x.get('number')) == str(NO)][0]
url = f'https://sdeuniverses.com/books/m/{NO}/'
e.update(pdfUrl=url + f'{SLUG}-reader.pdf?v={V}', printPdfUrl=url + f'{SLUG}-print.pdf?v={V}', coverUrl=url + f'cover.jpg?v={V}',
         backcoverUrl=url + f'cover.jpg?v={V}'.replace('cover.jpg', 'backcover.jpg'), pdfPages=pages, edition=M.EDITION, description=CT['description'])
cp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
print('updated', d, 'pages', pages, 'han', han)
