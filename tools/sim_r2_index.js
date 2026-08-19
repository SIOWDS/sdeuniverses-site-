/* 只测这一件事：搜索索引（218MB 生成物）迁 R2 的四段。
   这次迁移与学员 PDF 那次的关键差别是**索引会变**，由此派生出三条不同的纪律：
   ① 不加 immutable、不进边缘缓存 —— PDF 是死的，索引每次发文都重建，拿旧的比慢更糟；
   ② /search/index.html 是搜索页本身、必须留在仓库走 ASSETS，只有生成物才许从桶里出；
   ③ **Worker 内部那 8 处读取也必须改** —— env.ASSETS.fetch 绕过本 Worker 的路由，
      公网那条 R2 路由对内部调用完全无效，内部必须自己先问一次桶（这是最容易漏的一脚）。
   四段：内部读取(idxFetch) / 公网供给(R2_IDX) / 搬运(R2_MIGRATE) / 核对(R2_CHECK)。
   全部对着 worker.js 真源码，行为部分用桩实测。 */
"use strict";
const fs = require("fs");
const ROOT = __dirname + "/..";
const W = fs.readFileSync(ROOT + "/src/worker.js", "utf8");
let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };

/* 把 IDX_KEYS 与 idxFetch 从真源码里抠出来跑，不复刻一份——复刻的测试只会证明复刻品是对的。 */
const kLine = W.match(/^const IDX_KEYS = .*$/m);
const fnStart = W.indexOf("async function idxFetch(env, url, path) {");
const fnEnd = W.indexOf("\n}", fnStart) + 2;
const SRC = kLine[0] + "\n" + W.slice(fnStart, fnEnd) + "\nmodule.exports = { IDX_KEYS, idxFetch };";
const { IDX_KEYS, idxFetch } = (function () {
  const m = { exports: {} };
  new Function("module", "exports", "Response", "Request", "URL", SRC)(m, m.exports, RES, REQ, URL);
  return m.exports;
})();
function RES(body, init) { return { body: body, status: (init && init.status) || 200, headers: (init && init.headers) || {}, _r2: true }; }
function REQ(u) { return { url: String(u) }; }

console.log("\n[一] IDX_KEYS：只放行生成物，页面与越权路径一律不认");
{
  const yes = ["search/manifest.json", "search/sections.json", "search/keywords.json", "search/sde-coords.json",
    "search/shard-students-1.json", "search/shard-_root-4.json", "search/shard-plagiarism.json",
    "search/doc/0.json", "search/doc/1551.json", "search/kw/_root.json", "search/kw/students.json"];
  yes.forEach((k) => ok(IDX_KEYS.test(k), "放行 " + k));
  const no = ["search/index.html", "search/doc/../../etc/passwd", "search/../wrangler.jsonc",
    "students/x/y.pdf", "index.html", "search/", "search/doc/", "search/shard-.json.exe",
    "assets/daily-quotes.js", "search/manifest.json.bak"];
  no.forEach((k) => ok(!IDX_KEYS.test(k), "拒绝 " + k));
  ok(!IDX_KEYS.test("search/index.html"), "**搜索页本身永不从桶里出**（它在仓库里，改版靠 push 立即生效）");
}

