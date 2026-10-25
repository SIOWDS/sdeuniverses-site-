// sim_four_tri.js — 四三角交叉块（2026-10-24 王德生令；10-25 v2 改为异位套主力）的防回归检查
// 跑法：node tools/sim_four_tri.js
const fs = require("fs");
const path = require("path");
const src = fs.readFileSync(path.join(__dirname, "..", "src", "worker.js"), "utf8");
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) { pass++; console.log("  ✓ " + m); } else { fail++; console.log("  ✗ " + m); } };

// ① 定义恰好一次，且能当场求值
const defRe = /const FOUR_TRI_BLOCK = ([\s\S]*?);\n/;
const m = src.match(defRe);
ok(!!m, "FOUR_TRI_BLOCK 有定义");
let B = "";
try { B = Function('"use strict";return (' + m[1] + ");")(); } catch (e) { B = ""; }
ok(B.length > 800, "块能求值且非空（" + B.length + " 字符）");
ok((src.match(/const FOUR_TRI_BLOCK\b/g) || []).length === 1, "定义只有一处");

// ② 注入：恰好一处，且带「母体档、非研究产线」闸
const inj = src.match(/\+ \(\(prof \|\| rs\) \? "" : FOUR_TRI_BLOCK\)/g) || [];
ok(inj.length === 1, "WDS_CHAT_SYS 里注入一处，闸为 (prof || rs)");
const sysStart = src.indexOf("function WDS_CHAT_SYS(");
const sysEnd = src.indexOf("\n}\n", sysStart);
const sysBody = src.slice(sysStart, sysEnd);
ok(sysBody.indexOf("FOUR_TRI_BLOCK") > sysBody.indexOf("wdsToolSys(tool, prof, rung)"), "注入位在工序块之后（任务压在材料之后）");
ok(sysBody.indexOf("FOUR_TRI_BLOCK") < sysBody.indexOf("prof.term : \"\")"), "注入位在术语闸之前（术语闸仍是最末）");

// ③ 九宫格齐全
for (const cell of ["对比·变化·分布", "粒子·波·场", "真·善·美", "创造·自由·幸福", "前行·回写·跃层", "误差·冗余·损耗", "理念·现实·自我", "符号·逻辑·数学", "内能·动能·势能"]) {
  ok(B.indexOf(cell) >= 0, "九宫格一格：" + cell);
}
// ③b v2（2026-10-25 王德生裁定）：异位套六套轮换为主力，同位套三套只作对照
const HET = ["S1·D2·E3", "S1·D3·E2", "S2·D1·E3", "S2·D3·E1", "S3·D1·E2", "S3·D2·E1"];
const HOM = ["S1·D1·E1", "S2·D2·E2", "S3·D3·E3"];
for (const t of HET) ok(B.indexOf(t) >= 0, "异位套：" + t);
for (const t of HOM) ok(B.indexOf(t) >= 0, "同位套（对照）：" + t);
// 异位套确是 1/2/3 的六个排列，且不含同位
const perm = HET.map((x) => x.replace(/[^0-9]/g, ""));
ok(new Set(perm).size === 6 && perm.every((d) => new Set(d).size === 3), "异位六套＝编号 1/2/3 的全部六个排列");
// 两组拉丁三角：每组三套恰好用尽九格
const groups = [["S1·D2·E3", "S2·D3·E1", "S3·D1·E2"], ["S1·D3·E2", "S2·D1·E3", "S3·D2·E1"]];
for (const g of groups) {
  const cells = g.join("·").split("·");
  ok(new Set(cells).size === 9, "拉丁组用尽九格各一次：" + g.join("／"));
}
ok(/同位套（只作对照，不作主力）/.test(B), "同位套写明只作对照");
ok(/最容易出新典范/.test(B) && /最容易被占位/.test(B), "两类三角的用法理由都写进去了");
ok(/六套轮换/.test(B) && /本轮轮到/.test(B), "六套轮换与「本轮轮到」");

