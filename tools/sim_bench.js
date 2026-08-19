/* sim_bench.js —— 盯住同题基准这套工具本身
 *
 * 为什么它需要护栏：一套会**自己给自己打分**的实验，出错的方式不是崩溃，是**悄悄偏向自己**。
 * 去标识漏一个词、失败的格子被丢出均值、ΔIQ 换了个分母——每一处都不报错，
 * 而报告照样打印出一张漂亮的表。这个文件把最容易偏的那几处钉住。
 * 跑法：node tools/sim_bench.js
 */
"use strict";
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, "..");
let pass = 0, fail = 0;
const ok = (n, c, d) => { if (c) { pass++; console.log("  ✓ " + n); } else { fail++; console.log("  ✗ " + n + (d ? ("  " + d) : "")); } };
const RUN = fs.readFileSync(path.join(ROOT, "tools/bench_run.js"), "utf8");
const SCO = fs.readFileSync(path.join(ROOT, "tools/bench_score.js"), "utf8");
const REP = fs.readFileSync(path.join(ROOT, "tools/bench_report.js"), "utf8");
const QS = JSON.parse(fs.readFileSync(path.join(ROOT, "tools/bench/questions.json"), "utf8"));

/* ═══ 一、题库覆盖（建议书 §15.2）═══════════════════════════ */
console.log("── 题库 ──");
ok("★ 至少 30 题", QS.items.length >= 30, "实得 " + QS.items.length);
ok("id 不重复", new Set(QS.items.map((x) => x.id)).size === QS.items.length);
ok("题面不重复", new Set(QS.items.map((x) => x.q)).size === QS.items.length);
const cnt = (k, v) => QS.items.filter((x) => x.tags[k] === v).length;
["what", "how", "why"].forEach((t) => ok("What/How/Why 三类都够（" + t + " " + cnt("type", t) + " 题）", cnt("type", t) >= 6));
ok("学科内与跨学科都有（intra " + cnt("scope", "intra") + " / cross " + cnt("scope", "cross") + "）",
  cnt("scope", "intra") >= 6 && cnt("scope", "cross") >= 6);
ok("★ 有成熟最近邻的题够多（造新词一定撞人的那一类，mature " + cnt("nbr", "mature") + "）", cnt("nbr", "mature") >= 15);
ok("占位稀薄的题也留着（thin " + cnt("nbr", "thin") + "）——它专治「误以为自己原创」", cnt("nbr", "thin") >= 4);
ok("★ 有「容易造新名词但难产生新辨别维度」的陷阱题（namebait " + cnt("trap", "namebait") + "）", cnt("trap", "namebait") >= 6);
ok("可低成本证伪的题够多（cheap " + cnt("falsify", "cheap") + "）", cnt("falsify", "cheap") >= 12);
ok("证伪代价高的也留着（hard " + cnt("falsify", "hard") + "）", cnt("falsify", "hard") >= 6);
/* ⚠ 题目要同时喂给别家模型，带上自家术语等于给自己送分。 */
const SDEWORD = ["SDE", "显露", "差异序列", "特征纠缠", "发生学", "二阶", "碰撞", "创新智商"];
const dirty = QS.items.filter((x) => SDEWORD.some((w) => x.q.indexOf(w) >= 0));
ok("★★ 题面零自家术语（带术语＝给自己送分，别家答不上来不是它笨）", dirty.length === 0,
  dirty.map((x) => x.id).join(","));
ok("标签只用在覆盖自检，不进提示语", RUN.indexOf("tags") < 0 || !/content:[^\n]*tags/.test(RUN));

