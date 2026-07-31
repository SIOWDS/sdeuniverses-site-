/* 入口页 /assets/sde-portal.js 的模拟。
 * 覆盖：只在首页拦 · 一次会话只拦一次 · ?portal=1 可强出 · 三个顶点与三角形用同一组坐标 ·
 *      「浏览」是就地揭开不跳转、另两个是真链接 · Esc 与「直接浏览」都能出去 ·
 *      目的地与 /assets/sde-modes.js 一致。
 * 用法：node tools/sim_sde_portal.js
 */
"use strict";
const fs = require("fs");
let PASS = 0, FAILS = 0;
function ok(c, m) { if (c) { PASS++; console.log("  PASS " + m); } else { FAILS++; console.log("  FAIL " + m); } }
const SRC = fs.readFileSync("/home/claude/site/public/assets/sde-portal.js", "utf8");
const MODES = fs.readFileSync("/home/claude/site/public/assets/sde-modes.js", "utf8");

class N {
  constructor(t, ns) {
    this.tagName = String(t || "div").toUpperCase(); this.ns = ns || "";
    this.children = []; this.className = ""; this.attrs = {};
    // 桩的 style 得带上 setProperty / getPropertyValue —— 真浏览器里有，桩里没有的话
    // 脚本一用 CSS 变量就当场抛错，而这种错在页面上只表现为"三角形没画出来"，很难查。
    // 两处都要：模块用 setProperty 设 --c 色相与 --L 描线长度，断言用 getPropertyValue 读回来。
    this.style = {};
    Object.defineProperty(this.style, "setProperty", {
      enumerable: false, writable: true, configurable: true,
      value: function (k, v) { this[k] = String(v); },
    });
    Object.defineProperty(this.style, "getPropertyValue", {
      enumerable: false, writable: true, configurable: true,
      value: function (k) { return this[k] == null ? "" : String(this[k]); },
    });
    this._text = ""; this.parentNode = null; this.type = "";
  }
  set textContent(v) { this._text = String(v); this.children.length = 0; }
  get textContent() { return this._text || this.children.map((c) => c.textContent).join(""); }
  appendChild(c) { c.parentNode = this; this.children.push(c); return c; }
  removeChild(c) { const i = this.children.indexOf(c); if (i >= 0) this.children.splice(i, 1); c.parentNode = null; return c; }
  setAttribute(k, v) { this.attrs[k] = String(v); if (k === "class") this.className = String(v); }
  getAttribute(k) { return k === "class" ? this.className : (this.attrs[k] ?? null); }
  focus() {}
  _all(o) { o.push(this); this.children.forEach((c) => c._all(o)); return o; }
  _m(s) { return s[0] === "." ? this.className.split(/\s+/).includes(s.slice(1)) : this.tagName === s.toUpperCase(); }
  querySelector(s) { return this._all([]).slice(1).find((n) => n._m(s)) || null; }
  querySelectorAll(s) { return this._all([]).slice(1).filter((n) => n._m(s)); }
}
function env(path, search, seen) {
  const head = new N("head"), body = new N("body"), html = new N("html");
  html.style = {};
  const doc = {
    head, body, documentElement: html, readyState: "complete",
    createElement: (t) => new N(t),
    createElementNS: (ns, t) => new N(t, ns),
    querySelector: (s) => head.querySelector(s) || body.querySelector(s),
    _keys: [],
    addEventListener(t, f) { if (t === "keydown") this._keys.push(f); },
    removeEventListener(t, f) { if (t === "keydown") this._keys = this._keys.filter((x) => x !== f); },
    key(k) { this._keys.slice().forEach((f) => f({ key: k })); },
  };
  const ss = {}; if (seen) ss.sde_portal_seen = "1";
  const win = {
    location: { pathname: path, search: search || "" },
    document: doc,
    sessionStorage: { getItem: (k) => (k in ss ? ss[k] : null), setItem: (k, v) => { ss[k] = v; } },
    localStorage: { getItem: () => null },
  };
  return { doc, win, body, head, ss };
}
function run(e) {
  new Function("window", "document", "location", "sessionStorage", "localStorage", "setTimeout", SRC)(
    e.win, e.doc, e.win.location, e.win.sessionStorage, e.win.localStorage, (f) => f());
  return e;
}

console.log("① 只在首页拦，且一次会话只拦一次");
{
  const e = run(env("/column/a/"));
  ok(!e.body.querySelector(".sdep"), "内页不拦");
}
{
  const e = run(env("/", "", true));
  ok(!e.body.querySelector(".sdep"), "本次会话已经见过就不再拦（入口页是进门分道，不是每次回首页都拦一道）");
}
{
  const e = run(env("/index.html"));
  ok(!!e.body.querySelector(".sdep"), "/index.html 也算首页");
}
{
  const e = run(env("/column/a/", "?portal=1"));
  ok(!!e.body.querySelector(".sdep"), "?portal=1 可以随时把入口页叫出来");
}

