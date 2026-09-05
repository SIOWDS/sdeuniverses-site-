/* sim_review_gen.js —— 综述论文生成器 v2（十道工序）的护栏
 *   规范层 tools/skills/sde-review-genesis.md
 *   ⓪ 解析 tools/skills/sde-review-writing.md §三 三张解构卡字段表 → 与 worker.js 的 REVIEW_CARD_FIELDS 逐条比对
 *   ① 解析 §五 三张章目表（序｜节名｜写什么｜字数）→ 与 REVIEW_SKELETON 逐节比对（节名一字不差、字数相等）
 *   ② 从 worker.js 真取常量跑（new Function），不手抄
 *   ③ 路由与页面的静态检查：端点串、四个 mode、页面引用的 id 全在
 * 跑法：node tools/sim_review_gen.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");
let pass = 0, fail = 0;
const ok = (n, c) => { if (c) { pass++; console.log("  ✓ " + n); } else { fail++; console.log("  ✗ " + n); } };

const WSRC = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");
const SKILL_P = path.join(ROOT, "tools/skills/sde-review-genesis.md");
ok("Skill 在仓库里", fs.existsSync(SKILL_P));
const SKILL = fs.existsSync(SKILL_P) ? fs.readFileSync(SKILL_P, "utf8") : "";

/* ═══ 从 worker.js 真取两个常量 ═══ */
console.log("── 机器层常量（从 worker.js 真取）──");
const mF = WSRC.match(/const REVIEW_CARD_FIELDS = (\{[\s\S]*?\n\});\n/);
const mS = WSRC.match(/const _RS_HEAD = (\[[\s\S]*?\n\]);\nconst _RS_TAIL = (\[[\s\S]*?\n\]);\nconst REVIEW_SKELETON = (\{[\s\S]*?\n\});\n/);
ok("抠得到 REVIEW_CARD_FIELDS", !!mF);
ok("抠得到 REVIEW_SKELETON", !!mS);
const FIELDS = mF ? new Function("return " + mF[1] + ";")() : {};
const SKEL = mS ? new Function("const _RS_HEAD=" + mS[1] + ";const _RS_TAIL=" + mS[2] + ";return " + mS[3] + ";")() : {};
const TYPES = ["what", "how", "why"];
ok("三类齐全", TYPES.every((t) => Array.isArray(FIELDS[t]) && Array.isArray(SKEL[t])));

/* ═══ Skill 工序④：三张卡的字段行 ═══ */
console.log("── 工序④ 解构卡字段 ↔ REVIEW_CARD_FIELDS ──");
const CARD_LINE = { what: /\*\*What-卡（\d+ 格）\*\*：([^\n]+)/, how: /\*\*How-卡（\d+ 格）\*\*：([^\n]+)/, why: /\*\*Why-卡（\d+ 格）\*\*：([^\n]+)/ };
TYPES.forEach((t) => {
  const m = SKILL.match(CARD_LINE[t]);
  const rows = m ? m[1].split("｜").map((x) => x.trim()).filter(Boolean) : [];
  ok(t + "：Skill 字段行解析到 " + rows.length + " 格", rows.length >= 9);
  ok(t + "：字段数 Skill==机器（" + rows.length + " vs " + FIELDS[t].length + "）", rows.length === FIELDS[t].length);
  ok(t + "：逐字段一字不差", rows.every((r, i) => FIELDS[t][i] === r));
});

/* ═══ Skill §10.1 之二：章目表 ═══ */
function sliceSec(startMark) {
  const a = SKILL.indexOf(startMark);
  if (a < 0) return "";
  const ends = ["\n#### ", "\n### ", "\n## "].map((m) => SKILL.indexOf(m, a + startMark.length)).filter((x) => x > 0);
  const end = ends.length ? Math.min.apply(null, ends) : SKILL.length;
  return SKILL.slice(a, end);
}

