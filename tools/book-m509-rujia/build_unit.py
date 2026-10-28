#!/usr/bin/env python3
"""Build the 三位一体 publication unit for 德麦国际专著第509号 into the site repo,
templated on unit m/502 (same site generation)."""
import json, re, os, shutil, hashlib, html, subprocess, sys, math, collections
sys.path.insert(0, '/home/claude/rujia/build')
import importlib.util
spec = importlib.util.spec_from_file_location('mb', '/home/claude/rujia/build/make_book.py')
ROOT = '/home/claude/rujia'; B = ROOT + '/build'
SITE = '/home/claude/sdeuniverses-site-/public'
REF = SITE + '/books/m/502'
NO = 509; SLUG = 'rujia-liulujing'; V = '20261028a'
OUT = f'{SITE}/books/m/{NO}'
META = json.load(open(B + '/meta.json'))
S = json.load(open(ROOT + '/structure_v03.json'))
TITLE = META['title']; SUB = META['subtitle']; AUTHOR = META['author']
AGENT = '问路'
EPITHET = '先问你守着哪一个一，再看你惯走哪条路、末格落在哪里，最后问它还在回答问题吗'
VERSION = '初版（2026-10-28）'; TASKVER = '20261028-m509-unit-v1.0'
BASE = f'https://sdeuniverses.com/books/m/{NO}'
os.makedirs(OUT, exist_ok=True)
for d in ('text', 'agent', 'unit/sources', 'downloads'): os.makedirs(f'{OUT}/{d}', exist_ok=True)

def curly(t):
    out = []
    for line in t.split('\n'):
        if '"' in line:
            r = []; o = True
            for ch in line:
                if ch == '"': r.append('“' if o else '”'); o = not o
                else: r.append(ch)
            line = ''.join(r)
        out.append(line)
    return '\n'.join(out)

def md2html(md):
    p = subprocess.run(['pandoc', '-f', 'markdown-smart-auto_identifiers+east_asian_line_breaks', '-t', 'html', '--wrap=none'],
                       input=md, capture_output=True, text=True)
    return p.stdout

def chap_md(n):
    return curly(open(f'{ROOT}/chapters/ch{n:02d}.md').read().strip())

def lesson(n):
    return json.load(open(f'{ROOT}/learn/lesson_{n:02d}.json'))

# ---------- chapter registry ----------
chapters = []   # dicts n,title(full),name,label,part_i,bian_i,bian_name
for pi, p in enumerate(S['parts']):
    for bi, b in enumerate(p['bians']):
        for c in b['chs']:
            n = int(re.match(r'第(\d+)章', c[0]).group(1))
            first = chap_md(n).split('\n', 1)[0].lstrip('#').strip()
            name = first.split('　', 1)[1]
            chapters.append(dict(n=n, full=first, name=name, pi=pi, bi=bi, bian=b['t'].split('　', 1)[1], bianlab=b['t'].split('　', 1)[0]))
BIANS = []
for p in S['parts']:
    for b in p['bians']: BIANS.append(b['t'].split('　', 1)[1])
bian_index = {}
k = 0
for pi, p in enumerate(S['parts']):
    for bi, b in enumerate(p['bians']):
        k += 1; bian_index[(pi, bi)] = k

# ---------- copy binaries ----------
shutil.copy(B + '/cover.jpg', OUT + '/cover.jpg')
shutil.copy(B + '/backcover.jpg', OUT + '/backcover.jpg')
shutil.copy(f'{B}/{SLUG}-reader.pdf', f'{OUT}/{SLUG}-reader.pdf')
shutil.copy(f'{B}/{SLUG}-print.pdf', f'{OUT}/{SLUG}-print.pdf')

# ---------- text/index.html ----------
ref_text = open(REF + '/text/index.html').read()
head_css = re.search(r'<style>(.*?)</style>', ref_text, re.S).group(1)
head_css += '\nh4.sub{color:var(--navy);font-size:1.02rem;margin:1.6rem 0 .6rem}\n.mk{color:var(--gold);font-size:.86em}\n'
sid = [0]; anchors = {}
def nid():
    sid[0] += 1; return f's{sid[0]}'
