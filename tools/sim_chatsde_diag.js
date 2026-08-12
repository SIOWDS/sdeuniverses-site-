/* sim_chatsde_diag.js —— 「断稿必须自报，且不许写成完成」
 * 真跑读数：状态栏「完成 · 54」——54 个字断在半句上，却一句诊断都没有。
 * 病根：服务端那套自报（finish_reason / 用量 / 思考字数）只在 `!wrote` 时才发；
 *       wrote=54 走不进去，前端于是照字面写「完成」。
 * 跑法：node tools/sim_chatsde_diag.js
 */
"use strict";
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, "..");
let pass = 0, fail = 0;
const ok = (n, c) => { if (c) { pass++; console.log("  ✓ " + n); } else { fail++; console.log("  ✗ " + n); } };
const W = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");
const F = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");

console.log("── 服务端：短产出也要有仪表 ──");
const blk = W.slice(W.indexOf("const SHORT_OUT ="), W.indexOf("const SHORT_OUT =") + 1500);
ok("短产出这一支存在", blk.length > 400);
const thr = +((blk.match(/const SHORT_OUT = (\d+);/) || [])[1] || 0);
ok("门槛从源码取（" + thr + "），不是这里手抄的", thr > 0);
ok("只在写了、但写得不够时才发（零字仍走原来那条空产出兜底）", /if \(wrote && wrote < SHORT_OUT\)/.test(blk));
[["实际写了多少字", "只写出 \" + wrote + \" 字"], ["要了多少预算", "tokWant"], ["本档上限", "SPEC.tok"],
 ["思考了多少字", "_st.think"], ["入参多长", "convo.length"],
 ["★ 上游的收束理由", "上游给的收束理由"], ["没给理由时也要说清是被掐断", "多半是流被掐断"],
 ["上游自报用量", "prompt_tokens"], ["其中思考多少 tok", "reasoning_tokens"]]
  .forEach(([n, k]) => ok("诊断里报了：" + n, blk.indexOf(k) >= 0));
ok("短产出不在服务端重来（重来要放在能回滚残字的客户端那一侧）",
  blk.indexOf("重来一次") < 0 && blk.indexOf("wdsClock") < 0);
ok("零产出那条原有的兜底与重试没被动掉", /if \(!wrote\) \{/.test(W) && W.indexOf("关思考重写") > 0);

console.log("── 前端：断稿不许写成完成 ──");
/* 切到那条 stat.textContent 赋值**结束**为止——按 900 字符硬切会切在语句中间，
   new Function 拿到的是半句，报的是 SyntaxError 而不是真读数。 */
const _q0 = F.indexOf("      var _want = 0;");
const _q1 = F.indexOf("(t(\"dDone\") + text.length));", _q0);
const done = (_q0 > 0 && _q1 > _q0) ? F.slice(_q0, _q1 + '(t("dDone") + text.length));'.length) : "";
ok("抠得到那段判定", done.indexOf("dPartial") > 0);
/* 真跑：把那几行拿出来跑一遍，别只查字符串 */
function label(len, secs) {
  const src = "var text='x'.repeat(" + len + "), dSecs=" + JSON.stringify(secs)
    + ", stat={}; function t(k){return k+':';}\n" + done + "\nreturn stat.textContent;";
  return new Function(src)();
}
ok("54 字 · 目标一万 → 判未写完（这正是真跑那一份）", /dPartial/.test(label(54, [{ words: 10000 }])));
ok("未写完时把分母也写出来（54/10000 一眼看得出差多少）", label(54, [{ words: 10000 }]).indexOf("/10000") > 0);
ok("写够六成 → 才算完成", /dDone/.test(label(6500, [{ words: 10000 }])));
ok("刚好卡在六成下方 → 仍算未写完", /dPartial/.test(label(5999, [{ words: 10000 }])));
ok("没有分节表时用下限兜底：54 字仍是未写完", /dPartial/.test(label(54, null)));
ok("没有分节表时：写够下限就算完成", /dDone/.test(label(3000, null)));
ok("一个字都没有 → 仍是失败，不是未写完", /dFail/.test(label(0, null)));
ok("dSecs 在提纲拿到分节时被赋上", /var secs = plan\.sections; dSecs = secs;/.test(F));
ok("dSecs 有声明（否则收尾那一行会抛 ReferenceError）", /var dSecs = null;/.test(F));

console.log("\n" + (fail ? "✗ " : "✓ ") + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
