/* sim_portal_wave.js —— 入口页三条波形曲线的模拟验收
 *
 * 要挡住的两个毛病（2026-07-31 用户先后报的）：
 *   ① 曲线中间断成几截。病根：`stroke-dasharray` 在 vector-effect:non-scaling-stroke 下按
 *      屏幕像素算，而 getTotalLength() 给的是 viewBox 单位（这里差四五倍）——拿后者当虚线
 *      长度就成了"实 L、虚 L、实 L…"。现在长度按屏幕像素累加，且描完即把 dasharray 清成 none。
 *   ② 两头接不上圆、还压着标题。病根：**NODES 的坐标不是圆心**——入口节点是"圆+名字+副标题"
 *      的竖向 flex 块、用 translate(-50%,-50%) 定位，落在 NODES 上的是整块的中心，圆心比它
 *      高出大半个标题区（≈22px）。现在从 DOM 的 offset* 量出这段偏移补回去。
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

/* ---------- 取出源码里的 NODES / 波形常数 / waveEdges / circleCenters，原样跑 ---------- */
function grab(re, what) {
  var m = src.match(re);
  if (!m) { console.log("  FAIL  取不到 " + what); process.exit(1); }
  return m;
}
var NODES = eval("(" + grab(/var NODES = (\[[\s\S]*?\n  \]);/, "NODES")[1] + ")");
var WAVE_N = parseInt(grab(/var WAVE_N = (\d+);/, "WAVE_N")[1], 10);
var WAVE_A = parseFloat(grab(/var WAVE_A = ([\d.]+);/, "WAVE_A")[1]);
var waveEdges = eval("(" + grab(/function waveEdges\(C, W, H, gap\) \{[\s\S]*?\n    \}\n/, "waveEdges")[0] + ")");
var circleCentersSrc = grab(/function circleCenters\(W, H\) \{[\s\S]*?\n    \}\n/, "circleCenters")[0];

var W = 720, H = 440, RAD = 36;          // 舞台设计尺寸；圆半径 37 − 1

/* ---------- 一、圆心校正：拿一个假 DOM 跑 circleCenters ---------- */
console.log("[圆心校正 —— NODES 不是圆心]");
var DOTW = 74, NDW = 150, NDH = 119;     // 圆 74px；节点块 = 圆 + 名字 + 副标题
var stage = {
  querySelectorAll: function () {
    return NODES.map(function () {
      var dot = { offsetLeft: 0, offsetTop: 0, offsetWidth: DOTW, offsetHeight: DOTW };
      dot.parentNode = { offsetLeft: (NDW - DOTW) / 2, offsetTop: 0 };   // .sdep-dotwrap
      return { offsetWidth: NDW, offsetHeight: NDH, querySelector: function () { return dot; } };
    });
  }
};
var circleCenters = eval("(" + circleCentersSrc + ")");
var m = circleCenters(W, H);
ok("circleCenters 量得出三个圆心", !!m && m.C.length === 3);
ok("圆半径从 DOM 实测（74/2）", m && m.rad === DOTW / 2, m && String(m.rad));
var dyPx = m ? (m.C[0].y - NODES[0].y) * H / 100 : 0;
ok("圆心比锚点高出半个标题区（−22.5px，±0.5）", Math.abs(dyPx + 22.5) < 0.5, dyPx.toFixed(2) + "px");
ok("横向不偏（圆在块里居中）", m && Math.abs(m.C[0].x - NODES[0].x) < 1e-9);
ok("三个节点一视同仁（偏移量相同）",
   m && Math.abs((m.C[1].y - NODES[1].y) - (m.C[0].y - NODES[0].y)) < 1e-9);

/* ---------- 二、几何：三条边各自从圆边到圆边 ---------- */
var C = m.C;
var g = waveEdges(C, W, H, RAD);
var subs = g.d.trim().split(/(?=M)/).map(function (s) { return s.trim(); }).filter(Boolean);
var pts = subs.map(function (s) {
  return s.replace(/^M/, "").split(/\s*L\s*/).map(function (p) {
    var a = p.split(",");
    return { x: parseFloat(a[0]) * W / 100, y: parseFloat(a[1]) * H / 100 };
  });
});
function D(a, b) { return Math.sqrt((a.x - b.x) * (a.x - b.x) + (a.y - b.y) * (a.y - b.y)); }
var CP = C.map(function (n) { return { x: n.x * W / 100, y: n.y * H / 100 }; });

console.log("[几何]");
ok("三条边＝三条子路径（不是一个闭合环）", subs.length === 3, "得到 " + subs.length);
ok("不闭合：d 里没有 Z", !/Z/i.test(g.d));
ok("每条子路径只有一个 M（中间不另起笔）",
   subs.every(function (s) { return (s.match(/M/g) || []).length === 1; }));

