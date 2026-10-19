#!/usr/bin/env python3
"""由 content.json 生成 tools/book_unit/m444.json（build_unit.py 的配置）。"""
import json, sys
from pathlib import Path
C = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
cfg = {
 'number': 444, 'slug': 'yeli-shi-shenme', 'title': '业力是什么', 'subtitle': '消业与用业', 'authors': ['胡敏'],
 'isbn': '979-8-90690-388-4', 'price': 'US$20', 'partWord': '编', 'sourceEdition': '初版（2026-10-19）',
 'unitRev': '20261019-m444-unit-v1', 'assetVersion': '20261019a', 'manuscript': 'tools/book-m444/book.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agentEpithet'], 'bookMeta': C['bookMeta'], 'heroTagline': C['heroTagline'],
 'practiceWord': C['practiceWord'], 'pdfBg': '#16253d',
 'learningPdfUrl': 'https://sdeuniverses.com/books/m/444/downloads/yeli-shi-shenme-learning-v1.0.pdf',
 'readerPdfUrl': 'https://sdeuniverses.com/books/m/444/yeli-shi-shenme-reader.pdf',
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
Path('tools/book_unit/m444.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
