#!/usr/bin/env python3
"""第 364 号《AI赋能了谁？》：把 /home/claude/book/v2 下的统稿稿转成成书用的分编稿：front/ parts/ back/。
（由第 403 号 convert.py 改来；章式照第 302 号。）

章内转换：
  # 第N章　题           → ## 第 N 章　题（在编文件里）
  ## 场景　题           → 【场景】题
  ## 一、题 等二级标题   → ### ◆ 一、题
  > **这一章的问题**／**带走的话**／**小账** 各自成块
"""
import re
import sys
from pathlib import Path

SRC = Path('/home/claude/book/v2')
ROOT = Path(__file__).parent
NO, ISBN, PRICE = 364, '979-8-90690-975-6', 'US$23.00'
PARTS = [
    ('01-第一编', range(1, 7)),
    ('02-第二编', range(7, 25)),
    ('03-第三编', range(25, 29)),
    ('04-第四编', range(29, 35)),
    ('05-第五编', range(35, 39)),
]
LABELS = ('> **这一章的问题**', '> **带走的话**', '> **小账**')


def src(n):
    fs = sorted(SRC.glob('%02d_*.md' % n))
    assert len(fs) == 1, (n, fs)
    return fs[0]


def body_of(text):
    out = []
    for ln in text.splitlines():
        ln = ln.rstrip()
        if ln.startswith(LABELS):
            out += ['', ln]
        elif re.match(r'^## 场景[　 ]', ln):
            out += ['', '【场景】' + re.split(r'[　 ]', ln[3:].strip(), 1)[-1].strip(), '']
        elif ln.startswith('## '):
            out += ['', '### ◆ ' + ln[3:].strip(), '']
        elif ln.startswith('# '):
            pass
        else:
            out.append(ln)
    s = '\n'.join(out)
    s = re.sub(r'\n{3,}', '\n\n', s)
    s = re.sub(r'\*\* +(?=[一-鿿“（《])', '**', s)
    return s.strip() + '\n'


def chap(n):
    t = src(n).read_text()
    first = t.splitlines()[0]
    m = re.match(r'^# 第\s*(\d+)\s*章[　 ]+(.*)$', first)
    assert m and int(m[1]) == n, (n, first)
    return '## 第 %s 章　%s\n\n%s' % (m[1], m[2].strip(), body_of(t.split('\n', 1)[1]))


def main():
    for d in ('front', 'parts', 'back'):
        (ROOT / d).mkdir(exist_ok=True)
    intros, cur = {}, None
    for ln in (ROOT / 'parts_intro.md').read_text().splitlines():
        if ln.startswith('# '):
            cur = ln[2:].strip(); intros[cur] = []
        elif ln.strip():
            intros[cur].append(ln.strip())
    titles = list(intros)
    assert len(titles) == len(PARTS)
    for k, (name, rng) in enumerate(PARTS):
        txt = '# %s\n\n%s\n\n' % (titles[k], '\n\n'.join(intros[titles[k]]))
        txt += '\n\n'.join(chap(n) for n in rng)
        (ROOT / 'parts' / (name + '.md')).write_text(txt)
    t = src(0).read_text()
    (ROOT / 'front' / '01-导论.md').write_text(t.splitlines()[0] + '\n\n' + body_of(t.split('\n', 1)[1]))
    t = src(39).read_text()
    (ROOT / 'back' / '09-结语.md').write_text(t.splitlines()[0] + '\n\n' + body_of(t.split('\n', 1)[1]))
    (ROOT / 'back' / '10-后置.md').write_text((ROOT / 'back_src.md').read_text())
    han = sum(len(re.findall(r'[一-鿿]', src(n).read_text())) for n in range(0, 40))
    wan = '%.0f' % (han / 10000)
    front = (ROOT / 'front_src.md').read_text()
    front = (front.replace('__WAN__', wan).replace('__NO__', '第 %d 号' % NO)
             .replace('__ISBN__', ISBN).replace('__PRICE__', PRICE))
    (ROOT / 'front' / '00-前置.md').write_text(front)
    (ROOT / 'book.md').write_text('\n\n'.join((ROOT / 'parts' / (n + '.md')).read_text() for n, _ in PARTS))
    (ROOT / 'han.txt').write_text(str(han))
    print('han', han, 'wan', wan)


if __name__ == '__main__':
    main()
