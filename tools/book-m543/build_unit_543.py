#!/usr/bin/env python3
"""三位一体出版单元生成器（阅读 · 学习包 · 智能问对）——第 543 号《奥特曼为何感到悲伤？》用。

由第 542 号 build_unit_542.py（原由 tools/book_unit/build_unit.py 泛化）改来，三处不同：
  1. 学习包是“十三件明天能试的小事”，不是一章一题：每项对应本书一至两章（m543.json 的 chapters），
     unit/sources/chapter-NN.json 的 NN 是任务序号，正文取该项对应章节的全文拼接；
  2. 学习包 PDF 用 WeasyPrint 出（封面、版式沿第 541 号学习包：190×250mm，深蓝封面，奶白页，一项一页），
     每项含：对应章节、一句话任务、怎么做、做完自检（第 26 章三问）、带走的话；
  3. 只写 unit/、agent/learning.html、agent/dialogue.html、publication-unit.json 与 PDF；
     不碰 read.html、text/、封面、书本身的 PDF（任务书令）。详情页、目录、智能体登记在 publish.py。

只写 public/books/m/543/ 之下：
  unit/{app.js,core.js,unit.css,SKILL.md,learning.json,sources/chapter-NN.json}
  agent/{learning.html,dialogue.html}
  publication-unit.json
  PDF 写到 --out-pdf 指定处（不进 git；R2 路径 students/wang-desheng/altman-sadness/m543/altman-sadness-learning-v1.0.pdf）

用法（仓库根目录）：
  python3 tools/book-m543/build_unit_543.py --config tools/book_unit/m543.json \
      --out-pdf /home/claude/543-altman/build/out/altman-sadness-learning-v1.0.pdf
先要有 public/books/m/543/text/index.html（本脚本据它给每章找锚点）。
"""
import argparse, hashlib, html, json, re, sys
from pathlib import Path

ROOT = Path.cwd()
TPL = ROOT / 'tools/m398_unit'
CN = '零一二三四五六七八九十'


def cn(n):
    if n <= 10: return CN[n]
    if n < 20: return '十' + CN[n - 10]
    t, o = divmod(n, 10)
    return CN[t] + '十' + (CN[o] if o else '')


def sha(b): return hashlib.sha256(b).hexdigest()


def sub1(text, old, new, count=1):
    assert text.count(old) >= 1, 'template anchor missing: ' + old[:60]
    return text.replace(old, new) if count == 0 else text.replace(old, new, count)


def parse_manuscript(path):
    s = Path(path).read_text(encoding='utf-8')
    parts, chaps, cur = [], {}, None
    for blk in re.split(r'\n(?=#{1,2} )', '\n' + s):
        blk = blk.strip('\n')
        if not blk: continue
        head, _, body = blk.partition('\n')
        m = re.match(r'# (第[一二三四五六七八九十]+[编篇部])　(.*)', head)
        if m:
            parts.append(m.group(1) + '　' + m.group(2)); cur = len(parts); continue
        m = re.match(r'## 第 ?(\d+) ?章　(.*)', head)
        if m:
            chaps[int(m.group(1))] = {'lesson': int(m.group(1)), 'title': '第%s章　%s' % (m.group(1), m.group(2)), 'part': cur, 'body': body}
    return parts, chaps


def plain(body):
    t = re.sub(r'^#{1,6} ', '', body, flags=re.M).replace('**', '')
    t = re.sub(r'^> ?', '', t, flags=re.M)
    return re.sub(r'\n{3,}', '\n\n', t).strip()


def question_of(t):
    steps = ''.join('%s%s' % ('①②③④⑤'[i], s) for i, s in enumerate(t['how']))
    q = '一句话任务：' + t['task'] + '　怎么做：' + steps
    if t.get('note'): q += '　提醒：' + t['note']
    return q


