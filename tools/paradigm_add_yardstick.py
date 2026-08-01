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
SRC = ROOT / "tools" / "paradigm_yardstick_body.txt"
SLUG = "predictable-yardstick"
PUBDATE = "2026年8月1日"
FIELDS = "政治人类学 × 社会测量学 × 劳动经济学（本篇撞的是站外三家理论）"
BYLINE = "王德生 ＋ Claude"

TITLE = "可预期的尺子"
SUB = ("一个领域被评价体系覆盖得越久，它提出的问题就越像。三家成熟解释各有证据，"
       "却对同一批案例给出互相取消的预测——最粗糙的判断本该最坏却最好，最不可量化的裁量本该是解药却更保守。"
       "本文认为三家都漏掉了同一件事：那把尺子是公开的，被量的人能提前推断出它会怎么量。")
DECK = ("同一笔钱，两种发法：一种要你先交一份写清「你打算做什么」的计划书，"
        "另一种不问你要做什么、只看你是谁。按「简化摧毁复杂性」的说法，后者粗糙到极点，本该最糟；"
        "实测却是后者产出的新东西更多。按「指标一旦成为目标就被操纵」的说法，把裁量权交还给同行专家应当是解药；"
        "实测却是专家评审密集的那一侧更保守，而且**没有任何人作弊**。本文认为三家解释都盯着尺子的一个属性——"
        "粗细、时机、期限——却把同一件事当成了不需要说明的背景：**这把尺子是公开的，被量的人能提前推断出它会怎么量**。"
        "由此得到一条判断：**选题的收敛不是简化的代价，也不是博弈的产物，而是判据可被提前推断的直接后果**；"
        "它与判据粗细无关、与合同期限无关，且不必等任何一次测量真的发生。机制只有三步——预演、筛选、回流——"
        "全程不需要假设任何人不诚实。文末给十处跨领域读数、两处反过来迫使它让步的地方、六条能推翻它的条件"
        "（第一条只要公开文本和一台电脑），以及一条写死到 2032 年的赌注。")

ORIGIN = ("**本篇撞的是站外三家理论，不是站内学员论文**（同本栏之八、之九、之十的口径）。"
          "三家分属政治人类学、社会测量学与劳动经济学，都在解释同一个现象——被评价体系覆盖得久了，"
          "一个领域提出的问题会越来越像——而它们对同一批案例给出的预测互相取消。"
          "下面三条给出可直接点开核对的原始出处。正文第二至第四章逐一交代三家各自说到了哪一步，"
          "第五章把三对矛盾写死，第九章说明它们为什么各自推不出本文这一条，"
          "第十二章再与另外七种最容易被混为一谈的说法逐条分界——**包括与本文离得最近、"
          "且本文承认最可能被它吸收的那一个**。")

SOURCES = [
    ("可读性 · 詹姆斯·斯科特（1998）",
     "Seeing Like a State：国家为了看见而简化，简化摧毁了长在情境里的那种本事",
     "https://yalebooks.yale.edu/book/9780300246759/seeing-like-a-state/",
     "德国科学林业把混生杂木改造成等距成行、可清点的人工林，第一代长势极好，第二代土壤板结虫害成片。"
     "**与本文的分离线**：那一家按简化程度排序，把最粗的判断排在最坏一端；本文把它排在最好一端——"
     "同一个案例，相反的排序。"),
    ("反身性 · 埃斯佩兰 与 索德（2007）",
     "Rankings and Reactivity：公共测度不是在描述世界，是在重造它所测量的世界",
     "https://www.semanticscholar.org/paper/8e382703b550774b98c1d928b85a3855db6c1e48",
     "法学院排名一出，招生策略、就业数据口径、奖学金分配全部朝那几个被计入的量重新组织。"
     "**与本文的分离线**：那一家的时序是先测量、后反应；本文的机制在测量之前就闭合了——"
     "一条新判据刚公布、第一轮结果还没出来时，那一家预测无变化，本文预测申请文本的语言已经跃升。"),
    ("资助契约 · 阿祖莱、格拉夫·齐文 与 曼索（2011）",
     "Incentives and Creativity：容忍早期失败、拉长周期的资助，换来了更高的新颖度",
     "https://www.nber.org/papers/w15466",
     "以人为单位、明写容忍失败的资助，其研究者的高影响力论文与新关键词都更多，同时低引用的失败品也更多。"
     "**与本文的分离线**：那一家把差别全部归给期限与容错；本文预测，把期限与容错完全对齐、"
     "只改「要不要先交一份研究计划」，两条通道的选题分布仍会显著不同。"),
]

SIBLING = ("本栏另有一篇《别人怎么成的，学不来；别人怎么垮的，学得来》，同样撞的是站外三家在世学者，"
           "讲的是一个结论能走多远——成功是一长串「并且」，失败是一连串「或者」。"
           "那一篇管**知识能不能搬**，本篇管**知识被谁的尺子量**；两篇合起来是同一件事的两头："
           "我们几乎全部的学习制度都建在搬不走的那一半上，而我们几乎全部的评价制度都建在可被提前推断的那一种尺子上。"
           "另有《能停下来，是因为不必交代》讲一件事必须持续证明自己值得继续时就再也停不下来，"
           "与本文第十四章那笔「不可预期与不可问责只隔一层纸」的账是同一个结构。")

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
