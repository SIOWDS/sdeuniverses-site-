/* bench_report.js —— 同题基准的「算」这一半（建议书 §15.3／§15.4）
 *
 * 这个文件只做一件事：把 runs.jsonl ＋ scores.jsonl 算成一张**能被别人复核**的表。
 * 它不下判断、不粉饰、不挑对自己有利的口径。三条纪律：
 *  · **ΔIQ 一律以 bare 为分母**（同一家、同一型号、零提示语）。
 *    换任何别的分母都会把"这家基底行不行"混进"这套方法有没有用"里。
 *  · **失败的格子进完成率，不进均值**。把跑失败的那些悄悄丢掉，均值会自己往上飘——
 *    一条长流程越容易断，被丢掉的就越多，剩下的就越好看。这是最容易骗到自己的一处。
 *  · **达标与否照实写**。§15.4：没达标就报真实结果、回到失败的那一维去修，
 *    **不许调评分提示制造更高分**。
 *
 * 跑法：node tools/bench_report.js [--md 报告.md]
 */
"use strict";
const fs = require("fs"), path = require("path");
const RUNS = path.join(__dirname, "bench", "runs");
function arg(k, d) { const i = process.argv.indexOf("--" + k); return i > 0 && process.argv[i + 1] ? process.argv[i + 1] : d; }

const DIMS = ["S", "D", "E", "I", "F"];
const W = { S: 0.20, D: 0.25, E: 0.20, I: 0.20, F: 0.15 };
/* 与站内评分同一把尺：I 或 F 塌到 120 以下，综合分封顶 145。
   ⚠ 这一条必须在**这里**再算一遍，不能信评分者自报的 iq——
   它偶尔会忘了套闸门，而闸门正是这把尺子最不该被绕过的地方。 */
function iqOf(s) {
  let v = 0; for (const d of DIMS) v += W[d] * num(s[d]);
  if (num(s.I) < 120 || num(s.F) < 120) v = Math.min(v, 145);
  return Math.round(v * 10) / 10;
}
function num(x) { const v = (x && typeof x === "object") ? x.v : x; const n = parseFloat(v); return isFinite(n) ? n : 0; }
function mean(a) { return a.length ? a.reduce((x, y) => x + y, 0) / a.length : 0; }
function sd(a) { if (a.length < 2) return 0; const m = mean(a); return Math.sqrt(mean(a.map((x) => (x - m) * (x - m)))); }
function med(a) { if (!a.length) return 0; const b = a.slice().sort((x, y) => x - y); const i = b.length >> 1;
  return b.length % 2 ? b[i] : (b[i - 1] + b[i]) / 2; }
function r1(x) { return Math.round(x * 10) / 10; }

/* ⚠ 汇总单独抽成函数，是为了让护栏能**真跑**它。
   教训：第一版护栏查的是源码串 `armCells[r.arm] = ...`，
   而把它改成 `if (r.ok) armCells[r.arm] = ...` 之后**那条串仍在**、断言照样绿，
   可完成率已经从 78% 变成 100%（失败的格子被踢出了分母）。
   💡 心法：**"有没有做某件事"用源码串查得出，"做对没做对"只有真跑查得出。** */
