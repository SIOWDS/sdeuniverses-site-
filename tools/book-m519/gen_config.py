#!/usr/bin/env python3
"""由 content.json 生成 tools/book_unit/m519.json（build_unit_519.py 的配置）。用法（仓库根）：python3 tools/book-m519/gen_config.py tools/book-m519/content.json"""
import json, sys
from pathlib import Path
C = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
cfg = {
 'number': 519, 'slug': 'quanlv-tijiandan', 'title': '一张全绿的体检单：刻痕、标准与日子为什么总对不上', 'subtitle': 'SDE 符号学 · 医疗符号学', 'authors': ['胡敏'],
 'isbn': '979-8-90690-519-2', 'price': 'US$20.00', 'partWord': '编', 'sourceEdition': '胡敏统稿 V3.1（2026-10-25）',
 'unitRev': '20261025-m519-unit-v1', 'assetVersion': '20261025a', 'manuscript': 'tools/book-m519/book.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agent']['epithet'],
 'bookMeta': '《一张全绿的体检单：刻痕、标准与日子为什么总对不上》 · 胡敏著，王德生指导 · 第519卷 · ISBN 979-8-90690-519-2 · 2026年10月第1版',
 'heroTagline': C['heroTagline'], 'practiceWord': '对账', 'pdfBg': '#123528',
 'learningPdfUrl': 'https://sdeuniverses.com/books/m/519/downloads/quanlv-tijiandan-learning-v1.0.pdf',
 'readerPdfUrl': 'https://sdeuniverses.com/books/m/519/quanlv-tijiandan-reader.pdf',
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
Path('tools/book_unit/m519.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
