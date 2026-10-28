#!/usr/bin/env python3
"""第 504 号《被清零的不是博士》的碰撞库 public/books/m/504/rag.json。

做法同 tools/build_book_rag.py 的思路（字符 2 元 TF-IDF、按章求章向量、按来源去重、限每章入选数），
只是语料换成全站其他专著已上站的 keypoints.json（每本书的核心要点，约四百本），
因为本次构建环境没有全站正文的工作副本。产物只是检索出来的候选碰撞点，不是结论。
用法（仓库根目录）：python3 tools/book-m504-qingling/build_rag_504.py --kp <keypoints 目录> --ms tools/book-m504-qingling/book.md
"""
import argparse, datetime, json, re
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

NO, QUOTA, PER_CH, MIN_SIM, SAME_SRC, CROSS_MIN = 504, 24, 3, 0.08, 0.62, 5
CJK = re.compile(r'[一-鿿]')

ap = argparse.ArgumentParser(); ap.add_argument('--kp', required=True); ap.add_argument('--ms', required=True)
A = ap.parse_args()
cat = json.loads(Path('public/books/catalog.json').read_text())
info = {b['number']: b for b in cat['books'] if isinstance(b.get('number'), int)}
CATS = cat['categories']

# 本书各章
ms = Path(A.ms).read_text()
chs = []
for m in re.finditer(r'^## 第 (\d+) 章　(.+)$', ms, re.M):
    s = m.end(); e = ms.find('\n## 第 ', s); e2 = ms.find('\n# ', s)
    e = min(x for x in (e, e2, len(ms)) if x != -1)
    chs.append((int(m[1]), m[2], ms[s:e]))
for title, pat in (('导论　一条短视频引出的问题', r'^# 导论.*$'), ('结语　被清零的是哪条路，长出来的是谁', r'^# 结语.*$')):
    m = re.search(pat, ms, re.M); s = m.end(); e = ms.find('\n# ', s)
    chs.append((0, title, ms[s:e if e != -1 else len(ms)]))

# 语料：其他书的要点
docs = []
for f in sorted(Path(A.kp).glob('*.json')):
    n = int(f.stem)
    if n == NO or n not in info:
        continue
    d = json.loads(f.read_text())
    for it in d.get('items', []):
        x = (it.get('t', '') + '。' + it.get('x', '')).strip()
        if len(CJK.findall(x)) >= 30:
            docs.append({'no': n, 't': info[n]['title'], 'sch': it.get('t', ''), 'x': it.get('x', ''), 'src': x,
                         'cat': info[n].get('category', '')})
texts = [''.join(CJK.findall(t)) for _, _, t in chs] + [''.join(CJK.findall(d['src'])) for d in docs]
vec = TfidfVectorizer(analyzer='char', ngram_range=(2, 2), sublinear_tf=True, min_df=2, max_df=0.5)
X = vec.fit_transform(texts)
C, D = X[:len(chs)], X[len(chs):]
S = (C @ D.T).toarray()
terms = np.array(vec.get_feature_names_out())

order = []
for ci in range(len(chs)):
    for di in np.argsort(-S[ci])[:40]:
        order.append((S[ci, di], ci, di))
order.sort(reverse=True)
picked, used_books, per_ch = [], set(), {}
mycat = 'edu'
def take(cond):
    for s, ci, di in order:
        if len(picked) >= QUOTA: return
        d = docs[di]
        if s < MIN_SIM or d['no'] in used_books or per_ch.get(ci, 0) >= PER_CH or not cond(d):
            continue
        picked.append((s, ci, di)); used_books.add(d['no']); per_ch[ci] = per_ch.get(ci, 0) + 1
# 先保证跨书类的至少 CROSS_MIN 条，再按相似度补满
take(lambda d: d['cat'] != mycat and len([1 for _, _, k in picked if docs[k]['cat'] != mycat]) < CROSS_MIN)
take(lambda d: True)
items = []
for s, ci, di in sorted(picked, key=lambda q: (chs[q[1]][0] or 99, -q[0])):
    d = docs[di]
    a, b = C[ci].toarray()[0], D[di].toarray()[0]
    kw = [t for t in terms[np.argsort(-(a * b))[:6]] if (a * b)[list(terms).index(t)] > 0] if False else \
         [terms[j] for j in np.argsort(-(a * b))[:6] if a[j] * b[j] > 0]
    ch = chs[ci]
    items.append({'kind': 'book', 'no': d['no'], 't': d['t'], 'u': '/books/m/%d/' % d['no'], 'sch': d['sch'],
                  'ch': ('第 %d 章　%s' % (ch[0], ch[1])) if ch[0] else ch[1],
                  'rel': '同源' if s >= SAME_SRC else '近邻', 's': round(float(s), 3), 'kw': kw, 'x': d['x'][:300]})
out = {'no': NO, 'title': '被清零的不是博士', 'built': datetime.date.today().isoformat(),
       'method': 'char 2gram TF-IDF · 按章检索 · 全站专著要点库（keypoints）',
       'chapters': [('第 %d 章　%s' % (n, t)) if n else t for n, t, _ in chs], 'items': items}
p = Path('public/books/m/%d/rag.json' % NO); p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(out, ensure_ascii=False) + '\n')
print('rag items', len(items), 'from', len(set(i['no'] for i in items)), 'books; corpus', len(docs), 'keypoints')
