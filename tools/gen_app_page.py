# -*- coding: utf-8 -*-
"""SDE 应用文页面生成器 —— 复用 column 站点壳，供 20 颗种子 × 3 篇应用文使用。
用法：在 Python 里 import build_page(meta, body_html) -> full_html 字符串。
meta 为 dict；body_html 为 <article> 内部内容（h2/h3/p/sumbox）。TOC 自 body 的 h2 自动生成。
"""
import re, json, html

DISCUSSION_JS_CSS = r'''<section id="sde-talk">
<style id="sde-talk-css">
#sde-talk{max-width:722px;margin:56px auto 40px;padding:0 24px;line-height:1.9;text-align:left}
#sde-talk .tk-title{font-size:20px;font-weight:800;letter-spacing:.04em;margin:0 0 4px;padding-bottom:12px;border-bottom:2px solid rgba(128,128,128,.3);text-indent:0}
#sde-talk .tk-title span{font-size:13px;font-weight:400;opacity:.6;letter-spacing:.02em}
#sde-talk .tk-hint{font-size:13px;opacity:.62;margin:10px 0 18px;text-indent:0}
#sde-talk .tk-form{background:rgba(128,128,128,.06);border:1px solid rgba(128,128,128,.22);border-radius:8px;padding:16px 16px 12px;margin-bottom:26px}
#sde-talk input,#sde-talk textarea{display:block;width:100%;box-sizing:border-box;font:inherit;color:inherit;background:rgba(128,128,128,.12);border:1px solid rgba(128,128,128,.3);border-radius:6px;padding:9px 12px;margin:0 0 10px;outline:none}
#sde-talk textarea{min-height:88px;resize:vertical;line-height:1.8}
#sde-talk input:focus,#sde-talk textarea:focus{border-color:rgba(128,128,128,.6)}
#sde-talk .tk-bar{display:flex;justify-content:space-between;align-items:center}
#sde-talk .tk-note{font-size:12px;opacity:.55}
#sde-talk button{font:inherit;font-size:14px;letter-spacing:.2em;padding:7px 26px;border-radius:6px;border:1px solid currentColor;background:transparent;color:inherit;cursor:pointer;opacity:.85}
#sde-talk button:hover{opacity:1}
#sde-talk button:disabled{opacity:.4;cursor:default}
#sde-talk #tk-msg{font-size:13px;margin-top:8px;opacity:.75;min-height:1em;text-indent:0}
#sde-talk #tk-replying{font-size:13px;margin-bottom:8px;opacity:.8}
#sde-talk #tk-replying a{margin-left:8px;text-decoration:underline;color:inherit;opacity:.7;cursor:pointer}
#sde-talk .tk-item{border-bottom:1px solid rgba(128,128,128,.18);padding:16px 2px}
#sde-talk .tk-head{font-size:13px;margin-bottom:5px;text-indent:0}
#sde-talk .tk-name{font-weight:700}
#sde-talk .tk-time{opacity:.5;margin-left:10px;font-size:12px}
#sde-talk .tk-body{white-space:pre-wrap;word-break:break-word;font-size:15.5px;text-indent:0;margin:0}
#sde-talk .tk-reply{display:inline-block;font-size:12px;margin-top:7px;color:inherit;opacity:.55;text-decoration:none;border-bottom:1px dashed currentColor;cursor:pointer}
#sde-talk .tk-reply:hover{opacity:.9}
#sde-talk .tk-sub{margin:12px 0 0 22px;padding:10px 14px;background:rgba(128,128,128,.07);border-left:2px solid rgba(128,128,128,.35);border-radius:0 6px 6px 0}
#sde-talk .tk-empty{padding:26px 0;text-align:center;opacity:.55;font-size:14px}
</style>
<div class="tk-wrap">
  <h2 class="tk-title">读者讨论区 <span id="tk-count"></span> <span id="sde-pv-wrap">· 本文已被阅读 <span id="sde-pv-n">—</span> 次</span></h2>
  <p class="tk-hint">用 Google 账号登录即可发言——发言人就是你的 Google 账号名字。发言公开可见，请友善交流。</p>
  <div class="tk-form" id="tk-gform">
    <div id="tk-replying" style="display:none"><span id="tk-replying-to"></span><a id="tk-cancel">取消回复</a></div>
    <div id="tk-signed" style="display:none;font-size:14px;margin-bottom:10px">以 <b id="tk-gname"></b> 的身份发言 <a id="tk-gout" style="margin-left:10px;font-size:12px;opacity:.6;text-decoration:underline;cursor:pointer">退出</a></div>
    <div id="tk-gsi"></div>
    <textarea id="tk-text" maxlength="1000" placeholder="你的问题，或你的见解…" style="display:none;margin-top:10px"></textarea>
    <div class="tk-bar" id="tk-sendbar" style="display:none"><span class="tk-note">最多 1000 字 · 每人每天最多 30 条</span><button id="tk-send">发 言</button></div>
    <div id="tk-msg"></div>
  </div>
  <div id="tk-list"></div>
</div>
</section>
<script id="sde-talk-js">
(function(){
var slug="column/__SLUG__",API="/api/comments?slug="+slug;
function el(id){return document.getElementById(id)}
var items=[],parent="";
function note(s){el("tk-msg").textContent=s}
var GCID="985037699618-de3smmqf2rer0pfhf4mrtrj3rgahgu5u.apps.googleusercontent.com",gcred="";
try{var st=JSON.parse(sessionStorage.getItem("sde_gauth")||"null");if(st&&st.exp>Date.now()){gcred=st.cred;showSigned(st.name);}}catch(e){}
function showSigned(n){el("tk-gname").textContent=n;el("tk-signed").style.display="block";el("tk-gsi").style.display="none";el("tk-text").style.display="block";el("tk-sendbar").style.display="flex";}
function showSignIn(){gcred="";try{sessionStorage.removeItem("sde_gauth");}catch(e){}el("tk-signed").style.display="none";el("tk-gsi").style.display="block";el("tk-text").style.display="none";el("tk-sendbar").style.display="none";}
window.__sdeGCb=function(resp){try{var p=JSON.parse(atob(resp.credential.split(".")[1].replace(/-/g,"+").replace(/_/g,"/")));var nm=(p.name||(p.email||"").split("@")[0]||"").slice(0,20);gcred=resp.credential;try{sessionStorage.setItem("sde_gauth",JSON.stringify({cred:gcred,name:nm,exp:Date.now()+50*60*1000}));}catch(e){}showSigned(nm);}catch(e){note("登录信息解析失败，请重试。");}};
function bootGsi(){if(!(window.google&&google.accounts&&google.accounts.id)){el("tk-gsi").textContent="Google 登录组件加载失败——本讨论区需要 Google 账号登录后发言，请检查网络后刷新。";return}
google.accounts.id.initialize({client_id:GCID,callback:window.__sdeGCb,auto_select:true});
google.accounts.id.renderButton(el("tk-gsi"),{theme:"outline",size:"large",text:"signin_with",shape:"pill",logo_alignment:"left"});}
(function(){var s=document.createElement("script");s.src="https://accounts.google.com/gsi/client";s.async=true;s.defer=true;s.onload=bootGsi;s.onerror=function(){el("tk-gsi").textContent="无法连接 Google 登录服务——本讨论区需要 Google 账号登录后发言。";};document.head.appendChild(s);})();
el("tk-gout").onclick=showSignIn;
function tme(ts){var d=new Date(ts),p=function(x){return (x<10?"0":"")+x};
return d.getFullYear()+"-"+p(d.getMonth()+1)+"-"+p(d.getDate())+" "+p(d.getHours())+":"+p(d.getMinutes())}
function head(c){var h=document.createElement("div");h.className="tk-head";
var n=document.createElement("span");n.className="tk-name";n.textContent=c.name;
var t=document.createElement("span");t.className="tk-time";t.textContent=tme(c.ts);
h.appendChild(n);h.appendChild(t);return h}
function para(s){var p=document.createElement("p");p.className="tk-body";p.textContent=s;return p}
function replyLink(c){var a=document.createElement("a");a.className="tk-reply";a.textContent="回复";
a.onclick=function(){if(!gcred){note("回复也需要先用 Google 账号登录——请在上方登录。");var g=el("tk-gsi");if(g&&g.scrollIntoView)g.scrollIntoView({behavior:"smooth",block:"center"});return}
parent=c.id;el("tk-replying-to").textContent="回复 "+c.name+"：";
el("tk-replying").style.display="block";el("tk-text").focus()};return a}
function render(){var L=el("tk-list");L.textContent="";
var tops=items.filter(function(c){return !c.parent});
el("tk-count").textContent=items.length?"· "+items.length+" 条":"";
if(!tops.length){var d=document.createElement("div");d.className="tk-empty";d.textContent="还没有发言——欢迎第一个开口。";L.appendChild(d);return}
tops.forEach(function(c){var it=document.createElement("div");it.className="tk-item";
it.appendChild(head(c));it.appendChild(para(c.text));it.appendChild(replyLink(c));
items.filter(function(x){return x.parent===c.id}).forEach(function(x){
var sb=document.createElement("div");sb.className="tk-sub";sb.appendChild(head(x));sb.appendChild(para(x.text));it.appendChild(sb)});
L.appendChild(it)})}
function load(){fetch(API).then(function(r){return r.json()}).then(function(d){items=d.items||[];render()}).catch(function(){})}
el("tk-cancel").onclick=function(){parent="";el("tk-replying").style.display="none"};
el("tk-send").onclick=function(){var text=el("tk-text").value.trim();
if(!gcred){note("请先用 Google 账号登录。");return}
if(text.length<2){note("内容太短了。");return}
el("tk-send").disabled=true;note("发送中…");
fetch(API,{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({credential:gcred,text:text,parent:parent})})
.then(function(r){return r.json().then(function(d){return{s:r.status,d:d}})})
.then(function(x){el("tk-send").disabled=false;
if(x.d&&x.d.ok){el("tk-text").value="";parent="";el("tk-replying").style.display="none";note("已发布。");load()}
else if(x.s===401){note("登录已过期，请重新登录。");showSignIn()}
else{note((x.d&&x.d.msg)||"发送失败，请稍后再试。")}})
.catch(function(){el("tk-send").disabled=false;note("网络异常，请稍后再试。")})};
load();
(function(){var pn=el("sde-pv-n");if(!pn)return;
var day=new Date(Date.now()+8*3600*1000).toISOString().slice(0,10),k="sde_pv_"+slug.replace(/\//g,"_"),m="POST";
try{if(localStorage.getItem(k)===day)m="GET";}catch(e){}
fetch("/api/pv?slug="+slug,{method:m}).then(function(r){return r.json()})
.then(function(d){if(d&&typeof d.total==="number"){pn.textContent=d.total.toLocaleString("zh-Hans-CN");
if(m==="POST"){try{localStorage.setItem(k,day);}catch(e){}}}else{throw 0;}})
.catch(function(){var w=el("sde-pv-wrap");if(w)w.style.display="none";});
})();
})();
</script>'''

