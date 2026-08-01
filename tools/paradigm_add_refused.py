# -*- coding: utf-8 -*-
"""把《没有人拒绝过你》并入「每日必读」。

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
SRC = ROOT / "tools" / "paradigm_refused_body.txt"
SLUG = "nobody-refused-you"
PUBDATE = "2026年8月1日"
FIELDS = "家庭伦理学 × 艺术存在论 × 科学思想史（三篇源由程序随机抽出）"
BYLINE = "王德生 ＋ Claude"

TITLE = "没有人拒绝过你"
SUB = ("一个动作从一个社会里消失，通常被归给两件事：它被禁止了，或者它被抽走了资源。"
       "本文论证还有第三种，而且更深——它的必要性被更便宜地满足了。"
       "这一种关闭不经过拒绝，因此既不留下可上诉的裁定，也不在别处留下任何指纹。")
DECK = ("三个场景：一个儿子知道那笔家庭旧账是怎么被做成还不掉的，他能把每一步拆给你听，然后他照旧还不掉；"
        "一位清代学者把几年光阴投在一个冷僻字的古音上，投入的量远超他那个行当自身要求的必要量；"
        "一个人打开写作软件，还没想好第一句，屏幕上已经排好了六个开头，其中两个比他昨天想到的更顺。"
        "三处都出现了同一个读数——**某样东西没有发生**——而现有的词（压抑、剥夺、异化、退化、失传）不区分它们。"
        "本文把「关闭」拆成三层：拿走回报、拿走执行条件、拿走**必要性**。前两层都经过一次拒绝，"
        "因而在邻近领域留下超出该领域自身逻辑的过量投入；第三层不拒绝任何人，所以什么也不留。"
        "由此得到一条判断：**拒绝是指纹的唯一来源**——凡是以「去找被压抑的痕迹」为方法的研究传统，"
        "在第三层里必然空手而归，并且必然把空手而归读成「这里没问题」。文末给一张四格分辨表与四步查法、"
        "九处跨领域读数、一处反过来迫使它让步的地方（来自渔业生态学）、六条能推翻它的条件"
        "（第一条只要一支笔和一台打印机），以及一条写死到 2032 年的赌注。")

ORIGIN = ("**本篇的三篇源是随机抽出来的，不是挑出来的。** 做法：扫全站两千六百多个页面，"
          "按「正文段落汉字不少于三千、页内链接少于八十」筛出一千三百三十九篇正文文章，"
          "再以时间戳为种子随机抽取。抽出的三篇分属家庭伦理学、艺术存在论与科学思想史，"
          "对同一个读数——某样东西没有发生——给出互不相容的归因：一篇说是被主动锁死的，"
          "一篇说是维持它的力量断了补给，一篇说它根本没消失、只是改道去了别处。"
          "正文第一至第二章交代三处现象与两套现成解释各自停在哪里，第三至第四章给出分层与四格表，"
          "第五至第十一章按格展开，第十二章与最容易被混为一谈的六种说法逐条分界——"
          "**包括本文承认离得最近、也最可能把它吸收掉的那一个**。")

SOURCES = [
    ("家庭伦理学 · 《义务的债务化与痛苦的避税》",
     "功能被外部服务接走之后，家庭不但没散，反而被一笔拒绝任何偿还手段的道德旧账锁得更紧",
     "/family-ethics/non-clearing-debt/",
     "偿还的路每一条都通着，但每一条走到头都会被重新命名为「还不够」——汇款不算，探望不算，"
     "自己混得好也不算。**与本文的分离线**：那一篇的机制预设有人在维持这笔账，也预设债务人想还；"
     "本文的第三格里既没有债权人，也没有人想还——同样是「账目未结」，两种来路。"),
    ("艺术存在论 · 《守卫的漂移》",
     "不可代偿、不可撤回、亲自承担后果的那种慢判决，与可外包的快决策之间有一道边界，它正在被抹平",
     "/students/qin-li/guarding-drift/",
     "边界不是一面墙立在那里就永远在，它更像一条要被反复踩出来的山路；没人再踩，植被就盖上了。"
     "**与本文的分离线**：那一篇把边界的消失归给维持它的力量断了补给（时序性），"
     "本文归给必要性被外部满足（结构性）——同一件「没有了」，两种成因，不能同真。"),
    ("科学思想史 · 《并非缺失，而是生成》",
     "被制度拒绝供养的求真冲动不会消失，它被推进有名分的知识躯壳里，在那里留下过量的严谨",
     "/culture-tech/needham/structural-redirection/",
     "沉默是最彻底的拒绝，因为它连一份可以拿去申辩的否决都不给。"
     "**与本文的分离线**：那一篇的检索方法是「哪里有过量，哪里就曾经有被堵住的东西」；"
     "本文论证第三格里过量为零，于是那套方法在整片区域里必然空手而归，并把空手而归读成「没问题」。"),
]

SIBLING = ("本栏另有一篇《可预期的尺子》，讲一个领域为什么会越问越像——因为那把尺子是公开的，"
           "被量的人能提前推断出它会怎么量。那一篇管**判据被提前吃掉**，本篇管**动作被提前替掉**；"
           "两篇合起来是同一件事的两头：预演掉的是判断，替掉的是执行。"
           "另有《一拿出来，就不是它了》讲有些东西一被取出来就变成另一样，"
           "与本文第十一章那条「过量只在过程里可见、不在成品里可见」是同一个结构。")

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
    who = "本篇三篇源由<b>程序随机抽取</b>，三条来源均可直接点开核对"
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
