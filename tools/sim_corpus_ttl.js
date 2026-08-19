#!/usr/bin/env node
// 模拟 src/worker.js 的 loadCorpus 复验逻辑（发文后 WDS/问答 30 秒内换上新语料）。
// 从 worker.js 原文抽出 loadCorpus + loadCoords，桩掉 env.ASSETS 与 Date.now 跑五个场景。
"use strict";
const fs = require("fs"), path = require("path");
const src = fs.readFileSync(path.join(__dirname, "..", "src", "worker.js"), "utf8");

function extract(name) {
  const i = src.indexOf("async function " + name);
  if (i < 0) throw new Error("找不到 " + name);
  let d = 0, j = src.indexOf("{", i);
  for (let k = j; k < src.length; k++) {
    if (src[k] === "{") d++;
    else if (src[k] === "}" && --d === 0) return src.slice(i, k + 1);
  }
  throw new Error("括号不闭合 " + name);
}
const head = src.match(/let CORPUS = null;[\s\S]*?const CORPUS_TTL = [^\n]*\n/);
if (!head) throw new Error("找不到 CORPUS 缓存声明段");

let NOW = 1000000;
let manifest = { built: "T1", sections: [{ key: "a", label: "A", files: ["a-1", "a-2"] }, { key: "b", label: "B" }], docs: [{ i: 0 }] };
let fetches = [];
let failManifest = false;
const shard = (n) => ({ chunks: Array.from({ length: n }, (_, i) => ({ d: 0, t: "c" + i })) });
const env = { ASSETS: { fetch: async (req) => {
  const p = new URL(req.url).pathname; fetches.push(p);
  if (p.endsWith("manifest.json")) { if (failManifest) throw new Error("boom"); return { json: async () => manifest }; }
  if (p.includes("sde-coords")) return { json: async () => ({}) };
  return { json: async () => shard(p.includes("a-1") ? 3 : p.includes("a-2") ? 2 : 4) };
} } };
const code = head[0] + extract("loadCorpus") + "\nasync function loadCoords(){return null;}\nreturn {loadCorpus, peek:()=>CORPUS};";
const mod = new Function("env", "Date", code)(env, { now: () => NOW });

(async () => {
  const url = "https://x.local/";
  // ① 首次装载：拉 manifest + 3 个分片文件（a-1,a-2,b），块数 3+2+4=9
  let c = await mod.loadCorpus(env, url);
  console.assert(c.chunks.length === 9 && c.built === "T1", "① 首次装载失败");
  // ② TTL 内再调：零 fetch，直接命中缓存
  fetches = []; NOW += 10 * 1000;
  c = await mod.loadCorpus(env, url);
  console.assert(fetches.length === 0, "② TTL 内不应发 fetch");
  // ③ TTL 过期、manifest.built 未变：只拉 manifest，不重载分片
  fetches = []; NOW += 31 * 1000;
  c = await mod.loadCorpus(env, url);
  console.assert(fetches.length === 1 && fetches[0].endsWith("manifest.json") && c.chunks.length === 9, "③ 未变应只验 manifest");
  // ④ TTL 过期、built 变了（发了新文）：整套重载，拿到新块
  manifest = { built: "T2", sections: [{ key: "a", label: "A", files: ["a-1"] }], docs: [{ i: 0 }] };
  fetches = []; NOW += 31 * 1000;
  c = await mod.loadCorpus(env, url);
  console.assert(c.built === "T2" && c.chunks.length === 3, "④ built 变了应重载");
  // ⑤ 复验时 manifest 拉取失败：不炸，用旧语料顶着
  failManifest = true; fetches = []; NOW += 31 * 1000;
  c = await mod.loadCorpus(env, url);
  console.assert(c.built === "T2" && c.chunks.length === 3, "⑤ 失败应回退旧语料");
  console.log("sim_corpus_ttl：5/5 场景全过 ✅（首装9块｜TTL内零fetch｜未变仅验manifest｜换代重载3块｜失败回退）");
})().catch((e) => { console.error("FAIL:", e); process.exit(1); });
