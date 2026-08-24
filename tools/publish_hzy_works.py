#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把胡志英学员专栏的全部 96 件作品接进 lang.sdeuniverses.com。

不搬文件、不复制正文——每一件都链回主站 /students/hu-zhiying/…，
本站只做三件事：分组、写导语、写一篇总结文。

产物（幂等，重跑即重排）：
  public/sites/lang/works/index.html     作品全集 · 八组 96 件，每件带一句摘要
  public/sites/lang/survey/index.html    总结文《九十六件作品，问的是同一件事》

数据源：public/students/publications.json 的 hu-zhiying 条目（唯一真相）
"""
import json, os, re, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lang_theme import CSS, FILTER_JS, PREFIX_FIX, esc, nav, page

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "public", "students", "publications.json")
OUT = os.path.join(ROOT, "public", "sites", "lang")

# ── 八组：slug, 名, 序, 强调色, 导语, 收录的作品号 ──────────────────
GROUPS = [
    ("lang", "语言这一条线", "壹", "#2B4C7E",
     "十二篇，本站首页那一栏就是从这里来的。五篇追语感——「顺」不是一种感觉，是一批还没有被删掉的判断；"
     "四篇追语法的一生——证据先到、取得改判权、把差异交给新载体、最后退役；三篇追教学动作的代价。"
     "这一组的写法与别处不同：每篇都写死了一条可裁决预测，并用公开语料真跑过一遍，跑输了就当场改判。",
     [74, 73, 72, 71, 70, 67, 66, 65, 64, 3, 15, 7]),

    ("books", "账册 · 四部专著", "贰", "#A63A2B",
     "四部，每部九章、二十万字上下。它们不是论文的加长版，是把一个判断放进九个互不重复的领域反复问，"
     "看它在哪一处开始承受不住。《语言的智慧》问的是一句话关上之后还剩什么；"
     "《一花一世界》问一个局部凭什么算一个世界；《知行合一》问交出去的东西还认不认得出；"
     "《记到谁的账上》问一次答对该记在谁名下。",
     [76, 75, 69, 68]),

    ("edu", "教育与评价", "叁", "#B0603A",
     "九篇。这一组最狠的一句写在《论教育的不可为》里：凡担保成功的，那件事就已经不再是教育。"
     "其余几篇从不同侧面逼同一件事——评价怎样把「我愿」磨平（《选择的热寂》），"
     "实时反馈怎样在提高成绩的同时拿走建造权（《核替》），"
     "以及守护论撤退到「我知道你有一个真实的自己」之后，为什么还得再撤一层（《悬而未决的守护》）。",
     [58, 57, 42, 54, 51, 22, 2, 21, 20]),

    ("neuro", "神经发展与身体", "肆", "#3F7A63",
     "十篇。ADHD 与自闭症在这里不被当成两种故障，而被当成同一份地基缺失上长出来的两种住法"
     "（《异时性栖居》）；回避不是策略，是跨认知风格交流时必须实时支付的换算开销累积到阈值后的结算"
     "（《认知宪法与通算危机》）。另有三篇转向身体：量化健康怎样让身体感知不再被调用，"
     "以及撤掉外部代偿之后，生理时序不是显露出来的，是被重新结算出来的。",
     [62, 60, 59, 50, 48, 46, 45, 52, 47, 10]),

    ("institution", "制度病理与知识生产", "伍", "#8C3F52",
     "二十一篇，全集里最厚的一组，也是他被引用最多的那条线。它们讲的是同一件反直觉的事："
     "一套制度往往不是在失效时崩塌，而是在最忠实地执行自身规则时走向内源性崩溃"
     "（《制度性自体免疫》）；一个范式靠主动放弃经验承诺换取内核的即时免疫，"
     "每退一次都在永久让出边疆（《边界收缩即边疆永失》）；"
     "而在资源最充裕、压力最小的顶级机构里，探究照样退化（《探究的会计化退化》）。",
     [1, 4, 5, 6, 8, 11, 12, 13, 14, 16, 17, 18, 30, 34, 35, 36, 37, 38, 41, 43, 44]),

    ("ontology", "认知、因果与存在", "陆", "#5B4B6B",
     "十六篇，全集里最靠上游的一组。它们撤掉的都是些几乎从不被说出口的先验："
     "「先有积木、后有搭法」（《碰撞逼出》）、「边界总是某个施压者对某个受迫者的作用」（《事物的压差地层》）、"
     "「耗散只是生成的倒放」（《蚀先于生》）、「客观性是一种静态状态」（《因果的维持》）。"
     "《刀与伤口同源》则把刀口转向自己：追问者手里那套靠边界与命名才能运作的工具，"
     "去追溯先于一切分化的源头时，悖论是他自己制造的。",
     [63, 61, 9, 39, 40, 27, 28, 29, 31, 32, 33, 25, 26, 23, 24, 19]),

    ("gss", "全球系统科学", "柒", "#4A5B8C",
     "四篇一组，独立成栏，因为它们咬的是同一台机器。一份携带结构性不确定性的认知，"
     "经由变量、模型与审稿三道技术上完全正当的工序，在制度层面丧失引发行动的能力——"
     "无主体、无阴谋、无恶意（《消毒》）。另外三篇分别处理命名怎样把行动驱力转成拖延的理由、"
     "「看见」怎样把现实重塑成能承接特定干预的形状、以及界面越复杂解释力越不长。",
     [56, 55, 53, 49]),

    ("twin", "并蒂文 · 一题两写", "捌", "#6E7A4B",
     "十组二十篇，本站的一种特有体例：同一个判断写两遍。"
     "**诠释文**只讲事情本身，一个术语不用，读起来像散文；**实用文**给出可操作的步骤、判据与回滚方案。"
     "两篇同根同源，谁也不是谁的科普版——先读哪一篇都行，读完另一篇会发现它们在互相追问。",
     []),
]

TWIN_ORDER = ["traumatic-crystallization", "the-constitutable", "presencing",
              "identificatory-closure", "forced-rupture", "erosion-precedes-genesis",
              "conceptual-autophagy", "collisional-extrusion", "causal-upkeep",
              "adjudicative-atrophy"]

TWIN_LEAD = {
    "traumatic-crystallization": "有些理解不是学会的，是再也回不去以后长出来的——不可逆性从哪里来，以及它凭什么是人不可被替代的根据。",
    "the-constitutable": "创新不是多知道一点，是提问的人换了一个位置；于是评审要保护的不是潜能，是问题发生的条件。",
    "presencing": "积木之外，事物还会自己长出来——给出、持存、回嵌，一套让新结构真正落地的设计法。",
    "identificatory-closure": "一个名字为什么会逼着现实长成它的样子；解法是把标签降格成可撤销的工作假设。",
    "forced-rupture": "当两个都说得通的例子把你信过的规则撕开——用成对案例审查规则，而不是操控信念。",
    "erosion-precedes-genesis": "旧店没有突然消失，是另一套生活先搬了进来；于是有了在旧系统倒下前找到第一处替换的互蚀地图。",
    "conceptual-autophagy": "拿尺子去量尺子的出生会发生什么——理论审查得先照见自己的手。",
    "collisional-extrusion": "很多新东西不是设计出来的，是两股力量挤出来的；碰撞可以画成一张可试验、可回滚的地图。",
    "causal-upkeep": "客观性更像一团火，不像一块石头——因果铁律需要定期维护，像做一次消防检查。",
    "adjudicative-atrophy": "考满分以后为什么越来越看不见新答案；对策是设一个第二裁断共同体，别让成功把判断力变成量表。",
}

FOOTER = """<footer><div class="wrap">
  <p>作品全集 —— 胡志英在 <a href="https://sdeuniverses.com/students/hu-zhiying/">SDE Universes 学员专栏</a> 已发表的全部作品，本站按主题重新编次并写导语。每一件都链回主站原文，正文不在此处复制。</p>
  <p>语言发生学 · <a href="https://sdeuniverses.com/">SDE Universes</a> 的语言分站 —— 德麦国际 · Demai International Press</p>
