# -*- coding: utf-8 -*-
"""学科通融专栏 /confluence/ · 建文章页 + PDF + 三种读法 + 专栏索引。

与「每日必读」的分工是硬的：
  · 每日必读 撞的是站内学员论文
  · 学科通融 撞的是站外不同学科的理论体系（须联网检索、须给出真实出处）
两栏共用同一套规矩：三家必须分属不同学科、必须正面打架、
撞出来的判断必须任一家单独看不到、全文零术语、文末交出处与作废数。
版式沿用每日必读，保持全站一致。
"""
import html
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CF = ROOT / "public" / "confluence"
TPL = ROOT / "public" / "paradigm" / "taken-out" / "index.html"
PUBDATE = "2026年8月3日"

PAPERS = [{
    "slug": "one-edge-short",
    "src": Path("/home/claude/conf65.md"),
    "title": "差一条边",
    "sub": "论课堂的接手关系构成一张图，学习能否自持取决于这张图是否闭合，及为什么修好任意一条边可能毫无效果而补上某一条会突然全通",
    "cross": "教育学 × 化学反应网络 × 管理学",
    "no": "之六十五",
    "deck": ("课堂上真正的学习为什么很少发生，三家给出三条不能同时为真的答案："
             "教育学答承接者没有接，故要提高教师的注意与回应；管理学答每个局部都合法地关掉了自己的账，故要重配责任；"
             "化学答中间态没有被后续接住，故要保住那条通路。三条处方彼此正是对方诊断出的病因。"
             "而三家共有一个没说出口的前提——**每一条断掉的边都有一个可指认的理由，修好它就少一处损失**。"
             "推翻它的材料来自化学自己，且不是速率那一支，是网络那一支：**集体自催化集**。"
             "它的定义只有一句——集合内每一个反应都被集合内某成员所催化——而后果是刚性的："
             "**自持是集合的性质，不是任何单个反应的性质**；而集合能否自持是**阈值现象**："
             "催化密度低于临界值，无论修好多少条单边都不形成自持集；高于临界值，自持集突然出现。"
             "据此本文把课堂写成一张**接手图**，命名它的**闭合**，给出三个可从既有录像与教案算出的读数——"
             "催化覆盖率、闭合度、催化源分散度，并推出五条结论，其中三条方向违反通行判断："
             "**局部改善在阈值以下无效**；**星形闭合最脆，而「教师注意并跟随每一个学生」恰恰把图推向星形**；"
             "**任务越容易，无主的那一次越不可观察**。"
             "文中另论证回应式教学与教师注意研究同持两条在闭合条件下不能同真的处方，"
             "并从化学借来一条少见的正面判据——**加边实验**：两个平行班、一节课、一条额外规则即可跑。"
             "文末走查一节真实结构的数学课：覆盖率 0.56、分散度 1.0，而**闭合度为零**；"
             "补上一条回边，闭合度从 0 跳到 5/9。"),
    "clash": ("第一家主张差异之所以没有延续是因为承接者没有接，"
              "故应提高教师注意学生想法实质并据此调整的质量；"
              "第二家主张是因为每个局部环节都合法地关掉了自己的账、整体目标无人持有，"
              "故应重新配置责任与指标，别让局部闭账；"
              "第三家主张是因为不稳定的中间态在被后续利用之前已经消失，故应保住那条通路。"
              "三条不能同时为真，且各自的日课正是另一家诊断出的病："
              "第一家要教师更密地注意与回应，而第二家指出这恰把承接责任压在一个可被考核的可见动作上，"
              "一旦被记录就会被做成表演；第二家要重配责任让信号上行，"
              "而第一家指出责任配置改不了教师听不听得懂学生；"
              "第三家要保住中间态，而前两家都追问「由谁来保」——"
              "而第三家的回答是：不由任何人保，由网络的结构保。"),
    "sources": [
        ("化学 · 集体自催化集与自持性的网络条件",
         "Kauffman, Autocatalytic Sets of Proteins (<i>J. Theor. Biol.</i> 119:1, 1986)；"
         "形式化与多项式时间判定算法见 Hordijk &amp; Steel, Detecting Autocatalytic, Self-Sustaining Sets "
         "in Chemical Reaction Systems (<i>J. Theor. Biol.</i> 227:4, 2004)",
         "https://doi.org/10.1016/j.jtbi.2003.11.020",
         "定义只有一句：集合内每一个反应都被集合内某成员所催化。而它所定义的自持性不属于任何单个反应——"
         "把每一个反应单独拿出来检查都正常，集合仍可能不自持。这是本文推翻共有前提所用的全部材料。"),
        ("化学 · 自持集涌现所需的催化水平（阈值）",
         "Hordijk, Kauffman &amp; Steel, Required Levels of Catalysis for Emergence of Autocatalytic Sets "
         "in Models of Chemical Reaction Systems (<i>Int. J. Mol. Sci.</i> 12:5, 2011)；"
         "另见 Mossel &amp; Steel, Random Biochemical Networks (<i>J. Theor. Biol.</i> 233:3, 2005)",
         "https://doi.org/10.3390/ijms12053085",
         "自持集的出现随催化密度变化不是平缓上升，而是在临界值附近突然发生，与随机图中巨连通分支的涌现同类。"
         "本文的核心推论——局部改善在阈值以下无效——直接来自这一条。"),
        ("教育学 · 形成性评价、主动学习与教师注意",
         "Black &amp; Wiliam, Developing the Theory of Formative Assessment "
         "(<i>Educ. Assess. Eval. Account.</i> 21:1, 2009)；另见 Freeman 等, Active Learning Increases "
         "Student Performance in STEM (<i>PNAS</i> 111:23, 2014)；Chi &amp; Wylie, The ICAP Framework "
         "(<i>Educational Psychologist</i> 49:4, 2014)",
         "https://doi.org/10.1007/s11092-008-9068-5",
         "把「证据被用于决定后续步骤」写进形成性的构成条件，并要求教师注意学生想法的实质。"
         "本文第十一节所打的强制不一致正在这一支：它同时要求教师成为承接者、又以学生在教师不在场时的后续表现为证据。"),
        ("管理学 · 正式结构与实际工作过程的脱耦",
         "Meyer &amp; Rowan, Institutionalized Organizations: Formal Structure as Myth and Ceremony "
         "(<i>American Journal of Sociology</i> 83:2, 1977)；另见 Edmondson, Psychological Safety and "
         "Learning Behavior in Work Teams (<i>ASQ</i> 44:2, 1999)",
         "https://doi.org/10.1086/226550",
         "正式结构可作为合法性仪式与实际工作脱耦，而心理安全让差异能够出现却不保证它进入下一轮。"
         "这一支反过来限制本文：无指标的课堂同样可能接不上，故压力不是原因、安全不是充分条件。"),
        ("化学 · 过渡态位置（本文推论四所据）",
         "Hammond, A Correlation of Reaction Rates (<i>J. Am. Chem. Soc.</i> 77:2, 1955)",
         "https://doi.org/10.1021/ja01607a027",
         "放能反应的过渡态在结构上更接近反应物。课堂版本：任务越容易，那个不稳定的中间态越像旧规则本身，"
         "因而越不可能被观察者辨认为一次差异——简单任务上的无主轮次被系统性低估。"),
    ],
}]


