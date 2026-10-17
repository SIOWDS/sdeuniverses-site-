#!/usr/bin/env python3
"""统稿 book3.md（pandoc 版）→ 流水线分卷稿 front/ parts/ back/（第 220 号版式口径）。"""
import json, re, sys
from pathlib import Path

SRC = Path('/tmp/claude-0/-home-claude/b9923d4c-cf25-57f3-96c4-47df1c947132/scratchpad/yy/book3.md')
BZ = Path('/tmp/claude-0/-home-claude/b9923d4c-cf25-57f3-96c4-47df1c947132/scratchpad/yy/bz')
OUT = Path('/home/claude/bk353')
for d in ('front', 'parts', 'back'):
    (OUT / d).mkdir(exist_ok=True)

warn = []

# ───────── 行级规范化 ─────────
def quotes(s, lineno=0):
    n = s.count('"')
    if n:
        out, k = [], 0
        for ch in s:
            if ch == '"':
                out.append('“' if k % 2 == 0 else '”'); k += 1
            else:
                out.append(ch)
        s = ''.join(out)
        if n % 2:
            warn.append('odd quotes line %d' % lineno)
    s = re.sub(r"'([一-鿿][^'\n]{0,14}?)'", r'‘\1’', s)
    return s

def textnorm(s, lineno=0):
    s = s.replace('\\[', '[').replace('\\]', ']')
    s = re.sub(r'<(https?://[^>\s]+)>', r'\1', s)
    s = re.sub(r'-{6,}', '——', s)
    s = re.sub(r'-{4,5}', '——', s)
    s = s.replace('---', '—')
    s = re.sub(r'(?<=[\w\)）])--(?=[\w\(（])', '–', s)
    s = s.replace('--', '–')
    return quotes(s, lineno)

def norm_lines(lines, base=0):
    out = []
    for i, l in enumerate(lines):
        if l.startswith('|'):
            if re.fullmatch(r'\|[\s:|\-]+\|', l):
                out.append(l)
            else:
                out.append(textnorm(l, base + i))
            continue
        l = re.sub(r'^-\s{2,}', '- ', l)
        l = re.sub(r'^(\d+)\.\s{2,}', r'\1. ', l)
        out.append(textnorm(l, base + i))
    # 项目之间的空行去掉
    res = []
    for l in out:
        if l.strip() == '' and res and False:
            pass
        res.append(l)
    final = []
    for idx, l in enumerate(res):
        if l.strip() == '':
            prev = next((x for x in reversed(final) if x.strip()), '')
            nxt = next((x for x in res[idx + 1:] if x.strip()), '')
            if re.match(r'^(- |\d+\. )', prev) and re.match(r'^(- |\d+\. )', nxt):
                continue
        final.append(l)
    return final

def cap(title):
    """“标签 题目 副题” → “标签　题目：副题”（取第一个空格后的空格换成冒号）。"""
    return title

def head_split(t, kind):
    """第N章 X Y → ('第 N 章', 'X：Y')；第X编 X Y → ('第X编', 'X：Y')；年份 X Y → ('年份','X：Y')。"""
    m = re.match(r'^(第\d+章|第[一二三四五六七八九十]+编|\d{4}|下编结语|下编|导论|前言|导读|结语|附录[一二三四五六七八九十]+)\s+(.*)$', t)
    lab, rest = m[1], m[2]
    if kind == 'chap':
        lab = re.sub(r'第(\d+)章', r'第 \1 章', lab)
    rest = textnorm(rest).replace('建构一脉上', '建构一脉（上）').replace('建构一脉下', '建构一脉（下）')
    parts = rest.split(' ', 1)
    title = parts[0] + ('：' + parts[1].replace(' ', '　') if len(parts) > 1 else '')
    return lab, title

# ───────── 读入并按一级标题切块 ─────────
L = SRC.read_text(encoding='utf-8').split('\n')
# 去 YAML 与 说明
i0 = next(i for i, l in enumerate(L) if l.startswith('# 前言'))
L = L[i0:]
base_off = i0
blocks, cur = [], None
for i, l in enumerate(L):
    if l.startswith('# '):
        cur = [l[2:].strip(), []]; blocks.append(cur)
    else:
        cur[1].append(l)
