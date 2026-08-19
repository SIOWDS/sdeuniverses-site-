/* sim_wds_rte.js —— /assets/wds-rte.js 的护栏（纯函数，node 直测往返）
 * 这个模块唯一必须保证的事是：**在富文本里改完，字不会丢**。
 * 所以断言的重心不是"生成的 html 好不好看"，是往返之后可见文字一字不差。
 * 用法：node tools/sim_wds_rte.js
 */
"use strict";
const path = require("path");
const fs = require("fs");
let PASS = 0, FAIL = 0;
const ok = (c, m) => { if (c) PASS++; else { FAIL++; console.log("  ✗ " + m); } };
const sec = t => console.log("\n── " + t + " ──");
const R = require(path.join(__dirname, "..", "public/assets/wds-rte.js"));

/* 往返：可见文字必须一字不差 */
function rt(md, label) {
  const back = R.toMd(R.toHtml(md));
  const a = R.textOf(md), b = R.textOf(back);
  ok(a === b, label + " 往返丢字：\n    原 " + JSON.stringify(a.slice(0, 90)) + "\n    回 " + JSON.stringify(b.slice(0, 90)));
  return back;
}

sec("① 纯函数");
{
  ok(R.VERSION >= 1, "没有版本号");
  /* ⚠ 扫词之前必须先把注释剥掉 —— 文件头的说明里就写着「不用 `innerHTML` 完再遍历」，
     按原文扫必然把这句说明本身当成违规。（这是同一个坑的第二次，第一次在 sim_growth。） */
  const raw = fs.readFileSync(path.join(__dirname, "..", "public/assets/wds-rte.js"), "utf8");
  const src = raw.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
  ok(!/\bdocument\.|innerHTML|querySelector/.test(src), "模块碰了 DOM —— 就测不了往返了");
  ok(/不碰 DOM/.test(raw), "文件头那句纪律被删了");
}

sec("② 块级往返");
{
  rt("# 一级标题\n\n正文一段。\n\n## 二级标题\n\n又一段。", "标题与段落");
  rt("- 甲\n- 乙\n- 丙", "无序列表");
  rt("1. 第一\n2. 第二\n3. 第三", "有序列表");
  rt("> 引用的一句话。\n> 第二行。", "引用");
  rt("正文\n\n---\n\n正文", "分隔线");
  rt("| 甲 | 乙 |\n| --- | --- |\n| 一 | 二 |\n| 三 | 四 |", "表格");
  rt("```js\nvar a = 1;\nif (a) { b(); }\n```", "围栏代码");
  rt("第一段\n\n第二段\n\n第三段", "多段");

  const h = R.toHtml("# 标题\n\n正文");
  ok(/<h1>/.test(h) && /<p>/.test(h), "标题/段落没生成对：" + h);
  ok(/<ul><li>/.test(R.toHtml("- 甲")), "无序列表没生成 ul>li");
  ok(/<ol><li>/.test(R.toHtml("1. 甲")), "有序列表没生成 ol>li");
  ok(/<table>/.test(R.toHtml("| 甲 |\n| --- |\n| 一 |")), "表格没生成");
}

sec("②b 结构断言（往返按文字比对看不见结构错，必须单独钉）");
{
  const eq = (md, want, label) => {
    const back = R.toMd(R.toHtml(md));
    ok(back.trim() === want.trim(), label + "：\n    得 " + JSON.stringify(back) + "\n    期 " + JSON.stringify(want));
  };
  eq("# 一级标题", "# 一级标题", "标题必须还是一行（曾经被 block() 顶到下一行）");
  eq("### 三级标题\n\n正文", "### 三级标题\n\n正文", "标题后接正文");
  eq("- 甲\n- 乙", "- 甲\n- 乙", "无序列表");
  eq("1. 甲\n2. 乙", "1. 甲\n2. 乙", "有序列表");
  eq("> 引用", "> 引用", "引用");
  eq("正文**粗**尾", "正文**粗**尾", "行内加粗不带多余空白");
}

