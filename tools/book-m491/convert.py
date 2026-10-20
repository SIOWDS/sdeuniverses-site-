#!/usr/bin/env python3
"""第 491 号《SDE平台：慧店的诞生》：把统稿 full.md（系列 Markdown）转成 220 版式工具链的分卷稿。
用法：python3 tools/book-m503/convert.py /home/claude/ai-de-zhenyan/full.md"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
s = Path(sys.argv[1]).read_text(encoding='utf-8')
_, yaml, body = s.split('---', 2)
Y = {}
for l in yaml.strip().splitlines():
    k, _, v = l.partition(':'); Y.setdefault(k.strip(), []).append(v.strip())

def callouts(t):
    out, L = [], t.split('\n'); i = 0
    while i < len(L):
        l = L[i]
        m = re.match(r'^【(带走的话|想一想|编序)】\s*(.*)$', l)
        if m and m.group(1) == '编序':
            out.append(m.group(2)); i += 1; continue
        if m:
            out += ['> **%s**' % m.group(1), '> ' + m.group(2)]; i += 1
            while i < len(L) and L[i].strip() and not L[i].startswith(('【', '#')):
                out.append('> ' + L[i]); i += 1
            out.append(''); continue
        if l.startswith('【小账】'):
            out.append('> **小账**')
            while i < len(L) and (L[i].startswith('【小账】') or not L[i].strip()):
                if L[i].startswith('【小账】'):
                    x = L[i][4:].strip()
                    mm = re.match(r'^(.{2,30}?)：(.*)$', x)
                    out.append('> ' + ('%s？——%s' % (mm.group(1).rstrip('？'), mm.group(2)) if mm else x))
                i += 1
            out.append(''); continue
        out.append(l); i += 1
    return '\n'.join(out)

body = callouts(body)
# 按一级标题切块
blocks = re.split(r'\n(?=# )', '\n' + body)
blocks = [b.strip('\n') for b in blocks if b.strip()]
front, lun, parts, jieyu, back = [], None, [], None, []
for b in blocks:
    h = b.split('\n', 1)[0]
    if re.match(r'# 第[一二三四五六七八九十]+编', h): parts.append(b)
    elif parts and not h.startswith(('# 结语', '# 参考', '# 附录', '# 后记')): parts[-1] += '\n\n' + b
    elif h.startswith('# 导论'): lun = b
    elif h.startswith('# 结语'): jieyu = b
    elif parts or h.startswith(('# 参考', '# 附录', '# 后记')): back.append(b)
    else: front.append(b)
assert len(parts) == 8 and lun and jieyu, (len(parts), bool(lun), bool(jieyu))

cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|',
      '| 书名 | 《SDE平台：慧店的诞生——让天下没有难发生的知识》 |', '| 著者 | 王德生 |',
      '| 执笔 | 复合主体：王德生立题、口述承重命题与裁定，Claude 执笔与统稿 |',
      '| 出版 | 德麦国际出版社（Demai International Press）· 新加坡 |',
      '| 编号 | 德麦国际专著第 491 号 |', '| ISBN | 979-8-90690-150-7 |', '| 定价 | US$20.00 |',
      '| 开本 | 170 mm × 240 mm |', '| 字数 | 约 __WAN__ 万字 |', '| 版次 | 2026 年 10 月第 1 版 |', '']
for st in Y.get('statement', []): cp += [st, '']
cp += ['版权所有　侵权必究', '']
fr = '\n'.join(cp) + '\n'
for b in front:
    b = re.sub(r'^# ', '## ', b, count=1)
    if b.startswith('## 作者介绍'):
        fr += b + '\n\n'
    else:
        fr += b + '\n\n'
(HERE / 'front/00-前置.md').write_text(fr, encoding='utf-8')
(HERE / 'front/01-导论.md').write_text(lun + '\n', encoding='utf-8')
for i, p in enumerate(parts, 1):
    name = re.match(r'# (第[一二三四五六七八九十]+编)', p).group(1)
    (HERE / ('parts/%02d-%s.md' % (i, name))).write_text(p + '\n', encoding='utf-8')
(HERE / 'back/09-结语.md').write_text(jieyu + '\n', encoding='utf-8')
bk = []
for b in back:
    if re.match(r'# 附录[一二三四五六七八九十]', b): b = '#' + b
    bk.append(b)
(HERE / 'back/10-后置.md').write_text('\n\n'.join(bk) + '\n', encoding='utf-8')
print('front', len(front), 'parts', len(parts), 'back', [x.split('\n',1)[0] for x in back])