console.log("② 三角形与三个入口");
const E = run(env("/"));
const box = E.body.querySelector(".sdep");
const nodes = box.querySelectorAll(".sdep-node");
ok(nodes.length === 3, "三个入口，实得 " + nodes.length);
ok(nodes.map((n) => n.querySelector(".sdep-nm").textContent).join(" / ").indexOf("SDE") === 0,
  "三个名字，实得 " + nodes.map((n) => n.querySelector(".sdep-nm").textContent).join(" / "));
// 只认三角形的边：图标四周的火焰也是 path，一起数进来就永远对不上
const edges = box.querySelectorAll("path").filter(function (e) {
  return String(e.className || "").indexOf("sdep-tri") >= 0;
});
ok(edges.length === 3, "三条边各是一条独立曲线，实得 " + edges.length);
const nodePos = nodes.map((n) => parseFloat(n.style.left) + "," + parseFloat(n.style.top));
{
  // 每条边：必须是三次贝塞尔（S 型的载体），且首尾正好落在相邻两个入口上
  let allCubic = true, allJoin = true, detail = [];
  edges.forEach((e, i) => {
    const d = String(e.attrs.d || "");
    if (d.indexOf("C") < 0) allCubic = false;
    const m = d.match(/^M\s*([-\d.]+),([-\d.]+)\s*C[^]*\s([-\d.]+),([-\d.]+)$/);
    if (!m) { allJoin = false; detail.push("第" + (i + 1) + "条读不出首尾"); return; }
    const from = parseFloat(m[1]) + "," + parseFloat(m[2]);
    const to = parseFloat(m[3]) + "," + parseFloat(m[4]);
    if (from !== nodePos[i] || to !== nodePos[(i + 1) % 3]) {
      allJoin = false; detail.push("第" + (i + 1) + "条 " + from + "→" + to);
    }
  });
  ok(allCubic, "三条边都是三次贝塞尔曲线（不是直线）");
  ok(allJoin, "每条曲线首尾正落在相邻两个入口上（同一组坐标，不是各写一份）" + (detail.length ? "：" + detail.join(" ｜ ") : ""));
}
{
  // S 型的判据：两个控制点必须落在弦的两侧（同侧就是弓形，不是 S）
  let allS = true, sd = [];
  edges.forEach((e, i) => {
    const n = String(e.attrs.d || "").match(/[-\d.]+/g).map(Number);
    if (n.length < 8) { allS = false; return; }
    const [ax, ay, c1x, c1y, c2x, c2y, bx, by] = n;
    const dx = bx - ax, dy = by - ay;
    const s1 = dx * (c1y - ay) - dy * (c1x - ax);      // 叉积定侧
    const s2 = dx * (c2y - ay) - dy * (c2x - ax);
    if (!(s1 * s2 < 0)) { allS = false; sd.push("第" + (i + 1) + "条 " + s1.toFixed(1) + "/" + s2.toFixed(1)); }
  });
  ok(allS, "两个控制点分居弦的两侧 —— 是 S 型而不是弓形" + (sd.length ? "：" + sd.join(" ｜ ") : ""));
}
{
  // 描线长度得各算各的，写死一个数长短边就一快一慢
  const lens = edges.map((e) => String(e.style && e.style.getPropertyValue ? e.style.getPropertyValue("--L") : (e.style["--L"] || "")));
  ok(lens.every((v) => v && parseFloat(v) > 0), "每条边的描线长度是按自己算出来的：" + lens.join(" / "));
}
ok(parseFloat(nodes[0].style.top) < parseFloat(nodes[1].style.top), "第一个在顶端");
const mid = box.querySelector(".sdep-mid");
ok(!!mid && mid.textContent === "爱思乐园", "三角形正中是「爱思乐园」四个字，实得 " + (mid ? mid.textContent : "无"));
{
  // 重心必须由三个顶点现算——写死了就会在改顶点时飘到三角形外面去
  let cx = 0, cy = 0;
  nodes.forEach((n) => { cx += parseFloat(n.style.left); cy += parseFloat(n.style.top); });
  ok(Math.abs(parseFloat(mid.style.left) - cx / 3) < 0.01 && Math.abs(parseFloat(mid.style.top) - cy / 3) < 0.01,
    "落在三个顶点的重心上（跟着顶点走，不是写死的百分比）：" + mid.style.left + "/" + mid.style.top);
}
ok(/pointer-events:none/.test(SRC), "正中那四个字不挡点击（它是字，不是按钮）");
ok(/margin-right:-\.34em/.test(SRC), "字间距在末字后面多出的那一份被抵掉了（否则四个字看着偏左）");

