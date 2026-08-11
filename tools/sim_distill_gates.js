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

console.log("\n===== " + PASS + " PASS / " + FAIL + " FAIL =====");
process.exit(FAIL ? 1 : 0);
