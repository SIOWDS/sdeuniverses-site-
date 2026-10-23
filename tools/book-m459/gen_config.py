#!/usr/bin/env python3
"""由 content.json 生成 tools/book_unit/m459.json（build_unit_459.py 的配置）。用法：python3 tools/book-m459/gen_config.py content.json"""
import json, sys
from pathlib import Path
C = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
cfg = {
 'number': 459, 'slug': 'bingren-huayandan', 'title': '病人不是一张化验单：检验单、指南与身体为什么总对不上', 'subtitle': 'SDE 符号学系列 · 应用五', 'authors': ['王德生'],
 'isbn': '979-8-90690-712-7', 'price': 'US$23.00', 'partWord': '编', 'sourceEdition': '统稿定稿（2026-10-23）',
 'unitRev': '20261023-m459-unit-v1', 'assetVersion': '20261023a', 'manuscript': 'tools/book-m459/book.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agent']['epithet'],
 'bookMeta': '《病人不是一张化验单：检验单、指南与身体为什么总对不上》 · 王德生著 · 第459卷 · ISBN 979-8-90690-712-7 · 2026年10月第1版',
 'heroTagline': C['heroTagline'], 'practiceWord': '对账', 'pdfBg': '#142746',
 'learningPdfUrl': 'https://sdeuniverses.com/books/m/459/downloads/bingren-huayandan-learning-v1.0.pdf',
 'readerPdfUrl': 'https://sdeuniverses.com/books/m/459/bingren-huayandan-reader.pdf',
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
Path('tools/book_unit/m459.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
