#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_browse_directory.py —— 生成 /browse/ 「栏目总目录」页。

2026-08-18 用户裁定：长滚动的浏览页意义不大了（大家都是点栏目进的），
于是 /browse/ 从 893KB 的预告片长卷换成一页目录：**一屏之内看见所有栏目在哪儿**。

三条硬约束（改这个文件前先读）：
  1. **旧锚点必须落地**。全站有 4,517 处 href="/browse/…"，其中 888 处带锚点
     （#taste 749、#monograph 52、#daily 22、#drwang 19、#today-longread 17、
      #daily-hotspot 12、#grid 9、#today-articles/#books/#master 各 2、
      #daily-quotes/#feed 各 1）。这些 id 一个都不能少，少一个就是几百条死锚点。
  2. **两条 feed 不在这里**。今日长文与每日更新已迁到 /today/（那才是它们的正主），
     这一页只放去处，不放条目——放了就又长成一张长卷。
  3. **导航逐字取自旧首页**（nav 与 nav CSS 都从 public/overview/index.html 抽），
     顶栏与站内其余页面保持同一副面孔；不要在这里另画一套。

旧长卷原样保留在 /overview/，页尾留了入口。
"""
import re
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "public" / "overview" / "index.html"      # 旧首页长卷（nav 与 CSS 的来源）
OUT = ROOT / "public" / "browse" / "index.html"

CSS_TOKENS = ["nav", ".nav-", ".nl-", ".agent-strip", ".ag-", ".nbs", ".col-",
              ".lang-", ".visit-badge", ".vb-", ".zh-only", ".en-only", ".wdsm-",
              ":root", "html{", "body{", "body.en"]


def nav_and_css(src_html):
    """从旧首页里原样抽出 <nav> 与它用到的那部分 CSS。"""
    m = re.search(r"<nav>.*?</nav>", src_html, re.S)
    assert m, "旧首页里找不到 <nav>"
    nav = m.group(0)
    css = "".join(re.findall(r"<style>(.*?)</style>", src_html, re.S))
    kept, i = [], 0
    while i < len(css):
        if css[i:i + 6] == "@media":
            j = css.index("{", i)
            depth, k = 0, j
            while True:
                if css[k] == "{":
                    depth += 1
                elif css[k] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                k += 1
            block = css[i:k + 1]
            if any(t in block for t in CSS_TOKENS):
                kept.append(block)
            i = k + 1
        else:
            j = css.find("{", i)
            if j < 0:
                break
            k = css.find("}", j)
            if k < 0:
                break
            rule = css[i:k + 1]
            head = rule.split("{")[0]
            if any(t in head or t in rule[:60] for t in CSS_TOKENS):
                kept.append(rule.strip())
            i = k + 1
    return nav, "\n".join(kept)


# ── 目录内容 ───────────────────────────────────────────────────────────────
# 每组 = (区块 id, 眉题, 大标题, 一句话, [卡片…])
# 卡片 = (链接, 标题, 一句话, 卡片自己的 id 或 "")
GROUPS = [
    ("today-articles", "TODAY", "今日文章",
     "每天在这里更新的一切。两条 feed 都在 /today/ 里——长文一条，动态一条。", [
         ("/today/#today-longread", "今日长文", "当天发布的万字长文，按日期倒序，最新一篇在最上面。", "today-longread"),
         ("/today/#daily", "每日更新", "这个宇宙今天又长出了什么：新论文、新频道、新专著，逐条记。", "daily"),
         ("/today/", "两条一起看", "今日文章总页，长文与动态在同一页。", "feed"),
         ("/quotes/", "今日三句", "每天从已发表专栏正文里抽三句承重句；池子里还有往日全部。", "daily-quotes"),
     ]),
    ("must-read", "COLLISION", "三条主力栏目",
     "站里最新的思想都从这三条出：站内碰撞、站外碰撞、各学科前沿摘要。", [
         ("/paradigm/", "每日必读 · 典范文", "Claude 在王德生指导下把三篇站内论文正面撞在一起，撞出任何一篇单看都看不见的判断。", ""),
         ("/confluence/", "学科通融", "撞的是站外三个不同学科的理论体系——先找到它们在同一问题上互相排斥的地方，再撞。", ""),
         ("/frontier/", "新思想前沿", "近十年各主要领域最新思想摘要，六百余块学科面板，王德生亲撰。", ""),
     ]),
    ("taste", "AGENTS", "SDE 智能体 · 免费品尝",
     "用你自己的 API Key，浏览器直连厂商，服务器不经手；不注册、不留痕。", [
         ("/taste/chatsde/", "ChatSDE", "全站问答与 SDE 对谈：站内三千余篇随问随引。", ""),
         ("/taste/idea-generator/", "SDE 金点子", "把一个具体问题喂进去，长出可以被推翻的新命题。", ""),
         ("/taste/zhiwen/", "中华智问", "用发生学的眼读中华典籍。", ""),
         ("/taste/iq-scorer/", "创新智商评分官", "五维盲评一段思想文本走得多深。", ""),
         ("/taste/confluence/", "学科通融机", "三门学问进，一个新读数出。", ""),
         ("/taste/", "全部智能体 →", "品尝系列总入口。", ""),
     ]),
    ("drwang", "DR. WANG", "王博士与 SDE",
     "一个具体的问题，长成一套新地基。", [
         ("/drwang/", "专栏总页", "从九十年代那间机房到 SDE 发生学，一条线读下来。", ""),
         ("/column/ontology-grid/", "三维九宫", "一套本体论的九个入口：在 E 中，经 D，成 S。", "grid"),
         ("/master/", "解构大师", "用发生学的眼，解构思想史上的巨人。", "master"),
         ("/philosophy/", "SDE 哲学", "三大方程、123 原理、意义三律。", ""),
     ]),
    ("monograph", "BOOKS", "专著栏目",
     "德麦国际出版的跨域专著，与各书的摘要导读。", [
         ("/monographs/", "专著导读", "每部书一页摘要，先读导读再决定读哪本。", ""),
         ("/books/", "德麦国际专著", "全部已出版专著书架。", "books"),
         ("/books/sde-ontology-intro/", "《SDE 本体论入门》", "把根本追问从「世界是什么」换成「世界如何发生」。", ""),
     ]),
    ("columns", "COLUMNS", "主题专栏",
     "按题分栏，每一栏都是一个持续在长的方向。", [
         ("/creation/", "学术创造", "研究哲学、创造力、写作发生学。", ""),
         ("/thought/", "哲学与思想", "西方哲学解构与思想史。", ""),
         ("/discovery-vs-genesis/", "发现 VS 发生", "这套理论最锋利的那条分界。", ""),
         ("/ai/", "AI 专栏", "大模型、智能体，与人还剩下什么。", ""),
         ("/education/", "教育专栏", "从应试到发生：教育被什么卡住。", ""),
         ("/health/", "健康专栏", "健康发生学与医学频道。", ""),
         ("/life/", "人生与家庭", "婚姻、家庭、信仰、时间。", ""),
         ("/business/", "商业与经济", "企业本体论与经济发生学。", ""),
         ("/culture/", "文化与艺术", "我文化、艺术裁决、中华典籍。", ""),
         ("/how/", "怎么做", "落到操作那一层的实践文。", ""),
     ]),
    ("features", "CHANNELS", "特色频道",
     "近期新开的专栏与频道，每一个都是一整套写完的。", [
         ("/exam-education/", "应试教育", "划线、清点、算账：应试与教育的分界落在哪个可查的地方。", ""),
         ("/students/hu-min/mediation/", "中介", "中介与抽成在哪里分开，去中介化怎样才走得出去。", ""),
         ("/marriage-happiness/", "婚姻幸福", "幸福不是没有裂缝，而是两个人仍能在裂缝中生成共同生活。", ""),
         ("/students/chen-xiaoyan/precision-medicine/", "精准医疗与慢病发生学", "自组织权被接管之后，身体还剩哪一段是自己的。", ""),
         ("/family-ethics/", "家庭与伦理", "功能被一样样接走之后，家没有散——痛苦替下了它们。", ""),
         ("/faith-and-life/", "信仰与人生", "当算法替我们解释世界，信仰从确定性退回承担。", ""),
         ("/art/", "艺术专栏", "艺术被剩在那个还要求人亲自踩下去的位置上。", ""),
         ("/sde-education/", "SDE 教育学", "「传道授业」里那个「传」字，从未被拿出来检查过。", ""),
         ("/involution/", "内卷与出路", "内卷不是竞争太狠，是 0—1 的发生窗口缺席。", ""),
         ("/i-culture/", "我文化", "人情稳「时」、面子稳「位」、关系稳「势」。", ""),
     ]),
    ("students", "STUDENTS", "学员与师范",
     "学员的论文、专著与专栏——站上大部分新思想是从这里长出来的。", [
         ("/students/", "学员专栏", "全部学员名册、作品与排名。", ""),
         ("/mentor/", "师范文", "怎么带一个人从提问走到成篇。", ""),
         ("/students/submit/", "投稿", "把你的稿子投进来。", ""),
         ("/recruit/", "学徒招募", "智能体平台合作开发学徒，仅招 5 人。", ""),
     ]),
    ("brain-gym", "DAILY", "健脑三件日课",
     "智能体是给你跑产线的，这三件是给你自己练的。不烧 Key、不注册，记录只存在你自己的浏览器里。", [
         ("/brain-gym/", "健脑专栏", "三件日课总入口。", ""),
         ("/challenge/", "每日挑战", "一天一道，练的是提问不是答题。", ""),
         ("/training/", "训练场", "把一个念头逐步锻造成命题。", ""),
         ("/growth-tree/", "成长树", "看自己这半年长到哪儿了。", ""),
     ]),
    ("community", "COMMUNITY", "社区与平台",
     "人在的地方。会议、广场、微信群，以及这个平台到底是个什么地方。", [
         ("/meeting/", "SDE 会议", "大教室、答疑室、讨论室，输入会议号即入。", ""),
         ("/sde-talk/", "SDE 广场", "全站公共聊天室。", ""),
         ("/discussions/", "讨论区", "按篇讨论，实名登录。", ""),
         ("/sde-wechat/", "SDE 微信", "群聊、私聊、通讯录。", ""),
         ("/about/", "平台介绍", "这里到底是个什么地方，两万字讲清楚。", ""),
         ("/search/", "全站检索", "三千余篇、八千余万字，一个框里问。", ""),
     ]),
]

CARD_CSS = """
/* ── 目录页自己的版式（2026-08-18）──
   一页目录，不是一张长卷：卡片只放去处与一句话，条目一律不进这一页。 */