sec("③ 行内往返");
{
  rt("这里有**粗体**和*斜体*还有~~删除~~以及`代码`。", "行内四种");
  rt("一个[链接](https://example.com)在句中。", "链接");
  const back = R.toMd(R.toHtml("一个[链接](https://example.com)在句中。"));
  ok(back.indexOf("https://example.com") > -1, "链接地址丢了：" + back);
  rt("![图](https://example.com/a.png)", "图片");
  /* 代码里的星号不许被当成强调 */
  const h = R.toHtml("`a*b*c`");
  ok(h.indexOf("<em>") === -1, "行内代码里的星号被当成了强调：" + h);
}

sec("④ 中文与真实稿件");
{
  rt("理解不是信息的传递，也不是共识的达成，**而是判准的交接**。", "中文加粗");
  rt("## 承重命题\n\n- 它切开的辨别面：谁在为谁的判断兜底\n- 可裁决判据：三个月内能不能查到\n\n> 库未命中 ≠ 未被占位。", "一段真稿");
  const long = "# 稿子\n\n" + Array.from({ length: 30 }, (_, i) =>
    "第" + i + "段正文，里面有**重点**也有`代码`，还有一个[链接](https://x.cn)。").join("\n\n");
  rt(long, "长稿");
}

sec("⑤ 宽容进：contenteditable 吐出来的脏东西也要吃得下");
{
  const dirty = '<div style="color:red"><font face="x">正文</font> <b>粗</b> <i>斜</i></div>' +
    '<div><span></span>第二段</div>';
  const md = R.toMd(dirty);
  ok(md.indexOf("正文") > -1 && md.indexOf("**粗**") > -1 && md.indexOf("*斜*") > -1, "脏 html 没转对：" + md);
  ok(md.indexOf("<") === -1, "转出来的 markdown 里还留着标签：" + md);
  ok(md.indexOf("第二段") > -1, "div 分段丢了内容");
  ok(md.indexOf("style") === -1 && md.indexOf("font") === -1, "样式/字体属性漏进了正文");

  ok(R.toMd("<p>甲<br>乙</p>").indexOf("甲") > -1, "br 处理炸了");
  ok(R.toMd("") === "", "空输入应返回空串");
  ok(typeof R.toMd(null) === "string" && typeof R.toHtml(null) === "string", "null 炸了");
  ok(R.toMd("<p>没闭合").indexOf("没闭合") > -1, "没闭合的标签把内容吞了");
}

sec("⑥ 转义：画布里可能就装着一段 html");
{
  const h = R.toHtml("正文里有 <script>bad()</script> 这种东西");
  ok(h.indexOf("<script>") === -1, "md→html 没转义 script");
  ok(R.toMd(h).indexOf("<script>bad()</script>") > -1, "往返之后 script 那段文字丢了或变形了");
}

sec("⑦ check()：扶不住就得承认");
{
  const good = R.check("# 标题\n\n正文**粗**。\n\n- 甲\n- 乙");
  ok(good.ok === true, "正常稿子被判成扶不住：" + JSON.stringify(good));
  ok(typeof good.md === "string", "check 没回传往返结果");

  /* 认得出「有东西丢了」这件事，并说出丢了多少 —— 静默丢字比没这个功能坏得多 */
  const bad = R.check("正文\n\n$$\\int_0^1 f(x)\\,dx$$\n\n<div class='x' data-y='1'>原始 html 块</div>");
  ok(typeof bad.ok === "boolean", "check 没给结论");
  if (bad.ok === false) ok(typeof bad.lost === "number" || bad.why === "err", "判成扶不住却没说丢了多少");

  ok(R.check("").ok === true, "空稿子不该被判成扶不住");
}

console.log("\n" + PASS + " PASS / " + FAIL + " FAIL");
process.exit(FAIL ? 1 : 0);
