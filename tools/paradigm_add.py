# -*- coding: utf-8 -*-
"""把《账外的东西》并入已存在的典范文专栏。

另一个会话先建了 /paradigm/ 与之一《一拿出来，就不是它了》，版式更完整
（进度条·目录·来源盒·回顶）。同栏两篇不该长得不一样，所以本脚本：
  1. 以 taken-out/index.html 为版式模板重建 off-ledger 页
  2. 把 off-ledger 作为「之2」插进既有专栏索引（不动之一）
  3. 两篇互相点名（同栏同署名，必须交代彼此关系）
"""
import html
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PZ = ROOT / "public" / "paradigm"
TPL = PZ / "taken-out" / "index.html"
SRC_MD = Path("/home/claude/paradigm/off-ledger.md")
SLUG = "off-ledger"
PUBDATE = "2026年7月27日"

TITLE = "账外的东西"
SUB = "为什么一记账，它就不见了"
SCORE = 150
DECK = ("一对夫妻吵到最凶时的一杯水，一个画了十一年没卖出去一张画的人，一套被判定「无害」因而没人监管了三十年的医学——"
        "三件毫不相干的事，共用同一个形状：那个起决定作用的动作，当时都没有人在给它记账；"
        "而如果当时有人记账，那件事就不会发生。文章追出账本为什么会改变被它记录的东西，"
        "给出四条会反复撞上的规矩，并在八个行当里把它写成真两难——每一次记账，你都在同时得到频次、失去分量。")

COLLIDE = ("第一篇说关键原料不在你手里、必须由对方交付；第二篇说一旦有人接住你就不算数、必须自己独扛；"
           "第三篇说恰恰是被排斥、被判定无害，那个东西才长得出来。三个答案回答的是同一个问题——"
           "那种真正扛得住的分量到底从哪儿来——而且两两冲突。")

SOURCES = [
    ("亲密关系心理学", "爱的他手性：亲密关系根基的一个生成假说",
     "/students/qin-li/other-handedness/",
     "让人在冲突顶点仍能不回击的那层底子，其核心原料不掌握在自己手中。"),
    ("艺术哲学", "存押：艺术作为代偿时代中存在的不可逆赌注",
     "/students/qin-li/existential-stake/",
     "无保底、不可逆、自己独担代价，那个动作才在人身上留下不可删除的一笔。"),
    ("卫生政策与制度分析", "边缘的逆生产：制度化排斥逻辑下功能权威的意外生成",
     "/students/qin-li/reverse-production/",
     "被授予一个无威胁的次级身份，意外地换来了一块不被严格审查的生长空间。"),
]

SIBLING = ("本栏之三《账本记不下的那样东西》与本篇是同一条线上的两半，必须说清楚，否则读者会以为是重复。"
           "那一篇做的是**记录端**：账本能记下「做了什么」，记不下「有人为此把自己搭进去了」，"
           "以及为什么一旦写进要求就不再是自愿的。本篇不重走这一步，本篇做的是**转移端**——"
           "那样东西既然真的存在，它是从谁身上到谁身上的：谁少了一块，那一块在谁身上变成了厚度，"
           "为什么两边的账本都不记这一笔，以及它需要什么条件才划得动。"
           "两篇共用了《存押》作为源文之一，因此画家那个例子的形状会有些像，这是同源，不是巧合。"
           "合起来读是完整的，各自读则各缺一半。"
           "本栏之一《一拿出来，就不是它了》切的是另一刀：「取出来」是空间上的搬动，「记下来」是时间上的留痕，"
           "两者常同时发生但可以分开——本篇第十一节那个「记录但不打断」的设计，就是用来把这两样分开检验的。")