def _toc(body_html):
    items=re.findall(r'<h2 id="([^"]+)"[^>]*>(.*?)</h2>', body_html, re.S)
    out=[]
    for hid,txt in items:
        t=re.sub(r'<[^>]+>','',txt).strip()
        out.append(f'<a href="#{hid}">{t}</a>')
    return "\n".join(out)

def _refs(refs):
    lis="\n".join(f'    <li style="margin:0 0 9px;padding-left:6px">{html.escape(r) if False else r}</li>' for r in refs)
    return lis

def _scholarly(sb):
    # sb: dict with 'materials' (list of (bold, text)) and 'chain' (list of (label,text)) and 'closing'
    mats="\n".join(
        f'    <li style="margin-bottom:16px"><strong style="color:var(--gold,#8A6817)">{b}</strong>{t}</li>'
        for b,t in sb['materials'])
    chain="\n".join(
        f'    <li style="margin-bottom:12px"><strong>{lab}</strong>{t}</li>'
        for lab,t in sb['chain'])
    return f'''<section class="scholarly-base" style="max-width:760px;margin:56px auto 0;padding:0 22px;color:var(--ink,#1A1410)">
  <hr style="border:none;border-top:1px solid rgba(138,104,23,.28);margin:0 0 40px">
  <h2 style="font-size:23px;color:var(--gold,#8A6817);letter-spacing:.02em;margin-bottom:8px">材料与印证</h2>
  <p style="font-size:13.5px;color:#7a6a52;margin-bottom:22px">本文的诊断针对真实存在的机制与现象。下列材料给出可查证的出处与研究线索，读者可循以复核；文中所有具体人物场景均为构拟示例，不冒充田野记录或个案。</p>
  <ul style="font-size:15.5px;line-height:1.95;padding-left:0;list-style:none">
{mats}
  </ul>
  <h2 style="font-size:23px;color:var(--gold,#8A6817);letter-spacing:.02em;margin:36px 0 8px">论证的骨架</h2>
  <p style="font-size:13.5px;color:#7a6a52;margin-bottom:20px">把本文的说服力压到最紧，它是一条可被逐环检验的推理链，每一环都可以被单独反驳：</p>
  <ol style="font-size:15.5px;line-height:1.95;padding-left:22px">
{chain}
  </ol>
  <p style="font-size:14px;color:#7a6a52;margin-top:18px;font-style:italic">{sb['closing']}</p>
</section>'''

