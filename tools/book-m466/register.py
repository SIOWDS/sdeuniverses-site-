#!/usr/bin/env python3
"""第 466 号《认》（由第 520 号 register.py 改来）：写 keypoints.json，并在 public/books/agents.json 登记本书的智能体。
在仓库根目录运行：python3 tools/book-m466/register.py
"""
import datetime
import json
from pathlib import Path

NO = 466
C = json.loads(Path('tools/book-m466/content.json').read_text(encoding='utf-8'))
today = datetime.date.today().isoformat()

kp = {'no': NO, 'title': '普通人都能明白的「认」', 'built': today,
      'items': [{'t': x['t'], 'x': x['x'], 'ch': x['ch']} for x in C['keypoints']]}
p = Path('public/books/m/%d/keypoints.json' % NO)
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(kp, ensure_ascii=False) + '\n', encoding='utf-8')

ap = Path('public/books/agents.json')
reg = json.loads(ap.read_text(encoding='utf-8'))
name = C['agent']['name']
clash = [k for k, v in reg['agents'].items() if v.get('name') == name and k != str(NO)]
assert not clash, '智能体重名：%s' % clash
reg['agents'][str(NO)] = {'name': name, 'epithet': C['agentEpithet'], 'intro': C['agentIntro'], 'starts': C['agentStarts']}
for k in ('updatedAt', 'updated'):
    if k in reg:
        reg[k] = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') if k == 'updatedAt' else today
ap.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print('keypoints', len(kp['items']), 'agent', name)
