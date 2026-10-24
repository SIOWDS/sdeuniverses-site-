#!/usr/bin/env python3
"""第 512 号《班级之美》（由第 421 号 gen_config.py 改来）：由 content.json 生成 tools/book_unit/m512.json（build_unit_512.py 的配置）。"""
import json, sys
from pathlib import Path
C = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
cfg = {
 'number': 512, 'slug': 'banji-zhimei', 'title': '班级之美', 'subtitle': '同一性谱系发生学', 'authors': ['柴翱', '刘华杰'],
 'isbn': '979-8-90690-512-3', 'price': 'US$23.00', 'partWord': '编', 'sourceEdition': '初版（2026-10-24）',
 'unitRev': '20261024-m512-unit-v1', 'assetVersion': '20261024a', 'manuscript': 'tools/book-m512/book.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agentEpithet'], 'bookMeta': C['bookMeta'], 'heroTagline': C['heroTagline'],
 'practiceWord': C['practiceWord'], 'pdfBg': '#16253d',
 'learningPdfUrl': 'https://sdeuniverses.com/books/m/512/downloads/banji-zhimei-learning-v1.0.pdf',
 'readerPdfUrl': 'https://sdeuniverses.com/books/m/512/banji-zhimei-reader.pdf',
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
Path('tools/book_unit/m512.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
