#!/usr/bin/env python3
"""第 468 号《一看就不读》合成器：把 /home/claude/468-yikanjiubudu/chapters/ 下各稿合成 src/full.md，
并把正文里带〔待核〕的句子收进 待核总表.md。
稿件约定（质检后）：每章一级标题「# 第N章　题」「# 序章　题」「# 前言　题」「# 结语　题」「# 附录一　题」，
节为「## N.M 题」；稿末写手附录已由质检剪到 checks/。保险起见，仍按尾标切掉残留附注。
合成时在第 1、5、9、12 章前插入四编标题。
用法：python3 synth_full.py
"""
import re
from pathlib import Path
HERE = Path(__file__).parent
SRC = Path('/home/claude/468-yikanjiubudu/chapters')
ORDER = ['前言.md', '00-序章.md'] + ['%02d.md' % i for i in range(1, 14)] + ['14-结语附录.md']
PARTS = {1: ('上编', '发生：意义三律在人与 AI 之间转起来'),
         5: ('中编', '显露：真善美先对复合体亮，再对读者亮'),
         9: ('下编', '增量：复合体和读者的 E 都丰富了'),
         12: ('终编', '判据与承担')}
TAIL = re.compile(r'^(#+ ?|\*\*)?(〔待核〕清单|写手附录|校准题|附：|附件|新造案例清单|本稿新造|自查表|拿不准|待核清单)')


def norm(t):
    m = re.match(r'^(第\d+章|前言|序章|结语|附录[一二三四五六七八九十])[\s　：:]*(.*)$', t.strip())
    return ('%s　%s' % (m[1], m[2])).strip('　') if m else t.strip()


def main():
    book, todo = [], []
    for name in ORDER:
        lines = (SRC / name).read_text(encoding='utf-8').splitlines()
        k = len(lines)
        for i, l in enumerate(lines):
            if i > 3 and TAIL.match(l.strip()):
                k = i; break
        body = lines[:k]
        while body and body[-1].strip() in ('', '---'):
            body.pop()
        for l in body:
            if l.startswith('# '):
                t = norm(l[2:])
                m = re.match(r'^第(\d+)章', t)
                if m and int(m[1]) in PARTS:
                    book += ['# %s　%s' % PARTS[int(m[1])], '']
                book += ['# ' + t, '']
            else:
                book.append(l)
                if '〔待核' in l:
                    todo.append((name, re.sub(r'\s+', ' ', l.strip())[:220]))
        book.append('')
    (HERE / 'src').mkdir(exist_ok=True)
    txt = re.sub(r'\n{3,}', '\n\n', '\n'.join(book)) + '\n'
    (HERE / 'src/full.md').write_text(txt, encoding='utf-8')
    L = ['# 第 468 号 待核总表', '', '正文中带〔待核〕标记的句子（统稿时收集）。逐条核过即删标记并在此销号。', '']
    cur = None
    for n, s in todo:
        if n != cur:
            L += ['', '## ' + n, '']; cur = n
        L.append('- ' + s)
    (HERE / '待核总表.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    print('full.md written;', len(todo), 'lines with 〔待核〕')


if __name__ == '__main__':
    main()
