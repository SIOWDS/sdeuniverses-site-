#!/usr/bin/env python3
"""第 428 号《这把不算》（由第 423 号 gen_config.py 改来）：由 content.json 生成 tools/book_unit/m428.json（build_unit.py 的配置）。
用法（仓库根目录）：python3 tools/book-m428/gen_config.py tools/book-m428/content.json"""
import json, sys
from pathlib import Path
C = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
cfg = {
 'number': 428, 'slug': 'zhebabusuan', 'title': '这把不算', 'subtitle': '玩的发生学', 'authors': ['柴翱'],
 'isbn': '979-8-90690-428-7', 'price': 'US$20.00', 'partWord': '编', 'sourceEdition': '第一版（2026-10-25）',
 'unitRev': '20261025-m428-unit-v1', 'assetVersion': '20261025b', 'manuscript': 'tools/book-m428/book.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agentEpithet'], 'bookMeta': C['bookMeta'], 'heroTagline': C['heroTagline'],
 'practiceWord': C['practiceWord'], 'pdfBg': '#1d2b4c',
 'learningPdfUrl': 'https://sdeuniverses.com/books/m/428/downloads/zhebabusuan-learning-v1.0.pdf',
 'readerPdfUrl': 'https://sdeuniverses.com/books/m/428/zhebabusuan-reader.pdf',
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
Path('tools/book_unit/m428.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
