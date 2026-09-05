/* worker 提示层模拟：抽出 /api/wds/review-gen 的 prompt 构造，逐 mode 喂 GPT luna 请求体；跑法：node tools/sim_review_gen_worker.js */
// 抽出 worker.js 里 /api/wds/review-gen 的 prompt 构造层，逐 mode 喂输入，看有没有未定义引用/分支漏/字段漏
const fs=require("fs");
const W=fs.readFileSync(__dirname+"/../src/worker.js","utf8");
function grab(re){const m=W.match(re); if(!m) throw new Error("grab fail "+re); return m[0];}
const consts=[
  grab(/const REVIEW_CARD_FIELDS = \{[\s\S]*?\n\};\n/),
  grab(/const _RS_HEAD = \[[\s\S]*?\n\];\nconst _RS_TAIL = \[[\s\S]*?\n\];\nconst REVIEW_SKELETON = \{[\s\S]*?\n\};\n/),
  grab(/const REVIEW_TYPE_NAME = .*\n/), grab(/const REVIEW_TOOL_TEXT = \{[\s\S]*?\n\};\n/), grab(/const REVIEW_SHAPES = \[[\s\S]*?\n\];\n/), grab(/const REVIEW_SHAPE_NAMES = .*\n/), grab(/const REVIEW_QUESTION_FORM = .*\n/),
  grab(/function reviewType\(t\).*\n/), grab(/function reviewFieldTable\(type\).*\n/), grab(/const REVIEW_SDEM = .*\n/), grab(/const REVIEW_STYLE = .*\n/),
].join("\n");
const a=W.indexOf('if (url.pathname === "/api/wds/review-gen") {');
const b=W.indexOf("const rstream = new ReadableStream",a);
let blk=W.slice(a,b);
// 去掉 limiter 段（依赖 DO），其余原样
blk=blk.replace(/try \{\n\s*const lim = _do[\s\S]*?\} catch \(e\) \{\}\n/,"");
blk=blk.replace('if (url.pathname === "/api/wds/review-gen") {',"");
const fn=`
${consts}
const WDS_VMAP={ds:"deepseek",glm:"zhipu",gpt:"openai"};
function wdsVendorOf(v){return WDS_VMAP[String(v||"").toLowerCase()]||"zhipu";}
function wdsTopVC(vd,want){return {vd,model:want||"TOP",top:1};}
function wdsStdVC(vd,want){return {vd,model:want||"STD"};}
function _cors(){return {};}
module.exports=async function build(body){
  const url={pathname:"/api/wds/review-gen"};
  const request={method:"POST",headers:{get:()=>"1.1.1.1"},json:async()=>body};
  const Response={json:(o,init)=>({__json:o,status:(init||{}).status||200})};
  ${blk}
  return {sys,usr,tok,VC,deep};
};`;
fs.writeFileSync(__dirname+"/_built_review.js",fn);
const build=require(__dirname+"/_built_review.js");
const cards=[{i:1,title:"A",card:"承重命题：x\n起手维：S\n落点维：D\n所走路径：S→E→D\n中间维处置：映射\n判据与读数：y\n失效条件：z\n推翻对象：w\n余数：r\n原文锚句：“q”",layer:"经典"},{i:2,title:"B",card:"承重命题：x2\n起手维：E\n落点维：S\n所走路径：E→D→S",layer:"前沿"}];
const K={key:"sk-abcdefghij",vendor:"gpt",model:"gpt-5.6-luna",tier:"deep",type:"how",topic:"流程工业操作员辅助",question:"如何验证一个现场工步真的完成了"};
const cases=[
 {mode:"frame"},
 {mode:"card",title:"A",text:"x".repeat(200),idx:1,material:"abstract",meta:"m"},
 {mode:"map",cards},
 {mode:"neighbors",map:"整图……空格 D→S→E「显露即介入」；断链「区分先于显露」",aliases:"a；b"},
 {mode:"verdict",plan:"1．空格「显露即介入」｜邻近行：中断科学／临床告警",hits:"【项 1】Bailey 2006 …"},
 {mode:"surface",cards},
 {mode:"challenges",map:"M",verdict:"V",surface:"S",cards},
 {mode:"gaps",challenges:"C",map:"M"},
 {mode:"collide",map:"M 断链「区分先于显露」空格 S→D→E",verdict:"V",challenges:"C",gaps:"G",cards:cards.concat([{i:3,title:"C",card:"承重命题：x3\n起手维：D\n落点维：S\n所走路径：D→E→S",layer:"现代"}])},
 {mode:"collide_run",collide:"Z：…",cards:cards.concat([{i:3,title:"C",card:"承重命题：x3\n起手维：D",layer:"现代"}])},
 {mode:"conjectures",challenges:"C",gaps:"G",map:"M",verdict:"V",collide:"Z：…",collideRun:"支持"},
 {mode:"occupants",conjectures:"C",verdict:"V",hits:"H"},
 {mode:"territory",collide:"K",collideRun:"R",conjectures:"J",map:"M",verdict:"V",occupants:"O"},
 {mode:"territory_check",territory:"T",hits:"H"},
 {mode:"rename",frame:"F",map:"M",collide:"K",territory:"T",conjectures:"J",cards},
 ...[0,1,2,3,4,5,6,7,8,9,10,11,12,13].map(sec=>({mode:"write",sec,art:{frame:"F",map:"M",verdict:"V",surface:"S",challenges:"C",gaps:"G",collide:"Z",collideRun:"R",conjectures:"J",occupants:"O",territory:"T",territoryCheck:"TC"},rename:{terms:[{sde:"显露",disc:"画面",def:"d",src:"[1]",secs:"3"}],sections:{"问题与判类":"这个问题在问什么"},zName:"落锁位／Lock-in position",frameBox:"本文的分析框架……"},cards,refs:["r1","r2"],prev:"P"})),
 {mode:"bogus"},
 {mode:"frame",key:"short"},
];
(async()=>{
 let bad=0;
 for(const c of cases){
  const body=Object.assign({},K,c);
  try{ const r=await build(body);
    if(r&&r.__json){ console.log("• "+c.mode+(c.sec!=null?" sec"+c.sec:"")+" → 早退 "+r.status+" "+r.__json.msg); if(!(c.mode==="bogus"||c.key==="short"||(c.mode==="write"&&(c.sec===12||c.sec===13)))) bad++; continue; }
    const ok=r.sys.length>50&&r.usr.length>10&&r.tok>0&&r.VC.model==="gpt-5.6-luna";
    // 内容检查：v1.2 要素
    const flags=[];
    if(c.mode==="card"&&!/起手维→中间维→落点维/.test(r.sys)) flags.push("card 缺路径纪律");
    if(c.mode==="conjectures"&&!/语料空/.test(r.sys+r.usr)) flags.push("conjectures 未吃三判");
    if(c.mode==="conjectures"&&!/加一路|通道/.test(r.sys)) flags.push("conjectures 缺 S 侧加通道警报");
    if(c.mode==="occupants"&&/凭记忆点一位/.test(r.sys)) flags.push("occupants 仍允许凭记忆");
    if(c.mode==="occupants"&&!(/撤下条件/.test(r.sys)&&/检索盲区/.test(r.sys)&&/Crossref/.test(r.sys))) flags.push("occupants 缺 v1.3 撤下条件/盲区/三库");
    if(c.mode==="conjectures"&&!(/撤下条件/.test(r.sys)&&/形状/.test(r.sys)&&/闭环/.test(r.sys)&&/频率/.test(r.sys))) flags.push("conjectures 缺 v1.3 撤下/形状/闭环/频率");
    if(c.mode==="map"&&!/摘要级/.test(r.sys)) flags.push("map 缺空格分级");
    if(c.mode==="collide"&&!(/不得同维/.test(r.sys)&&/断链/.test(r.sys)&&/六型/.test(r.sys)&&/碰撞挑战/.test(r.sys))) flags.push("collide 缺 v1.4 纪律");
    if(c.mode==="collide"&&!(/起手维等于落格路径落点维/.test(r.sys)&&/借用/.test(r.sys)&&/典范级/.test(r.sys))) flags.push("collide 缺 v1.4.1 修补");
    if(c.mode==="conjectures"&&!/典范级/.test(r.sys)) flags.push("conjectures 缺三档");
    if(c.mode==="conjectures"&&!/领地接口/.test(r.sys)) flags.push("conjectures 缺领地接口");
    if(c.mode==="territory"&&!(/===TERRITORY===/.test(r.sys)&&/四改|四项至少三项/.test(r.sys)&&/退界/.test(r.sys))) flags.push("territory 缺要素");
    if(c.mode==="territory_check"&&!(/并入/.test(r.sys)&&/盲区/.test(r.sys))) flags.push("territory_check 缺要素");
    if(c.mode==="write"&&c.sec===10&&!/领地卡/.test(r.usr)) flags.push("write sec10 未喂领地卡");
    if(c.mode==="rename"&&!(/terms/.test(r.sys)&&/学科化/.test(r.sys))) flags.push("rename 缺要素");
    if(c.mode==="write"&&c.rename&&!/改性硬律/.test(r.sys)) flags.push("write 未吃映射表");
    if(c.mode==="write"&&c.rename&&c.sec===1&&!/方框/.test(r.usr)) flags.push("write sec1 未放方框");
    if(c.mode==="collide"&&!/语料内正主/.test(r.sys)) flags.push("collide 缺语料内正主");
    if(c.mode==="write"&&c.sec===9&&/领地卡/.test(r.usr)) flags.push("write sec9 多喂领地卡");
    if(c.mode==="collide_run"&&!/判负照登/.test(r.sys)) flags.push("collide_run 缺判负照登");
    if(c.mode==="conjectures"&&!(/碰撞级/.test(r.sys)&&/碰撞卡/.test(r.usr))) flags.push("conjectures 未吃碰撞卡/未标级");
    if(c.mode==="write"&&c.sec>=6&&c.sec<11&&!/碰撞卡/.test(r.usr)) flags.push("write sec"+c.sec+" 未喂碰撞卡");
    if(c.mode==="write"&&c.sec===8&&!/维度碰撞/.test(r.sys)) flags.push("write sec8 节名不是维度碰撞");
    if(c.mode==="write"&&c.sec>=5&&!/敌拓闸/.test(r.usr)) flags.push("write sec"+c.sec+" 未喂三判");
    if(c.mode==="write"&&c.sec<5&&/敌拓闸/.test(r.usr)) flags.push("write sec"+c.sec+" 多喂三判");
    if(/undefined/.test(r.sys+r.usr)) flags.push("prompt 里出现 undefined");
    console.log((ok&&!flags.length?"✓ ":"✗ ")+c.mode+(c.sec!=null?" sec"+c.sec:"")+"  sys="+r.sys.length+" usr="+r.usr.length+" tok="+r.tok+" model="+r.VC.model+(flags.length?"  ⚠ "+flags.join("；"):""));
    if(!ok||flags.length) bad++;
  }catch(e){ console.log("✗ "+c.mode+" 抛错："+e.message); bad++; }
 }
 console.log(bad?("FAIL "+bad):"ALL PASS");
})();
