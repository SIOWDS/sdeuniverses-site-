#!/usr/bin/env python3
"""第 455 号《晕痛苦》（工具链照五二〇号 gen_config.py）：由 content.json 生成 tools/book_unit/m455.json（build_unit_455.py 的配置）。
用法（仓库根目录）：python3 tools/book-m455/gen_config.py tools/book-m455/content.json
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import meta as M  # noqa: E402
C = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
U = 'https://sdeuniverses.com/books/m/%d/' % M.NO
cfg = {
 'number': M.NO, 'slug': M.SLUG, 'title': M.TITLE, 'subtitle': M.SUBTITLE, 'authors': M.AUTHORS,
 'isbn': M.ISBN, 'price': M.PRICE, 'partWord': '编', 'sourceEdition': '初版（%s）' % M.DATE,
 'unitRev': M.UNIT_REV, 'assetVersion': M.V, 'manuscript': 'tools/book-m455/book.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agentEpithet'], 'bookMeta': C['bookMeta'], 'heroTagline': C['heroTagline'],
 'practiceWord': C['practiceWord'], 'pdfBg': '#16253d',
 'learningPdfUrl': U + 'downloads/%s-learning-v1.0.pdf' % M.SLUG,
 'readerPdfUrl': U + '%s-reader.pdf' % M.SLUG,
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
Path('tools/book_unit/m%d.json' % M.NO).write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
