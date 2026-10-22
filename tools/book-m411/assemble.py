#!/usr/bin/env python3
"""第 411 号：把统稿 v2 的分章稿装成 220/302 版式工具链的分卷稿。
用法：python3 tools/book-m411/assemble.py /home/claude/v2
输入：<v2>/parts/ch00.md（导论）、ch01—ch23.md、ch24.md（结语）、<v2>/part-intros.md（五篇导语）、<v2>/front.md、<v2>/back.md
输出：front/00-前置.md、front/01-导论.md、parts/0N-第N篇.md、back/09-结语.md、back/10-后置.md、book.md（全稿，学习单元用）
"""
import re, sys
from pathlib import Path

HERE = Path(__file__).parent
V2 = Path(sys.argv[1])
CN = ['一', '二', '三', '四', '五']
SPLIT = [range(1, 6), range(6, 11), range(11, 17), range(17, 22), range(22, 24)]


def rd(p):
    return (V2 / p).read_text(encoding='utf-8').strip() + '\n'


def clean(t):
    t = re.sub(r'\n{3,}', '\n\n', t)
    t = re.sub(r'^\s*---\s*$', '', t, flags=re.M)
    return t.strip() + '\n'


intros = []
for blk in rd('part-intros.md').split('@@PART')[1:]:
    ls = [x.strip() for x in blk.strip().splitlines() if x.strip()]
    title = ls[0].replace('第一篇　', '').replace('第二篇　', '').replace('第三篇　', '').replace('第四篇　', '').replace('第五篇　', '')
    sub = ls[1].replace('副题：', '')
    intros.append((title, sub, ls[2:]))
assert len(intros) == 5

# 导论
lun = clean(rd('parts/ch00.md'))
assert lun.startswith('# 导论　'), lun[:40]
(HERE / 'front').mkdir(exist_ok=True); (HERE / 'parts').mkdir(exist_ok=True); (HERE / 'back').mkdir(exist_ok=True)
(HERE / 'front/01-导论.md').write_text(lun, encoding='utf-8')

book = [lun]
for k, rng in enumerate(SPLIT):
    title, sub, body = intros[k]
    head = '# 第%s篇　%s：%s\n\n' % (CN[k], title, sub) + '\n\n'.join(body) + '\n'
    chs = []
    for n in rng:
        t = clean(rd('parts/ch%02d.md' % n))
        m = re.match(r'## 第 (\d+) 章　', t)
        assert m and int(m.group(1)) == n, ('chapter heading', n, t[:40])
        assert '## 本章小结' not in t, ('本章小结 still present', n)
        chs.append(t)
    part = head + '\n' + '\n'.join(chs)
    (HERE / ('parts/%02d-第%s篇.md' % (k + 1, CN[k]))).write_text(part, encoding='utf-8')
    book.append(part)

jy = clean(rd('parts/ch24.md'))
assert jy.startswith('# 结语　'), jy[:40]
(HERE / 'back/09-结语.md').write_text(jy, encoding='utf-8')
book.append(jy)

(HERE / 'front/00-前置.md').write_text(clean(rd('front.md')), encoding='utf-8')
(HERE / 'back/10-后置.md').write_text(clean(rd('back.md')), encoding='utf-8')
(HERE / 'book.md').write_text('\n\n'.join(book), encoding='utf-8')
han = len(re.findall(r'[一-鿿]', '\n'.join(book) + rd('front.md') + rd('back.md')))
print('assembled; 汉字', han)
