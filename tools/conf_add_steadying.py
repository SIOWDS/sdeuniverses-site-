# -*- coding: utf-8 -*-
"""把《你站稳的动作，就是推它的动作》并入「学科通融」，之二十。

三源全在站外（非线性动力学 / 结构工程 / 音乐表演研究），领域由本次写作自选。
骨架取同栏 two-chain-type，并修掉它从 /paradigm/ 复制时残留的页尾两处。
"""
import html, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CF = ROOT / "public" / "confluence"
TPL = CF / "two-chain-type" / "index.html"
SRC = ROOT / "tools" / "conf_steadying_body.txt"
SLUG = "steadying-is-pushing"
PUBDATE = "2026年8月1日"
ORD = "之二十二"
FIELDS = "非线性动力学 × 结构工程 × 音乐表演研究"
BYLINE = "王德生 ＋ Claude"

TITLE = "你站稳的动作，就是推它的动作"
SUB = ("一群人为什么会突然齐步：不取决于耦合有多强，取决于他们共同参照的那个东西会不会把他们的对齐攒起来。"
       "危险只出在参照物既回应参与者、又有惯性的那一格。")
DECK = ("二〇〇〇年六月十日，伦敦千禧桥开放。桥先是静的，然后轻轻地晃，然后几乎从一个瞬间到下一个瞬间，"
        "桥上的人开始像刚学溜冰那样两脚岔开、每一步都往侧面撑——几乎整齐划一，而没有人打算这么走。"
        "这件事被三个行当各自拿去，判决互相取消：**非线性动力学**说自发锁相是耦合振子的自然归宿，是自然界最漂亮的秩序之一；"
        "**结构工程**说同一个机制是灾难，处方是加阻尼、切断反馈；**音乐表演研究**说合奏的目标就是对齐，"
        "而多项实证发现完全量化的节奏被评为最好——「偏差本身有价值」这个流行说法被自己人的数据打掉了。"
        "本文论证三家漏掉了同一个变量：它不在参与者身上，也不在耦合强度上，而在**大家共同参照的那个东西是什么样的东西**。"
        "把参照物拆成两条独立的轴——**它回不回应参与者，它有没有惯性**——得到四格，只有一格会过冲。"
        "千禧桥是那一格最干净的演示：行人为了站稳而做的横向调整，恰好落在给桥注入能量的相位上，"
        "**你站稳的动作，就是推它的动作**——不需要任何人知道别人的存在。文末给一分钟判据与半小时查法、"
        "十四处跨领域读数、两处反过来迫使本文让步的约束（电网惯量；音乐实证的测法之争）、六条判错条件，"
        "以及一条写死到 2033 年的赌注。")

ORIGIN = ("**本篇的三家源全在站外，三个领域由本次写作自行选定**（不是随机抽取），"
          "标准是彼此尽可能远：一支是数学，一支是土木，一支是音乐学，三家谁也不读谁，"
          "却在同一件事上给出不能并存的处方。下面三条给出可直接点开核对的原始出处。"
          "正文第二节逐一交代三家各自说到了哪一步，第三节把三处对顶写死，"
          "第十三节再与十一种最容易被混为一谈的说法逐条分界——**包括本文承认最可能把它吸收掉的那一个**。")

SOURCES = [
    ("非线性动力学 · 耦合振子的自发同步（Kuramoto 1975；Strogatz 2000）",
     "一群频率略有差异的振子，只要耦合超过临界值就会自发锁相——不需要指挥",
     "https://www.sciencedirect.com/science/article/abs/pii/S0167278900000944",
     "萤火虫齐闪、心脏起搏细胞、同一屋檐下的挂钟，用的是同一套式子。"
     "**与本文的分离线**：这一家为了可解，把中介写成一个即时合成的**平均量**——它没有自己的动力学，不储存任何东西。"
     "而那正是下一家出事的地方。同样的耦合强度，换一个会攒的中介，结局完全不同。"),
    ("结构工程 · 千禧桥的横向同步激励（Dallard et al. 2001；Strogatz et al. 2005；Belykh et al. 2021）",
     "行人为在晃动桥面上站稳而做的横向调整，恰好给桥补充能量——人群成了负阻尼",
     "https://www.nature.com/articles/438043a",
     "处方是加阻尼器，问题就此解决。而二〇二一年那项工作更进一步：**这类失稳可以在行人之间没有相位同步的情况下发生**，"
     "同步是后果不是原因。**与本文的分离线**：工程把加阻尼读成「削弱耦合」，本文读成「减少中介的储能」——"
     "两种读法在桥上一致，在榜单、市场这类没有物理中介的地方完全分开。"),
    ("音乐表演研究 · 微时序与 groove（Frühauf, Kopiez & Platz 2013）",
     "把鼓点提前或延后十五、二十五毫秒请人评分，结果是量化版最高、偏差越大越低，且提前比延后更差",
     "https://journals.sagepub.com/doi/abs/10.1177/1029864913486793",
     "另有研究换成测身体反应，得到不同结果，且效应随体裁变化——这一家自己还在吵。"
     "**与本文的分离线**：这一家把注意力全放在偏差的大小与方向上，从不问参与者是**跟着什么**在对齐；"
     "而多数实验用的恰好是一个不回应的时钟，因而它只占本文四格里的一格。"),
]

