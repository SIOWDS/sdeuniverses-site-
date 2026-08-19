#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""并库第一步：把 /kb/placeholders.json 的 80 条转成卡源 tools/nbr/cards_d.py。

为什么要并：站上此前有两个近邻库，schema 不同、消费者不同——
  · /nbr/cards.json（prop/alias/src/holds/sep）：金点子、中华智问
  · /kb/placeholders.json（p/a/o/au/y/d/h/s）：碰撞机的候选闸
**两份判据分家一定会漂**，而且漂起来是静默的：一边补了卡另一边不知道，
闸门照样显示"已过闸"，只是它查的那半个库里没有那个人。
这正是当初把 sde-nbr-gate.js 抽成唯一来源要避免的事，在库这一层又发生了一遍。

并法不是把一个塞进另一个，是**一份源、两个投影**：
  tools/nbr/cards_*.py（唯一源）
      ├→ public/nbr/cards.json        （原 schema，金点子/中华智问照旧读）
      └→ public/kb/placeholders.json  （原 schema，碰撞机照旧读）
两边的消费者一行都不用改，而判据只有一处。

本脚本只跑一次（把现有 80 条搬进源），此后新卡直接写进 cards_*.py。
"""
import json, io, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PH = os.path.join(ROOT, 'public/kb/placeholders.json')
OUT = os.path.join(ROOT, 'tools/nbr/cards_d.py')

sys.path.insert(0, os.path.join(ROOT, 'tools/nbr'))
from cards_a import CARDS_A
from cards_b import CARDS_B
from cards_c import CARDS_C
have = CARDS_A + CARDS_B + CARDS_C


def key(author, title):
    a = re.split(r'[,&]', str(author or ''))[0].strip().lower()
    a = re.sub(r'\s+', ' ', a)
    return (a, str(title or '')[:34].lower())


HAVE = {key((c.get('src') or {}).get('author'), (c.get('src') or {}).get('title')) for c in have}

db = json.load(io.open(PH, encoding='utf-8'))
items = db['items']

def q(s):
    """写成 Python 源里的双引号字符串：内部的 ASCII 引号一律换成「」，
    否则会像上一次那样把字符串提前截断（那次连代码行都被正则改坏了）。"""
    s = str(s or '').replace('\\', '').replace('"', '「', 1) if False else str(s or '')
    s = s.replace('\\', '')
    # 成对的 ASCII 双引号 → 「」
    parts = s.split('"')
    if len(parts) % 2 == 1 and len(parts) > 1:
        out = parts[0]
        for i in range(1, len(parts), 2):
            out += '「' + parts[i] + '」' + parts[i + 1]
        s = out
    s = s.replace('"', '”')          # 落单的一个，换成中文引号
    return '"' + s + '"'


rows, skipped = [], []
for it in items:
    k = key(it.get('au'), it.get('o'))
    if k in HAVE:
        skipped.append(it['id'])
        continue
    HAVE.add(k)
    alias = [a for a in (it.get('a') or []) if a]
    # sep：原库是一个字符串，切成列表；一条也拿不到时给一句诚实的占位
    s_raw = str(it.get('s') or '').strip()
    seps = [x.strip() for x in re.split(r'[；;]\s*', s_raw) if x.strip()] or \
           ['（本卡由占位者库并入时未带分离线，使用前必须补一条可裁决的分离线）']
    rows.append(dict(
        pid=it['id'], ring=str(it.get('d') or '未分类'),
        prop=str(it.get('p') or ''), alias=alias,
        author=str(it.get('au') or ''), title=str(it.get('o') or ''),
        # y 不一定是整数：库里有 "1997/2007" 这种（初版/修订版）。取第一个四位年，取不到记 0。
        year=(lambda v: int(re.search(r'(1[6-9]|20)\d{2}', str(v)).group(0))
              if re.search(r'(1[6-9]|20)\d{2}', str(v)) else 0)(it.get('y')),
        holds=str(it.get('h') or ''),
        sep=seps, verify='verified' if '核验' in str(it.get('v') or '') else 'unverified',
    ))

src = ['# -*- coding: utf-8 -*-',
       '"""近邻库种子·D 批：由 /kb/placeholders.json 并入（2026-08-01）。',
       '',
       '并库的理由写在 tools/merge_placeholder_cards.py 里：站上曾有两个近邻库，',
       'schema 不同、消费者不同，而**两份判据分家一定会漂，且漂起来是静默的**。',
       '现在只有这一处源，两个 json 都是它的投影。',
       '',
       '⚠ pid 是这张卡在占位者库里的原 id（语义 slug），投影回 placeholders.json 时要原样用，',
       '   否则碰撞机那边的引用会全部断掉。',
       '"""', '', 'CARDS_D = [']
for i, r in enumerate(rows, 1):
    src.append(' dict(id="nbr-%04d", pid=%s, ring=%s,' % (400 + i, q(r['pid']), q(r['ring'])))
    src.append('  prop=%s,' % q(r['prop']))
    src.append('  alias=[%s],' % ', '.join(q(a) for a in r['alias']))
    src.append('  src=dict(author=%s, title=%s, year=%d),' % (q(r['author']), q(r['title']), r['year']))
    src.append('  holds=%s,' % q(r['holds']))
    src.append('  sep=[%s],' % ',\n       '.join(q(x) for x in r['sep']))
    src.append('  verify=%s, frm="占位者库并入"),' % q(r['verify']))
    src.append('')
src.append(']')
io.open(OUT, 'w', encoding='utf-8').write('\n'.join(src) + '\n')
print(f'占位者库 {len(items)} 条 → 新增 {len(rows)} 张（与已有重复 {len(skipped)} 张，跳过）')
print('写出', OUT)
