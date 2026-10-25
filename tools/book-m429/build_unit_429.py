#!/usr/bin/env python3
"""三位一体出版单元生成器（阅读 · 学习包 · 智能问对）——第 429 号用（由第 519 号复制；认中文章号、导论／收束分组、直接显示编名），由第 444 号脚本复制；原由第398卷参考实现（tools/m398_unit）泛化。

只写 public/books/m/<号>/ 之下的这些东西，不碰别的书、不调用模型、不重建搜索索引：
  unit/{app.js,core.js,unit.css,SKILL.md,learning.json,sources/chapter-NN.json}
  agent/{learning.html,dialogue.html}
  publication-unit.json
  downloads/<slug>-learning-v1.0.pdf   （写到 --out-pdf 指定处，不进 git；上传 R2）

用法（仓库根目录）：
  python3 tools/book_unit/build_unit.py --config tools/book_unit/m267.json
配置里给：书号、书名、著者、ISBN、定价、智能体名与称号、统稿 md（# 第X编 / ## 第 N 章 版式）、
任务清单（每章一条：name/question/checkpoint）、各 URL。
先跑 webtext.py 生成 text/index.html（本脚本据它给每章找锚点）。
"""
import argparse, hashlib, html, json, re, sys
from pathlib import Path

ROOT = Path.cwd()
TPL = ROOT / 'tools/m398_unit'
CN = '零一二三四五六七八九十'

def cn(n):
    if n <= 10: return CN[n]
    if n < 20: return '十' + CN[n-10]
    if n >= 100:
        h, r = divmod(n, 100)
        if r == 0: return CN[h] + '百'
        return CN[h] + '百' + ('零' + cn(r) if r < 10 else (cn(r) if r >= 20 else '一' + cn(r)))
    t, o = divmod(n, 10)
    return CN[t] + '十' + (CN[o] if o else '')

def sha(b): return hashlib.sha256(b).hexdigest()

def sub1(text, old, new, count=1):
    assert text.count(old) >= 1, 'template anchor missing: ' + old[:60]
    return text.replace(old, new) if count == 0 else text.replace(old, new, count)

def parse_manuscript(path):
    s = Path(path).read_text(encoding='utf-8')
    parts, chaps, cur = [], [], None
    for blk in re.split(r'\n(?=#{1,2} )', '\n' + s):
        blk = blk.strip('\n')
        if not blk: continue
        head, _, body = blk.partition('\n')
        m = re.match(r'# (第[一二三四五六七八九十]+[编篇]|卷[一二三四五六七八九十]+|终章|[上中下尾]篇(?:（[一二三]）)?|[上中下]编|导论|收束)　(.*)', head)
        if m:
            parts.append(m.group(1) + '　' + m.group(2)); cur = len(parts); continue
        m = re.match(r'## 第 ?(\d+|[一二三四五六七八九十]+) ?章　(.*)', head)
        if m:
            n = int(m.group(1)) if m.group(1).isdigit() else cn2int(m.group(1))
            chaps.append({'lesson': n, 'title': '第%s章　%s' % (m.group(1), m.group(2)), 'part': cur, 'body': body})
    return parts, chaps

def cn2int(s):
    d = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
    if '十' in s:
        a, _, b = s.partition('十')
        return (d[a] if a else 1) * 10 + (d[b] if b else 0)
    return d[s]