def strongify(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    return s


def md_to_html(md: str):
    out, para, toc, n = [], [], [], 0

    def flush():
        if para:
            out.append("<p>" + strongify(" ".join(para)) + "</p>")
            para.clear()

    for raw in md.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush(); continue
        if line.strip() == "---":
            flush(); out.append("<hr>"); continue
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            flush()
            lvl, txt = len(m.group(1)), m.group(2).strip()
            if lvl == 1:
                continue
            if lvl == 2:
                n += 1
                out.append(f'<h2 id="s{n}">{strongify(txt)}</h2>')
                toc.append((f"s{n}", txt))
            else:
                out.append(f"<h{lvl}>{strongify(txt)}</h{lvl}>")
            continue
        para.append(line.strip())
    flush()
    return "".join(out), toc


def build_page(body: str, toc, pages: int) -> str:
    t = TPL.read_text(encoding="utf-8")
    # 头部字段
    t = re.sub(r"<title>.*?</title>", f"<title>{TITLE}——{SUB} · 典范文专栏 | SDE Universes</title>", t, flags=re.S)
    t = re.sub(r'(<meta name="description" content=")[^"]*(")',
               lambda m: m.group(1) + html.escape(DECK[:190], quote=True) + m.group(2), t)
    t = re.sub(r'<h1 class="art-title">.*?</h1>', f'<h1 class="art-title">{TITLE}</h1>', t, flags=re.S)
    t = re.sub(r'<p class="art-sub">.*?</p>', f'<p class="art-sub">{SUB}</p>', t, flags=re.S)
    t = re.sub(r'<div class="art-meta">.*?</div>',
               f'<div class="art-meta">王德生 ＋ Claude · 约 2.2 万字 · {pages} 页 · 三种阅读方式 · 发表于{PUBDATE}</div>', t, flags=re.S)
    t = re.sub(r'<div class="art-series">.*?</div>',
               '<div class="art-series">每 日 必 读 · 典 范 文 · 之 六</div>', t, flags=re.S)
    # deck
    t = re.sub(r'<div class="deck">.*?</div>', f'<div class="deck">{strongify(DECK)}</div>', t, flags=re.S)
    # toc
    links = "".join(f'<a href="#{i}">{html.escape(x)}</a>' for i, x in toc)
    t = re.sub(r'<div class="toc">.*?</div>\s*(?=<h2|<p|<hr)',
               f'<div class="toc"><div class="tl">目 录</div>{links}</div>\n', t, flags=re.S)
    # 正文：toc 结束到 src 开始之间整段换掉
    i = t.index('<div class="toc">'); i = t.index("</div>", t.index(links)) + 6
    j = t.index('<div class="src">')
    t = t[:i] + "\n" + body + f'\n<hr>\n<h2 id="sib">附：与本栏另外两篇的关系</h2><p>{strongify(SIBLING)}</p>\n' + t[j:]
    # 来源盒
    ones = "".join(
        f'<a class="one" href="{u}"><div class="k">{html.escape(k)}</div>'
        f'<div class="t">{html.escape(ti)}</div><div class="g">{html.escape(g)}</div></a>'
        for k, ti, u, g in SOURCES)
    t = re.sub(r'<div class="src">.*?</div>\s*(?=<div class="endbox">)',
               f'<div class="src"><div class="sl">这一篇由哪三篇撞成</div>'
               f'<p class="sd">{strongify(COLLIDE)}</p>{ones}</div>\n', t, flags=re.S)
    assert t.count("<html") == 1 and t.count("</html>") == 1
    for w in ("发生学", "本体论", "存在论", "显露", "纠缠", "裂缝", "金点子", "回写"):
        assert w not in t, f"术语残留 {w}"
    return t


def build_print(body: str) -> str:
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><title>{TITLE}</title>
<style>@page{{size:A4;margin:20mm 18mm}}
body{{font-family:"Noto Serif CJK SC","Source Han Serif SC",serif;font-size:11.5pt;line-height:1.85;color:#1a1a1a}}
h1{{font-size:21pt;margin:0 0 6pt;text-align:center}}
.sub{{text-align:center;font-size:12pt;color:#555;margin:0 0 4pt}}
.by{{text-align:center;font-size:10.5pt;color:#666;margin:0 0 18pt}}
h2{{font-size:14pt;margin:20pt 0 8pt;border-bottom:1px solid #ccc;padding-bottom:4pt}}
h3{{font-size:12.5pt;margin:14pt 0 6pt}} h4{{font-size:11.8pt;margin:12pt 0 5pt;color:#444}}
p{{margin:0 0 9pt;text-align:justify}} hr{{border:0;border-top:1px solid #ddd;margin:14pt 0}}
.src{{border:1px solid #bbb;padding:10pt 12pt;margin:0 0 16pt;font-size:10.5pt;background:#fafafa}}
.src ol{{margin:6pt 0;padding-left:16pt}}</style></head><body>
<h1>{TITLE}</h1><div class="sub">{SUB}</div>
<div class="by">王德生 ＋ Claude　·　{PUBDATE}　·　SDE Universes 每日必读 · 典范文 · 之六</div>
<div class="src"><b>本篇由这三篇撞成</b><ol>{''.join(
    f'<li>《{ti}》—— {k}：{g}</li>' for k, ti, u, g in SOURCES)}</ol>{strongify(COLLIDE)}</div>
{body}
<hr><h2>附：与本栏另外两篇的关系</h2><p>{strongify(SIBLING)}</p>
</body></html>"""


def main():
    body, toc = md_to_html(SRC_MD.read_text(encoding="utf-8"))
    d = PZ / SLUG
    d.mkdir(exist_ok=True)

    pf = d / "_p.html"
    pf.write_text(build_print(body), encoding="utf-8")
    pdf = d / f"{SLUG}.pdf"
    subprocess.run(["wkhtmltopdf", "--enable-local-file-access", "--encoding", "utf-8",
                    "--footer-center", "[page]", "--footer-font-size", "9", str(pf), str(pdf)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    pf.unlink()
    pages = int(subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True)
                .stdout.split("Pages:")[1].split()[0])

    (d / "index.html").write_text(build_page(body, toc, pages), encoding="utf-8")

    # 阅读器沿用之一的写法
    rd = (PZ / "taken-out" / "read.html").read_text(encoding="utf-8")
    rd = rd.replace("taken-out", SLUG).replace("一拿出来，就不是它了", TITLE)
    (d / "read.html").write_text(rd, encoding="utf-8")

    n = len(re.sub(r"<[^>]+>", "", body))
    print(f"  {SLUG}: {n} 字 · {pages} 页 · 目录 {len(toc)} 节")
    return pages, round(n / 10000, 1)


if __name__ == "__main__":
    main()
