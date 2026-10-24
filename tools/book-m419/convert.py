#!/usr/bin/env python3
"""第 419 号《这次谁去》：把 /home/claude/yinggaide/chapters/ 的定稿转成本工具链的分卷稿（front/parts/back）。"""
import json, re
from pathlib import Path

SRC = Path('/home/claude/yinggaide/chapters')
ROOT = Path(__file__).parent
X = json.loads((ROOT / 'parts419.json').read_text())
for d in ('front', 'parts', 'back'):
    (ROOT / d).mkdir(exist_ok=True)
    for f in (ROOT / d).glob('*.md'):
        f.unlink()


def body_lines(text):
    return text.strip().splitlines()[1:]  # 去掉首行 # 标题


def scene_breaks(lines):
    """章内：--- → ◆；把最后一个 --- 之后的斜体合成人物说明单独拎出来。"""
    out = [('◆' if l.strip() == '---' else l) for l in lines]
    note = None
    for i in range(len(out) - 1, -1, -1):
        s = out[i].strip()
        if not s:
            continue
        if re.fullmatch(r'\*[^*].*[^*]\*', s):
            note = s
            del out[i]
            # 去掉紧挨着的那个 ◆
            j = i - 1
            while j >= 0 and not out[j].strip():
                j -= 1
            if j >= 0 and out[j].strip() == '◆':
                del out[j]
        break
    while out and not out[-1].strip():
        out.pop()
    return out, note


def chapter(n):
    t = (SRC / ('%02d.md' % n)).read_text()
    title = t.strip().splitlines()[0]
    m = re.match(r'^# (第 \d+ 章)　(.*)$', title)
    assert m, title
    lines, note = scene_breaks(body_lines(t))
    conv = []
    for l in lines:
        if l.startswith('## '):
            conv.append('### ◆' + l[3:].strip())
        elif l.startswith('### '):
            raise SystemExit('第 %d 章出现 ### 标题：%s' % (n, l))
        else:
            conv.append(l)
    q, take = X['chapters'][str(n)]
    head = ['## %s　%s' % (m[1], m[2]), '', '> **这一章的问题**：%s' % q, '']
    tail = ['']
    if note:
        tail += [note, '']
    tail += ['> **带走的话**', '> %s' % take, '']
    return '\n'.join(head + conv + tail)


# ── 前置 ──
pre = (ROOT / 'front-static.md').read_text().rstrip() + '\n\n'
pt = (SRC / '00-preface.md').read_text()
ptitle = pt.strip().splitlines()[0][2:].strip()
plines = [('### ◆' + l[3:].strip()) if l.startswith('## ') else ('◆' if l.strip() == '---' else l) for l in body_lines(pt)]
pre += '## %s\n\n%s\n' % (ptitle, '\n'.join(plines).strip())
(ROOT / 'front/00-前置.md').write_text(pre)

# ── 各辑 ──
for k, p in enumerate(X['parts'], 1):
    s = ['# %s　%s' % (p['label'], p['title']), '']
    for para in p['intro']:
        s += [para, '']
    for n in range(p['from'], p['to'] + 1):
        s.append(chapter(n))
    (ROOT / ('parts/%02d-%s.md' % (k, p['label']))).write_text('\n'.join(s))

# ── 结语 ──
et = (SRC / '25-epilogue.md').read_text()
etitle = et.strip().splitlines()[0]
elines, enote = scene_breaks(body_lines(et))
elines = [('### ◆' + l[3:].strip()) if l.startswith('## ') else l for l in elines]
(ROOT / 'back/09-结语.md').write_text(etitle + '\n\n' + '\n'.join(elines).strip() + ('\n\n' + enote if enote else '') + '\n')

# ── 附录、后记 ──
ap = (SRC / '27-appendix.md').read_text().strip()
af = (SRC / '26-afterword.md').read_text().strip()
afl = af.splitlines()
af = afl[0] + '\n' + '\n'.join(('### ◆' + l[3:].strip()) if l.startswith('## ') else ('◆' if l.strip() == '---' else l) for l in afl[1:])
(ROOT / 'back/10-后置.md').write_text(ap + '\n\n' + af + '\n')
print('converted')
