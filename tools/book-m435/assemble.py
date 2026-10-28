#!/usr/bin/env python3
"""第 435 号：把统稿后的章节稿（scratchpad/chapters/*.md）装成 220/302 版式工具链的分卷稿。
front/00-前置.md 里「## 出版信息」与「## 导读」之间插入前言；按「# 第X编」切成 parts/0N-第X编.md；
附录接进 back/12-后置.md 的 __APPENDIX__ 处（生成 back/12-后置.md，模板为 back/12-后置.tpl.md）；最后拼出 book.md。
用法：python3 tools/book-m435/assemble.py <chapters 目录>
"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
src = Path(sys.argv[1])
txt = '\n\n'.join(p.read_text() for p in sorted(src.glob('[0-9][0-9]_*.md')))
txt = re.sub(r'\n{3,}', '\n\n', txt)
i_part = txt.index('\n# 第一编')
preface = txt[:i_part].strip()
assert preface.startswith('## 前言'), preface[:40]
i_app = txt.index('\n# 附录')
body, appx = txt[i_part:i_app], txt[i_app:].strip()
tpl = (HERE / 'front/00-前置.tpl.md').read_text()
k = tpl.index('## 导读')
(HERE / 'front/00-前置.md').write_text(tpl[:k] + preface + '\n\n' + tpl[k:])
parts = re.split(r'\n(?=# 第[一二三四五]编)', body)
parts = [p.strip() for p in parts if p.strip()]
assert len(parts) == 5, [p[:20] for p in parts]
CN = '一二三四五'
(HERE / 'parts').mkdir(exist_ok=True)
for n, p in enumerate(parts, 1):
    assert p.startswith('# 第%s编' % CN[n - 1])
    (HERE / 'parts' / ('%02d-第%s编.md' % (n, CN[n - 1]))).write_text(p + '\n')
back = (HERE / 'back/12-后置.tpl.md').read_text().replace('__APPENDIX__', appx)
(HERE / 'back/12-后置.md').write_text(back)
files = ['front/00-前置.md'] + ['parts/%02d-第%s编.md' % (n, CN[n - 1]) for n in range(1, 6)] + ['back/11-结语.md', 'back/12-后置.md']
(HERE / 'book.md').write_text('\n\n'.join((HERE / f).read_text().strip() for f in files) + '\n')
ch = re.findall(r'^## 第 ?(\d+) ?章　', (HERE / 'book.md').read_text(), re.M)
print('parts', len(parts), 'chapters', len(ch), ch[:3], ch[-3:])
