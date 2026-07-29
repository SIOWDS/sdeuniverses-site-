# -*- coding: utf-8 -*-
"""把《借来的、逼出来的、熬出来的，不是同一样东西》并入「每日必读」，作发布号之三十二（显示号由 renumber 刷成之一）。"""
import html
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PZ = ROOT / "public" / "paradigm"
TPL = PZ / "taken-out" / "index.html"
SRC = Path("/home/claude/pz/P32.txt")
SLUG = "borrowed-forced-earned"
PUBDATE = "2026年7月29日"
NO_CN = "之 三 十 二"
NO_CARD = "之三十二"
FIELDS = "劳动社会学 × 认知科学 × 道德哲学（本篇是群内碰撞：三位不同学员）"

TITLE = "借来的、逼出来的、熬出来的，不是同一样东西"
SUB = ("想不等一样东西慢慢长成就提前拿到手，无非三条路——预支（把账推给未来的你，到手的是欠条）、"
       "受迫（把账一次性重压当下，逼出真货但带伤）、慢熬（原价慢付，无债无伤的完整品）；"
       "三条路到期日不同、拿到手的东西也不同。时间的账逃不掉，你只能挑怎么付。")
DECK = ("有三个人都想早点拿到一样还没长成的东西：一个用一纸承诺把它从未来提前兑现，"
        "一个被绝境逼到没退路、硬生生逼了出来，一个还在慢慢熬。三人手里看着都叫「我有了它」，"
        "其实是三样东西——**借来的是一张欠条，逼出来的是带着伤的真货，只有熬出来的，才是无债无伤的完整品**。"
        "它们长得像，到期日和能不能用却全然不同。本文认为：**凡是「没熬够就提前到手」的，都不是白得，"
        "只是把时间的账换了付法**；而人最大的错，是把欠条当真货花、把带伤的应急版当成熟的完整版。")

COLLIDE = ("三篇给出关于「时间与形成」互不相容的答案：一篇说可以把未来预支到现在（身份预支）、"
           "一篇说绝境剥夺时间反而逼出此前不存在的东西（受迫生成）、"
           "一篇说好东西的长成需要慢、需要滞留的空间，而效率逻辑会把它驱逐（善的慢发生）。"
           "三头对齐，逼出本文的判断——所谓「不熬够就提前到手」都不是白得，只是把时间的账换了付法。"
           "**正文即从这条判断另起、用自备例子展开，不复述三篇原文**；三篇的功劳记在这里。")

SOURCES = [
    ("劳动社会学 · 刘言言",
     "身份预支：编制作为未来承诺的提前兑现装置",
     "/students/liu-yanyan/identity-advance/",
     "编制的深层吸引力不在当下更安稳，而在它把「未来的稳定」提前兑现成「现在的身份」——身份不是可持有的实体，是一次对未来承诺的预支。"),
    ("认知科学 · 胡志英",
     "受迫生成：在被剥夺了等待权的世界里，因果何以被逼出",
     "/students/hu-zhiying/forced-causation/",
     "从混沌经验里自生因果框架，不只需要一段不被答案填满的时间；当连「等待」的资格都被剥夺、退路救援延期全断，认知会硬逼出一种此前并不存在的因果直觉。"),
    ("道德哲学 · 高鹏",
     "善的慢发生与它的结构性驱逐",
     "/students/gao-peng/slow-genesis-of-good/",
     "善不是靠被制造出来的；它的长成依赖三样天生抵触效率的东西——无用的好奇养出的认知根系、容得下道德挣扎的滞留空间、谴责错误却仍容留犯错者的关系；效率逻辑会把这三样慢慢驱逐。"),
]

SIBLING = ("本栏有两篇与本篇同在时间这条线上，但切法不同。"
           "《改一样，另外两样多久跟上》问的是几样东西在一个系统里互相追赶要多久（单位是系统与时差）；"
           "本篇问的是一样东西长成、要怎么付时间这笔账（单位是个体与付法）。"
           "《有些本事，是准备不出来的》说有些东西没法靠提前准备得到；"
           "本篇顺这条线再走一步——那些没法提前准备的东西，若硬要提前到手，无非预支或受迫两条路，而两条都要还账。")

CARDS_AFTER = 0
BANNED = ("发生学", "发现学", "发生论", "本体论", "存在论", "显露", "纠缠", "裂缝",
          "金点子", "回写", "差异序列", "SDE")


def strongify(s):
    s = html.escape(s, quote=False)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)


