#!/usr/bin/env python3
"""由 content.json 生成 tools/book_unit/m411.json（build_unit_411.py 的配置）。"""
import json, sys
from pathlib import Path
C = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
cfg = {
 'number': 411, 'slug': 'che-kaichu-nongchang', 'title': '车开出农场之后', 'subtitle': 'AI、新知识与意义财富的发生', 'authors': ['王德生'],
 'isbn': '979-8-90690-411-9', 'price': 'US$23.00', 'partWord': '篇', 'partsWord': '导论、五篇', 'sourceEdition': '初版（2026-10-22）',
 'unitRev': '20261022-m411-unit-v1', 'assetVersion': '20261022a', 'manuscript': 'tools/book-m411/book.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agentEpithet'], 'bookMeta': C['bookMeta'], 'heroTagline': C['heroTagline'],
 'practiceWord': C['practiceWord'], 'pdfBg': '#16253d',
 'learningPdfUrl': 'https://sdeuniverses.com/books/m/411/downloads/che-kaichu-nongchang-learning-v1.0.pdf',
 'readerPdfUrl': 'https://sdeuniverses.com/books/m/411/che-kaichu-nongchang-reader.pdf',
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
Path('tools/book_unit/m411.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
