# -*- coding: utf-8 -*-
"""把《SDE 多学科通融创新法》挪进「学科通融」，并给该栏新开频道 c9「通融创新法」。

用户裁定：这篇是学科通融栏目的**特殊文章**（方法论），不是典范文也不是碰撞产物；
站内所有讲这套方法的文章，一律挂到这个子频道下。

本脚本做六件事：
  1. 用 return-leg 骨架在 /confluence/confluence-method/ 建页（网页长读单模）
  2. base.html 开频道 c9（chip／篇数字样／grid 列数／CHJS D 表／chdesc 五处）
  3. base.html 加四张 data-ch="c9" 卡（本篇 ＋ 三篇站内既有方法论外链篇）
  4. /paradigm/ 撤掉头条卡，旧 URL 留一页重定向（发出去一小时，不留死链）
  5. 首页两处（每日必读顶卡、今日更新 feed）改指新址并改称学科通融
  6. 全程 assert 锚点唯一
"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CF = ROOT / "public" / "confluence"
PZ = ROOT / "public" / "paradigm"
SKEL = CF / "return-leg" / "index.html"
SRC = ROOT / "tools" / "paradigm_method_body.txt"
SLUG = "confluence-method"
PUBDATE = "2026年8月16日"
BYLINE = "王德生 ＋ Claude"

TITLE = "SDE 多学科通融创新法"
SUB = "从 0 到 1 不是灵感，是一门可以重复的手艺——从厨房里的一盒剩菜讲起"
SERIES = "学 科 通 融 · 通 融 创 新 法 · 方 法 论 特 稿"

DECK = ("周三剩下的半锅红烧肉，周六还在冰箱里。做饭的人说菜端上桌就算做完了，"
        "排班的人说要等它被吃掉才算走完，管冰箱的人说它还占着格子就没结束——"
        "三个人吵不出结果，因为他们不是三个观点，是三个**算数的标准**。"
        "本文用这件事把本栏所用的那套工序从头走到尾：不看三家吵什么，看他们**不吵什么**——"
        "那句三个人都会说「这还用说吗」的话才是地基；而推翻它的材料，"
        "就在做饭的人自己手里（他故意多做，那一刻已经把一部分指派给了一顿还不存在的饭）。"
        "地基一塌，一个三家账本上都没有字段的东西露了出来。"
        "全文另有旧衣服与杂物抽屉两个案例走完另外两种题型，"
        "并交出五道闸、发生链五步、可清点的读数、敌意拓宽的五个方向、"
        "一条必须把不利结果写进正文的真跑，以及六类风险与五种伪形。")

KEYWORDS = "二阶碰撞　位置三分　共有前提　新存在物　可清点读数　敌意拓宽　真跑一条"

INTRO_NOTE = ("本篇是**方法论特稿**，不是碰撞产物。本栏其余各篇都是这套工序跑出来的东西——"
              "三家分属不同学科、在同一个问题上互相排斥，撞出一条任一家单独看不到的判断；"
              "本篇讲的是**跑那一趟的工序本身**，因此必须把术语摆到台面上。"
              "读完这一篇，再回头读本栏任何一篇，可以逐段对出它走的是哪一道工序。")

USES = [
    ("学科通融 · 站外三家碰撞",
     "整栏九十余篇：三家来源全部给出可点开核对的原始出处",
     "/confluence/",
     "本篇第六章那两把选源的尺子（位置三分、语汇族距离），在这一栏每一篇的开头都被走过一遍；"
     "撞不起来就换源，不许照跑。"),
    ("每日必读 · 站内三篇碰撞",
     "谁也没拿到——一份还没长成的东西被提前结清之后，账面完好无损",
     "/paradigm/nobody-held-it/",
     "第四章说的「共有前提」在那一篇里是：一样东西不在你手里就一定在别人手里。"
     "三篇源共享它，而账面为什么是平的这件事把它推翻了。"),
    ("站内工具 · 自己跑一次",
     "SDE 学科通融机：十八格工序逐格可见、可重跑、可手改",
     "/taste/confluence/",
     "本篇写的十七道工序，那台机器按十八格排开；附录 A 的清单可以拿去逐格对照。"),
]

# 频道 c9 里除本篇之外的三张外链卡（站内既有的方法论长文）
EXTRA_CARDS = [
    dict(href="/column/ontology-grid/innovation-iq-5d/",
         n="通融创新法 · 评分口径 · 站内长文",
         title="SDE 创新智商五维法评估模式",
         sub="三维两闸、全球文库口径与三个完整测评案例",
         hk="《通融创新法》第十二章用的那把尺子，完整版在这里：五个维度（结构精确度 S／差异锐度 D／"
            "纠缠深度 E／不可还原性 I／可证伪性 F）各自量什么、怎么打、加权怎么算，"
            "以及两条硬阈值。它写死了一条最要紧的口径——创新智商是**文本与参照文库之间的关系**，"
            "不是文本自己的属性，所以评分必须以全球最新文库为标准，收窄文库只能作对照组。"
            "这正是为什么「敌意拓宽」那一道工序是唯一能直接抬高上限的一道。",
         meta="约 2.0 万字 · 作者 王德生 · 含三个完整测评案例"),
    dict(href="/column/innovation-iq-intro/",
         n="通融创新法 · 评分入门 · 站内长文",
         title="SDE 创新智商评估入门",
         sub="五维度评估的完整解释，逐维给出评分标尺与提升路径",
         hk="上一篇的入门版：把五个维度拆开逐维解释，各自给一把标尺和一条提升路径，"
            "并论证它与科学创新评估同构。先读这一篇再读《五维法评估模式》会省力得多；"
            "而《通融创新法》第十二章讲的「唯一的瓶颈是 I」，在这里能看到它是怎么从五维的定义里长出来的。",
         meta="约 1.4 万字 · 十二章 · 作者 王德生"),
    dict(href="/column/thought-innovation-agent/",
         n="通融创新法 · 工程实现 · 站内长文",
         title="SDE 思想创新智能体的工程原理（增订版）",
         sub="把这套工序装进一条人—机器复合的知识发生产线",
         hk="《通融创新法》讲的是一个人怎么跑这套工序；这一篇讲的是怎么把它装成机器："
            "理念界知识发生的三相链、大模型的三维冻结态诊断、三元素补全、"
            "D 维度完整传动、三界回程与仪表盘。站上那台学科通融机就是按这张图纸做的。",
         meta="约 1.5 万字 · 作者 王德生 ＋ Claude"),
]

CH_ID = "c9"
CH_NAME = "通融创新法"
CH_DESC = ("这一栏用的是哪一套工序：位置三分、共有前提、新存在物、可清点的读数、"
           "敌意拓宽与真跑一条，以及给产出打分的那把尺子")


def strongify(s):
    s = html.escape(s, quote=False)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)


def md_to_html(md):
    out, para, toc, n = [], [], [], 0
    rows, qbuf = [], []

    def flush():
        if para:
            out.append("<p>" + strongify(" ".join(para)) + "</p>")
            para.clear()

    def flush_quote():
        if qbuf:
            out.append("<blockquote>" + "<br><br>".join(qbuf) + "</blockquote>")
            qbuf.clear()

    def flush_table():
        if not rows:
            return
        head, body = rows[0], rows[2:]
        trs = ["<tr>" + "".join(f"<th>{strongify(c)}</th>" for c in head) + "</tr>"]
        for r in body:
            trs.append("<tr>" + "".join(f"<td>{strongify(c)}</td>" for c in r) + "</tr>")
        out.append('<table class="tbl">' + "".join(trs) + "</table>")
        rows.clear()

    for raw in md.splitlines():
        line = raw.rstrip()
        if line.strip().startswith("|"):
            flush(); flush_quote()
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
            continue
        flush_table()
        if line.strip() == ">":
            continue
        if not line.strip():
            flush(); flush_quote(); continue
        if line.strip() == "---":
            flush(); flush_quote(); out.append("<hr>"); continue
        m = re.match(r"^(#{2,4})\s+(.*)$", line)
        if m:
            flush(); flush_quote()
            lvl, txt = len(m.group(1)), m.group(2).strip()
            if lvl == 2:
                n += 1
                out.append(f'<h2 id="s{n}">{strongify(txt)}</h2>')
                toc.append((f"s{n}", re.sub(r"\*\*", "", txt)))
            else:
                out.append(f"<h{lvl}>{strongify(txt)}</h{lvl}>")
            continue
        if line.strip().startswith("- "):
            flush(); flush_quote()
            out.append("<p>· " + strongify(line.strip()[2:]) + "</p>")
            continue
        if line.strip().startswith("> "):
            flush()
            qbuf.append(strongify(line.strip()[2:]))
            continue
        flush_quote()
        para.append(line.strip())
    flush(); flush_quote(); flush_table()
    return "".join(out), toc


def build_page(body, toc, wan):
    sk = SKEL.read_text(encoding="utf-8")
    head = sk[:sk.index('<div id="pbar"></div>')]
    tail = sk[sk.index('<button id="totop"'):]

    head = re.sub(r"<title>.*?</title>",
                  f"<title>{TITLE}——{SUB} · 学科通融 | SDE Universes</title>", head, flags=re.S)
    head = re.sub(r'(<meta name="description" content=")[^"]*(")',
                  lambda m: m.group(1) + html.escape(DECK.replace("**", "")[:190], quote=True) + m.group(2),
                  head, count=1)

    links = "".join(f'<a href="#{i}">{html.escape(x)}</a>' for i, x in toc)
    ones = "".join(
        f'<a class="one" href="{u}"><div class="k">{html.escape(k)}</div>'
        f'<div class="t">{html.escape(ti)}</div><div class="g">{strongify(g)}</div></a>'
        for k, ti, u, g in USES)

    page = (head
            + '<div id="pbar"></div>\n'
            + '<div class="readbar">\n'
            '  <a class="nav-back" href="/confluence/">‹ 学科通融</a>\n'
            '  <div class="rb-modes"><span class="rb-btn cur">📖 网页长读</span>\n'
            '  <a class="rb-btn" href="/taste/confluence/">⚔ 自己跑一次</a></div>\n'
            '</div>\n'
            + '<header class="art">\n'
            f'  <div class="art-series">{SERIES}</div>\n'
            f'  <h1 class="art-title">{TITLE}</h1>\n'
            f'  <div class="art-sub">{SUB}</div>\n'
            f'  <div class="art-meta">{BYLINE} 著 · 约 {wan} 万字 · 网页长读 · 发表于{PUBDATE}</div>\n'
            '</header>\n'
            + '<div class="wrap">\n'
            f'<div class="deck">{strongify(DECK)}</div>\n'
            f'<p class="kwline"><b>关键词</b>：{KEYWORDS}</p>\n'
            f'<div class="toc"><div class="tl">目 录</div>{links}</div>\n'
            f'<blockquote>{strongify(INTRO_NOTE)}</blockquote>\n'
            + body + "\n"
            + f'<div class="src"><div class="sl">这套工序在站内哪里被走过</div>'
              f'<p class="sd">本篇不由三家撞成——它讲的是撞的那套工序本身。'
              f'下面三处是它的产物与它的机器，可以拿本文的章节逐段对着读。</p>{ones}</div>\n'
            + '<div class="endbox"><p>网页长读 · 附录 A 工序清单 · 附录 B 十八条自检表 · '
              '附录 D 三个可以明天就开始的练习</p>\n'
              '<p><a href="/confluence/#c9">返回学科通融 · 通融创新法 →</a></p></div>\n'
            + '</div>\n'
            + tail.replace("学科通融 · 三学科交叉 · 作者", "学科通融 · 通融创新法 · 方法论特稿 · 作者"))

    assert page.count("<html") == 1 and page.count("</html>") == 1
    assert "return-leg" not in page, "骨架残留旧 slug"
    return page


def card_for_self(wan):
    trio = "".join(f'<div><b>{html.escape(k)}</b>{html.escape(v)}</div>' for k, v in [
        ("讲什么", "二阶碰撞的全套工序"),
        ("怎么讲", "厨房剩菜 · 旧衣服 · 杂物抽屉"),
        ("给谁看", "零基础，一路读得下来"),
    ])
    return (f'<div class="item" data-ch="{CH_ID}" style="border-left:3px solid var(--mark,#9e3d2c)">'
            f'<div class="n">通融创新法 · 方法论特稿 · 这一栏用的是哪一套工序</div>'
            f'<h2><a href="/confluence/{SLUG}/">{html.escape(TITLE)}</a></h2>'
            f'<p class="sub">{html.escape(SUB)}</p>'
            f'<p class="hk">{html.escape(DECK.replace("**", ""))}</p>'
            f'<div class="trio">{trio}</div>'
            f'<p class="rdmore"><a href="/confluence/{SLUG}/">读全文 →</a></p>'
            f'<p class="meta">约 {wan} 万字 · 网页长读 · 十三章 ＋ 四个附录 · 作者 {BYLINE} · '
            f'发表于{PUBDATE} · 本篇是方法论特稿，不占本栏篇号</p></div>\n')


def card_for_extra(d):
    return (f'<div class="item" data-ch="{CH_ID}">'
            f'<div class="n">{html.escape(d["n"])}</div>'
            f'<h2><a href="{d["href"]}">{html.escape(d["title"])}</a></h2>'
            f'<p class="sub">{html.escape(d["sub"])}</p>'
            f'<p class="hk">{html.escape(d["hk"])}</p>'
            f'<p class="rdmore"><a href="{d["href"]}">读全文 →</a></p>'
            f'<p class="meta">{html.escape(d["meta"])} · 本篇原发于站内其它栏目，此处按方法论归入本频道</p></div>\n')


def open_channel(wan):
    f = CF / "base.html"
    t = f.read_text(encoding="utf-8")
    assert SLUG not in t, "频道或卡片已存在"
    before_items = t.count('class="item"')

    # 1) chip
    a = ('<button class="chip" type="button" data-go="c8" aria-pressed="false">'
         '<span class="cn">权力</span><span class="cc" data-cnt="c8">— 篇</span></button>\n')
    assert t.count(a) == 1
    t = t.replace(a, a + f'<button class="chip" type="button" data-go="{CH_ID}" aria-pressed="false">'
                       f'<span class="cn">{CH_NAME}</span>'
                       f'<span class="cc" data-cnt="{CH_ID}">— 篇</span></button>\n', 1)

    # 2) 频道数字样
    assert t.count("八 个 频 道") == 1
    t = t.replace("八 个 频 道", "九 个 频 道", 1)

    # 3) grid 列数
    b = "grid-template-columns:repeat(8,1fr)"
    assert t.count(b) == 1
    t = t.replace(b, "grid-template-columns:repeat(9,1fr)", 1)

    # 4) chdesc
    c = "按承重判断分的八类。"
    assert t.count(c) == 1
    t = t.replace(c, "按承重判断分的八类，另加一个讲方法本身的频道。", 1)

    # 5) CHJS D 表
    d = "'c8':['权力','权力究竟落在记录的哪一栏上"
    assert t.count(d) == 1
    i = t.index(d)
    j = t.index("]", t.index("']", i)) + 1
    t = t[:j] + f",'{CH_ID}':['{CH_NAME}','{CH_DESC}']" + t[j:]

    # 6) 卡片：本篇在最前，三张外链跟在后面
    e = '<div class="item" data-ch='
    assert t.count(e) >= 1
    k = t.index(e)
    cards = card_for_self(wan) + "".join(card_for_extra(x) for x in EXTRA_CARDS)
    t = t[:k] + cards + t[k:]

    assert t.count('class="item"') == before_items + 4
    assert t.count(f'data-ch="{CH_ID}"') == 4
    f.write_text(t, encoding="utf-8")
    print("  base.html：频道 c9 已开，四张卡在位，共 %d 张卡" % t.count('class="item"'))


def retire_paradigm():
    # 撤掉每日必读的头条卡
    f = PZ / "index.html"
    t = f.read_text(encoding="utf-8")
    i = t.index('<div class="item" style="border:1px solid var(--clay)')
    j = t.index('\n', t.index('本篇是方法论特稿，不占典范文序号</div></div>', i)) + 1
    before = t.count('class="item"')
    t = t[:i] + t[j:]
    assert t.count('class="item"') == before - 1
    assert SLUG not in t
    f.write_text(t, encoding="utf-8")
    print("  /paradigm/：头条卡已撤，现共 %d 张卡" % t.count('class="item"'))

    # 旧 URL 留重定向（今天发出去过，不留死链）
    old = PZ / SLUG / "index.html"
    old.write_text(
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{TITLE} · 已移至学科通融 | SDE Universes</title>'
        f'<meta name="description" content="《{TITLE}》已归入「学科通融」专栏的「通融创新法」频道，'
        '本页自动跳转至新地址。">'
        f'<link rel="canonical" href="https://sdeuniverses.com/confluence/{SLUG}/">'
        f'<meta http-equiv="refresh" content="0;url=/confluence/{SLUG}/">'
        '<style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#f5f2e9;'
        'color:#23201a;font-family:"Noto Serif SC",Georgia,serif;padding:28px}'
        'main{max-width:640px;border:1px solid rgba(35,32,26,.16);border-top:3px solid #2a3b50;'
        'background:#fdfcf7;padding:44px}a{color:#9e3d2c;font-weight:700}</style></head><body>'
        f'<main><p style="font-size:12px;letter-spacing:.34em;color:#9e3d2c">页 面 已 迁 移</p>'
        f'<h1 style="font-size:28px;margin:16px 0">{TITLE}</h1>'
        '<p style="line-height:1.9">本篇已归入「学科通融」专栏新开的<b>通融创新法</b>频道。'
        f'正在跳转，若未自动跳转请点：<a href="/confluence/{SLUG}/">/confluence/{SLUG}/</a></p>'
        '<p style="line-height:1.9"><a href="/confluence/#c9">看这个频道的全部篇目 →</a></p>'
        '</main></body></html>\n', encoding="utf-8")
    print("  /paradigm/%s/：已改为重定向页" % SLUG)


def fix_home():
    f = ROOT / "public" / "index.html"
    t = f.read_text(encoding="utf-8")
    assert t.count(f'/paradigm/{SLUG}/') == 2, t.count(f'/paradigm/{SLUG}/')
    t = t.replace(f'/paradigm/{SLUG}/', f'/confluence/{SLUG}/')
    t = t.replace("每日必读 · 头条特稿 · 方法论 · 这个专栏用的是哪一套工序",
                  "学科通融 · 新开「通融创新法」频道 · 方法论特稿")
    t = t.replace("<p class=\"k\">每日必读 · 头条特稿 · 方法论</p>",
                  "<p class=\"k\">学科通融 · 新开「通融创新法」频道</p>")
    t = t.replace("<b style=\"color:#F0DCC8\">本篇是方法论特稿，不是典范文</b>——典范文是这套方法的产物，这一篇讲的是工序本身。",
                  "<b style=\"color:#F0DCC8\">本篇是方法论特稿</b>——学科通融栏其余各篇都是这套工序跑出来的产物，"
                  "这一篇讲的是工序本身；同频道另收站内三篇讲评分与工程实现的方法论长文。")
    assert f'/confluence/{SLUG}/' in t
    f.write_text(t, encoding="utf-8")
    print("  首页：两处已改指新址并改称学科通融")


def main():
    body, toc = md_to_html(SRC.read_text(encoding="utf-8"))
    n = len(re.findall(r"[\u4e00-\u9fff]", re.sub(r"<[^>]+>", "", body)))
    wan = round(n / 10000, 1)
    d = CF / SLUG
    d.mkdir(exist_ok=True)
    (d / "index.html").write_text(build_page(body, toc, wan), encoding="utf-8")
    print(f"  /confluence/{SLUG}/：{n} 汉字 · 目录 {len(toc)} 节")
    open_channel(wan)
    retire_paradigm()
    fix_home()


if __name__ == "__main__":
    main()
