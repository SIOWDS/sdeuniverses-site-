#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mkbanyu.py —— 「巴渝培训」专栏：/banyu/ 总目 ＋ 三个子频道。

  /banyu/        总目：三天是什么、给谁、课表、线上观摩
  /banyu/day1/   第一天 · SDE发生学教育入门
  /banyu/day2/   第二天 · SDE教材发生学
  /banyu/day3/   第三天 · SDE课堂发生学

⚠ 三条纪律（王德生 2026-08-22 定）：
 1. **页面上一个术语都不许留。** 受众是小学全学科教师与在线家长，不是学派内部。
    「显露/差异/纠缠」「光滑化」「回写」「封写」「岔口」一律换成大白话
    （磨平了的成品／心里那本账被改了／上了锁／还没定下来的地方）。
    子频道的标题是他指定的，照留；正文里不再出现。
 2. 专栏页自成一体，不把首页导航整套背进来（与 mkthreeviews.py 同一条）。
 3. 课表、时段、收费、赠书与退费条款都照他说的原样写，不替他加码，不替他打折。

用法：python3 tools/mkbanyu.py [--dry-run]
"""
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, 'public')
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(PUB, 'banyu')

sys.path.insert(0, HERE)
from banyu_plan import SESSIONS, BRING, RULES, LINKS  # noqa: E402

STAMP = re.search(r'^stamp=(\S+)',
                  open(os.path.join(HERE, 'wds-mode.stamp'), encoding='utf-8').read(),
                  re.M).group(1)

CSS = """<style>
:root{--bg:#0F0D0A;--pa:#EFE9DD;--dim:#B9AE99;--faint:#7C7466;--ac:#C9A227;
 --s:#7FA8C9;--d:#C98F5E;--e:#8FB3A0;--line:#2A2521;--card:#161310}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--pa);line-height:1.9;
 font-family:"Noto Serif CJK SC","Noto Serif SC","Songti SC",Georgia,serif;
 -webkit-text-size-adjust:100%}
a{color:var(--ac);text-decoration:none}
a:hover{text-decoration:underline;text-underline-offset:4px}
.w{max-width:860px;margin:0 auto;padding:0 22px}
header.top{border-bottom:1px solid var(--line);padding:13px 0;font-size:13.5px;color:var(--dim)}
header.top .w{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;align-items:center}
header.top nav{display:flex;gap:16px;flex-wrap:wrap}
header.top nav a{color:var(--dim)}
header.top nav a.cur{color:var(--ac);font-weight:700}
.hero{padding:48px 0 26px;border-bottom:1px solid var(--line)}
.kicker{font-size:12.5px;letter-spacing:.16em;color:var(--d)}
h1{font-size:33px;margin:10px 0 8px;letter-spacing:.03em;line-height:1.38}
.tag{font-size:15.5px;color:var(--ac);letter-spacing:.06em;margin:0 0 16px}
.keys{display:flex;gap:9px;flex-wrap:wrap;margin:18px 0 0}
.keys span{font-size:13px;letter-spacing:.05em;padding:5px 13px;border:1px solid var(--line);
 border-radius:2px;color:var(--dim)}
.keys span.hot{border-color:var(--ac);color:var(--ac)}
main{padding:30px 0 10px}
h2{font-size:21px;margin:42px 0 12px;letter-spacing:.04em;padding-left:13px;
 border-left:3px solid var(--ac)}
h3{font-size:17px;margin:26px 0 8px;color:var(--pa);letter-spacing:.03em}
p{margin:0 0 14px;font-size:15.8px;color:var(--dim)}
b{color:var(--pa)}
.lead{font-size:16.6px;color:var(--pa)}
.big{margin:22px 0;padding:19px 22px;background:#14120E;border-left:3px solid var(--ac);
 font-size:17.5px;color:var(--pa);line-height:1.85}
.note{margin:18px 0;padding:15px 19px;background:#12140F;border-left:3px solid var(--e);
 font-size:15.2px;color:var(--dim)}
.card{background:var(--card);border-left:2px solid var(--s);padding:17px 20px;margin:16px 0}
.card.d{border-left-color:var(--d)}
.card.e{border-left-color:var(--e)}
.card h3{margin:0 0 8px;font-size:16.6px}
.card p:last-child{margin:0}
.slot{font-size:13.4px;color:var(--faint);letter-spacing:.08em}
ul,ol{margin:0 0 14px;padding-left:1.35em;font-size:15.8px;color:var(--dim)}
li{margin:.3em 0}
table{width:100%;border-collapse:collapse;margin:16px 0;font-size:15px}
th,td{border:1px solid var(--line);padding:10px 12px;text-align:left;vertical-align:top;
 color:var(--dim);line-height:1.8}
