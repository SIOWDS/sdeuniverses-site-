#!/usr/bin/env python3
"""由 content.json 生成 tools/book_unit/m440.json（build_unit.py 的配置）。"""
import json, sys
from pathlib import Path
C = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
cfg = {
 'number': 440, 'slug': 'jiaguo-bufen', 'title': '家国不分', 'subtitle': '《春秋决狱》与道德的直接国家化', 'authors': ['高鹏'],
 'isbn': '979-8-90690-608-3', 'price': 'US$20', 'partWord': '编', 'sourceEdition': '初版（2026-10-19，终审工作稿）',
 'unitRev': '20261019-m440-unit-v1', 'assetVersion': '20261019a', 'manuscript': 'tools/book-m440/book5.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agentEpithet'], 'bookMeta': C['bookMeta'], 'heroTagline': C['heroTagline'],
 'practiceWord': C['practiceWord'], 'pdfBg': '#16253d',
 'learningPdfUrl': 'https://sdeuniverses.com/books/m/440/downloads/jiaguo-bufen-learning-v1.0.pdf',
 'readerPdfUrl': 'https://sdeuniverses.com/books/m/440/jiaguo-bufen-reader.pdf',
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
Path('tools/book_unit/m440.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
