#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把胡志英（约翰老师）公众号 418 篇文章上到 lang.sdeuniverses.com/wechat/。

产物（幂等，重跑即重排）：
  public/sites/lang/wechat/index.html          门厅：写作节律 + 九个频道
  public/sites/lang/wechat/all/index.html      全部正稿 · 词与年份双筛
  public/sites/lang/wechat/<slug>/index.html   九个频道页
  public/sites/lang/wechat/pdf/NNN.pdf         正文 PDF（另行落盘，本脚本不动）

数据源：tools/data/john_wechat.json
设计承 lang 分站体系：深色门面 + 浅色正文，宋体标题 + 等宽读数。
签名件＝「写作节律」——六十个月一列一格，真数据，不是装饰。
"""
import json, os, math, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lang_theme import CSS, FILTER_JS, PREFIX_FIX, esc, nav, page
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "tools", "data", "john_wechat.json")
OUT = os.path.join(ROOT, "public", "sites", "lang", "wechat")

# key, slug, 名, 序, 一句话, 强调色, 门厅代表作（两篇存档号）
CHANNELS = [
    ("theory", "genesis", "语言发生学", "壹",
     "语感、语法、语用、意义与输出。这一栏追的是同一个问题：一句话每条规则都对，母语者仍然会说「不是这么说的」——被违反的究竟是什么。",
     "#2B4C7E", ("077", "104")),
    ("qimeng", "enlighten", "英语启蒙", "贰",
     "家庭启蒙的路线与工序：三条线、看听线与听读线、听指、跟读与复述、敏感期、自然拼读。这一栏最厚，因为家长每天要用的就是它。",
     "#B0603A", ("300", "239")),
    ("vocab", "vocabulary", "词汇之路", "叁",
     "一个词怎样长出来，又怎样在需要的那一刻被取出来。词根词缀、形态、搭配、词卡、听力词汇转阅读词汇。",
     "#7A6A2E", ("084", "092")),
    ("materials", "materials", "素材与分级", "肆",
     "读什么、看什么、按什么次序排。RAZ、BrainPOP 与 ELL、原版动画、绘本、章节书与资源清单。",
     "#3F7A63", ("128", "160")),
    ("ai", "ai", "AI 与语言教育", "伍",
     "GPT、Claude 与各类工具进入学习现场之后：能力被放大了什么，又被换走了什么。这一栏从 2023 年那一波起，一路记到现在。",
     "#4A5B8C", ("332", "293")),
    ("school", "school", "课堂与制度", "陆",
     "翻转课堂、家校共学、考试与评价、高考与双减。每一个教学动作与制度安排都在取走一点什么，先把它算清楚。",
     "#8C3F52", ("132", "327")),
    ("lineage", "lineage", "思想谱系", "柒",
     "克拉申、维果茨基、索绪尔、洪堡、皮尔斯、斯韦恩、杜威、陶行知、林语堂。不是介绍生平，是把一个人读成一道还没有答完的问题。",
     "#5B4B6B", ("208", "127")),
    ("notes", "notes", "奶爸手记", "捌",
     "五个孩子、郊区的院子、种瓜与卖瓜、父亲与儿子。不谈方法的时候，他写这些。",
     "#6E7A4B", ("086", "161")),
    ("camp", "camp", "营地与公告", "玖",
     "训练营、开班、说明会、公开课与学员见证。现场记录，按时间存档。",
     "#A6772B", ("396", "390")),
]
CH_ORDER = [c[0] for c in CHANNELS]

MONTH_START = (2021, 9)
MONTH_END = (2026, 8)


def months():
    y, m = MONTH_START
    out = []
    while (y, m) <= MONTH_END:
        out.append("%04d-%02d" % (y, m))
        m += 1
        if m == 13:
            m, y = 1, y + 1
    return out


MONTHS = months()

RANDOM_JS = """<script>
(function(){
  var btn=document.getElementById("lucky");if(!btn)return;
  var pool=%s;
  btn.addEventListener("click",function(){
    var n=pool[Math.floor(Math.random()*pool.length)];
    location.href=(window.__wechatBase||"")+"/wechat/pdf/"+n+".pdf";
  });
})();
</script>"""

FOOTER = """<footer><div class="wrap">
  <p>约翰专栏 —— 胡志英（约翰老师）公众号「五宝爸约翰聊英语」原文存档，共 418 篇。原文一字未改，本站只做归类、排序与检索。</p>
  <p>语言发生学 · <a href="https://sdeuniverses.com/">SDE Universes</a> 的语言分站 —— 德麦国际 · Demai International Press</p>
