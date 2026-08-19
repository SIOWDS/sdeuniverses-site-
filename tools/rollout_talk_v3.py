#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sde-talk v3 全站替换器：讨论区改为 Google 实名登录（方案B，只认 Google）。
用法：python3 tools/rollout_talk_v3.py <GOOGLE_CLIENT_ID>
  - 扫描 public/ 下所有含 <section id="sde-talk"> 的页面
  - 把 v2 的"起名发言"表单替换为 Google 登录按钮 + 发言框（v3）
  - 保留各页原有 slug、区块标题（如会议页"会议讨论区"）与阅读计数
  - 幂等：已是 v3 的页面跳过
配套：src/worker.js 顶部 GOOGLE_CLIENT_ID 常量需同时填入同一 ID。
"""
import os, re, sys

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public")

V3_FORM = '''<div class="tk-form" id="tk-gform">
    <div id="tk-replying" style="display:none"><span id="tk-replying-to"></span><a id="tk-cancel">取消回复</a></div>
    <div id="tk-signed" style="display:none;font-size:14px;margin-bottom:10px">以 <b id="tk-gname"></b> 的身份发言 <a id="tk-gout" style="margin-left:10px;font-size:12px;opacity:.6;text-decoration:underline;cursor:pointer">退出</a></div>
    <div id="tk-gsi"></div>
    <textarea id="tk-text" maxlength="1000" placeholder="你的问题，或你的见解…" style="display:none;margin-top:10px"></textarea>
    <div class="tk-bar" id="tk-sendbar" style="display:none"><span class="tk-note">最多 1000 字 · 每人每天最多 30 条</span><button id="tk-send">发 言</button></div>
    <div id="tk-msg"></div>
  </div>'''

V3_JS_AUTH = '''var GCID="__GOOGLE_CLIENT_ID__",gcred="";
try{var st=JSON.parse(sessionStorage.getItem("sde_gauth")||"null");if(st&&st.exp>Date.now()){gcred=st.cred;showSigned(st.name);}}catch(e){}
function showSigned(n){el("tk-gname").textContent=n;el("tk-signed").style.display="block";el("tk-gsi").style.display="none";el("tk-text").style.display="block";el("tk-sendbar").style.display="flex";}
function showSignIn(){gcred="";try{sessionStorage.removeItem("sde_gauth");}catch(e){}el("tk-signed").style.display="none";el("tk-gsi").style.display="block";el("tk-text").style.display="none";el("tk-sendbar").style.display="none";}
window.__sdeGCb=function(resp){try{var p=JSON.parse(atob(resp.credential.split(".")[1].replace(/-/g,"+").replace(/_/g,"/")));var nm=(p.name||(p.email||"").split("@")[0]||"").slice(0,20);gcred=resp.credential;try{sessionStorage.setItem("sde_gauth",JSON.stringify({cred:gcred,name:nm,exp:Date.now()+50*60*1000}));}catch(e){}showSigned(nm);}catch(e){note("登录信息解析失败，请重试。");}};
function bootGsi(){if(!(window.google&&google.accounts&&google.accounts.id)){el("tk-gsi").textContent="Google 登录组件加载失败——本讨论区需要 Google 账号登录后发言，请检查网络后刷新。";return}
google.accounts.id.initialize({client_id:GCID,callback:window.__sdeGCb,auto_select:true});
google.accounts.id.renderButton(el("tk-gsi"),{theme:"outline",size:"large",text:"signin_with",shape:"pill",logo_alignment:"left"});}
(function(){var s=document.createElement("script");s.src="https://accounts.google.com/gsi/client";s.async=true;s.defer=true;s.onload=bootGsi;s.onerror=function(){el("tk-gsi").textContent="无法连接 Google 登录服务——本讨论区需要 Google 账号登录后发言。";};document.head.appendChild(s);})();
el("tk-gout").onclick=showSignIn;'''

HINT_V3 = '用 Google 账号登录即可发言——发言人就是你的 Google 账号名字。发言公开可见，请友善交流。'


def build_v3_js(slug):
    return '''<script id="sde-talk-js">
(function(){
var slug="%s",API="/api/comments?slug="+slug;
function el(id){return document.getElementById(id)}
var items=[],parent="";
function note(s){el("tk-msg").textContent=s}
%s
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
var day=new Date(Date.now()+8*3600*1000).toISOString().slice(0,10),k="sde_pv_"+slug.replace(/\\//g,"_"),m="POST";
try{if(localStorage.getItem(k)===day)m="GET";}catch(e){}
fetch("/api/pv?slug="+slug,{method:m}).then(function(r){return r.json()})
.then(function(d){if(d&&typeof d.total==="number"){pn.textContent=d.total.toLocaleString("zh-Hans-CN");
if(m==="POST"){try{localStorage.setItem(k,day);}catch(e){}}}else{throw 0;}})
.catch(function(){var w=el("sde-pv-wrap");if(w)w.style.display="none";});
})();
})();
</script>''' % (slug, V3_JS_AUTH)


def upgrade(path, cid):
    h = open(path, encoding="utf-8").read()
    if 'sde-talk v3' in h:
        return "skip-v3"
    m = re.search(r'<section id="sde-talk">.*?</section>\s*<script id="sde-talk-js">.*?</script>', h, re.S)
    if not m:
        return "no-block"
    old = m.group(0)
    slug_m = re.search(r'var slug="([^"]+)"', old)
    if not slug_m:
        return "no-slug"
    slug = slug_m.group(1)
    sec = re.search(r'(<section id="sde-talk">.*?</section>)', old, re.S).group(1)
    # 表单替换为 Google 版；提示语替换；标题保留原样（会议页等自定义标题不动）
    sec2 = re.sub(r'<div class="tk-form">.*?</div>\s*(?=<div id="tk-list">)', V3_FORM + "\n  ", sec, flags=re.S)
    sec2 = re.sub(r'<p class="tk-hint">.*?</p>', '<p class="tk-hint">' + HINT_V3 + '</p>', sec2, flags=re.S)
    if sec2 == sec:
        return "form-anchor-miss"
    new = sec2 + "\n" + build_v3_js(slug)
    new = new.replace("__GOOGLE_CLIENT_ID__", cid)
    h2 = h.replace(old, new, 1)
    # 版本标记
    h2 = h2.replace('<!-- 读者讨论区+阅读计数 · sde-talk v2 -->', '<!-- 读者讨论区+阅读计数 · sde-talk v3 (Google实名) -->', 1)
    open(path, "w", encoding="utf-8").write(h2)
    return "ok"


def main():
    if len(sys.argv) < 2 or ".apps.googleusercontent.com" not in sys.argv[1]:
        print("用法: python3 tools/rollout_talk_v3.py <GOOGLE_CLIENT_ID>")
        sys.exit(1)
    cid = sys.argv[1].strip()
    stats = {}
    for dp, _, fns in os.walk(ROOT):
        for fn in fns:
            if not fn.endswith(".html"):
                continue
            p = os.path.join(dp, fn)
            if 'id="sde-talk"' not in open(p, encoding="utf-8").read():
                continue
            r = upgrade(p, cid)
            stats[r] = stats.get(r, 0) + 1
            if r not in ("ok", "skip-v3"):
                print("!!", r, p)
    print(stats)


if __name__ == "__main__":
    main()
