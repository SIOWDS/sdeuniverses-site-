/* 后端 SDE 工序守门（源码级断言）：tools/sim_wds_sde_tools.js
 * 守的是几件一旦漂掉就静默出错的事：
 *   ① 九道工序 key 齐、每道都有实体块，且每道都留了「做不到就直说」的出口；
 *   ② tool 走白名单（绝不能把读者传来的字符串拼进 system）；
 *   ③ 工序块真的拼进了 WDS_CHAT_SYS，且近邻名单**前置**在语料之前（否则被两万字语料埋掉）；
 *   ④ 满功率档的 max_tokens 仍然 ≤ 8000（老血案：满功率＋大预算＝只有思考、正文 0 字）。
 * 用法：node tools/sim_wds_sde_tools.js
 */
"use strict";
const fs = require("fs");
let PASS = 0, FAILS = 0;
function ok(c, m) { if (c) { PASS++; console.log("  PASS " + m); } else { FAILS++; console.log("  FAIL " + m); } }

const W = fs.readFileSync("src/worker.js", "utf8");
const F = fs.readFileSync("public/wds-mode.js", "utf8");

console.log("① 每道工序齐全且各有实体");
// 别写死数量：加一道工序就要改三处数字，这种断言迟早被人图省事删掉。跟着白名单走。
const KEYS = ["iq", "three", "motif", "nbr", "rename", "gap", "collide", "forge", "what", "how", "why", "grid", "nine", "map", "genesis"];
const mKeys = W.match(/const WDS_TOOL_KEYS = \[([^\]]+)\]/);
ok(!!mKeys, "WDS_TOOL_KEYS 存在");
KEYS.forEach((k) => ok(mKeys && mKeys[1].includes('"' + k + '"'), "白名单里有 " + k));
/* ⚠ 原来切到 wdsToolSys 为止，把 WDS_TOOLS_LANG 那六道也数了进来（14 应得 20，红了两条）。
   改姓版是另一张表，另有护栏（sim_wds_profile）盯它，这里只切通用那张。 */
const seg = W.slice(W.indexOf("const WDS_TOOLS = {"), W.indexOf("const WDS_TOOLS_LANG = {"));
KEYS.forEach((k) => ok(new RegExp("\\n  " + k + ":").test(seg), k + " 有工序正文"));
ok(/本轮工序/.test(seg) && (seg.match(/本轮工序/g) || []).length === KEYS.length, "每道都以「本轮工序」开头，应 " + KEYS.length + " 道，实得 " + (seg.match(/本轮工序/g) || []).length);
// 每道都要有「做不到就直说」的出口——工序最怕的不是做不到，是假装做到了
const bodies = seg.split(/\n  (?=[a-z]+:)/).slice(1);
ok(bodies.length === KEYS.length, "切出 " + KEYS.length + " 段工序正文，实得 " + bodies.length);
const OUT = /直说|不要编|别硬凑|说不足以|不许说|凑不满|凑不出|撑不起|就说用不上|会的话指出/;
bodies.forEach((b) => ok(OUT.test(b), (b.match(/^([a-z]+):/) || [0, "?"])[1] + " 留了「做不到就直说」的出口"));

console.log("② tool 走白名单");
ok(/WDS_TOOL_KEYS\.indexOf\(String\(b\.tool \|\| ""\)\) >= 0 \? String\(b\.tool\) : ""/.test(W),
   "认不出的 tool 一律当没选（不把读者传来的字符串拼进 system）");

console.log("③ 工序块拼进 system；近邻名单前置");
/* ⚠ 这条原来把**整串形参**抄进正则，加一个参数就假红（2026-08-21 加 prof 时又红了一次，
   本仓同型坑第三次）。按用意重写：只认函数名，且形参表里有 tool。
   再补一条「收了却不用」——签名有、正文一处没用，才是真正会静默失效的那种坏法。 */
const _csSig = /function WDS_CHAT_SYS\(([^)]*)\)/.exec(W);
ok(!!_csSig && /\btool\b/.test(_csSig[1]), "WDS_CHAT_SYS 收 tool");
/* ⚠ 这两条原来把实参表写死成 (tool)，2026-08-22 加 prof 之后一直假红。按用意写：
   只认「wdsToolSys( 后面第一个实参是 tool」，加参数不再假红。 */
