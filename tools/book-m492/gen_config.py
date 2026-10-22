#!/usr/bin/env python3
"""由 content.json 生成 tools/book_unit/m492.json（build_unit_492.py 的配置）。"""
import json, sys
from pathlib import Path
C = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
cfg = {
 'number': 492, 'slug': 'yidian-sanmen', 'title': '一店三门', 'subtitle': '从作坊、实验室到书房，每个人一生的知识发生', 'authors': ['王德生'],
 'isbn': '979-8-90690-152-1', 'price': 'US$20.00', 'partWord': '编', 'sourceEdition': '初版（2026-10-22）',
 'unitRev': '20261022-m492-unit-v1', 'assetVersion': '20261022a', 'manuscript': 'tools/book-m492/book.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agentEpithet'], 'bookMeta': C['bookMeta'], 'heroTagline': C['heroTagline'],
 'practiceWord': C['practiceWord'], 'pdfBg': '#16253d',
 'learningPdfUrl': 'https://sdeuniverses.com/books/m/492/downloads/yidian-sanmen-learning-v1.0.pdf',
 'readerPdfUrl': 'https://sdeuniverses.com/books/m/492/yidian-sanmen-reader.pdf',
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
Path('tools/book_unit/m492.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
