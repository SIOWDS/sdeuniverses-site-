#!/usr/bin/env python3
"""第 563 号《开端发生学》：detail.html → public/books/m/563/index.html（由第 561 号 publish.py 的详情页部分抽出，不碰书目、站点地图、今日页）。
并补 read.html 目录的封面、出版信息、封底条目与导论、结语的副题。
用法（仓库根目录）：python3 tools/book-m563/fill_index.py
"""
import html as _h
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa: E402
REPO = HERE.resolve().parents[1]
D = REPO / ('public/books/m/%d' % M.NO)
CT = json.loads((HERE / 'content.json').read_text(encoding='utf-8'))


def pages_of(pdf):
    o = subprocess.run(['pdfinfo', str(pdf)], capture_output=True, text=True).stdout
    return int(re.search(r'Pages:\s+(\d+)', o).group(1))


han = M.body_han(HERE)
pages = pages_of(D / ('%s-print.pdf' % M.SLUG))
rpages = pages_of(D / ('%s-reader.pdf' % M.SLUG))
det = (HERE / 'detail.html').read_text(encoding='utf-8')
cards = ''.join('<div class="card"><b>%s</b><span>%s</span></div>' % (_h.escape(c['t']), _h.escape(c['x'])) for c in CT['loadBearing'])
det = (det.replace('__AGENT__', CT['agent']['name']).replace('__V__', M.V).replace('__PAGES__', str(pages)).replace('__WAN__', '32')
       .replace('__LINE__', _h.escape(CT['detailLine'])).replace('__INTRO__', _h.escape(CT['detailIntro'])).replace('__CARDS__', cards)
       .replace('__DESC_SHORT__', _h.escape(CT['detailLine'], quote=True)).replace('__PRICE_NUM__', '%.2f' % M.PRICE_USD).replace('__PRICE__', M.PRICE))


def _struct():
    li = ['<li><b>前置</b>　出版信息 · 作者介绍 · 前言 · 导论</li>']
    for f in sorted((HERE / 'parts').glob('*.md')):
        tx = f.read_text(encoding='utf-8')
        pt = tx.split('\n', 1)[0].lstrip('# ').strip()
        chs = re.findall(r'^## 第 ?(\d+) ?章　(.*)$', tx, re.M)
        li.append('<li><b>%s</b>（第 %s—%s 章）<span class="chs">%s</span></li>' % (
            _h.escape(pt), chs[0][0], chs[-1][0], ' · '.join('第%s章 %s' % (n, _h.escape(c)) for n, c in chs)))
    li.append('<li><b>后置</b>　结语 · 参考书目</li>')
    return '<ol class="vols">\n%s\n</ol>' % '\n'.join(li)


det = det.replace('__STRUCT__', _struct())
assert '__' not in det
(D / 'index.html').write_text(det, encoding='utf-8')

# read.html 目录
rp = D / 'read.html'
rd = rp.read_text(encoding='utf-8')
m_ = re.search(r'(<script type="application/json" id="toc">)(.*?)(</script>)', rd, flags=re.S)
tl = json.loads(m_[2].replace('<\\/', '</'))
if tl[0].get('t') != '封面':
    tl.insert(0, {'t': '封面', 'p': '', 'g': 1, 'l': 1})
    tl.insert(1, {'t': '出版信息', 'p': '', 'g': 4, 'l': 1})
if tl[-1].get('t') != '封底':
    tl.append({'t': '封底', 'p': '', 'g': rpages, 'l': 1})
for e in tl:
    if e['t'] == '导论':
        e['t'] = '导论 每一个开头，都是前面很多次的结尾'
    if e['t'] == '结语':
        e['t'] = '结语 写给下一个开端：本书自己的 0→1'
rp.write_text(rd[:m_.start(2)] + json.dumps(tl, ensure_ascii=False).replace('</', '<\\/') + rd[m_.end(2):], encoding='utf-8')
print('index ok; print pages', pages, 'reader pages', rpages, 'toc', len(tl))
