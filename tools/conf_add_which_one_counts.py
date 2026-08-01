# -*- coding: utf-8 -*-
"""把《哪一份算数》并入「学科通融」，之十三。

三源全在站外（软件工程 / 数字保存与条约法 / 演化遗传学），符合本栏口径。
署名照本栏惯例 王德生 ＋ Claude。
"""
import html, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CF = ROOT / "public" / "confluence"
TPL = CF / "suture-to-death" / "index.html"
SRC = ROOT / "tools" / "conf_which_one_counts_body.txt"
SLUG = "which-one-counts"
PUBDATE = "2026年8月1日"
ORD = "之十五"
FIELDS = "软件工程 × 数字保存与条约法 × 演化遗传学"
BYLINE = "王德生 ＋ Claude"

TITLE = "哪一份算数"
SUB = ("同一样东西存了好几份，三个互不往来的行当给出三种互相取消的处方：必须消除、必须增加且刻意不设正本、"
       "不一致才是产出。本文论证三家漏掉了同一条分界——副本本身既不危险也不安全，"
       "危险只发生在一个地方：系统预期它们一致，却没有人负责让它们一致。")
DECK = ("软件工程有一条流传二十多年的原则：每一条知识必须有单一、无歧义、权威的表示，否则改一处会漏另一处。"
        "数字保存的做法正好相反——多存几份才丢不了，而且刻意不指定哪一份是正本，节点之间不断互相比对、按多数修复；"
        "多语种条约也是这样，各文本同等作准，歧义时按条约目的解释，不设母本。"
        "演化遗传学则说，一个基因被复制之后，多出来的那份之所以能长成新东西，**前提恰恰是没有任何机制要求两份保持一致**。"
        "三家都有几十年的证据，处方却互相拆台。本文认为三家用的不是同一个变量："
        "**副本本身既不危险也不安全，危险只发生在一个地方——系统预期它们一致，却没有任何人负责让它们一致。**"
        "危害的量不由份数决定，由这个预期覆盖的范围决定。由此把「预期」与「机制」拆成两条独立的轴，得到一张四格表，"
        "其中最坏的一格此前没有名字：所有人心里都有一份「算数的那一份」，只是每个人心里的不是同一份——"
        "它有全部的效力，没有任何的位置。它的读数是一句一分钟就能问完的话：**如果这两份不一样，哪一份算数？**"
        "文末给一套半小时可执行的查法、十二处跨领域读数、两处反过来迫使本文让步的约束（多数重复基因终将丢失；"
        "独立编写的版本并不独立地出错）、六条判错条件，以及一条写死到 2032 年的赌注。")

ORIGIN = ("**本篇的三家源全在站外**，分属软件工程、数字保存与条约法、演化遗传学——三家谁也不读谁，"
          "却在同一个事实上给出不能并存的判决。下面三条给出可直接点开核对的原始出处。"
          "正文第二节逐一交代三家各自说到了哪一步，第三节把三处对顶写死，第五节说明它们各自为什么看不见本文那一格，"
          "第十三节再与九种最容易被混为一谈的说法逐条分界——**包括本文承认最可能把它吸收掉的那一个**。")

SOURCES = [
    ("软件工程 · 不要重复原则（Hunt & Thomas, 1999）",
     "每一条知识，在一个系统之内必须有单一的、无歧义的、权威的表示",
     "https://en.wikipedia.org/wiki/Don't_repeat_yourself",
     "它说的不是「不要复制粘贴」——两段代码长得一样却表达不同的事，不算违反；长得完全不同却表达同一条规则，才是。"
     "**与本文的分离线**：这一家的处方是减少份数；本文说份数与危害无关，要改的是预期或机制。"
     "一个有五百份副本、明确宣布不预期一致的生态，按它判是极端违规，按本文判是健康。"),
    ("数字保存与条约法 · 多副本互校，不设正本",
     "多存几份并且不断互相比对，按多数修复；多语种条约各文本同等作准，歧义时依条约目的解释",
     "https://en.wikipedia.org/wiki/LOCKSS",
     "它的关键动作不是复制，是校验；而它主动取消正本，是为了让权威落在**程序**上而不落在**某一份**上。"
     "**与本文的分离线**：这一家假设一致总是目标，因而在「不预期一致」的场合给不出任何指导；"
     "而在本文那最坏的一格里，加副本只会更糟——它的药在那里是毒。"),
    ("演化遗传学 · 基因重复（Ohno 1970；Force et al. 1999）",
     "复制之后一份继续供着原功能，另一份因而承受得起突变；或两份各丢掉不同部分而都被保住",
     "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1460548/",
     "这条路径被认为是生物学创新的主要来源，而它成立的前提是没有任何机制要求两份一致。"
     "**与本文的分离线**：这一家的世界里没有「预期」这个变量——基因组里没有人期待两份一样，"
     "所以「以为该一样、其实不一样」这种情形在那里根本不成立，而那正是前两家吵得最凶的地方。"),
]

SIBLING = ("本栏另有两篇与本篇形状相近而问题不同，正文里已各划一刀。《我们说的「本来的样子」，是我们造出来的》处理的是"
           "**原物够不着**时各领域如何应对，问题是缺口怎么填；本篇的所有副本都在手边，问题是它们之间谁说了算——"
           "一份人人都能打开、只是各自改过的文档，在那一篇里不构成问题，在本篇这里正是最坏的一格。"
           "《痕迹能不能被复制，决定了这门学科相信什么》问的是痕迹的可复制性如何塑造一门学科的默认判断，"
           "自变量在**证据的物理性质**上；本篇的自变量在**看着副本的人有没有预期**上，两者正交。")