th{background:#14120E;color:var(--ac);font-weight:600;white-space:nowrap}
td b{color:var(--pa)}
.days{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:22px 0 6px}
.days a{display:block;background:var(--card);border-top:2px solid var(--line);
 padding:18px 18px 20px;color:inherit;text-decoration:none}
.days a:hover{border-top-color:var(--ac);text-decoration:none}
.days a:nth-child(1){border-top-color:var(--s)}
.days a:nth-child(2){border-top-color:var(--d)}
.days a:nth-child(3){border-top-color:var(--e)}
.days b{display:block;font-size:12.5px;letter-spacing:.12em;color:var(--faint);
 font-weight:400;margin-bottom:7px}
.days span{display:block;font-size:17px;color:var(--pa);line-height:1.6}
.days em{display:block;font-style:normal;margin-top:9px;font-size:14px;color:var(--dim)}
.say{width:100%;border-collapse:collapse;margin:16px 0;font-size:15px}
.say td:first-child{color:#C98F5E;width:48%}
.say td:last-child{color:var(--e)}
.run{width:100%;border-collapse:collapse;margin:14px 0 18px;font-size:14.6px}
.run th{background:#14120E}
.run td:first-child{white-space:nowrap;color:var(--ac);width:9.6em;font-variant-numeric:tabular-nums}
.run td:nth-child(2){white-space:nowrap;color:var(--faint);width:4.2em}
.run td b{display:block;color:var(--pa);margin-bottom:3px}
.run td span{color:var(--dim)}
.links{margin:14px 0 0;padding:0;list-style:none}
.links li{margin:0 0 11px;padding-left:15px;border-left:2px solid var(--line);font-size:15px}
.links li a{font-size:15.6px}
.links li em{display:block;font-style:normal;color:var(--faint);font-size:13.8px;margin-top:2px}
.bring{background:#12140F;border-left:3px solid var(--d);padding:15px 19px;margin:18px 0;font-size:15.2px;color:var(--dim)}
.bring b{color:var(--pa)}
.pager{display:flex;justify-content:space-between;gap:14px;margin:40px 0 0;
 padding-top:18px;border-top:1px solid var(--line);font-size:15px}
.foot{border-top:1px solid var(--line);margin-top:44px;padding:26px 0 56px;
 color:var(--faint);font-size:13.2px;line-height:1.95;text-align:center}
@media(max-width:720px){.days{grid-template-columns:1fr}h1{font-size:25px}}
</style>"""

FOOT = """<div class="foot"><div class="w">
巴渝培训 · 重庆巴渝学校小学部全体教师培训（2026 年 8 月 24–26 日）<br>
主讲 王德生　·　线上直播与课后讲解 付自文<br>
<a href="/banyu/">本栏总目</a>　·　<a href="/browse/">爱思乐园 SDE Universes</a>
</div></div>"""

TAIL = '<script src="/wds-mode.js?v=%s" defer></script>\n</body>\n</html>' % STAMP

DAYS = [
    ('day1', '第一天', '8 月 24 日', 'SDE发生学教育入门'),
    ('day2', '第二天', '8 月 25 日', 'SDE教材发生学'),
    ('day3', '第三天', '8 月 26 日', 'SDE课堂发生学'),
]


def esc(s):
    return html.escape(s, quote=True)


def head(title, desc, canon):
    return ('<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n'
            '<meta name="sde-page-kind" content="channel">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            '<title>%s</title>\n<meta name="description" content="%s">\n'
            '<link rel="canonical" href="%s">\n'
            '<meta property="og:type" content="website">\n'
            '<meta property="og:title" content="%s">\n'
            '<meta property="og:description" content="%s">\n'
            '<meta property="og:url" content="%s">\n%s\n</head>\n<body>'
            % (esc(title), esc(desc), canon, esc(title), esc(desc), canon, CSS))


def topbar(cur):
    links = ['<a href="/banyu/"%s>总目</a>' % (' class="cur"' if cur == '' else '')]
    for slug, dn, date, name in DAYS:
        links.append('<a href="/banyu/%s/"%s>%s · %s</a>'
                     % (slug, ' class="cur"' if cur == slug else '', dn, esc(name)))
    return ('<header class="top"><div class="w">'
            '<span style="color:var(--ac);letter-spacing:.12em">巴渝培训</span>'
            '<nav>%s</nav></div></header>' % ''.join(links))


# ─────────────────────────── 三天的内容 ───────────────────────────
# 全部大白话。术语在这里只以「教师侧」的意思出现，不用学派词汇。

DAY_BODY = {

'day1': dict(
  tag='知识是被搬过来的，还是在孩子身上长出来的？',
  keys=['上午 9:30–11:30', '下午 14:00–16:30', '全学科', '工具：ChatSDE'],
  lead='第一天不讲新名词。第一天只把一件事情说清楚：我们平常上课，'
       '是<b>把结论搬给孩子</b>；还有另一种上法，是<b>让结论在孩子身上长一次</b>。'
       '这两种上法，孩子学完之后的样子是不一样的，而且能当堂看出来。',
  blocks=[
    ('上午 · 9:30–11:30　为什么讲清楚了，他还是不会', [
      ('p', '老办法只有三个动作：<b>搬过来、讲明白、请你接住</b>。'
            '这三个动作本身没错，错在它们默认了一件事——'
            '知识是一个可以整个端过去的东西。'),
      ('big', '课本上的每一个结论，都是<b>被磨平过</b>的。'
              '当年是怎么想到的、当年差一点走了哪条别的路，都被磨掉了；'
              '端到孩子面前时，它看上去就像<b>本来就在那里</b>。'
              '孩子接住的是那个光溜溜的成品，不是那条路。'),
      ('p', '所以会出现那个每位老师都见过的场面：讲得很清楚，例题也做了，'
            '换个说法一问就塌。因为他心里那本旧账<b>一个字都没被改过</b>。'),
      ('h3', '这一节要立起来的唯一一把尺'),
      ('p', '判断一节课有没有真的发生，不看他会不会做题，看一件事：'
            '<b>他心里原来的想法，有没有当场被推翻过一次。</b>'
            '没有推翻，就是没发生——哪怕全对。'),
      ('card', '小学里最好用的例子', 
       '问三年级：1/3 和 1/2 哪个大？有相当一部分孩子会答 1/3 大。'
       '这不是粗心。他心里那本账写的是「3 比 2 大」，'
       '这本账从来没有因为分数被改过。'
       '把这句话讲一遍，账还是不会改；让他自己撞一次，账才会改。'),
      ('h3', '上机：ChatSDE'),
      ('p', '每位老师现场打开站内的 ChatSDE，'
            '拿<b>自己学科里最难教的那一个概念</b>试一次：'
            '不要它给答案，要它把这个概念<b>当年还有哪些别的走法</b>摆出来。'
            '一节课的准备工作，从这里开始变得便宜。'),
    ]),
    ('下午 · 14:00–16:30　一节课是怎么长起来的', [
      ('p', '下午从「说明白」转到「做一遍」。用到站内的<b>教育专栏</b>，'
            '例子取<b>数学</b>与<b>英语</b>两科——不是因为只有这两科能用，'
            '是因为这两科最容易看出差别。'),
      ('h3', '五个动作，顺序不能换'),
      ('ol', ['先找到一个<b>对不上的地方</b>——孩子已有的想法在这里说不通了；',
              '让他<b>先摆出一个说法</b>，哪怕是错的；',
              '带他<b>走一遍</b>，看这个说法能撑到哪里；',
              '<b>落到具体东西上</b>：小棒、纸条、撕下来的三个角；',
              '走完之后，<b>又露出一个新的对不上</b>——下一节课从这里开始。']),
      ('note', '第四步是最常被跳过的一步。跳过它，前三步会变成一场热闹的活动课：'
               '孩子很投入，账本没动。'),
      ('h3', '这一节要守住的那件事'),
      ('big', '那个<b>还没定下来的地方</b>，是这节课最贵的东西。'
              '老师最大的诱惑，是在孩子卡住的那三十秒里把答案递过去。'
              '递过去，这节课就结束了。'),
      ('h3', '关于 AI，先把话说在前头'),
      ('p', 'AI 天生是<b>提前给答案</b>的机器。原样搬进课堂，它就是一台'
            '更快、更全、更贴心的老办法机器——把知识磨得更平，端得更快。'),
      ('p', '要用它，就得<b>配反过来</b>：不让它当答案的来源，'
            '让它当<b>出难题的那一方</b>——专门给反例，专门问'
            '「那不这样行不行」，专门把孩子的说法顶回去。'
            '这一条配错，后面两天全都白讲。'),
    ]),
  ],
  take=['一把当堂能用的尺：他心里的账被改了没有',
        '一个能立刻在自己学科里试的概念',
        'ChatSDE 会用了'],
),

'day2': dict(
  tag='课本的每一页，当年都曾经有过岔路',
  keys=['上午 9:30–11:30', '下午 14:00–16:30', '全学科', '各科各做一个概念'],
  lead='第二天动手。上午拆<b>课本</b>，下午拆<b>各科自己的知识</b>。'
       '拆的意思不是否定课本，是把课本上被磨掉的那一段路<b>找回来</b>，'
       '找回来之后再决定这节课怎么上。',
  blocks=[
    ('上午 · 9:30–11:30　课本是怎么被磨平的', [
      ('p', '课本要在四十分钟里讲清楚一件人类花了几百年才定下来的事，'
            '只能压缩。压缩的办法就是把过程去掉、只留结论，'
            '再按最省事的顺序排好。<b>这是课本的本分，不是课本的毛病。</b>'
            '毛病出在我们照着这个顺序讲。'),
      ('h3', '把一页课本还原成一个岔口：三句话'),
      ('table', [['要问的一句', '它在做什么'],
                 ['如果不这样，会怎么样？', '让孩子发现「这样」是被选出来的，不是天生的'],
                 ['当年是不是差一点选了别的？', '把被磨掉的那条岔路摆回桌面'],
                 ['你能不能自己造一个出来？', '让他站到定规矩的那一边，而不是接规矩的那一边']]),
      ('p', '这三句话是<b>还原课本的通用工具</b>，跟学科无关。'
            '语文、数学、英语、音乐、美术、体育都能用。'),
      ('h3', '为什么补课常常没用'),
      ('big', '有些孩子不是没听懂，是心里那条规矩<b>已经上了锁</b>——'
              '「这东西本来就是这样，不用想」。'
              '锁不打开，你把当年的路原样还给他，他也走不进去。'
              '<b>所以次序是：先开锁，再还路。</b>'),
      ('p', '开锁用的就是上面那三句话。它们看起来简单，'
            '难的是老师要忍住不替他回答。'),
    ]),
    ('下午 · 14:00–16:30　各科各做一个', [
      ('p', '下午分组，每一科挑<b>自己最难教的那一个概念</b>，'
            '用上午那三句话现场做一遍，做完当场讲给别科的老师听——'
            '<b>别科老师听不懂，就是还没拆开。</b>'),
      ('h3', '几个已经拆过的例子，供各组参考'),
      ('table', [['科目', '拆过的概念'],
                 ['数学', '数、位值、加法交换律、乘法、分数、等号、三角形内角和'],
                 ['语文', '一篇作文是怎么起头的'],
                 ['英语', '一个词是怎么被用会的，而不是背会的'],
                 ['音乐 · 美术', '一段旋律、一张画，是在哪一刻成立的']]),
      ('note', '这些例子只是参考。真正要拆的是<b>你们班上周刚讲砸的那一课</b>。'),
      ('h3', '一组做完的验收'),
      ('ul', ['说得出这一课当年有过哪条岔路；',
              '说得出孩子心里原来那本账写的是什么；',
              '说得出这一课要靠什么把那本账改掉；',
              '说得出如果没改掉，明天在什么地方会塌。']),
    ]),
  ],
  take=['三句还原课本的话，全学科通用',
        '本组一个概念的完整拆解',
        '一条次序：先开锁，再还路'],
),

'day3': dict(
  tag='一节课，究竟是在哪一刻发生的',
  keys=['上午 9:30–11:30', '下午 14:00–16:30', '当场备一节课', '专著《SDE课堂发生学》'],
  lead='第三天回到四十分钟本身。前两天讲的是想法和课本，'
       '第三天讲的是<b>人站在教室里的那四十分钟</b>：'
       '什么时候该说话，什么时候必须闭嘴，怎么当堂知道这节课成了没有。',
  blocks=[
    ('上午 · 9:30–11:30　四种「没发生」，长什么样', [
      ('p', '一节课没成，样子不止一种。分不清是哪一种，补救就会补错地方。'),
      ('table', [['样子', '实际发生了什么', '该怎么补'],
                 ['过两天全忘了', '当时是记住了，没跟他自己的东西接上', '换一个他自己的例子重来'],
                 ['太顺了，一路对到底', '中间没有一处卡住，等于没走', '故意做一道会撞墙的题'],
                 ['讲得头头是道，一换说法就塌', '话是圆的，账没改', '换个场合再问一遍'],
                 ['怎么讲都进不去', '心里那条规矩上了锁', '先开锁（第二天那三句话），再讲']]),
      ('note', '次序上有一条硬规矩：<b>先查是不是上了锁</b>。'
               '锁着的时候，另外三种补救全部无效——这是最常被浪费的一整节课。'),
      ('h3', '老师站在哪里'),
      ('big', '这一节课里，老师的位置不是<b>知道答案的那个人</b>，'
              '是<b>守住那个还没定下来的地方、不让它提前关上的那个人</b>。'
              '这句话听起来轻，做起来是全场最难的一件事。'),
    ]),
    ('下午 · 14:00–16:30　当场备一节课', [
      ('p', '下午每人拿出<b>下周要上的一节真课</b>，现场改。改完互相试讲十分钟。'),
      ('h3', '课堂用语：不要说 / 要说'),
      ('table', [['不要说', '改成'],
                 ['「记住，就是这样。」', '「如果不这样，会怎么样？」'],
                 ['「对，很好，下一题。」', '「你是怎么想到的？说给他听听。」'],
                 ['「这个先记下来，以后就懂了。」', '「先别记。你现在的想法是什么？」'],
                 ['「错了，我再讲一遍。」', '「按你的想法往下走，走到哪儿走不动了？」'],
                 ['「时间不够了，答案是……」', '「这个地方我们先不定下来，明天接着卡。」']]),
      ('h3', '两个当堂就能读的数'),
      ('ul', ['<b>那个还没定下来的地方，你让它开着多久。</b>'
              '整节课都没有一处开着，这节课就是老办法。',
              '<b>下课前的那一问。</b>不问会不会做，问：'
              '「你今天有没有哪个原来的想法被推翻了？是哪一个？」'
              '答不上来的人数，就是这节课的成绩。']),
      ('h3', '关于那本书'),
      ('p', '第三天讲的内容，会和付自文老师一起整理成专著'
            '<b>《SDE课堂发生学》</b>。线上观摩的老师与家长，'
            '结课后会收到一本纸质打印本。'),
    ]),
  ],
  take=['四种「没发生」的分辨法，以及先查哪一种',
        '一张课堂用语对照表，明天就能用',
        '一节改好的真课，和两个当堂能读的数'],
),
}


def render_blocks(blocks):
    out = []
    for title, items in blocks:
        out.append('<h2>%s</h2>' % esc(title))
        for it in items:
            kind = it[0]
            if kind == 'p':
                out.append('<p>%s</p>' % it[1])
            elif kind == 'h3':
                out.append('<h3>%s</h3>' % esc(it[1]))
            elif kind == 'big':
                out.append('<div class="big">%s</div>' % it[1])
            elif kind == 'note':
                out.append('<div class="note">%s</div>' % it[1])
            elif kind == 'card':
                out.append('<div class="card"><h3>%s</h3><p>%s</p></div>'
                           % (esc(it[1]), it[2]))
            elif kind in ('ul', 'ol'):
                out.append('<%s>%s</%s>'
                           % (kind, ''.join('<li>%s</li>' % x for x in it[1]), kind))
            elif kind == 'table':
                rows = it[1]
                out.append('<table><tr>%s</tr>%s</table>'
                           % (''.join('<th>%s</th>' % esc(c) for c in rows[0]),
                              ''.join('<tr>%s</tr>'
                                      % ''.join('<td>%s</td>' % c for c in r)
                                      for r in rows[1:])))
    return '\n'.join(out)


def rundown(sess):
    """一个半天的逐环节表。分钟数必须加得起来 —— 这里当场断言，别让它悄悄排错。"""
    name, span, total, rows = sess
    got = sum(r[1] for r in rows)
    assert got == total, '%s 分钟对不上：逐段合计 %d，应为 %d' % (name, got, total)
    out = ['<h2>%s</h2>' % esc(name),
           '<p class="slot">%s　共 %d 分钟　·　逐环节安排</p>' % (esc(span), total),
           '<table class="run"><tr><th>时间</th><th>分钟</th><th>环节与做法</th></tr>']
    for t, m, what, how in rows:
        out.append('<tr><td>%s</td><td>%d′</td><td><b>%s</b><span>%s</span></td></tr>'
                   % (esc(t), m, esc(what), how))
    out.append('</table>')
    return '\n'.join(out)


def linklist(rows):
    return ('<ul class="links">'
            + ''.join('<li><a href="%s">%s</a><em>%s</em></li>' % (u, esc(t), d)
                      for u, t, d in rows)
            + '</ul>')


def build_day(i):
    slug, dn, date, name = DAYS[i]
    b = DAY_BODY[slug]
    title = '%s · %s｜巴渝培训' % (dn, name)
    desc = ('重庆巴渝学校小学部三天教师培训%s（%s）：%s 上午 9:30–11:30、下午 14:00–16:30，'
            '全学科教师，全程大白话。' % (dn, date, name)) + b['tag']
    prev_l = ('<a href="/banyu/%s/">← %s · %s</a>' % (DAYS[i-1][0], DAYS[i-1][1], DAYS[i-1][3])
              if i > 0 else '<a href="/banyu/">← 本栏总目</a>')
    next_l = ('<a href="/banyu/%s/">%s · %s →</a>' % (DAYS[i+1][0], DAYS[i+1][1], DAYS[i+1][3])
              if i + 1 < len(DAYS) else '<a href="/banyu/">回本栏总目 →</a>')
    return '\n'.join([
        head(title, desc, 'https://sdeuniverses.com/banyu/%s/' % slug),
        topbar(slug),
        '<div class="hero"><div class="w">',
        '<div class="kicker">巴渝培训 · %s · %s</div>' % (esc(dn), esc(date)),
        '<h1>%s</h1>' % esc(name),
        '<p class="tag">%s</p>' % esc(b['tag']),
        '<div class="keys">%s</div>' % ''.join('<span>%s</span>' % esc(k) for k in b['keys']),
        '</div></div>',
        '<main><div class="w">',
        '<p class="lead">%s</p>' % b['lead'],
        render_blocks(b['blocks']),
        '<h2>这一天的现场安排</h2>',
        '<div class="bring">%s</div>' % BRING[slug],
        rundown(SESSIONS[slug][0]),
        rundown(SESSIONS[slug][1]),
        '<h3>主讲与巡场的三条纪律</h3>',
        '<ul>%s</ul>' % ''.join('<li>%s</li>' % esc(x) for x in RULES[slug]),
        '<h2>相关文章 · 站内可直接读</h2>',
        linklist(LINKS[slug]),
        '<h2>散会时，你带走什么</h2>',
        '<ul>%s</ul>' % ''.join('<li>%s</li>' % x for x in b['take']),
        '<div class="pager">%s%s</div>' % (prev_l, next_l),
        '</div></main>', FOOT, TAIL])


def build_index():
    title = '巴渝培训 · SDE发生学教育三天教师培训｜SDE Universes'
    desc = ('2026 年 8 月 24–26 日，重庆巴渝学校小学部全体教师三天培训：'
            '第一天 SDE发生学教育入门、第二天 SDE教材发生学、第三天 SDE课堂发生学。'
            '王德生主讲，全学科，全程大白话；线上观摩由付自文承办。')
    cards = []
    for slug, dn, date, name in DAYS:
        cards.append('<a href="/banyu/%s/"><b>%s · %s</b><span>%s</span><em>%s</em></a>'
                     % (slug, esc(dn), esc(date), esc(name),
                        esc(DAY_BODY[slug]['tag'])))
    return '\n'.join([
        head(title, desc, 'https://sdeuniverses.com/banyu/'),
        topbar(''),
        '<div class="hero"><div class="w">',
        '<div class="kicker">重庆巴渝学校小学部 · 全体教师培训</div>',
        '<h1>巴渝培训</h1>',
        '<p class="tag">SDE 发生学教育 · 三天</p>',
        '<div class="keys"><span class="hot">2026年8月24–26日</span>'
        '<span>上午 9:30–11:30</span><span>下午 14:00–16:30</span>'
        '<span>全学科教师</span><span>主讲 王德生</span></div>',
        '</div></div>',
        '<main><div class="w">',
        '<p class="lead">这三天要换的，不是一套教法，是一个判断标准：'
        '<b>一节课上完，凭什么说它真的发生过。</b></p>',
        '<div class="big">我们平常上课，是把结论<b>搬</b>给孩子。'
        '课本上的结论都是被磨平过的——当年是怎么想出来的、'
        '当年差一点走了哪条别的路，全都磨掉了，端上来就像本来就在那里。'
        '孩子接住的是那个光溜溜的成品。<br><br>'
        '所以判断一节课成没成，不看他会不会做题，看一件事：'
        '<b>他心里原来的想法，有没有当场被推翻过一次。</b></div>',
        '<h2>三天，三件事</h2>',
        '<div class="days">%s</div>' % ''.join(cards),
        '<h2>课表</h2>',
        '<table><tr><th>日期</th><th>上午 9:30–11:30</th><th>下午 14:00–16:30</th></tr>'
        '<tr><td><b>8月24日</b><br>第一天</td>'
        '<td>为什么讲清楚了他还是不会<br><span class="slot">上机：ChatSDE</span></td>'
        '<td>一节课是怎么长起来的<br><span class="slot">数学 · 英语两科示范</span></td></tr>'
        '<tr><td><b>8月25日</b><br>第二天</td>'
        '<td>课本是怎么被磨平的<br><span class="slot">三句话还原一页课本</span></td>'
        '<td>各科各做一个概念<br><span class="slot">分组现场拆，互相试讲</span></td></tr>'
        '<tr><td><b>8月26日</b><br>第三天</td>'
        '<td>四种「没发生」长什么样<br><span class="slot">先查哪一种</span></td>'
        '<td>当场备一节下周的真课<br><span class="slot">用语对照表 · 两个读数</span></td></tr>'
        '</table>',
        '<p class="slot">每一天都有<b>逐环节的时间安排</b>（上午 5 段、下午 6 段，'
        '分钟数已排到位）、现场要准备的东西，以及可以先读的站内文章——点开上面三张卡。</p>',
        '<h2>给谁</h2>',
        '<p>现场是重庆巴渝学校小学部<b>全体教师</b>，<b>不分学科</b>——'
        '语文、数学、英语、音乐、美术、体育、科学都在内。</p>',
        '<div class="note">三天<b>一个新名词都不用记</b>。'
        '所有内容都用日常话讲，举的例子都是小学课堂上真会发生的事。'
        '听不懂的地方，当场就该打断。</div>',
        '<h2>线上观摩</h2>',
        '<p>现场是学校的内部教师培训。校外的老师与家长可以线上观摩：'
        '直播与课后讲解由学员<b>付自文</b>（大学日语教师）承办，'
        '他不主讲现场任何一节课。</p>',
        '<table class="terms"><tr><th>费用</th>'
        '<td>三天 <b>300 元</b>。这笔费用用于支持付自文的直播与课后讲解。</td></tr>'
        '<tr><th>课后跟进</th>'
        '<td>三天之外，付自文另有<b>三次线上课</b>，'
        '讲《SDE课堂发生学》的要点与实操。</td></tr>'
        '<tr><th>赠书</th>'
        '<td>赠<b>纸质打印本专著《SDE课堂发生学》</b>一本。</td></tr>'
        '<tr><th>寄送</th>'
        '<td>结课后 <b>30 日内寄出</b>；逾期未寄出，<b>全额退费</b>。</td></tr>'
        '<tr><th>报名</th>'
        '<td><span class="slot">［报名二维码待放置：'
        '把图片放到 public/banyu/qr.jpg，本行改为 &lt;img&gt;］</span></td></tr>'
        '</table>',
        '<h2>先看点什么</h2>',
        '<p>三天里会反复用到站内两处现成的东西：'
        '<a href="/taste/">ChatSDE 与其他智能体</a>（第一天上机用），'
        '<a href="/education/">教育专栏</a>（第一天下午与第二天用）。'
        '两处都不需要提前准备，带着自己最难教的那一个概念来就行。</p>',
        '</div></main>', FOOT, TAIL])


def main():
    if '--dry-run' in sys.argv:
        print('巴渝培训：总目 1 页 ＋ 子频道 %d 页' % len(DAYS))
        return
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(build_index())
    for i, (slug, dn, date, name) in enumerate(DAYS):
        d = os.path.join(OUT, slug)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(build_day(i))
    print('已写 %d 页 →' % (len(DAYS) + 1), OUT)


if __name__ == '__main__':
    main()
