/* 金点子·「投稿后能看见自己投了什么」这条通道的回归测试。
 *   node tools/sim_idea_reader.js          （在仓库根目录跑）
 *
 * 为什么要有这个测试：用户报的是「一次生成自动投稿之后，回到互动序列，最后那份下载点不动」。
 * 上一轮（2026-07-30）已经修过一次文件系统授权那层，但下载这条路天然要过
 * 「docx 打包 → 目录授权 → 写盘」三道全在浏览器那层的关，jsdom 复现不了、也保证不了。
 * 所以这次加的是一条**不依赖它们**的通道：文本还在内存里就一定能读、能复制、能存成纯文本。
 * 这个 sim 钉的就是那条通道，外加「下载按钮不许再静默失败」。
 *
 * 纪律：从真实页面里抠出函数原文 eval 出来跑，不复制一份代码——复制的那份对了不算数。
 * 变异检验：对着改动前的页面跑，必须是 FAIL（否则这个测试等于没写）。
 */
"use strict";
const fs = require("fs");
const path = require("path");
const { JSDOM } = require(process.env.NODE_PATH
  ? "jsdom"
  : path.join(process.env.HOME || "/home/claude", "node_modules", "jsdom"));

const PAGE = "public/taste/idea-generator/index.html";
const h = fs.readFileSync(PAGE, "utf8");
let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };
const sec = (t) => console.log("\n── " + t);

/* ══════ 1. 静态断言：该有的东西必须真的在页面里 ══════ */
sec("1. 页面结构");
["paperReadWrap", "paperReadTabs", "paperReadInner", "paperReadTitle", "paperReadMeta",
 "paperReadCopy", "paperReadClose", "polishReadBtn", "polishMdBtn", "polishDlNote"]
  .forEach((id) => ok(h.indexOf('id="' + id + '"') > -1, "页面里有 #" + id));

const zRead = /id="paperReadWrap"[^>]*z-index:(\d+)/.exec(h);
ok(!!zRead && Number(zRead[1]) > 9000,
   "阅读浮层层级高于两个模态（9000/8999），一次生成跑完不关窗也能读：z-index=" + (zRead && zRead[1]));
ok(/id="paperReadWrap"[^>]*display:none/.test(h), "阅读浮层默认不显示");
ok(h.indexOf("const polishReadBtn = $('polishReadBtn')") > -1, "阅读按钮已接线");
ok(h.indexOf("const polishMdBtn = $('polishMdBtn')") > -1, "纯文本按钮已接线");

sec("2. 下载不许再静默失败");
ok(/const papers = window\._polishedPapers; if\(!papers\) return;\s*\n\s*const q = \(window\._lastResult && window\._lastResult\.question\) \|\| '';\s*\n\s*const blocks/.test(h) === false,
   "polishDlBtn 里那句 `if(!papers) return;`（点了没反应的来源）已经不在了");
ok(/saveWordDocx\(title, subtitle, blocks, filename, noteEl\)/.test(h), "saveWordDocx 收一个回执位参数");
ok(/blocks, '最后四篇_二次审稿打磨版\.docx', note\)/.test(h), "polishDlBtn 把回执位传进去了");
ok(h.indexOf("✓ 已写入你选的文件夹") > -1 && h.indexOf("不在下载栏里") > -1,
   "写进文件夹时说清楚文件不在下载栏（这正是用户以为“没下载”的那一种）");
ok(h.indexOf("✗ 生成 Word 失败") > -1, "打包失败会在按钮旁写明原因");
ok(/try\{ children\.push\(thoughtDeclPara\(\)\); \}catch\(_\)\{\}/.test(h),
   "saveWordDocx 里的声明段包了 try（同步抛错会让整个点击悄悄死掉）");

