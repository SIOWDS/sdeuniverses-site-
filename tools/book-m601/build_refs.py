#!/usr/bin/env python3
"""第 601 号：由三审后的 bibliography.md 生成 src/refs.md（后置「参考资料」）。每个条目合并成一段（条目＋链接＋核读说明）。
用法：python3 tools/book-m601/build_refs.py /home/claude/gs/bibliography.md"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
raw = Path(sys.argv[1]).read_text(encoding='utf-8')
raw = raw.replace('随包内部工作稿', '内部工作稿').replace('随包研究资料及引用码', '作者提供的研究资料及引用码')
raw = raw.replace('源文件包的 evidence 目录', '作者另存的来源台账').replace('源文件包', '作者另存的来源台账').replace('所提供的版本', '所提供的版本')
out = ['# 参考资料　来源与文献', '']
out.append('正文方括号中的 [S569，第 23 章] 一类，指向本表的来源编号；[JCGM] 即 [25]，[ASA] 即 [26]；[U1] 指作者对本书的正式规定。取得文献的范围与限制，写在条目之后。')
out.append('')
entries = []
cur = None
sect = None
for l in raw.splitlines():
    l = l.rstrip()
    if not l.strip() or l.startswith('# '):
        continue
    if l.startswith('## '):
        if cur: entries.append(cur); cur = None
        entries.append(('h', l[3:])); continue
    if re.match(r'^\[[A-Za-z0-9]+\]', l):
        if cur: entries.append(cur)
        cur = ['p', l]; continue
    if cur is None:
        entries.append(('p', l)); continue
    cur[1] += ' ' + l.strip('（）') if False else ' ' + l
if cur: entries.append(cur)
U1 = '[U1] 王德生：本书对高阶能力状态、高手与 S3—D3—E3 的正式规定，见统一思想基底 v1.1（A 节），2026 年 11 月 6 日。这是作者对本书的理论规定，不是已发表文献，也不是实证结果。'
for e in entries:
    if e[0] == 'h':
        out.append('### ' + e[1]); out.append('')
        if e[1].startswith('一'):
            out.append(U1); out.append('')
    else:
        out.append(e[1]); out.append('')
Path(HERE / 'src/refs.md').write_text('\n'.join(out), encoding='utf-8')
print('refs ok', len([e for e in entries if e[0] == 'p']))