def strongify(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"<i>\1</i>", s)   # 期刊名用斜体
    return s


def _table(rows):
    head, body = rows[0], rows[2:]
    th = "".join(f"<th>{strongify(c)}</th>" for c in head)
    tb = "".join("<tr>" + "".join(f"<td>{strongify(c)}</td>" for c in r) + "</tr>" for r in body)
    return f'<table class="tbl"><thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table>'


def md_to_html(md):
    out, para, li, toc, n = [], [], [], [], 0
    tbl = []

    def flush():
        if para:
            out.append("<p>" + strongify(" ".join(para)) + "</p>")
            para.clear()

    def flush_li():
        if li:
            out.append("<ul>" + "".join(f"<li>{strongify(x)}</li>" for x in li) + "</ul>")
            li.clear()

    def flush_tbl():
        if tbl:
            out.append(_table(tbl)); tbl.clear()

    for raw in md.splitlines():
        line = raw.rstrip()
        if line.strip().startswith("|") and line.strip().endswith("|"):
            flush(); flush_li()
            tbl.append([c.strip() for c in line.strip().strip("|").split("|")])
            continue
        flush_tbl()
        if not line.strip():
            flush(); flush_li(); continue
        if line.strip() == "---":
            flush(); flush_li(); out.append("<hr>"); continue
        if line.startswith("- "):
            flush(); li.append(line[2:].strip()); continue
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            flush(); flush_li()
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
    flush(); flush_li(); flush_tbl()
    return "".join(out), toc


