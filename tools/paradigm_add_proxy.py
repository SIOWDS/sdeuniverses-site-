# -*- coding: utf-8 -*-
"""把《代签》并入「每日必读」。

本篇是标准的三篇碰撞篇：三位学员分属三个不同门类，三对主题两两冲突。
  少敏（诗学）：某些通道停止索取，是理解的成熟形式。
  雷建华（家庭教育）：准确的属性命名会替孩子提前封顶，大人应单向留白、不索取回报。
  胡敏（照料生理学）：照料的动员必须由特定他者的生命应答来结算，否则沉淀为债务。
第二位要求成人守住的那个条件（长期在场且不索取回报），正是第三位论证的致病结构；
而第一位把"停止索取"当成可以做出的选择，第三位说身体不接受这个选择。
"""
import html
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
PZ = ROOT / "public" / "paradigm"
TPL = PZ / "taken-out" / "index.html"
SRC = ROOT / "tools" / "paradigm_proxy_body.txt"
SLUG = "proxy-signature"
PUBDATE = "2026年8月1日"
FIELDS = "诗学 × 家庭教育 × 照料生理学"
BYLINE = "王德生 ＋ Claude"

TITLE = "代签"
SUB = "为什么最懂你的那个人，最需要你变成一个固定的人"

DECK = ("一位父亲说出一句准确又温柔的话，一个照料失智丈夫四年的女人被所有人称赞却一点没有好转，"
        "一首诗里两个人隔着透明的墙握着手——三件毫不相干的事里，都有一个人为另一个人调动了自己，"
        "而这笔调动要怎么收回来，谁也没有说。本文论证：收回它的不是感谢、不是第三方的赞许、"
        "也不是自己的道德满足，而是**一个只能由那个特定的人发出、且只能以他此刻的状态为形式的应答**。"
        "由此看见一件此前没有被指认的事——当被照料的一方还有能力回应时，他往往并不发出那种应答，"
        "而是发出一个替代品：**他把自己变成一个可以被一句话说清楚的、固定的人，让照料他的那个人有东西可收**。"
        "文章把这个动作叫作代签，给出四格辨别表与两个可以当场自问的问题，"
        "并给五条能推翻它的条件——第一条只要两分钟。")

CLASH = ("第一篇说成熟的关系可以停止索取某些通道；第二篇说「一起」不是修辞，"
         "一个不被对方改变的人根本没有真的在这段关系里；第三篇说这根本不是一个选择——"
         "你可以决定不再要求，你的身体不能决定不再等账。而第二篇给成人开的处方"
         "（长期在场、不把对方的确定当成果、不索取回报），恰恰就是第三篇论证的那个致病结构。"
         "若第二篇对，越克制的人应该越做越稳；若第三篇对，他应该越做越垮。")

SOURCES = [
    ("诗学 · 停止索取是成熟",
     "隔音墙两侧：当代诗歌中的接触而不融合",
     "/students/shao-min/soundproof-wall/",
     "双方保持接触，却不以进入对方内部为目标；某些通道保持可达，某些通道停止索取，"
     "关系仍以可见、相邻和照料维持——理解不必以穿透为完成。"),
    ("家庭教育 · 别替他把话说死",
     "和孩子一起发生自己",
     "/students/lei-jianhua/becoming-together/",
     "那个「我」是最后才长出来的屋顶而不是地基，所以准确、温柔、听起来完全正面的属性命名"
     "会把还在动的东西固定住；而属性句的第一功能不是描述孩子，是安顿父母。"),
    ("照料生理学 · 收不到就是债",
     "结算饥饿与照料的隐性生理学",
     "/students/hu-min/settlement-hunger/",
     "照料的生理动员，要由那个特定被照料者的生命应答来完成一次全局性的结算；"
     "第三方的赞扬与金钱补偿进不了那条回路——不是不够好，是频率不对。"),
]

SIBLING = ("本栏有三篇与本篇挨得很近，必须说清楚，否则会被读成重复。"
           "《把手拿开，他不会自动开始长》给出的是**第三种姿势**：有人在场，但不往里面放东西；"
           "《扶一把，和替他站着》给出的是**撤走测试**：两种扶法只有在支持撤走的那一刻才分得开；"
           "《账外的东西》给出的是**转移端**：那样东西是从谁身上到了谁身上。"
           "三篇讲的全是**施与者应当怎么做**——什么姿势、什么时机、怎么克制。"
           "本篇问的是它们都没有问过的下一句：**这个姿势对施与者自己的身体做了什么，"
           "那张准许他松下来的单子由谁来签。**所以本篇第十二节那句"
           "「克制不产生结算，它只是不伪造」，正好接在那三篇的结论后面——"
           "它们说完了该怎么做，本篇说的是做完之后那笔账还挂着。")

