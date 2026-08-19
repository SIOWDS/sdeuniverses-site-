/* sim_wds_diff.js —— /assets/wds-diff.js 的护栏
 * 模块是纯函数（不碰 DOM/window），所以这里直接 require 真跑。
 * 用法：node tools/sim_wds_diff.js
 */
"use strict";
const path = require("path");
let PASS = 0, FAIL = 0;
const ok = (c, m) => { if (c) PASS++; else { FAIL++; console.log("  ✗ " + m); } };
const sec = t => console.log("\n── " + t + " ──");

const D = require(path.join(__dirname, "..", "public/assets/wds-diff.js"));

sec("① 纯函数、不碰环境");
{
  ok(typeof D === "object" && D.VERSION >= 1, "模块没导出或没有版本号");
  ["lines", "chars", "html", "stat"].forEach(k => ok(typeof D[k] === "function", "缺 " + k));
  const src = require("fs").readFileSync(path.join(__dirname, "..", "public/assets/wds-diff.js"), "utf8");
  ok(!/\bdocument\./.test(src), "模块碰了 document —— 就不能在 node 里直测了");
  ok(!/\blocalStorage\b/.test(src), "模块碰了 localStorage");
}

sec("② 行级");
{
  const a = "第一行\n第二行\n第三行";
  const b = "第一行\n第三行";
  const r = D.lines(a, b);
  ok(!r.big, "不该判成超大");
  const s = D.stat(r);
  ok(s.del === 1 && s.add === 0 && s.chg === 0, "删一行没识别出来：" + JSON.stringify(s));

  const s2 = D.stat(D.lines("甲\n乙", "甲\n乙\n丙"));
  ok(s2.add === 1 && s2.del === 0, "加一行没识别出来：" + JSON.stringify(s2));

  ok(D.stat(D.lines("一样", "一样")).add === 0 && D.stat(D.lines("一样", "一样")).del === 0, "相同的两版竟报有变化");

  /* 掐头去尾：前后大段不变时，中段才是要算的 */
  const head = Array.from({ length: 400 }, (_, i) => "不变行" + i).join("\n");
  const r3 = D.lines(head + "\n中间原文\n" + head, head + "\n中间改了\n" + head);
  ok(r3.pre === 400 && r3.post === 400, "掐头去尾没生效（pre/post = " + r3.pre + "/" + r3.post + "）");
  ok(r3.ops.length <= 2, "中段之外的行也进了 ops，说明没 trim");
}

sec("③ 字级细化（中文一行就是一整段，纯行级等于什么都没说）");
{
  const a = "理解不是信息的传递，而是判准的交接。";
  const b = "理解不是信息的传递，而是判准的移交。";
  const r = D.lines(a, b);
  const s = D.stat(r);
  ok(s.chg === 1, "改了两个字却没合成一条「改」：" + JSON.stringify(s));
  const parts = r.ops[0].parts;
  ok(Array.isArray(parts), "没有字级明细");
  /* ⚠ 不要去钉"删掉的应该是哪几个字"——「交接→移交」的**最小** diff 是删「接」加「移」
     （「交」是共有的），我第一版按直觉写成删「交接」，当场误报。
     正确的判据是**不变式**：从 parts 必须能逐字还原出两版。 */
  const back = t => parts.filter(p => p.t === "=" || p.t === t).map(p => p.v).join("");
  ok(back("-") === a, "从 parts 还原不出旧版：" + back("-"));
  ok(back("+") === b, "从 parts 还原不出新版：" + back("+"));
  const eqLen = parts.filter(p => p.t === "=").map(p => p.v).join("").length;
  ok(eqLen >= a.length - 3, "共有部分只认出 " + eqLen + " 字，diff 碎得没法看");

  /* 差太远就不做字级——那是"删一行加一行"，硬做字级会拼出满屏碎片 */
  const r2 = D.lines("完全不同的一句话甲乙丙丁", "另外一个毫不相干的东西戊己庚辛");
  ok(D.stat(r2).chg === 0, "两行毫不相干却被合成了「改」");

  /* 单行过长就退回整行替换，不做 O(n·m) 字级 */
  ok(D.chars("字".repeat(2000), "词".repeat(2000)) === null, "超长单行仍在做字级（会卡）");
}

sec("④ 超大要如实降级，不许悄悄只算一半");
{
  const a = Array.from({ length: 2200 }, (_, i) => "行" + i).join("\n");
  const b = Array.from({ length: 2200 }, (_, i) => "另" + i).join("\n");
  const r = D.lines(a, b);
  ok(r.big === true, "超大没有降级标记");
  ok(!r.ops, "降级了却还给了 ops（那就是只算了一半）");
  const h = D.html(a, b, { tBig: "太长了不算" });
  ok(h.indexOf("太长了不算") > -1, "超大时没有把话说出来");
}

sec("⑤ 渲染");
{
  const h = D.html("第一行\n第二行\n第三行", "第一行\n改过的第二行\n第三行");
  ok(h.indexOf("wdsd-add") > -1 && h.indexOf("wdsd-del") > -1, "没有加/删两种行");
  ok(/<i>[+\u2212]<\/i>/.test(h), "行首没有 +/− 记号（只靠颜色，色盲与打印都看不出来）");
  ok(D.html("同", "同", { tNone: "一模一样" }).indexOf("一模一样") > -1, "无变化时没说话");

  /* 转义：画布里装的可能就是一段 html */
  const hx = D.html("<script>bad()</script>", "<script>worse()</script>");
  ok(hx.indexOf("<script>") === -1, "diff 输出里混进了未转义的 script 标签");
  ok(hx.indexOf("&lt;script&gt;") > -1, "尖括号没被转义");

  /* 未改的大段要折起来 */
  const big = Array.from({ length: 60 }, (_, i) => "不变" + i).join("\n");
  const h2 = D.html(big + "\n甲", big + "\n乙");
  ok(h2.indexOf("未改") > -1 || h2.indexOf("unchanged") > -1, "未改的大段没有折叠（要往下翻半天才看到改动）");

  /* 空输入不炸 */
  ok(typeof D.html("", "新内容") === "string", "空对非空炸了");
  ok(typeof D.html("旧内容", "") === "string", "非空对空炸了");
  ok(typeof D.html(null, undefined) === "string", "null/undefined 炸了");
}

console.log("\n" + PASS + " PASS / " + FAIL + " FAIL");
process.exit(FAIL ? 1 : 0);