</div></footer>"""


def rhythm(counts, total_counts=None, hot=None):
    """counts: {月: 数}。total_counts 给出同月其他栏的轮廓做底衬。"""
    peak = max([1] + list(counts.values()) + list((total_counts or {}).values()))
    def scale(v):
        return 0 if v <= 0 else max(4, int(round(100 * math.sqrt(v) / math.sqrt(peak))))
    bars = ""
    for i, mo in enumerate(MONTHS):
        v = counts.get(mo, 0)
        base = (total_counts or {}).get(mo, 0)
        d = "%dms" % (i * 11)
        inner = ""
        if total_counts is not None and base > v:
            inner += '<i style="height:%d%%;animation-delay:%s"></i>' % (scale(base) - scale(v), d)
        inner += '<u style="height:%d%%;animation-delay:%s"></u>' % (scale(v), d)
        cls = " hot" if hot and mo == hot else ""
        bars += '<span class="b%s" title="%s · %d 篇">%s</span>' % (cls, mo, v, inner)
    yrs = ""
    for y in range(MONTH_START[0], MONTH_END[0] + 1):
        n = sum(v for k, v in counts.items() if k[:4] == str(y))
        flex = sum(1 for m in MONTHS if m[:4] == str(y))
        yrs += ('<span style="flex:%d 1 0"><b>%s</b><em>%d 篇</em></span>'
                % (flex, y, n))
    return bars, yrs


def build():
    arts = json.load(open(DATA, encoding="utf-8"))
    arts.sort(key=lambda x: x["num"])
    canon = [a for a in arts if not a["alt"]]
    altmap = defaultdict(list)
    for a in arts:
        if a["alt"]:
            altmap[a["alt_of"]].append(a)
    for a in arts:
        a["y"] = a["date"][:4] if a["date"] and a["date"][0] == "2" else ""
        a["mo"] = a["date"][:7] if a["y"] else ""

    canon.sort(key=lambda a: (0 if a["y"] else 1, a["num"]))
    by_ch = {k: [a for a in canon if a["ch"] == k] for k in CH_ORDER}
    for key, slug, name, no, blurb, cc, picks in CHANNELS:
        got = {a["num"] for a in by_ch[key]}
        for p in picks:
            assert p in got, "代表作 %s 不在频道 %s 里" % (p, key)

    gmonth = Counter(a["mo"] for a in canon if a["mo"])
    hot = gmonth.most_common(1)[0][0]
    total_pages = sum(a["pages"] for a in arts)
    dated = sorted(a["date"] for a in arts if a["y"])
    span = "%s–%s" % (dated[0][:4], dated[-1][:4])
    n_dated = sum(1 for a in arts if a["y"])

    os.makedirs(OUT, exist_ok=True)

    def item_html(a):
        meta = []
        if a["y"]:
            meta.append(a["date"])
        meta.append("%d 页" % a["pages"])
        key = (a["title"] + " " + a["sum"] + " " + (a["date"] or "")).replace('"', "")
        extra = "".join('<a href="/wechat/pdf/%s.pdf">同题另稿 %s</a>' % (b["num"], b["num"])
                        for b in altmap.get(a["num"], []))
        return ('<div class="item" data-k="%s" data-y="%s"><div class="it-hd">'
                '<span class="r-n" title="存档号">%s</span>'
                '<a class="it-t" href="/wechat/pdf/%s.pdf">%s</a>'
                '<span class="it-m">%s</span></div>'
                '<p class="it-d">%s</p>'
                '<div class="it-l"><a href="/wechat/pdf/%s.pdf">读原文 PDF</a>%s</div></div>\n'
                % (esc(key), esc(a["y"]), a["num"], a["num"], esc(a["title"]),
                   " · ".join(meta), esc(a["sum"]), a["num"], extra))

    def items_by_year(lst):
        out, cur = "", None
        for a in lst:
            y = a["y"] or "未标日期"
            if y != cur:
                if cur is not None:
                    out += "</div>\n"
                cnt = sum(1 for x in lst if (x["y"] or "未标日期") == y)
                out += ('<div data-group="%s"><div class="yr"><b>%s</b><i></i>'
                        '<span>%d 篇</span></div>\n' % (esc(y), esc(y), cnt))
                cur = y
            out += item_html(a)
        if cur is not None:
            out += "</div>\n"
        return out

    # ── 门厅 ──────────────────────────────────────────
    bars, yrs = rhythm(gmonth, hot=hot)
    cards = ""
    for key, slug, name, no, blurb, cc, picks in CHANNELS:
        lst = by_ch[key]
        pg = sum(a["pages"] for a in lst)
        yc = Counter(a["y"] for a in lst if a["y"])
        top = max(yc.values()) if yc else 0
        spark = ""
        for y in range(2021, 2027):
            v = yc.get(str(y), 0)
            h = max(3, int(100 * math.sqrt(v) / math.sqrt(top))) if (top and v) else 3
            spark += ('<i class="%s" style="height:%d%%" title="%s 年 %d 篇"></i>'
                      % ("pk" if top and v == top else "", h, y, v))
        sx = "".join('<i>%s</i>' % str(y)[2:] for y in range(2021, 2027))
        pk = "".join('<em>%s</em>' % esc(next(a["title"] for a in lst if a["num"] == p))
                     for p in picks)
        cards += ('<a class="ch" href="/wechat/%s/" style="--cc:%s">'
                  '<div class="rule"></div><div class="in">'
                  '<div class="n">%s</div><h3>%s</h3><p>%s</p>'
                  '<div class="foot"><div class="spark">%s</div><div class="spark-x">%s</div>'
                  '<div class="picks">%s</div>'
                  '<div class="ct"><span><b>%d</b> 篇</span><span>%d 页</span></div>'
                  '<div class="go">进入这一栏 →</div></div>'
                  '</div></a>\n'
                  % (slug, cc, no, esc(name), esc(blurb), spark, sx, pk, len(lst), pg))

    hub = """<div class="dark">
