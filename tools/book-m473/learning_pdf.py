#!/usr/bin/env python3
"""第 473 号《愧》学习包 PDF（排版美化版，WeasyPrint）。
读 public/books/m/473/unit/learning.json 与 tools/book-m473/book.md，出：
  封面 · 使用说明 · 目录 · 三编编首 · 81 节学习页（一节一页）· 封底说明。
170 mm × 240 mm，思源宋体（Noto Serif CJK SC）正文，思源黑体标签，藏青与金。
用法（仓库根目录）：python3 tools/book-m473/learning_pdf.py --out public/books/m/473/downloads/kui-learning-v1.0.pdf
"""
import argparse, html, json, re, sys
from pathlib import Path

ROOT = Path.cwd()
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa: E402

BOOK = ROOT / ('public/books/m/%d' % M.NO)
URL = 'https://sdeuniverses.com/books/m/%d/' % M.NO
CN = '零一二三四五六七八九'


def esc(s):
    s = html.escape(s, quote=False)
    # 拉丁字母／数字与紧邻汉字不拆行（如「D 欠」「第 3 章」）
    s = re.sub(r'([A-Za-z0-9]+) ([一-鿿])', r'<span class="nb">\1 \2</span>', s)
    s = re.sub(r'([一-鿿]) ([A-Za-z0-9]+)(?![^<]*</span>)', r'<span class="nb">\1 \2</span>', s)
    return s
    # 拉丁字母、数字与汉字之间的半角空格，排版里换成细空格，避免行首行尾空白


def parse_book():
    bk = (HERE / 'book.md').read_text()
    parts, chs, cur = [], [], None
    for line in bk.splitlines():
        m = re.match(r'^# (第[一二三]编)　(.+)$', line)
        if m:
            cur = {'label': m[1], 'title': m[2], 'chs': []}; parts.append(cur); continue
        m = re.match(r'^## 第(\d+)章　(.+)$', line)
        if m and cur is not None:
            ch = {'n': int(m[1]), 'title': m[2], 'secs': [], 'part': len(parts)}; cur['chs'].append(ch); chs.append(ch); continue
        m = re.match(r'^### ◆ (.+)$', line)
        if m and chs and len(chs[-1]['secs']) < 9:
            chs[-1]['secs'].append(m[1].strip())
        if re.match(r'^## 本编总账', line):
            pass
    assert len(chs) == 9 and all(len(c['secs']) == 9 for c in chs)
    return parts, chs


def split_question(q):
    m = re.match(r'^(先说一件事：.+?[？。])再带着问读：(.+)$', q)
    assert m, q[:40]
    items = [x for x in re.split(r'(?=第[一二三四]，)', m[2]) if x]
    return m[1].replace('先说一件事：', ''), [re.sub(r'^第[一二三四]，', '', x) for x in items]


LABELS = [('核对本节的判断：', '核对'), ('邻居一节。', '邻居'), ('本书分叉：', '分叉'), ('边界：', '边界'),
          ('失败条件：', '失败条件'), ('该局面是设想，尚未实施。', '注'), ('小行动：', '小行动')]


def split_check(c):
    # 按标签切段；未识别的「本书……：」也归入分叉
    c = re.sub(r'本书(往前一步|多问一步|在此分叉|添一问|往前推一步)：', '本书分叉：', c)
    pat = '(' + '|'.join(re.escape(a) for a, _ in LABELS) + ')'
    segs, lab = [], None
    for piece in re.split(pat, c):
        if not piece:
            continue
        hit = [b for a, b in LABELS if a == piece]
        if hit:
            lab = hit[0]
            if lab == '注':
                segs.append(['注', '本节的局面是设想，尚未实施。'])
                lab = None
            elif lab == '邻居':
                segs.append(['邻居', ''])
            else:
                segs.append([lab, ''])
            continue
        if not segs:
            segs.append(['核对', ''])
        segs[-1][1] += piece
    out = []
    for lab, t in segs:
        t = t.strip()
        if lab == '注':
            out.append((lab, t)); continue
        if not t:
            continue
        out.append((lab, t))
    return out