main.dir{max-width:1180px;margin:0 auto;padding:0 2rem 5rem}
.dir-hero{padding:2.2rem 0 1.4rem;border-bottom:1px solid var(--border2)}
.dir-hero .eyebrow{font-size:0.72rem;letter-spacing:0.34em;color:var(--gold2);margin-bottom:0.7rem}
.dir-hero h1{font-size:clamp(1.9rem,4vw,2.9rem);font-weight:600;letter-spacing:0.02em}
.dir-hero p{color:var(--text2);margin-top:0.7rem;max-width:56ch}
.dir-hero .qbar{margin-top:1.3rem;display:flex;flex-wrap:wrap;gap:0.5rem}
.dir-hero .qbar a{display:inline-block;padding:5px 14px;border:1px solid var(--border);border-radius:18px;
  text-decoration:none;color:var(--text);font-size:0.86rem;background:var(--card)}
.dir-hero .qbar a:hover{background:var(--card2);border-color:var(--gold2)}
section.grp{padding:2.1rem 0 0.4rem;border-bottom:1px solid var(--border2);scroll-margin-top:150px}
section.grp>.eyebrow{font-size:0.68rem;letter-spacing:0.3em;color:var(--gold2)}
section.grp>h2{font-size:1.42rem;font-weight:600;margin:0.35rem 0 0.3rem}
section.grp>.lede{color:var(--text2);font-size:0.94rem;max-width:62ch;margin-bottom:1.1rem}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(268px,1fr));gap:0.85rem;padding-bottom:1.6rem}
a.card-l{display:block;text-decoration:none;color:inherit;background:var(--card);border:1px solid var(--border2);
  border-left:3px solid var(--gold2);padding:0.85rem 1rem;transition:background .16s,border-color .16s;scroll-margin-top:150px}
