#!/usr/bin/env python3
"""由 content.json 生成 tools/book_unit/m412.json（build_unit_491.py 的配置）。"""
import json, sys
from pathlib import Path
C = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
cfg = {
 'number': 412, 'slug': 'yaoyan-jiejing', 'title': '谣言是没对过账的结晶', 'subtitle': '后真相时代，谣言为什么比辟谣跑得快', 'authors': ['王德生'],
 'isbn': '979-8-90690-412-6', 'price': 'US$23.00', 'partWord': '编', 'sourceEdition': '初版（2026-10-22）',
 'unitRev': '20261022-m412-unit-v1', 'assetVersion': '20261022a', 'manuscript': 'tools/book-m412/book.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agentEpithet'], 'bookMeta': C['bookMeta'], 'heroTagline': C['heroTagline'],
 'practiceWord': C['practiceWord'], 'pdfBg': '#16253d',
 'learningPdfUrl': 'https://sdeuniverses.com/books/m/412/downloads/yaoyan-jiejing-learning-v1.0.pdf',
 'readerPdfUrl': 'https://sdeuniverses.com/books/m/412/yaoyan-jiejing-reader.pdf',
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
Path('tools/book_unit/m412.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
