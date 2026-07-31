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
ok("导出 VERSION/doc/scrub/print", PDF.VERSION >= 1 && typeof PDF.doc === "function" && typeof PDF.scrub === "function" && typeof PDF.print === "function");

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
ok("菜单里挂了一处出口（且只有一处）", (SRC.match(/wdsm-pdfbtn-installed/g) || []).length === 1);
ok("出口紧挨着「导出本场对话」", /exportSession\(\); \};\n    menu\.appendChild\(dl\);\n    var pf = el\("button"/.test(SRC));
ok("点了走 exportPdf", /pf\.onclick[^\n]*exportPdf\(\)/.test(SRC));
ok("模块按版本串引（改了模块不 bump ⇒ 缓存里还是老的）", /wds-pdf\.js\?v=" \+ PDF_WANT/.test(SRC));
ok("装不上模块时说人话而不是静默", /if \(!ok\) \{ alert\(t\("pdfNo"\)\); return; \}/.test(SRC));
ok("出稿后把「目标选另存为 PDF」讲给用户", /toast\(t\("pdfTip"\)\)/.test(SRC));
ok("空对话不让导（needTalk）", /function exportPdf\(\) \{\s*\n\s*if \(!history\.length\) \{ alert\(t\("needTalk"\)\)/.test(SRC));
["mPdf", "mPdfS", "pdfWait", "pdfTip", "pdfNo", "pdfMe", "pdfFoot"].forEach((k) => {
  ok("中英两套文案都有 " + k, (SRC.match(new RegExp("\\b" + k + ":", "g")) || []).length === 2);
});
ok("公式走自托管 katex（打印时 CDN 未必在）", SRC.indexOf('katex: "/assets/katex/katex.min.css"') > 0);
// 上游（用户令）刻意删掉的空态提示，不许借这次改动加回来
ok("没有把空态 hero 提示加回来", SRC.indexOf("heroAfter") < 0
  && !/class=.?.?wdsm-hero-after/.test(SRC)
  && (SRC.match(/wdsm-hero-after/g) || []).length === 1);   // 只剩 CSS 里那条死规则，没有元素也没有文案

console.log((fail ? "✗ " : "✓ ") + pass + " 项通过，" + fail + " 项失败");
process.exit(fail ? 1 : 0);