// ③c v3：D2 三分＝九步三个角度；占位拆套
ok(B.indexOf("六步·九步") < 0, "D2 旧写法「六步·九步」已撤");
ok(/前行＝猜想→执行→评估/.test(B) && /回写＝反馈→修正→迭代/.test(B) && /跃层＝分化→重组→升维/.test(B), "D2 三项各对三步，合计九步");
ok(/占位就拆套/.test(B) && /3 套同位子三角/.test(B) && /6 套异位子三角/.test(B) && /【拆套】/.test(B), "占位拆套：3 同位＋6 异位子三角，交【拆套】行");
ok(/一答最多拆一层/.test(B) && /拆套未出新/.test(B), "拆套有层数上限与落空出口");
ok(/按①②③的序号排/.test(B), "各格三项有序号（同位/异位子三角的判据）");
// ④ 要件与禁令
for (const k of ["【交叉点】", "【交叉判断】", "【同位对照】", "不许贴标签", "不许并排", "不许退回同位", "此套此点不起作用"]) ok(B.indexOf(k) >= 0, "要件：" + k);
// ⑤ 两条平台纪律
ok(/不是读者在重贴/.test(B) && /不许指责读者重复/.test(B), "平台纪律①：自动追问不是读者重贴");
ok(/只围绕本场这一题/.test(B), "平台纪律②：不串入别的专著与场次");
ok(/闲聊/.test(B) && /不出四角卡/.test(B), "豁免：问站务、闲聊不出四角卡");
ok(/〔落位〕〔交账〕/.test(B), "与工序格式共存：落位/交账行照旧");

// ⑥ 术语纪律（站规铁律 6）
ok(B.indexOf("产生") < 0, "不写「产生」");
ok(B.indexOf("意识界") < 0, "不写「意识界」");
ok(!/S\s*[=＝]\s*结构/.test(B), "S 不写成结构");

// ⑦ 成文自检第十六条
const n16 = (src.match(/（十六）异位四角交叉：/g) || []).length;
ok(n16 === 1, "成文自检规程有（十六）异位四角交叉一条");
const s16 = src.slice(src.indexOf("（十六）异位四角交叉："), src.indexOf("（十六）异位四角交叉：") + 1200);
ok(HET.every((x) => s16.indexOf(x) >= 0), "（十六）列出六套异位");
ok(/只许作对照/.test(s16), "（十六）同位只许作对照");
ok(src.indexOf("（十六）异位四角交叉") < src.indexOf("【成文格式纪律（PDF 排版靠它"), "（十六）在成文格式纪律之前（同一 base 串内）");
ok(src.indexOf("（十六）四角交叉：") < 0, "旧版（十六）已替换");
ok(/前行·回写·跃层/.test(s16 + src.slice(src.indexOf("（十六）异位四角交叉："), src.indexOf("（十六）异位四角交叉：") + 2000)), "（十六）D2 已改三项");
ok(/拆成子三角/.test(src.slice(src.indexOf("（十六）异位四角交叉："), src.indexOf("（十六）异位四角交叉：") + 2000)), "（十六）含占位拆套");

