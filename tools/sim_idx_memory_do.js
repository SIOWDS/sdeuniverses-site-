/* sim_idx_memory_do —— 三层记忆·长期记忆（IndexMemory）的护栏（2026-08-18）
   守三件事：
     ① 重建真的把 manifest / kw 分片 / 坐标灌进了 SQLite，且是**分片跑**（一次 alarm 一件）；
     ② 重建期间老表照常应答，影子表建好才换手（绝不在重建那几秒里回空名单）；
     ③ 查询打分口径与旧的 L0/L1 **逐条对齐**（base+1 / exp+1.2 / prev+0.4 · 标题 base+3/exp+2 · 坐标只在 exp 时 +1.5）。
   纪律：判据从源码抠出来真跑，不手抄形状。SQLite 用一个够用的内存桩顶上。 */
"use strict";
const fs = require("fs"), path = require("path");
const SRC = fs.readFileSync(path.join(__dirname, "../src/worker.js"), "utf8");
let pass = 0, fail = 0;
const ok = (m, c, d) => { if (c) { pass++; console.log("  ✓ " + m); } else { fail++; console.log("  ✗ " + m + (d ? "  " + d : "")); } };
const sect = (t) => console.log("\n" + t);

/* ── 抠出扫描器 + DO 类，真跑 ── */
const sA = SRC.indexOf("function _scanTopLevel("), sB = SRC.indexOf("const _IDX_INFLIGHT");
const dA = SRC.indexOf("export class IndexMemory {"), dB = SRC.indexOf("// ===== 密钥保险箱");
if (sA < 0 || sB < 0 || dA < 0 || dB < 0 || dA > dB) { console.log("锚点找不到"); process.exit(1); }
const BLOCK = SRC.slice(sA, sB) + "\n" + SRC.slice(dA, dB).replace(/^export class/m, "class");
ok("抠出来的是完整可跑的一段", (() => { try { new Function(BLOCK); return true; } catch (e) { return false; } })());
const IndexMemory = new Function(BLOCK + "\nreturn IndexMemory;")();

