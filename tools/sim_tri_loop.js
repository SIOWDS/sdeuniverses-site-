/* 三角互消闭环护栏：tools/sim_tri_loop.js（2026-09-14 试点）
 *
 * 守的是 three 这一道被改成「猜想—执行—评估—反馈—修改—迭代」之后新加的那两层：
 *   ① 环一（押注卡）与环六（对账行）在下发的工序正文里，且交付件数得出来；
 *   ② 环三的两把程序尺子（三段独立度 / 互消句复述度 / 押注全中）**真跑**：
 *      好稿不误报、三种坏稿各自当场见红。
 *
 * 这两把尺子是本仓第一次不靠正则、而靠**重叠率**去判「有没有真做」，
 * 所以变异检验尤其要紧：阈值调松、段落抠法改错、押注全中那一条删掉——每一样都必须当场红。
 * 用法：node tools/sim_tri_loop.js
 */
"use strict";
const fs = require("fs");
let PASS = 0, FAIL = 0;
function ok(m, c) { if (c) { PASS++; console.log("  PASS " + m); } else { FAIL++; console.log("  FAIL " + m); } }

const W = fs.readFileSync("src/worker.js", "utf8");
const F = fs.readFileSync("public/wds-mode.js", "utf8");

/* ── 服务端：工序正文与规格抠出来真跑 ── */
const a = W.indexOf("const _LN = ");
const c = W.indexOf("\n// RESEARCH_STEP", a);
const nineA = W.indexOf("const NINE_CELLS = {");
const toolsA = W.indexOf("const WDS_TOOLS = {");
const SRC = W.slice(nineA, toolsA) + W.slice(toolsA, a) + W.slice(a, c)
  + "\nreturn { TOOL_SPEC, WDS_TOOLS, toolSpecFor };";
let S;
try { S = new Function(SRC)(); } catch (e) { console.log("  FAIL 服务端段抠不出来：" + e.message); process.exit(1); }

/* ── 前端：两把尺子抠出来真跑（不复制代码：复制一份就会有一天两份不一样） ── */
const fa = F.indexOf("  function triGram(s, k) {");
const fb = F.indexOf("  function triEchoRender(cell, text) {");
let FE;
try { FE = new Function(F.slice(fa, fb) + "\nreturn { triEcho, triGram, triJac, triCover };")(); }
catch (e) { console.log("  FAIL 前端尺子抠不出来：" + e.message); process.exit(1); }

console.log("① 六环写进了工序正文");
const T = String(S.WDS_TOOLS.three);
ok("环一·押注卡在正文里", /环一/.test(T) && /押注一/.test(T) && /押注二/.test(T) && /押注三/.test(T));
ok("押注卡明写「写在三段之前」且不许回头改", /三段一个字都还没写之前/.test(T) && /不许回头改/.test(T));
ok("押偏不扣分、押中也不加分（否则它会变成一道讨好题）", /押偏不扣分/.test(T) && /押中也不加分/.test(T));
ok("环六·对账行在正文里", /环六/.test(T) && /对账：押注一/.test(T));
ok("三条全押中要自报「动笔前就想完了」", /全押中/.test(T) && /没有独立跑过/.test(T));
ok("环一排在①之前（封条写在后面就不是封条了）", T.indexOf("押注一") < T.indexOf("① 只从"));
ok("环六排在⑤之后", T.indexOf("对账：押注一") > T.indexOf("⑤ 最脆一环"));

console.log("② 两件新交付件数得出来");
const items = S.TOOL_SPEC.three.items.map((x) => x.k);
ok("规格里有押注卡那一件", items.some((k) => /押注卡/.test(k)));
ok("规格里有对账那一件", items.some((k) => /对账/.test(k)));
ok("押注卡要数满三行", S.TOOL_SPEC.three.items.some((x) => /押注卡/.test(x.k) && x.n === 3));
ok("对账要逐条报（三次）", S.TOOL_SPEC.three.items.some((x) => /对账/.test(x.k) && x.n === 3));
ok("两件都配了英文件名与英文判据", S.TOOL_SPEC.three.items.filter((x) => /押注卡|对账/.test(x.k)).every((x) => x.ke && x.en));

