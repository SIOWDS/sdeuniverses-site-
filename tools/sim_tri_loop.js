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

console.log("① 环一与环六已撤（2026-09-14 当日撤回，账记在这里）");
/* ⚠ 按用意重写，不是删。撤的理由要留住，否则半年后有人照着「六环」四个字又装一遍：
   环一（押注卡）与环六（对账行）是六环里唯二真正压在基底身上的两件，而它们上线当天
   一次都没被真跑过——线上那一轮跑的还是旧规格（件名里没有「段首标明维名」），
   贴回来的稿只到①，环三的尺子直接返回 null。零数据。
   同时它们已经先付出两笔代价：① 押注卡预先喂饱了只认关键词的判据，害三段那三件当天改坏两次；
   ② 它们是在一道**第 1 件都还没交付**的工序上再加第 8、第 9 件（线上实测 9 件只交 3 件、845 字）。
   ⇒ 先撤，留环三（两把程序尺子：不占基底一个字、不多一次调用，纯测量）。
   要重装，先跑那个最小 A/B：同题四臂（旧版／加厚版／加厚+环一六／加厚但砍到 5 件），只数交付件数。 */
const T2 = String(S.WDS_TOOLS.three);
ok("正文里没有押注卡（环一已撤）", !/押注/.test(T2));
ok("正文里没有对账行（环六已撤）", !/对账/.test(T2));
ok("规格里没有那两件", !S.TOOL_SPEC.three.items.some((x) => /押注卡|对账/.test(x.k)));
ok("字数下限跟着回到 1600（两件撤了，篇幅要求也要跟着撤）", S.TOOL_SPEC.three.min === 1600);
ok("加厚本身保留（正文仍在千字以上，不是退回原来的 259 字）", T2.length > 900);
ok("反例带保留", /这样写＝没做/.test(T2));
ok("做不到就直说的出口保留", /直说/.test(T2));

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
  ok("工序正文明令段首照抄维名（判据与指令必须同源）", /段首各自照抄一次维名/.test(T2));
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
/* 押注读数随环一环六一起休眠：样本里还留着那两行，所以这里仍量得到；
     线上正文已不再要求它，读数为 0 时前端那一段自会不显示。 */
  ok("押注读数仍量得到（样本里留着那两行；线上正文已不再要求）", r.bets === 3 && r.hits === 2 && !r.allHit);

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
