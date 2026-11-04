#!/usr/bin/env python3
"""第 483 号：把书稿目录（前言、导言、五部、三十六章、结语、附录三件）合成 src/full.md。只改格式，不动正文；事实账不进书。
用法：python3 tools/book-m483/assemble.py [书稿目录]"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa: E402
SRC = Path(sys.argv[1] if len(sys.argv) > 1 else M.MS_DIR)
PARTS = [('part1.md', 1, 6), ('part2.md', 7, 11), ('part3.md', 12, 17), ('part4.md', 18, 29), ('part5.md', 30, 36)]


def body(name):
    t = (SRC / name).read_text(encoding='utf-8')
    i = t.find('## 本章事实账')
    if i >= 0:
        t = t[:i]
    assert '写作包' not in t and '事实库' not in t and (name == 'app3.md' or '待核' not in t), name
    return t.strip()


def demote(lines):
    out = []
    for l in lines:
        if l.strip() == '---':
            continue
        m = re.match(r'^(#{2,3}) (.*)$', l)
        if m:
            l = ('### ◆ ' if m[1] == '##' else '#### ') + m[2].strip()
        out.append(l.rstrip())
    return out


def main():
    res = ['# ' + M.TITLE, '']
    pre = body('front_preface.md').splitlines()
    assert pre[0] == '# 前言', pre[0]
    res += ['# 前言', ''] + demote(pre[1:]) + ['']
    lun = body('00_intro.md').splitlines()
    assert lun[0].startswith('# 导言　')
    res += [lun[0], ''] + demote(lun[1:]) + ['']
    for pf, a, b in PARTS:
        t = body(pf)
        lead, tail = t.split('## 部小结')
        ll = lead.strip().splitlines()
        m = re.match(r'^# (第.部)　(.*)$', ll[0])
        assert m, ll[0]
        res += [ll[0], ''] + ll[1:] + ['']
        for n in range(a, b + 1):
            c = body('ch%02d.md' % n).splitlines()
            cm = re.match(r'^# 第(\d+)章　(.*)$', c[0])
            assert cm and int(cm[1]) == n, c[0]
            res += ['## 第 %d 章　%s' % (n, cm[2]), ''] + demote(c[1:]) + ['']
        res += ['## 部小结　%s　%s' % (m[1], m[2]), ''] + tail.strip().splitlines() + ['']
    end = body('99_end.md').splitlines()
    assert end[0].startswith('# 结语　')
    res += [end[0], ''] + demote(end[1:]) + ['']
    res += ['# 附录', '']
    for f in ('app1.md', 'app2.md', 'app3.md'):
        a = body(f).splitlines()
        assert a[0].startswith('# 附录'), a[0]
        res += ['#' + a[0], ''] + demote(a[1:]) + ['']
    out = re.sub(r'\n{3,}', '\n\n', '\n'.join(res)).rstrip() + '\n'
    (HERE / 'src').mkdir(exist_ok=True)
    (HERE / 'src/full.md').write_text(out, encoding='utf-8')
    print('ok full.md chapters', len(re.findall(r'^## 第 \d+ 章　', out, re.M)), 'parts', len(re.findall(r'^# 第.部　', out, re.M)))


if __name__ == '__main__':
    main()
