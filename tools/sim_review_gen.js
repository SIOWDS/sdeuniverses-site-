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
    const m = ln.match(/^\|\s*(\d+(?:\s*之二|[AB])?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|/);
    if (m) rows.push({ n: m[1].replace(/\s+/g, ""), h: m[2], words: /^\d+$/.test(m[3]) ? +m[3] : 0 });
  });
  ok(t + "：Skill 章目表解析到 " + rows.length + " 行", rows.length >= 9);
  ok(t + "：序号连续（含 8 之二、9 之二、11A、11B）", rows.map((r) => String(r.n).replace(/\s+/g, "")).join(",") === ["1","2","3","4","5","6","7","8","8之二","9","9之二","10","11A","11B"].join(","));
  ok(t + "：节数 Skill==机器（" + rows.length + " vs " + SKEL[t].length + "）", rows.length === SKEL[t].length);
  ok(t + "：逐节节名一字不差", rows.every((r, i) => SKEL[t][i] && SKEL[t][i].h === r.h));
  ok(t + "：逐节字数一一相等", rows.every((r, i) => SKEL[t][i] && SKEL[t][i].words === r.words));
  const total = SKEL[t].reduce((a, s) => a + s.words, 0);
  ok(t + "：合计 " + total + " 汉字落在 22000–26500（v1.4.5 含 8 之二、9 之二）", total >= 22000 && total <= 26500);
  ok(t + "：末两节是 11A 核心语料／11B 敌拓与领地边界参考文献且 words=0（页面端拼装）", SKEL[t][SKEL[t].length - 2].h === "核心语料参考文献" && SKEL[t][SKEL[t].length - 1].h === "敌拓与领地边界参考文献" && SKEL[t].slice(-2).every((s) => s.words === 0));
  ok(t + "：其余各节都有 ask", SKEL[t].slice(0, -2).every((s) => s.ask && s.ask.length > 10));
  ok(t + "：节名互不重复", new Set(SKEL[t].map((s) => s.h)).size === SKEL[t].length);
});

