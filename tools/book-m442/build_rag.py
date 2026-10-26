#!/usr/bin/env python3
"""第 442 号专属碰撞库 rag.json：按章检索全站其他专著全文与专栏文章，字二元 TF-IDF，专著与文章分配额（12+6）；每章至多两条，关键词重合两个以上视为同一典故只留一条。
格式与第 443、520 号 rag.json 相同：{no,title,built,method,chapters,items:[{kind,no,t,u,sch,ch,rel,s,kw,x}]}
用法（仓库根目录）：python3 tools/book-m442/build_rag.py
"""
import datetime, html, json, re
from pathlib import Path
from collections import Counter, defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

NO, TITLE = 442, '懂的发生学'
PUB = Path('public')
cat = json.loads((PUB / 'books/catalog.json').read_text(encoding='utf-8'))
meta = {b['number']: b for b in cat['books'] if isinstance(b.get('number'), int)}
MYCAT = meta[NO].get('category', 'core')

def strip(h):
    h = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', h, flags=re.S)
    h = re.sub(r'<[^>]+>', ' ', h)
    return re.sub(r'\s+', ' ', html.unescape(h)).strip()

def han(s):
    return re.sub(r'[^一-鿿]', '', s)

def chunks(text, size=260):
    out, cur = [], ''
    for p in re.split(r'(?<=[。！？」])', text):
        cur += p
        if len(cur) >= size:
            out.append(cur.strip()); cur = ''
    if len(han(cur)) > 80:
        out.append(cur.strip())
    return out

# ---- this book: chapters (parts + chapters, in order)
mine = (PUB / ('books/m/%d/text/index.html' % NO)).read_text(encoding='utf-8')
qtitles, qtexts = [], []
for m in re.finditer(r'<section class="(part|chapter)" id="s\d+">(.*?)</section>', mine, re.S):
    body = m.group(2)
    t = re.search(r'<h2 class="(?:part|chap)-title">(.*?)</h2>', body)
    qtitles.append(html.unescape(t.group(1)))
    qtexts.append(strip(body))

# ---- corpus: other books' chapter chunks + column article chunks
docs = []
for p in sorted(PUB.glob('books/m/*/text/index.html')):
    n = int(p.parts[-3])
    if n == NO or n not in meta:
        continue
    h = p.read_text(encoding='utf-8', errors='ignore')
    for m in re.finditer(r'<section class="chapter"[^>]*>(.*?)</section>', h, re.S):
        body = m.group(1)
        t = re.search(r'<h2[^>]*>(.*?)</h2>', body)
        sch = strip(t.group(1)) if t else ''
        txt = strip(body)
        for c in chunks(txt[len(sch):] if txt.startswith(sch) else txt):
            docs.append({'kind': 'book', 'no': n, 't': meta[n]['title'], 'u': '/books/m/%d/text/' % n, 'sch': sch, 'x': c})
for p in sorted(PUB.glob('column/*/index.html')):
    h = p.read_text(encoding='utf-8', errors='ignore')
    tt = re.search(r'<title>(.*?)</title>', h, re.S)
    t = strip(tt.group(1)) if tt else p.parent.name
    body = re.search(r'<(article|main)[^>]*>(.*?)</\1>', h, re.S)
    txt = strip(body.group(2) if body else h)
    for c in chunks(txt):
        docs.append({'kind': 'article', 'no': None, 't': t, 'u': '/column/%s/' % p.parent.name, 'sch': '', 'x': c})
docs = [d for d in docs if len(han(d['x'])) >= 90]
print('corpus chunks', len(docs), 'queries', len(qtitles))

vec = TfidfVectorizer(analyzer='char', ngram_range=(2, 2), preprocessor=han, sublinear_tf=True, min_df=2, max_df=0.2)
X = vec.fit_transform([d['x'] for d in docs])
Q = vec.transform(qtexts)
S = (Q @ X.T).toarray()          # rows: chapters, cols: chunks
vocab = np.array(vec.get_feature_names_out())

# ---- allocation: 12 book items (distinct books), 6 articles (distinct urls), ≤3 per chapter
cand = []
for qi in range(S.shape[0]):
    for di in np.argsort(-S[qi])[:60]:
        cand.append((S[qi, di], qi, di))
cand.sort(reverse=True)
quota = {'book': 12, 'article': 6}
used_src, per_ch, picked = set(), Counter(), []
for s, qi, di in cand:
    d = docs[di]
    key = d['no'] if d['kind'] == 'book' else d['u']
    if quota[d['kind']] <= 0 or key in used_src or per_ch[qi] >= 2:
        continue
    q, x = Q[qi].toarray()[0], X[di].toarray()[0]
    shared = np.argsort(-(q * x))[:5]
    kw = [vocab[i] for i in shared if q[i] * x[i] > 0]
    if any(len(set(kw) & set(p['kw'])) >= 2 for p in picked):
        continue  # 同一典故只留最相撞的一条
    quota[d['kind']] -= 1; used_src.add(key); per_ch[qi] += 1
    rel = '同向' if d['kind'] == 'book' and meta[d['no']].get('category') == MYCAT else '跨界'
    picked.append(dict(kind=d['kind'], no=d['no'], t=d['t'], u=d['u'], sch=d['sch'], ch=qtitles[qi], rel=rel,
                       s=round(float(s), 3), kw=kw, x=d['x'][:300]))
    if not quota['book'] and not quota['article']:
        break
picked.sort(key=lambda i: -i['s'])
out = {'no': NO, 'title': TITLE, 'built': datetime.date.today().isoformat(),
       'method': 'char 2gram TF-IDF · 按章检索 · 专著与文章分配额', 'chapters': qtitles, 'items': picked}
(PUB / ('books/m/%d/rag.json' % NO)).write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
print(Counter(i['kind'] for i in picked), Counter(i['rel'] for i in picked))
for i in picked:
    print(i['s'], i['kind'], i['no'], i['t'][:24], '|', i['ch'][:18], '|', i['kw'])
