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

PAPERS = [
{
    "slug": "means-becomes-end",
    "src": Path("/home/claude/out/01-换位区间.md"),
    "title": "手段取得终点资格的那一段",
    "sub": "论课堂运行的次序不由目标方向单独结算，及「信息在哪一端多」如何决定该从哪一端开始",
    "cross": "教育学 × 化学 × 艺术学",
    "no": "之六十九",
    "deck": ("课堂如何运行才能让学习真正发生？三门学科各给一条完整的次序，三条互不相容。"
             "教育学说先把要到达的表现写清楚再倒推评估与活动，终点是可观察的表现；"
             "化学工艺说反了——不要先锁定产物，产物形态本身是条件的函数，先定产物等于先把条件锁死；"
             "艺术学的工作室传统给第三条：终点既不是表现也不是条件，是学习者自己那套能继续组织下去的做法。"
             "教育学每天在做的那件事，正是化学工艺诊断为病的那件事。三家共同站着而从未说出的那块地是："
             "**一堂课的运行方式可以由「要到达什么」单独决定，终点一旦确定，中间的次序就只是手段问题**。"
             "推翻它的材料来自化学自己：**逆合成分析与条件筛选并存了几十年，而化学选用哪一套的判据"
             "既不是哪种更科学、也不是事情的性质，是「信息在哪一端多，就从哪一端开始」**——"
             "终点与手段的角色由信息分布决定，因而可以互换。由此命名**换位区间**：一段区间，"
             "在其中原为手段的那一样取得终点资格、原终点退为手段，且它有可查的开合时刻与触发源。"
             "配套读数**换位率**与既有指标正交——一门目标写得最清楚、活动与目标对齐得最好、"
             "进度严格按大纲推进的课，换位率恰恰是零。文中另推出一条阈值：**最优换位时长与目标端的"
             "不确定性无关**，并论证一门同时要求「目标须先行确定并保持稳定」与「设计须依据试用数据修改」"
             "的学问，在不承认这个变量时无法同时守住这两条。"),
    "clash": ("第一家主张一切安排应从可观察的目标表现倒推，因而终点是表现、条件与做法都是手段；"
              "第二家主张产物形态是条件的函数，先锁定目标等于在不知道条件空间长什么样的时候排除大部分可能，"
              "因而终点是把条件建立起来；第三家主张作品与环境都只是副产品，终点是学习者手里那套能自己继续下去的做法。"
              "三家不能同为真，且各自的日课正是另一家诊断出的病——先定终点倒推在工艺开发看来会造出一条纸面上完美、"
              "实际到处断裂的路线；而先定终点这个动作本身在工作室看来会把「组织下去」外包给定终点的那个人。"),
    "sources": [
        ("教育学 · 目标先行与掌握学习",
         "Kulik, Kulik &amp; Bangert-Drowns, Effectiveness of Mastery Learning Programs: A Meta-Analysis "
         "(<i>Review of Educational Research</i> 60:2, 1990)",
         "https://doi.org/10.3102/00346543060002265",
         "把「先确定要到达的表现、再逐级设检查点」确立为可复现的有效做法，"
         "整条次序建立在终点先于过程被写死之上；而这一支自己也知道，"
         "在目标不容易被写成可观察表现的地方，这条次序无处落脚。"),
        ("化学 · 逆合成分析，与条件筛选驱动的发现",
         "Corey, The Logic of Chemical Synthesis (<i>Angewandte Chemie International Edition</i> 30:5, 1991)；"
         "另一端见 Perera et al., A Platform for Automated Nanomole-Scale Reaction Screening "
         "(<i>Science</i> 359:6374, 2018)",
         "https://doi.org/10.1002/anie.199104553",
         "同一门学科并存着两套完整而互相取代的做法：一套从目标分子反向拆解，"
         "一套不先定目标、把条件空间跑开再从给出的东西里挑。"
         "**关键不在于两套并存，而在于化学自己给出了选用判据——信息在哪一端多就从哪一端开始**；"
         "这条在化学里回答的是研发策略问题，从没有人拿它当终点与手段可互换的证据。"),
        ("艺术学 · 工作室讲评与做法的训练",
         "Dannels &amp; Martin, Critiquing Critiques: A Genre Analysis of Feedback Across Novice to Expert "
         "Design Studios (<i>Journal of Business and Technical Communication</i> 22:2, 2008)",
         "https://doi.org/10.1177/1050651907311923",
         "工作室里被反复训练的不是某一件作品，是做作品的人身上那套能自己继续下去的做法；"
         "一件作品完成之后不是结束，是下一件的材料。这一支因此把终点放在做法上，"
         "并据此指出：只要终点被别人定好，「自己组织下去」这件事就没有位置。"),
    ],
},
{
    "slug": "how-many-next-steps",
    "src": Path("/home/claude/out/02-可倒推区间.md"),
    "title": "下一步该做什么，有几个答案",
    "sub": "论课堂运行的次序应当按倒推的解的个数分段，及为什么「目标明确」与「下一步可算」是两件不相干的事",
    "cross": "物理学 × 心理学 × 工程学",
    "no": "之七十",
    "deck": ("课堂如何运行才能让学习真正发生？三门学科给出三条互不相容的次序。"
             "物理学的变分传统说，路径不是一步步试出来的，是由两端条件整体决定的，因此定住两端、路径自己出来；"
             "心理学的刻意练习传统说反了：路径只能一步一步走，而**学习者本人无法确定自己的下一步**，这正是教练存在的理由；"
             "工程学的稳健设计传统说两家都在追一个不该追的东西——**最优点恰恰是最脆弱的点**，"
             "要做的是把工作区放在平坦处，代价就是主动放弃最优。刻意练习要最大化的正是稳健设计要牺牲的。"
             "三家共同站着而从未说出的那块地是：**从当前状态到目标，「下一步该做什么」是一个有确定答案的问题，"
             "分歧只在该怎么求这个答案**。推翻它的材料来自物理学自己：同一个动力系统，"
             "**写成初值问题在很弱的条件下解存在且唯一，写成两点边值问题则可能无解、也可能有无穷多解**；"
             "物理学与数值分析据此选择方法，而这条在那里回答的是「用打靶法还是直接积分」。"
             "**倒推与推进不是同一个动作的两个方向，它们的适定性根本不同。** 由此命名**可倒推区间**（唯一／多解／无解三档），"
             "判据一句：**把这个学生此刻的状态和这门课的目标交给五位有经验的教师，他们说出的「下一步」"
             "是同一件事、五件不同的事、还是都说不出来？** 一次教研活动即可测。"
             "读数与「目标是否明确」正交——目标写得最清楚的课，倒推可以完全无解。"
             "文中另推出一条不对称：**错配的代价在两个方向上不相等，因此在档位不确定时应当默认推进而非倒推**。"),
    "clash": ("第一家主张实际路径由两端条件与一个整体量共同决定，逐步试探不是求解的方式；"
              "第二家主张可迁移的能力只能通过针对当前弱点的、有即时反馈的重复获得，而学习者本人看不见自己的下一步；"
              "第三家主张性能最好的那个点也是对参数变化最敏感的点，因此不该追最优，该选对扰动不敏感的区域。"
              "三条互不相容：变分说的整体决定要求两端都给定，而刻意练习的工作前提是终点只是一个方向；"
              "刻意练习最大化的是特定条件下的表现峰值，而这正是稳健设计要主动削掉的东西。"),
    "sources": [
        ("物理学 · 变分原理，与边值问题和初值问题的适定性差异",
         "Gray &amp; Taylor, When Action Is Not Least (<i>American Journal of Physics</i> 75:5, 2007)；"
         "适定性一侧见 Kierzenka &amp; Shampine, A BVP Solver Based on Residual Control and the MATLAB PSE "
         "(<i>ACM Transactions on Mathematical Software</i> 27:3, 2001)",
         "https://doi.org/10.1119/1.2710480",
         "变分表述把路径写成由两端条件决定的整体量，且这一支自己指出实际路径常常只是驻点、不是极小；"
         "**而更要紧的一条是它旁边那个不对称——初值问题在很弱的条件下解存在唯一，"
         "两点边值问题可以无解、可以有无穷多解**。这条在物理与数值分析里回答的是方法选择问题，"
         "从没有人拿它当「该不该先定终点」的证据。"),
        ("心理学 · 刻意练习",
         "Ericsson, Krampe &amp; Tesch-Römer, The Role of Deliberate Practice in the Acquisition of Expert "
         "Performance (<i>Psychological Review</i> 100:3, 1993)",
         "https://doi.org/10.1037/0033-295X.100.3.363",
         "主张顶尖水平由结构化训练时数而非总年限决定，而结构化的定义里最关键的一条是"
         "**任务由教练根据当前表现指定**；这使「专家能说出下一步」成为这一支能够做研究的前提。"
         "它自己承认效应在缺少成熟教练体系与子技能分解的领域显著减弱，"
         "而它把这个减弱读作有待改进的现状，不读作一个变量。"),
        ("工程学 · 稳健参数设计",
         "Nair (ed.), Taguchi's Parameter Design: A Panel Discussion (<i>Technometrics</i> 34:2, 1992)",
         "https://doi.org/10.2307/1269231",
         "主张寻找的不是性能均值最高的点而是性能对不可控扰动不敏感的区域，二者通常相距很远；"
         "该讨论本身是这一支内部一场公开的争论。它自己的边界也清楚："
         "稳健设计要求性能可测、扰动可枚举——当目标本身说不清是什么时，「对扰动不敏感」没有定义。"),
    ],
},
{
    "slug": "what-the-class-keeps",
    "src": Path("/home/claude/out/03-自建条件.md"),
    "title": "这一节课结束时，这个班手里多了什么",
    "sub": "论学习过程自己造出来、随后成为自己条件的那一类东西，及为什么三家的账本都把条件当作输入",
    "cross": "细胞学 × 工程学 × 艺术学",
    "no": "之七十一",
    "deck": ("课堂如何运行才能让学习真正发生？三门学科给出三条互不相容的次序。"
             "艺术学的判断传统说，只有做出来的那个东西本身算数——过程与条件都不进入判断；"
             "工程学的过程能力传统说反了，而且说得极重：**质量不是检出来的，是造出来的**，只盯成品是最贵的一种错误；"
             "细胞学的生态位传统说两家都把决定性的东西放错了地方——命运不写在细胞里，写在它周围。"
             "艺术学每天在做的那件事，正是工程学诊断为最贵错误的那件事。"
             "三家对条件的地位判断从「排除在外」到「决定一切」，而三家共同假定了同一件事：**条件是给定的输入**。"
             "推翻它的材料来自细胞学自己：**干细胞并不只是被生态位决定——它们分泌基质、招募支持细胞、"
             "重塑自己周围的微环境；而单个肠道干细胞可以在没有间充质生态位的条件下自己长出隐窝-绒毛结构**。"
             "生态位不是住户搬进去的容器，是住户造出来的东西；这条在细胞学里回答的是「体外培养怎样才能成功」。"
             "由此命名**自建条件**：一类由学习过程自己产生、随后被这个过程当作条件继续使用的东西——"
             "**它不是知识，是可以被指着看、可以交给新来的人直接用的物**：一个记号、一条这个班都认的判准、"
             "一份可查的错误清单。配套读数**存量**与既有指标正交——教材、题库、评分表、规程全部齐备且严格执行的课，"
             "存量恰恰是零。文中另推出一条稳态：**存量与外来条件覆盖度线性反相关，且覆盖度趋于完备时存量必然趋零**——"
             "这是设计的必然结果，不是执行不力。"),
    "clash": ("第一家主张判断只能面对作品，因为意图无法核实、过程无法被第三方重走、条件千差万别；"
              "第二家主张检验不产生质量，等成品出来再发现问题时，产生它的那套过程已经又造了一批，"
              "因而必须把注意力从成品移到过程；第三家主张决定性的东西既不在成品也不在过程，"
              "而在周围——同一个基因组放进不同的微环境会长出完全不同的东西。"
              "三条不能同为真：只看作品在过程派看来是最贵的一种终检；管工序在生态位一派看来是在错的层面上使劲；"
              "而建环境在作品一派看来等于用条件为结果开脱。"),
    "sources": [
        ("细胞学 · 生态位，与住户自己造出来的生态位",
         "Scadden, The Stem-Cell Niche as an Entity of Action (<i>Nature</i> 441:7097, 2006)；"
         "推翻材料见 Sato et al., Single Lgr5 Stem Cells Build Crypt-Villus Structures in Vitro Without a "
         "Mesenchymal Niche (<i>Nature</i> 459:7244, 2009)",
         "https://doi.org/10.1038/nature04957",
         "主张细胞命运主要由所处的微环境决定，把细胞搬离原位它就变了；"
         "**而同一门学科自己的材料表明，细胞会分泌基质、招募支持细胞、重塑自己周围的条件，"
         "少量细胞甚至能在没有既成生态位的情况下自己长出结构并长出维持它所需的那些条件**——"
         "这条在细胞学里回答的是体外培养的方法问题，从没有人拿它当条件与产物可互换的证据。"),
        ("工程学 · 过程能力：质量是造出来的，不是检出来的",
         "Benneyan, Lloyd &amp; Plsek, Statistical Process Control as a Tool for Research and Healthcare "
         "Improvement (<i>Quality and Safety in Health Care</i> 12:6, 2003)",
         "https://doi.org/10.1136/qhc.12.6.458",
         "主张把注意力从成品移到过程本身，在过程发生偏移时就介入，因为终检是所有质量手段里"
         "最贵、最慢、信息量最低的一种。它自己承认的边界是：过程控制要求过程可重复、输出可测量——"
         "而当每一次的输出本来就应当不同时，「过程能力」这个量没有定义。"),
        ("艺术学 · 判断面对作品本身",
         "Sadler, Indeterminacy in the Use of Preset Criteria for Assessment and Grading "
         "(<i>Assessment &amp; Evaluation in Higher Education</i> 34:2, 2009)",
         "https://doi.org/10.1080/02602930801956059",
         "论证对作品的整体判断无法被一组预设标准穷尽，评判必须面对作品本身；"
         "这一立场拒绝了一切用意图、努力与工作条件为结果开脱的说法。"
         "而它自己在讲评里天天遇到一处麻烦：两个学生做出了同样水平的东西，"
         "一个下次还能做出来、一个不能，而作品本身看不出这个差别。"),
    ],
},
]


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