def load_md():
    """把 一、xxx 形式的源稿转成 markdown 结构。"""
    lines = [x.rstrip() for x in SRC.read_text(encoding="utf-8").splitlines()]
    # 源稿前两行是题与副题，已由 TITLE/SUB 承担，不进正文
    while lines and not re.match(r"^[一二三四五六七八九十]+、", lines[0].strip()):
        lines.pop(0)
    out = []
    for x in lines:
        s = x.strip()
        if not s:
            out.append("")
            continue
        if s.startswith("摘要：") or s.startswith("关键词："):
            continue          # 本栏惯例：正文不放摘要与关键词，导语（deck）承担这个功能
        if re.match(r"^[一二三四五六七八九十]+、", s) and len(s) < 60:
            out.append("## " + s.split("、", 1)[1])
            continue
        out.append(s)
    return "\n".join(out)


def md_to_html(md):
    out, para, toc, n = [], [], [], 0

    def flush():
        if para:
            out.append("<p>" + strongify(" ".join(para)) + "</p>")
            para.clear()

    for raw in md.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush(); continue
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
        para.append(line.strip())
    flush()
    return "".join(out), toc


def build_page(body, toc, pages, wan):
    t = TPL.read_text(encoding="utf-8")
    t = re.sub(r"<title>.*?</title>",
               f"<title>{TITLE}——{SUB} · 每日必读 | SDE Universes</title>", t, flags=re.S)
    t = re.sub(r'(<meta name="description" content=")[^"]*(")',
               lambda m: m.group(1) + html.escape(DECK[:190], quote=True) + m.group(2), t)
    t = re.sub(r'<h1 class="art-title">.*?</h1>', f'<h1 class="art-title">{TITLE}</h1>', t, flags=re.S)
    # 模板里 art-sub 是 <div> 不是 <p>——两种都认，否则会留着模板自带的副标题
    t = re.sub(r'<(p|div) class="art-sub">.*?</\1>', f'<div class="art-sub">{SUB}</div>', t, flags=re.S)
    t = re.sub(r'<div class="art-meta">.*?</div>',
               f'<div class="art-meta">王德生 ＋ Claude · 约 {wan} 万字 · {pages} 页 · '
               f'三种阅读方式 · 发表于{PUBDATE}</div>', t, flags=re.S)
    t = re.sub(r'<div class="art-series">.*?</div>',
               f'<div class="art-series">每 日 必 读 · 典 范 文 · {NO_CN}</div>', t, flags=re.S)
    t = re.sub(r'<div class="deck">.*?</div>', f'<div class="deck">{strongify(DECK)}</div>', t, flags=re.S)

    links = "".join(f'<a href="#{i}">{html.escape(x)}</a>' for i, x in toc)
    t = re.sub(r'<div class="toc">.*?</div>\s*(?=<h2|<p|<hr)',
               f'<div class="toc"><div class="tl">目 录</div>{links}</div>\n', t, flags=re.S)

    i = t.index("</div>", t.index(links)) + 6
    j = t.index('<div class="src">')
    t = (t[:i] + "\n" + body
         + f'\n<hr>\n<h2 id="sib">附：与本栏另外几篇的关系</h2><p>{strongify(SIBLING)}</p>\n'
         + t[j:])

    ones = "".join(
        f'<a class="one" href="{u}"><div class="k">{html.escape(k)}</div>'
        f'<div class="t">{html.escape(ti)}</div><div class="g">{html.escape(g)}</div></a>'
        for k, ti, u, g in SOURCES)
    t = re.sub(r'<div class="src">.*?</div>\s*(?=<div class="endbox">)',
               f'<div class="src"><div class="sl">这一篇由哪三篇撞成</div>'
               f'<p class="sd">{strongify(COLLIDE)}</p>{ones}</div>\n', t, flags=re.S)

    assert t.count("<html") == 1 and t.count("</html>") == 1
    # 行话零容忍只查本篇内容（站名 SDE Universes 在模板 chrome 里，扫全页会误报）
    mine = body + DECK + COLLIDE + SIBLING + TITLE + SUB + "".join(
        k + ti + g for k, ti, _u, g in SOURCES)
    hit = [w for w in BANNED if w in body]   # 只查正文；来源盒里是三篇原标题，属引用
    assert not hit, f"本篇正文残留行话：{hit}"
    return t


