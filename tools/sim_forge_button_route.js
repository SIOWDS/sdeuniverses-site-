/* 锁住 2026-08-29 这次修复：「⊞ SDE 工序 → 学科通融」按钮此前只触发单轮简版
 * （服务端 WDS_TOOL_KEYS.forge），读者选中它、以为在走完整十八道，实际是另一条路。
 * 现在 curTool==="forge" 时 send() 直接短路成真产线（等同 /通融），按钮文案也同步改掉。
 * 这份护栏是纯文本静态检查（不搭 DOM），只为防止日后有人改动 send() 或按钮文案时
 * 无声滑回旧行为——真实端到端行为已由 sim_wds_mode_v2.js 与 sim_chatsde_forge.js 覆盖。
 * 用法：node tools/sim_forge_button_route.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const SITE = path.join(__dirname, "..");
let pass = 0, fail = 0;
function ok(name, cond) { if (cond) { pass++; console.log("  ✓ " + name); } else { fail++; console.log("  ✗ " + name); } }

const M = fs.readFileSync(path.join(SITE, "public/wds-mode.js"), "utf8");
const W = fs.readFileSync(path.join(SITE, "src/worker.js"), "utf8");

console.log("── SDE 工序 → 学科通融：按钮短路进真十八道产线 ──");
ok("★★ send() 里有 curTool==='forge' 的短路块", /curTool === "forge" && !streaming && !RS\.running/.test(M));
ok("★ 短路块只在 forgePick(q) 没命中时才接手（不抢真的 /通融 语义）", /!fgq && curTool === "forge"/.test(M));
ok("★ 短路块把整句 q 当 topic，不是只取斜杠后半句", /fgq = \{ topic: t0fg, judge:/.test(M));
ok("按钮文案（zh·主站）已不再自称\"简版\"", !/tlForgeS: "三家撞出一条新判断的简版/.test(M));
ok("按钮文案（zh·语言分站）已不再自称\"简版\"", !/tlForgeS: "三家互撞的简版/.test(M));
ok("按钮文案（en·主站/语言分站）已不再自称 short version", !/Short version of the three-way clash/.test(M));
ok("按钮文案说明现在等同 /通融或 /forge", /tlForgeS: "三家撞出一条新判断，走完整十八道产线（等同 \/通融）"/.test(M));

console.log("── 服务端旧单轮简版：留作死代码，但要有警示注释 ──");
ok("★ WDS_TOOL_KEYS.forge 前有\"已不可达\"的警示注释", /前端「⊞ SDE 工序 → 学科通融」按钮已在 send\(\) 里短路成真十八道产线/.test(W));
ok("旧单轮简版提示语本身还在（没删，留作兜底，只是标了警示）", /单轮简版】这一轮不写成品，只把二阶那一步做出来/.test(W));

console.log("\n" + (fail ? "✗ " : "✓ ") + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
