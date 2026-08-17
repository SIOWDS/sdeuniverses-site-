/* sim_asset_stamps.js —— 「线上是新的、读者拿到的是旧的」这一类静默失效的护栏（全资产版）
 *
 * `/wds-mode.js` 那一条线早有专用护栏（tools/sim_wds_mode_stamp.js）。本文件管**其余全部**
 * 带 `?v=` 的静态资产——2026-08-17 之前它们一个工具都没有、一条断言都没有：
 *   `/assets/sde-talk.js` 全站同时挂着四种戳（20260731b×7 / 20260802a×2 / 20260802b×1875 / 20260803a×1）、
 *   `/taste/wds-companion/wds-read.js` 两种、`sde-vault.js` 三种、`wds-savedir.js` 两种、
 *   `sde-handoff.js` 两种、`sde-essential-figures.js` 两种。
 *   **等于把读者分成了几批，各跑各的版本**，而构建、线上文件、所有 sim 全是绿的。
 *
 * 查五件：
 *   ① 账本在，且每一行读得到（路径 / 戳 / 哈希 / 用过的戳）
 *   ② 每个资产盘上的内容哈希与账本一致（不一致 ⇒ 改完没跑 tools/bump_asset.py，读者继续拿旧的）
 *   ③ 每个资产全站只有一种戳，且就是账本记的那一个
 *   ④ **凡是仓库里带 `?v=` 的资产，都必须在账上**（两本账之一：本账本或 tools/wds-mode.stamp）
 *      —— 这一条才是catch-all：新资产不登记就红，不必等下一次事故来提醒。
 *   ⑤ 账本里的 past 不复用（读者浏览器里可能还缓存着任何一个旧戳）
 *
 * 跑法：node tools/sim_asset_stamps.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const ROOT = path.join(__dirname, "..");
let pass = 0, fail = 0;
const ok = (n, c, d) => { if (c) { pass++; console.log("  ✓ " + n); } else { fail++; console.log("  ✗ " + n + (d ? ("  " + d) : "")); } };

const LEDGER = path.join(ROOT, "tools/asset-stamps.tsv");
ok("账本 tools/asset-stamps.tsv 在（没有它就说明从没跑过 bump_asset.py）", fs.existsSync(LEDGER));
if (!fs.existsSync(LEDGER)) { console.log("\n✗ 缺账本，无法继续"); process.exit(1); }

const rows = {};
for (const line of fs.readFileSync(LEDGER, "utf8").split("\n")) {
  if (!line.trim() || line.startsWith("#")) continue;
  const p = line.split("\t");
  if (p.length < 3) continue;
  rows[p[0]] = { stamp: p[1], sha: p[2], past: (p[3] || "").split(",").filter(Boolean) };
}
ok("账本里读得到资产（至少 10 个）", Object.keys(rows).length >= 10, "实得 " + Object.keys(rows).length);

/* /wds-mode.js 由另一本账单管；这里读它只为第 ④ 条"都必须在账上"用 */
const wmStamp = ((fs.readFileSync(path.join(ROOT, "tools/wds-mode.stamp"), "utf8")
  .match(/^stamp=(\S+)$/m) || [])[1]) || "";
ok("另一本账（tools/wds-mode.stamp）也读得到", !!wmStamp);

/* ② 哈希：从盘上真算，不手抄 */
{
  const bad = [];
  for (const a of Object.keys(rows)) {
    const disk = path.join(ROOT, "public", a.replace(/^\//, ""));
    if (!fs.existsSync(disk)) { bad.push(a + " 盘上没有"); continue; }
    const now = crypto.createHash("sha256").update(fs.readFileSync(disk)).digest("hex").slice(0, 16);
    if (now !== rows[a].sha) bad.push(a + "（记录 " + rows[a].sha + " / 实际 " + now + "）");
  }
  ok("每个资产的内容哈希与账本一致（不一致 ⇒ 改完忘了跑 tools/bump_asset.py）",
    bad.length === 0, bad.slice(0, 4).join(" / "));
}

/* ③④ 全仓库扫一遍引用 */
const PLACEHOLDER = /^(?:\{.*\}|__.*__|%[sd]|\$\{.*\})$/;
const REF = /((?:\/[A-Za-z0-9_.\-/]+\.(?:js|css))\?v=)([A-Za-z0-9_.\-%${}]+)/g;
const SKIP = ["tools/bump_wds_mode.py", "tools/bump_asset.py", "tools/wds-mode.stamp",
  "tools/asset-stamps.tsv", "tools/sim_wds_mode_stamp.js", "tools/sim_asset_stamps.js"];
/* 模拟脚本里的 `?v=` 是**测试夹具**，不是页面引用：sim 往一份假 HTML 里注一个 script 标签，
   跟"读者会拿到什么"毫无关系。扫 public/ 之外是为了逮住**生成器**（.py / .mjs / template.html），
   sim 不在此列。⚠ 这不是为了把红的变绿：夹具指向一个不存在的文件时，下面仍会单独报出来。 */
const isSim = (rel) => /^tools\/sim_[^/]*\.js$/.test(rel);
const seen = Object.create(null), simRefs = [];
(function walk(dir) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.name === ".git" || e.name === "node_modules") continue;
    const p = path.join(dir, e.name);
    if (e.isDirectory()) { walk(p); continue; }
    if (!/\.(html?|js|mjs|py|css)$/.test(e.name)) continue;
    const rel = path.relative(ROOT, p).split(path.sep).join("/");
    if (SKIP.indexOf(rel) >= 0) continue;
    if (isSim(rel)) { simRefs.push(rel); continue; }
    let s; try { s = fs.readFileSync(p, "utf8"); } catch (err) { continue; }
    let m; REF.lastIndex = 0;
    while ((m = REF.exec(s))) {
      const asset = m[1].slice(0, -"?v=".length);
      if (PLACEHOLDER.test(m[2])) continue;          // 运行时才填的占位符，不算引用
      (seen[asset] = seen[asset] || {})[m[2]] = (seen[asset][m[2]] || 0) + 1;
    }
  }
})(ROOT);