def build_page(p, body, toc, pages):
    zh = len(re.findall(r'[\u4e00-\u9fff]', re.sub(r'<[^>]+>', '', body)))
    t = TPL.read_text(encoding="utf-8")
    css = (ROOT / "tools" / "confluence-article.css").read_text(encoding="utf-8")
    t = re.sub(r"<style>.*?</style>", "<style>" + css + "</style>", t, count=1, flags=re.S)
    t = re.sub(r"<title>.*?</title>",
               f'<title>{p["title"]}——{p["sub"]} · 学科通融 | SDE Universes</title>', t, flags=re.S)
    t = re.sub(r'(<meta name="description" content=")[^"]*(")',
               lambda m: m.group(1) + html.escape(p["deck"].replace("**","")[:190], quote=True) + m.group(2), t)
    t = re.sub(r'<div class="art-series">.*?</div>',
               f'<div class="art-series">学 科 通 融 · {p["no"]} · {html.escape(p["cross"])}</div>', t, flags=re.S)
    t = re.sub(r'<h1 class="art-title">.*?</h1>', f'<h1 class="art-title">{p["title"]}</h1>', t, flags=re.S)
    t, _n = re.subn(r'<(p|div) class="art-sub">.*?</\1>',
                    lambda m: f'<{m.group(1)} class="art-sub">{p["sub"]}</{m.group(1)}>', t, flags=re.S)
    assert _n == 1, f'art-sub 替换命中 {_n} 次'
    assert p['sub'][:12] in t, 'art-sub 未写进页面'
    t = re.sub(r'<div class="art-meta">.*?</div>',
               f'<div class="art-meta">王德生 ＋ Claude · 约 {zh/10000:.1f} 万字 · {pages} 页 · '
               f'三种阅读方式 · 发表于{PUBDATE}</div>', t, flags=re.S)
    t = re.sub(r'<div class="deck">.*?</div>', f'<div class="deck">{strongify(p["deck"])}</div>', t, flags=re.S)
    links = "".join(f'<a href="#{i}">{html.escape(x)}</a>' for i, x in toc)
    t = re.sub(r'<div class="toc">.*?</div>\s*(?=<h2|<p|<hr)',
               f'<div class="toc"><div class="tl">目 录</div>{links}</div>\n', t, flags=re.S)
    i = t.index("</div>", t.index(links)) + 6
    j = t.index('<div class="src">')
    t = t[:i] + "\n" + body + "\n" + t[j:]
    ones = "".join(
        f'<a class="one" href="{u}"><div class="k">{html.escape(k)}</div>'
        f'<div class="t">{html.escape(ti)}</div><div class="g">{html.escape(g)}</div></a>'
        for k, ti, u, g in p["sources"])
    t = re.sub(r'<div class="src">.*?</div>\s*(?=<div class="endbox">)',
               f'<div class="src"><div class="sl">这一篇由哪三个学科的理论体系撞成</div>'
               f'<p class="sd">{strongify(p["clash"])}　'
               f'三家均为站外的公开文献，链接直达原始出处，可自行核对。</p>{ones}</div>\n', t, flags=re.S)
    # 下载按钮的 PDF 名沿用自模板，必须换成本篇 slug，否则 404（2026-08-03 全栏 27 页踩过）
    t = t.replace('href="taken-out.pdf"', f'href="{p["slug"]}.pdf"')
    assert "taken-out.pdf" not in t, "下载链接串了：仍指向模板的 PDF"
    t = t.replace("‹ 典范文专栏", "‹ 学科通融").replace("返回典范文专栏 →", "返回学科通融 →")
    t = t.replace("典范文专栏 · 作者 Claude ·", "学科通融 · 作者 阳涌 ＋ Claude ·")
    assert t.count("<html") == 1 and t.count("</html>") == 1
    # 本栏是学术论文体，标准学科词汇（本体论/存在论等）是正常表述，不在禁用之列；
    # 禁的只是学派专有词——它们会让论文读起来像内部文件。
    for w in ("发生学", "显露", "纠缠", "差异序列", "金点子", "裂缝", "回写",
              "生成机制", "改姓", "本体论级", "三界", "中心位", "母题"):
        assert w not in t, f"学派术语残留 {w}"
    return t


