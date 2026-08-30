/* sim_chatsde_book.js —— 「装成一本书」的护栏（2026-08-30）
 *
 * 装书＝把成文记录里的 N 份成品装成一本：扉页 · 目录 · 各编各章 · 附录 · 页码，出 Word，零调用。
 * 三件分开验：① bookAssemble（N 份 md → 书稿 md）真跑；② bookDocxBlob（书稿 md → docx）真跑并拆开 zip 逐件查；
 * ③ 接线：档位表 / 成文菜单（含空对话短菜单）/ 成文面板 Word 钮 / 面板四条出口 / 说明页。
 * 跑法：node tools/sim_chatsde_book.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");
let pass = 0, fail = 0;
const ok = (n, c, x) => { if (c) { pass++; console.log("  ✓ " + n); } else { fail++; console.log("  ✗ " + n + (x ? ("　← " + x) : "")); } };
const FSRC = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");
const DSRC = fs.readFileSync(path.join(ROOT, "public/assets/sde-docx.js"), "utf8");

/* ═══ 〇、把四件纯函数抠出来 ═══
   起点锚：模块头上那行注释；终点锚：bookPanel 的定义行（面板要 DOM，不抠）。 */
const a0 = FSRC.indexOf("  var BOOK_NUM = [");
const b0 = FSRC.indexOf("  function bookPanel() {", a0);
const PURE = (a0 > 0 && b0 > a0) ? FSRC.slice(a0, b0) : "";
ok("抠得到 bookStripNum / bookPieceMd / bookAssemble / bookDocxBlob",
  ["function bookStripNum(", "function bookPieceMd(", "function bookAssemble(", "function bookDocxBlob("].every((s) => PURE.indexOf(s) > 0));
