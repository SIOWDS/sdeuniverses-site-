#!/usr/bin/env python3
"""由 content.json 生成 tools/book_unit/m485.json（build_unit_485.py 的配置）。"""
import json, sys
from pathlib import Path
C = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
cfg = {
 'number': 485, 'slug': 'ci-fasheng-bushi-bi-fasheng', 'title': '此发生不是彼发生', 'subtitle': '普通人都能明白的发生学', 'authors': ['王德生'],
 'isbn': '979-8-90690-156-9', 'price': 'US$20', 'partWord': '篇', 'sourceEdition': '初版（2026-10-20）',
 'unitRev': '20261020-m485-unit-v1', 'assetVersion': '20261020b', 'manuscript': 'tools/book-m485/book.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agentEpithet'], 'bookMeta': C['bookMeta'], 'heroTagline': C['heroTagline'],
 'practiceWord': C['practiceWord'], 'pdfBg': '#16253d',
 'learningPdfUrl': 'https://sdeuniverses.com/books/m/485/downloads/ci-fasheng-bushi-bi-fasheng-learning-v1.0.pdf',
 'readerPdfUrl': 'https://sdeuniverses.com/books/m/485/ci-fasheng-bushi-bi-fasheng-reader.pdf',
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
Path('tools/book_unit/m485.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