def plain(body):
    t = re.sub(r'^#{1,6} ', '', body, flags=re.M).replace('**', '')
    t = re.sub(r'^> ?', '', t, flags=re.M)
    return re.sub(r'\n{3,}', '\n\n', t).strip()

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--config', required=True)
    ap.add_argument('--out-pdf', default=None)
    a = ap.parse_args()
    C = json.loads(Path(a.config).read_text(encoding='utf-8'))
    N = C['number']; U = '/books/m/%d/' % N; URL = 'https://sdeuniverses.com' + U
    BOOK = ROOT / ('public/books/m/%d' % N)
    REV = C['unitRev']; V = C['assetVersion']
    nch = len(C['tasks'])
    parts, chaps = parse_manuscript(C['manuscript'])
    assert len(chaps) == nch and [c['lesson'] for c in chaps] == list(range(1, nch + 1)), 'chapters vs tasks mismatch'
    part_names = list(parts)
    NUMW = cn(nch); PW = C.get('partWord', '编')

    # chapter anchors in text/index.html
    tx = (BOOK / 'text/index.html').read_text(encoding='utf-8')
    anchors = {(int(m.group(2)) if m.group(2).isdigit() else cn2int(m.group(2))): m.group(1) for m in re.finditer(r'<(?:div|section) class="chapter" id="(s\d+)">(?:<div class="chapnum[^"]*">[^<]*</div>)?<div class="chap-label">第 ?(\d+|[一二三四五六七八九十]+) ?章', tx)}
    assert len(anchors) == nch, 'text page anchors: %d' % len(anchors)

    def w(rel, content):
        p = BOOK / rel; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding='utf-8')
    def jw(rel, data): w(rel, json.dumps(data, ensure_ascii=False, indent=2) + '\n')

    # ---- sources + manifest
    manifest = {'schemaVersion': '1.0', 'book': 'm-%d' % N, 'number': N, 'title': C['title'], 'authors': C['authors'],
                'sourceEdition': C['sourceEdition'], 'taskVersion': REV, 'parts': part_names, 'tasks': [],
                'companionDesign': True, 'realModelTested': False, 'learningEffectTested': False}
    for t, c in zip(C['tasks'], chaps):
        i = t['lesson']; assert i == c['lesson']
        body = plain(c['body'])
        url = URL + 'text/'
        secs = [{'title': m.group(1).strip(), 'url': url + '#' + anchors[i]} for m in re.finditer(r'^◆ (.*)$', body, flags=re.M)]
        text = c['title'] + '\n\n' + body
        h = sha(text.encode())
        src = {'book': 'm-%d' % N, 'lesson': i, 'version': C['sourceEdition'], 'title': c['title'], 'url': url + '#' + anchors[i], 'sha256': h, 'sections': secs, 'text': text}
        jw('unit/sources/chapter-%02d.json' % i, src)
        manifest['tasks'].append({'lesson': i, 'problemId': 'M%d-C%02d' % (N, i), 'part': c['part'], 'title': t['name'], 'question': t['question'],
                                  'checkpoint': t['checkpoint'], 'chapterTitle': c['title'], 'sourceUrl': url + '#' + anchors[i],
                                  'sourceData': U + 'unit/sources/chapter-%02d.json' % i, 'sourceSha256': h})
    jw('unit/learning.json', manifest)

    # ---- templates derived from the reference implementation
    core = (TPL / 'core.js').read_text(encoding='utf-8')
    core = sub1(core, "BOOK='m-398'", "BOOK='m-%d'" % N)
    core = sub1(core, "sde-publication-m398-v1", "sde-publication-m%d-v1" % N)
    core = sub1(core, "e.lesson>40", "e.lesson>%d" % nch)
    core = sub1(core, "d.lesson>40", "d.lesson>%d" % nch)
    core = sub1(core, "Book 398", "Book %d" % N)
    core = sub1(core, "M398Core", "BookUnitCore", 0)
    w('unit/core.js', core)

    app = (TPL / 'app.js').read_text(encoding='utf-8')
    app = sub1(app, "window.M398Core", "window.BookUnitCore")
    app = sub1(app, "B='/books/m/398/'", "B='%s'" % U)
    app = sub1(app, "+' / 40 章 ·", "+' / %d 章 ·" % nch)
    app = sub1(app, "n>40)throw Error('题号不在本书四十章范围内。')", "n>%d)throw Error('题号不在本书%s章范围内。')" % (nch, NUMW))
    # part grouping by task.part instead of 5 per part
    app = sub1(app, "'第'+(i+1)+'编 · '", "''")
    app = sub1(app, "manifest.tasks.slice(i*5,i*5+5).forEach(", "manifest.tasks.filter(t=>t.part===i+1).forEach(")
    # agent identity and book points
    m = re.search(r"return \{q,bookagent:1,act:MODES\[mode\]\[1\],agentName:'判生',agentEpithet:'[^']*',bookMeta:'[^']*',docTitle", app)
    assert m, 'payload anchor'
    app = app.replace(m.group(0), "return {q,bookagent:1,act:MODES[mode][1],agentName:%s,agentEpithet:%s,bookMeta:%s,docTitle" % (
        json.dumps(C['agentName'], ensure_ascii=False).replace('"', "'"), "'" + C['agentEpithet'].replace("'", "\\'") + "'", "'" + C['bookMeta'].replace("'", "\\'") + "'"))
    m = re.search(r"bookPoints:'.*?本轮模式：'", app)
    assert m, 'bookPoints anchor'
    app = app.replace(m.group(0), "bookPoints:'" + C['bookPoints'].replace("'", "\\'") + "本轮模式：'")
    app = sub1(app, "m398-个人学习档案-", "m%d-个人学习档案-" % N)
    app = sub1(app, "m398-救援记录-", "m%d-救援记录-" % N)
    app = sub1(app, "sde-m398-learning", "sde-m%d-learning" % N)
    assert '398' not in app and '判生' not in app, 'leftover 398/判生 in app.js'
    w('unit/app.js', app)
    w('unit/unit.css', (TPL / 'unit.css').read_text(encoding='utf-8'))

    skill = ('# %s · 第%d卷学习问对规范 v1.0\n\n书籍：《%s》，%s著，第%d卷，ISBN %s。当前正文依据：%s。学习包为配套教学设计，不是著者原文、标准答案或已验证量表。\n' % (
        C['agentName'], N, C['title'], '、'.join(C['authors']), N, C['isbn'], C['sourceEdition']))
    tail = (TPL / 'SKILL.md').read_text(encoding='utf-8')
    tail = tail[tail.index('## 接续的最小单位'):tail.index('## 理论与证据')]
    skill += '\n' + tail.replace('m-398', 'm-%d' % N).replace('lesson=1..40', 'lesson=1..%d' % nch)
    skill += '## 理论与证据\n' + C['skillTheory'] + '\n\n'
    rest = (TPL / 'SKILL.md').read_text(encoding='utf-8')
    rest = rest[rest.index('## 两次回写与数据边界'):]
    skill += rest
    assert '398' not in skill, 'leftover 398 in SKILL.md'
    w('unit/SKILL.md', skill)

    # ---- pages
    pg = (TPL / 'page.html').read_text(encoding='utf-8')
    full_title = '《%s》' % C['title']
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
        ('学习包 · 四十章实践', '学习包 · %s章实践' % NUMW),
        ('下载四十章学习包 PDF', '下载%s章学习包 PDF' % NUMW),
        ('aria-label="四十章任务"><h2>八编 · 四十章</h2>', 'aria-label="%s章任务"><h2>%s</h2>' % (NUMW, C['structureLabel'])),
        ('智能问对 · 判生', '智能问对 · ' + C['agentName']),
        ('带着材料进入判生', '带着材料进入' + C['agentName']),
        ('原有判生入口', '原有' + C['agentName'] + '入口'),
        ('第398卷', '第%d卷' % N),
        ('ISBN 979-8-90690-868-1 · US$20', 'ISBN %s · %s' % (C['isbn'], C['price'])),
        ('正文修订版v3.0；封面与三位一体单元更新20261008-u1。', '正文%s；三位一体单元%s。' % (C['sourceEdition'], REV)),
        ('20261008u1', V),
        ('让判断沿着原文、实践与反馈继续发生。', C['heroTagline']),
        ('7px', '7px'),
    ]
    for old, new in reps:
        if old in pg: pg = pg.replace(old, new)
    pg = sub1(pg, '<title>@@PAGE_TITLE@@ · ' + C['title'] + '</title>', '<title>@@PAGE_TITLE@@ · ' + C['title'] + '</title>')
    assert '398' not in pg.replace('@@', ''), 'leftover 398 in page.html: ' + str([m.group(0) for m in re.finditer('.{20}398.{20}', pg)][:3])
    assert '判生' not in pg and '张琼' not in pg and '判断力' not in pg.replace(C['title'], ''), 'leftover m398 wording'
    for file, view, title in [('learning.html', 'learning', '学习包 · %s章%s实践' % (NUMW, C['practiceWord'])), ('dialogue.html', 'dialogue', '智能问对 · ' + C['agentName'])]:
        t = pg
        for k, v in {'PAGE_TITLE': title, 'FILE': file, 'VIEW': view,
                     'LEARN_CURRENT': 'aria-current="page"' if view == 'learning' else '',
                     'DIALOGUE_CURRENT': 'aria-current="page"' if view == 'dialogue' else ''}.items():
            t = t.replace('@@' + k + '@@', v)
        w('agent/' + file, t)

    unit = {'schemaVersion': '1.0', 'unitId': 'm-%d' % N, 'number': N, 'type': 'reading-learning-dialogue', 'label': '阅读、学习、智能问对三位一体出版单元',
            'title': C['title'], 'authors': C['authors'], 'isbn': C['isbn'], 'price': C['price'], 'publisher': '德麦国际出版社',
            'sourceEdition': C['sourceEdition'], 'revision': REV, 'learningTasks': nch, 'parts': len(parts), 'agentName': C['agentName'],
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

    # ---- learning workbook PDF (one task per page)
    if a.out_pdf:
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        from reportlab.platypus import Paragraph
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.colors import HexColor
        from reportlab.pdfbase.ttfonts import TTFont
        pdfmetrics.registerFont(TTFont('STSong-Light', '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', subfontIndex=0))
        c = canvas.Canvas(a.out_pdf, pagesize=(538.58, 708.66)); c.setTitle(C['title'] + ' · 学习包'); c.setAuthor('、'.join(C['authors']) + '（原书）；配套学习设计')
        style = ParagraphStyle('Body', fontName='STSong-Light', fontSize=11.5, leading=20, textColor=HexColor('#263039'), wordWrap='CJK', spaceAfter=8)
        def para(s, x, y, wd=450, size=11.5):
            st = ParagraphStyle('p', parent=style, fontSize=size, leading=size * 1.7); p = Paragraph(html.escape(s), st); _, h = p.wrap(wd, 700); p.drawOn(c, x, y - h); return y - h - 12
        def footer(n):
            c.setStrokeColor(HexColor('#cbb576')); c.line(43, 40, 495, 40); c.setFillColor(HexColor('#6c7378')); c.setFont('STSong-Light', 9)
            c.drawString(43, 23, '第%d卷 · 配套学习设计，不是能力认证' % N); c.drawRightString(495, 23, str(n))
        c.setFillColor(HexColor(C['pdfBg'])); c.rect(0, 0, 538.58, 708.66, fill=1, stroke=0)
        cover = BOOK / 'cover.jpg'
        if cover.exists(): c.drawImage(str(cover), 44, 220, width=179.6, height=253.6)
        c.setFillColor(HexColor('#ead5a6')); c.setFont('STSong-Light', 25); c.drawString(43, 640, C['title'] + ' · 学习包')
        c.setFont('STSong-Light', 15); c.drawString(43, 602, '%s · 阅读、学习、智能问对' % C['structureLabel'])
        c.setFillColor(HexColor('#f4eddc')); c.setFont('STSong-Light', 12)
        c.drawString(250, 450, '原书作者：' + '、'.join(C['authors'])); c.drawString(250, 420, 'ISBN ' + C['isbn']); c.drawString(250, 390, '第%d卷 · %s' % (N, C['price']))
        c.setFont('STSong-Light', 11)
        for yy, s in [(178, '先答、带问阅读、再答、讨论、本人修订、迁移与观察。'), (150, '初答不覆盖；建议待核对；理解、赞同和现实应用分别记录。'), (122, '本包是配套设计，不是著者原文或已验证训练量表。')]: c.drawString(43, yy, s)
        c.linkURL(URL + 'agent/learning.html', (40, 64, 500, 100), relative=0); c.drawString(43, 80, '在线学习：sdeuniverses.com' + U + 'agent/learning.html'); c.showPage()
        for t in manifest['tasks']:
            c.setFillColor(HexColor('#f8f5ed')); c.rect(0, 0, 538.58, 708.66, fill=1, stroke=0); y = 656
            c.setFillColor(HexColor('#8a6b22')); c.setFont('STSong-Light', 11); c.drawString(43, y, part_names[t['part'] - 1]); y -= 26
            y = para('%02d  %s' % (t['lesson'], t['title']), 43, y, size=21)
            y = para(t['chapterTitle'], 43, y, size=10)
            y = para(t['question'], 43, y, size=12)
            y = para('先答：保留自己的起点；不知道也可以如实记录。', 43, y, size=11)
            for _ in range(2): c.setStrokeColor(HexColor('#d3cdbf')); c.line(43, y - 8, 495, y - 8); y -= 24
            y -= 12; y = para('读后追问：' + t['checkpoint'], 43, y, size=11)
            y = para('复答／异议：什么改变，什么仍不同意？原文依据在哪里？', 43, y, size=11)
            for _ in range(2): c.line(43, y - 8, 495, y - 8); y -= 24
            y -= 10; y = para('下一步与回看：行动、观察、失败条件；未实施就写未实施。', 43, y, size=11)
            for _ in range(2): c.line(43, y - 8, 495, y - 8); y -= 24
            assert y > 55, (t['lesson'], y)
            c.setFont('STSong-Light', 9); c.setFillColor(HexColor('#8a6b22')); c.drawString(43, 59, '点击进入本章学习、原文与%s：第%d章' % (C['agentName'], t['lesson']))
            c.linkURL(URL + 'agent/learning.html?lesson=%d' % t['lesson'], (40, 49, 500, 75), relative=0); footer(t['lesson'] + 1); c.showPage()
        c.save()
    # ---- wire into existing pages (idempotent; author text untouched)
    nav = ('<nav data-unit="v1" aria-label="阅读学习智能问对" style="display:flex;gap:1rem;flex-wrap:wrap;padding:.7rem 1rem;border:1px solid #a88b43;background:#141611;color:#e7ce91;border-radius:8px;margin:1rem auto;max-width:980px;font:14px/1.8 sans-serif">'
           '<a style="color:inherit" href="%sread.html">阅读 · 在线翻页</a><a style="color:inherit" href="%sagent/learning.html">学习包 · %s章实践</a>'
           '<a style="color:inherit" href="%sagent/dialogue.html">智能问对 · %s</a></nav>') % (U, U, NUMW, U, C['agentName'])
    p = BOOK / 'text/index.html'; t = p.read_text(encoding='utf-8'); t = re.sub(r'<nav data-unit="v1".*?</nav>', '', t, flags=re.S)
    t = sub1(t, '<div class="wrap">', '<div class="wrap">' + nav); p.write_text(t, encoding='utf-8')
    p = BOOK / 'read.html'; t = p.read_text(encoding='utf-8')
    if 'id="unit-reader-link"' not in t:
        t = sub1(t, '</body>', '<a id="unit-reader-link" href="%sagent/learning.html" style="position:fixed;right:14px;bottom:68px;z-index:30;background:#d6b663;color:#141611;padding:8px 13px;border-radius:8px;text-decoration:none;font:14px/1.7 sans-serif">学习包 · 带问读</a></body>' % U)
    p.write_text(t, encoding='utf-8')
    p = BOOK / 'index.html'; t = p.read_text(encoding='utf-8')
    S0, E0 = '<!-- UNIT_START -->', '<!-- UNIT_END -->'
    t = re.sub(re.escape(S0) + '.*?' + re.escape(E0), '', t, flags=re.S)
    blk = (S0 + '<section aria-label="三位一体出版单元" style="margin:1.3rem 0"><p style="color:#d6b663;margin-bottom:.5rem">阅读、学习、智能问对三位一体出版单元</p><div style="display:grid;gap:.6rem">'
           '<a class="btn solid" href="%sread.html">阅读 · 在线翻页</a><a class="btn" href="%sagent/learning.html">学习包 · %s章%s实践</a>'
           '<a class="btn" href="%sagent/dialogue.html">智能问对 · %s</a></div><p style="color:#9aa;font-size:.85rem;margin-top:.5rem">配套学习设计，不是著者原文或能力认证；学习记录只留在你的浏览器。<a href="%sunit/SKILL.md">问对规范</a> · <a href="%spublication-unit.json">单元版本与边界</a> · <a href="%s">下载学习包 PDF</a></p></section>' + E0) % (
        U, U, NUMW, C['practiceWord'], U, C['agentName'], U, U, C['learningPdfUrl'])
    t = sub1(t, '<div class="btns">', blk + '<div class="btns">'); p.write_text(t, encoding='utf-8')
    print(json.dumps({'tasks': nch, 'parts': len(parts), 'sources': nch, 'pdf': a.out_pdf}, ensure_ascii=False))

if __name__ == '__main__':
    main()
