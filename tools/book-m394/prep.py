#!/usr/bin/env python3
"""第 394 号《一次闪光是谁的？》：/home/claude/quantum-book/*.md 分章稿 → front/ parts/ back/（照第 359 号管线）。

转换：
  章「# 第 N 章」→「## 第 N 章」，节「## ◆」→「### ◆」；
  「> **带走的话**：X」→ 带走的话块；「**两行小账**」两段 → 小账块（问句后加破折号，供加粗）；
  「**想一想**」+ 编号列表 → 想一想块；「**第X编总判断**」+ 粗体段 + 过渡句 → 编总判断块；
  独立整行粗体段 → 金线引句（pull）；附录各件降为二级标题挂在「# 附录」下。
用法：python3 prep.py
"""
import re
from pathlib import Path

SRC = Path('/home/claude/quantum-book')
OUT = Path(__file__).parent
CNP = '一二三四五六七八九十'


def convert(text):
    L = text.split('\n')
    o, i = [], 0
    while i < len(L):
        s = L[i]
        m = re.match(r'^# (第 ?\d+ ?章)　(.*)$', s)
        if m:
            o.append('## %s　%s' % (re.sub(r'第 ?(\d+) ?章', r'第 \1 章', m[1]), m[2])); i += 1; continue
        if re.match(r'^## ◆', s):
            o.append('#' + s); i += 1; continue
        m = re.match(r'^> \*\*带走的话\*\*[：:　 ]*(.*)$', s)
        if m:
            o += ['> **带走的话**', '> ' + m[1].strip(), '']; i += 1; continue
        if s.strip() == '**两行小账**':
            i += 1; rows = []
            while i < len(L) and len(rows) < 2:
                t = L[i].strip()
                if t:
                    mm = re.match(r'^(这一处，读数是谁的？|先在，还是发生？)(.*)$', t)
                    assert mm, ('ledger line', t[:30])
                    rows.append('> %s——%s' % (mm[1], mm[2].strip()))
                i += 1
            o += ['> **小账**'] + rows + ['']; continue
        if s.strip() == '**想一想**':
            o.append('> **想一想**'); i += 1
            while i < len(L) and not L[i].strip():
                i += 1
            while i < len(L) and re.match(r'^\d+\. ', L[i]):
                o.append('> ' + L[i]); i += 1
                while i < len(L) and not L[i].strip() and i + 1 < len(L) and re.match(r'^\d+\. ', L[i + 1]):
                    i += 1
            o.append(''); continue
        m = re.match(r'^\*\*(第[一二三四五六七八]编)总判断\*\*$', s.strip())
        if m:
            o.append('> **%s总判断**' % m[1]); i += 1
            while i < len(L) and (not L[i].strip() or L[i].startswith('**')):
                if L[i].strip():
                    o.append('> ' + L[i].strip())
                i += 1
            # 过渡句（下一编预告）
            while i < len(L) and L[i].strip() and not L[i].startswith('#'):
                o.append('> ' + L[i].strip()); i += 1
            o.append(''); continue
        if re.fullmatch(r'\*\*[^*]+\*\*', s.strip()):
            o += ['> ' + s.strip(), '']; i += 1; continue
        o.append(s); i += 1
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(o))


def front():
    t = (SRC / '00a-front.md').read_text()
    a = t.index('# 出 版 信 息'); b = t.index('# 作者介绍')
    cp = t[a:b].replace('# 出 版 信 息', '## 出版信息', 1)
    au = t[b:].replace('# 作者介绍', '## 作者介绍', 1)
    (OUT / 'front/00-前置.md').write_text(cp.rstrip() + '\n\n---\n\n' + au)
    (OUT / 'front/01-导论.md').write_text(convert((SRC / '00-daolun.md').read_text()))


def parts():
    body = ''.join((SRC / ('%02d-ch%02d.md' % (k, k))).read_text().rstrip() + '\n\n' for k in range(1, 48))
    body = convert(body)
    chunks = re.split(r'\n(?=# 第[一二三四五六七八]编　)', '\n' + body)
    chunks = [c.strip('\n') for c in chunks if c.strip()]
    assert len(chunks) == 8, len(chunks)
    for k, c in enumerate(chunks, 1):
        (OUT / ('parts/%02d-第%s编.md' % (k, CNP[k - 1]))).write_text(c + '\n')
    allp = '\n\n'.join(chunks)
    n = len(re.findall(r'(?m)^## 第 \d+ 章　', allp))
    assert n == 47, n
    (OUT / '统稿.md').write_text(allp + '\n')   # 学习单元用（# 第X编 / ## 第 N 章）


def back():
    (OUT / 'back/09-结语.md').write_text(convert((SRC / '48-jieyu.md').read_text()))
    fu = (SRC / '49-fulu.md').read_text()
    fu = re.sub(r'(?m)^# (附录[一二三四五])　', r'## \1　', fu)
    fu = re.sub(r'(?m)^## ◆', '### ◆', fu)
    hou = re.sub(r'(?m)^## ◆', '### ◆', (SRC / '50-houji.md').read_text())
    (OUT / 'back/10-后置.md').write_text(fu.rstrip() + '\n\n' + hou)


if __name__ == '__main__':
    front(); parts(); back()
    for f in sorted(OUT.glob('*/*.md')):
        print(f.relative_to(OUT), len(re.findall(r'[一-鿿]', f.read_text())))