</div></footer>"""


def load():
    d = json.load(open(DATA, encoding="utf-8"))
    hz = [x for x in d["students"] if x["slug"] == "hu-zhiying"][0]
    return hz


def clip(s, n=96):
    s = re.sub(r"\s+", "", s or "")
    if len(s) <= n:
        return s
    cut = s[:n]
    for k in range(len(cut) - 1, n - 26, -1):
        if cut[k] in "。！？；":
            return cut[:k + 1]
    return cut.rstrip("，、") + "……"


def item_html(a, lead=""):
    key = (a["title"] + " " + a.get("summary", "") + " " + a["kind"]).replace('"', "")
    return ('<div class="item" data-k="%s"><div class="it-hd">'
            '<span class="r-n" title="学员专栏编号">%02d</span>'
            '<a class="it-t" href="%s">%s</a>'
            '<span class="it-m">%s</span></div>'
            '<p class="it-d">%s</p>'
            '<div class="it-l"><a href="%s">读原文</a></div></div>\n'
            % (esc(key), a["number"], a["url"], esc(a["title"]),
               esc(a["kind"]), esc(lead or clip(a.get("summary", ""))), a["url"]))


def twin_html(slug, pair, lead):
    it, pr = pair["interpretation"], pair["practice"]
    key = (it["title"] + " " + pr["title"] + " " + lead).replace('"', "")
    return ('<div class="item" data-k="%s"><div class="it-hd">'
            '<span class="r-n" title="学员专栏编号">%02d</span>'
            '<a class="it-t" href="%s">%s</a>'
            '<span class="it-m">一题两写</span></div>'
            '<p class="it-d">%s</p>'
            '<div class="it-l"><a href="%s">诠释文 · %s</a>'
            '<a href="%s">实用文 · %s</a></div></div>\n'
            % (esc(key), it["number"], it["url"], esc(it["title"]), esc(lead),
               it["url"], esc(clip(it["title"], 18)),
               pr["url"], esc(clip(pr["title"], 18))))


def build():
    hz = load()
    items = {x["number"]: x for x in hz["items"]}
    twins = defaultdict(dict)
    for x in hz["items"]:
        m = re.match(r"/students/hu-zhiying/([^/]+)/(interpretation|practice)/", x["url"])
        if m:
            twins[m.group(1)][m.group(2)] = x

    # 全覆盖自检：一件都不许漏，一件都不许重
    seen = []
    for g in GROUPS:
        seen += g[5]
    for s in TWIN_ORDER:
        seen += [twins[s]["interpretation"]["number"], twins[s]["practice"]["number"]]
    assert len(seen) == len(set(seen)), "有作品被分进两组：%s" % [n for n in set(seen) if seen.count(n) > 1]
    missing = sorted(set(items) - set(seen))
    assert not missing, "有作品没有被收进任何一组：%s" % missing
    assert len(seen) == len(items), "分组总数 %d ≠ 作品总数 %d" % (len(seen), len(items))

    # ── 作品全集 ───────────────────────────────────────────
    secs, jump = "", ""
    for slug, name, no, cc, lead, nums in GROUPS:
        if slug == "twin":
            body = "".join(twin_html(s, twins[s], TWIN_LEAD[s]) for s in TWIN_ORDER)
            n = len(TWIN_ORDER) * 2
            ct = "%d 组 · %d 篇" % (len(TWIN_ORDER), n)
        else:
            body = "".join(item_html(items[k]) for k in nums)
            n = len(nums)
            ct = "%d 篇" % n
        secs += ('<section id="%s" data-group="%s" style="--accent:%s">'
                 '<div class="col-h"><span class="no">%s</span><h2>%s</h2>'
                 '<span class="ct">%s</span></div>'
                 '<p class="col-d">%s</p>\n%s</section>\n'
                 % (slug, slug, cc, no, esc(name), ct,
                    lead.replace("**", ""), body))
        jump += '<a href="#%s" style="--cc:%s">%s <b>%d</b></a>' % (slug, cc, esc(name), n)

    total = len(items)
    dark = """<div class="dark">
