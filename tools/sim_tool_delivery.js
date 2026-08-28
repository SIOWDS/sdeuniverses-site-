/* 工序交付审计守门：tools/sim_tool_delivery.js（2026-08-28）
 * 守的是这一刀的四件承重物，每一件都**真跑**，不靠源码串：
 *   ① TOOL_SPEC 与白名单同集、每道都有可判的件、正则在 JS 里编得出来；
 *   ② wdsToolSys 真的下发「长度解除 + 必交件」（少一样，这一刀等于没做）；
 *   ③ 工序块排在《站内资料》之后（原来夹在中段，被上万字语料埋掉）；
 *   ④ 前端 toolAudit 拿同一份规格真扫两份稿子：做全的判过、少件的逐件点名。
 * 用法：node tools/sim_tool_delivery.js
 */
"use strict";
const fs = require("fs");
let PASS = 0, FAIL = 0;
function ok(m, c) { if (c) { PASS++; console.log("  PASS " + m); } else { FAIL++; console.log("  FAIL " + m); } }

const W = fs.readFileSync("src/worker.js", "utf8");
const F = fs.readFileSync("public/wds-mode.js", "utf8");

/* ── 把服务端那一段抠出来真跑（不复制代码：复制一份就会有一天两份不一样） ── */
const a = W.indexOf("const _LN = ");
const b = W.indexOf("\nfunction wdsToolSys(tool, prof) {");
const c = W.indexOf("\n// RESEARCH_STEP", b);
const nineA = W.indexOf("const NINE_CELLS = {");
const nineB = W.indexOf("const WDS_TOOLS = {");
const toolsA = nineB, toolsB = a;
const SRC = W.slice(nineA, nineB) + W.slice(toolsA, toolsB) + W.slice(a, c)
  + "\nreturn { TOOL_SPEC, wdsToolSys, toolNeedBlock, WDS_TOOLS, WDS_TOOLS_LANG };";
let S;
try { S = new Function(SRC)(); } catch (e) { console.log("  FAIL 服务端段抠不出来：" + e.message); process.exit(1); }

const KEYS = ["iq", "three", "motif", "nbr", "rename", "gap", "collide", "forge", "what", "how", "why", "grid", "nine", "map", "genesis"];

console.log("① 规格表齐全、每一件都判得动");
const mKeys = W.match(/const WDS_TOOL_KEYS = \[([^\]]+)\]/);
KEYS.forEach((k) => ok("TOOL_SPEC 有 " + k, !!S.TOOL_SPEC[k]));
ok("规格表不多不少（与白名单同集）", Object.keys(S.TOOL_SPEC).length === KEYS.length
  && Object.keys(S.TOOL_SPEC).every((k) => mKeys[1].includes('"' + k + '"')));