function aggregate(runs, scores, km) {
  const armCells = {}, armOk = {}, armMs = {}, armChars = {}, armTok = {};
  runs.forEach((r) => {
    armCells[r.arm] = (armCells[r.arm] || 0) + 1;          // 分母＝计划跑的格子，失败的也算
    if (r.ok) { armOk[r.arm] = (armOk[r.arm] || 0) + 1;
      (armMs[r.arm] = armMs[r.arm] || []).push(r.ms || 0);
      (armChars[r.arm] = armChars[r.arm] || []).push(r.chars || 0);
      const u = r.usage || {}; if (u.total_tokens) (armTok[r.arm] = armTok[r.arm] || []).push(u.total_tokens); }
  });
  const byAnon = {};
  scores.forEach((s) => { if (!s.ok || !s.score) return; (byAnon[s.anon] = byAnon[s.anon] || []).push(s); });
  const perDoc = [];
  Object.keys(byAnon).forEach((a) => {
    const k = km[a]; if (!k) return;
    const js = byAnon[a];
    const iqs = js.map((x) => iqOf(x.score));
    const dim = {}; DIMS.forEach((d) => { dim[d] = mean(js.map((x) => num(x.score[d]))); });
    const evOk = js.filter((x) => x.score.evidence_ok === true).length;
    perDoc.push({ anon: a, q: k.q, arm: k.arm, rep: k.rep, iq: mean(iqs),
      spread: (Math.max.apply(null, iqs) - Math.min.apply(null, iqs)),
      dim: dim, judges: js.length, evOk: evOk, hiNoEv: (mean(iqs) >= 140 && evOk === 0) ? 1 : 0 });
  });
  const arms = Array.from(new Set(perDoc.map((d) => d.arm)));
  const A = {};
  arms.forEach((arm) => {
    const ds = perDoc.filter((d) => d.arm === arm);
    const dim = {}; DIMS.forEach((d) => { dim[d] = mean(ds.map((x) => x.dim[d])); });
    A[arm] = { n: ds.length, iq: mean(ds.map((d) => d.iq)), sd: sd(ds.map((d) => d.iq)),
      med: med(ds.map((d) => d.iq)), dim: dim, spread: mean(ds.map((d) => d.spread)),
      hiNoEv: ds.filter((d) => d.hiNoEv).length,
      done: (armOk[arm] || 0) + "/" + (armCells[arm] || 0),
      doneRate: armCells[arm] ? (armOk[arm] || 0) / armCells[arm] : 0,
      ms: mean(armMs[arm] || []), chars: mean(armChars[arm] || []), tok: mean(armTok[arm] || []) };
  });
  return { A: A, perDoc: perDoc, arms: arms };
}

