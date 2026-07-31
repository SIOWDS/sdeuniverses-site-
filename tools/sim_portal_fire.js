/* sim_portal_fire.js —— 入口页「烧 TOKEN」的火色与火星验收
 *
 * 用户定的（2026-07-31）：**浏览烧绿 · 对话烧红 · 微信烧蓝**，粒子要更大、四射的半径要更远。
 * 这里逐条钉死，免得日后调色时把三色调回一锅橙火、或把粒子调回原来那点大小。
 *
 * 注意：火色（FIRE）与节点色相（NODES[].c ＝ 青/金/紫）是两回事——
 *       色相标身份，火色标烧的是哪一种 TOKEN。两者不许互相“对齐”。
 *
 * 跑法：node tools/sim_portal_fire.js
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

var FIRE = eval("(" + grab(/var FIRE = (\{[\s\S]*?\n  \});/, "FIRE")[1] + ")");
var rgba = eval("(" + grab(/function rgba\(hex, a\) \{[\s\S]*?\n  \}\n/, "rgba")[0] + ")");
var SPARK_N = parseInt(grab(/var SPARK_N = (\d+), SPARK_R0 = (\d+);/, "SPARK_N")[1], 10);
var SPARK_R0 = parseInt(grab(/var SPARK_N = \d+, SPARK_R0 = (\d+);/, "SPARK_R0")[1], 10);
var sparkVec = eval("(" + grab(/function sparkVec\(s\) \{[\s\S]*?\n  \}\n/, "sparkVec")[0] + ")");

function rgb(hex) {
  var n = parseInt(hex.slice(1), 16);
  return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 };
}

console.log("[三色 TOKEN —— 浏览绿 · 对话红 · 微信蓝]");
ok("三个入口各有一组火色", !!(FIRE.browse && FIRE.wds && FIRE.im));
[["browse", "绿", "g"], ["wds", "红", "r"], ["im", "蓝", "b"]].forEach(function (t) {
  var key = t[0], zh = t[1], ch = t[2];
  var arr = FIRE[key] || [];
  var allDominant = arr.length === 3 && arr.every(function (hex) {
    var c = rgb(hex);
    return c[ch] > c.r * (ch === "r" ? 0 : 1) &&
           c[ch] > c.g * (ch === "g" ? 0 : 1) &&
           c[ch] > c.b * (ch === "b" ? 0 : 1);
  });
  ok(key + " 三色都是" + zh + "（该通道最大）", allDominant, arr.join(" "));
});
/* 三组之间不许撞车 */
var flat = [].concat(FIRE.browse, FIRE.wds, FIRE.im);
ok("九个火色互不重复", new Set(flat).size === flat.length);
/* 火色不得被“对齐”成节点色相 */
var NODES = eval("(" + grab(/var NODES = (\[[\s\S]*?\n  \]);/, "NODES")[1] + ")");
ok("火色与节点色相（青/金/紫）不相同",
   NODES.every(function (n) { return (FIRE[n.k] || []).indexOf(n.c) === -1; }));

console.log("[rgba() 注入]");
ok("rgba('#2FE07A',.52) 转得对", rgba("#2FE07A", .52) === "rgba(47,224,122,0.52)", rgba("#2FE07A", .52));
ok("rgba 处理 00 通道不丢位", rgba("#000000", 1) === "rgba(0,0,0,1)");

console.log("[火星：更大、射得更远、四面八方]");
var V = [];
for (var i = 0; i < SPARK_N; i++) V.push(sparkVec(i));
ok("粒子数 ≥12（旧版 9）", SPARK_N >= 12, String(SPARK_N));
var R0 = V.map(function (v) { return Math.sqrt(v.sx * v.sx + v.sy * v.sy); });
var R1 = V.map(function (v) { return Math.sqrt(v.tx * v.tx + v.ty * v.ty); });
ok("都从圆边起飞（起飞半径 = " + SPARK_R0 + "px，圆半径 37）",
   R0.every(function (r) { return Math.abs(r - SPARK_R0) < 0.01; }) && SPARK_R0 > 37 && SPARK_R0 < 48);
