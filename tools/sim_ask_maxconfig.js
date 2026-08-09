/* 只测一件事：/api/ask 这条**流式主路**上，「思考与正文吃同一份 max_tokens」这件事有没有被算清楚。

   病史（2026-08-09 线上真跑抓到，两次）：
     · mode=iq    ：思考 12,526 字 / 正文 0 字（预算 3600 被推演吃光，评分卡是必须完整的 JSON）
     · mode=polish：思考 10,906 字 / 正文 0 字（预算 6800 同样被吃光）
   用户看到的只是一句「0 字，重试一次后仍未成功」——**根因在页面上完全看不出来**。
   第一版处置是「关掉思考」（止血，但把最值钱的一半砍了）；
   现版按用户令「用最大配置」改成正解：**加预算、不减思考**，并给长思考期挂心跳。

   所以这个护栏钉的是三件事：预算够不够、满功率挂在该挂的地方、心跳在不在。
   这三件都属于「坏了也不报错」的那一类，只能靠判据钉死。 */
"use strict";
const fs = require("fs");
const W = fs.readFileSync("/home/claude/site/src/worker.js", "utf8");

let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };

/* ===== 一、预算：按「产出本身该有多长」定，不是按「想让它多想一会儿」 ===== */
console.log("— 一、各模式的 max_tokens —");
const grab = (re) => { const m = W.match(re); return m ? Number(m[1]) : -1; };
const iqTok = grab(/if \(mode === "iq"\) \{[\s\S]{0,400}?MAXTOK = (\d+);/);
const longTok = grab(/mode === "paper" \|\| mode === "polish"\) \{\s*\n\s*MAXTOK = (\d+);/);
/* 实测底数：思考 ≈8k tok（iq）／7–9k tok（polish），正文 2–3k（评分卡）／≈4000（五六千汉字）。
   预算必须同时装下这两半，否则第一遍结构性地一个字都出不来。 */
ok(iqTok >= 11000, "iq 预算 " + iqTok + " ≥ 11000（思考 ≈8k ＋ 评分卡 2–3k 要同吃这一份）");
ok(longTok >= 14000, "paper/polish 预算 " + longTok + " ≥ 14000（思考 7–9k ＋ 正文 ≈4000）");
ok(longTok <= 32000, "但也不许无界加码：" + longTok + " ≤ 32000（站内硬教训——预算给到几万，它会一路想到被平台时长上限杀在思考阶段）");

/* ===== 二、满功率：只挂在长文上，绝不挂在结构化短输出上 ===== */
console.log("— 二、满功率的位置 —");
const mTop = W.match(/const _topPower = \(([^)]*)\);/);
ok(!!mTop, "_topPower 判据在位");
const isTop = new Function("mode", "return (" + (mTop ? mTop[1] : "false") + ");");
ok(isTop("paper") === true && isTop("polish") === true, "真跑：paper / polish 挂满功率");
ok(isTop("iq") === false, "真跑：iq **不挂**满功率——满功率对要求结构化短输出的调用是毒（本文件 4500 行的硬教训）");
ok(isTop("answer") === false && isTop("distill") === false && isTop("nextq") === false,
   "真跑：answer / distill / nextq 不挂满功率");
ok(/const _VCX = _topPower \? \{ url: VC\.url, model: VC\.model, name: VC\.name, top: 1 \} : VC;/.test(W),
   "满功率靠给 VC 挂 top:1（wdsTopBody 认的就是这个标记）");
ok(/body: JSON\.stringify\(_topPower \? wdsTopBody\(_VCX, _mainBody\) : _mainBody\)/.test(W),
   "判据真的接到了主调用的 body 上（算对了没接上，等于没改）");
ok(/function wdsTopBody\(VC, body\) \{[\s\S]{0,300}?reasoning_effort = "max"/.test(W),
   "wdsTopBody 确实在挂满功率（thinking:enabled ＋ reasoning_effort:max）");

/* ===== 三、心跳：预算一大，思考期就长，链路会把静默判死 ===== */
console.log("— 三、心跳 —");
const iRun = W.indexOf("const runMain = async (controller) => {");
const iDone = W.indexOf('data: [DONE]', iRun);
const runBlk = W.slice(iRun, iDone);
ok(/const _hb = wdsBeat\(controller, _st\);/.test(runBlk), "出流后立刻起心跳");
ok(/const _st = \{ t0: Date\.now\(\), think: 0, out: 0/.test(runBlk), "心跳带活数据（已跑秒数／已推演字数），不是一个空 ping");
ok(runBlk.indexOf("_hb = wdsBeat") < runBlk.indexOf("_drain(upstream"), "心跳排在 _drain 之前（等它跑完再起，静默期正好没人守）");
ok(/try \{ clearInterval\(_hb\); \} catch \(e\) \{\}/.test(W.slice(iRun, iRun + 4000)), "收尾清掉定时器，不留孤儿");
ok(/function wdsBeat\(controller, state\)/.test(W), "wdsBeat 是站内既有的那一台，没另造一份");

/* ===== 四、兜底重跑：关思考＋降档，但长文不许降到断句 ===== */
console.log("— 四、兜底重跑 —");
const mR = W.match(/const _retryTok = ([^;]*);/);
ok(!!mR, "_retryTok 在位");
const retryFn = new Function("mode", "MAXTOK", "const _topPower = (" + mTop[1] + "); const _retryTok = " + mR[1] + "; return _retryTok;");
ok(retryFn("polish", 16000) === 8000, "polish 重跑降到 8000（≈13,000 汉字，够写完上半篇；不是砍到 4000 那种断句档）");
ok(retryFn("paper", 16000) === 8000, "paper 重跑同档");
ok(retryFn("iq", 12000) === 6000, "iq 重跑 6000（评分卡装得下，又确实降了档）");
ok(retryFn("answer", 4000) === 4000, "普通问答重跑仍是 4000");
ok(/max_tokens: _retryTok,/.test(W), "重跑真的用了 _retryTok，不是又写死一个数");
ok(/wdsPlainBody\(VC, \{\s*\n\s*model: VC\.model, stream: true, max_tokens: _retryTok/.test(W),
   "重跑这一遍是关思考的（wdsPlainBody）——这一遍的意义就是逼它停下推演开始写");

/* ===== 五、保险还在 ===== */
console.log("— 五、零正文兜底 —");
ok(/if \(r\.out === 0\) \{/.test(W), "零正文兜底还在（加预算只是少踩一次，不是取消保险）");
ok(/把额度全烧在思考上了/.test(W), "兜底文案说得出根因：思考多少字、正文 0 字");
ok(/基底没交出正文（第一遍/.test(W), "两遍都空时给明确 error 帧，不装作没事");

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
