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
PUBDATE = "2026年7月27日"

PAPERS = [{
<<<<<<< HEAD
    "slug": "discriminative-competence",
    "src": Path("/home/claude/confluence/discriminative-competence.md"),
    "title": "选择听谁，本身就是一次判断",
    "sub": "论鉴别资质的独立性，及证言依赖在何处失效",
    "cross": "美学 × 伦理学 × 知识论",
    "no": "之五",
    "deck": ("在绝大多数事情上靠别人告诉我们，是理性的常态。可有两个领域一直被当作例外："
             "审美判断须基于亲身经验，道德信念不应仅凭他人告知而形成。这两条禁令近年同时遭到强攻，"
             "而三家给出的处理互不相容。本文提出三家共同未加追问的那一步：在这个领域里，"
             "你凭什么认为那个人靠得住——而这个凭什么，一个不具备该领域判断力的人能不能用？"
             "能用的领域，依赖既理性又安全；不能用的领域，选择听谁本身就是那个判断的一次完整行使，"
             "依赖并没有省去判断，只是把它移到了一个不被记录、也不被自己察觉的位置。"),
    "clash": ("若知识论一侧正确（认知自主根本不是一种德性，应由智性互赖取代），"
              "则美学的熟识原则与伦理的道德证言悲观论是把一个误导性理想抬成了规范；"
              "若伦理一侧正确（以证言了结一个问题会使人此后更少去寻求理解），"
              "则互赖的处方正在系统性地生产不再求解的人；"
              "若美学乐观论一侧正确（那条禁令的来源不是认识论而是社会表演，且熟识原则今日已近乎被公认失败），"
              "则前两家都把一条表演规范误诊成了认识论规范。"),
    "sources": [
        ("美学 · 审美证言",
         "《审美证言》斯坦福哲学百科二〇二五年秋季版 —— 熟识原则与自主原则的攻防现状；"
         "另见罗布森《审美证言：一种乐观进路》（牛津大学出版社，二〇二二）书评",
         "https://plato.stanford.edu/archives/fall2025/entries/aesthetic-testimony/",
         "乐观论一侧的方法论要求最要紧：悲观论者必须交出一个说明，说明是什么使审美与味觉"
         "这两个领域独具熟识要求；找不到，那条禁令就只是一组直觉。"),
        ("伦理学 · 道德证言悲观论",
         "《道德理解：从德性到知识》（Noûs 二〇二五）与关于证言在发展理解中作用的悲观论新论证"
         "（Australasian Journal of Philosophy 103(3), 二〇二五）",
         "https://onlinelibrary.wiley.com/doi/full/10.1111/nous.12508",
         "悲观论由静态推进为动态：以证言了结一个问题，会使人此后更少有理由去寻求更广的理解，"
         "从而持续地缺乏理解；而道德理解本身系于领会以及情感与动机的投入。"),
        ("知识论 · 反自主一支",
         "《认知自主的哲学》专题导言（Social Epistemology 二〇二四）与其后二〇二五年"
         "列维—格林—卡沃尔三方公开往还",
         "https://www.tandfonline.com/doi/full/10.1080/02691728.2024.2335623",
         "列维主张「智性自主」是对一种执行管理德性的误导性命名，应改称智性互赖，"
         "并表示一旦把互赖理解妥当就完全不需要再设一个自主的德性；"
         "该支还带着「自己做研究」在若干领域可靠地把人带离真理的经验代价。"),
=======
    "slug": "binding-fails-where-needed",
    "src": Path("/home/claude/confluence/binding-fails-where-needed.md"),
    "title": "约束在最需要它的地方失效",
    "sub": "论自我约束装置的效力与需求的负相关，及其作为定价装置的重新定位",
    "cross": "政治学 × 经济学 × 法学",
    "no": "之五",
    "deck": ("宪法、司法审查、央行独立性、议会对财政的否决权，共同的承诺是：让掌权者不能做他本来能做的事。"
             "而三个领域各自最强的结果——可信承诺命题所依据的利率证据在后续检验中瓦解、"
             "委托的可信性取决于委托安排之外的否决者结构、"
             "反对司法审查的核心论证明确建立在「社会已有良好运转的民主制度」这一前提之上——"
             "合起来指向一个三家都没提出的结论：约束的效力从不由装置自身提供，"
             "因此它与对它的需求呈负相关。本文据此把自我约束装置从禁止装置重新定位为定价装置，"
             "并给出四项替代性评价指标。"),
    "clash": ("第一家明确把「靠声誉」判为不可行，主张真正的约束必须是「不给违约留下余地的规则」；"
              "第二家的结果恰恰是委托的可信性取决于规则之外的政治结构；"
              "第三家则主张最著名的宪法约束装置之一找不到证据表明它更好地保护了权利，"
              "且即使有好结果，它在程序上也是不正当的——而后果论与程序论这两套评价标准互不兼容。"),
    "sources": [
        ("政治学 · 制度与可信承诺",
         "诺思-温格斯特命题及其证据的后续检验 —— Constitutions and Commitment (JEH 49:4, 1989) "
         "与 Clark 1996、Quinn 2001、Stasavage 2002、Sussman & Yafeh 2006 的质疑",
         "https://www.cambridge.org/core/journals/journal-of-economic-history/article/abs/constitutions-and-commitment-the-evolution-of-institutions-governing-public-choice-in-seventeenthcentury-england/2C4D944F5CDDCEBAA6321C7BFF0D2E7A",
         "该文明确把统治者可信承诺的两条路径二分，判声誉路径不可行，"
         "而把制度路径表述为「被约束于一套不给违约留下余地的规则」；"
         "而作为其主要经验支撑的利率断点，在后续检验中未能成立、部分反向。"),
        ("经济学 · 规则、相机抉择与委托的限度",
         "Kydland & Prescott 1977 与 Keefer & Stasavage《委托的限度》(APSR 97:3, 2003)",
         "https://www.cambridge.org/core/journals/american-political-science-review/article/abs/limits-of-delegation-veto-players-central-bank-independence-and-the-credibility-of-monetary-policy/6C1D0BC5F0E2F6D0C0F8E3C2E8D4B6A1",
         "把货币政策委托给独立央行，其可信性并不由该委托安排本身提供，"
         "而取决于该政治体系中否决者的数量与结构——即取决于安排之外的权力分布。"),
        ("法学 · 司法审查的正当性",
         "Waldron《反对司法审查的核心论证》(Yale LJ 115:6, 2006) 与 Fallon 2008 的回应",
         "https://www.yalelawjournal.org/article/the-core-of-the-case-against-judicial-review",
         "两条论证：没有理由认为权利经由司法审查比经由立法机关得到更好保护；"
         "且抛开结果，它在程序上剥夺了多数的自治权。"
         "而该论证明确建立在「社会具有良好运转的民主制度、多数公民认真对待权利」这一前提之上。"),
>>>>>>> 437980adb (Add the fifth Confluence essay: political science, economics and law each evaluate the same kind of device — one that makes a power-holder unable to do what it otherwise could — and their strongest results converge on something none of them states, that such a device never supplies its own force, so it fails hardest where it is needed most)
    ],
}]


def strongify(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"<i>\1</i>", s)   # 期刊名用斜体
    return s


def md_to_html(md):
    out, para, li, toc, n = [], [], [], [], 0

    def flush():
        if para:
            out.append("<p>" + strongify(" ".join(para)) + "</p>")
            para.clear()

    def flush_li():
        if li:
            out.append("<ul>" + "".join(f"<li>{strongify(x)}</li>" for x in li) + "</ul>")
            li.clear()

    for raw in md.splitlines():
        line = raw.rstrip()
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
    flush(); flush_li()
    return "".join(out), toc


def build_page(p, body, toc, pages):
    t = TPL.read_text(encoding="utf-8")
    t = re.sub(r"<title>.*?</title>",
               f'<title>{p["title"]}——{p["sub"]} · 学科通融 | SDE Universes</title>', t, flags=re.S)
    t = re.sub(r'(<meta name="description" content=")[^"]*(")',
               lambda m: m.group(1) + html.escape(p["deck"][:190], quote=True) + m.group(2), t)
    t = re.sub(r'<div class="art-series">.*?</div>',
               f'<div class="art-series">学 科 通 融 · {p["no"]} · {html.escape(p["cross"])}</div>', t, flags=re.S)
    t = re.sub(r'<h1 class="art-title">.*?</h1>', f'<h1 class="art-title">{p["title"]}</h1>', t, flags=re.S)
    t = re.sub(r'<p class="art-sub">.*?</p>', f'<p class="art-sub">{p["sub"]}</p>', t, flags=re.S)
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
