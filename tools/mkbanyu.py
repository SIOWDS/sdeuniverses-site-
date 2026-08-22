#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mkbanyu.py —— 「巴渝培训」专栏：/banyu/ 总目 ＋ 三个子频道。

  /banyu/        总目：三天是什么、给谁、课表
  /banyu/day1/   第一天 · SDE发生学教育入门
  /banyu/day2/   第二天 · SDE教材发生学
  /banyu/day3/   第三天 · SDE课堂发生学

⚠ 三条纪律（王德生 2026-08-22 定）：
 1. **页面上一个术语都不许留。** 受众是小学全学科教师与在线家长，不是学派内部。
    「显露/差异/纠缠」「光滑化」「回写」「封写」「岔口」一律换成大白话
    （磨平了的成品／心里那本账被改了／上了锁／还没定下来的地方）。
    子频道的标题是他指定的，照留；正文里不再出现。
 2. 专栏页自成一体，不把首页导航整套背进来（与 mkthreeviews.py 同一条）。
 3. **不写报名、不写收费、不写赠书与退费**——王德生 2026-08-22 定：
    这一摊由付自文另走渠道。本栏只放课程内容，不做任何对外承诺。

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
主讲 王德生　·　线上直播与课后讲解 付自文（另行安排）<br>
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
  tag='从发现到发生：为什么这件事非改不可，以及为什么现在才做得到',
  keys=['上午 9:30–11:30', '下午 14:00–16:30', '全学科',
        '工具：SDE 爱思乐园平台 · ChatSDE'],
  lead='第一天不讲新名词。上午把一件事说清楚：我们平常上课，'
       '是<b>把结论搬给孩子</b>；还有另一种上法，是<b>让结论在孩子身上长一次</b>。'
       '这两种上法，孩子学完之后的样子不一样，而且能当堂看出来——'
       '这就是<b>从发现到发生</b>。下午分三科入门：数学、语言、科学，各带一遍。',
  blocks=[
    ('上午 · 9:30–11:30　从发现到发生：教育教学为什么非变不可', [
      ('h3', '一、两种上法'),
      ('p', '老办法只有三个动作：<b>搬过来、讲明白、请你接住</b>。'
            '这三个动作本身没错，错在它们默认了一件事——'
            '知识是一个可以整个端过去的东西。'),
      ('big', '课本上的每一个结论，都是<b>被磨平过</b>的。'
              '当年是怎么想到的、当年差一点走了哪条别的路，都被磨掉了；'
              '端到孩子面前时，它看上去就像<b>本来就在那里</b>。'
              '孩子接住的是那个光溜溜的成品，不是那条路。'),
      ('p', '另一种上法不换教材、不换考试，只换一件事：'
            '<b>把那条被磨掉的路，在课堂上重新走一遍。</b>'
            '走过一遍的孩子和只接住成品的孩子，隔一个星期就分得出来。'),
      ('h3', '二、判断一节课的唯一一把尺'),
      ('big', '不看他会不会做题，看一件事：'
              '<b>他心里原来的想法，有没有当场被推翻过一次。</b>'
              '没有推翻，就是没发生——哪怕全对。'),
      ('card', '小学里最好用的例子',
       '问三年级：1/3 和 1/2 哪个大？有相当一部分孩子会答 1/3 大。'
       '这不是粗心。他心里那本账写的是「3 比 2 大」，'
       '这本账从来没有因为分数被改过。'
       '把正确答案讲一遍，账还是不会改；让他自己撞一次，账才会改。'),
      ('h3', '三、为什么非改不可（三条，一条比一条硬）'),
      ('card d', '第一条：讲清楚了，他还是不会',
       '每位老师都见过——讲得很清楚，例题也做了，换个说法一问就塌。'
       '因为他心里那本旧账<b>一个字都没被改过</b>。'
       '这一条只是眼前的麻烦，还不算最重的。'),
      ('card d', '第二条：补课也没用',
       '有些孩子不是没听懂。他心里那条规矩<b>已经上了锁</b>——'
       '「这东西本来就是这样，不用想」。锁一旦上了，'
       '你把当年那条路原样还给他，他也走不进去。'
       '所以我们花在补课上的力气，很大一部分是打在锁上。'
       '这一条解释了为什么加课时不管用。'),
      ('card d', '第三条：AI 已经进教室了',
       '孩子随时能拿到一个比我们讲得更清楚、磨得更平的答案。'
       '也就是说，<b>「讲得清楚」这件本事，正在迅速地不值钱</b>。'
       '更麻烦的是，答案来得越快，孩子自己想到一次的机会就越少，'
       '想错了被顶回来一次的机会也越少——这两样正是判断力长出来的地方。'
       '老师剩下的、AI 拿不走的位置只有一个：'
       '<b>守住那个还没定下来的地方，不让它提前关上。</b>'),
      ('h3', '四、为什么现在才做得到'),
      ('p', '让每个孩子自己走一遍岔路，这件事从来不是没人想到，'
            '是<b>从来负担不起</b>：一个老师、四十个孩子、四十分钟，'
            '陪不起四十条不一样的弯路。'),
      ('big', 'AI 第一次改变了这笔账。<b>但它必须被配反过来用。</b><br><br>'
              'AI 天生是「提前给答案」的机器。原样搬进课堂，'
              '它就是一台更快、更全、更贴心的老办法机器。'
              '要用它，就得让它当<b>出难题的那一方</b>——'
              '专门给反例，专门问「那不这样行不行」，专门把孩子的说法顶回去。'
              '这一条配错，后面两天全都白讲。'),
      ('h3', '五、上机：SDE 爱思乐园平台 · ChatSDE'),
      ('p', '每位老师现场打开平台上的 <b>ChatSDE</b>，'
            '拿<b>自己学科里最难教的那一个概念</b>试一次。'
            '注意提问的方向：<b>不要它给答案</b>，'
            '要它把这个概念<b>当年还有哪些别的走法、'
            '哪些说法后来被推翻了</b>摆出来。'),
      ('note', '一节课的备课成本，从这里开始变得便宜。'
               '上午散会前，每人手上要有一条自己学科的岔路。'),
    ]),
    ('下午 · 14:00–16:30　三科入门：数学 · 语言 · 科学', [
      ('p', '下午从「说明白」转到「做一遍」。三科各带一遍——'
            '不是因为只有这三科能用，是因为这三科各自卡住的地方不一样，'
            '合起来正好把全学科都覆盖到。'),
      ('h3', '共用的五个动作，顺序不能换'),
      ('ol', ['先找到一个<b>对不上的地方</b>——孩子已有的想法在这里说不通了；',
              '让他<b>先摆出一个说法</b>，哪怕是错的；',
              '带他<b>走一遍</b>，看这个说法能撑到哪里；',
              '<b>落到具体东西上</b>：小棒、纸条、撕下来的三个角；',
              '走完之后，<b>又露出一个新的对不上</b>——下一节课从这里开始。']),
      ('note', '第四步是最常被跳过的一步。跳过它，前三步会变成一场热闹的活动课：'
               '孩子很投入，账本没动。'),
      ('card', 'SDE 数学 · 入门引导',
       '数学最容易被当成一堆规定：这么写就对，那么写就错。'
       '而每一条规定当年都是被<b>选</b>出来的。'
       '入门用这几个：<b>数</b>（为什么要有它）、<b>位值</b>（为什么要进位）、'
       '<b>等号</b>（它是「算出来是」还是「两边一样」）、'
       '<b>分数</b>（1/3 和 1/2 那一撞）、'
       '<b>三角形内角和</b>（撕下三个角拼成一条直线）。'
       '动作都是老动作，变的是次序：<b>先让他押一个说法，再动手。</b>'),
      ('card e', 'SDE 语言教学 · 入门引导',
       '语言不是背会的，是<b>用会的</b>。'
       '这一科最要改的一个习惯：<b>孩子一说错就立刻纠正</b>。'
       '错的那一句，往往正是他心里那本账露出来的唯一一次机会——'
       '当场抹掉，账就看不见了，也就改不了。'
       '入门的做法：先不给标准说法，让他把想说的意思'
       '<b>用手上现有的词硬凑一遍</b>，凑不出来的地方就是今天要教的地方。'),
      ('card d', 'SDE 科学教学 · 入门引导',
       '科学课最容易变成背结论：这个是对的，记住。'
       '可科学里的每一条结论，当年都是踩着<b>一堆被推翻的说法</b>站起来的，'
       '而那些被推翻的说法，恰恰跟孩子现在心里想的一模一样。'
       '入门的做法：做实验之前，<b>先让全班押注</b>——'
       '你猜会怎么样，为什么。押完再做。'
       '<b>押错的那些孩子，才是这节课真正教得动的人。</b>'),
      ('h3', '这一节要守住的那件事'),
      ('big', '那个<b>还没定下来的地方</b>，是这节课最贵的东西。'
              '老师最大的诱惑，是在孩子卡住的那三十秒里把答案递过去。'
              '递过去，这节课就结束了。'),
    ]),
  ],
  take=['一把当堂能用的尺：他心里的账被改了没有',
        '三条「为什么非改不可」，能讲给别人听',
        '一条自己学科的岔路，是在 ChatSDE 上找出来的',
        '数学 · 语言 · 科学三科各一个可以下周就上的入门做法'],
),

