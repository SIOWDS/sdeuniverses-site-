# -*- coding: utf-8 -*-
"""apply-* 三模式页 · 网页版(index.html)生成器
产出与站点既定 apply-* 规范一致的实践文网页；PDF 由 build_pdf_from_page.py 从本页生成，
read.html 复用站点翻书器（运行时读 PDF 页数，仅需改标题）。
输入：meta(dict) + body_html(<h2 id><h3><p><div class=sumbox>) → 完整 index.html 字符串。
"""
import re

HEAD_CSS = r''':root{--sky:#4FC3F7;--blue:#2196F3;--link:#0A66B2;--btn:#0A66C2;--teal:#14B8A6;--teal2:#0E7C71;--head:#0F2C4A;--text:#1E293B;--muted:#5A6B80;--bg:#F8FCFF;--card:#FFFFFF;--line:rgba(79,195,247,0.40)}
*{margin:0;padding:0;box-sizing:border-box}
::selection{background:rgba(79,195,247,0.35)}
body{background:var(--bg);color:var(--text);font-family:"Songti SC","Noto Serif SC",Georgia,serif;line-height:2.0;font-size:17.5px}
a{color:var(--link);text-decoration:none}
.readbar{position:sticky;top:0;z-index:20;background:rgba(248,252,255,0.94);backdrop-filter:blur(8px);border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:11px 20px;gap:12px;flex-wrap:wrap}
.readbar .nav-back{color:var(--muted);font-size:13px;letter-spacing:0.04em}
.rb-modes{display:flex;gap:8px;flex-wrap:wrap}
.rb-btn{font-size:13px;padding:6px 14px;border-radius:3px;border:1px solid rgba(33,150,243,0.45);color:var(--link);letter-spacing:0.03em}
.rb-btn.cur{background:var(--btn);color:#fff;font-weight:700;border-color:var(--btn)}
.art{max-width:760px;margin:0 auto;padding:56px 24px 20px;text-align:center}
.art-series{font-size:12px;letter-spacing:0.36em;color:var(--teal2);margin-bottom:22px}
.art-title{font-size:clamp(24px,4.2vw,36px);font-weight:800;line-height:1.55;color:var(--head);letter-spacing:0.02em}
.art-subtitle{font-size:clamp(15px,2.2vw,18px);color:var(--link);margin-top:18px;line-height:1.85;letter-spacing:0.01em}
.art-meta{margin-top:26px;font-size:13px;color:var(--muted);letter-spacing:0.12em}
.wrap{max-width:760px;margin:0 auto;padding:26px 24px 60px}
.abstract{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--sky);padding:22px 26px;margin:20px 0 26px;font-size:15.5px;line-height:1.95;border-radius:4px}
.abstract .ab-lbl{font-size:12px;letter-spacing:0.3em;color:var(--teal2);margin-bottom:10px}
.abstract p{color:var(--text);text-align:justify}
.keywords{font-size:14px;color:var(--muted);letter-spacing:0.02em;margin:0 0 30px;padding-bottom:24px;border-bottom:1px solid var(--line)}
.keywords strong{color:var(--teal2)}
.wrap h2{font-size:22px;font-weight:800;color:var(--head);margin:44px 0 18px;letter-spacing:0.02em;padding-top:8px;border-bottom:1px solid var(--line);padding-bottom:8px}
.wrap h2.notes-head{font-size:20px}
.wrap h3{font-size:18px;font-weight:700;color:var(--link);margin:30px 0 12px;letter-spacing:0.01em}
.wrap p{margin-bottom:20px;text-align:justify;color:var(--text);text-indent:2em}
.wrap p.ref{font-size:14px;line-height:1.7;color:var(--muted);margin-bottom:8px;text-indent:-2em;padding-left:2em;text-align:left}
.wrap p.noind{text-indent:0}
.wrap strong{color:var(--link);font-weight:700}
.sumbox{margin:24px 0 8px;padding:15px 20px;background:linear-gradient(135deg,#f4fbff,#edf6ff);border-left:3px solid var(--btn);border-radius:0 6px 6px 0;font-size:15.5px;line-height:1.9;color:#334155;text-indent:0}
.sumbox b{color:var(--head)}
.mat-list{list-style:none;padding:0;margin:0 0 8px}
.mat-list li{margin-bottom:15px;font-size:15.5px;line-height:1.9;text-indent:0}
.mat-list li strong{color:var(--teal2)}
.chain{padding-left:22px;margin:0 0 8px}
.chain li{margin-bottom:11px;font-size:15.5px;line-height:1.9;text-indent:0}
.closing{font-size:14.5px;color:var(--muted);font-style:italic;margin-top:16px;text-indent:0}
.endbox{background:linear-gradient(135deg,#2196F3 0%,#0A66C2 55%,#0F2C4A 100%);text-align:center;padding:60px 24px;margin-top:40px;border-radius:4px}
.endbox .lbl{font-size:12px;letter-spacing:0.4em;color:#BFE7FB;margin-bottom:16px}
.endbox .big{font-size:clamp(22px,3.4vw,30px);font-weight:700;color:#FFFFFF;letter-spacing:0.06em;margin-bottom:14px}
.endbox p{color:#DCEEFB;max-width:540px;margin:0 auto 26px;font-size:15px;line-height:1.95;text-indent:0}
.endbox a{display:inline-block;padding:12px 30px;font-size:14.5px;letter-spacing:0.08em;border-radius:2px;margin:5px;text-decoration:none}
.endbox .solid{background:#FFFFFF;color:#0A66C2;font-weight:700}
.endbox .ghost{border:1px solid #FFFFFF;color:#FFFFFF}
footer{background:#EAF6FE;color:var(--muted);text-align:center;padding:30px 24px;font-size:13px;letter-spacing:0.06em;border-top:1px solid var(--line)}
footer a{color:var(--link)}
@media(max-width:640px){body{font-size:16.5px}}'''

