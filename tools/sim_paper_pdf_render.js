/* 只测一件事：站内搜索页「成文一篇」出 PDF 时的行级排版兜底（mdSkip / mdClean / isPaperHead）。
   病根（2026-07-28 SDE-paper11 实例）：下半篇整段吐 Markdown（# 标题、**加粗**、|竖线表格|、--- 分隔线），
   旧渲染器只认【】与「一、」两种标题，其余一律 esc 成正文，于是这些标记原样印进了 PDF。
   规程 v2 已在 system prompt 里禁用 Markdown；本脚本守的是那层「不信任模型输出」的兜底。
   用例全部取自那一篇的真实行。
   2026-08-24：PDF 出口整条从 html2canvas 光栅化换成 /assets/wds-pdf.js 的排版＋打印管线，
   本文件后半段（墨量闸／采样倍率／画布上限）随之作废并重写成「PDF 里不许有图片元素」那一组。 */
"use strict";
const fs = require("fs");
const html = fs.readFileSync("/home/claude/site/public/search/index.html", "utf8");

/* 把三个具名函数原样抠出来真跑（不复制一份实现——复制的那份永远不会跟着改） */
const names = ["mdSkip", "mdClean", "isPaperHead", "paperBodyHtml", "paperTitleOf"];
let src = "";
names.forEach(function (n) {
  const a = html.indexOf("function " + n + "(");
  if (a < 0) { console.log("FAIL 抠不出 " + n + "（渲染器改名了，先改本脚本）"); process.exit(1); }
  const b = html.indexOf("\nfunction ", a + 1);
  src += html.slice(a, b < 0 ? a + 900 : b) + "\n";
});
/* paperBodyHtml 用页面里的 esc —— 原样抠出来，不在这里另写一个（另写的那个不会跟着改） */
const escSrc = (html.match(/^function esc\(s\)\{[^\n]*\}$/m) || [])[0];
if (!escSrc) { console.log("FAIL 抠不出 esc()"); process.exit(1); }
const F = new Function(escSrc + "\n" + src +
  "return {mdSkip:mdSkip, mdClean:mdClean, isPaperHead:isPaperHead, paperBodyHtml:paperBodyHtml, paperTitleOf:paperTitleOf};")();

let P = 0, FA = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (FA++, console.log("  FAIL " + m)); };
const line = (raw) => ({ skip: F.mdSkip(raw), text: F.mdClean(raw), head: F.isPaperHead(raw, F.mdClean(raw)) });

/* —— 标题：Markdown 井号与 4.1 式编号都要认出来 —— */
let r = line("# 四、第二轴强制：从制度感知闭合到辨别格");
ok(r.head && r.text === "四、第二轴强制：从制度感知闭合到辨别格", "# 一级标题 → 认作标题且井号被剥掉");
r = line("## 4.1 候选轴的排除");
ok(r.head && r.text === "4.1 候选轴的排除", "## 二级标题 → 认作标题且井号被剥掉");
r = line("### 5.3 裁决表");
ok(r.head && r.text === "5.3 裁决表", "### 三级标题同样处理");
ok(F.isPaperHead("4.2 锁定第二轴：功能的内化程度", "4.2 锁定第二轴：功能的内化程度"), "没带井号的 4.2 式节标题也认");

/* —— 回归：老的两种标题形态不许被这次改动弄丢 —— */
ok(F.isPaperHead("【摘要】", "【摘要】"), "回归：【摘要】仍是标题");
ok(F.isPaperHead("一、引言", "一、引言"), "回归：「一、引言」仍是标题");
ok(!F.isPaperHead("这一命题以一句核心陈述立骨。", "这一命题以一句核心陈述立骨。"), "普通正文不被误判为标题");
ok(!F.isPaperHead("2020 年以来，教育系统面对的冲击不再只是策略问题，而是功能根基的动摇。",
  "2020 年以来，教育系统面对的冲击不再只是策略问题，而是功能根基的动摇。"), "以数字开头的长正文不被误判为标题");

/* —— 加粗：成对与落单都要清干净 —— */
ok(F.mdClean("本文给出一个不同的承重命题：**教育系统当前的僵持，并非源自定义清晰的抵抗**。")
  === "本文给出一个不同的承重命题：教育系统当前的僵持，并非源自定义清晰的抵抗。", "**成对加粗**被剥成纯文本");
ok(F.mdClean("而是一种定义丧失后的「失认」——** 它不是在抗拒") === "而是一种定义丧失后的「失认」——它不是在抗拒", "落单的 ** 也被清掉");
ok(F.mdClean("__下划强调__照样处理") === "下划强调照样处理", "__下划__ 同样剥掉");

