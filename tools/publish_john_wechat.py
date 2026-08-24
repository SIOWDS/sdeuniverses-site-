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
import json, os, html, math, re
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

CSS = """
:root{
  --paper:#F2F1ED; --card:#FBFAF7; --ink:#171A22; --ink2:#5C6272; --ink3:#868C9B;
  --line:#CBCCD4; --line2:#E2E1DE;
  --indigo:#1F3A5F; --vermilion:#A63A2B;
  --night:#0B0E14; --night2:#121722; --bone:#E8E4DA; --bone2:#8E94A3;
  --edge:rgba(232,228,218,.16); --indigo-l:#6E9BD8; --vermilion-l:#D2604A;
  --accent:#1F3A5F;
  --serif:"Songti SC","Source Han Serif SC","Noto Serif CJK SC","SimSun",serif;
  --sans:"PingFang SC","Hiragino Sans GB","Microsoft YaHei",system-ui,sans-serif;
  --mono:ui-monospace,"SFMono-Regular",Menlo,Consolas,"Courier New",monospace;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-behavior:smooth}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);
  font-size:16px;line-height:1.75}
a{color:inherit;text-decoration:none}
.wrap{max-width:1000px;margin:0 auto;padding:0 22px}

.dark{background:var(--night);color:var(--bone);position:relative;overflow:hidden}
.dark::before{content:"";position:absolute;inset:0;pointer-events:none;
  background:
    radial-gradient(56% 44% at 10% 0%,rgba(110,155,216,.13),transparent 70%),
    radial-gradient(44% 40% at 94% 18%,rgba(210,96,74,.10),transparent 72%),
    radial-gradient(72% 52% at 52% 104%,rgba(111,169,140,.07),transparent 70%)}
.dark::after{content:"";position:absolute;inset:0;pointer-events:none;opacity:.45;
  background-image:linear-gradient(90deg,rgba(232,228,218,.05) 1px,transparent 1px);
  background-size:34px 100%}
.dark .wrap{position:relative;z-index:1}

.top{border-bottom:1px solid var(--edge);position:sticky;top:0;z-index:40;
  background:rgba(11,14,20,.88);backdrop-filter:saturate(140%) blur(8px)}
.top .wrap{display:flex;align-items:baseline;gap:18px;height:58px}
.brand{font-family:var(--serif);font-size:19.5px;letter-spacing:.14em;color:var(--bone);flex:none}
.brand em{font-style:normal;color:var(--bone2);font-size:11.5px;letter-spacing:.26em;margin-left:10px}
.top nav{margin-left:auto;display:flex;gap:19px;font-size:13.5px;color:var(--bone2);
  overflow-x:auto;white-space:nowrap;scrollbar-width:none}
.top nav::-webkit-scrollbar{display:none}
.top nav a:hover{color:var(--indigo-l)}
.top nav a[aria-current]{color:var(--bone);box-shadow:inset 0 -1px 0 var(--vermilion-l)}
.top nav a.out{font-family:var(--mono);font-size:11.5px}

.hero{padding:70px 0 58px}
.hero.tight{padding:44px 0 42px}
.crumb{font-family:var(--mono);font-size:11px;letter-spacing:.2em;color:var(--bone2);margin-bottom:16px}
.crumb a{color:var(--indigo-l)}
.crumb a:hover{color:var(--bone)}
.eyebrow{font-family:var(--mono);font-size:11.5px;letter-spacing:.24em;color:var(--indigo-l);text-transform:uppercase}
.dark h1{font-family:var(--serif);font-weight:600;font-size:clamp(30px,5.4vw,52px);line-height:1.26;
  letter-spacing:.03em;margin:.5em 0 .4em;max-width:15em;color:#F4F2EC}
.dark h1 em{font-style:normal;color:var(--vermilion-l)}
.lede{max-width:38em;color:#B9BECB;font-size:16.5px;margin:0}
.lede b{color:var(--bone);font-weight:600}
.lede + .lede{margin-top:.9em}

.rhythm{margin:42px 0 0;border:1px solid var(--edge);background:var(--night2)}
.rhythm .cap{display:flex;justify-content:space-between;align-items:baseline;gap:14px;flex-wrap:nowrap;
  padding:13px 20px;border-bottom:1px solid rgba(232,228,218,.28);
  font-family:var(--serif);letter-spacing:.22em;font-size:14.5px;color:#F4F2EC}
.rhythm .cap span{font-family:var(--mono);font-size:11px;color:var(--bone2);letter-spacing:.06em;
  text-align:right;letter-spacing:.06em}
.bars{display:flex;align-items:flex-end;gap:2px;height:116px;padding:20px 20px 0}
.bars .b{flex:1 1 0;min-width:2px;display:flex;flex-direction:column;justify-content:flex-end;height:100%}
.bars .b i,.bars .b u{display:block;width:100%;transform-origin:bottom;text-decoration:none;
  animation:grow .55s cubic-bezier(.2,.7,.3,1) both}
.bars .b i{background:rgba(232,228,218,.13)}
.bars .b u{background:var(--indigo-l)}
.bars .b.hot u{background:var(--vermilion-l)}
.bars .b:hover i,.bars .b:hover u{filter:brightness(1.45)}
@keyframes grow{from{transform:scaleY(.05);opacity:.15}to{transform:scaleY(1);opacity:1}}
.axis{display:flex;padding:0 20px 14px;margin-top:9px;border-top:1px solid var(--edge)}
.axis span{flex:1 1 0;font-family:var(--mono);font-size:10.5px;letter-spacing:.08em;color:var(--bone2);
  padding-top:8px;border-left:1px solid var(--edge);padding-left:7px;overflow:hidden}
.axis span b,.axis span em{display:block;white-space:nowrap;font-style:normal}
.axis span em{font-size:9.5px;opacity:.85;margin-top:1px}
.axis span:first-child{border-left:0;padding-left:0}
.axis span b{color:#C8CCD6;font-weight:400}
.rnote{padding:0 20px 18px;margin:0;font-size:12.5px;color:var(--bone2);line-height:1.75;max-width:60em}
.rnote b{color:#C8CCD6;font-weight:500}

.band{display:flex;flex-wrap:wrap;gap:0;margin:26px 0 0;border:1px solid var(--edge)}
.band div{flex:1 1 128px;padding:15px 18px;border-right:1px solid var(--edge)}
.band div:last-child{border-right:0}
.band b{display:block;font-family:var(--mono);font-size:22px;color:#F4F2EC;
  font-variant-numeric:tabular-nums;letter-spacing:.02em;line-height:1.3}
.band span{font-size:12.5px;color:var(--bone2)}
.acts{display:flex;flex-wrap:wrap;gap:12px;margin:30px 0 0}
.acts a,.acts button{font:inherit;font-size:14px;color:var(--bone);border:1px solid var(--edge);
  background:transparent;padding:9px 18px;cursor:pointer;transition:border-color .2s,color .2s,background .2s}
.acts a:hover,.acts button:hover{border-color:var(--indigo-l);color:#F4F2EC}
.acts .primary{background:var(--vermilion);border-color:var(--vermilion);color:#FBF7F2}
.acts .primary:hover{background:var(--vermilion-l);border-color:var(--vermilion-l);color:#fff}

.light{background:var(--paper);
  background-image:linear-gradient(90deg,var(--line2) 1px,transparent 1px);
  background-size:34px 100%;background-position:-1px 0}
section{padding:52px 0 6px}
.col-h{display:flex;align-items:baseline;gap:14px;border-bottom:2px solid var(--ink);padding-bottom:9px}
.col-h .no{font-family:var(--serif);font-size:13px;letter-spacing:.24em;color:var(--vermilion);flex:none}
.col-h h2{font-family:var(--serif);font-weight:600;font-size:22px;letter-spacing:.1em;margin:0}
.col-h .ct{margin-left:auto;font-family:var(--mono);font-size:12px;color:var(--ink2);
  font-variant-numeric:tabular-nums;flex:none;padding-left:10px}
.col-d{color:var(--ink2);font-size:14.5px;margin:13px 0 4px;max-width:46em}

.chs{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:0;
  border:1px solid var(--line);border-right:0;border-bottom:0;margin-top:20px;background:var(--card)}
.ch{display:flex;flex-direction:column;padding:0 0 20px;border-right:1px solid var(--line);
  border-bottom:1px solid var(--line);transition:background .22s}
.ch:hover{background:#fff}
.ch .rule{height:3px;background:var(--cc)}
.ch .in{padding:19px 22px 0;flex:1;display:flex;flex-direction:column}
.ch .foot{margin-top:auto}
.ch .n{font-family:var(--serif);font-size:12px;letter-spacing:.3em;color:var(--cc)}
.ch h3{font-family:var(--serif);font-weight:600;font-size:20px;letter-spacing:.1em;margin:8px 0 9px}
.ch:hover h3{color:var(--cc)}
.ch p{margin:0;font-size:13.5px;color:var(--ink2);line-height:1.72}
.spark{display:flex;align-items:flex-end;gap:3px;height:26px;margin:16px 0 0}
.spark i{flex:1 1 0;background:var(--cc);opacity:.26;min-height:1px}
.spark i.pk{opacity:.85}
.spark-x{display:flex;gap:3px;margin-top:5px;font-family:var(--mono);font-size:9.5px;color:var(--ink3);
  letter-spacing:.06em}
.spark-x i{flex:1 1 0;font-style:normal;text-align:center}
.ch .picks{margin:15px 0 0;padding-top:12px;border-top:1px dashed var(--line);
  font-size:13px;color:var(--ink2);line-height:1.7}
.ch .picks em{font-style:normal;color:var(--ink);display:block}
.ch .picks em::before{content:"— ";color:var(--cc)}
.ch .ct{margin-top:14px;font-family:var(--mono);font-size:11.5px;color:var(--ink3);
  font-variant-numeric:tabular-nums;display:flex;gap:14px}
.ch .ct b{color:var(--cc);font-weight:600;font-size:13px}
.ch .go{margin-top:12px;font-family:var(--mono);font-size:11.5px;color:var(--cc);opacity:0;
  transform:translateX(-4px);transition:opacity .22s,transform .22s}
.ch:hover .go,.ch:focus-visible .go{opacity:1;transform:none}

.chips{position:sticky;top:0;z-index:30;background:rgba(242,241,237,.95);
  backdrop-filter:saturate(140%) blur(6px);border-bottom:1px solid var(--line)}
.chips .wrap{display:flex;gap:0;overflow-x:auto;scrollbar-width:none;padding:0 22px;
  -webkit-mask-image:linear-gradient(to right,#000 92%,transparent);
  mask-image:linear-gradient(to right,#000 92%,transparent)}
.chips .wrap::-webkit-scrollbar{display:none}
.chips a{flex:none;padding:12px 15px;font-size:13.5px;color:var(--ink2);white-space:nowrap;
  border-bottom:2px solid transparent;transition:color .2s,border-color .2s}
.chips a:hover{color:var(--ink)}
.chips a[aria-current]{color:var(--ink);border-bottom-color:var(--accent);font-weight:600}
.chips a b{font-family:var(--mono);font-size:11px;color:var(--ink3);font-weight:400;margin-left:5px;
  font-variant-numeric:tabular-nums}

.tools{padding:30px 0 0}
.list{padding-top:10px}
.filter{display:flex;gap:12px;align-items:center;
  border:1px solid var(--line);background:var(--card);padding:11px 15px}
.filter input{flex:1;border:0;background:transparent;font:inherit;font-size:15px;color:var(--ink);outline:none}
.filter label{font-family:var(--mono);font-size:11.5px;letter-spacing:.16em;color:var(--ink2);flex:none}
.filter .n{font-family:var(--mono);font-size:12px;color:var(--accent);font-variant-numeric:tabular-nums;flex:none}
.chipy{display:flex;flex-wrap:wrap;gap:7px;margin:12px 0 0}
.chipy button,.chipy a{font:inherit;font-family:var(--mono);font-size:11.5px;letter-spacing:.08em;
  color:var(--ink2);background:var(--card);border:1px solid var(--line);padding:4px 11px;cursor:pointer;
  transition:border-color .18s,color .18s,background .18s}
.chipy button:hover,.chipy a:hover{border-color:var(--cc,var(--accent));color:var(--cc,var(--accent))}
.chipy button[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:#FBF7F2}
.empty{padding:24px 4px;color:var(--ink2);font-size:14.5px}
.empty a{color:var(--accent);border-bottom:1px solid var(--line)}

.yr{display:flex;align-items:baseline;gap:12px;margin:34px 0 2px;padding-bottom:6px}
.yr b{font-family:var(--mono);font-size:19px;letter-spacing:.06em;color:var(--accent);
  font-variant-numeric:tabular-nums;font-weight:500}
.yr span{font-family:var(--mono);font-size:11px;color:var(--ink3);letter-spacing:.12em}
.yr i{flex:1;height:1px;background:var(--line);font-style:normal}
.item{border-bottom:1px dashed var(--line);padding:15px 4px 14px;position:relative;transition:background .18s}
.item::before{content:"";position:absolute;left:-12px;top:15px;bottom:14px;width:2px;
  background:var(--accent);opacity:0;transition:opacity .18s}
.item:hover{background:var(--card)}
.item:hover::before{opacity:.75}
.it-hd{display:flex;gap:13px;align-items:baseline}
.r-n{font-family:var(--mono);font-size:11px;color:var(--ink3);min-width:3.2em;
  font-variant-numeric:tabular-nums;flex:none;letter-spacing:.06em}
.it-t{font-size:15.5px;line-height:1.62;font-family:var(--serif);font-weight:600;letter-spacing:.02em}
.item:hover .it-t{color:var(--accent)}
.it-m{margin-left:auto;flex:none;font-family:var(--mono);font-size:11px;color:var(--ink3);
  font-variant-numeric:tabular-nums;padding-left:12px;white-space:nowrap}
.it-d{margin:7px 0 0 4.3em;font-size:13.5px;color:var(--ink2);line-height:1.72}
.it-l{margin:8px 0 0 4.3em;display:flex;gap:15px;font-family:var(--mono);font-size:11px;flex-wrap:wrap;
  letter-spacing:.06em}
.it-l a{color:var(--accent);border-bottom:1px solid var(--line);padding-bottom:1px}
.it-l a:hover{border-color:var(--accent)}
.it-l span{color:var(--ink3)}

.note{background:var(--card);border:1px solid var(--line);padding:24px 26px;margin-top:36px}
.note h3{font-family:var(--serif);font-size:17.5px;letter-spacing:.1em;margin:0 0 12px;font-weight:600}
.note p{margin:0 0 12px;font-size:14.5px;color:var(--ink2)}
.note p:last-child{margin-bottom:0}
.note b{color:var(--ink)}
.note a{color:var(--indigo);border-bottom:1px solid var(--line)}
.nearby{display:flex;flex-wrap:wrap;gap:0;margin:46px 0 0;border:1px solid var(--line);background:var(--card)}
.nearby a{flex:1 1 210px;padding:17px 20px;border-right:1px solid var(--line);font-size:13.5px;
  color:var(--ink2);transition:background .2s,color .2s}
.nearby a:last-child{border-right:0}
.nearby a:hover{background:#fff;color:var(--ink)}
.nearby a small{display:block;font-family:var(--mono);font-size:10.5px;letter-spacing:.16em;
  color:var(--ink3);margin-bottom:5px}
.nearby a b{display:block;font-family:var(--serif);font-size:16.5px;letter-spacing:.08em;
  font-weight:600;color:var(--ink);margin-bottom:3px}

footer{margin-top:74px;border-top:1px solid var(--line);padding:28px 0 66px;
  font-size:13px;color:var(--ink2)}
footer a{color:var(--indigo);border-bottom:1px solid var(--line)}
footer p{margin:0 0 8px}
a:focus-visible,input:focus-visible,button:focus-visible{outline:2px solid var(--vermilion);outline-offset:2px}
@media(max-width:700px){
  .hero{padding:40px 0 34px}
  .hero.tight{padding:32px 0 30px}
  .top nav{-webkit-mask-image:linear-gradient(to right,#000 86%,transparent);
    mask-image:linear-gradient(to right,#000 86%,transparent)}
  .rhythm .cap{flex-wrap:wrap;letter-spacing:.14em;font-size:13.5px}
  .rhythm .cap span{text-align:left;flex:1 1 100%}
  .bars{height:82px;padding:16px 14px 0}
  .axis{padding:0 14px 12px}
  .axis span{font-size:9px;padding-left:4px;min-width:32px;letter-spacing:0}
  .axis span em{font-size:8.5px}
  .rnote{padding:0 14px 15px}
  .band div{flex:1 1 45%}
  .it-m{display:none}
  .it-d,.it-l{margin-left:0}
  .item::before{left:-8px}
  .chips a{padding:11px 12px;font-size:13px}
  .nearby a{flex:1 1 100%;border-right:0;border-bottom:1px solid var(--line)}
  .nearby a:last-child{border-bottom:0}
}
@media(prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  .bars .b i,.bars .b u{animation:none}
  *{transition:none!important}
}
"""

