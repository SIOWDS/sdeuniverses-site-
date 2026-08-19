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
SRC = ROOT / "tools" / "paradigm_parsing_body.txt"
SLUG = "who-calls-it-done"
PUBDATE = "2026年8月1日"
FIELDS = "专长研究 × 记忆与学习科学 × 运动控制（本篇撞的是站外三家理论，含俄语传统）"
BYLINE = "王德生 ＋ Claude"

TITLE = "谁说了这一次到此为止"
SUB = ("同样的时间投进去，有人练出了东西，有人只是把动作做旧了。三家成熟解释各有实验撑着，"
       "却互相取消——即时反馈究竟是引擎还是毒，变异究竟是噪声还是机制，可数的重复究竟真不真。"
       "本文认为三家漏掉了同一件事：「一次」的边界不是任务给的，是有人划的。")
DECK = ("一个人买了带传感器的球学颠球。第一周他做到三十七个，很高兴——直到他发现，"
        "自己进步的其实是**让传感器计数**这件事：失败的那一下屏幕上没有，于是他的全部注意力落在「不失败」上。"
        "第二周他改了一件小事：每一小段停下来，自己先说一句「刚才那算一次」，再去看屏幕。"
        "连续次数当场从三十七掉到十几，掉了三四天；而两周后上球场，能带过去的恰恰是后面那几天练的。"
        "本文认为，关于练习的三家成熟解释——重复加即时反馈、减频反馈与有益的困难、"
        "以及「根本不存在重复」——都漏掉了同一件事：**「一次」的边界不是任务给的，是有人划的**。"
        "由此得到一条判断：**练习的差别不是反馈频率的函数，也不是自主感的函数，"
        "而是「一次」的边界由谁划、划在哪里的函数**——因为没有可比较的两次，"
        "误差、间隔、难度、进度全都无从谈起。文末给十处跨领域读数、两处反过来迫使它让步的地方、"
        "六条能推翻它的条件（含一个用现成范式一个下午就能做的对照），以及一条写死到 2031 年的赌注。")
ORIGIN = ("**本篇撞的是站外三家理论，不是站内学员论文**（同本栏之八、之九、之十的口径）。"
          "三家分属专长研究、记忆与学习科学、运动控制，其中第三家出自俄语传统。"
          "它们都在解释同一件事——同样的练习量为什么长出不同的东西——而给出的处方互相取消："
          "一家要即时反馈，一家证明即时反馈损害长期保持，第三家干脆否认「重复」存在。"
          "下面三条给出可直接点开核对的原始出处。正文第二至第四章逐一交代三家说到了哪一步，"
          "第五章把三对矛盾写死，第八章说明它们为什么各自推不出本文这一条，"
          "第十一章再与另外六种最容易被混为一谈的说法逐条分界——**其中第一位是本文承认最可能吸收掉自己的那一个**。")
SOURCES = [
    ("专长研究 · 埃里克森等（1993）",
     "The Role of Deliberate Practice in the Acquisition of Expert Performance",
     "https://www.semanticscholar.org/paper/69df93e5e361c089d3ec41a1e4b37f77984bcd6e",
     "把新手与大师分开的是一种特定形态的练习：目标明确、难度在能力边缘、有即时反馈、可以立刻重来。"
     "**与本文的分离线**：它的每一个词都以「次」为坐标——累计多少次、在边缘反复、每次之后给反馈；"
     "要它把「谁来切次」当变量，等于要它把自己的坐标系当对象。"),
    ("学习科学 · 温斯坦与施密特（1990）",
     "Reduced Frequency of Knowledge of Results Enhances Motor Skill Learning",
     "https://www.semanticscholar.org/paper/d9f2ebe727d19195df73b6dcae151d987d8ad9a0",
     "每次都给结果反馈的一组，练习期表现更好；隔一天再测、且都不给反馈时，减频那一组明显更好。"
     "**与本文的分离线**：它把功劳归给「外部信息变少」；本文预测，在外部信息总量完全相同、"
     "只改由谁宣布「这一次结束」的条件下，切次权在内的一组仍然更好。"),
    ("运动控制 · 伯恩斯坦一脉与差异学习",
     "Repetition without Repetition：不存在两次相同的动作，变异本身是机制",
     "https://pubmed.ncbi.nlm.nih.gov/?term=differential+learning+Schollhorn",
     "熟练不是重复同一个动作，而是每一次都用不同的方式解决同一个问题；顺此发展的训练方法主动往每一次里塞进变化。"
     "**与本文的分离线**：它否认了物理上的重复，却默认记账上的重复仍然自动存在——"
     "恰恰因为没有物理重复，「这算同一件事的第二回」才第一次成为一个必须由谁来做的判断。"),
]
SIBLING = ("本栏另有一篇《可预期的尺子》，讲的是评价制度里的同一类事——判据能否被提前推断，"
           "决定了一个领域还提得出什么问题。那一篇管**判据**，本篇管**边界**："
           "一个说被量的人能不能猜到尺子怎么量，一个说那把尺子从哪儿下刀、由谁下。"
           "两篇合起来是同一件事的两头。另有《没有人拒绝过你》讲一个动作的消失可以不经过任何拒绝，"
           "与本文第十五章「切次不留痕，于是被默认不存在」是同一个结构。")
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
