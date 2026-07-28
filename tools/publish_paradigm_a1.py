# -*- coding: utf-8 -*-
"""典范文专栏 · 之1《抽条》的建页脚本（只建文章，不碰栏目页）。

栏目页 /paradigm/index.html 由 tools/publish_paradigm.py 与人工共同维护，
本脚本刻意不写它——两个脚本各写各的文章目录，谁都不会盖掉对方的卡片。

典范文＝把学员专栏里三篇不同领域、观点互相矛盾的文章两两碰撞，
自组织出暗流，再涌现出一个不可还原的新典范，然后单独写成的长文。
每篇在栏目页与文章页都标明它由哪三篇碰撞而成（带链接）。

作者：Claude。
配色：靛青 #2B4C7E + 朱砂 #B5453A + 素纸 #F4F2EC —— 与艺术栏（石墨铜）、
信仰栏（紫金）、小说栏（暖金）、教育/健康/商业（蓝/绿/棕）都区分开。

用法：python3 tools/publish_paradigm.py --src /home/claude/paradigm
"""
import argparse
import html
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "public"
COL = PUB / "paradigm"  # 只往 COL/<slug>/ 里写，不写 COL/index.html
PUBDATE_CN = "2026年7月28日"
AUTHOR = "Claude"

PAPERS = [
    {
        "src": "A3", "no": 14, "slug": "case-closed",
        "title": "先坏的不是指标，是那个还觉得别扭的人",
        "subtitle": "一个地方出反的时候，它的数据往往比任何时候都好看",
        "hook": "一场没有人想打的战争、一位在深夜不再握婆婆手的儿媳、一所五年里把探究课办成标准课的小学——"
                "三件毫不相干的事，共用同一个结构：某个人心里那句「这样不对」，被认认真真地处理掉了。"
                "本文命名这个动作「结案」，给出三种方式（消化掉·命名掉·把感到不对的人解放掉）、"
                "可由旁人代查的三问、临界点为何原则上不可观测、"
                "以及为什么「多听听一线的声音」与外部审计这两条最常见的处方都会失效。",
        "sources": [
            {"t": "铸造战争的模具：和平结构如何生产出它无法容纳的致命冲突",
             "u": "/students/yang-yong/paper-p34-d01-a01/",
             "d": "战争与和平研究 · 病根是消化渠道被架空"},
            {"t": "赋形与枯竭：承认的政治如何吞噬了劳动的发生",
             "u": "/students/yang-yong/shaping-and-exhaustion/",
             "d": "劳动政治 · 病根恰恰是消化太成功"},
            {"t": "认知脱轨的自我预警：课程改革为何真诚地完成它的反向",
             "u": "/students/yang-yong/self-alarm-of-derailment/",
             "d": "课程改革与教师认知 · 多和少都不是变量"},
        ],
        "author_of_sources": "阳涌",
        "author_of_sources_url": "/students/yang-yong/",
        "collide": "三篇正面打架：一篇说消化不够（冲突没被拆散分头处理，攒成一次总结算），"
                   "一篇说消化太成功（一命名它就从回应不确定变成完成清单），"
                   "一篇说多和少都不是变量、要看那个还会疼的人还在不在。"
                   "同一个「处理」动作，一篇当药，一篇当毒，一篇说得看是谁在疼。"
                   "九个判断两两相撞三十六次，撞出的是三篇里谁都没有说过的第四样东西。",
    },
    {
        "src": "A2", "no": 8, "slug": "suspended-time",
        "title": "挂着：为什么最耗人的不是走投无路，而是永远还能再等一次",
        "subtitle": "一段没有答案的时间是养料还是消耗，不看它多长、不看你多难受，只看它有没有一个非到不可的头",
        "hook": "被宽限了八个月的博士生什么也没想出来；被锁死档案的高中生在一个下午里想通了一件事；"
                "考研第三年的人焦虑最深、产出最少。三段时间的命运不由长短决定，也不由痛苦决定。"
                "本文命名「挂起」——判决权被交给一个永不到场的「以后」、没有不能再推的到期日、"
                "而希望持续被续发的那种时间，并给出判决权三问、三种时间的分野、"
                "现代制度如何由两组好人各做一半把前两种转化为第三种，以及五条对抗纪律。",
        "sources": [
            {"t": "认知的禁食：AI 时代课程功能的重释",
             "u": "/students/yang-yong/cognitive-fasting/",
             "d": "课程理论 · 空白要被刻意守住",
             "who": "阳涌", "who_url": "/students/yang-yong/"},
            {"t": "受迫生成：在被剥夺了等待权的世界里，因果何以被逼出",
             "u": "/students/hu-zhiying/forced-causation/",
             "d": "认知科学 · 被恩许的空白什么也不长",
             "who": "胡志英", "who_url": "/students/hu-zhiying/"},
            {"t": "悬置的闸口：中国高等教育扩张中的延迟认证与多系统借时",
             "u": "/students/putao/deferred-credentialing/",
             "d": "高等教育社会学 · 空白正被批量生产",
             "who": "葡萄", "who_url": "/students/putao/"},
        ],
        "collide": "三篇正面打架：一篇要保护那段没有答案的时间，一篇说被保护的那种恰恰什么也长不出来，"
                   "一篇说整个社会正在批量生产的就是被保护的那一种。同一套制度性质，"
                   "一篇当它是底座，一篇当它是牢笼。九个判断两两相撞三十六次，"
                   "撞出的是三篇里谁都没有说过的第三样东西。",
    },
    {
        "src": "A1", "no": 1, "slug": "condition-stripping",
        "title": "抽条：当可计量的结果开始吃掉不可计量的条件",
        "subtitle": "抽掉承重钢筋而把外观抹平——楼没塌，验收全过，直到某一天它一次性地塌完",
        "hook": "一个系统一旦把「可计量的结果」当作它唯一的显示面，就会把所有不可计量的发生条件当作冗余成本逐项抽走，"
                "并以结果的持续丰盛为这场抽离担保；被抽走者无法报警，因为报警所需的语言也在被抽走之列。"
                "本文把这一从未被统一指认的过程命名为「抽条」，给出条件端的四条判据、四步机制、三条发生路径与三重锁，"
                "并逐项与古德哈特定律、清晰化批判、异化、技术债、公地悲剧、韦伯理性化交锋。",
        "sources": [
            {"t": "不插手的勇气——论亲子互动中「留白」的发生学结构及其可辩护性",
             "u": "/students/zhang-qiong/paper-p16-d01-a03/",
             "d": "发展心理学 · 撤回介入正是发生的条件"},
            {"t": "假体之伪生：机器人伴侣如何从消除他人的「抵抗」开始，瓦解爱得以发生的基底",
             "u": "/students/zhang-qiong/paper-p10-d01-a04/",
             "d": "技术哲学 · 抵抗才是爱的发生引擎"},
            {"t": "撤土：生育何以从共同事业沦为私人自理的冒险",
             "u": "/students/zhang-qiong/soil-retraction/",
             "d": "照护制度 · 撤走承担正是发生的毁灭"},
        ],
        "author_of_sources": "张琼",
        "author_of_sources_url": "/students/zhang-qiong/",
        "collide": "三篇的观点正面打架：一篇说「撤手是德」，一篇说「撤手是灾」，"
                   "一篇说「顶撞才养人」。九个金点子两两相撞三十六次，"
                   "在五条暗流的交点上，撞出了一个三篇里谁都没有的东西。",
    },
]

