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
for (const cell of ["对比·变化·分布", "粒子·波·场", "真·善·美", "创造·自由·幸福", "六步·九步", "误差·冗余·损耗", "理念·现实·自我", "符号·逻辑·数学", "内能·动能·势能"]) {
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

console.log("\n" + (fail ? "✗ " : "✓ ") + pass + " PASS / " + fail + " FAIL");
process.exit(fail ? 1 : 0);
