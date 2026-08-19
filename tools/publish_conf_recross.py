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
    "slug": "critical-recrossing",
    "src": Path("/home/claude/conf60.md"),
    "title": "临界回落",
    "sub": "学习为何在抵达之后被记为从未发生，以及承接结构为什么不是帮助完成、而是阻止关闭",
    "cross": "教育学 × 化学 × 管理学",
    "no": "之六十",
    "deck": ("一个学生正在往前想。他已经离开了原来那个安稳的不懂，还没有到达懂，"
             "他处在一个自己维持不住的位置上。然后铃响了，或者老师说“我来讲一下”，"
             "或者他自己觉得说出来会显得很蠢。三十秒后他回到原处。"
             "**在这堂课留下的全部记录里，这三十秒不存在**——他与后排那个从头到尾在想中午吃什么的同学，"
             "在所有的账上是同一笔。本文把这一类事件从不存在变成一个可以被清点的对象，"
             "并说明为什么它至今没有一行：三条互不相容的现行解释——取向说、路径说、计量说——"
             "对“那几十秒该由谁动”给出三个不能同真的答案（教师动／制度动／不需要任何人动），"
             "**而每一家的处方恰好是另一家诊断出的病因**；三家却共同假定了一条谁也没说出口的东西："
             "在一段有界的过程里，改变从哪个位置发起是由角色事先定死的。"
             "推翻它的材料来自三家之一自己——在反应条件下，起作用的活性相不是投料时投进去的那一相，"
             "而是被反应本身长出来的，**发起权在同一个封闭体系内部换过手**。"
             "由此得到一张两轴辨别格（抵达 × 承接）、一句不含情态词的问话，"
             "以及两个必须分开的读数：**回落率**是三领域可通约的上界，**关闭率**才是承重的那个子集。"
             "把两个读数与机制放在一起还能直接推出一条**容量折线**："
             "净学习在抵达数等于承接容量处取最大值，此后按固定斜率下降，"
             "**而拐点的位置只由课时长度、班额、允许的沉默时长这些结构量决定，可在开课之前算出来**；"
             "并在一份公开的多机构数据（三十一门课／二十八所机构／两千八百五十五名学生）上"
             "对这条折线做了实测——**控制承接容量之后，抵达事件的偏效应为零，该预言未获支持**；"
             "而无功效的原因本身是一个结果：现实中凡是提高提问密度的做法同时也提高了小组时间，"
             "**本模型所要的那个「容量不变而抵达增加」的对照在野外不存在，必须新造**。"
             "本文最锋利的一步在这里：承接的功能不是帮助学习者完成那次转化，"
             "而是在那段不可自持的时间里**阻止一次关闭性归因**——"
             "这解释了为什么及时给出答案在短期指标上是改善、在关闭上是加速，"
             "为什么同伴的作用常大于教师且在同伴水平更低时依然如此（同伴不具备关闭的权威），"
             "以及为什么大规模的思维干预效应很小（它改的是关闭的措辞，不是是否关闭）。"
             "最后一句本文不打算缓和：**近三十年真实有效的教学改良提高了抵达率，"
             "而承接容量没有同步改变，因此它们在提高完成数的同时更快地提高了回落数，"
             "而后者不出现在任何一份报告里。**"),
    "clash": ("把三家摆到同一个问题上——一个学习者已经进入了他自己维持不住的推断，"
              "接下来的那几十秒该由谁动——三个答案不能同时为真。"
              "第一家答由教师动：取向不是学生能自己选的，它由感知到的评价要求诱发，"
              "指望他在这几十秒里自己翻转它等于指望结果去改原因；"
              "第二家答由制度动且绝不能由现场的个体判断来动，"
              "因为不被计量的动作在多任务代理下必然被从可测的那一侧抽走，"
              "而可审计只能审到可见动作那一层；"
              "第三家答不需要任何人动，因为转化发不发生只由路径决定，"
              "在有多条竞争通道的体系里普遍加压永远是选择性的敌人。"
              "三条互相取消，而且各自的处方正是另一家诊断出的病因："
              "教师及时进入正是第二家所说的普遍加压，"
              "把它做成可考核正是第一家所说的评价条件诱发浅层取向，"
              "零干预只修路径正是第三家所说的不可测者被判为不存在。"),
    "sources": [
        ("教育学 · 深浅学习取向，与它下游那条更硬的证据",
         "Marton &amp; S&auml;lj&ouml;, On Qualitative Differences in Learning: I&mdash;Outcome and Process "
         "(<i>British Journal of Educational Psychology</i> 46:1, 1976)；"
         "下游见 Kirschner, Sweller &amp; Clark, Why Minimal Guidance During Instruction Does Not Work "
         "(<i>Educational Psychologist</i> 41:2, 2006)",
         "https://doi.org/10.1111/j.2044-8279.1976.tb02980.x",
         "主张同一堂课同一教师同一份材料，取向不同学得完全不同，故教学法不决定学习、取向决定学习，"
         "而取向由学生感知到的评价要求诱发；"
         "而这一支自己确立的另一件事——取向不是一个人的稳定属性，同一学生在同一天的两门课里可以是两种取向——"
         "等于承认它是在每一次具体互动里被重新定住的，只是它从不问定在哪一秒。"),
        ("化学 · 过渡态理论的单因主张，与反应条件下的活性相重构",
         "Tao, Grass, Zhang, Butcher, Renzas, Liu, Chung, Mun, Salmeron &amp; Somorjai, "
         "Reaction-Driven Restructuring of Rh-Pd and Pt-Pd Core-Shell Nanoparticles "
         "(<i>Science</i> 322:5903, 2008)；另见 Halpern, Mechanism and Stereoselectivity of "
         "Asymmetric Hydrogenation (<i>Science</i> 217:4558, 1982)；"
         "理论侧见 Truhlar, Garrett &amp; Klippenstein, Current Status of Transition-State Theory "
         "(<i>J. Phys. Chem.</i> 100:31, 1996)",
         "https://doi.org/10.1126/science.1164170",
         "主张热力学允许的转化绝大多数不发生，不是因为没有能量，而是因为没有可走的路，故唯有路径是决定项、"
         "普遍加压是选择性的敌人；"
         "而这一支自己在近常压条件下反复观测到的一件事——活性相是被反应本身长出来的，不是投料时投进去的那一相，"
         "且气氛一变可以换回去——说明发起权在同一个封闭体系内部换过手，"
         "只是化学把它记在“反应前的表征为什么与实际活性对不上”名下。"),
        ("管理学 · 计量结构说，与它自己关于脱耦换代的观察",
         "Espeland &amp; Sauder, Rankings and Reactivity: How Public Measures Recreate Social Worlds "
         "(<i>American Journal of Sociology</i> 113:1, 2007)；"
         "另见 Kerr, On the Folly of Rewarding A, While Hoping for B (<i>AMJ</i> 18:4, 1975)；"
         "Holmstr&ouml;m &amp; Milgrom, Multitask Principal&ndash;Agent Analyses "
         "(<i>JLEO</i> 7, 1991)；Bromley &amp; Powell, From Smoke and Mirrors to Walking the Talk "
         "(<i>Academy of Management Annals</i> 6:1, 2012)",
         "https://doi.org/10.1086/517897",
         "主张只有什么被算作数是决定性的：当一项任务可测而另一项不可测时，对可测任务的任何强化激励都会把努力从不可测那一侧抽走，"
         "而被测者会重新组织整个条件场以适应测量；"
         "而这一支自己写明的脱耦换代——新的那一种是组织真的照做了、做得越来越认真、"
         "而这些动作与本来要服务的目的之间的联系已经断了——"
         "它用来解释合法性演化，没有用来问那些真的做出来的动作去了哪里。"),
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
    t = t.replace("典范文专栏 · 作者 Claude ·", "学科通融 · 作者 王德生 ＋ Claude ·")
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
<footer>学科通融 · 作者 王德生 ＋ Claude · © 德麦国际 Demai International</footer>
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
