#!/usr/bin/env node
/* 三道问对（What/How/Why 问对）的接力护栏 · 2026-09-08
   王德生令：「不断地追问，进入 SDE 更广和更深的关联，就是三方程、六路径、三原理的层层深入。
   对 What 是三方程的层层深入，对 How 是六路径的，对 Why 是三原理的。」
   同日另一句定调：「平的就是深度，即 SDE 的维度扩张；通常的『深度』其实是形式逻辑。」
   ⇒ 这里验的是：下一格是**服务端算出来的**（换一条方程／换一个起手维／换一条原理），
     不是让基底"再深入一点"自由发挥。

   做法：从 src/worker.js 抠原文 eval（不复制一份代码，复制的那份对了不算数）。
   变异检验：改坏 posNext 的任一条规则，本脚本应当变红。 */
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.resolve(__dirname, "..");
const W = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");
const M = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");
let PASS = 0, FAIL = 0;
const ok = (c, m, x) => { if (c) { PASS++; console.log("  ✓ " + m); } else { FAIL++; console.log("  ✗ " + m + (x ? "  ← " + x : "")); } };

function grab(a, b) { const i = W.indexOf(a), j = W.indexOf(b, i); if (i < 0 || j < 0) throw new Error("找不到 " + a); return W.slice(i, j); }
const SB = new Function(grab("const POS_RE =", "/* 兜底三问") + "\nreturn { posParse, posNext, posFromHistory, PROBE_TOOLS, posSeq, TOOL_SEQ };")();

console.log("① 落位行解析（三列各一）");
{
  const a = SB.posParse("正文若干\n〔落位〕列：What ｜ 位：S=F(D,E) ｜ 给定：E、D ｜ 已解释：S\n〔交账〕…");
  ok(a && a.col === "What" && /S=F/.test(a.pos) && /E/.test(a.given), "What 行解出列、位、给定", JSON.stringify(a));
  const b = SB.posParse("〔落位〕列：How ｜ 位：D→S→E ｜ 起手：D ｜ 落点：E");
  ok(b && b.col === "How" && b.from === "D" && b.to === "E", "How 行解出起手与落点", JSON.stringify(b));
  const c = SB.posParse("〔落位〕列：Why ｜ 位：原理一 D×E→S ｜ 结果项：S");
  ok(c && c.col === "Why" && c.res === "S", "Why 行解出结果项", JSON.stringify(c));
  ok(SB.posParse("一行落位都没有的答案") === null, "没有落位行就回 null（不许瞎猜）");
  ok(SB.posParse("〔落位〕列：随便 ｜ 位：x") === null, "认不出列就回 null");
}

console.log("② ⭐ 下一格是算出来的 —— What：把给定项提为待解释项");
{
  const r = SB.posNext({ col: "What", pos: "S=F(D,E)", given: "E、D", done: "S" });
  ok(/E=H\(S,D\)/.test(r), "上一答把 E 当给定 ⇒ 下一轮换 E=H(S,D)", r);
  ok(/不许绕回/.test(r) && /S=F\(D,E\)/.test(r), "并写死不许绕回上一条方程重讲");
  const r2 = SB.posNext({ col: "What", pos: "E=H(S,D)", given: "D", done: "E" });
  ok(/D=G\(S,E\)/.test(r2), "给定换成 D ⇒ 换 D=G(S,E)", r2);
  ok(SB.posNext({ col: "What", pos: "S=F(D,E)", given: "" }) === "", "没报给定项就不指定（空串＝这一轮不指定）");
}

console.log("③ ⭐ How：上一条的落点维就是下一条的起手维（首尾相衔）");
{
  const r = SB.posNext({ col: "How", pos: "D→S→E", from: "D", to: "E" });
  ok(/【本轮的起手维】E/.test(r), "落点 E ⇒ 下一条从 E 起手", r);
  ok(/未推进/.test(r), "换一条不相衔的路径判为未推进");
  const r2 = SB.posNext({ col: "How", pos: "E→D→S", from: "E", to: "S" });
  ok(/【本轮的起手维】S/.test(r2), "落点 S ⇒ 从 S 起手", r2);
  ok(SB.posNext({ col: "How", from: "D", to: "" }) === "", "没报落点就不指定");
}