def body_html(md):
    h = md2html(md)
    h = re.sub(r'<h3>(.*?)</h3>', r'<h4 class="sub">\1</h4>', h)
    h = re.sub(r'<h2>(.*?)</h2>', r'<h3 class="sec"><span class="dia">◆</span>\1</h3>', h)
    h = re.sub(r'<table>', '<div class="tw"><table class="tb">', h); h = h.replace('</table>', '</table></div>')
    h = re.sub(r'〔([^〕]{1,30})〕', r'<span class="mk">〔\1〕</span>', h)
    return h
secs = []; toc = []
i = nid(); toc.append(('f', i, '出版说明'))
secs.append(f'<section class="front-sec" id="{i}"><div class="fs-title">出版说明</div><div class="rule"></div>{body_html(curly(open(B+"/preface.md").read()))}</section>')
i = nid(); anchors[0] = i
t0 = chap_md(0); nm0 = t0.split('\n', 1)[0].lstrip('#').strip().split('　', 1)[1]
toc.append(('f', i, '导言　' + nm0.split('——')[0]))
secs.append(f'<section class="chapter" id="{i}"><div class="chap-label">导言</div><h2 class="chap-title">{html.escape(nm0)}</h2><div class="rule"></div>'
            f'<div class="takeaway"><span class="lab">导言要点</span><p>{html.escape(lesson(0)["keyline"])}</p></div>{body_html(t0.split(chr(10),1)[1])}</section>')
for pi, p in enumerate(S['parts']):
    m = re.match(r'(.)部　(.*?)（约', p['t'])
    i = nid(); toc.append(('p', i, f'{m.group(1)}部　{m.group(2)}'))
    secs.append(f'<section class="part" id="{i}"><div class="part-label">{m.group(1)}　部</div><div class="part-title">{html.escape(m.group(2))}</div><div class="rule"></div><div class="part-intro"><p class="bianxu">{html.escape(p["lead"])}</p></div></section>')
    for bi, b in enumerate(p['bians']):
        lab, nm = b['t'].split('　', 1)
        i = nid(); toc.append(('p', i, f'{lab}　{nm}'))
        secs.append(f'<section class="part" id="{i}"><div class="part-label">{lab}</div><div class="part-title">{html.escape(nm)}</div><div class="rule"></div></section>')
        for c in b['chs']:
            n = int(re.match(r'第(\d+)章', c[0]).group(1))
            ch = next(x for x in chapters if x['n'] == n)
            i = nid(); anchors[n] = i
            toc.append(('c', i, f'第 {n} 章　{ch["name"].split("——")[0]}'))
            body = chap_md(n).split('\n', 1)[1]
            secs.append(f'<section class="chapter" id="{i}"><div class="chapnum">{n:02d}</div><div class="chap-label">第 {n} 章</div><h2 class="chap-title">{html.escape(ch["name"])}</h2><div class="rule"></div>'
                        f'<div class="takeaway"><span class="lab">本章要点</span><p>{html.escape(lesson(n)["keyline"])}</p></div>{body_html(body)}</section>')
i = nid(); toc.append(('f', i, '附录一　本书的口径、读法与核查记录'))
a1 = curly(open(B + '/appendix1.md').read()).split('\n', 1)[1]
secs.append(f'<section class="back-sec" id="{i}"><div class="fs-title appx">附录一　本书的口径、读法与核查记录</div><div class="rule"></div>{body_html(a1)}</section>')
# appendix 2 from the PDF builder logic
i = nid(); toc.append(('f', i, '附录二　待核引文与判断清单'))
dh = []
for n in range(67):
    t = chap_md(n); hits = []
    for para in t.split('\n'):
        for mm in re.finditer(r'[^。！？\n]*〔[^〕]*待核[^〕]*〕', para):
            x = mm.group(0).strip().lstrip('#').strip().replace('**', '')
            x = x.strip('|').replace(' | ', '；').replace('|', '；').strip().lstrip('-').strip().lstrip('”’，、：；）)').strip()
            if x and x[-120:] not in hits: hits.append(x[-120:])
    if hits:
        tl = t.split('\n', 1)[0].lstrip('#').strip().split('——')[0]
        dh.append(f'<h3 class="sec">{html.escape(tl)}（{len(hits)}条）</h3><ol>' + ''.join(f'<li>{html.escape(h)}</li>' for h in hits) + '</ol>')
