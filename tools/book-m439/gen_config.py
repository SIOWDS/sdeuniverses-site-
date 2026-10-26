#!/usr/bin/env python3
"""由 content.json 生成 tools/book_unit/m439.json（build_unit_439.py 的配置）。用法（仓库根）：python3 tools/book-m439/gen_config.py tools/book-m439/content.json"""
import json, sys
from pathlib import Path
C = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
cfg = {
 'number': 439, 'slug': 'weilai-zhishi-jingji', 'title': '未来的知识经济主流产业：从母本到「我的……」', 'subtitle': '从母本到「我的……」', 'authors': ['王德生'],
 'isbn': '979-8-90690-439-3', 'price': 'US$20.00', 'partWord': '编', 'structureLabel': '导论 · 四编十二章 · 结语',
 'sourceEdition': '定稿 V1.0（2026-10-26）',
 'unitRev': '20261026-m439-unit-v1', 'assetVersion': '20261026b', 'manuscript': 'tools/book-m439/book-unit.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agent']['epithet'],
 'bookMeta': '《未来的知识经济主流产业——从母本到「我的……」》 · 王德生著 · 第439卷 · ISBN 979-8-90690-439-3 · 2026年10月第1版',
 'heroTagline': C['heroTagline'], 'practiceWord': '写我的字', 'pdfBg': '#0E2238',
 'learningPdfUrl': 'https://sdeuniverses.com/books/m/439/downloads/weilai-zhishi-jingji-learning-v1.0.pdf',
 'readerPdfUrl': 'https://sdeuniverses.com/books/m/439/weilai-zhishi-jingji-reader.pdf',
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
Path('tools/book_unit/m439.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