console.log("④ ⭐ Why：上一次的结果项成为下一次矛盾的一端（原理链传动）");
{
  const r = SB.posNext({ col: "Why", pos: "原理一 D×E→S", res: "S" });
  ok(/S×E→D/.test(r) && /S×D→E/.test(r), "推动了 S ⇒ 下一轮 S 必须作为矛盾一端出现", r);
  ok(!/D×E→S/.test(r.split("——")[0]), "不许把刚走过的那条原理再指一遍", r);
  const r2 = SB.posNext({ col: "Why", pos: "原理二 S×E→D", res: "D" });
  ok(/D×E→S/.test(r2) && /S×D→E/.test(r2), "推动了 D ⇒ 下一轮 D 作为矛盾一端", r2);
  ok(SB.posNext({ col: "Why", res: "" }) === "", "没报结果项就不指定");
  ok(SB.posNext(null) === "", "没有落位就不指定");
}

console.log("⑤ 接力取的是最近一条带落位的答复（中间插几句闲话不影响）");
{
  const h = [
    { role: "user", text: "问一" },
    { role: "wds", text: "答一\n〔落位〕列：How ｜ 位：S→D→E ｜ 起手：S ｜ 落点：E" },
    { role: "user", text: "顺口问一句别的" },
    { role: "wds", text: "一句闲答，没有落位行" },
  ];
  const p = SB.posFromHistory(h, "How");
  ok(p && p.to === "E", "越过没有落位的那一答，接住上一条真落位", JSON.stringify(p));
  ok(SB.posFromHistory(h, "Why") === null, "别的列不许拿 How 的落位来接");
  ok(SB.posFromHistory([], "How") === null, "空历史回 null");
}

