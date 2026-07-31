/* sim_portal_fire.js —— 入口页「烧 TOKEN」的火色与火星验收
 *
 * 用户一路定下来的（2026-07-31）：
 *   ① **浏览烧绿 · 对话烧红 · 微信烧蓝**，而且要**正色**——纯红/血红、草料与树叶的绿、蓝天的蓝；
 *   ② 粒子要一次比一次大（3 → 8 → 12 → 16px）；
 *   ③ 四射的半径要一直大到**屏幕四周边界**，让红绿蓝三种 TOKEN 在半路**彼此相遇**。
 * 这里逐条钉死，免得日后有人把三色调回一锅橙火、或把射程收回圆边那一小圈。
 *
 * 注意：火色（FIRE）与节点色相（NODES[].c ＝ 青/金/紫）是两回事——
 *       色相标身份，火色标烧的是哪一种 TOKEN。两者不许互相"对齐"。
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

var NODES = eval("(" + grab(/var NODES = (\[[\s\S]*?\n  \]);/, "NODES")[1] + ")");
var FIRE = eval("(" + grab(/var FIRE = (\{[\s\S]*?\n  \});/, "FIRE")[1] + ")");
var rgba = eval("(" + grab(/function rgba\(hex, a\) \{[\s\S]*?\n  \}\n/, "rgba")[0] + ")");
var SPARK_N = parseInt(grab(/var SPARK_N = (\d+), SPARK_R0 = (\d+);/, "SPARK_N")[1], 10);
var SPARK_R0 = parseInt(grab(/var SPARK_N = \d+, SPARK_R0 = (\d+);/, "SPARK_R0")[1], 10);
var SPARK_F = eval("(" + grab(/var SPARK_F = (\[[^\]]*\]);/, "SPARK_F")[1] + ")");
var sparkAngle = eval("(" + grab(/function sparkAngle\(s\) \{[\s\S]*?\n  \}\n/, "sparkAngle")[0] + ")");
var edgeReach = eval("(" + grab(/function edgeReach\(cx, cy, vw, vh, a\) \{[\s\S]*?\n  \}\n/, "edgeReach")[0] + ")");
var sparkVec = eval("(" + grab(/function sparkVec\(s, reach\) \{[\s\S]*?\n  \}\n/, "sparkVec")[0] + ")");

function rgb(hex) {
  var n = parseInt(hex.slice(1), 16);
  return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 };
}

console.log("[三色 TOKEN —— 浏览绿 · 对话红 · 微信蓝]");
ok("三个入口各有一组火色", !!(FIRE.browse && FIRE.wds && FIRE.im));
[["browse", "绿", "g"], ["wds", "红", "r"], ["im", "蓝", "b"]].forEach(function (t) {
  var key = t[0], zh = t[1], ch = t[2];
  var arr = FIRE[key] || [];
  ok(key + " 三色都是" + zh + "（该通道最大）",
     arr.length === 3 && arr.every(function (hex) {
       var c = rgb(hex);
       return c[ch] >= c.r && c[ch] >= c.g && c[ch] >= c.b;
     }), arr.join(" "));
});
/* 不只"该通道最大"，还得是正色（用户第二次裁定：纯红/血红、草料树叶的绿、蓝天的蓝） */
ok("wds 是血红不是橙火（绿≈蓝且远小于红）",
   FIRE.wds.every(function (hex) { var c = rgb(hex); return Math.abs(c.g - c.b) <= 6 && c.g < c.r * 0.35; }),
   FIRE.wds.join(" "));
ok("browse 是草叶绿不是薄荷/青（绿 > 蓝×1.5）",
   FIRE.browse.every(function (hex) { var c = rgb(hex); return c.g > c.b * 1.5; }), FIRE.browse.join(" "));
ok("im 是天蓝不是紫（蓝 > 绿 > 红）",
   FIRE.im.every(function (hex) { var c = rgb(hex); return c.b > c.g && c.g > c.r; }), FIRE.im.join(" "));
var flat = [].concat(FIRE.browse, FIRE.wds, FIRE.im);
ok("九个火色互不重复", new Set(flat).size === flat.length);
ok("火色与节点色相（青/金/紫）不相同",
   NODES.every(function (n) { return (FIRE[n.k] || []).indexOf(n.c) === -1; }));

console.log("[rgba() 注入]");
ok("rgba('#2FE07A',.52) 转得对", rgba("#2FE07A", .52) === "rgba(47,224,122,0.52)", rgba("#2FE07A", .52));
ok("rgba 处理 00 通道不丢位", rgba("#000000", 1) === "rgba(0,0,0,1)");