BANNED = ("发生学", "发现学", "发生论", "本体论", "存在论", "显露", "纠缠", "裂缝",
          "金点子", "回写", "差异序列", "SDE", "元隐喻", "创新智商", "母题")


def strongify(s):
    s = html.escape(s, quote=False)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)


def load_md():
    return SRC.read_text(encoding="utf-8")


def md_to_html(md):
    out, para, toc, n = [], [], [], 0

    def flush():
        if para:
            out.append("<p>" + strongify(" ".join(para)) + "</p>")
            para.clear()

    rows = []

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
        if not line.strip():
            flush(); continue
        if line.strip() == "---":
            flush(); out.append("<hr>"); continue
        m = re.match(r"^(#{2,4})\s+(.*)$", line)
        if m:
            flush()
            lvl, txt = len(m.group(1)), m.group(2).strip()
            if lvl == 2:
                n += 1
                out.append(f'<h2 id="s{n}">{strongify(txt)}</h2>')
                toc.append((f"s{n}", txt))
            else:
                out.append(f"<h{lvl}>{strongify(txt)}</h{lvl}>")
            continue
        if line.strip().startswith("- "):
            flush()
            out.append("<p>· " + strongify(line.strip()[2:]) + "</p>")
            continue
        if line.strip().startswith("> "):
            flush()
            out.append('<blockquote>' + strongify(line.strip()[2:]) + "</blockquote>")
            continue
        para.append(line.strip())
    flush(); flush_table()
    return "".join(out), toc


def build_page(body, toc, pages, wan, no_cn):
    t = TPL.read_text(encoding="utf-8")
    t = re.sub(r"<title>.*?</title>",
               f"<title>{TITLE}——{SUB} · 每日必读 | SDE Universes</title>", t, flags=re.S)
    t = re.sub(r'(<meta name="description" content=")[^"]*(")',
               lambda m: m.group(1) + html.escape(re.sub(r"\*\*", "", DECK)[:190], quote=True) + m.group(2), t)
    t = re.sub(r'<h1 class="art-title">.*?</h1>', f'<h1 class="art-title">{TITLE}</h1>', t, flags=re.S)
    t = re.sub(r'<(p|div) class="art-sub">.*?</\1>', f'<div class="art-sub">{SUB}</div>', t, flags=re.S)
    t = re.sub(r'<div class="art-meta">.*?</div>',
               f'<div class="art-meta">{BYLINE} · 约 {wan} 万字 · {pages} 页 · '
               f'三种阅读方式 · 发表于{PUBDATE}</div>', t, flags=re.S)
    t = re.sub(r'<div class="art-series">.*?</div>',
               f'<div class="art-series">每 日 必 读 · 典 范 文 · {no_cn}</div>', t, flags=re.S)
    t = re.sub(r'<div class="deck">.*?</div>', f'<div class="deck">{strongify(DECK)}</div>', t, flags=re.S)

    links = "".join(f'<a href="#{i}">{html.escape(x)}</a>' for i, x in toc)
    t = re.sub(r'<div class="toc">.*?</div>\s*(?=<h2|<p|<hr)',
               f'<div class="toc"><div class="tl">目 录</div>{links}</div>\n', t, flags=re.S)

    i = t.index("</div>", t.index(links)) + 6
    j = t.index('<div class="src">')
    t = (t[:i] + "\n" + body
         + f'\n<hr>\n<h2 id="sib">附：与本栏另外三篇的关系</h2><p>{strongify(SIBLING)}</p>\n'
         + t[j:])

    ones = "".join(
        f'<a class="one" href="{u}"><div class="k">{html.escape(k)}</div>'
        f'<div class="t">{html.escape(ti)}</div><div class="g">{strongify(g)}</div></a>'
        for k, ti, u, g in SOURCES)
    t = re.sub(r'<div class="src">.*?</div>\s*(?=<div class="endbox">)',
               f'<div class="src"><div class="sl">这一篇由哪三篇撞成</div>'
               f'<p class="sd">{strongify(CLASH)}</p>{ones}</div>\n', t, flags=re.S)

    if ".tbl" not in t:
        t = t.replace("</style>",
                      ".tbl{width:100%;border-collapse:collapse;margin:26px 0;font-size:14.5px;line-height:1.8}\n"
                      ".tbl th,.tbl td{border:1px solid var(--line);padding:11px 13px;vertical-align:top;text-align:left}\n"
                      ".tbl th{background:var(--card);color:var(--indigo);font-weight:600}\n"
                      "blockquote{margin:22px 0;padding:14px 22px;border-left:3px solid var(--clay);"
                      "background:var(--card);color:var(--ink2)}\n</style>")

    assert t.count("<html") == 1 and t.count("</html>") == 1
    hit = [w for w in BANNED if w in body]
    assert not hit, f"本篇正文残留行话：{hit}"
    return t


