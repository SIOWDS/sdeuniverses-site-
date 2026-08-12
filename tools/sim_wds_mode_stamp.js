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


/* ═══ past 历史戳：它自己曾经是死的（2026-08-12）═══
   past 是防「戳退回去撞车」的机制，而它被写成
   `open(path,"w").write(... past_stamps() ...)` —— open("w") 在参数求值之前就把文件截断了，
   于是每次都只记下当前这一个戳，历史全丢。⚠ 这条机制自己犯了它要防的那个病。 */
{
  const bump = fs.readFileSync(path.join(ROOT, "tools/bump_wds_mode.py"), "utf8");
  ok("past 在打开写句柄之前就算完（不是在 write 的参数里算）",
    /past_line = /.test(bump) && bump.indexOf("past_line = ") < bump.indexOf('open(STAMP_FILE, "w"'));
  ok("写 stamp 文件用 with，不用 open(...).write(...) 这种一次性写法",
    /with open\(STAMP_FILE, "w"/.test(bump));
  const pastLine = (rec.match(/^past=(.*)$/m) || [, ""])[1];
  const pastList = pastLine.split(",").map((x) => x.trim()).filter(Boolean);
  ok("past 记着不止一个戳（只有一个 ⇒ 历史又被截掉了）", pastList.length >= 2);
  const curStamp = (rec.match(/^stamp=(\S+)$/m) || [, ""])[1];
  ok("当前戳在 past 里", !!curStamp && pastList.indexOf(curStamp) >= 0);
  ok("past 无重复", new Set(pastList).size === pastList.length);
}

/* 🔴 2026-08-12：一天改到第 27 次时，next_stamp 的兜底交回了**刚刚用过的那一个** ⇒
   全站 0 个文件被改写、戳不换、读者继续跑旧脚本，而脚本照常打印"戳已写入"、
   这份 sim 也照样全绿（它只核对戳与哈希自洽）。
   💡 心法：**兜底不许返回一个"可能已经用过"的值。** */
console.log("── 戳用完了 26 个字母之后 ──");
const BUMP = fs.readFileSync(path.join(ROOT, "tools/bump_wds_mode.py"), "utf8");
/* ⚠ 剥掉注释再查——注释里必然会引到那句旧代码（今天第五次踩它了）。 */
const BUMPBARE = BUMP.replace(/^\s*#.*$/gm, " ");
ok("★★ 兜底不再返回写死的末位字母（那多半正是刚用过的那一个）", BUMPBARE.indexOf('return base + "z"') < 0);
ok("★★ 字母用完往两位走", /for c2 in "abcdefghijklmnopqrstuvwxyz"/.test(BUMP) && /base \+ c \+ c2 not in used/.test(BUMP));
ok("★ 两位再用完挂时分秒，仍旧不重复", /strftime\("%H%M%S"\)/.test(BUMP));
ok("★★ past 里没有重复（用过的戳一个都不许再用）", (() => {
  const src = fs.readFileSync(path.join(ROOT, "tools/wds-mode.stamp"), "utf8");
  const m = src.match(/past=([^\n]*)/); if (!m) return false;
  const arr = m[1].split(",").map((x) => x.trim()).filter(Boolean);
  return arr.length > 1 && new Set(arr).size === arr.length;
})());
ok("注释写明了这条兜底当天真的撞上过", /2026-08-12 当天真的撞上了/.test(BUMP));

console.log("\n" + (fail ? "✗ " : "✓ ") + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
