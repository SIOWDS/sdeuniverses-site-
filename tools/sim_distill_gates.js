#!/usr/bin/env node
/* 成文（/api/wds/distill）的三道闸 —— 源码级守门。
   Worker 跑不在这个沙盒里，所以这里守的是"代码里那几条口径还在不在"。
   守它们是因为每一条都是真金白银撞出来的，而且**已经被改回去过一次**：
   /api/ask 2026-08-03 修掉"以为不加 reasoning_effort 就等于关思考"这个误解，
   成文这一档却一直留着同一个误解，直到 2026-08-12 用户报「凝成一万字论文」交白卷。 */
const fs = require("fs");
const W = fs.readFileSync("/home/claude/site/src/worker.js", "utf8");
let PASS = 0, FAIL = 0;
const ok = (c, m) => { if (c) { PASS++; console.log("  PASS " + m); } else { FAIL++; console.log("  FAIL " + m); } };

// 只在成文那一段里找（从 SPEC 表到该路由结束），别让别的路由的同形代码蒙混过关
const i0 = W.indexOf('const SPEC = {\n        report: { name: "对话报告"');
const i1 = W.indexOf('/api/chat/clear', i0);
ok(i0 > 0 && i1 > i0, "定位到成文段（SPEC 表 → 路由结束）");
const D = W.slice(i0, i1);

console.log("① 预算：paper 档已是全站顶格，别再往上拧");
ok(/paper: \{ name: "一万字论文", tok: WDS_TOK_MAX,/.test(D), "paper 档 tok = WDS_TOK_MAX（顶格）");
ok(/const WDS_TOK_MAX = 64000;/.test(W), "WDS_TOK_MAX 仍是 64000");

console.log("② 闸一 · 关思考：满预算只有关掉思考才会变成正文");
const call = D.match(/wdsFetchMax\(VCuse, KEY, messages,[^\n]*/);
ok(!!call, "找得到成文的首发调用");
ok(!!call && /,\s*undefined,\s*true\);/.test(call[0]), "首发带 plain=true（第 9 个参数），实得 " + (call ? call[0].slice(-40) : "无"));
ok(/body: JSON\.stringify\(wdsPlainBody\(VC, \{ model: VC\.model, stream: true, max_tokens: _retryTok/.test(D),
   "兜底重跑走 wdsPlainBody（不走＝只是没加 reasoning_effort，基底默认仍在思考）");
ok(!/刻意不走 wdsTopBody：这一遍就是要/.test(D), "那条会误导人的旧注释已删（它声称的事它并没做到）");

console.log("③ 闸二 · 首帧闸只认正文");
ok(/if \(d\.reasoning_content\) \{ _st\.think \+= d\.reasoning_content\.length;/.test(D),
   "reasoning 不再触发 clk.firstFrame()（否则'只思考不写字'当场解除首帧闸）");
ok(/if \(d\.content\) \{ clk\.firstFrame\(\);/.test(D), "只有正文触发 firstFrame");

console.log("④ 闸三 · 降档口径");
ok(/const _retryTok = Math\.min\(16000, SPEC\.tok\);/.test(D),
   "重跑降到 16000：降的是'想多久'不是'能写多长'（4000 实测交回断在半句的稿）");
ok(D.indexOf("_retryTok") > 0 && !/Math\.min\(32000, Math\.round\(SPEC\.tok \/ 2\)\)/.test(D),
   "诊断行与真实预算是同一个数，不再各写一份");

console.log("⑤ 关思考没生效要看得见");
ok(/关思考未生效/.test(D), "重跑流里若仍收到 reasoning，阶段名写明'关思考未生效'（某家不认这个字段时的唯一线索）");

console.log("⑥ 拆趟：长档不许再走单趟");
ok(/paper: \{ name: "一万字论文", tok: WDS_TOK_MAX, parts: \d+,/.test(D), "paper 档标了 parts（提纲按它定节数）");
ok(/const dStage = String\(b\.stage \|\| ""\);/.test(D), "端点收 stage");
ok(/if \(dStage === "plan" \|\| dStage === "part"\)/.test(D), "plan / part 两个分支都在");
ok(/const _pl = att \? \[8000, 6000, 4000\] : \[12000, 8000, 6000\];/.test(D) && /_pl\[0\], pclk\.signal, false, _pl, true\)/.test(D),
   "拟题：关思考＋自带阶梯的有界预算（结构化 JSON 配满功率必崩，站内老账）");
ok(/const _sl = \[stok, Math\.max\(3000/.test(D) && /sclk\.signal, true, _sl, true\)/.test(D),
   "两处都自带阶梯——wdsLadder 的非满功率分支忽略 want，不自带就等于没设预算");
ok(/looseJSON\(raw\)/.test(D) && /att < 2/.test(D), "提纲解不出就再试一次，且用 looseJSON 兜住围栏与碎话");
ok(/sclk\.signal, true, _sl, true\)/.test(D), "分部：同样显式关思考（plain=true）");
ok(/Math\.min\(16000, Math\.max\(3000, Math\.round\(want \* 2\.2\)\)\)/.test(D), "分部预算按这一节的字数给，不是拍脑袋一个大数");
ok(/只写这一节/.test(D) && /别写全篇导言或结语/.test(D), "提示语钉死「只写这一节」——否则每节都会重写一遍全篇");
ok(/上一节的结尾（只为接得上，别复述它）/.test(D), "带上一节结尾做接缝，并明说别复述");

console.log("\n===== " + PASS + " PASS / " + FAIL + " FAIL =====");
process.exit(FAIL ? 1 : 0);
