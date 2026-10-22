#!/usr/bin/env python3
"""由 content.json 生成 tools/book_unit/m438.json（build_unit_438.py 的配置）。用法（仓库根）：python3 tools/book-m438/gen_config.py tools/book-m438/content.json"""
import json, sys
from pathlib import Path
C = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
cfg = {
 'number': 438, 'slug': 'dialogue-semiogenesis', 'title': '大模型是索绪尔的网、皮尔斯的链：符号在对话中才发生', 'subtitle': 'SDE 符号学系列 · 理论卷四', 'authors': ['王德生'],
 'isbn': '979-8-90690-614-4', 'price': 'US$23.00', 'partWord': '编', 'sourceEdition': '初版（2026-10-22）',
 'unitRev': '20261022-m438-unit-v1', 'assetVersion': '20261022a', 'manuscript': 'tools/book-m438/book.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agentEpithet'], 'bookMeta': C['bookMeta'], 'heroTagline': C['heroTagline'],
 'practiceWord': C['practiceWord'], 'pdfBg': '#0B1230',
 'learningPdfUrl': 'https://sdeuniverses.com/books/m/438/downloads/dialogue-semiogenesis-learning-v1.0.pdf',
 'readerPdfUrl': 'https://sdeuniverses.com/books/m/438/dialogue-semiogenesis-reader.pdf',
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
Path('tools/book_unit/m438.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
