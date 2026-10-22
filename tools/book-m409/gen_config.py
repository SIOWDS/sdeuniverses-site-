#!/usr/bin/env python3
"""由 tools/book-m409/content.json 生成 tools/book_unit/m409.json（build_unit_364.py 的配置）。在仓库根目录运行。"""
import json
from pathlib import Path
C = json.loads(Path('tools/book-m409/content.json').read_text(encoding='utf-8'))
cfg = {
 'number': 409, 'slug': 'jiaoyu-de-chanpin', 'title': '教育的产品是结晶', 'subtitle': 'AI 时代，为什么学了却没学会', 'authors': ['王德生'],
 'isbn': '979-8-90690-409-6', 'price': 'US$23.00', 'partWord': '编', 'sourceEdition': '初版（2026-10-22）',
 'unitRev': '20261022-m409-unit-v1', 'assetVersion': '20261022a', 'manuscript': 'tools/book-m409/book.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agentEpithet'], 'bookMeta': C['bookMeta'], 'heroTagline': C['heroTagline'],
 'practiceWord': C['practiceWord'], 'pdfBg': '#16253d',
 'learningPdfUrl': 'https://sdeuniverses.com/books/m/409/downloads/jiaoyu-de-chanpin-learning-v1.0.pdf',
 'readerPdfUrl': 'https://sdeuniverses.com/books/m/409/jiaoyu-de-chanpin-reader.pdf',
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
Path('tools/book_unit/m409.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
