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
ok("合计字数落在 25000–30000（v2.2 按实测放开到 27,500）", total >= 25000 && total <= 30000);
ok("每节都有 h 与 ask", SKEL.every((s) => s.h && s.ask && s.ask.length > 40));
ok("单节字数一律 ≤3000（v2.2 上调；仍不许再往上，加长单节必被时长墙掐在思考阶段）", SKEL.every((s) => s.words <= 3000));
ok("单节字数一律 ≥800（太碎会让接缝多于正文）", SKEL.every((s) => s.words >= 800));
ok("小标题互不重复", new Set(SKEL.map((s) => s.h)).size === SKEL.length);

/* ═══ 一之二、Skill 是唯一权威：体例表 ↔ 机器骨架必须逐条对上 ═══ */
console.log("── 规范层 ↔ 机器层 一致性 ──");
const SKILL_P = path.join(ROOT, "tools/skills/sde-academic-paper.md");
ok("《正规学术论文写作规范》在仓库里", fs.existsSync(SKILL_P));
const SKILL = fs.existsSync(SKILL_P) ? fs.readFileSync(SKILL_P, "utf8") : "";
/* 只解析第二节那张表，别把 §五 红线表、§八 分工表也扫进来 */
/* ⚠ 切片终点不写死章名——v2.0 在中间插了新的一章，写死就会把后面几章一并扫进来。
   改成「§二 之后的下一个 ## 标题」，此后再插章也不会失准。 */
const _tb0 = SKILL.indexOf("## 二 · 体例");
const _tb1 = SKILL.indexOf("\n## ", _tb0 + 8);
const tblSrc = SKILL.slice(_tb0, _tb1 > 0 ? _tb1 : SKILL.length);
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
 ["当场检验", "当场交出结果"], ["效度四类", "构念效度"], ["研究局限", "局限"],
 ["作者贡献 CRediT", "CRediT"], ["利益冲突", "利益冲突"], ["数据可得性", "数据与材料可得性"],
 ["AI 使用声明", "AI 使用声明"], ["参考文献 APA", "APA"], ["附录", "附录"], ["结论对上 RQ", "回答引言里那几条 RQ"]]
  .forEach(([n, k]) => ok("体例必交件在骨架里：" + n, allAsk.indexOf(k) >= 0));

/* ═══ 一之三、v2.0：创新智商五维的产出规程（Skill §三 ↔ 机器）═══
   v1.0 只管体例，两份真跑因此停在 123.3 与 126.2——失分几乎全在 I 与 F 两维。
   下面这一组保的是「体例齐≠有增量」那一层：产出件在不在、承重节排得够不够前、
   全局旗标有没有下发到每一节。少任何一条，稿子会退回 126 那个量级。 */
