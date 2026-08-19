# -*- coding: utf-8 -*-
"""把《步骤留下，岔路删除》并入「学科通融」，之九十二。

三源为站内学员论文（认知教育 / 伦理人类学 / 法哲学），照之八先例，
来源盒标题写明"由哪三个领域的论文撞成"，链接站内可核对。
署名照本栏惯例 王德生 ＋ Claude。分数不写进页面。
"""
import html, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CF = ROOT / "public" / "confluence"
TPL = CF / "borrowed-clarity" / "index.html"
SRC = Path("/home/claude/run/conf_body.md")
SLUG = "branch-deleted"
PUBDATE = "2026年8月11日"
ORD = "之九十二"
FIELDS = "认知教育 × 伦理人类学 × 法哲学"
BYLINE = "王德生 ＋ Claude"

TITLE = "步骤留下，岔路删除"
SUB = ("论选择次数何以在全部现行读数上不可见，及删除的顺序为何由可结算性而非后果重要性决定"
       "——附一次在职业数据上的预注册检验")
DECK = ("现代组织正在极快地取消人在工作中的选择，而所有现行的记录方式都读不出这件事。原因不在监测不足，在删除的形态："
        "被取消的是岔路，不是步骤。岗位仍在，工序仍在，工作量甚至上升，唯一减少的是那些「本来可以走另一条」的位置。"
        "本文命名这个量为**带责分叉**，给出三条同时成立才算数的判据——路真的分开、行动者知道并被允许走、"
        "选错的后果落在他本人身上且不至于将他废掉——并以单位工时内的分叉次数与对系统给定值的**越建议率**作为读数。"
        "本文进一步论证一条反直觉的命题：**删除的顺序不由该不该删决定，而由可结算性决定**，"
        "而可结算性与后果重要性是两条正交的轴。文中在职业信息网络数据库（O*NET 29.1，n=879）上做了一次预注册检验"
        "（预注册文本哈希已公开）：自动化程度与可结算性相关 0.466，与后果重量在控制可结算性后完全无关；"
        "时间压力与决策自由度近乎正交（0.017），证实忙与选是两笔账；"
        "**自动化程度与决策频次无关（0.042），与决策自由度显著负相关（−0.199）**——这一对系数正是"
        "「步骤留下、岔路删除」的字面读数。第三条预言部分不成立，本文据此收回一条过强主张；一次纵向检验失败，"
        "失败原因写在正文里。最后指出：人的监督条款所要的接管能力只能由带责分叉生产，而自动化设计的标准实现方式"
        "恰好把它降到零；现行法规要求人能够不采纳系统输出，却既不要求记录否决率，也不分配否决的责任。")

ORIGIN = ("**本篇的三家源是站内学员论文**，分属认知教育、伦理人类学与法哲学——三家互不相识，"
          "却对「同一段看起来什么也没发生的工作时间」给出不能并存的处置。下面三条可直接点开核对。"
          "正文第二节交代三家各自说到了哪一步，第三节把三处对顶写死，第四节第五小节说明它们各自为什么"
          "到不了本文这一条，第九节再与十种最容易被混为一谈的说法逐条分界——**包括本文承认最可能把它吸收掉的那一个**。")

SOURCES = [
    ("认知教育 · 陈晓艳《接缝思维》",
     "不可通约处如何成为生产性的认知立足点",
     "https://sdeuniverses.com/students/chen-xiaoyan/seam-thinking/",
     "主张两个对不上的框架之间那道缝正是新维度生成的位置，「综合起来看」「辩证地看」是填缝剂，"
     "评价体系应为「卡住」留出不受核算侵犯的地方。**与本文的分离线**：它给出了第一条判据的雏形，"
     "却没有判据区分真正的不可通约与被装饰出来的不可通约，因而无法回应第二家的怀疑。"),
    ("伦理人类学 · 张琼《伦理空转项》",
     "中国伦理人类学田野采集的诊断",
     "https://sdeuniverses.com/students/zhang-qiong/ethical-idling/",
     "主张田野中被反复采集到的不是伦理的发生，而是可以流畅叙说、却不承载任何抉择后果的道德话语，"
     "而学术机器的采集偏好恰好与这种形态咬合。**与本文的分离线**：它把承载与否处理为话语的属性；"
     "而在工作现场，同一个动作可以在一个人身上承载、在另一个人身上空转，差别不在话语，在后果落在谁头上。"),
    ("法哲学 · 高鹏《使人成为主体的规则》",
     "论禁止性规则与期待型规则所安装的两种主体结构",
     "https://sdeuniverses.com/students/gao-peng/rules-that-make-subjects/",
     "主张划红线的规则安装的是间歇激活、可休眠的零件，无上限的期待安装的是全天候、关不掉的零件；"
     "规则先造出一种人，再用这种人去执行它自己。**与本文的分离线**：它的单位是规则类型与主体类型，"
     "而本文所述的三种手法都不是规则——阈值是参数，默认值是界面，例外申请化是流程，它们不禁止任何事。"),
]

