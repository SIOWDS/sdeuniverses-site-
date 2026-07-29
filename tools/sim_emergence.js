/* 只测一件事：涌现流水线（十轮三观点 → 二阶碰撞 → 三典范择优 → 综合提炼）。
   规格来自王德生 2026-07-29：每次调用基底都装「内功＋心得＋SDE方法论」＝高超智慧；
   每轮三个观点；三观点二阶碰撞涌现新典范；创新检查不够就随机换碰撞方式重来，
   或碰三次出三典范比较择优；最后的综合提炼最要紧。
   随机抽签器与择优逻辑从页面里原样抠出来真跑——写死一份副本，那份永远不会跟着改。 */
"use strict";
const fs = require("fs");
const ROOT = "/home/claude/site";
const html = fs.readFileSync(ROOT + "/public/search/index.html", "utf8");
const wk = fs.readFileSync(ROOT + "/src/worker.js", "utf8");
let P = 0, FA = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (FA++, console.log("  FAIL " + m)); };

/* —— 抠出抽签器 —— */
const waysDecl = html.match(/var EMERGE_WAYS=\[[\s\S]*?\];/);
if (!waysDecl) { console.log("FAIL 抠不出 EMERGE_WAYS"); process.exit(1); }
let src = waysDecl[0] + "\nvar emergeUsed=[];\n";
["wayName", "pickWays"].forEach(function (n) {
  const a = html.indexOf("function " + n + "(");
  if (a < 0) { console.log("FAIL 抠不出 " + n); process.exit(1); }
  const b = html.indexOf("\nfunction ", a + 1);
  src += html.slice(a, b < 0 ? a + 900 : b) + "\n";
});
const F = new Function(src + "return {pick:pickWays,name:wayName,ways:EMERGE_WAYS,used:function(){return emergeUsed;},reset:function(){emergeUsed=[];}};")();

console.log("— 一、六种碰撞方式与随机不放回 —");
ok(F.ways.length === 6, "方式表有六种撞法");
ok(F.ways.map(w => w[0]).join() === "1,2,3,4,5,6", "编号 1–6 与服务端方式表对齐");
F.reset();
let r1 = F.pick(3);
ok(r1.length === 3 && new Set(r1).size === 3, "一次抽三种，互不重复");
let r2 = F.pick(3);
ok(r2.length === 3 && new Set(r2).size === 3, "第二次再抽三种，互不重复");
ok(r1.concat(r2).sort().join() === "1,2,3,4,5,6", "换方式重来时抽到的是剩下三种——真的换了方式");
let r3 = F.pick(3);
ok(r3.length === 3, "六种用完后自动重置牌堆，不会抽空");
F.reset();
let seen = new Set();
for (let i = 0; i < 60; i++) { F.reset(); F.pick(3).forEach(x => seen.add(x)); }
ok(seen.size === 6, "六十次抽样里六种撞法都出现过（确实是随机，不是固定前三）");
ok(F.name(4) === "换承重层级" && F.name(6).indexOf("反向撞") === 0, "方式名可读回");

console.log("— 二、worker：三观点纪律 —");
const tri = wk.slice(wk.indexOf('if (body.tri === true && mode === "answer")'), wk.indexOf('if (body.tri === true && mode === "answer")') + 2200);
ok(tri.length > 500, "tri 分支存在");
ok(/观点一：/.test(tri) && /观点二：/.test(tri) && /观点三：/.test(tri), "三个观点有固定行首标记（碰撞环节靠它切分）");
ok(/真有分歧/.test(tri) && /方向相反或互不相容/.test(tri), "硬性要求三者之间真有分歧");
ok(/同一判断的三种说法/.test(tri) && /作废/.test(tri), "三个只是同一判断的三种说法即本轮作废");
ok(/最容易在哪里被推翻/.test(tri), "每个观点自带一句可被推翻处");
ok(/不要综合、不要下结论、不要调和/.test(tri), "写完就停：现在调和等于把涌现的原料先烧掉");
ok(!/S 维度|三视角/.test(tri.replace(/这类内部环节词/, "")) || /绝不许出现/.test(tri), "内部环节词禁止出现在正文");

