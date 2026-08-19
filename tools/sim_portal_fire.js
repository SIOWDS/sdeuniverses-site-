/* sim_portal_fire.js —— 入口页「烧 TOKEN」的火色、火星与**节奏**验收
 *
 * 用户一路定下来的（2026-07-31）：
 *   ① **浏览烧绿 · 对话烧红 · 微信烧蓝**，而且要**正色**——纯红/血红、草料与树叶的绿、蓝天的蓝；
 *   ② 粒子一次比一次大（3 → 8 → 12 → 16）；
 *   ③ 四射的半径一直大到**屏幕四周边界**，让三种 TOKEN 在半路**彼此相遇**；
 *   ④ 出火要**随机**：有时多有时少，还要有**突然很多、突然很少**。
 *
 * ④ 是这一版的重头。判据不能只是"代码里调了随机数"，得对**跑出来的序列**下统计断言：
 * 一段时间里必须真的出现"零"的窗口和"轰一大阵"的窗口，且落差够大。
 * 所以随机数用的是**带种子的 mulberry32**——画面上是随机的，这里能逐次复演。
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
var SPARK_R0 = parseInt(grab(/var SPARK_R0 = (\d+), SPARK_POOL = (\d+);/, "SPARK_R0")[1], 10);
var SPARK_POOL = parseInt(grab(/var SPARK_R0 = \d+, SPARK_POOL = (\d+);/, "SPARK_POOL")[1], 10);
var rng = eval("(" + grab(/function rng\(seed\) \{[\s\S]*?\n  \}\n/, "rng")[0] + ")");
var PUFF = eval("(" + grab(/var PUFF = (\{[\s\S]*?\n  \});/, "PUFF")[1] + ")");
var puffPlan = eval("(" + grab(/function puffPlan\(rnd\) \{[\s\S]*?\n  \}\n/, "puffPlan")[0] + ")");
var edgeReach = eval("(" + grab(/function edgeReach\(cx, cy, vw, vh, a\) \{[\s\S]*?\n  \}\n/, "edgeReach")[0] + ")");
var sparkPlan = eval("(" + grab(/function sparkPlan\(rnd, reachAt, big\) \{[\s\S]*?\n  \}\n/, "sparkPlan")[0] + ")");

function rgb(hex) {
  var n = parseInt(hex.slice(1), 16);
  return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 };
}

console.log("[三色 TOKEN —— 浏览绿 · 对话红 · 微信蓝]");
ok("三个入口各有一组火色", !!(FIRE.browse && FIRE.wds && FIRE.im));
[["browse", "绿", "g"], ["wds", "红", "r"], ["im", "蓝", "b"]].forEach(function (t) {
  var arr = FIRE[t[0]] || [], ch = t[2];
  ok(t[0] + " 三色都是" + t[1] + "（该通道最大）",
     arr.length === 3 && arr.every(function (hex) {
       var c = rgb(hex); return c[ch] >= c.r && c[ch] >= c.g && c[ch] >= c.b;
     }), arr.join(" "));
});
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
ok("rgba('#2FE07A',.52) 转得对", rgba("#2FE07A", .52) === "rgba(47,224,122,0.52)", rgba("#2FE07A", .52));

console.log("[种子随机数 —— 画面随机、这里可复演]");
var r1 = rng(123), r2 = rng(123), r3 = rng(124);
var s1 = [], s2 = [], s3 = [];
for (var i = 0; i < 500; i++) { s1.push(r1()); s2.push(r2()); s3.push(r3()); }
ok("同种子逐次复演（模拟才立得住断言）", s1.every(function (v, k) { return v === s2[k]; }));
ok("换种子就换一串（三团火不会齐步）", s1.some(function (v, k) { return v !== s3[k]; }));
ok("落在 [0,1)", s1.every(function (v) { return v >= 0 && v < 1; }));
var buckets = [0, 0, 0, 0, 0];
s1.forEach(function (v) { buckets[Math.min(4, Math.floor(v * 5))]++; });
ok("大致均匀（五档每档 70–130/500）", buckets.every(function (b) { return b > 70 && b < 130; }), buckets.join("/"));
ok("⚠ 不许用 Math.random（那样既没法回放、也没法对节奏立断言）", !/Math\.random\(/.test(src));

console.log("[节奏：有多有少，突然很多、突然很少]");
var rnd = rng(0x5DE0);
var puffs = [];
for (var p = 0; p < 4000; p++) puffs.push(puffPlan(rnd));
var bigs = puffs.filter(function (q) { return q.big; });
ok("确实分「平常一阵」与「大阵」两种", bigs.length > 0 && bigs.length < puffs.length);
ok("大阵占比接近设定的 " + PUFF.bigP, Math.abs(bigs.length / puffs.length - PUFF.bigP) < 0.03,
   (bigs.length / puffs.length).toFixed(3));
ok("平常一阵 " + PUFF.small.join("–") + " 粒",
   puffs.filter(function (q) { return !q.big; })
        .every(function (q) { return q.n >= PUFF.small[0] && q.n <= PUFF.small[1]; }));
ok("大阵 " + PUFF.big.join("–") + " 粒", bigs.every(function (q) { return q.n >= PUFF.big[0] && q.n <= PUFF.big[1]; }));
ok("⚡ 大阵比平常一阵多出好几倍（落差够大）", PUFF.big[0] >= PUFF.small[1] * 3,
   PUFF.big[0] + " vs " + PUFF.small[1]);
ok("⚡ 大阵之后必跟一段更长的静默（先轰后静，才有起伏）", PUFF.gapB[0] > PUFF.gapS[1],
   PUFF.gapB[0] + "ms > " + PUFF.gapS[1] + "ms");
ok("两阵之间的间隔本身也忽长忽短", (function () {
  var g = puffs.map(function (q) { return q.gap; });
  return Math.max.apply(null, g) / Math.min.apply(null, g) > 4;
})());

/* 把一条时间线真跑出来：按 gap 累加时间、按 n 记粒数，再切成 1 秒的窗口看起伏 */
(function () {
  var rr = rng(0x5DE0), t = 0, W = 1000, TOTAL = 120000, win = new Array(TOTAL / W).fill(0);
  while (t < TOTAL) {
    var q = puffPlan(rr);
    win[Math.floor(t / W)] += q.n;
    t += q.gap;
  }
  var mean = win.reduce(function (a, b) { return a + b; }, 0) / win.length;
  var sd = Math.sqrt(win.reduce(function (a, b) { return a + (b - mean) * (b - mean); }, 0) / win.length);
  var quiet = win.filter(function (v) { return v === 0; }).length;
  var loud = win.filter(function (v) { return v >= 9; }).length;
  console.log("        （120 秒时间线：每秒均值 " + mean.toFixed(1) + " 粒，标准差 " + sd.toFixed(1) +
              "，最少 " + Math.min.apply(null, win) + "，最多 " + Math.max.apply(null, win) + "）");
  ok("⚡ 有「突然很少」的时候（存在一整秒一粒都不出）", quiet > 0, quiet + " 个空窗");
  ok("⚡ 有「突然很多」的时候（存在一秒 ≥9 粒）", loud > 0, loud + " 个爆发窗");
  ok("⚡ 起伏够明显（标准差 / 均值 > 0.6，不是一片均匀的沙沙声）", sd / mean > 0.6,
     (sd / mean).toFixed(2));
  ok("总量不至于把屏幕糊死（每秒均值 < 12 粒）", mean < 12, mean.toFixed(1));
})();

