# -*- coding: utf-8 -*-
"""学科通融各篇的翻页阅读器。

替换掉原先的裸 iframe（用浏览器自带的 PDF 控件，样式不可控、移动端体验差）。
本阅读器用 PDF.js 自行渲染，因而外观完全可控，且在手机上也能正常翻页。

要点：
  · 单页／双页跨页自动切换（宽屏跨页，窄屏单页）
  · 键盘 ← → PageUp/PageDown 翻页，Home/End 首末页
  · 移动端左右滑动翻页
  · 顶部细进度条 + 页码跳转框
  · 高分屏按 devicePixelRatio 渲染，不糊
  · 渲染失败时回退到 iframe，不至于白屏

用法： python3 tools/build_reader_confluence.py [--all | <slug>]
"""
import argparse
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CF = ROOT / "public" / "confluence"
PDFJS = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174"

TPL = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{title} · 翻页阅读 · 学科通融</title>
<meta name="description" content="{desc}">
<style>
:root{{--ink:#14161A;--ink2:#5A626C;--olive:#5B7247;--olive2:#7E9A55;
--bg:#171A16;--bg2:#1F241D;--paper:#FFF;--line:rgba(126,154,85,.28)}}
*{{box-sizing:border-box}}
html,body{{margin:0;height:100%;background:var(--bg);overflow:hidden;
font-family:"Noto Sans CJK SC","PingFang SC","Hiragino Sans GB",sans-serif}}
#bar{{position:fixed;top:0;left:0;right:0;height:54px;z-index:20;
background:rgba(31,36,29,.94);backdrop-filter:blur(12px);
border-bottom:1px solid var(--line);display:flex;align-items:center;
justify-content:space-between;padding:0 14px;gap:10px;color:#E8E9E1;font-size:13.5px}}
#bar a{{color:var(--olive2);text-decoration:none;white-space:nowrap}}
#bar a:hover{{color:#A8C077}}
.grp{{display:flex;align-items:center;gap:8px;min-width:0}}
.ttl{{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
color:#CFD3C4;font-size:13px;max-width:38vw}}
.btn{{border:1px solid var(--line);background:transparent;color:#D8DCCB;
border-radius:6px;padding:5px 11px;font-size:13px;cursor:pointer;line-height:1.4}}
.btn:hover{{border-color:var(--olive2);color:#fff}}
.btn:disabled{{opacity:.32;cursor:default}}
#pg{{width:44px;text-align:center;background:transparent;border:1px solid var(--line);
color:#E8E9E1;border-radius:6px;padding:5px 2px;font-size:13px}}
#prog{{position:fixed;top:54px;left:0;height:2px;background:var(--olive2);z-index:21;
width:0;transition:width .18s}}
#stage{{position:absolute;top:54px;bottom:0;left:0;right:0;overflow:auto;
display:flex;align-items:flex-start;justify-content:center;
padding:26px 16px 40px;-webkit-overflow-scrolling:touch}}
#spread{{display:flex;gap:18px;align-items:flex-start}}
canvas{{background:var(--paper);border-radius:2px;
box-shadow:0 2px 8px rgba(0,0,0,.34),0 18px 46px rgba(0,0,0,.44);
max-width:100%;height:auto;display:block}}
#hint{{position:fixed;bottom:14px;left:50%;transform:translateX(-50%);
color:#8F978A;font-size:11.5px;letter-spacing:.06em;z-index:10;
background:rgba(23,26,22,.7);padding:5px 13px;border-radius:14px;
opacity:0;transition:opacity .5s}}
#hint.on{{opacity:1}}
#fb{{display:none;width:100%;height:calc(100% - 54px);border:0;position:absolute;top:54px}}
@media(max-width:640px){{
  .ttl{{display:none}} #bar{{padding:0 10px;gap:6px}}
  #stage{{padding:14px 8px 30px}} .btn{{padding:5px 9px}}
}}
</style></head>
<body>
<div id="bar">
  <div class="grp"><a href="index.html">‹ 网页长文</a>
  <span class="ttl">{title}</span></div>
  <div class="grp">
    <button class="btn" id="prev">‹</button>
    <input id="pg" value="1" inputmode="numeric"><span style="color:#8F978A">/ <b id="tot">–</b></span>
    <button class="btn" id="next">›</button>
    <button class="btn" id="two" title="单页／跨页">跨页</button>
    <a class="btn" href="{slug}.pdf" download style="display:inline-block">⬇</a>
  </div>
