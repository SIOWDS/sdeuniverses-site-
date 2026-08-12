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

/* ═══ 拆趟那一条路（part）也要有同一套仪表 ═══════════════════════════
   ⚠ 上面那一套长在**单趟**那条路上。而两万字论文全程走的是拆趟这一条：
   于是「第 7–16 节每节只吐几十字」追了整整一天，也判不出是预算被吃光（length）、
   上游自己收的口（stop）、还是流被掐断（空）——因为这条路一台仪表都没装。 */
console.log("── 服务端：拆趟那一条路的仪表 ──");
/* ⚠ 终点锚必须从起点**往后**找：`const stream = new ReadableStream({` 在文件里
   出现不止一次，且更早的那一处在 part 这一段之前——不带起点找会切出一个空串，
   下面二十条当场全红（这一版就是这么红过一次的）。 */
const _p0 = W.indexOf("let pfin = \"\", pusage = null;");
const pblk = W.slice(_p0, W.indexOf("const stream = new ReadableStream({", _p0));
ok("抠得到 part 那一段", pblk.length > 1500);
ok("★ 收 finish_reason（最值钱的那个字段）", /finish_reason\) pfin = j\.choices\[0\]\.finish_reason/.test(pblk));
ok("★ 收上游自报用量", /if \(j\.usage\) pusage = j\.usage;/.test(pblk));
ok("这一趟本来就开着 include_usage（不然接也接不到）", /withUsage/.test(W) && /include_usage/.test(W));
const pthr = +((pblk.match(/const PART_SHORT = (\d+);/) || [])[1] || 0);
ok("短产出门槛从源码取（" + pthr + "）", pthr > 0);
ok("★ 写了但不够也发诊断（不再只在零字时才发）", /if \(wrote && wrote < PART_SHORT\)/.test(pblk));
ok("零字那一支也带上同一份诊断", /if \(!wrote\) controller\.enqueue\(_sseBytes\(\{ t: "error", code: "empty"/.test(pblk) && /_diag/.test(pblk));
[["第几节", "partIdx + 1"], ["这一节的字数目标", "want"], ["思考了多少字", "_st.think"],
 ["上游收束理由", "pfin"], ["入 tok", "prompt_tokens"], ["出 tok", "completion_tokens"],
 ["其中思考多少 tok", "reasoning_tokens"], ["本地时钟掐没掐", "sclk.cut"]]
  .forEach(([n2, k]) => ok("诊断里说清了" + n2, pblk.indexOf(k) > 0));
ok("★ 每一趟都发一帧结构化 meta（前端据此把撞墙原因说出来）", /t: "meta", v: \{/.test(pblk));
[["idx", "idx:"], ["out", "out:"], ["fin", "fin:"], ["ptok", "ptok:"], ["ctok", "ctok:"], ["rtok", "rtok:"], ["cut", "cut:"]]
  .forEach(([n2, k]) => ok("meta 带着 " + n2, pblk.indexOf(k) > 0));
ok("前端接得住 meta", /j\.t === "meta"/.test(F) && /lastMeta = j\.v;/.test(F));
ok("不在服务端重来（重来要放在能回滚残字的客户端那一侧）", /不在服务端重来/.test(W));
ok("★ 越界的 idx 当场报错，不静默兜成一个无题空节", /code: "badidx"/.test(W));

console.log("── 前端：看门狗够得着还没返回响应的那一趟 ──");
ok("★ 每趟带 AbortController", /new AbortController\(\)/.test(F) && /signal: ac \? ac\.signal : undefined/.test(F));
ok("★ 看门狗掐的是 controller，不只是 reader", /if \(dAC\) dAC\.abort\(\)/.test(F));
ok("dTimedOut 每趟复位（一趟被掐不该污染此后每一节的死因）", /dTimedOut = false;\s+\/\/ 每趟各判各的死因/.test(F));
ok("整篇被掐过与否另记一位（收尾那句话仍说得出）", /dCutAny = true;/.test(F) && /if \(dCutAny\) dNote\(t\("dCut"\), 1\);/.test(F));

console.log("\n" + (fail ? "✗ " : "✓ ") + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