console.log("[一粒火星：方向、远近、大小、快慢都随机]");
var VW = 1280, VH = 720, SW = Math.min(VW * 0.84, 720), SH = Math.min(VH * 0.62, 440);
var SX = (VW - SW) / 2, SY = (VH - SH) / 2 - 40;
var CEN = NODES.map(function (n) { return { k: n.k, x: SX + n.x * SW / 100, y: SY + n.y * SH / 100 - 22.5 }; });
function reachAtFor(c) { return function (a) { return edgeReach(c.x, c.y, VW, VH, a); }; }
function draw(c, n, big) {
  var rr = rng(0xBEEF), out = [];
  for (var k = 0; k < n; k++) {
    var pl = sparkPlan(rr, reachAtFor(c), !!big);
    out.push({ pl: pl, x: c.x + pl.tx, y: c.y + pl.ty, r: Math.hypot(pl.tx, pl.ty) });
  }
  return out;
}
var L0 = draw(CEN[0], 600), L1 = draw(CEN[1], 600), L2 = draw(CEN[2], 600);
var ALL = [L0, L1, L2];
ok("池子够大（" + SPARK_POOL + " ≥ 大阵上限 " + PUFF.big[1] + "）", SPARK_POOL >= PUFF.big[1]);
/* 光“装得下一阵”不够：大阵来的时候池子里还满是前几阵没飞完的。
   池子一抽干，大阵就发不出来——用户要的那个落差恰好就被磨平了。
   所以把 180 秒真跑一遍（带存活时长），看到底丢掉多少粒。 */
