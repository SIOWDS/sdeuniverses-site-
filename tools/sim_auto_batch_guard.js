/* sim_auto_batch_guard —— 钉住 2026-08-21 第七刀补上的四个黑洞：
   ① autoBatch 的看门狗（它是自动二十轮的主力，却曾是四条流式通道里唯一裸奔的一条）
   ② autoBatch 的 fin / beat 消费端（诊断帧只装了别的路，这条路整帧丢掉）
   ③ viewsText 的入料上限（二十轮四五万字符，20000 会切掉后十轮）
   ④ doIq 的入料上限（两万字论文，26000 会砍掉结尾——正是 F 维要评的那段）
   ③④ 都是「前后端成对」的判据：只放开一头等于换个地方静默砍。

   ⚠ 抠取锚点一律选「同类里唯一」的形状，且不得在注释里写出锚点原文
   （sim_paper_half_guard／four_parts／paper_thread／ask_quota 已各栽过一次）。 */
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");
const H = fs.readFileSync(path.join(ROOT, "public/search/index.html"), "utf8");
const W = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");

let pass = 0, fail = 0;
function ok(name, cond) { if (cond) { pass++; console.log("  PASS " + name); } else { fail++; console.log("  FAIL " + name); } }
function sec(t) { console.log("\n— " + t); }

/* ── 抠出 autoBatch 的函数体（从它的定义到下一个顶层 function） ── */
const AB0 = H.indexOf("function autoBatch(from, n, ix, attempt){");
const AB1 = H.indexOf("\nfunction batchWhy(", AB0);
const AB = AB0 >= 0 && AB1 > AB0 ? H.slice(AB0, AB1) : "";

