#!/usr/bin/env python3
"""第 439 号《未来的知识经济主流产业——从母本到「我的……」》（王德生 著）：把定稿全稿 full.md
（YAML 头；# 前后件／编；## 第X章；### ◆ 节；行首【带走的话】【小账】【想一想】【编序】）
切成 220 版式工具链的分卷稿：front/00-前置.md、front/01-导论.md、parts/01–04（四编）、back/11-结语.md、back/12-后置.md，
并拼出 book.md（全文底本）与 book-unit.md（学习包取材：四编十二章）。只做格式转换，不改正文。
用法（本目录）：python3 convert.py /path/to/full.md
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
SRC = Path(sys.argv[1]).read_text(encoding='utf-8')
for d in ('front', 'parts', 'back'):
    (HERE / d).mkdir(exist_ok=True)

# 去 YAML 头
assert SRC.startswith('---\n')
yaml_end = SRC.index('\n---\n', 4)
body = SRC[yaml_end + 5:]


def markers(t):
    """行首标记 → 工具链的引用块。"""
    L = t.split('\n')
    out, i = [], 0
    while i < len(L):
        s = L[i]
        if s.startswith('【带走的话】'):
            out += ['', '> **带走的话**', '> ' + s[len('【带走的话】'):].strip(), '']
            i += 1
            continue
        if s.startswith('【小账】'):
            out += ['', '> **小账**']
            while i < len(L) and (L[i].startswith('【小账】') or not L[i].strip()):
                if L[i].strip():
                    out.append('> ' + L[i][len('【小账】'):].strip())
                i += 1
            out.append('')
            continue
        if s.startswith('【想一想】'):
            out += ['', '> **想一想**']
            first = s[len('【想一想】'):].strip()
            if first:
                out.append('> ' + first)
            i += 1
            # 其后到下一个标题前的各行：连续的【想一想】行与追加的问题段
            while i < len(L) and not L[i].startswith('#'):
                x = L[i]
                if x.startswith('【想一想】'):
                    out.append('> ' + x[len('【想一想】'):].strip())
                elif x.strip():   # 想一想之后到下一个标题前的各段，都是追加的问题（全书逐处核过）
                    out.append('> ' + x.strip())
                i += 1
            out.append('')
            continue
        if s.startswith('【编序】'):
            out.append(s[len('【编序】'):].strip())
            i += 1
            continue
        assert not re.match(r'^【(带走的话|小账|想一想|编序)', s)
        out.append(s)
        i += 1
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip() + '\n'


# 按一级标题切块
blocks = re.split(r'\n(?=# )', '\n' + body)
blocks = [b.strip('\n') for b in blocks if b.strip()]
heads = [b.split('\n', 1)[0] for b in blocks]
get = {h: b for h, b in zip(heads, blocks)}


def blk(prefix):
    hs = [h for h in heads if h.startswith(prefix)]
    assert len(hs) == 1, (prefix, hs)
    return get[hs[0]]


def demote(b):
    """# 标题 → ## 标题（前置各件在工具链里是 ## 分组）。"""
    return '#' + b


cp = ['## 出版信息', '', '| 项 | 内容 |', '|---|---|',
      '| 书名 | 《未来的知识经济主流产业——从母本到「我的……」》 |',
      '| 著者 | 王德生 |',
      '| 出版 | 德麦国际出版社（Demai International Press）· 新加坡 |',
      '| 编号 | 德麦国际专著第 439 号 |',
      '| ISBN | 979-8-90690-439-3 |',
      '| 定价 | US$20.00 |',
      '| 开本 | 170 mm × 240 mm |',
      '| 字数 | 约 20 万字 |',
      '| 版次 | 2026 年 10 月第 1 版 |', '']
for line in SRC[4:yaml_end].split('\n'):
    if line.startswith('statement: '):
        cp += [line[len('statement: '):].strip(), '']
cp += ['版权所有　侵权必究', '']

front = '\n'.join(cp) + '\n' + '\n\n'.join(markers(demote(blk(x))) for x in ('# 作者介绍', '# 前言', '# 导读'))
(HERE / 'front/00-前置.md').write_text(front, encoding='utf-8')
lun = markers(blk('# 导论'))
(HERE / 'front/01-导论.md').write_text(lun, encoding='utf-8')

PARTS = ['第一编', '第二编', '第三编', '第四编']
n_ch = 0
for k, p in enumerate(PARTS, 1):
    t = markers(blk('# ' + p))
    n_ch += len(re.findall(r'^## 第[一二三四五六七八九十]+章　', t, flags=re.M))
    (HERE / ('parts/%02d-%s.md' % (k, p))).write_text(t, encoding='utf-8')
assert n_ch == 12, n_ch

jy = markers(blk('# 结语'))
(HERE / 'back/11-结语.md').write_text(jy, encoding='utf-8')

back = [markers(blk('# 参考书目')), markers(get['# 附录'])]
for x in ('# 附录一', '# 附录二', '# 附录三'):
    back.append(markers(demote(blk(x))))
back.append(markers(blk('# 后记')))
(HERE / 'back/12-后置.md').write_text('\n\n'.join(back), encoding='utf-8')

# 全部一级标题都已收进去
used = {'# 作者介绍', '# 前言', '# 导读', '# 导论', '# 结语', '# 参考书目', '# 附录', '# 附录一', '# 附录二', '# 附录三', '# 后记'} | {'# ' + p for p in PARTS}
left = [h for h in heads if not any(h == u or h.startswith(u + '　') for u in used)]
assert not left, left

files = ['front/00-前置.md', 'front/01-导论.md'] + ['parts/%02d-%s.md' % (k, p) for k, p in enumerate(PARTS, 1)] + ['back/11-结语.md', 'back/12-后置.md']
(HERE / 'book.md').write_text('\n\n'.join((HERE / f).read_text(encoding='utf-8') for f in files), encoding='utf-8')
(HERE / 'book-unit.md').write_text('\n\n'.join((HERE / f).read_text(encoding='utf-8') for f in files[2:6]), encoding='utf-8')
print('ok chapters', n_ch)
