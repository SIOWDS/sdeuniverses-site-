#!/usr/bin/env python3
"""由 content.json 生成 tools/book_unit/m491.json（build_unit_491.py 的配置）。"""
import json, sys
from pathlib import Path
C = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
cfg = {
 'number': 491, 'slug': 'huidian-dansheng', 'title': 'SDE平台：慧店的诞生', 'subtitle': '让天下没有难发生的知识', 'authors': ['王德生'],
 'isbn': '979-8-90690-150-7', 'price': 'US$20.00', 'partWord': '编', 'sourceEdition': '初版（2026-10-20）',
 'unitRev': '20261020-m491-unit-v1', 'assetVersion': '20261020h', 'manuscript': 'tools/book-m491/book.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agentEpithet'], 'bookMeta': C['bookMeta'], 'heroTagline': C['heroTagline'],
 'practiceWord': C['practiceWord'], 'pdfBg': '#16253d',
 'learningPdfUrl': 'https://sdeuniverses.com/books/m/491/downloads/huidian-dansheng-learning-v1.0.pdf',
 'readerPdfUrl': 'https://sdeuniverses.com/books/m/491/huidian-dansheng-reader.pdf',
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
Path('tools/book_unit/m491.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