sec("① 抠取本身要成立（抠不出来，后面全是假绿）");
ok("抠得出 autoBatch 函数体", AB.length > 800);
ok("抠出来的确实是这一条路（认得出成批问对的模式名）", /mode:'rounds'/.test(AB));
ok("没有把下一个函数一起抠进来", !/function batchWhy\(/.test(AB));

sec("② 看门狗：这条路不许再裸奔");
ok("有 AbortController", /new AbortController\(\)/.test(AB));
ok("fetch 带 signal（不带 signal 的 abort 是空转）", /signal:_ac\?_ac\.signal:undefined/.test(AB));
ok("有停滞闸 _bump", /function _bump\(ms\)\{[\s\S]{0,200}setTimeout/.test(AB));
ok("停滞时置旗标并真的 abort", /_stalled=true;[\s\S]{0,60}_ac && _ac\.abort\(\)/.test(AB));
const mFirst = AB.match(/_bump\((\d+)\);\s*\n\s*\/\*/) || AB.match(/_bump\((\d{5,6})\);/);
ok("首帧闸给得够宽（出流前要检索＋装内功心得，≥120 秒）",
  !!mFirst && parseInt(mFirst[1], 10) >= 120000);
const mFrame = AB.match(/_bump\((\d+)\);\s*\n\s*if\(j\.t==='token'\)/);
ok("每收到一帧就续闸（帧间闸 30–120 秒之间）",
  !!mFrame && parseInt(mFrame[1], 10) >= 30000 && parseInt(mFrame[1], 10) <= 120000);
ok("帧间闸比首帧闸严（否则等于只有一道闸）",
  !!mFirst && !!mFrame && parseInt(mFrame[1], 10) < parseInt(mFirst[1], 10));
ok("两条收口路径都清掉定时器（不清＝页面留一个必然触发的 abort）",
  (AB.match(/if\(_wd\) clearTimeout\(_wd\);/g) || []).length >= 2);
ok("主动掉线与真失败分开报（否则又回到猜）", /_stalled \?/.test(AB) && /主动掉线/.test(AB));

sec("③ 诊断帧：fin 与 beat 都要有消费端");
ok("接住收笔读数帧", /j\.t==='fin'/.test(AB));
ok("收笔读数四样都记下（停因/上游有没有收尾/第几秒/推演字数）",
  /_rd\.fin=/.test(AB) && /_rd\.done=/.test(AB) && /_rd\.sec=/.test(AB) && /_rd\.think=/.test(AB));
ok("接住心跳帧", /j\.t==='beat'/.test(AB));
ok("心跳记数（一个心跳都没有＝这一趟活了不到 5 秒，是最硬的证据）", /_rd\.beats\+\+/.test(AB));
ok("出流前用心跳接管状态行（那一段本来是纯静默）", /if\(!acc\.length\)\{[\s\S]{0,200}autoStat\(/.test(AB));
/* 这一条是本次最容易被写错的地方，单独钉死 */
ok("我们自己发的 [DONE] 不写进 done 字段（两者同名不同事）",
  /\[DONE\]'\)\{ _rd\.sseEnd=true;/.test(AB) && !/\[DONE\]'\)\{ _rd\.done=true/.test(AB));
ok("_rd 初值里 done 与 sseEnd 是两个字段", /done:false, sseEnd:false/.test(AB));

sec("④ 少写了几轮要说出为什么");
ok("有专门的解释函数", /function batchWhy\(rd\)\{/.test(H));
const BW0 = H.indexOf("function batchWhy(rd){");
const BW = H.slice(BW0, BW0 + 700);
ok("解释里带秒数", /流停在第 '\+\(rd\.sec\|\|0\)/.test(BW));
ok("解释里带停因", /rd\.fin/.test(BW));
ok("没收到上游收尾时明说（这是被掐断的铁证）", /if\(!rd\.done\)/.test(BW));
ok("一个心跳都没有时明说", /if\(!rd\.beats\)/.test(BW));
ok("没写满时把真因写进面板注记", /landed<n[\s\S]{0,160}batchWhy\(_rd\)/.test(AB));
ok("两次都切不出时也报真因，不再只说「没按标记交卷」",
  /两次都没切出完整轮次 —— '\+batchWhy\(_rd\)/.test(AB));
ok("掉线那一支也带读数", /主动掉线 —— '\+batchWhy\(_rd\)/.test(AB));
/* 回归：落了轮次就必须照常渲染，不许因为「没写满」这一支提前 return 而漏掉 */
ok("只要落了轮次就照常渲染入档（没写满也一样）",
  /if\(landed>0\)\{[\s\S]{0,320}renderThread\(\); updateTurnBar\(\);/.test(AB));
ok("面板注记分两种写法，但渲染只有一处（不许有第二条 return 绕开渲染）",
  (AB.match(/renderThread\(\); updateTurnBar\(\);/g) || []).length === 1);

sec("⑤ 入料上限：前后端成对，且够二十轮用");
const mV = H.match(/function viewsText\(\)\{[\s\S]{0,400}?slice\(0,(\d+)\)/);
ok("前端 viewsText 抠得出上限", !!mV);
ok("前端上限 ≥100000（二十轮四五万字符，要留足余量）", !!mV && parseInt(mV[1], 10) >= 100000);
const mVS = W.match(/const views = String\(body\.views \|\| ""\)\.slice\(0, (\d+)\)/);
ok("服务端 collide 的 views 抠得出上限", !!mVS);
ok("服务端与前端同一个数（只放开一头＝换个地方静默砍）",
  !!mV && !!mVS && mV[1] === mVS[1]);
const mIq = H.match(/mode:'iq',q:lastQ\|\|'创新智商评估',text:text\.slice\(0,(\d+)\)/);
ok("前端 doIq 抠得出上限", !!mIq);
ok("前端 iq 上限 ≥100000（两万汉字＝2.1–2.8 万字符，26000 正好砍掉结尾）",
  !!mIq && parseInt(mIq[1], 10) >= 100000);
const IQ0 = W.indexOf('if (mode === "iq") {');
const mIqS = W.slice(IQ0, IQ0 + 2000).match(/const text = String\(body\.text \|\| ""\)\.slice\(0, (\d+)\)/);
ok("服务端 iq 抠得出上限", !!mIqS);
ok("服务端与前端同一个数", !!mIq && !!mIqS && mIq[1] === mIqS[1]);
/* 回归：这两个旧数字不许再出现在这两处 */
ok("viewsText 不再是 20000", !!mV && mV[1] !== "20000");
ok("doIq 不再是 26000", !!mIq && mIq[1] !== "26000");

sec("⑥ 邻居没被碰坏（四条流式通道都该有闸）");
["function doAsk(){", "function streamPaper(part, extra){", "function sseCollect(payload, onStat){"].forEach(function (anchor) {
  const i = H.indexOf(anchor);
  const blk = H.slice(i, i + 4000);
  ok("仍有看门狗：" + anchor.replace(/function |\(.*/g, ""),
    i > 0 && /new AbortController\(\)/.test(blk) && /_bump\(/.test(blk));
});

console.log("\n===== " + pass + " PASS / " + fail + " FAIL =====");
process.exit(fail ? 1 : 0);
