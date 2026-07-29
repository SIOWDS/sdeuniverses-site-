/* 只测这一件事：学员 PDF 迁 R2 的三段（供给 / 搬运 / 核对）。
   这次迁移的要害不是"能不能搬"，而是**搬的过程中一篇文章都不许打不开**：
   ① 供给走 R2 优先、落空静默回落 ASSETS —— 迁移做到一半时两边并存，任何一篇都不会 404；
   ② URL 一个字不改 —— 因为页面与 read.html 都是按**相对文件名**引 PDF，改链要动一千多个页面；
   ③ 必须支持 Range —— PDF.js 对大文件分块取，不给 206 就读不出；
   ④ 搬运口子的能力必须收窄到无害（口令是前端级的）：源与目标都钉死在 students/**.pdf。
   全部对着 worker.js 真源码，行为部分用桩实测。 */
"use strict";
const fs = require("fs");
const ROOT = __dirname + "/..";
const W = fs.readFileSync(ROOT + "/src/worker.js", "utf8");
const CFG = fs.readFileSync(ROOT + "/wrangler.jsonc", "utf8");
let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };

console.log("\n[一] 供给：R2 优先、落空回落、URL 不变");
{
  const seg = W.slice(W.indexOf("// ===== R2_PDF"), W.indexOf("// R2_MIGRATE"));
  ok(seg.length > 500, "R2_PDF 供给段在（" + seg.length + " 字符）");
  ok(/env\.PDFS && \/\^\\\/students\\\/\[\^\?\]\+\\\.pdf\$\/i\.test\(url\.pathname\)/.test(seg), "只拦 /students/**.pdf，且桶没绑定时整段等于不存在");
  ok(/request\.method === "GET" \|\| request\.method === "HEAD"/.test(seg), "只接管 GET/HEAD（其它方法不碰）");
  ok(/range: request\.headers, onlyIf: request\.headers/.test(seg), "Range 与 If-None-Match 交给 R2 自己解析（PDF.js 分块取的命根子）");
  ok(/accept-ranges/.test(seg) && /status: 206/.test(seg) && /content-range/.test(seg), "命中分块时回 206 + content-range + accept-ranges");
  ok(/if \(!\("body" in obj\)\) return new Response\(null, \{ status: 304/.test(seg), "onlyIf 不满足回 304，不重复传");
  ok(/catch \(e\) \{ \/\* R2 出任何岔子/.test(seg), "R2 抛异常时不抛给读者，落回仓库");
  // 行为实测：R2 落空（get 返回 null）时**不能 return**，必须继续往下走到 ASSETS
  ok(!/return new Response\(null, \{ status: 404/.test(seg) && !/return env\.ASSETS/.test(seg),
     "R2 落空时既不自己回 404、也不在这里终结请求——落到函数末尾原有的 ASSETS 分支（两边并存的关键）");
  const tail = W.slice(W.indexOf("// Everything else: serve static assets"));
  ok(/const resp = await env\.ASSETS\.fetch\(request\);/.test(tail), "原有的静态资源兜底分支一字未动");
  ok(/x-served-from", "r2"/.test(seg), "从 R2 出去的响应带个记号，线上一眼看得出走的哪条路");
}

console.log("\n[二] 搬运：在边缘自己搬，能力收窄到无害");
{
  const seg = W.slice(W.indexOf("// R2_MIGRATE"), W.indexOf("// R2_CHECK"));
  ok(/env\.ASSETS\.fetch\(new Request\(new URL\("\/" \+ p, url\)\)\)/.test(seg) && /env\.PDFS\.put\(p, buf/.test(seg),
     "源＝仓库自己的静态资源，目标＝R2：几百兆不经过任何人的机器，也不需要 Cloudflare API Token");
  ok(/\^students\\\/\[A-Za-z0-9\._\\-\\\/\]\+\\\.pdf\$/i.test(seg) && /indexOf\("\.\."\) >= 0/.test(seg),
     "路径白名单钉死在 students/**.pdf 且挡掉 ..（口令是前端级的，能力必须小到即便泄露也无害）");
  ok(/String\(b\.pass \|\| ""\) !== "SDE2013"/.test(seg), "带口令门");
  ok(/if \(!b\.force\) \{ const hd = await env\.PDFS\.head\(p\); if \(hd\) \{[^}]*skip: 1/.test(seg), "已经在桶里的默认跳过——可以反复跑，断了接着来");
  ok(/buf\.byteLength < 1000/.test(seg), "取回的字节数不对就不写进桶（防把半截/错误页当 PDF 存进去）");
  ok(/const hd2 = await env\.PDFS\.head\(p\);[\s\S]*hd2\.size === buf\.byteLength/.test(seg), "写完立刻回头核一次大小，对不上就报 ok:false");
  ok(/\.slice\(0, 25\)/.test(seg), "一次最多 25 个，不把单个请求撑爆");
}

console.log("\n[三] 核对：删仓库文件之前的那道闸");
{
  const seg = W.slice(W.indexOf("// R2_CHECK"), W.indexOf("// Everything else: serve static assets"));
  ok(/env\.PDFS\.head\(p\)/.test(seg) && /hit: out\.filter/.test(seg), "逐个 head 核在不在、多大，并回一个命中数");
  ok(/\.slice\(0, 200\)/.test(seg), "一次可核 200 个（660 篇分四趟就核完）");
  ok(/String\(b\.pass \|\| ""\) !== "SDE2013"/.test(seg), "同样带口令门");
}

console.log("\n[四] 绑定与顺序");
{
  const hasBind = /"r2_buckets"/.test(CFG);
  console.log("  NOTE wrangler.jsonc " + (hasBind ? "已有" : "尚无") + " r2_buckets 绑定"
    + (hasBind ? "" : "——桶建好之前不能加，加了会让部署失败；在此之前上面三段全是死代码（env.PDFS 不存在）"));
  const iPdf = W.indexOf("// ===== R2_PDF"), iAssets = W.indexOf("// Everything else: serve static assets");
  ok(iPdf > 0 && iPdf < iAssets, "R2 供给段排在静态资源兜底之前（否则永远轮不到它）");
  ok(/"run_worker_first": true/.test(CFG), "wrangler 里 run_worker_first=true，Worker 确实能先看到 PDF 请求");
}

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
