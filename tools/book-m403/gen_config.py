#!/usr/bin/env python3
"""由 tools/book-m403/content.json 生成 tools/book_unit/m403.json（build_unit_403.py 的配置）。在仓库根目录运行。"""
import json
from pathlib import Path
C = json.loads(Path('tools/book-m403/content.json').read_text(encoding='utf-8'))
cfg = {
 'number': 403, 'slug': 'luoji-fasheng', 'title': '逻辑发生', 'subtitle': '好戏为什么意料之外、情理之中、正中心坎', 'authors': ['王德生'],
 'isbn': '979-8-90690-952-7', 'price': 'US$23.00', 'partWord': '篇', 'sourceEdition': '初版（2026-10-22）',
 'unitRev': '20261022-m403-unit-v1', 'assetVersion': '20261022a', 'manuscript': 'tools/book-m403/book.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agentEpithet'], 'bookMeta': C['bookMeta'], 'heroTagline': C['heroTagline'],
 'practiceWord': C['practiceWord'], 'pdfBg': '#16253d',
 'learningPdfUrl': 'https://sdeuniverses.com/books/m/403/downloads/luoji-fasheng-learning-v1.0.pdf',
 'readerPdfUrl': 'https://sdeuniverses.com/books/m/403/luoji-fasheng-reader.pdf',
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
Path('tools/book_unit/m403.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