def build_print(p, body):
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><title>{p["title"]}</title>
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
<h1>{p["title"]}</h1><div class="sub">{p["sub"]}</div>
<div class="by">王德生 ＋ Claude　·　{PUBDATE}　·　SDE Universes 学科通融 · {p["no"]}</div>
<div class="src"><b>本篇由三个学科的理论体系撞成</b>（{p["cross"]}）<ol>{''.join(
    f'<li>{k}：{ti}　—— {g}</li>' for k, ti, u, g in p["sources"])}</ol>{strongify(p["clash"])}</div>
{body}</body></html>"""


def build_index(built):
    tpl = (ROOT / "public" / "paradigm" / "index.html").read_text(encoding="utf-8")
    head = tpl[:tpl.index("<body")]
    assert head.count("<html") == 1, "模板头已含 html 标签，不要再加前缀"
    head = re.sub(r"<title>.*?</title>", "<title>学科通融 · 跨学科理论体系碰撞 | SDE Universes</title>", head, flags=re.S)
    head = re.sub(r'(<meta name="description" content=")[^"]*(")',
                  lambda m: m.group(1) + "把三个分属不同学科、观点互相冲突的理论体系放在一起撞，"
                  "撞出来的那条判断单独成文。三家均为站外公开文献，链接直达原始出处。" + m.group(2), head)
    cards = ""
    for p, wan, pages in built:
        ones = "".join(f'<div><b>{html.escape(k)}</b><a href="{u}">{html.escape(ti)}</a></div>'
                       for k, ti, u, g in p["sources"])
        cards += (f'<div class="item"><div class="n">之一 · 三学科交叉：{html.escape(p["cross"])}</div>'
                  f'<h2><a href="/confluence/{p["slug"]}/">{html.escape(p["title"])}</a></h2>'
                  f'<p class="sub">{html.escape(p["sub"])}</p>'
                  f'<p class="hk">{strongify(p["deck"])}</p>'
                  f'<div class="trio">{ones}</div>'
                  f'<a class="rdmore" href="/confluence/{p["slug"]}/">读全文 →</a>'
                  f'<div class="meta">约 {wan} 万字 · {pages} 页 · 三种读法 · '
                  f'作者 王德生 ＋ Claude · 发表于{PUBDATE} · 三家来源均为站外公开文献</div></div>\n')
    return f"""{head}
