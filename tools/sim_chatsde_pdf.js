/* sim_chatsde_pdf.js —— ChatSDE「导出为 PDF」的护栏
 *   ① /assets/wds-pdf.js 真 require 进来跑：doc() 是纯函数、scrub() 真的铲得干净
 *   ② 从 public/wds-mode.js 里抠出 pdfBlocks / PDF_DROP，配一副手搓的假 DOM 真跑
 *   ③ 源码级：出口挂了一处、模块带版本串、空态提示不许被加回来
 * 跑法：node tools/sim_chatsde_pdf.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");          // 不写死沙盒绝对路径（12 个老 sim 栽在这）
let pass = 0, fail = 0;
const ok = (n, c) => { if (c) { pass++; console.log("  ✓ " + n); } else { fail++; console.log("  ✗ " + n); } };

/* ═══ 一、模块本身 ═══ */
console.log("── /assets/wds-pdf.js ──");
const PDF = require(path.join(ROOT, "public/assets/wds-pdf.js"));
ok("导出 VERSION/doc/scrub/print/fitWide", PDF.VERSION >= 2 && typeof PDF.doc === "function" && typeof PDF.scrub === "function" && typeof PDF.print === "function" && typeof PDF.fitWide === "function");

const H = PDF.doc({
  title: "与 WDS 的对话",
  meta: ["2026-08-01", "3 轮", "ChatSDE · sdeuniverses.com"],
  katex: "/assets/katex/katex.min.css",
  foot: "导出自 ChatSDE",
  blocks: [
    { q: "什么是发生学？", qLabel: "我", aLabel: "WDS", html: "<p>先说<b>三方程</b>。</p><table><tr><th>S</th><td>显露</td></tr></table>" },
    { q: "再举个例子", qLabel: "我", aLabel: "WDS", html: "<h2>例子</h2><ul><li>一</li></ul>" },
  ],
});
ok("是一份完整 html（doctype + html 闭合）", /^<!DOCTYPE html><html /.test(H) && H.trim().endsWith("</html>"));
ok("标题进了 <title> 与封面", H.indexOf("<title>与 WDS 的对话</title>") > 0 && H.indexOf("<h1>与 WDS 的对话</h1>") > 0);
ok("三条 meta 都在", ["2026-08-01", "3 轮", "sdeuniverses.com"].every((s) => H.indexOf(s) > 0));
ok("提问与回答正文都在", H.indexOf("什么是发生学？") > 0 && H.indexOf("三方程") > 0 && H.indexOf("<h2>例子</h2>") > 0);
ok("角色标签在（我 / WDS）", H.indexOf(">我</b>") > 0 && H.indexOf(">WDS</div>") > 0);
ok("页脚在", H.indexOf("导出自 ChatSDE") > 0);
ok("引了自托管 katex 样式（公式不靠 CDN）", H.indexOf('href="/assets/katex/katex.min.css"') > 0);
ok("两轮之间有分隔线（一轮一段，不糊成一坨）", (H.match(/<hr class=rule>/g) || []).length === 1);

