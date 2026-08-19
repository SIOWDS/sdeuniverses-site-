/* sim_chatsde_mathlive.js —— ChatSDE「公式当场排成数学」这条线的护栏
 *
 * 缘起（2026-08-01）：用户配截图——一整屏答案里 $a^2+b^2=c^2$、$\frac{ab}{2}$ 全是原文，
 * 「数学化没有自动、没有成功」。真因**不是** KaTeX 没装上，是行内公式的**左边界**写成
 * [\s(（]（只认空白与左括号），而中文里公式总是紧贴标点：「试试，$c$」「兜底：$e^{…}$」
 * 一条都不匹配。加上 typeset 只在定稿后跑、还要现拉 275KB，读者整场看到的都是 $…$。
 *
 * 这份护栏钉三件事：① 中文标点后的行内公式必须被摘出来；② 放宽左边界之后**不许**把
 * 半句话排成数学（$5 买咖啡；变量 A$B）；③ 流式每帧同步排版、发问即预热、定稿后补一刀。
 *
 * 跑法：node tools/sim_chatsde_mathlive.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");
let pass = 0, fail = 0;
const ok = (n, c) => { if (c) { pass++; } else { fail++; console.log("  ✗ " + n); } };
const SRC = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");

/* ── 从真页面里抠出整条渲染链，别另写一份 ── */
const i0 = SRC.indexOf("  function el(t, c, x)");
const m0 = /  function mdRender\(src\) \{[\s\S]*?\n  \}\n/.exec(SRC.slice(i0));
ok("抠得到 el…mdRender 这一段", i0 > 0 && !!m0);
const slab = SRC.slice(i0, i0 + m0.index + m0[0].length);
const mdRender = new Function(
  'var window={},document={createElement:function(){return{};}};function t(k){return k;}var LANG="zh";\n'
  + slab + "\nreturn mdRender;")();

const RAW = /<span class='wdsm-tex raw( blk)?' data-m='(\d+)'>([\s\S]*?)<\/span>/g;
function maths(md) {
  const out = []; let m; RAW.lastIndex = 0;
  while ((m = RAW.exec(mdRender(md)))) out.push({ blk: !!m[1], s: m[3] });
  return out;
}
const has = (md, tex) => maths(md).some(x => x.s.indexOf(tex) >= 0);

/* ── 一 · 中文标点紧贴着的行内公式（本次的病灶，逐个钉死）── */
[
  ["逗号后", "把它放到球面上试试，$c$ 不再是那样。", "$c$"],
  ["冒号后", "键盘写法兜底：$e^{i3\\theta}$ 就是它。", "$e^{i3\\theta}$"],
  ["顿号后", "两条路、$a^2+b^2=c^2$、以及别的。", "$a^2+b^2=c^2$"],
  ["句号后", "先说到这里。$S=F(D,E)$ 是第一条。", "$S=F(D,E)$"],
  ["全角括号内", "（$D$ 是差异序列）", "$D$"],
  ["汉字后", "总面积$(a+b)^2$，算出来就是那样。", "$(a+b)^2$"],
  ["书名号后", "见《SDE本体论》$E$ 一节。", "$E$"],
  ["行首", "$\\frac{ab}{2}$ 是四周四个之一。", "$\\frac{ab}{2}$"],
  ["空格后（老规则本来就认，别改坏）", "四周四个 $\\frac{ab}{2}$，总面积如上。", "$\\frac{ab}{2}$"],
].forEach(([n, md, tex]) => ok("摘得出 · " + n, has(md, tex)));

/* ── 二 · 放宽之后不许误伤（每条写明凭哪道闸活下来）── */
[
  ["半句话不是公式（内含汉字 ⇒ 汉字闸）", "他花了 $5 买咖啡；变量 A$B 与报价。", "5 买咖啡"],
  ["美元金额之间（汉字闸）", "定价 $100 到 $200 不等。", "100 到 "],
  ["紧跟字母的 $（左边界闸）", "变量 A$B$C 的写法。", "B"],
  ["首字符是空白（原有闸）", "这是 $ x $ 的写法。", " x "],
  ["跨行不成对（[^$\\n] 闸）", "第一行 $a\n第二行 b$ 结束。", "a"],
].forEach(([n, md, bad]) => ok("不误伤 · " + n, !has(md, bad)));

/* 代码块/行内码里的 $ 一律让路（摘代码在摘公式之前） */
ok("不误伤 · 围栏代码块里的 $x^2$", !has("```js\nvar s = \"$x^2$\";\n```", "x^2"));
ok("不误伤 · 行内码里的 $x^2$", !has("这一句 `$x^2$` 是代码。", "x^2"));

/* ── 三 · 块级仍然走 $$，且优先于行内 ── */
{
  const r = maths("独立成行：\n\n$$\\sum_{k=1}^{n} k^2$$\n\n完。");
  ok("块级 $$…$$ 摘成 blk", r.length === 1 && r[0].blk === true);
}
{
  const r = maths("行内 $a$ 与块级 $$b$$ 同段。");
  ok("同段里块级不被行内抢走", r.some(x => x.blk) && r.some(x => !x.blk));
}

/* ── 四 · 接线：流式即排 / 发问即预热 / 定稿补一刀 ── */
ok("有同步渲染 typesetSync", /function typesetSync\(node\) \{/.test(SRC));
ok("typeset 先同步试一次、剩下的才去引导 KaTeX",
   /if \(!typesetSync\(node\)\) return;[\s\S]{0,120}katexBoot\(function \(\) \{ typesetSync\(node\); \}\);/.test(SRC));
ok("有源码级缓存 TEXC（流式每帧重贴 innerHTML，不缓存要排上百遍）", /var TEXC = \{\};/.test(SRC) && /TEXC\[ck\] = window\.katex\.renderToString/.test(SRC));
ok("paint 里排版排在贴 innerHTML 之后、scrollBottom 之前（同一任务 ⇒ 不闪）",
   /cell\.a\.innerHTML = mdRender\(answer\) \+ "<span class='cur'>▊<\/span>";\n\s+typesetSync\(cell\.a\);[\s\S]{0,120}\n\s+if \(stick\) scrollBottom\(\);/.test(SRC));
ok("send 一开头就预热 KaTeX（不是等定稿再拉 275KB）",
   /function send\(forceQ\) \{[\s\S]{0,400}try \{ katexBoot\(function \(\) \{\}\); \} catch \(e\) \{\}/.test(SRC));
ok("定稿后 1.2 秒补排一刀（兜 katex 未到位 / MATH 被下一次渲染重置）",
   /cell\.mathRetry = setTimeout\(function \(\) \{ typeset\(cell\.a\); \}, 1200\);/.test(SRC));
ok("补刀前先清掉上一颗定时器（重答/切版本不叠加）", /if \(cell\.mathRetry\) clearTimeout\(cell\.mathRetry\);/.test(SRC));
ok("异步回调里不拿 MATH 下标猜式子（有 textContent 兜底）",
   /var src = it \? it\.s : String\(e\.textContent \|\| ""\)/.test(SRC));
ok("自托管 KaTeX 仍排第一顺位", /KTX_HOSTS = \["\/assets\/katex"/.test(SRC));
ok("装不上就保持 $…$ 原样（不假装渲染过）", /if \(!window\.katex\) return els\.length;/.test(SRC));

console.log((fail ? "✗" : "✓") + " sim_chatsde_mathlive: " + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