FILTER_JS = """<script>
(function(){
  var q=document.getElementById("q"),n=document.getElementById("n"),
      empty=document.getElementById("empty"),
      items=[].slice.call(document.querySelectorAll(".item")),
      groups=[].slice.call(document.querySelectorAll("[data-group]")),
      ybtns=[].slice.call(document.querySelectorAll(".chipy button[data-year]")),
      year=null;
  if(!q&&!ybtns.length)return;
  var keys=items.map(function(el){return (el.getAttribute("data-k")||"").toLowerCase();}),
      years=items.map(function(el){return el.getAttribute("data-y")||"";});
  function run(){
    var v=q?q.value.trim().toLowerCase():"",c=0;
    for(var i=0;i<items.length;i++){
      var hit=(!v||keys[i].indexOf(v)>=0)&&(year===null||years[i]===year);
      items[i].style.display=hit?"":"none";
      if(hit)c++;
    }
    for(var j=0;j<groups.length;j++){
      var any=groups[j].querySelector('.item:not([style*="none"])');
      groups[j].style.display=any?"":"none";
    }
    if(n)n.textContent=c+" / "+items.length;
    if(empty)empty.style.display=c?"none":"";
  }
  if(q)q.addEventListener("input",run);
  ybtns.forEach(function(b){
    b.addEventListener("click",function(){
      var y=b.getAttribute("data-year");
      year=(year===y)?null:y;
      ybtns.forEach(function(o){
        o.setAttribute("aria-pressed",String(year!==null&&o.getAttribute("data-year")===year));
      });
      run();
    });
  });
  run();
})();
</script>"""

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