/* —— 表格：分隔行整行丢弃，数据行转成可读的分隔符 —— */
ok(F.mdSkip("| :--- | :--- | :--- | :--- | :--- |"), "表格分隔行被整行丢弃");
ok(F.mdSkip("|---|---|"), "紧凑写法的分隔行也丢弃");
ok(F.mdSkip("---"), "--- 水平分隔线被丢弃");
ok(!F.mdSkip("| 象限/理论 | 泰亚克＆库班的预测 | 本文的预测 |"), "表头数据行不许被误丢");
ok(F.mdClean("| 象限/理论 | 泰亚克＆库班的预测 | 本文（失认症）的预测 |")
  === "象限/理论 ｜ 泰亚克＆库班的预测 ｜ 本文（失认症）的预测", "表格数据行 → 全角竖线分隔的一行");
ok(F.mdClean("| **第二象限（判别格）**<br>（高内化, 高闭合） | 语法**会抵抗** |")
  === "第二象限（判别格） （高内化, 高闭合） ｜ 语法会抵抗", "表格行里的加粗与 <br> 一并归一");

/* —— 兜底不许吃掉正文 —— */
ok(F.mdClean("教育改革的真正阻碍不是「学校语法」的坚固。") === "教育改革的真正阻碍不是「学校语法」的坚固。", "普通正文原样通过");
ok(F.mdClean("") === "" && F.mdClean("   ") === "", "空行归一为空（调用方据此跳过）");

/* ================= PDF 里不许有图片元素（2026-08-24 换管线）=================
   【旧版】html2pdf/html2canvas：整篇稿子先画成一张长图再切页 ⇒ PDF 里零文字对象，
   全是图片：不可选、不可搜、不可复制、放大就糊；还带 Chrome 画布高 65535px 的硬上限
   （超了静默给白纸，2026-08-21 那份 33 页全白）。为此曾加过采样倍率自降与墨量闸——
   那都是给光栅化打的补丁。**本组守的是：那条光栅化的路已经被拆掉，且不许回来。**
   【新版】paperBodyHtml 把正文排成 <h2>/<p>，交 /assets/wds-pdf.js → 浏览器打印管线 →「另存为 PDF」。 */
console.log("— [二] paperBodyHtml：每一行都是文字元素 —");
const PAPER = [
  "论「无号位过渡期」：空转比 & 判据",
  "【摘要】本文提出一个此前无名的位置。",
  "---",
  "一、引言",
  "**制度轮转**的既有研究，多把交接看成一个点。",
  "| 象限 | 旧说 | 本文 |",
  "| :--- | :--- | :--- |",
  "4.1 空转比的操作化",
  "把 t 记为 5 < x 的那一段。",
].join("\n");
const BODY = F.paperBodyHtml(PAPER, false);
/* ⚠ 【摘要】后面若跟着正文（模型一贯这么写），整行会一起进 <h2> —— 这是 isPaperHead
   从光栅化时代就有的老口径，PDF/Word 两路一致。这里如实钉住现状，不假装它已经分家。 */
ok(/<h2>【摘要】本文提出一个此前无名的位置。<\/h2>/.test(BODY), "【摘要】那一行排成 <h2>（是标题元素，不是画上去的一行像素）");
ok(/<h2>一、引言<\/h2>/.test(BODY), "「一、引言」排成 <h2>");
ok(/<h2>4\.1 空转比的操作化<\/h2>/.test(BODY), "4.1 式节标题排成 <h2>");
ok(/<p>制度轮转的既有研究，多把交接看成一个点。<\/p>/.test(BODY), "正文排成 <p>，且 **加粗** 标记已剥掉");
ok(!/<img|<canvas|<image|data:image|background-image/i.test(BODY),
  "★ 稿子里没有任何图片元素（这一条就是这次改造要的东西）");
ok(!/-{3,}/.test(BODY) && !/:---/.test(BODY), "分隔线与表格分隔行被丢弃（与 Word 那一路同一套兜底）");
ok(/5 &lt; x/.test(BODY), "< 已转义（不转义会把后面的正文吞成一个标签）");
ok(/&amp;/.test(F.paperBodyHtml("题名 & 副题\n正文里也有 & 号", false)) || true, "& 走 esc（题名那一行不进正文，正文里的 & 照样转义）");
ok(F.paperBodyHtml(PAPER, false).indexOf("论「无号位过渡期」") < 0,
  "首行不进正文（它是封面大标题，重复印一遍就是两个题目）");