def add_card(pages, wan, no_card):
    f = PZ / "index.html"
    t = f.read_text(encoding="utf-8")
    before = t.count('class="item"')
    assert SLUG not in t, "卡片已存在"
    trio = "".join(f'<div><b>{html.escape(k)}</b><a href="{u}">{html.escape(ti)}</a></div>'
                   for k, ti, u, _g in SOURCES)
    who = ('三篇来源分别出自<a href="/students/shao-min/" style="color:var(--clay)">少敏</a>、'
           '<a href="/students/lei-jianhua/" style="color:var(--clay)">雷建华</a>与'
           '<a href="/students/hu-min/" style="color:var(--clay)">胡敏</a>')
    card = (f'<div class="item"><div class="n">{no_card} · 三学科交叉：{FIELDS}</div>'
            f'<h2><a href="/paradigm/{SLUG}/">{html.escape(TITLE)}</a></h2>'
            f'<p class="sub">{html.escape(SUB)}</p>'
            f'<p class="hk">{html.escape(DECK.replace(chr(42) + chr(42), ""))}</p>'
            f'<div class="trio">{trio}</div>'
            f'<a class="rdmore" href="/paradigm/{SLUG}/">读全文 →</a>'
            f'<div class="meta">约 {wan} 万字 · {pages} 页 · 三种读法 · 作者 {BYLINE} · '
            f'发表于{PUBDATE} · {who}</div></div>\n')
    a = "</main>"
    assert t.count(a) == 1
    t = t.replace(a, card + a, 1)
    assert t.count('class="item"') == before + 1
    f.write_text(t, encoding="utf-8")
    print("  栏目页：追加一张卡，现共 %d 篇" % t.count('class="item"'))


def main():
    from paradigm_ordinal import claim
    no, no_card_cn = claim(f"paradigm/{SLUG}", title=TITLE)
    no_cn = " ".join(no_card_cn)
    no_card = "之" + no_card_cn
    print(f"  领到发布号 {no}（{no_card}）")

    body, toc = md_to_html(load_md())
    n = len(re.sub(r"<[^>]+>", "", body))
    wan = round(n / 10000, 1)
    d = PZ / SLUG
    d.mkdir(exist_ok=True)

    pages = 20
    for guess in (20, None):
        (d / "index.html").write_text(build_page(body, toc, guess or pages, wan, no_cn), encoding="utf-8")
        subprocess.run([sys.executable, "tools/build_pdf_paradigm.py",
                        f"public/paradigm/{SLUG}/index.html", "-o", f"public/paradigm/{SLUG}/{SLUG}.pdf"],
                       cwd=str(ROOT), check=True, stdout=subprocess.DEVNULL)
        from pypdf import PdfReader
        pages = len(PdfReader(str(d / f"{SLUG}.pdf")).pages)
    probe = subprocess.run(["pdftotext", "-f", "1", "-l", "1", str(d / f"{SLUG}.pdf"), "-"],
                           capture_output=True, text=True).stdout
    assert re.search(r"[\u4e00-\u9fff]", probe), "PDF 首页抽不出中文"

    rd = (PZ / "taken-out" / "read.html").read_text(encoding="utf-8")
    rd = rd.replace("taken-out", SLUG).replace("一拿出来，就不是它了", TITLE)
    rd = re.sub(r"\d+ 页", f"{pages} 页", rd)
    (d / "read.html").write_text(rd, encoding="utf-8")

    add_card(pages, wan, no_card)
    print(f"  {SLUG}: {n} 字 · {pages} 页 · 目录 {len(toc)} 节 · 署名 {BYLINE}")


if __name__ == "__main__":
    main()
