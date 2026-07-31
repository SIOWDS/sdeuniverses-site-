/* sim_portal_icon.js —— 「SDE 对话」圆里那个图标的验收
 *
 * 用户定的（2026-07-31）：圆里不能是一个静止的图，要是**两个小人的碰撞**——对话碰撞的符号。
 * 所以这里要钉的不只是"画了两个人"，而是"这两个人确实在朝对方走、并且火花正落在相撞那一瞬"。
 *
 * 跑法：node tools/sim_portal_icon.js
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

/* ---------- 用一个假的 S() 把图标真造一遍 ---------- */
function S(tag, attrs) {
  var e = { tag: tag, attrs: {}, kids: [] };
  for (var k in attrs) e.attrs[k] = attrs[k];
  e.appendChild = function (c) { e.kids.push(c); return c; };
  e.setAttribute = function (k, v) { e.attrs[k] = v; };
  return e;
}
var collideIcon = eval("(" + grab(/function collideIcon\(\) \{[\s\S]*?\n  \}\n/, "collideIcon")[0] + ")");
var icon = collideIcon();

function byClass(node, cls) {
  var out = [];
  (function walk(n) {
    if (n.attrs && String(n.attrs["class"] || "").split(/\s+/).indexOf(cls) >= 0) out.push(n);
    (n.kids || []).forEach(walk);
  })(node);
  return out;
}
/* 把一段 path 的两个端点取出来 */
function ends(d) {
  var n = d.match(/-?\d+(\.\d+)?/g).map(Number);
  if (/V/.test(d)) return [{ x: n[0], y: n[1] }, { x: n[0], y: n[2] }];
  return [{ x: n[0], y: n[1] }, { x: n[2], y: n[3] }];
}

console.log("[两个小人]");
ok("图标是 svg，带 sdep-icon 类", icon.tag === "svg" && /sdep-icon/.test(icon.attrs["class"]));
ok("对装饰层隐身（aria-hidden）", icon.attrs["aria-hidden"] === "true");
var L = byClass(icon, "figL"), R = byClass(icon, "figR");
ok("左右各一个小人（figL / figR）", L.length === 1 && R.length === 1);
[["左", L[0]], ["右", R[0]]].forEach(function (t) {
  var g = t[1];
  var heads = g.kids.filter(function (k) { return k.tag === "circle"; });
  var limbs = g.kids.filter(function (k) { return k.tag === "path"; });
  ok(t[0] + "人有一个头", heads.length === 1);
  ok(t[0] + "人有身子＋两手两腿（5 段）", limbs.length === 5, String(limbs.length));
});

var vb = icon.attrs.viewBox.split(" ").map(Number);
var MIDX = vb[2] / 2;
var lx = L[0].kids[0].attrs.cx, rx = R[0].kids[0].attrs.cx;
ok("一左一右分站中线两侧", lx < MIDX && rx > MIDX, lx + " | " + MIDX + " | " + rx);
ok("左右对称（到中线等距，±0.1）", Math.abs((MIDX - lx) - (rx - MIDX)) < 0.1);

/* 前手必须伸向对面——这是"迎面"而不是"背对背"的判据 */
function frontArm(g, dir) {
  var arms = g.kids.filter(function (k) { return k.tag === "path" && /L/.test(k.attrs.d); })
                   .map(function (k) { return ends(k.attrs.d); })
                   .filter(function (p) { return p[0].y < 15; });          // 上半身那两段＝手
  return arms.sort(function (a, b) { return dir * (b[1].x - a[1].x); })[0];
}
var la = frontArm(L[0], 1), ra = frontArm(R[0], -1);
ok("左人的前手伸向右边（朝对面）", la[1].x > la[0].x, la[0].x + "→" + la[1].x);
ok("右人的前手伸向左边（朝对面）", ra[1].x < ra[0].x, ra[0].x + "→" + ra[1].x);
ok("两只前手之间留着相撞的缝（不重叠）", la[1].x < ra[1].x, la[1].x + " < " + ra[1].x);

console.log("[相撞的那一下]");
var clash = byClass(icon, "clash");
ok("有一组火花", clash.length === 1);
var rays = clash[0].kids.map(function (k) { return ends(k.attrs.d); });
ok("六道射线", rays.length === 6, String(rays.length));
var CX = 20, CY = 14;
ok("都从相撞点 (20,14) 往外射",
   rays.every(function (p) {
     var r0 = Math.hypot(p[0].x - CX, p[0].y - CY), r1 = Math.hypot(p[1].x - CX, p[1].y - CY);
     return r1 > r0 && r0 > 1.5 && r1 > 4;
   }));