%s
<div class="wrap"><div class="hero">
  <div class="eyebrow">作品全集 · COMPLETE WORKS</div>
  <h1>九十六件作品，<em>都在这里</em></h1>
  <p class="lede">胡志英（约翰）在 SDE Universes 学员专栏已发表的全部作品：<b>%d 件</b>，含四部专著、十二篇语言长论文、十组并蒂文，以及七十件跨到教育、神经发展、制度病理、认知与存在的研究。</p>
  <p class="lede">本站不复制正文。这一页做的是另一件事：<b>按主题重新编次、给每一组写一段导语、给每一件配一句可判断的摘要</b>，让人能先看清版图，再决定从哪一件进去。点标题即回主站读原文。</p>
  <div class="acts">
    <a class="primary" href="/survey/">先读总结文：这九十六件在问同一件事</a>
    <a href="https://sdeuniverses.com/students/hu-zhiying/">主站作者主页 ↗</a>
  </div>
</div></div>
</div>""" % (nav("works"), total)

    light = """<div class="light"><div class="wrap">
<div class="tools">
  <div class="filter"><label>全集筛选</label><input id="q" type="search" placeholder="输入任意词，例如：ADHD、评价、因果、语法" autocomplete="off" aria-label="筛选作品"><span class="n" id="n"></span></div>
  <p class="empty" id="empty" style="display:none">没有匹配的作品。换一个词试试。</p>
  <div class="chipy" style="margin-top:16px">%s</div>