%s
<div class="wrap"><div class="hero">
  <div class="eyebrow">约翰专栏 · WECHAT ARCHIVE</div>
  <h1>五年，四百一十八篇，<em>一次搬完</em></h1>
  <p class="lede">胡志英（约翰老师）公众号「五宝爸约翰聊英语」的全部原文存档。从 2021 年秋天那一篇写起，到今天为止 <b>418 篇、%s 页</b>。原文一字未改，本站做的只有三件事：<b>归类、按时间排序、可检索</b>。</p>
  <p class="lede">它和本站那十二篇长论文是同一个人写的两种东西。长论文要把一个判断立到能被推翻的程度；这里是他每天面对家长时，把同一批问题讲给用得上的人听。两边对着读，能看出一个判断是怎么从课堂里长出来的。</p>

  <div class="rhythm">
    <div class="cap">写　作　节　律<span>一列一个月 · 六十个月 · 高低即当月篇数</span></div>
    <div class="bars">%s</div>
    <div class="axis">%s</div>
    <p class="rnote">写作不是均匀滴下来的。头两年是零星的现场记录；<b>2023 年那一波几乎全在 AI 上</b>，正是 GPT 进课堂的那半年；<b>2025 年转向人物与谱系</b>；<b>2026 年最密</b>，一个月最多写到 %d 篇，理论文章几乎都长在这一段。另有 %d 篇正文里读不出发表日期，未计入本图。</p>
  </div>

  <div class="band">
    <div><b>418</b><span>篇 · 原文存档</span></div>
    <div><b>9</b><span>个频道</span></div>
    <div><b>%s</b><span>页</span></div>
    <div><b>%s</b><span>写作跨度</span></div>
  </div>

  <div class="acts">
    <a class="primary" href="/wechat/all/">一页翻完 %d 篇</a>
    <button id="lucky" type="button">随手抽一篇读</button>
    <a href="/all/">看十二篇长论文</a>
  </div>
