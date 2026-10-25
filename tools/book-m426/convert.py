#!/usr/bin/env python3
"""第 426 号《读人》：把统稿全文（读人_全稿.md，系列 Skill 体例）转成 220 版式工具链的分卷稿。只做格式转换，不动正文文字。
用法：python3 tools/book-m426/convert.py [全稿.md]
产物：front/00-前置.md、parts/01–09.md、back/10-后置.md，以及 book.md（按序拼合，供 publish.py 数字数、build_unit 解析章）。
约定：
- YAML 头 → `## 出版信息` 表格与声明；`# 作者介绍`、`# 前言　X`、`# 导读` → 前置里的 `## …`；
- `# 第X编　题` 照留为编首；`【编序】X` → 编首导语段（去掉「副题」「原问」前缀的引语记号）；
- `【带走的话】X` → `> **带走的话**` 引用块；各编末的 `【想一想】X` 连续几行 → 并入本编最后一章末尾的 `> **想一想**` 引用块；
- `# 参考书目` 照留；`# 附录` 与 `# 附录一　X` → `# 附录` 之下的 `## 附录一　X`；`# 后记` 照留。
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa: E402

SRC = Path(sys.argv[1] if len(sys.argv) > 1 else M.SRC)
raw = SRC.read_text(encoding='utf-8')
assert raw.startswith('---\n')
_, head, body = raw.split('---\n', 2)
meta = {}
st = []
for l in head.splitlines():
    k, _, v = l.partition(':')
    if k.strip() == 'statement':
        st.append(v.strip())
    elif k.strip():
        meta[k.strip()] = v.strip()

CPMETA = [('书名', '《%s》' % M.TITLE), ('副题', M.SUBTITLE), ('英文书名', M.TITLE_EN), ('著者', '王德生、刘春华'),
          ('执笔', meta['executor']), ('出版', '德麦国际出版社（Demai International Press）· 新加坡'),
          ('编号', '德麦国际专著第 %d 号' % M.NO), ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'),
          ('字数', meta['words']), ('版次', '2026 年 10 月第 1 版'), ('完稿', meta['finished'])]


def h1_split(text):
    out = []
    for blk in re.split(r'\n(?=# )', '\n' + text):
        blk = blk.strip('\n')
        if not blk:
            continue
        h, _, b = blk.partition('\n')
        out.append((h[2:].strip(), b.strip('\n')))
    return out


def fmt(b):
    out = []
    think = []
    for l in b.split('\n'):
        s = l.strip()
        m = re.match(r'^【带走的话】(.*)$', s)
        if m:
            out += ['> **带走的话**', '> ' + m[1].strip(), '']
            continue
        m = re.match(r'^【想一想】(.*)$', s)
        if m:
            think.append(m[1].strip()); continue
        out.append(l)
    if think:
        while out and not out[-1].strip():
            out.pop()
        out += ['', '> **想一想**'] + ['> ' + x for x in think] + ['']
    s = '\n'.join(out)
    return re.sub(r'\n{3,}', '\n\n', s).strip() + '\n'


blocks = h1_split(body)
front, parts, back = [], [], []
for t, b in blocks:
    if t == '作者介绍' or t.startswith('前言') or t.startswith('导读'):
        nm = t if '　' in t or t == '作者介绍' else t + '　九编一张图'
        front.append('## %s\n\n%s' % (nm, fmt(b)))
    elif re.match(r'^第[一二三四五六七八九]编　', t):
        lines = b.split('\n')
        intro, rest, i = [], [], 0
        while i < len(lines) and not lines[i].startswith('## '):
            s = lines[i].strip()
            if s.startswith('【编序】'):
                x = s[4:].strip()
                x = re.sub(r'^\*\*(.*)\*\*$', r'\1', x)
                if not intro and not x.startswith('这一编') and not x.startswith('原问'):
                    x = '原问：' + re.sub(r'^原问[：:]\s*', '', x)
                intro.append(x)
            i += 1
        parts.append('# %s\n\n%s\n\n%s' % (t, '\n\n'.join(intro), fmt('\n'.join(lines[i:]))))
    else:
        back.append((t, b))

cp = '## 出版信息\n| 项 | 内容 |\n|---|---|\n' + ''.join('| %s | %s |\n' % r for r in CPMETA) + '\n' + '\n\n'.join(st + [meta['copyright']])
(HERE / 'front').mkdir(exist_ok=True)
(HERE / 'front/00-前置.md').write_text(cp + '\n\n' + '\n'.join(front), encoding='utf-8')
(HERE / 'parts').mkdir(exist_ok=True)
assert len(parts) == 9, len(parts)
for k, p in enumerate(parts, 1):
    (HERE / ('parts/%02d.md' % k)).write_text(p, encoding='utf-8')
bk = []
appx_intro = None
for t, b in back:
    if t == '附录':
        appx_intro = b
    elif t.startswith('附录'):
        bk.append('# 附录\n\n%s\n\n## %s\n\n%s' % (appx_intro or '', t, b.strip()))
    else:
        bk.append('# %s\n\n%s' % (t, b.strip()))
(HERE / 'back').mkdir(exist_ok=True)
(HERE / 'back/10-后置.md').write_text('\n\n'.join(bk) + '\n', encoding='utf-8')
allf = [HERE / 'front/00-前置.md'] + [HERE / ('parts/%02d.md' % k) for k in range(1, 10)] + [HERE / 'back/10-后置.md']
(HERE / 'book.md').write_text('\n\n'.join(f.read_text(encoding='utf-8') for f in allf), encoding='utf-8')
han = len(re.findall(r'[一-鿿]', (HERE / 'book.md').read_text(encoding='utf-8')))
print('ok parts', len(parts), 'han', han)
