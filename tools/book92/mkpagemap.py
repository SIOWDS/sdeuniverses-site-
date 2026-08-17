# -*- coding: utf-8 -*-
import re, json
raw = open('out.txt', encoding='utf-8').read()
pages = raw.split('\f')
titles = []
for l in open('manuscript.md', encoding='utf-8'):
    if l.startswith('## '):
        titles.append(l[3:].strip())
    elif l.startswith('# ') and l[2:3] == '第':
        titles.append(l[2:].strip())
titles = [t for t in titles if t != '封　底']
def norm(s):
    return re.sub(r'\s|　', '', s)
pm = {}
cur = 0
for t in titles:
    nt = norm(t)
    for pi in range(cur, len(pages)):
        body = pages[pi]
        head = norm(body)[:80]           # 必须在页首（跳过页眉书名）
        head = head.replace('谁来陪伴我？', '', 1)
        ok = head.startswith(nt[:12]) or nt[:12] in head[:40]
        if not ok and len(nt) > 6:
            ok = head.startswith(nt[:3]) and nt[3:11] in head[:70]
        if ok:
            pm[t] = pi + 1
            cur = pi + 1
            break
json.dump(pm, open('pagemap.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('命中', len(pm), '/', len(titles))
for t in titles:
    if t not in pm:
        print('  MISS', t)