ok("落点半径 > 旧版的 64px（四射更远）", Math.min.apply(null, R1) > 64,
   Math.min.apply(null, R1).toFixed(0) + "–" + Math.max.apply(null, R1).toFixed(0) + "px");
ok("远近有层次（最远/最近 > 1.2）", Math.max.apply(null, R1) / Math.min.apply(null, R1) > 1.2);
ok("每粒都真往外走（行程 > 35px）",
   V.every(function (v, k) { return R1[k] - R0[k] > 35; }));

/* 角度：必须铺满一圈，不能挤在一边 */
var angs = V.map(function (v) { return (Math.atan2(v.ty, v.tx) * 180 / Math.PI + 360) % 360; })
            .sort(function (a, b) { return a - b; });
var gap = 0;
for (var k = 0; k < angs.length; k++) {
  var g2 = (k === angs.length - 1) ? (angs[0] + 360 - angs[k]) : (angs[k + 1] - angs[k]);
  if (g2 > gap) gap = g2;
}
ok("铺满一圈（最大角度空档 < 45°）", gap < 45, gap.toFixed(1) + "°");
var quad = [0, 0, 0, 0];
angs.forEach(function (a) { quad[Math.floor(a / 90)]++; });
ok("四个象限都有（每象限 ≥2 粒）", quad.every(function (c) { return c >= 2; }), quad.join("/"));

/* 起飞方向与落点方向必须同向——否则粒子会横着漂 */
ok("起飞点与落点同方向（沿半径直射）",
   V.every(function (v) {
     return Math.abs(Math.atan2(v.sy, v.sx) - Math.atan2(v.ty, v.tx)) < 1e-9;
   }));

console.log("[节奏]");
ok("时长在 2–4.5s 之间", V.every(function (v) { return v.dur >= 2 && v.dur <= 4.5; }));
ok("延迟各不相同（不会齐步走）", new Set(V.map(function (v) { return v.delay.toFixed(3); })).size === SPARK_N);
ok("延迟从 0 起、覆盖一个周期以上",
   Math.min.apply(null, V.map(function (v) { return v.delay; })) === 0 &&
   Math.max.apply(null, V.map(function (v) { return v.delay; })) > 2);

console.log("[源码守卫]");
ok("粒子直径 8px（旧版 3px）", /\.sdep-sp\{[^}]*width:8px;height:8px/.test(src));
ok("粒子带自发光 box-shadow:0 0 12px currentColor", /box-shadow:0 0 12px currentColor/.test(src));
ok("位移走 --tx/--ty（不是写死的 translateY）",
   /@keyframes sdepBurst\{[^]*?var\(--tx,0\),var\(--ty,0\)/.test(src));
ok("起飞点走 --sx/--sy", /var\(--sx,0\),var\(--sy,0\)/.test(src));
ok("⚠ 旧的上升火星（sdepRise）已清干净", !/sdepRise/.test(src));
ok("⚠ CSS 里不再有写死的橙火", !/rgba\(255,110,0/.test(src) && !/rgba\(255,190,60/.test(src));
ok("燃烧核吃 --f1/--f2/--f3", /var\(--f1\)/.test(src) && /var\(--f2\)/.test(src) && /var\(--f3\)/.test(src));
ok("三个 --f* 都在建节点时注入", (src.match(/setProperty\("--f[123]"/g) || []).length === 3);
ok("窄屏靠 scale 缩整团火（位移是像素值，改 width 没用）",
   /\.sdep-fire\{width:118px;height:118px;transform:translate\(-50%,-50%\) scale\(\.78\)\}/.test(src));
ok("reduced-motion 下火星与燃烧核都停", /prefers-reduced-motion:reduce\)\{\.sdep-sp,\.sdep-fire b\{animation:none\}/.test(src));
ok("⚠ 旧的 HOT 三色表已清干净", !/\bHOT\b/.test(src));

console.log("\n" + pass + " PASS / " + fail + " FAIL");
process.exit(fail ? 1 : 0);
