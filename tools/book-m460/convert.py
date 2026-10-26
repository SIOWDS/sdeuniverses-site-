#!/usr/bin/env python3
"""第 460 号《虚幻的焦虑：AI 与我的文明》：把统稿后的分段稿（ch/00…09 与前后附件）转成 220/302 版式工具链（照第 520 号）的分卷稿。
只做格式转换，不动正文文字。
产物：front/00-前置.md、front/01-导论.md、parts/0N-第X编.md、back/11-结语.md、back/12-后置.md、book.md。
用法：python3 tools/book-m460/convert.py <统稿目录>
"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
S = Path(sys.argv[1])
CN = '一二三四五六'


def ends(text):
    """【带走的话】/【小账】/【编序】 → 520 版式。"""
    out, L, i = [], text.split('\n'), 0
    while i < len(L):
        s = L[i].strip()
        if s.startswith('【带走的话】'):
            out += ['> **带走的话**', '> ' + s[len('【带走的话】'):].strip(), '']; i += 1; continue
        if s.startswith('【小账】'):
            rows = []
            while i < len(L) and (L[i].strip().startswith('【小账】') or (not L[i].strip() and i + 1 < len(L) and L[i + 1].strip().startswith('【小账】'))):
                if L[i].strip():
                    rows.append(L[i].strip()[len('【小账】'):].strip())
                i += 1
            out += ['> **小账**'] + ['> ' + r for r in rows] + ['']; continue
        if s.startswith('【编序】'):
            out.append(s[len('【编序】'):].strip()); i += 1; continue
        out.append(L[i]); i += 1
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip() + '\n'


body = '\n\n'.join(Path(f).read_text() for f in sorted(S.glob('ch/[0-9][0-9]-*.md')))
body = ends(body)
# 按一级标题切块
blocks, cur = [], None
for line in body.split('\n'):
    if line.startswith('# '):
        cur = [line]; blocks.append(cur)
    elif cur is not None:
        cur.append(line)
B = {b[0][2:].split('　')[0]: '\n'.join(b).strip() + '\n' for b in blocks}
order = [b[0][2:].split('　')[0] for b in blocks]
print('blocks:', order)

front = (S / 'extra-front.md').read_text().strip() + '\n\n'
qy = B['前言'].replace('# 前言', '## 前言', 1)
front += qy + '\n' + (S / 'extra-guide.md').read_text().strip() + '\n'
(HERE / 'front').mkdir(exist_ok=True); (HERE / 'parts').mkdir(exist_ok=True); (HERE / 'back').mkdir(exist_ok=True)
(HERE / 'front/00-前置.md').write_text(front)
(HERE / 'front/01-导论.md').write_text(B['导论'])
for k in range(6):
    key = '第%s编' % CN[k]
    i = order.index(key)
    j = order.index('第%s编' % CN[k + 1]) if k < 5 else order.index('结语')
    chunk = '\n'.join(B[order[x]] for x in range(i, j))
    (HERE / ('parts/%02d-%s.md' % (k + 1, key))).write_text(chunk)
(HERE / 'back/11-结语.md').write_text(B['结语'])
eb = (S / 'extra-back.md').read_text()
bib, apx23 = eb.split('# 附录', 1)
apx23 = apx23.split('\n', 1)[1]
a1 = B['附录一'].replace('# 附录一', '## 附录一', 1)
a4 = B['附录四'].replace('# 附录四', '## 附录四', 1)
post = bib.strip() + '\n\n# 附录\n\n' + a1 + '\n' + apx23.strip() + '\n\n' + a4 + '\n' + (S / 'extra-houji.md').read_text().strip() + '\n'
(HERE / 'back/12-后置.md').write_text(post)
FILES = ['front/00-前置.md', 'front/01-导论.md'] + ['parts/%02d-第%s编.md' % (k + 1, CN[k]) for k in range(6)] + ['back/11-结语.md', 'back/12-后置.md']
book = '\n\n'.join((HERE / f).read_text().strip() for f in FILES) + '\n'
(HERE / 'book.md').write_text(book)
print('han', len(re.findall(r'[一-鿿]', book)), 'chapters', len(re.findall(r'^## 第 \d+ 章　', book, re.M)))
