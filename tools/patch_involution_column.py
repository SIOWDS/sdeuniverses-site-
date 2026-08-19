#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""首页挂「内卷与出路」专栏：栏目条链接 + 配色 + 专栏区块（放在艺术专栏之后、今日长文之前）。"""
import io, sys

P = '/home/claude/site/public/index.html'
h = io.open(P, encoding='utf-8').read()
orig = h

# ---------- 1. 栏目条配色 ----------
CSS_OLD = '.nav-bar-sub a.col-bgy{color:#8A6A1E;font-weight:700}'
CSS_NEW = CSS_OLD + '.nav-bar-sub a.col-inv{color:#1F7A72;font-weight:700}'
assert h.count(CSS_OLD) == 1, 'CSS 锚点不唯一: %d' % h.count(CSS_OLD)
assert '.col-inv{' not in h, 'col-inv 已存在，勿重复挂'
h = h.replace(CSS_OLD, CSS_NEW, 1)

# ---------- 2. 栏目条链接（紧跟艺术专栏） ----------
NAV_OLD = '<a href="/art/" class="col-art zh-only">艺术专栏</a><a href="/art/" class="col-art en-only">Art</a>'
NAV_NEW = (NAV_OLD +
           '\n      <a href="/involution/" class="col-inv zh-only">内卷与出路</a>'
           '<a href="/involution/" class="col-inv en-only">Involution &amp; the Way Out</a>')
assert h.count(NAV_OLD) == 1, '导航锚点不唯一: %d' % h.count(NAV_OLD)
h = h.replace(NAV_OLD, NAV_NEW, 1)

# ---------- 3. 专栏区块 ----------
ANCHOR = ('<a href="/art/" style="display:inline-block;padding:12px 25px;border:1px solid #c6a468;'
          'border-radius:28px;color:#e0c084;text-decoration:none;font-weight:700">进入专栏 · 阅读四篇 →</a>'
          '</div></section>\n')
assert h.count(ANCHOR) == 1, '区块锚点不唯一: %d' % h.count(ANCHOR)
assert 'id="involution-feature"' not in h, 'involution-feature 已存在'

CARD = (
 '<div style="max-width:880px;margin:0 auto 16px;border:1px solid rgba(47,140,134,.42);border-radius:14px;'
 'padding:22px 26px;background:rgba(47,140,134,.09);text-align:left">\n'
 '<div style="font-size:11.5px;letter-spacing:.26em;color:#7FC5BD;margin-bottom:11px">{kick}</div>\n'
 '<a href="{href}" style="text-decoration:none"><div style="font-size:clamp(19px,3vw,26px);font-weight:700;'
 'color:#F0F5F3;line-height:1.5">{title}</div>\n'
 '<div style="font-size:15px;color:#CBD8D4;margin-top:9px;line-height:1.9">{desc}</div></a>\n'
 '</div>\n')

cards = ''.join([
  CARD.format(kick='开 栏 基 座 · 第 五 章 · 场 景',
              href='/books/involution/education/',
              title='教育内卷与出路：递减滞留、发生窗口与再生教育学',
              desc='教育不是内卷最严重的行业，而是内卷的总病灶——因为它决定一个社会如何理解成长、如何分配未来。'),
  CARD.format(kick='开 栏 基 座 · 第 七 章 · 场 景',
              href='/books/involution/research/',
              title='基于 AEI 的科研内卷与出路',
              desc='论文仍在增长，原创却在稀薄——高产而无生，是科研内卷的准确画像。'),
  CARD.format(kick='开 栏 基 座 · 第 一 章 · 原 理',
              href='/books/involution/marginal-utility/',
              title='边际效用递减原理：SIO 发生学证明',
              desc='效用不是满足度，而是意义体验；递减不是欲望疲劳，而是意义输入的条件被价值持续削减。'),
])

BLOCK = (
 '\n<!-- 内卷与出路专栏 -->\n'
 '<section id="involution-feature" style="padding:74px 22px;'
 'background:linear-gradient(148deg,#08282A,#0E3A3C 58%,#123033);color:#EAF1EE">\n'
 '<div style="max-width:1060px;margin:auto;text-align:center">\n'
 '<div style="font-size:12px;letter-spacing:.44em;color:#D8973C;margin-bottom:18px">'
 '新 专 栏 · 王 德 生 · 开 栏 基 座 十 章</div>\n'
 '<h2 style="font-family:\'Noto Serif SC\',serif;font-size:clamp(38px,6vw,66px);margin:0 0 18px">内卷与出路</h2>\n'
 '<p style="max-width:840px;margin:0 auto 24px;font-size:18px;line-height:2;color:#CBD8D4">'
 '内卷不是竞争太狠，而是 <b style="color:#7FD3C9">0—1 发生窗口</b>缺席之后，价值递减仍被滞留在原地。'
 '本栏每篇只做两件事：先把某个具体场域的内卷写成一条<b style="color:#7FD3C9">可以被推翻的机制</b>——'
 '它靠什么自我繁殖、在哪一步价值开始递减、这段递减最后由谁买单；再给出那个场域里能落地的出路——'
 '不是更快更狠更长，而是把 0—1 的发生窗口重新装回制度、课程与日程里。</p>\n'
 '<div style="display:flex;justify-content:center;gap:12px;flex-wrap:wrap;margin-bottom:26px">\n'
 '<span style="border:1px solid rgba(216,151,60,.55);border-radius:22px;padding:7px 17px;font-size:13px;color:#E6D9C4">'
 '不收抱怨</span>\n'
 '<span style="border:1px solid rgba(216,151,60,.55);border-radius:22px;padding:7px 17px;font-size:13px;color:#E6D9C4">'
 '不收口号</span>\n'
 '<span style="border:1px solid rgba(216,151,60,.55);border-radius:22px;padding:7px 17px;font-size:13px;color:#E6D9C4">'
 '每篇自带证伪条件</span>\n'
 '<span style="border:1px solid rgba(216,151,60,.55);border-radius:22px;padding:7px 17px;font-size:13px;color:#E6D9C4">'
 '出路要能落到日程上</span></div>\n'
 + cards +
 '<a href="/involution/" style="display:inline-block;margin-top:10px;padding:12px 25px;border:1px solid #2F8C86;'
 'border-radius:28px;color:#7FD3C9;text-decoration:none;font-weight:700">进入内卷与出路 →</a></div></section>\n'
)

h = h.replace(ANCHOR, ANCHOR + BLOCK, 1)

# ---------- 4. 标签配对自检 ----------
for tag in ('div', 'section', 'style', 'script', 'select', 'optgroup', 'a', 'p', 'h2', 'span'):
    o = h.count('<%s ' % tag) + h.count('<%s>' % tag)
    c = h.count('</%s>' % tag)
    ob = orig.count('<%s ' % tag) + orig.count('<%s>' % tag)
    cb = orig.count('</%s>' % tag)
    assert (o - ob) == (c - cb), '%s 开闭增量不一致: +%d 开 / +%d 闭' % (tag, o - ob, c - cb)

io.open(P, 'w', encoding='utf-8').write(h)
print('OK  首页 %d -> %d 字符 (+%d)' % (len(orig), len(h), len(h) - len(orig)))