console.log("[射到边界 —— edgeReach()]");
ok("正右方：到右边界的距离", Math.abs(edgeReach(200, 300, 1000, 600, 0) - 800) < 1e-6);
ok("正左方", Math.abs(edgeReach(200, 300, 1000, 600, Math.PI) - 200) < 1e-6);
ok("正下方", Math.abs(edgeReach(200, 300, 1000, 600, Math.PI / 2) - 300) < 1e-6);
ok("正上方", Math.abs(edgeReach(200, 300, 1000, 600, -Math.PI / 2) - 300) < 1e-6);
ok("斜向取最近的那块边界（不会穿出屏幕）", (function () {
  var a = Math.PI / 4, t = edgeReach(900, 300, 1000, 600, a);
  var x = 900 + Math.cos(a) * t, y = 300 + Math.sin(a) * t;
  return x <= 1000.001 && y <= 600.001 && (Math.abs(x - 1000) < 1e-6 || Math.abs(y - 600) < 1e-6);
})());

/* 三个入口在一块 1280×720 的屏上的圆心（按 NODES 百分比 × 舞台，再加舞台在视口里的偏移） */
var VW = 1280, VH = 720, SW = Math.min(VW * 0.84, 720), SH = Math.min(VH * 0.62, 440);
var SX = (VW - SW) / 2, SY = (VH - SH) / 2 - 40;
var CEN = NODES.map(function (n) { return { k: n.k, x: SX + n.x * SW / 100, y: SY + n.y * SH / 100 - 22.5 }; });
function land(c) {
  var out = [];
  for (var s = 0; s < SPARK_N; s++) {
    var v = sparkVec(s, edgeReach(c.x, c.y, VW, VH, sparkAngle(s)));
    out.push({ x: c.x + v.tx, y: c.y + v.ty, r: Math.hypot(v.tx, v.ty), dur: v.dur, s: s });
  }
  return out;
}
var LAND = CEN.map(land);

console.log("[火星：更大、射得更远、四面八方]");
ok("粒子数 ≥16（一路 9 → 12 → 16）", SPARK_N >= 16, String(SPARK_N));
ok("远近分四档，其中一档是 1（直达边界）", SPARK_F.length === 4 && Math.max.apply(null, SPARK_F) === 1, SPARK_F.join("/"));
ok("都从圆边起飞（起飞半径 = " + SPARK_R0 + "px，圆半径 37）", SPARK_R0 > 37 && SPARK_R0 < 48);
var maxR = Math.max.apply(null, LAND.map(function (L) { return Math.max.apply(null, L.map(function (p) { return p.r; })); }));
ok("最远的一粒射程 > 300px（旧版只有 115px）", maxR > 300, maxR.toFixed(0) + "px");
var atEdge = 0;
LAND.forEach(function (L) {
  L.forEach(function (p) {
    if (p.x < 1 || p.y < 1 || p.x > VW - 1 || p.y > VH - 1) atEdge++;
  });
});
ok("⚡ 真有火星落到屏幕四周边界上（每团至少 2 粒）", atEdge >= 6, atEdge + " 粒");
var quadHit = { L: 0, R: 0, T: 0, B: 0 };
LAND.forEach(function (L) {
  L.forEach(function (p) {
    if (p.x < 1) quadHit.L++; if (p.x > VW - 1) quadHit.R++;
    if (p.y < 1) quadHit.T++; if (p.y > VH - 1) quadHit.B++;
  });
});
ok("四条边都有火星打上去", quadHit.L && quadHit.R && quadHit.T && quadHit.B,
   "左" + quadHit.L + " 右" + quadHit.R + " 上" + quadHit.T + " 下" + quadHit.B);
/* 角度：必须铺满一圈，不能挤在一边 */
var angs = [];
for (var i = 0; i < SPARK_N; i++) angs.push((sparkAngle(i) * 180 / Math.PI % 360 + 360) % 360);
angs.sort(function (a, b) { return a - b; });
var gap = 0;
for (var k = 0; k < angs.length; k++) {
  var g2 = (k === angs.length - 1) ? (angs[0] + 360 - angs[k]) : (angs[k + 1] - angs[k]);
  if (g2 > gap) gap = g2;
}
ok("铺满一圈（最大角度空档 < 45°）", gap < 45, gap.toFixed(1) + "°");
var quad = [0, 0, 0, 0];
angs.forEach(function (a) { quad[Math.floor(a / 90)]++; });
ok("四个象限都有（每象限 ≥3 粒）", quad.every(function (c) { return c >= 3; }), quad.join("/"));
ok("每粒都真往外走（落点半径 > 起飞半径 + 50）",
   LAND.every(function (L) { return L.every(function (p) { return p.r > SPARK_R0 + 50; }); }));

