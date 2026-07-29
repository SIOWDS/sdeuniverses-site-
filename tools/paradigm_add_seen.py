# -*- coding: utf-8 -*-
"""把《被看见，对有的东西是成全，对有的东西是拆台》并入「每日必读」，作发布号之三十三（显示号由 renumber 刷成之一）。"""
import html
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PZ = ROOT / "public" / "paradigm"
TPL = PZ / "taken-out" / "index.html"
SRC = Path("/home/claude/pz/P33.txt")
SLUG = "seen-makes-or-breaks"
PUBDATE = "2026年7月29日"
NO_CN = "之 三 十 三"
NO_CARD = "之三十三"
FIELDS = "法哲学 × 冲突政治 × 仪式社会学（本篇是群内碰撞：三位不同学员）"

TITLE = "被看见，对有的东西是成全，对有的东西是拆台"
SUB = ("把一样东西摆上台面、让人看见、要它证明自己——这同一个动作，对不同的东西起相反的作用："
       "有的东西非被接住不能成形，有的东西一被要求当众显得确定就被表演顶替，有的东西全靠没露面的支撑运作、一被点破就塌。"
       "所以「该不该被看见」问错了；真问题是：这道光照过去，是确认它、逼它表演、还是拆掉它的支架。")
DECK = ("有三样东西都被人「看见」了，下场却完全不同：一样本来还是团模糊的东西，被人接了一下，立住了、成了形；"
        "一样本来带着犹豫和松动的东西，被架上台面要它当众显得斩钉截铁，就被一个硬邦邦的替身顶替了；"
        "一样本来靠底下一整套没露面的支撑好好运转的东西，被人点破、翻上台面，当场就散了。"
        "本文认为这不是巧合——**「被看见」其实一次做了三件被混起来的事：确认、逼表演、拆架**；"
        "同一道光泼向不同的东西，得到**成全、伪造、溶解**三种相反的结果。"
        "所以「该不该被看见」问错了，真问题是先认清：这道光照过去，对手里这样东西，起的是哪一件。")

COLLIDE = ("三篇给出关于「被看见」互不相容的答案：一篇说一个刚冒头的意愿必须被人「接住」（一种被看见）才成形、没被接住就消散；"
           "一篇说被持续观看反而把真实（含不确定与裂口）的立场逼成「确定性的表演」；"
           "一篇说仪式体验靠「看不见的维持」运作、一被点破就散。三头对齐，逼出本文判断——"
           "「被看见」一次做了确认、逼表演、拆架三件被混起来的事，同一道光泼向不同的东西得到成全/伪造/溶解三种相反结果。"
           "**正文即从这条判断另起、用自备例子展开，不复述三篇原文**；三篇的功劳记在这里。")

SOURCES = [
    ("法哲学 · 高鹏",
     "意愿的二次发生：权利如何在被看见中成形，在无回应中消散",
     "/students/gao-peng/second-genesis-of-will/",
     "一团模糊的冲动必须在与他人的互动中被「接住」才能成形为足以驱动行动的意愿；接住不是赞同鼓励，只需那个听的人在那一秒没有转开头；而权力最省力的打击，正是绕过禁令、直接让意愿在成形端持续落空。"),
    ("冲突政治 · 阳涌",
     "确定性的表演：冲突叙事的再生产与松动如何可能",
     "/students/yang-yong/paper-p34-d01-a03/",
     "冲突里叙事的确定性不是被「相信」出来的，是被「表演」出来的——行动者越是在被己方阵营持续观看下公开确认叙事，就越不可能在不丢失政治生命的前提下当众露出一丝确定性的降低；真实的不确定与裂口被挤到了台底下。"),
    ("仪式社会学 · 胡志英",
     "看不见的维持：论仪式体验的隐性基础设施",
     "/students/hu-zhiying/invisible-upkeep/",
     "一场仪式体验靠一整套「看不见的维持」在底下撑着；这种看不见不是运转良好的副产品，而是它生效的必要条件——一旦被点破、被搬上台面，那套隐性支撑就失效、体验随之散掉（与「基础设施用时隐、坏时显」的看法正面分歧）。"),
]

SIBLING = ("本栏有两篇与本篇相邻。《门关着，后果照样溜得出去》也是把一个笼统的动作拆开看——"
           "那篇拆的是「过一道界」其实是决定权与责任两样东西一起过还是分开过；"
           "本篇拆的是「被看见」其实是确认、逼表演、拆架三件被混起来的事。"
           "《非你不可，说的是世界，不是你》讲一样刚冒头、非得世界配合才立得住的东西；"
           "本篇第一类（意愿要被接住才成形）与它同气——都在说，有些东西的成立一半不在它自己手里，而在有没有人在那一秒不转开头。")

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
                      for n, u in [("高鹏", SOURCES[0][2]), ("阳涌", SOURCES[1][2]), ("胡志英", SOURCES[2][2])])
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
