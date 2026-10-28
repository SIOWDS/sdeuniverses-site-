#!/usr/bin/env python3
"""read.html, index.html, rag.json, learning PDF for m/509."""
import json, re, html, os, math, collections, hashlib
import pypdfium2 as pdfium
ROOT = '/home/claude/rujia'; B = ROOT + '/build'
SITE = '/home/claude/sdeuniverses-site-/public'; REF = SITE + '/books/m/502'
NO = 509; SLUG = 'rujia-liulujing'; V = '20261028a'; AGENT = '问路'
OUT = f'{SITE}/books/m/{NO}'; BASE = f'https://sdeuniverses.com/books/m/{NO}'
META = json.load(open(B + '/meta.json')); S = json.load(open(ROOT + '/structure_v03.json'))
TITLE = META['title']; SUB = META['subtitle']; AUTHOR = META['author']
EPI = '先问你守着哪一个一，再看你惯走哪条路、末格落在哪里，最后问它还在回答问题吗'

# ---------- read.html ----------
pdf = pdfium.PdfDocument(f'{OUT}/{SLUG}-reader.pdf')
NPAGES = len(pdf)
toc = [{'t': '出版信息', 'p': '', 'g': 4, 'l': 1}]
for b in pdf.get_toc():
    g = b.get_dest().get_index() + 1
    t = b.get_title()
    lvl = 1 if b.level <= 1 else 2
    if b.level == 0 and not t.startswith(('出版说明', '目', '导言', '本书的口径', '待核')):
        t = {'立经：孔子的发展之道': '上部　立经：孔子的发展之道', '分途与对话：六条路径与两千五百年儒学': '中部　分途与对话',
             '发生与应用：从1到N走向0到1': '下部　发生与应用'}.get(t, t)
    if t.startswith('本书的口径'): t = '附录一　' + t
    if t.startswith('待核引文'): t = '附录二　' + t
    p = str(g) if g > 9 else ''
    if b.level == 1:
        continue  # 编 omitted to keep the drawer readable; parts and chapters remain
    toc.append({'t': t.replace('　', ' '), 'p': p, 'g': g, 'l': lvl})
r = open(REF + '/read.html').read()
cfg_old = re.search(r'<script type="application/json" id="cfg">.*?</script>', r, re.S).group(0)
r = r.replace(cfg_old, f'<script type="application/json" id="cfg">{json.dumps({"pdf": f"/books/m/{NO}/{SLUG}-reader.pdf?v={V}", "key": f"books-m-{NO}-v1", "offset": 0}, ensure_ascii=False)}</script>')
toc_old = re.search(r'<script type="application/json" id="toc">.*?</script>', r, re.S).group(0)
r = r.replace(toc_old, f'<script type="application/json" id="toc">{json.dumps(toc, ensure_ascii=False)}</script>')
for a, b in [('个人知识发生平台的数据基因', TITLE), ('子本是用来发生的', '知所先后，则近道矣'), ('/books/m/502/', f'/books/m/{NO}/'),
             ('三十二章实践', '六十六章实践'), ('三十二章', '六十六章'), ('快门', AGENT), ('shuju-jiyin', SLUG), ('20261028a', V)]:
    r = r.replace(a, b)
left = re.findall(r'.{30}(?:502|数据基因|快门|三十二).{30}', r)
assert not left, left[:4]
open(OUT + '/read.html', 'w').write(r)

# ---------- rag.json ----------
def bigrams(t):
    t = re.sub(r'[^一-鿿]', '', t)
    return [t[i:i + 2] for i in range(len(t) - 1)]
others = {}
for f in sorted(os.listdir('/home/claude/corpus/site')):
    no = int(f.split('.')[0]); txt = open('/home/claude/corpus/site/' + f).read()
    title = re.search(r'· (.*?) · 德麦国际专著第', txt[:400]).group(1)
    lines = txt.split('\n'); segs = []; head = ''; buf = ''
    for ln in lines:
        s = ln.strip()
        if re.match(r'^(第\s*\d+\s*章|第[一二三四五六七八九十]+[章编]|附录|导[论言读]|前言|结语)', s) and len(s) < 60:
            head = s
        if len(s) < 40: continue
        buf += s
        if len(buf) > 260:
            segs.append((head, buf[:400])); buf = ''
    others[no] = (title, segs)
chs = []
for pi, p in enumerate(S['parts']):
    for b in p['bians']:
        for c in b['chs']:
            n = int(re.match(r'第(\d+)章', c[0]).group(1))
            t = open(f'{ROOT}/chapters/ch{n:02d}.md').read()
            chs.append((n, t.split('\n', 1)[0].lstrip('#').strip().split('　', 1)[1], t))
docs = [bigrams(x[2]) for x in chs] + [bigrams(s[1]) for no in others for s in others[no][1]]
df = collections.Counter()
for d in docs: df.update(set(d))
N = len(docs)
def vec(bg):
    c = collections.Counter(bg); v = {k: (1 + math.log(x)) * math.log(N / df[k]) for k, x in c.items() if df[k] > 1}
    nrm = math.sqrt(sum(x * x for x in v.values())) or 1
    return {k: x / nrm for k, x in v.items()}
segv = [(no, h, s, vec(bigrams(s))) for no in others for (h, s) in others[no][1]]
cands = []
for n, name, t in chs:
    cv = vec(bigrams(t))
    best = []
    for no, h, s, v in segv:
        sc = sum(w * v.get(k, 0) for k, w in cv.items())
        best.append((sc, no, h, s, v))
    best.sort(key=lambda x: -x[0])
    seen = set()
    for sc, no, h, s, v in best[:6]:
        if no in seen: continue
        seen.add(no)
        kw = sorted(((cv[k] * v[k], k) for k in v if k in cv), reverse=True)[:5]
        cands.append({'kind': 'book', 'no': no, 't': others[no][0], 'u': f'/books/m/{no}/text/', 'sch': name.split('——')[0],
                      'ch': h or others[no][0], 'rel': '同向' if no in (312, 313, 314, 331, 340, 484, 490, 493) else '跨界',
                      's': round(sc, 3), 'kw': [k for _, k in kw], 'x': s[:300]})
        if len(seen) >= 2: break
cands.sort(key=lambda x: -x['s'])
items = []; perbook = collections.Counter(); perch = collections.Counter()
for c in cands:
    if perbook[c['no']] >= 5 or perch[c['sch']] >= 1: continue
    items.append(c); perbook[c['no']] += 1; perch[c['sch']] += 1
    if len(items) >= 28: break
chapters_list = []
for p in S['parts']:
    for b in p['bians']:
        chapters_list.append(b['t'].split('　', 1)[1])
        for c in b['chs']:
            chapters_list.append(c[0].split('　', 1)[1].split('——')[0])
json.dump({'no': NO, 'title': TITLE, 'built': '2026-10-28', 'method': 'char 2gram TF-IDF · 按章检索 · 站上儒学诸卷与跨界卷分配额',
           'chapters': chapters_list, 'items': items}, open(OUT + '/rag.json', 'w'), ensure_ascii=False, indent=1)
print('rag items', len(items), collections.Counter(i['no'] for i in items))
json.dump({'pages': NPAGES}, open(B + '/reader_pages.json', 'w'))
print('read.html toc', len(toc), 'pages', NPAGES)