</div>
<div id="prog"></div>
<div id="stage"><div id="spread"></div></div>
<iframe id="fb" src="{slug}.pdf#view=FitH"></iframe>
<div id="hint">← → 翻页　·　手机可左右滑动</div>
<script src="{pdfjs}/pdf.min.js"></script>
<script>
(function(){{
  var URL_="{slug}.pdf", doc=null, cur=1, tot=0, two=false, busy=false;
  var stage=document.getElementById('stage'), spread=document.getElementById('spread');
  var elPg=document.getElementById('pg'), elTot=document.getElementById('tot');
  var elPrev=document.getElementById('prev'), elNext=document.getElementById('next');
  var elTwo=document.getElementById('two'), elProg=document.getElementById('prog');

  function fallback(){{
    document.getElementById('stage').style.display='none';
    document.getElementById('fb').style.display='block';
  }}
  if(!window.pdfjsLib){{ fallback(); return; }}
  pdfjsLib.GlobalWorkerOptions.workerSrc="{pdfjs}/pdf.worker.min.js";

  function fitScale(page){{
    var vp=page.getViewport({{scale:1}});
    var gap=two?18:0, cols=two?2:1;
    var availW=(stage.clientWidth-32-gap)/cols;
    var availH=stage.clientHeight-56;
    return Math.min(availW/vp.width, availH/vp.height);
  }}

  function drawOne(n){{
    return doc.getPage(n).then(function(page){{
      var dpr=Math.min(window.devicePixelRatio||1, 2.5);
      var s=fitScale(page), vp=page.getViewport({{scale:s*dpr}});
      var c=document.createElement('canvas');
      c.width=vp.width; c.height=vp.height;
      c.style.width=(vp.width/dpr)+'px'; c.style.height=(vp.height/dpr)+'px';
      return page.render({{canvasContext:c.getContext('2d'),viewport:vp}}).promise
        .then(function(){{ return c; }});
    }});
  }}

  function render(){{
    if(busy||!doc) return; busy=true;
    var ns=[cur]; if(two && cur+1<=tot) ns.push(cur+1);
    Promise.all(ns.map(drawOne)).then(function(cs){{
      spread.innerHTML=''; cs.forEach(function(c){{ spread.appendChild(c); }});
      elPg.value=cur; stage.scrollTop=0;
      elProg.style.width=(cur/tot*100)+'%';
      elPrev.disabled=(cur<=1); elNext.disabled=(cur>=tot);
      busy=false;
    }}).catch(function(){{ busy=false; fallback(); }});
  }}

  function go(n){{ n=Math.max(1,Math.min(tot,n)); if(n!==cur){{ cur=n; render(); }} }}
  var step=function(){{ return two?2:1; }};

  elPrev.onclick=function(){{ go(cur-step()); }};
  elNext.onclick=function(){{ go(cur+step()); }};
  elTwo.onclick=function(){{
    two=!two; elTwo.textContent=two?'单页':'跨页';
    if(two && cur%2===0) cur=Math.max(1,cur-1);
    render();
  }};
  elPg.addEventListener('change',function(){{ go(parseInt(elPg.value,10)||1); }});
  document.addEventListener('keydown',function(e){{
    if(e.target===elPg) return;
    if(e.key==='ArrowRight'||e.key==='PageDown'||e.key===' '){{ e.preventDefault(); go(cur+step()); }}
    else if(e.key==='ArrowLeft'||e.key==='PageUp'){{ e.preventDefault(); go(cur-step()); }}
    else if(e.key==='Home'){{ go(1); }} else if(e.key==='End'){{ go(tot); }}
  }});
  var sx=0,sy=0;
  stage.addEventListener('touchstart',function(e){{ sx=e.touches[0].clientX; sy=e.touches[0].clientY; }},{{passive:true}});
  stage.addEventListener('touchend',function(e){{
    var dx=e.changedTouches[0].clientX-sx, dy=e.changedTouches[0].clientY-sy;
    if(Math.abs(dx)>52 && Math.abs(dx)>Math.abs(dy)*1.6) go(cur+(dx<0?step():-step()));
  }},{{passive:true}});
  var rt; window.addEventListener('resize',function(){{ clearTimeout(rt); rt=setTimeout(render,180); }});

  pdfjsLib.getDocument(URL_).promise.then(function(d){{
    doc=d; tot=d.numPages; elTot.textContent=tot;
    two=(window.innerWidth>=1080);
    elTwo.textContent=two?'单页':'跨页';
    render();
    var h=document.getElementById('hint');
    h.classList.add('on'); setTimeout(function(){{ h.classList.remove('on'); }},3600);
  }}).catch(fallback);
}})();
</script>
</body></html>
"""


def title_of(slug: str) -> tuple:
    t = (CF / slug / "index.html").read_text(encoding="utf-8")
    title = re.search(r'<h1 class="art-title">([^<]*)</h1>', t)
    sub = re.search(r'<div class="art-sub">([^<]*)</div>|<p class="art-sub">([^<]*)</p>', t)
    ti = title.group(1).strip() if title else slug
    sb = ""
    if sub:
        sb = (sub.group(1) or sub.group(2) or "").strip()
    return ti, sb


def build(slug: str):
    ti, sb = title_of(slug)
    desc = f"{ti}——{sb}。学科通融 · 翻页阅读。" if sb else f"{ti}。学科通融 · 翻页阅读。"
    out = TPL.format(title=html.escape(ti), desc=html.escape(desc[:180], quote=True),
                     slug=slug, pdfjs=PDFJS)
    (CF / slug / "read.html").write_text(out, encoding="utf-8")
    return len(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug", nargs="?")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    slugs = ([d.name for d in sorted(CF.iterdir()) if d.is_dir()]
             if a.all else [a.slug])
    for s in slugs:
        n = build(s)
        print(f"  {s:<28s} read.html {n} 字节")


if __name__ == "__main__":
    main()
