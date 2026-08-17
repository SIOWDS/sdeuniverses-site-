#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mkhowpage.py —— 重建「怎么做」栏目页 public/how/index.html。

这一栏收的是全站只讲操作、不提新判断的文本。它们本来只能从母文摘要下面那个
小链接进去，没有任何总入口；本脚本把四类扫齐，列成一页：

  ① 解释文  <母文目录>/explain.html      白话重讲母文，不用术语
  ② 实践文  <母文目录>/practice.html     只讲方法、步骤、判据
  ③ 应用文  column/<idea>/apply-{education,health,business}/  或 apply/
            ideas/<idea>/{education,health,business}/
  ④ 每日必读应用篇  paradigm/<slug>/apply.html

①② 成对出现，页面里按「并蒂文」一组两篇列；③④ 按思想聚合，一行给出该思想在
教育／健康／商业三个现场的手册。

用法（在仓库根目录跑）：
    python3 tools/mkhowpage.py            # 重建页面
    python3 tools/mkhowpage.py --dry-run  # 只报数目，不写文件

⚠ 不要 import tools/mkcolumnpages.py —— 那个模块在顶层就执行建页动作，且会把
  /taste/ 覆盖成首页的 5 张预览、重建已删的 /agents/。所以下面那四个壳函数
  （head_of / nav_of / footer_of / scripts_of）是从它那里抄过来的副本。

⚠ 页面的强调色、栏目条里的 .col-how 都是 #1F7A72；改色要两处一起改
  （本文件的 AC 常量 ＋ public/index.html 里的 .col-how）。
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, 'public')
OUT = os.path.join(PUB, 'how', 'index.html')
AC = '#1F7A72'          # 本栏强调色
ZH, EN = '怎么做', 'How To'
DESC = ('怎么做：全站三百多篇只讲操作的文本汇于一处——每篇难文的白话解释文与方法实践文，'
        '以及每条思想在教育、健康、商业三个现场的操作手册。')


# ---------- 页壳（抄自 tools/mkcolumnpages.py，勿 import 那个模块） ----------

def head_of(t):
    return t[t.index('<head'):t.index('</head>') + 7]


def nav_of(t):
    m = re.search(r'<(nav|div|header)[^>]*class="[^"]*nav-bar[^"]*"', t)
    if not m:
        raise SystemExit('找不到顶栏')
    tag = m.group(1)
    i = m.start()
    depth = 0
    for mm in re.finditer(r'<%s\b|</%s>' % (tag, tag), t[i:]):
        depth += 1 if not mm.group(0).startswith('</') else -1
        if depth == 0:
            return t[i:i + mm.end()]
    raise SystemExit('顶栏没配上')


def footer_of(t):
    m = re.search(r'<footer\b', t)
    if not m:
        return ''
    i = m.start()
    return t[i:t.index('</footer>', i) + 9]


def scripts_of(t):
    tail = t[t.rindex('</footer>'):] if '</footer>' in t else t[-6000:]
    return '\n'.join(m.group(0) for m in
                     re.finditer(r'<script[^>]*\bsrc="[^"]*"[^>]*></script>', tail))


# ---------- 扫描 ----------

def title_of(path):
    """取页面标题：优先 <h1>，退回 <title> 的第一段。"""
    h = open(path, encoding='utf-8').read()
    m = re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S)
    t = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', m.group(1))).strip() if m else ''
    if not t:
        m = re.search(r'<title>(.*?)</title>', h, re.S)
        t = m.group(1).split('|')[0].split('·')[0].strip() if m else ''
    return t


def esc(s):
    return s.replace('&', '&amp;').replace('&amp;amp;', '&amp;').replace('<', '&lt;')


