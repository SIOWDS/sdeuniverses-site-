#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""decouple_column_nav.py —— 把栏目页的顶栏从「首页那一整套」解耦成「本栏自己的」。

基本原则（2026-08-22 王德生定）：**专栏页面不应出现首页的内容和链接，
每个专栏是一个单独的网页，干净、清洁、具有独立性。**

做四件事，只动 <nav>，不碰正文：
  ① 删掉 .agent-strip（智能体芯片带）、.nav-cols（每日必读/学科通融/新思想前沿/学徒招募）
     以及装**全站栏目条**的 .nav-bar-sub.nbs-grid（十四项那条）。
  ② .nav-bar-main 的 .nav-links 里，只留**指向本栏内部**的链接（本栏根下的路径、页内锚点）
     ＋ 中英切换；指向别的栏目的一律删。
  ③ .nav-logo 由「SDE Universes」改为**本栏名**，指向本栏首页。
  ④ 末尾补一条不抢戏的回站链接「爱思乐园 ↗」→ /browse/，免得页面成孤岛。
本栏自己的频道条（.nav-bar-sub 里装的本栏频道，如 /education/ 的十几个锚点）**原样保留**。

⚠ 三个站级页面不在处理范围：public/browse（真首页）、public/directory（栏目总目录）、
  public/overview（总览长卷）——它们本来就该带全站导航。
⚠ /three-views/ 那 22 页已经是自持壳（tools/mkthreeviews.py 生成），不走这里。

用法：python3 tools/decouple_column_nav.py [--dry-run]
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, 'public')

SKIP_TOP = {'browse', 'directory', 'overview', 'three-views'}

# 栏根 -> (中文名, 英文名)。键是本栏的根路径。
COLUMNS = {
    '/drwang/': ('王博士与SDE', 'Dr. Wang & SDE'),
    '/nine-doorways/': ('三维九宫', 'Nine Doorways'),
    '/taste/': ('SDE 智能体', 'SDE Agents'),
    '/thought/': ('哲学与思想', 'Thought'),
    '/master/': ('解构大师', 'Deconstructing the Masters'),
    '/culture/': ('文化与艺术', 'Culture & Art'),
    '/brain-gym/': ('健脑三件', 'Brain Gym'),
    '/how/': ('怎么做', 'How To'),
    '/today/': ('今日文章', 'Today'),
    '/life/': ('人生与家庭', 'Life & Family'),
    '/monographs/': ('专著栏目', 'Monographs'),
    '/ai/': ('AI 专栏', 'AI'),
    '/education/': ('教育专栏', 'Education'),
    '/health/': ('健康专栏', 'Health'),
    '/business/': ('商业与经济', 'Business'),
    '/creation/': ('学术创造', 'Academic Creation'),
    '/discovery-vs-genesis/': ('发现VS发生', 'Discovery vs Genesis'),
    '/culture-tech/': ('中华文化与科技创新', 'Culture & Technology'),
    '/hotspot/': ('热点', 'Hotspot'),
    '/plagiarism/': ('论文抄袭专栏', 'Plagiarism'),
    '/headline/': ('头条', 'Headline'),
    '/western-philosophy/': ('西方哲学', 'Western Philosophy'),
}

LANG = ('    <div class="lang-toggle">\n'
        '      <button class="lang-btn active" onclick="setLang(\'zh\')">中</button>\n'
        '      <button class="lang-btn" onclick="setLang(\'en\')">EN</button>\n'
        '    </div>\n')

CSS = ("\n/* 2026-08-22 栏目页与首页解耦：本栏名做站标，回站那一条不抢戏 */\n"
       ".nav-logo .nlg-en{display:block;font-family:'Playfair Display',Georgia,serif;"
       "font-size:.66rem;letter-spacing:.18em;opacity:.72;text-transform:uppercase}\n"
       ".nav-links a.nav-back{margin-left:auto;opacity:.62;font-size:.9rem}\n"
       ".nav-links a.nav-back:hover{opacity:1}\n")


def column_root(rel):
    """页面属于哪个栏：拿路径逐段回退，找 COLUMNS 里最长的匹配。"""
    parts = rel.split('/')[:-1]          # 去掉 index.html
    while parts:
        cand = '/' + '/'.join(parts) + '/'
        if cand in COLUMNS:
            return cand
        parts.pop()
    return None


def _close_div(h, i):
    """h[i] 处是一个 <div ...>，返回它闭合之后的下标。"""
    depth = 0
    for mm in re.finditer(r'<div\b|</div>', h[i:]):
        depth += 1 if not mm.group(0).startswith('</') else -1
        if depth == 0:
            return i + mm.end()
    raise SystemExit('div 没配上')


def find_navzone(h, rel):
    """顶栏区在站上有两种写法，都要认：
       ① <nav> … </nav> 包着（browse 那一系）
       ② 裸的 <div class="nav-bar-main"> 直接在 body 里，后面再跟 .agent-strip /
          .nav-bar-sub / .nav-cols 几个平级 div（tools/mkcolumnpages.py 抄出来的那一系）。
       第二种没有 <nav>，只找 <nav> 会整批漏掉——正是首页链最多的那十二页。
    """
    m = re.search(r'<nav\b[^>]*>', h)
    if m:
        i = m.start()
        depth = 0
        for mm in re.finditer(r'<nav\b|</nav>', h[i:]):
            depth += 1 if not mm.group(0).startswith('</') else -1
            if depth == 0:
                return i, i + mm.end()
        raise SystemExit('nav 没配上：' + rel)
    m = re.search(r'<div[^>]*class="[^"]*\bnav-bar-main\b[^"]*"[^>]*>', h)
    if not m:
        return None
    i = m.start()
    j = _close_div(h, i)
    # 吞掉紧随其后的平级顶栏块（中间只允许空白与注释）
    while True:
        mm = re.match(r'(?:\s|<!--.*?-->)*<div[^>]*class="[^"]*\b'
                      r'(?:agent-strip|nav-bar-sub|nav-cols)\b[^"]*"[^>]*>',
                      h[j:], re.S)
        if not mm:
            return i, j
        j = _close_div(h, j + mm.group(0).rindex('<div'))