function main() {
  const runsF = path.join(RUNS, "runs.jsonl"), scF = path.join(RUNS, "scores.jsonl"), kmF = path.join(RUNS, "keymap.json");
  for (const f of [runsF, scF, kmF]) if (!fs.existsSync(f)) { console.error("缺 " + path.basename(f) + "，先把跑与评做完。"); process.exit(1); }
  const jl = (f) => fs.readFileSync(f, "utf8").split("\n").filter(Boolean).map((l) => { try { return JSON.parse(l); } catch (e) { return null; } }).filter(Boolean);
  const runs = jl(runsF), scores = jl(scF);
  const km = {}; JSON.parse(fs.readFileSync(kmF, "utf8")).forEach((x) => { km[x.anon] = x; });
  const snap = fs.existsSync(path.join(RUNS, "manifest.json")) ? JSON.parse(fs.readFileSync(path.join(RUNS, "manifest.json"), "utf8")) : {};

  const { A, perDoc, arms } = aggregate(runs, scores, km);

  const L = [];
  L.push("# 同题基准读数");
  L.push("");
  L.push("> 口径快照：基底 " + (snap.vendor || "?") + " / " + (snap.model || "?")
    + "　worker " + (snap.worker_sha || "?") + "　wds-mode " + (snap.wdsmode_sha || "?")
    + "　跑于 " + (snap.at || "?"));
  L.push("> 评分者 " + (perDoc[0] ? perDoc[0].judges : 0) + " 位／份。**ΔIQ 一律以 bare（同一家、零提示语）为分母。**");
  L.push("");
  L.push("| 臂 | 说明 | n | 综合分均值 | 标准差 | 中位数 | ΔIQ | 完成率 | 评分者最大分歧 | 无外部证据却给了高分 |");
  L.push("|---|---|---|---|---|---|---|---|---|---|");
  const baseIq = A.bare ? A.bare.iq : null;
  const doc = { bare: "同基底裸调用（分母）", std: "标准档", deep: "深度档", forge: "完整通融（十八道）" };
  ["bare", "std", "deep", "forge"].concat(arms).filter((x, i, s) => A[x] && s.indexOf(x) === i).forEach((arm) => {
    const a = A[arm];
    L.push("| " + arm + " | " + (doc[arm] || "") + " | " + a.n + " | " + r1(a.iq) + " | " + r1(a.sd) + " | " + r1(a.med)
      + " | " + (baseIq === null || arm === "bare" ? "—" : (r1(a.iq - baseIq) > 0 ? "+" : "") + r1(a.iq - baseIq))
      + " | " + a.done + "（" + Math.round(a.doneRate * 100) + "%）"
      + " | " + r1(a.spread) + " | " + a.hiNoEv + " |");
  });
  L.push("");
  L.push("## 每维增益（相对 bare）");
  L.push("");
  L.push("| 臂 | " + DIMS.join(" | ") + " |");
  L.push("|---|" + DIMS.map(() => "---").join("|") + "|");
  arms.forEach((arm) => {
    if (arm === "bare" || !A.bare) return;
    L.push("| " + arm + " | " + DIMS.map((d) => {
      const v = A[arm].dim[d] - A.bare.dim[d];
      return (v > 0 ? "+" : "") + r1(v);
    }).join(" | ") + " |");
  });
  L.push("");
  L.push("## 成本与时间");
  L.push("");
  L.push("| 臂 | 平均耗时 | 平均字数 | 平均 token |");
  L.push("|---|---|---|---|");
  arms.forEach((arm) => L.push("| " + arm + " | " + r1(A[arm].ms / 1000) + "s | " + Math.round(A[arm].chars)
    + " | " + (A[arm].tok ? Math.round(A[arm].tok) : "—") + " |"));

  /* ④ 对着建议书 §15.4 那几条验收目标逐条判。**没达标就写没达标。** */
  L.push("");
  L.push("## 验收目标逐条（建议书 §15.4）");
  L.push("");
  const chk = [];
  const dIq = (arm) => (A[arm] && A.bare) ? (A[arm].iq - A.bare.iq) : null;
  chk.push(["深度档相对同基底 ≥ +10", dIq("deep"), (v) => v !== null && v >= 10]);
  chk.push(["完整通融相对同基底 ≥ +15", dIq("forge"), (v) => v !== null && v >= 15]);
  ["I", "F"].forEach((d) => chk.push(["深度档 " + d + " 维 ≥ +8",
    (A.deep && A.bare) ? (A.deep.dim[d] - A.bare.dim[d]) : null, (v) => v !== null && v >= 8]));
  chk.push(["长流程完成率 ≥ 95%", A.forge ? A.forge.doneRate * 100 : null, (v) => v !== null && v >= 95]);
  chk.push(["外部近邻无法核验时高分率 = 0", perDoc.filter((d) => d.hiNoEv).length, (v) => v === 0]);
  chk.forEach((c) => {
    const v = c[1], pass = v === null ? null : c[2](v);
    L.push("- " + (pass === null ? "○ 未测" : pass ? "✅" : "❌") + " " + c[0]
      + "：" + (v === null ? "这一批里没有这一臂的数据" : r1(v)));
  });
  L.push("");
  L.push("> ⚠ 没达标就是没达标。**回到失败的那一维去修，不许调评分提示制造更高分**（§15.4）。");
  L.push("> 单次实验只是一个读数，不是结论；换一批题、换一家评分者再跑一次，差多少要如实记下来。");

  const out = L.join("\n") + "\n";
  const md = arg("md", "");
  if (md) { fs.writeFileSync(md, out); console.log("已写 " + md); } else console.log(out);
}
if (require.main === module) main();
module.exports = { aggregate: aggregate, iqOf: iqOf, mean: mean, sd: sd, med: med, W: W, DIMS: DIMS };
