/* 工序交付率量具：tools/bench_tools.js（2026-08-28）
 *
 * 它回答的是这条产线上**唯一还没有读数的那个问题**：规格与审计都验过了，
 * 可是**基底照不照做**？此前所有断言证的都是「审计判得准」，一次真调用都没有。
 *
 * 与 bench_run.js 分工：那台量的是 ΔIQ（bare/std/deep 三臂 × 30 题 × 3 次），
 * 它**没有工序臂**，量不到交付。这一台量的就是交付：十五道工序 × 若干题，
 * 每答一次就拿服务端那份 TOOL_SPEC 逐件扫，出一张「哪一道最常漏哪一件」的表。
 *
 * 三条纪律（都写在建议书 §14.6／§15 里，这里照办）：
 *   ① **不擅自烧 Key**：没有 WDS_KEY 就只打印计划，一分钱不动。
 *   ② **走真正的那条路**：打线上 /api/wds/chat，不在本地重拼一份提示语——
 *      另拼一份测到的是读者永远走不到的路（本仓栽过，见 forge 那条 P0 空转）。
 *   ③ **失败留在分母里**：报错的格子照记，完成率不许把它们悄悄摘掉。
 *
 * 用法：
 *   node tools/bench_tools.js --dry                 只算不跑
 *   node tools/bench_tools.js --mock                拿本地假上游跑一遍（验管道，不烧钱）
 *   WDS_KEY=sk-… WDS_VENDOR=ds node tools/bench_tools.js --n 2
 *   参数：--n <每道几题，默认 2> --tools <逗号分隔，默认全部> --base <站点地址>
 */
"use strict";
const fs = require("fs");
const path = require("path");
const http = require("http");

const ARGV = process.argv.slice(2);
function opt(k, d) { const i = ARGV.indexOf("--" + k); return i >= 0 ? ARGV[i + 1] : d; }
const DRY = ARGV.includes("--dry"), MOCK = ARGV.includes("--mock");
const PER = Math.max(1, parseInt(opt("n", "2"), 10));
const BASE = opt("base", MOCK ? "" : "https://sdeuniverses.com");
const KEY = process.env.WDS_KEY || "";
const VENDOR = process.env.WDS_VENDOR || "ds";
const DEEP = ARGV.includes("--deep");

/* ── 规格与审计：都从源码抠，绝不在这里复制一份 ── */
const W = fs.readFileSync("src/worker.js", "utf8");
const F = fs.readFileSync("public/wds-mode.js", "utf8");
const _a = W.indexOf("const _LN = "), _b = W.indexOf("\nfunction wdsToolSys(tool, prof) {");
const _c = W.indexOf("\n// RESEARCH_STEP", _b), _n = W.indexOf("const NINE_CELLS = {");
const S = new Function(W.slice(_n, _a) + W.slice(_a, _c) + "\nreturn { TOOL_SPEC, toolSpecFor };")();
const _fa = F.indexOf("  function toolAudit(text, spec) {"), _fb = F.indexOf("  function toolAuditRender(cell, text, spec) {");
const FE = new Function(F.slice(_fa, _fb) + "\nreturn { toolAudit };")();

const KEYS = Object.keys(S.TOOL_SPEC);
const TOOLS = (opt("tools", "") ? opt("tools").split(",") : KEYS).filter((k) => S.TOOL_SPEC[k]);
const QS = JSON.parse(fs.readFileSync("tools/bench/questions.json", "utf8")).items;

/* 题目按类型配工序：what 题去问 what 那一道才公平，
   不配型的（改姓/评分/近邻这些对材料的工序）一律用通用那几题。 */
const BYTYPE = { what: [], how: [], why: [] };
QS.forEach((q) => { const t = q.tags && q.tags.type; if (BYTYPE[t]) BYTYPE[t].push(q); });
function qsFor(tool) {
  const pool = BYTYPE[tool] && BYTYPE[tool].length ? BYTYPE[tool] : QS;
  return pool.slice(0, PER);
}

const CELLS = [];
TOOLS.forEach((t) => qsFor(t).forEach((q) => CELLS.push({ tool: t, qid: q.id, q: q.q })));

console.log("工序 " + TOOLS.length + " 道 × 每道 " + PER + " 题 ＝ " + CELLS.length + " 次调用"
  + (DEEP ? "（深度档）" : "（标准档）") + "；基底 " + VENDOR + "，站点 " + (BASE || "本地假上游"));
if (DRY) { console.log("（--dry：只算不跑）"); process.exit(0); }
if (!KEY && !MOCK) {
  console.log("没有 WDS_KEY，不跑——这一台烧的是你自己的 Key，不许替你决定。");
  console.log("要跑：WDS_KEY=<你的 Key> WDS_VENDOR=ds node tools/bench_tools.js --n 2");
  process.exit(2);
}

