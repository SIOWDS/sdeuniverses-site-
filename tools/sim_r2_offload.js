/* R2_OFFLOAD：仓库里删掉的 PDF 由桶接上（ASSETS 落空才问桶）。对着 worker.js 真源码，行为部分用桩实测。
   跑法：node tools/sim_r2_offload.js   —— 改 _r2PdfOnAssetMiss 或两处挂点必跑。 */
"use strict";
const fs = require("fs");
const W = fs.readFileSync(__dirname + "/../src/worker.js", "utf8");
let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };
const a = W.indexOf("async function _r2PdfOnAssetMiss"), b = W.indexOf("\nexport default {");
const src = W.slice(a, b);
ok(a > 0 && b > a, "助手函数在 export default 之前（模块级）");
const fn = new Function("Headers", "Response", "Request", "caches", src + "\nreturn _r2PdfOnAssetMiss;");
class H { constructor(o){ this.m = new Map(); if (o) for (const [k,v] of (o instanceof H ? o.m : Object.entries(o))) this.m.set(k.toLowerCase(), v); }
  get(k){ const v = this.m.get(k.toLowerCase()); return v === undefined ? null : v; } set(k,v){ this.m.set(k.toLowerCase(), String(v)); } }
class R { constructor(body, init){ this.body = body; this.status = (init && init.status) || 200; this.headers = (init && init.headers) || new H(); } clone(){ return this; } }
class Q { constructor(u, i){ this.url = u; this.method = (i && i.method) || "GET"; this.headers = new H((i && i.headers) || {}); } }
const store = new Map();
const cachePuts = [];
const fakeCache = { default: { match: async () => null, put: async (k) => { cachePuts.push(k.url); } } };
const f = fn(H, R, Q, fakeCache);
const mkObj = (key, size, range) => ({ size, range, httpEtag: '"e' + key.length + '"', body: { cancel(){} }, writeHttpMetadata(h){ h.set("content-type", "application/octet-stream"); } });
let lastGet = null, throwIt = false;
const env = { PDFS: { get: async (k, o) => { lastGet = { k, o }; if (throwIt) throw new Error("boom");
  if (!store.has(k)) return null; const s = store.get(k);
  if (o && o.range) return mkObj(k, s, { offset: 0, length: 1024 });
  if (o && o.onlyIf && o.onlyIf.get("if-none-match")) { const x = mkObj(k, s); delete x.body; return x; }
  return mkObj(k, s); } } };
const ctx = { waitUntil(){} };
const U = new URL("https://sdeuniverses.com/x");
store.set("books/m/48/a.pdf", 5000);
store.set("books/m/80/判断的危机.pdf", 7000);
store.set("sites/health/p/x.pdf", 3000);
(async () => {
  console.log("\n[一] 行为");
  let r = await f(new Q("u"), env, ctx, "/books/m/48/a.pdf", U);
  ok(r && r.status === 200 && r.headers.get("x-served-from") === "r2" && r.headers.get("content-length") === "5000", "桶里有 → 200、content-length 对、记号 r2");
  ok(r.headers.get("content-type") === "application/pdf", "content-type 强制 application/pdf（不信桶里元数据）");
  ok(lastGet.o.range === undefined, "无 Range 头时不向桶要分段（否则普通下载被回成 206）");
  ok(cachePuts.length === 1 && /__r2off\/books\/m\/48\/a\.pdf$/.test(cachePuts[0]), "整份 GET 留边缘副本，缓存键带 __r2off 前缀、不与 /students/ 段串键");
  r = await f(new Q("u", { headers: { range: "bytes=0-1023" } }), env, ctx, "/books/m/48/a.pdf", U);
  ok(r.status === 206 && r.headers.get("content-range") === "bytes 0-1023/5000", "Range → 206 + content-range（PDF.js 分块取要它）");
  ok(cachePuts.length === 1, "206 不进缓存");
  r = await f(new Q("u", { headers: { "if-none-match": '"x"' } }), env, ctx, "/books/m/48/a.pdf", U);
  ok(r.status === 304, "onlyIf 不满足 → 304");
  r = await f(new Q("u", { method: "HEAD" }), env, ctx, "/books/m/48/a.pdf", U);
  ok(r.status === 200 && r.body === null && r.headers.get("content-length") === "5000", "HEAD → 200 无正文、带长度");
  r = await f(new Q("u"), env, ctx, "/books/m/80/" + encodeURIComponent("判断的危机") + ".pdf", U);
  ok(r && r.status === 200 && lastGet.k === "books/m/80/判断的危机.pdf", "中文文件名：URL 编码解回原字面再当键");
  r = await f(new Q("u"), env, ctx, "/sites/health/p/x.pdf", U);
  ok(r && r.status === 200, "分站改写后的 /sites/<名>/… 路径能取到");
  console.log("\n[二] 不该接的一律交回 null（照旧 404）");
  ok(await f(new Q("u"), env, ctx, "/books/m/48/none.pdf", U) === null, "桶里也没有 → null");
  ok(await f(new Q("u"), env, ctx, "/books/m/48/a.html", U) === null, "非 PDF 不碰");
  ok(await f(new Q("u", { method: "POST" }), env, ctx, "/books/m/48/a.pdf", U) === null, "非 GET/HEAD 不碰");
  for (const k of ["/plib/a.pdf", "/search/a.pdf", "/live/a.pdf", "/moments/a.pdf"]) ok(await f(new Q("u"), env, ctx, k, U) === null, "保留前缀不碰：" + k);
  ok(await f(new Q("u"), env, ctx, "/books/../plib/a.pdf", U) === null, "含 .. 不碰");
  ok(await f(new Q("u"), env, ctx, "/books/%E0%A4%A.pdf", U) === null, "坏的 URL 编码不抛异常");
  ok(await f(new Q("u"), {}, ctx, "/books/m/48/a.pdf", U) === null, "桶没绑定 → null");
  throwIt = true;
  ok(await f(new Q("u"), env, ctx, "/books/m/48/a.pdf", U) === null, "桶抛异常 → null，不比迁移前更坏");
  throwIt = false;
  console.log("\n[三] 两处挂点（静态）");
  ok(/if \(cand\.status === 404\) \{\s*const _off = await _r2PdfOnAssetMiss\(request, env, ctx, subPrefix \+ contentPath, url\);\s*if \(_off\) \{ resp = _off; subLocal = true; \}/.test(W), "分站挂点：按改写后的路径问桶，命中算本分站本地");
  ok(/if \(!resp\) resp = await env\.ASSETS\.fetch\(assetReq\);\s*\/\/ R2_OFFLOAD[^\n]*\n\s*if \(resp\.status === 404 && \/\\\.pdf\$\/i\.test\(new URL\(assetReq\.url\)\.pathname\)\)/.test(W), "主站挂点：ASSETS 404 且是 PDF 才问桶");
  ok((W.match(/_r2PdfOnAssetMiss\(/g) || []).length === 3, "定义 1 处 + 挂点 2 处，没有别处偷用");
  console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
  process.exit(F ? 1 : 0);
})();