console.log("②之二 三段判据的四态真跑（这三件今天改坏过两次，钉死在这里）");
{
  const it = S.TOOL_SPEC.three.items.filter((x) => /只从显露/.test(x.k))[0];
  const hit = function (t) { return new RegExp(it.re, "g").test(t); };
  ok("标准写法「① 只从显露看：…」判交付", hit("押注一：x\n① 只从显露看：沉默呈现成一段没有人说话的时长。"));
  ok("自定标题＋段内标明维名 也判交付（第二版收紧时这里出过假阴性）",
     hit("押注一：x\n① 先看教育最后留下的可辨认单位\n只从显露这一维看：至少有六种单位。"));
  ok("只有押注卡、三段一字未写 ⇒ 判未交付（第一版被它喂饱过）",
     !hit("押注一：三段里会被判错的是显露与纠缠两段，各错在什么上"));
  ok("写了三段却通篇不标维名 ⇒ 判未交付（工序正文已明令段首照抄维名）",
     !hit("① 先看教育最后留下的可辨认单位\nAI进入课堂后，眼前能数清的成果不再只有一份终稿。"));
  ok("正则里的 [\\s\\S] 没被 JS 字符串转义吃成 [sS]（写少一层反斜杠就会）", it.re.indexOf("[\\s\\S]") >= 0);
  ok("工序正文明令段首照抄维名（判据与指令必须同源）", /段首各自照抄一次维名/.test(T));
}

console.log("③ 环三两把尺子真跑：好稿不误报");
/* 一份三段真独立的答（题材统一取「课堂上的沉默」，与 sim_tool_each 同题，便于对读）。 */
const GOOD = [
  "押注一：会被判错的是第一段与第三段。押注二：形状大概是「沉默不是一段时长，而是一段没有责任人的时间」。押注三：最脆的一环大概押在责任人可数这个假定上。",
  "① 只从显露看：它显影出来的可辨认单位是一段没有人说话的时长，边界是上一句的句末与下一句的开头，到后排学生也停下动作才算成形。",
  "② 只从差异看：它从一次提问与一次不作答的落差里长出来，路径是提问、扫视、点名，点名那一步过了就回不去。",
  "③ 只从纠缠看：它与座位表、评分办法、录像设备缠在一起，逐根试抽，抽掉评分办法它就散，抽掉录像它只是换个样子。",
  "④ 互相校正：第一段写的是「边界是上一句的句末与下一句的开头」，它按钟表划边界，于是把等长而性质相反的两段收进同一个名下；第三段写的是「抽掉评分办法它就散」，它把制度当成缠绕物，其实制度改的是这件事记在谁头上。互消之后剩下：沉默不是一段时长，而是一段没有责任人的时间。",
  "⑤ 最脆一环：这条判断押在责任人能落到可数对象上；若课堂记录里始终没有这一栏，它就从第一句开始倒。",
  "对账：押注一〔押中〕· 押注二〔押中〕· 押注三〔押偏〕",
].join("\n");
let r = FE.triEcho(GOOD);
ok("好稿抠得出五段（抠不出就返回 null，不冒充算过）", !!r);
ok("好稿三段独立度都在 25% 以下（实得 " + r.ind.map((x) => Math.round(x * 100) + "%").join("/") + "）", !r.dup);
ok("好稿互消句复述度在 50% 以下（实得 " + Math.round(r.echo * 100) + "%）", !r.rep);
ok("好稿押注读数对（3 条、2 中）", r.bets === 3 && r.hits === 2 && !r.allHit);

console.log("④ 三种坏稿各自当场见红");
/* 坏稿甲：三段是同一套话换三个标题——这道工序唯一的、也最难被事后发现的失败方式。 */
const SAME = "只从显露看：沉默是一段没有人说话的时长，它由评分办法与座位表共同撑住，从提问到点名一步步长成这样。";
const BAD_DUP = [
  "押注一：会被判错的是第一段与第三段。押注二：形状大概是「沉默不是时长，而是无主时间」。押注三：押在可数这个假定上。",
  "① " + SAME, "② " + SAME, "③ " + SAME,
  "④ 互相校正：三段互为补充，共同构成完整图景。互消之后剩下：沉默是一段没有人说话的时长。",
  "⑤ 最脆一环：可数。",
  "对账：押注一〔押中〕· 押注二〔押中〕· 押注三〔押中〕",
].join("\n");
r = FE.triEcho(BAD_DUP);
ok("三段同一套话 ⇒ 独立度见红（实得 " + r.ind.map((x) => Math.round(x * 100) + "%").join("/") + "）", r.dup);
ok("三条押注全中 ⇒ 见红（结论在动笔前就有了）", r.allHit);

