// kb_retrieve.js — SDE 九库结构化检索(将并入 src/worker.js)
// 用法(本地模拟): node tools/kb_retrieve.js
// worker 侧只需把 loadKB/kbLink/kbSubgraph/retrieveKB 四个函数贴入,env.ASSETS.fetch 取代下方 fs 读取。

// ==================== 将并入 worker.js 的函数(纯逻辑,不依赖 fs) ====================
const KB_TYPE_LABEL = { concept:"概念", proposition:"命题", theory:"理论", evidence:"证据",
  case:"案例", method:"方法", scholar:"学者", controversy:"争议", version:"版本" };
const KB_ORDER = ["concept","proposition","theory","evidence","case","method","scholar","controversy","version"];
const _norm = (s) => String(s).replace(/\s+/g, "").toLowerCase();

// 查询 → 种子实体 id:index 键子串命中查询 + SDE 扩展词命中 index 键
function kbLink(kb, q, expTerms) {
  const qn = _norm(q);
  const cand = new Set();
  for (const key in kb.idx) {                       // 1) 概念名/别名直接出现在问句里
    if (key.length >= 2 && qn.indexOf(key) >= 0) cand.add(kb.idx[key][1]);
  }
  for (const t of (expTerms || [])) {               // 2) SDE 词义扩展词命中 index
    const tn = _norm(t); if (tn.length < 2) continue;
    if (kb.idx[tn]) { cand.add(kb.idx[tn][1]); continue; }
    for (const key in kb.idx) {                      // 扩展词与键互为子串(键≥3 防碎片误命中)
      if (key.length >= 3 && (key.indexOf(tn) >= 0 || tn.indexOf(key) >= 0)) cand.add(kb.idx[key][1]);
    }
  }
  return [...cand].filter((id) => kb.byId[id]);
}

// 种子 → 一跳邻域子图(BFS,种子优先,预算封顶)
function kbSubgraph(kb, seedIds, maxEntities) {
  const picked = new Map();
  const queue = seedIds.slice();
  while (queue.length && picked.size < maxEntities) {
    const id = queue.shift(); const e = kb.byId[id];
    if (!e || picked.has(id)) continue;
    picked.set(id, e);
    for (const ids of Object.values(e.links || {})) for (const l of ids) if (!picked.has(l)) queue.push(l);
  }
  return picked;
}

// 顶层:查询 → { block(结构化上下文), srcs(出处), n(实体数), seeds }
function retrieveKB(kb, corpus, q, expTerms, budget) {
  const seeds = kbLink(kb, q, expTerms);
  if (!seeds.length) return { block: "", srcs: [], n: 0, seeds: [] };
  const picked = kbSubgraph(kb, seeds, budget || 24);
  const groups = {}; const srcDocs = new Set();
  for (const e of picked.values()) {
    (groups[e.type] = groups[e.type] || []).push(e);
    for (const d of (e.sources || []).slice(0, 3)) srcDocs.add(d);
  }
  let block = "【SDE 结构化知识 · 调用自九库(概念→命题→理论→证据→案例→方法→学者→争议,已是成体系的判断而非相似句)】\n";
  for (const ty of KB_ORDER) {
    if (!groups[ty]) continue;
    for (const e of groups[ty]) {
      const seedMark = seeds.indexOf(e.id) >= 0 ? "▶" : "·";
      block += seedMark + KB_TYPE_LABEL[ty] + "｜" + e.name + "：" + e.def + "\n";
      if (e.body && seeds.indexOf(e.id) >= 0) block += "   " + e.body + "\n";
    }
  }
  const srcs = [];
  for (const d of srcDocs) { const dd = corpus.docs[d]; if (dd) srcs.push({ u: dd.u, t: dd.t }); }
  return { block, srcs: srcs.slice(0, 8), n: picked.size, seeds };
}

// ==================== 以下仅为本地模拟(worker 不需要) ====================
if (typeof require !== "undefined" && require.main === module) {
  const fs = require("fs"), path = require("path");
  const KB = path.join(__dirname, "..", "public", "kb");
  const S  = path.join(__dirname, "..", "public", "search");
  const rd = (p) => JSON.parse(fs.readFileSync(p, "utf8"));

  // 装 KB(模拟 loadKB)
  const man = rd(path.join(KB, "kb-manifest.json"));
  const idx = rd(path.join(KB, "kb-index.json"));
  const byId = {};
  for (const lib of Object.values(man.libraries)) for (const e of rd(path.join(KB, lib.file))) byId[e.id] = e;
  const kb = { built: man.built, idx, byId };
  const corpus = { docs: rd(path.join(S, "manifest.json")).docs };

  // 极简 SDE 扩展词模拟(worker 里由 sdeExpandQuery 调基底产出;此处用规则近似,足以验证链路)
  const EXP = {
    "什么是显露": ["显露","S","结构","三大方程"],
    "为什么现在很多人不结婚": ["婚姻","三界","退化态","不结婚"],
    "黑格尔的绝对精神是什么": ["黑格尔","绝对精神","封顶","辩证法"],
    "怎么让大模型输出更深的内容": ["提智","四步法","三视角","创新智商"],
    "一批论文怎么装成一本书": ["母题","缝隙创新法","解构"],
    "SDE 怎么看抑郁症": ["三界","能量三状态","势能","单视角不可达"],
  };

  const QUERIES = Object.keys(EXP);
  for (const q of QUERIES) {
    const r = retrieveKB(kb, corpus, q, EXP[q], 22);
    console.log("\n" + "═".repeat(72));
    console.log("问:", q);
    console.log("种子实体(" + r.seeds.length + "):", r.seeds.join(", ") || "(无)");
    console.log("子图实体数:", r.n, "· 出处文档:", r.srcs.length);
    console.log("—— 注入模型的结构化上下文 ——");
    console.log(r.block.trimEnd());
    console.log("—— 出处(前3)——");
    r.srcs.slice(0, 3).forEach((s) => console.log("  " + s.u + "  " + s.t.slice(0, 46)));
  }

  // 冒烟:无命中查询应安全返回空块(退回纯 chunk 检索)
  const miss = retrieveKB(kb, corpus, "今天天气怎么样", ["天气"], 22);
  console.log("\n" + "═".repeat(72));
  console.log("无关查询『今天天气怎么样』→ 结构块为空?", miss.block === "" ? "是(安全退回 chunk 检索)" : "否 ✗");
}
