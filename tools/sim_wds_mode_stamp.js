/* sim_wds_mode_stamp.js —— 「线上是新的、读者拿到的是旧的」这一类静默失效的护栏
 *
 * 2026-08-12 的血案：wds-mode.js 当天改了四轮并四次构建成功，而全站 4016 个页面引的
 * 都是 `/wds-mode.js?v=20260808a`——四天没动过。URL 不变，读者标签页里那份旧脚本就一直用着：
 * 短产出重试没上、白屏自愈没上、PDF 按钮压根不存在。
 * **构建是绿的、线上文件是新的、所有 sim 也是绿的，唯独读者拿到的是旧的。**
 * 这条链上原来一个检查点都没有，本文件就是那个检查点。
 *
 * 查三件：① 记录的哈希与 wds-mode.js 当前内容一致（不一致 ⇒ 改完没跑 bump 工具）
 *         ② 全站引用的戳与记录的戳一致（不一致 ⇒ 漏改了页面）
 *         ③ 全站只有一种戳（历史上同时存在过三种，等于三批读者拿三个版本）
 * 跑法：node tools/sim_wds_mode_stamp.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const ROOT = path.join(__dirname, "..");
let pass = 0, fail = 0;
const ok = (n, c) => { if (c) { pass++; console.log("  ✓ " + n); } else { fail++; console.log("  ✗ " + n); } };

const JS = path.join(ROOT, "public/wds-mode.js");
const STAMP = path.join(ROOT, "tools/wds-mode.stamp");
ok("wds-mode.js 在", fs.existsSync(JS));
ok("tools/wds-mode.stamp 在（没有它就说明从没跑过 bump 工具）", fs.existsSync(STAMP));
if (!fs.existsSync(JS) || !fs.existsSync(STAMP)) { console.log("\n✗ 缺文件，无法继续"); process.exit(1); }

const rec = fs.readFileSync(STAMP, "utf8");
const wantStamp = (rec.match(/^stamp=(\S+)$/m) || [])[1];
const wantSha = (rec.match(/^sha256=(\S+)$/m) || [])[1];
ok("stamp 文件里读得到 stamp 与 sha256 两行", !!wantStamp && !!wantSha);

/* ① 哈希：从文件真算，不手抄 */
const nowSha = crypto.createHash("sha256").update(fs.readFileSync(JS)).digest("hex").slice(0, 16);
ok("wds-mode.js 的内容哈希与记录一致（不一致 ⇒ 改完忘了跑 tools/bump_wds_mode.py，"
   + "读者会继续拿旧脚本）—— 记录 " + wantSha + " / 实际 " + nowSha, nowSha === wantSha);

/* ②③ 全站引用 */
const REF = /\/wds-mode\.js\?v=([A-Za-z0-9_.-]+)/g;
const seen = Object.create(null);
let refFiles = 0, badFiles = [];
(function walk(dir) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.name === ".git" || e.name === "node_modules") continue;
    const p = path.join(dir, e.name);
    if (e.isDirectory()) { walk(p); continue; }
    if (!/\.(html?|js)$/.test(e.name)) continue;
    let s; try { s = fs.readFileSync(p, "utf8"); } catch (err) { continue; }
    let m, hit = false, bad = false;
    REF.lastIndex = 0;
    while ((m = REF.exec(s))) {
      hit = true;
      seen[m[1]] = (seen[m[1]] || 0) + 1;
      if (m[1] !== wantStamp) bad = true;
    }
    if (hit) refFiles++;
    if (bad) badFiles.push(path.relative(ROOT, p));
  }
})(path.join(ROOT, "public"));

const stamps = Object.keys(seen);
console.log("     引用页面 " + refFiles + " 个 · 戳分布 " + stamps.map((k) => k + "×" + seen[k]).join(", "));
ok("全站只有一种版本戳（多种 ⇒ 不同页面的读者拿到不同版本的脚本）", stamps.length === 1);
ok("全站用的就是记录里那个戳（" + wantStamp + "）",
  stamps.length === 1 && stamps[0] === wantStamp);
if (badFiles.length) console.log("     对不上的前几个：" + badFiles.slice(0, 5).join(" / "));
ok("引用页面数量合理（>1000，防止 walk 因为路径写错只扫到几个就报绿）", refFiles > 1000);

/* 顺带：按需装载的那几个模块，各自的 *_WANT 必须与模块自报 VERSION 对齐——同一类病 */
const FS2 = fs.readFileSync(JS, "utf8");
[["PDF_WANT", "public/assets/wds-pdf.js"], ["PPTX_WANT", "public/assets/wds-pptx.js"]]
  .forEach(([key, mod]) => {
    const want = +((FS2.match(new RegExp("var " + key + " = (\\d+);")) || [])[1] || -1);
    const p = path.join(ROOT, mod);
    if (!fs.existsSync(p)) { ok(key + " 对应的模块在", false); return; }
    const ver = +((fs.readFileSync(p, "utf8").match(/var VERSION = (\d+);/) || [])[1] || -2);
    ok(key + " 与 " + path.basename(mod) + " 的 VERSION 对齐（" + want + " vs " + ver + "）", want === ver);
  });

console.log("\n" + (fail ? "✗ " : "✓ ") + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
