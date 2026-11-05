#!/usr/bin/env python3
"""第 583 号：把定稿 parts/*.md 装成 convert.py 认的 src/。只改标题的空格，不动正文文字。"""
import re, sys
from pathlib import Path
P = Path(sys.argv[1] if len(sys.argv) > 1 else '/home/claude/involution-book/parts')
OUT = Path(__file__).parent / 'src'
OUT.mkdir(exist_ok=True)
for f in OUT.glob('*.md'):
    f.unlink()
def head(s):
    s = re.sub(r'^# (第[一二三四五六七八九十]+编) (.*)$', r'## \1　\2', s, flags=re.M)
    s = re.sub(r'^# (第\d+章) (.*)$', r'# \1　\2', s, flags=re.M)
    s = re.sub(r'^# (导论|结语|附录[一二三四五六七八九十]+) (.*)$', r'# \1　\2', s, flags=re.M)
    return s.strip() + '\n'
(OUT / 'qianyan.md').write_text(head((P / '00_前言.md').read_text()))
(OUT / 'daolun.md').write_text(head((P / '00_导论.md').read_text()))
(OUT / 'jieyu.md').write_text(head((P / 'ch46_结语.md').read_text()))
for i in range(1, 46):
    (OUT / ('ch%02d.md' % i)).write_text(head((P / ('ch%02d.md' % i)).read_text()))
fu = head((P / 'ch47_附录.md').read_text())
a, b = re.split(r'(?=^# 附录二)', fu, flags=re.M)
(OUT / 'fulu1.md').write_text(a.strip() + '\n')
(OUT / 'fulu2.md').write_text(b.strip() + '\n')
print('assembled', len(list(OUT.glob('*.md'))))
