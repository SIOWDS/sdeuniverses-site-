/* sim_tool_registry.js —— 工序注册表三处对账（2026-09-08）
 *
 * 缘起：加一道工序要在**三处**同时落地——① WDS_TOOLS 里的提示语正文；
 * ② WDS_TOOL_KEYS 白名单（后端唯一准入口）；③ 前端菜单 TOOLS 表。
 * 少了 ②，症状是**菜单点得到、后端认不出**：tool 被判成空串，工序 system 一个字都挂不上，
 * 而答案照样通顺——没有任何人会发现。
 *
 * 🔴 这不是假想：2026-09-08 上午上线的三道问对（whatq/howq/whyq）就漏了 ②，
 * 从头到尾没生效；那条线自己的 43 项护栏全绿也没抓住，因为它们抠的是 WDS_TOOLS 与
 * posNext，不走白名单这条路。同日做「九问专著」时才发现。
 *
 * 这份护栏只做一件事：三处逐键对账，任一处缺就红。
 *
 * 跑法：node tools/sim_tool_registry.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");
let pass = 0, fail = 0;
const ok = (n, c) => { if (c) { pass++; } else { fail++; console.log("  ✗ " + n); } };

const W = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");
const F = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");

/* ① WDS_TOOLS 正文的键（顶层 `  xxx: "` 开头那一批） */
const i0 = W.indexOf("const WDS_TOOLS = {");
const i1 = W.indexOf("\nconst WDS_TOOLS_LANG");
ok("抠得到 WDS_TOOLS 段", i0 > 0 && i1 > i0);
const BODY = W.slice(i0, i1);
const tools = (BODY.match(/^  ([a-z][a-z0-9]*): "/gm) || []).map(s => s.trim().replace(/: "$/, ""));
ok("WDS_TOOLS 里至少 15 道", tools.length >= 15);

/* ② 白名单 */
const mw = /const WDS_TOOL_KEYS = \[([^\]]*)\]/.exec(W);
ok("抠得到 WDS_TOOL_KEYS", !!mw);
const keys = mw ? mw[1].split(",").map(s => s.trim().replace(/^"|"$/g, "")).filter(Boolean) : [];

/* ③ 前端菜单 */
const front = (F.match(/\{ k: "([a-z0-9]+)", n: "tl/g) || []).map(s => /\{ k: "([a-z0-9]+)"/.exec(s)[1]);
ok("抠得到前端菜单表", front.length >= 15);

/* ── 逐键对账：三处必须完全一致 ── */
const missWl = tools.filter(k => keys.indexOf(k) < 0);
ok("WDS_TOOLS 的每一道都在白名单里" + (missWl.length ? "（缺：" + missWl.join("、") + "）" : ""), !missWl.length);
const missTool = keys.filter(k => tools.indexOf(k) < 0);
ok("白名单里没有空头键" + (missTool.length ? "（多：" + missTool.join("、") + "）" : ""), !missTool.length);
const missFront = tools.filter(k => front.indexOf(k) < 0);
ok("WDS_TOOLS 的每一道前端菜单都挂了" + (missFront.length ? "（缺：" + missFront.join("、") + "）" : ""), !missFront.length);
const ghost = front.filter(k => keys.indexOf(k) < 0);
ok("前端菜单里没有后端认不出的键" + (ghost.length ? "（幽灵：" + ghost.join("、") + "）" : ""), !ghost.length);

/* ── 白名单确实是准入口（改了这一句，上面的对账就白做了）── */
ok("tool 由白名单判定（indexOf 校验还在）", /WDS_TOOL_KEYS\.indexOf\(String\(b\.tool/.test(W));

/* ── 九问专著：这一次新加的那道，三处逐一钉死 ── */
ok("book9 · WDS_TOOLS 有正文", tools.indexOf("book9") >= 0);
ok("book9 · 在白名单里", keys.indexOf("book9") >= 0);
ok("book9 · 前端菜单挂了", front.indexOf("book9") >= 0);
ok("book9 · 前端有中文名与说明", /tlBook9: "九问专著"/.test(F) && /tlBook9S: "/.test(F));
ok("book9 · 前端有英文名", /tlBook9: "Nine-question monograph"/.test(F));
ok("book9 · 斜杠命令带「九问专著」与「立题书」", /cmd: \["九问专著", "book9", "专著", "立题书"\]/.test(F));

/* ── 三道问对：这次一并补进白名单，钉住别再掉出去 ── */
["whatq", "howq", "whyq"].forEach(k => ok("三道问对 · " + k + " 在白名单里", keys.indexOf(k) >= 0));

/* ── 机检面：book9 的两行必须在 TOOL_SPEC 里 ── */
const spec = /  book9: \{ min: \d+, items: \[([\s\S]*?)\] \},/.exec(W);
ok("book9 · TOOL_SPEC 有条目", !!spec);
if (spec) {
  ok("book9 · 机检面要〔本篇边界〕", /本篇边界/.test(spec[1]));
  ok("book9 · 机检面要〔落位〕", /落位/.test(spec[1]));
  ok("book9 · 机检面要报题号（W1…Y3）", /\[WHY\]\[123\]/.test(spec[1]));
}

/* ── 接力：book9 的列由题号决定，不预设 ── */
ok("book9 · _rungOf 里不筛列（posFromHistory(history, null)）",
   /if \(tool === "book9"\) return posNext\(posFromHistory\(history, null\)\);/.test(W));

/* ── 正文里那几条边界（这一道存在的理由，删了就退化成普通问对）── */
const b9 = /  book9: "([\s\S]*?)\n\n  [a-z]/.exec(BODY);
const T = b9 ? b9[1] : (BODY.slice(BODY.indexOf("  book9:"), BODY.indexOf("  book9:") + 4000));
ok("book9 正文 · 只写一题", /只写本题/.test(T));
ok("book9 正文 · 别题靶位是禁区", /禁区/.test(T));
ok("book9 正文 · 本篇不管什么", /本篇不管/.test(T));
ok("book9 正文 · 一符一义", /一符一义/.test(T));
ok("book9 正文 · 占位者接着往下切", /接着往下切/.test(T));
ok("book9 正文 · 没有立题书就先停下来要", /先停下来要/.test(T));
ok("book9 正文 · 列由题号决定（三列都写明）", /三方程/.test(T) && /六路径/.test(T) && /三原理/.test(T));

console.log((fail ? "✗" : "✓") + " sim_tool_registry: " + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