SIBLING = ("本栏另有一篇与本篇形状相近而变量相反：《没有人要求的时候》测的是无任务、无奖惩时段里系统还动不动，"
           "其定义条件是**没有人在等它交出什么**；本篇的读数恰恰要求**后果落在本人身上**。两者在定义上互斥而正交——"
           "那一个问「没人要求时它还动不动」，本篇问「有人要求时他还能不能走另一条」，可同批测量且互不蕴含。")

BANNED = ("发生学", "本体论", "存在论", "显露态", "特征纠缠", "差异序列",
          "金点子", "二阶碰撞", "近邻划界", "候选判断", "改姓")


def strongify(s):
    s = html.escape(s, quote=False)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)


def md_to_html(md):
    out, para, toc, n = [], [], [], 0
    lines = md.splitlines()
    i = 0

    def flush():
        if para:
            out.append("<p>" + strongify(" ".join(para)) + "</p>")
            para.clear()

    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            flush(); i += 1; continue
        m = re.match(r"^(#{2,4})\s+(.*)$", line)
        if m:
            flush()
            lvl, txt = len(m.group(1)), m.group(2).strip()
            if lvl == 2:
                n += 1
                out.append(f'<h2 id="s{n}">{strongify(txt)}</h2>')
                toc.append((f"s{n}", txt))
            else:
                out.append(f"<h3>{strongify(txt)}</h3>")
            i += 1; continue
        if re.match(r"^- ", line):
            flush()
            items = []
            while i < len(lines) and re.match(r"^- ", lines[i]):
                items.append(lines[i][2:].strip()); i += 1
            out.append("<ul class=pl>" + "".join(f"<li>{strongify(x)}</li>" for x in items) + "</ul>"); continue
        para.append(line.strip()); i += 1
    flush()
    return "".join(out), toc


def build_page(body, toc, wan):
    t = TPL.read_text(encoding="utf-8")
    t = re.sub(r"<title>.*?</title>",
               f"<title>{TITLE}——{SUB[:52]} · 学科通融 | SDE Universes</title>", t, flags=re.S)
    t = re.sub(r'(<meta name="description" content=")[^"]*(")',
               lambda m: m.group(1) + html.escape(re.sub(r"\*\*", "", DECK)[:190], quote=True) + m.group(2), t)
    t = re.sub(r'(<link rel="canonical" href="https://sdeuniverses\.com/confluence/)[^"]*(")',
               lambda m: m.group(1) + SLUG + "/" + m.group(2), t)
    t = re.sub(r'<h1 class="art-title">.*?</h1>', f'<h1 class="art-title">{TITLE}</h1>', t, flags=re.S)
    t = re.sub(r'<(p|div) class="art-sub">.*?</\1>', f'<div class="art-sub">{SUB}</div>', t, flags=re.S)
    t = re.sub(r'<div class="art-meta">.*?</div>',
               f'<div class="art-meta">{BYLINE} · 约 {wan} 万字 · 网页长文 · 发表于{PUBDATE}</div>', t, flags=re.S)
    t = re.sub(r'<div class="art-series">.*?</div>',
               f'<div class="art-series">学 科 通 融 · {ORD} · {FIELDS}</div>', t, flags=re.S)
    t = re.sub(r'<div class="deck">.*?</div>', f'<div class="deck">{strongify(DECK)}</div>', t, flags=re.S)

    links = "".join(f'<a href="#{i}">{html.escape(x)}</a>' for i, x in toc)
    t = re.sub(r'<div class="toc">.*?</div>\s*(?=<h2|<p|<hr)',
               f'<div class="toc"><div class="tl">目 录</div>{links}</div>\n', t, flags=re.S)

    i = t.index("</div>", t.index(links)) + 6
    j = t.index('<div class="src">')
    t = (t[:i] + "\n" + body
         + f'\n<hr>\n<h2 id="sib">附：与本栏另一篇的关系</h2><p>{strongify(SIBLING)}</p>\n'
         + t[j:])

    ones = "".join(
        f'<a class="one" href="{u}"><div class="k">{html.escape(k)}</div>'
        f'<div class="t">{html.escape(ti)}</div><div class="g">{strongify(g)}</div></a>'
        for k, ti, u, g in SOURCES)
    t = re.sub(r'<div class="src">.*?</div>\s*(?=<div class="endbox">)',
               f'<div class="src"><div class="sl">这一篇由哪三个领域的论文撞成</div>'
               f'<p class="sd">{strongify(ORIGIN)}</p>{ones}</div>\n', t, flags=re.S)

    assert t.count("<html") == 1 and t.count("</html>") == 1
    hit = [w for w in BANNED if w in body]
    assert not hit, f"正文残留行话：{hit}"
    return t


