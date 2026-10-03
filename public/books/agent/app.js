(function(){
"use strict";
var $=function(id){return document.getElementById(id)};
var API="/api/wds/read",PAPER="/api/wds/read-paper";
var GATES=[
 {k:"read",n:"壹",t:"读懂",d:"把这本书读明白：一个词、一步论证、全书骨架",ph:"哪里没读懂？说一个词、一句话或一章……",starts:["这本书最承重的那一句话是什么？在哪一章？","用一个日常生活的例子，把全书的主张讲给我听","我读到这里卡住了：……"]},
 {k:"apply",n:"贰",t:"用上",d:"把书里的方法用到你自己的事上",ph:"说说你想用这本书解决的那件事：现场、卡在哪、试过什么……",starts:["我有一件具体的事，想用这本书的方法走一遍：……","这本书的方法，用在孩子教育上会是什么样？","这本书的方法在什么情况下不适用？"]},
 {k:"cut",n:"叁",t:"拆开",d:"解构这本书：拆一处缝，补一处骨",ph:"想拆哪一处？或者让它先找出全书最大的那道缝……",starts:["这本书把什么当作给定，因此看不见什么？","找出这本书里最大的一道缝隙，并给出补法","先说这本书最强的地方，再动刀"]},
 {k:"clash",n:"肆",t:"对撞",d:"拿它撞你的思想、另一位大师或另一本书",ph:"拿它和谁撞？你的一个想法、一位思想家、或另一本书……",starts:["你推荐这本书最该撞的敌意最近邻是谁？撞一撞","拿这本书和我的这个想法撞一撞：……","拿这本书和库恩的《科学革命的结构》撞一撞"]},
 {k:"write",n:"伍",t:"写出",d:"把长出来的新命题定题、定纲，写成论文或专著",ph:"想写什么？让它先认出这场对话里真正新的那个命题……",starts:["这场对话里，哪个命题真正是新的、值得写成论文？","帮我把它定题：标题、承重命题、敌意最近邻、可错预言","给我一份六节论文提纲，标清来源"]}
];
var BOOK=null,CH=[],SEL=null,act="read",hist=[],busy=false,HK="";
function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
function ls(k,v){try{if(v===undefined)return localStorage.getItem(k);if(v===null)localStorage.removeItem(k);else localStorage.setItem(k,v)}catch(e){return null}}
function path(u){try{var x=new URL(u,location.origin);return x.pathname+x.search}catch(e){return u||""}}
function fail(msg){$("ldmsg").innerHTML=msg}
var CFG=window.BOOK_AGENT||{};
var mno=parseInt(CFG.no||new URLSearchParams(location.search).get("m"),10);
if(!mno){fail('没有指定书号。请从<a href="/books/">专著书架</a>里任选一本进来。');return}
HK="sde_shusheng_m"+mno;
var AG={name:"书生",epithet:"",intro:"",starts:{}},RAG=null;

/* —— 1. 找书：catalog.json —— */
function J(u){return fetch(u,{cache:"no-cache"}).then(function(r){return r.ok?r.json():null}).catch(function(){return null})}
Promise.all([J("/books/catalog.json"),J("/books/agents.json"),J("/books/m/"+mno+"/rag.json")]).then(function(a){
 var c=a[0]||{};if(a[1]&&a[1].agents&&a[1].agents[mno])AG=a[1].agents[mno];RAG=a[2];
 return c;
}).then(function(c){
 var b=(c.books||[]).filter(function(x){return x.number===mno})[0];
 if(!b)throw new Error("书架里没有第 "+mno+" 号");
 BOOK=b;
 var tu=b.textUrl||b.chapterUrl||("/books/m/"+mno+"/text/");
 $("ldmsg").textContent="「"+AG.name+"」正在逐字通读《"+b.title+"》……";
 var tp=path(tu);
 return fetch(tp).then(function(r){return r.ok?r.text():""}).then(function(html){
  if(!html)return;   /* 没有全文网页：书生凭书目介绍陪聊 */
  var d=new DOMParser().parseFromString(html,"text/html");
  var subs=subLinks(d,tp);
  CH=chapters(d);
  /* 分章子页的书（全文页只是目录）：逐章取回，一章一页 */
  if(total()<20000&&subs.length)return fetchSubs(subs);
 });
}).then(function(){
 if(CH.length&&BOOK&&CH[0].t===BOOK.title&&CH[0].n<200)CH.shift();
 boot();
}).catch(function(e){fail("没能打开这本书："+esc(e&&e.message)+'。<a href="/books/">回到书架</a>')});

/* —— 2. 抽全文、分章 —— 适配站上各代全文页：h1/h2 作章，h2.sec/h3 作节；只有目录的，逐章取子页 —— */
function subLinks(d,tp){
 var base=tp.split("?")[0].replace(/\/?$/,"/"),seen={},out=[];
 d.querySelectorAll("a[href]").forEach(function(a){
  var u=path(new URL(a.getAttribute("href"),location.origin+base).href).split("#")[0].split("?")[0];
  if(u.indexOf(base)!==0||u===base||seen[u])return;
  var rest=u.slice(base.length).replace(/\/$/,"");if(!rest||rest.indexOf("/")>=0)return;
  seen[u]=1;out.push({u:u,t:(a.textContent||"").replace(/\s+/g," ").trim().slice(0,60)});
 });
 return out;
}
function fetchSubs(subs){
 var res=new Array(subs.length),i=0;
 function one(){var k=i++;if(k>=subs.length)return Promise.resolve();
  $("ldmsg").textContent="正在逐章通读："+(k+1)+" / "+subs.length;
  return fetch(subs[k].u).then(function(r){return r.ok?r.text():""}).then(function(t){
   if(t){var d=new DOMParser().parseFromString(t,"text/html");var cs=chapters(d,true);var x=cs.map(function(c){return c.x}).join("\n");res[k]={t:subs[k].t||(cs[0]&&cs[0].t)||("第"+(k+1)+"章"),x:x,n:x.length}}
  }).catch(function(){}).then(one)}
 return Promise.all([one(),one(),one(),one()]).then(function(){CH=res.filter(function(c){return c&&c.n>40})});
}
function chapters(d,flat){
 d.querySelectorAll("script,style,nav,header,footer,noscript,.crumb,.toc,#toc,.sde-talk,#sde-talk,.foot").forEach(function(x){x.remove()});
 var root=d.querySelector("article")||d.querySelector("main")||d.querySelector(".wrap")||d.body;
 var hasChap=!!root.querySelector("h2.chap-title,h1.front-title");
 var CHAPSEL=hasChap?"h1.front-title,h2.chap-title,h1.part-title,h1.vol-title,.part-title":"h1,h2";
 if(flat)CHAPSEL="h1";
 var nodes=root.querySelectorAll(CHAPSEL+",h2,h3,h4,p,li,blockquote,pre,td,th,dt,dd,figcaption");
 var cur={t:"开篇",s:[]},out=[cur],chapSet=new Set(root.querySelectorAll(CHAPSEL));
 nodes.forEach(function(n){
  if(n.closest("li")&&n.tagName!=="LI")return;           /* 列表里的段只取一次 */
  if(n.tagName==="P"&&n.closest("blockquote,td,li"))return;
  var t=(n.textContent||"").replace(/\s+/g," ").trim(); if(!t)return;
  if(chapSet.has(n)){cur={t:t.slice(0,60),s:[]};out.push(cur);return}
  if(/^H[234]$/.test(n.tagName)){cur.s.push("\n〔"+t+"〕");return}
  cur.s.push(t);
 });
 return out.map(function(c){var tx=c.s.join("\n");return{t:c.t,x:tx,n:tx.length}}).filter(function(c){return c.n>40||c.t!=="开篇"});
}
var BUDGET=116000;   /* 服务端书生档收 12 万字符；留出目录与章名的余量 */
function total(){return CH.reduce(function(a,c){return a+c.n},0)}
function defaultSel(){var s=[],u=0;for(var i=0;i<CH.length;i++){if(u+CH[i].n>BUDGET*0.82)break;s.push(i);u+=CH[i].n}return s}
function loadSel(){var v=ls(HK+"_sel");if(v){try{var a=JSON.parse(v);if(Array.isArray(a))return a.filter(function(i){return i>=0&&i<CH.length})}catch(e){}}return null}
function docText(cap){
 if(!CH.length)return "";
 var B=cap||BUDGET,T=total(),fmt=function(c){return "【"+c.t+"】\n"+c.x};
 if(T<=B)return CH.map(fmt).join("\n\n");
 /* 成文时只能带约 6 万字：优先保住读者选的章，再按章序补，余下读目录与开头 */
 var sel=(SEL||defaultSel()).slice(),on={},used=0;
 if(cap){var keep=[];sel.forEach(function(i){if(used+CH[i].n<=B*0.8){keep.push(i);used+=CH[i].n}});sel=keep}
 sel.forEach(function(i){on[i]=1});
 var toc="【全书目录（共 "+CH.length+" 章，约 "+Math.round(T/1000)+" 千字；本场逐字读的是标★的章，其余只读开头）】\n"+CH.map(function(c,i){return(on[i]?"★ ":"· ")+c.t}).join("\n");
 var body=CH.map(function(c,i){return on[i]?fmt(c):("【"+c.t+"（开头）】\n"+c.x.slice(0,260)+"……")}).join("\n\n");
 return (toc+"\n\n"+body).slice(0,cap?cap:119000);
}
function readInfo(){
 var T=total();
 if(!CH.length){$("readInfo").innerHTML="这本书在站上还没有全文网页，「"+esc(AG.name)+"」只能凭书目介绍和你聊。";return}
 if(T<=BUDGET){$("readInfo").innerHTML="「"+esc(AG.name)+"」已逐字通读<b>全书</b> · "+CH.length+" 章 · 约 "+(T/10000).toFixed(1)+" 万字";return}
 var s=SEL||defaultSel(),u=s.reduce(function(a,i){return a+CH[i].n},0);
 $("readInfo").innerHTML="全书约 "+(T/10000).toFixed(1)+" 万字，超过一次能读的上限。「"+esc(AG.name)+"」逐字读<b>"+s.length+" 章</b>（约 "+(u/10000).toFixed(1)+" 万字），其余读目录与开头。<button type='button' id='pickBtn'>换章 ›</button>";
 $("pickBtn").onclick=pickChapters;
}

/* —— 3. 起页 —— */
function boot(){
 var b=BOOK;
 document.title=AG.name+" · 《"+b.title+"》的智能体 | 德麦国际专著第 "+b.number+" 号";
 $("agName").textContent=AG.name;$("agEpi").textContent=AG.epithet||"这本书的智能体";
 $("agTag").textContent=AG.intro||("我只为《"+b.title+"》而生：陪你读懂它、用上它、拆开它、拿它去对撞，再把碰出来的新东西写成论文，甚至一部新专著。");
 ragInfo();
 $("bt").textContent=b.title; $("bs").textContent=(b.subtitle?b.subtitle+" · ":"")+(b.authors||[]).join("、")+" 著 · 德麦国际专著第 "+b.number+" 号";
 if(b.coverUrl){$("cov").src=path(b.coverUrl);$("cov").hidden=false}
 $("detailA").href=path(b.detailUrl); $("readA").href=path(b.readUrl||b.textUrl||b.detailUrl);
 SEL=loadSel(); readInfo();
 GATES.forEach(function(g){
  var x=document.createElement("button");x.type="button";x.className="gate";x.dataset.k=g.k;
  x.innerHTML="<span class='n'>"+g.n+"</span><div><b>"+g.t+"</b><span>"+g.d+"</span></div>";
  x.onclick=function(){setAct(g.k,true)};$("gates").appendChild(x);
  var y=document.createElement("button");y.type="button";y.className="gb";y.dataset.k=g.k;y.textContent=g.t;
  y.onclick=function(){setAct(g.k,false)};$("gbar").appendChild(y);
 });
 try{hist=JSON.parse(ls(HK)||"[]")||[]}catch(e){hist=[]}
 $("loading").hidden=true;$("app").hidden=false;
 setAct(ls(HK+"_act")||"read",false);
 render();
 $("send").onclick=send;
 $("q").addEventListener("keydown",function(e){if(e.key==="Enter"&&!e.shiftKey&&!e.isComposing){e.preventDefault();send()}});
 $("q").addEventListener("input",grow);
 $("keyBtn").onclick=function(){keyPanel(null)};
 $("clrBtn").onclick=function(){if(!hist.length||confirm("清空这一场对话？（只清你浏览器里的这一份）")){hist=[];save();render()}};
 $("oPaper").onclick=function(){writeOut("paper")};
 $("oMono").onclick=function(){writeOut("mono")};
 $("oSum").onclick=summary;
 paint();
}
function grow(){var t=$("q");t.style.height="auto";t.style.height=Math.min(200,t.scrollHeight)+"px"}
function gateOf(k){return GATES.filter(function(g){return g.k===k})[0]||GATES[0]}
function setAct(k,fromSide){
 act=gateOf(k).k; ls(HK+"_act",act);
 document.querySelectorAll(".gate,.gb").forEach(function(x){x.setAttribute("aria-pressed",x.dataset.k===act?"true":"false")});
 var g=gateOf(act);$("q").placeholder=g.ph;
 $("now").innerHTML="「"+esc(AG.name)+"」 · <b>"+esc(BOOK.title)+"</b> · 第"+g.n+"道门「"+g.t+"」";
 $("hint").textContent="这一问走「"+g.t+"」："+g.d+"。换门只需点上面的标签。";
 fillStarts();
 if(fromSide)$("q").focus();
}
function save(){ls(HK,JSON.stringify(hist.slice(-200)))}
function paint(){
 var n=hist.filter(function(m){return m.role==="reader"}).length;
 $("send").disabled=busy;
 ["oPaper","oMono","oSum"].forEach(function(id){$(id).disabled=busy||n<2});
 $("oPaper").title=$("oMono").title=n<2?"先聊上几轮，聊出新东西来再写":"";
}

/* —— 3b. 专属碰撞库：每本书提前打造（tools/build_book_rag.py）；每一问按问题挑出最相撞的几条递上去 —— */
function grams(s){var g={},t=String(s||"").replace(/[^\u4e00-\u9fff]/g,"");for(var i=0;i<t.length-1;i++)g[t.substr(i,2)]=1;return g}
function lastAns(){for(var i=hist.length-1;i>=0;i--)if(hist[i].role==="wds")return String(hist[i].text).slice(0,600);return ""}
function ragPick(q,a,k){
 var items=(RAG&&RAG.items)||[];if(!items.length)return{text:"",items:[]};
 var g=grams(q),sc=items.map(function(it,i){
  var h=grams(it.t+it.ch+(it.kw||[]).join("")+it.x),o=0;for(var x in g)if(h[x])o++;
  var s=o+it.s*20;if((a==="clash"||a==="cut")&&it.rel==="跨界")s+=4;if((a==="clash"||a==="cut")&&it.rel==="同源")s-=6;
  return{i:i,s:s};
 }).sort(function(x,y){return y.s-x.s}).slice(0,k);
 var pick=sc.map(function(x){return items[x.i]});
 var idx="【本书碰撞库总目（共 "+items.length+" 条）】"+items.map(function(it){return "《"+it.t.replace(/[｜|].*$/,"").slice(0,24)+"》"}).join("、");
 var text=pick.map(function(it){return "〔"+it.rel+"·"+(it.kind==="book"?"专著":"文章")+"〕《"+it.t+"》"+(it.sch?"「"+it.sch+"」":"")+"——撞本书「"+it.ch+"」；共有："+(it.kw||[]).join("、")+"\n"+it.x}).join("\n\n");
 return{text:(idx+"\n\n"+text).slice(0,15500),items:pick};
}
function ragInfo(){
 var items=(RAG&&RAG.items)||[],box=$("ragInfo");
 if(!items.length){box.innerHTML="这本书的专属碰撞库还在打造；这期间对撞时会现场检索全站。";return}
 var nb=items.filter(function(x){return x.kind==="book"}).length,na=items.length-nb,cr=items.filter(function(x){return x.rel==="跨界"}).length;
 box.innerHTML="为这本书提前配好 <b>"+items.length+"</b> 个碰撞点：<b>"+nb+"</b> 本专著 · <b>"+na+"</b> 篇文章，其中跨界 "+cr+" 个。<button type='button' id='ragBtn'>看看撞谁 ›</button>";
 $("ragBtn").onclick=ragList;
}
function ragList(){
 var items=(RAG&&RAG.items)||[];
 var o=document.createElement("div");o.className="ov";
 var rows=items.map(function(it,i){return "<div class='rg'><div class='rgh'><i class='r-"+(it.rel==="跨界"?"x":it.rel==="同源"?"s":"t")+"'>"+esc(it.rel)+"</i><a href='"+esc(path(it.u))+"' target='_blank' rel='noopener'>"+esc(it.t)+"</a><em>"+(it.kind==="book"?"专著":"文章")+"</em></div><div class='rgc'>撞本书「"+esc(it.ch)+"」"+((it.kw||[]).length?" · 共有："+esc(it.kw.join("、")):"")+"</div><div class='rgx'>"+esc(it.x.slice(0,150))+"……</div><button type='button' class='chip rgb' data-i='"+i+"'>拿它来撞</button></div>"}).join("");
 o.innerHTML="<div class='box' role='dialog' aria-label='专属碰撞库'><div class='hd'><b>「"+esc(AG.name)+"」的专属碰撞库</b><button class='tbtn' data-x>×</button></div><div class='bd rgl'><p class='rgn'>从站上全部专著与文章里，按本书各章检索出的最相撞的段落（"+esc(RAG.built||"")+" 建）。<b>同源</b>＝这本书的前身或姊妹篇，<b>同向</b>＝同一方向的近邻，<b>跨界</b>＝别的书架、别的领域。</p>"+rows+"</div></div>";
 document.body.appendChild(o);
 o.querySelector("[data-x]").onclick=function(){o.remove()};
 o.querySelectorAll(".rgb").forEach(function(b){b.onclick=function(){var it=items[+b.dataset.i];o.remove();setAct("clash",false);$("q").value="拿《"+it.t.replace(/[｜|].*$/,"")+"》里这一段，撞本书「"+it.ch+"」那一章：两边共有的前提是什么？撞出一个新命题。";send()}});
}

/* —— 4. 显示 —— */
function fmt(s){
 var h=esc(s).replace(/\*\*([^*\n]{1,120})\*\*/g,"<b>$1</b>").replace(/^#{1,4}\s*/gm,"");
 return h.split(/\n{2,}|\n(?=[一二三四五六七八九十①②③④⑤⑥⑦⑧⑨]+[、．.）)]|\d+[.、）)]|〔)/).map(function(p){return "<p>"+p.replace(/\n/g,"<br>")+"</p>"}).join("");
}
function render(){
 var col=$("col");col.innerHTML="";
 var g=gateOf(act),b=BOOK;
 var hello=document.createElement("div");hello.className="hello";
 hello.innerHTML="<h2>我是「"+esc(AG.name)+"」<small>《"+esc(b.title)+"》的智能体</small></h2>"
  +(AG.intro?"<p>"+esc(AG.intro)+"</p>":"")
  +"<p>"+(CH.length?(total()<=BUDGET?"这本书我已逐字读过。":"这本书的目录、开头和左边标出的那几章，我已逐字读过；想深谈别的章，点左边「换章」。"):"")+"你可以从五道门里任走一道：<b>读懂</b>它，把它<b>用上</b>，把它<b>拆开</b>，拿它去<b>对撞</b>，最后把碰出来的新东西<b>写出</b>来——一篇论文，甚至一部新专著。</p>"
  +"<p style='color:var(--dim);font-size:13px'>书里的话我照原文引，并标出章名；我推出来的，我会说明是推论；你提出来的，记在你名下。这本账就是你将来那篇论文的底稿。</p>"
  +"<div class='starts' id='starts'></div>";
 col.appendChild(hello);
 fillStarts();
 hist.forEach(function(m){add(m.role,m.text,m.act,m.srcs)});
 scroll();
}
function fillStarts(){
 var box=$("starts");if(!box)return;box.innerHTML="";
 var own=AG.starts&&AG.starts[act],ss=gateOf(act).starts.slice();if(own){ss=[own].concat(ss.slice(0,2))}
 ss.forEach(function(s){var c=document.createElement("button");c.type="button";c.className="chip";c.textContent=s;c.onclick=function(){var t=$("q");if(/……$/.test(s)){t.value=s.replace(/……$/,"");t.focus();grow()}else{t.value=s;send()}};box.appendChild(c)});
}
function add(role,text,a,srcs){
 var w=document.createElement("div");w.className="m "+(role==="reader"?"me":"ai");
 var bub=document.createElement("div");bub.className="bub";w.appendChild(bub);
 if(role==="reader")bub.textContent=text;
 else{bub.innerHTML=(a?"<span class='gtag'>"+esc(gateOf(a).t)+"</span>":"")+"<div class='tx'>"+fmt(text||"")+"</div>";if(srcs&&srcs.length)bub.appendChild(srcBox(srcs));if(text)bub.appendChild(actBox(text))}
 $("col").appendChild(w);return bub;
}
function srcBox(s){var d=document.createElement("div");d.className="srcs";d.innerHTML="这一问带上的碰撞点："+s.slice(0,6).map(function(x){return (x.rel?"<i>"+esc(x.rel)+"</i>":"")+"<a href='"+esc(path(x.u||x.url||"/books/"))+"' target='_blank' rel='noopener'>"+esc(x.t||x.title||"篇目")+"</a>"}).join(" · ");return d}
function actBox(text){
 var d=document.createElement("div");d.className="acts";
 var c=document.createElement("button");c.type="button";c.textContent="复制";c.onclick=function(){try{navigator.clipboard.writeText(text);c.textContent="已复制";setTimeout(function(){c.textContent="复制"},1500)}catch(e){}};
 d.appendChild(c);
 [["cut","拆开这一答"],["clash","拿这一答去对撞"]].forEach(function(p){var x=document.createElement("button");x.type="button";x.textContent=p[1];x.onclick=function(){setAct(p[0],false);$("q").value=p[0]==="cut"?"拆开你上一答：它把什么当作了给定？哪一句最经不起追问？":"拿你上一答去撞它最强的敌意最近邻，撞出一个新命题。";send()};d.appendChild(x)});
 return d;
}
function scroll(){var m=$("msgs");m.scrollTop=m.scrollHeight}

/* —— 5. Key —— */
function keyGet(){var k=(ls("sde_wds_key")||"").trim(),v=ls("sde_wds_vendor")||"ds";if(k.length>=8)return{key:k,vendor:v};var d=(ls("sde_ds_key")||"").trim();if(d.length>=8)return{key:d,vendor:"ds"};var g=(ls("sde_glm_key")||"").trim();if(g.length>=8)return{key:g,vendor:"glm"};return null}
function keyPanel(cb){
 var cur=keyGet()||{key:"",vendor:"ds"},v=cur.vendor;
 var o=document.createElement("div");o.className="ov";
 o.innerHTML="<div class='box kbox' role='dialog' aria-label='设置 API Key'><div class='hd'><b>用你自己的大模型 Key</b><button class='tbtn' data-x>×</button></div><div class='bd'>书生用你自己的 Key 运行。<b style='color:var(--gold)'>Key 只存在你的浏览器本地，不会上传本站</b>，随时可清除。与站内 ChatSDE、陪读共用同一把。"
 +"<div class='kv'><button type='button' data-v='ds'>DeepSeek</button><button type='button' data-v='glm'>智谱 GLM</button></div><input class='kin' type='password' placeholder='粘贴你的 API Key' aria-label='API Key'><div class='small' data-l></div></div>"
 +"<div class='ft'><span class='pg'></span><button class='out' data-s type='button'>保存并开始</button></div></div>";
 document.body.appendChild(o);
 var kin=o.querySelector(".kin");kin.value=cur.key;
 function pv(){o.querySelectorAll("[data-v]").forEach(function(b){b.setAttribute("aria-pressed",b.dataset.v===v?"true":"false")});o.querySelector("[data-l]").innerHTML=v==="ds"?"还没有 Key？去 <a href='https://platform.deepseek.com' target='_blank' rel='noopener'>platform.deepseek.com</a> 申请":"还没有 Key？去 <a href='https://open.bigmodel.cn' target='_blank' rel='noopener'>open.bigmodel.cn</a> 申请"}
 o.querySelectorAll("[data-v]").forEach(function(b){b.onclick=function(){v=b.dataset.v;pv()}});pv();
 o.querySelector("[data-x]").onclick=function(){o.remove()};
 o.querySelector("[data-s]").onclick=function(){var k=kin.value.trim();if(k.length<8){kin.style.borderColor="var(--err)";return}ls("sde_wds_key",k);ls("sde_wds_vendor",v);ls(v==="glm"?"sde_glm_key":"sde_ds_key",k);o.remove();if(cb)cb()};
 setTimeout(function(){kin.focus()},60);
}

/* —— 6. 对话（SSE）—— */
function meta(){var b=BOOK;return "德麦国际专著第"+b.number+"号 · "+(b.authors||[]).join("、")+" 著"+(b.subtitle?" · "+b.subtitle:"")}
function sse(resp,on){
 if(!resp.ok||!resp.body)throw new Error("HTTP "+resp.status);
 var rd=resp.body.getReader(),dec=new TextDecoder(),buf="";
 function pump(){return rd.read().then(function(r){
  if(r.done)return;
  buf+=dec.decode(r.value,{stream:true});var i;
  while((i=buf.indexOf("\n"))>=0){var line=buf.slice(0,i).trim();buf=buf.slice(i+1);if(line.slice(0,5)!=="data:")continue;var p=line.slice(5).trim();if(p==="[DONE]")continue;var j;try{j=JSON.parse(p)}catch(e){continue}on(j)}
  return pump();
 })}
 return pump();
}
function send(){
 var t=$("q"),q=t.value.trim();if(!q||busy)return;
 var kv=keyGet();if(!kv){keyPanel(send);return}
 t.value="";grow();
 var a=act;
 add("reader",q);hist.push({role:"reader",text:q,act:a});save();
 var bub=add("wds","",a),tx=bub.querySelector(".tx");tx.innerHTML="<span class='think'>「"+esc(AG.name)+"」正在想……</span>";
 busy=true;paint();scroll();
 var ans="",srcs=[],notes=[];
 var rp=ragPick(q+" "+lastAns(),a,10);
 var body={q:q,bookagent:1,act:a,agentName:AG.name,agentEpithet:AG.epithet||"",bookRag:rp.text,bookMeta:meta(),docTitle:BOOK.title,docText:docText(),history:hist.slice(0,-1).map(function(m){return{role:m.role,text:m.text}}),key:kv.key,vendor:kv.vendor};
 fetch(API,{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify(body)}).then(function(r){
  return sse(r,function(j){
   if(j.t==="token"){ans+=j.v;tx.innerHTML=fmt(ans);scroll()}
   else if(j.t==="think"&&!ans){tx.innerHTML="<span class='think'>「"+esc(AG.name)+"」正在想……</span>"}
   else if(j.t==="sources"&&Array.isArray(j.v)){srcs=j.v}
   else if(j.t==="note"){notes.push(j.v)}
   else if(j.t==="error"){var e=document.createElement("div");e.className="err";e.textContent=j.v;bub.appendChild(e);if(j.code==="need_key"||j.code==="bad_key")setTimeout(function(){keyPanel(null)},300)}
  });
 }).catch(function(e){var x=document.createElement("div");x.className="err";x.textContent="接不上「"+AG.name+"」（"+(e&&e.message)+"）。检查网络后再问一次——你刚才那句已记下。";bub.appendChild(x)}).then(function(){
  if(rp.items.length&&(a==="clash"||a==="cut"))srcs=rp.items.slice(0,5).map(function(it){return{t:it.t,u:it.u,rel:it.rel}});
  if(ans){hist.push({role:"wds",text:ans,act:a,srcs:srcs});save();if(srcs.length)bub.appendChild(srcBox(srcs));bub.appendChild(actBox(ans))}
  else if(tx.querySelector(".think"))tx.innerHTML="";
  if(notes.length){var n=document.createElement("div");n.className="note";n.textContent=notes.join("；");bub.appendChild(n)}
  busy=false;paint();scroll();
 });
}

/* —— 7. 写出来：论文 / 专著立项 / 小结 —— */
function modal(title){
 var o=document.createElement("div");o.className="ov";
 o.innerHTML="<div class='box' role='dialog'><div class='hd'><b></b><button class='tbtn' data-x>×</button></div><div class='bd'></div><div class='ft'><span class='pg'></span><button class='tbtn' data-c type='button'>复制全文</button><button class='tbtn' data-p type='button'>导出 PDF</button><a class='tbtn' href='/students/submit/' target='_blank' rel='noopener'>投给德麦</a></div></div>";
 document.body.appendChild(o);
 var hd=o.querySelector(".hd b"),bd=o.querySelector(".bd"),pg=o.querySelector(".pg");hd.textContent=title;
 o.querySelector("[data-x]").onclick=function(){o.remove()};
 o.querySelector("[data-c]").onclick=function(){try{navigator.clipboard.writeText(bd.textContent);pg.textContent="已复制"}catch(e){}};
 o.querySelector("[data-p]").onclick=function(){printDoc(bd.textContent)};
 return{bd:bd,pg:pg,hd:hd};
}
function printDoc(text){
 var w=window.open("","_blank");if(!w){alert("浏览器拦了弹窗，请允许后重试。");return}
 var lines=String(text).split(/\n+/).filter(function(x){return x.trim()}),title=lines.shift()||"";
 var body=lines.map(function(l){l=l.trim();return(l.length<=30&&!/[。！？；：.!?]$/.test(l))?"<h2>"+esc(l)+"</h2>":"<p>"+esc(l)+"</p>"}).join("");
 w.document.write("<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><title>"+esc(title)+"</title><style>@page{size:A4;margin:22mm 20mm}body{font-family:'Songti SC','Noto Serif SC',serif;color:#141A24;line-height:1.95;font-size:11.5pt}h1{text-align:center;font-size:19pt}.mt{text-align:center;color:#6B7684;font-size:9pt;border-bottom:1px solid #D8DEE6;padding-bottom:12px;margin-bottom:22px}h2{font-size:13pt;margin:20px 0 8px}p{text-indent:2em;margin:0 0 10px;text-align:justify}.f{margin-top:28px;border-top:1px solid #D8DEE6;padding-top:10px;color:#8B98A5;font-size:8.5pt;text-align:center}</style></head><body><h1>"+esc(title)+"</h1><div class='mt'>读者 × 「"+esc(AG.name)+"」（《"+esc(BOOK.title)+"》的智能体· 德麦国际专著第 "+BOOK.number+" 号）· "+new Date().toLocaleDateString("zh-CN")+"</div>"+body+"<div class='f'>SDE Universes · sdeuniverses.com —— 本文由读者与「"+esc(AG.name)+"」（这本书的智能体）在共读中碰撞而成，引文与观点请自行核实。</div></body></html>");
 w.document.close();setTimeout(function(){try{w.print()}catch(e){}},600);
}
function convo(){return hist.map(function(m){return{role:m.role,text:m.text}})}
function writeOut(form){
 if(busy)return;var kv=keyGet();if(!kv){keyPanel(function(){writeOut(form)});return}
 var M=modal(form==="mono"?"正在写新专著的立项书与全书提纲……":"正在把这场对话写成论文……");
 M.pg.textContent="「"+AG.name+"」在用你的 Key 写，约需两三分钟，请别关掉这一页。";
 busy=true;paint();var out="";
 fetch(PAPER,{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({mode:"full",bookagent:1,form:form,paperN:6,agentName:AG.name,bookRag:ragPick(hist.map(function(m){return m.text}).join(" ").slice(-6000),"clash",14).text,bookMeta:meta(),docTitle:BOOK.title,docText:docText(58000),history:convo(),key:kv.key,vendor:kv.vendor})})
 .then(function(r){
  if(r.headers.get("content-type")&&r.headers.get("content-type").indexOf("json")>=0)return r.json().then(function(j){throw new Error(j.msg||("HTTP "+r.status))});
  return sse(r,function(j){if(j.t==="token"){out+=j.v;M.bd.textContent=out;M.bd.scrollTop=M.bd.scrollHeight}else if(j.t==="think"&&!out){M.bd.textContent="「"+AG.name+"」在构思……"}else if(j.t==="error"){M.pg.textContent=j.v}});
 }).then(function(){
  if(out){M.hd.textContent=(out.split("\n").filter(function(x){return x.trim()})[0]||"成稿").slice(0,60);M.pg.textContent="共 "+out.replace(/\s/g,"").length+" 字 · 读者 × 「"+AG.name+"」（《"+BOOK.title+"》）"}
 }).catch(function(e){M.pg.textContent="没写成："+(e&&e.message)+"。已写出的部分仍可复制。"}).then(function(){busy=false;paint()});
}
function summary(){
 if(busy)return;var kv=keyGet();if(!kv){keyPanel(summary);return}
 var M=modal("正在小结这一场……");busy=true;paint();var out="";
 fetch(PAPER,{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({mode:"summary",bookagent:1,agentName:AG.name,bookMeta:meta(),docTitle:BOOK.title,docText:docText(58000),history:convo(),key:kv.key,vendor:kv.vendor})})
 .then(function(r){
  if(r.headers.get("content-type")&&r.headers.get("content-type").indexOf("json")>=0)return r.json().then(function(j){throw new Error(j.msg||("HTTP "+r.status))});
  return sse(r,function(j){if(j.t==="token"){out+=j.v;M.bd.textContent=out}else if(j.t==="error"){M.pg.textContent=j.v}});
 }).then(function(){M.hd.textContent="本场小结 ·《"+BOOK.title+"》"}).catch(function(e){M.pg.textContent="没写成："+(e&&e.message)}).then(function(){busy=false;paint()});
}

/* —— 8. 长书选章 —— */
function pickChapters(){
 var s=SEL||defaultSel(),on={};s.forEach(function(i){on[i]=1});
 var o=document.createElement("div");o.className="ov";
 o.innerHTML="<div class='box' role='dialog' aria-label='选章'><div class='hd'><b>让书生逐字读哪几章</b><button class='tbtn' data-x>×</button></div><div class='bd' style='white-space:normal;font-family:var(--sans);font-size:13px'>一次最多逐字读约 11 万字；没选的章，书生只读目录和开头。<div class='chs'></div></div><div class='ft'><span class='pg'></span><button class='out' data-s type='button'>就读这几章</button></div></div>";
 document.body.appendChild(o);
 var box=o.querySelector(".chs"),pg=o.querySelector(".pg");
 CH.forEach(function(c,i){var l=document.createElement("label");l.innerHTML="<input type='checkbox'"+(on[i]?" checked":"")+"><span>"+esc(c.t)+"</span><em>"+(c.n/1000).toFixed(1)+" 千字</em>";l.querySelector("input").onchange=cnt;l.dataset.i=i;box.appendChild(l)});
 function picked(){return Array.prototype.map.call(box.querySelectorAll("input"),function(x,i){return x.checked?i:-1}).filter(function(i){return i>=0})}
 function cnt(){var u=picked().reduce(function(a,i){return a+CH[i].n},0);pg.textContent="已选 "+(u/10000).toFixed(1)+" 万字"+(u>BUDGET*0.9?"（超了，后面的章会被截掉）":"")}
 cnt();
 o.querySelector("[data-x]").onclick=function(){o.remove()};
 o.querySelector("[data-s]").onclick=function(){SEL=picked();ls(HK+"_sel",JSON.stringify(SEL));o.remove();readInfo()};
}
})();