BEAUTIFY_CSS = r'''body{background:linear-gradient(180deg,#fbfdff 0%,#f5f9ff 100%);font-size:18px;line-height:2.05}
.art{padding-top:74px}
.art-series{color:var(--teal2);font-size:12.5px;letter-spacing:.42em}
.art-title{font-size:clamp(26px,4.4vw,38px);line-height:1.5;letter-spacing:.015em}
.art-title::after{content:"";display:block;width:50px;height:3px;background:linear-gradient(90deg,var(--sky),var(--btn));margin:24px auto 0;border-radius:2px}
.art-subtitle{font-size:clamp(15px,2.1vw,17.5px);color:var(--muted);line-height:1.95}
.wrap{max-width:722px}
.wrap h2{font-size:22.5px;margin:56px 0 20px;padding:0;border-bottom:none;position:relative;letter-spacing:.02em}
.wrap h2::before{content:"";position:absolute;left:0;top:-20px;width:36px;height:3px;background:var(--btn);border-radius:2px}
.wrap h2::after{content:"";display:block;height:1px;background:linear-gradient(90deg,var(--line),transparent);margin-top:12px}
.wrap h2.refs-h{font-size:19px}
.wrap h3{color:var(--link);font-size:18.5px;margin:36px 0 14px}
.wrap p{margin-bottom:22px;line-height:2.05;letter-spacing:.006em}
.wrap p strong{color:var(--head);font-weight:700;background:linear-gradient(transparent 66%,rgba(79,195,247,.34) 0)}
.abstract{background:linear-gradient(135deg,#f4fbff,#edf6ff);border:1px solid var(--line);border-left:3px solid var(--btn);border-radius:7px;box-shadow:0 8px 26px rgba(15,44,74,.07);padding:26px 30px}
.abstract .ab-lbl{letter-spacing:.34em}
.keywords{font-size:14px;padding-bottom:30px;margin-bottom:40px;border-bottom:1px dashed var(--line)}
.wrap p.ref{font-size:13.5px;line-height:1.75;color:var(--muted)}
@media(max-width:640px){body{font-size:17px}.wrap{max-width:100%}}'''

POLISH_CSS = r'''#sde-progress{position:fixed;top:0;left:0;height:3px;width:0;background:var(--link);z-index:99}
.wrap h2{position:relative;scroll-margin-top:74px}
.wrap h3{scroll-margin-top:74px}
.abstract{box-shadow:0 3px 16px rgba(15,44,74,.06)}
#sde-toc{position:fixed;left:20px;top:112px;width:196px;max-height:calc(100vh - 170px);overflow-y:auto;font-size:12.5px;line-height:1.65;z-index:15;display:none}
#sde-toc .t-h{font-size:11px;letter-spacing:.32em;color:var(--teal2);margin-bottom:9px}
#sde-toc a{display:block;color:var(--muted);padding:3px 0 3px 10px;border-left:2px solid rgba(15,44,74,.10);text-decoration:none;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#sde-toc a.on{color:var(--link);border-left-color:var(--link);font-weight:700}
@media(min-width:1420px){#sde-toc{display:block}}
#sde-top{position:fixed;right:22px;bottom:26px;width:42px;height:42px;border-radius:50%;background:var(--btn);color:#fff;border:none;font-size:18px;line-height:1;cursor:pointer;opacity:0;pointer-events:none;transition:opacity .25s;z-index:30;box-shadow:0 4px 14px rgba(15,44,74,.2)}
#sde-top.show{opacity:.94;pointer-events:auto}
@media print{.readbar,#sde-toc,#sde-top,#sde-progress,.endbox,footer{display:none!important}body{background:#fff!important}}'''

