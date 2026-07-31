/* 三态切换器 /assets/sde-modes.js 的模拟。
 * 覆盖：三个落点（[data-sde-modes] / .nav-links / .top / 兜底浮动）· 当前态判定 ·
 *      问WDS 页不重复挂 · 顶栏旧的单按钮被取代（不留两个入口）·
 *      **跨文件一致性**：wds-mode.js 侧栏三档的目的地要与本模块的 SDE_MODES 逐一对上。
 * 用法：node tools/sim_sde_modes.js
 */
"use strict";
const fs = require("fs");
let PASS = 0, FAILS = 0;
function ok(c, m) { if (c) { PASS++; console.log("  PASS " + m); } else { FAILS++; console.log("  FAIL " + m); } }

const SRC = fs.readFileSync(require("path").join(__dirname, "../public/assets/sde-modes.js"), "utf8");
// 模块里的 CSS 是一长串 "…" + "…" 拼出来的，所以对源码直接跑 /\.sel\{[^"]*prop/ 这种正则
// 会在第一个引号处截断——属性只要恰好落在下一段就永远匹配不到，断言假失败（这坑踩过不止一次）。
// 先把拼接缝合掉再验。
const CSSFLAT = SRC.replace(/"\s*\+\s*"/g, "");
const WM = fs.readFileSync("/home/claude/site/public/wds-mode.js", "utf8");

/* ---------- 极简 DOM（节点用 createElement 建，所以嵌套是真的） ---------- */
class N {
  constructor(t) {
    this.tagName = String(t || "div").toUpperCase();
    this.children = []; this.className = ""; this.attrs = {}; this.style = {};
    this._text = ""; this.parentNode = null;
  }
  set textContent(v) { this._text = String(v); this.children.length = 0; }
  get textContent() { return this._text || this.children.map((c) => c.textContent).join(""); }
  appendChild(c) { c.parentNode = this; this.children.push(c); return c; }
  insertBefore(c, ref) { const i = this.children.indexOf(ref); c.parentNode = this; if (i < 0) this.children.push(c); else this.children.splice(i, 0, c); return c; }
  get nextSibling() { if (!this.parentNode) return null; const i = this.parentNode.children.indexOf(this); return this.parentNode.children[i + 1] || null; }
  removeChild(c) { const i = this.children.indexOf(c); if (i >= 0) this.children.splice(i, 1); c.parentNode = null; return c; }
  setAttribute(k, v) { this.attrs[k] = String(v); if (k === "class") this.className = String(v); }
  getAttribute(k) { return k === "class" ? this.className : (this.attrs[k] ?? null); }
  addEventListener() {}
  _all(out) { out.push(this); this.children.forEach((c) => c._all(out)); return out; }
  _match(sel) {
    if (sel[0] === "[") { const k = sel.slice(1, -1); return this.attrs[k] !== undefined; }
    if (sel[0] === ".") return this.className.split(/\s+/).includes(sel.slice(1));
    return this.tagName === sel.toUpperCase();
  }
  querySelector(s) { return this._all([]).slice(1).find((n) => n._match(s)) || null; }
  querySelectorAll(s) { return this._all([]).slice(1).filter((n) => n._match(s)); }
}
function freshDoc(path, opts) {
  opts = opts || {};
  const head = new N("head"), body = new N("body");
  const doc = {
    head, body, readyState: "complete",
    documentElement: new N("html"),
    createElement: (t) => new N(t),
    querySelector: (s) => head.querySelector(s) || body.querySelector(s),
    querySelectorAll: (s) => body.querySelectorAll(s),
    addEventListener() {},
  };
  const win = { location: { pathname: path }, document: doc };
  if (opts.wdsPage) win.WDSM_PAGE = 1;
  const store = {};
  const ls = { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = v; } };
  return { doc, win, ls, head, body };
}
function run(env) {
  // 每次都要一份干净的模块实例：模块自带 __sdeModesMounted 单例锁
  new Function("window", "document", "location", "localStorage", SRC)(env.win, env.doc, env.win.location, env.ls);
  return env.win.SDEModes;
}

