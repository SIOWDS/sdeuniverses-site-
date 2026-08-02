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
    "slug": "before-first-reading",
    "src": Path("/home/claude/conf/before-first-reading.md"),
    "title": "第一个读数之前",
    "sub": "论新旧之别不在产出、不在效率、也不在承认，而在一样东西从被做出来到取得第一个读数所需的时间",
    "cross": "经济学 × 艺术学 × 工程学",
    "no": "之五十",
    "ch": "c1",
    "deck": (
        "一个领域有没有真的长出新东西？工程学说看输出——在标准评测上的表现就够了；经济学说看投入产出比——"
        "把多少人力组织成多少产出增长，这正是「想法越来越难找」那条读数的做法；艺术学说两个都不算数——"
        "一样东西是不是那件事由条件场决定，而条件场自己是被历史地生产出来的。把同一个用人工智能大幅提高了"
        "产出的团队交给三家，一家判进步、一家判衰退、一家判两边都在测一个已经不在那里的东西。"
        "三家共同假定了**这件事可以在某一维上单独读出来**，而**推翻这条假定的材料来自其中一家自己**："
        "研究生产率必须为每个领域各选一个产出代理，而代理只能从已被承认为该领域产出的那一类里挑——"
        "于是新的产出落在分子之外、却已经落在分母之内，这条读数在结构上必然下降，与新东西实际有多少无关。"
        "由此得到的判断是：**新与旧的分别不在产出、不在效率、也不在承认，而在无量期的长短**——"
        "一样东西从被做出来到在任何一维上取得第一个读数之间的那一段；在此之前它在三家账上都不是「小」，是零。"
        "而人工智能压缩的只是**已有现成读数**那一类的无量期，完全没有压缩**需要先造一把新尺子**的那一类，"
        "两类的显形速度差被拉开了数量级；资源被抽向短的那一侧不是因为人短视，是加总规则的算术后果。"
        "文中给出一句不含判断词的问话（上一轮做完的东西里，有多少件在开工时还没有任何现成的量可以判定它）、"
        "一个四领域量纲不同而比率相同的读数（无量期占比）、两轴四格与最危险的那一格（断供）及三个写实场景、"
        "十二处兑现、三件有固定次序的出路与一条反直觉推论（**在造尺子被单独记账之前，任何提高评价质量的努力"
        "都会拉大差距**）、两处反过来把本文削小的约束、与十种既有说法的判决性分界（含最危险的方法学占位者"
        "「睡美人系数」）、与本栏同题六篇各一条对照预测，七条排除了最强竞争解释的判错条件，"
        "以及一条写死到二〇三一年年中的赌注。**本稿为理论建构与研究设计，不报告任何虚构的样本、"
        "统计结果或实验结论。**"),
    "clash": (
        "三家在「一个领域有没有真的长出新东西该在哪儿读出来」这同一问题上给出互斥答案："
        "工程学说看输出在标准评测上的表现就够了；经济学说看投入产出比就够了；"
        "艺术学说两个都是由旧条件定义的代理，而条件场自己正在被改变，因而两个读数都在测一个已经不在那里的东西。"
        "把同一个对象交给三家，得到判进步、判衰退、判两边都在测错三种不能并存的归属。"),
    "sources": [
        ("经济学 · 研究生产率与产出代理",
         "Are Ideas Getting Harder to Find?（Bloom, Jones, Van Reenen & Webb, *American Economic Review* 110(4), 2020）",
         "https://www.aeaweb.org/articles?id=10.1257/aer.20180338",
         "长期增长率＝有效研究人员数 × 研究生产率；多领域证据显示研究投入大幅上升而研究生产率急剧下降"
         "（维持芯片密度每两年翻番所需的研究人员是 1970 年代初的十八倍以上）。"
         "关键的技术细节是：因为「想法」没有统一单位，每个领域必须各选一个产出代理——"
         "晶体管密度、作物单产、寿命、获批新药。"),
        ("工程学 · 基准饱和与构念效度",
         "When AI Benchmarks Plateau: A Systematic Study of Benchmark Saturation（Akhtar et al., 2026, arXiv:2602.16763）；"
         "另见对 445 篇基准论文的系统检查（Bean et al., 2025）与欧盟联合研究中心的评测审视（Eriksson et al., 2025）",
         "https://arxiv.org/abs/2602.16763",
         "六十个常用基准中二十九个出现高度或极高度饱和——排在前面的模型被压缩在一起，"
         "分数差不再对应能力差；污染与构念效度问题被普遍承认。该支给出的处方始终是造更好的基准，"
         "即承认尺子不好、但不承认「尺子」这个判定位置有问题。"),
        ("艺术学 · 现场性是被历史地生产出来的范畴",
         "Liveness: Performance in a Mediatized Culture, 3rd ed.（Philip Auslander, Routledge, 2023）；"
         "Digital Liveness: A Historico-Philosophical Perspective（*PAJ* 34(3), 2012）；"
         "对照 Peggy Phelan, *Unmarked*（1993）",
         "https://www.routledge.com/Liveness-Performance-in-a-Mediatized-Culture/Auslander/p/book/9780367468170",
         "「现场」不是可在技术之外被指认的本体属性，它作为一个范畴是在录音与广播出现之后才成立的；"
         "本真性并不站在技术之外，它是技术的产物。推论：一样东西是不是那件事由条件场决定，"
         "而条件场自己在动——因此「被不被承认」永远滞后于「发生」。"),
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


WAN = 0.0


def build_page(p, body, toc, pages):
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
    t, _n = re.subn(r'<(p|div) class="art-sub">.*?</\1>', f'<div class="art-sub">{p["sub"]}</div>', t, count=1, flags=re.S)
    assert _n == 1, "art-sub 未被替换——副题会残留上一篇的"

    t = re.sub(r'<div class="art-meta">.*?</div>',
               f'<div class="art-meta">王德生 ＋ Claude · 约 {WAN} 万字 · {pages} 页 · '
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
        globals()["WAN"] = round(len(re.findall(r"[\u4e00-\u9fff]", re.sub(r"<[^>]+>", "", body))) / 10000, 1)
        (d / "index.html").write_text(build_page(p, body, toc, pages), encoding="utf-8")
        rd = (ROOT / "public" / "paradigm" / "taken-out" / "read.html").read_text(encoding="utf-8")
        rd = rd.replace("/paradigm/taken-out", f'/confluence/{p["slug"]}') \
               .replace("taken-out", p["slug"]).replace("一拿出来，就不是它了", p["title"]) \
               .replace("典范文专栏", "学科通融")
        (d / "read.html").write_text(rd, encoding="utf-8")
        n = len(re.sub(r"<[^>]+>", "", body))
        built.append((p, WAN, pages))
        print(f'  {p["slug"]}: {n} 字 · {pages} 页 · 目录 {len(toc)} 节 · 来源 {len(p["sources"])} 家')
    idx = CF / "index.html"
    if idx.exists() and "measurable-face" in idx.read_text(encoding="utf-8"):
        old = idx.read_text(encoding="utf-8")
        for p, wan, pages in built:
            if f'/confluence/{p["slug"]}/' in old:
                continue
            ones = "".join(f'<div><b>{html.escape(k)}</b><a href="{u}">{html.escape(ti)}</a></div>'
                           for k, ti, u, g in p["sources"])
            card = (f'<div class="item" data-ch="{p["ch"]}"><div class="n">{p["no"]} · 三学科交叉：{html.escape(p["cross"])}</div>'
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