'day2': dict(
  tag='先看已经拆好的，再动手拆自己那一科的',
  keys=['上午 9:30–11:30', '下午 14:00–16:30',
        '上午：数学 · ChatSDE', '下午：语言 · ChatJohn · 科学'],
  lead='第二天动手做教材。上午<b>数学</b>：先把已经拆好的小学数学发生内容整套看一遍，'
       '再带大家用 <b>ChatSDE</b> 自己发明还没拆过的那些主题。'
       '下午两科：<b>语言</b>进 <b>ChatJohn</b>，把语义、语序、语法逐层拆开；'
       '最后是<b>科学</b>。',
  blocks=[
    ('上午 · 9:30–11:30　SDE 数学教材发生学', [
      ('h3', '一、先看已经做好的：小学数学的十一处'),
      ('p', '不从方法讲起，从成品讲起。小学数学里最要紧的那些概念，'
            '已经一处一处拆过了——每一处都写清楚了三件事：'
            '<b>孩子心里原来那本账写的是什么</b>、'
            '<b>当年那条被磨掉的路是什么</b>、'
            '<b>课堂上靠哪一个动作让他撞一次</b>。'),
      ('table', [['已经拆好的', '孩子心里原来那本账'],
                 ['数', '「数就是数出来的那个字」'],
                 ['位值', '「数字一个一个往上排」'],
                 ['加法交换律', '「这是规定」'],
                 ['乘法', '「乘法就是加得快一点」'],
                 ['分数', '「3 比 2 大，所以 1/3 比 1/2 大」'],
                 ['等号', '「等号后面写答案」'],
                 ['三角形内角和', '「书上说是 180 度」'],
                 ['退位减 · 平行四边形面积 · 小数 · 平均数', '（四处延伸，同样拆到底）']]),
      ('note', '这一整套就是这三天的底稿。上午前半场把它当范本看：'
               '<b>一份「发生内容」长什么样，看完就有数了。</b>'),
      ('h3', '二、然后自己发明：小学数学还有一大半没拆'),
      ('p', '拆好的只有十一处，小学数学远不止这些。'
            '时间与钟面、周长与面积、角、倍数与因数、'
            '统计图、比与比例、字母表示数、圆、负数……'
            '<b>这一段就是带着大家，用 ChatSDE 把它们一个个做出来。</b>'),
      ('card', '给 ChatSDE 三样，要它交回三样',
       '<b>给它：</b>①这个概念　②孩子最常犯的那一个错　③课本上它出现的那一句原话。<br>'
       '<b>要它：</b>①当年还有过哪些别的走法、哪一种后来被淘汰了　'
       '②能让孩子当场撞上的<b>一件具体东西</b>（能拿在手上的，不是一段话）　'
       '③一句能开锁的问话。<br>'
       '⚠ 不要问它「这个概念怎么教」——那样它给的是更漂亮的老办法。'),
      ('big', '产出的验收只有一条：<b>你做出来的这份东西，'
              '能不能把昨天那张四行卡填满。</b>'
              '填不满，说明还停在教案，没到发生内容。'),
      ('note', '上午散会时，每位数学老师手上要有<b>至少一个自己做出来的新主题</b>。'
               '别科老师同样上机，只是换成自己那一科的概念——做法一模一样。'),
    ]),
    ('下午 · 14:00–16:30　SDE 语言发生学教材 · ChatJohn ／ SDE 科学发生学', [
      ('h3', '一、语言这一科，卡在三层上'),
      ('p', '语言不是背会的，是用会的。可教材把它写成了三摞要记的东西：'
            '词的意思、句子的次序、语法的规矩。'
            '这三摞每一摞当年都是<b>被用出来的</b>，不是被定下来的。'),
      ('table', [['层', '教材通常怎么给', '它当年其实是怎么来的'],
                 ['语义（意思）', '一个词配一条解释，背下来',
                  '意思是用出来的。同一句「你真行」，可以是夸，也可以是骂——'
                  '决定它是哪一个的，从来不在词典里'],
                 ['语序（次序）', '「就是这么排的」',
                  '次序是被逼出来的：不这么排就说不清谁对谁做了什么。'
                  '换一种排法会怎样，可以当场试'],
                 ['语法（规矩）', '先给规矩，再做练习',
                  '语法是<b>事后总结出来的账</b>，不是事先定下的法。'
                  '孩子说错的那一句，往往正踩在这本账还没盖住的地方']]),
      ('h3', '二、上机：ChatJohn'),
      ('p', '语言这一科有专门的一台——<b>ChatJohn</b>，'
            '在语言分站上（<a href="https://lang.sdeuniverses.com/chatjohn/" '
            'target="_blank" rel="noopener">lang.sdeuniverses.com/chatjohn</a>）。'
            '它读的是语言这一路的材料，不跟主站混。'),
      ('card e', '带一句真错句进去，别带概念',
       '拿<b>本班孩子上周真说错、真写错的一句</b>——原话，别改。'
       '问它两件事：<b>这一句卡在哪一层</b>（意思、次序、还是规矩）；'
       '<b>这一层当年是怎么被用出来的</b>。<br>'
       '拿到答案之后，自己再多做一步：'
       '把这一句<b>拿回去在课堂上再用一次</b>，'
       '让说错的那个孩子自己听出不对——这一步 AI 替不了。'),
      ('h3', '三、SDE 科学发生学'),
      ('p', '科学教材是最容易只剩结论的一科：一课书翻下来，'
            '全是「这个是对的，记住」。'
            '可科学里的每一条结论，当年都踩着<b>一堆被推翻的说法</b>站起来——'
            '而那些被推翻的说法，恰恰跟孩子现在心里想的一模一样。'),
      ('big', '所以科学教材的还原动作只有一个：'
              '<b>把当年被推翻的那个说法找回来，摆在课的开头。</b>'
              '然后让全班先押注——你猜会怎么样，为什么。押完再做。'),
      ('p', '押错的那些孩子，才是这节课真正教得动的人。'
            '押对的那些，要多问一句「你怎么知道的」——'
            '很多时候答案是「书上写的」，那就等于没押。'),
      ('note', '科学组要提前定一个<b>结果出人意料的小实验</b>，下午当场做。'
               '越是「明明应该是这样、结果不是」的越好。'),
    ]),
  ],
  take=['一整套已经拆好的小学数学发生内容，直接能用',
        '一个自己用 ChatSDE 做出来的新主题',
        '语言三层（意思 · 次序 · 规矩）各自的还原做法，以及 ChatJohn 会用了',
        '科学课的一个动作：把被推翻的说法找回来，先押注再做'],
),

