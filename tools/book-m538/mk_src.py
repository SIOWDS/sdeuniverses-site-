#!/usr/bin/env python3
"""第 538 号《被照顾得很好之后》（陈晓艳 著）：把三审统稿后的分章稿装成 convert.py 认的 src/。
只改标题层级与章题写法，不动正文文字：
  删去章题下的「*副题*」行；节「## 一、T」→「## T」（convert 重新编号）；小节「### （一）T」→「#### （一）T」；
  各编首章前插入编题与编序；各章末尾接上原论文所列参考书目（refs.json，取自原论文 PDF，未增删条目）。
用法：python3 tools/book-m538/mk_src.py <统稿目录 chapters/> <refs.json>
统稿目录里应有：ch_preface.md、ch00_intro.md、part1-3.md、ch01-09.md、ch10_conclusion.md、appendix.md。
"""
import json, re, sys
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / 'src'
D = Path(sys.argv[1])
REFS = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
PART_AT = {1: 'part1.md', 4: 'part2.md', 7: 'part3.md'}


def strip_sub(lines):
    """删去紧跟一级标题的 *副题* 行。"""
    out, prev = [], ''
    for l in lines:
        if re.match(r'^\*[^*].*\*$', l.strip()) and prev.startswith('# '):
            continue
        if l.strip():
            prev = l
        out.append(l)
    return out


def chapter(i):
    lines = strip_sub((D / ('ch%02d.md' % i)).read_text(encoding='utf-8').splitlines())
    out = []
    for l in lines:
        if l.startswith('## '):
            out.append('## ' + re.sub(r'^[一二三四五六七八九十]+、\s*', '', l[3:].strip()))
        elif l.startswith('### '):
            out.append('#### ' + l[4:].strip())
        else:
            out.append(l)
    body = '\n'.join(out).strip() + '\n'
    refs = REFS.get('ch%02d' % i)
    if refs:
        body += '\n## 本章参考文献\n\n' + '\n\n'.join(refs) + '\n'
    if i in PART_AT:
        p = (D / PART_AT[i]).read_text(encoding='utf-8').strip()
        head, _, intro = p.partition('\n')
        body = '## ' + head.lstrip('# ').strip() + '\n\n' + intro.strip() + '\n\n' + body
    return body


def plain(name, src):
    t = (D / src).read_text(encoding='utf-8')
    (SRC / name).write_text('\n'.join(strip_sub(t.splitlines())).strip() + '\n', encoding='utf-8')


def main():
    SRC.mkdir(exist_ok=True)
    plain('qianyan.md', 'ch_preface.md')
    plain('daolun.md', 'ch00_intro.md')
    for i in range(1, 10):
        (SRC / ('ch%02d.md' % i)).write_text(chapter(i), encoding='utf-8')
    plain('jieyu.md', 'ch10_conclusion.md')
    plain('fulu1.md', 'appendix.md')
    print('ok', sorted(p.name for p in SRC.glob('*.md')))


if __name__ == '__main__':
    main()
