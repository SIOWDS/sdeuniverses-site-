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

/* ===== 一、预算：首发走最高档，装不下由阶梯自己降 ===== */
console.log("— 一、预算与阶梯 —");
const grab = (re) => { const m = W.match(re); return m ? Number(m[1]) : -1; };
const iqTok = grab(/if \(mode === "iq"\) \{[\s\S]{0,400}?MAXTOK = (\d+);/);
const longTok = grab(/mode === "paper" \|\| mode === "polish"\) \{\s*\n\s*MAXTOK = (\d+);/);
/* 实测底数：思考 ≈8k tok（iq）／3–9k tok（polish），正文 2–3k（评分卡）／≈7k（一万字上半篇）。
   max_tokens 是上限不是目标：给到最高档不会让它多写，只是让思考与正文不必互相挤。 */
ok(iqTok >= 12000, "iq 的降档位 " + iqTok + " ≥ 12000（思考 ≈8k ＋ 评分卡 2–3k 要同吃一份）");
ok(longTok >= 16000, "paper/polish 的降档位 " + longTok + " ≥ 16000");
ok(/_heavy \? WDS_TOK_HEAVY : MAXTOK/.test(W), "三个重档首发给 WDS_TOK_HEAVY");
/* 【这条判据是用一次线上事故换来的，别顺手放宽】
   首发 64000 ＋ 满功率时，paper 上半篇在第 133 秒被平台杀掉：思考 17,233 字、正文 0 字，
   流里没有 [DONE]、没有 error、心跳停在第 120 秒——最难查的那种死法。
   预算的真正作用是**给思考封顶**，封顶才活得过那两分钟。所以首发必须有界。 */
/* 用户令「每一次调用都要 MaxToken」⇒ 预算给满，刹车改挂在推理投入档上。
   于是判据从"预算必须有界"改成"**必须有一处刹得住思考**"——两者必居其一，
   谁都没有的那一版就是 2026-08-09 第 133 秒断流的那一版。 */
ok(/const WDS_TOK_HEAVY = WDS_TOK_MAX;/.test(W) || (grab(/const WDS_TOK_HEAVY = (\d+);/) <= 20000),
   "重档预算：要么给满 MaxToken，要么有界——不许介于两者之间地随手写一个大数");
ok(/const _plainLong = _topPower;/.test(W) || (grab(/const WDS_TOK_HEAVY = (\d+);/) <= 20000),
   "给满预算时长文必须关思考——预算是油门不是容器，投入档刹不住它（实测 high 与 max 的思考一样长）");
ok(/body\.reasoning_effort = \(VC && VC\.effort\) \? VC\.effort : "max";/.test(W),
   "推理投入档这个旋钮做在 wdsTopBody 里且默认仍是 max（不传 effort 的既有调用点行为不变）");
const mH = W.match(/const _heavy = \(([^)]*)\);/);
ok(!!mH, "_heavy 判据在位");
const isHeavy = new Function("mode", "deep",
  "const _topPower = (mode === \"paper\" || mode === \"polish\"); const _deepAns = (mode === \"answer\" && deep); return (" + (mH ? mH[1] : "false") + ");");
ok(isHeavy("paper") && isHeavy("polish") && isHeavy("iq") && isHeavy("distill"), "真跑：成文／打磨／盲评／提炼四档都算重档");
/* 【这条是用户那场真实的自动十轮换来的，别放宽】
   深度档问答的思考与正文共用一份预算，4000 那一版会走出一条必然的下坡：
   第 1–4 轮 3405／3673／3135／2838 字 → 第 5 轮 936 字 → 第 6 轮 0 字，整场自动十轮就断在这儿。 */