(function () {
  var rr = rng(0x5DE0), t = 0, active = [], want = 0, got = 0, peak = 0;
  var rAt = reachAtFor(CEN[0]);
  while (t < 180000) {
    var q = puffPlan(rr);
    active = active.filter(function (e) { return e > t; });
    var n = Math.min(q.n, SPARK_POOL - active.length);
    want += q.n; got += n;
    for (var k = 0; k < n; k++) active.push(t + sparkPlan(rr, rAt, q.big).dur * 1000);
    peak = Math.max(peak, active.length);
    t += q.gap;
  }
  console.log("        （180 秒真跑：想发 " + want + " 粒，实发 " + got + " 粒，同时在飞峰值 " + peak + "）");
  ok("⚡ 池子抽不干（丢掉 < 2%，大阵才真能轰出来）", got / want > 0.98,
     ((1 - got / want) * 100).toFixed(1) + "% 丢失");
  ok("同时在飞的数量不失控（峰值 ≤ 池子）", peak <= SPARK_POOL, String(peak));
})();
ok("都从圆边起飞（起飞半径 " + SPARK_R0 + "–" + (SPARK_R0 + 8) + "px，圆半径 37）",
   L0.every(function (o) {
     var r0 = Math.hypot(o.pl.sx, o.pl.sy);
     return r0 >= SPARK_R0 - 0.01 && r0 <= SPARK_R0 + 8.01;
   }) && SPARK_R0 > 37);
ok("起飞点与落点同方向（沿半径直射）",
   L0.every(function (o) {
     return Math.abs(Math.atan2(o.pl.sy, o.pl.sx) - Math.atan2(o.pl.ty, o.pl.tx)) < 1e-9;
   }));
var qc = [0, 0, 0, 0];
L0.forEach(function (o) { qc[Math.floor(((o.pl.a * 180 / Math.PI) % 360 + 360) % 360 / 90)]++; });
ok("方向铺满一圈（四象限每档 ≥100/600）", qc.every(function (v) { return v >= 100; }), qc.join("/"));
var rs = L0.map(function (o) { return o.r; });
ok("远近有大有小（最远/最近 > 3）", Math.max.apply(null, rs) / Math.min.apply(null, rs) > 3,
   Math.min.apply(null, rs).toFixed(0) + "–" + Math.max.apply(null, rs).toFixed(0) + "px");
