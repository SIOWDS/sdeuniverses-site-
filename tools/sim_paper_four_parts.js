/* 只测一件事：站内搜索页「成文一篇／打磨修改」的**四段流水**（public/search/index.html · runFourParts）。

   2026-08-10 由两段改四段（两万字·投稿体例）。分段这件事有三种静默死法，每一种都不会报错：
   ① 某一段没写出来，后面几段照跑——但它们要接前一段的结尾，接到空气上就会重写题目、重排章号；
   ② 某一段没写出来，全文照样打「✓ 全文完成」，PDF 里缺参考文献与投稿声明，拿去投稿当场退；
   ③ 段收尾标记（〔第一段完·待续〕…）没被剥干净，原样印进 PDF 正文。
   下面每一条都对着其中一种。本脚本把 paperHalf 与 runFourParts 从页面里抠出来真跑。 */
"use strict";
const fs = require("fs");
const SRC = "/home/claude/site/public/search/index.html";
const h = fs.readFileSync(SRC, "utf8");

let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };

/* ===== 抠出 paperHalf + 四段流水，打桩真跑 ===== */
const a = h.indexOf("function paperHalf(");
const b = h.indexOf("function doPaper(");
if (a < 0 || b <= a) { console.log("FAIL 抠不出 paperHalf/runFourParts（锚点变了，先改本脚本）"); process.exit(1); }
const seg = h.slice(a, b);

let calls = [], plan = [];
function makeRunner() {
  calls = [];
  const stub = { getElementById: () => ({ set textContent(v) { }, classList: { add() { }, remove() { } }, style: {} }) };
  const streamPaper = function (part) {
    const step = plan[calls.length] || { text: "" };
    calls.push(part);
    return step.err ? Promise.reject(new Error(step.err)) : Promise.resolve(step.text);
  };
  const fn = new Function("document", "streamPaper", "GEN_STAT", "setProg",
    seg + "\nreturn { runFourParts: runFourParts, missText: missText, paperHalf: paperHalf, PAPER_PARTS: PAPER_PARTS, partHead: partHead };");
  return fn(stub, streamPaper, "paperStat", function () { });
}
const seedFor = (i, head, tail) => ({ i: i, head: head, tail: tail });
const stat = { set textContent(v) { } };
const LONG = (n) => "字".repeat(n);
/* 每个场景开跑前必须重置：plan 按 calls.length 取步，不清零会串场 */
const reset = (p) => { plan = p; calls = []; };

(async () => {
  const R = makeRunner();

  console.log("— 一、四段规格 —");
  ok(R.PAPER_PARTS.length === 4, "整整四段 · 实得 " + R.PAPER_PARTS.length);
  ok(R.PAPER_PARTS.every((p) => p.min > 0 && p.name && p.desc), "每段都有最短长度、段名与职能说明");
  ok(new Set(R.PAPER_PARTS.map((p) => p.desc)).size === 4, "四段职能互不重复（重复＝会写出四段同样的东西）");
  ok(/参考文献/.test(R.PAPER_PARTS[3].desc) && /投稿声明/.test(R.PAPER_PARTS[3].desc),
    "末段职能里点名参考文献与投稿声明（投稿体例的收尾件）");

  console.log("— 二、顺利跑完四段 —");
  reset([{ text: LONG(5000) + "\n【一、引言】起" }, { text: LONG(5000) }, { text: LONG(5000) }, { text: LONG(5000) }]);
  let r = await R.runFourParts(seedFor, stat, "写作中");
  ok(calls.join(",") === "1,2,3,4", "四段依次发出 part=1,2,3,4 · 实得 " + calls.join(","));
  ok(r.done === 4, "done=4");
  ok(r.text.length > 19000, "全文约两万字 · 实得 " + r.text.length);
  ok(R.missText(r.done) === false, "四段齐全时不打未完成稿标记");

  console.log("— 三、中途某段写不出来（最要命的一种）—");
  reset([{ text: LONG(5000) }, { text: LONG(5000) }, { text: "" }, { text: "" }, { text: LONG(5000) }]);
  r = await R.runFourParts(seedFor, stat, "写作中");
  ok(calls.join(",") === "1,2,3,3", "第三段重试一次后就地停住，绝不硬跑第四段 · 实得 " + calls.join(","));
  ok(r.done === 2, "done=2（只认真正写成的段）");
  ok(r.text.length > 9000, "已写的两段一个字都不丢 · 实得 " + r.text.length);
  const miss = R.missText(r.done);
  ok(typeof miss === "string" && /第三段/.test(miss) && /第四段/.test(miss), "缺段说明点名缺的是第三、第四段");
  ok(/参考文献/.test(miss), "缺段说明里能看出参考文献没写（读者据此不按完稿评阅）");

  console.log("— 四、第一段彻底失败 —");
  reset([{ err: "网络抖动" }, { err: "网络抖动" }]);
  let threw = null;
  try { await R.runFourParts(seedFor, stat, "写作中"); } catch (e) { threw = e; }
  ok(!!threw, "第一段两次都失败 → 抛给调用方（没有稿子就不该往下跑）");
  ok(calls.length === 2, "重试封顶两次，不烧配额 · 实得 " + calls.length);

  console.log("— 五、末段失败：前三段必须保住 —");
  reset([{ text: LONG(5000) }, { text: LONG(5000) }, { text: LONG(5000) }, { err: "超时" }, { err: "超时" }]);
  r = await R.runFourParts(seedFor, stat, "写作中");
  ok(r.done === 3 && r.text.length > 14000, "末段挂掉不丢前三段 · done=" + r.done + " 字数=" + r.text.length);

  console.log("— 六、段收尾标记必须剥干净（漏一个就原样印进 PDF）—");
  for (const mk of ["〔第一段完·待续〕", "〔第二段完·待续〕", "〔第三段完·待续〕", "〔全文完〕", "〔上半篇完·待续〕"]) {
    reset([{ text: LONG(2000) + "\n" + mk + "\n" }]);
    const one = await R.paperHalf(1, {}, 600, "第一段");
    ok(one.indexOf(mk.slice(1, 4)) < 0 && one.length === 2000, "剥掉 " + mk);
  }

  console.log("— 七、续写起点：后段拿得到前段的题名与结尾 —");
  /* 用真实的投稿体例开头：题名+英文题名+中英摘要与关键词，正常有六七百字，
     远超 partHead 里那道 80 字的护栏（护栏是防「引言标记出现得太早＝没有摘要」时切出个空 head）。 */
  const FRONT = "论文题名\nTitle: A Study\n【摘要】" + LONG(400) + "\n【关键词】甲；乙\n【Abstract】" + LONG(200) + "\n【Keywords】a; b\n";
  reset([{ text: FRONT + "【一、引言】" + LONG(5000) }, { text: LONG(5000) }, { text: LONG(5000) }, { text: LONG(5000) }]);
  const seen = [];
  await R.runFourParts((i, head, tail) => { seen.push({ i: i, head: head, tail: tail }); return {}; }, stat, "写作中");
  ok(seen[0].head === "", "第一段不带 head（它自己就是题名的来源）");
  ok(seen[1].head.indexOf("论文题名") === 0 && seen[1].head.indexOf("【一、") < 0,
    "第二段拿到的 head 是题名到引言之前那一段（不是整篇）");
  ok(/【摘要】/.test(seen[1].head) && /【Abstract】/.test(seen[1].head),
    "head 里带着中英摘要——后三段据此不重写题名与摘要");
  ok(seen[3].tail && seen[3].tail.length === 1000, "末段拿到的续写起点是已写全文的最后 1000 字");

  console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
  process.exit(F ? 1 : 0);
})();