BANNED = ("发生学", "发现学", "本体论", "存在论", "显露态", "特征纠缠", "差异序列",
          "SDE", "金点子", "二阶", "碰撞出典范", "近邻划界", "五重检验", "候选判断")


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
            t = ['<div class="tblwrap"><table class="tbl">']
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
           ".tblwrap th,.tblwrap td{border:1px solid rgba(126,154,85,.35);padding:.55rem .7rem;text-align:left;"
           "vertical-align:top;line-height:1.75}.tblwrap th{background:rgba(126,154,85,.10);font-weight:700}"
           "ul.pl{margin:0 0 1.1rem 1.4rem}ul.pl li{margin-bottom:.5rem;line-height:1.95}"
           "blockquote{margin:1.6rem 0;padding:1rem 1.3rem;border-left:3px solid #7E9A55;"
           "background:rgba(126,154,85,.07);font-weight:600}\n")


def build_page(body, toc, pages, wan):
    t = TPL.read_text(encoding="utf-8")
    t = re.sub(r"<title>.*?</title>",
               f"<title>{TITLE}——{SUB[:56]} · 学科通融 | SDE Universes</title>", t, flags=re.S)
    t = re.sub(r'(<meta name="description" content=")[^"]*(")',
               lambda m: m.group(1) + html.escape(re.sub(r"\*\*", "", DECK)[:190], quote=True) + m.group(2), t)
    t = re.sub(r'<h1 class="art-title">.*?</h1>', f'<h1 class="art-title">{TITLE}</h1>', t, flags=re.S)
    t = re.sub(r'<(p|div) class="art-sub">.*?</\1>', f'<div class="art-sub">{SUB}</div>', t, flags=re.S)
    t = re.sub(r'<div class="art-meta">.*?</div>',
               f'<div class="art-meta">{BYLINE} · 约 {wan} 万字 · {pages} 页 · '
               f'三种阅读方式 · 发表于{PUBDATE}</div>', t, flags=re.S)
    t = re.sub(r'<div class="art-series">.*?</div>',
               f'<div class="art-series">学 科 通 融 · {ORD} · {FIELDS}</div>', t, flags=re.S)
    t = re.sub(r'<div class="deck">.*?</div>', f'<div class="deck">{strongify(DECK)}</div>', t, flags=re.S)
    t = t.replace("suture-to-death.pdf", f"{SLUG}.pdf")
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
    assert not hit, f"正文残留行话：{hit}"
    return t


def add_card(pages, wan):
    f = CF / "index.html"
    t = f.read_text(encoding="utf-8")
    before = t.count('class="item"')
    assert SLUG not in t, "卡片已存在"
    trio = "".join(f'<div><b>{html.escape(k)}</b><a href="{u}">{html.escape(ti)}</a></div>'
                   for k, ti, u, _g in SOURCES)
    card = (f'<div class="item"><div class="n">{ORD} · 三学科交叉：{FIELDS}（三家源全在站外）</div>'
            f'<h2><a href="/confluence/{SLUG}/">{html.escape(TITLE)}</a></h2>'
            f'<p class="sub">{html.escape(SUB)}</p>'
            f'<p class="hk">{html.escape(DECK.replace(chr(42)+chr(42), ""))}</p>'
            f'<div class="trio">{trio}</div>'
            f'<a class="rdmore" href="/confluence/{SLUG}/">读全文 →</a>'
            f'<div class="meta">约 {wan} 万字 · {pages} 页 · 三种读法 · 作者 {BYLINE} · '
            f'发表于{PUBDATE}</div></div>\n')
    a = "</main>"
    assert t.count(a) == 1, t.count(a)
    t = t.replace(a, card + a, 1)
    assert t.count('class="item"') == before + 1
    f.write_text(t, encoding="utf-8")
    print("  栏目页：追加一张卡，现共 %d 篇" % t.count('class="item"'))


def main():
    body, toc = md_to_html(SRC.read_text(encoding="utf-8"))
    txt = re.sub(r"<[^>]+>", "", body)
    n = len(re.findall(r"[\u4e00-\u9fff]", txt))
    wan = round(n / 10000, 1)
    d = CF / SLUG
    d.mkdir(exist_ok=True)

    pages = 18
    for guess in (18, None):
        (d / "index.html").write_text(build_page(body, toc, guess or pages, wan), encoding="utf-8")
        subprocess.run([sys.executable, "tools/build_pdf_paradigm.py",
                        f"public/confluence/{SLUG}/index.html", "-o", f"public/confluence/{SLUG}/{SLUG}.pdf"],
                       cwd=str(ROOT), check=True, stdout=subprocess.DEVNULL)
        from pypdf import PdfReader
        pages = len(PdfReader(str(d / f"{SLUG}.pdf")).pages)
    probe = subprocess.run(["pdftotext", "-f", "1", "-l", "1", str(d / f"{SLUG}.pdf"), "-"],
                           capture_output=True, text=True).stdout
    assert re.search(r"[\u4e00-\u9fff]", probe), "PDF 首页抽不出中文"

    rd = (CF / "suture-to-death" / "read.html").read_text(encoding="utf-8")
    rd = rd.replace("suture-to-death", SLUG).replace("缝合致死", TITLE)
    rd = re.sub(r"\d+ 页 · 王德生 ＋ Claude", f"{pages} 页 · {BYLINE}", rd)
    (d / "read.html").write_text(rd, encoding="utf-8")

    add_card(pages, wan)
    print(f"  {SLUG}: {n} 字 · {pages} 页 · 目录 {len(toc)} 节 · {ORD}")


if __name__ == "__main__":
    main()