console.log("── §五 章目表 ↔ REVIEW_SKELETON ──");
const SKEL_MARK = { what: "#### What-综述", how: "#### How-综述", why: "#### Why-综述" };
TYPES.forEach((t) => {
  const src = sliceSec(SKEL_MARK[t]);
  const rows = [];
  src.split("\n").forEach((ln) => {
    const m = ln.match(/^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|/);
    if (m) rows.push({ n: +m[1], h: m[2], words: /^\d+$/.test(m[3]) ? +m[3] : 0 });
  });
  ok(t + "：Skill 章目表解析到 " + rows.length + " 行", rows.length >= 9);
  ok(t + "：序号连续", rows.every((r, i) => r.n === i + 1));
  ok(t + "：节数 Skill==机器（" + rows.length + " vs " + SKEL[t].length + "）", rows.length === SKEL[t].length);
  ok(t + "：逐节节名一字不差", rows.every((r, i) => SKEL[t][i] && SKEL[t][i].h === r.h));
  ok(t + "：逐节字数一一相等", rows.every((r, i) => SKEL[t][i] && SKEL[t][i].words === r.words));
  const total = SKEL[t].reduce((a, s) => a + s.words, 0);
  ok(t + "：合计 " + total + " 汉字落在 17000–20000", total >= 17000 && total <= 20000);
  ok(t + "：末节是参考文献且 words=0（页面端拼装）", SKEL[t][SKEL[t].length - 1].h === "参考文献" && SKEL[t][SKEL[t].length - 1].words === 0);
  ok(t + "：其余各节都有 ask", SKEL[t].slice(0, -1).every((s) => s.ask && s.ask.length > 10));
  ok(t + "：节名互不重复", new Set(SKEL[t].map((s) => s.h)).size === SKEL[t].length);
});

/* ═══ 路由静态检查 ═══ */
console.log("── 路由与页面 ──");
ok("worker.js 里有 /api/wds/review-gen 路由", WSRC.indexOf('url.pathname === "/api/wds/review-gen"') > 0);
["frame", "card", "map", "surface", "challenges", "gaps", "conjectures", "occupants", "write"].forEach((m) => ok("mode " + m + " 有分支", WSRC.indexOf('rmode === "' + m + '"') > 0));
ok("worker.js 写明权威出处", WSRC.indexOf("tools/skills/sde-review-genesis.md") > 0);
const PAGE_P = path.join(ROOT, "public/taste/review-gen/index.html");
ok("页面在仓库里", fs.existsSync(PAGE_P));
if (fs.existsSync(PAGE_P)) {
  const PG = fs.readFileSync(PAGE_P, "utf8");
  ok("页面指向端点", PG.indexOf("/api/wds/review-gen") > 0);
  const ids = new Set(); PG.replace(/id="([A-Za-z0-9_-]+)"/g, (_, i) => { ids.add(i); return _; });
  const used = new Set(); PG.replace(/\$\("#([A-Za-z0-9_-]+)"\)/g, (_, i) => { used.add(i); return _; });
  const miss = [...used].filter((i) => !ids.has(i));
  ok("页面脚本用到的 id 全部存在" + (miss.length ? "（缺 " + miss.join(",") + "）" : ""), miss.length === 0);
  // 页面里的章目表也必须是编译产物（客户端要按节名与 words=0 决定哪一节自己拼）
  const mP = PG.match(/var HEAD=(\[[^\n]*\]);\nvar TAIL=(\[[^\n]*\]);\nvar SKELETON=(\{[\s\S]*?\n\});/);
  ok("页面里抠得到 SKELETON", !!mP);
  if (mP) {
    const PS = new Function("var HEAD=" + mP[1] + ";var TAIL=" + mP[2] + ";return " + mP[3] + ";")();
    ok("页面 SKELETON 与机器逐节一致", TYPES.every((t) => PS[t] && PS[t].length === SKEL[t].length && PS[t].every((s, i) => s.h === SKEL[t][i].h && s.words === SKEL[t][i].words)));
  }
  ok("页面无 href=\"#\" 死链", !/href="#"/.test(PG));
}

console.log("\n" + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