</div>
%s
<div class="nearby">
  <a href="/survey/"><small>总结文</small><b>问的是同一件事</b>把九十六件读成一条线</a>
  <a href="/all/"><small>长论文</small><b>语言这一条线</b>十二篇的详目与摘要</a>
  <a href="/wechat/"><small>存档</small><b>约翰专栏</b>公众号五年 418 篇原文</a>
</div>
</div></div>""" % (jump, secs)

    os.makedirs(os.path.join(OUT, "works"), exist_ok=True)
    open(os.path.join(OUT, "works", "index.html"), "w", encoding="utf-8").write(
        page("作品全集 · 语言发生学",
             "胡志英在 SDE Universes 学员专栏已发表的全部 %d 件作品，按八组重新编次：语言、专著、教育与评价、神经发展与身体、制度病理与知识生产、认知因果与存在、全球系统科学、并蒂文。" % total,
             "https://lang.sdeuniverses.com/works/",
             dark + light, FOOTER, "#1F3A5F", FILTER_JS))

    # ── 总结文 ─────────────────────────────────────────────
    survey_dark = """<div class="dark">
%s
<div class="wrap"><div class="hero tight">
  <div class="crumb"><a href="/works/">作品全集</a> · 总结文</div>
  <h1>九十六件作品，<em>问的是同一件事</em></h1>
  <p class="lede">一份读法。把这些分散在语言学、教育学、精神医学、组织理论与存在论里的作品放到一起，会发现它们反复在同一处下刀——而那一处，在通行的说法里通常被算作好消息。</p>
</div></div>
</div>""" % nav("works")

    survey_light = """<div class="light"><div class="wrap">
<article class="essay">

<section id="s1">
<div class="col-h"><span class="no">一</span><h2>一句反直觉的判断</h2></div>
<p>把九十六件作品的结论摘出来排在一起，最先跳出来的是一句几乎处处成立的话：<b>一套东西往往不是在失效的时候崩塌，而是在它最成功、最合规、最精确的时候，开始吃掉自己赖以发生的条件。</b></p>
<p>这不是一个比喻，而是被反复具体化过的机制。学术范式靠主动放弃经验承诺来换取内核的即时免疫，每退一次都在永久让出边疆（[[1|边界收缩即边疆永失]]）；旨在保护脆弱主体的修复制度，会在忠实执行自身规则的过程中走向内源性崩溃（[[17|制度性自体免疫]]）；一个技艺体系在巅峰状态下，其活性被自身成功建构的评价结构悄悄驯化，进入一种以持续运动维持的精致僵死（[[21|活死态]]）；一个在封闭边界内持续成功的人，其独立裁断的身体知觉会被内化的尺子不可逆地替换掉（[[30|成功者的茧]]）。</p>
<p>这批研究之所以不落进「异化」「内卷」这类现成词，是因为每一篇都拒绝了一个更省事的解释：没有压迫者，没有阴谋，没有恶意，也没有能力下降。[[16|《探究的会计化退化》]]把这一点做成了判别条件——在资源最充裕、职位最稳定、竞争压力最小的顶级机构里，退化照样发生；于是「压力」这个解释被排除掉了。[[38|《熔蚀》]]更直白：每一个决定在个体层面都无可指摘，可日积月累的合规决定放进同一框架，组织的可能性被无声溶解。</p>
</section>

<section id="s2">
<div class="col-h"><span class="no">二</span><h2>代理物怎样篡位</h2></div>
<p>第二条线索追的是同一件事的通道：<b>认识的代理物——指标、名号、分数、模型——怎样从临时工具变成认识对象本身。</b></p>
<p>[[37|《代理僭政》]]给了这个过程一个名字：后续的认识活动不再指向那个最初需要被认识的东西，而指向代理物。[[20|《比较的假肢》]]把它压成一句更短的话——「我比」变成了「比我」。[[51|《核替》]]指出实时反馈拿走的不是动机而是建造权，并与心流理论的即时反馈条件正面冲突。[[52|《意会荒漠化》]]处理身体那一端：不是它说不出来，是它不再被调用。</p>
<p>这条线在语言这一栏里落到最具体的地方。[[3|《算法闭环与生物代价》]]问的是一个刺眼的现象：一批在 AI 评分里近乎满分的孩子，换一本新绘本就发音僵硬、怎么纠都改不过来——损害为什么恰恰在成绩被制造出来的同时发生。[[7|《庇护所即牢笼》]]则把语言石化从「个体学习失败」重判为刚性评价制度与理性学习者的共谋。</p>
</section>