def collect():
    os.chdir(PUB)
    names = {s['slug']: s['name']
             for s in json.load(open('students/roster.json', encoding='utf-8'))['students']}
    pairs = []
    for p in sorted(glob.glob('**/explain.html', recursive=True)):
        d = os.path.dirname(p)
        if not os.path.exists(os.path.join(d, 'practice.html')):
            continue          # 只收两篇齐全的
        mp = os.path.join(d, 'index.html')
        t = title_of(mp) if os.path.exists(mp) else title_of(p)
        if d.startswith('students/'):
            au = names.get(d.split('/')[1], d.split('/')[1])
        elif d.startswith('books/'):
            au = '专著'
        else:
            au = '王德生'
        pairs.append({'d': '/' + d + '/', 't': t, 'au': au})

    ideas = {}
    for p in (sorted(glob.glob('column/*/apply-*/index.html'))
              + sorted(glob.glob('column/*/apply/index.html'))):
        leg = p.split('/')[2].replace('apply-', '')
        ideas.setdefault(('column', p.split('/')[1]), {})[leg if leg != 'apply' else 'general'] \
            = '/' + os.path.dirname(p) + '/'
    for p in sorted(glob.glob('ideas/*/*/index.html')):
        ideas.setdefault(('ideas', p.split('/')[1]), {})[p.split('/')[2]] \
            = '/' + os.path.dirname(p) + '/'
    for p in sorted(glob.glob('paradigm/*/apply.html')):
        ideas.setdefault(('paradigm', p.split('/')[1]), {})['general'] = '/' + p

    out = []
    for (src, slug), legs in ideas.items():
        mp = {'column': 'column/%s/index.html',
              'ideas': 'ideas/%s/index.html',
              'paradigm': 'paradigm/%s/index.html'}[src] % slug
        out.append({'src': src, 'slug': slug,
                    't': title_of(mp) if os.path.exists(mp) else slug,
                    'legs': legs, 'm': '/' + os.path.dirname(mp) + '/'})
    return pairs, out


# ---------- 建页 ----------

CSS = '''
<style>
[id]{scroll-margin-top:190px}
@media(max-width:820px){[id]{scroll-margin-top:210px}}
.hw-wrap{max-width:1040px;margin:0 auto;padding:0 24px}
.hw-sec{padding:64px 0 12px}
.hw-num{font-size:12.5px;letter-spacing:.4em;color:%(AC)s;font-weight:700;margin-bottom:12px}
.hw-h{font-size:clamp(21px,3vw,28px);font-weight:700;color:#2A2315;margin:0 0 10px}
.hw-p{max-width:780px;font-size:15.5px;line-height:1.95;color:#4A4029;margin:0 0 26px}
.hw-au{font-size:12.5px;letter-spacing:.3em;color:%(AC)s;font-weight:700;margin:26px 0 10px;padding-bottom:6px;border-bottom:1px solid rgba(138,104,23,.22)}
.hw-row{display:flex;align-items:baseline;gap:12px;padding:9px 0;border-bottom:1px solid rgba(138,104,23,.10);flex-wrap:wrap}
.hw-t{flex:1;min-width:230px;font-size:15px;color:#2A2315;line-height:1.6}
.hw-t a{color:#2A2315;text-decoration:none}
.hw-t a:hover{text-decoration:underline;text-underline-offset:3px}
.hw-lk{display:inline-flex;gap:8px;flex-shrink:0}
.hw-lk a{font-size:12.8px;font-weight:700;text-decoration:none;color:%(AC)s;border:1px solid rgba(31,122,114,.34);border-radius:999px;padding:3px 12px;white-space:nowrap;transition:background .15s}
.hw-lk a:hover{background:rgba(31,122,114,.10)}
.hw-lk a.g2{color:#8A6817;border-color:rgba(138,104,23,.34)}
.hw-lk a.g2:hover{background:rgba(138,104,23,.10)}
.hw-note{font-size:13.5px;color:#8B7C5F;line-height:1.85;margin:14px 0 0}
</style>
'''