/* ═══ 二、跑分器 ═══════════════════════════════════════════ */
console.log("── 跑分器 ──");
ok("★ Key 只从环境变量取，不写进文件", /process\.env\.BENCH_KEY/.test(RUN) && !/sk-[A-Za-z0-9]{16,}/.test(RUN));
ok("★★ 产物里的 Key 会被抹掉（一旦落进产物就收不回来）",
  /function scrub\(/.test(RUN) && /split\(KEY\)\.join\("<KEY>"\)/.test(RUN) && /Bearer/.test(RUN));
const SCRUB = new Function("KEY", RUN.slice(RUN.indexOf("function scrub(s) {"), RUN.indexOf("/* ── 臂：")) + "\n return scrub;");
const sc = SCRUB("sk-abcdefghijklmnop");
ok("抹得掉直给的那一把", sc("报错：Bearer sk-abcdefghijklmnop 无效").indexOf("sk-abcdefghijklmnop") < 0);
ok("★ 也抹得掉**别的**形状的 Key（上游回显里那一把不是你的）",
  sc("upstream said sk-ZZZZZZZZZZZZZZZZZZ bad").indexOf("sk-ZZZZZZZZZZZZZZ") < 0);
ok("失败也留记录（不是丢掉）", /ok: !!r\.ok/.test(RUN) && /err: scrub\(r\.err/.test(RUN) && /fs\.appendFileSync\(outFile/.test(RUN));
ok("★ 断点续跑：只跳过**成功**的格子，失败的下一趟还要重试", /if \(r\.ok\) done\[r\.cell\] = 1;/.test(RUN));
ok("★★ 口径快照：跑到一半换了代码就停（前后两半不可比）",
  /worker_sha/.test(RUN) && /old\.worker_sha !== snap\.worker_sha/.test(RUN) && /process\.exit\(2\)/.test(RUN));
ok("bare 臂是零提示语（它是 ΔIQ 的分母）",
  /messages: \[\{ role: "user", content: q \}\]/.test(RUN) && /分母/.test(RUN));
ok("★ std/deep 走站内那条真路，不另写一份提示语", /不要在这里另写一份提示语/.test(RUN) && /\/api\/wds\/chat/.test(RUN));
ok("forge 臂遇闸门不过就停，并记下停在第几道", /stopped_at_/.test(RUN) && /gate !== "passed"/.test(RUN));
ok("forge 一题十八次调用，默认不跑（要跑自己点名）", /默认不跑/.test(RUN));
/* ⚠ 站内 WDS_PER_MIN = 20 ⇒ 走站内的臂至少 3 秒一发。发快了限流器会挡，
   而挡下来的那一条会被记成"失败"，把完成率这个读数弄脏。 */
const perMin = (parseInt((fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8")
  .match(/const WDS_PER_DAY = \d+, WDS_PER_MIN = (\d+)/) || [])[1], 10) || 20);
const gap = parseInt((RUN.match(/await sleep\(c\.arm === "bare" \? \d+ : (\d+)\)/) || [])[1], 10) || 0;
ok("★★ 走站内的臂发得比限流慢（限流 " + perMin + "/分钟，实际间隔 " + gap + "ms）",
  gap > 0 && gap >= (60000 / perMin), "需要 ≥" + Math.ceil(60000 / perMin) + "ms");
ok("★ 阈值是从 worker 的限流常数**算出来**的，不是这里手抄的一个数", /WDS_PER_DAY = \\d\+, WDS_PER_MIN/.test(fs.readFileSync(path.join(ROOT, "tools/sim_bench.js"), "utf8")));
ok("forge 逐道之间同样留够（每一道都是一次站内调用）", /await sleep\(3400\);\s*\/\/ 同上/.test(RUN));
ok("bare 直连厂商，不吃站内那条限流，可以快一点", /c\.arm === "bare" \? 1200/.test(RUN));
ok("★ 提纲那一趟打的是 research 端点（打错 chat 整条 forge 臂跑不起来）",
  /fetch\(SITE \+ "\/api\/wds\/research"/.test(RUN));
ok("std/deep 的档位字段与服务端对得上（b.mode === \"deep\"）", /mode: deep \? "deep" : "std"/.test(RUN));
ok("--take 能先只跑前 N 题（先要一个读数，别一上来烧满）", /const TAKE = /.test(RUN) && /items\.slice\(0, TAKE\)/.test(RUN));

/* ═══ 三、⭐ 盲评：这套实验的命根子 ═══════════════════════ */
console.log("── 盲评 ──");
const BL = new Function(SCO.slice(SCO.indexOf("const BLIND_WORDS = ["), SCO.indexOf("/* 确定性打乱"))
  + "\n return { words: BLIND_WORDS, blind: blind };")();
ok("★★ 产线工艺术语全在遮蔽表里",
  ["碰撞", "二阶", "闸门", "工序", "学科通融", "创新智商", "本段提取"].every((w) => BL.words.indexOf(w) >= 0));
ok("★★ 各家厂商名也在表里（认出是哪家＝认出是哪一臂）",
  ["DeepSeek", "GPT", "Claude", "Kimi", "GLM"].every((w) => BL.words.indexOf(w) >= 0));
const raw = "## 7. 共有前提\n\n这一步用二阶碰撞撞出候选判断，学科通融的工序表如此。创新智商 148。\n【闸门】passed";
const bl = BL.blind(raw);
ok("★★ 抹完之后一个标识词都不剩", !BL.words.some((w) => bl.indexOf(w) >= 0), bl.slice(0, 60));
ok("★★ 成品里残留的自评分数也抹掉（不然评分者被它锚住）", bl.indexOf("148") < 0);
ok("道次编号那一行抹掉（「## 7.」本身就说明它出自一条产线）", !/##\s*7\./.test(bl));
ok("抹的是标识不是内容（留下可读的正文）", bl.length > 10);

/* ⚠ new Function 的壳里没有 require——crypto 当参数传进去，别在壳里去 require。 */
const SH = new Function("crypto", SCO.slice(SCO.indexOf("function shuffle(arr, seed)"), SCO.indexOf("/* ── 评分者的系统提示"))
  + "\n return shuffle;");
const shuffle = SH(require("crypto"));
const src = Array.from({ length: 40 }, (_, i) => i);
const s1 = shuffle(src, "seed-a"), s2 = shuffle(src, "seed-a"), s3 = shuffle(src, "seed-b");
ok("★ 顺序真的打乱了（不打乱，同一题各臂会挨着出现，一眼看得出）", s1.join() !== src.join());
ok("★★ 同一个 seed 给同一个顺序（实验要可复核，不能每跑一次换一个次序）", s1.join() === s2.join());
ok("换 seed 就换顺序", s1.join() !== s3.join());
ok("一个都不多一个都不少", s1.slice().sort((a, b) => a - b).join() === src.join());

ok("★★ 评分者不装心得、不装骨架、不用老师人格（装了会对自家语汇过敏性加分）",
  /你是一位独立的评分者/.test(SCO) && SCO.indexOf("SDE 本体论的老师") < 0 && SCO.indexOf("reflect") < 0);
ok("★ 告诉评分者 ⟦…⟧ 是抹掉的标识，别据此猜来源、别据此扣分", /不要据此猜测来源/.test(SCO) && /不要因为「看不清」而扣分/.test(SCO));
ok("★★ I 维必须落到外部材料上，材料里没有的作者年份不许写", /材料里没有的作者与年份一个都不许写/.test(SCO));
ok("★★ 同一题各臂共用同一份外部材料（同一块地面上判占位，才谈得上公平）", /同一题的所有臂共用同一份证据/.test(SCO));
ok("没取到外部材料时强制 evidence_ok=false、conf=low、I 不许给高分",
  /evidence_ok 必须写 false/.test(SCO) && /I 不许给高分/.test(SCO));
ok("五维权重与闸门写死在提示里", /0\.20S\+0\.25D\+0\.20E\+0\.20I\+0\.15F/.test(SCO) && /封顶 145/.test(SCO));
ok("对照表另存（报告那一步才还原成臂）", /keymap\.json/.test(SCO));
ok("--dry 能先做一次去标识自检，不烧一分钱", /去标识自检/.test(SCO) && /DRY/.test(SCO));

/* ═══ 四、统计口径 ═══════════════════════════════════════ */
console.log("── 统计 ──");
const RP = new Function(REP.slice(REP.indexOf("const DIMS = ["), REP.indexOf("function main() {"))
  + "\n return { iqOf: iqOf, mean: mean, sd: sd, med: med, W: W };")();
ok("五维权重与站内同源", RP.W.S === 0.20 && RP.W.D === 0.25 && RP.W.E === 0.20 && RP.W.I === 0.20 && RP.W.F === 0.15);
const good = { S: 150, D: 150, E: 150, I: 150, F: 150 };
ok("满分算得对", RP.iqOf(good) === 150);
ok("★★ 闸门在**这里**再算一遍（评分者偶尔会忘了套，而闸门最不该被绕过）",
  RP.iqOf({ S: 160, D: 170, E: 160, I: 110, F: 150 }) === 145);
ok("F 塌了同样封顶", RP.iqOf({ S: 160, D: 170, E: 160, I: 150, F: 110 }) === 145);
ok("两维都不塌就不封顶", RP.iqOf({ S: 160, D: 170, E: 160, I: 125, F: 125 }) > 145);
ok("取得到 {v:…} 这种形状", RP.iqOf({ S: { v: 150 }, D: { v: 150 }, E: { v: 150 }, I: { v: 150 }, F: { v: 150 } }) === 150);
ok("统计函数对：mean/sd/med", RP.mean([1, 2, 3]) === 2 && Math.round(RP.sd([2, 4, 4, 4, 5, 5, 7, 9])) === 2 && RP.med([3, 1, 2]) === 2);
ok("★★ ΔIQ 一律以 bare 为分母（换分母会把「这家基底行不行」混进来）",
  /const baseIq = A\.bare \? A\.bare\.iq : null;/.test(REP) && /ΔIQ 一律以 bare/.test(REP));
/* ⚠⚠ 这一条第一版查的是源码串，而把 `armCells[...] = ...` 改成 `if (r.ok) armCells[...] = ...`
   之后**那条串仍在**、断言照样绿，可完成率已经从 78% 变成 100%（失败的格子被踢出了分母）。
   💡 心法：**"有没有做某件事"用源码串查得出，"做对没做对"只有真跑查得出。**
   所以改成拿一份 fixture 真跑汇总。 */
const AGG = require(path.join(ROOT, "tools/bench_report.js")).aggregate;
const fxRuns = [
  { cell: "c1", q: "q01", arm: "forge", rep: 1, ok: true, ms: 1000, chars: 5000, usage: { total_tokens: 100 } },
  { cell: "c2", q: "q01", arm: "forge", rep: 2, ok: false, ms: 500, chars: 0, err: "stopped_at_7" },
  { cell: "c3", q: "q02", arm: "forge", rep: 1, ok: true, ms: 1000, chars: 5000, usage: { total_tokens: 100 } },
  { cell: "c4", q: "q02", arm: "forge", rep: 2, ok: false, ms: 500, chars: 0, err: "stopped_at_9" },
  { cell: "c5", q: "q01", arm: "bare", rep: 1, ok: true, ms: 100, chars: 900, usage: { total_tokens: 20 } },
];
const fxKm = { A1: { anon: "A1", cell: "c1", q: "q01", arm: "forge", rep: 1 },
               A2: { anon: "A2", cell: "c3", q: "q02", arm: "forge", rep: 1 },
               A3: { anon: "A3", cell: "c5", q: "q01", arm: "bare", rep: 1 } };
const mkS = (anon, v, ev) => [1, 2, 3].map((j) => ({ anon: anon, judge: j, ok: true,
  score: { S: v, D: v, E: v, I: v, F: v, evidence_ok: ev !== false } }));
const fxSc = mkS("A1", 145).concat(mkS("A2", 145), mkS("A3", 115));
const G = AGG(fxRuns, fxSc, fxKm);
ok("★★ 失败的格子留在完成率的分母里（丢掉它，完成率会自己变成 100%）",
  G.A.forge.done === "2/4" && Math.abs(G.A.forge.doneRate - 0.5) < 1e-9, G.A.forge.done);
ok("★★ 失败的格子不进均值（它没有正文，也没人评过）", G.A.forge.n === 2);
ok("ΔIQ 的分母确实是 bare 那一臂", Math.abs(G.A.forge.iq - G.A.bare.iq - 30) < 1e-9);
ok("耗时/字数只统计成功的那几格（失败的 0 字不该把均值拉下来）", G.A.forge.chars === 5000);
const G2 = AGG(fxRuns, mkS("A1", 145, false).concat(mkS("A2", 145, false), mkS("A3", 115)), fxKm);
ok("★★ 「无外部证据却给了高分」数得出来（它为 0 才算这套闸真的立住了）",
  G2.perDoc.filter((d) => d.hiNoEv).length === 2 && G.perDoc.filter((d) => d.hiNoEv).length === 0);
ok("源码里也写明了分母是计划跑的格子", /分母＝计划跑的格子，失败的也算/.test(REP));
ok("完成率单独报，不和均值混在一起", /doneRate/.test(REP) && /完成率/.test(REP));
ok("★ 评分者之间的分歧要报（一次输出不能当客观测量）", /spread/.test(REP) && /最大分歧/.test(REP));
ok("★★ 「无外部证据却给了高分」单列一栏——它为 0 才算这套闸真的立住了", /hiNoEv/.test(REP) && /evidence_ok === true/.test(REP));
ok("成本与时间照实报", /平均耗时/.test(REP) && /平均 token/.test(REP));
ok("★★ 逐条对着 §15.4 判达标，没达标就写没达标", /验收目标逐条/.test(REP) && /❌/.test(REP));
ok("★★ 明写不许调评分提示制造更高分", /不许调评分提示制造更高分/.test(REP));
ok("明写单次实验只是一个读数、不是结论", /不是结论/.test(REP));

console.log("\n" + (fail ? "✗ " : "✓ ") + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
