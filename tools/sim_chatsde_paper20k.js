/* sim_chatsde_paper20k.js —— ChatSDE「成文一篇·论文档」两万字扩容的护栏
 *   ① 从 src/worker.js 里把 PAPER_SKELETON **真取出来跑**（new Function），不手抄形状、不写字面量
 *   ② plan 合并逻辑真跑：模型少给／多给／乱给 sections，合并后必须永远是骨架那几节
 *   ③ 从 public/wds-mode.js 里抠出 step()，配假 runLeg 真跑：短产出要回滚、要重试、要记账
 *   ④ /assets/wds-pdf.js 的无抬头块，与前端 PDF_WANT 必须与模块 VERSION 对齐
 * 跑法：node tools/sim_chatsde_paper20k.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");
let pass = 0, fail = 0;
const ok = (n, c) => { if (c) { pass++; console.log("  ✓ " + n); } else { fail++; console.log("  ✗ " + n); } };

const WSRC = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");
const FSRC = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");

/* ═══ 一、骨架表：从源码里真取出来，不抄 ═══ */
console.log("── PAPER_SKELETON（从 worker.js 真取）──");
const mSkel = WSRC.match(/const PAPER_SKELETON = (\[[\s\S]*?\n      \]);\n/);
ok("worker.js 里抠得到 PAPER_SKELETON", !!mSkel);
const SKEL = mSkel ? new Function("return " + mSkel[1] + ";")() : [];
const total = SKEL.reduce((a, s) => a + s.words, 0);
console.log("     节数 " + SKEL.length + " · 合计 " + total + " 字");
ok("节数在 12–16 之间（两万字靠加节数，不靠加长单节）", SKEL.length >= 12 && SKEL.length <= 16);
ok("合计字数落在 19000–22000（目标两万）", total >= 19000 && total <= 22000);
ok("每节都有 h 与 ask", SKEL.every((s) => s.h && s.ask && s.ask.length > 40));
ok("单节字数一律 ≤1900（超过安全区必被时长墙掐在思考阶段）", SKEL.every((s) => s.words <= 1900));
ok("单节字数一律 ≥800（太碎会让接缝多于正文）", SKEL.every((s) => s.words >= 800));
ok("小标题互不重复", new Set(SKEL.map((s) => s.h)).size === SKEL.length);

/* 投稿体例的必交件：缺一件就不是一篇能投出去的论文——这正是上一版真跑翻车的地方 */
const allAsk = SKEL.map((s) => s.h + "｜" + s.ask).join("\n");
[["摘要", "摘要"], ["关键词", "关键词"], ["英文摘要", "Abstract"], ["英文关键词", "Keywords"],
 ["引言", "引言"], ["文献述评", "文献述评"], ["证伪", "证伪"], ["参考文献", "参考文献"],
 ["附录", "附录"], ["投稿声明", "投稿声明"], ["结论", "结论"], ["研究局限", "局限"]]
  .forEach(([n, k]) => ok("体例必交件在骨架里：" + n, allAsk.indexOf(k) >= 0));
ok("禁编造那一条写进了骨架（参考文献节）", /绝不编造页码与引文/.test(allAsk));
ok("不含情态词那一条写进了判据节", /禁用：应当／有意义／实质性／充分／真正／恰当／合理/.test(allAsk));
ok("当场检验那一条写进了证伪节", /当场交出你这次执行的结果/.test(allAsk));

/* ═══ 二、paper 档挂上骨架 ═══ */
console.log("── paper 档 ──");
const mPaper = WSRC.match(/paper: \{ name: "([^"]+)", tok: WDS_TOK_MAX, parts: ([^,]+),\n\s*fixed: (\w+), spec:/);
ok("paper 表头形状对（name/parts/fixed 三样齐）", !!mPaper);
ok("档名已改成两万字", !!mPaper && /两万字/.test(mPaper[1]));
ok("parts 由骨架推导，不是手写的数字", !!mPaper && mPaper[2].trim() === "PAPER_SKELETON.length");
ok("fixed 指向 PAPER_SKELETON", !!mPaper && mPaper[3] === "PAPER_SKELETON");
ok("旧的「一万字论文」口径已经不在了", WSRC.indexOf('name: "一万字论文"') < 0);

