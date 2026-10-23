#!/usr/bin/env python3
"""第 459 号：把 content.json 的智能体「三栏」写进 public/books/agents.json，并装 keypoints.json。用法（仓库根）：python3 tools/book-m459/register_agent.py /home/claude/vol15/unit/keypoints.json"""
import json, sys, datetime, shutil
from pathlib import Path
HERE = Path(__file__).parent; SITE = HERE.resolve().parents[1] / 'public'
C = json.loads((HERE / 'content.json').read_text()); A = C['agent']
p = SITE / 'books' / 'agents.json'; d = json.loads(p.read_text())
names = {v.get('name') for k, v in d['agents'].items() if k != '459'}
assert A['name'] not in names, '重名：' + A['name']
d['agents']['459'] = {'name': A['name'], 'epithet': A['epithet'], 'intro': A['intro'], 'starts': A['starts']}
d['updatedAt'] = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
shutil.copy(sys.argv[1], SITE / 'books' / 'm' / '459' / 'keypoints.json')
print('agent', A['name'], 'registered; keypoints installed')