// SDEDocx 真模块（toParas / esc / zip 都从它来）
const win = {};
new Function("window", "TextEncoder", "Blob", DSRC)(win, TextEncoder, Blob);
ok("SDEDocx 装得上且导出了 toParas / esc / zip", !!(win.SDEDocx && win.SDEDocx.toParas && win.SDEDocx.esc && win.SDEDocx.zip));
const M = {};
new Function("window", "TextEncoder", "Blob", "firstTitleOf", "__m",
  PURE + "\n__m.bookStripNum=bookStripNum;__m.bookPieceMd=bookPieceMd;__m.bookAssemble=bookAssemble;__m.bookDocxBlob=bookDocxBlob;__m.BOOK_STRIP_RE=BOOK_STRIP_RE;")(
  win, TextEncoder, Blob, (md) => { const m = /^\s*#\s+(.+)$/m.exec(String(md || "")); return m ? m[1].trim().slice(0, 60) : ""; }, M);

/* ═══ 一、去序号 ═══ */
console.log("── 一、章名去序号 ──");
[["一、引言：研究问题", "引言：研究问题"], ["3.2 判据", "判据"], ["第二章 老路", "老路"], ["（三）分界", "分界"], ["3、赌注", "赌注"],
 ["十一、讨论", "讨论"], ["1) 起点", "起点"], ["二", "二"], ["参考文献", "参考文献"]].forEach(([i, o]) => {
  ok("「" + i + "」→「" + o + "」", M.bookStripNum(i) === o, "实得「" + M.bookStripNum(i) + "」");
});

/* ═══ 二、装配真跑 ═══ */
console.log("── 二、bookAssemble ──");
const P1 = "# 老路已被包办\n\n## 摘要与关键词\n\n【摘要】这是摘要。\n\n【关键词】A；B\n\n## 一、引言：研究问题\n\n引言正文 & 带一个符号。\n\n### 1.1 缘起\n\n缘起正文。\n\n## 二、文献述评\n\n述评正文。\n\n## 十四、注释与声明组\n\n声明。\n\n## 参考文献\n\n王德生（2026）。\n";
const P2 = "# 加速的发现式教育\n\n第一段没有小标题。\n\n## 一、核心命题\n\n命题正文。\n\n# 篇内又一个一级标题\n\n它该降成章。\n";
const F1 = "# 前言\n\n## 为什么写这本书\n\n前言正文。\n";
const A1 = "# 五十章承重判断一览\n\n- 第一条\n- 第二条\n";
const meta = { title: "老路已被包办", sub: "AI 之后，教育还剩下哪一段", author: "王德生", pub: "Demai International Press", date: "2026-08-30" };
const items = [{ name: "老路", role: "part", md: P1 }, { name: "前言", role: "front", md: F1 }, { name: "附录一", role: "appendix", md: A1 }, { name: "新路", role: "part", md: P2 }];
const R = M.bookAssemble(meta, items, { renum: true, strip: true, chBreak: true });
const md = R.md;
ok("扉页：第一行是书名", /^# 老路已被包办\n/.test(md));
ok("扉页：副题、著者、出版行各占一行引用", /> AI 之后，教育还剩下哪一段\n\n> 王德生\n\n> Demai International Press\n/.test(md));
ok("扉页末行带装书日期与编数", /> 2026-08-30 · 装书 · 2 编/.test(md));
ok("目录节在正文之前", md.indexOf("# 目录") > 0 && md.indexOf("# 目录") < md.indexOf("# 前言"));
ok("次序：前置件 → 第一编 → 第二编 → 附录", (() => { const i = ["# 前言", "# 第一编　老路", "# 第二编　新路", "# 附录一　附录一"].map((s) => md.indexOf(s)); return i.every((x) => x > 0) && i[0] < i[1] && i[1] < i[2] && i[2] < i[3]; })());
ok("章连续编号跨编不重来（第1章…第4章）", /## 第1章　引言：研究问题/.test(md) && /## 第2章　文献述评/.test(md) && /## 第3章　核心命题/.test(md) && /## 第4章　篇内又一个一级标题/.test(md));
ok("篇首标题只用来当编名，正文里不再出现「# 老路已被包办」第二次", md.split("老路已被包办").length === 2);
ok("摘要／关键词整节拿掉（到下一个 ## 为止）", md.indexOf("这是摘要") < 0 && md.indexOf("【关键词】") < 0);
ok("声明组整节拿掉", md.indexOf("声明。") < 0);
ok("参考文献保留且不编号", /## 参考文献\n/.test(md) && !/章　参考文献/.test(md));
ok("三级标题跟着走", /### 1.1 缘起/.test(md));
ok("前置件的 ## 不编号", /## 为什么写这本书/.test(md) && !/章　为什么写这本书/.test(md));
ok("读数：2 编 · 4 章 · 1 前置 · 1 附录", R.stats.parts === 2 && R.stats.chapters === 4 && R.stats.fronts === 1 && R.stats.appendices === 1, JSON.stringify(R.stats));
ok("读数：汉字数只数正文（不含扉页与目录）", R.stats.han > 40 && R.stats.han < 200, String(R.stats.han));
ok("目录条目按一二级列出且含第二编", R.toc.some((x) => x.lvl === 1 && /第二编/.test(x.t)) && R.toc.some((x) => x.lvl === 2 && /第3章/.test(x.t)));
// 两个开关反着跑：不是变异测试，是证明开关真接着
const R2 = M.bookAssemble(meta, items, { renum: false, strip: false, chBreak: true });
ok("关掉编号：章名保留原序号", /## 一、引言：研究问题/.test(R2.md) && !/第1章/.test(R2.md));
ok("关掉去摘要：摘要留在书里", R2.md.indexOf("这是摘要") > 0);
ok("没有 name 的一编退回篇首标题", /# 第一编　加速的发现式教育/.test(M.bookAssemble({ title: "x" }, [{ role: "part", md: P2 }], {}).md));
ok("空稿子被跳过，不算一编", M.bookAssemble({ title: "x" }, [{ role: "part", md: "   " }, { role: "part", md: P2 }], {}).stats.parts === 1);

/* ═══ 三、docx 真造 ＋ 拆 zip 逐件查 ═══ */
console.log("── 三、bookDocxBlob ──");
const blob = M.bookDocxBlob(md, { chBreak: true });
ok("造得出 Blob", !!blob && typeof blob.arrayBuffer === "function");
function unzipStored(u8) {   // 只认 stored（SDEDocx.zip 只写 stored）
  const out = {}; let p = 0;
  const u16 = (i) => u8[i] | (u8[i + 1] << 8), u32 = (i) => (u8[i] | (u8[i + 1] << 8) | (u8[i + 2] << 16) | (u8[i + 3] << 24)) >>> 0;
  while (p + 30 <= u8.length && u32(p) === 0x04034b50) {
    const clen = u32(p + 18), nlen = u16(p + 26), xlen = u16(p + 28);
    const name = Buffer.from(u8.slice(p + 30, p + 30 + nlen)).toString("utf8");
    out[name] = Buffer.from(u8.slice(p + 30 + nlen + xlen, p + 30 + nlen + xlen + clen)).toString("utf8");
    p += 30 + nlen + xlen + clen;
  }
  return out;
}
(async () => {
  const u8 = new Uint8Array(await blob.arrayBuffer());
  const Z = unzipStored(u8);
  const need = ["[Content_Types].xml", "_rels/.rels", "word/_rels/document.xml.rels", "word/document.xml", "word/styles.xml", "word/settings.xml", "word/footer1.xml"];
  ok("七件都在 zip 里：" + need.length, need.every((n) => typeof Z[n] === "string" && Z[n].length > 0), Object.keys(Z).join(","));
  const doc = Z["word/document.xml"] || "", sty = Z["word/styles.xml"] || "", set = Z["word/settings.xml"] || "", ftr = Z["word/footer1.xml"] || "", ct = Z["[Content_Types].xml"] || "", dr = Z["word/_rels/document.xml.rels"] || "";
  const bal = (s, tag) => (s.match(new RegExp("<" + tag + "[ >]", "g")) || []).length === (s.match(new RegExp("</" + tag + ">", "g")) || []).length;
  ok("document.xml 标签配平（p / r / pPr / sectPr）", ["w:p", "w:r", "w:pPr", "w:sectPr"].every((tg) => bal(doc, tg)));
  ok("正文里没有未转义的 & / < （那一个 & 变成了 &amp;）", !/&(?!amp;|lt;|gt;|quot;|apos;|#)/.test(doc) && doc.indexOf("&amp; 带一个符号") > 0);
  ok("目录域在：TOC \\o \"1-2\" \\h \\z \\u，且标 dirty 让 Word 开文件就问要不要更新", /<w:instrText xml:space="preserve"> TOC \\o "1-2" \\h \\z \\u <\/w:instrText>/.test(doc) && /fldCharType="begin" w:dirty="true"/.test(doc));
  ok("目录域预填了不带页码的条目（不更新域也看得到章节清单）", /w:pStyle w:val="TOC1"/.test(doc) && /w:pStyle w:val="TOC2"/.test(doc) && doc.indexOf("第二编　新路") > 0);
  ok("目录域首尾成对（一个 begin、一个 separate、一个 end）", (doc.match(/TOC \\o/g) || []).length === 1 && (doc.match(/fldCharType="separate"/g) || []).length === 1 && (doc.match(/fldCharType="end"/g) || []).length === 1);
  ok("两节：扉页＋目录 罗马页码；正文另起一节从 1 起", /<w:type w:val="nextPage"\/>/.test(doc) && /<w:pgNumType w:fmt="lowerRoman"\/>/.test(doc) && /<w:pgNumType w:start="1" w:fmt="decimal"\/>/.test(doc) && (doc.match(/<w:sectPr>/g) || []).length === 2);
  ok("两节都挂着页码页脚（footerReference r:id=rId3）", (doc.match(/<w:footerReference w:type="default" r:id="rId3"\/>/g) || []).length === 2);
  ok("编 → Heading1，章 → Heading2，节 → Heading3（按样式，不是按字号）", (doc.match(/w:pStyle w:val="Heading1"/g) || []).length === 4 && (doc.match(/w:pStyle w:val="Heading2"/g) || []).length >= 6 && /w:pStyle w:val="Heading3"/.test(doc));
  ok("每编另起页，第一个编除外（它已在新节的第一页）；每章另起页", (() => {
    const h1 = doc.split(/<w:p><w:pPr><w:pStyle w:val="Heading1"\/>/).slice(1);
    const brk1 = h1.filter((s) => /^<w:keepNext\/><w:pageBreakBefore\/>/.test(s)).length;
    const h2 = doc.split(/<w:p><w:pPr><w:pStyle w:val="Heading2"\/>/).slice(1);
    const brk2 = h2.filter((s) => /^<w:keepNext\/><w:pageBreakBefore\/>/.test(s)).length;
    // 前置件那一章不另起页、附录里没有章；两编里五个 ##（引言／述评／参考文献／核心命题／降下来的那个）各一次
    return h1.length === 4 && brk1 === 3 && brk2 === 5;
  })(), "实得 " + JSON.stringify({ h1: (doc.match(/w:pStyle w:val="Heading1"/g) || []).length, brk: (doc.match(/<w:pageBreakBefore\/>/g) || []).length }));
  ok("样式表：Heading1/2/3 带 outlineLvl 0/1/2（目录域靠它认层级）", /styleId="Heading1"[\s\S]*?outlineLvl w:val="0"/.test(sty) && /styleId="Heading2"[\s\S]*?outlineLvl w:val="1"/.test(sty) && /styleId="Heading3"[\s\S]*?outlineLvl w:val="2"/.test(sty));
  ok("样式表：目录标题自己不进目录（outlineLvl 9）", /styleId="TOCHeading"[\s\S]*?outlineLvl w:val="9"/.test(sty));
  ok("样式表：toc 1 / toc 2 带右对齐点线制表位", (sty.match(/w:leader="dot" w:pos="9070"/g) || []).length === 2);
  ok("样式表：中文默认宋体、英文 Times New Roman", /w:eastAsia="宋体"/.test(sty) && /w:ascii="Times New Roman"/.test(sty));
  ok("settings：updateFields 开着（Word 打开时问要不要更新域）", /<w:updateFields w:val="true"\/>/.test(set));
  ok("页脚：PAGE 域居中", /<w:instrText xml:space="preserve"> PAGE <\/w:instrText>/.test(ftr) && /<w:jc w:val="center"\/>/.test(ftr));
  ok("Content_Types 四个 Override（document / styles / settings / footer1）", ["document.main", "styles+xml", "settings+xml", "footer+xml"].every((s) => ct.indexOf(s) > 0));
  ok("document.xml.rels 三条关系与 rId 对得上", /Id="rId1"[^>]*styles/.test(dr) && /Id="rId2"[^>]*settings/.test(dr) && /Id="rId3"[^>]*footer/.test(dr) && /Target="footer1.xml"/.test(dr));
  ok("扉页四行都在（书名走 Title 样式，副题／著者／出版行居中）", /w:pStyle w:val="Title"/.test(doc) && doc.indexOf("AI 之后，教育还剩下哪一段") > 0 && doc.indexOf("Demai International Press") > 0);
  ok("扉页之后正文里不再出现目录的 md 列表行", doc.indexOf("· 第一编　老路") < 0);
  // 没有目录节的稿子也造得出（从成文记录取回一份手写 md 时）
  const b2 = M.bookDocxBlob("# 只有标题\n\n正文一段。\n", null);
  const Z2 = unzipStored(new Uint8Array(await b2.arrayBuffer()));
  ok("无目录节的稿子照样成书（不插目录域、仍两节）", !/TOC \\o/.test(Z2["word/document.xml"]) && (Z2["word/document.xml"].match(/<w:sectPr>/g) || []).length === 2);
  const Z3 = unzipStored(new Uint8Array(await M.bookDocxBlob(md, null).arrayBuffer()));
  // 目录标题 1 ＋ 三个非首编 3 ＋ 五个章 5 ＝ 9 处分页
  ok("opts 缺省（成文面板取回那条路传 null）按每章另起页处理（9 处分页）", (Z3["word/document.xml"].match(/<w:pageBreakBefore\/>/g) || []).length === 9, String((Z3["word/document.xml"].match(/<w:pageBreakBefore\/>/g) || []).length));
  const Z4 = unzipStored(new Uint8Array(await M.bookDocxBlob(md, { chBreak: false }).arrayBuffer()));
  ok("关掉「每章另起页」：只剩目录与非首编的 4 处分页", (Z4["word/document.xml"].match(/<w:pageBreakBefore\/>/g) || []).length === 4);

  /* ═══ 四、接线 ═══ */
  console.log("── 四、接线 ──");
  const kd = (FSRC.match(/var KIND_DEF = \[([\s\S]*?)\n  \];/) || ["", ""])[1];
  ok("档位表有 book，出 Word，且不是隐藏档（要摆在菜单上）", /\{ k: "book", t: "kBook", doc: 1 \}/.test(kd) && !/k: "book"[^}]*hid/.test(kd));
  ok("book 不挂字数闸也不拆趟（它不进 distill）", !/k: "book"[^}]*\bw:/.test(kd) && !/k: "book"[^}]*\bc: 1/.test(kd));
  ok("kBook 的档名不含「 · 」（成文记录按「 · 」分段反查档名，含了就认不回来）", /kBook: "装成一本书"/.test(FSRC) && /kBook: "Bind into a book"/.test(FSRC));
  ok("菜单点 book 开挑稿面板，不进 distill（排在 deck 那一支之前）", /if \(k === "book"\) \{ bookPanel\(\); return; \}[\s\S]{0,120}if \(k === "deck"\) \{ tplMenu\(\); return; \}/.test(FSRC));
  ok("book 也带 NEW 标（与 deck 同一句）", /if \(k === "deck" \|\| k === "book"\) \{ var nb = el\("i", "wdsm-new", "NEW"\)/.test(FSRC));
  ok("空对话不再 alert：改成短菜单，头一行仍是那句「先聊两句」", !/alert\(t\("needTalkDeck"\)\)/.test(FSRC) && /if \(!_talked\) menu\.appendChild\(el\("div", "mh", t\("needTalkDeck"\)\)\)/.test(FSRC));
  ok("空对话的菜单只摆 book 一档（其余档都要对话）", /if \(!_talked && k !== "book"\) return;/.test(FSRC));
  ok("空对话不摆「导出本场对话」（没东西可导）", /if \(!_talked\) dl\.style\.display = "none";/.test(FSRC));
  ok("成文面板的 Word 钮：book 档走 bookDocxBlob，其余照旧 SDEDocx.build", /var blob = \(kind === "book"\) \? bookDocxBlob\(text, null\) : window\.SDEDocx\.build\(\{ title: firstTitleOf\(text\)/.test(FSRC) && /verse: !!\(_kd && _kd\.verse\) \}\);\n\s*if \(!blob\) \{ stat\.textContent = t\("dPptxWait"\); return; \}/.test(FSRC));
  const pa = FSRC.indexOf("  function bookPanel() {"), pb = FSRC.indexOf("  // 成文面板。第三个参数给「成文记录」复用", pa);
  const PAN = pa > 0 && pb > pa ? FSRC.slice(pa, pb) : "";
  ok("面板沿用 .wdsm-dist 遮罩并挂 wrap._close（全局 Esc 认它）", /el\("div", "wdsm-dist"\)/.test(PAN) && /wrap\._close = close;/.test(PAN));
  ok("面板四条出口：顶栏 ✕ 与角落逃生钮都带 dx，靠 wrap 上的委托关；点遮罩空白处也关", /class='wdsm-dist-esc dx'/.test(PAN) && /tg\.closest\("\.dx"\)\) \{ close\(\); return; \}/.test(PAN) && /if \(tg === wrap\) close\(\);/.test(PAN));
  ok("面板读的是成文记录那个 agent（AGENT_DIST），先 list 再逐条 get", /A\.list\(AGENT_DIST\)/.test(PAN) && /A\.get\(m\.id\)/.test(PAN));
  ok("装好的书再进来默认不勾（免得书里套书）", /isBook/.test(PAN) && /kindT\("book"\)/.test(PAN));
  ok("存回成文记录走 distSave(distLabel(\"book\", …))，取回时才认得出是 book", /distSave\(distLabel\("book", "", r\.md\), r\.md/.test(PAN));
  ok("出 Word 走 bookDocxBlob(r.md, opts)，出 .md 走 saveToDir，文件名带书名与时间戳", /bookDocxBlob\(r\.md, opts\)/.test(PAN) && /saveToDir\(fileTag\("WDS"\) \+ "-" \+ safeName\(inT\.value\) \+ "-" \+ stampName\(\) \+ "\.md"/.test(PAN));
  ok("没起书名不许出稿（先定名）", /if \(!String\(inT\.value \|\| ""\)\.trim\(\)\) \{ stat\.textContent = t\("bkNoTitle"\)/.test(PAN));
  ok("面板不打 /api/wds/（零调用）", !/\/api\/wds\//.test(PAN) && !/fetch\(/.test(PAN.replace(/sc\.src = "\/assets\/wds-store\.js"/, "")));
  const DOC = fs.readFileSync(path.join(ROOT, "public/banyu/chatsde/index.html"), "utf8");
  ok("说明页写到了「装成一本书」", DOC.indexOf("装成一本书") > 0);

  console.log("\n" + (fail ? "✗ " : "✓ ") + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
})();
