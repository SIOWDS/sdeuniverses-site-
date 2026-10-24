#!/usr/bin/env python3
"""由 content.json 生成 tools/book_unit/m420.json（build_unit_420.py 的配置）。用法（仓库根目录）：python3 tools/book-m420/gen_config.py tools/book-m420/content.json"""
import json, sys
from pathlib import Path
C = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
cfg = {
 'number': 420, 'slug': 'yijuhua-huoqilai', 'title': '一句话是怎么活起来的', 'subtitle': '普通人都能懂的英语语法', 'authors': ['麦子'],
 'isbn': '979-8-90690-600-7', 'price': 'US$20.00', 'partWord': '编', 'partsWord': '六编', 'sourceEdition': '三审定稿 v1.0（2026-10-24）',
 'unitRev': '20261024-m420-unit-v1', 'assetVersion': '20261024a', 'manuscript': 'tools/book-m420/book.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agentEpithet'], 'bookMeta': C['bookMeta'], 'heroTagline': C['heroTagline'],
 'practiceWord': C['practiceWord'], 'pdfBg': '#16284E',
 'learningPdfUrl': 'https://sdeuniverses.com/books/m/420/downloads/yijuhua-huoqilai-learning-v1.0.pdf',
 'readerPdfUrl': 'https://sdeuniverses.com/books/m/420/yijuhua-huoqilai-reader.pdf',
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
assert len(cfg['tasks']) == 20
Path('tools/book_unit/m420.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