def build_print(body):
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><title>{TITLE}</title>
<style>@page{{size:A4;margin:20mm 18mm}}
body{{font-family:"Noto Serif CJK SC","Source Han Serif SC",serif;font-size:11.5pt;line-height:1.85;color:#1a1a1a}}
h1{{font-size:21pt;margin:0 0 6pt;text-align:center}}
.sub{{text-align:center;font-size:12pt;color:#555;margin:0 0 4pt}}
.by{{text-align:center;font-size:10.5pt;color:#666;margin:0 0 18pt}}
h2{{font-size:14pt;margin:20pt 0 8pt;border-bottom:1px solid #ccc;padding-bottom:4pt}}
h3{{font-size:12.5pt;margin:14pt 0 6pt}}
p{{margin:0 0 9pt;text-align:justify}} hr{{border:0;border-top:1px solid #ddd;margin:14pt 0}}
.src{{border:1px solid #bbb;padding:10pt 12pt;margin:0 0 16pt;font-size:10.5pt;background:#fafafa}}
.src ol{{margin:6pt 0;padding-left:16pt}}</style></head><body>
<h1>{TITLE}</h1><div class="sub">{SUB}</div>
<div class="by">王德生 ＋ Claude　·　{PUBDATE}　·　SDE Universes 每日必读 · 典范文 · {NO_CN}</div>
<div class="src"><b>本篇由这三篇撞成</b><ol>{''.join(
    f'<li>《{ti}》—— {k}：{g}</li>' for k, ti, u, g in SOURCES)}</ol>{strongify(COLLIDE)}</div>
{body}
<hr><h2>附：与本栏另外几篇的关系</h2><p>{strongify(SIBLING)}</p>
</body></html>"""


def add_card(pages, wan):
    f = PZ / "index.html"
    t = f.read_text(encoding="utf-8")
    before_cards = t.count('class="item"')
    assert SLUG not in t, "卡片已存在"
    trio = "".join(f'<div><b>{html.escape(k)}</b><a href="{u}">{html.escape(ti)}</a></div>'
                   for k, ti, u, _g in SOURCES)
    who = ("三篇来源分属"
           + "、".join(f'<a href="/students/{u.split("/")[2]}/" style="color:var(--clay)">{n}</a>'
                      for n, u in [("刘言言", SOURCES[0][2]), ("胡志英", SOURCES[1][2]), ("高鹏", SOURCES[2][2])])
           + "三位学员")
    card = (f'<div class="item"><div class="n">{NO_CARD} · 三学科交叉：{FIELDS}</div>'
            f'<h2><a href="/paradigm/{SLUG}/">{html.escape(TITLE)}</a></h2>'
            f'<p class="sub">{html.escape(SUB)}</p>'
            f'<p class="hk">{html.escape(DECK)}</p>'
            f'<div class="trio">{trio}</div>'
            f'<a class="rdmore" href="/paradigm/{SLUG}/">读全文 →</a>'
            f'<div class="meta">约 {wan} 万字 · {pages} 页 · 三种读法 · 作者 王德生 ＋ Claude · '
            f'发表于{PUBDATE} · {who}</div></div>\n')
    a = "</main>"
    assert t.count(a) == 1
    t = t.replace(a, card + a, 1)
    assert t.count('class="item"') == before_cards + 1, f'插入后卡片数 {t.count(chr(39)+chr(99)+chr(108)+chr(97)+chr(115)+chr(115)+chr(61)+chr(34)+chr(105)+chr(116)+chr(101)+chr(109)+chr(34)+chr(39))}，应为 {before_cards + 1}'
    f.write_text(t, encoding="utf-8")
    print(f"  栏目页：追加一张卡，现共 {t.count('class=\"item\"')} 篇")


def main():
    md = load_md()
    body, toc = md_to_html(md)
    n = len(re.sub(r"<[^>]+>", "", body))
    wan = round(n / 10000, 1)
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
    probe = subprocess.run(["pdftotext", "-f", "1", "-l", "1", str(pdf), "-"],
                           capture_output=True, text=True).stdout
    assert re.search(r"[\u4e00-\u9fff]", probe), "PDF 首页抽不出中文"

    (d / "index.html").write_text(build_page(body, toc, pages, wan), encoding="utf-8")

    rd = (PZ / "taken-out" / "read.html").read_text(encoding="utf-8")
    rd = rd.replace("taken-out", SLUG).replace("一拿出来，就不是它了", TITLE)
    (d / "read.html").write_text(rd, encoding="utf-8")

    add_card(pages, wan)
    print(f"  {SLUG}: {n} 字 · {pages} 页 · 目录 {len(toc)} 节")


if __name__ == "__main__":
    main()
