/* sim_chatsde_oneshot.js —— 「一趟出全篇」这一档（kind = paper1）
 *
 * 缘起（2026-08-12）：[stated] 用户「以前的论文都是一次出 2 万字，绝对可以」
 * 「你自己读读 SDE 金点子」「不要持续吐字，要做成『完成多少字』的流，来对付 Worker 的限制」。
 *
 * 去读了 /taste/idea-generator/，他是对的，而我 memory 里那条「一万字装不进一趟」是**错判**。
 * 那台机器一直这么干，注释白纸黑字：
 *   · `PAPER_MAX_TOKENS = 32000`，「token 上限只做安全天花板，**绝不让论文断头**」
 *   · 「流式…永不撞 ~100s 网关超时——这才让长文跑得通」
 *   · 「**论文生成不用"流式蹦字"**——正文区不显示逐字过程，只让状态栏"✍ 已生成 N 字"滚动，
 *      每一步完成后再把整篇一次性显示到正文区」
 *
 * 我信了那条错判去拆十六趟，然后花一整天查"第 7 节为什么写不出来"——**那道题是拆趟自己造出来的**。
 * 💡💡 心法：**动手改一台机器之前，先去看站里那台已经跑通同一件事的。**
 * 💡💡 心法：**长文的瓶颈不在生成端，在渲染端。** 每 130ms 排一次版，主线程被占死，
 *      读流的回调就排不上——流不是被上游停的，是被我们自己停的。
 *
 * 跑法：node tools/sim_chatsde_oneshot.js
 */
"use strict";
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, "..");
let pass = 0, fail = 0;
const ok = (n, c, d) => { if (c) { pass++; console.log("  ✓ " + n); } else { fail++; console.log("  ✗ " + n + (d ? ("  " + d) : "")); } };
const W = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");
const F = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");
const G = fs.readFileSync(path.join(ROOT, "public/taste/idea-generator/index.html"), "utf8");
/* 判「某句旧代码已经不在」时先剥注释——注释里必然引到它（今天踩过五次）。 */
const bare = (s) => s.replace(/\/\*[\s\S]*?\*\//g, " ").replace(/^\s*\/\/.*$/gm, " ");

/* ═══ 一、口径与金点子那台对齐 ═══════════════════════════════ */
console.log("── 三条口径逐条对着金点子抄 ──");
const gCap = +((G.match(/const PAPER_MAX_TOKENS = (\d+);/) || [])[1] || 0);
ok("★ 读得到金点子那台的论文预算（" + gCap + "）", gCap > 0);
const seg = W.slice(W.indexOf("paper1: {"), W.indexOf("paper: { name:"));
ok("抠得到 paper1 这一档", seg.length > 500);
const p1tok = +((seg.match(/tok: (\d+)/) || [])[1] || 0);
ok("★★ 预算与金点子同源（" + p1tok + " vs " + gCap + "）", p1tok === gCap,
  "抄它的数，别自己另定一个");
ok("★★ 不是 64000：天花板不是目标，给太大反而让思考吃掉预算", p1tok !== 64000);
ok("★★ 长度靠 Prompt 硬约束（写进规格的字数区间），不靠拆节",
  /18000[–\-]22000/.test(seg) && /字数服从内容/.test(seg));
ok("★ 十六节体例整个写进提示语（一趟里要交的全部东西）",
  /PAPER_SKELETON\.map/.test(seg) && seg.indexOf("逐节要交的东西") > 0);
ok("★★ 明写从头写到尾、中途不要停下来问", /中间不要停下来问/.test(seg) && /必须把最后一节写完/.test(seg));

console.log("── 预算不许被入参挤掉 ──");
ok("★★ 一趟出全篇不参与「按剩余上下文收窄」（那会把两万字压成一万出头）",
  /const _oneShot = kind === "paper1";/.test(W)
  && /const tokWant = _oneShot \? SPEC\.tok/.test(W));
ok("注释说清了为什么：token 上限只做天花板，绝不让论文断头", /绝不让论文断头/.test(W));
ok("★★ 总时长闸跟着放宽（300 秒是按三千字那档配的）",
  /_oneShot \? 900000 : DISTILL_TOTAL_MS/.test(W));
ok("注释留下这条心法：换了产出量级就回头看所有按旧量级配的常数",
  /换了产出量级，先回头看所有按旧量级配的常数/.test(W));

/* ═══ 二、⭐ 渲染端：这一条才是「写不下去」的真病根 ═══════════ */
console.log("── 不逐字排版，只滚「已生成 N 字」 ──");
ok("★★★ 一趟出全篇时一个字都不排版（排版全部推到收尾）",
  /if \(!oneShot && Date\.now\(\) - lastP > paintGap\)/.test(F));
ok("★★ 另起一个 ticker 只读 text.length（不占主线程）",
  /function tickStart\(\)/.test(F) && /setInterval\(function \(\)/.test(F) && /dOneN1/.test(F));
const mTick = F.match(/tickT = setInterval\([\s\S]{0,200}?\}, (\d+)\);/);
ok("★ ticker 的间隔与金点子同量级（" + (mTick ? mTick[1] : "?") + "ms）",
  !!mTick && +mTick[1] >= 300 && +mTick[1] <= 1000);
ok("★★ ticker 在收尾时停掉（setInterval 不停会一直跑）",
  /function tickStop\(\)/.test(F) && /tickStop\(\);\s*\/\/ 先停/.test(F));
ok("★ 正文区先摆一句「生成中」，并说清为什么不逐字上屏",
  /dOneWait/.test(F) && /逐字排版会把浏览器主线程占死/.test(F));
ok("★★ 只有 paper1 走这条路，别的档一个字都没动",
  /oneShot = \(kind === "paper1"\);/.test(F));
ok("注释写明了这条心法（长文的瓶颈在渲染端）", /长文的瓶颈不在生成端，在渲染端/.test(F));
ok("注释引了金点子那句原话（下一个人不必再去翻）", /只让状态栏"✍ 已生成 N 字"滚动/.test(F));

/* ═══ 三、两档并存，旧的那条一个字没动 ═══════════════════════ */
console.log("── 两档并存 ──");
ok("★ 十六趟那一档还在（拿两条的读数对账，别拿信念对账）",
  /paper: \{ name: "学术论文（两万字·投稿体例）"/.test(W) && /var CHUNKED = \{ paper: 1 \}/.test(bare(F)));
ok("★★ paper1 不在 CHUNKED 表里（在表里就又被拆成十六趟了）",
  !/CHUNKED = \{[^}]*paper1/.test(bare(F)));
ok("界面上两档分得清（一趟写完 / 分十六趟）",
  /kPaper1: "凝成两万字论文 · 一趟写完"/.test(F) && /kPaper: "凝成两万字论文 · 分十六趟"/.test(F));
ok("英文同步（中英双份纪律）", /single pass/.test(F) && /sixteen passes/.test(F));
ok("★ 出稿三口（Word／PDF／投稿）认得 paper1", /kind === "paper" \|\| kind === "paper1"/.test(F));
ok("落进「成文记录」的档名也认得", /KIND_KEYS = \["report", "essay", "paper1", "paper"/.test(F));
ok("注释记下了这是用户指出来的、我 memory 那条是错判", /是\*\*错判\*\*/.test(W) && /那道题是拆趟自己造出来的/.test(W));

console.log("\n" + (fail ? "✗ " : "✓ ") + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