<body>
<nav><div class="navin"><a href="/">SDE Universes</a><a href="/paradigm/">每日必读 →</a></div></nav>
<header class="hero"><div class="heroin">
<div class="eyebrow">CONFLUENCE · CROSS-DISCIPLINE</div>
<h1>学科通融</h1>
<p>每一篇，都是三个分属不同学科、且互相冲突的理论体系撞在一起之后剩下的东西。</p>
<div class="how"><span>三家来自不同学科</span><span>三家必须互相打架</span><span>来源全在站外，链接可核对</span></div>
</div></header>
<main class="wrap">
<p class="lead">这个专栏与「每日必读」是一对：那一栏撞的是站内学员的论文，这一栏撞的是站外不同学科的理论体系。
做法只有一件——先在公开文献里找到三个分属不同学科、而且在同一个问题上给出互相排斥答案的理论体系，
把它们各自最承重的判断拆出来两两去撞；只有当两个判断在同一个问题上互相顶住、
顶出一个任何一家单独都看不见的东西时，才算数。</p>
<p class="rule">这个专栏由王德生博士定题、判方向，Claude 执行检索、碰撞与成文，因此每篇署王德生 ＋ Claude。
与「每日必读」不同的是，这一栏的三个来源全部在站外，每一家都给出可以直接点开核对的原始出处——
因为撞的是别人的理论，把出处交清楚是最低限度的规矩。全文不使用任何学派术语，普通读者可一路读下来；
每篇都在文中交出可以让自己失败的判据，文末记着这一次作废了多少条。</p>
<hr class="sep">
{cards}
</main>
<footer>学科通融 · 作者 阳涌 ＋ Claude · © 德麦国际 Demai International</footer>
</body></html>"""


def main():
    CF.mkdir(exist_ok=True)
    built = []
    for p in PAPERS:
        body, toc = md_to_html(p["src"].read_text(encoding="utf-8"))
        d = CF / p["slug"]; d.mkdir(exist_ok=True)
        pf = d / "_p.html"; pf.write_text(build_print(p, body), encoding="utf-8")
        pdf = d / f'{p["slug"]}.pdf'
        subprocess.run(["wkhtmltopdf", "--enable-local-file-access", "--encoding", "utf-8",
                        "--footer-center", "[page]", "--footer-font-size", "9", str(pf), str(pdf)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pf.unlink()
        pages = int(subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True)
                    .stdout.split("Pages:")[1].split()[0])
        (d / "index.html").write_text(build_page(p, body, toc, pages), encoding="utf-8")
        rd = (ROOT / "public" / "paradigm" / "taken-out" / "read.html").read_text(encoding="utf-8")
        rd = rd.replace("/paradigm/taken-out", f'/confluence/{p["slug"]}') \
               .replace("taken-out", p["slug"]).replace("一拿出来，就不是它了", p["title"]) \
               .replace("典范文专栏", "学科通融")
        (d / "read.html").write_text(rd, encoding="utf-8")
        n = len(re.findall(r"[\u4e00-\u9fff]", re.sub(r"<[^>]+>", "", body)))
        built.append((p, round(n / 10000, 1), pages))
        print(f'  {p["slug"]}: {n} 字 · {pages} 页 · 目录 {len(toc)} 节 · 来源 {len(p["sources"])} 家')
    idx = CF / "index.html"
    if idx.exists() and "measurable-face" in idx.read_text(encoding="utf-8"):
        old = idx.read_text(encoding="utf-8")
        for p, wan, pages in built:
            if f'/confluence/{p["slug"]}/' in old:
                continue
            ones = "".join(f'<div><b>{html.escape(k)}</b><a href="{u}">{html.escape(ti)}</a></div>'
                           for k, ti, u, g in p["sources"])
            card = (f'<div class="item"><div class="n">{p["no"]} · 三学科交叉：{html.escape(p["cross"])}</div>'
                    f'<h2><a href="/confluence/{p["slug"]}/">{html.escape(p["title"])}</a></h2>'
                    f'<p class="sub">{html.escape(p["sub"])}</p>'
                    f'<p class="hk">{strongify(p["deck"])}</p>'
                    f'<div class="trio">{ones}</div>'
                    f'<a class="rdmore" href="/confluence/{p["slug"]}/">读全文 →</a>'
                    f'<div class="meta">约 {wan} 万字 · {pages} 页 · 三种读法 · '
                    f'作者 王德生 ＋ Claude · 发表于{PUBDATE} · 三家来源均为站外公开文献</div></div>\n')
            old = old.replace("</main>", card + "</main>", 1)
        idx.write_text(old, encoding="utf-8")
        print("  已并入既有索引")
    else:
        idx.write_text(build_index(built), encoding="utf-8")
    print(f"学科通融建成：/confluence/ · {len(built)} 篇")


if __name__ == "__main__":
    main()