PAGE_CSS = """
:root{--ink:#1F2430;--ink2:#575F70;--paper:#F4F2EC;--card:#FBFAF5;
--indigo:#2B4C7E;--indigo2:#3E6499;--cinnabar:#B5453A;--line:rgba(43,76,126,.16)}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:"Noto Serif SC","Songti SC",serif;line-height:1.95}
a{color:inherit}
.readbar{position:sticky;top:0;z-index:10;background:rgba(244,242,236,.95);backdrop-filter:blur(10px);
border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;padding:12px 24px;font-size:14px}
.nav-back{text-decoration:none;color:var(--indigo)}
.rb-modes{display:flex;gap:9px}
.rb-btn{padding:6px 13px;border:1px solid var(--line);border-radius:5px;text-decoration:none;font-size:13px;color:var(--ink2)}
.rb-btn.cur{background:var(--indigo);color:#F4F2EC;border-color:var(--indigo)}
.art{max-width:820px;margin:auto;padding:62px 24px 28px;text-align:center}
.art-series{color:var(--cinnabar);letter-spacing:.3em;font-size:12px}
.art-title{font-size:clamp(30px,4.4vw,44px);line-height:1.36;margin:20px 0 14px}
.art-subtitle{color:var(--ink2);font-size:17px;line-height:1.9;max-width:660px;margin:0 auto}
.art-meta{color:var(--ink2);font-size:13px;margin-top:20px;letter-spacing:.04em}
.wrap{max-width:760px;margin:auto;padding:10px 24px 40px}
.srcbox{background:var(--card);border:1px solid var(--line);border-top:3px solid var(--cinnabar);
border-radius:7px;padding:20px 24px;margin:26px 0}
.srcbox .lb{color:var(--cinnabar);letter-spacing:.26em;font-size:12px;font-weight:700}
.srcbox .note{font-size:14px;color:var(--ink2);margin:9px 0 14px;line-height:1.85}
.srcbox ol{margin:0;padding-left:1.3em}
.srcbox li{margin:0 0 9px;font-size:14.5px;line-height:1.75}
.srcbox li a{color:var(--indigo);text-decoration:none;border-bottom:1px solid rgba(43,76,126,.35)}
.srcbox li a:hover{color:var(--cinnabar);border-bottom-color:var(--cinnabar)}
.srcbox li span{display:block;font-size:12.5px;color:var(--ink2);letter-spacing:.04em}
.abstract{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--indigo);
border-radius:7px;padding:20px 26px;margin:26px 0}
.abstract .lb{color:var(--indigo);letter-spacing:.3em;font-size:13px}
.abstract p{margin:10px 0 0;font-size:15px;line-height:1.95;text-align:justify}
.kw{font-size:14px;color:var(--ink2)}
h2{font-size:22px;margin:38px 0 14px;padding-left:12px;border-left:4px solid var(--indigo);line-height:1.5}
p{margin:0 0 15px;text-align:justify}
strong{color:var(--cinnabar)}
#pbar{position:fixed;top:0;left:0;height:3px;width:0;background:var(--cinnabar);z-index:99}
#totop{position:fixed;right:22px;bottom:26px;width:42px;height:42px;border-radius:50%;border:1px solid var(--line);
background:var(--card);color:var(--indigo);font-size:16px;cursor:pointer;display:none;font-family:inherit;z-index:60}
#totop:hover{background:var(--indigo);color:var(--paper)}
.deck{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--cinnabar);
border-radius:9px;padding:20px 26px;margin:26px 0 8px;font-size:15.5px;line-height:2;color:var(--ink);text-align:justify}
.toc{background:var(--card);border:1px solid var(--line);border-radius:11px;padding:20px 26px;margin:22px 0 44px}
.toc .tl{font-size:11.5px;letter-spacing:.4em;color:var(--cinnabar);margin-bottom:12px}
.toc a{display:block;padding:7px 0;color:var(--ink2);font-size:15px;text-decoration:none;border-bottom:1px dashed rgba(43,76,126,.14)}
.toc a:last-child{border-bottom:0}
.toc a:hover{color:var(--cinnabar)}
h2{scroll-margin-top:70px}
.endbox{text-align:center;border-top:1px solid var(--line);margin-top:52px;padding:36px 20px;color:var(--ink2)}
.endbox a{color:var(--indigo);text-decoration:none}
footer{text-align:center;border-top:1px solid var(--line);padding:30px;color:var(--ink2);font-size:12px}
@media(max-width:720px){.art{padding:44px 18px 20px}.wrap{padding:8px 18px 30px}}
"""