</div></div>
</div>

<div class="light"><div class="wrap">
<section>
  <div class="col-h"><span class="no">频　道</span><h2>九个入口</h2><span class="ct">同一篇只进一栏</span></div>
  <p class="col-d">分栏不按体裁，按它要回答的问题：讲道理的进「语言发生学」，讲怎么做的进「英语启蒙」，讲用什么的进「素材与分级」。每一栏下面那排小柱是它自己的六年分布——有的栏一直在写，有的栏只属于某一年。</p>
  <div class="chs">
%s  </div>
</section>

<div class="note">
  <h3>关于这批存档</h3>
  <p><b>同题另稿。</b>公众号常有「原创版」与「非原创版」两稿，或同一篇改标题重发。这类共 <b>30</b> 篇，已配对认出：列表里只出现正稿一条，另一稿挂在它下面的「同题另稿」链接上，一篇不删。</p>
  <p><b>日期。</b>%d 篇能从正文里读出确切发表日期，直接显示；其余按存档号排在应有的位置，归入「未标日期」。<b>存档号越小越新</b>——001 是最近的一篇，418 是最早的一篇。</p>
  <p><b>怎么读。</b>点标题直接打开 PDF。想找某一篇，去 <a href="/wechat/all/">全部篇目</a>，输入任意词即时筛选，也可以只看某一年。</p>
</div>

<section>
  <div class="col-h"><span class="no">另　见</span><h2>同一个人的另一面</h2></div>
  <p class="col-d">公众号写给家长，长论文写给同行。后者要过敌意拓宽、可裁决预测与独立盲评三道关。</p>
  <div class="nearby">
    <a href="/all/"><small>长论文</small><b>十二篇新判断</b>语感、语法、语言教学与习得，创新智商 135–143</a>
    <a href="/#books"><small>账册</small><b>四部专著</b>语言的智慧 · 一花一世界 · 知行合一 · 记到谁的账上</a>
    <a href="/chatjohn/"><small>对话</small><b>ChatJohn</b>把一句「说不上来就是不对」交给它往下追</a>
  </div>
</section>
</div></div>""" % (nav("wechat"), "{:,}".format(total_pages), bars, yrs, gmonth[hot],
                   len(arts) - n_dated, "{:,}".format(total_pages), span,
                   len(canon), cards, n_dated)

    pool = json.dumps([a["num"] for a in canon])
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(
        page("约翰专栏 · 语言发生学",
             "胡志英（约翰老师）公众号原文存档 418 篇，分九个频道：语言发生学、英语启蒙、词汇之路、素材与分级、AI 与语言教育、课堂与制度、思想谱系、奶爸手记、营地与公告。",
             "https://lang.sdeuniverses.com/wechat/", hub, FOOTER, "#1F3A5F", RANDOM_JS % pool))

    # ── 频道切换条 ────────────────────────────────────
    def chipbar(cur):
        s = '<div class="chips"><div class="wrap">'
        s += '<a href="/wechat/">全部频道</a>'
        for key, slug, name, no, blurb, cc, picks in CHANNELS:
            a = ' aria-current="page"' if key == cur else ""
            s += '<a href="/wechat/%s/"%s>%s<b>%d</b></a>' % (slug, a, esc(name), len(by_ch[key]))
        s += '<a href="/wechat/all/">全部篇目<b>%d</b></a>' % len(canon)
        return s + "</div></div>"

    HINTS = {
        "theory": "语感、语用、句子",
        "qimeng": "看听线、复述、听指",
        "vocab": "词根、词卡、词汇量",
        "materials": "RAZ、动画、BrainPOP",
        "ai": "GPT、Claude、词根",
        "school": "高考、翻转、评价",
        "lineage": "克拉申、林语堂、洪堡",
        "notes": "父亲、院子、种瓜",
        "camp": "训练营、见证、开班",
    }

    for i, (key, slug, name, no, blurb, cc, picks) in enumerate(CHANNELS):
        lst = by_ch[key]
        pg = sum(a["pages"] for a in lst)
        cmonth = Counter(a["mo"] for a in lst if a["mo"])
        cbars, cyrs = rhythm(cmonth, total_counts=gmonth)
        yc = Counter(a["y"] for a in lst if a["y"])
        peak_y, peak_n = (yc.most_common(1)[0] if yc else ("—", 0))
        ds = sorted(a["date"] for a in lst if a["y"])
        first, last = (ds[0], ds[-1]) if ds else ("—", "—")
        prev = CHANNELS[i - 1] if i > 0 else CHANNELS[-1]
        nxt = CHANNELS[i + 1] if i < len(CHANNELS) - 1 else CHANNELS[0]

        body = """<div class="dark">
