# -*- coding: utf-8 -*-
"""/meeting/ 参加会议：只填「学员名字 ＋ 会议号」即进视频教室。
   去掉密码这道门（社区/讨论区那边不受影响）；名字记在 localStorage sde_meet_name，
   若此人已在 /sde-wechat/ 或讨论区用社区账号登录过，默认带出那个名字。"""
import re, io
FP = "/home/claude/site/public/meeting/index.html"
h = io.open(FP, encoding="utf-8").read()
def rep(old, new, n=1):
    global h
    assert h.count(old) == n, (h.count(old), old[:80])
    h = h.replace(old, new, n)

# ① CSS：卡片也能闪一下；名字框窄一些
rep('.meet-auth.maflash{animation:maflash 0.9s ease 2}',
    '.meet-auth.maflash,.room-card.maflash{animation:maflash 0.9s ease 2}\n'
    'input.txt.nm{max-width:230px}')

# ② 身份条：去掉密码输入行，只留说明与当前名字
rep('<!-- 身份条：SDE 社区名字＋密码（Google 通道暂时关闭）-->', '<!-- 身份条：只显示当前名字；名字本身在下面「参加会议」里填 -->')
rep('<div id="ma-out" style="display:none">已进入 · 进入任何会议都会自动显示为 <b id="ma-name"></b> <a id="ma-signout">退出</a></div>',
    '<div id="ma-out" style="display:none">进入会议将显示为 <b id="ma-name"></b> <a id="ma-signout">换个名字</a></div>')
rep('<div id="ma-in">进入会议前，先用你在 <b>SDE 社区</b>的名字和密码进入——与社区、讨论区同一个账号，进会议自动带上你的名字，不用在教室里再输入。</div>',
    '<div id="ma-in">参加会议只要两样：<b>你的名字</b>和<b>会议号</b>——在下面「参加会议」里填好，点一下就进视频教室，不用登录、不用装软件。</div>')
rep('''    <span id="ma-gsi" style="display:none"></span>
  </div>
  <div class="ma-pw" id="ma-pw">
    <input id="ma-pw-name" list="ma-pw-roster" maxlength="20" autocomplete="off" placeholder="社区名字">
    <datalist id="ma-pw-roster"></datalist>
    <input id="ma-pw-code" type="password" autocomplete="current-password" placeholder="密码">
    <button class="btn" id="ma-pw-go">进入</button>
  </div>
  <div class="ma-msg" id="ma-msg"></div>''',
    '''  </div>
  <div class="ma-msg" id="ma-msg"></div>''')

# ③ 参加会议卡：名字 ＋ 会议号 ＋ 进入
rep('''  <div class="room-card">
    <h3>输入会议号</h3>
    <p>不在列表里的会议，输入会议号加入：数字号（9–11 位）自动走 Zoom；字母教室名进对应视频教室。</p>
    <div class="row">
      <input class="txt" id="meetCode" maxlength="60" placeholder="会议号，如 123 4567 8901 或 sde-group-3">
      <button class="btn" onclick="joinByCode()">加入会议</button>
    </div>''',
    '''  <div class="room-card" id="joincard">
    <h3>参加会议</h3>
    <p>填两样就进：<b>你的名字</b>和<b>会议号</b>。教室名（可含中文、字母、数字）进对应视频教室；数字号（9–11 位）自动走 Zoom。名字本机会记住，下次只填会议号。</p>
    <div class="row">
      <input class="txt nm" id="joinName" list="meet-roster" maxlength="20" autocomplete="off" placeholder="你的名字（学员名字）">
      <datalist id="meet-roster"></datalist>
      <input class="txt" id="meetCode" maxlength="60" placeholder="会议号，如 SDE-Group-3 或 123 4567 8901">
      <button class="btn" onclick="joinByCode()">进入会议</button>
    </div>
    <div class="ma-msg" id="join-msg"></div>''')

# ④ 正文说明
rep('<p>点「进入教室」即在新标签页打开，自动带上你的社区名字，不限时长。开课时间以下方讨论区预告为准。</p>',
    '<p>点「进入教室」即在新标签页打开，自动带上你填的名字，不限时长。开课时间以下方讨论区预告为准。</p>')