ok(isHeavy("answer", true), "真跑：**深度档问答**也算重档（十轮问对全都走这条路）");
ok(!isHeavy("answer", false) && !isHeavy("nextq") && !isHeavy("collide"), "真跑：普通档问答与其余模式不进重档（各自原有的那一个数不变）");
ok(/if \(_deepAns\) MAXTOK = 8000;/.test(W), "深度档问答自带预算 8000（4000 会把正文挤没；12000 实测思考 38,777 字、第 128 秒被平台杀掉）");
/* 阶梯：真跑一遍，确认 iq 首发最高档、普通模式仍是单一档（＝行为不变） */
const mL = W.match(/const _ladder = _topPower \? \[([\s\S]{0,500}?)\);\n/);
ok(!!mL, "_ladder 在位");
const ladderFn = new Function("mode", "MAXTOK", "WDS_TOK_MAX", "WDS_TOK_HEAVY", "deep",
  "const _topPower = (mode === \"paper\" || mode === \"polish\"); const _deepAns = (mode === \"answer\" && deep); const _ladder = " + W.slice(W.indexOf("_topPower ? [", W.indexOf("const _ladder =")), W.indexOf(";", W.indexOf("a.indexOf(v) === i))"))) + "; return _ladder;");
ok(JSON.stringify(ladderFn("iq", 32000, 64000, 64000)) === "[64000,12000,8000]", "真跑：iq 阶梯首档给满 MaxToken");
ok(JSON.stringify(ladderFn("distill", 12000, 64000, 64000)) === "[64000,12000,8000]", "真跑：distill 走同一条阶梯（它也被实测抓到思考 8,977 / 正文 0）");
ok(JSON.stringify(ladderFn("paper", 32000, 64000, 64000)) === "[64000,32000,16000]", "真跑：长文阶梯 = 64000 → 32000 → 16000（首档给满）");
ok(JSON.stringify(ladderFn("answer", 4000, 64000, 64000, false)) === "[4000]", "真跑：**普通档**问答仍是单一档 4000——行为一个字都没变");
ok(JSON.stringify(ladderFn("answer", 8000, 64000, 64000, true)) === "[8000,6000,4000]", "真跑：深度档问答走 8000 → 6000 → 4000");
ok(JSON.stringify(ladderFn("collide", 5200, 64000, 64000)) === "[5200]", "真跑：碰撞仍是单一档 5200——行为一个字都没变");
ok(/if \(resp\.ok \|\| resp\.status !== 400 \|\| i === ladder\.length - 1\) return resp;/.test(W),
   "阶梯只在 400 且报 max_tokens 相关时才降档（别的错照原样抛回去）");
ok(/ladderOverride && ladderOverride\.length\) \? ladderOverride : wdsLadder\(VC, want\)/.test(W),
   "wdsFetchMax 的阶梯参数是加法式的：不传就与从前完全一样（既有七个调用点行为不变）");

/* ===== 二、满功率：只挂在长文上，绝不挂在结构化短输出上 ===== */
console.log("— 二、满功率的位置 —");
const mTop = W.match(/const _topPower = \(([^)]*)\);/);
ok(!!mTop, "_topPower 判据在位");
const isTop = new Function("mode", "return (" + (mTop ? mTop[1] : "false") + ");");
ok(isTop("paper") === true && isTop("polish") === true, "真跑：paper / polish 挂满功率");
ok(isTop("iq") === false, "真跑：iq **不挂**满功率——满功率对要求结构化短输出的调用是毒（本文件 4500 行的硬教训）");
ok(isTop("answer") === false && isTop("distill") === false && isTop("nextq") === false,
   "真跑：answer / distill / nextq 不挂满功率");
ok(/const _plainLong = _topPower;/.test(W) && /wdsFetchMax\(_VCX, KEY, _msgs, true[\s\S]{0,140}_plainLong\)/.test(W),
   "长文两档 ＝ 满预算 ＋ 关思考（实测：给满预算时交稿的本来就是关思考那一遍）");
ok(/plain \? wdsPlainBody\(VC, body\) : wdsTopBody\(VC, body\)/.test(W),
   "关思考这一路真的接到 wdsFetchMax 的 body 上；不传 plain 的既有调用点行为不变");
