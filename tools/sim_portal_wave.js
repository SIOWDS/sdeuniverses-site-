/* sim_portal_wave.js —— 入口页三条波形曲线的模拟验收
 *
 * 要挡住的毛病（2026-07-31 用户报的那个）：曲线中间断成几截、两头够不到圆。
 * 病根有两个，都在这里立断言：
 *   ① 三条边曾是一条闭合环，端点落在圆心；现在每条边从圆边到圆边，各自一笔。
 *   ② stroke-dasharray 在 vector-effect:non-scaling-stroke 下按屏幕像素算，
 *      而 getTotalLength() 给的是 viewBox 单位（这里差四五倍）——拿后者当虚线长度
 *      就成了"实 L、虚 L、实 L…"。现在长度按屏幕像素累加，且描完即把 dasharray 清成 none。
 *
 * 跑法：node tools/sim_portal_wave.js
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

/* ---------- 取出源码里的 NODES 与 waveEdges，原样跑 ---------- */
var mN = src.match(/var NODES = (\[[\s\S]*?\n  \]);/);
if (!mN) { console.log("  FAIL  取不到 NODES"); process.exit(1); }
var mW = src.match(/function waveEdges\(W, H, gap\) \{[\s\S]*?\n    \}\n/);
if (!mW) { console.log("  FAIL  取不到 waveEdges"); process.exit(1); }
var mC = src.match(/var WAVE_N = (\d+);/), mA = src.match(/var WAVE_A = ([\d.]+);/);
if (!mC || !mA) { console.log("  FAIL  取不到 WAVE_N / WAVE_A"); process.exit(1); }
var NODES = eval("(" + mN[1] + ")");
var WAVE_N = parseInt(mC[1], 10), WAVE_A = parseFloat(mA[1]);
var waveEdges = eval("(" + mW[0].replace(/^\s*function waveEdges/, "function waveEdges") + ")");

var W = 720, H = 440, RAD = 36;          // 舞台设计尺寸；圆半径 37 − 1
var g = waveEdges(W, H, RAD);

/* 解析 d：拆成子路径，坐标换算到屏幕像素 */
var subs = g.d.trim().split(/(?=M)/).map(function (s) { return s.trim(); }).filter(Boolean);
var pts = subs.map(function (s) {
  return s.replace(/^M/, "").split(/\s*L\s*/).map(function (p) {
    var a = p.replace(/^M/, "").split(",");
    return { x: parseFloat(a[0]) * W / 100, y: parseFloat(a[1]) * H / 100 };
  });
});
function D(a, b) { return Math.sqrt((a.x - b.x) * (a.x - b.x) + (a.y - b.y) * (a.y - b.y)); }
var C = NODES.map(function (n) { return { x: n.x * W / 100, y: n.y * H / 100 }; });

console.log("[几何]");
ok("三条边＝三条子路径（不是一个闭合环）", subs.length === 3, "得到 " + subs.length);
ok("不闭合：d 里没有 Z", !/Z/i.test(g.d));
ok("每条子路径只有一个 M（中间不另起笔）",
   subs.every(function (s) { return (s.match(/M/g) || []).length === 1; }));

/* 每条边 i：从 C[i] 出发到 C[i+1]，两端都应落在圆边上 */
var endsOK = true, endsMsg = "";
pts.forEach(function (P, i) {
  var a = C[i], b = C[(i + 1) % 3];
  var d0 = D(P[0], a), d1 = D(P[P.length - 1], b);
  if (Math.abs(d0 - RAD) > 0.6 || Math.abs(d1 - RAD) > 0.6) {
    endsOK = false; endsMsg += " 边" + i + "(" + d0.toFixed(1) + "/" + d1.toFixed(1) + ")";
  }
});
ok("两端恰好搭在圆边上（距圆心 = 半径 " + RAD + "px，±0.6）", endsOK, endsMsg);

/* 端点必须落在两圆心的连线上（包络在两端归零），否则接圆处会有折角 */
var straightOK = true;
pts.forEach(function (P, i) {
  var a = C[i], b = C[(i + 1) % 3];
  [P[0], P[P.length - 1]].forEach(function (p) {
    var L = D(a, b);
    var cross = Math.abs((b.x - a.x) * (a.y - p.y) - (a.x - p.x) * (b.y - a.y)) / L;
    if (cross > 0.05) straightOK = false;
  });
});
ok("两端落在圆心连线上（波幅归零，接圆不留折角）", straightOK);