PREFIX_FIX = """<script>
/* 分站页面的自家链接写的是分站根。在二级域名下这就是对的；
   若从主站以 /sites/lang/… 预览，就地补前缀，两处都能点。 */
(function(){window.__wechatBase="";var b="/sites/lang";
if(location.pathname.indexOf(b)!==0)return;
window.__wechatBase=b;
var own=["/#","/all/","/wechat","/chatjohn/"];
var as=document.querySelectorAll("a[href]");
for(var i=0;i<as.length;i++){var h=as[i].getAttribute("href");
if(h==="/"){as[i].setAttribute("href",b+"/");continue;}
for(var k=0;k<own.length;k++){if(h.indexOf(own[k])===0){as[i].setAttribute("href",b+h);break;}}}})();
</script>"""

FOOTER = """<footer><div class="wrap">
  <p>约翰专栏 —— 胡志英（约翰老师）公众号「五宝爸约翰聊英语」原文存档，共 418 篇。原文一字未改，本站只做归类、排序与检索。</p>
  <p>语言发生学 · <a href="https://sdeuniverses.com/">SDE Universes</a> 的语言分站 —— 德麦国际 · Demai International Press</p>
</div></footer>"""


def esc(s):
    return html.escape(str(s), quote=True)


def nav():
    return ('<header class="top"><div class="wrap">\n'
            '  <a class="brand" href="/">语言发生学<em>HU ZHIYING</em></a>\n'
            '  <nav>\n'
            '    <a href="/#books">账册</a>\n'
            '    <a href="/#cols">栏目</a>\n'
            '    <a href="/all/">全部篇目</a>\n'
            '    <a href="/wechat/" aria-current="page">约翰专栏</a>\n'
            '    <a href="/chatjohn/">ChatJohn</a>\n'
            '    <a class="out" href="https://sdeuniverses.com/">SDE Universes ↗</a>\n'
            '  </nav>\n</div></header>')