for b in blocks:
    while b[1] and not b[1][-1].strip(): b[1].pop()
    while b[1] and not b[1][0].strip(): b[1].pop(0)
    if b[1] and b[1][-1].strip() == '---':
        b[1].pop()
    b[1] = norm_lines(b[1], base_off)
B = {b[0].split(' ')[0] if not re.match(r'^第[一二三四五六七八九十]+编', b[0]) else re.match(r'^(第[一二三四五六七八九十]+编)', b[0])[1]: b for b in blocks}
print('blocks:', [b[0][:14] for b in blocks])

# ───────── 数据：编序、带走的话、小账 ─────────
BX, CH = {}, {}
for f in sorted(BZ.glob('A*.json')):
    d = json.loads(f.read_text(encoding='utf-8'))
    BX.update(d.get('bianxu', {})); CH.update(d.get('chapters', {}))
print('bianxu', len(BX), 'chapters', len(CH))

def han(s): return len(re.findall(r'[一-鿿]', s))

# ───────── 章内小节标题 ─────────
def sec_head(t):
    t = t.strip()
    if t in ('本章来源', '导论来源', '本节来源'):
        return '### ' + t
    m = re.match(r'^([一二三四五六七八九十]+)\s+(.*)$', t)
    if m:
        return '### ◆ %s、%s' % (m[1], m[2])
    m = re.match(r'^(\d+[a-z]?)\s+(.*)$', t)
    if m:
        r = m[2].split(' ', 1)
        return '### ◆ %s　%s' % (m[1], r[0] + ('：' + r[1] if len(r) > 1 else ''))
    return '### ◆ ' + t

def convert_body(lines):
    """正文里的 ##/### 小节标题 → ### ◆；其余原样。"""
    out = []
    for l in lines:
        m = re.match(r'^(#{2,3}) (.*)$', l)
        if m:
            out.append(sec_head(m[2]))
        else:
            out.append(l)
    return out

def tail_cards(n):
    c = CH.get(str(n))
    if not c:
        warn.append('no card for chapter %s' % n); return []
    o = ['> **带走的话**', '> ' + c['take'], '', '> **小账**']
    for q, a in c['ledger']:
        o.append('> %s——%s' % (q, a))
    return o

def with_cards(n, body):
    """带走的话和小账放在「本章来源」之前。"""
    cards = tail_cards(n)
    if not cards:
        return body
    idx = next((i for i, l in enumerate(body) if l.startswith('### 本章来源')), None)
    if idx is None:
        return body + [''] + cards
    return body[:idx] + cards + [''] + body[idx:]

def split_h2(lines):
    """按 ## 切成 [(title, body)]；第一个 ## 之前的内容单独返回。"""
    pre, items, cur = [], [], None
    for l in lines:
        m = re.match(r'^## (.*)$', l)
        if m:
            cur = [m[1].strip(), []]; items.append(cur)
        elif cur is None:
            pre.append(l)
        else:
            cur[1].append(l)
    return pre, items

def blank_join(lines):
    # 确保块与块之间有空行（引号块、表格前后）
    out = []
    for l in lines:
        out.append(l)
    return '\n'.join(out).strip('\n')

def join_paras(lines):
    s = '\n'.join(lines)
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s.strip('\n')

# ───────── 前置 ─────────
def bx(name):
    return BX.get(name)

def part_text(label_cn, title, chapters, intro_paras):
    """label_cn：第一编；chapters：[(num, rawtitle, body_lines)]"""
    out = ['# %s　%s' % (label_cn, title), '']
    for p in intro_paras:
        out += [p, '']
    for num, ttl, body in chapters:
        lab, t = head_split(ttl, 'chap')
        out += ['## %s　%s' % (lab, t), '']
        body = convert_body(body)
        out += (with_cards(num, body) if isinstance(num, int) else body)
        out += ['']
    return join_paras(out) + '\n'

# 出版信息与作者介绍
PUB = open(OUT / 'pub.md', encoding='utf-8').read()
_h = sum(len(re.findall(r'[\u4e00-\u9fff]', x)) for b in blocks for x in b[1])
PUB = PUB.replace('__WAN__', '%d' % round(_h / 10000))
print('source han', _h)

# 前言、导读
front_md = []
if PUB:
    front_md.append(PUB.rstrip())
for key in ('前言', '导读'):
    t, body = B[key]
    lab, ttl = head_split(t, 'f')
    front_md.append('## %s　%s\n\n%s' % (lab, ttl.replace('：', '：'), join_paras(body)))