console.log("②b 多样 · 统一 · 和谐");
{
  const cols = nodes.map((n) => n.style["--c"]);
  ok(new Set(cols).size === 3, "三个入口三种色相（多样），实得 " + cols.join(" "));
  ok(/linearGradient/.test(SRC) && /sdepEdge/.test(SRC), "三角形那条边用一支渐变把三色走完全程（统一：一条线，三种颜色）");
  const deco = box.querySelector(".sdep-deco");
  ok(!!deco, "四周有图案层");
  ok(deco.attrs.preserveAspectRatio === "xMidYMid slice",
    "图案层用 slice —— 圆必须是圆的；三角形那张是 none（要跟着拉满），两张不能共用");
  ok(deco.querySelectorAll("line").length >= 10, "互联网的连接：一张节点网，实得连线 " + deco.querySelectorAll("line").length + " 条");
  ok(deco.querySelectorAll("rect").length >= 5, "大模型的活力：声波柱，实得 " + deco.querySelectorAll("rect").length + " 根");
  ok(deco.querySelectorAll("circle").length >= 20, "社群的三环与浮尘，实得圆 " + deco.querySelectorAll("circle").length + " 个");
  ok(deco.querySelectorAll("animate").length >= 8, "图案是活的（有动画），实得 " + deco.querySelectorAll("animate").length + " 条");
  ok(!/\.focus\(\)/.test(SRC), "不自动聚焦——鼠标进来的人会平白看到一圈方形焦点环（第一版就是这样）");
  ok(!!box.querySelector(".sdep-glow"), "三团角落微光把画面兜圆");
}

console.log("②c 三个图标四周烧 TOKEN");
{
  const fires = box.querySelectorAll(".sdep-fire");
  ok(fires.length === 3, "三个图标各烧一团，实得 " + fires.length);
  ok(fires.every((f) => f.querySelector("b")), "每团都有火焰底光");
  const sp = fires[0].querySelectorAll(".sdep-sp");
  ok(sp.length === 18, "火星十八粒，实得 " + sp.length);
  ok(new Set(sp.map((x) => x.style.animationDelay)).size > 1, "火星错开起飞（同时起飞就成了一排跳动的点，不像火）");
  const cols = new Set(sp.map((x) => x.style.background));
  ok(cols.has(NODEC(nodes[0])), "火星里掺了本入口自己的色（同为一种火，各带各的色）");
  ok(cols.size >= 3, "其余是首页那套火色（橙/琥珀/橘），实得 " + cols.size + " 种");
  ok(/z-index:1/.test(SRC) && /sdep-dotwrap/.test(SRC), "火在下、图标在上（分层，别让火盖住图标）");
  ok(/@keyframes sdepBurn/.test(SRC), "火在形变，不是只改透明度（只改透明度做不出火）");
  const tg = fires[0].querySelectorAll("b");
  ok(tg.length === 3, "三层火舌（外焰暗红/中焰橙/内焰黄白），实得 " + tg.length);
  const durs = (SRC.match(/animation-duration:[.\d]+s/g) || []);
  ok(new Set(durs).size >= 3, "三层各用不同时长与相位，永远不同步——火之所以像火，全在于它从不重复自己");
  ok(/transform-origin:50% 100%/.test(SRC), "火苗底部定住、只有上部乱窜");
}
function NODEC(n) { return n.style["--c"]; }

console.log("③ 浏览＝就地揭开，另两个＝真链接");
{
  const browse = nodes[0], wds = nodes[1], im = nodes[2];
  ok(browse.tagName === "BUTTON" && !browse.attrs.href && !browse.href,
    "「SDE 浏览」不是链接——它就地揭开下面这一页，不再加载一次首页");
  ok(wds.href === "/taste/wds-chat/" && im.href === "/sde-wechat/",
    "另两个是真链接，实得 " + wds.href + " / " + im.href);
  browse.onclick();
  ok(E.ss.sde_portal_seen === "1", "选过之后本次会话不再拦");
  ok(E.doc.documentElement.style.overflow === "", "揭开后把页面滚动还回去（拦的时候锁了）");
}

console.log("④ 两条出路：Esc 与「直接浏览」");
{
  const e = run(env("/"));
  ok(!!e.body.querySelector(".sdep-skip"), "有「直接浏览」");
  e.doc.key("Escape");
  ok(e.ss.sde_portal_seen === "1", "Esc 也能出去（入口页不该是个关不掉的墙）");
}

console.log("⑤ 目的地与三态模块一致");
{
  const mine = (SRC.match(/GO = \{([^}]+)\}/) || ["", ""])[1];
  ok(/"\/sde-wechat\/"/.test(mine) && /"\/taste\/wds-chat\/"/.test(mine), "入口页用的是那两个地址");
  ok(MODES.indexOf('"/sde-wechat/"') >= 0 && MODES.indexOf('"/taste/wds-chat/"') >= 0,
    "与 sde-modes.js 的 SDE_MODES 同址（三处入口不许各写各的）");
  const page = fs.readFileSync("/home/claude/site/public/index.html", "utf8");
  ok(/assets\/sde-portal\.js/.test(page), "首页引入了入口页模块");
}

console.log("\n===== " + PASS + " PASS / " + FAILS + " FAIL =====");
process.exit(FAILS ? 1 : 0);
