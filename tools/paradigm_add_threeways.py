# -*- coding: utf-8 -*-
"""把《能改的看不见，看得见的改不了》并入「每日必读」栏目，作「之二十」。

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
SRC = Path("/home/claude/paradigm3/P18.txt")
SLUG = "three-ways-to-die"
PUBDATE = "2026年7月28日"
NO_CN = "之 二 十"
NO_CARD = "之二十"
FIELDS = "行动系统与临床心理 × 文化心理与教育 × 审美与感知"

TITLE = "能改的看不见，看得见的改不了"
SUB = "一样东西没能长出来，有三种死法，而我们只认得最后一种"
DECK = ("一个人培训后真心认同、半年后在深夜里做出三年前的反应；一个人说不清自己想要什么，"
        "不是不敢说、是确实没有内容；一个人正看着什么、旁边一句「你觉得这个好在哪里」，"
        "正在发生的那个东西就没了。三个人在任何评估表上都是同一句「没有这个能力」。"
        "本文认为这是三种性质相反的死法——没成形、没位置、没掌权——而它们的可见性从后往前急剧递减、"
        "可改性从后往前递增：**唯一看得见的那一关，恰好是唯一改不动的；两关能改的，恰好都看不见。**"
        "更麻烦的是，用来补救第三关的每一样工具，恰好都是前两关的致病因子。")

COLLIDE = ("三篇对同一个问题给出了互相排斥的答案：一样东西「不见了」，它现在在哪儿？"
           "第一篇说它还在——旧的行动配置被完整保留、删不掉，压力下会整包上线夺回控制权；"
           "第二篇说它从没长出来——不是被压抑，是该长的那几年那块地被更好的替代品先占了；"
           "第三篇说它连成形都没来得及——而且你想守护的那个「完整版本」，恰恰是靠你所批评的命名与评价才得以存在的。"
           "三个答案分别把损失定位在保存端、生长端与发生端，且每一个都取消了另外两个的前提。")

SOURCES = [
    ("行动系统 · 临床心理", "并存韧度：论行动系统中旧路径为何无法被消除",
     "/students/huang-qianying/coexistence-resilience/",
     "旧配置不被删除、完整保留，可在极短时间内重新获得执行权；删除本身是成本极高、风险极大的工程。"),
    ("文化心理 · 教育", "从压抑到占位：儒家文化、竞争教育与关系能力损伤的机制重判",
     "/students/hu-min/developmental-preoccupation/",
     "损伤不是源于被压抑（心里有未表达的欲望），而是生长通道在该破土的那几年被替代品提前进驻。"),
    ("审美 · 感知", "序前中断：审美感知为何在成形之前就已停止发生",
     "/students/liu-yanyan/pre-arrest-of-perception/",
     "被牺牲的不是「完整感知的失落」，而是那些从未有机会凝结为可被认领形态的片段。"),
]

SIBLING = ("本栏已有几篇都在讲「有东西悄悄没了」，容易被读成同一件事，所以把分工说清。"
           "之十一《没人吭声，其实有三种》问**读数为零的多义性**；"
           "之十二《交出去的不止那件事》问**委托的连带损失**；"
           "之十三《扶一把，和替他站着》问**支持有没有留出力位**；"
           "之十四《先坏的不是指标》问**那台负责感到不对的仪器还在不在**。"
           "本篇问的是另一件事：**一样东西没能长出来，它是在哪一关死的**——"
           "死在成形之前、占地之前，还是掌权那一刻。前几篇的主角是读数、账本、支持、感知，"
           "本篇的主角是**从发生到能用的那条链条本身**，以及一个残酷的事实："
           "越靠前的断点越不可见，而我们所有的力气都用在最靠后、也最结实的那一段上。")

BANNED = ("发生学", "发现学", "发生论", "本体论", "存在论", "显露", "纠缠", "裂缝",
          "金点子", "回写", "差异序列", "并存韧度", "发育占位", "占位", "序前中断", "抢先覆盖", "SDE")


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
    assert SLUG not in t, "卡片已存在"
    trio = "".join(f'<div><b>{html.escape(k)}</b><a href="{u}">{html.escape(ti)}</a></div>'
                   for k, ti, u, _g in SOURCES)
    who = ("三篇来源分属"
           + "、".join(f'<a href="/students/{u.split("/")[2]}/" style="color:var(--clay)">{n}</a>'
                      for n, u in [("黄倩盈", SOURCES[0][2]), ("胡敏", SOURCES[1][2]), ("刘言言", SOURCES[2][2])])
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
    assert t.count('class="item"') == 21, '插入后卡片数不对——推之前重数一遍远端再定序号'
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