def build_page(meta, body_html):
    accent=meta.get('accent', {'red':'#8A2E2E','red2':'#6E2222','line':'rgba(138,46,46,0.16)','ink_red':'#D89A9A'})
    toc=_toc(body_html)
    nb=meta['nextbox']
    nb_links="\n".join(f'<a class="go" href="{u}">{t} →</a>' for t,u in nb['links'])
    refs_html=_refs(meta['refs'])
    schol=_scholarly(meta['scholarly'])
    disc=DISCUSSION_JS_CSS.replace("__SLUG__", meta['slug'])
    root=(f":root{{--bg:#F5F1E8;--card:#FBF8F0;--card2:#F0E8D3;--red:{accent['red']};--red2:{accent['red2']};"
          f"--gold:#8A6817;--gold2:#B08A2E;--text:#231D16;--muted:#7A6F5E;--line:{accent['line']};"
          f"--ink-gold:#D9B45B;--ink-red:{accent['ink_red']}}}")
    return f'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{meta['title']}</title>
<meta name="description" content="{meta['desc']}">
<meta property="og:title" content="{meta['og']}"><meta property="og:type" content="article">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
{root}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:var(--bg);color:var(--text);font-family:"Songti SC","Noto Serif SC","Source Han Serif SC","Noto Serif CJK SC",Georgia,serif;line-height:2.02;font-size:17px}}
a{{color:var(--red);text-decoration:none}}a:hover{{text-decoration:underline}}
.w{{max-width:820px;margin:0 auto;padding:0 24px}}
nav{{position:sticky;top:0;background:rgba(245,241,232,0.94);backdrop-filter:blur(8px);border-bottom:1px solid var(--line);z-index:10}}
nav .w{{display:flex;align-items:center;justify-content:space-between;height:58px}}
.nav-logo{{font-weight:700;letter-spacing:0.06em;color:var(--text)}}.nav-back{{font-size:14px;color:var(--muted)}}
header.art{{background:linear-gradient(158deg,#1C120A 0%,#191008 100%);color:#F2E8D8;padding:78px 0 58px;text-align:center;position:relative;overflow:hidden}}
.eyebrow{{font-size:12px;letter-spacing:0.4em;color:var(--ink-gold);margin-bottom:24px}}
.art-title{{font-size:clamp(27px,5vw,42px);font-weight:700;letter-spacing:0.05em;line-height:1.5;color:#F5ECDC}}
.art-sub{{font-size:clamp(15px,2.2vw,18px);color:var(--ink-red);margin-top:16px;letter-spacing:0.05em;line-height:1.7}}
.art-meta{{margin-top:28px;font-size:12.5px;color:#8A7A62;letter-spacing:0.12em}}
.brand-line{{position:absolute;left:50%;bottom:0;transform:translateX(-50%);width:120px;height:3px;background:linear-gradient(90deg,transparent,var(--ink-red),transparent)}}
.body{{padding:52px 0 20px}}
.deck{{max-width:820px;margin:0 auto 30px;padding:22px 26px;background:var(--card);border-left:3px solid var(--gold2);border-radius:0 8px 8px 0;color:#4A4235;font-size:16px;line-height:1.95;font-style:italic}}
.motif{{max-width:820px;margin:0 auto 40px;padding:24px 28px;background:#F3EADB;border:1px solid var(--line);border-radius:8px;color:var(--red2);font-size:16.5px;line-height:1.95}}
.motif .ml{{font-size:11.5px;letter-spacing:0.4em;color:var(--red);margin-bottom:12px;font-style:normal}}
.toc{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:22px 28px;margin-bottom:44px}}
.toc .tl{{font-size:12px;letter-spacing:0.42em;color:var(--red);margin-bottom:14px}}
.toc a{{display:block;padding:5px 0;color:#3E362A;font-size:15px;border-bottom:1px dashed rgba(51,102,153,0.10)}}.toc a:last-child{{border-bottom:none}}
article h2{{font-size:22px;font-weight:700;margin:52px 0 20px;padding-top:16px;letter-spacing:0.03em;color:var(--red2);border-top:1px solid var(--line)}}
article h3{{font-size:17.5px;font-weight:700;margin:34px 0 14px;color:var(--red);letter-spacing:0.02em}}
article p{{margin:0 0 20px;text-align:justify}}article strong,article b{{color:var(--red2);font-weight:700}}article em{{font-style:italic;color:#4A4235}}
.sumbox{{margin:26px 0 8px;padding:16px 20px;background:var(--card);border-left:3px solid var(--red);border-radius:0 6px 6px 0;font-size:15.5px;line-height:1.9;color:#4A4235}}
.sumbox b{{color:var(--red2)}}
.nextbox{{max-width:820px;margin:52px auto 0;padding:26px 28px;background:var(--card);border:1px solid var(--line);border-left:4px solid var(--gold2);border-radius:0 8px 8px 0}}
.nextbox .nl{{font-size:11.5px;letter-spacing:0.36em;color:var(--gold);margin-bottom:10px}}
.nextbox h4{{font-size:18px;color:var(--red2);margin-bottom:8px;line-height:1.5}}
.nextbox p{{font-size:15px;color:#4A4235;line-height:1.85;margin-bottom:12px}}
.nextbox a.go{{display:inline-block;color:var(--red);font-weight:700;font-size:15px;margin-right:20px}}
footer{{border-top:1px solid var(--line);padding:30px 24px;text-align:center;color:#6B6250;font-size:13px}}footer a{{color:var(--gold);text-decoration:none}}
@media(max-width:640px){{.art-title{{font-size:26px}}body{{font-size:16px}}}}
</style></head><body>
<nav><div class="w"><a class="nav-logo" href="/">SDE Universes</a><a class="nav-back" href="{meta['back_url']}">← {meta['back_label']}</a></div></nav>
<header class="art"><div class="eyebrow">{meta['eyebrow']}</div><h1 class="art-title">{meta['h1']}</h1><div class="art-sub">{meta['sub']}</div><div class="art-meta">{meta['byline']}</div><div class="brand-line"></div></header>
<div class="body"><div class="w">
<div class="deck">{meta['deck']}</div>
<div class="motif"><div class="ml">母 题</div>{meta['motif']}</div>
<div class="toc"><div class="tl">目 录</div>
{toc}
</div><article>
{body_html}
{schol}
</article>
<div class="nextbox"><div class="nl">{nb['kicker']}</div>
<h4>{nb['h4']}</h4>
<p>{nb['p']}</p>
{nb_links}
</div>
</div></div>

<section id="sde-refs" style="max-width:820px;margin:56px auto 8px;padding:34px 30px;background:#FBF8F0;border:1px solid #E2D8C2;border-radius:6px">
  <h2 style="font-size:20px;letter-spacing:0.14em;color:#7A5C1E;margin:0 0 10px">参考文献 · References</h2>
  <p style="font-size:13.5px;line-height:1.9;color:#A08A5C;margin:0 0 20px">本文为依 SDE 发生学（王德生《SDE本体论》）延伸的原创应用论述。下列文献为文中所涉思想的原典与代表性研究，供读者对读与查证；本文观点不代表所列作者立场。</p>
  <ol style="margin:0;padding-left:22px;font-size:14px;line-height:1.85;color:#4A4335">
{refs_html}
  </ol>
</section>

{disc}

<footer>© 2026 德麦国际 · SDE Universes · <a href="{meta['back_url']}">返回 {meta['back_label']}</a> · <a href="/">首页</a></footer>
</body></html>'''

if __name__=='__main__':
    print("gen_app_page module ready")
