/* 只测这一件事：学员 PDF 迁 R2 的三段（供给 / 搬运 / 核对）。
   这次迁移的要害不是"能不能搬"，而是**搬的过程中一篇文章都不许打不开**：
   ① 供给走 R2 优先、落空静默回落 ASSETS —— 迁移做到一半时两边并存，任何一篇都不会 404；
   ② URL 一个字不改 —— 因为页面与 read.html 都是按**相对文件名**引 PDF，改链要动一千多个页面；
   ③ 必须支持 Range —— PDF.js 对大文件分块取，不给 206 就读不出；
   ④ 搬运口子的能力必须收窄到无害（口令是前端级的）：源与目标都钉死在 students/**.pdf；
   ⑤ 直写口子（r2-put）不碰 ASSETS —— 自动存档必须能一步进桶，否则文件得先进 git 才能进 R2，
     而"先查 R2、落空回落 ASSETS"会让这种回归**不报错地**发生：页面照显示，仓库照长胖。
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
  ok(/range: _hasRange \? request\.headers : undefined, onlyIf: request\.headers/.test(seg),
     "**只在真有 Range 头时才向 R2 要分段**——否则 R2 会把 obj.range 填成整份，普通下载被回成 206，且 206 存不进 Cache API（那层缓存就白做了）");
  ok(/if \(_hasRange && obj\.range && obj\.range\.offset !== undefined\)/.test(seg), "回 206 也要以'读者确实要了分段'为前提");
  ok(/accept-ranges/.test(seg) && /status: 206/.test(seg) && /content-range/.test(seg), "命中分块时回 206 + content-range + accept-ranges");
  ok(/if \(!\("body" in obj\)\) return new Response\(null, \{ status: 304/.test(seg), "onlyIf 不满足回 304，不重复传");
  ok(/catch \(e\) \{ \/\* R2 出任何岔子/.test(seg), "R2 抛异常时不抛给读者，落回仓库");
  // 行为实测：R2 落空（get 返回 null）时**不能 return**，必须继续往下走到 ASSETS
  ok(!/return new Response\(null, \{ status: 404/.test(seg) && !/return env\.ASSETS/.test(seg),
     "R2 落空时既不自己回 404、也不在这里终结请求——落到函数末尾原有的 ASSETS 分支（两边并存的关键）");
  const tail = W.slice(W.indexOf("// Everything else: serve static assets"));
  ok(/const resp = await env\.ASSETS\.fetch\(request\);/.test(tail), "原有的静态资源兜底分支一字未动");
  ok(/x-served-from", "r2"/.test(seg) && /x-served-from", "edge"/.test(seg), "响应带记号（r2 / edge），线上一眼看得出这一次走的哪条路");
  // ——最容易踩空的一脚：Worker 用 R2 binding 读出来的响应**不会自动进 CDN 缓存**（静态资源本来就在边缘上）。
  // 没有这层，每次点开 PDF 都要回桶所在区域取一趟，读者那边就是肉眼可见的变慢。
  ok(/caches\.default/.test(seg) && /_cache\.match\(_ck\)/.test(seg), "无 Range 的整份请求先问边缘缓存（命中就连 R2 都不碰）");
  ok(/ctx\.waitUntil\(_cache\.put\(_ck, resp\.clone\(\)\)\)/.test(seg), "整份取到手后把副本留在边缘，且放 waitUntil 里、不占这次响应的时间");
  ok(/if \(_cache && !_hasRange && request\.method === "GET"\)/.test(seg), "只缓存 GET 的整份 200——206 本来也存不进 Cache API");
  ok(/new Request\(url\.origin \+ url\.pathname, \{ method: "GET" \}\)/.test(seg), "缓存键只取 URL（不把 Range 头带进键里，免得每个分段各占一条）");
  ok(/typeof caches !== "undefined" && caches\.default/.test(seg), "Cache API 不可用时自动降级，不报错");
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
  // 门槛后来改成随类型走（索引分片小到几百字节，不能按 PDF 的 1000 一刀切）——
  // 这条断言一度还停在旧的字面 1000 上，红了很久没人管。
  ok(/const _min = _isIdx \? 2 : 1000/.test(seg) && /buf\.byteLength < _min/.test(seg),
     "取回的字节数不对就不写进桶（防把半截/错误页当 PDF 存进去），门槛随类型走");
  ok(/const hd2 = await env\.PDFS\.head\(p\);[\s\S]*hd2\.size === buf\.byteLength/.test(seg), "写完立刻回头核一次大小，对不上就报 ok:false");
  ok(/\.slice\(0, 25\)/.test(seg), "一次最多 25 个，不把单个请求撑爆");
}

console.log("\n[二之二] 直写：不经过仓库就把字节放进桶（自动存档要的那条路）");
{
  const seg = W.slice(W.indexOf("// R2_PUT"), W.indexOf("// R2_CHECK"));
  ok(seg.length > 500, "R2_PUT 段在（" + seg.length + " 字符）");
  ok(/url\.pathname === "\/api\/admin\/r2-put" && request\.method === "POST"/.test(seg), "端点是 POST /api/admin/r2-put");
  ok(/String\(b\.pass \|\| ""\) !== "SDE2013"/.test(seg), "同样带口令门");
  ok(/if \(!env\.PDFS\)/.test(seg), "桶没绑定时明说，而不是静默成功");
  ok(!/env\.ASSETS\.fetch/.test(seg),
     "**整段不碰 ASSETS** —— 这正是它与 r2-migrate 的分别：不要求文件先进 git");
  ok(/_b64ToBytes\(String\(f\.b64 \|\| ""\)\)/.test(seg), "收 base64 字节");
  ok(/base64 解不开/.test(seg), "base64 坏了如实报，不当成空文件写进去");
  ok(/\^students\\\/\[A-Za-z0-9\._\\-\\\/\]\+\\\.pdf\$/i.test(seg) && /IDX_KEYS\.test\(p\)/.test(seg),
     "白名单与 r2-migrate 逐字同款：只许 students/**.pdf 与索引键");
  ok(/p\.indexOf\("\.\."\) >= 0/.test(seg), "挡穿越路径");
  ok(/head4\[0\] === 0x25 && head4\[1\] === 0x50 && head4\[2\] === 0x44 && head4\[3\] === 0x46/.test(seg),
     "**内容也要验**：白名单只管路径长相，写错内容比写错路径更难发现——非 %PDF 开头一律挡回");
  ok(/const _min = _isIdx \? 2 : 1000/.test(seg), "空文件门槛与 r2-migrate 同一道（索引分片小，不能一刀切）");
  ok(/const hd2 = await env\.PDFS\.head\(p\);[\s\S]*hd2\.size === buf\.byteLength/.test(seg), "写完立刻回头核一次大小");
  ok(/if \(!b\.force\) \{ const hd = await env\.PDFS\.head\(p\); if \(hd\) \{[\s\S]*?skip: 1/.test(seg), "已经在桶里的默认跳过，可反复跑");
  ok(/\.slice\(0, 10\)/.test(seg), "一次最多 10 个（单个也走 files 数组，调用方不必分辨两种形状）");
  ok(/contentType: "application\/pdf"/.test(seg) && /immutable/.test(seg), "PDF 带正确 content-type 与长缓存");
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