ok(/wdsToolSys\(tool\b/.test(W), "tool 在正文里真用上了（不是收了不用）");
ok(/\+ wdsToolSys\(tool\b/.test(W), "system 里拼了 wdsToolSys(tool…)");
ok(/WDS_CHAT_SYS\(reflect, SDEM, \(nbrCtx \? nbrCtx \+ "\\n" : ""\) \+ ctxText/.test(W),
   "近邻名单前置在站内语料之前（放后面会被两万字语料埋掉）");
ok(/if \(tool === "nbr"\)/.test(W) && /await nbrFor\(env, url, q, 10/.test(W), "近邻工序取的是真名单（共用 nbrFor）");
ok(/t: "nbrfail"/.test(W) && /nbrfail/.test(F), "取不到名单时发 nbrfail，前端如实说一句——不许静默失败");
ok(/wide = deep \|\| tool === "collide"/.test(W), "碰撞工序加宽站内检索（否则挑不出互相矛盾的三篇）");

console.log("④ 满功率预算没被工序顶破");
// 这条守的是全站最贵的那个教训：满功率档的 max_tokens 一旦调大，思考就跑过平台时长上限、
// 被杀在思考阶段——流干净结束、正文 0 字、不报任何错。正则写死了行文形状，早先加 askLen 长文档时
// 就已经匹配不上、空转至今；改成先揪出 tokWant 那一整段表达式，再从里面挑数字。
// 必须先切到 chat 段内：/api/wds/read 里也有一份同名的 tokWant，直接 indexOf 会跨过几千行检索代码
const CHATSEG = W.slice(W.indexOf('url.pathname === "/api/wds/chat"'), W.indexOf('url.pathname === "/api/wds/research"'));
/* 2026-08-30 难度条：三分支搬到了 tokGrade（定了档就按档给，没定档仍是这三分支），tokWant 从它取。要守的事不变。 */
const twSeg = CHATSEG.slice(CHATSEG.indexOf("const tokGrade = "), CHATSEG.indexOf("const clk = wdsClock"));
const mt = twSeg.match(/deep \? (\d+) : \(tool \? (\d+) : (\d+)\)/);
ok(!!mt && /const tokWant = askLen[\s\S]{0,300}?tokGrade\)\)/.test(twSeg), "chat 的 max_tokens 三分支存在（深度/工序/闲聊）且 tokWant 从它取");
ok(mt && +mt[1] <= 8000, "满功率档 ≤ 8000（这是硬约束不是可调参数），实得 " + (mt ? mt[1] : "?"));
ok(mt && +mt[2] > +mt[3] && +mt[2] <= 12000, "工序档比闲聊宽但仍有界，实得 " + (mt ? mt[2] + " vs " + mt[3] : "?"));
{ const kn = W.match(/tok: (\d+), method/g) || []; ok(kn.length === 6 && kn.every((x) => +x.match(/\d+/)[0] <= 8000), "难度条五档的预算也都 ≤ 8000（" + kn.map((x) => x.match(/\d+/)[0]).join("/") + "）"); }
const bigs = (twSeg.match(/\b(\d{4,6})\b/g) || []).map(Number).filter((n) => n > 8000 && n !== 32000);
ok(bigs.length === 0, "tokWant 段里没有 8000 以上的裸预算（32000 是长文档档的天花板，另有出处），实得 " + bigs.join("/"));

console.log("⑤ 前端只传 key，不自己拼工序文本");
ok(/tool: curTool/.test(F), "payload 带 tool");
/* ⚠ 2026-08-28：原来扫的是「本轮工序」四个字，于是前端新加一条 UI 文案
   （「⚠ 本轮工序未交付：」，工序交付审计报缺件用的）当场把它撞红——
   而它要守的用意没变：**工序正文只准在后端**。改成认块头「【本轮工序」，
   那才是正文的形状；文案不再自伤。同型坑（判文案扫整份源码）本仓第五次。 */
ok(!/【本轮工序/.test(F), "前端不含任何工序正文（拼在前端会被后端 q 的 800 字钳位吃掉）");
ok(/curTool = toolInfo\(k\) \? k : ""/.test(F), "前端也只放行认得的 key");
ok(!/sde_wds_tool/.test(F), "工序不落 localStorage（会实质改变产出形态，不该在看不见处跨会话生效）");

console.log("⑥ 九宫格取三格：只许同号位或 123 轮换（把表抠出来真跑）");
/* 守的是这条规矩最容易漂掉的三处：
     ① 合法组合表被人加/删一组（84 取 3 里只有这 9 组合法）；
     ② 抽签从服务端挪回基底自己挑（挑不是抽）；
     ③ 工序正文里那张表与代码里的表说的不是同一回事（读者按一套写、机器按另一套抽）。 */
const nineSeg = W.slice(W.indexOf("const NINE_CELLS = {"), W.indexOf("const WDS_TOOLS = {"));
ok(nineSeg.length > 200, "九宫格组合表在 WDS_TOOLS 之前定义（工序正文要用它拼字）");
let NG = null;
try {
  NG = new Function(nineSeg + "\nreturn { NINE_CELLS, NINE_COMBOS, nineLegal, ninePick, nineDrawBlock, NINE_TABLE };")();
} catch (e) { ok(false, "组合表段能单独求值（真跑），实得错误 " + e.message); }
if (NG) {
  ok(Object.keys(NG.NINE_CELLS).length === 9, "九格齐（S1-S3/D1-D3/E1-E3），实得 " + Object.keys(NG.NINE_CELLS).length);
  ok(NG.NINE_COMBOS.length === 9 && new Set(NG.NINE_COMBOS.map((c) => c.join())).size === 9,
     "合法组合恰 9 组且不重，实得 " + NG.NINE_COMBOS.length);
  const same = NG.NINE_COMBOS.filter((c) => c[0][1] === c[1][1] && c[1][1] === c[2][1]);
  ok(same.length === 3, "其中同号位 3 组，实得 " + same.length);
  ok(NG.NINE_COMBOS.every((c) => new Set(c.map((x) => x[0])).size === 3), "每组都是 S/D/E 各一格");
  ok(NG.NINE_COMBOS.every(NG.nineLegal), "表里每一组自己都判得合法");
  // ⭐ 穷举 C(9,3)=84：合法的必须正好是这 9 组，一个不多一个不少
  const cells = Object.keys(NG.NINE_CELLS), legal = [];
  for (let i = 0; i < 9; i++) for (let j = i + 1; j < 9; j++) for (let k = j + 1; k < 9; k++) {
    const c = [cells[i], cells[j], cells[k]];
    if (NG.nineLegal(c)) legal.push(c.slice().sort().join("·"));
  }
  const want = NG.NINE_COMBOS.map((c) => c.slice().sort().join("·")).sort().join("|");
  ok(legal.length === 9 && legal.sort().join("|") === want, "穷举 84 组，判合法的正好是表里那 9 组，实得 " + legal.length);
  // 两种犯规必须被挡住
  ok(!NG.nineLegal(["S1", "S2", "D3"]), "同一维取两格判非法（S1·S2·D3）");
  ok(!NG.nineLegal(["S1", "D1", "E2"]), "层号重复但不全同判非法（S1·D1·E2）");
  ok(NG.nineLegal(["S2", "D2", "E2"]) && NG.nineLegal(["S3", "D1", "E2"]), "同号位与 123 轮换都判合法");
  // 抽签：只抽合法的，且九组都抽得到（少抽一组＝有格位永远轮不上）
  const seen = new Set(); let bad = 0;
  for (let i = 0; i < 3000; i++) { const c = NG.ninePick(); if (!NG.nineLegal(c)) bad++; seen.add(c.join("·")); }
  ok(bad === 0, "抽签 3000 次没有一次非法，实得非法 " + bad);
  ok(seen.size === 9, "抽签 3000 次九组全覆盖，实得 " + seen.size);
  // 下发块：三格连同各自三分一起写死（防"凭记忆贴标签"），并写明是哪一类
  const blk = NG.nineDrawBlock(["S2", "D3", "E1"]);
  ok(/S2 粒子/.test(blk) && /D3 三最小/.test(blk) && /E1 理念/.test(blk), "抽签块把三格的三分原样写出来");
  ok(/123 轮换/.test(blk) && /同号位/.test(NG.nineDrawBlock(["S1", "D1", "E1"])), "抽签块写明本轮走的是哪一类");
  ok(/不许只换掉一格/.test(blk), "要换就整组换（单换一格必然出表）");
  // 传进来一组非法的，必须当场退回抽签，不许照单下发
  const forced = NG.nineDrawBlock(["S1", "S2", "D3"]);
  ok(!/S1 对比[\s\S]*S2 粒子/.test(forced), "递进来一组非法组合时不照单下发，退回重抽");
}
/* 抽签必须在服务端做：交给基底自己「抽三个」，它挑的永远是最顺手那几格。
   这里不只扫源码——把 WDS_TOOLS ＋ WDS_TOOLS_LANG ＋ wdsToolSys 一起抠出来**真调一遍**，
   证的是接线本身（正则只能证那行字还在，证不了它真的拼进了下发文本）。 */
ok(/tool === "nine" \? nineDrawBlock\(\)/.test(W), "nine 这一档由 wdsToolSys 附上服务端抽签块");
const wireSeg = W.slice(W.indexOf("const NINE_CELLS = {"), W.indexOf("// RESEARCH_STEP"));
try {
  const wire = new Function(wireSeg + "\nreturn { wdsToolSys, nineLegal, NINE_CELLS };")();
  const out = wire.wdsToolSys("nine", null);
  ok(/【本轮抽到的三格/.test(out), "真调 wdsToolSys(\"nine\") —— 下发文本里确有抽签块");
  // 连调 200 次，每次抽到的三格都得是合法组合（这才是这条规矩最终要成立的地方）
  let bad = 0, got = new Set();
  for (let i = 0; i < 200; i++) {
    const t = wire.wdsToolSys("nine", null);
    const cells = (t.slice(t.indexOf("【本轮抽到的三格")).match(/\n· ([SDE][123]) /g) || []).map((s) => s.slice(3, 5));
    if (cells.length !== 3 || !wire.nineLegal(cells)) bad++; else got.add(cells.join("·"));
  }
  ok(bad === 0, "连调 200 次，下发的三格次次合法，实得非法 " + bad);
  ok(got.size === 9, "连调 200 次，九组都下发得到，实得 " + got.size);
  ok(!/【本轮抽到的三格/.test(wire.wdsToolSys("grid", null)), "别的工序不会误挂抽签块（只有 nine 挂）");
  ok(wire.wdsToolSys("nine", { tools: ["what", "how"] }) === "", "档案没开这道工序时，连抽签块都不下发");
} catch (e) { ok(false, "wdsToolSys 能抠出来真调，实得错误 " + e.message); }
/* 工序正文里的那张表是用组合表拼出来的，所以要**求值后再看**——
   只扫源码会把 NINE_SAME 这种变量名当成"列全了"，正是这条断言该防的事。 */
const nineExpr = (seg.match(/\n  nine: ([\s\S]*?)\n\};/) || [0, ""])[1].replace(/,\s*$/, "");
let nineText = "";
try { nineText = new Function(nineSeg + "\nreturn (" + nineExpr + ");")(); }
catch (e) { ok(false, "nine 工序正文能求值（真拼一遍），实得错误 " + e.message); }
ok(/同号位/.test(nineText) && /123 轮换/.test(nineText), "工序正文写明两类合法取法");
ok(/其余 75 种/.test(nineText), "工序正文点明其余 75 种取法作废（84 − 9）");
ok(/S1·S2·D3/.test(nineText) && /S1·D1·E2/.test(nineText), "工序正文举出两种犯规的样子");
if (NG) ok(NG.NINE_COMBOS.every((c) => nineText.indexOf(c.join("·")) >= 0), "9 组合法组合在工序正文里逐组列全（读者与机器看同一张表）");
if (NG) ok(Object.keys(NG.NINE_CELLS).every((k) => nineText.indexOf(k + " " + NG.NINE_CELLS[k]) >= 0), "九格表逐格列全（贴标签前要拿它逐字核）");
ok(/整段作废重写/.test(nineText), "标签与内容对不上就整段重写这条纪律还在（上一版刚补的，别被这次改动挤掉）");

console.log("\n结果：PASS " + PASS + " · FAIL " + FAILS);
process.exit(FAILS ? 1 : 0);
