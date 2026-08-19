/* tools/sim_pipeline3.mjs —— 金点子发生器「产线三修」护栏
   从页面里抠出 sanitizePaper 真代码来跑，喂的是**真实投稿里出现过的脏文本**，
   不是我编的样例。凡这里绿了而线上仍脏，说明净化点没接对，不是函数不对。 */
import fs from "node:fs";

let P = 0, F = 0;
const ok = (c, m) => { if (c) P++; else { F++; console.log("  FAIL:", m); } };

const page = fs.readFileSync("public/taste/idea-generator/index.html", "utf8");
const a = page.indexOf("var T2S = {");
const b = page.indexOf("window.__sanitizeLog = [];");
ok(a > 0 && b > a, "能从页面里定位三修函数段");
const src = page.slice(a, b);
const mk = new Function(src + "\nreturn { sanitizePaper: sanitizePaper, _t2s: _t2s, MONO_LINE: MONO_LINE, RHETORICAL: RHETORICAL };");
const { sanitizePaper, _t2s } = mk();
const S = (t) => sanitizePaper(t, "t");

console.log("── 1. 繁体归一（① 修）");
let r = S("製止幻象：一种消费心理\n正文。");
ok(r.text.includes("制止幻象") && !r.text.includes("製"), "「製止」→「制止」（金华那篇的真实字样）");
ok(r.log.t2s === 1, "计数准确");
r = S("发生学的实在\n没有繁体。");
ok(r.log.t2s === 0, "干净文本不误报");

console.log("── 2. 掐掉基底独白（② 修）");
r = S("好的，我将综合审稿人A和审稿人B的意见，特别是他们共同指出的关键问题，对这篇论文进行一次实质性的修改。\n以下是修改后的完整论文。\n被导航的学习者：当知识图谱将个性化做成假自主态\n摘要：本文论证……");
ok(r.text.split("\n")[0].startsWith("被导航的学习者"), "★ 黄倩盈 82 号的真实开头：两行独白被掐掉，标题浮到首行");
ok(r.log.mono === 2, "掐掉两行并计数");
ok(r.log.title === "ok", "掐完首行是标题");
r = S("正文里说：好的，我们来看下一个例子。\n这句在中间，不该被删。");
ok(r.text.includes("好的，我们来看下一个例子"), "★ 只掐开头，正文中间的「好的」不碰");

console.log("── 3. 虚构评审史（② 修的第二层）");
r = S("认知接地\n作者感谢两位匿名审稿人提出的尖锐批评，这些批评迫使本文做了更精确的划定。\n正文。");
ok(!/匿名审稿人/.test(r.text), "★ 胡志英 97 号的真实致谢已清除");
ok(r.log.review >= 1, "计入 review");
r = S("标题\n其中与施密特的对质，是在审稿意见推动下增补的，用于检验。");
ok(!/审稿意见推动下/.test(r.text), "★ 孔凡鹤 21 号的真实字样已清除");
r = S("标题\n此次修订将案例2拆分，以回应审稿人对纵向证据的关切。");
ok(!/以回应审稿人对/.test(r.text), "★ 王德生《炉膛》的真实字样已清除");

console.log("── 4. 修辞式假想审稿人必须放过（最容易误伤的一格）");
r = S("目光的尸检报告\n它与坎贝尔定律是本文最直接的近邻——任何审稿人都有理由第一秒就问：你这不是在重述古德哈特吗？");
ok(/任何审稿人都有理由/.test(r.text), "★「任何审稿人都有理由问」是论证手法，不能删");
r = S("标题\n一位严苛的审稿人可能会问：如果排斥如此彻底，那么我还能意识到它这件事本身，是否构成证伪？");
ok(/一位严苛的审稿人可能会问/.test(r.text), "★「审稿人可能会问」是虚拟语气，不能删");
r = S("标题\n这里必须正面回应一个尖锐的质疑，如审稿人所指出的：福柯的规训难道没有预见到吗？");
ok(!/如审稿人所指出的/.test(r.text), "断言语气的「如审稿人所指出的」要清除");

