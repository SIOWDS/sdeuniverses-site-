#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mkthreeviews_library.py —— 把《三视角文章集合》按九个子频道挂上「三视角专栏」。

产出：
  · public/three-views/doc/<id>/index.html   每篇一页：PDF.js 分页阅读 ＋ 纯文字版 ＋ 下载
  · public/three-views/doc/<id>/<id>.pdf     文章本体
  · public/three-views/library/<slug>/       每个子频道一页
  · public/three-views/library/index.html    九个子频道总目

底料：tools/threeviews_library.py（CHANNELS / LIBRARY / BY_CH），
      正文文本读 tools/threeviews_library_text/<id>.txt。

⚠ 四条纪律（前三条与 mkthreeviews_articles.py 同源，第四条是本轮新加的）：
 1. 壳是本栏自己的浅色纸本，不许把首页导航背进来。
 2. 每页同目录既有 index.html 又有 PDF，阅读页里**必须同时内嵌纯文字版**，
    否则站内检索按「同目录页面 URL」收正文时这篇会落在索引外。
 3. PDF 文件名用 ASCII（<id>.pdf），中文标题走 <a download> 属性。
 4. LIBRARY 里带 reuse 字段的条目**不产出任何文件**——那 49 篇已作为图册扫码原文
    存在 /three-views/read/<aNNN>/，子频道只列条目并指过去。一篇文章在站内只存一份 PDF。

用法：python3 tools/mkthreeviews_library.py [--dry-run]
"""
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, 'public')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from threeviews_library import CHANNELS, LIBRARY, BY_CH        # noqa: E402
from mkthreeviews_articles import CSS, FONTS, FIT, READER_JS   # noqa: E402

OUT = os.path.join(PUB, 'three-views')
TEXTDIR = os.path.join(HERE, 'threeviews_library_text')
STAGE = os.environ.get('TV_LIB_STAGE', '/home/claude/stage')

CH_BY_SLUG = {c['slug']: c for c in CHANNELS}

FOOT = """<footer class="tv-foot">
<p>三视角文章由王德生历年撰写　·　文库整理：德麦国际</p>
<p>© 德麦国际　·　<a href="/three-views/">三视角专栏</a>　·　<a href="/browse/">爱思乐园 SDE Universes</a></p>
</footer>"""

EXTRA_CSS = """<style>
.chgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(268px,1fr));
 gap:1.1rem;margin:2rem 0 1rem}
.chcard{display:block;text-decoration:none;color:inherit;border:1px solid var(--border2);
 border-radius:10px;background:var(--card);padding:1.05rem 1.15rem 1.15rem;
 transition:transform .18s,box-shadow .18s,border-color .18s}
.chcard:hover{transform:translateY(-3px);box-shadow:0 10px 26px rgba(0,0,0,.09);
 border-color:var(--ac)}
.chcard b{display:block;font-size:1.12rem;letter-spacing:.03em}
.chcard .en{display:block;font-family:'Playfair Display',Georgia,serif;font-size:.7rem;
 letter-spacing:.18em;text-transform:uppercase;color:var(--muted);margin-top:.2rem}
.chcard .bl{display:block;margin-top:.6rem;font-size:.88rem;line-height:1.75;color:var(--text2)}
.chcard .ct{display:block;margin-top:.7rem;font-size:.8rem;color:var(--ac);font-weight:600}
.mark{display:inline-block;margin-left:.4rem;padding:.05rem .38rem;border-radius:3px;
 font-size:.68rem;color:var(--muted);border:1px solid var(--border2);vertical-align:.08em}
