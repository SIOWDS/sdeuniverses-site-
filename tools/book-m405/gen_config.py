#!/usr/bin/env python3
"""由 content.json 生成 tools/book_unit/m405.json（build_unit_405.py 的配置）。用法：python3 tools/book-m405/gen_config.py content.json"""
import json, sys
from pathlib import Path
C = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
cfg = {
 'number': 405, 'slug': 'sde-fuhaoxue', 'title': 'SDE符号学：超越皮尔斯的三元与索绪尔的二元', 'subtitle': 'SDE 符号学系列 · 理论卷二', 'authors': ['王德生'],
 'isbn': '979-8-90690-405-8', 'price': 'US$23.00', 'partWord': '编', 'sourceEdition': '三审定稿（2026-10-22）',
 'unitRev': '20261022-m405-unit-v1', 'assetVersion': '20261022a', 'manuscript': 'tools/book-m405/book.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agent']['epithet'],
 'bookMeta': '《SDE符号学：超越皮尔斯的三元与索绪尔的二元》 · 王德生著 · 第405卷 · ISBN 979-8-90690-405-8 · 2026年10月第1版',
 'heroTagline': C['heroTagline'], 'practiceWord': '拆符号', 'pdfBg': '#142746',
 'learningPdfUrl': 'https://sdeuniverses.com/books/m/405/downloads/sde-fuhaoxue-learning-v1.0.pdf',
 'readerPdfUrl': 'https://sdeuniverses.com/books/m/405/sde-fuhaoxue-reader.pdf',
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
Path('tools/book_unit/m405.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
