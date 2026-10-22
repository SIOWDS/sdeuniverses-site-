#!/usr/bin/env python3
"""把 /home/claude/book 下的章稿转成成书用的分篇稿：front/ parts/ back/。

章内转换：
  # 第N章　题         → ## 第 N 章　题（在篇文件里）
  ## 场景　题 / ## 引子　题 → 【场景】题
  ## 一、题 等其他二级标题 → ### ◆ 一、题
  > 本章涉及……（剧透）  → 〔剧透提示：……〕小字
  > **这一章的问题**／**带走的话**／**小账** 各自成块（前面补空行）
"""
import os
import re
from pathlib import Path

SRC = Path('/home/claude/book')
ROOT = Path(__file__).parent
PARTS = [
    ('01-第一篇', ['ch01.md', 'ch02.md', 'ch03.md']),
    ('02-第二篇', ['ch04.md', 'ch05.md', 'ch06.md', 'ch07.md', 'ch08.md']),
    ('03-第三篇', ['ch09.md', 'ch10.md', 'ch11.md', 'ch12.md', 'ch13.md', 'ch14.md']),
    ('04-第四篇', ['ch_p4a_戏曲.md', 'ch_p4b_长篇.md', 'ch_p4c_喜剧.md', 'ch_p4d_老去复活.md', 'ch_p4e_回写方向.md']),
    ('05-第五篇', ['ch_p5_新缺口.md']),
]
LABELS = ('> **这一章的问题**', '> **带走的话**', '> **小账**')


def body_of(text):
    """转换一章正文（不含首行标题）。"""
    out = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        ln = lines[i].rstrip()
        if ln.startswith('> 本章涉及') or ln.startswith('> 本章涉及以下'):
            # 剧透提示可能跨多行引用
            buf = [ln[2:].strip()]
            while i + 1 < len(lines) and lines[i + 1].startswith('>') and not lines[i + 1].startswith(LABELS):
                i += 1
                buf.append(lines[i][1:].strip())
            t = ''.join(buf).replace('〔', '（').replace('〕', '）')
            out += ['', '〔剧透提示：%s〕' % t, '']
        elif ln.startswith(LABELS):
            out += ['', ln]
        elif re.match(r'^## (场景|引子)　', ln):
            out += ['', '【场景】' + ln.split('　', 1)[1].strip(), '']
        elif ln.startswith('## '):
            out += ['', '### ◆ ' + ln[3:].strip(), '']
        elif ln.startswith('# '):
            pass
        else:
            out.append(ln)
        i += 1
    s = '\n'.join(out)
    s = re.sub(r'\n{3,}', '\n\n', s)
    s = re.sub(r'\*\* +(?=[\u4e00-\u9fff“（《])', '**', s)
    return s.strip() + '\n'


def chap(fn):
    t = (SRC / fn).read_text()
    first = t.splitlines()[0]
    m = re.match(r'^# 第\s*(\d+)\s*章[　 ]+(.*)$', first)
    assert m, (fn, first)
    return '## 第 %s 章　%s\n\n%s' % (m[1], m[2].strip(), body_of(t.split('\n', 1)[1]))


def main():
    for d in ('front', 'parts', 'back'):
        (ROOT / d).mkdir(exist_ok=True)
    allchars = 0
    intros = {}
    cur = None
    for ln in (ROOT / 'parts_intro.md').read_text().splitlines():
        if ln.startswith('# '):
            cur = ln[2:].strip(); intros[cur] = []
        elif ln.strip():
            intros[cur].append(ln.strip())
    titles = list(intros)
    for k, (name, files) in enumerate(PARTS):
        txt = '# %s\n\n%s\n\n' % (titles[k], '\n\n'.join(intros[titles[k]]))
        txt += '\n\n'.join(chap(f) for f in files)
        (ROOT / 'parts' / (name + '.md')).write_text(txt)
    # 引子
    t = (SRC / 'ch00_引子.md').read_text()
    (ROOT / 'front' / '01-引子.md').write_text(t.splitlines()[0] + '\n\n' + body_of(t.split('\n', 1)[1]))
    # 结语
    t = (SRC / 'ch99_结语.md').read_text()
    (ROOT / 'back' / '09-结语.md').write_text(t.splitlines()[0] + '\n\n' + body_of(t.split('\n', 1)[1]))
    # 后置
    back = (ROOT / 'back_src.md').read_text()
    (ROOT / 'back' / '10-后置.md').write_text(back)
    # 字数
    for f in ['ch00_引子.md', 'ch99_结语.md'] + [x for _, fs in PARTS for x in fs]:
        allchars += len(re.sub(r'[#>*\-\s]', '', (SRC / f).read_text()))
    wan = '%.0f' % (allchars / 10000)
    front = (ROOT / 'front_src.md').read_text()
    front = (front.replace('__WAN__', wan).replace('__NO__', '第 403 号')
             .replace('__ISBN__', '979-8-90690-952-7').replace('__PRICE__', 'US$23.00'))
    (ROOT / 'front' / '00-前置.md').write_text(front)
    (ROOT / 'book.md').write_text('\n\n'.join((ROOT / 'parts' / (n + '.md')).read_text() for n, _ in PARTS))
    print('chars', allchars, 'wan', wan)


if __name__ == '__main__':
    main()