'day3': dict(
  tag='把前两天合成一节课：先看一节，再改一节，然后带走两个数',
  keys=['上午 9:30–11:30', '下午 14:00–16:30',
        '第三天不上机', '每人带走一节改好的真课'],
  lead='第三天回到四十分钟本身。前两天讲的是想法和教材，'
       '第三天讲的是<b>人站在教室里的那四十分钟</b>：'
       '什么时候该说话，什么时候必须闭嘴，怎么当堂知道这节课成了没有。',
  blocks=[
    ('上午 · 9:30–11:30　先看一节课，再拆开它', [
      ('note', '<b>第三天不上机。</b>前两天开了两台机器，第三天一台都不开——'
               '因为课堂上那四十分钟里没有机器，只有你和一屋子孩子。'
               '前两天做出来的东西，今天要靠人送出去。'),
      ('h3', '零、先上一节课给你们看'),
      ('p', '不先讲要点。开场就上一节<b>真课</b>，二十来分钟，'
            '全场当学生坐着上。<b>事先不说这节课要看什么。</b>'
            '这与昨天那半天同一个办法——昨天先看的是做好的教材，'
            '今天先看的是上完的课。'),
      ('h3', '一、当场解剖刚才那一节：只有三个位置要紧'),
      ('table', [['位置', '这一刻要做的', '刚才那一节在这里是怎么做的'],
                 ['开口之前', '先让他押一个说法——哪怕是错的',
                  '回想：老师第一句话是给答案，还是要你先押一个？'],
                 ['卡住的那三十秒', '什么都不做',
                  '回想：全场卡住的时候，安静了几秒？谁先受不了？'],
                 ['下课之前', '问那一问（见下午）',
                  '回想：这节课收尾时，问的是会不会做，还是问你被推翻了什么？']]),
      ('p', '其余的三十几分钟怎么安排，各人有各人的办法，不必统一。'
            '<b>这三个位置错了，别的再好也白搭。</b>'),
      ('h3', '二、四种「没发生」，长什么样'),
      ('p', '一节课没成，样子不止一种。分不清是哪一种，补救就会补错地方——'
            '而补错地方，比不补更费时间。'),
      ('table', [['样子', '实际发生了什么', '该怎么补'],
                 ['过两天全忘了', '当时是记住了，没跟他自己的东西接上', '换一个他自己的例子重来'],
                 ['太顺了，一路对到底', '中间没有一处卡住，等于没走', '故意做一道会撞墙的题'],
                 ['讲得头头是道，一换说法就塌', '话是圆的，账没改', '换个场合、换个说法再问一遍'],
                 ['怎么讲都进不去', '心里那条规矩上了锁', '先开锁（第二天那三句话），再讲']]),
      ('big', '次序上有一条硬规矩：<b>先查是不是上了锁。</b>'
              '锁着的时候，另外三种补救全部无效——'
              '这是我们最常浪费掉的一整节课。'),
      ('p', '这一段拿<b>昨天各组的任务卡</b>现场判：'
            '你们那一课上砸的时候，是四种里的哪一种？'),
      ('h3', '三、三十秒忍耐练习'),
      ('card d', '两人一组，规则只有一条',
       '一人扮学生，当场卡住；一人扮老师。'
       '<b>不许给答案，也不许换题。</b>计时三十秒，做完交换。<br>'
       '全场只问一句：<b>你是在第几秒开口的？</b><br>'
       '这三十秒是这节课最贵的三十秒，也是全场最难做到的一件事——'
       '难在它要求老师什么都不做，而所有的职业本能都在催你做点什么。'),
    ]),
    ('下午 · 14:00–16:30　改一节自己的真课，然后带走两个数', [
      ('h3', '一、课堂用语：不要说 / 要说'),
      ('table', [['不要说', '改成'],
                 ['「记住，就是这样。」', '「如果不这样，会怎么样？」'],
                 ['「对，很好，下一题。」', '「你是怎么想到的？说给他听听。」'],
                 ['「这个先记下来，以后就懂了。」', '「先别记。你现在的想法是什么？」'],
                 ['「错了，我再讲一遍。」', '「按你的想法往下走，走到哪儿走不动了？」'],
                 ['「时间不够了，答案是……」', '「这个地方我们先不定下来，明天接着卡。」']]),
      ('p', '右边这五句不是话术。它们的共同点是：'
            '<b>把说话的权利还回去</b>，并且都不需要老师先知道答案。'),
      ('h3', '二、改自己下周那节真课，只改三处'),
      ('ol', ['<b>哪一刻让他卡住</b>——整节课至少要有一处；',
              '<b>卡住的时候你说哪一句</b>——从上面那张表里挑，写下来；',
              '<b>下课前那一问怎么问</b>——照抄也行。']),
      ('note', '不重写教案，不做课件，不换环节。'
               '只改这三处——<b>改得动的东西越少，回去越用得上。</b>'),
      ('h3', '三、两两试讲，只评两件事'),
      ('big', '听的人只回答两句：<b>那个还没定下来的地方，你让它开着了多久；</b>'
              '<b>他卡住的时候，你有没有把答案递过去。</b><br>'
              '不评教态、不评环节、不评课件——越界的当场打断。'),
      ('h3', '四、两个数，怎么带回去'),
      ('ul', ['<b>那个还没定下来的地方，你让它开着多久。</b>'
              '不用问学生，自己就能记。整节课一处都没开着，这节课就是老办法。',
              '<b>下课前的那一问。</b>不问会不会做，问：'
              '「你今天有没有哪个原来的想法被推翻了？是哪一个？」'
              '答得上来的人数，就是这节课的成绩。']),
      ('big', '这两个数最要紧的地方在于：<b>它们不需要考试，也不需要等。</b>'
              '当堂就有，每周记一次，一个学期就是一条看得见的曲线。'),
      ('h3', '五、开学以后：怎么不靠热情把它接着做下去'),
      ('p', '三天散会，热情大概能撑两周。要它撑一个学期，只有一个办法：'
            '<b>把这两个数放进教研组本来就在做的事里</b>，'
            '不新增会议、不新增表格。'),
      ('card e', '两处最省力的接口',
       '<b>听课单加两栏</b>：把原来那些评教态、评环节的格子留着不动，'
       '末尾加「岔口开了多久」「那一问几人答得上来」两栏。'
       '一学期下来，谁的曲线在动，一目了然。<br>'
       '<b>教研组每周挑一节课当众判一次</b>：不判好坏，只判'
       '「这一节属于四种里的哪一种」。判错不要紧，'
       '<b>要紧的是全组开始用同一把尺说话。</b>'),
      ('h3', '六、这一天之后'),
      ('p', '第三天讲的内容，会和付自文老师一起整理成专著'
            '<b>《SDE课堂发生学》</b>。'
            '此外付自文另有三次线上课，讲这一天的要点与实操。'),
    ]),
  ],
  take=['一节课里真正要紧的那三个位置',
        '四种「没发生」的分辨法，以及先查哪一种',
        '一张课堂用语对照表，明天就能用',
        '一节改好的真课——只改了三处，回去就能上',
        '两个当堂能读的数，和把它们放进教研组的两个接口'],
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
            elif kind.split()[0] == 'card':
                # 'card'／'card d'／'card e' —— 后一段是左边那条竖线的颜色。
                # ⚠ 这里以前写死了 kind == 'card'，带修饰的卡片被**静默丢掉**，
                #    页面照常构建、内容少了四块。凡新增 kind，务必在这里同步。
                out.append('<div class="%s"><h3>%s</h3><p>%s</p></div>'
                           % (esc(kind), esc(it[1]), it[2]))
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
            '王德生主讲，全学科，全程大白话。')
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
        '<td>从发现到发生：教育教学为什么非变不可'
        '<br><span class="slot">上机：SDE 爱思乐园平台 · ChatSDE</span></td>'
        '<td>三科入门引导'
        '<br><span class="slot">SDE数学 · SDE语言教学 · SDE科学教学</span></td></tr>'
        '<tr><td><b>8月25日</b><br>第二天</td>'
        '<td>SDE 数学教材发生学'
        '<br><span class="slot">先看已拆好的，再用 ChatSDE 发明新的</span></td>'
        '<td>SDE 语言发生学教材 ／ SDE 科学发生学'
        '<br><span class="slot">ChatJohn：语义 · 语序 · 语法</span></td></tr>'
        '<tr><td><b>8月26日</b><br>第三天</td>'
        '<td>先上一节课给你们看，再拆开它'
        '<br><span class="slot">三个位置 · 四种「没发生」· 三十秒忍耐</span></td>'
        '<td>改一节自己的真课，带走两个数'
        '<br><span class="slot">只改三处 · 试讲只评两件事 · 开学后怎么接着做</span></td></tr>'
        '</table>',
        '<p class="slot">每一天都有<b>逐环节的时间安排</b>（上午 5 段、下午 6 段，'
        '分钟数已排到位）、现场要准备的东西，以及可以先读的站内文章——点开上面三张卡。</p>',
        '<h2>给谁</h2>',
        '<p>现场是重庆巴渝学校小学部<b>全体教师</b>，<b>不分学科</b>——'
        '语文、数学、英语、音乐、美术、体育、科学都在内。</p>',
        '<div class="note">三天<b>一个新名词都不用记</b>。'
        '所有内容都用日常话讲，举的例子都是小学课堂上真会发生的事。'
        '听不懂的地方，当场就该打断。</div>',
        # ⚠ 王德生 2026-08-22 定：**报名与线上观摩一概不写在站上**，
        #   由付自文另走渠道负责。原来这里有一张收费/赠书/退费/二维码的表，已整块撤掉。
        #   连带好处：先前挂着的两条风险（对外付费直播需学校书面同意、
        #   收款方与赠书方不是同一人）在本站这一侧不再成立——本栏不做任何承诺。
        #   要恢复请先问过他，别自作主张把条款搬回来。
        '<h2>线上观摩</h2>',
        '<p>现场是重庆巴渝学校小学部的内部教师培训。'
        '线上观摩与报名<b>不在本站办理</b>，由学员<b>付自文</b>另行安排——'
        '他负责三天的线上直播与课后讲解，不主讲现场任何一节课。'
        '本栏只放课程内容。</p>',
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
