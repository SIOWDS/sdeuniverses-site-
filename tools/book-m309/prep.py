#!/usr/bin/env python3
"""第 309 号《躺平的SDE解构》：/home/claude/tangping/parts/*.md 分章稿 → front/ parts/ back/（照第 394 号管线）。

转换：
  YAML 头 → 「## 出版信息」字段表＋小字声明；前置各件「# 题」→「## 题」；
  「【编序】X」→ 编首导语段；「【带走的话】X」→ 带走的话块；相邻两行「【小账】A：B」→ 小账块；
  「【想一想】X」→ 想一想块；独立整行粗体段 → 金线引句（pull）。
另写 统稿.md（# 第X编 / ## 第 N 章）供 tools/book_unit/build_unit.py 用。
用法：python3 prep.py
"""
import re
from pathlib import Path

SRC = Path('/home/claude/tangping/parts')
OUT = Path(__file__).parent
CNP = '一二三四五'
PARTS = [(1, 6), (7, 15), (16, 25), (26, 36), (37, 44)]
SUB = '一台怠速的发动机'


def convert(text):
    L = text.split('\n')
    o, i = [], 0
    while i < len(L):
        s = L[i]
        if s.startswith('【编序】'):
            o += [s[4:].strip(), '']; i += 1; continue
        if s.startswith('【带走的话】'):
            o += ['> **带走的话**', '> ' + s[6:].strip(), '']; i += 1; continue
        if s.startswith('【小账】'):
            rows = []
            while i < len(L) and (L[i].startswith('【小账】') or (not L[i].strip() and i + 1 < len(L) and L[i + 1].startswith('【小账】'))):
                if L[i].strip():
                    rows.append('> ' + L[i][4:].strip())
                i += 1
            assert len(rows) == 2, rows
            o += ['> **小账**'] + rows + ['']; continue
        if s.startswith('【想一想】'):
            o += ['> **想一想**', '> ' + s[5:].strip(), '']; i += 1; continue
        assert not s.startswith('【'), s[:30]
        if re.fullmatch(r'\*\*[^*]+\*\*', s.strip()):
            o += ['> ' + s.strip(), '']; i += 1; continue
        o.append(s); i += 1
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(o)).strip('\n') + '\n'


def front():
    t = (SRC / '00_front.md').read_text()
    _, yml, body = t.split('---\n', 2)
    meta, notes = {}, []
    for line in yml.strip().splitlines():
        k, _, v = line.partition(': ')
        if k == 'statement':
            notes.append(v.strip())
        else:
            meta[k] = v.strip()
    rows = [('书名', '《躺平的SDE解构——%s》' % SUB), ('著者', '王德生'), ('执笔', meta['executor']),
            ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 309 号'),
            ('ISBN', '979-8-90690-817-9'), ('定价', 'US$20.00'), ('开本', '170 mm × 240 mm（16 开）'),
            ('字数', '约 20 万字'), ('版次', '2026 年 10 月第 1 版'), ('完稿', '2026 年 10 月 14 日')]
    cp = '## 出版信息\n\n| 字段 | 内容 |\n|---|---|\n' + ''.join('| %s | %s |\n' % r for r in rows) + '\n'
    notes = [n.replace('全书结构：出版信息、作者介绍、十分钟读完这本书、前言、导读、目录；',
                       '全书结构：扉页、出版信息、作者介绍、十分钟读完这本书、前言、导读、目录；') for n in notes]
    cp += '\n\n'.join(notes) + '\n\n' + meta.get('copyright', '版权所有　侵权必究') + '\n'
    body = re.sub(r'(?m)^# ', '## ', body.strip())
    (OUT / 'front/00-前置.md').write_text(cp + '\n---\n\n' + convert(body))
    (OUT / 'front/01-导论.md').write_text(convert((SRC / '01_intro.md').read_text()))


def parts():
    chunks = []
    for k, (a, b) in enumerate(PARTS, 1):
        txt = '\n\n'.join((SRC / ('ch%02d.md' % n)).read_text().strip() for n in range(a, b + 1))
        txt = convert(txt)
        assert txt.startswith('# 第%s编　' % CNP[k - 1]), txt[:30]
        (OUT / ('parts/%02d-第%s编.md' % (k, CNP[k - 1]))).write_text(txt)
        chunks.append(txt)
    allp = '\n\n'.join(chunks)
    n = len(re.findall(r'(?m)^## 第 \d+ 章　', allp))
    assert n == 44, n
    (OUT / '统稿.md').write_text(allp)


def back():
    t = (SRC / '99_back.md').read_text()
    a = t.index('\n# 附录')
    (OUT / 'back/09-结语.md').write_text(convert(t[:a]))
    (OUT / 'back/10-后置.md').write_text(convert(t[a:]))


if __name__ == '__main__':
    for d in ('front', 'parts', 'back'):
        (OUT / d).mkdir(exist_ok=True)
    front(); parts(); back()
    for f in sorted(OUT.glob('*/*.md')):
        print(f.relative_to(OUT), len(re.findall(r'[一-鿿]', f.read_text())))
