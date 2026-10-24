#!/usr/bin/env python3
"""由 content.json 生成 tools/book_unit/m419.json（build_unit_419.py 的配置）。用法（仓库根目录）：python3 tools/book-m419/gen_config.py tools/book-m419/content.json"""
import json, sys
from pathlib import Path
C = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
cfg = {
 'number': 419, 'slug': 'zheci-shuiqu', 'title': '这次谁去', 'subtitle': '写给每一位母亲', 'authors': ['刘春华'],
 'isbn': '979-8-90690-987-9', 'price': 'US$20.00', 'partWord': '辑', 'partsWord': '五辑', 'sourceEdition': '三审定稿 v1.0（2026-10-24）',
 'unitRev': '20261024-m419-unit-v1', 'assetVersion': '20261024a', 'manuscript': 'tools/book-m419/book.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agentEpithet'], 'bookMeta': C['bookMeta'], 'heroTagline': C['heroTagline'],
 'practiceWord': C['practiceWord'], 'pdfBg': '#16284E',
 'learningPdfUrl': 'https://sdeuniverses.com/books/m/419/downloads/zheci-shuiqu-learning-v1.0.pdf',
 'readerPdfUrl': 'https://sdeuniverses.com/books/m/419/zheci-shuiqu-reader.pdf',
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
assert len(cfg['tasks']) == 24
Path('tools/book_unit/m419.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