console.log("── v2.0 · 创新智商五维的产出规程 ──");
ok("Skill 里有 §三 创新智商五维的产出规程", /## 三 · 创新智商五维的产出规程/.test(SKILL));
[["I 占位盘点表", "占位盘点表"], ["I 四栏", "撤名条件"], ["I 反稻草人", "他本人会认这句话是他的主张吗"],
 ["I 外学科配额", "≥3 位来自本命题所属学科之外"], ["I 看似支持者配额", "看起来支持本文"],
 ["I 最强反对者", "最强反对者"], ["F 撤稿级条件", "撤稿级条件"], ["F 执行状态标注", "[已执行]"],
 ["F 读数自我否决", "自我否决条款"], ["F 单次事件如何取值", "单次事件如何取值"],
 ["E 改引擎", "改了它哪一个零件"], ["E 删段自检", "是否一字不改"],
 ["D 对手最强版本", "最强的那一版"], ["D 不利结果必须报", "不利结果"],
 ["S 四格给不出独有预测就删", "宁可两格"], ["S 一术语一所指", "一术语一所指"],
 ["全局旗标 EMPIRICAL", "EMPIRICAL"], ["全局旗标 ANCESTORS", "ANCESTORS"],
 ["禁写死节号", "禁止写死节号"]]
  .forEach(([n, k]) => ok("Skill §三 有：" + n, SKILL.indexOf(k) >= 0));

/* 承重节的位置：两次真跑都从第 7、8 节起被限流吃掉。
   判据一句——只写到第八节就断了，五维承重件也必须全部在手。 */
const posOf = (kw) => SKEL.findIndex((x) => x.h.indexOf(kw) >= 0) + 1;
const pThesis = posOf("核心命题"), pBound = posOf("占位划界"), pCrit = posOf("可裁决判据"), pFals = posOf("证伪条件");
console.log("     承重节位置：核心命题 " + pThesis + " · 划界 " + pBound + " · 判据 " + pCrit + " · 证伪 " + pFals);
ok("D 承重节（核心命题）排在第 5 节或更前", pThesis > 0 && pThesis <= 5);
ok("I 承重节（最近邻盘点与占位划界）排在第 6 节或更前", pBound > 0 && pBound <= 6);
ok("F 承重节（可裁决判据）排在第 7 节或更前", pCrit > 0 && pCrit <= 7);
ok("F 承重节（稳健性与证伪条件）排在第 8 节或更前", pFals > 0 && pFals <= 8);
ok("写到第八节就断，五维承重件也全部在手", Math.max(pThesis, pBound, pCrit, pFals) <= 8);
ok("核心命题排在划界之前（先立论再划界）", pThesis > 0 && pBound > 0 && pThesis < pBound);
ok("判据排在证伪之前（先给判据才谈怎么判它错）", pCrit > 0 && pFals > 0 && pCrit < pFals);

/* 骨架里那五条产出件的编译产物 */
[["占位盘点四栏", "撤名条件"], ["反稻草人自问", "他本人会认这句话是他的主张吗"],
 ["撤稿级条件形状", "则本文第 X 节须删除"], ["执行状态标注", "[已执行]"],
 ["读数四件齐", "在一次可观测事件里到底怎么取值"], ["读数三条自我否决", "改名嫌疑"],
 ["机制层辨异", "至少一条须切在机制层"], ["最强的那一版", "最强的那一版"],
 ["不利结果也要报", "如实写"], ["四格空格直接删", "宁可两格"]]
  .forEach(([n, k]) => ok("骨架里有：" + n, allAsk.indexOf(k) >= 0));

/* 全局旗标：plan 那一趟产出，part 每一趟都要收到 */
console.log("── v2.0 · 全局旗标的产出与下发 ──");
ok("plan 的 JSON 模板里要 empirical", /"empirical"/.test(WSRC));
ok("plan 的 JSON 模板里要 ancestors", /"ancestors"/.test(WSRC));
ok("empirical 缺省一律 no（宁可少说，不可编造）", /=== "yes"\) \? "yes" : "no"/.test(WSRC));
ok("ancestors 做了数组化与截断", /Array\.isArray\(plan\.ancestors\)/.test(WSRC));
ok("旗标下发到 part（不是只给声明组）", /全局旗标（全篇通用，本节必须遵守）/.test(WSRC));
ok("EMPIRICAL 为 no 时禁实施测叙述", /不得写「实验表明」/.test(WSRC));
ok("EMPIRICAL 为 no 时禁凭空给伦理批号", /绝不可凭空给出伦理批号/.test(WSRC));
ok("ANCESTORS 要求参考文献那一节认账", /一位不漏地列进条目/.test(WSRC));
ok("part 硬规矩里禁写死节号", /禁止写死节号/.test(WSRC));
ok("五维产出件只在 PFIX 下发", (function () {
  const i = WSRC.indexOf("【创新智商五维的产出件");
  if (i < 0) return false;
  const head = WSRC.slice(Math.max(0, i - 4000), i);
  return head.lastIndexOf("PFIX ?") > head.lastIndexOf('") : ""）');
})());

