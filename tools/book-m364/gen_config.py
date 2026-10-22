#!/usr/bin/env python3
"""由 tools/book-m364/content.json 生成 tools/book_unit/m364.json（build_unit_364.py 的配置）。在仓库根目录运行。"""
import json
from pathlib import Path
C = json.loads(Path('tools/book-m364/content.json').read_text(encoding='utf-8'))
cfg = {
 'number': 364, 'slug': 'ai-funeng-le-shei', 'title': 'AI赋能了谁？', 'subtitle': '拆开“AI赋能大脑”的六种主流说法', 'authors': ['王德生'],
 'isbn': '979-8-90690-975-6', 'price': 'US$23.00', 'partWord': '编', 'sourceEdition': '初版（2026-10-22）',
 'unitRev': '20261022-m364-unit-v1', 'assetVersion': '20261022a', 'manuscript': 'tools/book-m364/book.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agentEpithet'], 'bookMeta': C['bookMeta'], 'heroTagline': C['heroTagline'],
 'practiceWord': C['practiceWord'], 'pdfBg': '#16253d',
 'learningPdfUrl': 'https://sdeuniverses.com/books/m/364/downloads/ai-funeng-le-shei-learning-v1.0.pdf',
 'readerPdfUrl': 'https://sdeuniverses.com/books/m/364/ai-funeng-le-shei-reader.pdf',
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
Path('tools/book_unit/m364.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
