#!/usr/bin/env python3
"""第 307 号《还是它吗？》：分章稿（v2/*.md）→ front/ parts/ back/（照第 394 号管线，版式照第 220 号）。

源稿约定：「## 第 N 章　题」「### ◆ 一、」；章尾【带走的话】【小账】【想一想】；篇首「# 上篇　题」＋【编序】。
用法：python3 prep.py --src <v2 目录>
"""
import argparse, re
from pathlib import Path

OUT = Path(__file__).parent
PIAN = ['上篇', '中篇', '下篇', '尾篇']
FIRST = {1: 0, 10: 1, 21: 2, 33: 3}


def convert(text):
    o = []
    L = text.split('\n'); i = 0
    while i < len(L):
        s = L[i]
        if s.startswith('【编序】'):
            o.append(s[len('【编序】'):].strip()); i += 1; continue
        if s.startswith('【带走的话】'):
            o += ['> **带走的话**', '> ' + s[len('【带走的话】'):].strip(), '']; i += 1; continue
        if s.startswith('【小账】'):
            rows = []
            while i < len(L) and (L[i].startswith('【小账】') or not L[i].strip()):
                t = L[i][len('【小账】'):].strip() if L[i].startswith('【小账】') else ''
                if t:
                    m = re.match(r'^(.{2,30}?)[：:](.*)$', t)
                    rows.append('> %s？——%s' % (m[1].rstrip('？?'), m[2].strip()) if m else '> ' + t)
                i += 1
            o += ['> **小账**'] + rows + ['']; continue
        if s.startswith('【想一想】'):
            rows = []
            while i < len(L) and (L[i].startswith('【想一想】') or not L[i].strip()):
                t = L[i][len('【想一想】'):].strip() if L[i].startswith('【想一想】') else ''
                if t:
                    rows.append('> ' + t.lstrip('- '))
                i += 1
            o += ['> **想一想**'] + rows + ['']; continue
        if re.fullmatch(r'\*\*[^*]+\*\*', s.strip()):
            o += ['> ' + s.strip(), '']; i += 1; continue
        o.append(s); i += 1
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(o)).strip() + '\n'


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--src', type=Path, required=True)
    S = ap.parse_args().src
    f = (S / '00_front.md').read_text()
    yaml, body = f.split('\n---\n', 1)[0], f.split('\n---\n', 1)[1]
    a = body.index('# 导论')
    fr, lun = body[:a], body[a:]
    fr = re.sub(r'(?m)^# ', '## ', fr)
    (OUT / 'front/00-前置.md').write_text((S.parent / 'cp.md').read_text().rstrip() + '\n\n---\n\n' + convert(fr))
    (OUT / 'front/01-导论.md').write_text(convert(lun))
    groups = [[] for _ in PIAN]; k = -1
    for n in range(1, 41):
        if n in FIRST: k = FIRST[n]
        groups[k].append(convert((S / ('ch%02d.md' % n)).read_text()))
    for j, g in enumerate(groups):
        (OUT / ('parts/%02d-%s.md' % (j + 1, PIAN[j]))).write_text('\n'.join(g))
    (OUT / '统稿.md').write_text('\n'.join(x.read_text() for x in sorted((OUT / 'parts').glob('*.md'))))
    (OUT / 'back/09-结语.md').write_text(convert((S / '90_jieyu.md').read_text()))
    bib = (S / '91_biblio.md').read_text().rstrip()
    apps = [(S / x).read_text().rstrip() for x in ['92_app_1.md', '93_app_23.md', '94_app_4.md', '95_app_5.md', '96_app_6.md']]
    apps = '\n\n'.join(apps)
    out_lines, fence = [], False
    for l in apps.split('\n'):
        if l.startswith('```'): fence = not fence
        if not fence and re.match(r'^# 附录[一二三四五六]', l): l = '#' + l
        out_lines.append(l)
    hou = convert((S / '97_houji.md').read_text())
    (OUT / 'back/10-后置.md').write_text(bib + '\n\n' + '\n'.join(out_lines) + '\n\n' + hou)
    for p in sorted(OUT.glob('*/*.md')):
        print(p.relative_to(OUT), len(re.findall(r'[一-鿿]', p.read_text())))


if __name__ == '__main__':
    main()
