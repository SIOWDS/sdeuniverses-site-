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
SRC = ROOT / "tools" / "paradigm_channel_body.txt"
SLUG = "once-said-its-gone"
PUBDATE = "2026年8月1日"
FIELDS = "生成语法 × 发展心理学与灵长类认知 × 认知科学与语言演化（本篇撞的是站外三家理论）"
BYLINE = "王德生 ＋ Claude"

TITLE = "说过去就没了"
SUB = ("同样一门语言，三岁孩子不用人教就能用起来，写下来却能复杂到没人听得懂。"
       "四种成熟解释各有实验撑着，却互相取消——输入究竟是穷是富、重点在知识还是在时间、"
       "因果箭头指向听的人还是说的人。本文认为四家漏掉了同一件事：一段话说过去就没了，你没法请它重来。")
DECK = ("有一种句子在纸上很常见：把主语说出来，插进去一整段限定，再回来给它谓语。"
        "跨七种欧洲语言的语料清点显示，这种「中间套」在书面语里最深只到三层，"
        "而在口语里连两层都罕见到近乎不存在；更要命的是，**它是随着书面语的出现才被造出来的**。"
        "与此同时，一路往后接的长句在口语里活得好好的，能接到三四层。"
        "**限制挑的不是难度，是形状**——被筛掉的偏偏是那种要求你把一个成分悬在半空、"
        "越过一段材料再回来接住的结构。本文由此提出：塑形语言的不是输入的贫乏、不是社会互动的丰富、"
        "也不是记忆的容量，而是**信道让不让你回头**，以及回头的代价由谁承担；"
        "而这个量与记忆容量、与呈现速度、与看还是听，三者都正交——"
        "**给足记忆而不许回头，同一批结构照样长不出来**。文末给十处跨领域读数、"
        "两处反过来迫使它让步的地方、一个用现成范式一个下午就能跑的四组实验"
        "（三家解释在这一个实验里给出三种不同的分组），以及一条写死到 2031 年的赌注。")
ORIGIN = ("**本篇撞的是站外三家理论，不是站内学员论文**（同本栏之八、之九、之十的口径）。"
          "三家都在解释同一件事——孩子凭什么学会、语言又为什么长成这个形状——而给出的归因互相取消："
          "一家说输入太穷所以必须有先天骨架，一家说输入其实足够只要把社会认知算进去，"
          "第三家说穷不穷根本不是重点、重点是它不等人。第三家内部还有一场没打完的仗，"
          "同期评论直接顶回去：记忆限制是可变的，解释不了结构那么整齐的规律。"
          "下面三条给出可直接点开核对的原始出处。正文第二至第四章逐一交代四家说到了哪一步，"
          "第五章把矛盾写死，第九章给出一条已经躺在语料里、四家都不预测其形状的读数，"
          "第十三章再与另外五种最容易被混为一谈的说法逐条分界——**其中第一位是本文承认最可能吸收掉自己的那一个**。")
SOURCES = [
    ("生成语法 · 乔姆斯基一脉",
     "刺激的贫乏：孩子听到的话不足以支持他最终掌握的规则，多出来的那部分必须是先天的",
     "https://www.semanticscholar.org/search?q=poverty%20of%20the%20stimulus",
     "论证的形状是：结论超出了证据，因此差额来自骨架。"
     "**与本文的分离线**：它把孩子听到的东西记成一个**集合**，而集合没有时间也没有次数——"
     "一句话听过之后能不能倒回去再听一遍，在集合里根本没有位置。"),
    ("发展心理学与灵长类认知 · 托马塞洛",
     "基于用法的习得：语言长在共同注意与意图理解上，语法是从大量具体用例里抽出来的",
     "https://www.hup.harvard.edu/books/9780674017641",
     "先有「我们此刻在共同关心同一件事」，才有指着某物说出一个词。"
     "**与本文的分离线**：它把互动与「没懂就再说一遍」捆成了一体，"
     "于是推不出这样一个问题——把共同注意与用例数量全部保持不变，只拿掉「再说一遍」，会怎样。"),
    ("认知科学与语言演化 · 克里斯蒂安森与查特（2016）",
     "The Now-or-Never Bottleneck：记忆转瞬即逝，语言必须当场被压缩与递交，否则永远失去",
     "https://pubmed.ncbi.nlm.nih.gov/25869618/",
     "这条约束被推得极宽：处理、习得、历时演变乃至结构本身，都是它的下游。"
     "**与本文的分离线**：它把「记忆转瞬即逝」与「材料不可重取」当成了同一件事——"
     "在面对面说话时二者确实同时出现，但可以分开：给足记忆而不许回头，同一批结构照样长不出来。"),
]
SIBLING = ("本栏另有一篇《谁说了这一次到此为止》，讲的是练习里的同一类事——「一次」的边界由谁划，"
           "决定了什么东西被当作可比较的两次。那一篇管**边界**，本篇管**能不能回去**："
           "一个说这段活动到哪儿算完，一个说完了之后还能不能再取一遍。"
           "另有《可预期的尺子》讲判据能否被提前推断如何决定一个领域还提得出什么问题——"
           "三篇合起来是同一个形状的三处：**决定长出什么的，往往不是内容，是内容所在的那条管子的性质**。")
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
