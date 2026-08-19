/* sim_portal_gate.js —— 入口层「什么时候该出现」的验收
 *
 * 用户定的（2026-07-31）：**这个入口严格对应 sdeuniverses.com，而且是唯一对应。**
 * 于是门规只剩一条：域名根地址每一次打开都是入口；除了根地址，别的地址一概不是入口。
 * 从前那些分叉（?portal=1 第二门牌、referrer 判站内、navigation type、
 * sessionStorage 记「这一会话进过门没有」）全部作废——一个入口只能有一个地址，
 * 一个地址也只能对着一件事。
 *
 * 跑法：node tools/sim_portal_gate.js
 */
"use strict";
var fs = require("fs");
var path = require("path");
var ROOT = path.join(__dirname, "..");
var SRC = path.join(ROOT, "public", "assets", "sde-portal.js");
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
var NODES = eval("(" + grab(/var NODES = (\[[\s\S]*?\n  \]);/, "NODES")[1] + ")");
var GO = eval("(" + grab(/var GO = (\{[^}]*\});/, "GO")[1] + ")");

/* 门规现在只看一样东西：路径。所以 env 里多塞什么都不该改变结论——
   下面几组刻意把从前起作用的四个变量都塞进来，验它们确实**不再**起作用。 */
function E(o) {
  o = o || {};
  return { path: o.path || "/", force: !!o.force, seen: !!o.seen,
           navType: o.navType || "navigate", internal: !!o.internal };
}

console.log("[域名根地址 —— 每一次都是入口]");
ok("直接输 sdeuniverses.com（无 referrer）→ 拦", shouldOpen(E({})) === true);
ok("这一会话已经进过门 → 还是拦（不再记 seen）", shouldOpen(E({ seen: true })) === true);
ok("刷新根地址 → 拦", shouldOpen(E({ navType: "reload", seen: true })) === true);
ok("后退回到根地址 → 拦", shouldOpen(E({ navType: "back_forward", seen: true })) === true);
ok("⚠ 站内点“首页”回来 → 一样拦（严格对应：这个地址就是入口）",
   shouldOpen(E({ internal: true, seen: true })) === true);
ok("从搜索结果/外链/书签进来 → 拦", shouldOpen(E({ internal: false, seen: true })) === true);
ok("/index.html 与 / 一视同仁（边缘已 307 到 /，这里是双保险）",
   shouldOpen(E({ path: "/index.html", seen: true })) === true);

console.log("[除了根地址，别的地址一概不是入口]");
["/students/", "/column/x/", "/sde-wechat/", "/taste/chatsde/", "/books/m/48/", "/index.htm", "//"]
  .forEach(function (p) { ok(p + " 不是入口", shouldOpen(E({ path: p })) === false); });
ok("⚠ 内页带 ?portal=1 也不是入口（第二门牌已作废）",
   shouldOpen(E({ path: "/students/", force: true })) === false);
ok("内页不受 seen / navType 影响",
   shouldOpen(E({ path: "/health/", seen: false, navType: "reload" })) === false);

/* ── 浏览页有自己的门牌 /browse/（2026-07-31）────────────────────────────
 * 根地址严格且唯一地属于入口页，那浏览页就不能也叫根地址——否则收藏、分享、
 * 刷新拿到的都是"入口"，而人明明在浏览页。揭开门之后地址换成 /browse/，
 * worker 让这个地址返回同一份首页 HTML，所以不必真跳转。            */
ok("/browse/ 不是入口，不开门", shouldOpen(E({ path: "/browse/" })) === false);
ok("/browse 不带尾斜杠也不开门", shouldOpen(E({ path: "/browse" })) === false);
ok("在 /browse/ 刷新照样不开门（这正是它有自己网址的意义）",
   shouldOpen(E({ path: "/browse/", navType: "reload" })) === false);
var BROWSE = (src.match(/var BROWSE = "([^"]+)"/) || [, ""])[1];
ok("BROWSE 门牌是 /browse/，实得 " + BROWSE, BROWSE === "/browse/");
var closeBody = (src.match(/function close\(\) \{[\s\S]*?\n    \}/) || [, ""])[0];
/* 2026-08-18 口径变更（用户裁定「长滚动那页意义不大了」）：入口页拆成独立的轻量
   HTML，这一层底下**不再有浏览页可揭**。于是旧的两条断言（close 里 replaceState、
   不许出现 location.href）随口径作废——它们钉的正是"就地揭开"那套做法。
   新口径下 close() 只剩一件事：离开这一页去 /browse/。 */
ok("close() 是真的离开这一页去 BROWSE（不再是就地揭开）",
   /location\.href = BROWSE;/.test(closeBody));