console.log("── 5. 标题槽位校验（③ 修）");
ok(S("提升·论文③ · 金点子③（纠缠(E) · E2 · 信息）\n摘要……").log.title.startsWith("bad"),
   "★ 黄倩盈 34 号的真实症状：产线标记占住标题位 → 报 bad");
ok(S("摘　要\n本文论证……").log.title.startsWith("bad"), "首行是「摘要」→ bad");
ok(S("一、引言：一个问题如何被问错\n正文").log.title.startsWith("bad"), "★ 陈晓艳那份的真实症状：首行是节标题 → bad");
ok(S("——数字时代亲密关系的形成、错位与重建\n正文").log.title === "ok", "副标题行不误判（不以句号收尾、不含关键词）");
ok(S("理解的诞生：它从来不是看见，而是一次重写\n摘要……").log.title === "ok", "正常标题判 ok");
ok(S("本文论证这一视觉隐喻系统性地误导了我们对理解的把握。\n").log.title.startsWith("bad"), "首行是完整句子（以句号收尾）→ bad");
ok(S("").log.title.startsWith("bad"), "空文本 → bad，不崩");

console.log("── 6. 不静默 · 计数可读");
r = S("好的，我将改写。\n製止的幻象\n承蒙匿名审稿人指正。\n正文。");
ok(r.log.mono === 1 && r.log.t2s === 1 && r.log.review >= 1, "三类同时命中时各自计数");
ok(typeof r.log.tag === "string", "带 tag 便于定位是哪一篇");

console.log("── 7. 页面接线");
ok(page.includes("window.__sanitizeLog = []"), "有日志容器");
ok(page.includes("function sanitizeNotice"), "有面向人的提示函数");
ok(page.includes("正在上传到收件箱…'+sanitizeNotice()"), "★ 投稿状态栏会把净化结果说出来（不静默）");
const wired = (page.match(/sanitizeAndLog\(/g) || []).length;
ok(wired >= 5, `四个阶段落定点 + docx 打包都接了（实测 ${wired} 处调用）`);
for (const v of ["_fourPapers", "_upliftPapers", "_normalizedPapers", "_polishedPapers"]) {
  const i = page.indexOf("window." + v + " = results.map");
  ok(i > 0 && page.slice(i, i + 260).includes("sanitizeAndLog("), `${v} 落定点已接`);
}
const d = page.indexOf("function buildPapersDocxBlob");
ok(page.slice(d, d + 1400).includes("sanitizeAndLog(pp.text"), "★ 进投稿箱的最后一道也接了");
ok(!/sanitizeAndLog\([^)]*\)\s*\.catch/.test(page), "净化是同步的，没有被吞进 promise");


console.log("── 8. 源头修：提示里的交付纪律");
const specs = ["PAPER_SPEC", "PAPER_SPEC_1W", "UPLIFT_SPEC", "REVISE_SPEC"];
for (const name of specs) {
  const i = page.indexOf("const " + name + " = `");
  const j = i > 0 ? page.indexOf("`;", i) : -1;
  const seg = i > 0 ? page.slice(i, j) : "";
  ok(seg.includes("交付纪律"), `${name} 带交付纪律`);
  ok(seg.includes("第一行必须是论文标题本身"), `${name} 要求首行是标题`);
  ok(seg.includes("并未经过同行评议"), `${name} 禁止伪造评审史`);
  ok(seg.includes("全文用简体中文"), `${name} 要求简体`);
}
ok(page.includes("把某位审稿人可能提的质疑当作论证对手来正面回应是可以的"),
   "★ 提示里明写了修辞式假想审稿人可以留——与净化器的放过规则口径一致");

console.log(`\n${P} PASS / ${F} FAIL`);
process.exit(F ? 1 : 0);
