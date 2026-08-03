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
    "slug": "both-sides-of-the-equation",
    "src": Path("/home/claude/conf54.md"),
    "title": "方程两边都有它",
    "sub": "论一类被记入学习者账户、却不进入净变化的课堂轮次，及决定它锁死与否的不是障碍高度与延迟长度，而是首次选择的可逆性",
    "cross": "教育学 × 化学 × 管理学",
    "no": "之五十四",
    "deck": ("课堂顺利完成、学生当场答对，而支持一撤、时间一延、情境一换，成果迅速消失。"
             "教育学把病灶放在协助的量与时机，管理学放在公开指标对被测系统的反向塑造，"
             "两家的处方互不相容，却共有一个没说出口的前提：可验收的产物属于交出它的那个人。"
             "推翻它的材料来自被引来作类比的第三家自己——化学写净离子方程时，"
             "把在方程两边同时出现、未进入焦点转化的组分划掉，称旁观离子；"
             "它在体系中、浓度可测、维持电中性、缺了它反应甚至不成立，"
             "而这些没有一条使它进入净变化。**归属由是否进入焦点转化决定，不由是否在场决定。**"
             "由此命名旁观轮次，并做一次必须做的术语修正：本文处理的是同一产物两条路径，"
             "属选择性而非速率，承重的那一步不是限速步而是**分岔步**——"
             "于是要交还给学生的不是最难的一步，是分岔的那一步；难而不分岔的代做无害，不难却分岔的代做致命。"
             "最强的一条结论来自动力学控制与热力学控制：占优的是生成最快的还是最稳定的，"
             "取决于**可逆性**而非障碍高度。课堂的首次作答高度不可逆——提交即计分、答案给出即不可未看见，"
             "因此延长测验延迟与提高任务难度根本不进入路径选择，"
             "这正是延迟测验、撤除支架与增加活动三类改革局部有效、随后被吸收的形式解释。"
             "文中另给两个当场可算的读数，并论证一门同时持有「日志活跃是学习代理」"
             "与「日志活跃可与学习负相关」两条既有结论的学科，在不承认本文变量时无法自洽。"),
    "clash": ("第一家主张决定学习的是协助的量与时机——给多则浅层学习，给少则挫败，最优点在中间；"
              "第二家主张病不在教学技巧而在公开指标，被测量的结果会反过来改造被测系统，"
              "故必须改指标、改责任周期；第三家主张产物不能识别路径，"
              "而多条路径中哪一条占优，第一取决于可逆性而非障碍高度。三家不能同为真，"
              "且各自的日课正是另一家诊断出的病：调协助量的方子会被评价系统在下一轮压回去（管理判教育），"
              "改指标与加延迟测验改的仍是时间与障碍、而这两个量在不可逆条件下不进入选择（化学判管理），"
              "而所谓「给第二次机会」若只是减少协助量的一个换算，可逆性就不是另一根轴（教育判化学）。"),
    "sources": [
        ("教育学 · 协助两难与元认知惰性",
         "Koedinger &amp; Aleven, Exploring the Assistance Dilemma in Experiments with Cognitive Tutors "
         "(<i>Educational Psychology Review</i> 19:3, 2007)；另见 Fan, Tang, Le, Shen, Tan, Zhao, Shen, Li &amp; "
         "Gašević, Beware of Metacognitive Laziness (<i>BJET</i> 56:2, 2025)；Baker, Corbett, Koedinger &amp; "
         "Wagner, When Students “Game the System” (CHI 2004)",
         "https://doi.org/10.1007/s10648-007-9049-0",
         "主张核心变量是协助的量与时机，最优点在给多与给少之间；"
         "而这一支自己确立的求助滥用与钻系统空子结果表明，日志上最活跃的那批学生学得最少——"
         "同样的协助量落在不同步骤上后果不可比，故它不是一条曲线。"),
        ("化学 · 净离子方程、选择性决定步与动力学／热力学控制",
         "IUPAC <i>Compendium of Chemical Terminology</i>（Gold Book）: mechanism, intermediate, catalyst, "
         "rate-controlling step, kinetic control, thermodynamic control；另见 Buskirk, Can Reaction "
         "Mechanisms Be Proven? (<i>J. Chem. Educ.</i> 86:5, 2009)；Carey &amp; Sundberg, "
         "<i>Advanced Organic Chemistry</i> Part A (5th ed., Springer 2007)",
         "https://goldbook.iupac.org/terms/view/R05139",
         "写净离子方程时，在方程两边同时出现而未进入焦点转化的组分被划掉，称旁观离子——"
         "它在场、可测、甚至必要，却不在净变化里。这一条正是推翻共有前提的材料；"
         "而占优产物由可逆性而非障碍高度决定，这一条给出本文最独有的干预。"),
        ("管理学 · 指标反应性与制度脱耦",
         "Espeland &amp; Sauder, Rankings and Reactivity (<i>American Journal of Sociology</i> 113:1, 2007)；"
         "另见 Meyer &amp; Rowan, Institutionalized Organizations (<i>AJS</i> 83:2, 1977)；"
         "Bevan &amp; Hood, What’s Measured Is What Matters (<i>Public Administration</i> 84:3, 2006)",
         "https://doi.org/10.1086/517897",
         "主张公开指标不是中性的镜子，它通过反应性重塑被测组织，故病灶在评价与责任结构；"
         "而这一支自己承认，脱耦可以在无人作弊的情况下长期存续——"
         "这恰恰说明指标扭曲不能单独说明认知工作在何处被替换。"),
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
