#!/usr/bin/env python3
"""第 437 号：为智能体「约分」预建碰撞库 public/books/m/437/rag.json（格式照第 527 号）。
做法：本书 37 章与站内被吸收专著的各章做字二元组 TF-IDF 余弦相似；每章取最相近的一段（同一本书最多两次），
专著与本书同属"工具 / AI / 复合体"一线的记"同向"，其余记"跨界"。不调用模型。
用法（仓库根目录）：python3 tools/book-m437/build_rag.py --src /home/claude/book
"""
import argparse, collections, datetime, json, math, re, subprocess
from pathlib import Path

ap = argparse.ArgumentParser(); ap.add_argument('--src', type=Path, required=True); a = ap.parse_args()
CAT = json.loads(Path('public/books/catalog.json').read_text())
HASTEXT = {int(x.split('/')[3]) for x in subprocess.run(['git', 'ls-tree', '-r', '--name-only', 'HEAD', 'public/books/m/'], capture_output=True, text=True).stdout.split() if re.match(r'public/books/m/\d+/text/index\.html$', x)}
T = {b['number']: b for b in CAT['books'] if b.get('number')}
han = re.compile(r'[一-鿿]')


def grams(s):
    s = ''.join(han.findall(s))
    return collections.Counter(s[i:i + 2] for i in range(len(s) - 1))


# 本书各章
mine = []
for i in range(1, 38):
    t = (a.src / 'chapters' / ('ch%02d.md' % i)).read_text().split('## 本章接引')[0]
    title = t.split('\n', 1)[0].lstrip('# ').split('　', 1)[1].strip()
    mine.append((title, t))

# 站内专著各章
docs = []
HEAD = re.compile(r'^(第[一二三四五六七八九十百零\d]+章)[　\s]+([^，。：；！？、,.:;]{2,30})$', re.M)
for f in sorted((a.src / 'sources').glob('m*.txt')):
    n = int(f.stem[1:])
    if n not in T or n == 437:
        continue
    s = f.read_text(errors='ignore')
    hs = list(HEAD.finditer(s))
    for k, h in enumerate(hs):
        body = s[h.end(): hs[k + 1].start() if k + 1 < len(hs) else len(s)]
        if len(han.findall(body)) < 800:
            continue
        docs.append((n, h.group(1) + '　' + h.group(2).strip(), body))

df = collections.Counter()
G = []
for _, _, body in docs:
    g = grams(body); G.append(g); df.update(g.keys())
N = len(docs)
idf = {k: math.log((N + 1) / (v + 1)) + 1 for k, v in df.items()}


def vec(g):
    v = {k: c * idf.get(k, 1.0) for k, c in g.items() if k in idf}
    nrm = math.sqrt(sum(x * x for x in v.values())) or 1
    return {k: x / nrm for k, x in v.items()}


DV = [vec(g) for g in G]
SAME = {110, 111, 112, 114, 115, 122, 278, 281, 329, 355, 357, 364, 366, 367, 401, 460, 224, 347, 330, 263, 268, 36, 398, 416}
used = collections.Counter(); items = []
for title, t in mine:
    mv = vec(grams(t))
    best = sorted(((sum(w * DV[j].get(k, 0) for k, w in mv.items()), j) for j in range(N)), reverse=True)
    for s, j in best:
        n, sch, body = docs[j]
        if used[n] >= 2:
            continue
        used[n] += 1
        common = sorted(((mv[k] * DV[j][k], k) for k in mv if k in DV[j]), reverse=True)[:5]
        paras = [p.strip() for p in body.split('\n') if len(han.findall(p)) > 60]
        pg = grams(t)
        para = max(paras, key=lambda p: sum(min(c, pg.get(k, 0)) for k, c in grams(p).items())) if paras else body.strip()
        b = T[n]
        u = '/books/m/%d/text/' % n if n in HASTEXT else b['detailUrl'].replace('https://sdeuniverses.com', '')
        items.append({'kind': 'book', 'no': n, 't': b['title'], 'u': u, 'sch': sch, 'ch': title,
                      'rel': '同向' if n in SAME else '跨界', 's': round(s, 3), 'kw': [k for _, k in common],
                      'x': re.sub(r'\s+', ' ', para)[:200]})
        break
out = {'no': 437, 'title': '被替代的从来不是人', 'built': datetime.date.today().isoformat(),
       'method': 'char 2gram TF-IDF · 按章检索 · 每本专著至多两段', 'chapters': [t for t, _ in mine], 'items': items}
p = Path('public/books/m/437/rag.json'); p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')) + '\n')
print('rag items', len(items), 'docs', N, 'books', len({i['no'] for i in items}))