console.log("[三色相遇]");
function minDist(A, B) {
  var m = Infinity;
  A.forEach(function (a) { B.forEach(function (b) { m = Math.min(m, Math.hypot(a.x - b.x, a.y - b.y)); }); });
  return m;
}
[[0, 1], [0, 2], [1, 2]].forEach(function (pr) {
  var d = minDist(LAND[pr[0]], LAND[pr[1]]);
  ok("🔥 " + CEN[pr[0]].k + " 与 " + CEN[pr[1]].k + " 的 TOKEN 会碰面（落点最近 < 120px）", d < 120, d.toFixed(0) + "px");
});
/* 更强的一条：一团火的射程要够到另一团的圆心附近，才叫"迎面遇上"而不是各扫各的角落 */
[[0, 1], [0, 2], [1, 2]].forEach(function (pr) {
  var a = CEN[pr[0]], b = CEN[pr[1]], sep = Math.hypot(a.x - b.x, a.y - b.y);
  var ra = Math.max.apply(null, LAND[pr[0]].map(function (p) { return p.r; }));
  var rb = Math.max.apply(null, LAND[pr[1]].map(function (p) { return p.r; }));
  ok(CEN[pr[0]].k + "↔" + CEN[pr[1]].k + " 两团火的射程之和跨得过它们的间距", ra + rb > sep,
     (ra + rb).toFixed(0) + " > " + sep.toFixed(0));
});

console.log("[节奏]");
var allDur = [].concat.apply([], LAND.map(function (L) { return L.map(function (p) { return p.dur; }); }));
ok("时长在 2–7.5s 之间", allDur.every(function (d) { return d >= 2 && d <= 7.5; }),
   Math.min.apply(null, allDur).toFixed(1) + "–" + Math.max.apply(null, allDur).toFixed(1) + "s");
ok("飞得远的也飞得久（速度不至于像子弹）", (function () {
  var L = LAND[0].slice().sort(function (a, b) { return a.r - b.r; });
  return L.every(function (p, i) { return i === 0 || p.dur >= L[i - 1].dur - 1e-9; });
})());
var delays = [];
for (var q = 0; q < SPARK_N; q++) delays.push(sparkVec(q, 400).delay);
ok("延迟各不相同（不会齐步走）", new Set(delays.map(function (d) { return d.toFixed(3); })).size === SPARK_N);
ok("延迟从 0 起、覆盖一个周期以上",
   Math.min.apply(null, delays) === 0 && Math.max.apply(null, delays) > 2);

console.log("[源码守卫]");
ok("粒子直径 16px（一路从 3 → 8 → 12 → 16）", /\.sdep-sp\{[^}]*width:16px;height:16px/.test(src));
ok("位移前先用 margin 拿掉自身一半（随尺寸同步改）", /\.sdep-sp\{[^}]*margin:-8px 0 0 -8px/.test(src));
ok("粒子带自发光 box-shadow:0 0 22px currentColor", /box-shadow:0 0 22px currentColor/.test(src));
ok("位移走 --tx/--ty（不是写死的 translateY）",
   /@keyframes sdepBurst\{[^]*?var\(--tx,0\),var\(--ty,0\)/.test(src));
ok("起飞点走 --sx/--sy", /var\(--sx,0\),var\(--sy,0\)/.test(src));
ok("⚡ 上屏后按视口重设落点（aimSparks）", /function aimSparks\(\)/.test(src) && /drawRing[\s\S]{0,400}aimSparks\(\);/.test(src));
ok("落点用 offset* 算圆心（不用 rect，pop 动画在缩放）",
   /function aimSparks\(\)[\s\S]*?stage\.offsetLeft \+ nd\.offsetLeft/.test(src) &&
   !/function aimSparks\(\)[\s\S]*?getBoundingClientRect\(/.test(src));
ok("⚠ 窄屏不许再整团 scale（会把射程一起缩掉）",
   !/\.sdep-fire\{width:118px;height:118px;transform:translate\(-50%,-50%\) scale/.test(src) &&
   /\.sdep-fire\{width:118px;height:118px\}\.sdep-fire b\{width:84px/.test(src));
ok("⚠ 旧的上升火星（sdepRise 那支）已清干净", !/@keyframes sdepRise\{/.test(src));
ok("⚠ CSS 里不再有写死的橙火", !/rgba\(255,110,0/.test(src) && !/rgba\(255,190,60/.test(src));
ok("燃烧核吃 --f1/--f2/--f3", /var\(--f1\)/.test(src) && /var\(--f2\)/.test(src) && /var\(--f3\)/.test(src));
ok("三个 --f* 都在建节点时注入", (src.match(/setProperty\("--f[123]"/g) || []).length === 3);
ok("reduced-motion 下火星与燃烧核都停", /prefers-reduced-motion:reduce\)\{\.sdep-sp,\.sdep-fire b\{animation:none\}/.test(src));
ok("⚠ 旧的 HOT 三色表已清干净", !/\bHOT\b/.test(src));

console.log("\n" + pass + " PASS / " + fail + " FAIL");
process.exit(fail ? 1 : 0);