a.card-l:hover{background:var(--card2);border-color:var(--border)}
a.card-l b{display:block;font-size:1.02rem;font-weight:600;margin-bottom:0.28rem}
a.card-l span{display:block;font-size:0.85rem;color:var(--text2);line-height:1.62}
.dir-foot{padding:2rem 0 0;color:var(--text2);font-size:0.88rem}
.dir-foot a{color:var(--gold);text-decoration:none}
.dir-foot a:hover{text-decoration:underline}
.dir-foot .scroll-note{margin-top:0.9rem;padding:0.9rem 1rem;background:var(--card);border:1px dashed var(--border);font-size:0.86rem}
@media(max-width:760px){main.dir{padding:0 1.1rem 4rem}.cards{grid-template-columns:1fr}}
"""

PAGE = """<!doctype html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>浏览 · 栏目总目录 | 爱思乐园 SDE Universes</title>
<meta name="description" content="爱思乐园全站栏目总目录：今日文章、每日必读、学科通融、新思想前沿、SDE 智能体、专著栏目、主题专栏、学员专栏、社区与平台——一页看清所有栏目在哪儿。">
<link rel="canonical" href="https://sdeuniverses.com/browse/">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600&family=EB+Garamond:wght@400;500&family=Noto+Serif+SC:wght@300;400;500;600&display=swap" media="print" onload="this.media='all';this.onload=null">
<style>
__NAVCSS__
__CARDCSS__
body{padding-top:150px}
@media(max-width:900px){body{padding-top:190px}}
</style>
</head>
<body class="zh">
__NAV__
<main class="dir">
  <div class="dir-hero">
    <p class="eyebrow">BROWSE · SITE DIRECTORY</p>
    <h1>浏览 · 栏目总目录</h1>
    <p>这一页只回答一个问题：<b>哪一栏在哪儿。</b>条目不在这里——各栏自己的页里才有。要找具体某一篇，用<a href="/search/" style="color:var(--gold)">全站检索</a>比翻目录快得多。</p>
    <div class="qbar">
      <a href="/today/">今日文章</a><a href="/paradigm/">每日必读</a><a href="/confluence/">学科通融</a><a href="/frontier/">新思想前沿</a><a href="/taste/chatsde/">ChatSDE</a><a href="/students/">学员专栏</a><a href="/search/">🔍 全站检索</a>
    </div>
  </div>