/* ── 假上游：只为验管道（SSE 解析、审计、汇总、失败计入分母），不产生任何可引用的读数 ── */
function mockServer() {
  return new Promise((res) => {
    const srv = http.createServer((req, rs) => {
      let body = ""; req.on("data", (d) => { body += d; });
      req.on("end", () => {
        const b = JSON.parse(body || "{}");
        rs.writeHead(200, { "content-type": "text/event-stream" });
        // 一半的格子故意只交一半，另有一格直接报错——汇总必须如实反映这三种
        if (b.tool === "gap") { rs.write("data: " + JSON.stringify({ t: "error", v: "假上游：这一格故意失败" }) + "\n\n"); rs.end(); return; }
        const spec = S.TOOL_SPEC[b.tool];
        const half = (b.q || "").indexOf("沉默") >= 0;
        const items = half ? spec.items.slice(0, Math.ceil(spec.items.length / 2)) : spec.items;
        let txt = items.map((it) => "· " + it.k + "：" + "内容内容内容内容内容内容内容。").join("\n");
        while (txt.length < spec.min + 20) txt += "\n补白补白补白补白补白补白补白补白补白补白。";
        rs.write("data: " + JSON.stringify({ t: "toolspec", v: S.toolSpecFor(b.tool, "zh") }) + "\n\n");
        for (const ch of txt.match(/.{1,60}/g)) rs.write("data: " + JSON.stringify({ t: "token", v: ch }) + "\n\n");
        rs.end();
      });
    });
    srv.listen(0, () => res({ srv, url: "http://127.0.0.1:" + srv.address().port }));
  });
}

async function askOne(base, cell) {
  const body = { q: cell.q, key: KEY || "mock-key-0000", vendor: VENDOR, tool: cell.tool, mode: DEEP ? "deep" : "std", lang: "zh" };
  const t0 = Date.now();
  let text = "", spec = null, err = "";
  try {
    const r = await fetch(base + "/api/wds/chat", {
      method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body),
    });
    if (!r.ok) return { ...cell, ok: false, err: "HTTP " + r.status, ms: Date.now() - t0 };
    const rd = r.body.getReader(), dec = new TextDecoder();
    let buf = "";
    for (;;) {
      const { done, value } = await rd.read(); if (done) break;
      buf += dec.decode(value, { stream: true });
      let i;
      while ((i = buf.indexOf("\n")) >= 0) {
        const line = buf.slice(0, i).trim(); buf = buf.slice(i + 1);
        if (!line.startsWith("data:")) continue;
        let j; try { j = JSON.parse(line.slice(5).trim()); } catch (e) { continue; }
        if (j.t === "token") text += j.v;
        else if (j.t === "toolspec") spec = j.v;
        else if (j.t === "error") err = String(j.v).slice(0, 120);
      }
    }
  } catch (e) { err = (e && e.message) || "调用异常"; }
  if (err && !text) return { ...cell, ok: false, err: err, ms: Date.now() - t0 };
  /* 用**服务端下发的那一份**规格审计（不是本地那份）——读者页面上判的就是它。
     没下发（老版本）才退回本地，并如实标出来。 */
  const used = spec || S.toolSpecFor(cell.tool, "zh");
  const a = FE.toolAudit(text, used);
  return { ...cell, ok: true, specFrom: spec ? "server" : "local", len: a.len, min: a.min,
    done: a.done, total: a.total, miss: a.miss, short: !!(a.min && a.len < a.min * 0.7),
    err: err, ms: Date.now() - t0, head: text.slice(0, 80) };
}

(async function main() {
  let base = BASE, srv = null;
  if (MOCK) { const m = await mockServer(); base = m.url; srv = m.srv; }
  const out = [];
  for (const cell of CELLS) {
    const r = await askOne(base, cell);
    out.push(r);
    console.log((r.ok ? "  " : "✗ ") + cell.tool.padEnd(8) + cell.qid
      + (r.ok ? ("  交付 " + r.done + "/" + r.total + (r.short ? " · 篇幅不足" : "") + (r.miss.length ? "  缺：" + r.miss.join("、") : ""))
              : ("  失败：" + r.err)));
  }
  if (srv) srv.close();

  console.log("\n── 逐道交付率（失败的格子留在分母里）──");
  const rows = [];
  TOOLS.forEach((t) => {
    const g = out.filter((x) => x.tool === t);
    const okg = g.filter((x) => x.ok);
    const rate = okg.length ? okg.reduce((s, x) => s + x.done / x.total, 0) / g.length : 0;
    const missCount = {};
    okg.forEach((x) => x.miss.forEach((m) => { missCount[m] = (missCount[m] || 0) + 1; }));
    const worst = Object.keys(missCount).sort((a, b) => missCount[b] - missCount[a])[0] || "";
    rows.push({ tool: t, n: g.length, fail: g.length - okg.length, rate: rate,
      short: okg.filter((x) => x.short).length, worst: worst ? (worst + " ×" + missCount[worst]) : "—" });
    console.log("  " + t.padEnd(8) + " 交付率 " + (rate * 100).toFixed(0).padStart(3) + "%"
      + " · 失败 " + (g.length - okg.length) + "/" + g.length
      + " · 篇幅不足 " + okg.filter((x) => x.short).length
      + " · 最常漏：" + (worst ? worst + " ×" + missCount[worst] : "—"));
  });
  const all = out.filter((x) => x.ok);
  console.log("\n全批：调用 " + out.length + " · 成功 " + all.length
    + " · 平均交付率 " + (all.reduce((s, x) => s + x.done / x.total, 0) / out.length * 100).toFixed(0) + "%"
    + (MOCK ? "（--mock 假上游，不是可引用的读数）" : ""));

  const dir = "tools/bench/runs";
  fs.mkdirSync(dir, { recursive: true });
  const f = path.join(dir, "tools-" + new Date().toISOString().replace(/[:.]/g, "-") + (MOCK ? "-mock" : "") + ".json");
  fs.writeFileSync(f, JSON.stringify({ at: new Date().toISOString(), mock: MOCK, vendor: VENDOR, deep: DEEP, per: PER, rows: rows, cells: out }, null, 1));
  console.log("读数留在 " + f + "（runs/ 已在 .gitignore 里，不进仓库）");
})();
