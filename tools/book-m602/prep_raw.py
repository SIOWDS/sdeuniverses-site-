#!/usr/bin/env python3
"""第 602 号《难得糊涂》：把统稿全稿（/home/claude/out/nande-hutu/full.md）整理成 convert.py 认的 src/full.raw.md。
由第 599 号 prep_raw.py 改来。只做结构／标题格式的转换，一个字的正文都不改：
  去书名块（「# 难得糊涂」至「## 前言」之前）；
  「## 前言／导论／第 N 章／结语　T」→ 一级「# …」；「# 第X编　T」「# 附录」原样；「## 附录 A　T」原样（附录内二级）；
  「### N.M　T」「### 一、T」「### A.1　T」→ 二级「## …」（convert.py 再降成 ◆ 小节）。
用法：python3 prep_raw.py [全稿.md]（缺省读 /home/claude/out/nande-hutu/full.md）"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
src = Path(sys.argv[1] if len(sys.argv) > 1 else '/home/claude/out/nande-hutu/full.md').read_text(encoding='utf-8').splitlines()
out, started = [], False
for l in src:
    if not started:
        if l.startswith('## 前言'):
            started = True
        else:
            continue
    if re.match(r'^## (前言|导论|结语|第 \d+ 章)[ 　]', l):
        out.append(l[1:]); continue          # 二级 → 一级
    if l.startswith('### '):
        out.append(l[1:]); continue          # 三级 → 二级
    out.append(l)
txt = '\n'.join(out).rstrip() + '\n'
han = lambda s: len(re.findall(r'[一-鿿]', s))
full = '\n'.join(src)
skipped = full[:full.index('\n## 前言')]
assert han(txt) + han(skipped) == han(full), '汉字数对不上'
(HERE / 'src/full.raw.md').write_text(txt, encoding='utf-8')
print('ok raw', len(txt), 'han', han(txt), '(书名块 %d 字未计)' % han(skipped))