__GROUPS__
  <div class="dir-foot">
    <p class="scroll-note">要一页滚完全站的旧版长卷（今日三句、智能体集群、各专栏预告依次排下来）仍在：<a href="/overview/">总览长卷 →</a></p>
    <p style="margin-top:1.2rem">© 德麦国际 · <a href="/browse/">爱思乐园 SDE Universes</a> · <a href="/home/">回系统入口</a></p>
  </div>
</main>
<script>
// 中英切换：这一页自带一份最小实现（首页那份绑在 renderMatrix 上，搬不过来）
function setLang(lang){
  var cl=document.body.classList; cl.remove('zh'); cl.remove('en'); cl.add(lang);
  document.querySelectorAll('.lang-btn').forEach(function(b){
    b.classList.toggle('active', b.textContent.toLowerCase()===lang || (b.textContent==='中'&&lang==='zh'));
  });
  document.documentElement.lang = lang==='zh' ? 'zh' : 'en';
  try{ localStorage.setItem('sde_wds_lang', lang); }catch(e){}
}
try{ var _l=localStorage.getItem('sde_wds_lang'); if(_l==='en') setLang('en'); }catch(e){}
// 访问总次数（与旧首页同一个 Durable Object 计数）
(async function(){
  try{
    var el=document.getElementById('visitCount'); if(!el) return;
    var counted=sessionStorage.getItem('sde_visit_counted');
    var r=await fetch('/api/visits',{method:counted?'GET':'POST'});
    if(!counted) sessionStorage.setItem('sde_visit_counted','1');
    var d=await r.json();
    el.textContent=d.total.toLocaleString('zh-Hans-CN');
  }catch(e){}
})();
</script>
<script src="/wds-mode.js?v=20260818a" defer></script>
</body>
</html>
"""


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build():
    src = SRC.read_text(encoding="utf-8")
    nav, navcss = nav_and_css(src)
    out = []
    for gid, eyebrow, title, lede, cards in GROUPS:
        rows = []
        for href, name, desc, cid in cards:
            idattr = ' id="%s"' % cid if cid else ""
            rows.append('      <a class="card-l"%s href="%s"><b>%s</b><span>%s</span></a>'
                        % (idattr, href, esc(name), esc(desc)))
        out.append(
            '  <section class="grp" id="%s">\n'
            '    <p class="eyebrow">%s</p>\n'
            '    <h2>%s</h2>\n'
            '    <p class="lede">%s</p>\n'
            '    <div class="cards">\n%s\n    </div>\n'
            '  </section>' % (gid, eyebrow, esc(title), esc(lede), "\n".join(rows))
        )
    html = (PAGE.replace("__NAVCSS__", navcss)
                .replace("__CARDCSS__", CARD_CSS)
                .replace("__NAV__", nav)
                .replace("__GROUPS__", "\n".join(out)))
    # 旧锚点一个都不能少 —— 少一个就是几百条死锚点
    need = ["taste", "monograph", "daily", "drwang", "today-longread", "grid",
            "today-articles", "books", "master", "daily-quotes", "feed"]
    miss = [a for a in need if ('id="%s"' % a) not in html]
    assert not miss, "旧锚点落空：%s" % miss
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print("wrote %s  %d bytes" % (OUT, len(html.encode("utf-8"))))


if __name__ == "__main__":
    if not SRC.exists():
        sys.exit("找不到 %s —— 先把旧首页长卷搬到 /overview/ 再跑本脚本" % SRC)
    build()