def page(title, desc, canon, body, accent="#1F3A5F", extra=""):
    return """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title>
<meta name="description" content="%s">
<link rel="canonical" href="%s">
<meta property="og:title" content="%s">
<meta property="og:description" content="%s">
<meta property="og:type" content="website">
<meta name="theme-color" content="#0B0E14">
<style>%s</style>
<style>:root{--accent:%s}</style>
</head>
<body>
%s
%s
%s
%s
</body></html>
""" % (esc(title), esc(desc), esc(canon), esc(title), esc(desc), CSS, accent,
       body, FOOTER, PREFIX_FIX, extra)


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
</div></div>""" % (nav(), "{:,}".format(total_pages), bars, yrs, gmonth[hot],
                   len(arts) - n_dated, "{:,}".format(total_pages), span,
                   len(canon), cards, n_dated)

    pool = json.dumps([a["num"] for a in canon])
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(
        page("约翰专栏 · 语言发生学",
             "胡志英（约翰老师）公众号原文存档 418 篇，分九个频道：语言发生学、英语启蒙、词汇之路、素材与分级、AI 与语言教育、课堂与制度、思想谱系、奶爸手记、营地与公告。",
             "https://lang.sdeuniverses.com/wechat/", hub, "#1F3A5F", RANDOM_JS % pool))

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
</div></div>""" % (nav(), no, esc(name), esc(blurb), cbars, cyrs,
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
                 body, cc, FILTER_JS))

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
%s</div></div>""" % (nav(), len(canon), ychips, jump, secs)

    d = os.path.join(OUT, "all")
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(
        page("全部篇目 · 约翰专栏 · 语言发生学",
             "胡志英公众号原文存档全部 %d 篇正稿，九栏排列，可按词与年份即时筛选。" % len(canon),
             "https://lang.sdeuniverses.com/wechat/all/",
             all_body, "#1F3A5F", FILTER_JS))

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