<section id="s3">
<div class="col-h"><span class="no">三</span><h2>发生，不是特征</h2></div>
<p>前两条线要成立，得先有一个更上游的区分，而这个区分正是全集的地基：<b>特征不是事物本来就有的属性，而是认知压力下被逼出来的代偿产物。</b></p>
<p>[[44|《认知绝食悖论》]]写得最狠：特征以认知为食，使发生挨饿——它切断与完整叙事的联系、压缩发生史的时间厚度、依赖他者的差别回应站稳自身。[[24|《构成与可构成者》]]把创新的追问从产出端移回发生端；[[25|《碰撞逼出》]]拆掉「先有积木、后有搭法」这条几乎从未被当成先验对待的信念；[[23|《事物的压差地层》]]追问施压者自己的边界又从哪里来；[[33|《蚀先于生》]]反过来主张耗散比生成更原始，而不是生成的倒放。</p>
<p>把刀口转向自己的是[[32|《刀与伤口同源》]]：追问者手里那套靠边界、区分与命名才能运作的概念工具，本身是长过程的后期结晶；他用它去追溯先于一切分化的源头时，悖论不是撞上的，是亲手制造的。这一篇解释了这批作品为什么总在同一个位置发力——它们要处理的，恰好是工具够不着的那一段。</p>
</section>

<section id="s4">
<div class="col-h"><span class="no">四</span><h2>在教育与神经发展上，这意味着什么</h2></div>
<p>这套判断落到人身上时最不客气。[[58|《论教育的不可为》]]正面迎击卢曼与舍尔斯基的「教育的技术缺陷」：他们把问题定位在手段，认为原则上可随技术改善而缩小；本文把它定位在教育本身——<b>凡担保成功的，那件事就已经不再是教育</b>。[[57|《悬而未决的守护》]]接着指出，守护论从塑造论那里撤退了，却只撤到「我知道你有一个真实的自己」，还得再撤一层，撤到「我不知道你会成为什么」。</p>
<p>神经发展这一组则把「故障」这个前提整个掀掉。[[48|《异时性栖居》]]主张 ADHD 与 ASD 不是两种病，是同一个缺口上长出来的两种住法；[[45|《生存，而非故障》]]指出被当作故障来治理的那些行为，可能正是一套供给失败之后仍在运转的生存方案；[[46|《认知宪法与通算危机》]]把社交回避从策略选择改判为换算开销累积到阈值后的结算。[[60|《制度的神经化》]]更进一步：缺陷说、神经多样性叙事、代偿理论与差别易感性在批判之路上停在同一个地方——都把个体与环境当作两个可分离的实体，再在二者之间分配因果；本文撤销的是可分离性本身。</p>
</section>

<section id="s5">
<div class="col-h"><span class="no">五</span><h2>语言那一栏为什么单列</h2></div>
<p>语言这十二篇在全集里体例特殊：<b>每篇都写死了一条可裁决预测，并用公开语料真跑过一遍</b>。[[67|《语法境阈体》]]用 500 句公开评分数据，总体翻面率 28.0% 过了事前门槛；[[64|《语法载差体》]]在七个日耳曼语树库上跑出 Spearman ρ=0.000、p=1.000，简单静态假说没能成立，作者把这条结果原样写进了正文；[[65|《语法退役体》]]查 GUM 里的 shall，结果与自己的先验假说方向相反。</p>
<p>这一点值得单独说，因为它是这批作品与「读起来很有道理的思想文章」之间的分界线：<b>一个判断只有在它写明了什么结果会推翻自己、并且真的去跑了一遍之后，才算立住。</b>跑输了不改口径、照实写进去，这条纪律在全集里是通例，不是例外。</p>
</section>