def checkpoint_of(t):
    return ('自检三问（第26章）——它从哪里来？' + t['origin'] + '　它在我这里变成了什么？' + t['mine'] + '　怎样会错？' + t['wrong'] +
            '　本项的带走的话（第%s章）：%s' % ('、'.join(str(c) for c in t['chapters']), t['takeaway']))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--config', required=True)
    ap.add_argument('--out-pdf', default=None)
    a = ap.parse_args()
    C = json.loads(Path(a.config).read_text(encoding='utf-8'))
    N = C['number']; U = '/books/m/%d/' % N; URL = 'https://sdeuniverses.com' + U
    BOOK = ROOT / ('public/books/m/%d' % N)
    REV = C['unitRev']; V = C['assetVersion']
    nt = len(C['tasks'])
    parts, chaps = parse_manuscript(C['manuscript'])
    assert len(chaps) == 27 and len(parts) == 7, (len(chaps), len(parts))
    part_names = [p.split('　', 1)[1] for p in parts]
    plabels = [p.split('　', 1)[0] for p in parts]
    NUMW = C['countWord']; PW = C['partWord']; UW = C['unitWord']
    assert [t['lesson'] for t in C['tasks']] == list(range(1, nt + 1))
    assert cn(nt) == NUMW, (cn(nt), NUMW)
    assert sorted({t['part'] for t in C['tasks']}) == list(range(1, 8)), '七编每编至少一项'
    for t in C['tasks']:
        assert all(chaps[c]['part'] == t['part'] for c in t['chapters']), t['name']
        for k in ('task', 'how', 'origin', 'mine', 'wrong', 'takeaway'): assert t.get(k), (t['lesson'], k)

    tx = (BOOK / 'text/index.html').read_text(encoding='utf-8')
    anchors = {int(m.group(2)): m.group(1) for m in re.finditer(r'<(?:div|section) class="chapter" id="(s\d+)">(?:<div class="chapnum[^"]*">[^<]*</div>)?<div class="chap-label">第 ?(\d+) ?章', tx)}
    assert len(anchors) == 27, 'text page anchors: %d' % len(anchors)

    def w(rel, content):
        p = BOOK / rel; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding='utf-8')
    def jw(rel, data): w(rel, json.dumps(data, ensure_ascii=False, indent=2) + '\n')

    # ---- sources + manifest（一项一个来源文件：对应章节全文拼接）
    manifest = {'schemaVersion': '1.0', 'book': 'm-%d' % N, 'number': N, 'title': C['title'], 'authors': C['authors'],
                'sourceEdition': C['sourceEdition'], 'taskVersion': REV, 'taskUnit': UW, 'parts': part_names, 'tasks': [],
                'companionDesign': True, 'realModelTested': False, 'learningEffectTested': False}
    for t in C['tasks']:
        i = t['lesson']
        cs = [chaps[c] for c in t['chapters']]
        text = '\n\n————\n\n'.join(c['title'] + '\n\n' + plain(c['body']) for c in cs)
        title = '；'.join(c['title'] for c in cs)
        url = URL + 'text/#' + anchors[t['chapters'][0]]
        secs = []
        for c in cs:
            for m in re.finditer(r'^◆ (.*)$', plain(c['body']), flags=re.M):
                secs.append({'title': '第%d章 ' % c['lesson'] + m.group(1).strip(), 'url': URL + 'text/#' + anchors[c['lesson']]})
        h = sha(text.encode())
        jw('unit/sources/chapter-%02d.json' % i, {'book': 'm-%d' % N, 'lesson': i, 'chapters': t['chapters'], 'version': C['sourceEdition'], 'title': title,
                                                  'url': url, 'sha256': h, 'sections': secs, 'text': text})
        # problemId 取 C 是为合 tools/check_publication_identity.py；NN 是任务序号（不是章号）
        manifest['tasks'].append({'lesson': i, 'problemId': 'M%d-C%02d' % (N, i), 'part': t['part'], 'title': t['name'], 'question': question_of(t),
                                  'checkpoint': checkpoint_of(t), 'chapters': t['chapters'], 'chapterTitle': title, 'sourceUrl': url,
                                  'sourceData': U + 'unit/sources/chapter-%02d.json' % i, 'sourceSha256': h,
                                  'task': t['task'], 'how': t['how'], 'note': t.get('note', ''),
                                  'selfCheck': {'origin': t['origin'], 'mine': t['mine'], 'wrong': t['wrong']}, 'takeaway': t['takeaway']})
    jw('unit/learning.json', manifest)

    # ---- 程序与样式：取参考实现（tools/m398_unit），按本书改
    core = (TPL / 'core.js').read_text(encoding='utf-8')
    core = sub1(core, "BOOK='m-398'", "BOOK='m-%d'" % N)
    core = sub1(core, "sde-publication-m398-v1", "sde-publication-m%d-v1" % N)
    core = sub1(core, "e.lesson>40", "e.lesson>%d" % nt)
    core = sub1(core, "d.lesson>40", "d.lesson>%d" % nt)
    core = sub1(core, "Book 398", "Book %d" % N)
    core = sub1(core, "M398Core", "BookUnitCore", 0)
    w('unit/core.js', core)

    app = (TPL / 'app.js').read_text(encoding='utf-8')
    app = sub1(app, "window.M398Core", "window.BookUnitCore")
    app = sub1(app, "B='/books/m/398/'", "B='%s'" % U)
    app = sub1(app, "' / 40 章 ·", "' / %d %s ·" % (nt, UW))
    app = sub1(app, "n>40)throw Error('题号不在本书四十章范围内。')", "n>%d)throw Error('题号不在本书%s%s范围内。')" % (nt, NUMW, UW))
    app = sub1(app, "'第'+(i+1)+'编 · '", "(%s[i]||('第'+(i+1)+'%s'))+' · '" % (json.dumps(plabels, ensure_ascii=False), PW))
    app = sub1(app, "manifest.tasks.slice(i*5,i*5+5).forEach(", "manifest.tasks.filter(t=>t.part===i+1).forEach(")
    # 一项对应一至两章：把“章”的说法改成“项”
    app = sub1(app, "+lesson+'章已准备好", "+lesson+'%s已准备好" % UW)
    app = sub1(app, "· 本章完整文本已载入浏览器", "· 本项对应章节的完整文本已载入浏览器")
    app = sub1(app, "【本章原文】", "【本项对应章节原文】")
    app = sub1(app, "本轮只选本书第'+lesson+'章。", "本轮只选本书第'+lesson+'%s任务对应的章节。" % UW)
    app = sub1(app, "正在请求第'+p.lesson+'章的「", "正在请求第'+p.lesson+'%s任务的「" % UW)
    app = sub1(app, "'第'+p.lesson+'章回复已返回", "'第'+p.lesson+'%s回复已返回" % UW)
    app = sub1(app, "已保留第'+p.lesson+'章的本轮记录", "已保留第'+p.lesson+'%s的本轮记录" % UW)
    m = re.search(r"return \{q,bookagent:1,act:MODES\[mode\]\[1\],agentName:'判生',agentEpithet:'[^']*',bookMeta:'[^']*',docTitle", app)
    assert m, 'payload anchor'
    for k in ('agentName', 'agentEpithet', 'bookMeta', 'bookPoints'): assert "'" not in C[k], k
    app = app.replace(m.group(0), "return {q,bookagent:1,act:MODES[mode][1],agentName:'%s',agentEpithet:'%s',bookMeta:'%s',docTitle" % (C['agentName'], C['agentEpithet'], C['bookMeta']))
    m = re.search(r"bookPoints:'.*?本轮模式：'", app)
    assert m, 'bookPoints anchor'
    app = app.replace(m.group(0), "bookPoints:'" + C['bookPoints'] + "本轮模式：'")
    app = sub1(app, "m398-个人学习档案-", "m%d-个人学习档案-" % N)
    app = sub1(app, "m398-救援记录-", "m%d-救援记录-" % N)
    app = sub1(app, "sde-m398-learning", "sde-m%d-learning" % N)
    assert '398' not in app and '判生' not in app, 'leftover 398/判生 in app.js'
    w('unit/app.js', app)
    w('unit/unit.css', (TPL / 'unit.css').read_text(encoding='utf-8'))

    # ---- SKILL.md：头部 + 角色与纪律（本书新增）+ 模板的接续单位/六种任务 + 理论与证据 + 两次回写与数据边界
    skill = ('# %s · 第%d卷学习问对规范 v1.0\n\n书籍：《%s》，%s著，第%d卷，ISBN %s。当前正文依据：%s。学习包为配套教学设计，不是著者原文、标准答案或已验证量表。\n\n' % (
        C['agentName'], N, C['title'], '、'.join(C['authors']), N, C['isbn'], C['sourceEdition']))
    skill += C['skillRole'] + '\n\n'
    tail = (TPL / 'SKILL.md').read_text(encoding='utf-8')
    tail = tail[tail.index('## 接续的最小单位'):tail.index('## 理论与证据')]
    tail = tail.replace('m-398', 'm-%d' % N).replace('lesson=1..40', 'lesson=1..%d（一项一件小事，对应本书一至两章）' % nt)
    skill += tail
    skill += '## 理论与证据\n' + C['skillTheory'] + '\n\n'
    rest = (TPL / 'SKILL.md').read_text(encoding='utf-8')
    skill += rest[rest.index('## 两次回写与数据边界'):]
    assert '398' not in skill, 'leftover 398 in SKILL.md'
    w('unit/SKILL.md', skill)

    # ---- 页面（learning.html / dialogue.html）
    pg = (TPL / 'page.html').read_text(encoding='utf-8')
    byline = ' · '.join(C['authors'])
    reps = [
        ('AI时代的判断力发生学导论', C['title']),
        ('王德生、张琼', '、'.join(C['authors'])),
        ('王德生 · 张琼', byline),
        ('content="398"', 'content="%d"' % N),
        ('m-398', 'm-%d' % N),
        ('/books/m/398/chapters.html', U + 'text/'),
        ('/books/m/398/downloads/judgment-learning-v1.0.pdf', C['learningPdfUrl']),
        ('cover-unit-v1.jpg', 'cover.jpg?v=' + V),
        ('刀切冬瓜主题封面，', ''),
        ('/books/m/398/', U),
        ('学习包 · 四十章实践', '学习包 · %s件%s' % (NUMW, C['practiceWord'])),
        ('下载四十章学习包 PDF', '下载%s件%s学习包 PDF' % (NUMW, C['practiceWord'])),
        ('aria-label="四十章任务"><h2>八编 · 四十章</h2>', 'aria-label="%s%s任务"><h2>%s%s · %s%s</h2>' % (NUMW, UW, cn(7), PW, NUMW, UW)),
        ('选择本章任务', '选择任务'),
        ('阅读本章原文', '阅读对应章节原文'),
        ('智能问对 · 判生', '智能问对 · ' + C['agentName']),
        ('带着材料进入判生', '带着材料进入' + C['agentName']),
        ('原有判生入口', '原有' + C['agentName'] + '入口'),
        ('第398卷', '第%d卷' % N),
        ('ISBN 979-8-90690-868-1 · US$20', 'ISBN %s · %s' % (C['isbn'], C['price'])),
        ('正文修订版v3.0；封面与三位一体单元更新20261008-u1。', '正文%s；三位一体单元%s。' % (C['sourceEdition'], REV)),
        ('20261008u1', V),
        ('让判断沿着原文、实践与反馈继续发生。', C['heroTagline']),
    ]
    for old, new in reps:
        if old in pg: pg = pg.replace(old, new)
    assert '398' not in pg.replace('@@', ''), 'leftover 398 in page.html: ' + str([m.group(0) for m in re.finditer('.{20}398.{20}', pg)][:3])
    assert '判生' not in pg and '张琼' not in pg and '判断力' not in pg.replace(C['title'], ''), 'leftover m398 wording'
    for file, view, title in [('learning.html', 'learning', '学习包 · %s件%s' % (NUMW, C['practiceWord'])), ('dialogue.html', 'dialogue', '智能问对 · ' + C['agentName'])]:
        t = pg
        for k, v in {'PAGE_TITLE': title, 'FILE': file, 'VIEW': view,
                     'LEARN_CURRENT': 'aria-current="page"' if view == 'learning' else '',
                     'DIALOGUE_CURRENT': 'aria-current="page"' if view == 'dialogue' else ''}.items():
            t = t.replace('@@' + k + '@@', v)
        w('agent/' + file, t)

    unit = {'schemaVersion': '1.0', 'unitId': 'm-%d' % N, 'number': N, 'type': 'reading-learning-dialogue', 'label': '阅读、学习、智能问对三位一体出版单元',
            'title': C['title'], 'authors': C['authors'], 'isbn': C['isbn'], 'price': C['price'], 'publisher': '德麦国际出版社',
            'sourceEdition': C['sourceEdition'], 'revision': REV, 'learningTasks': nt, 'learningTaskUnit': '件明天能试的小事（每项对应本书一至两章）',
            'parts': len(parts), 'agentName': C['agentName'],
            'components': [
                {'kind': 'reading', 'url': URL + 'read.html', 'textUrl': URL + 'text/', 'pdfUrl': C['readerPdfUrl']},
                {'kind': 'learning', 'url': URL + 'agent/learning.html', 'dataUrl': URL + 'unit/learning.json', 'pdfUrl': C['learningPdfUrl']},
                {'kind': 'dialogue', 'url': URL + 'agent/dialogue.html', 'legacyUrl': URL + 'agent/', 'name': C['agentName'], 'skillUrl': URL + 'unit/SKILL.md'}],
            'workflow': ['封存初答', '带问阅读', '复答留版本', '预览并确认本题材料', '登记待核对模型建议', '本人确认修订', '迁移计划与自报观察'],
            'localStorage': 'IndexedDB / sde-publication-m%d-v1; append-only events; no silent trimming' % N,
            'privacy': 'Key only supplied explicitly for current request; via site to selected provider; no key in learning archive; no automatic public manuscript writeback',
            'upstreamCompletion': 'Current site API has no exposed upstream finish_reason. End-of-stream is received-unverified, not certified complete.',
            'realModelTested': False, 'learningEffectTested': False, 'reindexRequested': False}
    jw('publication-unit.json', unit)

    # ---- 学习包 PDF（WeasyPrint；版式沿第 541 号：190×250mm，深蓝封面，奶白页，一项一页）
    if a.out_pdf:
        make_pdf(C, manifest, parts, chaps, BOOK, URL, Path(a.out_pdf), plabels, part_names)
    print(json.dumps({'tasks': nt, 'parts': len(parts), 'sources': nt, 'pdf': a.out_pdf}, ensure_ascii=False))