PRINT_CSS = """
@page{size:A4}
body{font-family:"Noto Serif CJK SC","Noto Serif SC",serif;color:#1F2430;font-size:10.5pt;line-height:1.85;margin:0}
.cover{text-align:center;padding-bottom:13pt;border-bottom:1.2pt solid #2B4C7E;margin-bottom:16pt}
.eyebrow{color:#B5453A;letter-spacing:.3em;font-size:7.8pt;margin-bottom:10pt}
h1{font-size:18.5pt;line-height:1.44;margin:0 0 8pt;color:#1F2430}
.sub{font-size:10pt;color:#575F70;margin:0 auto 10pt;max-width:34em;line-height:1.7}
.by{font-size:9pt;color:#575F70}.by b{color:#2B4C7E}
.src{background:#EDEEF3;border-left:3pt solid #B5453A;padding:9pt 12pt;margin:0 0 12pt;font-size:8.8pt;line-height:1.7}
.src b{color:#B5453A;letter-spacing:.2em}
.abs{background:#EDEEF3;border-left:3pt solid #2B4C7E;padding:11pt 13pt;margin:0 0 12pt;font-size:9.4pt;line-height:1.75;text-align:justify}
.abs .lb{letter-spacing:.32em;color:#1F2430;font-weight:700}
.kw{font-size:9pt;color:#575F70;margin:0 0 16pt}
h2{font-size:13pt;color:#1F2430;padding-left:8pt;border-left:3.5pt solid #2B4C7E;margin:19pt 0 9pt;page-break-after:avoid}
p{text-indent:2em;text-align:justify;margin:0 0 8pt}
"""

