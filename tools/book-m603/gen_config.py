#!/usr/bin/env python3
"""第 603 号《AI时代企业本体论的典范转移》（由第 602 号 gen_config.py 改来）：由 content.json 生成 tools/book_unit/m603.json（build_unit_603.py 的配置）。
用法（仓库根目录）：python3 tools/book-m603/gen_config.py tools/book-m603/content.json
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import meta as M  # noqa: E402
C = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
U = 'https://sdeuniverses.com/books/m/%d/' % M.NO
cfg = {
 'number': M.NO, 'slug': M.SLUG, 'title': M.TITLE, 'subtitle': M.SUB_FULL, 'authors': M.AUTHORS, 'advisor': '',
 'isbn': M.ISBN, 'price': M.PRICE, 'partWord': '编', 'sourceEdition': '统稿合成稿（%s）' % M.DATE,
 'unitRev': M.UNIT_REV, 'assetVersion': M.V, 'manuscript': 'tools/book-m603/src/manuscript.md', 'authorship': M.AUTHORSHIP,
 'agentName': C['agent']['name'], 'agentEpithet': C['agentEpithet'], 'bookMeta': C['bookMeta'], 'heroTagline': C['heroTagline'],
 'practiceWord': C['practiceWord'], 'pdfBg': '#1a1d2e',
 'learningPdfUrl': U + 'learning-pack.pdf?v=' + M.V, 'learningDocxUrl': U + 'learning-pack.docx?v=' + M.V,
 'readerPdfUrl': U + '%s-reader.pdf?v=%s' % (M.SLUG, M.V), 'printPdfUrl': U + '%s-print.pdf?v=%s' % (M.SLUG, M.V),
 'docxUrl': U + '%s.docx?v=%s' % (M.SLUG, M.V), 'tier': M.TIER,
 'bookPoints': C['bookPoints'], 'skillTheory': C['skillTheory'], 'tasks': C['tasks']}
Path('tools/book_unit/m%d.json' % M.NO).write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', len(cfg['tasks']))