/* ── v2.1 新增：文献综述五十年扫描 · 引言缺陷账 · 文献真实性分级 · 与主流理论的对话 ── */
console.log("── v2.1：综述扫描／缺陷账／文献分级／对话规程 ──");
const byH = (kw) => SKEL.find((x) => x.h.indexOf(kw) >= 0) || { h: "", ask: "" };
const INTRO = byH("引言"), REVIEW = byH("文献述评"), NEAR = byH("最近邻"), REFS = byH("参考文献");
[["综述扫描范围写死五十年", REVIEW, "最近五十年"],
 ["综述须列三个不同叫法", REVIEW, "三个不同的叫法"],
 ["综述按三档年代各扫一遍", REVIEW, "三十到五十年"],
 ["综述每档须交出结论本身", REVIEW, "结论本身"],
 ["综述判据：结论句排一列", REVIEW, "结论句"],
 ["禁把检索边界写成领域边界", REVIEW, "不许把检索的边界写成领域的边界"],
 ["引言须交缺陷账", INTRO, "缺陷账"],
 ["缺陷账形状固定且两处实指", INTRO, "解释到了⟨某一步⟩"],
 ["缺陷是做到哪一步不是他们错了", INTRO, "不是「他们错了」"],
 ["引言与述评盘点表须同源", INTRO, "必须同源"],
 ["文献分三级", REFS, "【二】级"],
 ["页码只在一级上给", REFS, "页码只在【一】级上给"],
 ["吃不准年份宁可不写", REFS, "不填是谨慎"],
 ["表末如实交代分级", REFS, "表末如实交代分级"],
 ["对话四步形状", NEAR, "四步形状"],
 ["必须与主流理论对话", NEAR, "研究生入学书单"],
 ["禁四种没读原文的写法", NEAR, "他会不会说"],
 ["至少一条本文没有答案", NEAR, "这一条本文没有答案"]]
  .forEach(([n, sec, kw]) => ok("v2.1 规程在位：" + n, (sec.h + sec.ask).indexOf(kw) >= 0));
/* 规范层同样要有，且两层都要在——只改一层是站内反复犯的那个病 */
[["五十年扫描", "最近五十年"], ["缺陷账", "缺陷账"], ["文献三级", "【三】"],
 ["对话四步", "四步形状"], ["主流理论对话", "研究生入学书单"], ["有一位打不赢", "这一条本文没有答案"]]
  .forEach(([n, kw]) => ok("Skill 里也写着：" + n, SKILL.indexOf(kw) >= 0));

/* ── v2.2：额度放开 —— 正文各趟不再重送整份对话，省下的入参额度让给正文 ── */
console.log("── v2.2：入参重复已砍／字数额度按实测放开 ──");
ok("v2.2 骨架合计 27,500 字", SKEL.reduce((a, x) => a + x.words, 0) === 27500);
[["盘点表 3000", "五、最近邻盘点与占位划界", 3000], ["核心命题 2400", "四、核心命题", 2400],
 ["述评 2600", "二、文献述评", 2600], ["引言 2200", "一、引言", 2200],
 ["理论框架 2200", "三、理论框架", 2200]]
  .forEach(([n, kw, w]) => ok("v2.2 额度：" + n, (SKEL.find((x) => x.h.indexOf(kw) >= 0) || {}).words === w));
