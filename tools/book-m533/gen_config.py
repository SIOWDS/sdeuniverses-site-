#!/usr/bin/env python3
"""第 533 号《精益求精的空转》（由第 546 号 gen_config.py 改来）：由 content.json 生成 tools/book_unit/m533.json（build_unit_533.py 的配置）。
用法（仓库根目录）：python3 tools/book-m533/gen_config.py tools/book-m533/content.json
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import meta as M  # noqa: E402
C = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
U = 'https://sdeuniverses.com/books/m/%d/' % M.NO
cfg = {
 'number': M.NO, 'slug': M.SLUG, 'title': M.TITLE, 'subtitle': M.SUBTITLE, 'authors': M.AUTHORS, 'advisor': '',
 'isbn': M.ISBN, 'price': M.PRICE, 'partWord': '编', 'sourceEdition': '成稿（%s）' % M.DATE,
 'unitRev': M.UNIT_REV, 'assetVersion': M.V, 'manuscript': 'tools/book-m533/book.md',
 'agentName': C['agent']['name'], 'agentEpithet': C['agentEpithet'], 'bookMeta': C['bookMeta'], 'heroTagline': C['heroTagline'],
 'practiceWord': C['practiceWord'], 'pdfBg': '#16253d',
 'learningPdfUrl': U + 'learning-pack.pdf?v=' + M.V, 'learningDocxUrl': U + 'learning-pack.docx?v=' + M.V,
 'readerPdfUrl': M.READER_PDF, 'printPdfUrl': M.PRINT_PDF, 'tier': M.TIER,
 'authorship': '王德生 著：立题、承重命题与裁定出自王德生口述；正文由 AI（Claude）执笔与统稿，经质检；同一底座的执笔者与检查者不能互作独立证据；无独立学术评审，无用户试验。',
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
Path('tools/book_unit/m%d.json' % M.NO).write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
