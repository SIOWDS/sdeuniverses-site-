/* 只测这次改的那一件事：满功率档的预算阶梯与空答降档。
   把 worker 里的 wdsLadder 抠出来单独跑，不依赖整个 worker 环境。 */
"use strict";
const fs = require("fs");
const src = fs.readFileSync("/home/claude/site/src/worker.js", "utf8");
const seg = src.slice(src.indexOf("const WDS_TOK_MAX"), src.indexOf("async function wdsFetchMax"));
const fn = new Function(seg + "\nreturn { wdsLadder, WDS_TOK_MAX, WDS_TOK_SAFE, WDS_TOK_RETRY, WDS_TOK_LADDER };")();
let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };

const top = { top: 1 }, plain = {};
const L = fn.wdsLadder(top);
ok(L[0] === 8000, "满功率首发预算 = 8000（不是 64000），实得 " + L[0]);
ok(L[0] > L[1] && L[1] > L[2], "阶梯逐级下降：" + L.join(" → "));
ok(L[L.length - 1] === 4000, "最低档 4000");
ok(Math.max(...L) <= 8000, "满功率档任何一级都不超过 8000（超了就会想到被杀）");
const LP = fn.wdsLadder(plain);
ok(LP[0] === 64000, "非满功率档不受影响，仍从 64000 起，实得 " + LP[0]);
const LR = fn.wdsLadder(top, fn.WDS_TOK_RETRY);
ok(LR[0] === 4000 && Math.max(...LR) === 4000, "重答传 4000 时整条阶梯都被压到 4000，不会反弹回高档");
ok(fn.WDS_TOK_RETRY < fn.WDS_TOK_SAFE, "重答预算严格小于首发预算——重答的意义就是降档");
console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
