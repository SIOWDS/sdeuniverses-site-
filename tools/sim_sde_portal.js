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
    this.children = []; this.className = ""; this.attrs = {}; this.style = {};
    this._text = ""; this.parentNode = null; this.type = "";
    this.style.setProperty = (k, v) => { this.style[k] = v; };   // 桩补：模块用它设 --c 色相变量
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
const poly = box.querySelector("polygon");
ok(!!poly, "三角形是真画出来的（polygon）");
const pts = String(poly.attrs.points || "").split(" ");
const nodePos = nodes.map((n) => parseFloat(n.style.left) + "," + parseFloat(n.style.top));
ok(pts.length === 3 && pts.join(" ") === nodePos.join(" "),
  "三个入口正落在三角形的三个顶端（同一组坐标，不是各写一份）：" + pts.join(" ") + " ｜ " + nodePos.join(" "));
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
  ok(sp.length === 9, "火星九粒，实得 " + sp.length);
  ok(new Set(sp.map((x) => x.style.animationDelay)).size > 1, "火星错开起飞（同时起飞就成了一排跳动的点，不像火）");
  const cols = new Set(sp.map((x) => x.style.background));
  ok(cols.has(NODEC(nodes[0])), "火星里掺了本入口自己的色（同为一种火，各带各的色）");
  ok(cols.size >= 3, "其余是首页那套火色（橙/琥珀/橘），实得 " + cols.size + " 种");
  ok(/z-index:1/.test(SRC) && /sdep-dotwrap/.test(SRC), "火在下、图标在上（分层，别让火盖住图标）");
  ok(/@keyframes sdepFlick/.test(SRC), "火在明灭，不是一张静止的橙色贴纸");
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
