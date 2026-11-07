/* 护栏：PDF 下载锁不许咬到「打印出口」。
 * 病史：2026-11-04 全站禁下载的客户端锁按文案判下载口，把 ChatSDE 的「⤓ PDF」
 *       三颗按钮（顶栏整场对话 / 成文面板 / 画布菜单）一并灰掉且 disabled——
 *       而它们是排版后交给浏览器打印框，不取仓里任何文件。2026-11-07 修。
 * 判据两面都守：打印出口不锁、真下载口照锁。末尾做定向变异（抽掉豁免那一行必须当场红）。
 * 用法：node tools/sim_pdf_lock.js
 */
"use strict";
const fs = require("fs"), path = require("path");
const SRC = fs.readFileSync(path.join(__dirname, "..", "public/assets/pdf-lock.js"), "utf8");
let PASS = 0, FAIL = 0;
const ok = (c, m) => { if (c) { PASS++; console.log("  PASS " + m); } else { FAIL++; console.log("  FAIL " + m); } };

/* 从真文件里抠出判据段 eval（不复制一份代码，免得护栏与实现各走各的）。 */
function judgeOf(src) {
  const a = src.indexOf("  var TIP ="), b = src.indexOf("  function lock(");
  if (a < 0 || b < 0) throw new Error("锚点没了：pdf-lock.js 的结构变了，先修护栏再说");
  return new Function(src.slice(a, b) + "\n return { shouldLock: shouldLock, isPrintExit: isPrintExit };")();
}

/* 极简元素：只要 shouldLock 用到的那几样。closest 按祖先链逐个比对选择器。 */
function mk(tag, opt) {
  opt = opt || {};
  const el = {
    tagName: String(tag).toUpperCase(),
    textContent: opt.text || "",
    className: opt.cls || "",
    attrs: opt.attrs || {},
    parent: opt.parent || null,
    getAttribute(n) { return Object.prototype.hasOwnProperty.call(this.attrs, n) ? this.attrs[n] : null; },
    matchesSel(sel) {
      return sel.split(",").map((s) => s.trim()).some((s) => {
        if (s.startsWith("[") && s.endsWith("]")) return Object.prototype.hasOwnProperty.call(this.attrs, s.slice(1, -1).split("=")[0]);
        if (s.startsWith(".")) return this.className.split(/\s+/).includes(s.slice(1));
        if (s.startsWith("#")) return this.attrs.id === s.slice(1);
        return this.tagName === s.toUpperCase();
      });
    },
    closest(sel) { let n = this; while (n) { if (n.matchesSel(sel)) return n; n = n.parent; } return null; },
  };
  return el;
}

const J = judgeOf(SRC);
const layer = mk("div", { cls: "wdsm-layer" });
const menu = mk("div", { cls: "wdsm-menu" });

console.log("① 打印出口：一个字节都不下载，不许锁");
ok(!J.shouldLock(mk("button", { text: "⤓ PDF", cls: "wdsm-tbtn wdsm-pdfbtn", parent: layer })), "ChatSDE 顶栏「⤓ PDF」（导出整场对话）");
ok(!J.shouldLock(mk("button", { text: "⤓ PDF", cls: "wdsm-tbtn dpdfx", parent: layer })), "成文面板「⤓ PDF」");
ok(!J.shouldLock(mk("button", { text: "⤓ PDF", parent: menu })), "画布「⋯」菜单里的「⤓ PDF」");
ok(!J.shouldLock(mk("button", { text: "⤓ PDF", parent: menu })), "顶栏窄屏「⋯」菜单里代点的那一项");
ok(!J.shouldLock(mk("button", { text: "🖨 导出 PDF · 矢量文字", attrs: { "data-pdf-print": "1", id: "pdfBtn" } })), "挂了 data-pdf-print 的打印按钮（智能问对）");

console.log("② 真下载口：照锁不误");
ok(J.shouldLock(mk("a", { text: "⤓ 下载 PDF", attrs: { href: "/books/m/609/x.pdf", download: "" } })), "专著页的 PDF 下载链接");
ok(J.shouldLock(mk("button", { text: "下载 PDF" })), "写着「下载 PDF」的普通按钮");
ok(J.shouldLock(mk("a", { text: "Download", cls: "download", attrs: { href: "/x.pdf" } })), "英文 Download 的 .pdf 链接");
ok(!J.shouldLock(mk("button", { text: "⤓ 导出 Markdown", parent: layer })), "导出 Markdown 本来就不该被锁");

console.log("③ 定向变异：抽掉豁免那一行，①必须当场红");
const MUT = SRC.replace("    if (isPrintExit(el)) return false;", "");
if (MUT === SRC) { FAIL++; console.log("  FAIL 变异没切中（豁免那一行的写法变了）"); }
else {
  const M = judgeOf(MUT);
  ok(M.shouldLock(mk("button", { text: "⤓ PDF", cls: "wdsm-pdfbtn", parent: layer })), "去掉豁免后顶栏 PDF 又被判成下载口（证明这条护栏真的在守）");
}

console.log("\n" + PASS + " PASS / " + FAIL + " FAIL");
process.exit(FAIL ? 1 : 0);
