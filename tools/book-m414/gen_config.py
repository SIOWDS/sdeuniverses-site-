#!/usr/bin/env python3
"""由 content.json 生成 tools/book_unit/m414.json（build_unit_414.py 的配置）。"""
import json, sys
from pathlib import Path
C = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
cfg = {
 'number': 414, 'slug': 'sde-agent-what-can-it-do', 'title': 'SDE智能体到底能做什么？', 'subtitle': '信息与知识的发生学', 'authors': ['王德生'],
 'isbn': '979-8-90690-420-1', 'price': 'US$23.00', 'partWord': '编', 'sourceEdition': '初版（2026-10-22）',
 'unitRev': '20261022-m414-unit-v1', 'assetVersion': '20261022a', 'manuscript': 'tools/book-m414/book.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agentEpithet'], 'bookMeta': C['bookMeta'], 'heroTagline': C['heroTagline'],
 'practiceWord': C['practiceWord'], 'pdfBg': '#16253d',
 'learningPdfUrl': 'https://sdeuniverses.com/books/m/414/downloads/sde-agent-what-can-it-do-learning-v1.0.pdf',
 'readerPdfUrl': 'https://sdeuniverses.com/books/m/414/sde-agent-what-can-it-do-reader.pdf',
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
Path('tools/book_unit/m414.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
