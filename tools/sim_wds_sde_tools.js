/* 后端 SDE 工序守门（源码级断言）：tools/sim_wds_sde_tools.js
 * 守的是几件一旦漂掉就静默出错的事：
 *   ① 九道工序 key 齐、每道都有实体块，且每道都留了「做不到就直说」的出口；
 *   ② tool 走白名单（绝不能把读者传来的字符串拼进 system）；
 *   ③ 工序块真的拼进了 WDS_CHAT_SYS，且近邻名单**前置**在语料之前（否则被两万字语料埋掉）；
 *   ④ 满功率档的 max_tokens 仍然 ≤ 8000（老血案：满功率＋大预算＝只有思考、正文 0 字）。
 * 用法：node tools/sim_wds_sde_tools.js
 */
"use strict";
const fs = require("fs");
let PASS = 0, FAILS = 0;
function ok(c, m) { if (c) { PASS++; console.log("  PASS " + m); } else { FAILS++; console.log("  FAIL " + m); } }

const W = fs.readFileSync("src/worker.js", "utf8");
const F = fs.readFileSync("public/wds-mode.js", "utf8");

console.log("① 九道工序齐全且各有实体");
const KEYS = ["iq", "three", "motif", "nbr", "rename", "gap", "collide", "grid", "nine"];
const mKeys = W.match(/const WDS_TOOL_KEYS = \[([^\]]+)\]/);
ok(!!mKeys, "WDS_TOOL_KEYS 存在");
KEYS.forEach((k) => ok(mKeys && mKeys[1].includes('"' + k + '"'), "白名单里有 " + k));
const seg = W.slice(W.indexOf("const WDS_TOOLS = {"), W.indexOf("function wdsToolSys("));
KEYS.forEach((k) => ok(new RegExp("\\n  " + k + ":").test(seg), k + " 有工序正文"));
ok(/本轮工序/.test(seg) && (seg.match(/本轮工序/g) || []).length === 9, "九道都以「本轮工序」开头，实得 " + (seg.match(/本轮工序/g) || []).length);
// 每道都要有「做不到就直说」的出口——工序最怕的不是做不到，是假装做到了
const bodies = seg.split(/\n  (?=[a-z]+:)/).slice(1);
ok(bodies.length === 9, "切出九段工序正文，实得 " + bodies.length);
const OUT = /直说|不要编|别硬凑|说不足以|不许说|凑不满|凑不出|撑不起|就说用不上|会的话指出/;
bodies.forEach((b, i) => ok(OUT.test(b), KEYS[i] + " 留了「做不到就直说」的出口"));

console.log("② tool 走白名单");
ok(/WDS_TOOL_KEYS\.indexOf\(String\(b\.tool \|\| ""\)\) >= 0 \? String\(b\.tool\) : ""/.test(W),
   "认不出的 tool 一律当没选（不把读者传来的字符串拼进 system）");

console.log("③ 工序块拼进 system；近邻名单前置");
ok(/function WDS_CHAT_SYS\(reflect, SDEM, siteCtx, webCtx, deep, docCtx, about, lang, docNote, tool\)/.test(W),
   "WDS_CHAT_SYS 收 tool");
ok(/\+ wdsToolSys\(tool\)/.test(W), "system 里拼了 wdsToolSys(tool)");
ok(/WDS_CHAT_SYS\(reflect, SDEM, \(nbrCtx \? nbrCtx \+ "\\n" : ""\) \+ ctxText/.test(W),
   "近邻名单前置在站内语料之前（放后面会被两万字语料埋掉）");
ok(/if \(tool === "nbr"\)/.test(W) && /await nbrFor\(env, url, q, 10/.test(W), "近邻工序取的是真名单（共用 nbrFor）");
ok(/t: "nbrfail"/.test(W) && /nbrfail/.test(F), "取不到名单时发 nbrfail，前端如实说一句——不许静默失败");
ok(/wide = deep \|\| tool === "collide"/.test(W), "碰撞工序加宽站内检索（否则挑不出互相矛盾的三篇）");

console.log("④ 满功率预算没被工序顶破");
const mt = W.match(/max_tokens: deep \? (\d+) : \(tool \? (\d+) : (\d+)\)/);
ok(!!mt, "chat 的 max_tokens 三分支存在");
ok(mt && +mt[1] <= 8000, "满功率档 ≤ 8000（这是硬约束不是可调参数），实得 " + (mt ? mt[1] : "?"));
ok(mt && +mt[2] > +mt[3] && +mt[2] <= 12000, "工序档比闲聊宽但仍有界，实得 " + (mt ? mt[2] + " vs " + mt[3] : "?"));

console.log("⑤ 前端只传 key，不自己拼工序文本");
ok(/tool: curTool/.test(F), "payload 带 tool");
ok(!/本轮工序/.test(F), "前端不含任何工序正文（拼在前端会被后端 q 的 800 字钳位吃掉）");
ok(/curTool = toolInfo\(k\) \? k : ""/.test(F), "前端也只放行认得的 key");
ok(!/sde_wds_tool/.test(F), "工序不落 localStorage（会实质改变产出形态，不该在看不见处跨会话生效）");

console.log("\n结果：PASS " + PASS + " · FAIL " + FAILS);
process.exit(FAILS ? 1 : 0);