// 排印口径：这几条错一条，出来的 PDF 就不像一份稿子
ok("@page 设了 A4 与页边距", /@page\{size:A4;margin:/.test(H));
ok("中文字体栈在最前（不靠浏览器默认宋体运气）", /Songti SC|Noto Serif CJK SC/.test(H));
ok("强制打印颜色（否则金线与底色被浏览器吞掉）", /print-color-adjust:exact/.test(H));
ok("提问块不许被切页", /\.q\{[^}]*break-inside:avoid/.test(H));
ok("标题后不许分页（孤行标题）", /break-after:avoid/.test(H));
ok("代码块自动折行（PDF 没有横向滚动条）", /\.a pre\{[^}]*white-space:pre-wrap/.test(H));

/* scrub：稿子里不许留能动的东西 */
const dirty = '<p onclick="x()">a</p><script>bad()<\/script><button class=wdsm-act>复制</button>' +
  '<style>*{}</style><a href="javascript:evil()">走</a><img src=x onerror="y()">';
const cleaned = PDF.scrub(dirty);
ok("scrub 铲掉 <script>", cleaned.indexOf("bad()") < 0);
ok("scrub 铲掉 <style>", cleaned.toLowerCase().indexOf("<style") < 0);
ok("scrub 铲掉按钮整块（含文字）", cleaned.indexOf("<button") < 0 && cleaned.indexOf("复制") < 0);
ok("scrub 铲掉 on* 事件属性（带引号与不带引号两种）", !/on(click|error)\s*=/i.test(cleaned));
ok("scrub 掐掉 javascript: 链接", cleaned.indexOf("javascript:") < 0);
ok("scrub 留下正文与图片", cleaned.indexOf("<p") === 0 && cleaned.indexOf("<img") > 0);
ok("doc() 对传进来的 html 也过一遍 scrub", PDF.doc({ blocks: [{ html: "<script>z()<\/script><p>留着</p>" }] }).indexOf("z()") < 0);

/* 注入：标题与 meta 是纯文本，必须转义而不是当 html 贴 */
const X = PDF.doc({ title: '<img src=x onerror="hack()">', meta: ['"><script>h()<\/script>'], blocks: [] });
ok("标题里的尖括号被转义（当文本贴，不当 html）", X.indexOf("&lt;img") > 0 && X.indexOf("<img") < 0);
ok("meta 里的注入被转义", X.indexOf("hack()") < 0 && X.indexOf("h()") < 0 || X.indexOf("&lt;script&gt;") > 0);
ok("空对话也出得了一份合法稿子", /<\/html>$/.test(PDF.doc({}).trim()));

/* ═══ 一之二、公式（2026-08-01「升级为最高配置」）═══ */
console.log("── 公式 ──");
const KTX = '<span class="katex"><span class="katex-mathml"><math xmlns="http://www.w3.org/1998/Math/MathML">' +
  '<semantics><mrow><mi>S</mi></mrow><annotation encoding="application/x-tex">S=F(D,E)</annotation></semantics>' +
  '</math></span><span class="katex-html" aria-hidden="true"><span class="base">S</span></span></span>';
const KC = PDF.scrub(KTX);
ok("KaTeX 的可视 HTML 原样留着", KC.indexOf("katex-html") > 0 && KC.indexOf('<span class="katex">') === 0);
// 一条公式 KaTeX 出两份：MathML（含 TeX 原文）＋ 可视 HTML。屏幕上前者靠 clip 藏起来，
// 印进 PDF 之后照样躺在文字层里——选中/搜索会把同一条式子取出三遍。
ok("重复的 MathML 连同 TeX 原文一并摘掉", KC.indexOf("katex-mathml") < 0 && KC.indexOf("annotation") < 0);
ok("摘 MathML 不会误伤正文", PDF.scrub("<p>a</p>" + KTX + "<p>b</p>").indexOf("<p>b</p>") > 0);

const M = PDF.doc({ blocks: [{ html: KTX }], katex: "/assets/katex/katex.min.css", base: "https://sdeuniverses.com/" });
ok("<base> 钉住了（srcdoc 的相对地址各家解析不一）", M.indexOf('<base href="https://sdeuniverses.com/">') > 0);
ok("引的是站内自托管 katex 样式", M.indexOf('href="/assets/katex/katex.min.css"') > 0);
// katex.min.css 自带 .katex-display{overflow-x:auto}——屏幕上是滚动条，纸上就是被裁掉一截
ok("块级公式改回 overflow visible（否则印出来缺一截）", /\.katex-display\{[^}]*overflow-x:visible/.test(M));
ok("块级公式不许被切页", /\.katex-display\{[^}]*break-inside:avoid/.test(M));
ok("**没有**给 .katex 设 max-width（一设就永远量不出超宽）", !/\.katex-display>\.katex\{[^}]*max-width/.test(M));
ok("KaTeX 装不上时的 $…$ 兜底也有样式", /\.wdsm-tex\.raw\{/.test(M) && /\.wdsm-tex\.blk\{/.test(M));

/* fitWide：配一副只回答"多宽"的假 document 直测缩放判据 */
function fakeBox(w) {
  const inner = { style: {}, offsetHeight: 40, offsetWidth: w, scrollWidth: w, getBoundingClientRect: () => ({ width: w }) };
  const box = { style: {}, attrs: {}, querySelector: () => inner, firstElementChild: inner,
                setAttribute: (k, v) => { box.attrs[k] = v; }, _inner: inner };
  return box;
}
function runFit(hostW, boxes) {
  PDF.fitWide({ querySelector: (s) => (s === ".wrap" ? { clientWidth: hostW } : null), querySelectorAll: () => boxes });
}
const narrow = fakeBox(400), wide = fakeBox(1200), huge = fakeBox(9000);
runFit(600, [narrow, wide, huge]);
ok("没超宽的公式一个字节都不动", !narrow._inner.style.transform && !narrow.attrs["data-fit"]);
// 缩的是内层 .katex，外层留着占位——缩外层会把上下留白一起压扁
ok("超宽的被等比缩到版心（缩的是内层）", /^scale\(0\.49/.test(wide._inner.style.transform || "") && wide.attrs["data-fit"] === "0.498" && !wide.style.transform);
ok("缩放有下限 0.45（再小就不是给人读的了）", huge.attrs["data-fit"] === "0.450");
ok("缩过的外层收了高、切了溢出（transform 不改布局高度）", wide.style.overflow === "hidden" && /px$/.test(wide.style.height || ""));
ok("版心量不到就整段跳过，不乱缩", (() => { const b = fakeBox(9000); PDF.fitWide({ querySelector: () => null, querySelectorAll: () => [b] }); return !b._inner.style.transform; })());
ok("传进来的不是 document 也不炸", (() => { try { PDF.fitWide(null); PDF.fitWide({}); return true; } catch (e) { return false; } })());

/* ═══ 二、抠出 pdfBlocks 配假 DOM 真跑 ═══ */
console.log("── pdfBlocks（真代码 + 假 DOM）──");
const SRC = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");
const grabDrop = /var PDF_DROP = "[^"]+";/.exec(SRC);
const grabFn = /function pdfBlocks\(\) \{[\s\S]*?\n  \}/.exec(SRC);
ok("抠得到 PDF_DROP 与 pdfBlocks", !!grabDrop && !!grabFn);

/* 手搓最小 DOM：只实现 pdfBlocks 用到的那几件事。
   （本机没有 jsdom；而这段逻辑要测的是"铲干净没有"，不需要真排版引擎。） */
function mk(tag, cls, text) { return { tag, cls: cls || "", text: text || "", kids: [], parentNode: null }; }
function add(p, c) { c.parentNode = p; p.kids.push(c); return p; }
function matches(n, sel) {
  return sel.startsWith(".") ? (" " + n.cls + " ").indexOf(" " + sel.slice(1) + " ") >= 0 : n.tag === sel;
}
function walk(n, out) { n.kids.forEach((k) => { out.push(k); walk(k, out); }); return out; }
function qsa(n, sels) {
  const parts = String(sels).split(",").map((s) => s.trim()).filter(Boolean);
  const all = walk(n, []);
  const hit = [];
  parts.forEach((p) => {
    const seq = p.split(/\s+/);
    if (seq.length === 1) all.forEach((x) => { if (matches(x, seq[0]) && hit.indexOf(x) < 0) hit.push(x); });
    else all.forEach((x) => { if (matches(x, seq[0])) walk(x, []).forEach((y) => { if (matches(y, seq[1]) && hit.indexOf(y) < 0) hit.push(y); }); });
  });
  return hit;
}
function inner(n) { return n.kids.map((k) => "<" + k.tag + (k.cls ? " class=" + k.cls : "") + ">" + k.text + inner(k) + "</" + k.tag + ">").join(""); }
function deco(n) {
  n.querySelector = (s) => qsa(n, s)[0] || null;
  n.querySelectorAll = (s) => qsa(n, s);
  Object.defineProperty(n, "textContent", { get: () => n.text + n.kids.map((k) => k.text).join(""), configurable: true });
  Object.defineProperty(n, "innerHTML", { get: () => inner(n), configurable: true });
  n.cloneNode = () => { const c = mk(n.tag, n.cls, n.text); n.kids.forEach((k) => add(c, deco(k.cloneNode ? k.cloneNode() : k))); return deco(c); };
  n.removeChild = (c) => { const i = n.kids.indexOf(c); if (i >= 0) n.kids.splice(i, 1); return c; };
  n.kids.forEach(deco);
  return n;
}

const msgs = mk("div", "wdsm-msgs");
function turn(q, aParts) {
  const tn = mk("div", "wdsm-turn");
  const qd = mk("div", "wdsm-q"); add(qd, mk("span", "", q)); add(tn, qd);
  const a = mk("div", "wdsm-a");
  aParts.forEach((p) => add(a, p));
  add(tn, a);
  add(tn, mk("div", "wdsm-acts", "复制重答"));     // 动作条挂在 turn 上，不该进稿
  add(msgs, tn);
  return tn;
}
turn("第一问", [mk("p", "", "第一答"), mk("div", "wdsm-think", "内部思考不该外传"), mk("span", "cur", "▊")]);
turn("第二问", [mk("h2", "", "小标题"), mk("button", "wdsm-act", "交给智能体")]);
deco(msgs);

const runner = new Function("msgsEl", "history", "mdRender",
  grabDrop[0] + "\n" + grabFn[0] + "\nreturn pdfBlocks();");
const blocks = runner(msgs, [], () => "");
ok("两轮都取到了", blocks.length === 2);
ok("提问取的是文本不是 html", blocks[0].q === "第一问" && blocks[1].q === "第二问");
ok("回答正文在", blocks[0].html.indexOf("第一答") > 0 && blocks[1].html.indexOf("小标题") > 0);
ok("思考过程没进稿（界面里本来就是收起的）", blocks[0].html.indexOf("内部思考不该外传") < 0);
ok("流式光标 ▊ 没进稿", blocks[0].html.indexOf("▊") < 0);
ok("回答里的按钮没进稿", blocks[1].html.indexOf("<button") < 0 && blocks[1].html.indexOf("交给智能体") < 0);
ok("动作条没进稿", blocks[0].html.indexOf("重答") < 0);
ok("**没有改坏页面上的原 DOM**（铲的是克隆体）", msgs.querySelectorAll(".wdsm-think").length === 1);

// 回退路径：DOM 一个 turn 都没有时，按 history 重渲，不能返回空
const back = new Function("msgsEl", "history", "mdRender",
  grabDrop[0] + "\n" + grabFn[0] + "\nreturn pdfBlocks();")(
  deco(mk("div", "wdsm-msgs")),
  [{ role: "reader", text: "问" }, { role: "wds", text: "答" }],
  (s) => "<p>" + s + "</p>");
ok("DOM 取不到时按 history 回退出稿", back.length === 1 && back[0].q === "问" && back[0].html.indexOf("答") > 0);

/* ═══ 三、源码级 ═══ */
console.log("── 接线 ──");
// 出口在顶栏，不在「成文 · PPT」下拉里——PDF 是零调用的原样打印，跟"调基底重新锻一篇"
// 不是一回事，埋进成文菜单既难找、也把它说成了成文的子功能。（用户 2026-08-01 令）
ok("顶栏有一颗独立 PDF 按钮", (SRC.match(/wdsm-tbtn wdsm-pdfbtn/g) || []).length === 1);
ok("按钮紧挨着「成文 · PPT」", /wdsm-distbtn'><\/button>" \+\n\s*"<button class='wdsm-tbtn wdsm-pdfbtn/.test(SRC));
ok("点了走 exportPdf", /\.wdsm-pdfbtn"\)\.onclick = function \(\) \{ exportPdf\(\); \}/.test(SRC));
ok("**没有**再挂在成文下拉里", SRC.indexOf("wdsm-pdfbtn-installed") < 0 && SRC.indexOf("mPdfS") < 0);
ok("按钮文字与 title 随语言刷新", /wdsm-pdfbtn"\); pb\.textContent = t\("bPdf"\); pb\.title = t\("bPdfT"\)/.test(SRC));
ok("模块按版本串引（改了模块不 bump ⇒ 缓存里还是老的）", /wds-pdf\.js\?v=" \+ PDF_WANT/.test(SRC));
ok("装不上模块时说人话而不是静默", /if \(!ok\) \{ alert\(t\("pdfNo"\)\); return; \}/.test(SRC));
ok("出稿后把「目标选另存为 PDF」讲给用户", /toast\(t\("pdfTip"\)\)/.test(SRC));
ok("空对话不让导（needTalk）", /function exportPdf\(\) \{\s*\n\s*if \(!history\.length\) \{ alert\(t\("needTalk"\)\)/.test(SRC));
["bPdf", "bPdfT", "pdfWait", "pdfTip", "pdfNo", "pdfMe", "pdfFoot"].forEach((k) => {
  ok("中英两套文案都有 " + k, (SRC.match(new RegExp("\\b" + k + ":", "g")) || []).length === 2);
});
ok("公式走自托管 katex（打印时 CDN 未必在）", SRC.indexOf('katex: "/assets/katex/katex.min.css"') > 0);
ok("出稿带 base", /base: \(location && location\.origin/.test(SRC));
ok("模块要到 v2（等字体、缩超宽公式）", /var PDF_WANT = 2;/.test(SRC));
// KaTeX 挂在 CDN 上，等于把"界面上有没有公式"押在第三方可达性上，PDF 跟着一起赌
ok("KaTeX 自托管排第一顺位", /var KTX_HOSTS = \["\/assets\/katex",/.test(SRC));
ok("导出前先把没排的公式排完（pdfMath 在取稿之前）",
   /pdfMath\(function \(\) \{\n\s*var blocks = pdfBlocks\(\);/.test(SRC));
// typeset() 按 MATH[data-m] 取源码，而 MATH 是上一次 mdRender 的全局数组——
// 导出这一刻下标撞上就会渲染出另一条式子。错得像对的，比空着更坏。
ok("pdfMath 不碰全局 MATH（一律以 DOM 里的 $…$ 原文为准）",
   (() => { const m = /function pdfMath\(then\) \{[\s\S]*?\n  \}/.exec(SRC); return m && m[0].indexOf("MATH[") < 0 && m[0].indexOf("textContent") > 0; })());
ok("KaTeX 拉不动也要出稿（有超时兜底）", /setTimeout\(go, 6000\)/.test(SRC));
// 上游（用户令）刻意删掉的空态提示，不许借这次改动加回来
ok("没有把空态 hero 提示加回来", SRC.indexOf("heroAfter") < 0
  && !/class=.?.?wdsm-hero-after/.test(SRC)
  && (SRC.match(/wdsm-hero-after/g) || []).length === 1);   // 只剩 CSS 里那条死规则，没有元素也没有文案

console.log((fail ? "✗ " : "✓ ") + pass + " 项通过，" + fail + " 项失败");
process.exit(fail ? 1 : 0);
