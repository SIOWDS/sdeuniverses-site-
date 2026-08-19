/* sim_static_cache.js —— 静态资源缓存分流 与 主页图片负担 的源码检视式模拟。
 *
 * 守的是两条容易悄悄回归的纪律：
 *   1) HTML 永远 no-store（推上去就得是最新版），而图片/字体这类几乎不变的东西
 *      给 30 天缓存——**.js/.css 绝不能混进长缓存那一档**，否则改了代码用户拿不到新版，
 *      而且这种回归不会自己暴露：页面照常显示，只是显示的是旧的。
 *   2) 主页不许再挂没懒加载的图，也不许再直接引用 og.png（那是 2.25MB 的社交分享原图，
 *      当页面配图用会让每个首访者白下 2MB）。
 *
 * 用法：node tools/sim_static_cache.js
 */
const fs = require("fs");
const path = require("path");

let pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; console.log("  PASS  " + name); }
  else { fail++; console.log("  FAIL  " + name + (extra ? "  → " + extra : "")); }
}

const root = path.join(__dirname, "..");
const worker = fs.readFileSync(path.join(root, "src/worker.js"), "utf8");
const home = fs.readFileSync(path.join(root, "public/index.html"), "utf8");

console.log("\n── 一、worker 静态出口的缓存分流 ──");

const m = worker.match(/if \(\/\\\.\(([^)]+)\)\$\/i\.test\(url\.pathname\)\)/);
ok("图片/字体分流的扩展名正则存在", !!m);
const exts = m ? m[1].split("|") : [];

// 该长缓存的
for (const e of ["png", "webp", "svg", "woff2?", "ico"]) {
  ok(`  ${e} 在长缓存档内`, exts.includes(e), exts.join("|"));
}
ok("  jpe?g 在长缓存档内", exts.includes("jpe?g"), exts.join("|"));

// 绝不能长缓存的（命门）
for (const e of ["js", "css", "mjs", "html", "json"]) {
  ok(`  ${e} 不在长缓存档内（命门）`, !exts.includes(e), exts.join("|"));
}

ok("长缓存用 30 天而非 immutable/一年（同名替换要能见新版）",
  /max-age=2592000/.test(worker) && !/max-age=31536000, immutable[\s\S]{0,200}url\.pathname/.test(worker));

ok("HTML 仍然 no-store", /text\/html[\s\S]{0,400}no-store, no-cache, must-revalidate, max-age=0/.test(worker));
ok("HTML 仍然剥掉 etag/last-modified", /headers\.delete\("etag"\)/.test(worker) && /headers\.delete\("last-modified"\)/.test(worker));
ok("缓存分流排在 HTML 分支之后、兜底 return 之前",
  worker.indexOf("max-age=2592000") > worker.indexOf("no-store, no-cache, must-revalidate") &&
  worker.lastIndexOf("return resp;") > worker.indexOf("max-age=2592000"));
ok("新响应用了独立变量名，没覆盖外层 r/resp", /const r2 = new Response\(resp\.body, resp\)/.test(worker));

console.log("\n── 二、主页图片负担 ──");

const imgs = home.match(/<img\b[^>]*>/g) || [];
ok("主页确实有 img 标签", imgs.length > 0, String(imgs.length));
const eager = imgs.filter((t) => !/loading=/.test(t));
ok("主页每张 img 都带 loading（无 eager 漏网）", eager.length === 0, eager.slice(0, 3).join(" | "));
ok("主页不再直接引用 og.png（2.25MB 社交原图）", !/marriage-happiness\/og\.png/.test(home));
ok("主页改用压缩版 card.webp", /marriage-happiness\/card\.webp/.test(home));
ok("webp 有 jpg 兜底（picture/source 成对）",
  (home.match(/<picture>/g) || []).length === (home.match(/<\/picture>/g) || []).length &&
  /<source srcset="\/marriage-happiness\/card\.webp" type="image\/webp">/.test(home) &&
  /src="\/marriage-happiness\/card\.jpg"/.test(home));
ok("卡片图带 width/height（防布局跳动）", /card\.jpg"[^>]*width="1200"[^>]*height="628"/.test(home));

console.log("\n── 三、压缩版图确实在仓库里且真的小 ──");
for (const [f, cap] of [["public/marriage-happiness/card.webp", 120000], ["public/marriage-happiness/card.jpg", 200000]]) {
  const p = path.join(root, f);
  const exists = fs.existsSync(p);
  ok(`${f} 存在`, exists);
  if (exists) ok(`${f} 小于 ${cap / 1000}KB`, fs.statSync(p).size < cap, fs.statSync(p).size + " B");
}
const og = path.join(root, "public/marriage-happiness/og.png");
ok("og.png 仍保留（25 个专栏页的 og:image 靠它）", fs.existsSync(og));

console.log("\n" + "═".repeat(52));
console.log(`  ${pass} PASS   ${fail} FAIL`);
console.log("═".repeat(52) + "\n");
process.exit(fail ? 1 : 0);