%s
<div class="wrap"><div class="hero tight">
  <div class="crumb"><a href="/wechat/">约翰专栏</a> · 频道 %s</div>
  <h1>%s</h1>
  <p class="lede">%s</p>

  <div class="rhythm">
    <div class="cap">本　栏　节　律<span>亮色＝本栏 · 暗色＝同月其他栏</span></div>
    <div class="bars">%s</div>
    <div class="axis">%s</div>
    <p class="rnote">写得最多的一年是 <b>%s</b>（%d 篇）。本栏最早一篇 %s，最新一篇 %s。</p>
  </div>

  <div class="band">
    <div><b>%d</b><span>篇</span></div>
    <div><b>%d</b><span>页</span></div>
    <div><b>%s</b><span>写得最多的一年</span></div>
    <div><b>%d%%</b><span>占全站篇数</span></div>
  </div>
</div></div>
</div>

%s
<div class="light"><div class="wrap">
<div class="tools">
  <div class="filter"><label>本栏筛选</label><input id="q" type="search" placeholder="输入任意词，例如：%s" autocomplete="off" aria-label="在本栏内筛选"><span class="n" id="n"></span></div>
  <p class="empty" id="empty" style="display:none">本栏没有匹配的篇目。换一个词，或去<a href="/wechat/all/">全部篇目</a>里找。</p>
</div>
<section class="list">
%s</section>

<div class="nearby">
  <a href="/wechat/%s/"><small>上一栏</small><b>%s</b>%d 篇</a>
  <a href="/wechat/"><small>门厅</small><b>九个频道</b>回到总目，看写作节律</a>
  <a href="/wechat/%s/"><small>下一栏</small><b>%s</b>%d 篇</a>
</div>
</div></div>""" % (nav("wechat"), no, esc(name), esc(blurb), cbars, cyrs,
                   peak_y, peak_n, first, last, len(lst), pg, peak_y,
                   round(100 * len(lst) / len(canon)),
                   chipbar(key), esc(HINTS[key]), items_by_year(lst),
                   prev[1], esc(prev[2]), len(by_ch[prev[0]]),
                   nxt[1], esc(nxt[2]), len(by_ch[nxt[0]]))

        d = os.path.join(OUT, slug)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(
            page("%s · 约翰专栏 · 语言发生学" % name,
                 "%s共 %d 篇。%s" % (name, len(lst), blurb),
                 "https://lang.sdeuniverses.com/wechat/%s/" % slug,
                 body, FOOTER, cc, FILTER_JS))

    # ── 全部篇目 ──────────────────────────────────────
    secs = ""
    for key, slug, name, no, blurb, cc, picks in CHANNELS:
        lst = by_ch[key]
        items = "".join(item_html(a) for a in lst)
        secs += ('<section id="%s" data-group="%s" style="--accent:%s">'
                 '<div class="col-h"><span class="no">%s</span><h2>%s</h2>'
                 '<span class="ct">%d 篇 · <a href="/wechat/%s/">单看这一栏</a></span></div>'
                 '<p class="col-d">%s</p>\n%s</section>\n'
                 % (slug, slug, cc, no, esc(name), len(lst), slug, esc(blurb), items))

    jump = "".join('<a href="#%s" style="--cc:%s">%s <b>%d</b></a>'
                   % (c[1], c[5], esc(c[2]), len(by_ch[c[0]])) for c in CHANNELS)
    ychips = "".join('<button type="button" data-year="%s" aria-pressed="false">%s · %d 篇</button>'
                     % (y, y, sum(1 for a in canon if a["y"] == str(y)))
                     for y in range(2021, 2027))
    ychips += ('<button type="button" data-year="" aria-pressed="false">未标日期 · %d 篇</button>'
               % sum(1 for a in canon if not a["y"]))

    all_body = """<div class="dark">
