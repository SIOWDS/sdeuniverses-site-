/* sim_portal_gate.js —— 入口层「什么时候该出现」的验收
 *
 * 用户定的（2026-07-31）：**输入 sdeuniverses.com 打开，见到的应该是入口**；
 * 从入口再点进浏览、微信、对话这三大功能体系。
 *
 * 所以规矩是：从站外进来或刷新根地址，每次都拦；只有站内点回首页、且这一会话
 * 已经进过门，才放行——否则每点一次"首页"都被拦一道，门就成了路障。
 *
 * 跑法：node tools/sim_portal_gate.js
 */
"use strict";
var fs = require("fs");
var path = require("path");
var SRC = path.join(__dirname, "..", "public", "assets", "sde-portal.js");
var src = fs.readFileSync(SRC, "utf8");

var pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; console.log("  PASS  " + name); }
  else { fail++; console.log("  FAIL  " + name + (extra ? "   " + extra : "")); }
}
function grab(re, what) {
  var m = src.match(re);
  if (!m) { console.log("  FAIL  取不到 " + what); process.exit(1); }
  return m;
}
var shouldOpen = eval("(" + grab(/function shouldOpen\(env\) \{[\s\S]*?\n  \}\n/, "shouldOpen")[0] + ")");
var sameOrigin = eval("(" + grab(/function sameOrigin\(ref, origin\) \{[\s\S]*?\n  \}\n/, "sameOrigin")[0] + ")");
var NODES = eval("(" + grab(/var NODES = (\[[\s\S]*?\n  \]);/, "NODES")[1] + ")");
var GO = eval("(" + grab(/var GO = (\{[^}]*\});/, "GO")[1] + ")");

function E(o) {
  return { force: !!o.force, path: o.path || "/", seen: !!o.seen,
           navType: o.navType || "navigate", internal: !!o.internal };
}

console.log("[进门：输入域名就该见到入口]");
ok("直接输地址（无 referrer）→ 拦", shouldOpen(E({})) === true);
ok("直接输地址、这一会话已进过门 → 还是拦（每次进门都见门）",
   shouldOpen(E({ seen: true })) === true);
ok("从搜索结果/外链进来 → 拦", shouldOpen(E({ internal: false, seen: true })) === true);
ok("新标签页打开根地址 → 拦", shouldOpen(E({ navType: "navigate" })) === true);
ok("刷新根地址 → 拦（刷新＝重新进门）", shouldOpen(E({ navType: "reload", seen: true })) === true);
ok("/index.html 与 / 一视同仁", shouldOpen(E({ path: "/index.html" })) === true);

console.log("[站内走动：门不能变成路障]");
ok("站内点回首页、已进过门 → 放行", shouldOpen(E({ internal: true, seen: true })) === false);
ok("站内点到首页、但这一会话还没进过门 → 仍要拦",
   shouldOpen(E({ internal: true, seen: false })) === true);
ok("后退回首页、已进过门 → 放行",
   shouldOpen(E({ navType: "back_forward", internal: true, seen: true })) === false);
ok("后退回首页、还没进过门 → 拦",
   shouldOpen(E({ navType: "back_forward", seen: false })) === true);

console.log("[别的页面一律放行]");
["/students/", "/column/x/", "/sde-wechat/", "/taste/wds-chat/", "/books/m/48/"].forEach(function (p) {
  ok(p + " 不拦", shouldOpen(E({ path: p })) === false);
});
ok("内页也不受 seen 影响", shouldOpen(E({ path: "/health/", seen: false })) === false);

console.log("[?portal=1 永远能回看]");
ok("根地址带 ?portal=1 → 拦", shouldOpen(E({ force: true, seen: true, internal: true })) === true);
ok("内页带 ?portal=1 也拦（专供回看）",
   shouldOpen(E({ force: true, path: "/students/" })) === true);

console.log("[referrer 判本站：不许被仿冒域名骗过去]");
var O = "https://sdeuniverses.com";
ok("本站页面算站内", sameOrigin(O + "/column/x/", O) === true);
ok("本站根算站内", sameOrigin(O + "/", O) === true);
ok("空 referrer 不算站内", sameOrigin("", O) === false);
ok("外站不算站内", sameOrigin("https://www.google.com/", O) === false);
ok("⚠ 前缀相同的仿冒域名不算站内", sameOrigin("https://sdeuniverses.com.evil.example/", O) === false);
ok("末尾无斜杠也认", sameOrigin(O, O) === true);

console.log("[三大功能体系的去处]");
ok("三个入口，一个不多一个不少", NODES.length === 3, NODES.map(function (n) { return n.k; }).join("/"));
ok("浏览＝就地揭开首页（不跳转，不再加载一次首页）", GO.browse === "");
ok("微信 → /sde-wechat/", GO.im === "/sde-wechat/");
ok("对话 → /taste/wds-chat/", GO.wds === "/taste/wds-chat/");
ok("每个入口都有去处（GO 的键与 NODES 对得上）",
   NODES.every(function (n) { return Object.prototype.hasOwnProperty.call(GO, n.k); }));

console.log("[接线]");
ok("真的用 shouldOpen(readEnv()) 把关", /if \(!shouldOpen\(readEnv\(\)\)\) return;/.test(src));
ok("⚠ 不再是「一会话只拦一次」那句老判断",
   !/if \(!FORCE && sessionStorage\.getItem\(KEY\)\) return;/.test(src));
ok("readEnv 读的是 referrer / sessionStorage / navigation 三样",
   /document\.referrer/.test(src) && /sessionStorage\.getItem\(KEY\)/.test(src) &&
   /getEntriesByType\("navigation"\)/.test(src));
ok("老浏览器有 performance.navigation 兜底", /performance\.navigation\.type === 1 \? "reload"/.test(src));
ok("点进任一入口都记一笔「进过门」", /a\.onclick = function \(\) \{ seen\(\);/.test(src));
ok("「直接浏览 ›」与 Esc 也记", /skip\.onclick = function \(\) \{ seen\(\); close\(\); \}/.test(src) &&
   /e\.key === "Escape"\) \{ seen\(\); close\(\); \}/.test(src));

console.log("\n" + pass + " PASS / " + fail + " FAIL");
process.exit(fail ? 1 : 0);
