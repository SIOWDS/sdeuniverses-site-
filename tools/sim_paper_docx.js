/* sim_paper_docx.js —— /search/「成文一篇 / 打磨修改」的 **Word(.docx) 出口** 护栏（2026-08-24 新增）
 *
 * 为什么要有它：这台机器此前只有 PDF 一个出口，而那条链要走 html2canvas 光栅化——
 * 长稿超画布上限会**静默给白纸**（见 index.html 里 canvasInk 上方那段病史），
 * 而且出来的是图，读者拿不进 Word 接着改。Word 这条路是纯文本造 zip，本来就该独立于 PDF。
 * 于是本文件守的第一条就是**它真的独立**：wordActs 的亮灯必须排在 buildPdf 之前，
 * PDF 白页/超限/引擎加载失败都不许把 Word 一起拖下水。
 *
 * 五组：
 *   [一] 抠出 paperToMd 真跑（标题识别、Markdown 兜底共用、未完成稿红旗跟到 Word）
 *   [二] 端到端真造一份 docx（用站内那份 /assets/sde-docx.js，不是自己写一个）
 *   [三] dlDocx 接线真跑（从「点按钮」那一层进，不是从 build 进）
 *   [四] 源码契约（独立于 PDF、戳与账本一致、miss 有留住、段数式的字面量不许手抄）
 *   [五] 变异检验：把标题分支拆掉，第 [一] 组必须见红
 *
 * 跑法：node tools/sim_paper_docx.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");
const PAGE = path.join(ROOT, "public/search/index.html");
const html = fs.readFileSync(PAGE, "utf8");
const docxSrc = fs.readFileSync(path.join(ROOT, "public/assets/sde-docx.js"), "utf8");

let P = 0, FA = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (FA++, console.log("  FAIL " + m)); };

/* ---------- 抠取：原样取源码，不复制实现（复制的那份永远不会跟着改） ---------- */
function grab(names, src) {
  let out = "";
  for (const n of names) {
    const a = src.indexOf("function " + n + "(");
    if (a < 0) { console.log("FAIL 抠不出 " + n + "（改名了？先改本脚本）"); process.exit(1); }
    const b = src.indexOf("\nfunction ", a + 1);
    out += src.slice(a, b < 0 ? src.length : b) + "\n";
  }
  return out;
}
const CODE = grab(["loadDocx", "paperToMd", "docxName", "dlDocx", "mdSkip", "mdClean", "isPaperHead"], html);
ok(CODE.length > 1500, "抠出的源码非空（切片抠空了会让下面所有断言安静全绿）");

/* ---------- 环境：只给它真正用到的东西，缺什么当场就会炸出来 ---------- */
function mkEls() {
  const els = {};
  const el = (id) => els[id] || (els[id] = {
    id, textContent: "", disabled: false, _cls: [],
    classList: { add(c) { el(id)._cls.push("+" + c); }, remove(c) { el(id)._cls.push("-" + c); } }
  });
  return { els, el };
}
function loadSDEDocx() {
  const w = {};
  new Function("window", docxSrc)(w);
  if (!w.SDEDocx) { console.log("FAIL /assets/sde-docx.js 没挂上 window.SDEDocx"); process.exit(1); }
  return w.SDEDocx;
}
function build(code) {
  const F = new Function(
    "document", "window", "flashAsk", "paperAll", "polishAll", "paperMiss", "polishMiss",
    code + "\nreturn {loadDocx:loadDocx, paperToMd:paperToMd, docxName:docxName, dlDocx:dlDocx};"
  );
  return F;
}

/* 一份逼真的成文稿：带 Markdown 垃圾（模型偶尔会吐）、带 XML 危险字符、带各式标题 */
const PAPER = [
  "论「无号位过渡期」：中心位轮转中的空转比 & 其判据",
  "【摘要】本文提出一个此前无名的位置。",
  "---",
  "【Abstract】This paper proposes <a position> without a name.",
  "一、引言",
  "**制度轮转**的既有研究，多把交接看成一个点。",
  "| 象限 | 旧说 | 本文 |",
  "| :--- | :--- | :--- |",
  "| 一 | 点 | 段 |",
  "4.1 空转比的操作化",
  "把 t 记为 5 < x & y 的那一段。",
  "十、结论",
  "位置先于人。"
].join("\n");

