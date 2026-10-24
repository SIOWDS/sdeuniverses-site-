#!/usr/bin/env python3
"""由 content.json 生成 tools/book_unit/m421.json（build_unit_491.py 的配置）。"""
import json, sys
from pathlib import Path
C = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
cfg = {
 'number': 421, 'slug': 'guang-de-kexue-zhiwai', 'title': '光的科学之外', 'subtitle': '视觉科学的代签与触觉、听觉科学的新生', 'authors': ['王德生'],
 'isbn': '979-8-90690-027-2', 'price': 'US$23.00', 'partWord': '编', 'sourceEdition': '初版（2026-10-24）',
 'unitRev': '20261024-m421-unit-v1', 'assetVersion': '20261024a', 'manuscript': 'tools/book-m421/book.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agentEpithet'], 'bookMeta': C['bookMeta'], 'heroTagline': C['heroTagline'],
 'practiceWord': C['practiceWord'], 'pdfBg': '#16253d',
 'learningPdfUrl': 'https://sdeuniverses.com/books/m/421/downloads/guang-de-kexue-zhiwai-learning-v1.0.pdf',
 'readerPdfUrl': 'https://sdeuniverses.com/books/m/421/guang-de-kexue-zhiwai-reader.pdf',
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
Path('tools/book_unit/m421.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