BODY = '''<body class="zh">
%(nav)s
<main>
<section id="how" style="background:#F7F1E4;border-bottom:1px solid rgba(138,104,23,0.22);padding:88px 24px 0">
  <div class="hw-wrap">
    <div class="zh-only" style="font-size:12.5px;letter-spacing:0.45em;color:%(AC)s;margin-bottom:16px">专栏 · 怎么做</div>
    <div class="en-only" style="font-size:12.5px;letter-spacing:0.45em;color:%(AC)s;margin-bottom:16px">COLUMN · HOW TO</div>
    <h1 class="zh-only" style="font-size:clamp(26px,4.4vw,40px);font-weight:700;letter-spacing:0.03em;margin:0 0 20px;color:#2A2315">读完之后，明天早上做什么</h1>
    <h1 class="en-only" style="font-size:clamp(26px,4.4vw,40px);font-weight:700;letter-spacing:0.03em;margin:0 0 20px;color:#2A2315">And Tomorrow Morning, What Do You Do</h1>
    <p class="zh-only" style="max-width:780px;font-size:16.5px;line-height:2.0;color:#4A4029;margin:0 0 18px">站上其余每一个栏目都按<b>讲什么题目</b>分；这一栏按<b>拿它干什么</b>分。里面的文章不提出新判断，只做一件事：把已经立住的判断，换成你今天就能照着做的动作。</p>
    <p class="zh-only" style="max-width:780px;font-size:16.5px;line-height:2.0;color:#4A4029;margin:0 0 40px">共 <b>%(n)d 篇、约 %(w)s 万汉字</b>。它们此前散落在各自母文的页脚，从未有过一个总入口——这一栏就是那个入口。</p>
    <p class="en-only" style="max-width:780px;font-size:16.5px;line-height:2.0;color:#4A4029;margin:0 0 40px">Every other column here is organised by subject. This one is organised by use. Nothing in it advances a new claim; it turns claims already made into things you can do today — %(n)d pieces in all, until now reachable only from the foot of their parent essays.</p>
  </div>
</section>
<section style="padding:0 24px 80px">
  <div class="hw-wrap">
%(body)s
  </div>
</section>
</main>
%(foot)s
%(scripts)s
</body>
</html>
'''

AUTHOR_ORDER = ['王德生', '专著', '胡敏', '秦莉', '张琼', '陈晓艳', '高鹏',
                '孔凡鹤', '阳涌', '黄倩盈', 'Judy']
LEGS = [('education', '教育', 'Education'),
        ('health', '健康', 'Health'),
        ('business', '商业', 'Business')]