POLISH_JS = r'''(function(){
if(document.getElementById('sde-progress'))return;
var bar=document.createElement('div');bar.id='sde-progress';document.body.appendChild(bar);
var top=document.createElement('button');top.id='sde-top';top.textContent='↑';top.setAttribute('aria-label','回到顶部');document.body.appendChild(top);
top.addEventListener('click',function(){window.scrollTo({top:0,behavior:'smooth'});});
var hs=[].slice.call(document.querySelectorAll('.wrap h2'));
var toc=null,links=[];
if(hs.length>=4){
  toc=document.createElement('nav');toc.id='sde-toc';
  var lb=document.createElement('div');lb.className='t-h';lb.textContent='目 录';toc.appendChild(lb);
  hs.forEach(function(h,i){
    if(!h.id)h.id='sec-'+(i+1);
    var a=document.createElement('a');a.href='#'+h.id;
    a.textContent=h.textContent.replace(/^[一-鿿]{1,3}、/,'');
    links.push(a);toc.appendChild(a);
  });
  document.body.appendChild(toc);
}
function onScroll(){
  var d=document.documentElement,max=d.scrollHeight-window.innerHeight,y=window.scrollY||d.scrollTop;
  bar.style.width=(max>0?Math.min(100,y/max*100):0)+'%';
  if(y>600){top.classList.add('show');}else{top.classList.remove('show');}
  if(toc){var cur=-1;for(var i=0;i<hs.length;i++){if(hs[i].getBoundingClientRect().top<140)cur=i;}
    links.forEach(function(a,i){a.className=(i===cur?'on':'');});}
}
window.addEventListener('scroll',onScroll,{passive:true});window.addEventListener('resize',onScroll);onScroll();
})();'''

def _materials(mats):
    lis="\n".join(f'  <li><strong>{b}</strong>{t}</li>' for b,t in mats)
    return f'<ul class="mat-list">\n{lis}\n</ul>'

def _chain(chain):
    lis="\n".join(f'  <li><strong>{lab}</strong>{t}</li>' for lab,t in chain)
    return f'<ol class="chain">\n{lis}\n</ol>'

def _refs(refs):
    return "\n".join(f'<p class="ref">{r}</p>' for r in refs)

def build_apply_page(meta, body_html):
    m=meta
    materials=_materials(m['materials'])
    chain=_chain(m['chain'])
    refs=_refs(m['refs'])
    pdf=m['pdf_name']
    return f'''<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{m['title']}</title>
<meta name="description" content="{m['desc']}">
<style>
{HEAD_CSS}
</style><style id="beautify-v1">
{BEAUTIFY_CSS}
</style>
</head>
<body class="zh">
<div class="readbar"><a class="nav-back" href="/column/{m['seed_slug']}/">‹ 返回《{m['seed_title']}》</a>
  <div class="rb-modes"><span class="rb-btn cur">📖 长文阅读</span><a class="rb-btn" href="read.html">📄 在线 PDF</a><a class="rb-btn" href="{pdf}" download>⬇ 下载</a></div></div>
<div class="art"><div class="art-series">{m['series']}</div><h1 class="art-title">{m['art_title']}</h1>
  <div class="art-subtitle">{m['art_subtitle']}</div>
  <div class="art-meta">{m['byline']}</div></div>
<div class="wrap">
<div class="abstract"><div class="ab-lbl">摘 要</div><p>{m['abstract']}</p></div>
<p class="keywords"><strong>关键词</strong>　{m['keywords']}</p>
{body_html}
<h2 class="notes-head">材料与印证</h2>
{materials}
<h2 class="notes-head">论证的骨架</h2>
{chain}
<p class="closing">{m['closing']}</p>
<h2 class="notes-head refs-h">参考文献 · References</h2>
{refs}
</div>
<div class="endbox"><div class="lbl">这是《{m['seed_title']}》的一篇应用实践文</div><div class="big">回到母文，看它从何而来</div>
  <p>本手册的每一步操作，都源自母文的核心机制。读懂母文，这套工具会用得更准。</p>
  <a class="solid" href="/column/{m['seed_slug']}/">阅读母文《{m['seed_title']}》 →</a><a class="ghost" href="/column/">更多长文专栏 →</a></div>
<footer>© 德麦国际 Demai International · {m['seed_title']}应用实践 · Claude 著 · 依王德生《SDE本体论》 · <a href="/">sdeuniverses.com</a></footer>
<style id="sde-polish-v1">
{POLISH_CSS}
</style>
<script id="sde-polish-v1-js">
{POLISH_JS}
</script>
</body></html>'''

if __name__=='__main__':
    print("gen_apply_page ready")