KEYS.forEach((k) => {
  const sp = S.TOOL_SPEC[k];
  ok(k + " 有字数地板", typeof sp.min === "number" && sp.min >= 200);
  ok(k + " 有 ≥3 件交付件", sp.items && sp.items.length >= 3);
  let bad = "";
  (sp.items || []).forEach((it) => {
    if (!it.k) bad = "件名空";
    try { new RegExp(it.re, "g"); } catch (e) { bad = "正则编不出：" + it.re; }
    if (/\(\?<[=!]/.test(it.re)) bad = "用了后向断言（旧 Safari 当场抛错）";
  });
  ok(k + " 每件都有件名、正则编得出、无后向断言" + (bad ? "（" + bad + "）" : ""), !bad);
});

console.log("② 下发的三样：长度解除 · 必交件 · 口吻尾注");
KEYS.filter((k) => k !== "iq").forEach((k) => {
  const out = S.wdsToolSys(k, null);
  ok(k + " 明写解除《怎么答》第 5 条", /当轮解除/.test(out) && /第 5 条/.test(out));
  ok(k + " 带字数地板 " + S.TOOL_SPEC[k].min, out.indexOf("下限约 " + S.TOOL_SPEC[k].min + " 字") >= 0);
  ok(k + " 必交件逐件列出（" + S.TOOL_SPEC[k].items.length + " 件）",
    S.TOOL_SPEC[k].items.every((it) => out.indexOf(it.k) >= 0));
  ok(k + " 交不出要写出来（不是跳过）", /这一件交不出/.test(out));
});
ok("尾注仍在（口吻不变，长度与交付件按工序来）",
  /工序只管这一轮要交付什么/.test(S.wdsToolSys("three", null)) && /不受《怎么答》第 5 条约束/.test(S.wdsToolSys("three", null)));
ok("iq 不下发必交件块（它整段改道 WDS_IQ_SYS），但规格仍在表里供审计",
  !!S.TOOL_SPEC.iq && /tool === "iq"/.test(W));
ok("档案没开的那一道仍然一个字不下发", S.wdsToolSys("genesis", { tools: ["iq", "three"] }) === "");
ok("带术语闸而无改姓版的那几道会挂回退提醒",
  /成品里一个都不许出现/.test(S.wdsToolSys("collide", { term: "x", tools: ["collide"] }))
  && !/成品里一个都不许出现/.test(S.wdsToolSys("three", { term: "x", tools: ["three"] })));

console.log("③ 位置：工序压在所有材料之后");
const sysSeg = W.slice(W.indexOf("function WDS_CHAT_SYS("), W.indexOf("// ===== SDE 词义查询扩展"));
const pSite = sysSeg.indexOf("【站内资料");
const pTool = sysSeg.indexOf("+ wdsToolSys(tool");
const pDoc = sysSeg.indexOf("【读者带来的文件");
ok("wdsToolSys 拼进 system", pTool > 0);
ok("工序排在《站内资料》之后（原来在它前面，被上万字语料埋掉）", pTool > pSite);
ok("工序也排在附件之后", pTool > pDoc);
ok("产线/深度研究跟着一起挪到末尾", sysSeg.indexOf("wdsForgeSys(rs)") > pSite);

console.log("④ 料：近邻走站外链，碰撞走分歧向召回");
ok("近邻工序接进占位者专用链", /tool === "nbr"/.test(W.slice(W.indexOf("const wantNbrG"), W.indexOf("const wantNbrG") + 300)));
ok("评分那一路的判据没被动过（两处 sim 钉着它）",
  /const wantNbr = \(rs && rs\.forge && FORGE_NBR_STAGES\[rs\.i \| 0\]\) \|\| tool === "iq"/.test(W));
ok("近邻工序正文交代了「拿不到就写未核验」", /站外占位者：未核验/.test(W));
ok("碰撞加了分歧向检索词", /if \(tool === "collide"\) expTerms\.push/.test(W));
ok("碰撞仍然加宽召回面", /wide = deep \|\| tool === "collide"/.test(W));
ok("规格随流下发给前端", /t: "toolspec"/.test(W) && /toolspec/.test(F));

/* ── 把前端审计抠出来真跑 ── */
const fa = F.indexOf("  function toolAudit(text, spec) {");
const fb = F.indexOf("  function toolAuditRender(cell, text, spec) {");
const FSRC = F.slice(fa, fb) + "\nreturn { toolAudit };";
let FE;
try { FE = new Function(FSRC)(); } catch (e) { console.log("  FAIL 前端审计抠不出来：" + e.message); process.exit(1); }

console.log("⑤ 前端审计真跑：做全的放行，少件的逐件点名");
// 一份「三视角」做全了的稿子（照规格的五件写）
const good3 = [
  "显露这一刀：它当下呈现成一个可辨认的单位……",
  "差异这一刀：它从一处落差里长出来，第三步不可逆……",
  "纠缠这一刀：抽掉考核这一根它就散……",
  "互相校正：显露那一刀看漏了时间，差异那一刀看错了主语。",
  "最脆的一环：判据落不到具体读数上。",
].join("\n") + "正文".repeat(500);
let r = FE.toolAudit(good3, S.TOOL_SPEC.three);
ok("做全的：零缺件", r.miss.length === 0 && r.done === 5);
// 少两件：删掉互消与最脆
const bad3 = good3.split("\n").slice(0, 3).join("\n") + "正文".repeat(500);
r = FE.toolAudit(bad3, S.TOOL_SPEC.three);
ok("少件的：抓得出，且点得出是哪两件", r.miss.length === 2
  && r.miss.join("｜").indexOf("互相校正") >= 0 && r.miss.join("｜").indexOf("最脆") >= 0);
ok("已交的件仍如实计数", r.done === 3);
// 字数：短稿要判短
r = FE.toolAudit("显露…\n差异…\n纠缠…\n互消…\n最脆…", S.TOOL_SPEC.three);
ok("被截短的稿子字数读数拿得到", r.len < S.TOOL_SPEC.three.min * 0.7 && r.min === S.TOOL_SPEC.three.min);
// 结构图那道：认围栏与关系动词
const goodMap = "```mermaid\nflowchart TD\nA -->|约束| B\nB -->|反过来锁死| A\n```\n这张图最承重的是那条锁死边；不确定的是 A→B；抽掉 B 整张图就散。";
r = FE.toolAudit(goodMap, S.TOOL_SPEC.map);
ok("结构图：围栏＋关系动词＋图下三句，零缺件", r.miss.length === 0);
r = FE.toolAudit("我给你描述一下这张结构图：A 约束 B，B 又锁死 A。", S.TOOL_SPEC.map);
ok("只用文字描述结构图 ⇒ 当场判未交付", r.miss.length >= 2);
// 发生场：候选四行要数得出条数
const gen = ["摆料：站内说法与站外占位者……", "对阵：甲与乙不能同时成立；共同假定……"]
  .concat([1, 2, 3].map((i) => "候选：X 不是 Y，而是 Z" + i + "\n分岔：与某家从第二步分岔\n作废：若观察到 W" + i + "\n张力源：第二步那一场对阵"))
  .concat(["〔交账〕3 条候选（自淘 0、带作废 3）"]).join("\n");
r = FE.toolAudit(gen, S.TOOL_SPEC.genesis);
ok("发生场：四行行首各数到 3 条，零缺件", r.miss.length === 0);
const gen2 = gen.replace(/\n作废：[^\n]*/g, "");
r = FE.toolAudit(gen2, S.TOOL_SPEC.genesis);
ok("发生场：抽掉「作废」行 ⇒ 只报这一件缺", r.miss.length === 1 && r.miss[0].indexOf("作废") >= 0);
// 近邻：库外三个年份
r = FE.toolAudit("本文所属学科：教育学\n近邻检测\n站内：《甲》分离线……\n库外：Smith 1998 分离线……对照预测……", S.TOOL_SPEC.nbr);
ok("近邻：只给一个年份一条分离线 ⇒ 判缺（要三个）", r.miss.length >= 2);
// 正则跑不动时不冒充查过
r = FE.toolAudit("随便一段话", { min: 100, items: [{ k: "坏正则", re: "(" }, { k: "好件", re: "随便" }] });
ok("坏正则跳过、不冒充查过（既不算交付也不算缺件）", r.miss.length === 0 && r.done === 1 && r.total === 2);

console.log("⑥ 前端接线（收规格 → 答完就扫 → 贴进正文）");
ok("SSE 收 toolspec", /j\.t === "toolspec"/.test(F));
ok("每轮独立的规格容器（不跨轮沿用）", /var toolSpec = null;/.test(F));
ok("finish 里调审计", /toolAuditRender\(cell, answer, toolSpec\)/.test(F));
ok("审计贴进 .wdsm-a（写在正文里，导出 PDF 才带得走）", /cell\.a\.appendChild\(d\)/.test(F.slice(F.indexOf("function toolAuditRender"))));
/* ⚠ 判文案/判「有没有某样东西」的断言要**先剥注释**——注释里必然引到那个名字，
   扫整份源码就是自伤（本仓同型坑第四次）。只剥块注释，够用且不会误伤字符串里的 // 。 */
const F_CODE = F.replace(/\/\*[\s\S]*?\*\//g, "");
ok("前端不留规格副本（唯一来源在服务端）", !/TOOL_SPEC/.test(F_CODE));
ok("停下来的那一轮不判缺件（它本来就没写完）", /if \(toolSpec && !stoppedByUser\)/.test(F));

console.log("\n" + (FAIL ? "✗ " : "✓ ") + PASS + " PASS / " + FAIL + " FAIL\n");
process.exit(FAIL ? 1 : 0);
