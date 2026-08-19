# -*- coding: utf-8 -*-
"""把《可预期的尺子》并入「每日必读」。

与本栏站内碰撞各篇的不同（须在页面上如实标出）：
  · **撞的是站外三家理论**（同 之八/之九/之十 的口径），来源栏给可直接点开核对的原始出处；
  · 三家分属政治人类学 / 社会测量学 / 劳动经济学，对同一现象给出互相取消的预测。
署名照本栏惯例 **王德生 ＋ Claude**（模板默认，不做替换）。
"""
import html, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
PZ = ROOT / "public" / "paradigm"
TPL = PZ / "taken-out" / "index.html"
SRC = ROOT / "tools" / "paradigm_stop_body.txt"
SLUG = "why-it-has-to-stop"
PUBDATE = "2026年8月1日"
FIELDS = "系统神经科学 × 计算机系统 × 会计与内控（本篇撞的是站外三家传统）"
BYLINE = "王德生 ＋ Claude"

TITLE = "为什么非得停下来"
SUB = ("盘点要关门，修路要封路，清理内存要卡一下，而人每天要交出七八个小时。"
       "最顺口的解释是「维护和干活抢同一副硬件」——可如果只是资源问题，加倍投入就该解决它。"
       "本文认为三家成熟传统都漏了同一件事：停机不是为了腾出资源，是为了冻结判断的前提。")
DECK = ("清点一百件货，力气可以忽略不计——可只要收发不停，你就永远得不到一份对的数。"
        "而冲刷一条管道里的沉积极耗资源，却可以一边用一边冲。**这两个例子放在一起，"
        "「停机是为了腾出资源」这个解释就塌了。** 三家成熟传统在这件事上立场互相取消："
        "睡眠研究说那段离线不可取消；并发内存回收三十年的纲领就是消灭停顿，"
        "把必须暂停的窗口从几秒压到亚毫秒；会计取消了停业盘点，却坚决保留截止日，"
        "而它自己给的两个理由互相推不出。本文提出的判断是：**一项维护之所以必须停机，"
        "是因为它所依据的那个判断会被在线活动推翻——停机是为了冻结判断的前提**；"
        "由此得到一条可判定的判据：看那个判据是不是**单调**的（一旦成立就不会被逆转）。"
        "这条判据不是思辨，工程界已经算了三十年，只是把它写成了自己的局部事实。"
        "文末给十处跨领域读数、两处反过来迫使它让步的地方、"
        "六条能推翻它的条件（最便宜的一条只需翻一份公开的功能演进史，另一条只需一间仓库和一天），"
        "以及一条写死到 2032 年的赌注。")
ORIGIN = ("**本篇撞的是站外三家传统，不是站内学员论文**（同本栏之八、之九、之十的口径）。"
          "三家都在处理同一个问题——有些维护为什么必须让被维护的东西先停下来——"
          "而给出的立场互相取消：一家说离线是不可取消的根基，一家的整个研究纲领是消灭停顿，"
          "一家在实践上取消了关门却坚决保留划刀。其中第二家已经把条件算到了极精确的程度，"
          "只是把答案写成了自己领域的实现细节。正文第二至第四章逐一交代三家说到了哪一步，"
          "第五章把矛盾写死，第九章摆出三条已经被算清楚、却没人搬出来的读数，"
          "第十三章再与另外五种最容易被混为一谈的说法逐条分界——"
          "**其中第一位是本文承认最可能吸收掉自己的那一个**。")
SOURCES = [
    ("系统神经科学 · 睡眠功能之争",
     "整晚在做什么：普遍下调、选择性重演，还是代谢废物的冲刷",
     "https://pubmed.ncbi.nlm.nih.gov/24411729/",
     "三派对功能归属互不相容，却在一件事上高度一致：这些工作必须离线做，而且离线不能被取消。"
     "**与本文的分离线**：三派给出的不可取消理由其实是三种（边调边加、回放会被当成现实、通道打不开），"
     "被笼统记成「必须离线」之后，那条决定哪一项**有可能**被搬上线的区分就永远得不到。"),
    ("计算机系统 · 并发内存回收",
     "把必须暂停的窗口从几秒压到亚毫秒：快照式标记、写屏障、疏散与安全点",
     "https://dl.acm.org/doi/10.1145/359642.359655",
     "它为了取消停顿，被迫把停顿的理由拆开了：正因为「一个对象一旦不可达就永远不可达」，"
     "才可以在过时的快照上遍历；代价有名字，叫浮动垃圾。"
     "**与本文的分离线**：它把这条判据写成了自己的局部事实（可达性、写屏障、疏散），"
     "而这些词没有一个是可迁移的——本文要做的正是把它搬出来。"),
    ("会计与内控 · 盘点与截止",
     "关门盘点被循环盘点与持续审计取代，而截止日不可取消",
     "https://www.iaasb.org/publications/international-standard-auditing-501-audit-evidence-specific-considerations-selected-items",
     "同一个行当取消掉了关门，却取消不掉划刀，而它给的两个理由（技术进步、内控要求）不在同一层。"
     "**与本文的分离线**：本文预测，只要一项程序所依据的判定是单调的，它迟早会被持续化；"
     "只要不是，它就会被保留为一个时点，无论技术多好。"),
]
SIBLING = ("本栏另有三篇与本篇同形：《可预期的尺子》说判据能不能被提前推断，决定了一个领域还提得出什么问题；"
           "《谁说了这一次到此为止》说「一次」的边界由谁划，决定了什么被当作可比较的两次；"
           "《说过去就没了》说信道让不让你回头，决定了哪些结构长得出来。"
           "四篇合起来是同一个形状的四处——**决定长出什么的，往往不是内容，"
           "而是内容所在那条管子的性质**；本篇问的则是：那条管子什么时候非得先停下来不可。")