rep('<li>在本页顶部用你在 SDE 社区的名字和密码进入一次（与社区、讨论区同一个账号，本机会记住半天）——之后进入任何会议都会自动显示你的名字，不用在教室里再登录或改名。</li>',
    '<li>在「参加会议」里填上你的名字（本机会记住，下次自动带出）——之后点任何教室都会自动显示这个名字，不用在教室里再登录或改名。</li>')
rep('<li><b>开房：</b>提前十分钟点「进入 SDE 大教室」，先进者即成为主持人；学生同样用各自社区名字和密码进入。</li>',
    '<li><b>开房：</b>提前十分钟点「进入 SDE 大教室」，先进者即成为主持人；学生填各自名字＋会议号即可进入。</li>')
rep('<li>实名显示：全站同一个社区账号，进会议自动带真名</li>',
    '<li>实名显示：填一次名字，进任何会议自动带上</li>')

# ⑤ joinRoom / joinByCode：名字来自输入框，不再拦登录
rep('''function meetNeedLogin(){var m=document.getElementById("ma-msg");if(m){m.textContent="进入会议前，请先在上方用社区名字和密码进入——进会议会自动显示你的名字。";m.className="ma-msg";}var f=document.getElementById("ma-pw-name");if(f)try{f.focus()}catch(e){}var a=document.getElementById("meet-auth");if(a){a.classList.remove("maflash");void a.offsetWidth;a.classList.add("maflash");a.scrollIntoView({behavior:"smooth",block:"center"});}}''',
    '''function meetNeedLogin(){if(window.meetNeedName)window.meetNeedName();}''')
rep('''function joinRoom(r){
  r=canonicalRoom(r);
  if(!r){alert("会议号无效");return}
  if(!window.SDE_MEET_NAME){meetNeedLogin();return}
  window.open(roomUrl(r),"_blank","noopener");
}''',
    '''function joinRoom(r){
  r=canonicalRoom(r);
  if(!r){alert("会议号无效");return}
  var nm=window.SDE_MEET_REMEMBER?window.SDE_MEET_REMEMBER(window.SDE_MEET_PICK()):window.SDE_MEET_NAME;
  if(!nm){if(window.meetNeedName)window.meetNeedName();return}
  window.open(roomUrl(r),"_blank","noopener");
}''')
rep('''function joinByCode(){
  var v=(document.getElementById("meetCode").value||"").trim();
  if(!v){alert("请先输入会议号");return}''',
    '''function joinByCode(){
  var nm=window.SDE_MEET_PICK?window.SDE_MEET_PICK():"";
  if(!nm){if(window.meetNeedName)window.meetNeedName();return}
  var v=(document.getElementById("meetCode").value||"").trim();
  if(!v){if(window.meetNeedCode)window.meetNeedCode();return}
  window.SDE_MEET_REMEMBER(nm);''')
rep('''  var room=canonicalRoom(v);
  if(!room){alert("会议号是 9-11 位数字（Zoom），或教室名（可含中文、字母、数字）");return}
  joinRoom(room);''',
    '''  var room=canonicalRoom(v);
  if(!room){if(window.meetSay)window.meetSay("会议号是 9–11 位数字（Zoom），或教室名（可含中文、字母、数字）。",1);return}
  joinRoom(room);''')