/* ═══ 路由静态检查 ═══ */
console.log("── 路由与页面 ──");
ok("worker.js 里有 /api/wds/review-gen 路由", WSRC.indexOf('url.pathname === "/api/wds/review-gen"') > 0);
["frame", "card", "map", "neighbors", "verdict", "surface", "challenges", "gaps", "collide", "collide_run", "conjectures", "occupants", "territory", "territory_check", "write"].forEach((m) => ok("mode " + m + " 有分支", WSRC.indexOf('rmode === "' + m + '"') > 0));
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
  ok("页面有工序⑤之二敌拓闸阶段（neighbors/verdict）", PG.indexOf('mode:"neighbors"') > 0 && PG.indexOf('mode:"verdict"') > 0);
  ok("页面有 How-卡路径机检 routeCheck", PG.indexOf("function routeCheck(") > 0);
  ok("Skill 是 v1.4.5 且含⑤之二两道、⑧之二维度碰撞、典范判据、⑨之二新研究领地", /version:\s*1\.4\.5/.test(SKILL) && SKILL.indexOf("工序⑨之二 新研究领地发生") > 0 && SKILL.indexOf("典范判据") > 0 && SKILL.indexOf("工序⑤之二 敌拓闸") > 0 && SKILL.indexOf("第二道：按读数形状查对象词") > 0 && SKILL.indexOf("工序⑧之二 SDE 维度碰撞") > 0 && SKILL.indexOf("学科内") > 0);
  /* v1.4：⑧之二 学科内维度碰撞 */
  ok("collide 提示：三家取自清单内、不得同维、共有前提＝断链、六型对照、删维测试、碰撞挑战", /rmode === "collide"[\s\S]*?不得同维[\s\S]*?六型[\s\S]*?删维测试[\s\S]*?碰撞挑战/.test(WSRC));
  ok("collide_run 提示：判负照登、不得改口", /rmode === "collide_run"[\s\S]*?判负照登/.test(WSRC));
  ok("conjectures 带三档级别（典范／碰撞／改判）且 QUERIES 带 level", WSRC.indexOf("级别：典范级") > 0 && WSRC.indexOf("级别：碰撞级") > 0 && /\\"level\\"/.test(WSRC));
  ok("collide 提示含 v1.4.5 要素（How 主家／测量原语同构闸／借用／级别裁定／领地接口）", WSRC.indexOf("起手维等于落格路径落点维") > 0 && WSRC.indexOf("测量原语卡") > 0 && WSRC.indexOf("借用") > 0 && WSRC.indexOf("级别裁定") > 0 && WSRC.indexOf("领地接口") > 0);
  ok("worker territory 提示含四改／六族重绘／五问／退界／最高自判 T0；territory_check 含并入或退界与盲区", WSRC.indexOf("===TERRITORY===") > 0 && WSRC.indexOf("四项至少三项必须改写") > 0 && WSRC.indexOf("6 个族") > 0 && WSRC.indexOf("最高只能自判 T0") > 0 && WSRC.indexOf("并入该领域、改名或退界") > 0);
  ok("页面有 ⑨之二 阶段、runTerritory、11B 拼装 refsB", PG.indexOf('mode:"territory"') > 0 && PG.indexOf('mode:"territory_check"') > 0 && PG.indexOf("function runTerritory(") > 0 && PG.indexOf('data-s="territory"') > 0 && PG.indexOf("function refsB(") > 0);
  ok("conjectures 守恒式两边不同事件集", WSRC.indexOf("不同的事件集") > 0);
  ok("页面有 ⑧之二 阶段与 runCollide", PG.indexOf('mode:"collide"') > 0 && PG.indexOf('mode:"collide_run"') > 0 && PG.indexOf("function runCollide(") > 0 && PG.indexOf('data-s="collide"') > 0);
  ok("页面导出 md 含 ⑧之二", PG.indexOf("### ⑧之二 维度碰撞卡") > 0);
  /* v1.3：读数形状六型表 ↔ REVIEW_SHAPES */
  const mSh = WSRC.match(/const REVIEW_SHAPES = (\[[\s\S]*?\n\]);\n/);
  ok("抠得到 REVIEW_SHAPES", !!mSh);
  const SH = mSh ? new Function("return " + mSh[1] + ";")() : [];
  const shRows = []; sliceSec("| 读数形状 |").split("\n").forEach((ln) => { const m = ln.match(/^\|\s*\*\*([^*]+)\*\*\s*\|/); if (m) shRows.push(m[1].trim()); });
  ok("Skill 形状表解析到 " + shRows.length + " 型", shRows.length === 6);
  ok("形状名 Skill==机器逐行一字不差", shRows.length === SH.length && shRows.every((r, i) => SH[i] && SH[i].shape === r));
  ok("每型至少三个对象词", SH.every((x) => Array.isArray(x.words) && x.words.length >= 3));
  ok("worker 有 GET /api/wds/review-shapes", WSRC.indexOf('url.pathname === "/api/wds/review-shapes"') > 0);
  ok("conjectures 的 QUERIES 带 shape 与 freq", /\\"shape\\"/.test(WSRC) && /\\"freq\\"/.test(WSRC));
  ok("occupants 提示含撤下条件与检索盲区", WSRC.indexOf("撤下条件") > 0 && WSRC.indexOf("检索盲区") > 0);
  ok("页面三库实搜（searchCR/searchS2/loadShapes）", PG.indexOf("function searchCR(") > 0 && PG.indexOf("function searchS2(") > 0 && PG.indexOf("function loadShapes(") > 0 && PG.indexOf("/api/wds/review-shapes") > 0);
  ok("页面自检 28 项", PG.indexOf("自检 28 项") > 0 && (PG.match(/out\.push\(\{n:/g) || []).length === 28);
  ok("worker 占位者栏只引⑤之二（prompt 里有三判）", WSRC.indexOf("只许引给定的敌拓闸三判结果") > 0);
}

console.log("\n" + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
