/* /api/john 的离线模拟：把端点里的消息钳位、SSE 逐行解析、错误分支拿出来单独跑。
   不联网、不碰 Key——只验"给什么输入 → 出什么帧"。改 /api/john 必跑这个。 */
function clamp(messages){
  let msgs = Array.isArray(messages) ? messages : [];
  return msgs.filter((m)=>m&&(m.role==="user"||m.role==="assistant")&&typeof m.content==="string"&&m.content.trim())
             .slice(-16).map((m)=>({role:m.role,content:String(m.content).slice(0,4000)}));
}
function parseSSE(chunks){
  let buf="",got=0,out=[],fin=false;
  const feed=(s)=>{ if(fin) return; buf+=s; let nl;
    while((nl=buf.indexOf("\n"))>=0){ const line=buf.slice(0,nl).trim(); buf=buf.slice(nl+1);
      if(!line||line.indexOf("data:")!==0) continue;
      const pay=line.slice(5).trim();
      if(pay==="[DONE]"){ fin=true; buf=""; break; }
      try{ const j=JSON.parse(pay); const d=j&&j.choices&&j.choices[0]&&j.choices[0].delta; const tx=d&&d.content;
        if(tx){ got+=tx.length; out.push(tx); } }catch(e){}
    }};
  chunks.forEach(feed);
  return {text:out.join(""),got};
}
let pass=0,fail=0;
const t=(name,cond)=>{ console.log((cond?"PASS":"FAIL"),name); cond?pass++:fail++; };

t("空消息被挡", clamp([]).length===0);
t("system 角色被过滤", clamp([{role:"system",content:"x"},{role:"user",content:"a"}]).length===1);
t("空白内容被过滤", clamp([{role:"user",content:"   "}]).length===0);
t("只留最近16轮", clamp(Array.from({length:30},(_,i)=>({role:"user",content:"q"+i}))).length===16);
t("超长内容被截到4000", clamp([{role:"user",content:"字".repeat(9000)}])[0].content.length===4000);
t("非字符串被过滤", clamp([{role:"user",content:{a:1}}]).length===0);

const mk=(s)=>'data: '+JSON.stringify({choices:[{delta:{content:s}}]})+'\n\n';
t("单帧解析", parseSSE([mk("你好")]).text==="你好");
t("跨块半行拼接", (()=>{const f=mk("语感");return parseSSE([f.slice(0,9),f.slice(9)]).text==="语感";})());
t("[DONE] 后不再吐字", parseSSE([mk("A"),"data: [DONE]\n\n",mk("B")]).text==="A");
t("坏 JSON 被跳过不炸", parseSSE(["data: {坏\n\n",mk("好")]).text==="好");
t("无 delta.content 不计数", parseSSE(['data: '+JSON.stringify({choices:[{delta:{reasoning_content:"想"}}]})+'\n\n']).got===0);
t("got=0 触发兜底提示", parseSSE([]).got===0);
t("多帧顺序不乱", parseSSE([mk("一"),mk("二"),mk("三")]).text==="一二三");

console.log("pass",pass,"fail",fail);
if(fail) process.exit(1);

/* ── johnRag 的白名单过滤（离线复刻 JOHN_SCOPE）── */
const JOHN_SCOPE = [
  /\/students\/hu-zhiying\//,
  /\/books\/m\/(60|62|71|77)\b/,
  /\/column\/pike-linguistics\//,
  /\/confluence\/evidence-responsibility-alignment\//,
  /\/students\/bao-jinchao\/preemptive-compensation/,
  /\/students\/huang-qianying\/regenerative-boundary\//,
  /\/students\/jin-hua\/(grammar-shame|cognitive-recession|load-bearing-body)\//,
  /\/paradigm\/(civil-war-scar|who-gets-to-settle)\//,
];
function inScope(u){ return JOHN_SCOPE.some((re)=>re.test(u)); }
function pick(hits, docs){
  const out=[], cnt=new Map();
  for(const ck of hits){ const d=docs[ck.d]; if(!d||!d.u) continue;
    const u=String(d.u); if(!inScope(u)) continue;
    const c=cnt.get(u)||0; if(c>=2) continue; cnt.set(u,c+1);
    out.push({u,s:String(ck.t||'')}); if(out.length>=6) break; }
  return out;
}
let p2=0,f2=0; const t2=(n,c)=>{console.log((c?"PASS":"FAIL"),n); c?p2++:f2++;};
t2("收 John 自己的篇", inScope("/students/hu-zhiying/post-hand-slot/"));
t2("收专著62", inScope("/books/m/62/"));
t2("收派克篇", inScope("/column/pike-linguistics/"));
t2("收鲍锦朝语感篇", inScope("/students/bao-jinchao/preemptive-compensation/"));
t2("不收别人的非语言篇", !inScope("/students/hu-min/lodging-in-class/"));
t2("不收新思想前沿面板", !inScope("/frontier/linguistics/"));
t2("不收别的专著", !inScope("/books/m/83/"));
const docs=[{u:"/students/hu-zhiying/a/",t:"A"},{u:"/students/hu-min/x/",t:"X"},{u:"/books/m/62/",t:"B"}];
t2("站外篇被滤掉", pick([{d:1,t:"x"},{d:0,t:"a"}],docs).length===1);
t2("同一篇最多两段", pick([{d:0,t:"1"},{d:0,t:"2"},{d:0,t:"3"}],docs).length===2);
t2("最多六段", pick(Array.from({length:20},()=>({d:2,t:"s"})),docs).length<=6);
t2("空命中返回空", pick([],docs).length===0);
console.log("scope pass",p2,"fail",f2);
if(f2) process.exit(1);