var edged = 0;
ALL.forEach(function (L) {
  L.forEach(function (o) { if (o.x < 1 || o.y < 1 || o.x > VW - 1 || o.y > VH - 1) edged++; });
});
ok("⚡ 真有火星打到屏幕四周边界（甚至飞出去被裁掉）", edged > 60, edged + "/1800 粒");
var side = { L: 0, R: 0, T: 0, B: 0 };
ALL.forEach(function (L) {
  L.forEach(function (o) {
    if (o.x < 1) side.L++; if (o.x > VW - 1) side.R++;
    if (o.y < 1) side.T++; if (o.y > VH - 1) side.B++;
  });
});
ok("四条边都被打到", side.L && side.R && side.T && side.B,
   "左" + side.L + " 右" + side.R + " 上" + side.T + " 下" + side.B);
var ds = L0.map(function (o) { return o.pl.d; });
ok("粒子大小也随机（9–20px 之间且有差别）",
   ds.every(function (d) { return d >= 9 && d <= 20; }) &&
   Math.max.apply(null, ds) - Math.min.apply(null, ds) > 5,
   Math.min.apply(null, ds).toFixed(1) + "–" + Math.max.apply(null, ds).toFixed(1) + "px");
var bigD = draw(CEN[0], 300, true).map(function (o) { return o.pl.d; });
ok("大阵里的粒子更大（均值更高）",
   bigD.reduce(function (a, b) { return a + b; }, 0) / bigD.length >
   ds.reduce(function (a, b) { return a + b; }, 0) / ds.length);
var durs = L0.map(function (o) { return o.pl.dur; });
ok("时长在 1–7.5s 之间", durs.every(function (d) { return d >= 1 && d <= 7.5; }),
   Math.min.apply(null, durs).toFixed(1) + "–" + Math.max.apply(null, durs).toFixed(1) + "s");
ok("飞得远的整体也飞得久（相关为正）", (function () {
  var near = L0.filter(function (o) { return o.r < 300 && o.r > 0; });
  var far = L0.filter(function (o) { return o.r > 600; });
  if (!near.length || !far.length) return false;
  var mn = near.reduce(function (a, o) { return a + o.pl.dur; }, 0) / near.length;
  var mf = far.reduce(function (a, o) { return a + o.pl.dur; }, 0) / far.length;
  return mf > mn;
})());

console.log("[三色相遇]");
function minDist(A, B) {
  var m = Infinity;
  A.forEach(function (a) { B.forEach(function (b) { m = Math.min(m, Math.hypot(a.x - b.x, a.y - b.y)); }); });
  return m;
}
[[0, 1], [0, 2], [1, 2]].forEach(function (pr) {
  var d = minDist(ALL[pr[0]], ALL[pr[1]]);
  ok("🔥 " + CEN[pr[0]].k + " 与 " + CEN[pr[1]].k + " 的 TOKEN 会碰面（落点最近 < 40px）", d < 40, d.toFixed(0) + "px");
});
[[0, 1], [0, 2], [1, 2]].forEach(function (pr) {
  var a = CEN[pr[0]], b = CEN[pr[1]], sep = Math.hypot(a.x - b.x, a.y - b.y);
  var ra = Math.max.apply(null, ALL[pr[0]].map(function (o) { return o.r; }));
  var rb = Math.max.apply(null, ALL[pr[1]].map(function (o) { return o.r; }));
  ok(CEN[pr[0]].k + "↔" + CEN[pr[1]].k + " 两团火的射程之和跨得过它们的间距", ra + rb > sep,
     (ra + rb).toFixed(0) + " > " + sep.toFixed(0));
});

console.log("[edgeReach()]");
ok("正右方：到右边界的距离", Math.abs(edgeReach(200, 300, 1000, 600, 0) - 800) < 1e-6);
ok("正左方", Math.abs(edgeReach(200, 300, 1000, 600, Math.PI) - 200) < 1e-6);
ok("正下方", Math.abs(edgeReach(200, 300, 1000, 600, Math.PI / 2) - 300) < 1e-6);
ok("斜向取最近的那块边界", (function () {
  var a = Math.PI / 4, t = edgeReach(900, 300, 1000, 600, a);
  var x = 900 + Math.cos(a) * t, y = 300 + Math.sin(a) * t;
  return x <= 1000.001 && y <= 600.001 && (Math.abs(x - 1000) < 1e-6 || Math.abs(y - 600) < 1e-6);
})());