# ⑥ 身份脚本整段替换
START='// ===== 身份：SDE 社区名字＋密码 ====='
END='boot();syncId();\nsetInterval(syncId,1200);\nwindow.addEventListener("focus",syncId);\n})();'
i0=h.index(START); i1=h.index(END)+len(END)
new_js='''// ===== 身份：一个名字就够 =====
// 参加会议＝名字 ＋ 会议号，本页不设登录门（社区 /sde-wechat/ 与文章讨论区的名字+密码那道门不受影响）。
// 名字记在 localStorage sde_meet_name；若此人已在社区或讨论区登录过（sde_gauth / sde_talk_id），默认带出那个名字。
(function(){
function el(id){return document.getElementById(id)}
var NKEY="sde_meet_name",SKEY="sde_gauth",LKEY="sde_talk_id";
window.SDE_MEET_NAME="";
function jget(store,k){try{return JSON.parse(store.getItem(k)||"null")}catch(e){return null}}
function alive(o){return !!(o&&o.cred&&o.exp>Date.now())}
function communityName(){var s=jget(sessionStorage,SKEY);if(alive(s)&&s.name)return s.name;var l=jget(localStorage,LKEY);if(alive(l)&&l.name)return l.name;return""}
function remembered(){try{return String(localStorage.getItem(NKEY)||"").slice(0,20)}catch(e){return ""}}
function typed(){var f=el("joinName");return f?(f.value||"").trim().slice(0,20):""}
function paint(){
  var nm=window.SDE_MEET_NAME||"",o=el("ma-out"),i=el("ma-in"),n=el("ma-name");
  if(nm){if(n)n.textContent=nm;if(o)o.style.display="block";if(i)i.style.display="none";}
  else{if(o)o.style.display="none";if(i)i.style.display="block";}
}
function jsay(t,bad){var m=el("join-msg");if(m){m.textContent=t||"";m.className="ma-msg"+(bad?" bad":"")}}
window.meetSay=jsay;
// 取名字：先看输入框，再看本机记住的，再看社区身份
window.SDE_MEET_PICK=function(){return typed()||remembered()||communityName()};
window.SDE_MEET_REMEMBER=function(nm){
  nm=String(nm||"").trim().slice(0,20);
  if(!nm)return "";
  try{localStorage.setItem(NKEY,nm)}catch(e){}
  window.SDE_MEET_NAME=nm;
  var f=el("joinName");if(f&&(f.value||"").trim()!==nm)f.value=nm;
  paint();jsay("");
  return nm;
};
window.meetNeedName=function(){
  jsay("先填一下你的名字，会议里会用它显示。",1);
  var f=el("joinName");if(f)try{f.focus()}catch(e){}
  var c=el("joincard");if(c){c.classList.remove("maflash");void c.offsetWidth;c.classList.add("maflash");try{c.scrollIntoView({behavior:"smooth",block:"center"})}catch(e){}}
};
window.meetNeedCode=function(){jsay("再填一下会议号。",1);var f=el("meetCode");if(f)try{f.focus()}catch(e){}};
var so=el("ma-signout");
if(so)so.onclick=function(){
  try{localStorage.removeItem(NKEY)}catch(e){}
  window.SDE_MEET_NAME="";
  var f=el("joinName");if(f){f.value="";try{f.focus()}catch(e){}}
  paint();jsay("换个名字：填好后再点「进入会议」。");
};
var rosterLoaded=false;
function loadRoster(){
  if(rosterLoaded)return;rosterLoaded=true;
  fetch("/students/roster.json").then(function(r){return r.json()}).then(function(j){
    var dl=el("meet-roster");if(!dl)return;
    dl.innerHTML=((j&&j.students)||[]).map(function(x){return x&&x.name?'<option value="'+String(x.name).replace(/"/g,"&quot;")+'">':""}).join("");
  }).catch(function(){});
}
(function boot(){
  var f=el("joinName"),c=el("meetCode");
  var init=remembered()||communityName();
  if(f&&!(f.value||"").trim()&&init)f.value=init;
  window.SDE_MEET_NAME=typed()||init||"";
  paint();
  if(f){
    f.addEventListener("input",function(){window.SDE_MEET_NAME=typed();paint()});
    f.addEventListener("focus",loadRoster);
    f.addEventListener("keydown",function(e){if(e.key!=="Enter")return;if(c&&!(c.value||"").trim()){try{c.focus()}catch(e2){}}else joinByCode()});
  }
  if(c)c.addEventListener("keydown",function(e){if(e.key==="Enter")joinByCode()});
})();
})();'''
h=h[:i0]+new_js+h[i1:]
assert "SDE_MEET_PICK" in h and "sdepw1" not in h and "GOOGLE_ON" not in h
for t in ["div","section","script","style","button"]:
    o=len(re.findall(r"<%s[\s>]"%t,h)); c=len(re.findall(r"</%s>"%t,h))
    assert o==c,(t,o,c)
io.open(FP,"w",encoding="utf-8").write(h)
print("patched /meeting/index.html chars=",len(h))