CSS = r'''
@page { size: 170mm 240mm; margin: 17mm 17mm 19mm 19mm;
  @bottom-left { content: string(runfoot); font: 7.2pt 'Noto Sans CJK SC'; color: #8a8f93; vertical-align: top; padding-top: 3mm; }
  @bottom-right { content: counter(page); font: 8pt 'Noto Serif CJK SC'; color: #8a6b22; vertical-align: top; padding-top: 3mm; }
  @top-left { content: string(runhead); font: 7.2pt 'Noto Sans CJK SC'; color: #a48c55; letter-spacing: .06em; vertical-align: bottom; padding-bottom: 3mm; }
}
@page cover { margin: 0; background: #16253d; @bottom-left { content: none } @bottom-right { content: none } @top-left { content: none } }
@page dark { margin: 0; background: #16253d; @bottom-left { content: none } @bottom-right { content: none } @top-left { content: none } }
@page plain { @top-left { content: none } }
html { font-family: 'Noto Serif CJK SC', serif; color: #263039; font-size: 9.6pt; line-height: 1.78; text-align: justify; }
body { margin: 0; }
.runfoot { string-set: runfoot content(); height: 0; overflow: hidden; font-size: 0; line-height: 0; }
.cover { page: cover; height: 240mm; position: relative; color: #f1e7cf; page-break-after: always; overflow: hidden; }
.cover .band { position: absolute; left: 19mm; top: 22mm; right: 19mm; }
.cover .kicker { font: 500 8pt 'Noto Sans CJK SC'; letter-spacing: .32em; color: #c9a85c; }
.cover h1 { font: 700 64pt/1 'Noto Serif CJK SC'; margin: 9mm 0 0; color: #ead5a6; letter-spacing: .05em; }
.cover .sub { font: 400 12.5pt/1.6 'Noto Serif CJK SC'; color: #e8dcc0; margin-top: 4mm; }
.cover .pack { margin-top: 9mm; font: 500 15pt 'Noto Serif CJK SC'; color: #f4eddc; letter-spacing: .12em; }
.cover .pack small { display: block; font: 400 8.6pt/1.8 'Noto Sans CJK SC'; color: #b8ad95; letter-spacing: .08em; margin-top: 2mm; }
.cover img { position: absolute; right: 19mm; bottom: 46mm; width: 52mm; box-shadow: 0 3mm 7mm rgba(0,0,0,.45); }
.cover .rule { position: absolute; left: 19mm; width: 22mm; top: 112mm; border-top: .6pt solid #c9a85c; }
.cover .meta { position: absolute; left: 19mm; bottom: 46mm; font: 400 9pt/2.1 'Noto Sans CJK SC'; color: #d9ccb0; }
.cover .meta b { color: #ead5a6; font-weight: 500; }
.cover .foot { position: absolute; left: 19mm; right: 19mm; bottom: 16mm; border-top: .5pt solid #3c4d68; padding-top: 4mm; font: 400 7.6pt/1.8 'Noto Sans CJK SC'; color: #9fa7b2; }
h2.pt { font: 600 17pt/1.3 'Noto Serif CJK SC'; color: #16253d; margin: 0 0 2mm; letter-spacing: .04em; }
.eyebrow { font: 500 7.4pt 'Noto Sans CJK SC'; letter-spacing: .28em; color: #a48c55; }
.goldrule { width: 16mm; border-top: .8pt solid #c9a85c; margin: 4mm 0 6mm; }
.howto { page: plain; page-break-after: always; }
.howto p { margin: 0 0 3.2mm; text-indent: 2em; }
.steps { margin: 5mm 0 6mm; padding: 0; list-style: none; counter-reset: st; }
.steps li { counter-increment: st; position: relative; padding: 2.1mm 0 2.1mm 11mm; border-bottom: .4pt solid #e3dccb; line-height: 1.6; }
.steps li::before { content: counter(st); position: absolute; left: 0; top: 2mm; width: 6.4mm; height: 6.4mm; border-radius: 50%; background: #16253d; color: #ead5a6; font: 500 7.6pt/6.4mm 'Noto Sans CJK SC'; text-align: center; }
.steps b { font-family: 'Noto Sans CJK SC'; font-weight: 500; color: #16253d; margin-right: 2mm; }
.entr { display: flex; gap: 3mm; margin-top: 5mm; }
.entr div { flex: 1; border: .5pt solid #d8cba6; background: #faf6ec; padding: 3mm 3.4mm; font-size: 8.2pt; line-height: 1.6; text-align: left; }
.entr b { display: block; font: 500 8.6pt 'Noto Sans CJK SC'; color: #8a6b22; margin-bottom: 1mm; }
.entr a { color: #2b4a73; text-decoration: none; word-break: break-all; font-size: 7.2pt; }
.note { margin-top: 6mm; font-size: 8pt; color: #6c7378; line-height: 1.7; border-left: 1.4pt solid #c9a85c; padding-left: 3.5mm; text-indent: 0 !important; }
.toc { page: plain; }
.toc h2.pt { margin-bottom: 1mm; }
.toc .part { font: 600 10pt 'Noto Serif CJK SC'; color: #8a6b22; margin: 4.6mm 0 1.4mm; padding-bottom: 1mm; border-bottom: .5pt solid #d8cba6; break-after: avoid; }
.toc .ch { font: 600 8.8pt 'Noto Serif CJK SC'; color: #16253d; margin: 2.4mm 0 .6mm; break-after: avoid; }
.toc .row { display: flex; font-size: 8pt; line-height: 1.62; color: #3b444b; }
.toc .row .no { width: 7mm; font: 500 7.4pt 'Noto Sans CJK SC'; color: #a48c55; padding-top: .3mm; }
.toc .row a { flex: 1; color: inherit; text-decoration: none; display: flex; }
.toc .row a .t { flex: 1; }
.toc .row a::after { content: target-counter(attr(href), page); font: 400 7.6pt 'Noto Serif CJK SC'; color: #8a6b22; padding-left: 2mm; }
.toc .cols { columns: 1; }
.opener { page: dark; height: 240mm; position: relative; color: #efe4c9; page-break-before: always; page-break-after: always; }
.opener .in { position: absolute; left: 22mm; right: 22mm; top: 44mm; }
.opener .lab { font: 500 9pt 'Noto Sans CJK SC'; letter-spacing: .5em; color: #c9a85c; }
.opener h2 { font: 700 26pt/1.35 'Noto Serif CJK SC'; color: #ead5a6; margin: 7mm 0 0; }
.opener h2 small { display: block; font: 400 12pt/1.7 'Noto Serif CJK SC'; color: #d9ccb0; margin-top: 3mm; }
.opener .r { width: 18mm; border-top: .7pt solid #c9a85c; margin: 11mm 0 9mm; }
.opener .chs div { margin-bottom: 6mm; }
.opener .chs b { display: block; font: 600 10.5pt 'Noto Serif CJK SC'; color: #f4eddc; margin-bottom: 1.2mm; }
.opener .chs span { font: 400 7.8pt/1.75 'Noto Sans CJK SC'; color: #9fa7b2; }
.unit { page-break-before: always; position: relative; }
.unit .rh { string-set: runhead content(); display: block; height: 0; overflow: hidden; font-size: 0; line-height: 0; }
.unit .head { display: flex; align-items: flex-end; gap: 4.5mm; margin-top: 1mm; }
.unit .num { font: 300 34pt/0.9 'Noto Serif CJK SC'; color: #c9a85c; letter-spacing: -.02em; }
.unit .src { font: 400 7.6pt/1.5 'Noto Sans CJK SC'; color: #8a8f93; padding-bottom: 1mm; }
.unit .src b { color: #8a6b22; font-weight: 500; }
.unit h3 { font: 600 14.2pt/1.45 'Noto Serif CJK SC'; color: #16253d; margin: 3.2mm 0 0; text-align: left; letter-spacing: .01em; }
.unit .hr { border-top: .5pt solid #c9a85c; width: 100%; margin: 3.4mm 0 3.6mm; }
.blk { margin-bottom: 3mm; }
.tag { display: inline-block; font: 500 7.2pt/1 'Noto Sans CJK SC'; letter-spacing: .14em; color: #fff; background: #16253d; padding: 1.1mm 2mm 1mm; margin-bottom: 1.6mm; }
.tag.gold { background: #a48c55; }
.ask p { margin: 0 0 1.4mm; }
.ask .story { font-size: 9.6pt; color: #263039; }
.ask ol { margin: 1mm 0 0; padding: 0; list-style: none; }
.ask li { position: relative; padding-left: 8.2mm; margin-bottom: 1mm; font-size: 9.1pt; line-height: 1.68; }
.ask li::before { content: attr(data-n); position: absolute; left: 0; top: .2mm; font: 500 7.4pt 'Noto Sans CJK SC'; color: #a48c55; }
.lines { margin: 1.2mm 0 0; }
.lines div { height: 7mm; border-bottom: .45pt solid #d3cdbf; }
.lines .hint { height: auto; border: 0; font: 400 7.2pt 'Noto Sans CJK SC'; color: #9a9384; margin-bottom: -.6mm; }
.chk { border: .5pt solid #e1d6b8; background: #faf6ec; padding: 2.8mm 3.4mm 1.6mm; margin: 3.4mm 0 3mm; }
.chk .r { display: flex; gap: 3mm; margin-bottom: 1.5mm; font-size: 8.7pt; line-height: 1.66; }
.chk .k { flex: 0 0 13mm; font: 500 7.3pt/1.9 'Noto Sans CJK SC'; color: #8a6b22; letter-spacing: .06em; }
.chk .v { flex: 1; }
.chk .r.act .v { color: #16253d; }
.chk .r.nt .v { color: #8a8f93; font-size: 8pt; }
.tail { display: flex; justify-content: space-between; align-items: center; margin-top: 3mm; font: 400 7pt 'Noto Sans CJK SC'; color: #8a8f93; }
.tail a { color: #8a6b22; text-decoration: none; }
.back { page: dark; height: 240mm; position: relative; color: #d9ccb0; page-break-before: always; }
.back .in { position: absolute; left: 22mm; right: 22mm; top: 52mm; font: 400 9.4pt/2 'Noto Serif CJK SC'; }
.back .in p { margin: 0 0 4mm; text-indent: 2em; }
.back .q { font: 500 13pt/1.8 'Noto Serif CJK SC'; color: #ead5a6; text-indent: 0 !important; margin-bottom: 9mm !important; }
.back .ft { position: absolute; left: 22mm; right: 22mm; bottom: 18mm; border-top: .5pt solid #3c4d68; padding-top: 4mm; font: 400 7.6pt/1.9 'Noto Sans CJK SC'; color: #9fa7b2; }
.ts { display: inline-block; width: .18em; }
.nb { white-space: nowrap; }
.opener .chs i { font-style: normal; color: #c9a85c; padding: 0 .5em; }
'''


