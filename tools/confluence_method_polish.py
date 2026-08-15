# -*- coding: utf-8 -*-
"""「通融创新法」频道的打磨与完善（第三刀）。

上一刀只把文章挪进来、开了频道。这一刀把链路做成双向闭合：
  1. 三篇外链方法论长文各加一条回链横幅（→ /confluence/#c9 与本篇）
  2. 本篇文末加「本频道另外三篇」的导航
  3. /confluence/index.html 壳页的「最新发布」框与 meta 改成新频道
  4. 首页「学科通融」板块加一行频道入口，并校掉「五 十 二 篇」那个陈旧字样
  5. /paradigm/ 栏目页的说明里加一句：这套工序写在哪儿
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "public"
CH = "/confluence/#c9"
ART = "/confluence/confluence-method/"

BANNER = ('<div style="max-width:820px;margin:20px auto 0;padding:13px 20px;'
          'border-left:3px solid #9e3d2c;background:rgba(158,61,44,.06);'
          'font-size:14.5px;line-height:1.85;color:#3a352c">'
          '<b>方法论频道</b> · 本篇同时收录于「学科通融 · '
          f'<a href="{CH}" style="color:#9e3d2c;font-weight:700">通融创新法</a>'
          '」——该频道收全站讲这套工序的文章，含'
          f'<a href="{ART}" style="color:#9e3d2c;font-weight:700">《SDE 多学科通融创新法》</a>'
          '（用厨房剩菜、旧衣服与杂物抽屉三个日常案例把全套工序走一遍）。</div>\n')

BACKLINKS = [
    ("column/innovation-iq-intro/index.html", '<div class="modes">'),
    ("column/ontology-grid/innovation-iq-5d/index.html", '<main class="wrap">'),
    ("column/thought-innovation-agent/index.html", '<div class="modes">'),
]

SIBS = [
    ("/column/ontology-grid/innovation-iq-5d/", "SDE 创新智商五维法评估模式",
     "评分口径的完整版：五维怎么打、两条硬阈值，以及「创新智商是文本与参照文库之间的关系」那条口径"
     "——它正是本文第九章那道工序存在的理由。"),
    ("/column/innovation-iq-intro/", "SDE 创新智商评估入门",
     "上一篇的入门版：五个维度逐维给标尺与提升路径。本文第十二章说的「唯一的瓶颈是 I」，"
     "在那里能看到它是怎么从五维的定义里长出来的。"),
    ("/column/thought-innovation-agent/", "SDE 思想创新智能体的工程原理",
     "本文讲一个人怎么跑这套工序，那一篇讲怎么把它装成机器：三相链、冻结态诊断、"
     "D 维度传动与仪表盘。站上那台学科通融机就是按那张图纸做的。"),
]


def add_backlinks():
    for rel, anchor in BACKLINKS:
        f = PUB / rel
        t = f.read_text(encoding="utf-8")
        assert "通融创新法" not in t, f"{rel} 已经有回链了"
        assert t.count(anchor) == 1, (rel, anchor, t.count(anchor))
        t = t.replace(anchor, BANNER + anchor, 1)
        f.write_text(t, encoding="utf-8")
        print("  回链：", rel)


def add_sibling_nav():
    f = PUB / "confluence" / "confluence-method" / "index.html"
    t = f.read_text(encoding="utf-8")
    assert "本频道另外三篇" not in t
    ones = "".join(
        f'<a class="one" href="{u}"><div class="k">通融创新法 · 站内长文</div>'
        f'<div class="t">{ti}</div><div class="g">{g}</div></a>' for u, ti, g in SIBS)
    block = ('<div class="src"><div class="sl">本频道另外三篇</div>'
             '<p class="sd">「通融创新法」频道收的是讲这套方法本身的文章。'
             '本篇讲工序，另外三篇分别讲怎么给产出打分、怎么入门那把尺子，以及怎么把整条工序装成机器。'
             f'<a href="{CH}">看频道全部篇目 →</a></p>' + ones + '</div>\n')
    a = '<div class="endbox">'
    assert t.count(a) == 1
    t = t.replace(a, block + a, 1)
    f.write_text(t, encoding="utf-8")
    print("  文章页：已加「本频道另外三篇」")


def fix_confluence_shell():
    f = PUB / "confluence" / "index.html"
    t = f.read_text(encoding="utf-8")
    a = ('  <strong>最新发布 · 之九十四至之九十八 · 新开「权力」频道</strong><br>\n'
         '  <a href="/confluence/preset-site/">《先备点·恒项·让段·原封·应答级数》五篇同发，'
         '与已发《隔账》同属权力频道</a><br>\n'
         '  作者：王德生 ＋ Claude\n')
    assert t.count(a) == 1
    t = t.replace(a, '  <strong>最新发布 · 新开「通融创新法」频道 · 方法论</strong><br>\n'
                     f'  <a href="{ART}">《SDE 多学科通融创新法》——'
                     '从厨房里的一盒剩菜讲起，把本栏所用的整套工序走一遍</a><br>\n'
                     '  作者：王德生 ＋ Claude\n'
                     f'<br><a href="/confluence/preset-site/">上一批：之九十四至之九十八 · 权力频道六篇</a>\n', 1)

    b = ('<meta name="description" content="学科通融：把分属不同学科、彼此冲突的理论体系放在一起碰撞。'
         '新开「权力」频道，六篇同题：隔账、应答级数、恒项、让段、原封、先备点。作者王德生 ＋ Claude。">')
    assert t.count(b) == 1
    t = t.replace(b, '<meta name="description" content="学科通融：把分属不同学科、彼此冲突的理论体系放在一起碰撞。'
                     '九个频道，新开「通融创新法」——收全站讲这套工序的方法论文章，'
                     '含《SDE 多学科通融创新法》。作者王德生 ＋ Claude。">', 1)
    f.write_text(t, encoding="utf-8")
    print("  /confluence/ 壳页：最新发布框与 meta 已更新")


def fix_home_confluence():
    f = PUB / "index.html"
    t = f.read_text(encoding="utf-8")
    a = '新 专 栏 · 王 德 生 ＋ Claude · 五 十 二 篇'
    assert t.count(a) == 1
    t = t.replace(a, '新 专 栏 · 王 德 生 ＋ Claude · 九 个 频 道', 1)

    b = ('<span style="border:1px solid rgba(168,184,136,.5);border-radius:22px;padding:7px 17px;'
         'font-size:13px;color:#DCD8C6">零术语 · 人人读得懂</span></div>\n')
    assert t.count(b) == 1
    t = t.replace(b, b + '<div style="max-width:820px;margin:-10px auto 26px;font-size:15px;'
                         'line-height:1.95;color:#C6D6A6">'
                         f'新开 <a href="{CH}" style="color:#E8F0D8;font-weight:700">'
                         '「通融创新法」频道</a>：这一栏用的是哪一套工序——'
                         f'<a href="{ART}" style="color:#E8F0D8;font-weight:700">'
                         '《SDE 多学科通融创新法》</a>用厨房剩菜、旧衣服与杂物抽屉三个日常案例从头走一遍，'
                         '同频道另收站内三篇讲评分与工程实现的方法论长文。</div>\n', 1)
    f.write_text(t, encoding="utf-8")
    print("  首页学科通融板块：频道入口已加，陈旧篇数字样已校")


def fix_paradigm_lead():
    f = PUB / "paradigm" / "index.html"
    t = f.read_text(encoding="utf-8")
    a = ('<p class="rule">这个专栏由 <b>王德生博士</b>定题、选篇、判方向，'
         '<b>Claude</b> 执行碰撞与成文，因此每篇署<b>王德生 ＋ Claude</b>。')
    assert t.count(a) == 1
    t = t.replace(a, '<p class="rule">这一栏与《学科通融》用的是同一套工序，它写在哪儿：'
                     f'<a href="{ART}">《SDE 多学科通融创新法》</a>'
                     '——用厨房里的一盒剩菜、一件旧衣服与一个杂物抽屉三个日常案例从头走一遍，'
                     f'收在学科通融的<a href="{CH}">「通融创新法」频道</a>。</p>\n' + a, 1)
    f.write_text(t, encoding="utf-8")
    print("  /paradigm/ 栏目页：已加一句指向工序")


def main():
    add_backlinks()
    add_sibling_nav()
    fix_confluence_shell()
    fix_home_confluence()
    fix_paradigm_lead()


if __name__ == "__main__":
    main()
