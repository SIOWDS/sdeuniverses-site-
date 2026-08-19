# -*- coding: utf-8 -*-
"""把《目击位》并入「每日必读」。

三位学员分属三个不同门类，三对主题两两冲突：
  阳涌（课程论）：课程的功能位移为「有纪律地不提供」，而它要靠制度壳体才施加得上。
  高鹏（法学教育）：那一下不可被制度事先编排，教育者只能不消除艰难，不能设计艰难。
  金华（知识社会学）：被弄丢的是生成条件本身，而它只能靠在场感染，不能被传递。
三方争的是那个困境该由谁安排，而三方共享一个从未被质疑的预设：学习者必须站在困境里。
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
SRC = ROOT / "tools" / "paradigm_witness_body.txt"
SLUG = "witness-seat"
PUBDATE = "2026年8月1日"
FIELDS = "课程论 × 法学教育 × 知识社会学"
BYLINE = "王德生 ＋ Claude"

TITLE = "目击位"
SUB = "为什么点着一个人的，不是他被放进的困境，而是他在旁边看见的那一下"

DECK = ("一门研讨课上教师有原则地不回答，一间法学院的模拟法庭里赛前一晚没人管的沉默，"
        "一台只凭论文造不出来、必须有人去现场站过才能造成的机器——三件毫不相干的事里，"
        "都有一个人在旁边看着，而没有人问过他看见的是什么。"
        "关于怎样让一个人长出自己下判断的能力，眼下两条路线互相对峙：一条主张把困难设计出来，"
        "一条主张困难不能被设计、只能克制地不去填平。本文论证两条都在同一个位置上问错了——"
        "**它们都假定学习者必须站在困境里，因此只争那个困境该由谁安排**。"
        "而把一个人身上「敢自己裁」的东西点着的那一下，多数时候发生在他坐在旁边、"
        "**看见另一个人当众做了一次他自己也可能做错、且做错要由他自己承担的判断**的时刻。"
        "文章把学习者在那一刻所占的位置叫作目击位，给出「谁在裁 × 那一下可不可撤回」的四格辨别表，"
        "并接受两条从外面反过来削掉本命题的约束——一条来自学徒制研究，一条来自飞行模拟舱。")

CLASH = ("第一篇要求教师识别学生此刻的认知状态、并据此决定暂停供给；第二篇明说那一下的降临"
         "不取决于教师的识别，教育者能做的只有不消除；第三篇说前两条争的东西可能都不是关键——"
         "制度在第一步就把生成条件筛掉了，起作用的是一个已经生成过的人走进来。"
         "若第一篇对，好教师应当能提高那类瞬间的发生率；若第二篇对，他提高的只是学生"
         "在被设计的困难内部的表现；而若第三篇对，守着一条空裂缝什么也不会发生。")

SOURCES = [
    ("课程论 · 有纪律地不提供",
     "认知的禁食：AI时代课程功能的重释",
     "/students/yang-yong/cognitive-fasting/",
     "在答案可以随时被取走的环境里，课程的功能从提供位移到有纪律地不提供；"
     "而这个「不给」必须可逆、必须配补偿性条件，并且要靠一套学习者不能随意退出的制度壳体才施加得上。"),
    ("法学教育 · 不可被事先编排",
     "守护「心裁」：人工智能时代法学教育不可代偿之物的重新发现",
     "/students/gao-peng/heart-adjudication/",
     "那一下是能力被激活、在没有任何外部代偿的条件下写下不可撤回结论的瞬间；"
     "由教师设计、且事后有整合兜底的困难，在原理上已经取消了它——"
     "教育者能做的不是设计艰难，是不消除艰难。"),
    ("知识社会学 · 只能靠在场",
     "生成隔离：为什么一个领域的知识生成能力无法被制度性地传下去",
     "/students/jin-hua/generative-isolation/",
     "被制度弄丢的不是说不出来的知识，是那种知识当初被生成出来的逼迫处境；"
     "而真正异质的那份记忆无法被接收者现有的框架理解——能被理解的就证明它不异质。"),
]

SIBLING = ("本栏有三篇与本篇挨得很近，必须说清楚，否则会被读成重复。"
           "《把手拿开，他不会自动开始长》给出的是**第三种姿势**：有人在场，但不往里面放东西；"
           "《有些本事，是准备不出来的》分开了三种「先」，指出加大准备恰恰挤掉后两种；"
           "《传得下去的，都是没做完的》给出的是**空模子**：凝固下来的必须带着一处由接手者亲自补上的缺口。"
           "三篇处理的都是**那个空白该怎么留**——留多大、谁来留、留了会不会被填。"
           "本篇问的是它们都没有问过的下一句：**那个空白里，到底需要有什么。**"
           "答案不是更好的空白，是一个人——而且那个人得当着你的面，做一次他自己也可能做错的判断。")

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
    who = ('三篇来源分别出自<a href="/students/yang-yong/" style="color:var(--clay)">阳涌</a>、'
           '<a href="/students/gao-peng/" style="color:var(--clay)">高鹏</a>与'
           '<a href="/students/jin-hua/" style="color:var(--clay)">金华</a>')
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
    from paradigm_ordinal import claim, to_cn, load_ledger as load
    led = load()
    have = [int(k) for k, v in led.items() if v == f"paradigm/{SLUG}"]
    if have:
        no = have[0]
        no_card_cn = to_cn(no)
    else:
        no, no_card_cn = claim(f"paradigm/{SLUG}", title=TITLE)
    no_cn = " ".join(no_card_cn)
    no_card = "之" + no_card_cn
    print(f"  领到发布号 {no}（{no_card}）")

    body, toc = md_to_html(load_md())
    n = len(re.findall(r"[\u4e00-\u9fff]", re.sub(r"<[^>]+>", "", body)))
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
