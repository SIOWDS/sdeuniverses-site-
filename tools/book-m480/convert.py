#!/usr/bin/env python3
"""第 480 号《感》：把排版用全稿 /home/claude/gan-book/gan-full.md（YAML＋导论＋上中下三篇九编五十四章＋结语＋附录四件）
转成 220/302 版式工具链（照第 520 号）的分卷稿，只供全文网页与学习包使用（PDF 已另行排好，不重排）。
只做格式转换，不动正文文字：章末【带走的话】【小账】【想一想】改成引用框；附录各件降一级标题；
三处「### ◆ X### ◆ X」重复标题行在网页稿里只留一个。
产物：front/00-前置.md、front/01-导论.md、parts/0N-第N编.md、back/11-结语.md、back/12-后置.md、book.md。
用法（仓库根目录）：python3 tools/book-m480/convert.py
"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa
src = (Path(M.SRC) / 'gan-full.md').read_text()
m = re.match(r'^---\n(.*?)\n---\n', src, re.S)
yaml, body = m[1], src[m.end():]
Y = {}
for line in yaml.splitlines():
    k, _, v = line.partition(':')
    Y.setdefault(k.strip(), []).append(v.strip())
body = re.sub(r'^(### ◆ [^\n]*?)### ◆ .*$', r'\1', body, flags=re.M)


def ends(t):
    out, L, i = [], t.split('\n'), 0
    while i < len(L):
        s = L[i].strip()
        mk = re.fullmatch(r'【(带走的话|小账|想一想)】', s)
        if mk:
            out.append('> **%s**' % mk[1]); i += 1
            while i < len(L) and L[i].strip():
                x = L[i].strip()
                if mk[1] == '带走的话':
                    x = re.sub(r'^\*\*(.*)\*\*$', r'\1', x)
                out.append('> ' + x); i += 1
            continue
        out.append(L[i]); i += 1
    return '\n'.join(out)


body = ends(body)
tops = re.split(r'\n(?=# )', '\n' + body)
tops = [t.strip('\n') for t in tops if t.strip()]
get = lambda pfx: [t for t in tops if t.startswith('# ' + pfx)]
author = get('作者介绍')[0].split('\n', 1)[1].strip()
lun = get('导论')[0]
jie = get('结语')[0]
fulu = [t for t in tops if t.startswith('# 附录')]
PIAN = {}
parts = []
cur_pian = None
for t in tops:
    h = t.split('\n', 1)[0]
    if re.match(r'^# [上中下]篇　', h):
        cur_pian = h[2:]; continue
    if re.match(r'^# 第[一二三四五六七八九]编　', h):
        parts.append((cur_pian, t)); cur_pian = None
assert len(parts) == 9

cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|',
      '| 书名 | 《%s——%s》 |' % (M.TITLE, M.SUBTITLE), '| 英文书名 | %s |' % M.TITLE_EN, '| 著者 | %s |' % M.AUTHOR,
      '| 执笔 | %s |' % Y['executor'][0], '| 出版 | 德麦国际出版社（Demai International Press）· 新加坡 |',
      '| 编号 | 德麦国际专著第 %d 号 |' % M.NO, '| ISBN | %s |' % M.ISBN, '| 定价 | %s |' % M.PRICE,
      '| 开本 | 170 mm × 240 mm |', '| 字数 | %s |' % Y['words'][0], '| 版次 | %s |' % Y['edition'][0], '| 完稿 | %s |' % Y['finished'][0], '']
for s in Y['statement']:
    cp += [s, '']
cp += [Y['copyright'][0], '', '## 作者介绍', '', author, '']
out = HERE
(out / 'front').mkdir(exist_ok=True); (out / 'parts').mkdir(exist_ok=True); (out / 'back').mkdir(exist_ok=True)
(out / 'front/00-前置.md').write_text('\n'.join(cp) + '\n')
(out / 'front/01-导论.md').write_text(lun + '\n')
CN = '一二三四五六七八九'
for k, (pian, t) in enumerate(parts, 1):
    head, _, rest = t.partition('\n')
    if pian:
        rest = '\n**%s**\n' % pian + rest
    (out / ('parts/%02d-第%s编.md' % (k, CN[k - 1]))).write_text(head + '\n' + rest.rstrip() + '\n')
(out / 'back/11-结语.md').write_text(jie + '\n')
back = []
for t in fulu:
    t = re.sub(r'^## ', '### ', t, flags=re.M)
    t = re.sub(r'^# (附录[一二三四])', r'## \1', t, flags=re.M)
    back.append(t)
(out / 'back/12-后置.md').write_text('\n\n'.join(back) + '\n')
book = '\n\n'.join([(out / 'front/00-前置.md').read_text(), lun] + [p for _, p in parts] + [jie] + fulu)
(out / 'book.md').write_text(book + '\n')
han = len(re.findall(r'[一-鿿]', src))
print('ok parts', len(parts), 'appendix', len(fulu), 'han(full)', han)