%s
<div class="wrap"><div class="hero tight">
  <div class="crumb"><a href="/wechat/">约翰专栏</a> · 全部篇目</div>
  <h1>%d 篇正稿，<em>一页找完</em></h1>
  <p class="lede">九栏全部展开，另有 30 篇同题另稿挂在各自正稿下面。输入任意词即时筛选——<b>名目、摘要与日期都在检索范围内</b>；点年份只看那一年，再点一次取消。点标题读原文 PDF。</p>
</div></div>
</div>

<div class="light"><div class="wrap">
<div class="tools">
  <div class="filter"><label>全库筛选</label><input id="q" type="search" placeholder="输入任意词，例如：克拉申、看听线、GPT、词根" autocomplete="off" aria-label="筛选篇目"><span class="n" id="n"></span></div>
  <div class="chipy">%s</div>
  <p class="empty" id="empty" style="display:none">没有匹配的篇目。换一个词，或取消年份限制。</p>
  <div class="chipy" style="margin-top:18px">%s</div>
</div>
%s</div></div>""" % (nav("wechat"), len(canon), ychips, jump, secs)

    d = os.path.join(OUT, "all")
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(
        page("全部篇目 · 约翰专栏 · 语言发生学",
             "胡志英公众号原文存档全部 %d 篇正稿，九栏排列，可按词与年份即时筛选。" % len(canon),
             "https://lang.sdeuniverses.com/wechat/all/",
             all_body, FOOTER, "#1F3A5F", FILTER_JS))

    # ── 同步 lang 首页「栏五 · 约翰专栏」的九行与篇数 ──────────
    home = os.path.join(ROOT, "public", "sites", "lang", "index.html")
    if os.path.exists(home):
        h = open(home, encoding="utf-8").read()
        S, E = "<!-- wechat-rows:start -->", "<!-- wechat-rows:end -->"
        if S in h and E in h:
            rows = ""
            SHORT = {'genesis': '语感、语法、语用、意义与输出', 'enlighten': '三条线、看听线、听指、跟读与复述、敏感期', 'vocabulary': '一个词怎样长出来，又怎样被取出来', 'materials': 'RAZ、BrainPOP 与 ELL、原版动画与绘本', 'ai': '工具进课堂之后，能力被换走了什么', 'school': '翻转课堂、家校共学、考试与评价', 'lineage': '克拉申、维果茨基、索绪尔、洪堡、林语堂', 'notes': '五个孩子、郊区的院子、父亲与儿子', 'camp': '训练营、开班、公开课与学员见证'}
            for k, (key, slug, name, no, blurb, cc, picks) in enumerate(CHANNELS, 1):
                short = SHORT[slug]
                rows += ('  <a class="row" href="/wechat/%s/"><span class="r-n">%d</span>'
                         '<span class="r-t"><b class="r-h">%s</b>%s</span>'
                         '<span class="cnt"><b>%d</b> 篇</span></a>\n'
                         % (slug, k, esc(name), esc(short), len(by_ch[key])))
            head = h[:h.index(S) + len(S)]
            tail = h[h.index(E):]
            h = head + "\n" + rows + tail
            h = re.sub(r'(<h2>约翰专栏</h2><span class="ct">)\d+( 篇</span>)',
                       r'\g<1>%d\g<2>' % len(arts), h)
            open(home, "w", encoding="utf-8").write(h)
            print("  已同步 lang 首页栏五的九行与篇数")

    print("门厅 + %d 个频道页 + 全部篇目页 已生成于 %s" % (len(CHANNELS), OUT))
    for key, slug, name, no, blurb, cc, picks in CHANNELS:
        print("  %-11s %-8s %3d 篇" % (slug, name, len(by_ch[key])))
    print("  正稿 %d + 同题另稿 %d = %d 篇；最密的一个月 %s（%d 篇）；有日期 %d 篇"
          % (len(canon), len(arts) - len(canon), len(arts), hot, gmonth[hot], n_dated))


if __name__ == "__main__":
    build()