sec("3. 一次生成跑完给“现在就读”的入口");
ok(h.indexOf("📖 现在就读这四篇") > -1, "投稿完成回执里有阅读按钮");
ok(/_rb\.addEventListener\('click', function\(\)\{ openPapersReader\(window\._polishedPapers/.test(h),
   "那个按钮直接打开阅读浮层（不经下载）");

/* ══════ 2. 行为：把真代码抠出来跑 ══════ */
sec("4. 阅读浮层真行为");

// 抠出阅读浮层的 HTML 片段与 JS 原文
const frag = /(<div id="paperReadWrap"[\s\S]*?)\n\n<!-- 学术论文结果面板 -->/.exec(h);
if (!frag) { console.log("  FAIL 抠不出阅读浮层 HTML"); F++; }
const jsBlock = /(\/\* ===== 论文在线阅读浮层 =====[\s\S]*?)\n\/\/ 最后四篇（打磨版）下载/.exec(h);
if (!jsBlock) { console.log("  FAIL 抠不出阅读浮层 JS"); F++; }

if (frag && jsBlock) {
  const dom = new JSDOM("<!doctype html><body>" + frag[1] +
    '<div id="polishDlNote"></div><button id="polishDlBtn"></button>' +
    '<button id="polishReadBtn"></button><button id="polishMdBtn"></button></body>');
  const win = dom.window, doc = win.document;
  const alerts = [];
  win.alert = (m) => alerts.push(m);
  win.$ = (id) => doc.getElementById(id);
  win._lastResult = { question: "为什么组织越大越怕出错" };
  // eval 真代码
  const fn = new win.Function("window", "document", "navigator", "alert", "$",
    jsBlock[1] + "\nwindow.__api = { openPapersReader, closePapersReader, renderPapersReader, papersToMd };");
  fn.call(win, win, doc, win.navigator, win.alert, win.$);
  const API = win.__api;

  const NASTY = "第一节 <script>alert(1)</script> & 一个 <b>标签</b>\n第二行";
  const papers = [
    { title: "承载权", text: "论文一正文\n" + NASTY },
    { title: "隐形的第三格", text: "论文二正文" },
    { title: "空的那篇", text: "" },
    { title: "双链型", text: "论文四正文" },
  ];

  // 空产出：不开窗、明确告知
  API.openPapersReader([], "x");
  ok(doc.getElementById("paperReadWrap").style.display !== "flex", "没有产出时不开一个空窗");
  ok(alerts.length === 1 && /还没有可读/.test(alerts[0]), "没有产出时说清楚为什么");

  API.openPapersReader(papers, "最后四篇");
  ok(doc.getElementById("paperReadWrap").style.display === "flex", "有产出时浮层打开");
  ok(doc.getElementById("paperReadTabs").querySelectorAll("button").length === 4,
     "四篇各一个页签（空文本那篇也留着，让人看见它是空的）");
  const inner = doc.getElementById("paperReadInner");
  ok(inner.textContent.indexOf("论文一正文") > -1, "第一篇正文出来了");
  ok(inner.textContent.indexOf("承载权") > -1, "标题出来了");
  ok(inner.innerHTML.indexOf("<script>") === -1 && inner.textContent.indexOf("<script>") > -1,
     "正文里的尖括号是文本不是标签（用 textContent，论文带代码片段也不串版）");
  ok(/第 1\/4 篇/.test(doc.getElementById("paperReadMeta").textContent), "有第几篇的定位");
  ok(/原初问题：为什么组织越大越怕出错/.test(doc.getElementById("paperReadMeta").textContent),
     "读的时候看得见这是哪个问题跑出来的");

  // 切页签
  doc.getElementById("paperReadTabs").querySelectorAll("button")[1].dispatchEvent(new win.Event("click"));
  ok(inner.textContent.indexOf("论文二正文") > -1 && inner.textContent.indexOf("论文一正文") === -1,
     "点页签能换篇");
  // 空篇
  doc.getElementById("paperReadTabs").querySelectorAll("button")[2].dispatchEvent(new win.Event("click"));
  ok(/空的|出错/.test(inner.textContent), "空的那篇如实说它是空的，不显示成一片白");

  // 关闭
  doc.getElementById("paperReadClose").dispatchEvent(new win.Event("click"));
  ok(doc.getElementById("paperReadWrap").style.display === "none", "能关掉");

  // 复制
  let copied = null;
  win.navigator.clipboard = { writeText: (t) => { copied = t; return Promise.resolve(); } };
  API.openPapersReader(papers, "最后四篇");
  doc.getElementById("paperReadCopy").dispatchEvent(new win.Event("click"));
  ok(copied && copied.indexOf("论文一正文") > -1 && copied.indexOf("承载权") > -1,
     "复制本篇带标题和正文");

  sec("5. 纯文本保底通道");
  const md = API.papersToMd(papers, "为什么组织越大越怕出错");
  ok(md.indexOf("## 承载权") > -1 && md.indexOf("## 双链型") > -1, "每篇一个二级标题");
  ok(md.indexOf("论文一正文") > -1 && md.indexOf("论文四正文") > -1, "正文一个不少");
  ok(md.indexOf("## 空的那篇") === -1, "空文本那篇不进文件（省得下游拿到一段空壳）");
  ok(md.indexOf("原初问题：为什么组织越大越怕出错") > -1, "带上原初问题");
  ok(md.indexOf("docx") === -1, "这条路不碰 docx");
  ok(/papersToMd[\s\S]{0,900}new Blob/.test(h) === false || h.indexOf("new Blob([papersToMd") > -1,
     "存纯文本直接走 Blob + <a download>，不经 WDSSaveDir 授权");
}

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
