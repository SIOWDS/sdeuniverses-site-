# -*- coding: utf-8 -*-
"""/meeting/ 身份条：Google 登录暂时关闭，改用「SDE 社区名字＋密码」。
   与 /sde-wechat/ 与 /assets/sde-talk.js 共用同一张身份（sessionStorage sde_gauth ＋ localStorage sde_talk_id），
   凭证格式 sdepw1:<密码>:<名字>，服务端走 verifyPasscode（名字须在 /students/roster.json 名录里）。
   Google 通道的代码保留在 GOOGLE_ON 开关后面，改回 true 即恢复。"""
import re, io

FP = "/home/claude/site/public/meeting/index.html"
h = io.open(FP, encoding="utf-8").read()
def rep(old, new, n=1):
    global h
    assert h.count(old) == n, (h.count(old), old[:70])
    h = h.replace(old, new, n)

rep('.meet-auth .ma-msg{font-size:0.8rem;color:var(--mtg);margin-top:8px}',
    '.meet-auth .ma-msg{font-size:0.8rem;color:var(--mtg);margin-top:8px}\n'
    '.meet-auth .ma-msg.bad{color:#B3261E}\n'
    '.meet-auth .ma-pw{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}\n'
    '.meet-auth .ma-pw input{flex:1;min-width:132px;padding:0.5rem 0.7rem;border:1px solid var(--border2);border-radius:8px;background:#FFFDF8;font:inherit;font-size:0.86rem;color:var(--text)}\n'
    '.meet-auth .ma-pw input:focus{outline:none;border-color:var(--mtg)}\n'
    '.meet-auth .ma-pw .btn{padding:0.5rem 1.3rem;font-size:0.82rem;flex:none}')

rep('<!-- 统一 Google 登录身份条 -->', '<!-- 身份条：SDE 社区名字＋密码（Google 通道暂时关闭）-->')
rep('<div id="ma-out" style="display:none">已用 Google 登录 · 进入任何会议都会自动显示为 <b id="ma-name"></b> <a id="ma-signout">退出</a></div>',
    '<div id="ma-out" style="display:none">已进入 · 进入任何会议都会自动显示为 <b id="ma-name"></b> <a id="ma-signout">退出</a></div>')
rep('<div id="ma-in">进入会议前，先用 <b>Google 账号</b>登录（自动登录一次即可）——进会议自动带上你的名字，不用在教室里再输入。</div>',
    '<div id="ma-in">进入会议前，先用你在 <b>SDE 社区</b>的名字和密码进入——与社区、讨论区同一个账号，进会议自动带上你的名字，不用在教室里再输入。</div>')
rep('    <span id="ma-gsi"></span>\n  </div>\n  <div class="ma-msg" id="ma-msg"></div>',
    '    <span id="ma-gsi" style="display:none"></span>\n  </div>\n'
    '  <div class="ma-pw" id="ma-pw">\n'
    '    <input id="ma-pw-name" list="ma-pw-roster" maxlength="20" autocomplete="off" placeholder="社区名字">\n'
    '    <datalist id="ma-pw-roster"></datalist>\n'
    '    <input id="ma-pw-code" type="password" autocomplete="current-password" placeholder="密码">\n'
    '    <button class="btn" id="ma-pw-go">进入</button>\n'
    '  </div>\n  <div class="ma-msg" id="ma-msg"></div>')

rep('function meetNeedLogin(){var m=document.getElementById("ma-msg");if(m)m.textContent="进入会议前，请先用上方 Google 账号登录——登录后进会议会自动显示你的名字。";',
    'function meetNeedLogin(){var m=document.getElementById("ma-msg");if(m){m.textContent="进入会议前，请先在上方用社区名字和密码进入——进会议会自动显示你的名字。";m.className="ma-msg";}var f=document.getElementById("ma-pw-name");if(f)try{f.focus()}catch(e){}')

rep('<li>实名显示：全站 Google 登录，进会议自动带真名</li>',
    '<li>实名显示：全站同一个社区账号，进会议自动带真名</li>')
rep('<p>点「进入教室」即在新标签页打开，Google 账号自动登录，不限时长。开课时间以下方讨论区预告为准。</p>',
    '<p>点「进入教室」即在新标签页打开，自动带上你的社区名字，不限时长。开课时间以下方讨论区预告为准。</p>')
rep('<li>在本页顶部用 Google 账号登录一次（自动登录，浏览器会记住）——之后进入任何会议都会自动显示你的 Google 名字，不用在教室里再登录或改名。</li>',
    '<li>在本页顶部用你在 SDE 社区的名字和密码进入一次（与社区、讨论区同一个账号，本机会记住半天）——之后进入任何会议都会自动显示你的名字，不用在教室里再登录或改名。</li>')
rep('<li><b>开房：</b>提前十分钟点「进入 SDE 大教室」，用 Google 账号登录即成为主持人；学生同样用各自 Google 账号自动登录进入。</li>',
    '<li><b>开房：</b>提前十分钟点「进入 SDE 大教室」，先进者即成为主持人；学生同样用各自社区名字和密码进入。</li>')
rep('<!-- 读者讨论区+阅读计数 · sde-talk v3 (Google实名) -->',
    '<!-- 读者讨论区+阅读计数 · sde-talk v3（社区实名） -->')

