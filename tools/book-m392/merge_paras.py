#!/usr/bin/env python3
"""把相邻的短段合并成信息更足的长段：只合并普通段，不动标题、引用块、表格、列表、整段加粗、出处注、很短的单句成段。"""
import re, sys, statistics
from pathlib import Path
MAXLEN, STOP, KEEP_SHORT = 520, 330, 40
FILES = ['front/01-导论.md'] + sorted(str(p) for p in Path('parts').glob('*.md')) + ['back/09-结语.md']
def plain(s):
    if not s.strip(): return False
    if re.match(r'^(#|>|\||- |\d+\. |```|---|◆)', s): return False
    if re.fullmatch(r'\*\*.+\*\*', s.strip()): return False
    if re.fullmatch(r'〔[^〔〕]*〕', s.strip()): return False
    return True
def merge(text):
    blocks, cur = [], []
    for line in text.split('\n'):
        if line.strip() == '':
            if cur: blocks.append('\n'.join(cur)); cur = []
        else:
            cur.append(line)
    if cur: blocks.append('\n'.join(cur))
    res = []
    for b in blocks:
        single = '\n' not in b
        if single and plain(b) and res and '\n' not in res[-1] and plain(res[-1]):
            a = res[-1]
            if len(a) < STOP and len(a) + len(b) <= MAXLEN and len(a) >= KEEP_SHORT and len(b) >= KEEP_SHORT:
                res[-1] = a + b; continue
        res.append(b)
    return '\n\n'.join(res) + '\n'
def lens(text):
    return [len(l) for l in text.split('\n') if plain(l)]
if __name__ == '__main__':
    apply = '--apply' in sys.argv
    allb, alla = [], []
    for f in FILES:
        t = Path(f).read_text(); m = merge(t)
        allb += lens(t); alla += lens(m)
        if apply: Path(f).write_text(m)
    print('before', len(allb), statistics.median(allb), 'after', len(alla), statistics.median(alla), 'max', max(alla))