PDF_CSS = '''
@page { size: 190mm 250mm; margin: 0 }
* { box-sizing: border-box }
body { margin: 0; font-family: "Noto Sans CJK SC", "WenQuanYi Zen Hei", sans-serif; color: #263039 }
.cover { width: 190mm; height: 250mm; background: %(bg)s; position: relative; page-break-after: always; overflow: hidden }
.cover h1 { position: absolute; left: 15mm; top: 33mm; margin: 0; font-weight: 400; font-size: 25pt; color: #ead5a6; width: 160mm; line-height: 1.35 }
.cover .sub { position: absolute; left: 15mm; top: 66mm; font-size: 15pt; color: #ead5a6 }
.cover img { position: absolute; left: 15mm; top: 100mm; width: 63.4mm; height: 89.5mm }
.cover .meta { position: absolute; left: 88mm; top: 116mm; font-size: 12pt; color: #f4eddc; line-height: 2.7 }
.cover .notes { position: absolute; left: 15mm; top: 200mm; font-size: 11pt; color: #f4eddc; line-height: 2.1; width: 160mm }
.cover .link { position: absolute; left: 15mm; top: 226mm; font-size: 10.5pt; color: #f4eddc }
.cover a { color: #f4eddc; text-decoration: none }
.pg { width: 190mm; height: 250mm; background: #f8f5ed; position: relative; page-break-after: always; overflow: hidden; padding: 14mm 15mm 0 15mm }
.pg .part { color: #8a6b22; font-size: 10.5pt; margin: 0 0 3mm }
.pg h2 { font-weight: 400; font-size: 20pt; margin: 0 0 2mm; line-height: 1.35; color: #263039 }
.pg .chap { font-size: 9.5pt; color: #5d666c; margin: 0 0 4.5mm }
.lab { color: #8a6b22; font-size: 9pt; letter-spacing: .08em; margin: 3.5mm 0 1mm }
.pg p.task { font-size: %(t)spt; line-height: 1.75; margin: 0; padding: 2.5mm 3.5mm; background: #efe8d5; border-left: 1.2mm solid #cbb576 }
.pg ol { margin: 0; padding-left: 5.2mm; font-size: %(b)spt; line-height: 1.7 }
.pg ol li { margin: 0 0 1.2mm }
.pg .note { font-size: %(s)spt; color: #5d666c; margin: 1.5mm 0 0; line-height: 1.6 }
.pg .q { font-size: %(b)spt; line-height: 1.65; margin: 0 0 .6mm }
.pg .q b { font-weight: 400; color: #8a6b22 }
.ln { border-bottom: .5pt solid #d3cdbf; height: 6.6mm }
.pg .take { font-size: %(s)spt; color: #5d666c; line-height: 1.6; margin-top: 3.5mm; padding-top: 2mm; border-top: .5pt dashed #cbb576 }
.pg .foot { position: absolute; left: 15mm; right: 15mm; bottom: 6mm; border-top: .5pt solid #cbb576; padding-top: 2mm; font-size: 8pt; color: #6c7378; display: flex; justify-content: space-between }
.pg .go { position: absolute; left: 15mm; bottom: 14mm; font-size: 8pt }
.pg .go a { color: #8a6b22; text-decoration: none }
.pg ul.map { margin: 0; padding: 0; list-style: none; font-size: %(b)spt; line-height: 1.9 }
.pg ul.map li b { color: #8a6b22; font-weight: 400; display: inline-block; width: 15mm }
'''


