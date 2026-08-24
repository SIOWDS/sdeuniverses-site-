#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lang.sdeuniverses.com 分站的共用外观：一套 CSS、一条导航、一个页壳、
两段脚本（筛选、主站预览补前缀）。

由 publish_john_wechat.py（约翰专栏）与 publish_hzy_works.py（作品全集）
共读——样式一处维护，两栏不会走样。
"""
import html

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

.essay{padding:8px 0 0}
.essay section{padding:46px 0 4px}
.essay p{font-size:16.5px;line-height:1.95;margin:18px 0 0;max-width:40em;color:#23262F}
.essay p b{color:var(--ink);font-weight:600;
  background:linear-gradient(transparent 62%,rgba(166,58,43,.16) 62%)}
.essay p a{color:var(--indigo);border-bottom:1px solid var(--line)}
.essay p a:hover{border-color:var(--indigo);background:rgba(31,58,95,.06)}
.essay .col-h .no{font-size:15px;letter-spacing:.3em}
.essay .nearby{margin-top:40px}
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


def esc(s):
    return html.escape(str(s), quote=True)


NAV_ITEMS = [
    ("/#books", "账册", ""),
    ("/#cols", "栏目", ""),
    ("/all/", "全部篇目", "all"),
    ("/works/", "作品全集", "works"),
    ("/wechat/", "约翰专栏", "wechat"),
    ("/chatjohn/", "ChatJohn", "chatjohn"),
]


def nav(current=""):
    out = ('<header class="top"><div class="wrap">\n'
           '  <a class="brand" href="/">语言发生学<em>HU ZHIYING</em></a>\n'
           '  <nav>\n')
    for href, label, key in NAV_ITEMS:
        cur = ' aria-current="page"' if key and key == current else ""
        out += '    <a href="%s"%s>%s</a>\n' % (href, cur, label)
    out += ('    <a class="out" href="https://sdeuniverses.com/">SDE Universes ↗</a>\n'
            '  </nav>\n</div></header>')
    return out


def page(title, desc, canon, body, footer, accent="#1F3A5F", extra=""):
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
       body, footer, PREFIX_FIX, extra)