var endsOK = true, endsMsg = "";
pts.forEach(function (P, i) {
  var a = CP[i], b = CP[(i + 1) % 3];
  var d0 = D(P[0], a), d1 = D(P[P.length - 1], b);
  if (Math.abs(d0 - RAD) > 0.6 || Math.abs(d1 - RAD) > 0.6) {
    endsOK = false; endsMsg += " 边" + i + "(" + d0.toFixed(1) + "/" + d1.toFixed(1) + ")";
  }
});
ok("两端恰好搭在圆边上（距**圆心** = 半径 " + RAD + "px，±0.6）", endsOK, endsMsg);

/* 端点必须落在两圆心的连线上（包络在两端归零），否则接圆处会有折角 */
var straightOK = true;
pts.forEach(function (P, i) {
  var a = CP[i], b = CP[(i + 1) % 3], L = D(a, b);
  [P[0], P[P.length - 1]].forEach(function (p) {
    var cross = Math.abs((b.x - a.x) * (a.y - p.y) - (a.x - p.x) * (b.y - a.y)) / L;
    if (cross > 0.05) straightOK = false;
  });
});
ok("两端落在圆心连线上（波幅归零，接圆不留折角）", straightOK);

/* 接点必须落在圆上、不得落到圆下方的标题上——这正是第一版的毛病：
   拿 NODES（整块中心）当接点，线就停在“SDE 浏览”四个字上。 */
var topEnds = [pts[0][0], pts[2][pts[2].length - 1]];      // 两条搭在顶部圆上的边
ok("顶部接点在圆上（高于圆底），不是落在下面的标题上",
   topEnds.every(function (p) { return p.y <= CP[0].y + RAD + 0.1; }),
   topEnds.map(function (p) { return p.y.toFixed(1); }).join(" / ") + " vs 圆底 " + (CP[0].y + RAD).toFixed(1));
/* 与旧版（直接拿 NODES 当接点）逐点对比：新版必须明显往上提了一截 */
var oldTop = waveEdges(NODES, W, H, RAD).d.trim().split(/(?=M)/).filter(Boolean)
  .map(function (t) { var a = t.replace(/^M/, "").split(/\s*L\s*/)[0].split(","); 
                      return parseFloat(a[1]) * H / 100; })[0];
ok("顶部接点比旧版（落在 NODES 锚点）往上提了 >15px",
   oldTop - topEnds[0].y > 15, (oldTop - topEnds[0].y).toFixed(1) + "px");

var amps = pts.map(function (P, i) {
  var a = CP[i], b = CP[(i + 1) % 3], L = D(a, b), mx = 0;
  P.forEach(function (p) {
    var cross = Math.abs((b.x - a.x) * (a.y - p.y) - (a.x - p.x) * (b.y - a.y)) / L;
    if (cross > mx) mx = cross;
  });
  return mx;
});
var aMax = Math.max.apply(null, amps), aMin = Math.min.apply(null, amps);
ok("三条边波幅一致（屏幕像素，差 <10%）", (aMax - aMin) / aMax < 0.10,
   amps.map(function (v) { return v.toFixed(2); }).join(" / "));
ok("波幅在合理区间（4–14px，密而不刺）", aMin > 4 && aMax < 14, aMin.toFixed(2) + "–" + aMax.toFixed(2));

var maxStep = 0;
pts.forEach(function (P) { for (var i = 1; i < P.length; i++) maxStep = Math.max(maxStep, D(P[i - 1], P[i])); });
ok("采样够密（相邻点 <6px，不成锯齿）", maxStep < 6, maxStep.toFixed(2) + "px");

console.log("[描线长度 —— 断线的真凶]");
var straightSum = CP.reduce(function (s, c, i) { return s + D(c, CP[(i + 1) % 3]); }, 0);
ok("len 用的是屏幕像素（> 三边直线长度和）", g.len > straightSum, g.len.toFixed(0) + " vs " + straightSum.toFixed(0));
var vbLen = 0;
pts.forEach(function (P) {
  for (var i = 1; i < P.length; i++) {
    var dx = (P[i].x - P[i - 1].x) * 100 / W, dy = (P[i].y - P[i - 1].y) * 100 / H;
    vbLen += Math.sqrt(dx * dx + dy * dy);
  }
});
ok("屏幕长度显著大于 viewBox 长度（>3 倍，证明二者不可混用）", g.len / vbLen > 3,
   g.len.toFixed(0) + " / " + vbLen.toFixed(0) + " = " + (g.len / vbLen).toFixed(1) + "x");

