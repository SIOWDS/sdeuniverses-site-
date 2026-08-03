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
    "slug": "block-out-the-rest",
    "src": Path("/home/claude/一·先挡住其余的.md"),
    "title": "先挡住其余的",
    "sub": "论课堂为使一处改变而作的悬置，如何在悬置期内结成无人拆除的连接",
    "cross": "教育学 × 化学 × 艺术学",
    "no": "之六十六",
    "deck": ("要讲清一件事，几乎总要先说一句「暂时不考虑」——不挡住其余部分，那一处就淹没在其余部分里。"
             "教育学把这种悬置读作认知负荷的合理分配，化学读作合成里的保护基策略，艺术学读作作品的未完成状态。"
             "三家争的是改变由什么驱动，而共同假定了一条没说出口的话：**被挡住的那部分不参与，参与名单是给定的。**"
             "推翻它的材料来自化学自己——**酰基迁移**：用来挡住一个位点的基团会自己跑到另一个位点上去，"
             "挡住这个动作改写了它本要固定的那张名单；而结果在形式检查上仍然合格，"
             "错误不表现为失败，表现为**一个位置不同的正确产物**。"
             "由此命名**悬置连接**：悬置期内被悬置项与新学内容之间自行结成、脱悬后不被拆除、也不进任何账本的关联。"
             "承重判断是：学习之所以少，不是那一处该变的没变，而是每一次悬置都附带产出一批未被指认的连接，"
             "它们在原题型里从不出错、只在换情境时决定表现，而课堂的账本按内容点记，看不见内容点之间的东西。"
             "文中给出悬置密度与脱悬率两个读数、四种亚型、一段初中物理单元的完整推演"
             "（那条多出来的等号如何形成、拆解为何只要十分钟、而它为何从未被拿出来），"
             "以及化学反过来削掉的一条价值排序：**少挡优先于多拆**。"),
    "clash": ("第一家主张学习由原有解释与新经验的不相容驱动，故处方是制造认知冲突；"
              "第二家主张选择性来自阻断而非驱动，要让一处反应必先把其余位点挡住；"
              "第三家主张一件东西算不算完成，由它被放进什么样的条件决定，而非由制作者的意图或技术完成度决定。"
              "三条不能同时为真，且各自的日课正是另一家诊断出的病：**化学每天在做的「先挡住其余」，"
              "恰恰在原理上取消了不相容得以发生的条件**（化学判教育）；"
              "艺术学让未竟状态保持可见、交由后来的条件判定，在合成里就叫脱保护没做完就出料（化学判艺术）；"
              "而教学要求在单元结束时给出完成判定，正是艺术学主张不该在制作现场作出的那件事（艺术判教育）。"),
    "sources": [
        ("教育学 · 概念转变：不相容驱动路径改变",
         "Posner, Strike, Hewson &amp; Gertzog, Accommodation of a Scientific Conception "
         "(<i>Science Education</i> 66:2, 1982)；另见 Strike &amp; Posner, A Revisionist Theory of "
         "Conceptual Change (SUNY Press, 1992)",
         "https://doi.org/10.1002/sce.3730660207",
         "主张决定学习的不是信息是否到达，而是原有解释是否被逼到必须重组；"
         "而这一支的修正稿自己承认，原有概念的**整个生态**——包括与目标概念看似无关的部分——"
         "都参与对新经验的接纳与排斥。这句话从未被用来问：教学明确挡住一部分生态时，被挡的那部分是否仍在参与。"),
        ("化学 · 保护基策略与酰基迁移",
         "Baran, Maimone &amp; Richter, Total Synthesis of Marine Natural Products without Using "
         "Protecting Groups (<i>Nature</i> 446, 2007)；另见 Wuts &amp; Greene, "
         "<i>Greene's Protective Groups in Organic Synthesis</i> (4th ed., Wiley 2007)",
         "https://doi.org/10.1038/nature05569",
         "主张多官能团分子能被改造成什么，取决于哪些位点在这一步被挡住，而非试剂多强。"
         "这一支自曝两处：保护每加一对，收率下降、步骤增加，故有一整支在追求**不用保护基**的路线；"
         "而酰基迁移说明，挡住这个动作本身会改写它要保护的那张名单。"),
        ("艺术学 · 未完成状态与完成判定",
         "Schulz, Michelangelo's Unfinished Works (<i>The Art Bulletin</i> 57:3, 1975)",
         "https://doi.org/10.2307/3049410",
         "主张一件东西算未完成还是算作品，不由作者意图也不由技术完成度决定，"
         "而由它被放进什么样的展示与流通条件决定；同一块石头在工作室里叫未完成，进美术馆就叫作品。"
         "这一支自曝：许多被称为未完成的作品，作者当时并不这么认为——未完成这个身份是后世追加的。"),
    ],
}, {
    "slug": "read-while-still-moving",
    "src": Path("/home/claude/二·还在动的时候就读了数.md"),
    "title": "还在动的时候就读了数",
    "sub": "论课堂判定的时点相对于重组时长过早，如何把仍在进行的变化冻在当时的构型上",
    "cross": "物理学 × 心理学 × 工程学",
    "no": "之六十七",
    "deck": ("课堂每隔一两周作一次「会了没有」的判定，并据此配置此后的一切条件；判定的时点由课表决定，"
             "不由被判定的那件事本身决定。物理学主张决定一个系统有没有在变的是弛豫时长与观测窗口之比，"
             "心理学主张一次提取会主动抑制同类竞争项，工程学主张进不了传感回路的状态就进不了控制。"
             "三家争的是变化由什么驱动，而共同假定了一条没说出口的话："
             "**正在变的部分与不在变的部分，可以在观测的那一刻被分开。**"
             "推翻它的材料来自物理学自己——**物理老化**：被判为「冻住了」的玻璃态系统，"
             "性质随冻住之后所等的时间持续演化，且演化的起点正是被冻住那一刻的构型。"
             "⇒ **读数为零是关于窗口的，不是关于系统的**；而判定这个动作参与了后续演化的初始条件。"
             "由此命名**冻结构型**，并给出一个不需要分母、任何学校都做得起的读数：**双向翻转率**——"
             "同一份卷子隔四周原样再做、期间不教，看有多少人翻过来、两个方向各占多少。"
             "**单向翻转是遗忘的签名；「不会到会」那一支显著非零，是本文的独有签名，遗忘与「没学扎实」都预测不出它。**"
             "文中另逼出教育测量学的一处自相矛盾，并给出一段初中数学单元的完整推演："
             "同一次不及格里混着重组时长差一个数量级的三类学生，而补救内容的性质决定了哪一类被救、哪一类被冻。"),
    "clash": ("第一家主张一个系统是固体还是流体、有没有在变，只由弛豫时长与观测时长之比决定，与驱动力大小无关；"
              "第二家主张决定什么留下的是提取时的竞争关系，遗忘不是衰退而是提取这个动作自己造成的抑制；"
              "第三家主张系统实际表现成什么样，取决于哪些状态进得了反馈回路，而非这些状态本身多要紧。"
              "三条不能同时为真：**工程学「不可观测就证明它稳定然后不管」的日课，"
              "正是物理学诊断的病根——看起来不动恰恰不是稳定的证据**（物理判工程）；"
              "心理学最有力的教学建议是用提取来巩固，而它同一套实验证明提取会主动抑制同类未被提取项（心理判自己）；"
              "而物理学的处方是把窗口拉长到超过弛豫时长，这在课时有限的课堂里不可执行，"
              "且按工程学，推迟判定等于降低采样率，只会加重混叠（工程判物理）。"),
    "sources": [
        ("物理学 · 玻璃转变、德博拉数与物理老化",
         "Debenedetti &amp; Stillinger, Supercooled Liquids and the Glass Transition "
         "(<i>Nature</i> 410, 2001)；另见 Reiner, The Deborah Number (<i>Physics Today</i> 17:1, 1964)；"
         "Struik, <i>Physical Aging in Amorphous Polymers and Other Materials</i> (Elsevier 1978)",
         "https://doi.org/10.1038/35065704",
         "主张玻璃转变不是相变，而是弛豫时长超过了实验时长、系统被困在能量地形的一个盆地里；"
         "它并没有停止，只是慢到读不出来。这一支自曝：被判为冻结的材料，其性质随**等待时间**持续演化，"
         "蠕变曲线形状不变只沿时间轴平移——它用这条预测保质期，从没有人拿它当作「正在变与不在变可否当下区分」的证据。"),
        ("心理学 · 提取诱发遗忘",
         "Anderson, Bjork &amp; Bjork, Remembering Can Cause Forgetting "
         "(<i>J. Exp. Psychol.: LMC</i> 20:5, 1994)；另见 Anderson &amp; McCulloch, "
         "Integration as a General Boundary Condition (<i>JEP:LMC</i> 25:3, 1999)",
         "https://doi.org/10.1037/0278-7393.20.5.1063",
         "主张练习一部分内容会**主动削弱**同类中未被练到的那些，遗忘是提取这个动作自己造成的抑制。"
         "这一支自曝一处边界条件：当类别内成员被整合成相互关联的结构时，该效应消失甚至反转——"
         "它用这条划定适用范围，没有用来问一次判定本身在改变什么。"),
        ("工程学 · 可观测性、采样定理与抗混叠",
         "Kalman, Mathematical Description of Linear Dynamical Systems "
         "(<i>SIAM J. Control</i> 1:2, 1963)；另见 Shannon, Communication in the Presence of Noise "
         "(<i>Proc. IRE</i> 37:1, 1949)",
         "https://doi.org/10.1137/0301010",
         "主张不可观测的状态无论多要紧都进不了反馈回路，工程实践对这一块只做一件事：证明它稳定，然后不管。"
         "这一支自曝采样定理的另一半：采样过疏得到的不是「没有信号」而是**混叠**——"
         "一个虚假的、比真实变化慢得多的低频信号；对策不是提高采样率，是先滤掉快成分、宁可承认「这部分我不测」。"),
    ],
}, {
    "slug": "open-and-nobody-came",
    "src": Path("/home/claude/三·开着的时候没人来.md"),
    "title": "开着的时候没人来",
    "sub": "论课堂的内容时序与感受窗口时序不对齐，及为什么窗口关上不产生任何信号",
    "cross": "细胞学 × 工程学 × 艺术学",
    "no": "之六十八",
    "deck": ("课堂按内容的逻辑关系排序：先讲这个，因为后面那个要用它。这条排法从未被认真质疑，因为它看起来只是常识。"
             "细胞学主张一次诱导成不成不取决于信号强度、取决于靶细胞当时在不在感受态，"
             "工程学主张装配成不成不取决于每个零件多精确、取决于公差链怎么分配，"
             "艺术学主张作品成为什么样子不取决于意图、取决于材料在制作序列里的抵抗。"
             "三家争的是改变由什么驱动，而共同假定了一条没说出口的话："
             "**「准备好了没有」是可以先于动作被读出的属性**——课堂对它的信奉最彻底，"
             "前测、分层、先修要求、学情分析整套装置都在做这一件事。"
             "推翻它的材料来自细胞学自己——**序贯诱导**：靶组织的感受期窗口本身由更早一轮的信号打开，"
             "**准备度不是靶方的属性，是上一轮的产物**；而它有时限，窗外不是打折是归零。"
             "由此命名**空窗**：由上一轮教学打开、而在其开启期间没有任何相应内容到达的感受期。"
             "四类窗口的时长差两个数量级（秒到周），签名各不相同，其中最难辨认的一类"
             "**表现为追问减少而不是增加**。承重判断是：学习之所以少，"
             "不是内容顺序错了、不是学生基础差、也不是教法不对，而是教学序列按内容逻辑排、"
             "窗口按上一轮的产物开合，两套时序互不迁就，而课堂只记录前一套；"
             "**窗口未开而内容到达会产生信号，窗口已开而内容未到达不产生任何信号**——"
             "课堂的全部纠错能力只对前一格有效。"),
    "clash": ("第一家主张一次诱导成不成只由靶方当时在不在感受态决定，窗外同样的信号完全无效；"
              "第二家主张装配失败不是零件不合格、是公差链没有被分配，而现实解是**事后配对**；"
              "第三家主张形式由材料在制作序列中的抵抗决定，熟练者的做法是随时改路线以就窗口。"
              "三条不能同时为真：**工程学「先做、实测、再分组配对」的日课，"
              "正是细胞学判为不可能的那件事——窗口关上之后没有任何办法把当时该来的信号补配给它**（细胞判工程）；"
              "而细胞学那套被严格编排的时序，恰恰是艺术学判为坏工艺的东西"
              "（预设的工序表在材料面前就是不会做活，艺术判细胞）；"
              "至于细胞学的处方——让信号时序与窗口时序精确对齐——课堂做不到，"
              "因为课程表必须事先写出来，而窗口在上一轮结束前不可知（工程与艺术共同判细胞）。"),
    "sources": [
        ("细胞学 · 感受态窗口与序贯诱导",
         "Gurdon &amp; Bourillot, Morphogen Gradient Interpretation (<i>Nature</i> 413, 2001)；"
         "另见 Gurdon, Embryonic Induction — Molecular Prospects (<i>Development</i> 99:3, 1987)；"
         "Waddington, <i>Organisers and Genes</i> (Cambridge 1940)",
         "https://doi.org/10.1038/35101500",
         "主张一次诱导是否成功取决于靶组织当时处不处在感受态，窗外同样浓度同样时长的信号完全无效——"
         "不是打折，是归零。这一支自曝：感受期窗口本身由更早一轮的信号打开，"
         "它用这条解释发育时序为何被如此精确地编排，从没有人拿它当作「准备度不是可先于动作读出的属性」的证据。"),
        ("工程学 · 公差链与选择性装配",
         "Chen, Optimising Tolerance Allocation for Mechanical Components Correlated by Selective "
         "Assembly (<i>Int. J. Adv. Manuf. Technol.</i> 12, 1996)；另见 Whitney, "
         "<i>Mechanical Assemblies</i> (Oxford University Press, 2004)",
         "https://doi.org/10.1007/BF01179810",
         "主张装配失败不是零件不合格、是公差沿装配序列的累积没有被分配；"
         "提高单件精度成本按指数上升而累积公差只按平方根下降，故正解从来不是「都做准一点」。"
         "这一支自曝：现实对策是**选择性装配**——先做、实测、再分组配对，用事后配对吸收累积误差。"),
        ("艺术学 · 材料的抵抗与工艺时间窗",
         "Ingold, <i>Making: Anthropology, Archaeology, Art and Architecture</i> (Routledge, 2013)；"
         "另见 Rhodes, <i>Clay and Glazes for the Potter</i> (1957)；Mayer, "
         "<i>The Artist's Handbook of Materials and Techniques</i> (5th ed., Viking 1991)",
         "https://www.routledge.com/9780415567237",
         "主张决定一件作品成为什么样子的是材料与工具在制作序列中的抵抗，不是作者的意图；"
         "意图只有通过抵抗才成为形式。工坊里的时间窗有名字、有判据——陶土的皮革硬阶段以小时计，"
         "油画的可覆时间以天计。这一支自曝：熟练者不是更能预测窗口，而是**随时改路线以就窗口**。"),
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
