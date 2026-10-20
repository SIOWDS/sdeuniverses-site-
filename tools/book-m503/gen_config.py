#!/usr/bin/env python3
"""由 content.json 生成 tools/book_unit/m503.json（build_unit_503.py 的配置）。"""
import json, sys
from pathlib import Path
C = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
cfg = {
 'number': 503, 'slug': 'ai-de-zhenyan-xinjie', 'title': '爱的箴言新解', 'subtitle': '信是内能，望是动能，爱是势能', 'authors': ['王德生'],
 'isbn': '979-8-90690-175-0', 'price': 'US$23.40', 'partWord': '编', 'sourceEdition': '初版（2026-10-20）',
 'unitRev': '20261020-m503-unit-v1', 'assetVersion': '20261020a', 'manuscript': 'tools/book-m503/book.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agentEpithet'], 'bookMeta': C['bookMeta'], 'heroTagline': C['heroTagline'],
 'practiceWord': C['practiceWord'], 'pdfBg': '#16253d',
 'learningPdfUrl': 'https://sdeuniverses.com/books/m/503/downloads/ai-de-zhenyan-xinjie-learning-v1.0.pdf',
 'readerPdfUrl': 'https://sdeuniverses.com/books/m/503/ai-de-zhenyan-xinjie-reader.pdf',
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
Path('tools/book_unit/m503.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