def lines(n, hint=''):
    h = '<div class="hint">%s</div>' % esc(hint) if hint else ''
    return '<div class="lines">%s%s</div>' % (h, '<div></div>' * n)


LINES = {}
SHRINK = [(4, 4, 3), (4, 3, 3), (3, 3, 2), (3, 2, 2), (2, 2, 2)]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); ap.add_argument('--html', default=None)
    a = ap.parse_args()
    man = json.loads((BOOK / 'unit/learning.json').read_text())
    tasks = man['tasks']
    parts, chs = parse_book()
    assert len(tasks) == 81
    for attempt in range(6):
        H = ['<!doctype html><html lang="zh-Hans"><head><meta charset="utf-8"><title>%s · 学习包</title><style>%s</style></head><body>' % (M.TITLE, CSS)]
        # 封面
        H.append('''<section class="cover"><div class="band"><div class="kicker">德麦国际专著第 %d 号 · 配套学习包</div>
    <h1 style="font-size:34pt;line-height:1.3">还清了钱，<br>没还清位置</h1><div class="sub">愧，一次只走了两步的发生 · 文学版</div>
    <div class="pack">学习包<small>三编 · 九章 · 八十一节<br>阅读　学习　智能问对</small></div></div>
    <div class="rule"></div>
    <img src="file://%s">
    <div class="meta"><b>秦莉</b>　著<br>ISBN %s<br>%s</div>
    <div class="foot">一节一页：先答，带问读，再答；核对判断、看清失败条件，留一个明天能做的小行动。<br>在线学习　sdeuniverses.com/books/m/%d/agent/learning.html</div></section>''' % (
            M.NO, BOOK / 'cover.jpg', M.ISBN, M.PRICE, M.NO))
        # 使用说明
        H.append('''<section class="howto"><div class="runfoot">《还清了钱，没还清位置》学习包 · 德麦国际专著第 %d 号</div><div class="eyebrow">HOW TO USE</div><h2 class="pt">怎样用这本学习包</h2><div class="goldrule"></div>
    <p>这本学习包把《还清了钱，没还清位置》（《愧》文学版）的三编九章拆成八十一节，一节一页。每一页都从你自己的一件事开始，再带着两三个问题回到书里那一节去读。读完，不急着同意，先核对这一节的判断站不站得住、在什么情况下会错，最后留下一个明天就能做的小行动。</p>
    <p>请用笔写。愧这件事，最怕只在心里过一遍：想得越周全，越容易停在显露里。写下来的那一行，哪怕只有一句，也是一笔可以回看的记录。</p>
    <ol class="steps">
    <li><b>先答</b>读之前，凭自己的经验写下起点；不知道，也如实写「不知道」。</li>
    <li><b>带问读</b>带着页上的问题读这一节原文，留意人物、场景与转折。</li>
    <li><b>复答</b>读后再答一次，不涂改先答，看哪里变了、哪里没变。</li>
    <li><b>核对</b>对照页上的判断、边界与失败条件，问：什么结果出现，就算本书说错了？</li>
    <li><b>讨论</b>可以带着这一页去问智能体「落款」，它的回答只是待核对的建议。</li>
    <li><b>修订</b>由你本人决定改不改、改在哪里；赞同、理解与实际做到，分开记。</li>
    <li><b>行动与回看</b>做那件小行动，过几天回来写下发生了什么；没做，就写没做。</li>
    </ol>
    <div class="entr"><div><b>阅读</b>全文网页，每节有锚点<br><a href="%stext/">sdeuniverses.com/books/m/%d/text/</a></div>
    <div><b>学习</b>在线学习包，记录留在你的浏览器<br><a href="%sagent/learning.html">…/m/%d/agent/learning.html</a></div>
    <div><b>智能问对</b>智能体「落款」<br><a href="%sagent/dialogue.html">…/m/%d/agent/dialogue.html</a></div></div>
    <p class="note">本学习包是配套教学设计，不是著者原文、标准答案或能力认证。页上的「失败条件」多数是设想中的检验，尚未实施；书中人物与场景都是虚构，只承担画面，不承担证据。若自责、失眠、自我否定长期缠着你，请找医生或心理咨询师。</p></section>''' % (
            M.NO, URL, M.NO, URL, M.NO, URL, M.NO))
        # 目录
        H.append('<section class="toc"><div class="eyebrow">CONTENTS</div><h2 class="pt">目录</h2><div class="goldrule"></div>')
        for pi, p in enumerate(parts, 1):
            H.append('<div class="part">%s　%s</div>' % (p['label'], esc(p['title'])))
            for ch in p['chs']:
                H.append('<div class="ch">第 %d 章　%s</div>' % (ch['n'], esc(ch['title'])))
                for j, st in enumerate(ch['secs'], 1):
                    n = (ch['n'] - 1) * 9 + j
                    H.append('<div class="row"><span class="no">%02d</span><a href="#u%d"><span class="t">%s</span></a></div>' % (n, n, esc(st)))
        H.append('</section>')
        # 编首 + 学习页
        for pi, p in enumerate(parts, 1):
            H.append('<section class="opener"><div class="in"><div class="lab">%s</div><h2>%s</h2><div class="r"></div><div class="chs">%s</div></div></section>' % (
                ' '.join(p['label']), esc(p['title'].split('：')[0]) + ('<small>%s</small>' % esc(p['title'].split('：', 1)[1]) if '：' in p['title'] else ''),
                ''.join('<div><b>第 %d 章　%s</b><span>%s</span></div>' % (c['n'], esc(c['title']), '<i>·</i>'.join(esc(re.sub(r'^[一二三四五六七八九]、', '', s)) for s in c['secs'])) for c in p['chs'])))
            for ch in p['chs']:
                for j, st in enumerate(ch['secs'], 1):
                    n = (ch['n'] - 1) * 9 + j
                    t = tasks[n - 1]; assert t['lesson'] == n
                    story, asks = split_question(t['question'])
                    checks = split_check(t['checkpoint'])
                    L = LINES.get(n, (4, 4, 3))
                    rows = []
                    for lab, v in checks:
                        if lab == '注':
                            rows.append('<div class="r nt"><span class="k"></span><span class="v">%s</span></div>' % esc(v)); continue
                        k = {'邻居': '近邻', '分叉': '本书分叉'}.get(lab, lab)
                        if lab == '邻居':
                            v = re.sub(r'^邻居一节。', '', v)
                        rows.append('<div class="r%s"><span class="k">%s</span><span class="v">%s</span></div>' % (' act' if lab == '小行动' else '', k, esc(v)))
                    H.append('''<section class="unit" id="u%d"><span class="rh">%s · 第 %d 章　%s</span><div class="runfoot">《还清了钱，没还清位置》学习包 · 德麦国际专著第 %d 号</div>
    <div class="head"><span class="num">%02d</span><span class="src"><b>第 %d 章 · 第 %s 节</b><br>%s</span></div>
    <h3>%s</h3><div class="hr"></div>
    <div class="blk ask"><span class="tag">先说一件事</span><p class="story">%s</p>%s<span class="tag gold">带着问读</span><ol>%s</ol></div>
    %s
    <div class="chk">%s</div>
    %s%s
    <div class="tail"><span>原文：sdeuniverses.com/books/m/%d/text/#c%ds%d</span><a href="%sagent/learning.html?lesson=%d">在线学习本节 · 问「落款」 →</a></div></section>''' % (
                        n, esc(p['label'] + '　' + p['title'].split('：')[0]), ch['n'], esc(ch['title']), M.NO,
                        n, ch['n'], CN[j], esc(st), esc(t['title']), esc(story), lines(L[0], '先答：我的起点（读之前写）'),
                        ''.join('<li data-n="%s">%s</li>' % ('问' + CN[i], esc(x)) for i, x in enumerate(asks, 1)),
                        '', ''.join(rows),
                        lines(L[1], '复答／异议：读后什么变了，什么仍不同意？原文依据在哪一段？'),
                        lines(L[2], '小行动与回看：哪天做，发生了什么；没做，就写没做。'),
                        M.NO, ch['n'], j, URL, n))
        # 封底
        H.append('''<section class="back"><div class="in"><p class="q">愧，是欠在自己身上显露；<br>欠，是撞了、变了，回写却没有发生——<br>一次只走了两步的发生。</p>
    <p>八十一节读完，愿你手上留下的，不是一堆答对的题，而是几笔写清楚了的回写：改了什么，记在哪里，谁能说落定。</p>
    <p>还不上的那一份，先问缺的是哪一维；能落定的，就让它落定；不该背的，就把它放回原处。</p></div>
    <div class="ft">《还清了钱，没还清位置——愧，一次只走了两步的发生（文学版）》　秦莉　著<br>德麦国际出版社 · 德麦国际专著第 %d 号 · ISBN %s · %s<br>配套学习设计，不是著者原文或能力认证；学习记录只留在你自己的纸上和浏览器里。</div></section>''' % (M.NO, M.ISBN, M.PRICE))
        H.append('</body></html>')
        doc = '\n'.join(H)
        if a.html:
            Path(a.html).write_text(doc)
        from weasyprint import HTML
        r = HTML(string=doc, base_url=str(ROOT)).render()
        # 每节必须恰好一页
        first, span = {}, {}
        for i, pg in enumerate(r.pages):
            for bid in pg.anchors:
                if re.fullmatch(r'u\d+', bid):
                    k = int(bid[1:]); first.setdefault(k, i); span[k] = span.get(k, 0) + 1
        assert len(first) == 81, len(first)
        over = [k for k, v in span.items() if v > 1]
        if not over: break
        for k in over: LINES[k] = SHRINK[min(SHRINK.index(LINES.get(k, SHRINK[0])) + 1, len(SHRINK) - 1)]
        print('attempt', attempt, 'shrink', over)
    assert not over, over
    r.copy(r.pages).write_pdf(a.out)
    meta_pages = len(r.pages)
    print('ok', a.out, meta_pages, 'pages')


if __name__ == '__main__':
    main()