console.log("① 浏览态：顶栏紧跟「问WDS」插一颗「SDE 微信」");
{
  const env = freshDoc("/column/some-piece/");
  const nav = new N("div"); nav.className = "nav-links";
  const search = new N("a"); search.className = "primary"; search.href = "/search/";
  const wds = new N("a"); wds.className = "zh-only wdsm-navbtn"; wds.href = "/taste/wds-chat/"; wds.textContent = "✦ 问WDS";
  const wdsEn = new N("a"); wdsEn.className = "en-only wdsm-navbtn"; wdsEn.href = "/taste/wds-chat/"; wdsEn.textContent = "✦ Ask WDS";
  const later = new N("a"); later.className = "zh-only"; later.textContent = "每日必读";
  [search, wds, wdsEn, later].forEach((n) => nav.appendChild(n));
  env.body.appendChild(nav);
  run(env);
  const pills = nav.querySelectorAll(".sdemx-pill");
  ok(pills.length === 2, "插了中英两颗（站点靠 body class 切 .zh-only/.en-only），实得 " + pills.length);
  ok(pills.every((p) => p.href === "/sde-wechat/"), "都指向 SDE 微信");
  ok(nav.children.indexOf(pills[0]) === nav.children.indexOf(wdsEn) + 1,
    "紧跟在「问WDS」后面，实得位置 " + nav.children.indexOf(pills[0]) + "（问WDS 在 " + nav.children.indexOf(wdsEn) + "）");
  ok(nav.children.indexOf(pills[1]) < nav.children.indexOf(later), "排在后面那些栏目链接之前");
  ok(!!nav.querySelector(".wdsm-navbtn"), "「问WDS」原样留着（不是被取代，是并排）");
  ok(!nav.querySelector(".sdemx"), "浏览态不画三段条——人就在浏览态，顶栏要的是通往另外两态的门");
  ok(!!env.head.querySelector("style"), "样式自带，不依赖页面");
  const home = nav.querySelector(".sdemx-home");
  // 2026-07-31 改口径：入口严格且唯一地对应域名根地址，第二门牌 /?portal=1 作废，
  // 这颗 △ 因此改指 "/"（根地址每次打开都是入口，见 tools/sim_portal_gate.js）。
  ok(!!home && home.href === "/", "顶栏有一颗回入口页的 △，指的是域名根，实得 " + (home && home.href));
  ok(!!home && nav.children.indexOf(home) === nav.children.indexOf(pills[1]) + 1, "△ 排在两颗药丸之后");
  // 2026-07-31 改口径：这颗 △ 上面要写「系统入口」。原来的断言是 textContent === "△"
  // （固化"图形按钮不带字"），已随口径作废。保住的是原意里仍成立的那半句——**一颗即可**：
  // 标签成对是靠 zh-only/en-only 由 CSS 隐掉一个，不是像药丸那样插两颗 <a>。
  const hlabs = home.querySelectorAll(".sdemx-hlab");
  ok(hlabs.length === 2, "△ 带一对中英标签，实得 " + hlabs.length + " 个");
  ok(hlabs[0].className.indexOf("zh-only") >= 0 && hlabs[0].textContent === "系统入口",
    "中文标签是「系统入口」，实得「" + (hlabs[0] && hlabs[0].textContent) + "」");
  ok(hlabs[1].className.indexOf("en-only") >= 0 && hlabs[1].textContent === "System Entry",
    "英文标签是「System Entry」，实得「" + (hlabs[1] && hlabs[1].textContent) + "」");
  ok(nav.querySelectorAll(".sdemx-home").length === 1, "△ 仍然只有一颗（标签靠 CSS 隐显，不是插两颗按钮）");
  ok(home.textContent.indexOf("△") >= 0, "△ 字形还在");
  const kids = Array.prototype.slice.call(home.children);
  ok(kids.indexOf(hlabs[0]) < kids.findIndex((c) => c.tagName === "I"), "标签排在 △ 之前（字在上、三角在下）");
  ok(!home.querySelector(".sdemx-fire"), "内页那颗 △ 是安静的（烧一处才是记号，处处都烧就成了噪音）");
}