</style>"""


def esc(s):
    return html.escape(str(s), quote=True)


def page_head(title, desc, canon):
    return ('<!doctype html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            '<title>%s</title>\n<meta name="description" content="%s">\n'
            '<link rel="canonical" href="%s">\n'
            '<meta property="og:type" content="article">\n'
            '<meta property="og:title" content="%s">\n'
            '<meta property="og:description" content="%s">\n'
            '<meta property="og:url" content="%s">\n%s\n%s\n%s\n</head>'
            % (esc(title), esc(desc), canon, esc(title), esc(desc), canon,
               FONTS, CSS, EXTRA_CSS))


def topbar(links):
    return ('<header class="tv-top">\n<a class="tv-brand" href="/three-views/">'
            '<b>三视角专栏</b><span>Three Views</span></a>\n<nav>%s</nav>\n</header>'
            % ''.join(links))


NAV_LIB = '<a href="/three-views/">图册二十一篇</a><a href="/three-views/articles/">扫码原文</a>'


def href_of(a):
    return ('/three-views/read/%s/' % a['reuse']) if 'reuse' in a \
        else ('/three-views/doc/%s/' % a['id'])


def build_reader(k, rows, ch):
    a = rows[k]
    pdf = '/three-views/doc/%s/%s.pdf' % (a['id'], a['id'])
    txt = open(os.path.join(TEXTDIR, a['id'] + '.txt'), encoding='utf-8').read()
    lead = re.sub(r'\s+', ' ', txt[:110]).strip()
    desc = ('%s——王德生三视角文章，收在「%s」子频道，共 %d 页。%s'
            % (a['title'], ch['zh'], a['pages'], lead))[:190]
    prev_a = ('<a href="%s">← 上一篇</a>' % href_of(rows[k - 1])) if k > 0 \
        else '<a href="/three-views/library/%s/">← 回「%s」</a>' % (ch['slug'], esc(ch['zh']))
    next_a = ('<a href="%s">下一篇 →</a>' % href_of(rows[k + 1])) if k + 1 < len(rows) \
        else '<a href="/three-views/library/%s/">回「%s」→</a>' % (ch['slug'], esc(ch['zh']))
    plain = (('<details class="plain"><summary>纯文字版（全文 %s 字，便于手机阅读、复制与站内检索）'
              '</summary><div class="body">%s</div></details>'
              % (format(a['chars'], ','), esc(txt))) if a['chars'] >= 40 else
             '<div class="tv-note">本篇原件是整页图表（无文字层），只能看图或下载 PDF。</div>')
    body = [
        page_head('%s · 三视角%s' % (a['title'], ch['zh']), desc,
                  'https://sdeuniverses.com/three-views/doc/%s/' % a['id']),
        '<body>',
        topbar([NAV_LIB,
                '<a href="/three-views/library/">文库九频道</a>',
                '<a class="cur" href="/three-views/library/%s/">%s</a>'
                % (ch['slug'], esc(ch['zh']))]),
        '<main class="tv-wrap">', '<header class="tv-hd">',
        '<div class="tv-eyebrow">三视角文库 · %s</div>' % esc(ch['zh']),
        '<h1>%s</h1>' % esc(a['title']),
        '<p class="tv-sub">共 %d 页 · 约 %s 字　|　王德生　|　子频道：'
        '<a href="/three-views/library/%s/">%s</a></p>'
        % (a['pages'], format(a['chars'], ','), ch['slug'], esc(ch['zh'])),
        '</header>',
        '<div class="bar">',
        '<button class="btn" id="prev" disabled>‹ 上一页</button>',
        '<div class="pagebox"><input id="pageInput" type="number" min="1" value="1">'
        '<span>/ <span id="totalPages">…</span></span></div>',
        '<button class="btn" id="next" disabled>下一页 ›</button>',
        '<button class="btn" id="zoomOut">−</button>',
        '<button class="btn" id="zoomIn">＋</button>',
        '<a class="btn dl" href="%s" download="%s.pdf">⬇ 下载 PDF</a>' % (pdf, esc(a['title'])),
        '<a class="btn" href="/three-views/library/%s/">回「%s」</a>'
        % (ch['slug'], esc(ch['zh'])),
        '</div>',
        '<div class="stage" id="stage">',
        '<div id="loading" class="loading"><div class="spinner"></div>正在载入本篇…</div>',
        '<div id="page-wrap" style="display:none"><canvas id="pdfCanvas"></canvas>'
        '<div class="textLayer" id="textLayer"></div></div>',
        '<div id="error" class="err" style="display:none"></div>',
        '</div>',
        '<p class="hint">← → 方向键翻页 · 选中正文任意一句可问 WDS</p>',
        plain,
        '<div class="tv-pager">%s%s</div>' % (prev_a, next_a),
        '</main>', FOOT,
        READER_JS % {'pdf': pdf, 'title_js': '"%s"' % a['title'].replace('"', '\\"')},
        FIT, '</body>', '</html>']
    return '\n'.join(body)


def build_channel(ch):
    rows = BY_CH[ch['slug']]
    n_new = sum(1 for a in rows if 'id' in a)
    n_re = len(rows) - n_new
    chars = sum(a.get('chars', 0) for a in rows)
    title = '三视角%s · %d 篇' % (ch['zh'], len(rows))
    desc = ('%s　%s' % (ch['blurb'], '共 %d 篇，可分页阅读与下载。' % len(rows)))[:190]
    body = [page_head(title, desc,
                      'https://sdeuniverses.com/three-views/library/%s/' % ch['slug']),
            '<body>',
            topbar([NAV_LIB, '<a href="/three-views/library/">文库九频道</a>',
                    '<a class="cur">%s</a>' % esc(ch['zh'])]),
            '<main class="tv-wrap">', '<header class="tv-hd">',
            '<div class="tv-eyebrow">%s</div>' % esc(ch['en']),
            '<h1>%s</h1>' % esc(ch['zh']),
            '<p class="tv-sub">%d 篇　|　约 %s 万字　|　王德生</p>'
            % (len(rows), format(round(chars / 10000, 1))),
            '</header>',
            '<div class="tv-note">%s</div>' % esc(ch['blurb']),
            '<ul class="alist" style="margin-top:1.8rem">']
    for a in rows:
        if 'reuse' in a:
            body.append('<li><a href="/three-views/read/%s/">%s</a>'
                        '<span class="mark">已在扫码原文</span>'
                        '<em>图册扫码原文，点开即读</em></li>'
                        % (a['reuse'], esc(a['title'])))
        else:
            body.append('<li><a href="/three-views/doc/%s/">%s</a>'
                        '<em>%d 页 · %s 字</em></li>'
                        % (a['id'], esc(a['title']), a['pages'], format(a['chars'], ',')))
    body.append('</ul>')
    if n_re:
        body.append('<p class="hint" style="text-align:left;margin-top:1.2rem">'
                    '其中 %d 篇此前已作为图册扫码原文上站，点进去是同一篇，不另存一份。</p>' % n_re)
    idx = [c['slug'] for c in CHANNELS].index(ch['slug'])
    prev_c = CHANNELS[idx - 1] if idx > 0 else None
    next_c = CHANNELS[idx + 1] if idx + 1 < len(CHANNELS) else None
    body += ['<div class="tv-pager">%s%s</div>'
             % ('<a href="/three-views/library/%s/">← %s</a>' % (prev_c['slug'], esc(prev_c['zh']))
                if prev_c else '<a href="/three-views/library/">← 文库总目</a>',
                '<a href="/three-views/library/%s/">%s →</a>' % (next_c['slug'], esc(next_c['zh']))
                if next_c else '<a href="/three-views/library/">回文库总目 →</a>'),
             '</main>', FOOT, FIT, '</body>', '</html>']
    return '\n'.join(body)


def build_hub():
    n = len(LIBRARY)
    chars = sum(a.get('chars', 0) for a in LIBRARY)
    title = '三视角文库 · %d 篇 · 九个子频道' % n
    desc = ('王德生历年三视角文章 %d 篇，按基础理论、学科解构、教育、学习法、商业管理、'
            '个人成长、学员实践、培训笔记、走向 SDE 九个子频道分列，篇篇可分页阅读与下载。' % n)
    body = [page_head(title, desc, 'https://sdeuniverses.com/three-views/library/'),
            '<body>',
            topbar([NAV_LIB, '<a class="cur">文库九频道</a>']),
            '<main class="tv-wrap">', '<header class="tv-hd">',
            '<div class="tv-eyebrow">Library</div>',
            '<h1>三视角文库</h1>',
            '<p class="tv-sub">%d 篇 · 九个子频道 · 约 %s 万字　|　王德生历年撰写</p>'
            % (n, format(round(chars / 10000))),
            '</header>',
            '<div class="tv-note">这是《三视角图册》之外的另一半：图册给的是<b>一张张图</b>，'
            '文库给的是<b>成篇的文章</b>。每一篇都能<b>在线分页翻阅</b>、<b>下载 PDF</b>，'
            '也附<b>纯文字版</b>。同一篇在原始文件夹里往往出现三四次，已按正文比对并成一条；'
            '成系列的（如「从圣经到三视角(1)(2)」）按篇号分开保留。</div>',
            '<div class="chgrid">']
    for c in CHANNELS:
        body.append('<a class="chcard" href="/three-views/library/%s/">'
                    '<b>%s</b><span class="en">%s</span>'
                    '<span class="bl">%s</span><span class="ct">%d 篇 →</span></a>'
                    % (c['slug'], esc(c['zh']), esc(c['en']), esc(c['blurb']), c['n']))
    body += ['</div>',
             '<div class="tv-pager"><a href="/three-views/">← 回三视角图册</a>'
             '<a href="/three-views/articles/">扫码原文 166 篇 →</a></div>',
             '</main>', FOOT, FIT, '</body>', '</html>']
    return '\n'.join(body)


def main():
    dry = '--dry-run' in sys.argv
    new = [a for a in LIBRARY if 'id' in a]
    print('文库 %d 篇（新上 %d ＋ 复用图册原文 %d）· PDF 合计 %.1f MB · 正文 %s 字'
          % (len(LIBRARY), len(new), len(LIBRARY) - len(new),
             sum(a['bytes'] for a in new) / 1e6,
             format(sum(a['chars'] for a in new), ',')))
    for c in CHANNELS:
        print('   %-11s %-8s %3d 篇' % (c['slug'], c['zh'], c['n']))
    if dry:
        return
    import shutil
    for c in CHANNELS:
        rows = BY_CH[c['slug']]
        for k, a in enumerate(rows):
            if 'reuse' in a:
                continue
            d = os.path.join(OUT, 'doc', a['id'])
            os.makedirs(d, exist_ok=True)
            open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(
                build_reader(k, rows, c))
            tgt = os.path.join(d, a['id'] + '.pdf')
            src = os.path.join(STAGE, a['id'] + '.pdf')
            if not os.path.exists(tgt) and os.path.exists(src):
                shutil.copy(src, tgt)
        d = os.path.join(OUT, 'library', c['slug'])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(build_channel(c))
    d = os.path.join(OUT, 'library')
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(build_hub())
    print('已写 %d 个阅读页 ＋ %d 个子频道页 ＋ 1 个文库总目 →' % (len(new), len(CHANNELS)), OUT)


if __name__ == '__main__':
    main()
