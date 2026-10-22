#!/usr/bin/env python3
"""第 412 号《谣言是没对过账的结晶》：把三审定稿（各章 Markdown）转成 220 版式工具链的分卷稿。
用法：python3 tools/book-m412/convert412.py /home/claude/rumor-book
"""
import re, sys, json
from pathlib import Path

HERE = Path(__file__).parent
R = Path(sys.argv[1])
C, F, B = R / 'chapters', R / 'front', R / 'build'
CN = '零一二三四五六七八九十'
PARTS = [('第一编', '谣言的现场', [1, 2, 3]), ('第二编', '前人对在哪里', [4, 5, 6]), ('第三编', '诊断：谣言是什么结晶', [7, 8, 9]),
         ('第四编', '为什么辟谣跑得慢', [10, 11, 12]), ('第五编', '对账：老手艺与它的账本', [13, 14, 15]),
         ('第六编', '方向：把对账的成本降下来', [16, 17, 18]), ('第七编', '检验与收束', [19, 20, 21])]
NOTE = re.compile(r'^〔(本章|前言|导读|结语)?约[^〕]*〕$')
notes = []


def rd(p):
    return Path(p).read_text(encoding='utf-8')


def callouts(md, label):
    """章末三块 → 220 工具链的引用块写法；收走章末核验栏。"""
    out, L, i = [], md.split('\n'), 0
    while i < len(L):
        s = L[i].strip()
        if NOTE.match(s):
            notes.append((label, s[1:-1])); i += 1; continue
        m = re.match(r'^\*\*带走的话[:：]\*\*\s*(.*)$', s)
        if m:
            out += ['> **带走的话**', '> ' + m.group(1), '']; i += 1; continue
        if re.match(r'^\*\*两行小账[:：]?\*\*', s):
            i += 1; items = []
            while i < len(L) and (L[i].strip().startswith('- ') or not L[i].strip()):
                if L[i].strip(): items.append(L[i].strip()[2:])
                i += 1
            out += ['> **小账**'] + ['> ' + x for x in items] + ['']; continue
        m = re.match(r'^\*\*想一想[:：]?\*\*\s*$', s)
        if m:
            out += ['**想一想**', '']; i += 1; continue
        if s == '---':
            i += 1; continue
        out.append(L[i]); i += 1
    return '\n'.join(out)


def split_h2(md):
    res = []
    for b in re.split(r'(?m)^## ', md):
        if not b.strip(): continue
        t, _, body = b.partition('\n')
        res.append((t.strip(), body.strip('\n')))
    return res


# ── 卷首 ──
imp = rd(F / 'imprint.md')
note = re.search(r'复合主体注释[：:](.*)', imp).group(1).strip()
han_total = sum(len(re.findall(r'[一-鿿]', rd(p))) for p in list(C.glob('*.md')) + [F / 'author.md', F / 'diagnosis.md', B / 'app2.md', B / 'bib.md'])
cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|',
      '| 书名 | 《谣言是没对过账的结晶：后真相时代，谣言为什么比辟谣跑得快》 |', '| 著者 | 王德生 |',
      '| 执笔 | 复合主体：王德生立题、口述承重命题与分寸，Claude 执笔与统稿 |',
      '| 出版 | 德麦国际出版社（Demai International Press）· 新加坡 |',
      '| 编号 | 德麦国际专著第 412 号 |', '| ISBN | 979-8-90690-412-6 |', '| 定价 | US$23.00 |',
      '| 系列 | SDE 符号学系列 · 应用符号学十二套之二（系列第 12 卷） |',
      '| 开本 | 170 mm × 240 mm |', '| 字数 | 约 %d 万字 |' % round(han_total / 10000), '| 版次 | 2026 年 10 月第 1 版 |', '',
      'AI 协作声明：' + note, '',
      '书中各章开头的人物、郑桂兰一家，均为综合人物，非真人；真实案例只取公开、已有定论的事件，被谣言伤到的当事人一律不具名。凡标〔待核〕处，汇总于附录四。', '',
      '全书结构：出版信息、作者介绍、前言、导读、判词的三层与可错条款、目录；七编二十一章；结语、参考书目、附录四件、后记。', '',
      '版权所有　侵权必究', '']
fr = '\n'.join(cp) + '\n'
au = [x.strip() for x in re.split(r'\n\s*\n', rd(F / 'author.md')) if x.strip() and not x.strip().startswith('#')]
fr += '## 作者介绍\n\n' + '\n\n'.join(au) + '\n\n'
front_md = callouts(rd(C / 'ch00-front.md'), '前言与导读')
for t, body in split_h2(front_md):
    fr += '## %s\n\n%s\n\n' % (t, body)
