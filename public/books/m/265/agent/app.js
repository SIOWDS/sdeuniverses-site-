/* Volume 265 dedicated app. Adapted from shared app blob dfb29b2f7e296de88e4fd5875fe4ba328468f6bf; shared app unchanged. */
(function(){
"use strict";
var $=function(id){return document.getElementById(id)};
var Core=window.XuwenCore,SPEC=null;
var API="/api/wds/read",PAPER="/api/wds/read-paper";
var GATES=[{"k": "read", "n": "壹", "t": "读懂原文", "d": "定位概念与论证，区分发现和发生", "ph": "想细读哪一章、哪一处论证？", "starts": ["第6章怎样区分发现的结构性终点与持续发生？请给原文依据。"]}, {"k": "apply", "n": "贰", "t": "进入实践", "d": "把问题、学习与原文接在一起", "ph": "你在阅读、写作或出版中遇到什么具体问题？", "starts": ["请用第26至30章帮我设计一个有限的三合一试用，先说检验条件，不假定有效。"]}, {"k": "cut", "n": "叁", "t": "检验母题", "d": "寻找反例，保留不利结果", "ph": "哪一个主张需要核对、限制或反驳？", "starts": ["稳定纸书也能促成持续发生，这会怎样挑战本书的总纲？"]}, {"k": "clash", "n": "肆", "t": "理论对话", "d": "公平比较已有理论与本书增量", "ph": "想与哪种出版、阅读或学习理论比较？", "starts": ["请依据第10章公平比较本书与接受美学，并标明哪些只是本书对原典的转述。"]}, {"k": "write", "n": "伍", "t": "形成成果", "d": "保留来源、异议与修订依据", "ph": "想把哪一个新问题写成自己的成果？", "starts": ["请据本场讨论拟研究提纲，分开已知证据、模型推论与尚未实施的研究。"]}];
var BOOK=null,CH=[],SEL=null,act="read",hist=[],busy=false,HK="";
function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
function ls(k,v){try{if(v===undefined)return localStorage.getItem(k);if(v===null)localStorage.removeItem(k);else localStorage.setItem(k,v)}catch(e){return null}}
function path(u){try{var x=new URL(u,location.origin);return x.pathname+x.search+x.hash}catch(e){return u||""}}
function fail(msg){$("ldmsg").innerHTML=msg}
var CFG=window.BOOK_AGENT||{};
var mno=parseInt(CFG.no||new URLSearchParams(location.search).get("m"),10);
if(!mno){fail('没有指定书号。请从<a href="/books/">专著书架</a>里任选一本进来。');return}
HK="sde_xuwen_m265_v1";
var AG={name:"书生",epithet:"",intro:"",starts:{}},RAG=null,KP=null,DUI=null,CAT=null,AGS=null,CTX={},DDJ=[290,297,311];

/* —— 1. 找书：catalog.json —— */
function J(u){return fetch(u,{cache:"no-cache"}).then(function(r){return r.ok?r.json():null}).catch(function(){return null})}
Promise.all([J("/books/catalog.json"),J("/books/agents.json"),J("/books/m/265/rag.json"),J("/books/m/265/keypoints.json"),J("/books/m/265/agent/corpus.json"),J("/books/m/265/agent/spec.json")]).then(function(a){
 Core.validate(a[4],a[2],a[3],a[5]);
 CAT=a[0]||{};AGS=(a[1]&&a[1].agents)||{};SPEC=a[5];AG=SPEC.agent;RAG=a[2];KP=a[3];CH=a[4].units;
 BOOK=(CAT.books||[]).filter(function(b){return +b.number===265})[0];
 if(!BOOK)throw new Error("书架暂未载入第265卷，请稍后刷新");
 boot();
}).catch(function(e){fail("没能打开续问："+esc(e&&e.message)+'。<a href="/books/m/265/text/">先读原文</a> · <a href="/books/m/265/agent/">重试</a>')});

/* 原文由同版HTML离线提取并验证，加载42单元而非只读第一个article。 */
var BUDGET=116000;   /* 服务端书生档收 12 万字符符；留出目录与章名的余量 */
function total(){return CH.reduce(function(a,c){return a+c.n},0)}
function defaultSel(){return [0,1]}
function loadSel(){var v=ls(HK+"_sel");if(v){try{var a=JSON.parse(v);if(Array.isArray(a))return a.filter(function(i){return i>=0&&i<CH.length})}catch(e){}}return null}
function docText(cap){return Core.docText(CH,SEL||defaultSel(),cap)}
function readInfo(){
 var selected=SEL||defaultSel(),n=selected.reduce(function(sum,i){return sum+CH[i].n},0);
 $("readInfo").innerHTML="浏览器已载入 <b>42 个单元</b>（导论、40章及结语），约 "+(total()/10000).toFixed(1)+" 万字符。每次发送提供所选 <b>"+selected.length+" 个单元</b>（约 "+(n/10000).toFixed(1)+" 万字符）及问题相关的原文片段。<button type='button' id='pickBtn'>选择阅读单元 ›</button>";
 $("pickBtn").onclick=pickChapters;
}
/* —— 3. 起页 —— */
function boot(){
 var b=BOOK;
 document.title=AG.name+" · 《"+b.title+"》的智能体 | 德麦国际专著第 "+b.number+" 号";
 $("agName").textContent=AG.name;$("agEpi").textContent=AG.epithet||"这本书的智能体";
 $("agTag").textContent=AG.intro||("我只为《"+b.title+"》而生：陪你读懂它、用上它、拆开它、拿它去对撞，再把碰出来的新东西写成论文，甚至一部新专著。");
 ragInfo();kpInfo();sibBar();
 $("bt").textContent=b.title; $("bs").textContent=(b.subtitle?b.subtitle+" · ":"")+(b.authors||[]).join("、")+" 著 · 德麦国际专著第 "+b.number+" 号";
 if(b.coverUrl){$("cov").src=path(b.coverUrl);$("cov").hidden=false}
 $("detailA").href=path(b.detailUrl); $("readA").href=path(b.readUrl||b.textUrl||b.detailUrl);
 SEL=loadSel(); var incoming=Core.queryState(location.search,CH); if(incoming.selected)SEL=incoming.selected; readInfo();
 GATES.forEach(function(g){
  var x=document.createElement("button");x.type="button";x.className="gate";x.dataset.k=g.k;
  x.innerHTML="<span class='n'>"+g.n+"</span><div><b>"+g.t+"</b><span>"+g.d+"</span></div>";
  x.onclick=function(){setAct(g.k,true)};$("gates").appendChild(x);
  var y=document.createElement("button");y.type="button";y.className="gb";y.dataset.k=g.k;y.textContent=g.t;
  y.onclick=function(){setAct(g.k,false)};$("gbar").appendChild(y);
 });
 try{hist=JSON.parse(ls(HK)||"[]")||[];if(!Array.isArray(hist))hist=[];hist=hist.filter(function(m){return m&&(m.role==="reader"||m.role==="wds")&&typeof m.text==="string"})}catch(e){hist=[]}
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
 if(incoming.prompt){$("q").value=incoming.prompt;grow();$("hint").textContent="已预填学习任务，请审阅后点击发送。页面没有自动发问。"}
 if(incoming.invalidChapter)$("hint").textContent="未识别链接中的章节；已保留问题，请先选择阅读单元。";
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

/* 本书原文检索与逐字节录；不生成引文。 */
function grams(s){var g={},t=String(s||"").replace(/[^\u4e00-\u9fff]/g,"");for(var i=0;i<t.length-1;i++)g[t.substr(i,2)]=1;return g}
function lastAns(){for(var i=hist.length-1;i>=0;i--)if(hist[i].role==="wds")return String(hist[i].text).slice(0,600);return ""}
function cnNum(t){var M={"零":0,"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9};t=String(t);if(/^\d+$/.test(t))return +t;var b=t.indexOf("百"),r=0;if(b>=0){r=(b?M[t[0]]:1)*100;t=t.slice(b+1);if(!t)return r}var i=t.indexOf("十");if(i>=0)return r+(i?M[t[0]]:1)*10+(t.length>i+1?M[t[i+1]]:0);return r+(M[t]||0)}
function qChapters(q){var o={},re=/第\s*([0-9一二三四五六七八九十百]+)\s*章/g,m;while((m=re.exec(q)))o[cnNum(m[1])]=1;return o}
function ragPick(q,a,k){return Core.retrieve(q,a,RAG,CH,SEL||defaultSel(),k)}
function kpText(){return Core.points(KP,SPEC)}
function kpInfo(){
 $("kpInfo").innerHTML="<b>42 条原文节录</b>作为各阅读单元的入口；节录不是章摘要。<button type='button' id='kpBtn'>看节录与出处 ›</button>";$("kpBtn").onclick=kpList;
}
function kpList(){
 var it=KP.items,o=document.createElement("div");o.className="ov";
 o.innerHTML="<div class='box' role='dialog' aria-label='各单元原文节录'><div class='hd'><b>42 单元 · 原文节录</b><button class='tbtn' data-x aria-label='关闭'>×</button></div><div class='bd rgl'><p class='rgn'>下列文字逐字摘自出版版。短节录不代表完整论证；请打开出处核查上下文。</p>"+it.map(function(x,i){return "<div class='rg'><div class='rgh'><i>"+(i+1)+"</i><a href='"+esc(path(x.url))+"' target='_blank' rel='noopener'>"+esc(x.t)+"</a></div><div class='rgx'>"+esc(x.x)+"</div><button type='button' class='chip rgb' data-i='"+i+"'>以此预填问题</button></div>"}).join("")+"</div></div>";
 document.body.appendChild(o);o.querySelector("[data-x]").onclick=function(){o.remove()};
 o.querySelectorAll(".rgb").forEach(function(b){b.onclick=function(){var x=it[+b.dataset.i];SEL=[CH.findIndex(function(c){return c.id===x.unit})];readInfo();o.remove();$("q").value="请解释《出版的发现到发生的典范转移》“"+x.t+"”中这段原文的论证，并区分本书原文、假设案例、拟议研究、读者判断和模型推论：\n"+x.x;$("q").focus();grow()}});
}
function ragInfo(){
 $("ragInfo").innerHTML="<b>"+RAG.items.length+" 个原文段落</b>可按问题检索，覆盖全部 42 单元。<button type='button' id='ragBtn'>看原文检索范围 ›</button>";$("ragBtn").onclick=ragList;
}
function ragList(){
 var o=document.createElement("div");o.className="ov";
 o.innerHTML="<div class='box' role='dialog' aria-label='原文检索范围'><div class='hd'><b>原文检索范围</b><button class='tbtn' data-x aria-label='关闭'>×</button></div><div class='bd rgl'><p class='rgn'>本库只包含《出版的发现到发生的典范转移》原文。书中引用或转述外部材料，不表示本服务已取得外部著作全文。每轮按问题选择片段，仍可能漏检；下列链接可回查全文。</p>"+CH.map(function(c,i){return "<div class='rg'><div class='rgh'><i>"+(i+1)+"</i><a href='"+esc(path(c.u))+"' target='_blank' rel='noopener'>"+esc(c.t)+"</a></div><div class='rgc'>"+RAG.items.filter(function(r){return r.unit===c.id}).length+" 个原文段落</div></div>"}).join("")+"</div></div>";
 document.body.appendChild(o);o.querySelector("[data-x]").onclick=function(){o.remove()};
}
/* —— 4. 显示 —— */
function fmt(s){
 var h=esc(s).replace(/\*\*([^*\n]{1,120})\*\*/g,"<b>$1</b>").replace(/^#{1,4}\s*/gm,"");
 return h.split(/\n{2,}|\n(?=[一二三四五六七八九十①②③④⑤⑥⑦⑧⑨]+[、．.）)]|\d+[.、）)]|〔)/).map(function(p){return "<p>"+p.replace(/\n/g,"<br>")+"</p>"}).join("");
}
function render(){
 var col=$("col");col.innerHTML="";var hello=document.createElement("div");hello.className="hello";
 hello.innerHTML="<h2>我是「续问」<small>《出版的发现到发生的典范转移》的专属阅读智能体</small></h2><p>"+esc(AG.intro)+"</p><p>从五道门进入：<b>读懂原文、进入实践、检验母题、理论对话、形成成果</b>。所选单元与检索片段会随你的问题提供给模型；引用须回到原书核查。</p><p style='color:var(--dim);font-size:13px'>问答区分原文、事实、假设案例、拟议研究与模型推论；模型不代表作者回应。缺少证据时应明确说明。点建议题只会预填；点击发送才调用模型。<a href='/books/m/265/agent/spec.json' target='_blank' rel='noopener'>查看公开问答规范</a></p><div class='starts' id='starts'></div>";
 col.appendChild(hello);fillStarts();hist.forEach(function(m){add(m.role,m.text,m.act,m.srcs,m.who)});scroll();
}
function fillStarts(){
 var box=$("starts");if(!box)return;box.innerHTML="";
 var own=AG.starts&&AG.starts[act],ss=(Array.isArray(own)?own:own?[own]:[]).concat(gateOf(act).starts).filter(function(s,i,a){return a.indexOf(s)===i}).slice(0,3);
 ss.forEach(function(s){var c=document.createElement("button");c.type="button";c.className="chip";c.textContent=s;c.onclick=function(){$("q").value=s;$("q").focus();grow()};box.appendChild(c)});
}
function add(role,text,a,srcs,who){
 var w=document.createElement("div");w.className="m "+(role==="reader"?"me":"ai");
 var bub=document.createElement("div");bub.className="bub";w.appendChild(bub);
 if(role==="reader")bub.textContent=text;
 else{
  var sb=who&&who!==mno?sibOf(who):null;
  if(sb){w.className+=" sib";bub.innerHTML="<span class='gtag sg'>「"+esc(sb.name)+"」接话 · 《"+esc(sb.title)+"》</span><div class='tx'>"+fmt(text||"")+"</div>"}
  else bub.innerHTML=(a?"<span class='gtag'>"+esc(gateOf(a).t)+"</span>":"")+"<div class='tx'>"+fmt(text||"")+"</div>";
  if(srcs&&srcs.length)bub.appendChild(srcBox(srcs));if(text)bub.appendChild(actBox(text,who||mno))}
 $("col").appendChild(w);return bub;
}
function srcBox(s){var d=document.createElement("div");d.className="srcs";d.innerHTML="本轮提供的原文来源（并非逐句核验结果）："+s.slice(0,10).map(function(x){return "<a href='"+esc(path(x.u||x.url||"/books/m/265/text/"))+"' target='_blank' rel='noopener'>"+esc(x.t||x.title||"原文")+"</a>"}).join(" · ");return d}
function actBox(text,who){
 var d=document.createElement("div");d.className="acts";
 var c=document.createElement("button");c.type="button";c.textContent="复制";c.onclick=function(){Promise.resolve().then(function(){return navigator.clipboard.writeText(text)}).then(function(){c.textContent="已复制";setTimeout(function(){c.textContent="复制"},1500)},function(){c.textContent="复制失败，请手动选取"})};
 d.appendChild(c);
 [["cut","拆开这一答"],["clash","拿这一答去对撞"]].forEach(function(p){var x=document.createElement("button");x.type="button";x.textContent=p[1];x.onclick=function(){setAct(p[0],false);$("q").value=p[0]==="cut"?"拆开你上一答：它把什么当作了给定？哪一句最经不起追问？":"拿你上一答去撞它最强的敌意最近邻，撞出一个新命题。";$("q").focus();grow()};d.appendChild(x)});
 var tb=talkBar(who||mno);if(tb)d.appendChild(tb);
 return d;
}
function scroll(){var m=$("msgs");m.scrollTop=m.scrollHeight}

/* —— 5. Key —— */
function keyGet(){var k=(ls("sde_wds_key")||"").trim(),v=ls("sde_wds_vendor")||"ds";if(k.length>=8)return{key:k,vendor:v};var d=(ls("sde_ds_key")||"").trim();if(d.length>=8)return{key:d,vendor:"ds"};var g=(ls("sde_glm_key")||"").trim();if(g.length>=8)return{key:g,vendor:"glm"};return null}
function keyPanel(cb){
 var cur=keyGet()||{key:"",vendor:"ds"},v=cur.vendor;
 var o=document.createElement("div");o.className="ov";
 o.innerHTML="<div class='box kbox' role='dialog' aria-label='设置 API Key'><div class='hd'><b>用你自己的大模型 Key</b><button class='tbtn' data-x>×</button></div><div class='bd'>续问使用你选择的模型服务。<b style='color:var(--gold)'>Key 保存在本浏览器；发送时经本站服务转交所选模型服务</b>。问题、所选原文及对话也会随请求发送，费用由模型服务方按你的账户计算。与站内 ChatSDE、陪读共用设置。"
 +"<div class='kv'><button type='button' data-v='ds'>DeepSeek</button><button type='button' data-v='glm'>智谱 GLM</button></div><input class='kin' type='password' placeholder='粘贴你的 API Key' aria-label='API Key'><div class='small' data-l></div></div>"
 +"<div class='ft'><span class='pg'></span><button class='out' data-s type='button'>保存设置</button></div></div>";
 document.body.appendChild(o);
 var kin=o.querySelector(".kin");kin.value=cur.key;
 function pv(){o.querySelectorAll("[data-v]").forEach(function(b){b.setAttribute("aria-pressed",b.dataset.v===v?"true":"false")});o.querySelector("[data-l]").innerHTML=v==="ds"?"还没有 Key？去 <a href='https://platform.deepseek.com' target='_blank' rel='noopener'>platform.deepseek.com</a> 申请":"还没有 Key？去 <a href='https://open.bigmodel.cn' target='_blank' rel='noopener'>open.bigmodel.cn</a> 申请"}
 o.querySelectorAll("[data-v]").forEach(function(b){b.onclick=function(){v=b.dataset.v;pv()}});pv();
 o.querySelector("[data-x]").onclick=function(){o.remove()};
 o.querySelector("[data-s]").onclick=function(){var k=kin.value.trim();if(k.length<8){kin.style.borderColor="var(--err)";return}ls("sde_wds_key",k);ls("sde_wds_vendor",v);ls(v==="glm"?"sde_glm_key":"sde_ds_key",k);o.remove();if(cb)cb()};
 setTimeout(function(){kin.focus()},60);
}

/* —— 6. 对话（SSE）—— */
function meta(){return Core.meta(BOOK,SPEC)}
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
 var t=$("q"),q=t.value.trim();if(!q||busy)return;if(q.length>4000){$("hint").textContent="问题超过4,000字符，请缩短后发送，避免接口截断。";return}
 var kv=keyGet();if(!kv){keyPanel(send);return}
 t.value="";grow();
 var a=act;
 add("reader",q);hist.push({role:"reader",text:q,act:a});save();
 var bub=add("wds","",a),tx=bub.querySelector(".tx");tx.innerHTML="<span class='think'>「"+esc(AG.name)+"」正在想……</span>";
 busy=true;paint();scroll();
 var ans="",srcs=[],notes=[];
 var rp=ragPick(q+" "+lastAns(),a,10);
 var built=Core.payload(q,a,{book:BOOK,spec:SPEC,rag:RAG,kp:KP,units:CH,selected:SEL||defaultSel(),history:hist.slice(0,-1).map(function(m){return{role:m.role,text:m.text}})});
 var body=Object.assign(built.request,{key:kv.key,vendor:kv.vendor});

 fetch(API,{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify(body)}).then(function(r){
  return sse(r,function(j){
   if(j.t==="token"){ans+=j.v;tx.innerHTML=fmt(ans);scroll()}
   else if(j.t==="think"&&!ans){tx.innerHTML="<span class='think'>「"+esc(AG.name)+"」正在想……</span>"}
   else if(j.t==="sources"&&Array.isArray(j.v)){srcs=j.v}
   else if(j.t==="note"){notes.push(j.v)}
   else if(j.t==="error"){var e=document.createElement("div");e.className="err";e.textContent=j.v;bub.appendChild(e);if(j.code==="need_key"||j.code==="bad_key")setTimeout(function(){keyPanel(null)},300)}
  });
 }).catch(function(e){var x=document.createElement("div");x.className="err";x.textContent="接不上「"+AG.name+"」（"+(e&&e.message)+"）。检查网络后再问一次——你刚才那句已记下。";bub.appendChild(x)}).then(function(){
  srcs=built.sources;
  if(ans){hist.push({role:"wds",text:ans,act:a,srcs:srcs,who:mno});save();if(srcs.length)bub.appendChild(srcBox(srcs));bub.appendChild(actBox(ans,mno))}
  else if(tx.querySelector(".think"))tx.innerHTML="";
  if(notes.length){var n=document.createElement("div");n.className="note";n.textContent=notes.join("；");bub.appendChild(n)}
  busy=false;paint();scroll();
 });
}


function sibOf(){return null}
function tagged(m){return m.text}
function talkBar(){return null}
function sibBar(){}

/* —— 7. 写出来：论文 / 专著立项 / 小结 —— */
function modal(title){
 var o=document.createElement("div");o.className="ov";
 o.innerHTML="<div class='box' role='dialog'><div class='hd'><b></b><button class='tbtn' data-x>×</button></div><div class='bd'></div><div class='ft'><span class='pg'></span><button class='tbtn' data-c type='button'>复制全文</button><button class='tbtn' data-p type='button'>导出 PDF</button><a class='tbtn' href='/students/submit/' target='_blank' rel='noopener'>投给德麦</a></div></div>";
 document.body.appendChild(o);
 var hd=o.querySelector(".hd b"),bd=o.querySelector(".bd"),pg=o.querySelector(".pg");hd.textContent=title;
 o.querySelector("[data-x]").onclick=function(){o.remove()};
 o.querySelector("[data-c]").onclick=function(){Promise.resolve().then(function(){return navigator.clipboard.writeText(bd.textContent)}).then(function(){pg.textContent="已复制"},function(){pg.textContent="复制失败，请手动选取"})};
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
function convo(){return hist.map(function(m){return{role:m.role,text:tagged(m,mno)}})}
function writeOut(form){
 if(busy)return;var kv=keyGet();if(!kv){keyPanel(function(){writeOut(form)});return}
 var M=modal(form==="mono"?"正在写新专著的立项书与全书提纲……":"正在把这场对话写成论文……");
 M.pg.textContent="「"+AG.name+"」在用你的 Key 写，约需两三分钟，请别关掉这一页。";
 busy=true;paint();var out="";
 fetch(PAPER,{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({mode:"full",bookagent:1,bookNo:265,form:form,paperN:6,agentName:AG.name,bookPoints:kpText(),bookRag:ragPick(hist.map(function(m){return m.text}).join(" ").slice(-6000),"clash",14).text,bookMeta:meta(),docTitle:BOOK.title,docText:docText(58000),history:convo(),key:kv.key,vendor:kv.vendor})})
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
 fetch(PAPER,{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({mode:"summary",bookagent:1,bookNo:265,bookPoints:kpText(),agentName:AG.name,bookMeta:meta(),docTitle:BOOK.title,docText:docText(58000),history:convo(),key:kv.key,vendor:kv.vendor})})
 .then(function(r){
  if(r.headers.get("content-type")&&r.headers.get("content-type").indexOf("json")>=0)return r.json().then(function(j){throw new Error(j.msg||("HTTP "+r.status))});
  return sse(r,function(j){if(j.t==="token"){out+=j.v;M.bd.textContent=out}else if(j.t==="error"){M.pg.textContent=j.v}});
 }).then(function(){M.hd.textContent="本场小结 ·《"+BOOK.title+"》"}).catch(function(e){M.pg.textContent="没写成："+(e&&e.message)}).then(function(){busy=false;paint()});
}

/* —— 8. 长书选章 —— */
function pickChapters(){
 var selected=SEL||defaultSel(),o=document.createElement("div");o.className="ov";
 o.innerHTML="<div class='box' role='dialog' aria-label='选择原文范围'><div class='hd'><b>选择本轮提供的原文</b><button class='tbtn' data-x aria-label='关闭'>×</button></div><div class='bd' style='white-space:normal;font-family:var(--sans);font-size:13px'>可选择完整阅读单元（正文合计最多约10万字符）。未选单元仍可按问题检索片段；目录不代表已提供正文。长篇写作的正文上限较低，将按选择顺序提供完整单元，并列出未提供的单元。<div class='chs'></div></div><div class='ft'><span class='pg'></span><button class='out' data-s type='button'>使用所选范围</button></div></div>";
 document.body.appendChild(o);var box=o.querySelector(".chs"),pg=o.querySelector(".pg"),saveBtn=o.querySelector("[data-s]");
 CH.forEach(function(c,i){var l=document.createElement("label");l.innerHTML="<input type='checkbox'"+(selected.includes(i)?" checked":"")+"><span>"+esc(c.t)+"</span><em>"+(c.n/1000).toFixed(1)+" 千字</em>";l.querySelector("input").onchange=count;box.appendChild(l)});
 function picked(){return Array.from(box.querySelectorAll("input")).map(function(x,i){return x.checked?i:-1}).filter(function(i){return i>=0})}
 function count(){var n=picked().reduce(function(sum,i){return sum+CH[i].n},0);pg.textContent="所选约 "+(n/10000).toFixed(1)+" 万字符"+(n>100000?"，请减少单元":"");saveBtn.disabled=n>100000}
 count();o.querySelector("[data-x]").onclick=function(){o.remove()};saveBtn.onclick=function(){SEL=picked();ls(HK+"_sel",JSON.stringify(SEL));o.remove();readInfo()};
}
})();

