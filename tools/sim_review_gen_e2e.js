/* 端到端模拟（jsdom）：假基底＋假 OpenAlex 跑完 ①–⑩＋自检；跑法：npm i jsdom && node tools/sim_review_gen_e2e.js */
const fs=require("fs"); const {JSDOM}=require("jsdom");
const html=fs.readFileSync(""+__dirname+"/../public/taste/review-gen/index.html","utf8");
const calls={modes:{},oa:0,models:new Set(),vendors:new Set(),retryCards:0,badBodies:[]};
function sseResp(text){
  const enc=new TextEncoder(); const chunks=[]; 
  for(let i=0;i<text.length;i+=40) chunks.push("data: "+JSON.stringify({t:"token",v:text.slice(i,i+40)})+"\n\n");
  chunks.push("data: "+JSON.stringify({t:"end",v:{}})+"\n\ndata: [DONE]\n\n");
  const body=new ReadableStream({start(c){ chunks.forEach(x=>c.enqueue(enc.encode(x))); c.close(); }});
  return new Response(body,{status:200,headers:{"content-type":"text/event-stream"}});
}
const HOWCARD=(i,bad)=>{ const st=["S","D","E"][i%3], fin=["D","S","S"][i%3], mid="SDE".replace(st,"").replace(fin,""); const good=st+"→"+mid+"→"+fin, badP=st+"→"+fin+"→"+mid; return `承重命题：命题${i}\n起手维：${st}\n落点维：${fin}\n所走路径：${bad?badP:good}\n中间维处置：映射\n判据与读数：正确率\n失效条件：模型不完整\n推翻对象：单变量显示\n余数：显露改变区分未测\n原文锚句：“make visible the constraints”`; };
function canned(b){
  calls.modes[b.mode]=(calls.modes[b.mode]||0)+1; calls.models.add(b.model); calls.vendors.add(b.vendor);
  for(const k of ["key","vendor","tier","type","topic","question"]) if(!(k in b)) calls.badBodies.push(b.mode+" 缺 "+k);
  switch(b.mode){
    case "frame": return JSON.stringify({surface:"表面",genesis:"从哪一维起手落在哪一维",aliases:["supervisory control","joint cognitive systems","alarm management","ecological interface","procedural assistance","mistake detection","copilot","operator 4.0"],queries:["operator assistance process industry","alarm management","ecological interface design","procedure mistake detection egocentric","operator training simulator","digital twin process operator"],classicHint:"Bainbridge"});
    case "card": { const retry=/【机检退回】/.test(b.text); if(retry) calls.retryCards++; return HOWCARD(b.idx, b.idx%7===0&&!retry); }
    case "map": return "格位分布\nS→E→D｜1,2,3｜1\n挤格：S→E→D 最挤\n空格：D→S→E 一篇没有——起名「显露即介入」（摘要级空格；降级条件：全文重出卡后站进三篇即降为半空格）\n自撞：无\n断链：「区分先于显露」——若不成立 D→E→S 整格塌\n越位文献与悬位：无";
    case "neighbors": return JSON.stringify([{item:"显露即介入",kind:"gap",neighbors:["中断科学","临床告警","注意力感知系统"],queries:["interruption task performance","alert timing attention-aware"]},{item:"区分先于显露",kind:"chain",neighbors:["认知科学表征效应","框架效应","显示设计"],queries:["representational effect distributed cognition","framing effect display"]}]);
    case "verdict": return "项名｜判｜命中｜猜想可落的那一段\n显露即介入｜语料空｜Bailey & Konstan 2006 CHB 22(4):685-708，锚句“users require from 3% to 27% more time”｜时机之外的位置改变\n区分先于显露｜语料空｜Zhang & Norman 1994 Cognitive Science 18:87-122，锚句“different isomorphic representations”｜从偏差改判为发生\n三判分布：语料空 2／全语料空 0／本地空 0";
    case "surface": return "1｜“alarm floods”｜［1］［2］｜2\n2｜“errors outside the procedure”｜［3］｜1";
    case "challenges": return "表面与发生之间隔着一张图。\n挑战一：把操作员接进 E\n定位：(a)……\n挑战二：显露被当终点\n定位：(b)……\n挑战三：判据无回写\n定位：(c)\n挑战四：区分先于显露\n定位：(d)\n挑战五：读数错位\n定位：(e)\n挑战六（碰撞挑战）：定位 (f)";
    case "gaps": return "挑战一的现有方案：站在 E→D→S；缺维\n挑战二：错位\n挑战三：无回写\n挑战四：读数错位\n挑战五：读数错位\n四型分布：缺维1 错位1 无回写1 读数错位2";
    case "collide": return "共有前提：区分先于显露\n塌格范围：D→E→S、E→D→S\n落格：S→D→E\nS 之家：［1］\nD 之家：［2］\nE 之家：［3］\n主家：E\n推翻材料：［5］“mode error”\nY：程序先行\nZ：显中定——区分在显露里才定下\n旗舰读数：定位次 k\n六型对照：不归入\n删维测试：删任一家 Z 塌\n分离线：……\n预注册真跑：E→D→S 至少三篇移到 S→D→E\n撤下条件：若隔壁已有……\n碰撞挑战：E→D→S 格内［9］与［40］互相矛盾\n===Z===\n"+JSON.stringify({z:"显中定",reading:"定位次 k",shapeFree:true,homes:[1,2,3],prereg:"E→D→S 至少三篇移到 S→D→E"});
    case "collide_run": return "［1］｜S→E→D｜S→D→E｜动｜…\n［2］｜D→E→S｜D→E→S｜不动｜…\n对表预注册：动了三格。结论：支持。";
    case "conjectures": return ["一","二","三","四","五"].map((k,i)=>`猜想${k}：X 不是 Y，而是 Z${i}\n级别：${i===0?"典范级":"改判级"}\n所站的位：D→S→E\n读数：ζ${i}，[0,1]，取法……\n预测：［1］［2］\n可证伪条件：若……（每千次报警约 3 次）删第 9 节\n撤下条件：若隔壁已有 W${i}，整条撤`).join("\n\n")+"\n\n五条之间：五个读数排成一条路，守恒式 β×N＝p×M，闭环删除条件……"+"\n===QUERIES===\n"+JSON.stringify([1,2,3,4,5].map(k=>({k,level:k===1?"碰撞级":"改判级",reading:"ζ"+k,shape:["差型","改写型","介入型","周期型","分歧型"][k-1],freq:"每千次报警约 3 次",queries:["q"+k+"a","q"+k+"b"]})));
    case "occupants": return ["一","二","三","四","五"].map(k=>"猜想"+k+"：占位者 Bailey 2006（库：Crossref）……分离线……读数命名闸：近邻量 work-as-done……撤下条件：若隔壁已有……整条撤").join("\n")+"\n检索盲区：三库只索引题名摘要；OECD 1990 未取到。";
    case "write": { const sec=b.sec; if(sec===0) return "主类：How。发生层改写：从哪一维起手。"+"正文".repeat(50); return "第"+(sec+1)+"节正文，引［1］［2］。"+"正文".repeat(60); }
  }
  return "？";
}
function oaResults(q,n){
  const YEAR=new Date().getFullYear(); const out=[];
  for(let i=0;i<n;i++){ const age=[25,30,22,8,12,15,10,7,2,3,1,4][i%12]; const key=q.replace(/\W/g,"").slice(0,6)+i;
    out.push({id:"W"+key,doi:"https://doi.org/10.1/"+key,title:"Paper "+key,publication_year:YEAR-age,cited_by_count:10*i,authorships:[{author:{display_name:"Au "+i}}],primary_location:{source:{display_name:"J"}},abstract_inverted_index:{"abstract":[0],"text":[1],"here":[2]}}); }
  return {results:out};
}
const dom=new JSDOM(html,{url:"https://sdeuniverses.com/taste/review-gen/",runScripts:"dangerously",resources:undefined,pretendToBeVisual:true});
const w=dom.window; const errs=[];
w.addEventListener("error",e=>errs.push(e.message)); dom.virtualConsole.on("jsdomError",e=>errs.push(String(e.message||e).slice(0,120)));
w.fetch=async function(url,init){
  const u=String(url);
  if(u.indexOf("/api/wds/review-gen")>=0){ const b=JSON.parse(init.body); await new Promise(r=>setTimeout(r,2)); return sseResp(canned(b)); }
  if(u.indexOf("/api/wds/review-shapes")>=0){ return new Response(JSON.stringify({version:"1.4",shapes:[{shape:"差型",words:["work-as-imagined work-as-done","prescribed task actual activity","compliance reliance warning"]},{shape:"改写型",words:["model repair process mining"]},{shape:"介入型",words:["behavioural adaptation assistance"]},{shape:"周期型",words:["incident learning cycle"]},{shape:"分歧型",words:["representational effect"]},{shape:"比例型",words:["appropriate reliance"]}]}),{status:200,headers:{"content-type":"application/json"}}); }
  if(u.indexOf("api.crossref.org")>=0){ calls.cr=(calls.cr||0)+1; const q=new URL(u).searchParams.get("query.bibliographic"); return new Response(JSON.stringify({message:{items:[{DOI:"10.2/cr"+q.replace(/\W/g,"").slice(0,5),title:["CR "+q],issued:{"date-parts":[[2004]]},"container-title":["Transp Res F"],author:[{given:"A",family:"B"}],volume:"7",issue:"2",page:"59-76"}]}}),{status:200,headers:{"content-type":"application/json"}}); }
  if(u.indexOf("api.semanticscholar.org")>=0){ calls.s2=(calls.s2||0)+1; const q=new URL(u).searchParams.get("query"); return new Response(JSON.stringify({data:[{title:"S2 "+q,year:2015,venue:"Inf Syst",externalIds:{DOI:"10.3/s2"+q.replace(/\W/g,"").slice(0,5)},abstract:"model repair abstract",authors:[{name:"Fahland"}],citationCount:100}]}),{status:200,headers:{"content-type":"application/json"}}); }
  if(u.indexOf("api.openalex.org")>=0){ calls.oa++; const p=new URL(u).searchParams; return new Response(JSON.stringify(oaResults(p.get("search"),+p.get("per-page"))),{status:200,headers:{"content-type":"application/json"}}); }
  throw new Error("unexpected fetch "+u);
};
w.TextDecoder=TextDecoder; w.TextEncoder=TextEncoder; w.URL.createObjectURL=()=>"blob:x"; w.URL.revokeObjectURL=()=>{}; w.HTMLElement.prototype.scrollIntoView=function(){};
const $=s=>w.document.querySelector(s);
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,ms){ const t=Date.now(); while(Date.now()-t<ms){ if(fn()) return true; await sleep(30);} return false; }
(async()=>{
  await sleep(200);
  // 选 GPT-5.6 Luna、How、深度档
  $('#vendSeg button[data-v="gpt"]').click();
  console.log("gptKeyBox 显示：", $("#gptKeyBox").style.display);
  $("#gptKey").value="sk-testkey-0123456789"; $("#gptKey").dispatchEvent(new w.Event("input"));
  $('#typeSeg button[data-k="how"]').click();
  $("#topic").value="流程工业操作员辅助"; $("#question").value="如何验证一个现场工步真的完成了";
  ["#topic","#question"].forEach(s=>$(s).dispatchEvent(new w.Event("input")));
  console.log("goBtn disabled:", $("#goBtn").disabled, " runBtn disabled:", $("#runBtn").disabled);
  $("#goBtn").click();
  const ok1=await until(()=>/清单已备好|中断/.test($("#status").textContent),8000);
  console.log("①②：", ok1, $("#status").textContent.slice(0,80));
  console.log("文献表行数：", w.document.querySelectorAll("table.lit tr").length-1, " 选中：", w.document.querySelectorAll("input[data-lit]:checked").length);
  $("#runBtn").click();
  const ok2=await until(()=>/完成|中断|失败/.test($("#status").textContent),60000);
  console.log("③–⑩：", ok2, $("#status").textContent.slice(0,100));
  const R=$("#results").textContent;
  const stages=[...w.document.querySelectorAll("#stages span")].map(x=>x.textContent+":"+(x.className||"-")).join(" ");
  console.log("阶段：",stages);
  console.log("产出件出现：", ["⑤ 整图","⑤ 之二","⑥ 表面","⑦ 五大","⑧ 现有","⑧ 之二","⑨ SDE","⑨ 之二","⑩ "].map(k=>k+"="+(R.indexOf(k)>=0)).join(" "));
  const chk=[...w.document.querySelectorAll("[data-check], .chk, .selfcheck li, .sc li")];
  const scText=(R.match(/自检[\s\S]{0,900}/)||[""])[0];
  console.log("自检片段：", scText.replace(/\s+/g," ").slice(0,700));
  console.log("mode 调用次数：", JSON.stringify(calls.modes), " OpenAlex 次数：", calls.oa, " Crossref：", calls.cr||0, " S2：", calls.s2||0, " 机检重出：", calls.retryCards);
  console.log("送往端点的 vendor/model：", [...calls.vendors], [...calls.models]);
  console.log("请求体缺字段：", calls.badBodies.length?calls.badBodies.slice(0,5):"无");
  console.log("页面脚本错误：", errs.length?errs.slice(0,8):"无");
  // 导出 md
  try{ $("#mdBtn").click(); console.log("导出 .md 点击：无异常"); }catch(e){ console.log("导出 .md 异常：",e.message); }
})();
