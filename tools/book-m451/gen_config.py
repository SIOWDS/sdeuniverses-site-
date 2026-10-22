#!/usr/bin/env python3
"""由 content.json 生成 tools/book_unit/m451.json（build_unit_451.py 的配置）。"""
import json, sys
from pathlib import Path
C = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
cfg = {
 'number': 451, 'slug': 'fasheng-shicha', 'title': '发生的时差', 'subtitle': '普通人都能懂的快慢之学', 'authors': ['王德生'],
 'isbn': '979-8-90690-451-5', 'price': 'US$23.00', 'partWord': '编', 'partsWord': '七编', 'sourceEdition': '三审定稿 v1.0（2026-10-22）',
 'unitRev': '20261022-m451-unit-v1', 'assetVersion': '20261022a', 'manuscript': 'tools/book-m451/book.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agentEpithet'], 'bookMeta': C['bookMeta'], 'heroTagline': C['heroTagline'],
 'practiceWord': C['practiceWord'], 'pdfBg': '#16284E',
 'learningPdfUrl': 'https://sdeuniverses.com/books/m/451/downloads/fasheng-shicha-learning-v1.0.pdf',
 'readerPdfUrl': 'https://sdeuniverses.com/books/m/451/fasheng-shicha-reader.pdf',
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
Path('tools/book_unit/m451.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