def strip_block(nav, cls):
    """删掉 nav 里 class 含 cls 的那个 div（含其全部子内容）。返回 (新nav, 删了几个)。"""
    n = 0
    while True:
        m = re.search(r'<div[^>]*class="[^"]*\b%s\b[^"]*"[^>]*>' % re.escape(cls), nav)
        if not m:
            return nav, n
        i = m.start()
        depth = 0
        for mm in re.finditer(r'<div\b|</div>', nav[i:]):
            depth += 1 if not mm.group(0).startswith('</') else -1
            if depth == 0:
                nav = nav[:i] + nav[i + mm.end():]
                n += 1
                break
        else:
            raise SystemExit('div 没配上：' + cls)


def is_internal(href, root):
    return (href.startswith('#')
            or href.startswith(root)
            or href.rstrip('/') == root.rstrip('/'))


def process(rel, dry):
    path = os.path.join(PUB, rel)
    h = open(path, encoding='utf-8').read()
    root = column_root(rel)
    if not root:
        return ('跳过（认不出属于哪一栏）', 0)
    zh, en = COLUMNS[root]

    span = find_navzone(h, rel)
    if not span:
        return ('跳过（找不到顶栏）', 0)
    i, j = span
    nav = h[i:j]
    before = nav
    dropped = []

    # ① 整块删：智能体条、nav-cols、全站栏目条
    for cls in ('agent-strip', 'nav-cols'):
        nav, n = strip_block(nav, cls)
        if n:
            dropped.append('%s×%d' % (cls, n))
    if re.search(r'<div[^>]*class="[^"]*nav-bar-sub[^"]*nbs-grid', nav):
        nav, n = strip_block(nav, 'nav-bar-sub')      # 只有带 nbs-grid 的才是全站栏目条
        dropped.append('全站栏目条×%d' % n)

    # ② nav-links 里只留本栏内部链接
    # ⚠ 别用 `(.*?)</div>` 找 nav-links 的内容——里面就有一个 <div class="lang-toggle">，
    #   非贪婪会在它的 </div> 上提前收尾，替换后当场多出一个 </div>。必须数深度。
    lm = re.search(r'<div[^>]*class="[^"]*\bnav-links\b[^"]*"[^>]*>', nav)
    kept_out = []
    if lm:
        a = lm.end()
        depth = 1
        b = None
        for mm in re.finditer(r'<div\b|</div>', nav[a:]):
            depth += 1 if not mm.group(0).startswith('</') else -1
            if depth == 0:
                b = a + mm.start()
                break
        assert b is not None, 'nav-links 没配上：' + rel
        inner = nav[a:b]
        keep = []
        for am in re.finditer(r'<a\b[^>]*href="([^"]*)"[^>]*>.*?</a>', inner, re.S):
            href = am.group(1)
            label = re.sub(r'<[^>]+>', '', am.group(0)).strip()
            if is_internal(href, root):
                keep.append('    ' + am.group(0))
            else:
                kept_out.append('%s(%s)' % (label, href))
        new_inner = ('\n' + '\n'.join(keep) + '\n' if keep else '\n') + LANG + \
            '    <a class="nav-back" href="/browse/"><span class="zh-only">爱思乐园 ↗</span>' \
            '<span class="en-only">SDE Universes ↗</span></a>\n  '
        nav = nav[:a] + new_inner + nav[b:]

    # ③ 站标改本栏名
    nav = re.sub(r'<a class="nav-logo"[^>]*>.*?</a>',
                 '<a class="nav-logo" href="%s"><span class="zh-only">%s</span>'
                 '<span class="en-only">%s</span><span class="nlg-en">%s</span></a>'
                 % (root, zh, en, en), nav, count=1, flags=re.S)

    if nav == before:
        return ('无需改动', 0)
    out = h[:i] + nav + h[j:]
    if '.nav-links a.nav-back' not in out:
        k = out.rindex('</style>')
        out = out[:k] + CSS + out[k:]
    if not dry:
        open(path, 'w', encoding='utf-8').write(out)
    return ('删 %s；移出 %d 条外栏链接%s'
            % ('·'.join(dropped) or '—', len(kept_out),
               '：' + '、'.join(kept_out[:6]) + ('…' if len(kept_out) > 6 else '')
               if kept_out else ''), len(kept_out))


def targets():
    out = []
    for dirpath, _, files in os.walk(PUB):
        for fn in files:
            if fn != 'index.html':
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), PUB).replace(os.sep, '/')
            if rel.split('/')[0] in SKIP_TOP:
                continue
            h = open(os.path.join(PUB, rel), encoding='utf-8', errors='replace').read()
            if re.search(r'class="[^"]*\bnav-bar-main\b', h):
                out.append(rel)
    return sorted(out)


def main():
    dry = '--dry-run' in sys.argv
    tg = targets()
    print('待处理页面 %d' % len(tg))
    tot = 0
    for rel in tg:
        msg, n = process(rel, dry)
        tot += n
        print('  %-52s %s' % (rel, msg))
    print('%s共移出外栏链接 %d 条' % ('[dry-run] ' if dry else '', tot))


if __name__ == '__main__':
    main()