def build(pairs, ideas):
    src = open(os.path.join(PUB, 'index.html'), encoding='utf-8').read()
    head, nav = head_of(src), nav_of(src)
    foot, scripts = footer_of(src), scripts_of(src)
    head = re.sub(r'<title>.*?</title>', '<title>%s · SDE Universes</title>' % ZH, head, flags=re.S)
    head = re.sub(r'<meta name="description" content="[^"]*"',
                  '<meta name="description" content="%s"' % DESC, head)
    head = re.sub(r'<meta property="og:title" content="[^"]*"',
                  '<meta property="og:title" content="%s · SDE Universes"' % ZH, head)
    head = re.sub(r'<meta property="og:description" content="[^"]*"',
                  '<meta property="og:description" content="%s"' % DESC, head)
    if 'canonical' in head:
        head = re.sub(r'<link rel="canonical" href="[^"]*"',
                      '<link rel="canonical" href="https://sdeuniverses.com/how/"', head)
    else:
        head = head.replace('</head>',
                            '<link rel="canonical" href="https://sdeuniverses.com/how/">\n</head>')
    head = head.replace('</head>', CSS % {'AC': AC} + '</head>')

    by = {}
    for p in pairs:
        by.setdefault(p['au'], []).append(p)
    b = []
    b.append('<div class="hw-sec" id="pair">')
    b.append('  <div class="hw-num"><span class="zh-only">壹 · 并蒂文 · %d 组 · 每组两篇</span>'
             '<span class="en-only">I · PAIRED READINGS · %d SETS</span></div>' % (len(pairs), len(pairs)))
    b.append('  <h2 class="hw-h zh-only">难的那一篇，另配两篇好读的</h2>'
             '<h2 class="hw-h en-only">For Every Hard Essay, Two Easier Ones</h2>')
    b.append('  <p class="hw-p zh-only">每一篇理论长文下面挂着两篇：<b>白话解释文</b>把它重讲一遍，不用一个术语；'
             '<b>方法实践文</b>只讲怎么用——步骤、判据、可以照着做的动作。两篇各约五千字。'
             '以前它们只在母文摘要下面露一个小链接，这里是第一次全部列出来。</p>')
    b.append('  <p class="hw-p en-only">Under each theory essay sit two companions: a plain-language '
             'retelling with no jargon, and a method piece that gives only the steps and the criteria. '
             'About 5,000 characters each. Until now they appeared only as a small link beneath the '
             'parent abstract.</p>')
    for au in AUTHOR_ORDER + [a for a in by if a not in AUTHOR_ORDER]:
        if au not in by:
            continue
        b.append('  <div class="hw-au">%s · %d 组</div>' % (esc(au), len(by[au])))
        for it in by[au]:
            b.append('  <div class="hw-row"><div class="hw-t"><a href="%s">%s</a></div>'
                     '<div class="hw-lk"><a href="%sexplain.html">白话解释</a>'
                     '<a class="g2" href="%spractice.html">方法实践</a></div></div>'
                     % (it['d'], esc(it['t']), it['d'], it['d']))
    b.append('</div>')

    three = [o for o in ideas if len(o['legs']) == 3]
    one = [o for o in ideas if len(o['legs']) != 3]
    nman = sum(len(o['legs']) for o in ideas)
    b.append('<div class="hw-sec" id="apply">')
    b.append('  <div class="hw-num"><span class="zh-only">贰 · 落到现场 · %d 条思想 · %d 篇手册</span>'
             '<span class="en-only">II · ON THE GROUND · %d IDEAS</span></div>'
             % (len(ideas), nman, len(ideas)))
    b.append('  <h2 class="hw-h zh-only">同一条判断，在三个现场分别怎么做</h2>'
             '<h2 class="hw-h en-only">One Judgement, Three Places to Apply It</h2>')
    b.append('  <p class="hw-p zh-only">一条思想立住之后，接着要问的是：在课堂上怎么做，在身体上怎么做，'
             '在组织里怎么做。同一条判断分头写成三份操作手册——不是同一篇话换三个说法，'
             '三个现场的阻力本来就不同。点标题读母文，点右边直接进手册。</p>')
    b.append('  <p class="hw-p en-only">Once an idea stands, the next question is what to do with it — '
             'in a classroom, in a body, in an organisation. Each idea is written out as three separate '
             'manuals, because the resistance differs in each place.</p>')
    for grp, zt, et in [(three, '三个现场齐全', 'All three'), (one, '单篇手册', 'Single manual')]:
        if not grp:
            continue
        b.append('  <div class="hw-au"><span class="zh-only">%s · %d 条</span>'
                 '<span class="en-only">%s · %d</span></div>' % (zt, len(grp), et, len(grp)))
        for o in sorted(grp, key=lambda x: x['t']):
            lk = ['<a href="%s"><span class="zh-only">%s</span><span class="en-only">%s</span></a>'
                  % (o['legs'][k], zh, en) for k, zh, en in LEGS if k in o['legs']]
            if 'general' in o['legs']:
                lk.append('<a class="g2" href="%s"><span class="zh-only">应用</span>'
                          '<span class="en-only">Apply</span></a>' % o['legs']['general'])
            b.append('  <div class="hw-row"><div class="hw-t"><a href="%s">%s</a></div>'
                     '<div class="hw-lk">%s</div></div>' % (o['m'], esc(o['t']), ''.join(lk)))
    b.append('  <p class="hw-note zh-only">母文在各自的栏目里（每日必读 · 思想·应用 · 今日长文），'
             '这里只收它们的操作手册。</p>')
    b.append('  <p class="hw-note en-only">The parent essays live in their own columns; only the '
             'manuals are collected here.</p>')
    b.append('</div>')

    n = len(pairs) * 2 + nman
    return ('<!doctype html><html lang="zh-CN">\n' + head + '\n'
            + BODY % {'nav': nav, 'foot': foot, 'scripts': scripts,
                      'body': '\n'.join(b), 'AC': AC, 'n': n, 'w': '171'})


def main():
    pairs, ideas = collect()
    nman = sum(len(o['legs']) for o in ideas)
    print('并蒂文 %d 组（%d 篇）· 思想 %d 条（%d 篇手册）· 合计 %d 篇'
          % (len(pairs), len(pairs) * 2, len(ideas), nman, len(pairs) * 2 + nman))
    if '--dry-run' in sys.argv:
        return
    page = build(pairs, ideas)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, 'w', encoding='utf-8').write(page)
    print('写入 %s（%d 字节）' % (OUT, len(page)))


if __name__ == '__main__':
    main()