/* 入参那一刀：机器层必须真的分出两份对话额度，且 part 用的是短的那一份 */
ok("worker 里另立了 convoMaxPart", /convoMaxPart\s*=/.test(WSRC));
ok("convoMaxPart 由 convoMax 折算而非照抄", /convoMaxPart[\s\S]{0,160}convoMax\s*\*/.test(WSRC));
ok("convoMaxPart 有上下限（9000–18000）", /convoMaxPart[\s\S]{0,120}9000[\s\S]{0,60}18000/.test(WSRC));
ok("生成了 convoPart 切片", /convoPart\s*=\s*convo\.length\s*>\s*convoMaxPart/.test(WSRC));
ok("part 那一趟送的是 convoPart", /convoPart[\s\S]{0,200}现在只写第/.test(WSRC));
ok("part 那一趟不再送整份 convo", !/content:\s*CONVO\s*\+\s*"现在只写第/.test(WSRC));
ok("plan 那一趟仍通读全场", /content:\s*CONVO\s*\+\s*"现在只输出那个 JSON/.test(WSRC));
ok("注释写明了这一刀的理由（入参按从不发生的输出量配的）", WSRC.indexOf("从不发生的输出量") >= 0);
ok("Skill 里也写着 v2.2 为什么放开", SKILL.indexOf("字数额度为什么放开") >= 0);
ok("Skill 写明放开不等于多烧", SKILL.indexOf("放开」不等于「多烧") >= 0);
ok("Skill 保留「靠加节数不靠加长单节」那条", SKILL.indexOf("篇幅只能靠加节数") >= 0);

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
/* 起点锚原来是 `var shortSecs = [];`——2026-08-12 加退避与撞墙检测后，那一行前面多了
   RETRY_WAIT/WALL_RUN 两个声明，锚点本身还在，但**它们落在了切片之外**，
   抠出来的 step() 里 RETRY_WAIT 就成了未定义。锚要挪到这一组变量的头一行。 */
const _s0 = FSRC.indexOf("      var RETRY_WAIT =") >= 0
  ? FSRC.indexOf("      var RETRY_WAIT =")
  : FSRC.indexOf("      var shortSecs = [];");
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
    /* 真实退避是 20 秒（下面单独有一条断言盯住这个数）；行为测试里把它换成 20 毫秒，
       否则四组用例要跑一分多钟。换的是等待时长，不是逻辑——逻辑仍是源码原文。 */
    stepSrc.replace(/var RETRY_WAIT = \d+;/, "var RETRY_WAIT = 20;")
           .replace("var shortSecs = [], runFail = 0, hitWall = false;", "var shortSecs = [], runFail = 0, hitWall = false; __short = function(){ return shortSecs; };") +
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
    if (box.done || Date.now() - t0 > 15000) return cb();
    setTimeout(w, 10);
  })();
}

/* ⚠ 第二遍现在要退避 20 秒才打——等待时间必须放宽，否则 waitDone 先超时，读到的是假失败 */
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
  /* 留白可以是常数，也可以是「前段一个数、后段一个更大的数」。两种写法都取到，取最小的那个来判。
     ⚠ 2026-08-12 两份真跑都从第 7、8 节起连续多节只吐六七十字 ⇒ 后段必须比前段更松。 */
  const gaps = (stepSrc.match(/setTimeout\(step,[^)]*?(\d{3,5})\s*[:)]/g) || [])
    .map((x) => +(x.match(/(\d{3,5})/) || [0, 0])[1]).filter(Boolean);
  /* ⭐ 2026-08-12 13:23 真跑：第 7–16 节十节、每节两遍、二十次尝试全部只吐几十字。
     十节连撞一次不成 ⇒ 是上游在挡，不是这几节难写。下面六条盯的就是那次读数逼出来的两条对策。 */
  const mWait = stepSrc.match(/var RETRY_WAIT = (\d+);/);
  ok("第二遍是退避之后才打的（立刻重打＝把同一堵墙再撞一次）", !!mWait && +mWait[1] >= 10000);
  ok("退避真的用在第二遍上，不是摆着好看", /setTimeout\(res, RETRY_WAIT\)/.test(stepSrc));
  const mWall = stepSrc.match(/var WALL_RUN = (\d+);/);
  ok("连着几节全败即判撞墙（阈值从源码取：" + (mWall ? mWall[1] : "?") + "）", !!mWall && +mWall[1] >= 2 && +mWall[1] <= 4);
  ok("写够了要把连败计数清零（别把零星失败攒成假撞墙）", (stepSrc.match(/runFail = 0;/g) || []).length >= 2);
  ok("撞墙后立刻收口，不再往下打", /if \(dStopped \|\| hitWall \|\| i >= secs\.length\)/.test(stepSrc));
  ok("撞墙时明说是上游在挡、并说清还差哪几节", /dWallRun1/.test(stepSrc) && /dWallLeft1/.test(stepSrc));

  const mGapAll = (stepSrc.match(/setTimeout\(step,([^;]*?)\);/) || [])[1] || "";
  const gapNums = (mGapAll.match(/\d{3,5}/g) || []).map(Number);
  ok("节间留白取得到数值", gapNums.length > 0);
  ok("最小留白 ≥1200ms（十七趟连打，700 已被两次真跑证明不够）", gapNums.length > 0 && Math.min.apply(null, gapNums) >= 1200);
  ok("后段留白比前段更松（限流是在后几趟撞上的）", gapNums.length >= 2 && Math.max.apply(null, gapNums) > Math.min.apply(null, gapNums));
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