secs.append(f'<section class="back-sec" id="{i}"><div class="fs-title appx">附录二　待核引文与判断清单</div><div class="rule"></div><p>引文与事实核查之后仍未能对照原书核实的句子，按章列出。正文中这些地方都标有〔待核〕或其变体。</p>{"".join(dh)}</section>')

def tocli(kind, i, t):
    cls = {'f': 'f', 'p': 'p', 'c': 'c'}[kind]
    return f'<li class="{cls}"><a href="#{i}">{html.escape(t)}</a></li>'
nav = (f'<nav data-unit="v1" aria-label="阅读学习智能问对" style="display:flex;gap:1rem;flex-wrap:wrap;padding:.7rem 1rem;border:1px solid #a88b43;background:#141611;color:#e7ce91;border-radius:8px;margin:1rem auto;max-width:980px;font:14px/1.8 sans-serif">'
       f'<a style="color:inherit" href="/books/m/{NO}/read.html">阅读 · 在线翻页</a><a style="color:inherit" href="/books/m/{NO}/agent/learning.html">学习包 · 六十六章实践</a><a style="color:inherit" href="/books/m/{NO}/agent/dialogue.html">智能问对 · {AGENT}</a></nav>')
text_html = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>全文网页阅读 · {TITLE} · 德麦国际专著第 {NO} 号</title>
<meta name="description" content="《{TITLE}：{SUB}》全文网页版。{AUTHOR} 著，德麦国际专著第 {NO} 号，约 94 万汉字。">
<meta name="tier" content="L0"><link rel="canonical" href="{BASE}/text/">
<style>{head_css}</style></head>
<body><div id="prog"></div> <div class="bar"><a href="/books/m/{NO}/">← 书籍详情</a><a href="/books/m/{NO}/read.html">在线翻页</a><a href="/books/m/{NO}/{SLUG}-print.pdf?v={V}" target="_blank" rel="noopener">PDF</a><span class="sp"></span><button id="fs">字号</button><button id="th">夜间</button></div> <div class="wrap">{nav} <div class="hero"><img src="/books/m/{NO}/cover.jpg?v={V}" alt="封面"><h1>{TITLE}</h1><p>{SUB}</p> <p style="color:var(--dim);margin-top:.5rem">{AUTHOR} 著 · 德麦国际专著第 {NO} 号 · ISBN {META["isbn"]} · 约 94 万汉字</p></div> <details class="toc"><summary>目录（出版说明 · 导言 · 三部十三编六十六章 · 附录一、二）</summary><ul>{"".join(tocli(*x) for x in toc)}</ul></details>
{chr(10).join(secs)}
<div class="foot">德麦国际出版社 · Demai International Press · <a href="/books/">专著书架</a> · <a href="/books/m/{NO}/">书籍详情</a> · <a href="/books/m/{NO}/read.html">在线翻页</a></div> </div> <script> (function(){{var p=document.getElementById('prog');addEventListener('scroll',function(){{var h=document.documentElement;p.style.width=(h.scrollTop/(h.scrollHeight-h.clientHeight)*100)+'%';}},{{passive:true}}); var sizes=[16,17,18,20,22],k=2;try{{var s=localStorage.getItem('bk{NO}-fs');if(s)k=+s;var d=localStorage.getItem('bk{NO}-dark');if(d==='1')document.documentElement.classList.add('dark');}}catch(e){{}} function ap(){{document.body.style.fontSize=sizes[k]+'px';}}ap(); document.getElementById('fs').onclick=function(){{k=(k+1)%sizes.length;ap();try{{localStorage.setItem('bk{NO}-fs',k)}}catch(e){{}}}}; document.getElementById('th').onclick=function(){{var on=document.documentElement.classList.toggle('dark');try{{localStorage.setItem('bk{NO}-dark',on?'1':'0')}}catch(e){{}}}};}})(); </script></body></html>'''
open(OUT + '/text/index.html', 'w').write(text_html)

# ---------- sources + learning.json ----------
def plain(md):
    out = []
    for line in md.split('\n'):
        l = line
        m = re.match(r'^(#+)\s+(.*)', l)
        if m:
            l = ('◆ ' if len(m.group(1)) == 2 else '') + m.group(2)
        l = l.replace('**', '')
        if l.startswith('|'):
            if re.match(r'^\|[\s\-:|]+\|$', l): continue
            l = '｜'.join(x.strip() for x in l.strip('|').split('|'))
        out.append(l)
    t = '\n'.join(out)
    return re.sub(r'\n{3,}', '\n\n', t).strip()
tasks = []
for ch in chapters:
    n = ch['n']; L = lesson(n); md = chap_md(n)
    txt = plain(md); sha = hashlib.sha256(txt.encode()).hexdigest()
    url = f'{BASE}/text/#{anchors[n]}'
    sections = [{'title': re.sub(r'\*\*', '', s), 'url': url} for s in re.findall(r'^##\s+(.*)$', md, re.M)]
    src = {'book': f'm-{NO}', 'lesson': n, 'version': VERSION, 'title': ch['full'], 'url': url, 'sha256': sha, 'sections': sections, 'text': txt}
    json.dump(src, open(f'{OUT}/unit/sources/chapter-{n:02d}.json', 'w'), ensure_ascii=False, indent=2)
    tasks.append({'lesson': n, 'problemId': f'M{NO}-C{n:02d}', 'part': bian_index[(ch['pi'], ch['bi'])], 'title': L['title'], 'question': L['question'],
                  'checkpoint': L['checkpoint'], 'chapterTitle': ch['full'], 'sourceUrl': url,
                  'sourceData': f'/books/m/{NO}/unit/sources/chapter-{n:02d}.json', 'sourceSha256': sha})
learning = {'schemaVersion': '1.0', 'book': f'm-{NO}', 'number': NO, 'title': TITLE, 'authors': [AUTHOR], 'sourceEdition': VERSION,
            'taskVersion': TASKVER, 'parts': BIANS, 'tasks': tasks, 'companionDesign': True, 'realModelTested': False, 'learningEffectTested': False}
json.dump(learning, open(OUT + '/unit/learning.json', 'w'), ensure_ascii=False, indent=2)

# ---------- unit JS/CSS ----------
BOOKPOINTS = open(B + '/bookpoints.txt').read().strip().replace("'", '’').replace('\n', ' ')
app = open(REF + '/unit/app.js').read()
old_meta = re.search(r"agentName:'快门',agentEpithet:'[^']*',bookMeta:'[^']*'", app).group(0)
app = app.replace(old_meta, f"agentName:'{AGENT}',agentEpithet:'{EPITHET}',bookMeta:'《{TITLE}》 · {AUTHOR}'")
old_pts = re.search(r"bookPoints:'.*?本轮模式：'", app).group(0)
app = app.replace(old_pts, f"bookPoints:'{BOOKPOINTS} 本轮模式：'")
reps = [("B='/books/m/502/'", f"B='/books/m/{NO}/'"), ("n<1||n>32", "n<1||n>66"), ("+' / 32 章", "+' / 66 章"), ("题号不在本书三十二章范围内", "题号不在本书六十六章范围内"),
        ("'m502-个人学习档案-'", f"'m{NO}-个人学习档案-'"), ("'m502-救援记录-'", f"'m{NO}-救援记录-'"), ("'sde-m502-learning'", f"'sde-m{NO}-learning'")]
for a, b in reps:
    assert a in app, a; app = app.replace(a, b)
assert '502' not in app and '快门' not in app and '王德生' not in app, [m.start() for m in re.finditer('502|快门|王德生', app)]
open(OUT + '/unit/app.js', 'w').write(app)
core = open(REF + '/unit/core.js').read()
for a, b in [('Book 502', f'Book {NO}'), ("BOOK='m-502'", f"BOOK='m-{NO}'"), ("NAME='sde-publication-m502-v1'", f"NAME='sde-publication-m{NO}-v1'"), ('e.lesson>32', 'e.lesson>66'), ('d.lesson>32', 'd.lesson>66')]:
    assert a in core, a; core = core.replace(a, b)
assert '502' not in core and '>32' not in core
open(OUT + '/unit/core.js', 'w').write(core)
shutil.copy(REF + '/unit/unit.css', OUT + '/unit/unit.css')
open(OUT + '/unit/SKILL.md', 'w').write(open(B + '/SKILL.md').read())

# ---------- agent pages ----------
def agent_page(fn):
    h = open(f'{REF}/agent/{fn}').read()
    for a, b in [('三十二章快门实践', f'六十六章{AGENT}实践'), ('三十二章学习包', '六十六章学习包'), ('三十二章实践', '六十六章实践'), ('七编 · 三十二章', '十三编 · 六十六章'),
                 ('三十二章任务', '六十六章任务'), ('快门', AGENT), ('个人知识发生平台的数据基因', TITLE), ('王德生', AUTHOR),
                 ('shuju-jiyin', SLUG), ('m502', f'm{NO}'), ('m-502', f'm-{NO}'), ('/m/502/', f'/m/{NO}/'), ('第502卷', f'第{NO}卷'),
                 ('content="502"', f'content="{NO}"'), ('20261028a', V), ('979-8-90690-502-4', META['isbn']), ('US$20.00', META['price']), ('20261028-m502-unit-v1.0', TASKVER), ('带一件你的事来，先问你自己的问', '带一件你守了多年的事来，先问你守着哪一个一')]:
        h = h.replace(a, b)
    left = [m.group(0) for m in re.finditer(r'.{20}(502|三十二|快门|数据基因).{20}', h)]
    assert not left, (fn, left[:3])
    return h
for fn in ('learning.html', 'dialogue.html'):
    open(f'{OUT}/agent/{fn}', 'w').write(agent_page(fn))
ag = open(REF + '/agent/index.html').read()
AG = json.load(open(B + '/agent_entry.json'))
desc = AG['intro'][:150]
ag = re.sub(r'<title>.*?</title>', f'<title>{AGENT} · 《{TITLE}》的智能体 | 德麦国际专著第 {NO} 号</title>', ag, flags=re.S)
ag = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{html.escape(desc)}">', ag)
ag = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{html.escape(desc)}">', ag)
ag = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{AGENT} · 《{TITLE}》的智能体">', ag)
ag = ag.replace('content="快门"', f'content="{AGENT}"').replace('content="502"', f'content="{NO}"').replace('/m/502/', f'/m/{NO}/').replace('{no:502}', '{no:' + str(NO) + '}').replace('20261028a', V)
assert not re.search('502|快门|数据基因', ag), re.findall('.{30}(?:502|快门|数据基因).{30}', ag)[:3]
open(OUT + '/agent/index.html', 'w').write(ag)

# ---------- keypoints / publication-unit ----------
kp = json.load(open(B + '/keypoints_src.json'))
json.dump({'no': NO, 'title': TITLE, 'built': '2026-10-28', 'items': kp}, open(OUT + '/keypoints.json', 'w'), ensure_ascii=False, indent=1)
pu = json.load(open(REF + '/publication-unit.json'))
pu.update({'unitId': f'm-{NO}', 'number': NO, 'title': TITLE, 'authors': [AUTHOR], 'isbn': META['isbn'], 'price': META['price'],
           'sourceEdition': VERSION, 'revision': TASKVER, 'learningTasks': len(tasks), 'parts': len(BIANS), 'agentName': AGENT,
           'localStorage': f'IndexedDB / sde-publication-m{NO}-v1; append-only events; no silent trimming'})
pu['components'] = [
    {'kind': 'reading', 'url': f'{BASE}/read.html', 'textUrl': f'{BASE}/text/', 'pdfUrl': f'{BASE}/{SLUG}-reader.pdf'},
    {'kind': 'learning', 'url': f'{BASE}/agent/learning.html', 'dataUrl': f'{BASE}/unit/learning.json', 'pdfUrl': f'{BASE}/downloads/{SLUG}-learning-v1.0.pdf'},
    {'kind': 'dialogue', 'url': f'{BASE}/agent/dialogue.html', 'legacyUrl': f'{BASE}/agent/', 'name': AGENT, 'skillUrl': f'{BASE}/unit/SKILL.md'}]
json.dump(pu, open(OUT + '/publication-unit.json', 'w'), ensure_ascii=False, indent=2)
json.dump({'anchors': anchors, 'tasks': len(tasks)}, open(B + '/unit_anchors.json', 'w'))
print('unit built:', len(tasks), 'tasks;', sid[0], 'text sections')
