#!/usr/bin/env python3
"""第 511 号：把书稿目录（前言、导读、七编、四十一章、结语）与 parts_intro.json（编序）、app1/app2（附录）合成 src/full.md。只改格式，不动正文。
用法：python3 tools/book-m511/assemble.py [书稿目录]"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa: E402
SRC = Path(sys.argv[1] if len(sys.argv) > 1 else M.MS_DIR)
PARTS = json.loads((HERE / 'parts_intro.json').read_text(encoding='utf-8'))
ENDS = ('带走的话', '小账', '路标', '这一章的问题')


def body(path):
    t = Path(path).read_text(encoding='utf-8')
    assert '待作者补' not in t and '待核' not in t and '写作包' not in t, path
    return t.strip()


def demote(lines):
    out = []
    for l in lines:
        s = l.strip()
        if s == '---':
            continue
        m = re.match(r'^#{0,3} ?(带走的话|小账|路标|这一章的问题)$', s)
        if m:
            out.append('#### ' + m[1]); continue
        m = re.match(r'^## ◆ ?(.*)$', l)
        if m:
            out.append('### ◆ ' + m[1].strip()); continue
        m = re.match(r'^(#{2,3}) (.*)$', l)
        if m:
            l = ('### ◆ ' if m[1] == '##' else '#### ') + m[2].strip()
        out.append(l.rstrip())
    return out


def main():
    res = ['# ' + M.TITLE, '']
    pre = body(SRC / 'ch00a.md').splitlines()
    assert pre[0].startswith('# 前言'), pre[0]
    res += [pre[0], ''] + demote(pre[1:]) + ['']
    lun = body(SRC / 'ch00b.md').splitlines()
    assert lun[0].startswith('# 导读　'), lun[0]
    res += [lun[0], ''] + demote(lun[1:]) + ['']
    for p in PARTS:
        assert re.match(r'^第.编　', p['title']), p['title']
        res += ['# ' + p['title'], '', p['intro'], '']
        for n in range(p['from'], p['to'] + 1):
            c = body(SRC / ('ch%02d.md' % n)).splitlines()
            cm = re.match(r'^# 第 ?(\d+) ?章　(.*)$', c[0])
            assert cm and int(cm[1]) == n, c[0]
            res += ['## 第 %d 章　%s' % (n, cm[2]), ''] + demote(c[1:]) + ['']
    end = body(SRC / 'ch99.md').splitlines()
    assert end[0].startswith('# 结语　'), end[0]
    res += [end[0], ''] + demote(end[1:]) + ['']
    res += ['# 附录', '']
    for f in ('app1.md', 'app2.md'):
        a = body(HERE / 'src' / f).splitlines()
        assert a[0].startswith('# 附录'), a[0]
        res += ['#' + a[0], ''] + demote(a[1:]) + ['']
    out = re.sub(r'\n{3,}', '\n\n', '\n'.join(res)).rstrip() + '\n'
    (HERE / 'src').mkdir(exist_ok=True)
    (HERE / 'src/full.md').write_text(out, encoding='utf-8')
    print('ok full.md chapters', len(re.findall(r'^## 第 \d+ 章　', out, re.M)), 'parts', len(re.findall(r'^# 第.编　', out, re.M)))


if __name__ == '__main__':
    main()
