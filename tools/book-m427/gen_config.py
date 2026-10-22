#!/usr/bin/env python3
"""由 content.json 生成 tools/book_unit/m427.json（build_unit_427.py 的配置）。"""
import json, sys
from pathlib import Path
C = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
cfg = {
 'number': 427, 'slug': 'fanchou-sde', 'title': '范畴的SDE解构入门', 'subtitle': '慢到被当成发现的发生', 'authors': ['王德生'],
 'isbn': '979-8-90690-838-4', 'price': 'US$20.00', 'partWord': '部', 'partsWord': '导论与四部', 'sourceEdition': '初稿 v1.0（2026-10-22）',
 'unitRev': '20261022-m427-unit-v1', 'assetVersion': '20261022a', 'manuscript': 'tools/book-m427/book.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agentEpithet'], 'bookMeta': C['bookMeta'], 'heroTagline': C['heroTagline'],
 'practiceWord': C['practiceWord'], 'pdfBg': '#16253d',
 'learningPdfUrl': 'https://sdeuniverses.com/books/m/427/downloads/fanchou-sde-learning-v1.0.pdf',
 'readerPdfUrl': 'https://sdeuniverses.com/books/m/427/fanchou-sde-reader.pdf',
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
Path('tools/book_unit/m427.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
