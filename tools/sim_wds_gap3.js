/* sim_wds_gap3.js —— 缝隙创新法（gap3，2026-11-03 王德生令）护栏：正文三元素三缝齐全、TOOL_SPEC 十件可编译、好样本全中、空话样本判缺。跑法：node tools/sim_wds_gap3.js */
const fs=require("fs");const W=fs.readFileSync(require("path").join(__dirname,"..","src/worker.js"),"utf8");
function grab(a,b){const i=W.indexOf(a),j=W.indexOf(b,i);if(i<0||j<0)throw new Error("grab "+a);return W.slice(i,j);}
let p=0,f=0;const ok=(n,c)=>{c?p++:(f++,console.log("  ✗ "+n));};
const T=new Function("return {"+grab("  gap3: \"","\n  collide: \"")+"};")();
const s=T.gap3; ok("gap3 正文存在",typeof s==="string"&&s.length>1500);
for(const w of ["三方程","六路径","三原理","发现学预设","发生学原理","自然","本来","天生","天赋","S＝F(D,E)","D＝G(S,E)","E＝H(S,D)","原理一 D×E","原理二 S×E","原理三 S×D","S→D→E","E→D→S","证伪","分离线","做不到就直说","第一道闸"]) ok("正文含 "+w,s.includes(w));
const SP=new Function(grab("const _LN =","\nconst EN_MIN_RATIO")+"\nreturn TOOL_SPEC;")();
const g=SP.gap3; ok("TOOL_SPEC.gap3",g&&g.min===2600&&g.items.length===11);
for(const it of g.items){try{new RegExp(it.re);new RegExp(it.en||".");p++}catch(e){f++;console.log("  ✗ regex "+it.k)}}
// a mock good answer should satisfy all zh items; an empty-ish one should fail most
const good=`它已经走到这一句：「教师的提问质量决定了课堂学习的深度」。\n发现学预设一：「孩子天生就有好奇心，教师只需保护它」。发现学预设二：「学生的已有经验本来就是稳定的起点」。\n三方程：冻结了E，当常量。六路径：只走E→D→S，回程没走。三原理：压下了原理三的矛盾。\n发生学原理一：…陈述…成立条件：…证伪：…发生学原理二：…成立条件…证伪…\n换上原理之后，原文那一句接下去变成：…\n分离线：在甲情形下，旧说法预测A，本原理预测B。\n合看与自指：这个预设本身是怎样发生的。`;
const cnt=(re,t)=>(t.match(new RegExp(re,"g"))||[]).length;
const miss=g.items.filter(it=>cnt(it.re,good)<(it.n||1)).map(it=>it.k);ok("好样本全件命中"+(miss.length?"（缺："+miss.join("；")+"）":""),!miss.length);
const bad="这篇论文很好，还可以进一步研究。";ok("空话样本被判缺件",g.items.filter(it=>cnt(it.re,bad)<(it.n||1)).length>=8);
console.log(`✓ sim_gap3: ${p} passed, ${f} failed`);process.exit(f?1:0);