/* ── 一个够用的 SQLite 桩：只实现本 DO 用到的那几种语句 ── */
function makeSql() {
  const T = {};                                     // 表名 → 行数组
  const idx = {};
  const api = {
    exec(q, ...a) {
      const s = q.trim();
      /* ⚠ 平台硬限制：DO SQLite 每条语句最多 100 个绑定参数。桩必须一起限，
         否则「按行数分批」这种错在模拟里永远是绿的——线上第一次跑就炸。 */
      if (a.length > 100) throw new Error("too many SQL variables");
      let m;
      if (/^CREATE TABLE/i.test(s)) { const n = s.match(/CREATE TABLE (?:IF NOT EXISTS )?(\w+)/)[1]; if (!T[n]) T[n] = []; return []; }
      if (/^CREATE INDEX/i.test(s)) { idx[s] = 1; return []; }
      if ((m = s.match(/^DROP TABLE (?:IF EXISTS )?(\w+)/i))) { delete T[m[1]]; return []; }
      if ((m = s.match(/^ALTER TABLE (\w+) RENAME TO (\w+)/i))) { if (T[m[1]]) { T[m[2]] = T[m[1]]; delete T[m[1]]; } return []; }
      if ((m = s.match(/^INSERT (?:OR REPLACE )?INTO (\w+)\(([^)]+)\) VALUES/i))) {
        const tbl = m[1], cols = m[2].split(",").map((x) => x.trim());
        if (!T[tbl]) T[tbl] = [];
        if (/ON CONFLICT/i.test(s)) {                 // meta 的 upsert
          const row = {}; cols.forEach((c, ix) => row[c] = a[ix]);
          const e = T[tbl].find((r) => r[cols[0]] === row[cols[0]]);
          if (e) Object.assign(e, row); else T[tbl].push(row);
          return [];
        }
        const lit = (s.match(/\((?:\?|'[^']*')(?:,(?:\?|'[^']*'))*\)/g) || [])[0] || "";
        const perRow = (lit.match(/[?']/g) || []).filter((c) => c === "?" || c === "'").length;
        const slots = lit.slice(1, -1).split(",").map((x) => x.trim());
        const nQ = slots.filter((x) => x === "?").length;
        for (let p = 0; p < a.length; p += nQ) {
          const row = {}; let qi = 0;
          slots.forEach((sl, ix) => { row[cols[ix]] = sl === "?" ? a[p + (qi++)] : sl.replace(/'/g, ""); });
          if (/OR REPLACE/i.test(s)) { const e = T[tbl].find((r) => r[cols[0]] === row[cols[0]]); if (e) { Object.assign(e, row); continue; } }
          T[tbl].push(row);
        }
        return [];
      }
      if ((m = s.match(/^SELECT count\(\*\) AS n FROM (\w+)/i))) return [{ n: (T[m[1]] || []).length }];
      if ((m = s.match(/^SELECT v FROM meta WHERE k=\?/i))) return (T.meta || []).filter((r) => r.k === a[0]).map((r) => ({ v: r.v }));
      if ((m = s.match(/^SELECT i,src FROM terms WHERE term=\?/i))) return (T.terms || []).filter((r) => String(r.term) === String(a[0])).map((r) => ({ i: r.i, src: r.src }));
      if ((m = s.match(/^SELECT i FROM docs WHERE tl LIKE \?/i))) {
        const pat = String(a[0]).replace(/^%|%$/g, "").replace(/\\(.)/g, "$1");
        return (T.docs || []).filter((r) => String(r.tl || "").indexOf(pat) >= 0).map((r) => ({ i: r.i }));
      }
      if ((m = s.match(/^SELECT i FROM docs WHERE sec=\?/i))) return (T.docs || []).filter((r) => r.sec === a[0]).map((r) => ({ i: r.i }));
      if ((m = s.match(/^SELECT i,u,t,sec FROM docs WHERE i=\?/i))) return (T.docs || []).filter((r) => r.i === a[0]);
      if (/^SELECT sec,label FROM secs/i.test(s)) return (T.secs || []).map((r) => ({ sec: r.sec, label: r.label }));
      throw new Error("桩不认识这条语句：" + s.slice(0, 70));
    },
    _T: T,
  };
  return api;
}
/* ⚠ 夹具必须**大到能触发分批**。第一版只有 3 篇 —— 于是「批量按行数算」这个真 bug
   在模拟里永远是绿的（一批都凑不满），线上第一次跑就 "too many SQL variables"。
   现在垫到 300 篇 / 每篇 64 词：docs 一批 20 行、terms 一批 50 行，都要 flush 很多次。 */
const PAD = [];
for (let n = 3; n < 300; n++) PAD.push({ i: n, u: "/p" + n, t: "填充篇目" + n, s: n % 2 ? "col" : "bk" });
const MAN = JSON.stringify({ built: "b1", counts: { docs: 300 },
  sections: [{ key: "col", label: "专栏", docs: 2 }, { key: "bk", label: "专著", docs: 1 }],
  docs: [{ i: 0, u: "/a", t: "显露与差异", s: "col" }, { i: 1, u: "/b", t: "纠缠的发生", s: "col" }, { i: 2, u: "/c", t: "无关的书", s: "bk" }].concat(PAD) });
const padRows = (sec) => PAD.filter((d) => d.s === sec).map((d) => ({ i: d.i, k: Array.from({ length: 64 }, (_, z) => "词" + d.i + "_" + z) }));
const KW = { col: JSON.stringify({ rows: [{ i: 0, k: ["显露", "差异", "sde"] }, { i: 1, k: ["纠缠", "发生"] }].concat(padRows("col")) }),
             bk: JSON.stringify({ rows: [{ i: 2, k: ["园林", "水力"] }].concat(padRows("bk")) }) };
const CO = JSON.stringify({ "0": ["显露"], "1": ["纠缠"] });
const N_DOCS = 300, N_TERMS = 3 + 2 + 2 + 297 * 64 + 2;   // 篇层词 + 坐标词
function makeCtx() {
  let alarmAt = null;
  return { storage: { sql: makeSql(), setAlarm: async (t) => { alarmAt = t; }, _alarm: () => alarmAt, _clr: () => { alarmAt = null; } } };
}
const ENV = { PDFS: { head: async () => ({ etag: "E1" }),
  get: async (k) => { const map = { "search/manifest.json": MAN, "search/sde-coords.json": CO,
    "search/kw/col.json": KW.col, "search/kw/bk.json": KW.bk };
    return map[k] ? { text: async () => map[k] } : null; } } };

(async () => {
  sect("一、重建：分片跑，一次 alarm 一件");
  const ctx = makeCtx();
  const im = new IndexMemory(ctx, ENV);
  im._init();
  const q0 = await im._ensure(false);
  ok("首次问指纹后把任务排进队列", q0.ok && q0.why === "queued");
  ok("排完队就挂了 alarm", ctx.storage._alarm() !== null);
  let ticks = 0;
  while (ticks < 20) { const a = ctx.storage._alarm(); if (a === null) break; ctx.storage._clr(); await im.alarm(); ticks++; }
  ok("分片跑完（manifest + 两个 kw 分片 + 坐标 = 4 件，逐件各一次 alarm）", ticks === 4, "实际 " + ticks + " 次");
  const st = im._status();
  ok("全部文档进表（300 篇，足以逼出分批）", st.docs === N_DOCS, JSON.stringify(st));
  ok("倒排词条全部进表", st.terms === N_TERMS, "实际 " + st.terms + " 应为 " + N_TERMS);
  ok("指纹已落定", st.stamp === "E1");
  ok("队列已清空", st.pending === 0);
  ok("没有报错", !st.err, st.err);

  sect("二、打分口径与旧的 L0/L1 逐条对齐");
  /* 旧口径（_scoreKeys + 标题 + 坐标），照抄一份当参照物——**这份参照是从源码里读出来的权重，不是我编的** */
  const wSrc = SRC.slice(SRC.indexOf("function _scoreKeys("), SRC.indexOf("async function ragScan("));
  const wBase = +(wSrc.match(/for \(const key of baseKeys\) if \(hit\(key\)\) sc \+= ([\d.]+);/) || [])[1];
  const wExp = +(wSrc.match(/for \(const key of exp\) if \(hit\(key\)\) sc \+= ([\d.]+);/) || [])[1];
  const wPrev = +(wSrc.match(/for \(const key of prev\) if \(hit\(key\)\) sc \+= ([\d.]+);/) || [])[1];
  ok("从源码读到旧的三档权重", wBase === 1 && wExp === 1.2 && wPrev === 0.4, [wBase, wExp, wPrev].join("/"));
  const r1 = im._query({ baseKeys: ["显露"], exp: [], prev: [], pick: 10 });
  // 篇 0：篇层命中 +1，标题「显露与差异」含"显露" +3 ⇒ 4
  ok("base 命中：篇层 +1 与标题 +3 都算上（坐标不参与 base）", r1.ok && r1.cand[0].i === 0 && Math.abs(r1.cand[0].sc - 4) < 1e-9, JSON.stringify(r1.cand));
  const r2 = im._query({ baseKeys: [], exp: ["纠缠"], prev: [], pick: 10 });
  // 篇 1：篇层 +1.2、坐标 +1.5、标题「纠缠的发生」+2 ⇒ 4.7
  ok("exp 命中：篇层 1.2 + 坐标 1.5 + 标题 2 = 4.7", r2.ok && Math.abs(r2.cand[0].sc - 4.7) < 1e-9, JSON.stringify(r2.cand));
  const r3 = im._query({ baseKeys: [], exp: [], prev: ["差异"], pick: 10 });
  ok("prev 只加 0.4，且坐标不参与", r3.ok && Math.abs(r3.cand[0].sc - 0.4) < 1e-9, JSON.stringify(r3.cand));
  const r4 = im._query({ baseKeys: ["显露", "纠缠"], exp: [], prev: [], only: "bk", pick: 10 });
  ok("限定版块时把别栏的候选滤干净", r4.ok && r4.cand.length === 0, JSON.stringify(r4.cand));

  sect("三、只回候选那几篇的元数据，不回全站");
  const r5 = im._query({ baseKeys: ["显露"], exp: [], prev: [], pick: 10 });
  ok("docs 只含候选（1 篇），不是全站 300 篇", r5.docs.length === 1 && r5.docs[0].u === "/a", JSON.stringify(r5.docs));
  ok("版块名照常回", r5.secLabel && r5.secLabel.col === "专栏");

  sect("四、重建期间老表照常应答（影子表建好才换手）");
  ENV.PDFS.head = async () => ({ etag: "E2" });      // 索引换了一版
  await im._ensure(false);
  ctx.storage._clr(); await im.alarm();               // 只跑第一件（建影子表 + 灌 manifest）
  const mid = im._query({ baseKeys: ["显露"], exp: [], prev: [], pick: 10 });
  ok("重建跑到一半，查询仍拿得到候选（走的是老表）", mid.ok && mid.cand.length === 1, JSON.stringify(mid.cand));
  ok("此时指纹还没换（没换手就不算数）", im._get("stamp") === "E1");
  while (ctx.storage._alarm() !== null) { ctx.storage._clr(); await im.alarm(); }
  ok("跑完才换手：指纹更新", im._get("stamp") === "E2");
  ok("换手后数据仍完整", im._status().docs === N_DOCS && im._status().terms === N_TERMS);

  sect("四之二、绑定参数上限与「失败即作废」（第一次上线就栽在这两条）");
  const im3 = new IndexMemory(makeCtx(), ENV); im3._init();
  await im3._ensure(false);
  let t3 = 0; while (im3.ctx.storage._alarm() !== null && t3 < 20) { im3.ctx.storage._clr(); await im3.alarm(); t3++; }
  ok("整次重建没有触到 100 个绑定参数的上限", !im3._get("err"), im3._get("err"));
  ok("批量是按参数个数算的，不是按行数", /_rows\(\d+\)/.test(SRC) && /Math\.floor\(IndexMemory\._CAP \/ perRow\)/.test(SRC));

  // 造一件必失败的任务：坐标那一份读不回来时不算失败（跳过），所以改成让 manifest 读崩
  const badEnv = { PDFS: { head: async () => ({ etag: "E9" }), get: async (k) => k === "search/manifest.json" ? { text: async () => { throw new Error("读崩了"); } } : null } };
  const im4 = new IndexMemory(makeCtx(), badEnv); im4._init();
  im4.sql.exec("INSERT INTO docs(i,u,t,tl,sec) VALUES(?,?,?,?,?)", 7, "/old", "旧的", "旧的", "col");
  im4.sql.exec("INSERT INTO terms(term,i,src) VALUES(?,?,'k')", "旧的", 7);
  im4._set("stamp", "E-old");
  await im4._ensure(false);
  let t4 = 0; while (im4.ctx.storage._alarm() !== null && t4 < 20) { im4.ctx.storage._clr(); await im4.alarm(); t4++; }
  ok("有一件失败就把整次重建作废（记下来、停住）", !!im4._get("err") && im4._get("abort") === "1", im4._get("err"));
  ok("失败时**绝不换手**：老表原样留着", im4._status().docs === 1 && im4._status().terms === 1);
  ok("失败时不许把新指纹记下来（否则下次复验「没变」就再也不会重建）", im4._get("stamp") === "E-old");
  const still = im4._query({ baseKeys: ["旧的"], exp: [], prev: [], pick: 10 });
  ok("失败之后查询照常走老索引", still.ok && still.cand.length === 1);

  sect("五、表还没建好时必须说 ok:false（让调用方退回旧路，绝不回空名单）");
  const im2 = new IndexMemory(makeCtx(), ENV); im2._init();
  const empty = im2._query({ baseKeys: ["显露"], exp: [], prev: [], pick: 10 });
  ok("空表回 ok:false 而不是 cand:[]", empty.ok === false && empty.why === "empty", JSON.stringify(empty));

  sect("六、接线：调用侧的契约");
  ok("ragScan 先问长期记忆", /const lt = await idxAsk\(env, \{ op: "query"/.test(SRC));
  ok("ok:false 或拿不到就往下走旧路（退路仍在）", /const man = await idxManifest\(env, url\);\n  const coords = await loadCoords\(env, url\);/.test(SRC));
  ok("idxAsk 失败一律吞掉回 null", /async function idxAsk[\s\S]{0,700}catch \(e\) \{ return null; \}/.test(SRC));
  ok("长期记忆是全站单例", /IDXMEM\.idFromName\("global"\)/.test(SRC));
  ok("两条前端共用同一台下钻（只有一处在管取多少块）", (SRC.match(/await ragDrill\(/g) || []).length === 2);
  const WR = fs.readFileSync(path.join(__dirname, "../wrangler.jsonc"), "utf8");
  ok("wrangler 绑定了 IDXMEM", /"name": "IDXMEM", "class_name": "IndexMemory"/.test(WR));
  ok("migration 里 IndexMemory 是 sqlite 类", /"new_sqlite_classes": \["IndexMemory"\]/.test(WR));
  ok("重建口要管理员口令", /\/api\/idx\/rebuild[\s\S]{0,400}adminPassOk/.test(SRC));

  console.log("\n──────── " + pass + " passed, " + fail + " failed ────────");
  process.exit(fail ? 1 : 0);
})();
