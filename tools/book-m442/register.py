#!/usr/bin/env python3
"""第 442 号《懂的发生学》（由第 443 号 register.py 扩来）：
写 keypoints.json；在 public/books/agents.json 登记本书智能体「下半句」；
照 tools/build_book_agents.py 的同一模板只生成本书的 agent/index.html（不重跑全站）；
在 /books/agent/ 名录里补本书卡片与总数；给 catalog.json 本书条目补三位一体字段。
在仓库根目录运行：python3 tools/book-m442/register.py
"""
import datetime, html, json, re, sys
from pathlib import Path

sys.path.insert(0, 'tools/book-m442')
import meta as M  # noqa: E402

NO = M.NO
C = json.loads(Path('tools/book-m442/content.json').read_text(encoding='utf-8'))
today = datetime.date.today().isoformat()
now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
esc = lambda s: html.escape(str(s or ''), quote=True)
name = C['agent']['name']

# ---- keypoints
kp = {'no': NO, 'title': M.TITLE, 'built': today, 'items': [{'t': x['t'], 'x': x['x'], 'ch': x['ch']} for x in C['keypoints']]}
Path('public/books/m/%d/keypoints.json' % NO).write_text(json.dumps(kp, ensure_ascii=False) + '\n', encoding='utf-8')

# ---- agents.json
ap = Path('public/books/agents.json')
reg = json.loads(ap.read_text(encoding='utf-8'))
clash = [k for k, v in reg['agents'].items() if v.get('name') == name and k != str(NO)]
assert not clash, '智能体重名：%s' % clash
reg['agents'][str(NO)] = {'name': name, 'epithet': C['agentEpithet'], 'intro': C['agentIntro'], 'starts': C['agentStarts']}
for k in ('updatedAt', 'updated'):
    if k in reg:
        reg[k] = now if k == 'updatedAt' else today
ap.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')

# ---- catalog entry
cp = Path('public/books/catalog.json')
cat = json.loads(cp.read_text(encoding='utf-8'))
b = next(x for x in cat['books'] if x.get('number') == NO)
url = 'https://sdeuniverses.com/books/m/%d/' % NO
b.update(chapterUrl=url + 'text/', titleEn=M.TITLE_EN,
         agentUrl=url + 'agent/dialogue.html', agentName=name, agentLabel='智能问对 · ' + name,
         learnUrl=url + 'agent/learning.html', learningUrl=url + 'agent/learning.html', learnLabel='学习包 · 54个学习单元',
         learningPackUrl=url + 'downloads/%s-learning-v1.0.pdf' % M.SLUG,
         publicationUnit={'id': 'm-%d' % NO, 'type': 'reading-learning-dialogue', 'revision': M.UNIT_REV})
cp.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

# ---- agent/index.html (same template as tools/build_book_agents.py)
BODY = Path('tools/book_agent_body.html').read_text(encoding='utf-8')
V = re.search(r'^V = "([^"]+)"', Path('tools/build_book_agents.py').read_text(encoding='utf-8'), re.M).group(1)
page = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>%(name)s · 《%(title)s》的智能体 | 德麦国际专著第 %(n)s 号</title>
<meta name="description" content="%(desc)s">
<meta name="sde-page-kind" content="tool">
<meta name="book-agent" content="%(name)s"><meta name="book_no" content="%(n)s">
<link rel="canonical" href="https://sdeuniverses.com/books/m/%(n)s/agent/">
<meta property="og:title" content="%(name)s · 《%(title)s》的智能体">
<meta property="og:description" content="%(desc)s">
%(og)s<link rel="stylesheet" href="/books/agent/app.css?v=%(v)s">
</head>
<body>
%(body)s<script>window.BOOK_AGENT={no:%(n)s};</script>
<script src="/books/agent/app.js?v=%(v)s" defer></script>
</body></html>
""" % {'name': esc(name), 'title': esc(b['title']), 'n': NO, 'desc': esc(C['agentIntro']), 'v': V, 'body': BODY,
       'og': '<meta property="og:image" content="%s">\n' % esc(b['coverUrl'])}
Path('public/books/m/%d/agent/index.html' % NO).write_text(page, encoding='utf-8')

# ---- /books/agent/ directory: insert card in its category, keep descending order, bump totals
dp = Path('public/books/agent/index.html')
d = dp.read_text(encoding='utf-8')
card = ('<a class="c" href="/books/m/%d/agent/"><b>%s</b><i>%s</i><span>《%s》 · 第 %d 号</span></a>'
        % (NO, esc(name), esc(C['agentEpithet']), esc(b['title']), NO))
if '/books/m/%d/agent/"' % NO not in d:
    label = cat['categories'][b.get('category', 'core')]
    m = re.search(r'<section><h2>%s<span>(\d+)</span></h2><div class="g">(.*?)</div></section>' % re.escape(esc(label)), d, re.S)
    assert m, label
    cards = re.findall(r'<a class="c" href="/books/m/(\d+)/agent/">.*?</a>', m.group(2), re.S)
    nums = [int(x) for x in cards]
    pos = next((i for i, x in enumerate(nums) if x < NO), len(nums))
    items = re.findall(r'<a class="c" href="/books/m/\d+/agent/">.*?</a>', m.group(2), re.S)
    items.insert(pos, card)
    sec = '<section><h2>%s<span>%d</span></h2><div class="g">%s</div></section>' % (esc(label), int(m.group(1)) + 1, ''.join(items))
    d = d[:m.start()] + sec + d[m.end():]
    d = re.sub(r'共 (\d+) 位', lambda x: '共 %d 位' % (int(x.group(1)) + 1), d, count=1)
    dp.write_text(d, encoding='utf-8')
print('keypoints', len(kp['items']), 'agent', name, 'agent page v', V)
