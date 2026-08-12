/* sim_chatsde_paper20k.js —— ChatSDE「成文一篇·论文档」两万字扩容的护栏
 *   ⓪ 解析 tools/skills/sde-academic-paper.md 第二节那张体例表，与 PAPER_SKELETON **逐条比对**——
 *      Skill 是唯一权威，机器是它的编译产物；两份一旦不一样，这条先红
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

/* ═══ 一之二、Skill 是唯一权威：体例表 ↔ 机器骨架必须逐条对上 ═══ */
console.log("── 规范层 ↔ 机器层 一致性 ──");
const SKILL_P = path.join(ROOT, "tools/skills/sde-academic-paper.md");
ok("《正规学术论文写作规范》在仓库里", fs.existsSync(SKILL_P));
const SKILL = fs.existsSync(SKILL_P) ? fs.readFileSync(SKILL_P, "utf8") : "";
/* 只解析第二节那张表，别把 §五 红线表、§八 分工表也扫进来 */
const tblSrc = SKILL.slice(SKILL.indexOf("## 二 · 体例"), SKILL.indexOf("## 三 · 逐节的形状要求"));
const ROWS = [];
tblSrc.split("\n").forEach((ln) => {
  const m = ln.match(/^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|/);
  if (m) ROWS.push({ n: +m[1], h: m[2], words: +m[3] });
});
ok("解析得到体例表（" + ROWS.length + " 行）", ROWS.length >= 12);
ok("表里的序号连续，没漏行", ROWS.every((r, i) => r.n === i + 1));
ok("Skill 的节数 == 机器的节数（" + ROWS.length + " vs " + SKEL.length + "）", ROWS.length === SKEL.length);
ok("逐节章目一字不差", ROWS.every((r, i) => SKEL[i] && SKEL[i].h === r.h));
ok("逐节字数一一相等", ROWS.every((r, i) => SKEL[i] && SKEL[i].words === r.words));
const skillTotal = ROWS.reduce((a, r) => a + r.words, 0);
ok("Skill 自报的合计字数与逐行相加对得上", new RegExp("合计 \\*\\*" + skillTotal.toLocaleString("en-US") + " 字\\*\\*").test(tblSrc)
  || tblSrc.indexOf(String(skillTotal)) > 0);
ok("机器合计 == Skill 合计", skillTotal === total);
ok("worker.js 里写明了权威出处（改 Skill 必须同步改机器）",
  WSRC.indexOf("tools/skills/sde-academic-paper.md") > 0);

/* 投稿体例的必交件：缺一件就不是一篇能投出去的论文——这正是上一版真跑翻车的地方 */
const allAsk = SKEL.map((s) => s.h + "｜" + s.ask).join("\n");
[["结构化摘要", "结构化摘要"], ["关键词", "关键词"], ["英文摘要", "Abstract"], ["英文关键词", "Keywords"],
 ["研究问题 RQ", "RQ1"], ["贡献声明", "贡献声明"], ["文献述评", "述评是"], ["名义定义", "名义定义"],
 ["操作性定义", "操作性定义"], ["测量层次", "测量层次"], ["取样标准", "纳入与排除"], ["分析程序可复现", "能复现"],
 ["信度与研究者立场", "研究者自身立场"], ["研究伦理", "不涉及人类被试"], ["证伪条款", "证伪条款"],
 ["当场检验", "当场交出你这次执行的结果"], ["效度四类", "构念效度"], ["研究局限", "局限"],
 ["作者贡献 CRediT", "CRediT"], ["利益冲突", "利益冲突"], ["数据可得性", "数据与材料可得性"],
 ["AI 使用声明", "AI 使用声明"], ["参考文献 APA", "APA"], ["附录", "附录"], ["结论对上 RQ", "回答引言里那几条 RQ"]]
  .forEach(([n, k]) => ok("体例必交件在骨架里：" + n, allAsk.indexOf(k) >= 0));
ok("禁编造那一条写进了骨架（参考文献节）", /绝不编造页码与引文/.test(allAsk));
ok("不含情态词那一条写进了判据节", /禁用：应当／有意义／实质性／充分／真正／恰当／合理/.test(allAsk));
ok("分析与讨论分家写进了骨架（两侧各一条）",
  /分析节只出结果、不出意义解读/.test(allAsk) && /讨论节只解读、不出新证据/.test(allAsk));
ok("不可判定的比较句被禁在骨架里", /更强调／更深入／更系统/.test(allAsk));
ok("「随着……的发展」这类开头被明令禁止", /随着……的发展/.test(allAsk));

/* ═══ 二、paper 档挂上骨架 ═══ */
console.log("── paper 档 ──");
const mPaper = WSRC.match(/paper: \{ name: "([^"]+)", tok: WDS_TOK_MAX, parts: ([^,]+),\n\s*fixed: (\w+), spec:/);
ok("paper 表头形状对（name/parts/fixed 三样齐）", !!mPaper);
ok("档名标明了投稿体例与字数口径", !!mPaper && /两万字/.test(mPaper[1]) && /体例/.test(mPaper[1]));
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

  console.log("── part 阶段的学术规程 ──");
  const rules = WSRC.slice(WSRC.indexOf("【正规学术论文写作规程"), WSRC.indexOf("【正规学术论文写作规程") + 4000);
  [["引注三验", "引注三验"], ["作者—年份制", "「作者 年份」制"], ["禁脚注编号", "不得出现脚注编号"],
   ["诚信红线", "越线即撤稿级"], ["禁编造", "绝不编造"], ["禁伪装引号", "伪装成原文"],
   ["转引自", "转引自"], ["不利结果也要报", "不利的那一次也要报"],
   ["禁不可判定比较句", "更强调／更深入／更系统"], ["禁对话痕迹", "读者没参与过任何对话"],
   ["分析与讨论分家", "分析节只出结果不出意义解读"], ["禁画表格", "不画表格"],
   ["章节两级真标题", "真标题行"], ["写完比写长要紧", "写完比写长要紧"]]
    .forEach(([n, k]) => ok("规程里有：" + n, rules.indexOf(k) >= 0));
  ok("规程只挂在骨架档上（PFIX 为真才发）", /\+ \(PFIX \? \("\\n\\n【正规学术论文写作规程/.test(WSRC));
  ok("论文档的文案已改成两万字", /kPaper: "凝成两万字论文"/.test(FSRC));
  ok("英文文案同步改了（中英双份纪律）", /Forge a 20,000-word paper/.test(FSRC));

  console.log("\n" + (fail ? "✗ " : "✓ ") + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
}
