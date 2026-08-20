/* 只测一件事：**索引重建一天只跑一次，不再挂在每次检索上。**

   病史（2026-08-21 查实，代价是全站躺了大半天）：
   `IndexMemory._query` 每次被调用都 fire-and-forget 触发一次 `_ensure(false)`，
   而复验的判据只有一条 —— R2 上 `search/manifest.json` 的 etag 变没变。
   **而每一次 push 之后，CI 都会重建搜索索引并 sync 到 R2，指纹必变。**
   于是：推一次站 ⇒ 下一个检索的人替全站扛一次全量重建。

   这张表的实测规模是 docs 4488 / **terms 29 万行**，而 Durable Object 免费档是
   **10 万行/天** —— **一次重建就是当天额度的 2.9 倍，一次就爆。**
   那天推了八次，站上计数、留言、系统密钥、心得存储全跟着躺下，
   而用户看到的症状是「智能问答很快就停止」，谁也想不到根子在这里。

   [stated] 用户令：「每天 reindex 一次，自动的，每天固定时间。」

   💡 心法：**「源头变了就重建」这种判据，要先算一遍「源头一天变几次、一次重建多贵」。**
      两个数一乘，才知道它是省事还是灾难。 */
"use strict";
const fs = require("fs");
const W = fs.readFileSync("/home/claude/site/src/worker.js", "utf8");
const CFG = fs.readFileSync("/home/claude/site/wrangler.jsonc", "utf8");

let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };

/* 把 query 分支抠出来单独看 —— 判据只在这一段里找，免得被别处同名的调用蒙混。 */
const iQ = W.indexOf('if (op === "query") {');
const QBLK = iQ >= 0 ? W.slice(iQ, W.indexOf('return this._json({ ok: false, why: "unknown op" });', iQ)) : "";
ok(!!QBLK, "抠得出 IndexMemory 的 query 分支");

console.log("— 一、漏水的那个口子堵上了 —");
/* 旧代码那一行是无条件触发。现在只有「表是空的」这一种情况才建。 */
ok(!/^\s*this\._ensure\(false\)\.catch\(\(\) => \{\}\);\s*$/m.test(QBLK),
   "查询分支里没有**无条件**触发重建的那一行了（那正是把额度写爆的口子）");
ok(/if \(!_n0\) this\._ensure\(false\)\.catch\(\(\) => \{\}\);/.test(QBLK),
   "只剩冷启动兜底：**表是空的**才建（不然新部署后要等到明天才有索引）");
ok(/SELECT count\(\*\) AS n FROM docs/.test(QBLK) && /try \{ _n0 =/.test(QBLK),
   "数表用 try 包着（DO 存储躺下时不许把查询也拖死——这一整天就是这么过来的）");
ok(/return this\._json\(this\._query\(b\)\);/.test(QBLK),
   "查询本身照旧应答（重建与否，老表都要能答）");

console.log("— 二、每日定时器接上了 —");
const iS = W.indexOf("async scheduled(event, env, ctx) {");
const SBLK = iS >= 0 ? W.slice(iS, W.indexOf("async fetch(request, env, ctx) {", iS)) : "";
ok(!!SBLK, "抠得出 scheduled 处理器");
ok(/const ir = await idxAsk\(env, \{ op: "ensure" \}\);/.test(SBLK),
   "每日定时器里真的跑了一次重建");
ok(!/force: true/.test(SBLK),
   "**不是** force：仍走指纹复验，源头没变就什么都不做 ⇒ 这一趟幂等且廉价，多跑一次不多写一行");
ok(/wxSweep\(env, Date\.now\(\)\)/.test(SBLK) && SBLK.indexOf("wxSweep") < SBLK.indexOf("idxAsk"),
   "原有的微信库清扫仍在，且排在前面（新活不许挤掉旧活）");
ok(/console\.log\("\[idx-daily\]"/.test(SBLK),
   "留一行日志（这一趟没人看着，出了事只能靠它）");
/* idxAsk 内部吞错回 null：定时任务不能因为索引重建而整个红掉。 */
const iAsk = W.indexOf("async function idxAsk(env, body) {");
ok(iAsk > 0 && /catch \(e\) \{ return null; \}/.test(W.slice(iAsk, iAsk + 700)),
   "idxAsk 失败回 null 不抛（重建挂了不许把定时任务连累成红的）");
ok(iAsk > 0 && iAsk < iS, "idxAsk 定义在 scheduled 之前（顺序错了就是运行时 undefined）");

console.log("— 三、定时器本身还在配置里 —");
ok(/"triggers":\s*\{\s*"crons":\s*\[/.test(CFG), "wrangler 里有定时触发器");
const mC = CFG.match(/"crons":\s*\[([^\]]*)\]/);
ok(!!mC && /\d/.test(mC[1]), "cron 表达式非空 · 实得 " + (mC ? mC[1].trim() : "?"));

console.log("— 四、手动那条路仍在（出事时要能立刻重建，不必等明天）—");
ok(/url\.pathname === "\/api\/idx\/status"/.test(W), "状态与手动触发的探口还在");
ok(/if \(url\.searchParams\.get\("build"\) === "1"\) op = "ensure";/.test(W),
   "?build=1 仍可手动触发一次指纹复验式重建");
ok(/force && !\(await adminPassOk\(/.test(W),
   "无条件全量重建（force）仍要管理口令——它才是贵的那一格");

console.log("— 五、注释不许留下过时的说法（下一个人会照着它判断）—");
ok(!/_query 每次都会 fire-and-forget 触发这里/.test(W),
   "那句「_query 每次都会触发这里」的旧注释已改掉（留着它，下一个人会以为漏还在）");

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
