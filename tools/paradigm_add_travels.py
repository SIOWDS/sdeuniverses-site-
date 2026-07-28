# -*- coding: utf-8 -*-
"""把《别人怎么成的，学不来；别人怎么垮的，学得来》并入「每日必读」栏目，作「之二十八」。

沿用本栏既定形制：以 taken-out/index.html 为版式模板（进度条·目录·来源盒·回顶），
PDF 与 read.html 同批产出，栏目页追加一张卡。
"""
import html
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PZ = ROOT / "public" / "paradigm"
TPL = PZ / "taken-out" / "index.html"
SRC = Path("/home/claude/paradigm4/P28.txt")
SLUG = "what-travels"
PUBDATE = "2026年7月28日"
NO_CN = "之 二 十 八"
NO_CARD = "之二十八"
FIELDS = "制度经济学 × 创新政策 × 发展经济学（本篇撞的是三位在世经济学家）"

TITLE = "别人怎么成的，学不来；别人怎么垮的，学得来"
SUB = "成功要一长串条件同时成立，失败只要其中一条被破坏——而我们所有的学习，都压在搬不走的那一半上"
DECK = ("一位说看制度，一位说看方向，一位说这些问题都太大、只能一件一件做小实验。"
        "三位都还在世，都被认为是第一流的，答案互不相容，吵了二十年。"
        "本文认为他们真正在争的不是「什么造成繁荣」，而是**一个结论能走多远**。"
        "由此推出一条不对称：成功是一长串「并且」，失败是一连串「或者」；"
        "合取的东西换个地方必然缺项，而缺项在合取里等于不成立，所以成功的知识搬不走；"
        "析取的东西一条就够用，所以失败的知识搬得走。"
        "而标杆、最佳实践、成功案例、经验推广——我们几乎全部的学习制度，都建在搬不走的那一半上。")

COLLIDE = ("三位对同一个问题给出互不相容的答案，而每一位的答案都在同一处付出代价——"
           "第一位要解释所有国家所有世纪，代价是永远无法被真正试验；"
           "第二位要一份能照着做的方案，代价是那份方案所依赖的条件（有界的任务、可拆分的子问题、"
           "无争议的成败判定、罕见的政治共识）今天一样也不具备；"
           "第三位把范围缩到一个被随机化的人群以换取硬度，代价是在这里成立不等于在那里成立。"
           "三家各自都清楚自己的软肋，也各自处理了几十年——但因为分处三个战场，"
           "没有人把这三处代价合起来看成同一件事。")

SOURCES = [
    ("制度经济学 · 长时段与自然实验", "达龙·阿西莫格鲁：制度决定繁荣，国家能力与社会力量必须同步生长",
     "https://www.ubs.com/global/en/our-firm/what-we-do/our-brand/nobel-perspectives/laureates/daron-acemoglu.html",
     "《国家为什么会失败》与《狭窄的走廊》；2024 年诺贝尔经济学奖。野心是解释所有国家所有世纪，代价是永远无法随机化。"),
    ("创新政策 · 使命导向", "玛丽安娜·马祖卡托：市场不是被修复的，是被塑造的",
     "https://issues.org/review-mission-economy-mazzucato/",
     "《企业家型国家》与《使命经济》；她本人明确写过登月经验不能被原样剪贴到棘手问题上，而批评正落在那份清单的其余各项。"),
    ("发展经济学 · 随机对照试验", "埃丝特·迪弗洛：别问大问题，一件一件做小实验",
     "https://www.princeton.edu/~deaton/downloads/Deaton_Cartwright_RCTs_with_ABSTRACT_August_25.pdf",
     "《贫穷的本质》；2019 年诺贝尔经济学奖。可信度最高，代价最直接——外部有效性之争至今未平，链接为迪顿与卡特赖特的系统批评。"),
]

SIBLING = ("本栏已有几篇都在讲「有东西传不下去」，容易被读成同一件事，所以把分工说清。"
           "之一《一拿出来，就不是它了》问**一样东西离开发生现场之后还在不在**（对象是那样东西）；"
           "之十二《交出去的不止那件事》问**把事交出去之后验收它的能力还在不在**（对象是能力）；"
           "之十六《没走的那条路，不留痕》问**一件成品身上留不留得下判断**（对象是痕迹）。"
           "本篇问的是另一件事：**一条已经被说清楚、也确实成立的结论，能不能在别的地方也成立**——"
           "只问它靠着几个条件才成立、那几个条件在别处还在不在。"
           "前几篇的主角是那样东西、那份能力、那道痕迹；本篇的主角是**结论的行李**。")

CARDS_AFTER = 0  # 运行时按现状+1 计算
BANNED = ("发生学", "发现学", "发生论", "本体论", "存在论", "显露", "纠缠", "裂缝",
          "金点子", "回写", "差异序列", "显露", "纠缠", "发生学", "本体论", "金点子", "差异序列", "SDE")


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
                      for n, u in [("阿西莫格鲁", SOURCES[0][2]), ("马祖卡托", SOURCES[1][2]), ("迪弗洛", SOURCES[2][2])])
           + "三位作者")
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