var angs = rays.map(function (p) { return (Math.atan2(p[1].y - CY, p[1].x - CX) * 180 / Math.PI + 360) % 360; })
               .sort(function (a, b) { return a - b; });
var gap = 0;
for (var i = 0; i < angs.length; i++) {
  var g2 = (i === angs.length - 1) ? (angs[0] + 360 - angs[i]) : (angs[i + 1] - angs[i]);
  if (g2 > gap) gap = g2;
}
ok("六个方向铺开（最大空档 ≤ 70°）", gap <= 70, gap.toFixed(0) + "°");
ok("相撞点正落在两人中间", Math.abs(CX - (lx + rx) / 2) < 0.1);

console.log("[真的在动，而且撞点对得上]");
var CSS = eval(grab(/var CSS =\n?([\s\S]*?);\n\n  var NS/, "CSS")[1]);
function kf(name) {
  var m = CSS.match(new RegExp("@keyframes " + name + "\\{([^}]*\\}[^}]*)*?\\}\\}"));
  return m ? m[0] : "";
}
function stops(name) {
  var out = {};
  kf(name).replace(/([\d.,%\s]+)\{([^}]*)\}/g, function (all, keys, body) {
    keys.split(",").forEach(function (k) {
      k = k.trim(); if (!/%$/.test(k)) return;
      out[parseFloat(k)] = body;
    });
    return all;
  });
  return out;
}
var kL = stops("sdepBumpL"), kR = stops("sdepBumpR"), kC = stops("sdepClash");
ok("左人有位移关键帧", Object.keys(kL).length >= 4);
ok("右人有位移关键帧", Object.keys(kR).length >= 4);
function tx(body) { var m = body.match(/translateX\((-?[\d.]+)px\)/); return m ? parseFloat(m[1]) : null; }
var offs = Object.keys(kL).map(Number).sort(function (a, b) { return a - b; });
ok("左右永远反向（一个往右另一个必往左）",
   offs.every(function (o) { return kR[o] !== undefined && tx(kL[o]) === -tx(kR[o]); }));
ok("先分开、再走近（起点是分开的）", tx(kL[0]) < 0 && tx(kR[0]) > 0);
var innerWin = offs.filter(function (o) { return tx(kL[o]) > 0; });
ok("中途真的走到对面去了（相撞）", innerWin.length >= 2, innerWin.join("–") + "%");
/* 火花必须在"两人最靠拢"的那段时间里最亮 */
var peak = Object.keys(kC).map(Number).filter(function (o) { return /opacity:1\b/.test(kC[o]); });
ok("火花有一个最亮点", peak.length === 1, peak.join(","));
ok("⚡ 火花的最亮点落在两人相撞的窗口里",
   peak[0] >= Math.min.apply(null, innerWin) && peak[0] <= Math.max.apply(null, innerWin),
   peak[0] + "% in " + Math.min.apply(null, innerWin) + "–" + Math.max.apply(null, innerWin) + "%");
var durs = (CSS.match(/animation:sdep(BumpL|BumpR|Clash) ([\d.]+)s/g) || [])
  .map(function (t) { return t.match(/([\d.]+)s/)[1]; });
ok("三支动画同一个周期（否则火花会飘到没人的时候）",
   durs.length === 3 && new Set(durs).size === 1, durs.join("/"));

console.log("[挂载与守卫]");
ok("wds 走现画图标（ART 映射）", /var ART = \{ wds: collideIcon \}/.test(src));
ok("没列进 ART 的仍用字形兜底", /if \(ART\[n\.k\]\) dot\.appendChild\(ART\[n\.k\]\(\)\); else dot\.textContent = n\.icon;/.test(src));
ok("图标尺寸跟着字号走（em，不写死 px）", /\.sdep-icon\{width:1\.55em;height:1\.1em/.test(src));
ok("描边用 currentColor（hover 反白时跟着变）", /\.sdep-icon\{[^"]*stroke:currentColor/.test(src));
ok("火花缩放绕自身中心（transform-box:fill-box）", /\.clash\{[^"]*transform-box:fill-box;transform-origin:center/.test(src));
ok("reduced-motion 下三支都停、火花留着不闪", /prefers-reduced-motion:reduce\)\{\.sdep-icon \.figL,\.sdep-icon \.figR,\.sdep-icon \.clash\{animation:none\}/.test(src));
var NODES = eval("(" + grab(/var NODES = (\[[\s\S]*?\n  \]);/, "NODES")[1] + ")");
ok("wds 仍留着字形做兜底", !!(NODES.filter(function (n) { return n.k === "wds"; })[0] || {}).icon);

console.log("\n" + pass + " PASS / " + fail + " FAIL");
process.exit(fail ? 1 : 0);