/* 坏稿乙：互消句其实是第②段的原话——最常见的"看起来撞出来了"。 */
const BAD_REP = [
  "押注一：会被判错的是第一段与第三段。押注二：形状待定。押注三：押在可数上。",
  "① 只从显露看：它显影出来的可辨认单位是一段没有人说话的时长，边界是上一句的句末与下一句的开头。",
  "② 只从差异看：它从一次提问与一次不作答的落差里长出来，路径是提问扫视点名，点名那一步过了就回不去。",
  "③ 只从纠缠看：它与座位表、评分办法、录像设备缠在一起，抽掉评分办法它就散。",
  "④ 互相校正：第一段看漏了性质，第三段看错了层。互消之后剩下：它从一次提问与一次不作答的落差里长出来，路径是提问扫视点名，点名那一步过了就回不去。",
  "⑤ 最脆一环：押在可数上。",
  "对账：押注一〔押中〕· 押注二〔押偏〕· 押注三〔押偏〕",
].join("\n");
r = FE.triEcho(BAD_REP);
ok("互消句抄第②段 ⇒ 复述度见红（实得 " + Math.round(r.echo * 100) + "%）", r.rep);
ok("这一份的三段本身仍判独立（只红该红的那一条）", !r.dup);

/* 坏稿丙：段落标记缺失 ⇒ 返回 null，而不是拿半份文本硬算。 */
ok("缺段落标记 ⇒ 返回 null，不冒充算过", FE.triEcho("显露…差异…纠缠…互消…最脆…") === null);
ok("空文本 ⇒ 返回 null", FE.triEcho("") === null);

console.log("⑤ 接线：尺子真的被调用，且只在 three 这一道调");
ok("成文收尾处调了 triEchoRender", /triEchoRender\(cell, answer\)/.test(F));
ok("只对 three 这一道调（别道不误挂）", /toolSpec\.k === "three"/.test(F));
ok("包在 try 里（尺子自己出错不许把整答带走）", /try \{ triEchoRender/.test(F));
ok("读数贴进 .wdsm-a（不贴正文里，导出 PDF 就带不走）", /cell\.a\.appendChild\(d\)/.test(F.slice(F.indexOf("function triEchoRender"))));

console.log("⑥ 变异检验：每一条都该当场红");
function mut(src, from, to) { return new Function(src.replace(from, to) + "\nreturn { triEcho };")(); }
const FSRC = F.slice(fa, fb);
{ const M = mut(FSRC, "> 0.25", "> 0.99");
  /* 坏稿甲的实测重叠是 95.5%，所以阈值要调到 99% 才漏得掉——这条断言本身也是一次读数：
     真正的"三段换三个标题"重叠在 95% 这一带，25% 的线留了很大余量。 */
  ok("把独立度阈值调松到 99% ⇒ 坏稿甲漏网（它的实测重叠是 " + Math.round(Math.max.apply(null, FE.triEcho(BAD_DUP).ind) * 100) + "%）", !M.triEcho(BAD_DUP).dup); }
{ const M = mut(FSRC, "> 0.5", "> 0.99");
  ok("把复述度阈值调松到 99% ⇒ 坏稿乙漏网", !M.triEcho(BAD_REP).rep); }
{ const M = mut(FSRC, "bets >= 3 && hits >= 3", "false");
  ok("删掉「三条全押中」那一条 ⇒ 坏稿甲的那条读数没了", !M.triEcho(BAD_DUP).allHit); }
{ const M1 = mut(FSRC, "triGram(x, 4)", "triGram(x, 1)");
  /* ⚠ 第一版这条写成「单字窗 ⇒ 好稿被误报」，实跑不红：好稿在单字窗下也只到 17%，还在 25% 线内。
     红不了不等于窗口大小无所谓——它把独立稿的读数抬了一个数量级（0% → 17%），
     再长一点的稿子就会翻线。所以这条按实测改成守**信噪比**：窗口改小，好稿与坏稿的距离必须显著缩短。 */
  const g4 = Math.max.apply(null, FE.triEcho(GOOD).ind), g1 = Math.max.apply(null, M1.triEcho(GOOD).ind);
  ok("四字窗改成单字窗 ⇒ 好稿底噪从 " + Math.round(g4 * 100) + "% 抬到 " + Math.round(g1 * 100) + "%（窗太小，汉字本来就共用）",
     g1 > g4 + 0.1); }
{ const M = mut(FSRC, "if (pos[i] < 0 || (pos[i + 1] >= 0 && pos[i + 1] < pos[i])) return null;", "if (false) return null;");
  let crashed = false, got = null;
  try { got = M.triEcho("显露…差异…纠缠…"); } catch (e) { crashed = true; }
  ok("去掉「抠不出就返回 null」 ⇒ 要么炸、要么拿半份文本硬算出一个假读数", crashed || (got && !isNaN(got.echo))); }

console.log("\n" + (FAIL ? "✗ " : "✓ ") + PASS + " PASS / " + FAIL + " FAIL");
process.exit(FAIL ? 1 : 0);