dg = rd(F / 'diagnosis.md')
dg = re.sub(r'(?m)^## ', '### ', dg)
dg = re.sub(r'(?m)^# (.*)$', r'## \1', dg)
fr += dg.strip() + '\n'
(HERE / 'front').mkdir(exist_ok=True)
(HERE / 'front/00-前置.md').write_text(fr, encoding='utf-8')
lun = HERE / 'front/01-导论.md'
if lun.exists(): lun.unlink()

# ── 编序与章问 ──
bx = {}
for blk in re.split(r'(?m)^## ', rd(F / 'bianxu.md')):
    m = re.match(r'(第[一二三四五六七]编)[^\n]*\n(.*)', blk, re.S)
    if m: bx[m.group(1)] = [x.strip() for x in re.split(r'\n\s*\n', m.group(2)) if x.strip()]
qs = {}
for line in rd(F / 'questions.md').split('\n'):
    m = re.match(r'^\s*第\s*(\d+)\s*章\s*[｜|]\s*(?:这一章的问题[:：])?\s*(.+)$', line.strip())
    if m: qs[int(m.group(1))] = m.group(2).strip()

(HERE / 'parts').mkdir(exist_ok=True)
for k, (lab, name, chs) in enumerate(PARTS, 1):
    out = ['# %s　%s' % (lab, name), ''] + sum(([p, ''] for p in bx[lab]), [])
    for c in chs:
        md = callouts(rd(C / ('ch%02d.md' % c)), '第 %d 章' % c)
        first, _, rest = md.partition('\n')
        m = re.match(r'^##\s*第\s*(\d+)\s*章\s*[　 ]*(.*)$', first.strip())
        assert m and int(m.group(1)) == c, first
        out += ['## 第 %d 章　%s' % (c, m.group(2).strip()), '']
        if c in qs: out += ['> **这一章的问题**：' + qs[c], '']
        out += [rest.strip('\n'), '']
    (HERE / ('parts/%02d-%s.md' % (k, lab))).write_text('\n'.join(out) + '\n', encoding='utf-8')

# ── 结语、参考书目、附录、后记 ──
back = callouts(rd(C / 'ch99-back.md'), '后置')
bs = dict(split_h2(back))
order = list(bs)
jy = next(t for t in order if t.startswith('结语'))
(HERE / 'back').mkdir(exist_ok=True)
(HERE / 'back/09-结语.md').write_text('# %s\n\n%s\n' % (jy, bs[jy]), encoding='utf-8')
bib = rd(B / 'bib.md')
bib = re.sub(r'^## 参考书目\s*\n', '', bib.strip())
bib = re.sub(r'(?m)^### ', '## ', bib)
app2 = rd(B / 'app2.md').strip()
app2_t, _, app2_b = re.sub(r'^## ', '', app2).partition('\n')
def table_to_list(md):
    out, rows = [], []
    for line in md.split('\n') + ['']:
        if line.strip().startswith('|'):
            rows.append([c.strip() for c in line.strip().strip('|').split('|')]); continue
        if rows:
            hdr = rows[0]; data = [r for r in rows[1:] if not re.match(r'^:?-{2,}', r[0] or '-')]
            for r in data:
                r = r + [''] * (len(hdr) - len(r))
                out.append('**%s　%s**' % (r[0], r[1])); out.append('')
                for h, c in zip(hdr[2:], r[2:]):
                    if c: out.append('%s：%s' % (h, c)); out.append('')
            rows = []
        out.append(line)
    return '\n'.join(out)
app2_b = table_to_list(app2_b)
a4 = ['本表汇集各章写作与审校时的核验记录。〔待核〕为尚未落实、出版前须逐条核对的项目；"已核"为写作时已查得来源的项目。', '']
for lab, s in notes:
    s = re.sub(r'^(本章|前言|导读|结语)约[^；]*；', '', s)
    a4 += ['**%s**　%s' % (lab, s), '']
apps = []
for t in order:
    if t.startswith('附录一'): apps.append((t, bs[t])); apps.append((app2_t.strip(), app2_b.strip()))
    elif t.startswith('附录三'): apps.append((t, bs[t])); apps.append(('附录四　引文与研究核验总表', '\n'.join(a4)))
hj = next(t for t in order if t.startswith('后记'))
bk = ['# 参考书目', '', bib, '', '# 附录', '', '本书附录四件：术语表、案例出处总表、转发前三问卡片、引文与研究核验总表。', '']
for t, b in apps:
    b = re.sub(r'(?m)^## ', '### ', b)
    bk += ['## ' + t, '', b, '']
bk += ['# ' + hj, '', bs[hj], '']
(HERE / 'back/10-后置.md').write_text('\n'.join(bk), encoding='utf-8')
print('front ok; parts', len(PARTS), '; notes', len(notes), '; han', han_total, '; back', [t for t, _ in apps])
