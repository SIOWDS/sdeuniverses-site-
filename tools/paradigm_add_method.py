# -*- coding: utf-8 -*-
"""把《SDE 多学科通融创新法》并入「每日必读」，置于栏目头条。

它不是典范文（典范文＝站内三篇撞出来的产物、且全文零术语），而是**方法论特稿**：
把这个专栏与姊妹栏《学科通融》所用的那套工序，用日常案例从头讲一遍。
因此不领典范文序号，题头标「头条特稿 · 方法论」，卡片插在卡片流最前。
"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PZ = ROOT / "public" / "paradigm"
TPL = PZ / "taken-out" / "index.html"
SRC = ROOT / "tools" / "paradigm_method_body.txt"
SLUG = "confluence-method"
PUBDATE = "2026年8月16日"
BYLINE = "王德生 ＋ Claude"

TITLE = "SDE 多学科通融创新法"
SUB = "从 0 到 1 不是灵感，是一门可以重复的手艺——从厨房里的一盒剩菜讲起"

DECK = ("周三剩下的半锅红烧肉，周六还在冰箱里。做饭的人说菜端上桌就算做完了，"
        "排班的人说要等它被吃掉才算走完，管冰箱的人说它还占着格子就没结束——"
        "三个人吵不出结果，因为他们不是三个观点，是三个**算数的标准**。"
        "本文用这件事把一套方法从头走到尾：不看三家吵什么，看他们**不吵什么**——"
        "那句三个人都会说「这还用说吗」的话，才是地基；而推翻它的材料，"
        "就在做饭的人自己手里（他故意多做，那一刻已经把一部分指派给了一顿还不存在的饭）。"
        "地基一塌，一个三家账本上都没有字段的东西露了出来。"
        "全文另有旧衣服与杂物抽屉两个案例走完另外两种题型，"
        "并交出五道闸、发生链五步、可清点的读数、敌意拓宽的五个方向、"
        "一条必须把不利结果写进正文的真跑，以及六类风险与五种伪形。")

INTRO_NOTE = ("本篇是**方法论特稿**，不是典范文。典范文是这套方法的产物——"
              "站内三篇分属不同学科的文章撞出来的那样东西，且全文零术语；"
              "本篇讲的是**做出那些产物的工序本身**，因此必须把术语摆到台面上。"
              "读完这一篇，再回头读本栏任何一篇典范文，可以逐段对出它走的是哪一道工序。")

USES = [
    ("每日必读 · 站内三篇碰撞",
     "谁也没拿到——一份还没长成的东西被提前结清之后，账面完好无损",
     "/paradigm/nobody-held-it/",
     "第四章说的「共有前提」在这一篇里是：一样东西不在你手里就一定在别人手里。"
     "三篇源共享它，而账面为什么是平的这件事把它推翻了。"),
    ("每日必读 · 站内三篇碰撞",
     "没有人拒绝过你——一个动作的消失有三种来路，只有第三种不留下任何痕迹",
     "/paradigm/nobody-refused-you/",
     "第八章说的「读数必须能清点」在这一篇里兑现为一张四格辨别表："
     "必要性是否仍在 × 执行条件是否仍在——两个字段一填，三种消失当场分开。"),
    ("学科通融 · 站外三家碰撞",
     "整栏五十余篇：三家来源全部给出可点开核对的原始出处",
     "/confluence/",
     "本篇第六章那两把选源的尺子（位置三分、语汇族距离），"
     "在那一栏每一篇的开头都被走了一遍；撞不起来就换源，不许照跑。"),
]


def strongify(s):
    s = html.escape(s, quote=False)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)


def md_to_html(md):
    out, para, toc, n = [], [], [], 0

    def flush():
        if para:
            out.append("<p>" + strongify(" ".join(para)) + "</p>")
            para.clear()

    rows = []
    qbuf = []

    def flush_quote():
        if qbuf:
            out.append("<blockquote>" + "<br><br>".join(qbuf) + "</blockquote>")
            qbuf.clear()

    def flush_table():
        if not rows:
            return
        head, body = rows[0], rows[2:]
        cells = "".join(f"<th>{strongify(c)}</th>" for c in head)
        trs = ["<tr>" + cells + "</tr>"]
        for r in body:
            trs.append("<tr>" + "".join(f"<td>{strongify(c)}</td>" for c in r) + "</tr>")
        out.append('<table class="tbl">' + "".join(trs) + "</table>")
        rows.clear()

    for raw in md.splitlines():
        line = raw.rstrip()
        if line.strip().startswith("|"):
            flush()
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
    t = TPL.read_text(encoding="utf-8")

    # 只做网页长读：去掉三模式条里的两个 PDF 入口
    a = ('<div class="rb-modes"><span class="rb-btn cur">📖 长文阅读</span>\n'
         '  <a class="rb-btn" href="read.html">📄 在线 PDF</a>\n'
         '  <a class="rb-btn" href="taken-out.pdf" download>⬇ 下载 PDF</a></div>')
    assert a in t
    t = t.replace(a, '<div class="rb-modes"><span class="rb-btn cur">📖 网页长读</span>\n'
                     '  <a class="rb-btn" href="/taste/confluence/">⚔ 自己跑一次</a></div>')

    # 特稿不入频道
    t = re.sub(r'<!-- ch-stamp --><div class="art-channel".*?</div>\s*', "", t, flags=re.S)

    t = re.sub(r"<title>.*?</title>",
               f"<title>{TITLE}——{SUB} · 每日必读 | SDE Universes</title>", t, flags=re.S)
    t = re.sub(r'(<meta name="description" content=")[^"]*(")',
               lambda m: m.group(1) + html.escape(re.sub(r"\*\*", "", DECK)[:190], quote=True) + m.group(2), t)
    t = re.sub(r'<h1 class="art-title">.*?</h1>', f'<h1 class="art-title">{TITLE}</h1>', t, flags=re.S)
    t = re.sub(r'<(p|div) class="art-sub">.*?</\1>', f'<div class="art-sub">{SUB}</div>', t, flags=re.S)
    t = re.sub(r'<div class="art-meta">.*?</div>',
               f'<div class="art-meta">{BYLINE} 著 · 约 {wan} 万字 · 网页长读 · '
               f'发表于{PUBDATE}</div>', t, flags=re.S)
    t = re.sub(r'<div class="art-series">.*?</div>',
               '<div class="art-series">每 日 必 读 · 头 条 特 稿 · 方 法 论</div>', t, flags=re.S)
    t = re.sub(r'<div class="deck">.*?</div>', f'<div class="deck">{strongify(DECK)}</div>', t, flags=re.S)

    links = "".join(f'<a href="#{i}">{html.escape(x)}</a>' for i, x in toc)
    t = re.sub(r'<div class="toc">.*?</div>\s*(?=<h2|<p|<hr)',
               f'<div class="toc"><div class="tl">目 录</div>{links}</div>\n', t, flags=re.S)

    i = t.index("</div>", t.index(links)) + 6
    j = t.index('<div class="src">')
    t = (t[:i] + "\n"
         + f'<blockquote>{strongify(INTRO_NOTE)}</blockquote>\n'
         + body + "\n" + t[j:])

    ones = "".join(
        f'<a class="one" href="{u}"><div class="k">{html.escape(k)}</div>'
        f'<div class="t">{html.escape(ti)}</div><div class="g">{strongify(g)}</div></a>'
        for k, ti, u, g in USES)
    t = re.sub(r'<div class="src">.*?</div>\s*(?=<div class="endbox">)',
               f'<div class="src"><div class="sl">这套工序在站内哪里被走过</div>'
               f'<p class="sd">本篇不由三篇撞成——它讲的是撞的那套工序本身。'
               f'下面三处是它的产物，可以拿本文的章节逐段对着读。</p>{ones}</div>\n',
               t, flags=re.S)

    t = t.replace('<div class="endbox"><p>三种读法 · 网页长文 · 在线 PDF 翻页 · PDF 下载</p>',
                  '<div class="endbox"><p>网页长读 · 附录 A 工序清单 · 附录 B 十八条自检表 · '
                  '附录 D 三个可以明天就开始的练习</p>')
    t = t.replace("<footer>每日必读 · 典范文 · 作者",
                  "<footer>每日必读 · 头条特稿 · 方法论 · 作者")

    if ".tbl" not in t:
        t = t.replace("</style>",
                      ".tbl{width:100%;border-collapse:collapse;margin:26px 0;font-size:14.5px;line-height:1.8}\n"
                      ".tbl th,.tbl td{border:1px solid var(--line);padding:11px 13px;vertical-align:top;text-align:left}\n"
                      ".tbl th{background:var(--card);color:var(--indigo);font-weight:600}\n"
                      "blockquote{margin:22px 0;padding:14px 22px;border-left:3px solid var(--clay);"
                      "background:var(--card);color:var(--ink2)}\n</style>")

    assert t.count("<html") == 1 and t.count("</html>") == 1
    assert "taken-out" not in t, "模板残留旧 slug"
    return t


def add_card(wan):
    f = PZ / "index.html"
    t = f.read_text(encoding="utf-8")
    before = t.count('class="item"')
    assert SLUG not in t, "卡片已存在"
    trio = "".join(f'<div><b>{html.escape(k)}</b>{html.escape(v)}</div>' for k, v in [
        ("讲什么", "二阶碰撞的全套工序"),
        ("怎么讲", "厨房剩菜 · 旧衣服 · 杂物抽屉"),
        ("给谁看", "零基础，一路读得下来"),
    ])
    card = ('<div class="item" style="border:1px solid var(--clay);box-shadow:0 0 0 3px rgba(181,113,74,.08)">'
            '<div class="n">头 条 特 稿 · 方 法 论 · 这个专栏用的是哪一套工序</div>'
            f'<h2><a href="/paradigm/{SLUG}/">{html.escape(TITLE)}</a></h2>'
            f'<p class="sub">{html.escape(SUB)}</p>'
            f'<p class="hk">{html.escape(DECK.replace(chr(42) + chr(42), ""))}</p>'
            f'<div class="trio">{trio}</div>'
            f'<a class="rdmore" href="/paradigm/{SLUG}/">读全文 →</a>'
            f'<div class="meta">约 {wan} 万字 · 网页长读 · 十三章 ＋ 四个附录 · 作者 {BYLINE} · '
            f'发表于{PUBDATE} · 本篇是方法论特稿，不占典范文序号</div></div>\n')
    a = "<!-- paradigm-channels:end -->\n"
    assert t.count(a) == 1
    t = t.replace(a, a + "\n" + card, 1)
    assert t.count('class="item"') == before + 1
    f.write_text(t, encoding="utf-8")
    print("  栏目页：头条卡已插在卡片流最前，现共 %d 张卡" % t.count('class="item"'))


def main():
    body, toc = md_to_html(SRC.read_text(encoding="utf-8"))
    n = len(re.findall(r"[\u4e00-\u9fff]", re.sub(r"<[^>]+>", "", body)))
    wan = round(n / 10000, 1)
    d = PZ / SLUG
    d.mkdir(exist_ok=True)
    (d / "index.html").write_text(build_page(body, toc, wan), encoding="utf-8")
    add_card(wan)
    print(f"  {SLUG}: {n} 汉字 · 目录 {len(toc)} 节 · 署名 {BYLINE}")


if __name__ == "__main__":
    main()
