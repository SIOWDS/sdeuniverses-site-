#!/usr/bin/env python3
"""第 263 号《教育的新使命》：把单文件全稿 docs/papers/教育的新使命-全稿.md 拆成 build.py 要的分篇稿。

全稿是唯一的底本；改文字只改全稿，再跑本脚本重新生成 front/、parts/、back/。
转换只做格式：一级标题降为二级（前置），【编序】→编序段落，【带走的话】【小账】【想一想】→引用块。
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT.parents[1] / 'docs' / 'papers' / '教育的新使命-全稿.md'

PUB = [('书名', '教育的新使命——从「一个人全包」到「人与 AI 分层分工」'), ('著者', '王德生'),
       ('执笔', '王德生立题、口述承重命题与裁定；AI（Claude）协作执笔、统稿与版式校订'),
       ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 263 号'),
       ('ISBN', '979-8-90690-248-1'), ('定价', 'US$20.00'), ('开本', '170 mm × 240 mm（16 开）'),
       ('字数', '约 23 万字'), ('版次', '2026 年 10 月第 1 版'), ('完稿', '2026 年 10 月 1 日（系列风格统稿版）')]


def endparts(lines):
    """把章尾的【…】行转成引用块。"""
    out, i = [], 0
    while i < len(lines):
        l = lines[i]
        m = re.match(r'^【(带走的话|小账|想一想|编序)】(.*)$', l)
        if not m:
            out.append(l); i += 1; continue
        kind, text = m[1], m[2].strip()
        if kind == '编序':
            out += [text, '', '---', '']; i += 1; continue
        items = [text]
        i += 1
        while kind != '带走的话' and i < len(lines) and lines[i].startswith('【%s】' % kind):
            items.append(lines[i][len(kind) + 2:].strip()); i += 1
        out.append('')
        out.append('> **%s**' % kind)
        for it in items:
            out += ['>', '> ' + it]
        out.append('')
    return out


def spaced_lines(text):
    """原稿一行一段；build.py 会把相邻普通行并成一段，所以普通行之间补空行。"""
    out = []
    def kind(l):
        if not l.strip(): return 'blank'
        if l.startswith('|'): return 'table'
        if l.startswith('>'): return 'quote'
        if re.match(r'^(- |\d+\. )', l): return 'list'
        return 'p'
    lines = text.split('\n')
    for j, l in enumerate(lines):
        out.append(l)
        nxt = lines[j + 1] if j + 1 < len(lines) else ''
        k, kn = kind(l), kind(nxt)
        if k != 'blank' and kn != 'blank' and (k == 'p' or kn == 'p' or k != kn):
            out.append('')
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out))


def main():
    t = SRC.read_text()
    t = re.sub(r'^---\n.*?\n---\n', '', t, count=1, flags=re.S)  # 去掉 YAML 头
    L = t.split('\n')
    # 按一级标题切块
    blocks, cur = [], None
    for l in L:
        if l.startswith('# '):
            cur = [l[2:].strip(), []]; blocks.append(cur)
        elif cur is not None:
            cur[1].append(l)
    def body(b):
        return '\n'.join(endparts(b[1])).strip('\n')
    # 前置
    statements = [m for m in re.findall(r'^statement: (.*)$', SRC.read_text(), flags=re.M)]
    fr = ['## 出版信息', '', '| 字段 | 内容 |', '|---|---|'] + ['| %s | %s |' % kv for kv in PUB] + ['']
    for s in statements:
        fr += [s, '']
    fr += ['版权所有　侵权必究', '', '---', '']
    i = 0
    while not blocks[i][0].startswith('第一篇'):
        fr += ['## ' + blocks[i][0], '', body(blocks[i]), '', '---', '']
        i += 1
    (ROOT / 'front').mkdir(exist_ok=True)
    (ROOT / 'front' / '00-前置.md').write_text(spaced_lines('\n'.join(fr).rstrip('-\n')) + '\n')
    # 各篇
    (ROOT / 'parts').mkdir(exist_ok=True)
    for old in (ROOT / 'parts').glob('*.md'):
        old.unlink()
    n = 0
    while not blocks[i][0].startswith('结语'):
        n += 1
        (ROOT / 'parts' / ('%02d-%s.md' % (n, blocks[i][0].split('　')[0]))).write_text(
            spaced_lines('# %s\n\n%s\n' % (blocks[i][0], body(blocks[i]))))
        i += 1
    # 结语
    (ROOT / 'back').mkdir(exist_ok=True)
    (ROOT / 'back' / '09-结语.md').write_text(spaced_lines('# %s\n\n%s\n' % (blocks[i][0], body(blocks[i]))))
    i += 1
    # 后置：参考书目、附录（附录一……降为二级）、后记
    bk = []
    for title, b in blocks[i:]:
        txt = '\n'.join(endparts(b)).strip('\n')
        if title == '参考书目':
            txt = re.sub(r'^### ◆ ', '## ', txt, flags=re.M)
            bk += ['# 参考书目', '', txt, '']
        elif title.startswith('附录') and title != '附录':
            bk += ['## ' + title, '', txt, '']
        else:
            bk += ['# ' + title, '', txt, '']
    (ROOT / 'back' / '10-后置.md').write_text(spaced_lines('\n'.join(bk)))
    print('parts', n, 'blocks', len(blocks))


if __name__ == '__main__':
    main()