<section id="s6">
<div class="col-h"><span class="no">六</span><h2>怎么读这九十六件</h2></div>
<p>如果只读三件：[[44|《认知绝食悖论》]]给你地基（特征与发生的区分），<a href="/students/hu-zhiying/boundary-contraction/">《边界收缩即边疆永失》</a>给你机制的原型，[[58|《论教育的不可为》]]给你它最不留情的一次应用。</p>
<p>如果你是家长或老师，从<a href="/wechat/enlighten/">约翰专栏</a>那边进来更顺——同一个人，同一批问题，但那边是讲给每天要用的人听的。两边对着读，能看出一个判断是怎么从课堂里长出来的。</p>
<p>如果你只想看一个判断怎样被写成可操作的东西，去读<a href="/works/#twin">并蒂文</a>：同一件事写两遍，诠释文一个术语不用，实用文给步骤、判据与回滚方案。</p>
<div class="nearby">
  <a href="/works/"><small>回到</small><b>作品全集</b>八组 96 件，逐件带摘要</a>
  <a href="/all/"><small>细读</small><b>语言这一条线</b>十二篇长论文的详目</a>
  <a href="https://sdeuniverses.com/students/hu-zhiying/"><small>主站</small><b>作者主页 ↗</b>全部作品的原始发表位置</a>
</div>
</section>

</article>
</div></div>"""

    # 正文里的 [[编号|显示名]] 一律按数据解析成真链接；解析不了就报错，绝不让死链上站
    def resolve(m):
        n = int(m.group(1))
        assert n in items, "总结文引了不存在的作品号 %d" % n
        return '<a href="%s" title="%s">%s</a>' % (items[n]["url"],
                                                  esc(items[n]["title"]), m.group(2))
    survey_light = re.sub(r"\[\[(\d+)\|([^\]]+)\]\]", resolve, survey_light)
    assert "[[" not in survey_light, "总结文里还有没解析的占位符"

    os.makedirs(os.path.join(OUT, "survey"), exist_ok=True)
    open(os.path.join(OUT, "survey", "index.html"), "w", encoding="utf-8").write(
        page("九十六件作品，问的是同一件事 · 语言发生学",
             "胡志英全部作品的一份总读法：一套东西往往不是在失效时崩塌，而是在最成功、最合规、最精确的时候开始吃掉自己赖以发生的条件。",
             "https://lang.sdeuniverses.com/survey/",
             survey_dark + survey_light, FOOTER, "#1F3A5F"))

    # ── 同步 lang 首页「栏六 · 作品全集」 ─────────────────────
    home = os.path.join(OUT, "index.html")
    if os.path.exists(home):
        h = open(home, encoding="utf-8").read()
        S, E = "<!-- works-rows:start -->", "<!-- works-rows:end -->"
        if S in h and E in h:
            rows = ""
            for k, (slug, name, no, cc, lead, nums) in enumerate(GROUPS, 1):
                n = len(TWIN_ORDER) * 2 if slug == "twin" else len(nums)
                short = SHORT_HOME[slug]
                rows += ('  <a class="row" href="/works/#%s"><span class="r-n">%d</span>'
                         '<span class="r-t"><b class="r-h">%s</b>%s</span>'
                         '<span class="cnt"><b>%d</b> 件</span></a>\n'
                         % (slug, k, esc(name), esc(short), n))
            h = h[:h.index(S) + len(S)] + "\n" + rows + h[h.index(E):]
            open(home, "w", encoding="utf-8").write(h)
            print("  已同步 lang 首页「作品全集」那一栏")

    print("作品全集（%d 件 / 8 组）与总结文已生成于 %s" % (total, OUT))
    for slug, name, no, cc, lead, nums in GROUPS:
        n = len(TWIN_ORDER) * 2 if slug == "twin" else len(nums)
        print("  %-12s %-10s %2d" % (slug, name, n))


SHORT_HOME = {
    "lang": "语感五篇 · 语法四篇 · 教学三篇，每篇真跑过一条证伪条款",
    "books": "语言的智慧 · 一花一世界 · 知行合一 · 记到谁的账上",
    "edu": "凡担保成功的，那件事已经不再是教育",
    "neuro": "ADHD 与自闭症不是两种病，是同一个缺口上的两种住法",
    "institution": "制度不是在失效时崩塌，是在忠实执行时崩塌",
    "ontology": "先有积木后有搭法——这条先验被逐一撤掉",
    "gss": "不确定性怎样被三道正当工序加工成无害的残余",
    "twin": "同一个判断写两遍：诠释文不用术语，实用文给步骤",
}


if __name__ == "__main__":
    build()
