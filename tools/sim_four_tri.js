// sim_four_tri.js — 四三角交叉块（2026-10-24 王德生令）的防回归检查
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

// ③ 四套三角九宫格齐全
for (const cell of ["对比·变化·分布", "粒子·波·场", "真·善·美", "创造·自由·幸福", "六步·九步", "误差·冗余·损耗", "理念·现实·自我", "符号·逻辑·数学", "内能·动能·势能"]) {
  ok(B.indexOf(cell) >= 0, "九宫格一格：" + cell);
}
for (const t of ["T1 S1·D1·E1", "T2 S2·D2·E2", "T3 S3·D3·E3", "T4 S3·D1·E2"]) ok(B.indexOf(t) >= 0, "三角：" + t);

// ④ 四件必做事与三条禁令
for (const k of ["【交叉点】", "【交叉判断】", "去掉 T?", "不许贴标签", "不许并排", "不许只交叉不预测", "此点不起作用"]) ok(B.indexOf(k) >= 0, "要件：" + k);
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
const n16 = (src.match(/（十六）四角交叉：/g) || []).length;
ok(n16 === 1, "成文自检规程有（十六）四角交叉一条");
ok(src.indexOf("（十六）四角交叉") < src.indexOf("【成文格式纪律（PDF 排版靠它"), "（十六）在成文格式纪律之前（同一 base 串内）");

console.log("\n" + (fail ? "✗ " : "✓ ") + pass + " PASS / " + fail + " FAIL");
process.exit(fail ? 1 : 0);