// ⑧ v4（2026-10-25「改」）：近邻先行、可观察落点、轮换照实；成文请求接入成文规矩
ok(/【近邻】/.test(B) && /至少跨三个学科/.test(B), "四角卡加【近邻】行，至少跨三个学科");
ok(/Y 取上一行里最近的那一个近邻/.test(B), "交叉判断的 Y 取最近邻");
ok(/能看见、能数的事/.test(B), "每行须落到可观察之事（防贴标签）");
ok(/本轮未换/.test(B) && /不许写「全换」/.test(B), "轮换照实自报");
const fm = src.match(/function wdsPaperAsk\(q\) \{[\s\S]*?\n\}/);
ok(!!fm, "wdsPaperAsk 有定义");
let PA = null; try { PA = Function(fm[0] + "; return wdsPaperAsk;")(); } catch (e) {}
ok(!!PA, "wdsPaperAsk 可求值");
if (PA) {
  ok(PA("请将我们上面的问对进行提炼，打造一个创新智商分数超过140的论文，长度是 8000字。"), "识别：九问成书那句成文指令");
  ok(PA("请将我们上面的讨论总结和提炼出一篇8000字的创新论文"), "识别：学员版成文指令");
  ok(!PA("客气是什么、不是什么？"), "不误认：普通提问");
  ok(!PA("这篇论文里的戈夫曼是谁？"), "不误认：只提到论文二字的提问");
}
const pm = src.match(/const PAPER_ASK_BLOCK = ([\s\S]*?);\n/);
let PB = ""; try { PB = Function('"use strict";return (' + pm[1] + ");")(); } catch (e) {}
ok(PB.length > 600, "PAPER_ASK_BLOCK 可求值（" + PB.length + " 字符）");
for (const k of ["字数写足", "异位四角交叉", "同位对照", "敌意拓宽", "方向相反的已有实验", "判别局面", "本文怎样会错", "借来的结构必须论证", "文献三验"]) ok(PB.indexOf(k) >= 0, "成文规矩：" + k);
ok(PB.indexOf("产生」") >= 0 && PB.replace("用「发生」不用「产生」", "").indexOf("产生") < 0, "成文规矩里「产生」只出现在禁用说明里");
ok(/wdsPaperAsk\(q\)\) \? PAPER_ASK_BLOCK : ""/.test(src), "成文规矩挂在当轮 user 消息上");
ok(/\(!tool \|\| \/\^\(what\|how\|why\)q\?\$\/\.test\(tool\)\)/.test(src), "工序里只放行 What/How/Why 问对");

// ⑨ v5（2026-10-25「三处改」＋远域结构修）
const tm = src.match(/function sentryTermOf\(seed\) \{[\s\S]*?\n\}/);
let TERM = null; try { TERM = Function(tm[0] + "; return sentryTermOf;")(); } catch (e) {}
ok(!!TERM, "sentryTermOf 可求值");
if (TERM) {
  ok(TERM("客气是什么、不是什么？亲戚来家里吃饭，主人一再说「没什么菜，随便吃」") === "客气", "占位哨检索词：整句→「客气」");
  ok(TERM("1. 舍不得是什么、不是什么？母亲舍不得扔孩子小时候的一件毛衣") === "舍不得", "占位哨检索词：去编号→「舍不得」");
  ok(TERM("「断舍离」很流行，很多人说「东西只是东西」") === "断舍离", "占位哨检索词：引号里的概念");
}
ok(/async function nbrChain\(env, seed, glmKey, extra, fq\)/.test(src), "nbrChain 收外文译词 fq（旧三处调用不受影响）");
ok(/k: "外文\(译\)"/.test(src) && /k: "中文原典"/.test(src), "外文(译) 与 中文原典 两趟");
ok(/_whys\.filter\(\(w\) => w !== "skipped_no_latin"\)/.test(src), "占位哨报真因：跳过外文不算失败原因");
ok(/sentryEnQuery\(VC, KEY, _term\)/.test(src) && /no names, no years/.test(src), "中文题目译英文检索词，只译概念不编人名");
ok(/不许替近邻编一个它没说过的预测/.test(B) && /与它同向，此处无判别力/.test(B), "四角卡：近邻预测只用它本人说过的");
ok(/先收窄/.test(PB) && /真正没人说过的新东西/.test(PB), "成文：先收窄到真新的一两条");
ok(/先写它已经说中了什么、引原话/.test(PB) && /不许把他的立场说反/.test(PB), "成文：先承认近邻、不许说反");
ok(/wdsPaperAsk\(q\) \? null : farPick/.test(src), "成文那一轮不挂远域结构");
ok(/m\.role === "reader" \|\| m\.role === "user"\)\)\.length : 0;\n\s*const _far/.test(src), "远域轮转按读者轮数（24 门全可达）");

console.log("\n" + (fail ? "✗ " : "✓ ") + pass + " PASS / " + fail + " FAIL");
process.exit(fail ? 1 : 0);
