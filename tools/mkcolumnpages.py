#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mkcolumnpages.py —— 把首页里只有锚点、没有独立网页的专栏区块，各做成一个独立网页。

背景：首页顶栏子导航 22 条里，有 10 条指向的是 #锚点 而不是页面。锚点跳转在固定顶栏
（两三行、约 130–180px 高）下只留了 scroll-margin-top:70px，标题会被顶栏盖住，
看起来就像"链接有错误"。做成独立网页后，这些栏目才真正各有一个地址。

做法：从 index.html 抽出 <head>（换标题/描述）、固定顶栏、页脚，把目标 <section>
原样搬进 <main>，写到 public/<slug>/index.html。区块内的 #锚点链接一律改写为新页地址。
"""
import re, os, sys, json

ROOT = '/home/claude/site'
SRC = os.path.join(ROOT, 'public/index.html')

# section id → (路径, 中文标题, 英文标题, meta description)
PAGES = {
    'brain-gym': ('brain-gym', '健脑三件日课',
                  'Brain Gym · Three Daily Exercises',
                  '健脑三件日课：不烧 Key、无需注册、记录只留在本机的三个每日思维练习。'),
    'taste': ('taste', 'SDE 智能体品尝系列',
              'SDE Agents · Taste Series',
              'SDE 智能体品尝系列：可直接试用的全部智能体入口，写作、共读、语音解析、金点子发生器等。'),
    'grid': ('nine-doorways', '一套本体论的九个入口',
             'One Ontology, Nine Doorways',
             '一套本体论的九个入口：从九个不同的问题进入同一套发生学地基。'),
    'drwang': ('drwang', '一个具体的问题，长成一套新地基',
               'One Concrete Question, Grown into a New Foundation',
               '一个具体的问题如何长成一套新地基——王德生与 SDE 发生学的来路。'),
    'master': ('master', '解构大师',
               'Deconstruction Master',
               '用发生学的眼，解构思想史上的巨人：先把对手扶到最强，再指出他在哪一步把动词冻成了名词。'),
    'matrix': ('agents', '99 个 SDE 智能体',
               '99 SDE Agents',
               '99 个 SDE 智能体：按领域编排的智能体矩阵。'),
    'monograph': ('monographs', '专著栏目',
                  'Monographs',
                  '德麦国际出版的跨域专著：新书发布、摘要导读与全部已出版书目。'),
}

# 今日文章：导语 + 两个子栏合成一页
TODAY = ('today', '今日文章', "Today's Articles",
         '今日文章：今日长文与每日更新两个子栏目，每天在这里更新的一切。',
         ['today-articles', 'today-longread', 'daily'])

# 锚点 → 新地址（区块内与全站导航都按这张表改写）
ANCHOR_MAP = {
    '#brain-gym': '/brain-gym/',
    '#taste': '/taste/',
    '#grid': '/nine-doorways/',
    '#drwang': '/drwang/',
    '#master': '/master/',
    '#matrix': '/agents/',
    '#monograph': '/monographs/',
    '#today-articles': '/today/',
    '#today-longread': '/today/#today-longread',
    '#daily': '/today/#daily',
}


def load():
    return open(SRC, encoding='utf-8').read()


def cut_section(t, sid):
    """取出 <section id="sid" ...> … </section>（按 section 标签配对扫描）"""
    m = re.search(r'<section[^>]*\bid="%s"' % re.escape(sid), t)
    if not m:
        raise SystemExit('找不到 section #%s' % sid)
    i = m.start()
    depth = 0
    for mm in re.finditer(r'<section\b|</section>', t[i:]):
        depth += 1 if mm.group(0).startswith('<section') else -1
        if depth == 0:
            return t[i:i + mm.end()]
    raise SystemExit('#%s 的 </section> 没配上' % sid)


def head_of(t):
    return t[t.index('<head'):t.index('</head>') + 7]


def nav_of(t):
    """固定顶栏：从 <nav 或 class="nav-bar" 起，到其闭合"""
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
    j = t.index('</footer>', i) + 9
    return t[i:j]


def scripts_of(t):
    """页尾的 <script src=...>（不含内联大段逻辑，避免搬进未定义的 DOM）"""
    tail = t[t.rindex('</footer>'):] if '</footer>' in t else t[-6000:]
    return '\n'.join(m.group(0) for m in re.finditer(r'<script[^>]*\bsrc="[^"]*"[^>]*></script>', tail))


def rewrite_anchors(html, self_path):
    for a, p in ANCHOR_MAP.items():
        if p.rstrip('/') == self_path.rstrip('/'):
            continue  # 指向本页的锚点保留
        html = html.replace('href="%s"' % a, 'href="%s"' % p)
    return html


def make_head(head, zh, en, desc, path):
    h = head
    h = re.sub(r'<title>.*?</title>', '<title>%s · SDE Universes</title>' % zh, h, flags=re.S)
    h = re.sub(r'<meta name="description" content="[^"]*"',
               '<meta name="description" content="%s"' % desc, h)
    h = re.sub(r'<meta property="og:title" content="[^"]*"',
               '<meta property="og:title" content="%s · SDE Universes"' % zh, h)
    h = re.sub(r'<meta property="og:description" content="[^"]*"',
               '<meta property="og:description" content="%s"' % desc, h)
    if 'rel="canonical"' in h:
        h = re.sub(r'<link rel="canonical" href="[^"]*"',
                   '<link rel="canonical" href="https://sdeuniverses.com/%s/"' % path, h)
    else:
        h = h.replace('</head>',
                      '<link rel="canonical" href="https://sdeuniverses.com/%s/">\n</head>' % path, 1)
    # 锚点被顶栏盖住的老毛病：独立页统一给足偏移
    h = h.replace('</head>', '<style>[id]{scroll-margin-top:190px}'
                             '@media(max-width:900px){[id]{scroll-margin-top:210px}}'
                             '.colret{max-width:1100px;margin:0 auto;padding:22px 24px 0;font-size:13.5px;'
                             'letter-spacing:0.08em}.colret a{color:#8A6A1E;text-decoration:none}'
                             '.colret a:hover{text-decoration:underline}</style></head>')
    return h


def build(t, path, zh, en, desc, sids):
    head = make_head(head_of(t), zh, en, desc, path)
    nav = nav_of(t)
    foot = footer_of(t)
    scr = scripts_of(t)
    body = '\n'.join(cut_section(t, s) for s in sids)
    ret = ('<div class="colret"><a href="/">← 返回首页</a>　·　'
           '<span class="zh-only">%s</span><span class="en-only">%s</span></div>' % (zh, en))
    page = ('<!doctype html><html lang="zh-CN">\n' + head + '\n<body class="zh">\n'
            + nav + '\n' + ret + '\n<main>\n' + body + '\n</main>\n' + foot + '\n' + scr
            + '\n</body></html>\n')
    page = rewrite_anchors(page, path)
    d = os.path.join(ROOT, 'public', path)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(page)
    return path, len(page), len(re.findall(r'[\u4e00-\u9fff]', re.sub(r'<[^>]+>', '', page)))


def main():
    t = load()
    out = []
    for sid, (path, zh, en, desc) in PAGES.items():
        out.append(build(t, path, zh, en, desc, [sid]))
    p, zh, en, desc, sids = TODAY
    out.append(build(t, p, zh, en, desc, sids))
    print(f'{"页面":<16}{"字节":>9}{"汉字":>9}')
    for path, b, c in out:
        print(f'/{path+"/":<15}{b:>9,}{c:>9,}')


main()
