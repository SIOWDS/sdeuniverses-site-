#!/usr/bin/env python3
"""由 content.json 生成 tools/book_unit/m497.json（build_unit_497.py 的配置）。"""
import json, sys
from pathlib import Path
C = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
cfg = {
 'number': 497, 'slug': 'shijingxue-geming', 'title': '释经学的典范革命', 'subtitle': '从发现学到发生学', 'authors': ['王德生'],
 'isbn': '979-8-90690-497-3', 'price': 'US$23.00', 'partWord': '编', 'partsWord': '十编', 'sourceEdition': '三审定稿（2026-10-22）',
 'unitRev': '20261022-m497-unit-v1', 'assetVersion': '20261022a', 'manuscript': 'tools/book-m497/book.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agentEpithet'], 'bookMeta': C['bookMeta'], 'heroTagline': C['heroTagline'],
 'practiceWord': C['practiceWord'], 'pdfBg': '#16253d',
 'learningPdfUrl': 'https://sdeuniverses.com/books/m/497/downloads/shijingxue-geming-learning-v1.0.pdf',
 'readerPdfUrl': 'https://sdeuniverses.com/books/m/497/shijingxue-geming-reader.pdf',
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
Path('tools/book_unit/m497.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
