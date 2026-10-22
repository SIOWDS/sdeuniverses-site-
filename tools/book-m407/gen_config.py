#!/usr/bin/env python3
"""由 content.json 生成 tools/book_unit/m407.json（build_unit_491.py 的配置）。"""
import json, sys
from pathlib import Path
C = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
cfg = {
 'number': 407, 'slug': 'kejin-shijie-gongshi', 'title': '被刻进世界的公式', 'subtitle': '科学的符号学', 'authors': ['王德生'],
 'isbn': '979-8-90690-407-2', 'price': 'US$23.00', 'partWord': '编', 'sourceEdition': '三审定稿（2026-10-22）',
 'unitRev': '20261022-m407-unit-v1', 'assetVersion': '20261022a', 'manuscript': 'tools/book-m407/book.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agentEpithet'], 'bookMeta': C['bookMeta'], 'heroTagline': C['heroTagline'],
 'practiceWord': C['practiceWord'], 'pdfBg': '#16253d',
 'learningPdfUrl': 'https://sdeuniverses.com/books/m/407/downloads/kejin-shijie-gongshi-learning-v1.0.pdf',
 'readerPdfUrl': 'https://sdeuniverses.com/books/m/407/kejin-shijie-gongshi-reader.pdf',
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
Path('tools/book_unit/m407.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
