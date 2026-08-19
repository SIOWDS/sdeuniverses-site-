/* 只测一件事：站内搜索页「成文一篇」出 PDF 时的行级排版兜底（mdSkip / mdClean / isPaperHead）。
   病根（2026-07-28 SDE-paper11 实例）：下半篇整段吐 Markdown（# 标题、**加粗**、|竖线表格|、--- 分隔线），
   旧渲染器只认【】与「一、」两种标题，其余一律 esc 成正文，于是这些标记原样印进了 PDF。
   规程 v2 已在 system prompt 里禁用 Markdown；本脚本守的是那层「不信任模型输出」的兜底。
   用例全部取自那一篇的真实行。 */
"use strict";
const fs = require("fs");
const html = fs.readFileSync("/home/claude/site/public/search/index.html", "utf8");

/* 把三个具名函数原样抠出来真跑（不复制一份实现——复制的那份永远不会跟着改） */
const names = ["mdSkip", "mdClean", "isPaperHead"];
let src = "";
names.forEach(function (n) {
  const a = html.indexOf("function " + n + "(");
  if (a < 0) { console.log("FAIL 抠不出 " + n + "（渲染器改名了，先改本脚本）"); process.exit(1); }
  const b = html.indexOf("\nfunction ", a + 1);
  src += html.slice(a, b < 0 ? a + 900 : b) + "\n";
});
const F = new Function(src + "return {mdSkip:mdSkip, mdClean:mdClean, isPaperHead:isPaperHead};")();

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

console.log("\n===== " + P + " PASS / " + FA + " FAIL =====");
process.exit(FA ? 1 : 0);