console.log("— [一] paperToMd 真跑 —");
{
  const { el } = mkEls();
  const F = build(CODE)({ getElementById: el }, {}, () => {}, "", "", false, false);
  const md = F.paperToMd(PAPER, false, {});
  const L = md.split("\n");
  ok(L[0] === "# 论「无号位过渡期」：中心位轮转中的空转比 & 其判据", "首行 → 一级标题（# 题名）");
  ok(L[1].startsWith("> ") && /SDE UNIVERSES/.test(L[1]), "第二行是抬头行（署名/日期那一条走引用体）");
  ok(md.includes("\n## 【摘要】"), "【摘要】认作标题");
  ok(md.includes("\n## 一、引言"), "「一、引言」认作标题");
  ok(md.includes("\n## 4.1 空转比的操作化"), "4.1 式节标题认作标题");
  ok(md.includes("\n## 十、结论"), "「十、结论」认作标题");
  ok(!/\n-{3,}\n/.test(md), "--- 分隔线被丢弃（与 PDF 同一套兜底）");
  ok(!md.includes(":---"), "表格分隔行被丢弃");
  ok(md.includes("象限 ｜ 旧说 ｜ 本文"), "表格数据行归一成全角竖线一行");
  ok(md.includes("制度轮转的既有研究"), "**加粗**标记被剥掉，正文不丢");
  ok(!md.includes("未完成稿"), "完整稿不加红旗");

  /* 未完成稿这面旗必须跟到 Word 里：PDF 首页有、Word 没有，等于给断稿发了张干净封面 */
  const md2 = F.paperToMd(PAPER, "缺第四、第五段。", {});
  ok(/^> ⚠ 未完成稿 · 缺第四、第五段。/m.test(md2), "未完成稿红旗跟进 Word（不只印在 PDF 首页）");
  ok(F.paperToMd("", false, {}).split("\n")[0] === "# 成文一篇", "空稿不炸，退回默认题名");
  const md3 = F.paperToMd(PAPER, false, { eyebrow: "SDE UNIVERSES · 智能问对 · 打磨修改稿" });
  ok(md3.includes("打磨修改稿"), "打磨稿走自己的抬头（不冒充成文稿）");
}