(OUT / 'front/00-前置.md').write_text('\n\n---\n\n'.join(front_md) + '\n', encoding='utf-8')

# 导论
t, body = B['导论']
lab, ttl = head_split(t, 'f')
(OUT / 'front/01-导论.md').write_text('# %s　%s\n\n%s\n' % (lab, ttl, join_paras(convert_body(body))), encoding='utf-8')

# ───────── 各编（上编） ─────────
CN = '一二三四五六七八九十'
def pfile(idx, name): return OUT / 'parts' / ('%02d-%s.md' % (idx, name))
part_files = []
for k in range(1, 11):
    key = '第%s编' % ('十' if k == 10 else CN[k - 1])
    t, body = B[key]
    lab, ttl = head_split(t, 'part')
    pre, items = split_h2(body)
    chapters = []
    for it_t, it_b in items:
        m = re.match(r'^第(\d+)章', it_t)
        chapters.append((int(m[1]), it_t, it_b))
    intro = ['\n'.join(x for x in BX.get(key, [])).split('\n')] if False else BX.get(key, [])
    if not intro:
        warn.append('no bianxu for ' + key)
    txt = part_text(lab, ttl, chapters, intro)
    fname = pfile(k, key)
    fname.write_text(txt, encoding='utf-8'); part_files.append(fname.stem)

# ───────── 下编 ─────────
t, body = B['下编']
lab, ttl = head_split(t, 'f')
pre, items = split_h2(body)
intro_paras = [p for p in '\n'.join(pre).split('\n\n') if p.strip()]
tbl_title, tbl_body = items[0]
out = ['# 下编　' + ttl.replace('：', '——', 1), '']
for p in intro_paras:
    out += [p.strip(), '']
out += ['## 总表　' + tbl_title, '']
out += tbl_body + ['']
(pfile(11, '下编导')).write_text(join_paras(out) + '\n', encoding='utf-8'); part_files.append('11-下编导')

for k in range(11, 16):
    key = '第%s编' % ('十' + (CN[k - 11] if k > 10 else ''))
    key = {11: '第十一编', 12: '第十二编', 13: '第十三编', 14: '第十四编', 15: '第十五编'}[k]
    t, body = B[key]
    lab, ttl = head_split(t, 'part')
    pre, items = split_h2(body)
    out = ['# %s　%s' % (lab, ttl), '']
    for p in BX.get(key, []):
        out += [p, '']
    for it_t, it_b in items:
        l2, t2 = head_split(it_t, 'year')
        out += ['## %s　%s' % (l2, t2), '']
        out += convert_body(it_b) + ['']
    if k == 15:
        t3, b3 = B['下编结语']
        l3, tt3 = head_split(t3, 'f')
        out += ['## 下编结语　' + tt3, '']
        out += convert_body(b3 and [x for x in b3]) + ['']
    pfile(k + 1, key).write_text(join_paras(out) + '\n', encoding='utf-8'); part_files.append(pfile(k + 1, key).stem)

# ───────── 结语 ─────────
t, body = B['结语']
lab, ttl = head_split(t, 'f')
(OUT / 'back/09-结语.md').write_text('# 结语　%s\n\n%s\n' % (ttl, join_paras(convert_body(body))), encoding='utf-8')

# ───────── 附录 ─────────
ap = ['# 附录', '', '本书附录八件：AI 时代的我教育（本书的出口）、教育学派总表（逐章登记）、异象登记与吸收手法表、本书的可错条款、近亲划界表、术语大白话对照、引文核验与承接书目、生活案例索引。']
ap += ['']
for k in range(1, 9):
    key = '附录' + CN[k - 1] if k < 10 else '附录十'
    t, body = B[key]
    lab, ttl = head_split(t, 'f')
    ap += ['## %s　%s' % (lab, ttl), '']
    ap += convert_body(body) + ['']
(OUT / 'back/10-后置.md').write_text(join_paras(ap) + '\n', encoding='utf-8')

(OUT / 'part_files.json').write_text(json.dumps(part_files, ensure_ascii=False))
print('part files', part_files)
for w in warn: print('WARN', w)
tot = 0
for f in list((OUT / 'front').glob('*.md')) + list((OUT / 'parts').glob('*.md')) + list((OUT / 'back').glob('*.md')):
    tot += han(f.read_text(encoding='utf-8'))
print('汉字 total', tot)
