#!/usr/bin/env python3
"""第 607 号成书体检：python3 check607.py <out目录> [print|reader]
查：字体全部嵌入；目录页码（书签／toc json 的物理页含该标题，印刷页码与页脚一致）；115 章＋总导论＋总合论＋21 编扉齐全；
无 Markdown 残符；公式与表；近空白页。退出码 1＝有失败项。"""
import json, re, subprocess, sys
from pathlib import Path
import pymupdf
out = Path(sys.argv[1]); tag = sys.argv[2] if len(sys.argv) > 2 else 'print'
pdf = out / ('sde-compendium-%s.pdf' % tag); toc = json.loads((out / ('toc-%s.json' % tag)).read_text())
fails, notes = [], []
fo = subprocess.run(['pdffonts', str(pdf)], capture_output=True, text=True).stdout.splitlines()[2:]
bad = [l for l in fo if l.split()[-5] != 'yes']
(fails if bad else notes).append('字体：共 %d 个，未嵌入 %d' % (len(fo), len(bad)))
d = pymupdf.open(str(pdf)); notes.append('页数 %d' % len(d))
ent = toc['toc']
titles = [e['t'] for e in ent]
chs = [t for t in titles if re.match(r'^第 \d+ 章', t)]
parts = [t for t in titles if re.match(r'^第.+编 ', t)]
if len(chs) != 115 or len({re.match(r'^第 (\d+)', t)[1] for t in chs}) != 115: fails.append('章数 %d' % len(chs))
if len(parts) != 21: fails.append('编数 %d' % len(parts))
for k in ('总导论', '总合论', '作者介绍'):
    if not any(t.startswith(k) for t in titles): fails.append('缺 ' + k)
wrongp = []
for e in ent:
    g = e['g']; txt = re.sub(r'\s+', '', d[g - 1].get_text())
    key = re.sub(r'\s+', '', e['t'])
    head = key[:6] if re.match(r'^第\d+章', key) else key[:5]
    if head not in txt: wrongp.append((e['t'], g))
    if e['p'] and not re.match(r'^第.+编 ', e['t']):
        last = [l for l in d[g - 1].get_text().split('\n') if l.strip()]
        if not any(l.strip() == e['p'] for l in last[-3:] + last[:3]): wrongp.append(('印刷页码', e['t'], e['p'], g))
(fails if wrongp else notes).append('目录页码不符 %d：%s' % (len(wrongp), wrongp[:5]))
res, thin = [], []
for i, pg in enumerate(d, 1):
    t = pg.get_text()
    if re.search(r'####|\*\*|\\\[|\\\]|`|^#+ ', t, re.M): res.append(i)
    h = len(re.findall(r'[一-鿿]', t))
    if 0 < h < 60 and i > 2: thin.append(i)
(fails if res else notes).append('Markdown 残符页 %s' % res[:10])
notes.append('字很少的页（含扉页、章首短页）%d 个：%s' % (len(thin), thin[:40]))
alltxt = '\n'.join(p.get_text() for p in d)
for k in ('t+1', '＝'):
    pass
notes.append('三式公式页：%s' % [i + 1 for i, p in enumerate(d) if 'd t∨e' in re.sub(r'\s+', '', p.get_text()).replace('∨', ' ∨ ').replace(' ', '') or ('t+1' in p.get_text() and '∧' in p.get_text())][:5])
notes.append('表格页（含「格位」「三角套一」）：%s' % [i + 1 for i, p in enumerate(d) if '三角套一' in p.get_text() or '当前名称' in p.get_text() or '当前能成立的内容' in p.get_text()][:6])
print('\n'.join(['FAIL ' + f for f in fails] + ['OK   ' + n for n in notes]))
sys.exit(1 if fails else 0)