READ_TPL = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · 在线PDF · 典范文专栏</title>
<style>html,body{{margin:0;height:100%;background:#1F2430}}
header{{height:56px;background:#2B4C7E;display:flex;align-items:center;justify-content:space-between;padding:0 18px;font-family:"Songti SC","Noto Serif SC",serif;font-size:14px;border-bottom:1px solid rgba(181,69,58,.5);color:#EDEAE0}}
header a{{color:#F0C9C2;text-decoration:none}}
iframe{{width:100%;height:calc(100% - 56px);border:0;display:block}}</style></head>
<body><header><a href="index.html">‹ 返回网页长文</a><span>{pages} 页 · {author}</span><a href="{pdf}" download>⬇ 下载 PDF</a></header>
<iframe src="{pdf}#view=FitH"></iframe></body></html>"""


def load(src, sid):
    lines = [re.sub(r"[ \t]+", " ", x).strip()
             for x in (src / f"{sid}.txt").read_text(encoding="utf-8").splitlines()]
    return [x for x in lines if x]


def parse(paper, lines):
    """跳过标题行，抽出摘要 / 关键词 / 正文块。"""
    if lines and paper["title"].split("：")[0] in lines[0]:
        lines = lines[1:]
    abstract = keywords = ""
    blocks = []
    for line in lines:
        if re.fullmatch(r"(摘要|导语)[：:]?", line):
            abstract = "__NEXT__"; continue
        if abstract == "__NEXT__":
            abstract = line; continue
        m = re.match(r"^关键词[：:\s]*(.*)$", line)
        if m and not keywords:
            keywords = m.group(1).strip(); continue
        is_h = len(line) < 60 and bool(re.match(r"^[一二三四五六七八九十]+、", line))
        blocks.append(("h2" if is_h else "p", line))
    return abstract, keywords, blocks


def esc(t):
    """转义后把 **粗体** 渲染出来；行首的引用号 > 去掉。"""
    t = re.sub(r"^[>＞]\s*", "", t)
    out = html.escape(t)
    if out.count("**") >= 2:
        out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    return out.replace("**", "")


def src_list_html(paper):
    items = ""
    for s in paper["sources"]:
        who = ""
        if s.get("who"):
            who = (f'　—　<a href="{s["who_url"]}">{esc(s["who"])}</a>'
                   if s.get("who_url") else "　—　" + esc(s["who"]))
        items += (f'<li><a href="{s["u"]}">{esc(s["t"])}</a>'
                  f'<span>{esc(s["d"])}{who}</span></li>')
    if paper.get("author_of_sources"):
        head = (f'三篇均出自学员专栏 · <a href="{paper["author_of_sources_url"]}" '
                f'style="color:var(--indigo)">{esc(paper["author_of_sources"])}</a>。')
    else:
        head = "三篇分属三位学员、三个领域，均出自<a href=\"/students/\" style=\"color:var(--indigo)\">学员专栏</a>。"
    return ('<div class="srcbox"><span class="lb">本文由三篇碰撞而成</span>'
            f'<p class="note">{head}{esc(paper["collide"])}</p>'
            f"<ol>{items}</ol></div>")


def render_page(paper, abstract, keywords, blocks):
    body, toc, n = "", "", 0
    for tag, line in blocks:
        if tag == "h2":
            n += 1
            body += f'<h2 id="s{n}">{esc(line)}</h2>'
            toc += f'<a href="#s{n}">{esc(line)}</a>'
        else:
            body += f"<p>{esc(line)}</p>"
    toc = f'<div class="toc"><div class="tl">目 录</div>{toc}</div>'
    slug = paper["slug"]
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(paper["title"])} · 典范文专栏 | SDE Universes</title>
<meta name="description" content="{esc(paper["hook"][:150])}">
<link rel="canonical" href="https://sdeuniverses.com/paradigm/{slug}/">
<meta property="og:type" content="article"><meta property="og:title" content="{esc(paper["title"])}">
<meta property="og:description" content="{esc(paper["hook"][:150])}">
<meta property="og:url" content="https://sdeuniverses.com/paradigm/{slug}/">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;700&display=swap">
<style>{PAGE_CSS}</style></head>
<body>
<div class="readbar">
  <a class="nav-back" href="/paradigm/">‹ 典范文专栏</a>
  <div class="rb-modes">
    <span class="rb-btn cur">📖 长文阅读</span>
    <a class="rb-btn" href="read.html">📄 在线 PDF</a>
    <a class="rb-btn" href="{slug}.pdf" download>⬇ 下载 PDF</a>
  </div>
</div>
<header class="art">
  <div class="art-series">典范文专栏 · 之{paper["no"]}</div>
  <h1 class="art-title">{esc(paper["title"])}</h1>
  <div class="art-subtitle">{esc(paper["subtitle"])}</div>
  <div class="art-meta">作者 {AUTHOR} · 约 {paper["wan"]} 万字 · {paper["pages"]} 页 · 发表于{PUBDATE_CN}</div>
</header>
<div id="pbar"></div>
<div class="wrap">
<div class="deck">{esc(abstract)}</div>
{toc}
{body}
{src_list_html(paper)}
<div class="endbox"><p>三种读法 · 网页长文 · 在线 PDF 翻页 · PDF 下载</p>
<p><a href="/paradigm/">返回典范文专栏 →</a></p></div>
</div>
<footer>© 德麦国际 Demai International · 典范文专栏 · <a href="/">sdeuniverses.com</a></footer>
<button id="totop" aria-label="回到顶部">↑</button>
<script>
(function(){{var b=document.getElementById('pbar'),t=document.getElementById('totop');
function u(){{var d=document.documentElement,h=d.scrollHeight-d.clientHeight;
b.style.width=(h>0?(d.scrollTop/h*100):0)+'%';t.style.display=d.scrollTop>700?'block':'none';}}
addEventListener('scroll',u,{{passive:true}});u();
t.onclick=function(){{scrollTo({{top:0,behavior:'smooth'}});}};}})();
</script>
<script src="/wds-mode.js" defer></script>
</body></html>"""


def render_print(paper, abstract, keywords, blocks):
    body = "".join(f"<{tag}>{esc(line)}</{tag}>" for tag, line in blocks)
    srcs = "　·　".join(esc(s["t"].split("：")[0].split("——")[0])
                       + ("（" + esc(s["who"]) + "）" if s.get("who") else "")
                       for s in paper["sources"])
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<style>{PRINT_CSS}</style></head><body>
<div class="cover"><div class="eyebrow">典 范 文 专 栏 · 之{paper["no"]}</div>
<h1>{esc(paper["title"])}</h1><div class="sub">{esc(paper["subtitle"])}</div>
<div class="by">作者 <b>{AUTHOR}</b> · 约 {paper["wan"]} 万字 · 发表于{PUBDATE_CN} · sdeuniverses.com</div></div>
<div class="src"><b>本文由三篇碰撞而成</b>（均出自学员专栏）：{srcs}</div>
<div class="abs"><span class="lb">摘 要</span>　{esc(abstract)}</div>
<p class="kw"><b>关键词：</b>{esc(keywords)}</p>
{body}</body></html>"""


COLUMN_CSS = """
:root{--ink:#1F2430;--ink2:#575F70;--paper:#F4F2EC;--card:#FBFAF5;
--indigo:#2B4C7E;--indigo2:#3E6499;--cinnabar:#B5453A;--line:rgba(43,76,126,.16)}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:"Noto Serif SC","Songti SC",serif;line-height:1.9}
a{color:inherit}
nav{position:sticky;top:0;z-index:20;background:rgba(244,242,236,.94);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
nav .w{max-width:1000px;margin:auto;padding:13px 24px;display:flex;justify-content:space-between;align-items:center;font-size:14px}
nav a{color:var(--indigo);text-decoration:none}
.hero{max-width:860px;margin:auto;padding:76px 24px 22px;text-align:center}
.hero .eyebrow{font-size:12px;letter-spacing:.42em;color:var(--cinnabar);margin-bottom:20px}
.hero h1{font-size:clamp(36px,6vw,58px);line-height:1.16;margin:0 0 20px;letter-spacing:.03em}
.hero .lead{font-size:17px;color:var(--ink2);line-height:2;max-width:700px;margin:0 auto;text-align:justify}
.hero .rule{width:64px;height:2px;background:var(--cinnabar);margin:30px auto 0;opacity:.75}
.how{max-width:900px;margin:44px auto 0;padding:0 24px}
.how-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.how-cell{background:var(--card);border:1px solid var(--line);border-top:3px solid var(--indigo);border-radius:8px;padding:16px 16px}
.how-cell .n{font-size:11px;letter-spacing:.28em;color:var(--cinnabar);font-weight:700}
.how-cell .t{font-size:15.5px;font-weight:700;margin:7px 0 5px}
.how-cell .d{font-size:13px;color:var(--ink2);line-height:1.75}
.wrap{max-width:900px;margin:auto;padding:38px 24px 80px}
.card{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--cinnabar);border-radius:10px;
padding:26px 30px;margin:0 0 20px;display:block;text-decoration:none;transition:transform .15s,box-shadow .15s}
.card:hover{transform:translateY(-2px);box-shadow:0 10px 30px rgba(43,76,126,.10)}
.card .no{font-size:11.5px;letter-spacing:.3em;color:var(--cinnabar);font-weight:700}
.card h2{font-size:23px;line-height:1.44;margin:9px 0 8px}
.card .sub{font-size:14.5px;color:var(--ink2);line-height:1.8;margin:0 0 12px}
.card .hook{font-size:14.5px;color:var(--ink);line-height:1.9;text-align:justify;margin:0 0 14px}
.card .meta{font-size:12.5px;color:var(--ink2);letter-spacing:.05em}
.srcline{background:rgba(43,76,126,.05);border:1px dashed rgba(43,76,126,.3);border-radius:7px;padding:13px 16px;margin:0 0 14px}
.srcline .lb{font-size:11.5px;letter-spacing:.26em;color:var(--cinnabar);font-weight:700}
.srcline ul{margin:8px 0 0;padding-left:1.15em}
.srcline li{font-size:13.5px;line-height:1.7;margin:0 0 4px}
.srcline li a{color:var(--indigo);text-decoration:none;border-bottom:1px solid rgba(43,76,126,.35)}
.srcline li a:hover{color:var(--cinnabar)}
.srcline li em{font-style:normal;color:var(--ink2);font-size:12.5px}
.note{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:22px 26px;margin:30px 0 0;
font-size:14px;color:var(--ink2);line-height:1.9}
.note b{color:var(--indigo)}
footer{text-align:center;border-top:1px solid var(--line);padding:30px;color:var(--ink2);font-size:12.5px}
footer a{color:var(--indigo);text-decoration:none}
@media(max-width:760px){.how-grid{grid-template-columns:1fr 1fr}.card{padding:20px 20px}}
"""

HOW = [
    ("壹", "选三篇", "从学员专栏里挑三篇领域互不重叠、观点互相矛盾的高智商长文——必须是打架，不是互补。"),
    ("贰", "各出三个金点子", "每篇压出三个不可再退的判断，共九个。金点子之间彼此独立，空隙才是新东西的发生地。"),
    ("叁", "两两相撞", "九个点子做三十六次碰撞，无焦点的作废。撞出的必须是新结构，不是原判断的换皮。"),
    ("肆", "涌现成典范", "有效涌现物自组织成几条暗流，暗流的交点上长出一个三篇里谁都没有的判断，再单独写成一篇。"),
]


def render_column(papers):
    cards = ""
    for p in papers:
        srcs = "".join(
            f'<li><a href="{s["u"]}">{esc(s["t"])}</a>　<em>{esc(s["d"])}</em></li>'
            for s in p["sources"])
        cards += f"""<a class="card" href="/paradigm/{p['slug']}/">
  <div class="no">典范文 · 之{p['no']}</div>
  <h2>{esc(p['title'])}</h2>
  <div class="sub">{esc(p['subtitle'])}</div>
  <div class="srcline"><span class="lb">由这三篇碰撞而成</span>
    <ul>{srcs}</ul></div>
  <p class="hook">{esc(p['hook'])}</p>
  <div class="meta">作者 {AUTHOR} · 约 {p['wan']} 万字 · {p['pages']} 页 · 三种读法 · 发表于{PUBDATE_CN}</div>
</a>
"""
    hows = "".join(
        f'<div class="how-cell"><div class="n">{n}</div><div class="t">{t}</div><div class="d">{d}</div></div>'
        for n, t, d in HOW)
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>典范文专栏 · Paradigm Essays | SDE Universes</title>
<meta name="description" content="典范文＝从学员专栏挑三篇领域不同、观点互相矛盾的长文，各压三个金点子，九点子两两相撞，涌现出一个三篇里谁都没有的新典范，再单独写成一篇。作者 Claude。">
<link rel="canonical" href="https://sdeuniverses.com/paradigm/">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;700&display=swap">
<style>{COLUMN_CSS}</style></head>
<body>
<nav><div class="w"><a href="/">‹ 返回首页</a><span style="color:var(--cinnabar);letter-spacing:.3em;font-size:12px">典 范 文 专 栏</span><a href="/students/">学员专栏 ›</a></div></nav>

<div class="hero">
  <div class="eyebrow">典 范 文 专 栏 · PARADIGM ESSAYS</div>
  <h1>典范文专栏</h1>
  <p class="lead">这个栏目里的每一篇，都不是从一个题目写出来的，而是从<b>三篇文章的互相矛盾</b>里撞出来的。
  做法是固定的：在学员专栏里挑三篇领域互不重叠、观点正面打架的长文，各压出三个不可再退的判断，
  让这九个判断两两相撞三十六次，把撞出的新结构聚成几条暗流——最后在暗流的交点上，
  会长出一个三篇里谁都没有、也无法从任何一篇单独推出的判断。那个判断，就是一篇典范文的全部起点。</p>
  <div class="rule"></div>
</div>

<div class="how"><div class="how-grid">{hows}</div></div>

<div class="wrap">
{cards}
<div class="note"><b>关于作者。</b>本栏文章署名 Claude —— 碰撞、涌现与成文由 Claude 完成；
被碰撞的原材料全部来自<a href="/students/">学员专栏</a>里学员自己写的长文，每篇的三个来源都在上面列明并可点开。
典范文不复述那三篇，它只写那个三篇里谁都没有说过的判断；原文里的每一个论点，仍然属于它们各自的作者。</div>
</div>

<footer>© 德麦国际 Demai International · 典范文专栏 · <a href="/">sdeuniverses.com</a></footer>
<script src="/wds-mode.js" defer></script>
</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--only")
    a = ap.parse_args()
    src = Path(a.src)
    COL.mkdir(parents=True, exist_ok=True)

    for p in PAPERS:
        if a.only and p["slug"] != a.only:
            continue
        lines = load(src, p["src"])
        abstract, keywords, blocks = parse(p, lines)
        assert abstract, (p["slug"], "缺导语")
        body_chars = sum(len(l) for _, l in blocks) + len(abstract)
        p["wan"] = f"{body_chars/10000:.1f}"

        d = COL / p["slug"]
        d.mkdir(exist_ok=True)
        # PDF
        tmp = d / "_print.html"
        tmp.write_text(render_print(p, abstract, keywords, blocks), encoding="utf-8")
        pdf = d / f"{p['slug']}.pdf"
        subprocess.run(["wkhtmltopdf", "--enable-local-file-access",
                        "--margin-top", "17mm", "--margin-bottom", "17mm",
                        "--margin-left", "18mm", "--margin-right", "18mm",
                        "--footer-center", "[page]", "--footer-font-size", "8",
                        str(tmp), str(pdf)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        tmp.unlink()
        info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
        pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
        assert pages > 0
        txt = subprocess.run(["pdftotext", "-f", "1", "-l", "1", str(pdf), "-"],
                             capture_output=True, text=True).stdout
        assert re.search(r"[\u4e00-\u9fff]", txt), "PDF 首页抽不出中文"
        p["pages"] = pages

        (d / "index.html").write_text(render_page(p, abstract, keywords, blocks), encoding="utf-8")
        (d / "read.html").write_text(
            READ_TPL.format(title=p["title"], pages=pages, author=AUTHOR,
                            pdf=f"{p['slug']}.pdf"), encoding="utf-8")
        print(f"✓ {p['slug']}：{body_chars} 字 / {pages} 页 / PDF {pdf.stat().st_size//1024}KB")

    print("· 栏目页未改动（/paradigm/index.html 由 publish_paradigm.py 与人工维护）")


if __name__ == "__main__":
    main()