console.log("— [二] 端到端真造一份 docx —");
let DOCXML = "";
(async function () {
  const { el } = mkEls();
  const SDEDocx = loadSDEDocx();
  const F = build(CODE)({ getElementById: el }, { SDEDocx }, () => {}, "", "", false, false);
  const blob = SDEDocx.build({ md: F.paperToMd(PAPER, "缺第五段。", {}), author: "SDE UNIVERSES" });
  const u8 = new Uint8Array(await blob.arrayBuffer());
  const buf = Buffer.from(u8);
  ok(buf[0] === 0x50 && buf[1] === 0x4b, "造出来的是真 zip（首字节 PK ⇒ Word 与 python zipfile 都开得了）");
  const s = buf.toString("utf8");
  DOCXML = s.slice(s.indexOf("<w:document"), s.indexOf("</w:document>"));
  ok(DOCXML.length > 500, "包里取得出 word/document.xml 正文");
  ok(DOCXML.includes("空转比 &amp; 其判据"), "& 已转义（不转义 Word 会判文档损坏，且是静默的）");
  ok(DOCXML.includes("&lt;a position&gt;"), "< > 已转义");
  ok(!/[\u0000-\u0008]/.test(DOCXML), "无控制字符");
  ok(DOCXML.includes("未完成稿"), "红旗真进了 document.xml，不只是留在 md 里");
  const iTitle = DOCXML.indexOf("无号位过渡期"), iAuthor = DOCXML.indexOf("SDE UNIVERSES");
  ok(iTitle > 0 && iAuthor > iTitle, "署名排在题名之后（塞到最前会让作者名跑到题目前面）");
  ok((DOCXML.match(/<w:p>/g) || []).length >= 10, "段落数合理（≥10 段，不是只造了个壳）");
  ok(blob.size > 1200, "体量像一份稿子（" + blob.size + " 字节）");

  /* ---------- [三] 从「点按钮」那一层真跑 ---------- */
  console.log("— [三] dlDocx 接线真跑 —");
  const { el: el2, els } = mkEls();
  let saved = null;
  const SD2 = loadSDEDocx();
  const realSave = SD2.save;
  SD2.save = (b, n) => { saved = { b, n }; };            // 只截住落盘那一步，其余全真跑
  ok(typeof realSave === "function", "SDEDocx.save 确实存在（截的是真方法，不是打空气）");
  const G = build(CODE)({ getElementById: el2 }, { SDEDocx: SD2 }, () => { els.flash = 1; },
    PAPER, "打磨稿正文：位置先于人，且第二轮由谁开始是可算的。".repeat(4), "缺第五段。", false);
  await G.dlDocx("paper");
  ok(saved && /^SDE-paper-\d{4}-\d{2}-\d{2}\.docx$/.test(saved.n), "成文导出的文件名 SDE-paper-日期.docx");
  ok(saved && saved.b.size > 1200, "成文导出的 blob 有体量");
  ok(/✅ Word 已导出/.test(el2("paperStat").textContent), "成文状态行报导出成功与字数");
  saved = null;
  await G.dlDocx("polish");
  ok(saved && /^SDE-polished-\d{4}-\d{2}-\d{2}\.docx$/.test(saved.n), "打磨导出的文件名带 polished（两份不会互相覆盖）");
  ok(/✅ Word 已导出/.test(el2("polishStat").textContent), "打磨状态行单独报，不写到成文那一栏");
  ok(el2("docxDl")._cls.join(",").indexOf("+") === -1, "按钮用的是 disabled 而不是 class 开关（防重复点）");

  /* 空正文：不许静默出一份空 Word */
  saved = null;
  const H = build(CODE)({ getElementById: el2 }, { SDEDocx: SD2 }, () => { els.flash = (els.flash || 0) + 1; }, "", "", false, false);
  await H.dlDocx("paper");
  ok(saved === null && els.flash >= 1, "没有正文时不造文件，只提示（不交空稿）");

  /* 造出来是空壳：交付层必须当场拦下，不许静默成功（与 PDF 那道墨量闸同一条规矩） */
  saved = null;
  let threw = "";
  const SD3 = { build: () => new Blob(["x"]), save: (b, n) => { saved = { b, n }; } };
  const K = build(CODE)({ getElementById: el2 }, { SDEDocx: SD3 }, () => {}, PAPER, "", false, false);
  await K.dlDocx("paper").catch(e => { threw = e.message || String(e); });
  ok(saved === null, "造出来是空壳时不落盘");
  ok(/空的/.test(threw), "空壳当场抛错并报字节数：" + threw.slice(0, 40));
  ok(/✗/.test(el2("paperStat").textContent), "失败写进状态行（不是只在控制台）");

  /* ---------- [四] 源码契约 ---------- */
  console.log("— [四] 源码契约 —");
  const iShow = html.indexOf("document.getElementById('wordActs').classList.add('show')");
  const iPdf = html.indexOf("return buildPdf(paperAll, miss)");
  ok(iShow > 0 && iPdf > 0 && iShow < iPdf,
    "★ Word 入口在 buildPdf **之前**亮灯 —— PDF 白页/超限/引擎失败都不连坐（这条是本文件的命根子）");
  const iShow2 = html.indexOf("document.getElementById('wordActs2').classList.add('show')");
  const iPdf2 = html.indexOf("return buildPdf(polishAll, miss");
  ok(iShow2 > 0 && iPdf2 > 0 && iShow2 < iPdf2, "打磨那一侧同理");
  ok(/id="wordActs"[\s\S]{0,400}?dlDocx\('paper'\)/.test(html), "成文区有独立的 Word 行 #wordActs");
  ok(/id="wordActs2"[\s\S]{0,400}?dlDocx\('polish'\)/.test(html), "打磨区有独立的 Word 行 #wordActs2");
  ok(!/id="pdfActs"[\s\S]{0,300}?dlDocx/.test(html), "Word 按钮不寄生在 pdfActs 里（寄生就等于跟着 PDF 一起不出现）");
  ok(/paperAll=r\.text; miss=missText\(r\.done\); paperMiss=miss;/.test(html), "成文落稿时留住 miss（Word 是随后另一次点击才造的）");
  ok(/polishAll=r\.text; miss=missText\(r\.done\); polishMiss=miss;/.test(html), "打磨落稿时同样留住");
  ok(/paperAll=''; paperMiss=false;/.test(html), "重开一篇时把上一篇的 miss 清掉（否则新完整稿会被扣上未完成帽子）");

  /* 戳必须与账本一致：手写一个新戳＝把读者分成两批各跑各的版本（见 tools/sim_asset_stamps.js） */
  const ledger = fs.readFileSync(path.join(ROOT, "tools/asset-stamps.tsv"), "utf8")
    .split("\n").map(l => l.split("\t")).find(p => p[0] === "/assets/sde-docx.js");
  const used = [...html.matchAll(/\/assets\/sde-docx\.js\?v=([\w.-]+)/g)].map(m => m[1]);
  ok(!!ledger, "账本里有 /assets/sde-docx.js");
  ok(used.length >= 1, "页面确实引了 /assets/sde-docx.js");
  ok(ledger && used.every(v => v === ledger[1]),
    "页面用的戳＝账本当前戳（账本 " + (ledger && ledger[1]) + "，页面 " + [...new Set(used)].join("/") + "）");
  ok(!/function\s+(esc|crc32|zip)\s*\(/.test(CODE), "页面里没有另写一份 docx 实现（只借 /assets/sde-docx.js 那一份）");
  ok(/mdSkip\(raw\)/.test(CODE) && /mdClean\(raw\)/.test(CODE) && /isPaperHead\(raw,L\)/.test(CODE),
    "paperToMd 与 buildPdf 共用同三个兜底函数（各认一套标题＝同一份稿子两种目录）");
  ok((html.match(/function docxName\(/g) || []).length === 1, "文件名只有一处定义");

  /* ---------- [五] 变异检验：拆掉标题分支，[一] 组必须见红 ---------- */
  console.log("— [五] 变异检验 —");
  const mut = CODE.replace("isPaperHead(raw,L) ? ('## '+L)", "false ? ('## '+L)");
  ok(mut !== CODE, "变异体确实改到了（改不到说明判据在测一个不存在的形状）");
  const M = build(mut)({ getElementById: mkEls().el }, {}, () => {}, "", "", false, false);
  const mmd = M.paperToMd(PAPER, false, {});
  ok(!mmd.includes("\n## 一、引言"), "拆掉标题分支后 [一] 组的标题断言会红（判据没在空转）");

  console.log("\n" + (FA ? "✗ " : "✓ ") + P + " PASS / " + FA + " FAIL");
  process.exit(FA ? 1 : 0);
})().catch(e => { console.log("✗ 脚本自身炸了：" + (e && e.stack || e)); process.exit(1); });
