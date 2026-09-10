/* sim_docx_math.js —— Word 导出那一路的【行内公式 → Unicode】护栏
 *
 * 缘起（2026-09-10 王德生指出）：成文长档面板里 $D_{t}$、$E_{t}$、$M_{t}$
 * 一路显示为 LaTeX 源码。查下来三层里断的是**排版层**：
 *   · 提示层 —— 2026-09-08 已令基底在文章档写 LaTeX（见 sim_dist_math.js），基底照办了；
 *   · 排版层 —— 对话区那一路早已修好（patch_chatsde_pdf_math.py 的 pdfMath），
 *               而**成文长档面板不在 msgsEl 里**，typeset 一次都没被调过；
 *   · docx —— sde-docx.js 对公式零处理，$…$ 原样印进 Word。
 *
 * Word 要真显示数学得走 OMML，那是另一件工程。在它做出来之前，这里是保底层：
 * 常见下标/上标/希腊字母换 Unicode，换不动的整体回退原样。
 *
 * 三条纪律都是这份模拟当场抓出来的（初版三条全踩）：
 *   ① 货币不许误吃 —— "价格 $100 到 $200" 曾被吃成 "价格 100 到 200"；
 *   ② 转不干净整体回退 —— 半转换的 "\text未知宏_q" 比原样更难读；
 *   ③ 块级 $$…$$ 先摘走 —— 否则行内正则从第二个 $ 起手，"$$x=1$$" 被吃成 "$x=1$"。
 *
 * 跑法：node tools/sim_docx_math.js
 */
"use strict";
const fs = require("fs"), path = require("path");
const SRC = path.join(__dirname, "..", "public/assets/sde-docx.js");
const src = fs.readFileSync(SRC, "utf8");

const m = src.match(/var SUB = [\s\S]*?function deTex\(line\) \{[\s\S]*?\n  \}/);
if (!m) { console.log("✗ 抽不出 deTex 片段——sde-docx.js 的公式层被改动或删除了"); process.exit(1); }
/* 用 new Function 而不是 eval：本文件是 "use strict"，严格模式下 eval 的变量声明
   不泄漏到外层作用域 —— 直接 eval 会在下面报 "deTex is not defined"（本机踩过）。 */
const deTex = new Function(m[0] + "\n; return deTex;")();

const C = [
  ["$D_{t}$、$E_{t}$ 和 $M_{t}$ 的连续成立确认。", "Dₜ、Eₜ 和 Mₜ 的连续成立确认。", "截图真样本"],
  ["生成性失败可以成立，但 $E_{t}=0$。", "生成性失败可以成立，但 Eₜ=0。", "截图真样本"],
  ["读数 $\\gamma$ 与落差 $\\Lambda$", "读数 γ 与落差 Λ", "希腊字母"],
  ["$x^{2}+y^{2}$", "x²+y²", "上标"],
  ["$\\sum_{i}$ 与 $\\infty$", "∑ᵢ 与 ∞", "符号+下标"],
  ["$\\alpha_{1} \\leq \\beta_{2}$", "α₁ ≤ β₂", "组合"],
  ["不含公式的普通中文一行。", "不含公式的普通中文一行。", "无公式不动"],
  ["价格 $100 到 $200 之间", "价格 $100 到 $200 之间", "① 货币不许误吃"],
  ["成本 $ 50 与 $ 80", "成本 $ 50 与 $ 80", "① $ 后留白"],
  ["$\\text{未知宏}_{q}$", "$\\text{未知宏}_{q}$", "② 转不干净则回退"],
  ["$\\frac{a}{b}$", "$\\frac{a}{b}$", "② 分式暂不支持→回退"],
  ["$$x=1$$", "$$x=1$$", "③ 块级不动"],
];
let pass = 0, fail = 0;
for (const [inp, want, tag] of C) {
  const got = deTex(inp), ok = got === want;
  console.log((ok ? "✓" : "✗") + " [" + tag + "] " + JSON.stringify(inp));
  if (!ok) { console.log("   期望 " + JSON.stringify(want) + "\n   实得 " + JSON.stringify(got)); fail++; } else pass++;
}
console.log(`\n${fail ? "✗" : "✓"} sim_docx_math: ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
