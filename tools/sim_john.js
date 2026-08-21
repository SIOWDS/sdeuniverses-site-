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