console.log("[窄屏 / 极端尺寸 / 退路]");
var g2 = waveEdges(C, 340, 300, 28);
ok("窄屏也是三条子路径", g2.d.trim().split(/(?=M)/).filter(Boolean).length === 3);
ok("窄屏 len > 0 且有限", g2.len > 0 && isFinite(g2.len), String(g2.len));
var g3 = waveEdges(C, 60, 60, 200);      // 圆比边还大：缩进必须被夹住，不能反转
ok("圆大于边时缩进被夹住（仍出三条、坐标有限）",
   g3.d.trim().split(/(?=M)/).filter(Boolean).length === 3 && !/NaN|Infinity/.test(g3.d));
var g4 = waveEdges(NODES, W, H, RAD);
ok("量不到 DOM 时退回 NODES 也能出图", g4.d.indexOf("M") === 0 && g4.len > 0);

console.log("[版式：sdepPop 只能给绝对定位的元素用]");
/* CSS 在源码里是一堆字符串拼出来的，直接对源码正则会被引号截断
   （第一版就这么写的，结果 popUsers 是空集、断言白白通过）——先 eval 成真 CSS 再查。 */
var CSS = eval(grab(/var CSS =\n?([\s\S]*?);\n\n  var NS/, "CSS")[1]);
var rules = {};
CSS.replace(/(\.[a-zA-Z0-9_.-]+)\{([^{}]*)\}/g, function (all, sel, body) { rules[sel] = (rules[sel] || "") + body; return all; });
ok("CSS 真的 eval 出来了（不是空串）", CSS.length > 2000 && Object.keys(rules).length > 10,
   CSS.length + " 字符 / " + Object.keys(rules).length + " 条规则");
ok("sdepPop 本体带 translate(-50%,-50%)",
   /@keyframes sdepPop\{from\{opacity:0;transform:translate\(-50%,-50%\)/.test(CSS));
var popUsers = Object.keys(rules).filter(function (sel) { return /animation:sdepPop/.test(rules[sel]); });
ok("确实抄到了 sdepPop 的使用者（不是空集假通过）", popUsers.length >= 3, popUsers.join(" "));
ok("用 sdepPop 的都是绝对定位的（自带 translate(-50%,-50%)）",
   popUsers.every(function (sel) { return /transform:translate\(-50%,-50%\)/.test(rules[sel]); }), popUsers.join(" "));
ok("⬇ 底部块不再用 sdepPop（它是 flex 流内元素，一用就往左拉半个身位）",
   popUsers.indexOf(".sdep-foot") === -1 && /animation:sdepFootIn/.test(rules[".sdep-foot"] || ""));
ok("底部自己的入场动画里没有位移百分比",
   /@keyframes sdepFootIn\{from\{opacity:0;transform:translateY\(8px\)\}to\{opacity:1;transform:none\}\}/.test(CSS));
ok("底部块本身居中靠 text-align:center 与父层 align-items:center",
   /text-align:center/.test(rules[".sdep-foot"] || "") && /align-items:center/.test(rules[".sdep"] || ""));

console.log("[源码守卫]");
ok("CSS 有 .sdep-tri.done{stroke-dasharray:none", /\.sdep-tri\.done\{stroke-dasharray:none/.test(src));
ok("animationend 绑了 doneDraw", /ring\.addEventListener\("animationend", doneDraw\)/.test(src));
ok("有定时器兜底（animationend 没触发也不会断着）", /setTimeout\(doneDraw, \d+\)/.test(src));
ok("reduced-motion 下也不留虚线", /prefers-reduced-motion:reduce\)\{\.sdep-tri\{animation:none;stroke-dasharray:none/.test(src));
ok("上屏后立即按实测尺寸重画（中间只允许插一两句）",
   /document\.body\.appendChild\(box\);[\s\S]{0,140}?drawRing\(\);/.test(src));
ok("resize 重画", /addEventListener\("resize", drawRing\)/.test(src));
ok("关闭时撤掉 resize 监听（不漏）", /removeEventListener\("resize", drawRing\)/.test(src));
ok("⚠ 不许再用 getTotalLength 当 dasharray（viewBox 单位，会断）", !/ring\.getTotalLength\(\)/.test(src));
ok("⚠ 圆心用 offset*（布局值）量，不用 getBoundingClientRect（pop 动画正在缩放）",
   /offsetHeight \/ 2/.test(src) && !/\.getBoundingClientRect\(/.test(src));
ok("drawRing 走 circleCenters，不直接拿 NODES 当接点",
   /var C = m \? m\.C : NODES/.test(src) && /waveEdges\(C, W, H, rad\)/.test(src));

console.log("\n" + pass + " PASS / " + fail + " FAIL");
process.exit(fail ? 1 : 0);