console.log("①b 只有浏览首页那颗 △ 在烧，且火盖住三角形");
{
  const env = freshDoc("/");
  const nav = new N("div"); nav.className = "nav-links";
  const wds = new N("a"); wds.className = "zh-only wdsm-navbtn"; wds.href = "/taste/wds-chat/";
  nav.appendChild(wds); env.body.appendChild(nav);
  run(env);
  const home = nav.querySelector(".sdemx-home");
  const hf = home.querySelector(".sdemx-fire");
  ok(!!hf && hf.querySelectorAll("b").length === 3, "首页那颗在烧，三层火舌");
  ok(hf.querySelectorAll(".sdemx-sp").length === 12, "火星十二粒，实得 " + hf.querySelectorAll(".sdemx-sp").length);
  const kids = home.children.map((c) => c.className || c.tagName);
  ok(kids.indexOf("sdemx-fire") === kids.length - 1,
    "火最后加入＝盖在三角形上面，不是垫在它背后，实得顺序 " + kids.join(" > "));
  ok(/\.sdemx-fire\{[^"]*z-index:2/.test(SRC), "火层 z-index 在字之上");
  ok(/\.sdemx-fire \.f3\{[^"]*opacity:\.6/.test(SRC), "内焰压到半透明——不然三角形会被糊没");
  ok(!/mix-blend-mode:\s*screen/.test(SRC),
    "不用 screen 混合：顶栏是米色浅底，screen 会把橙色直接洗成白，火就没了");
  ok(/text-shadow:0 0 8px rgba\(255,140,20/.test(SRC), "三角形本身调成受热的颜色，不然在火里会变成一个黑洞");
  // 「系统入口」四个字在烧着的这一颗上也得有，而且必须压在火之上：
  // 火层是 z-index:2、△ 是 1（有意让火裹住三角），标签若不抬到 3，火苗窜上来就把字糊掉了。
  ok(home.querySelectorAll(".sdemx-hlab").length === 2, "烧着的这颗也带中英标签");
  ok(/\.sdemx-hlab\{[^}]*z-index:3/.test(CSSFLAT), "标签 z-index:3，压在火层（2）之上");
  ok(/\.sdemx-home\{[^}]*flex-direction:column/.test(CSSFLAT), "按钮竖排：字在上、三角在下");
  ok(/\.sdemx-hlab\{[^}]*white-space:nowrap/.test(CSSFLAT), "四个字不许折行");
}

console.log("② 当前态按路径判定");
{
  const e1 = freshDoc("/sde-wechat/"); e1.body.appendChild(Object.assign(new N("div"), { className: "top" }));
  const M1 = run(e1);
  ok(M1.current() === "im", "在 /sde-wechat/ 判为 SDE 微信，实得 " + M1.current());
  const box = e1.body.querySelector(".sdemx");
  ok(box.querySelectorAll("a")[1].className === "on", "高亮的是第二档");
  ok(box.querySelectorAll("a").length === 4 && box.querySelector(".sdemx-home"),
    "三段条尾也有回入口的 △（三态＋一个回门口，不是四态），实得 " + box.querySelectorAll("a").length + " 个");
  ok(box.parentNode.className === "top", "微信页没有 .nav-links，就近挂到 .top 顶栏");
}
{
  const e2 = freshDoc("/taste/chatsde/");
  const M2 = run(e2);
  ok(M2.current() === "wds", "在 /taste/chatsde/ 判为 SDE 对话，实得 " + M2.current());
  // 旧门牌仍在流通（跳转页），切换器不能把它错标成"浏览"
  const e2b = freshDoc("/taste/wds-chat/");
  const M2b = run(e2b);
  ok(M2b.current() === "wds", "旧址 /taste/wds-chat/ 也仍判为 SDE 对话，实得 " + M2b.current());
}

console.log("③ 兜底浮动 / 指定落点 / 问WDS 页不挂");
{
  const e = freshDoc("/books/m/46/read.html");
  run(e);
  const box = e.body.querySelector(".sdemx");
  ok(!!box && box.className.includes("sdemx-float"), "页面里找不到落点时才浮动（浮动是兜底不是首选）");
  ok(box.parentNode === e.body, "浮动条挂在 body 上");
}
{
  const e = freshDoc("/anything/");
  const slot = new N("div"); slot.setAttribute("data-sde-modes", "");
  e.body.appendChild(slot);
  run(e);
  ok(e.body.querySelector(".sdemx").parentNode === slot, "页面指定了落点就用它（[data-sde-modes] 优先级最高）");
}
{
  const e = freshDoc("/taste/chatsde/", { wdsPage: true });
  const M = run(e);
  ok(!e.body.querySelector(".sdemx"), "问WDS 是全屏层，模块不重复挂（它自己侧栏里画）");
  ok(typeof M.build === "function", "但仍然把 build/list 暴露出来，谁要谁自己画");
}

console.log("④ 跨文件一致：问WDS 侧栏三档 vs 本模块 SDE_MODES");
{
  const hrefs = (SRC.match(/href:\s*"([^"]+)"/g) || []).map((s) => s.replace(/.*"([^"]+)".*/, "$1"));
  const m = WM.match(/var TAB_GO = \{([^}]+)\}/);
  ok(!!m, "wds-mode.js 里有 TAB_GO 目的地表");
  const tab = m ? (m[1].match(/"([^"]+)"/g) || []).map((s) => s.slice(1, -1)) : [];
  ok(hrefs.length === 3, "模块里三个目的地，实得 " + hrefs.join(" "));
  ok(JSON.stringify(tab) === JSON.stringify(hrefs),
    "两处目的地逐一对上（定义只有一处，但接线有两处，接线是会漂的）：模块 " + hrefs.join(" ") + " ｜ 侧栏 " + tab.join(" "));
  ok(/data-m='im'/.test(WM), "侧栏有 SDE 微信那一档");
  ok(/tabBrowse:/.test(WM) && /tabIm:/.test(WM), "三档都有文案（不许再出现没名字的按钮）");
  ok(/sc\.onerror = injectNav/.test(WM), "三态模块拉不到时退回老的单按钮注入（宁可少一个入口，不能一个都没有）");
  const pm = (SRC.match(/var PORTAL = "([^"]+)"/) || [])[1];
  const pw = (WM.match(/var PORTAL_URL = "([^"]+)"/) || [])[1];
  ok(pm && pm === pw, "回入口页的地址两处同一串（模块 " + pm + " ｜ 问WDS " + pw + "）");
  ok(/wdsm-portal/.test(WM), "问WDS 侧栏也有回入口的 △");
}

console.log("⑤ 微信页确实引了模块");
{
  const wechat = fs.readFileSync("/home/claude/site/public/sde-wechat/index.html", "utf8");
  ok(/assets\/sde-modes\.js/.test(wechat), "/sde-wechat/ 引入了三态模块");
}

console.log("\n===== " + PASS + " PASS / " + FAILS + " FAIL =====");
process.exit(FAILS ? 1 : 0);
