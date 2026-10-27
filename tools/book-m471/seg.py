#!/usr/bin/env python3
"""第 471 号《舍不得》：把每章切成 9 个学习节（共 81 节）。
本书各章的「一、二、三」节数不一（6—34 节），节下又有小节，所以学习节不直接等于原书的节：
按汉字数均衡切分，切点只落在节题（### ◆）或小节题（####）上，能落在节题上就不落在小节题上。
每个学习节记下起点标题（锚点据此加在全文网页上）、起止范围与正文。
用法：python3 tools/book-m471/seg.py   （打印切分结果）
"""
import re
from pathlib import Path

HERE = Path(__file__).parent
N_UNITS = 9
H4_PENALTY = 0.12


def han(s):
    return len(re.findall(r'[一-鿿]', s))


def chapters(path=HERE / 'book.md'):
    bk = Path(path).read_text()
    out, cur_part = [], 0
    for blk in re.split(r'\n(?=#{1,2} )', '\n' + bk):
        blk = blk.strip('\n')
        if not blk:
            continue
        head, _, body = blk.partition('\n')
        if re.match(r'^# 第[一二三]编　', head):
            cur_part += 1; continue
        m = re.match(r'^## 第(\d+)章　(.+)$', head)
        if not m:
            continue
        k = int(m[1])
        body = re.split(r'\n(?=> \*\*带走的话\*\*)', body, maxsplit=1)[0]
        # 原子块：每个 #### 小节；节题自身的引子并入其后第一个块
        atoms, sec = [], None
        for piece in re.split(r'^(?=#{3,4} )', body, flags=re.M):
            if not piece.strip():
                continue
            h = piece.split('\n', 1)[0]
            if h.startswith('### ◆ '):
                sec = h[6:].strip()
                atoms.append({'kind': 'h3', 'sec': sec, 'h4': None, 'text': piece})
            elif h.startswith('#### '):
                if atoms and atoms[-1]['kind'] == 'h3' and atoms[-1]['h4'] is None and han(atoms[-1]['text']) < 400:
                    atoms[-1]['h4'] = h[5:].strip(); atoms[-1]['text'] += piece; atoms[-1]['merged'] = True
                else:
                    atoms.append({'kind': 'h4', 'sec': sec, 'h4': h[5:].strip(), 'text': piece})
            else:
                assert not atoms, (k, h[:30])  # 「这一章的问题」框
        out.append({'n': k, 'title': m[2].strip(), 'part': cur_part, 'atoms': atoms})
    assert len(out) == 9
    return out


def partition(atoms, n=N_UNITS):
    L = [max(han(a['text']), 1) for a in atoms]
    T = sum(L) / n
    m = len(atoms)
    INF = float('inf')
    pre = [0]
    for x in L:
        pre.append(pre[-1] + x)
    # dp[j][i]: 前 i 个原子分成 j 段的最小代价
    dp = [[INF] * (m + 1) for _ in range(n + 1)]
    bk = [[0] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = 0
    for j in range(1, n + 1):
        for i in range(j, m + 1):
            for s in range(j - 1, i):
                if dp[j - 1][s] == INF:
                    continue
                seg = pre[i] - pre[s]
                c = dp[j - 1][s] + ((seg - T) / T) ** 2 + (H4_PENALTY if atoms[s]['kind'] == 'h4' else 0)
                if c < dp[j][i]:
                    dp[j][i] = c; bk[j][i] = s
    cuts, i = [], m
    for j in range(n, 0, -1):
        s = bk[j][i]; cuts.append(s); i = s
    cuts = sorted(cuts)
    assert cuts[0] == 0 and len(cuts) == n
    return cuts


def units(path=HERE / 'book.md'):
    res = []
    for ch in chapters(path):
        at = ch['atoms']
        cuts = partition(at)
        bounds = cuts + [len(at)]
        for j in range(N_UNITS):
            seg = at[bounds[j]:bounds[j + 1]]
            a0, a1 = seg[0], seg[-1]
            secs = []
            for a in seg:
                if a['sec'] not in secs:
                    secs.append(a['sec'])
            title = a0['sec'] if a0['kind'] == 'h3' else a0['h4']
            if len(secs) > 1:
                title = '%s（至%s）' % (title, re.match(r'^([一二三四五六七八九十]+)、', secs[-1])[1] + '节')
            res.append({'lesson': len(res) + 1, 'ch': ch['n'], 'sec': j + 1, 'part': ch['part'], 'chTitle': '第%d章　%s' % (ch['n'], ch['title']),
                        'secTitle': title, 'startKind': a0['kind'], 'startSec': a0['sec'], 'startH4': a0['h4'] if a0['kind'] == 'h4' else None,
                        'body': ''.join(a['text'] for a in seg), 'han': sum(han(a['text']) for a in seg),
                        'title': '第%d章 · %s' % (ch['n'], title)})
    assert len(res) == 81
    return res


if __name__ == '__main__':
    for u in units():
        print('%02d  第%d章-%d  %5d  %s%s' % (u['lesson'], u['ch'], u['sec'], u['han'], '' if u['startKind'] == 'h3' else '[h4] ', u['secTitle']))