console.log("⑥ 三道工序的接线（服务端）");
{
  ok(/whatq: "【本轮工序 · What 问对/.test(W), "whatq 工序正文在");
  ok(/howq: "【本轮工序 · How 问对/.test(W), "howq 工序正文在");
  ok(/whyq: "【本轮工序 · Why 问对/.test(W), "whyq 工序正文在");
  ["whatq", "howq", "whyq"].forEach((k) => {
    const seg = W.slice(W.indexOf("  " + k + ": \"【本轮工序"), W.indexOf("  " + k + ": \"【本轮工序") + 2600);
    ok(/〔落位〕/.test(seg), k + " 要求答末交〔落位〕行（接力全靠它）");
    ok(/若本轮已由上游指定/.test(seg), k + " 写明「上游指定了就照它走」（等的就是算出来的那一格）");
  });
  ok(/const PROBE_TOOLS = \{ whatq: "What", howq: "How", whyq: "Why" \};/.test(W), "三道与三列的对应表只有一份");
  ok(/function _rungOf\(tool, history\)/.test(W) && /wdsToolSys\(tool, prof, rung\)/.test(W),
    "接力格算好后挂进工序 system");
  ok(/sentryCtx, _rungOf\(tool, history\)[,)]/.test(W), "调用点真把它算出来传进去（不是留了个空参数）");
  ok(/const _rung = \(rung && PROBE_TOOLS\[tool\]\)/.test(W), "只有三道问对吃这一格，别的工序不受影响");
  // 必交件：〔落位〕行必须进机检面，否则漏了没人发现
  ["whatq", "howq", "whyq"].forEach((k) => {
    const seg = W.slice(W.indexOf("  " + k + ": { min:"), W.indexOf("  " + k + ": { min:") + 700);
    ok(/落位/.test(seg), k + " 的必交件里有〔落位〕行");
  });
}

console.log("⑦ 前端接线");
{
  ok(/k: "whatq", n: "tlWhatq"/.test(M) && /k: "howq"/.test(M) && /k: "whyq"/.test(M), "三道进了工序菜单");
  ok(/tlWhatq: "What 问对"/.test(M) && /tlWhatq: "What probe"/.test(M), "中英文案都有（少一边＝英文界面显示 undefined）");
  ok(/cmd: \["what问对", "whatq"/.test(M), "斜杠命令也认");
}

console.log("⑧ ⭐ 追问仍是 What/How/Why 三条 —— 2026-09-08 王德生定「保持原状，这样丰富材料」");
{
  ok(/三条必须各用一件不同的工具，恰好是一个 What、一个 How、一个 Why/.test(W), "追问的规矩没被问对改掉");
  ok(!/两深一广/.test(W.replace(/\/\*[\s\S]*?\*\//g, "")), "「两深一广」只许留在注释里的撤回记录，不许留在活代码里");
  ok(/function followSys\(prof\) \{/.test(W), "followSys 没有多出 probe 参数");
}

console.log("⑨ ⭐ 工序自己的序列 —— 2026-09-14 王德生令「工序应该有自己独特的序列，这个『接着问』要去掉」");
{
  // ── 真跑 posSeq：下一格是算出来的，连点下去发的那一问一起算 ──
  const a = SB.posSeq("whatq", "正文\n〔落位〕列：What ｜ 位：S=F(D,E) ｜ 给定：E、D ｜ 已解释：S");
  ok(a && !a.miss && /E=H\(S,D\)/.test(a.label) && /E/.test(a.send), "What：给定 E ⇒ 下一格 E=H(S,D)", JSON.stringify(a));
  const b = SB.posSeq("howq", "〔落位〕列：How ｜ 位：D→S→E ｜ 起手：D ｜ 落点：E");
  ok(b && !b.miss && /从 E 起手/.test(b.label), "How：落点 E ⇒ 下一条从 E 起手", JSON.stringify(b));
  const c = SB.posSeq("whyq", "〔落位〕列：Why ｜ 位：原理一 D×E→S ｜ 结果项：S");
  ok(c && !c.miss && /原理二|原理三/.test(c.label), "Why：结果项 S ⇒ 传到下一条原理", JSON.stringify(c));
  // ── 🔴 断链必须显形：这是这一道存在的主要理由（答案照样通顺，从前一点看不出来）──
  const m1 = SB.posSeq("whatq", "一段完全没有交落位行的正文。");
  ok(m1 && m1.miss === 1 && /〔落位〕/.test(m1.send) && /不要重写正文/.test(m1.send), "没交〔落位〕⇒ miss 1 并给补交的那一句", JSON.stringify(m1));
  const m2 = SB.posSeq("whatq", "〔落位〕列：What ｜ 位：S=F(D,E) ｜ 给定：其他因素 ｜ 已解释：S");
  ok(m2 && m2.miss === 2, "给定写成「其他因素」（抠不出 S/D/E）⇒ miss 2，不许硬给一格", JSON.stringify(m2));
  // ── 只有三道问对吃这条：别的工序拿不到序列帧 ──
  ok(SB.posSeq("nine", "〔落位〕列：What ｜ 给定：E") === null && SB.posSeq("book9", "x") === null,
     "非问对工序不出 seq 帧（九问专著的下一格在前端从〔进度〕行算）");

  // ── 名单：一轮交付完的工序不许进 TOOL_SEQ，否则「接着问」变成拖延 ──
  ok(SB.TOOL_SEQ.whatq && SB.TOOL_SEQ.howq && SB.TOOL_SEQ.whyq && SB.TOOL_SEQ.book9, "四道自带序列的工序都在表里");
  ok(!SB.TOOL_SEQ.what && !SB.TOOL_SEQ.how && !SB.TOOL_SEQ.why && !SB.TOOL_SEQ.nine && !SB.TOOL_SEQ.forge,
     "轻松版三道与九宫格/通融单轮版不在表里（它们一轮交付完就结束）");

  // ── 闸：走工序时不再配三条通用追问；没有工序照旧配 ──
  ok(/outText\.length > 150 && !rs && !TOOL_SEQ\[tool\]/.test(W), "自带序列的工序不再调 followUps（三条与那一格脱钩，点哪颗都走同一格）");
  ok(/outText\.length > 150 && !rs && PROBE_TOOLS\[tool\]/.test(W) && /t: "seq"/.test(W), "三道问对改发 seq 帧");
  ok(W.indexOf('!TOOL_SEQ[tool]') > W.indexOf('t: "seq"'), "seq 帧排在追问那一闸之前（两者互斥，先出算好的那一颗）");

  // ── 前端接线 ──
  ok(/function renderSeq\(cell, ansText, sq\)/.test(M), "前端有独立的序列条 renderSeq");
  ok(/j\.t === "seq"/.test(M) && /seqV = j\.v/.test(M), "seq 帧收得到");
  ok((M.match(/renderSeq\(cell, answer, seqV\);/g) || []).length === 2, "两条收尾路（正常结束与中断保底）都挂序列条");
  ok(/cell\.tool === "book9"/.test(M.slice(M.indexOf("function renderSeq"), M.indexOf("function renderFollows"))),
     "九问专著的主道钮已搬进 renderSeq");
  ok(!/nextChip/.test(M), "追问框里不再留主道钮与压暗逻辑（已搬走）");
  ok(/seqH: "这一道的下一步"/.test(M) && /seqH: "NEXT STEP IN THIS TRACK"/.test(M), "中英文案都有");
  ok(/seqMiss: "这一答没交〔落位〕行/.test(M), "断链那句话在前端也说破了，不只在帧里");
  // 🔴 词条在不等于它会被画出来：miss 分支必须活着（变异检验专设——上一版只验词条，改坏分支照样全绿）
  ok(/if \(sq\.miss\) \{ line = t\("seqMiss"\);/.test(M), "miss 分支真的会画出来（不是只有词条躺在表里）");
}

console.log("\n===== " + PASS + " PASS / " + FAIL + " FAIL =====");
process.exit(FAIL ? 1 : 0);
