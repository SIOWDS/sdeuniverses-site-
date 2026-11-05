#!/usr/bin/env python3
"""第 586 号《你没交给企业的那一半》：把三审定稿的分章稿装成 convert.py 认的 src/。原样复制，不动文字。
用法：python3 tools/book-m586/mk_src.py <定稿目录>"""
import sys
from pathlib import Path
B = Path(sys.argv[1]); OUT = Path(__file__).parent / 'src'
OUT.mkdir(exist_ok=True)
for f in OUT.glob('*.md'): f.unlink()
names = {'_作者简介.md': 'zuozhe.md', '_前言.md': 'qianyan.md', 'R00_导论.md': 'daolun.md',
         'R99_结语.md': 'jieyu.md', 'R_参考文献.md': 'cankao.md'}
names.update({'R%02d.md' % i: 'ch%02d.md' % i for i in range(1, 15)})
for a, b in names.items():
    (OUT / b).write_text((B / a).read_text(encoding='utf-8').strip() + '\n', encoding='utf-8')
print('src', sorted(p.name for p in OUT.glob('*.md')))
