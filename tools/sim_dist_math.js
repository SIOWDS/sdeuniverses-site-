/* sim_dist_math.js —— 成文那一路的【数学写法】护栏
 *
 * 缘起（2026-09-08 王德生令）：ChatSDE 的对话早就硬性要求基底写 LaTeX
 * （WDS_CHAT_SYS／WDS_PLAIN_SYS 各有一段【数学写法】），但**成文 · PPT** 这一路
 * （/api/wds/distill）的 system 里一直没有 ⇒ 一进成文，那条要求就没了，
 * 基底自由发挥，稿子里的式子写成键盘写法，预览与导出都排不出来。
 *
 * 这份护栏钉三件事：
 *   ① 分档必须存在：deck 出的是真 .pptx（wds-pptx.js 是纯文本 XML、没有 KaTeX）
 *      ⇒ 幻灯片档**禁止** LaTeX、改用 Unicode 符号；文章类才要 LaTeX。
 *   ② 文章档必须交代「中文写进 \text{}」——行内 $…$ 的汉字闸只放行花括号内的中文
 *      （见 sim_chatsde_mathlive「二之半」节），不说这一条，量具名照样排不出来。
 *   ③ 这一段必须真的挂进 BASE，且排在术语闸（prof.term）之前——术语闸必须留在最末。
 *
 * 跑法：node tools/sim_dist_math.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");
let pass = 0, fail = 0;
const ok = (n, c) => { if (c) { pass++; } else { fail++; console.log("  ✗ " + n); } };
const SRC = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");

/* ── 从真源码里抠出这个函数，别另写一份 ── */
const m = /function DIST_MATH_BLOCK\(kind, lang\) \{[\s\S]*?\n\}/.exec(SRC);
ok("抠得到 DIST_MATH_BLOCK", !!m);
const F = m ? new Function(m[0] + "; return DIST_MATH_BLOCK;")() : function () { return ""; };

const deck = F("deck", "zh"), art = F("paper", "zh");
const deckEn = F("deck", "en"), artEn = F("essay", "en");

/* ── 一 · 分档存在且方向相反 ── */
ok("deck 档禁止 LaTeX", /绝不要写/.test(deck) && deck.indexOf("LaTeX") >= 0);
ok("deck 档给 Unicode 符号", ["×", "÷", "≤", "≥", "√", "∑", "θ", "Δ"].every(c => deck.indexOf(c) >= 0));
ok("deck 档给上下标字符", deck.indexOf("²") >= 0 && deck.indexOf("₁") >= 0);
ok("deck 档说清理由（.pptx 排不了）", /pptx/i.test(deck));
ok("文章档要求 LaTeX", /一律用 LaTeX/.test(art));
ok("文章档给行内与块级两种定界符", art.indexOf("$…$") >= 0 && art.indexOf("$$…$$") >= 0);
ok("文章档禁止把公式放进代码块", /代码块/.test(art));
ok("两档口径相反（deck 不许、文章必须）", /绝不要写 \$…\$/.test(deck) && /行内式包在 \$…\$ 里/.test(art));

/* ── 二 · 文章档必须交代 \text{} 这条（否则量具名排不出来）── */
ok("文章档交代中文写进 \\text{}", art.indexOf("\\text{…}") >= 0 || art.indexOf("\\text{}") >= 0);
ok("文章档给了带中文的例子", /\\text\{拒收率\}|\\text\{增量\}/.test(art));
ok("文章档说明裸中文排不出来", /裸露的中文/.test(art));

/* ── 三 · 英文场两档都有 ── */
ok("en · deck 档也禁 LaTeX", /cannot typeset LaTeX/.test(deckEn));
ok("en · 文章档要求 LaTeX", /LaTeX/.test(artEn) && /KaTeX/.test(artEn));
ok("en · 文章档也交代 \\text{…}", artEn.indexOf("\\text{…}") >= 0);

/* ── 四 · 真的挂进 BASE，且在术语闸之前 ── */
const iCall = SRC.indexOf("DIST_MATH_BLOCK(kind, dlang)");
const iTerm = SRC.indexOf("术语闸必须留在最末");
ok("BASE 里调用了 DIST_MATH_BLOCK", iCall > 0);
ok("挂在术语闸之前（闸必须留在最末）", iCall > 0 && iTerm > 0 && iCall < iTerm);
ok("传的是 kind 不是写死的档", /DIST_MATH_BLOCK\(kind,/.test(SRC));

/* ── 五 · 幻灯片生成器确实没有 KaTeX（分档的前提，塌了就该重议）── */
const PPTX = fs.readFileSync(path.join(ROOT, "public/assets/wds-pptx.js"), "utf8");
ok("wds-pptx.js 里没有 KaTeX（分档前提成立）", !/katex/i.test(PPTX));

console.log((fail ? "✗" : "✓") + " sim_dist_math: " + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