/* 三条边的波幅在眼睛里要一样（横竖缩放比不同，必须折算） */
var amps = pts.map(function (P, i) {
  var a = C[i], b = C[(i + 1) % 3], L = D(a, b), m = 0;
  P.forEach(function (p) {
    var cross = Math.abs((b.x - a.x) * (a.y - p.y) - (a.x - p.x) * (b.y - a.y)) / L;
    if (cross > m) m = cross;
  });
  return m;
});
var aMax = Math.max.apply(null, amps), aMin = Math.min.apply(null, amps);
ok("三条边波幅一致（屏幕像素，差 <10%）", (aMax - aMin) / aMax < 0.10,
   amps.map(function (v) { return v.toFixed(2); }).join(" / "));
ok("波幅在合理区间（4–14px，密而不刺）", aMin > 4 && aMax < 14, aMin.toFixed(2) + "–" + aMax.toFixed(2));

/* 采样密度：相邻点跨度太大，正弦会被采成锯齿 */
var maxStep = 0;
pts.forEach(function (P) { for (var i = 1; i < P.length; i++) maxStep = Math.max(maxStep, D(P[i - 1], P[i])); });
ok("采样够密（相邻点 <6px，不成锯齿）", maxStep < 6, maxStep.toFixed(2) + "px");

console.log("[描线长度 —— 断线的真凶]");
var straightSum = C.reduce(function (s, c, i) { return s + D(c, C[(i + 1) % 3]); }, 0);
ok("len 用的是屏幕像素（> 三边直线长度和）", g.len > straightSum, g.len.toFixed(0) + " vs " + straightSum.toFixed(0));
/* viewBox 单位下的同一条折线长度：若拿它当 dasharray 就会断成几截 */
var vbLen = 0;
pts.forEach(function (P) {
  for (var i = 1; i < P.length; i++) {
    var dx = (P[i].x - P[i - 1].x) * 100 / W, dy = (P[i].y - P[i - 1].y) * 100 / H;
    vbLen += Math.sqrt(dx * dx + dy * dy);
  }
});
ok("屏幕长度显著大于 viewBox 长度（>3 倍，证明二者不可混用）", g.len / vbLen > 3,
   g.len.toFixed(0) + " / " + vbLen.toFixed(0) + " = " + (g.len / vbLen).toFixed(1) + "x");

console.log("[窄屏 / 极端尺寸]");
var g2 = waveEdges(340, 300, 28);
var subs2 = g2.d.trim().split(/(?=M)/).filter(Boolean);
ok("窄屏也是三条子路径", subs2.length === 3);
ok("窄屏 len > 0 且有限", g2.len > 0 && isFinite(g2.len), String(g2.len));
var g3 = waveEdges(60, 60, 200);        // 圆比边还大：缩进必须被夹住，不能反转
var subs3 = g3.d.trim().split(/(?=M)/).filter(Boolean);
ok("圆大于边时缩进被夹住（仍出三条、坐标有限）",
   subs3.length === 3 && !/NaN|Infinity/.test(g3.d));

console.log("[源码守卫]");
ok("CSS 有 .sdep-tri.done{stroke-dasharray:none", /\.sdep-tri\.done\{stroke-dasharray:none/.test(src));
ok("animationend 绑了 doneDraw", /ring\.addEventListener\("animationend", doneDraw\)/.test(src));
ok("有定时器兜底（animationend 没触发也不会断着）", /setTimeout\(doneDraw, \d+\)/.test(src));
ok("reduced-motion 下也不留虚线", /prefers-reduced-motion:reduce\)\{\.sdep-tri\{animation:none;stroke-dasharray:none/.test(src));
ok("上屏后立即按实测尺寸重画", /document\.body\.appendChild\(box\);\s*\n\s*drawRing\(\);/.test(src));
ok("resize 重画", /addEventListener\("resize", drawRing\)/.test(src));
ok("关闭时撤掉 resize 监听（不漏）", /removeEventListener\("resize", drawRing\)/.test(src));
ok("⚠ 不许再用 getTotalLength 当 dasharray（viewBox 单位，会断）",
   !/ring\.getTotalLength\(\)/.test(src));
ok("圆半径从 DOM 实测（不写死）", /querySelector\("\.sdep-dot"\)/.test(src) && /offsetWidth \/ 2/.test(src));

console.log("\n" + pass + " PASS / " + fail + " FAIL");
process.exit(fail ? 1 : 0);