console.log("— 三、worker：二阶碰撞（collide） —");
const co = wk.slice(wk.indexOf('if (mode === "collide") {'), wk.indexOf('else if (mode === "synth")'));
ok(co.length > 2000, "collide 分支存在且不是空壳");
ok(/const WAYS = \{/.test(co), "服务端持有权威方式表（换方式重撞换的就是这一段）");
[1, 2, 3, 4, 5, 6].forEach(function (n) { ok(new RegExp("\\n        " + n + ": \"").test(co), "方式 " + n + " 有独立指令段"); });
ok(/一阶＝把已知元素重组/.test(co) && /二阶＝拿那个一阶产物当待撞物/.test(co), "写清一阶与二阶的分界");
ok(/只换名、只引自己人、给不出可裁决判据/.test(co) && /本次碰撞作废/.test(co), "停在一阶即作废");
ok(/不许在三个观点里挑一个当结论/.test(co), "择优不是碰撞");
ok(/不许把三个观点调和成一个更周全的说法/.test(co), "周全＝张力被抹平＝没有涌现");
ok(/X 不是 Y₁、也不是 Y₂，而是 Z/.test(co), "承重命题写成否定—重命名形态");
ok(/【可裁决判据】/.test(co) && /【两条证伪条件】/.test(co) && /【可观测代理】/.test(co), "典范骨架含判据/证伪/代理（好让盲评能打分）");
ok(/外文占位者（须给原题）/.test(co), "最近邻须含外文占位者并给原题");
ok(/neigong/.test(co) && /心得/.test(co), "碰撞装内功＋心得＝高超智慧");
ok(/S=F\(D,E\)/.test(co) && /逮先验/.test(co), "后台走三方程与逮先验");

console.log("— 四、worker：最终综合提炼（synth） —");
const sy = wk.slice(wk.indexOf('else if (mode === "synth")'), wk.indexOf('else if (mode === "distill")'));
ok(sy.length > 1800, "synth 分支存在且不是空壳");
ok(/最后一环/.test(sy) && /最要紧的一步/.test(sy), "写明这是整条产线最要紧的一步");
["一、最终承重命题", "二、它是怎么涌现出来的", "三、两个落选典范的可回收零件",
 "四、辨别面与二维辨别格", "五、可裁决判据", "六、敌意最近邻清单",
 "七、两条独立证伪条件", "八、经验材料清单", "九、评分卡开出的作业", "十、明确不写什么"].forEach(function (s) {
  ok(sy.indexOf(s) > 0, "十栏齐备 · " + s);
});
ok(/不浪费落选者/.test(sy), "落选典范的可回收零件不许扔");
ok(/把评分卡的短板变成作业/.test(sy), "盲评短板转写成论文作业");
ok(/这是入口资料不是论文/.test(sy), "入口资料不是可直接扩写的初稿");
ok(/body\.winner/.test(sy) && /body\.others/.test(sy) && /body\.cards/.test(sy), "吃胜出典范＋落选典范＋评分卡");
ok(/histTxt/.test(sy), "整场问对进得去");

console.log("— 五、路由与「高超智慧」口径 —");
ok(/_MODES = \{ recommend: 1, paper: 1, iq: 1, polish: 1, distill: 1, collide: 1, synth: 1 \}/.test(wk), "七个模式都在白名单里");
ok(/mode === "collide" \|\| mode === "synth"/.test(wk), "碰撞与综合提炼都走深度档（装内功＋心得＋方法论）");
const deepLine = wk.match(/const deep = body\.deep === true[^;]*;/)[0];
ok(!/mode === "iq"/.test(deepLine), "唯独盲评不装内功（防对 SDE 语言过敏性加分）");
ok(/_lightDeep/.test(wk), "碰撞/提炼的检索档下调（控成本）");

console.log("— 六、前端接线 —");
ok(/var deepOn=true/.test(html), "深度档默认打开：每次调用都是高超智慧");
ok(/function syncDeepUI/.test(html), "开机把开关 UI 同步成打开态（状态与请求不许对不上）");
ok(/triOn\?\{tri:true\}:\{\}/.test(html), "涌现档把 tri 透传给 worker");
ok(/if\(triOn && !deepOn\) toggleDeep\(\)/.test(html), "开涌现档强制拉起深度档");
ok(/id="btnEmerge"/.test(html) && /id="triBtn"/.test(html), "两个入口已挂上");
ok(/mode:'collide'/.test(html) && /mode:'iq',q:oq,text:p\.text/.test(html) && /mode:'synth'/.test(html), "碰撞→创新检查→综合提炼三环都接了");
ok(/paradigms\[best\]/.test(html) && /if\(\(p\.total\|\|0\)>\(paradigms\[best\]\.total\|\|0\)\) best=ix/.test(html), "择优＝同尺子下取最高分");
ok(/brief=String\(t\|\|''\)\.trim\(\)/.test(html), "综合提炼直接成为论文入口资料 brief");
ok(/换碰撞方式重来一次/.test(html), "不够创新可换方式重撞");
ok(/串行/.test(html) || /chain=chain\.then/.test(html), "三路碰撞串行跑，不并发点燃三份内功");
ok(/单路失败不拖垮另外两路/.test(html), "单路失败不拖垮另外两路");
ok(/turns\.length<2/.test(html), "少于两轮不许碰撞");

console.log("\n" + (FA ? "✗ " : "✓ ") + P + " PASS / " + FA + " FAIL");
process.exit(FA ? 1 : 0);
