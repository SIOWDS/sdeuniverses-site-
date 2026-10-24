#!/usr/bin/env python3
"""第 420 号：把智能体「换档」登记进 public/books/agents.json，并写 keypoints.json（只增本书条目，不动别的书）。
用法（仓库根目录）：python3 tools/book-m420/register.py
"""
import json, datetime
from pathlib import Path

HERE = Path(__file__).parent
PUB = HERE.resolve().parents[1] / 'public'
X = json.loads((HERE / 'extra.json').read_text(encoding='utf-8'))

p = PUB / 'books' / 'agents.json'
reg = json.loads(p.read_text(encoding='utf-8'))
ag = reg['agents']
assert '420' not in ag, '420 already registered'
assert all(v.get('name') != X['agentEntry']['name'] for v in ag.values()), 'agent name not unique'
ag['420'] = X['agentEntry']
today = datetime.date.today().isoformat()
for k in ('updatedAt', 'updated'):
    if k in reg:
        reg[k] = today
p.write_text(json.dumps(reg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

kp = {'no': 420, 'title': '一句话是怎么活起来的', 'built': today, 'items': X['keypoints']}
(PUB / 'books' / 'm' / '420' / 'keypoints.json').write_text(json.dumps(kp, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print('registered', X['agentEntry']['name'], 'keypoints', len(X['keypoints']))
