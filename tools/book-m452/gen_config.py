#!/usr/bin/env python3
"""由 tools/book-m452/content.json 生成 tools/book_unit/m452.json（build_unit_452.py 的配置）。在仓库根目录运行。"""
import json
from pathlib import Path
C = json.loads(Path('tools/book-m452/content.json').read_text(encoding='utf-8'))
cfg = {
 'number': 452, 'slug': 'shei-zai-gei-shan-jizhang', 'title': '谁在给善记账', 'subtitle': '学校制度的道德发生学', 'authors': ['刘华杰'],
 'isbn': '979-8-90690-108-8', 'price': 'US$15.00', 'partWord': '编', 'sourceEdition': '初版三审定稿（2026-10-24）',
 'unitRev': '20261024-m452-unit-v1', 'assetVersion': '20261024a', 'manuscript': 'tools/book-m452/book.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agentEpithet'], 'bookMeta': C['bookMeta'], 'heroTagline': C['heroTagline'],
 'practiceWord': C['practiceWord'], 'pdfBg': '#16253d',
 'learningPdfUrl': 'https://sdeuniverses.com/books/m/452/downloads/shei-zai-gei-shan-jizhang-learning-v1.0.pdf',
 'readerPdfUrl': 'https://sdeuniverses.com/books/m/452/shei-zai-gei-shan-jizhang-reader.pdf',
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
Path('tools/book_unit/m452.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