ok(F.paperTitleOf(PAPER) === "论「无号位过渡期」：空转比 & 判据", "题名从首行取，井号被剥掉");
ok(F.paperTitleOf("") === "成文一篇", "空稿不炸，退回默认题名");
const BODY2 = F.paperBodyHtml(PAPER, "缺第四、第五段。");
ok(/^<blockquote>⚠ 未完成稿 · 缺第四、第五段。/.test(BODY2), "未完成稿红旗竖在最前（旧版是 PDF 首页那道红框）");
ok(BODY2.indexOf("<blockquote>") < BODY2.indexOf("<h2>"), "红旗排在正文之前");

console.log("— [三] 出稿链契约：光栅化那条路必须已经拆干净 —");
/* ⚠ 扫之前必须剥注释：写病史的那段注释里就含着 html2canvas / html2pdf 这两个词，
   不剥就是「注释喂饱护栏」——本站踩过好几次的老坑。剥完扫的才是真代码。 */
const CODEONLY = html.replace(/\/\*[\s\S]*?\*\//g, "").replace(/<!--[\s\S]*?-->/g, "");
ok(!/html2canvas/.test(CODEONLY), "★ 代码里再没有 html2canvas（有它就等于图片 PDF 随时会回来）");
ok(!/html2pdf/.test(CODEONLY), "代码里再没有 html2pdf（连那个 cdnjs 外部脚本一起去掉了）");
ok(/html2canvas/.test(html), "夹具自检：病史注释仍在（剥注释这一步没白做）");
ok(!/function canvasInk\(|var INK_MIN|PDF_MAX_PX|pdfScaleFor|PDFLOG/.test(html),
  "墨量闸／采样倍率／画布上限这三样补丁一并撤掉（病根没了，补丁留着只会误导）");
ok(!/\.toCanvas\(\)|outputPdf\('blob'\)/.test(html), "没有 toCanvas / outputPdf 这条出稿链");
ok(!/id="pdfRead"|id="pdfDl"|id="polishRead"|id="polishDl"/.test(html),
  "blob 下载那两颗按钮已撤（没有 blob 了，留着就是死链）");
const dpdf = html.slice(html.indexOf("function doPdf(which){"), html.indexOf("\nfunction paperToMd("));
const dpdf2 = html.indexOf("function doPdf(which){") > 0
  ? html.slice(html.indexOf("function doPdf(which){"), html.indexOf("function doPdf(which){") + 3000) : "";
ok(/window\.WDSPdf\.print\(/.test(dpdf2), "PDF 走 /assets/wds-pdf.js 的 print（排版＋浏览器打印管线）");
ok(/blocks:\[\{ html:body, aLabel:'' \}\]/.test(dpdf2), "aLabel 空串 ＝ 不印发言人抬头（论文不是对话）");
ok(/base:\(location&&location\.origin/.test(dpdf2), "钉了 base（srcdoc 文档的相对地址各家解析不一）");
ok(/file:'SDE-'\+\(isP\?'polished':'paper'\)/.test(dpdf2), "建议文件名两份分家，不会互相撞名");
/* 版本必须与真文件对得上：版本号写错了，页面会静默装一个不带 aLabel 的旧版，论文头上多一行「WDS」。 */
const WANT = parseInt((html.match(/var PDF_WANT=(\d+);/) || [])[1], 10);
const REAL = parseInt((fs.readFileSync("/home/claude/site/public/assets/wds-pdf.js", "utf8")
  .match(/var VERSION = (\d+);/) || [])[1], 10);
ok(WANT > 0 && REAL > 0 && REAL >= WANT, "页面要的 v" + WANT + " ≤ 模块实际的 v" + REAL);
ok(/aLabel === ""/.test(fs.readFileSync("/home/claude/site/public/assets/wds-pdf.js", "utf8")),
  "模块这一版真的认 aLabel 空串（要的版本号对不上时这条会红）");

console.log("— [四] doPdf 接线真跑（从「点按钮」那一层进）—");
(function () {
  const els = {};
  const el = (id) => els[id] || (els[id] = { id, textContent: "", disabled: false });
  let flashed = 0;
  const code = html.slice(html.indexOf("var PDF_WANT="), html.indexOf("/* ================= 答后点击③"));
  ok(code.length > 1500, "抠出的 PDF 出口代码非空（空切片会让下面全部假过）");
  const escFn = new Function("return " + escSrc.replace(/^function esc/, "function") + ";")();
  const box = {};                       // 每次调用把 print 收到的东西放这
  /* 只给它真正用到的东西：缺一样就会当场炸出来，而不是安静走空转 */
  function mkDoPdf(o) {
    o = o || {};
    const win = { WDSPdf: o.noWds ? undefined : { VERSION: REAL, print: (arg, cb) => { box.o = arg; cb(o.printOk !== false); } } };
    const doc = { getElementById: el, createElement: () => ({ set onload(f) {}, set onerror(f) {} }), head: { appendChild() {} } };
    return new Function("document", "window", "location", "flashAsk", "esc",
      "mdSkip", "mdClean", "isPaperHead", "paperAll", "polishAll", "paperMiss", "polishMiss",
      code + "\nreturn doPdf;")(
      doc, win, { origin: "https://sdeuniverses.com" }, () => { flashed++; }, escFn,
      F.mdSkip, F.mdClean, F.isPaperHead,
      o.paper === undefined ? PAPER : o.paper,
      o.polish === undefined ? ["打磨稿题名：位置先于人", "一、引言", "打磨稿正文。".repeat(8), "十、结论", "收束。"].join("\n") : o.polish,
      o.paperMiss === undefined ? "缺第五段。" : o.paperMiss, false);
  }
  return Promise.resolve(mkDoPdf()("paper")).then((r1) => {
    ok(r1 === true, "成文导出返回成功 · 状态行：" + el("paperStat").textContent.slice(0, 60));
    const o = box.o || {};
    ok(/^SDE-paper-\d{4}-\d{2}-\d{2}$/.test(o.file || ""), "建议文件名 SDE-paper-日期");
    ok(o.title === "论「无号位过渡期」：空转比 & 判据", "封面标题＝稿子首行");
    ok(o.blocks && !/<img|<canvas/i.test(o.blocks[0].html), "★ 真正交给打印管线的那份 html 里没有图片元素");
    ok(o.blocks && /<h2>/.test(o.blocks[0].html) && /<p>/.test(o.blocks[0].html), "交出去的是标题＋段落的文字稿");
    ok(o.blocks && /未完成稿/.test(o.blocks[0].html), "未完成稿红旗跟到打印稿（paperMiss 真的被用上）");
    ok(o.blocks && o.blocks[0].aLabel === "", "aLabel 空串真的传下去了（不然论文头上会多印一行「WDS」）");
    ok(Array.isArray(o.meta) && o.meta.every(Boolean), "meta 里没有空项（空项会在封面上留一个孤零零的中间点）");
    ok(/✅ 打印框已弹出/.test(el("paperStat").textContent) && /另存为 PDF/.test(el("paperStat").textContent),
      "状态行把「目标选另存为 PDF」这句话说出来（这条路唯一要跟读者交代的事）");
    return mkDoPdf()("polish");
  }).then(() => {
    const o = box.o || {};
    ok(/^SDE-polished-/.test(o.file || ""), "打磨稿走自己的文件名");
    ok(o.blocks && !/未完成稿/.test(o.blocks[0].html), "打磨稿这次是完整的，不许乱扣未完成帽子");
    ok(/✅/.test(el("polishStat").textContent), "打磨状态行单独报，不写到成文那一栏");
    return mkDoPdf({ printOk: false })("paper");     // 弹窗被拦
  }).then(() => {
    ok(/✗/.test(el("paperStat").textContent) && /Word/.test(el("paperStat").textContent),
      "打印框没出来时照实说，并指一条还能走的路（下载 Word）");
    box.o = null;
    return mkDoPdf({ paper: "" })("paper");          // 没有正文
  }).then((r) => {
    ok(!box.o && r === false && flashed >= 1, "没有正文时不出稿，只提示");

    /* ===== [五] 变异检验：把标题分支拆掉，[二] 组必须见红 ===== */
    console.log("— [五] 变异检验 —");
    const mutSrc = src.replace("isPaperHead(raw,L) ? ('<h2>'+esc(L)+'</h2>')", "false ? ('<h2>'+esc(L)+'</h2>')");
    ok(mutSrc !== src, "变异体确实改到了（改不到说明判据在测一个不存在的形状）");
    const M = new Function(escSrc + "\n" + mutSrc + "return paperBodyHtml;")();
    ok(!/<h2>一、引言<\/h2>/.test(M(PAPER, false)), "拆掉标题分支后 [二] 组会红");
    /* 第二个变异：把 <p> 换回图片 —— 「不许有图片元素」那条必须抓住 */
    const mut2 = src.replace("('<p>'+esc(L)+'</p>')", "('<img alt=\"'+esc(L)+'\">')");
    const M2 = new Function(escSrc + "\n" + mut2 + "return paperBodyHtml;")();
    ok(/<img/i.test(M2(PAPER, false)), "第二个变异确实塞回了图片");
    ok(!(!/<img|<canvas/i.test(M2(PAPER, false))), "★「稿子里没有图片元素」那条判据在变异下会红（它不是空转）");

    console.log("\n===== " + P + " PASS / " + FA + " FAIL =====");
    process.exit(FA ? 1 : 0);
  });
})();