/* ═══ 三、plan 合并：模型怎么乱给，体例都必须齐 ═══ */
console.log("── plan 合并逻辑（真跑）──");
const mMerge = WSRC.match(/(if \(FIXED\) \{\n[\s\S]*?\n                \}\) \)?;?\n?)                controller\.enqueue\(_sseBytes\(\{ t: "plan"/);
const mergeSrc = WSRC.slice(WSRC.indexOf("                if (FIXED) {"), WSRC.indexOf('                controller.enqueue(_sseBytes({ t: "plan"'));
ok("抠得到合并那一段", mergeSrc.length > 200 && mergeSrc.indexOf("FIXED.map") > 0);
const merge = new Function("FIXED", "plan", mergeSrc + "\n return plan;");
[["模型只给 3 条", [{ h: "甲" }, { h: "乙" }, { h: "丙" }]],
 ["模型给 40 条", Array.from({ length: 40 }, (_, i) => ({ h: "第" + i }))],
 ["模型一条不给", []],
 ["sections 根本不是数组", null],
 ["h 全是空串", SKEL.map(() => ({ h: "   " }))],
 ["还夹带了自己的 words/ask", SKEL.map(() => ({ h: "x", words: 9999, ask: "乱写" }))]]
  .forEach(([name, secs]) => {
    const out = merge(SKEL, { title: "T", sections: secs });
    const good = out.sections.length === SKEL.length
      && out.sections.every((s, i) => s.ask === SKEL[i].ask && s.words === SKEL[i].words && !!s.h);
    ok(name + " → 仍是 " + SKEL.length + " 节、ask/words 一律取表里的", good);
  });
const filled = merge(SKEL, { sections: [{ h: "一、这一场从哪儿起" }] });
ok("模型给了的小标题被采用（第 1 节）", filled.sections[0].h === "一、这一场从哪儿起");
ok("模型没给的退回表里的默认标题（第 2 节）", filled.sections[1].h === SKEL[1].h);

/* ═══ 四、前端 step()：短产出必须回滚重试 ═══ */
console.log("── step() 短产出重试（真跑）──");
/* step() 在 wds-mode.js 里不止一处（附件解析那边也有一个同名的），
   所以起点先锚 shortSecs、终点再从起点往后找——不这么做会切到另一个 step 上去。 */
const _s0 = FSRC.indexOf("      var shortSecs = [];");
const _s1 = FSRC.indexOf("      step();", _s0);
const stepSrc = (_s0 > 0 && _s1 > _s0) ? FSRC.slice(_s0, _s1) : "";
ok("抠得到 step()", stepSrc.indexOf("function step()") > 0 && stepSrc.indexOf("text.slice(0, before)") > 0);

/* runLeg 在真实实现里是**边流边往 text 上加**的，所以假 runLeg 也必须真的加——
   否则「回滚」这条恰恰测不到（回滚的正是那半截已经落进 text 的残稿）。
   壳里注入 __hook.append，让假 runLeg 能碰到闭包里的 text。 */
function harness2(secs, outs) {
  const box = { notes: [], attempt: {}, done: false, appended: [] };
  const src =
    "var text='', i=0, dStopped=false, __short=null;\n" +
    stepSrc.replace("var shortSecs = [];", "var shortSecs = []; __short = function(){ return shortSecs; };") +
    "\n __hook.append = function(s){ text += s; };" +
    "\n __hook.text = function(){ return text; };" +
    "\n __hook.short = function(){ return __short(); };" +
    "\n step();";
  const hook = {};
  new Function("secs", "plan", "t", "dNote", "paintD", "saveProgress", "traceSave",
    "pTrace", "stat", "runLeg", "done", "__hook", src)(
    secs, { sections: secs },
    (k) => "[" + k + "]",
    (v) => box.notes.push(String(v)),
    () => {}, () => {}, () => {},
    {}, { textContent: "" },
    (o) => {
      const k = o.idx;
      box.attempt[k] = (box.attempt[k] || 0) + 1;
      const arr = outs[k] || [];
      const n = (box.attempt[k] - 1 < arr.length) ? arr[box.attempt[k] - 1] : (secs[k].words || 0);
      hook.append("<" + (k + 1) + ":" + box.attempt[k] + ">" + "x".repeat(Math.max(0, n - 8)));
      box.appended.push((k + 1) + ":" + box.attempt[k] + ":" + n);
      return Promise.resolve({ out: n, plan: null, err: "" });
    },
    () => { box.done = true; }, hook);
  return { hook, box };
}

const SECS3 = [{ h: "一", ask: "a", words: 1000 }, { h: "二", ask: "b", words: 1000 }, { h: "三", ask: "c", words: 1000 }];
function waitDone(box, cb) {
  const t0 = Date.now();
  (function w() {
    if (box.done || Date.now() - t0 > 8000) return cb();
    setTimeout(w, 10);
  })();
}

const A = harness2(SECS3, { 0: [1000], 1: [90, 950], 2: [1000] });   // 第 2 节第一遍只吐 90 字
waitDone(A.box, function () {
  const txt = A.hook.text();
  ok("短产出触发了重试（第 2 节跑了两遍）", A.box.appended.filter((s) => s.startsWith("2:")).length === 2);
  ok("重试前把残稿回滚了（<2:1> 不在成稿里）", txt.indexOf("<2:1>") < 0);
  ok("第二遍的正文留下了（<2:2> 在成稿里）", txt.indexOf("<2:2>") > 0);
  ok("前后两节不受影响", txt.indexOf("<1:1>") >= 0 && txt.indexOf("<3:1>") > 0);
  ok("重试一次就够，没有第三遍", A.box.appended.filter((s) => s.startsWith("2:")).length === 2);

  const B = harness2(SECS3, { 0: [1000], 1: [80, 70], 2: [1000] });  // 两遍都短
  waitDone(B.box, function () {
    ok("两遍都短：记进了 shortSecs 并报了账", B.hook.short().length === 1 && B.box.notes.join("|").indexOf("dShort1") >= 0);
    ok("两遍都短仍继续往下写（第 3 节照跑）", B.hook.text().indexOf("<3:") > 0);

    const C = harness2(SECS3, { 1: [0, 0] });                         // 两遍都空
    waitDone(C.box, function () {
      ok("两遍都空：残稿被清干净，且报了 dPartLost", C.hook.text().indexOf("<2:") < 0 && C.box.notes.join("|").indexOf("dPartLost") >= 0);

      const D = harness2(SECS3, {});                                  // 全部达标
      waitDone(D.box, function () {
        ok("全部达标时一遍过、不记账、不报警", D.hook.short().length === 0 && D.box.appended.length === 3 && D.box.notes.length === 0);
        tail();
      });
    });
  });
});

function tail() {
  /* ═══ 五、门槛与限流留白：数值从源码取，不手抄 ═══ */
  console.log("── 阈值与节奏 ──");
  const mNeed = stepSrc.match(/var need = Math\.max\((\d+), Math\.round\(\(parseInt\(secs\[i\]\.words, 10\) \|\| \d+\) \* ([\d.]+)\)\);/);
  ok("门槛写成「本节目标字数 × 比例」而不是一个死数", !!mNeed);
  ok("比例在 0.3–0.6 之间（太松等于没门槛，太紧会把正常段判成失败）", !!mNeed && +mNeed[2] >= 0.3 && +mNeed[2] <= 0.6);
  const mGap = stepSrc.match(/setTimeout\(step, (\d+)\)/);
  ok("节间留白 ≥300ms（十五趟连打最容易在后几趟撞限流）", !!mGap && +mGap[1] >= 300);
  ok("回滚只回滚本节（用的是 before 这个游标）", /text = text\.slice\(0, before\)/.test(stepSrc));
  ok("重试用的是同一份 prevTail（不是回滚后的新尾巴）", /prevTail: tail0/.test(stepSrc) && (stepSrc.match(/prevTail: tail0/g) || []).length === 2);

  /* ═══ 六、PDF 出口 ═══ */
  console.log("── PDF 出口 ──");
  delete require.cache[require.resolve(path.join(ROOT, "public/assets/wds-pdf.js"))];
  const PDF = require(path.join(ROOT, "public/assets/wds-pdf.js"));
  const withLabel = PDF.doc({ title: "T", blocks: [{ html: "<p>正文</p>", aLabel: "WDS" }] });
  const noLabel = PDF.doc({ title: "T", blocks: [{ html: "<p>正文</p>", aLabel: "" }] });
  const omitted = PDF.doc({ title: "T", blocks: [{ html: "<p>正文</p>" }] });
  ok("aLabel 显式空串 → 不印抬头", noLabel.indexOf("class=who") < 0 && noLabel.indexOf("正文") > 0);
  ok("aLabel 有值 → 照旧印抬头", withLabel.indexOf(">WDS</div>") > 0);
  ok("不传 aLabel 的老调用方行为不变（仍印 WDS）", omitted.indexOf(">WDS</div>") > 0);

  const mWant = FSRC.match(/var PDF_WANT = (\d+);/);
  const mVer = fs.readFileSync(path.join(ROOT, "public/assets/wds-pdf.js"), "utf8").match(/var VERSION = (\d+);/);
  ok("PDF_WANT 与模块 VERSION 对齐（不对齐＝读者拿到缓存的旧版，新行为静默丢失）",
    !!mWant && !!mVer && +mWant[1] === +mVer[1]);

  const btn = FSRC.slice(FSRC.indexOf('var pdfB = el("button"'), FSRC.indexOf('subBtn = el("button", "wdsm-tbtn dsub"'));
  ok("成文面板挂上了 PDF 按钮", btn.length > 200);
  ok("PDF 按钮走 pdfBoot（按需装载，不假设模块已在）", btn.indexOf("pdfBoot(") > 0);
  ok("PDF 按钮传的是 aLabel 空串（论文稿不印发言人抬头）", /aLabel: ""/.test(btn));
  ok("排版抛错有纯文本兜底（白屏不是可接受形态）", btn.indexOf("catch") > 0 && btn.indexOf("<pre>") > 0);
  ok("Word 出口仍在", FSRC.indexOf("window.SDEDocx.build(") > 0);
  ok("论文档的文案已改成两万字", /kPaper: "凝成两万字论文"/.test(FSRC));
  ok("英文文案同步改了（中英双份纪律）", /Forge a 20,000-word paper/.test(FSRC));

  console.log("\n" + (fail ? "✗ " : "✓ ") + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}
