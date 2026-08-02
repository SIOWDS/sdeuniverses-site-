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
    "slug": "how-many-is-one",
    "src": Path("/home/claude/conf/how-many-is-one.md"),
    "title": "一件是几件",
    "sub": "论生成成本趋零之后计数单位失去下界，以及「并项」这个从未被生产的单位",
    "cross": "经济学 × 艺术学 × 工程学",
    "no": "之四十九",
    "deck": ("产生一件东西的代价降到接近于零之后，几乎每个行当都在报告同一组读数：交出来的件数暴涨、人均件数暴涨，"
             "而通过的人没有变多。这被普遍读作「投入增加而产出不增」。本文指出这个读法有一个从未被检验的前提——"
             "它假定**「一件」是一个稳定的计数单位**，因而件数上升可以充当投入上升的证据。"
             "三个互不往来的学科各自持有一套关于「是几件」的成熟读法，而三套不能同真："
             "计量与指数理论说把产出按质量调整后加总即可、件数无关；当代艺术的本体研究说一件作品是不是「一件」由创作者可公开查证的授权决定；"
             "流动与批量理论说一个变更是不是「一个」由交易成本与持有成本的 U 形权衡决定、不存在独立于流水条件的答案。"
             "三家争的是「是几件」该由哪一维读出，而共同假定了**它是一个可以被单独读出的事实**。"
             "推翻它的材料来自三家自己：指数理论承认品种更替够快时项目全域是流动的、不存在跨期一致的同一样商品；"
             "批量理论承认交易成本被自动化压掉后最优批量随之变小——推到底则**「一个」没有下界**；"
             "作品研究承认许多作品在保管者介入之前于关键方面是不定的、件数由一句授权规定。"
             "由此得到一条三家都到不了的判断：**这一轮的「更卷」不是产出量增加、不是作品数增加、也不是工作项增加，"
             "而是「一件」这个计数单位失去了下界**——件数与「把全部提交合并同类项之后还剩几项」之间裂开了一道口子，"
             "而后者从来没有被任何人生产过，因为它不归任何人。本文把后者命名为**并项**，"
             "并指出真正的后果不是某一件事变糟，而是**一整排以件为分母的读数同时失去意义而外表毫无变化**（人均件数、每岗申请数、"
             "每人年发表数、通过率、变更频率）。文中给出一句只问记录的问话（把这一轮的全部提交合并同类项，还剩几项）、"
             "一个三领域量纲不同而比率相同的读数（**并项率**，与产量、频率、周期正交：部署频率最高的精英团队并项率可以最低）、"
             "三个写死判准的算例、两轴四格与靶格（件数上升而并项不增，且它由正确的管理造成）、十三处兑现、"
             "与专利族／切香肠／古德哈特／压缩率／模块化／分母问题等十种既有说法的判决性分界、"
             "三处反过来削弱本文的约束（其中一处把读数从绝对量降为同期横比量）、八条排除了最强竞争解释的判错条件，"
             "以及一条写死到二〇二九年十二月三十一日的赌注。"),
    "clash": ("三家在「一件东西凭什么算一件」这同一问题上给出互相取消的答案："
              "计量与指数理论说看结果这一维就够（按质量调整后加总，件数无关）；"
              "当代艺术本体研究说看完成动作这一维就够（创作者可公开查证的授权规定了作品边界）；"
              "流动与批量理论说看条件这一维就够（批量由交易成本与持有成本的 U 形权衡决定，件数随条件而变才是对的）。"
              "三条处方在同一位学者的十二篇论文上正面分岔——改用质量加权、承认十二次独立完成、还是接受更小的批量并把评审也做小；"
              "而三家各自撑不住的那一处，恰好是另一家的主张。"),
    "sources": [
        ("经济学 · 计量与指数理论",
         "Advisory Commission to Study the CPI《Toward a More Accurate Measure of the Cost of Living》(Boskin Report, 1996)；"
         "Griliches《Hedonic Price Indexes for Automobiles》(NBER 1961)；Hausman《Sources of Bias and Solutions to Bias in the CPI》(JEP 17(1), 2003)",
         "https://www.ssa.gov/history/reports/boskinrpt.html",
         "把产出按质量调整后加总即可读出「多了没有」，件数无关。而这一家自己写着：品种更替够快时，被比较的那一组东西本身是流动的——"
         "不存在跨期一致的「同一样商品」。它拿这条答「通胀被高估多少」，从不拿它当「件也没有一致含义」的证据。"),
        ("艺术学 · 作品个体化与创作者授权",
         "Sherri Irvin《The Artist's Sanction in Contemporary Art》(Journal of Aesthetics and Art Criticism 63(4), 2005)；"
         "《Immaterial: Rules in Contemporary Art》(Oxford University Press, 2022)",
         "https://philpapers.org/rec/IRVTAS",
         "一件作品是不是「一件」，不由材料或外观决定，而由创作者可被公开查证的授权行为决定；规则本身已成为一种艺术媒介。"
         "而这一家自己承认：许多需要保管者按规则重新实现的作品，在他人介入之前于关键方面是不定的——件数由一句话规定，且规定它的可以不止一人。"),
        ("工程学 · 流动与批量理论",
         "Donald G. Reinertsen《The Principles of Product Development Flow》(Celeritas, 2009)，B11 批量经济学原理（U 形优化）、B12 低交易成本、B13 批量减小的收益",
         "http://lpd2.com/sample-page/the-principles-of-flow/",
         "一个变更是不是「一个」，由交易成本与持有成本的 U 形权衡决定，不存在独立于流水条件的答案。"
         "而这一家自己写着：测试自动化压低了交易成本，因而使小得多的批量成为可能——顺着这条曲线推到底，"
         "最优批量的存在依赖交易成本有正的下限；下限没了，「一个」在它自己的理论里就没有底。"),
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


def build_page(p, body, toc, pages, wan):
    t = TPL.read_text(encoding="utf-8")
    css = (ROOT / "tools" / "confluence-article.css").read_text(encoding="utf-8")
    t = re.sub(r"<style>.*?</style>", "<style>" + css + "</style>", t, count=1, flags=re.S)
    t = re.sub(r"<title>.*?</title>",
               f'<title>{p["title"]}——{p["sub"]} · 学科通融 | SDE Universes</title>', t, flags=re.S)
    t = re.sub(r'(<meta name="description" content=")[^"]*(")',
               lambda m: m.group(1) + html.escape(p["deck"][:190].replace("**",""), quote=True) + m.group(2), t)
    t = re.sub(r'<div class="art-series">.*?</div>',
               f'<div class="art-series">学 科 通 融 · {p["no"]} · {html.escape(p["cross"])}</div>', t, flags=re.S)
    t = re.sub(r'<h1 class="art-title">.*?</h1>', f'<h1 class="art-title">{p["title"]}</h1>', t, flags=re.S)
    t, _n = re.subn(r'<(p|div) class="art-sub">.*?</\1>', lambda m: f'<{m.group(1)} class="art-sub">{p["sub"]}</{m.group(1)}>', t, flags=re.S)
    assert _n == 1, f"art-sub 替换了 {_n} 处"
    assert p["sub"][:12] in t, "art-sub 未写入" 
    t = re.sub(r'<div class="art-meta">.*?</div>',
               f'<div class="art-meta">王德生 ＋ Claude · 约 2.4 万字 · {pages} 页 · '
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
        (d / "index.html").write_text(build_page(p, body, toc, pages, round(len(re.findall(r'[\u4e00-\u9fff]', re.sub(r'<[^>]+>','',body)))/10000,1)), encoding="utf-8")
        rd = (ROOT / "public" / "paradigm" / "taken-out" / "read.html").read_text(encoding="utf-8")
        rd = rd.replace("/paradigm/taken-out", f'/confluence/{p["slug"]}') \
               .replace("taken-out", p["slug"]).replace("一拿出来，就不是它了", p["title"]) \
               .replace("典范文专栏", "学科通融")
        (d / "read.html").write_text(rd, encoding="utf-8")
        n = len(re.findall(r'[\u4e00-\u9fff]', re.sub(r'<[^>]+>', '', body)))
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
            card = (f'<div class="item" data-ch="c1"><div class="n">{p["no"]} · 三学科交叉：{html.escape(p["cross"])}</div>'
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
