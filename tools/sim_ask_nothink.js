/* 只测一件事：/api/ask 这条**流式主路**上，哪些模式必须显式关思考、兜底重跑给多少额度。

   为什么要有这个护栏：站内早有一条纪律「短额度的结构化调用必须显式关思考」，
   但它只写在 llmText 里，而这条流式主路自己拼 body，**绕过了那条纪律**——
   于是同一个坑在 2026-08-09 被线上真跑第二次抓到，症状与第一次一模一样：
     · mode=iq    ：思考 12,526 字 / 正文 0 字（评分卡是必须完整的 JSON，截断即整张卡作废）
     · mode=polish：思考 10,906 字 / 正文 0 字（交出正文的从来是那次关思考的重跑）
   这类故障在页面上看不出根因——用户只看到「0 字，重试一次后仍未成功」。
   所以判据要钉在**代码形态**上，而不是等下一次真跑再发现。 */
"use strict";
const fs = require("fs");
const W = fs.readFileSync("/home/claude/site/src/worker.js", "utf8");

let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };

/* ===== 一、关思考名单 ===== */
console.log("— 一、哪些模式第一遍就关思考 —");
const mNo = W.match(/const _noThink = \(([^)]*)\);/);
ok(!!mNo, "_noThink 判据在位");
const noExpr = mNo ? mNo[1] : "";
ok(/mode === "iq"/.test(noExpr), "iq 关思考（评分卡是一个必须完整的 JSON）");
ok(/mode === "polish"/.test(noExpr), "polish 关思考（实测第一遍 100% 被思考吃光）");
/* 真跑：把判据抠出来，四个模式各喂一次 */
const isNo = new Function("mode", "return (" + noExpr + ");");
ok(isNo("iq") === true && isNo("polish") === true, "真跑：iq / polish 判 true");
ok(isNo("paper") === false && isNo("answer") === false && isNo("distill") === false,
   "真跑：paper / answer / distill 仍留着思考（那是它们写得好的原因，且实测出得来正文）");

/* ===== 二、关思考必须真的接到主调用上 ===== */
console.log("— 二、接线 —");
ok(/body: JSON\.stringify\(_noThink \? wdsPlainBody\(VC, _mainBody\) : _mainBody\)/.test(W),
   "主调用按 _noThink 走 wdsPlainBody（判据算对了却没接上 body，等于没改）");
const iMain = W.indexOf("const _mainBody = {");
const iFetch = W.indexOf("upstream = await fetch(VC.url", iMain);
ok(iMain > 0 && iFetch > iMain, "_mainBody 定义排在主调用之前");
ok(/function wdsPlainBody\(VC, body\) \{[\s\S]{0,400}?thinking = \{ type: "disabled" \}/.test(W),
   "wdsPlainBody 确实在关思考（deepseek/智谱走 thinking:disabled）");

/* ===== 三、兜底重跑的额度：长文不许砍 ===== */
console.log("— 三、兜底重跑额度 —");
const mR = W.match(/const _retryTok = \(([^;]*);/);
ok(!!mR, "_retryTok 在位");
const retryFn = new Function("mode", "MAXTOK", "const _retryTok = (" + mR[1] + "; return _retryTok;");
ok(retryFn("polish", 6800) === 6800, "polish 重跑给满额度 6800（砍到 4000 必然断在半句上——线上抓到过原样）");
ok(retryFn("paper", 6800) === 6800, "paper 重跑给满额度");
ok(retryFn("iq", 4200) === 4000, "iq 重跑仍降档到 4000（短输出降档是对的）");
ok(retryFn("answer", 4000) === 4000 && retryFn("distill", 5200) === 4000, "其余模式照旧 4000 封顶");
ok(/max_tokens: _retryTok,/.test(W), "重跑真的用了 _retryTok，不是又写死一个 4000");

/* ===== 四、各模式额度 ===== */
console.log("— 四、额度 —");
const grab = (re) => { const m = W.match(re); return m ? Number(m[1]) : -1; };
const iqTok = grab(/if \(mode === "iq"\) \{[\s\S]{0,400}?MAXTOK = (\d+);/);
ok(iqTok >= 4000, "iq 额度 " + iqTok + " ≥ 4000（评分卡带三张清单：最近邻／扣分／提升）");
const polishTok = grab(/mode === "paper" \|\| mode === "polish"\) \{\s*\n\s*MAXTOK = (\d+);/);
ok(polishTok >= 6000, "paper/polish 额度 " + polishTok + " ≥ 6000（上下半篇各要五六千字）");

/* ===== 五、零正文兜底仍在（关思考只是少踩一次坑，不是取消保险） ===== */
console.log("— 五、保险还在 —");
ok(/if \(r\.out === 0\) \{/.test(W), "零正文兜底还在");
ok(/把额度全烧在思考上了/.test(W), "兜底文案仍说得出根因（思考多少字、正文 0 字）");
ok(/基底没交出正文（第一遍/.test(W), "两遍都空时给明确 error 帧，不装作没事");

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
