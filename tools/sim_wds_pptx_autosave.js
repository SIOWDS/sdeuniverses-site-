/* 成文·PPT「生成即自动保存」的护栏（2026-09-02）。
   用户定的口径：PPT 生成后自动落盘，免得在一排按钮里错点；「存为 .pptx」按钮照留，想另存再点。
   本 sim 两层：①静态对账——收尾 deckPrep 回调里挂了 pxSave(true)，且三个不该自动存的条件都在；
   ②把 pxSave 那一段抠出来在 mock 里跑一遍：自动一趟落盘一次、状态条写「已自动保存」、手动再点仍能存。 */
"use strict";
const fs = require("fs");
const ROOT = "/home/claude/site";
const wm = fs.readFileSync(ROOT + "/public/wds-mode.js", "utf8");
let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };

console.log("── 一 · 静态对账");
ok(/dPptxAuto: "已自动保存 \.pptx/.test(wm) && /dPptxAuto: "Saved \.pptx automatically/.test(wm), "中英文案各一条");
ok(/pxSave = function \(auto\)/.test(wm), "存盘逻辑独立成 pxSave(auto)");
ok(/pxBtn\.onclick = function \(\) \{ pxSave\(false\); \};/.test(wm), "按钮仍在：手动点走 pxSave(false)");
const hook = wm.match(/deckPrep\(text, function \(d\) \{[\s\S]*?\}\);\n\s*\} catch \(e\) \{\}/);
ok(!!hook, "收尾 deckPrep 回调里挂了自动保存");
if (hook) {
  const h = hook[0];
  ok(/!existing/.test(h), "取回的旧稿不自动存");
  ok(/!dStopped/.test(h), "读者按停的不自动存");
  ok(/!dAutoSaved/.test(h) && /dAutoSaved = true/.test(h), "一场只自动存一次");
  ok(/pxSave\(true\)/.test(h), "自动那一趟传 auto=true");
  ok(/b9Show\(text\)/.test(h), "原有的 b9Show 没被挤掉");
}

console.log("── 二 · 抠出 pxSave 在 mock 里跑");
const seg = wm.slice(wm.indexOf("      pxSave = function (auto) {"), wm.indexOf("      pxBtn.onclick = function () { pxSave(false); };"));
ok(seg.length > 200, "抠到 pxSave 段");
const saved = [];
const T = { dPptxWait: "等", dPptxNo: "无", dPptxOk: "已生成 幻灯片 ", dPptxAuto: "已自动保存 .pptx（幻灯片 ", dPptxAutoS: "）。" };
const ctx = {
  text: "# t\n---\n## a\n- b", stat: { textContent: "" }, deckReady: { title: "T", slides: [{}, {}] }, tpl: "", kind: "deck",
  window: { WDSPptx: { VERSION: 10, blob: () => "BLOB" } },
  t: (k) => T[k], deckOf: () => null, tplTheme: () => "", fileTag: () => "WDS", safeName: (s) => s, kindT: () => "PPT", stampName: () => "s",
  pptxBoot: () => {}, saveBlobToDir: (nm, blob, say) => { saved.push(nm); say("已存到 D / " + nm); },
};
const fn = new Function(...Object.keys(ctx), "var pxSave;\n" + seg + "\nreturn pxSave;");
const pxSave = fn(...Object.values(ctx));
pxSave(true);
ok(saved.length === 1 && /\.pptx$/.test(saved[0]), "自动一趟落盘一次");
ok(/^已自动保存 \.pptx（幻灯片 3）。 已存到/.test(ctx.stat.textContent), "状态条先写「已自动保存」再接目录回执（实得：" + ctx.stat.textContent + "）");
pxSave(false);
ok(saved.length === 2, "手动再点仍能另存一份");
ok(/^已存到/.test(ctx.stat.textContent), "手动那一趟状态条走原来的回执");

console.log((F ? "✗ " : "✓ ") + P + " passed, " + F + " failed");
process.exit(F ? 1 : 0);