ok(/upstream = await wdsFetchMax\(_VCX, KEY, _msgs, true, _heavy \? WDS_TOK_HEAVY : MAXTOK,/.test(W),
   "主调用真的走了最高档取数器，并把 _VCX 递进去（算对了没接上，等于没改）");
ok(/function wdsTopBody\(VC, body\) \{[\s\S]{0,600}?thinking = \{ type: "enabled" \}/.test(W),
   "wdsTopBody 确实在开思考（thinking:enabled）");
ok(/body: JSON\.stringify\(plain \? wdsPlainBody\(VC, body\) : wdsTopBody\(VC, body\)\),/.test(W), "wdsFetchMax 内部：plain 优先，否则按 VC.top 决定挂不挂满功率");

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
ok(retryFn("polish", 32000) === 16000, "polish 重跑降一档到 16000（不是砍到 4000 那种断句档）");
ok(retryFn("paper", 32000) === 16000, "paper 重跑同档");
ok(retryFn("iq", 12000) === 6000, "iq 重跑 6000（评分卡装得下，又确实降了档）");
ok(retryFn("answer", 4000) === 4000, "普通问答重跑仍是 4000");
ok(/max_tokens: _retryTok,/.test(W), "重跑真的用了 _retryTok，不是又写死一个数");
ok(/wdsPlainBody\(VC, \{\s*\n\s*model: VC\.model, stream: true, max_tokens: _retryTok/.test(W),
   "重跑这一遍是关思考的（wdsPlainBody）——这一遍的意义就是逼它停下推演开始写");

/* ===== 四之二、时钟护栏：预算大了，卡死也要看得见 ===== */
console.log("— 四之二、时钟 —");
ok(/const _clk = _deepAns \? wdsClock\(\d+, (\d+)\) : \(_heavy \? wdsClock\((\d+), (\d+)\) : null\);/.test(W), "重档挂时钟（首帧闸＋总时长闸），深度档问答另有更早的一档");
const mD = W.match(/const _clk = _deepAns \? wdsClock\(\d+, (\d+)\)/);
/* 深度档问答的闸要早到"兜底还跑得完"：掐断后关思考重跑约二三十秒，仍要落在平台那约 128 秒的墙之内。 */
ok(mD && Number(mD[1]) <= 90000, "深度档问答闸 " + (mD ? mD[1] / 1000 : "?") + "s ≤ 90s：掐了还来得及关思考重跑一遍，答案照样交得出来");
const mC = W.match(/_heavy \? wdsClock\((\d+), (\d+)\) : null\);/);
/* 总时长闸必须**早于平台**：实测平台在约 133 秒无声杀掉整个请求（连 [DONE] 都没有）。
   闸设在它之后＝这台时钟形同虚设，用户仍然只会看到一个说不出理由的 0 字。 */
ok(mC && Number(mC[1]) >= 30000 && Number(mC[2]) >= 90000 && Number(mC[2]) <= 130000,
   "闸值 " + (mC ? (mC[1] / 1000 + "s / " + mC[2] / 1000 + "s") : "?") + "：首帧不太紧，总时长早于平台那约 133 秒的无声一刀");
ok(/if \(_clk\) _clk\.firstFrame\(\);/.test(W), "出流即撤首帧闸（后面还有真活要干）");
ok(/if \(_clk\) _clk\.stop\(\);/.test(W), "收尾停表，不留孤儿定时器");
ok(/\(_clk && _clk\.cut\) \? _clk\.why\(VC\.name\)/.test(W), "被时钟掐断时说清掐在哪一闸、多少秒——不与「流自己坏了」混为一谈");
/* 掐断时一个字都没写＝下面马上要关思考重跑，此刻抛红色 error 是骗人的：它还没失败，只是换了条路。 */
ok(/if \(r\.out > 0\) controller\.enqueue\(_sseBytes\(\{ t: "error", v: _cutMsg \}\)\);/.test(W),
   "掐断时**已经写了一半**才报 error（那才是真丢字）");
ok(/else controller\.enqueue\(_sseBytes\(\{ t: "status", v: "⏱ " \+ _cutMsg/.test(W),
   "掐断时一个字都没写 ⇒ 只发 status，不吓人；红色留给「两遍都空」那一句");
ok(/r = \{ out: _st\.out, think: _st\.think/.test(W),
   "掐断后用心跳里的活数据接着往下判（否则兜底会把「思考了一万字」误报成「一个字都没吐」）");

/* ===== 五、保险还在 ===== */
console.log("— 五、零正文兜底 —");
ok(/if \(r\.out === 0\) \{/.test(W), "零正文兜底还在（加预算只是少踩一次，不是取消保险）");
ok(/把额度全烧在思考上了/.test(W), "兜底文案说得出根因：思考多少字、正文 0 字");
ok(/基底没交出正文（第一遍/.test(W), "两遍都空时给明确 error 帧，不装作没事");

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
