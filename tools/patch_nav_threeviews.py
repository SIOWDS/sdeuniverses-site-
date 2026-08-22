#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把栏目条从 12 项扩到 14 项（两排各 7）：新增「三视角专栏」，并把此前首页零入口的
「三维九宫」提上来补满对称。一次性脚本，改完即为存量；留档以备回溯。

⚠ 这套栏目条在三个页面上是**三种结构**，不能一把正则套过去：
   · public/browse/index.html —— 单个 .nbs-row 装 12 项，靠 6 列 grid 自动折成两排
   · public/directory/index.html、public/overview/index.html —— 两个 .nbs-row 各 6 项
   · public/how/index.html —— 只有 .nbs-row 的 CSS，没有 markup
   三视角专栏自己那 22 页的顶栏是 tools/mkthreeviews.py 从 browse 现取的，
   **本脚本改完 browse 之后必须重跑 mkthreeviews.py**，否则那 22 页还挂着 12 项的旧条。
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, 'public')

TV_ZH = ('      <a href="/three-views/" class="col-tv zh-only">三视角专栏</a>'
         '<a href="/three-views/" class="col-tv en-only">Three Views</a>\n')
ND_ZH = ('      <a href="/nine-doorways/" class="col-ndw zh-only">三维九宫</a>'
         '<a href="/nine-doorways/" class="col-ndw en-only">Nine Doorways</a>\n')
AI = ('      <a href="/ai/" class="col-ai zh-only">AI 专栏</a>'
      '<a href="/ai/" class="col-ai en-only">AI</a>\n')
DVG_TAIL = ('<a href="/discovery-vs-genesis/" class="col-dvg en-only">'
            'Discovery vs Genesis</a>\n')
HEA_TAIL = '<a href="/health/" class="col-hea en-only">Health</a>\n'
NEW_CSS = ('.col-tv{color:#0F6E8C;font-weight:700}\n'
           '.col-ndw{color:#4A5D23;font-weight:700}\n')


def rep(h, old, new, path, n=1):
    assert h.count(old) == n, ('锚点计数不符 %d≠%d：%s / %r' % (h.count(old), n, path, old[:70]))
    return h.replace(old, new, n)


def patch_markup(h, path):
    # AI 那一项从第一排挪到第二排（第一排要腾出两格给三维九宫与三视角专栏）
    h = rep(h, AI, '', path)
    # 第一排：发现VS发生 之后接 三维九宫 · 三视角专栏
    h = rep(h, DVG_TAIL, DVG_TAIL + ND_ZH + TV_ZH, path)
    # 第二排：健康专栏 之后接 AI 专栏
    h = rep(h, HEA_TAIL, HEA_TAIL + AI, path)
    return h


def patch_css(h, path):
    m = re.search(r'\.nbs-row\{display:grid;grid-template-columns:repeat\(6,minmax\(0,1fr\)\);'
                  r'(.*?)max-width:(\d+)px;', h)
    assert m, '找不到 .nbs-row 主规则：' + path
    h = rep(h, m.group(0),
            m.group(0).replace('repeat(6,', 'repeat(7,')
                      .replace('max-width:%spx;' % m.group(2), 'max-width:1200px;'), path)
    # ⚠ .col-how 这条规则在四个页面里有两种写法：directory 单独占一行，
    #   overview/how/browse 则紧跟在上一条之后。所以只锚定规则本身，换行交给下面补。
    if '.col-tv{' not in h:
        anchor = '.col-how{color:#1F7A72;font-weight:700}'
        assert h.count(anchor) == 1, '找不到 .col-how 定义：' + path
        h = h.replace(anchor, anchor + '\n' + NEW_CSS.rstrip('\n'), 1)
    return h


def main():
    for rel, has_markup in (('browse/index.html', True),
                            ('directory/index.html', True),
                            ('overview/index.html', True),
                            ('how/index.html', False)):
        p = os.path.join(PUB, rel)
        h = open(p, encoding='utf-8').read()
        before = h
        h = patch_css(h, rel)
        if has_markup:
            h = patch_markup(h, rel)
        assert h != before, '什么都没改：' + rel
        open(p, 'w', encoding='utf-8').write(h)
        n = len(re.findall(r'class="col-[a-z0-9]+ zh-only"', h))
        print('✓ %-26s 栏目条 zh 项数 %d' % (rel, n))


if __name__ == '__main__':
    main()