console.log("[源码守卫]");
ok("粒子尺寸走 --d（每粒不同）", /\.sdep-sp\{[^}]*width:var\(--d,16px\);height:var\(--d,16px\)/.test(src));
ok("margin 跟着 --d 走（位移前先拿掉自身一半）", /margin:calc\(var\(--d,16px\) \/ -2\)/.test(src));
ok("默认不放动画（闲着等点名）", /\.sdep-sp\{[^}]*animation-name:none/.test(src));
ok("放一次就完（不是 infinite）", /\.sdep-sp\{[^}]*animation-iteration-count:1\}/.test(src));
ok("粒子带自发光 box-shadow:0 0 22px currentColor", /box-shadow:0 0 22px currentColor/.test(src));
ok("位移走 --tx/--ty", /@keyframes sdepBurst\{[^]*?var\(--tx,0\),var\(--ty,0\)/.test(src));
ok("起飞点走 --sx/--sy", /var\(--sx,0\),var\(--sy,0\)/.test(src));
ok("⚡ 重启动画前强制回流（否则同一帧清了再设不算重启）",
   /animationName = "none";\s*\n\s*void sp\.offsetWidth;/.test(src));
ok("放完抬手回池（animationend 清 __busy 与 animationName）",
   /addEventListener\("animationend"[\s\S]{0,160}__busy = false;[\s\S]{0,80}animationName = "none"/.test(src));
ok("忙着的粒子不会被重复点名", /if \(sp\.__busy\) continue;/.test(src));
ok("三团火各用各的种子（不会齐步）", /rng\(0x5DE0 \+ i \* 7717\)/.test(src));
ok("⚡ 关掉入口时收摊定时器（不然后台一直烧）",
   /function stopFire\(\)/.test(src) && /function close\(\)[\s\S]{0,260}stopFire\(\);/.test(src));
ok("几何量一次存起来，窗口变了才重量",
   /function refreshGeom\(\)/.test(src) && /drawRing[\s\S]{0,500}refreshGeom\(\);/.test(src));
ok("圆心用 offset* 算（不用 rect，pop 动画在缩放）",
   /function refreshGeom\(\)[\s\S]*?stage\.offsetLeft \+ nd\.offsetLeft/.test(src) &&
   !/function refreshGeom\(\)[\s\S]*?getBoundingClientRect\(/.test(src));
ok("reduced-motion 下干脆不点火", /prefers-reduced-motion: reduce\)"\)\.matches\) return;/.test(src));
ok("⚠ 窄屏不许再整团 scale（会把射程一起缩掉）",
   /\.sdep-fire\{width:118px;height:118px\}\.sdep-fire b\{width:84px/.test(src) &&
   !/\.sdep-fire\{[^}]*transform:translate\(-50%,-50%\) scale/.test(src));
ok("⚠ 旧的匀速版（sparkVec / SPARK_N / SPARK_F）已清干净",
   !/sparkVec\(/.test(src) && !/SPARK_N\b/.test(src) && !/SPARK_F\b/.test(src));
ok("⚠ 旧的上升火星（sdepRise 那支）已清干净", !/@keyframes sdepRise\{/.test(src));
ok("⚠ CSS 里不再有写死的橙火", !/rgba\(255,110,0/.test(src) && !/rgba\(255,190,60/.test(src));
ok("燃烧核吃 --f1/--f2/--f3", /var\(--f1\)/.test(src) && /var\(--f2\)/.test(src) && /var\(--f3\)/.test(src));
ok("reduced-motion 下燃烧核也停", /prefers-reduced-motion:reduce\)\{\.sdep-sp,\.sdep-fire b\{animation:none\}/.test(src));

console.log("\n" + pass + " PASS / " + fail + " FAIL");
process.exit(fail ? 1 : 0);
