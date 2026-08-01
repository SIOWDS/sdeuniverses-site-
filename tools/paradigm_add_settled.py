# -*- coding: utf-8 -*-
"""把《谁也没拿到》并入「每日必读」。

与本栏其它各篇的不同（须在页面上如实标出）：
  · 三篇源是**从站内 1339 篇正文文章里程序随机抽出**的，不是挑出来的；
  · 三篇分属家庭伦理学 / 艺术存在论 / 科学思想史，对同一个读数（某样东西没有发生）
    给出互不相容的归因。
署名照本栏惯例 **王德生 ＋ Claude**。
"""
import html, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
PZ = ROOT / "public" / "paradigm"
TPL = PZ / "taken-out" / "index.html"
SRC = ROOT / "tools" / "paradigm_settled_body.txt"
SLUG = "nobody-held-it"
PUBDATE = "2026年8月1日"
FIELDS = "教育技术 × 科学思想史 × 政治经济学（三篇源随机抽出，且强制跨栏跨作者）"
BYLINE = "王德生 ＋ Claude"

TITLE = "谁也没拿到"
SUB = ("一个人学了很多却没有变强，通常被归给两件事：他被提取了，或者它从未兑现。"
       "本文论证这两种记法在同一批案例上互相取消，并给出第三种：那份东西在长成之前，"
       "就被结清成了一条只能读、不能支取的记录。这不是一次转移，是一次相变；"
       "转移有持有者，相变没有——所以账是平的。")
DECK = ("一个学生在一道题上刚被咬住，那股'不搞清楚不舒服'的劲还没长到能推他自己去翻书，"
        "系统已经读出'知识点 X 有偏差'并推来一段刚好对症的讲解。他懂了，往下走了，"
        "学期末完成率很好看——而把他放到一个没人划范围的场合里，他会茫然。"
        "那股劲去哪了？最顺手的答案是被系统拿走了。可同一时期另一本账显示，"
        "被指为拿走的那一方也没变强：能演示，难落地，难负责。**两边都亏，那它在谁手里？**"
        "本文的回答是：不在任何人手里。它被结清成了一条记录——记录是真的，"
        "偏差真的存在、干预真的发生、闭环真的完成，**每一步都是真的，而合起来什么也没留下**。"
        "由此得到两条轴：结清发生在它成型之前还是之后，结清的产物是可支取的存量还是只可读的记录；"
        "四格里最难发现的那一格，账面完整甚至更好看，因为**没有任何一个科目登记'已确认而未实现'**。"
        "文末给十二处跨领域读数、两处反过来迫使它让步的地方（一处来自代谢生化，一处来自软件工程的技术债台账）、"
        "六条能推翻它的条件（第一条一个部门就能做一次），以及一条写死到 2031 年的赌注。")

ORIGIN = ("**本篇的三篇源是随机抽出来的，并且加了一道约束：三篇必须来自不同栏目、出自不同作者。** "
          "做法：扫全站两千六百多个页面，按「正文段落汉字不少于六千、页内链接少于八十」筛出正文文章，"
          "再以时间戳为种子反复抽取，直到抽中一组满足跨栏跨作者约束的为止（第三次抽中）。"
          "加这道约束的理由很实际：同一位作者、同一个栏目里的文章共享太多零件，撞出来的东西容易落回共同的前提上。"
          "抽出的三篇分属教育技术、科学思想史与政治经济学，对同一个读数——某样东西没有变成力量——"
          "给出互不相容的归因：一篇说它被提取了，一篇说它被安置了，一篇说它从未兑现。"
          "正文第一至第三章交代三笔账与两种现成记法为何互相取消，第四章给出四格表与四步查法，"
          "第五至第十二章按格展开，第十三章与最容易被混为一谈的八种说法逐条分界——"
          "**其中第八种同时是本文被迫让步的地方**。")

SOURCES = [
    ("教育技术 · 《势能被谁取走了》",
     "知识图谱把学习的组织原则从学习者的困惑换成了学科的分类，更隐蔽的是把他尚未成型的张力翻译成了系统的误差信号",
     "/students/chen-xiaoyan/potential-siphoning/",
     "每一次精准推送所消耗的，恰恰是那股尚未成型的「为自己而问」的张力。"
     "**与本文的分离线**：那一篇的链条终点是系统受益（算法、点击、停留时长）；"
     "本文追问下去发现系统那边也拿不出可支取的存量——于是提取这个记法在这里断了。"),
    ("科学思想史 · 《圣化》",
     "异质认知不被禁止，只被消化：请进来、重新命名、降格归类，于是它在不被察觉的情况下丧失了异质性",
     "/culture-tech/needham/sanctification-mechanism/",
     "一部译本没有被禁毁，它被归入了天文历算的余事，然后一百多年无人接手。"
     "**与本文的分离线**：那一篇问的是异质性怎么丧失的；本文问的是那笔账记在哪儿——"
     "「给它一个位置」这个动作同时把一个还在长的问题登记成了一个已经了结的问题。"),
    ("政治经济学 · 《AGI：从一个巨型教育泡沫到全球性经济泡沫》",
     "学习规模的扩张与力量的增长不是同一件事：可搬运的知识没有被编译成可承担、可验收的流程",
     "/books/involution/agi-bubble/",
     "一边是巨量资源被吞掉，一边是「能演示、难落地、难负责」。"
     "**与本文的分离线**：那一篇说没有人拿走任何东西，只是缺一道工序；"
     "本文指出损失发生在更早的位置——不是编译能力缺失，是编译所需的那份余额被提前结清掉了。"),
]

SIBLING = ("本栏另有一篇《没有人拒绝过你》，讲一个动作从社会里消失的第三种来路——它的必要性被更便宜地满足了，"
           "因此那次关闭不经过拒绝，也就不留下任何指纹。那一篇管**动作为什么不再被执行**，"
           "本篇管**执行留下的东西去了哪里**；两篇合起来是同一条街的两端，而且共用一个不舒服的结论："
           "最难发现的损失，都是那种不产生受害者、也不产生受益者的损失。"
           "另有《可预期的尺子》讲一把公开的尺子如何在被使用之前就改变了被量者，"
           "与本文第十二节「结清成本降到接近于零之后会怎样」是同一个结构。")

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
        if line.lstrip().startswith("|"):
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
                    f"<{tag}>{strongify(c).replace('&lt;br&gt;', '<br>')}</{tag}>" for c in r) + "</tr>")
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
               f'<div class="src"><div class="sl">这一篇撞的三家，与可点开核对的出处</div>'
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
    who = "本篇三篇源由<b>程序随机抽取</b>并强制跨栏跨作者，三条来源均可直接点开核对"
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
    n = len(re.findall(r"[\u4e00-\u9fff]", txt))
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
