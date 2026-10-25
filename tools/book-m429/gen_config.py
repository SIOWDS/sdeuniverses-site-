#!/usr/bin/env python3
"""由 content.json 生成 tools/book_unit/m429.json（build_unit_429.py 的配置）。用法（仓库根）：python3 tools/book-m429/gen_config.py tools/book-m429/content.json"""
import json, sys
from pathlib import Path
C = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
cfg = {
 'number': 429, 'slug': 'jibushikuai', 'title': '急不是快：SDE方法论的简阉', 'subtitle': 'SDE方法论的简阉', 'authors': ['王德生', '邬燕琴'],
 'isbn': '979-8-90690-429-4', 'price': 'US$20.00', 'partWord': '编', 'structureLabel': '导论 · 上中下三编 · 收束 · 十二章',
 'sourceEdition': '三审定稿 V1.0（2026-10-26）',
 'unitRev': '20261026-m429-unit-v1', 'assetVersion': '20261026a', 'manuscript': 'tools/book-m429/book-unit.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agent']['epithet'],
 'bookMeta': '《急不是快——SDE方法论的简阉》 · 王德生、邬燕琴著 · 第429卷 · ISBN 979-8-90690-429-4 · 2026年10月第1版',
 'heroTagline': C['heroTagline'], 'practiceWord': '拆急', 'pdfBg': '#0E2238',
 'learningPdfUrl': 'https://sdeuniverses.com/books/m/429/downloads/jibushikuai-learning-v1.0.pdf',
 'readerPdfUrl': 'https://sdeuniverses.com/books/m/429/jibushikuai-reader.pdf',
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
Path('tools/book_unit/m429.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
