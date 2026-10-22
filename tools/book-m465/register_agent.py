#!/usr/bin/env python3
"""第 465 号：在 public/books/agents.json 登记专属智能体（名字全站唯一），放核心要点 keypoints.json。
用法（仓库根目录）：python3 tools/book-m465/register_agent.py --content tools/book-m465/content.json --keypoints <keypoints.json>
之后：python3 tools/build_book_rag.py 465 && python3 tools/build_bookshelf.py
"""
import argparse, json, shutil
from pathlib import Path

ROOT = Path.cwd()
NO = '465'
ap = argparse.ArgumentParser(); ap.add_argument('--content', required=True); ap.add_argument('--keypoints', required=True)
A = ap.parse_args()
C = json.loads(Path(A.content).read_text(encoding='utf-8'))
p = ROOT / 'public/books/agents.json'
d = json.loads(p.read_text(encoding='utf-8'))
name = C['agent']['name']
clash = [k for k, v in d['agents'].items() if isinstance(v, dict) and v.get('name') == name and k != NO]
assert not clash, f'智能体名「{name}」已被第 {clash} 号使用'
d['agents'][NO] = {'name': name, 'epithet': C['agentEpithet'], 'intro': C['intro'], 'starts': C['starts']}
p.write_text(json.dumps(d, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
dst = ROOT / f'public/books/m/{NO}/keypoints.json'
shutil.copy(A.keypoints, dst)
print('registered', name, '->', NO)