ok("⚠ close() 里不再改地址栏冒充跳转（replaceState 那套已作废）",
   !/replaceState/.test(closeBody));
ok("走完退场动画再走（不硬切画面）", /setTimeout\(function \(\) \{[\s\S]{0,120}location\.href = BROWSE/.test(closeBody));
ok("现在只剩 Esc 走 close（三个入口卡本身都是真 <a>）",
   /e\.key === "Escape"[\s\S]{0,40}close\(\)/.test(src) &&
   !/if \(!href\) close\(\);/.test(src));
ok("⚠ 底部不再是「直接浏览」那颗按钮（旧口径必须从源码里消失）",
   !/skip\.onclick/.test(src) && !/createElement\("button"\)/.test(src));
var ABOUT = (src.match(/var ABOUT = "([^"]+)"/) || [, ""])[1];
ok("平台介绍的门牌是 /about/，实得 " + ABOUT, ABOUT === "/about/");
ok("底部那颗是真链接（<a href=ABOUT>），不是 button——要能中键新开、右键复制",
   /about = document\.createElement\("a"\)/.test(src) && /about\.href = ABOUT;/.test(src) &&
   /foot\.appendChild\(about\)/.test(src));
ok("⚠ 它不走 close()（是真跳转，不是就地揭开）", !/about\.onclick/.test(src));
ok(".sdep-skip 挂到 <a> 上之后补了 inline-block 与去下划线",
   /\.sdep-skip\{display:inline-block;text-decoration:none;/.test(src));
{
  var fsA = require("fs"), pA = path.join(ROOT, "public", "about", "index.html");
  ok("平台介绍页真的存在", fsA.existsSync(pA));
  var A = fsA.existsSync(pA) ? fsA.readFileSync(pA, "utf8") : "";
  ok("平台介绍页引了两张图（三位一体 / 文明增长飞轮）",
     /\/about\/trinity\.svg/.test(A) && /\/about\/flywheel\.svg/.test(A));
  ok("两张 SVG 文件都在", fsA.existsSync(path.join(ROOT, "public", "about", "trinity.svg")) &&
     fsA.existsSync(path.join(ROOT, "public", "about", "flywheel.svg")));
  ok("平台介绍页挂了三态面板脚本 wds-mode.js", /wds-mode\.js\?v=/.test(A));
  var plain = A.replace(/<[^>]+>/g, "").replace(/\s/g, "");
  ok("正文体量达到「两万字」口径，实得 " + plain.length, plain.length >= 19000);
}
{
  var W = fs.readFileSync(path.join(ROOT, "src", "worker.js"), "utf8");
  /* 2026-08-18：入口与浏览各是各的一页，worker 不再让两个地址取同一份 HTML。
     /home/ 仍原地取根那一份（＝轻量入口页）；/browse/ 是真目录页，只在没有尾斜杠时补一下。 */
  ok("worker 让 /home/（带不带尾斜杠）原地取根那一份", /\/\^\\\/home\\\/\?\$\//.test(W));
  ok("worker 不再把 /browse/ 改写成根（它现在是真的一页）",
     !/\(browse\|home\)/.test(W) && /url\.pathname === "\/browse"/.test(W));
  ok("worker 仍是原地取内容，不是 30x 跳转",
     /assetReq = new Request\(new URL\("\/", url\), request\)/.test(W) &&
     !/browse[\s\S]{0,200}status:\s*30\d/.test(W));
  ok("改写后的请求确实喂给了 ASSETS", /env\.ASSETS\.fetch\(assetReq\)/.test(W));
}

/* ── 全站扫描：回「浏览」的一律指 /browse/，只有回「系统入口」才进 /home/ ──────
 * 用户 2026-07-31 定的分工。裸 href="/" 现在是个 bug：站标、页脚站名、板块锚点
 * 点下去会落到裸域名 → 当场触发开门，人明明只是想回浏览页。
 * 尤其是 /#taste 这类锚点：在 /browse/ 页上点它会整页跳走再被弹一次门。 */
{
  var walk = function (dir, out) {
    fs.readdirSync(dir, { withFileTypes: true }).forEach(function (e) {
      var full = path.join(dir, e.name);
      if (e.isDirectory()) walk(full, out);
      else if (e.name.endsWith(".html")) out.push(full);
    });
    return out;
  };
  var pages = walk(path.join(ROOT, "public"), []);
  var bare = 0, anchor = 0, browse = 0;
  pages.forEach(function (f) {
    var t = fs.readFileSync(f, "utf8");
    bare += (t.match(/href="\/"/g) || []).length;
    anchor += (t.match(/href="\/#/g) || []).length;
    browse += (t.match(/href="\/browse\//g) || []).length;
  });
  ok("扫到的页面数够多（防止空集假通过），实得 " + pages.length, pages.length > 2000);
  ok("全站没有裸 href=\"/\"（回浏览要指 /browse/），实得 " + bare, bare === 0);
  ok("全站没有 href=\"/#锚点\"（同上，且它会把人弹出 /browse/），实得 " + anchor, anchor === 0);
  ok("确实换成了 /browse/，实得 " + browse + " 处", browse > 2000);
}

console.log("[唯一对应：从前那些分叉必须真的从源码里消失]");
/* 这条断言只挑“调用形态”，不挑关键词：源码的注释里还留着 /?portal=1 的来龙去脉，
   而地址栏归一那段又要正当地读一次 location.search——按关键词断言必假失败。 */
ok("⚠ 没有 ?portal=1 这个第二门牌了（不再按 search 判门）",
   !/var FORCE/.test(src) && !/env\.force/.test(src) && !/portal=1\/\.test/.test(src));
ok("location.search 只剩地址栏归一那一处用途",
   (src.match(/location\.search/g) || []).length === 1);
ok("⚠ 不再记「这一会话进过门没有」", !/sessionStorage/.test(src) && !/sde_portal_seen/.test(src));
ok("⚠ 不再看 referrer 判站内", !/document\.referrer/.test(src) && !/sameOrigin\(/.test(src));
ok("⚠ 不再看 navigation type（刷新/前进后退不再分家）",
   !/getEntriesByType\(/.test(src) && !/performance\.navigation/.test(src));
// 2026-07-31 用户改口径：「入口页用 home，输入 sdeuniverses.com 就自动进入 home 页」。
// 于是入口认四种写法（裸域名／index.html／/home／/home/），落地后地址栏改写成 /home/。
ok("shouldOpen 只吃 path 一个字段（不看 referrer / navType / seen）",
   /function shouldOpen\(env\) \{[\s\S]{0,220}?\}/.test(src) &&
   !/env\.(force|seen|navType|ref)/.test((src.match(/function shouldOpen\(env\) \{[\s\S]*?\n  \}/) || [""])[0]));
ok("裸域名开门", shouldOpen(E({ path: "/" })) === true);
ok("/home/ 开门", shouldOpen(E({ path: "/home/" })) === true);
ok("/home 不带尾斜杠也开门", shouldOpen(E({ path: "/home" })) === true);
ok("/index.html 仍兜底开门", shouldOpen(E({ path: "/index.html" })) === true);
ok("⚠ /browse/ 依旧不开门（它是浏览页，不是入口）", shouldOpen(E({ path: "/browse/" })) === false);

console.log("[地址栏也归一：入口露面时地址正好是 sdeuniverses.com/home/]");
var HOME = (src.match(/var HOME = "([^"]+)"/) || [, ""])[1];
ok("HOME 门牌是 /home/，实得 " + HOME, HOME === "/home/");
ok("有 replaceState 归一这一段，且归到 HOME", /history\.replaceState\(null, "", HOME\)/.test(src));
ok("三种不干净的地址都覆盖到（路径不是 /home/ · 带 query · 带 #hash）",
   /location\.pathname !== HOME \|\| location\.search \|\| location\.hash/.test(src));
ok("⚠ 归一目标不再是裸域名（否则输了域名地址栏还是光秃秃的）",
   !/history\.replaceState\(null, "", "\/"\)/.test(src));
ok("⚠ 用 replaceState 而不是跳转（不多发一次请求、不在后退历史里多留一格）",
   !/location\.replace\(/.test(src) && !/location\.href = "\/"/.test(src));
ok("归一发生在开门判定之后（不开门的页面地址不许动）",
   src.indexOf('history.replaceState') > src.indexOf("if (!shouldOpen(readEnv())) return;"));

console.log("[站内那颗回入口的 △ 也指同一个地址]");
[["public/assets/sde-modes.js", /var PORTAL = "\/home\/";/],
 ["public/wds-mode.js", /var PORTAL_URL = "\/home\/";/]].forEach(function (t) {
  var s = fs.readFileSync(path.join(ROOT, t[0]), "utf8");
  ok(t[0] + " 的回入口按钮指向 /home/", t[1].test(s));
  ok(t[0] + " 里没有 /?portal=1 残留", s.indexOf("/?portal=1") < 0);
});

console.log("[三大功能体系的去处]");
ok("三个入口，一个不多一个不少", NODES.length === 3, NODES.map(function (n) { return n.k; }).join("/"));
/* 旧断言「浏览＝就地揭开首页」随 2026-08-18 的拆分作废：当时不揭开就得再加载一次
   893KB 的首页，所以宁可就地揭；现在入口页只有几 KB、浏览页只有几十 KB，
   真跳转反而更省，而且三个入口终于形态一致（都能中键新开、右键复制）。 */
ok("浏览 → /browse/（栏目总目录，真跳转）", GO.browse === "/browse/");
ok("⚠ 三个入口没有一个是空去处了（空值＝就地揭开的旧做法）",
   Object.keys(GO).every(function (k) { return !!GO[k]; }));
ok("微信 → /sde-wechat/", GO.im === "/sde-wechat/");
ok("对话 → /taste/chatsde/（更名后的正式门牌）", GO.wds === "/taste/chatsde/");
ok("每个入口都有去处（GO 的键与 NODES 对得上）",
   NODES.every(function (n) { return Object.prototype.hasOwnProperty.call(GO, n.k); }));

console.log("[接线]");
ok("真的用 shouldOpen(readEnv()) 把关", /if \(!shouldOpen\(readEnv\(\)\)\) return;/.test(src));
ok("⚠ 不再是「一会话只拦一次」那句老判断",
   !/if \(!FORCE && sessionStorage\.getItem\(KEY\)\) return;/.test(src));
ok("入口卡不再挂 onclick（三个都是真链接，交给浏览器走），Esc 仍走 close",
   !/a\.onclick =/.test(src) &&
   /e\.key === "Escape"\) \{ close\(\); \}/.test(src) &&
   !/ seen\(\);/.test(src));

console.log("[不允许先闪一下浏览页]");
/* 输完域名回车，第一眼就该是入口。defer 是“整页解析完才执行”，
   浏览器会先把浏览页画出来再盖上门——这正是用户看见的那一闪。 */
var IDX = fs.readFileSync(path.join(ROOT, "public", "index.html"), "utf8");
var tag = (IDX.match(/<script[^>]*sde-portal\.js[^>]*>/) || [""])[0];
ok("首页确实引了入口脚本", !!tag, tag);
ok("⚠ 引入时**不得**带 defer（defer = 先渲染整页再执行 = 必闪）", !/\bdefer\b/.test(tag), tag);
ok("⚠ 也不得带 async（同样不保证在 <body> 之前跑）", !/\basync\b/.test(tag), tag);
ok("脚本写在 </head> 之前（正文一行都没开始渲染）",
   IDX.indexOf(tag) < IDX.indexOf("</head>"));

ok("有 lockPage / unlockPage 一对", /function lockPage\(\)/.test(src) && /function unlockPage\(\)/.test(src));
ok("⚡ 判定要开门之后立刻按住（lockPage 在 mount 之前就调）",
   src.indexOf("\n  lockPage();") > src.indexOf("if (!shouldOpen(readEnv())) return;") &&
   src.indexOf("\n  lockPage();") < src.indexOf("function mount()"));
ok("不开门就不按（return 在 lockPage 之前）",
   src.indexOf("if (!shouldOpen(readEnv())) return;") < src.indexOf("\n  lockPage();"));
ok("按住的是页面本体、放行的是入口那一层",
   /html\.sdep-hold body\{visibility:hidden\}/.test(src) &&
   /html\.sdep-hold body \.sdep\{visibility:visible\}/.test(src));
ok("按住期间背景就是入口的暗底（不会先白一下）",
   /html\.sdep-hold\{background:#0C0906;overflow:hidden\}/.test(src));
ok("用 visibility 而不是 display（揭开时不用重排）",
   !/html\.sdep-hold body\{display:none/.test(src));
ok("入口一上屏就松手", /document\.body\.appendChild\(box\);\s*\n\s*unlockPage\(\);/.test(src));
ok("按住着进场时不做整层淡入（否则那半秒会把下面透出来）",
   /box\.className = HOLD \? "sdep nofade" : "sdep";/.test(src) && /\.sdep\.nofade\{animation:none\}/.test(src));
ok("⚡ 有看门狗兜底（mount 没跑成也不会一直黑着）", /setTimeout\(unlockPage, \d+\);/.test(src));
ok("⚡ <body> 一出现就挂，不等 DOMContentLoaded（首页 HTML 四十多万字符）",
   /function whenBody\(\)[\s\S]{0,140}document\.body\) \{ mount\(\); return; \}/.test(src) &&
   !/addEventListener\("DOMContentLoaded", mount\)/.test(src));
ok("语言判定推迟到用的时候（现在脚本跑在 <body> 之前，模块层问 body 会问到空）",
   /var L = null;/.test(src) && /if \(L === null\) L = lang\(\);/.test(src));

console.log("\n" + pass + " PASS / " + fail + " FAIL");
process.exit(fail ? 1 : 0);
