/* sim_texify.js —— 「键盘写法的数学 → 正式数学式」这条线的护栏
 *
 * 缘起（2026-08-01）：用户配截图——ChatSDE 答出来的是 `e^(i3θ) = cos3θ + i sin3θ`，
 * 代码写法，不是数学。两层修：① worker 的 WDS_CHAT_SYS 硬性要求写 LaTeX；
 * ② 前端 texify() 兜底，把已经生成的键盘写法就地扶正。
 *
 * 这份护栏的重心不在"转得对"，而在**"该不动的一个字都别动"**——
 * 误把普通句子判成公式，整句会变成一串数学斜体，比不转坏得多。
 * 所以下面负例比正例还多，且每条负例都写明它凭哪道闸活下来。
 *
 * 跑法：node tools/sim_texify.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");
let pass = 0, fail = 0;
const ok = (n, c) => { if (c) { pass++; } else { fail++; console.log("  ✗ " + n); } };

const SRC = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");
const WORKER = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");

/* ── 从真页面里抠出整套 texify，别另写一份 ── */
function grab(re, what) { const m = re.exec(SRC); if (!m) { console.log("  ✗ 抠不到 " + what); fail++; return ""; } return m[0]; }
const texify = new Function([
  grab(/var TEX_GREEK = \{[\s\S]*?\n  \};/, "TEX_GREEK"),
  grab(/var TEX_SYM = \{[\s\S]*?\n  \};/, "TEX_SYM"),
  grab(/var TEX_FUNCS = \([\s\S]*?\.split\(" "\);/, "TEX_FUNCS"),
  grab(/var TEX_GNAMES = \([\s\S]*?\.split\(" "\);/, "TEX_GNAMES"),
  grab(/function texWordOk\(w\) \{[\s\S]*?\n  \}/, "texWordOk"),
  grab(/var TEX_SUP = \{[\s\S]*?\};/, "TEX_SUP"),
  grab(/var TEX_SUB = \{[\s\S]*?\};/, "TEX_SUB"),
  grab(/var TEX_CH = [\s\S]*?;\n/, "TEX_CH"),
  grab(/var TEX_RUN = .*?;/, "TEX_RUN"),
  grab(/var TEX_HARD = .*?;/, "TEX_HARD"),
  grab(/function texBody\(x\) \{[\s\S]*?\n  \}/, "texBody"),
  grab(/function texRun\(raw\) \{[\s\S]*?\n  \}/, "texRun"),
  grab(/function texify\(src\) \{[\s\S]*?\n  \}/, "texify"),
  "return texify;",
].join("\n"))();

const katex = require(path.join(ROOT, "public/assets/katex/katex.min.js"));
function renders(tex) { try { katex.renderToString(tex, { throwOnError: true }); return true; } catch (e) { return false; } }
// 每条正例都要过两关：转成什么样，以及 **KaTeX 真的排得出来**
function yes(name, input, mustHave) {
  const out = texify(input);
  const got = mustHave.every((x) => out.indexOf(x) >= 0);
  const bodies = out.match(/\$\$?([^$]+)\$\$?/g) || [];
  const allRender = bodies.length > 0 && bodies.every((b) => renders(b.replace(/^\$\$?|\$\$?$/g, "")));
  if (!got) console.log("    ↳ 实得: " + JSON.stringify(out));
  ok(name, got && allRender);
}
function no(name, input) {
  const out = texify(input);
  if (out !== input) console.log("    ↳ 被动了: " + JSON.stringify(out));
  ok(name, out === input);
}

console.log("── 正例：键盘写法该被扶正 ──");
// 用户截图里的原句，一字不改
yes("用户截图那句：e^(i3θ) = cos3θ + i sin3θ", "写下:  e^(i3θ) = cos3θ + i sin3θ",
    ["$e^{i3\\theta}", "\\cos 3\\theta", "\\sin 3\\theta"]);
yes("截图第二句：带 ³ 的三次方", "也写下:  e^(i3θ) = (e^(iθ))³ = (cosθ + i sinθ)³",
    ["(e^{i\\theta})^{3}", "(\\cos\\theta+ i \\sin\\theta)^{3}"]);
yes("独占一行的式子排成块级 $$…$$", "e^(iπ) + 1 = 0", ["$$e^{i\\pi} + 1 = 0$$"]);
yes("上下标：∫_0^∞ 与 √", "∫_0^∞ e^(-x^2) dx = √π/2", ["\\int_{0}^{\\infty}", "e^{-x^{2}}", "\\sqrt\\pi"]);
yes("纯 ASCII 幂次（独占一行 ⇒ 块级）", "x^2 + y^2 = r^2", ["$$x^{2} + y^{2} = r^{2}$$"]);
// 「独占一行」必须拿原文量：一行里前面已有 $…$ 时，剩下的残段自己看着像"整行"，
// 拿残段量就会把行内式误升成块级、把句子劈成两半
yes("同一行前面已有 $…$ 时，后面那条仍是行内式", "已知 $a=1$，那么 x^2 ≤ 1 成立",
    ["$a=1$", "$x^{2} \\le 1$"]);
ok("上一条确实没有升成块级", texify("已知 $a=1$，那么 x^2 ≤ 1 成立").indexOf("$$") < 0);
yes("句子中间的式子保持行内", "由此可得 e^(iθ) 的模长为 1", ["$e^{i\\theta}$"]);
ok("句中式子不许升块级", texify("由此可得 e^(iθ) 的模长为 1").indexOf("$$") < 0);
yes("科学计数与乘号", "光速约 3*10^8 m/s", ["\\times", "10^{8}"]);
yes("下标变量", "取 x_1 与 x_2，则 x_1^2 ≤ x_2^2", ["x_{1}", "x_{2}", "\\le"]);

console.log("── 负例：这些一个字都不许动 ──");
// 闸②（每个英文词都得是单字母/函数名/希腊名）是那道真正的闸
no("夹在英文散文里的公式（identity、Euler 不是数学词）", "The identity e^(iθ) is Euler's famous formula");
no("英文长句里带 ^ 也不碰", "Use the caret ^ to raise a number in most languages");
// 闸①（必须有硬数学符号）
no("SDE = Show Difference Entanglement", "这里 SDE = Show Difference Entanglement，别搞混");
no("三大方程 S=F(D,E) 保持原样（没有硬数学符号）", "三大方程 S=F(D,E)、D=G(S,E)、E=H(S,D) 互为因果");
no("普通中文句子", "显露、差异、纠缠三者互为因果，缺一不可。");
// 已经是数学的，让路
no("已经写好的 $x^2+y^2=z^2$ 不再包一层", "已经写好的 $x^2+y^2=z^2$ 不该被再包一层");
no("已经写好的块级 $$…$$ 也让路", "$$\\int_0^1 x^{2}\\,dx = \\frac{1}{3}$$");
// 别跟 Markdown 抢
no("**加粗** 与 __下划__ 不受影响", "**加粗θ**与 __下划__ 不受影响");
// 桩本身必须原样穿过去（桩坏了＝那段代码/公式当场丢失）；桩**外面**的 x^2 该扶正就扶正
ok("行内代码桩原样穿过", (() => { const o = texify("看这里 \u0000I3\u0000 的 x^2"); return o.indexOf("\u0000I3\u0000") >= 0 && o.indexOf("$x^{2}$") > 0; })());
no("代码块桩不碰", "\u0000B0\u0000");
ok("空串/undefined 不炸", texify("") === "" && texify(undefined) === "" && texify(null) === "");

console.log("── 接线 ──");
// 行首必须是四个空格 + 语句本身：写成 `// raw = texify(raw);` 照样能被宽松正则匹配上，
// 那样这条断言就成了摆设（第一版就是这么漏的，变异检验当场抓到）
ok("texify 真的被调用（不是被注释掉的那一行）", /\n    raw = texify\(raw\);\n/.test(SRC));
ok("排在代码摘除之后、公式摘除之前（次序即判据）",
   /\n    raw = texify\(raw\);\n\s*\/\/ ③ 摘公式/.test(SRC));
ok("mdRender 里只调一次", (SRC.match(/\n    raw = texify\(raw\);\n/g) || []).length === 1);
// 根子在提示词：基底按键盘写法输出，前端再神也只是补救
ok("worker 的 ChatSDE system 里有硬性【数学写法】", WORKER.indexOf("【数学写法") > 0);
["行内式包在", "不写 e^(i3θ)", "\\\\frac{a}{b}", "绝不要把公式放进代码块"].forEach((k) => {
  ok("提示词写清了：" + k, WORKER.indexOf(k) > 0);
});
ok("提示词给了正确写法的例子（欧拉公式）", /例：欧拉公式该写成 \$e\^\{i3\\\\theta\}/.test(WORKER));
ok("提示词挂在 ChatSDE 的答题 system 上（WDS_CHAT_SYS）",
   (() => { const m = /function WDS_CHAT_SYS\([\s\S]*?\n\}/.exec(WORKER); return m && m[0].indexOf("【数学写法") > 0; })());

console.log((fail ? "✗ " : "✓ ") + pass + " 项通过，" + fail + " 项失败");
process.exit(fail ? 1 : 0);