def add_card(wan):
    f = CF / "base.html"
    t = f.read_text(encoding="utf-8")
    before = t.count('class="item"')
    assert SLUG not in t, "卡片已存在"
    trio = "".join(f'<div><b>{html.escape(k)}</b><a href="{u}">{html.escape(ti)}</a></div>'
                   for k, ti, u, _g in SOURCES)
    hk = re.sub(r"\*\*", "", DECK)
    card = (f'<div class="item" data-ch="c1"><div class="n">{ORD} · 三学科交叉：{FIELDS}（三家源为站内学员论文）</div>'
            f'<h2><a href="/confluence/{SLUG}/">{html.escape(TITLE)}</a></h2>'
            f'<p class="sub">{html.escape(SUB)}</p>'
            f'<p class="hk">{html.escape(hk)}</p>'
            f'<div class="trio">{trio}</div>'
            f'<p class="rdmore"><a href="/confluence/{SLUG}/">读全文 →</a></p>'
            f'<p class="meta">约 {wan} 万字 · 网页长文 · 作者 {BYLINE} · 发表于{PUBDATE}</p></div>\n')
    a = "</main>"
    assert t.count(a) == 1, t.count(a)
    t = t.replace(a, card + a, 1)
    assert t.count('class="item"') == before + 1
    f.write_text(t, encoding="utf-8")
    return before + 1


def update_loader(wan):
    f = CF / "index.html"
    t = f.read_text(encoding="utf-8")
    t = re.sub(r'<strong>最新发布 · 之[^<]*</strong>', f'<strong>最新发布 · {ORD}</strong>', t)
    t = re.sub(r'<a href="/confluence/borrowed-clarity/">《[^》]*》</a>',
               f'<a href="/confluence/{SLUG}/">《{TITLE}：{SUB[:40]}》</a>', t, count=1)
    t = t.replace("const href='/confluence/borrowed-clarity/';", f"const href='/confluence/{SLUG}/';")
    t = re.sub(r'<div class="item" data-ch="c1">.*?</div>\n`', "PLACEHOLDER`", t, flags=re.S)
    trio = "".join(f'<div><b>{html.escape(k)}</b><a href="{u}">{html.escape(ti)}</a></div>'
                   for k, ti, u, _g in SOURCES)
    hk = re.sub(r"\*\*", "", DECK)
    card = (f'<div class="item" data-ch="c1"><div class="n">{ORD} · 三学科交叉：{FIELDS}（三家源为站内学员论文）</div>'
            f'<h2><a href="/confluence/{SLUG}/">{html.escape(TITLE)}</a></h2>'
            f'<p class="sub">{html.escape(SUB)}</p>'
            f'<p class="hk">{html.escape(hk)}</p>'
            f'<div class="trio">{trio}</div>'
            f'<p class="rdmore"><a href="/confluence/{SLUG}/">读全文 →</a></p>'
            f'<p class="meta">约 {wan} 万字 · 网页长文 · 作者 {BYLINE} · 发表于{PUBDATE}</p></div>\n')
    t = t.replace("PLACEHOLDER`", card + "`")
    t = re.sub(r'最新论文：<a href="/confluence/[^"]*">《[^》]*》</a>',
               f'最新论文：<a href="/confluence/{SLUG}/">《{TITLE}》</a>', t)
    t = re.sub(r'(<meta name="description" content="学科通融：把分属不同学科、彼此冲突的理论体系放在一起碰撞。最新论文)《[^》]*》',
               lambda m: m.group(1) + f'《{TITLE}》', t)
    f.write_text(t, encoding="utf-8")


if __name__ == "__main__":
    md = SRC.read_text(encoding="utf-8")
    han = len(re.findall(r"[\u4e00-\u9fff]", md))
    wan = f"{han/10000:.1f}"
    body, toc = md_to_html(md)
    page = build_page(body, toc, wan)
    d = CF / SLUG
    d.mkdir(exist_ok=True)
    (d / "index.html").write_text(page, encoding="utf-8")
    n = add_card(wan)
    update_loader(wan)
    print(f"建成 /confluence/{SLUG}/ · {ORD} · {han} 汉字 · {wan} 万字 · 章 {len(toc)} · 栏目卡 {n} 张")