console.log("\n[二] idxFetch：R2 优先，落空/出错/没绑桶一律静默回落 ASSETS");
{
  const mkEnv = (r2) => ({
    PDFS: r2,
    ASSETS: { fetch: (req) => Promise.resolve({ _assets: true, url: req.url, ok: true }) },
  });
  const U = new URL("https://sdeuniverses.com/search/");
  const run = (env, path) => idxFetch(env, U, path);

  // 命中
  return_test();
  async function return_test() {
    let r = await run(mkEnv({ get: () => Promise.resolve({ body: "FROM_R2" }) }), "/search/manifest.json");
    ok(r._r2 === true && r.body === "FROM_R2", "桶里有 → 从 R2 出");
    ok(/application\/json/.test(String(r.headers["content-type"] || "")), "从 R2 出时补上 JSON content-type（R2 里没存也不至于被当成八位字节流）");

    // 落空
    r = await run(mkEnv({ get: () => Promise.resolve(null) }), "/search/manifest.json");
    ok(r._assets === true, "桶里没有 → 回落 ASSETS（迁移做到一半时两边并存，搜索一次都不会断）");

    // 抛错
    r = await run(mkEnv({ get: () => Promise.reject(new Error("R2 down")) }), "/search/shard-column-1.json");
    ok(r._assets === true, "R2 抛异常 → 回落 ASSETS，不把错抛给读者");

    // 没绑桶
    r = await run({ ASSETS: mkEnv().ASSETS }, "/search/manifest.json");
    ok(r._assets === true, "桶没绑定（env.PDFS 不存在）→ 整段等于不存在");

    // 非索引路径不许走桶
    let asked = null;
    r = await run(mkEnv({ get: (k) => { asked = k; return Promise.resolve({ body: "X" }); } }), "/search/index.html");
    ok(asked === null && r._assets === true, "非 IDX_KEYS 路径根本不问桶，直接 ASSETS");

    // 查询串不能骗过白名单
    asked = null;
    await run(mkEnv({ get: (k) => { asked = k; return Promise.resolve(null); } }), "/search/manifest.json?v=123");
    ok(asked === "search/manifest.json", "带 ?v= 时按去掉查询串后的 key 问桶（前端每次都带时间戳）");

    console.log("\n[三] 公网供给段 R2_IDX：索引会变，故与 PDF 那段三处不同");
    const seg = W.slice(W.indexOf("// ===== R2_IDX"), W.indexOf("// R2_MIGRATE"));
    ok(seg.length > 400, "R2_IDX 供给段在（" + seg.length + " 字符）");
    ok(/request\.method === "GET" \|\| request\.method === "HEAD"/.test(seg), "只接管 GET/HEAD");
    ok(/env\.PDFS && url\.pathname\.startsWith\("\/search\/"\)/.test(seg), "桶没绑定时整段等于不存在");
    ok(/IDX_KEYS\.test\(_k\)/.test(seg), "路径必须过 IDX_KEYS 白名单");
    ok(!/max-age=31536000|cacheControl: "public/.test(seg) && !/cache-control", "public, max-age/.test(seg), "**不加 immutable** —— 索引每次发文都重建，钉死一年等于永远搜不到新文章");
    ok(/cache-control", "no-cache"/.test(seg), "回 no-cache：允许存但每次必须回源验，配 etag 用");
    ok(!/caches\.default/.test(seg), "**不进边缘缓存** —— 前端本就带 ?v=Date.now()，每次都是新 URL，缓存命不中还白占空间");
    ok(!/accept-ranges|content-range|status: 206/.test(seg), "不做 Range —— 索引都是整份 JSON，不是给 PDF.js 分块读的");
    ok(/etag", obj\.httpEtag/.test(seg) && /status: 304/.test(seg), "带 etag 且支持 304，内容没变时不重复传");
    ok(/catch \(e\) \{ \/\* 桶里没有或出岔子：静默回落 ASSETS/.test(seg), "出岔子静默回落，不在这里终结请求");
    ok(!/return new Response\(null, \{ status: 404/.test(seg), "落空时不自己回 404");

    console.log("\n[四] 内部读取全部改完（漏一处就是线上搜索读旧索引）");
    ok(/ASSETS\.fetch[^\n]*\/search\//.test(W) === false, "worker.js 里**再没有**直接用 ASSETS.fetch 读 /search/ 的地方");
    const calls = (W.match(/idxFetch\(env, url,/g) || []).length - 1;   // 减去函数定义那一行
    ok(calls === 7, "七处内部读取全部改走 idxFetch（实得 " + calls + "）");
    ok(/const r = await idxFetch\(env, url, path\);/.test(W), "tierGet 也改了（kw 分层检索走它）");
    ok(/idxFetch\(env, url, "\/search\/doc\/" \+ c\.i \+ "\.json"\)/.test(W), "doc/ 逐篇正文也改了（智能问答的第二段取它）");

    console.log("\n[五] 搬运与核对口子：能力放宽到索引，但不许放宽到任意路径");
    const mig = W.slice(W.indexOf("// R2_MIGRATE"), W.indexOf("// R2_CHECK"));
    ok(/const _isIdx = IDX_KEYS\.test\(p\);/.test(mig), "索引路径经 IDX_KEYS 判定，与供给段同一把尺子");
    ok(/!\/\^students\\\/\[A-Za-z0-9\._\\-\\\/\]\+\\\.pdf\$\/i\.test\(p\) && !_isIdx/.test(mig), "只放行两类：学员 PDF 或索引生成物");
    ok(/p\.indexOf\("\.\."\) >= 0/.test(mig), "仍然挡 .. 穿越");
    ok(/contentType: "application\/json; charset=utf-8", cacheControl: "no-cache"/.test(mig), "索引按 JSON + no-cache 落桶（不是 PDF 那套 immutable）");
    ok(/const _min = _isIdx \? 2 : 1000;/.test(mig), "**小分片门槛下调** —— shard-plagiarism 只有 12KB，更小的分片按 1000 字节一刀切会被误判为取回失败");
    ok(/hd2\.size === buf\.byteLength/.test(mig), "落桶后回读比对字节数，对不上就算失败");
    ok(/if \(!b\.force\) \{ const hd = await env\.PDFS\.head\(p\); if \(hd\)/.test(mig), "已在桶里的默认跳过，可重复跑");

    console.log("\n[六] 未被波及的东西一字未动");
    ok(/const resp = await env\.ASSETS\.fetch\(request\);/.test(W.slice(W.indexOf("// Everything else: serve static assets"))), "静态资源兜底分支原样");
    const pdfSeg = W.slice(W.indexOf("// ===== R2_PDF"), W.indexOf("// ===== R2_IDX"));
    ok(/immutable/.test(pdfSeg) && /caches\.default/.test(pdfSeg) && /status: 206/.test(pdfSeg), "学员 PDF 那段的 immutable/边缘缓存/Range 全都还在");

    console.log("\n结果：" + P + " 项通过，" + F + " 项失败");
    process.exit(F ? 1 : 0);
  }
}