def make_pdf(C, manifest, parts, chaps, BOOK, URL, out, plabels, part_names):
    from weasyprint import HTML
    N = C['number']; nt = len(manifest['tasks']); E = lambda s: html.escape(s, quote=False)
    cover = (BOOK / 'cover.jpg')
    sizes = [(12, 10.5, 9.5), (11.5, 10, 9), (11, 9.5, 8.5), (10.5, 9, 8)]

    def build(t_, b_, s_):
        css = PDF_CSS % {'bg': C['pdfBg'], 't': t_, 'b': b_, 's': s_}
        foot = lambda n: '<div class="foot"><span>第%d卷 · 配套学习设计，不是能力认证；不作诊断，不给投资建议</span><span>%d</span></div>' % (N, n)
        h = ['<html><head><meta charset="utf-8"><style>%s</style></head><body>' % css]
        h.append('<div class="cover"><h1>%s · 学习包</h1><div class="sub">%s编%s件明天能试的小事 · 阅读、学习、智能问对</div>'
                 '<img src="file://%s"><div class="meta">原书作者：%s<br>ISBN %s<br>第%d卷 · %s</div>'
                 '<div class="notes">先做一件手边的小事，再用三问自检；每项只用本书已有的内容。<br>人物与场景多为书中构想；〔待核〕处本包不展开，也不当事实用。<br>本包是配套设计，不是著者原文，不是能力认证，也不是诊断或投资建议。</div>'
                 '<div class="link"><a href="%sagent/learning.html">在线学习：sdeuniverses.com%sagent/learning.html</a></div></div>' % (
                     E(C['title']), cn(7), C['countWord'], cover, E('、'.join(C['authors'])), C['isbn'], N, C['price'], URL, '/books/m/%d/' % N))
        # 用法页
        mp = []
        for pi, pn in enumerate(part_names, 1):
            ls = [t['lesson'] for t in manifest['tasks'] if t['part'] == pi]
            mp.append('<li><b>第%s编</b>%s　（第%s项）</li>' % (cn(pi), E(pn), '、'.join(str(x) for x in ls)))
        h.append('<div class="pg"><p class="part">怎么用这份学习包</p><h2>一件小事一页，七编各有几件</h2><p class="chap">按全书七编排列；每项对应本书一至两章</p>'
                 '<div class="lab">做法</div><ol><li>先挑一件手边的小事。只动手边的一样东西，一天内能动手，一周后能看出起点变没变。</li>'
                 '<li>做之前，先写下你现在的猜想；不知道也可以如实记录。</li><li>读对应章节，做那件小事，把当天的事写下来。</li>'
                 '<li>做完用第26章的三问自检：它从哪里来？它在我这里变成了什么？怎样会错？三问最好由你自己问。</li>'
                 '<li>你写的东西归你：谁写的归谁，拿去给谁用，由写的人定。</li></ol>'
                 '<div class="lab">七编对照</div><ul class="map">%s</ul>'
                 '<div class="lab">边界</div><p class="note" style="font-size:%spt">每项只用本书已有的内容，不新增本书没有的命题；书中的陪读人物与场景多是作者构想，已在书中写明；凡本书标〔待核〕〔待验〕之处，本包不展开成断言。不作诊断，不作政策表态，不给投资建议；读数不拿去给人打分或排名。</p>%s</div>' % (
                     ''.join(mp), b_, foot(2)))
        for t in manifest['tasks']:
            how = ''.join('<li>%s</li>' % E(x) for x in t['how'])
            ch = '；'.join(E(chaps[c]['title']) for c in t['chapters'])
            h.append('<div class="pg"><p class="part">第%s编 · %s</p><h2>%02d　%s</h2><p class="chap">对应：%s</p>'
                     '<div class="lab">一句话任务</div><p class="task">%s</p>'
                     '<div class="lab">怎么做</div><ol>%s</ol>%s'
                     '<div class="lab">我做了什么（日期、地点，一两句）</div><div class="ln"></div><div class="ln"></div>'
                     '<div class="lab">做完自检（第26章三问）</div>'
                     '<p class="q"><b>它从哪里来？</b>%s</p><div class="ln"></div>'
                     '<p class="q"><b>它在我这里变成了什么？</b>%s</p><div class="ln"></div>'
                     '<p class="q"><b>怎样会错？</b>%s</p><div class="ln"></div>'
                     '<p class="take">带走的话（第%s章）：%s</p>'
                     '<div class="go"><a href="%sagent/learning.html?lesson=%d">点击进入本项学习、原文与%s：第%d项</a></div>%s</div>' % (
                         cn(t['part']), E(part_names[t['part'] - 1]), t['lesson'], E(t['title']), ch, E(t['task']), how,
                         ('<p class="note">%s</p>' % E(t['note'])) if t['note'] else '',
                         E(t['selfCheck']['origin']), E(t['selfCheck']['mine']), E(t['selfCheck']['wrong']),
                         '、'.join(str(c) for c in t['chapters']), E(t['takeaway']), URL, t['lesson'], E(C['agentName']), t['lesson'], foot(t['lesson'] + 2)))
        h.append('</body></html>')
        return ''.join(h)

    for sz in sizes:
        doc = HTML(string=build(*sz), base_url=str(BOOK)).render()
        if len(doc.pages) == nt + 2:
            doc.write_pdf(str(out), pdf_version='1.7')
            print('PDF %s pages=%d fontset=%s' % (out, len(doc.pages), sz))
            return
        print('overflow at fontset', sz, 'pages', len(doc.pages))
    raise SystemExit('学习包 PDF 有任务页放不下一页，请缩短文字')


if __name__ == '__main__':
    main()