SIBLING = ("本栏另有两篇与本篇形状相近而问题不同。《哪一份算数》问的是同一样东西存了好几份时谁说了算，"
           "自变量在**参照物的权威归属**上；本篇的自变量在**参照物的动力学性质**上（回不回应、会不会攒），两者正交——"
           "一个权威归属清清楚楚的参照物，照样可以是会攒的那一种。"
           "《可预期的尺子》问的是判据能否被参与者提前推断，自变量是**认知的**；本篇的自变量是**动力学的**："
           "一个完全不可预期、谁也猜不到的实时榜单，按那一篇不该趋同，按本篇仍会过冲——参与者不需要预测它，只需要跟随它。")

BANNED = ("发生学", "发现学", "显露态", "特征纠缠", "差异序列", "裂缝",
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


CSS_ADD = ("\n.tblwrap{overflow-x:auto;margin:1.6rem 0}"
           "ul.pl{margin:0 0 1.1rem 1.4rem}ul.pl li{margin-bottom:.5rem;line-height:1.95}\n")


def build_page(body, toc, wan):
    t = TPL.read_text(encoding="utf-8")
    t = re.sub(r"<title>.*?</title>",
               f"<title>{TITLE}——{SUB[:50]} · 学科通融 | SDE Universes</title>", t, flags=re.S)
    t = re.sub(r'(<meta name="description" content=")[^"]*(")',
               lambda m: m.group(1) + html.escape(re.sub(r"\*\*", "", DECK)[:190], quote=True) + m.group(2), t)
    t = re.sub(r'<h1 class="art-title">.*?</h1>', f'<h1 class="art-title">{TITLE}</h1>', t, flags=re.S)
    t = re.sub(r'<(p|div) class="art-sub">.*?</\1>', f'<div class="art-sub">{SUB}</div>', t, flags=re.S)
    t = re.sub(r'<div class="art-meta">.*?</div>',
               f'<div class="art-meta">{BYLINE} · 约 {wan} 万字 · 三种阅读方式 · 发表于{PUBDATE}</div>',
               t, flags=re.S)
    t = re.sub(r'<div class="art-series">.*?</div>',
               f'<div class="art-series">学 科 通 融 · {ORD} · {FIELDS}</div>', t, flags=re.S)
    t = re.sub(r'<div class="deck">.*?</div>', f'<div class="deck">{strongify(DECK)}</div>', t, flags=re.S)
    t = t.replace("two-chain-type.pdf", f"{SLUG}.pdf")
    t = t.replace("</style>", CSS_ADD + "</style>", 1)

    # 修掉骨架从 /paradigm/ 复制时残留的页尾两处
    t = t.replace('<a href="/paradigm/">返回每日必读 →</a>', '<a href="/confluence/">返回学科通融 →</a>')
    t = t.replace("<footer>每日必读 · 典范文 · 作者", "<footer>学科通融 · 三学科交叉 · 作者")

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
    assert "返回每日必读" not in t and "每日必读 · 典范文 · 作者" not in t, "页尾没改干净"
    assert 'class="tbl"' in t, "2×2 没渲染成真表"
    for i2, _ in toc:
        assert f'id="{i2}"' in t, f"锚点缺失 {i2}"
    return t


def add_card(pages, wan):
    f = CF / "index.html"
    t = f.read_text(encoding="utf-8")
    before = t.count('class="item"')
    assert SLUG not in t, "卡片已存在"
    trio = "".join(f'<div><b>{html.escape(k)}</b><a href="{u}">{html.escape(ti)}</a></div>'
                   for k, ti, u, _g in SOURCES)
    card = (f'<div class="item"><div class="n">{ORD} · 三学科交叉：{FIELDS}（三家源全在站外，领域自选）</div>'
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
    (d / "index.html").write_text(build_page(body, toc, wan), encoding="utf-8")

    subprocess.run([sys.executable, "tools/build_pdf_confluence.py",
                    f"public/confluence/{SLUG}/index.html"], cwd=str(ROOT), check=True)
    from pypdf import PdfReader
    pages = len(PdfReader(str(d / f"{SLUG}.pdf")).pages)
    probe = subprocess.run(["pdftotext", "-f", "1", "-l", "1", str(d / f"{SLUG}.pdf"), "-"],
                           capture_output=True, text=True).stdout
    assert ORD in probe.replace(" ", ""), f"PDF 封面序号不对：{probe[:120]!r}"

    subprocess.run([sys.executable, "tools/build_reader_confluence.py", SLUG],
                   cwd=str(ROOT), check=True)

    add_card(pages, wan)
    print(f"  {SLUG}: {n} 字 · {pages} 页 · 目录 {len(toc)} 节 · {ORD}")


if __name__ == "__main__":
    main()
