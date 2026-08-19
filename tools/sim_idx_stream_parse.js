/* sim_idx_stream_parse —— 三层记忆·第一刀的护栏（2026-08-18）
   守的事：索引装载**永不整份 JSON.parse**，而逐条解析出来的结果必须与整份解析**逐字节等价**。
   纪律（本仓吃过五次亏）：判据一律从源码 indexOf 抠出来 new Function 真跑，不手抄形状、不写字面量。 */
const fs = require("fs");
const path = require("path");
const SRC = fs.readFileSync(path.join(__dirname, "../src/worker.js"), "utf8");
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) { pass++; console.log("  ✓ " + m); } else { fail++; console.log("  ✗ " + m); } };
const sect = (t) => console.log("\n" + t);

/* ── 从源码抠出三个扫描器真跑（不手抄）── */
const a = SRC.indexOf("function _scanTopLevel(");
const b = SRC.indexOf("const _IDX_INFLIGHT");
const c = SRC.indexOf("const TIER_L1_ALL");
if (a < 0 || b < 0 || c < 0 || !(a < b && b < c)) { console.log("切片锚点找不到或次序不对"); process.exit(1); }
const block = SRC.slice(a, c);
if (!block.trim()) { console.log("切出来是空串——空串对 !/…/.test() 全是 PASS，断言会安静失效"); process.exit(1); }
const F = new Function(block + "\nreturn {_scanTopLevel:_scanTopLevel,_scanObjEntries:_scanObjEntries,_once:_once};")();

sect("一、顶层数组扫描 = 整份 parse（逐元素等价）");
const cases = [
  '{"rows":[{"i":1,"k":["a","b"]},{"i":2,"k":["c"]}]}',
  '{"rows":[{"i":1,"k":["带\\"引号","反斜杠\\\\","逗号,词","括号}{","方括号][" ]}]}',
  '{"rows":[{"i":0,"k":[]},{"i":9,"k":["\\u4e2d\\u6587"]}]}',
  '{"built":"x","rows":[{"i":5,"k":["嵌套"],"z":{"a":[1,2,{"b":3}]}}]}',
  '{"rows":[]}',
];
for (const t of cases) {
  const got = [];
  F._scanTopLevel(t, "rows", (x) => got.push(JSON.parse(x)));
  ok(JSON.stringify(got) === JSON.stringify(JSON.parse(t).rows), "等价：" + t.slice(0, 46) + (t.length > 46 ? "…" : ""));
}
ok(F._scanTopLevel('{"rows":[{"i":1}]}', "nope", () => {}) === 0, "找不到该键返回 0（调用方据此退回旧路）");

sect("二、顶层对象扫描 = 整份 parse（sde-coords 形状）");
const oCases = [
  '{"3":["a","b"],"17":["c"]}',
  '{"1":["带\\"引号","逗号,词"],"2":[]}',
  '{"1":["x"],"2":["y"],"10":["z"]}',
];
for (const t of oCases) {
  const got = {};
  F._scanObjEntries(t, (k, v) => { got[k] = JSON.parse(v); });
  ok(JSON.stringify(got) === JSON.stringify(JSON.parse(t)), "等价：" + t.slice(0, 40));
}

sect("三、拿线上真文件比对（有就跑，没有就跳过）");
const real = path.join(__dirname, "../.idxfixture");
let ran = 0;
for (const [f, key] of [["kw.json", "rows"], ["man.json", "docs"], ["co.json", null]]) {
  const p2 = path.join(real, f);
  if (!fs.existsSync(p2)) continue;
  ran++;
  const txt = fs.readFileSync(p2, "utf8");
  if (key) {
    const got = [];
    F._scanTopLevel(txt, key, (x) => got.push(JSON.parse(x)));
    const want = JSON.parse(txt)[key];
    ok(got.length === want.length && JSON.stringify(got) === JSON.stringify(want), f + " 的 " + key + " 逐条等价（" + got.length + " 条）");
  } else {
    const got = {};
    F._scanObjEntries(txt, (k, v) => { got[k] = JSON.parse(v); });
    const want = JSON.parse(txt);
    ok(JSON.stringify(got) === JSON.stringify(want), f + " 逐条等价（" + Object.keys(got).length + " 条）");
  }
}
if (!ran) console.log("  · 无真文件夹具（.idxfixture/），跳过本节");

sect("四、冷载互斥：并发只建一次");
(async () => {
  let built = 0;
  const mk = () => F._once("k", async () => { built++; await new Promise((r) => setTimeout(r, 20)); return built; });
  const rs = await Promise.all([mk(), mk(), mk(), mk()]);
  ok(built === 1, "四个并发请求只跑了一遍装载");
  ok(rs.every((v) => v === 1), "四个都拿到同一份结果");
  const again = await F._once("k", async () => { built++; return built; });
  ok(built === 2 && again === 2, "跑完即释放，下一次照常重建（不是永久缓存）");

  sect("五、源码契约：热路径不许整份 parse");
  const seg = (from, to) => { const i = SRC.indexOf(from); const j = SRC.indexOf(to, i); return i < 0 || j < 0 ? "" : SRC.slice(i, j); };
  const tg = seg("async function tierGet(", "function _scoreKeys(");
  const lc = seg("async function loadCoords(", "// RAG_STREAMED_SCAN");
  const im = seg("async function idxManifest(", "// IDX_KEYS");
  ok(tg && lc && im, "三段切片都非空");
  ok(/_scanTopLevel\(txt, "rows"/.test(tg), "tierGet 走逐行扫描");
  ok(/_scanObjEntries\(txt/.test(lc), "loadCoords 走逐条扫描");
  ok(/_scanTopLevel\(txt, "docs"/.test(im), "idxManifest 走逐条扫描");
  for (const [n, s2] of [["tierGet", tg], ["loadCoords", lc], ["idxManifest", im]]) {
    ok(/_once\(/.test(s2), n + " 挂了冷载互斥");
  }
  /* 退路那一份 JSON.parse(txt) 是**有意留的**（形状不认识就退回旧路），所以判据不是"一次都不许有"，
     而是"不许在正常路径上整份 parse"——即每段里 JSON.parse(txt) 至多出现在 `if (!n)` 的退路里。 */
  ok((tg.match(/JSON\.parse\(txt\)/g) || []).length <= 2, "tierGet 的整份 parse 只剩退路（l0 与形状不认识）");
  ok((im.match(/JSON\.parse\(txt\)/g) || []).length <= 1, "idxManifest 的整份 parse 只剩退路");
  ok(!/JSON\.parse\(txt\)/.test(lc), "loadCoords 已无整份 parse");
  ok(/tl: String\(d\.t \|\| ""\)\.toLowerCase\(\)/.test(im), "标题小写在装载时备好（tl）");
  ok((SRC.match(/const tl = d\.tl \|\|/g) || []).length === 3, "三处热循环都改用备好的 tl，不再每请求重算");

  console.log("\n──────── " + pass + " passed, " + fail + " failed ────────");
  process.exit(fail ? 1 : 0);
})();
