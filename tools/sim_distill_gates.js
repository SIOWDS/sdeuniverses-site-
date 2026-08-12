#!/usr/bin/env node
/* 成文（/api/wds/distill）的三道闸 —— 源码级守门。
   Worker 跑不在这个沙盒里，所以这里守的是"代码里那几条口径还在不在"。
   守它们是因为每一条都是真金白银撞出来的，而且**已经被改回去过一次**：
   /api/ask 2026-08-03 修掉"以为不加 reasoning_effort 就等于关思考"这个误解，
   成文这一档却一直留着同一个误解，直到 2026-08-12 用户报「凝成一万字论文」交白卷。 */
const fs = require("fs");
const path = require("path");
const W = fs.readFileSync(path.join(__dirname, "..", "src/worker.js"), "utf8");   // 别写死沙盒绝对路径
let PASS = 0, FAIL = 0;
const ok = (c, m) => { if (c) { PASS++; console.log("  PASS " + m); } else { FAIL++; console.log("  FAIL " + m); } };

// 只在成文那一段里找（从 SPEC 表到该路由结束），别让别的路由的同形代码蒙混过关
const i0 = W.indexOf('const SPEC = {\n        report: { name: "对话报告"');
const i1 = W.indexOf('/api/chat/clear', i0);
ok(i0 > 0 && i1 > i0, "定位到成文段（SPEC 表 → 路由结束）");
const D = W.slice(i0, i1);

console.log("① 预算：paper 档已是全站顶格，别再往上拧");
/* 档名不写死：它随字数口径改（一万字 → 两万字），而这一条要守的是 tok 顶格，不是叫什么名字。 */
ok(/paper: \{ name: "[^"]+", tok: WDS_TOK_MAX,/.test(D), "paper 档 tok = WDS_TOK_MAX（顶格）");
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
ok(/paper: \{ name: "[^"]+", tok: WDS_TOK_MAX, parts: [^,\n]+,/.test(D), "paper 档标了 parts（提纲按它定节数）");
/* 2026-08-12 扩到两万字之后又多一条：论文档的分节是**体例定死的**，不许再交给提纲那一趟发挥。
   parts 必须由骨架推导（不是一个手写的数），且 plan 合并时 ask/words 一律取表里的。 */
ok(/parts: PAPER_SKELETON\.length,\n\s*fixed: PAPER_SKELETON,/.test(D), "paper 档挂了固定骨架，parts 由骨架推导");
ok(/plan\.sections = FIXED\.map\(\(f, i\) => \(\{[\s\S]{0,220}ask: f\.ask,[\s\S]{0,60}words: f\.words,/.test(D),
  "plan 合并只收模型给的小标题，ask/words 一律取骨架里的");
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