{
  const split = [], wrong = [];
  for (const a of Object.keys(rows)) {
    const st = Object.keys(seen[a] || {});
    if (st.length > 1) split.push(a + "：" + st.join("/"));
    else if (st.length === 1 && st[0] !== rows[a].stamp) wrong.push(a + " → " + st[0]);
  }
  ok("每个资产全站只有一种戳（多种 ⇒ 不同页面的读者拿到不同版本）", split.length === 0, split.slice(0, 4).join(" / "));
  ok("全站用的就是账本记的那个戳", wrong.length === 0, wrong.slice(0, 4).join(" / "));
}

/* ④ catch-all：任何带 ?v= 的资产都得在两本账之一上 */
{
  const orphan = Object.keys(seen).filter((a) => a !== "/wds-mode.js" && !rows[a]);
  if (orphan.length) console.log("     没登记的：" + orphan.slice(0, 6).join(" / "));
  ok("凡带 ?v= 的资产都在账上（新资产不登记就红，不必等下一次事故来提醒）", orphan.length === 0);
  ok("/wds-mode.js 确实由另一本账管着（不在本账本里重复管）",
    !rows["/wds-mode.js"] && Object.keys(seen["/wds-mode.js"] || {}).join() === wmStamp);
  ok("扫到的引用数量合理（>2000，防止 walk 因为路径写错只扫到几个就报绿）",
    Object.keys(seen).reduce((n, a) => n + Object.values(seen[a]).reduce((x, y) => x + y, 0), 0) > 2000);
}

/* ⑤ past 不复用 —— wds-mode 那边为此栽过一次（兜底交回了刚用过的那个戳） */
{
  let bad = 0;
  for (const a of Object.keys(rows)) {
    const p = rows[a].past;
    if (new Set(p).size !== p.length) bad++;
    if (p.indexOf(rows[a].stamp) < 0) bad++;
  }
  ok("账本里 past 无重复、且当前戳在 past 里", bad === 0);
}

/* 顺带：引用得到、盘上却没有的资产 —— 死引用，读者拿到 404 */
{
  const dead = Object.keys(seen).filter((a) => !fs.existsSync(path.join(ROOT, "public", a.replace(/^\//, ""))));
  if (dead.length) console.log("     ⚠ 引用得到但盘上没有：" + dead.join(" / "));
  ok("没有引用得到、盘上却没有的资产", dead.length === 0);
}

/* 顺带二：模拟脚本的夹具指向不存在的文件 —— 那份 sim 已经是死的（跑起来必然 readFileSync 抛错），
   它守的那件事其实一条都没在守。只报不红：删不删由人定，但账上要留一笔。 */
{
  const dead = [];
  for (const rel of simRefs) {
    const s2 = fs.readFileSync(path.join(ROOT, rel), "utf8");
    const R = /((?:\/[A-Za-z0-9_.\-/]+\.(?:js|css))\?v=)([A-Za-z0-9_.\-%${}]+)/g;
    let m;
    while ((m = R.exec(s2))) {
      const a = m[1].slice(0, -"?v=".length);
      if (!fs.existsSync(path.join(ROOT, "public", a.replace(/^\//, "")))) dead.push(rel + " → " + a);
    }
  }
  if (dead.length) console.log("     NOTE 夹具指向不存在的文件（那份 sim 已经是死的）：" + dead.join(" / "));
}

console.log("\n" + (fail ? "✗ " : "✓ ") + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
