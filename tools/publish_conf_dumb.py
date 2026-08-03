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
PUBDATE = "2026年8月2日"

PAPERS = [{
    "slug": "who-walked-it",
    "src": Path("/home/claude/conf49.md"),
    "title": "那一段谁走的",
    "sub": "论不产出任何可验收之物的那段时间如何生产验收能力，及生成式协助前置产出之后教育内卷的机制改变",
    "cross": "教育学 × 哲学 × 经济学",
    "no": "之五十一",
    "deck": ("人工智能进入教育之后，三门学科各给了一条出路：教育学要给工具装上护栏，让练习重新长出能力；"
             "经济学要换掉学历这个凭据，让筛选对准真正稀缺的东西；教育哲学要把教育从「学习」一词手里要回来，"
             "让人重新成为能自己开口的主体。三条路各自成立，却指定了三个互相取消的终点。"
             "三家共有一个没说出口的前提——一次教育经历的价值，由它的产出被验收时的样子决定；"
             "而推翻它的三件材料全部来自三家自己：练习期成绩上升四成八、工具撤走后低一成七，"
             "说明这段经历在发生时一切可见指标都在变好；年轻组的相对下降由招聘坍塌而非裁员驱动，"
             "说明被砍掉的是入口而不是位置；哲学侧自己写下「召唤不必是显性的」，"
             "说明它发生在没有任何产出的时刻。由此得到的判断是：教育里有一段当期不产出任何可被验收之物、"
             "而日后一切验收能力由它生成的时间——本文称之为哑段。生成式协助做的不是让人变懒，"
             "而是把这段时间的产出提前兑现，于是它在所有账上记为已完成、实际没有被走过。"
             "由此形成的回路不需要人更多，也不需要位置更少，在总投入下降时同样加速——"
             "这使它与经典的内卷概念在方向上分开。文中给出两个可算的读数、一张关键对照表、"
             "十处兑现（其中两处迫使命题收窄）、与十三种既有说法各自可分开的观察、"
             "一条一学期内用现成考务数据可跑完的检验，以及一条四步不可颠倒的可干预次序。"),
    "clash": ("第一家把困境读作技能获得的失败，主张可干预处在工具与任务的设计；"
              "第二家把它读作筛选装置的失灵，主张可干预处在凭据与雇佣制度；"
              "第三家把它读作目的的丧失，主张这件事根本不可被设计，只能被召唤。"
              "三家指定的终点互不相同，因而不能同为出路——而且各自的日课正是另一家诊断出的病："
              "为一切能力找到可测的代理（教育学）是哲学侧诊断的病根，"
              "把教育折算为凭据与回报（经济学）是教育学侧诊断的病根，"
              "坚持有一种价值不可测量不可规模化（哲学）是经济学侧诊断的病根。"),
    "sources": [
        ("教育学 · 护栏可以止损，但没有产生增益",
         "Bastani, Bastani, Sungu, Ge, Kabakc&#305; &amp; Mariman, Generative AI Without Guardrails Can Harm "
         "Learning: Evidence from High School Mathematics (<i>PNAS</i> 122:26, 2025)",
         "https://doi.org/10.1073/pnas.2422633122",
         "近千名高中生的现场实验：无护栏组练习期成绩相对提高约四成八，工具撤走后比从未使用者低约一成七；"
         "经提示词改造的辅导版把负效应抵消到统计上不显著，但未产生长期增益。"),
        ("经济学 · 收缩发生在入口，不在存量",
         "Brynjolfsson, Chandar &amp; Chen, Canaries in the Coal Mine? Six Facts about the Recent Employment "
         "Effects of Artificial Intelligence (Stanford Digital Economy Lab, 2025；2025-11 与 2026-02 两次更新)",
         "https://digitaleconomy.stanford.edu/publication/canaries-in-the-coal-mine-six-facts-about-the-recent-employment-effects-of-artificial-intelligence/",
         "覆盖数百万劳动者的按月薪资记录：高暴露职业中二十二至二十五岁组相对就业下降约一成三，"
         "同职业年长组未见同等下降，且下降主要由招聘收缩而非裁员驱动。该结论目前处在活跃争论中，"
         "本文只取各方均不否认的那条事实。"),
        ("哲学 · 那种召唤发生在没有产出的时刻",
         "Biesta, <i>World-Centred Education</i> (Routledge, 2022)；另见 Generative AI and the Irreducible Role "
         "of Teachers as Callers into Subjectness (<i>Studies in Philosophy and Education</i>, 2026)",
         "https://doi.org/10.1007/s11217-026-10051-w",
         "主张教育有三个目的，其中主体化——成为一个能自己回应的人——既不能被测量也不能被生产，"
         "只能以一种「促其自为」的方式被召唤；并明确写下这种召唤不必是显性的，"
         "教师的在场本身就能提出一个未被说出的问题。"),
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
               lambda m: m.group(1) + html.escape(p["deck"][:190], quote=True) + m.group(2), t)
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
                  f'<p class="hk">{html.escape(p["deck"])}</p>'
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
        n = len(re.sub(r"<[^>]+>", "", body))
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
                    f'<p class="hk">{html.escape(p["deck"])}</p>'
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