/* ── 概括成文：段数表与前后端一致性、分段拼接、字数闸 ── */
const JOHN_COMPOSE={paper:{parts:4,per:2500},essay:{parts:2,per:2000},wechat:{parts:1,per:2000}};
const fs2=require("fs");
let p3=0,f3=0; const t3=(n,c)=>{console.log((c?"PASS":"FAIL"),n); c?p3++:f3++;};

// 前端 KINDS 必须与后端 JOHN_COMPOSE 段数一致（两处对不上＝缺段或空转）
const page=fs2.readFileSync("public/sites/lang/chatjohn/index.html","utf8");
const m=page.match(/var KINDS=\{([\s\S]*?)\};/);
t3("页面里有 KINDS 表", !!m);
if(m){
  for(const k of Object.keys(JOHN_COMPOSE)){
    const re=new RegExp(k+":\\{n:(\\d+)");
    const hit=m[1].match(re);
    t3("段数一致 "+k, !!hit && Number(hit[1])===JOHN_COMPOSE[k].parts);
  }
}
// 服务端 part 钳位
const clampPart=(kind,part)=>{const K=JOHN_COMPOSE[kind]||JOHN_COMPOSE.wechat;
  return Math.max(1,Math.min(K.parts,parseInt(part,10)||1));};
t3("part 下限钳到1", clampPart("paper",0)===1);
t3("part 上限钳到4", clampPart("paper",99)===4);
t3("wechat 只有1段", clampPart("wechat",3)===1);
t3("未知文体退回 wechat", clampPart("zzz",2)===1);
// 对话长度闸
const tooShort=(s)=>s.length<200;
t3("过短对话被挡", tooShort("读者：你好\n\nJohn：你好"));
t3("够长的放行", !tooShort("字".repeat(250)));
// 超长对话的头尾压缩：保头2万、留尾4万，且总长下降
const squeeze=(c)=>c.length>60000 ? (c.slice(0,20000)+"\n\n……（中间略）……\n\n"+c.slice(-40000)) : c;
const big="A".repeat(100000);
t3("超长对话被压缩", squeeze(big).length<70000 && squeeze(big).startsWith("A") && squeeze(big).endsWith("A"));
t3("正常长度不动", squeeze("B".repeat(1000)).length===1000);
// 短段告警阈值＝目标四成
const warn=(kind,wrote)=>wrote>0&&wrote<Math.round(JOHN_COMPOSE[kind].per*0.4);
t3("论文段写 900 字要告警", warn("paper",900));
t3("论文段写 2400 字不告警", !warn("paper",2400));
console.log("compose pass",p3,"fail",f3);
if(f3) process.exit(1);


/* ── ChatJohn：BYOK 校验 · markdown 渲染 · 前后端一致 ── */
let p4=0,f4=0; const t4=(n,c)=>{console.log((c?"PASS":"FAIL"),n); c?p4++:f4++;};
const needKey=(k)=>String(k||"").trim().length<8;
t4("空 Key 被挡", needKey(""));
t4("短 Key 被挡", needKey("sk-123"));
t4("正常 Key 放行", !needKey("sk-abcdefghijklmn"));

// 与页面同一份 md()：从页面里抠出来跑，防止两边漂移
const page2=fs2.readFileSync("public/sites/lang/chatjohn/index.html","utf8");
const mdSrc=[null, (page2.match(/function inline\(s\)\{[\s\S]*?\n\}/)||[])[0], (page2.match(/function md\(src\)\{[\s\S]*?\n\}\n/)||[])[0]];
t4("页面里能抠出 md 渲染器", !!(mdSrc[1]&&mdSrc[2]));
if(mdSrc[1]&&mdSrc[2]){
  const F=new Function("var esc=function(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');};"
    + mdSrc[1] + "\n" + mdSrc[2] + "\nreturn md;");
  const md=F();
  t4("段落", md("你好").indexOf("<p>")===0);
  t4("二级标题", md("## 标题").indexOf("<h2>")>=0);
  t4("粗体", md("**重**").indexOf("<strong>")>=0);
  t4("无序列表", (md("- a\n- b").match(/<li>/g)||[]).length===2);
  t4("有序列表", md("1. a").indexOf("<ol>")>=0);
  t4("引用", md("> q").indexOf("<blockquote>")>=0);
  t4("行内代码", md("`x`").indexOf("<code>")>=0);
  t4("代码块", md("```\nx\n```").indexOf("<pre>")>=0);
  t4("裸链接自动成锚", md("见 https://a.com/b").indexOf('<a href="https://a.com/b"')>=0);
  t4("HTML 被转义（防注入）", md("<img src=x onerror=alert(1)>").indexOf("<img")<0);
  t4("脚本标签被转义", md("<script>alert(1)</"+"script>").indexOf("<script")<0);
  t4("列表后接段落不粘连", md("- a\n\n正文").indexOf("</ul>")>=0);
}
// 入口一致性：首页/nav 指向 /chatjohn/，老 /john/ 是跳转页
const home=fs2.readFileSync("public/sites/lang/index.html","utf8");
t4("首页第二张卡指向 chatjohn", home.indexOf('href="/chatjohn/"')>=0);
t4("首页不再指向旧 /john/", home.indexOf('href="/john/"')<0);
const old=fs2.readFileSync("public/sites/lang/john/index.html","utf8");
t4("旧页是跳转页", old.indexOf('/chatjohn/')>=0 && old.indexOf('noindex')>=0);
console.log("chatjohn pass",p4,"fail",f4);
if(f4) process.exit(1);