BANNED = ("发生学", "发现学", "本体论", "存在论", "显露态", "特征纠缠", "差异序列",
          "SDE", "金点子", "回写", "二阶", "碰撞出典范", "近邻划界", "五重检验")


def strongify(s):
    s = html.escape(s, quote=False)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)


def md_to_html(md):
    out, para, toc, n = [], [], [], 0
    lines = md.splitlines()
    i = 0

    def flush():
        if para:
            out.append("<p>" + strongify(" ".join(para)) + "</p>")
            para.clear()

    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            flush(); i += 1; continue
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
            i += 1; continue
        if line.lstrip().startswith("|"):                    # 表格
            flush()
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            rows = [r for r in rows if not all(set(c) <= set("-: ") for c in r)]
            t = ['<div class="tblwrap"><table>']
            for k, r in enumerate(rows):
                tag = "th" if k == 0 else "td"
                t.append("<tr>" + "".join(
                    f"<{tag}>{strongify(c).replace(chr(60)+'br>', '<br>')}</{tag}>" for c in r) + "</tr>")
            t.append("</table></div>")
            out.append("".join(t)); continue
        if line.startswith("> "):
            flush()
            buf = []
            while i < len(lines) and lines[i].startswith("> "):
                buf.append(lines[i][2:].strip()); i += 1
            out.append("<blockquote>" + strongify(" ".join(buf)) + "</blockquote>"); continue
        if re.match(r"^- ", line):
            flush()
            items = []
            while i < len(lines) and re.match(r"^- ", lines[i]):
                items.append(lines[i][2:].strip()); i += 1
            out.append("<ul class=pl>" + "".join(f"<li>{strongify(x)}</li>" for x in items) + "</ul>"); continue
        para.append(line.strip()); i += 1
    flush()
    return "".join(out), toc


CSS_ADD = ("\n.tblwrap{overflow-x:auto;margin:1.6rem 0}.tblwrap table{border-collapse:collapse;width:100%;font-size:.93rem}"
           ".tblwrap th,.tblwrap td{border:1px solid rgba(138,104,23,.3);padding:.55rem .7rem;text-align:left;"
           "vertical-align:top;line-height:1.75}.tblwrap th{background:rgba(138,104,23,.08);font-weight:700}"
           "ul.pl{margin:0 0 1.1rem 1.4rem}ul.pl li{margin-bottom:.5rem;line-height:1.95}"
           "blockquote{margin:1.6rem 0;padding:1rem 1.3rem;border-left:3px solid #B5714A;"
           "background:rgba(181,113,74,.06);font-weight:600}\n")


def build_page(body, toc, pages, wan, no_cn):
    t = TPL.read_text(encoding="utf-8")
    t = re.sub(r"<title>.*?</title>",
               f"<title>{TITLE}——{SUB[:52]} · 每日必读 | SDE Universes</title>", t, flags=re.S)
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
    t = t.replace("</style>", CSS_ADD + "</style>", 1)

    links = "".join(f'<a href="#{i}">{html.escape(x)}</a>' for i, x in toc)
    t = re.sub(r'<div class="toc">.*?</div>\s*(?=<h2|<p|<hr)',
               f'<div class="toc"><div class="tl">目 录</div>{links}</div>\n', t, flags=re.S)

    i = t.index("</div>", t.index(links)) + 6
    j = t.index('<div class="src">')
    t = (t[:i] + "\n" + body
         + f'\n<hr>\n<h2 id="sib">附：与本栏另外两篇的关系</h2><p>{strongify(SIBLING)}</p>\n'
         + t[j:])

    ones = "".join(
        f'<a class="one" href="{u}"><div class="k">{html.escape(k)}</div>'
        f'<div class="t">{html.escape(ti)}</div><div class="g">{strongify(g)}</div></a>'
        for k, ti, u, g in SOURCES)
    t = re.sub(r'<div class="src">.*?</div>\s*(?=<div class="endbox">)',
               f'<div class="src"><div class="sl">这一篇撞的三家，与可核对的出处</div>'
               f'<p class="sd">{strongify(ORIGIN)}</p>{ones}</div>\n', t, flags=re.S)

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
    who = "本篇撞的是<b>站外</b>三家理论，三条来源均给出可直接点开核对的原始出处"
    card = (f'<div class="item"><div class="n">{no_card} · 三学科交叉：{FIELDS}</div>'
            f'<h2><a href="/paradigm/{SLUG}/">{html.escape(TITLE)}</a></h2>'
            f'<p class="sub">{html.escape(SUB)}</p>'
            f'<p class="hk">{html.escape(DECK.replace(chr(42)+chr(42), ""))}</p>'
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
    import os
    if os.environ.get("ORD_CN"):
        no, no_card_cn = 0, os.environ["ORD_CN"]
    else:
        no, no_card_cn = claim(f"paradigm/{SLUG}", title=TITLE)
    no_cn = " ".join(no_card_cn)
    no_card = "之" + no_card_cn
    print(f"  领到发布号 {no}（{no_card}）")

    body, toc = md_to_html(SRC.read_text(encoding="utf-8"))
    txt = re.sub(r"<[^>]+>", "", body)
    n = len(re.findall(r"[\u4e00-\u9fff]", txt))   # 按纯汉字算，站内口径
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
    rd = re.sub(r"\d+ 页 · 王德生 ＋ Claude", f"{pages} 页 · {BYLINE}", rd)
    (d / "read.html").write_text(rd, encoding="utf-8")

    add_card(pages, wan, no_card)
    print(f"  {SLUG}: {n} 字 · {pages} 页 · 目录 {len(toc)} 节 · 署名 {BYLINE}")


if __name__ == "__main__":
    main()