END = 'boot();syncId();\nsetInterval(syncId,1200);\nwindow.addEventListener("focus",syncId);\n})();'
i0 = h.index('// ===== 统一 Google 登录身份'); i1 = h.index(END) + len(END)
old_js = h[i0:i1]
new_js = '''// ===== 身份：SDE 社区名字＋密码 =====
// 与 /sde-wechat/ 与 /assets/sde-talk.js 共用同一张身份：sessionStorage sde_gauth ＋ localStorage sde_talk_id
// （凭证 sdepw1:<密码>:<名字>，服务端 verifyPasscode 校验，名字须在 /students/roster.json 名录里）。
// Google 通道暂时关闭：把 GOOGLE_ON 改回 true 即恢复（还需页面自行提供 GSI 脚本与 window.__sdeGCb 回调）。
(function(){
function el(id){return document.getElementById(id)}
var GOOGLE_ON=false;
var GCID="985037699618-de3smmqf2rer0pfhf4mrtrj3rgahgu5u.apps.googleusercontent.com",tries=0;
var SKEY="sde_gauth",LKEY="sde_talk_id",TTL=12*3600*1000;
window.SDE_MEET_NAME="";
function jget(store,k){try{return JSON.parse(store.getItem(k)||"null")}catch(e){return null}}
function alive(o){return !!(o&&o.cred&&o.exp>Date.now())}
function readRec(){
  var ss=jget(sessionStorage,SKEY),ls=jget(localStorage,LKEY);
  if(!alive(ss)&&alive(ls)){ss=ls;try{sessionStorage.setItem(SKEY,JSON.stringify(ls))}catch(e){}}
  else if(alive(ss)&&String(ss.cred).slice(0,7)==="sdepw1:"&&!alive(ls)){try{localStorage.setItem(LKEY,JSON.stringify(ss))}catch(e){}}
  return alive(ss)?ss:null;
}
function say(t,bad){var m=el("ma-msg");if(m){m.textContent=t||"";m.className="ma-msg"+(bad?" bad":"")}}
function syncId(){
  var r=readRec(),nm=r?(r.name||""):"";
  if(nm){window.SDE_MEET_NAME=nm;var e=el("ma-name");if(e)e.textContent=nm;el("ma-out").style.display="block";el("ma-in").style.display="none";el("ma-pw").style.display="none";}
  else{window.SDE_MEET_NAME="";el("ma-out").style.display="none";el("ma-in").style.display="block";el("ma-pw").style.display="flex";}
}
var so=el("ma-signout");
if(so)so.onclick=function(){
  try{sessionStorage.removeItem(SKEY)}catch(e){}
  try{localStorage.removeItem(LKEY)}catch(e){}
  try{if(GOOGLE_ON&&window.google&&google.accounts&&google.accounts.id)google.accounts.id.disableAutoSelect()}catch(e){}
  syncId();say("已退出。");
};
function pwLogin(){
  var nm=(el("ma-pw-name").value||"").trim().slice(0,20),pw=el("ma-pw-code").value||"";
  if(!nm){say("先填名字。",1);return}
  if(!pw){say("请输入密码。",1);return}
  var c="sdepw1:"+pw+":"+nm,go=el("ma-pw-go");
  go.disabled=true;say("正在进入…");
  fetch("/api/im",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({credential:c,op:"hello"})})
    .then(function(r){return r.json()})
    .then(function(d){
      go.disabled=false;
      if(!d||!d.ok){say((d&&d.msg)||"进不去，请检查名字和密码。",1);return}
      var real=(d.me&&d.me.name)||nm,rec={cred:c,name:real,exp:Date.now()+TTL};
      try{sessionStorage.setItem(SKEY,JSON.stringify(rec))}catch(e){}
      try{localStorage.setItem(LKEY,JSON.stringify(rec))}catch(e){}
      el("ma-pw-code").value="";say("");syncId();
    })
    .catch(function(){go.disabled=false;say("网络异常，请重试。",1)});
}
el("ma-pw-go").onclick=pwLogin;
el("ma-pw-code").addEventListener("keydown",function(e){if(e.key==="Enter")pwLogin()});
el("ma-pw-name").addEventListener("keydown",function(e){if(e.key==="Enter")el("ma-pw-code").focus()});
var rosterLoaded=false;
el("ma-pw-name").addEventListener("focus",function(){
  if(rosterLoaded)return;rosterLoaded=true;
  fetch("/students/roster.json").then(function(r){return r.json()}).then(function(j){
    el("ma-pw-roster").innerHTML=((j&&j.students)||[]).map(function(x){return x&&x.name?'<option value="'+String(x.name).replace(/"/g,"&quot;")+'">':""}).join("");
  }).catch(function(){});
});
function boot(){
  if(!GOOGLE_ON)return;
  if(window.google&&google.accounts&&google.accounts.id&&window.__sdeGCb){
    try{google.accounts.id.initialize({client_id:GCID,callback:window.__sdeGCb,auto_select:true});}catch(e){}
    try{var g0=el("ma-gsi");if(g0){g0.style.display="";google.accounts.id.renderButton(g0,{theme:"outline",size:"medium",text:"signin_with",shape:"pill"});}}catch(e){}
    return;
  }
  if(tries++>24){var g=el("ma-gsi");if(g){g.style.display="";g.textContent="Google 登录组件加载失败，请检查网络后刷新。";}return;}
  setTimeout(boot,250);
}
boot();syncId();
setInterval(syncId,1200);
window.addEventListener("focus",syncId);
})();'''
h = h.replace(old_js, new_js, 1)
assert "GOOGLE_ON=false" in h and "统一 Google 登录身份" not in h
for t in ["div","section","script","style","button"]:
    o=len(re.findall(r"<%s[\s>]"%t,h)); c=len(re.findall(r"</%s>"%t,h))
    assert o==c,(t,o,c)
io.open(FP,"w",encoding="utf-8").write(h)
print("patched /meeting/index.html chars=",len(h))
