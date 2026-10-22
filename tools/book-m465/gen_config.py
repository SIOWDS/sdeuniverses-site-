#!/usr/bin/env python3
"""由 content.json 生成 tools/book_unit/m465.json（build_unit_465.py 的配置）。由第 492 号改来。"""
import json, sys
from pathlib import Path
C = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
cfg = {
 'number': 465, 'slug': 'daan-zhu-zai-nali', 'title': '答案住在哪里', 'subtitle': '希腊三哲与两千年哲学的纠缠史', 'authors': ['王德生'],
 'isbn': '979-8-90690-465-2', 'price': 'US$23.00', 'partWord': '编', 'sourceEdition': '初版（2026-10-22）',
 'unitRev': '20261022-m465-unit-v1', 'assetVersion': '20261022a', 'manuscript': 'tools/book-m465/book.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agentEpithet'], 'bookMeta': C['bookMeta'], 'heroTagline': C['heroTagline'],
 'practiceWord': C['practiceWord'], 'pdfBg': '#16253d',
 'learningPdfUrl': 'https://sdeuniverses.com/books/m/465/downloads/daan-zhu-zai-nali-learning-v1.0.pdf',
 'readerPdfUrl': 'https://sdeuniverses.com/books/m/465/daan-zhu-zai-nali-reader.pdf',
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
Path('tools/book_unit/m465.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
