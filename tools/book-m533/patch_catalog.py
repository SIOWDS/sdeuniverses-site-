#!/usr/bin/env python3
"""第 533 号：给 public/books/catalog.json 里 533 条目补出学习包与智能体字段（照第 545、546 号条目的字段与次序）。幂等。
用法（仓库根目录）：python3 tools/book-m533/patch_catalog.py
"""
import json, sys
from pathlib import Path
sys.path.insert(0, 'tools/book-m533')
import meta as M  # noqa: E402
C = json.loads(Path('tools/book-m533/content.json').read_text(encoding='utf-8'))
p = Path('public/books/catalog.json')
cat = json.loads(p.read_text(encoding='utf-8'))
U = 'https://sdeuniverses.com/books/m/%d/' % M.NO
name = C['agent']['name']
new = {
 'agentUrl': U + 'agent/dialogue.html', 'agentName': name, 'agentLabel': '智能问对 · ' + name,
 'learnUrl': U + 'agent/learning.html', 'learningUrl': U + 'agent/learning.html', 'learnLabel': '学习包 · %d个学习单元' % len(C['tasks']),
 'learningPackUrl': U + 'learning-pack.pdf?v=' + M.V, 'learningPackDocxUrl': U + 'learning-pack.docx?v=' + M.V,
}
for i, b in enumerate(cat['books']):
    if b.get('number') == M.NO:
        assert b['isbn'] == '9798906905475' and b['isbnDisplay'] == M.ISBN, 'ISBN 不得改动'
        out = {}
        for k, v in b.items():
            if k in ('tier', 'citeOk', 'publicationUnit') or k in new:
                continue
            out[k] = v
        out.update(new)
        out['tier'] = b.get('tier', 'L0'); out['citeOk'] = b.get('citeOk', True)
        out['publicationUnit'] = {'id': 'm-%d' % M.NO, 'type': 'reading-learning-dialogue', 'revision': M.UNIT_REV}
        cat['books'][i] = out
        break
else:
    raise SystemExit('catalog 里没有 533')
p.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('catalog patched', M.NO)
