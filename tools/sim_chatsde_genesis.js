#!/usr/bin/env node
/* 「发生场」工序护栏（2026-08-28）：ChatSDE 第 15 道工序——布置发生、只生不判。
   抠 worker.js 的 NINE_CELLS→RESEARCH_STEP 整段（与 sim_wds_sde_tools 同一条已验证可 eval 的切片）
   真跑 wdsToolSys 与 WDS_TOOLS，不复制代码。
   变异检验：W_JS=/tmp/w.mut.js 或 M_JS=/tmp/m.mut.js node tools/sim_chatsde_genesis.js 应当变红。 */
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.resolve(__dirname, "..");
const W = fs.readFileSync(process.env.W_JS || path.join(ROOT, "src/worker.js"), "utf8");
const F = fs.readFileSync(process.env.M_JS || path.join(ROOT, "public/wds-mode.js"), "utf8");

let pass = 0, fail = 0;
const ok = (c, n, x) => { if (c) pass++; else { fail++; console.log("  ✗ " + n + (x ? "  ← " + x : "")); } };

console.log("【一】白名单与工序实体（真 eval，不数字符串）");
const mKeys = W.match(/const WDS_TOOL_KEYS = \[([^\]]+)\]/);
ok(!!mKeys, "WDS_TOOL_KEYS 在");
let KEYS = [];
try { KEYS = new Function("return [" + (mKeys ? mKeys[1] : "") + "];")(); } catch (e) { ok(false, "白名单能求值", e.message); }
ok(KEYS.indexOf("genesis") >= 0, "白名单里有 genesis");
ok(KEYS.length === 15, "十五道整（原十四道一道不少），实得 " + KEYS.length);
["iq", "three", "motif", "nbr", "rename", "gap", "collide", "forge", "what", "how", "why", "grid", "nine", "map"]
  .forEach((k) => ok(KEYS.indexOf(k) >= 0, "老工序 " + k + " 仍在"));

let WIRE = null;
try {
  const a = W.indexOf("const NINE_CELLS = {"), b = W.indexOf("// RESEARCH_STEP");
  WIRE = new Function(W.slice(a, b) + "\nreturn { wdsToolSys, WDS_TOOLS, WDS_TOOLS_LANG };")();
} catch (e) { ok(false, "工序段能整段求值真跑", e.message); }

if (WIRE) {
  const T = WIRE.WDS_TOOLS.genesis || "";
  ok(T.length > 400, "genesis 有工序正文（非占位空串），实得 " + T.length + " 字");
  ok((T.match(/本轮工序/g) || []).length === 1, "「本轮工序」恰好一次（sim_wds_sde_tools 按次数点道数）");

  console.log("【二】使命：不答题、只布场、只生不判");
  ok(/不回答读者的问题/.test(T), "写明这一轮不回答问题");
  ok(/只生不判/.test(T), "写明只生不判");
  ok(/摆料/.test(T) && /上张力/.test(T) && /出候选/.test(T), "三步齐（摆料/上张力/出候选）");

  console.log("【三】摆料纪律（第二刀＋第五刀同源）");
  ok(/跨至少两个学科/.test(T), "家底须跨学科");
  ok(/宁缺勿造/.test(T) && /不等于没人说过/.test(T), "反造假两纪律在");
  ok(/站外对手：未核验/.test(T), "没名单时明写〔未核验〕");
  ok(/据我所知尚无人提出/.test(T), "点名禁句「据我所知尚无人提出」");
  ok(/至少请两位上台/.test(T), "有名单时至少两位占位者上台");

  console.log("【四】张力：对阵不是清单");
  ok(/不能同时成立/.test(T), "对阵＝两两不能同时成立");
  ok(/共同假定了什么/.test(T), "逼问共有前提");
  ok(/只有并列、没有对阵/.test(T), "摆不出对阵要直说（做不到就直说的出口）");

  console.log("【五】候选：四行机检面＋数量口径");
  ["\n候选：", "\n分岔：", "\n作废：", "\n张力源："].forEach((h) =>
    ok(T.indexOf(h) >= 0, "行首「" + h.trim() + "」在（下一棒过闸靠它机检）"));
  ok(/X 不是 Y，而是 Z/.test(T), "承重句形状 X-Y-Z");
  ok(/5 条/.test(T) && /8 条/.test(T) && /宁缺勿滥/.test(T), "5–8 条且宁缺勿滥");
  ok(/给不出就写「给不出」/.test(T), "作废条件给不出要直说");

  console.log("【六】三禁令与自淘");
  ok(/不许给候选排名/.test(T), "禁排名（排名＝把锦标赛搬回来）");
  ok(/不许自评分数/.test(T), "禁自评");
  ok(/同一条分辨换几种说法/.test(T), "禁一辨多壳");
  ok(/〔自淘：只到复述〕/.test(T), "自淘标记格式在");
  ok(/敢淘汰自己的批次才可信/.test(T), "自淘不惩罚的理由在（删掉它下一步就是凑数）");

  console.log("【七】交账改批账（不动客户端剥账器）");
  ok(/〔交账〕行照常交/.test(T), "交账行照常交（客户端 ledgerTake 零改动）");
  ok(/N 条候选（自淘 M、带作废 K）/.test(T), "「新在」写成批账");
  ok(/作废条件抄候选里最硬的那一句/.test(T), "作废条件从候选里抄（真条件句，过得了 ledgerAudit）");

  console.log("【八】接线真跑：wdsToolSys 的门");
  const out = WIRE.wdsToolSys("genesis", null);
  ok(out.indexOf("发生场") >= 0, "ChatSDE 本体真下发发生场");
  ok(out.indexOf("工序只管这一轮要交付什么") >= 0, "标准工序尾注跟上（口吻条款）");
  ok(WIRE.wdsToolSys("genesis", { tools: ["iq", "three", "what"] }) === "", "档案没开这道 ⇒ 一个字不下发");
  ok(!/【本轮抽到的三格/.test(out), "发生场不误挂九宫抽签块");
  ok(!("genesis" in (WIRE.WDS_TOOLS_LANG || {})), "改姓表无 genesis（分身本就不该有这道）");

  console.log("【九】分身档一个都没拿到（服务端＋前端两张表逐条查）");
  const profLists = (W.match(/tools: \[[^\]]*\]/g) || []);
  ok(profLists.length >= 6, "worker 里分身 tools 表 ≥6 张，实得 " + profLists.length);
  profLists.forEach((l, i) => ok(l.indexOf("genesis") < 0, "worker 分身表 #" + (i + 1) + " 不含 genesis"));
  const fLists = (F.match(/tools: \[[^\]]*\]/g) || []);
  ok(fLists.length >= 6, "前端分身 tools 表 ≥6 张，实得 " + fLists.length);
  fLists.forEach((l, i) => ok(l.indexOf("genesis") < 0, "前端分身表 #" + (i + 1) + " 不含 genesis"));
}

console.log("【十】占位者链：旁挂接线，被钉的原行原样");
ok(/const wantNbr = \(rs && rs\.forge && FORGE_NBR_STAGES\[rs\.i \| 0\]\) \|\| tool === "iq";/.test(W),
   "原行一字未动（sim_chatsde_forge:196 / sim_distill_nbr:72 钉着它）");
/* ⚠ 这三条原来把**整行**抄进来，2026-08-28 近邻工序也接上这条链（+ tool === "nbr"）
   就当场假红，而它们要守的用意一个字没变：**旁挂在自己一行、不并进 wantNbr 那一行；
   先定义后使用**。按用意重写：只认「wantNbrG = wantNbr ||」这个形状 ＋ 里面有 genesis。 */
ok(/const wantNbrG = wantNbr \|\|[^\n]*tool === "genesis"/.test(W), "旁挂 wantNbrG 在");
const iA = W.search(/const wantNbrG = wantNbr \|\|/);
const iB = W.indexOf("if (wantNbrG) {");
ok(iA >= 0, "wantNbrG 定义找得到");           /* 次序断言先断「在」——indexOf 回 -1 比谁都小，
ok(iB >= 0, "if (wantNbrG) 找得到");             2026-08-23 第四刀在这上面栽过一次 */
ok(iA >= 0 && iB >= 0 && iA < iB, "先定义后使用");
ok(!/if \(wantNbr\) \{/.test(W), "老的 if (wantNbr) 已让位（不许两个门并存）");

console.log("【十一】前端：清单、命令、文案");
const iMap = F.indexOf('{ k: "map"');
const iGen = F.indexOf('{ k: "genesis", n: "tlGenesis", s: "tlGenesisS"');
ok(iMap >= 0, "map 条目在");
ok(iGen >= 0, "genesis 条目在");
ok(iMap >= 0 && iGen >= 0 && iGen > iMap, "genesis 排在 map 之后（清单末位）");
const toolsSeg = F.slice(F.indexOf("var TOOLS = ["), F.indexOf("\n  ];", F.indexOf("var TOOLS = [")));
ok(toolsSeg.indexOf('k: "genesis"') >= 0, "genesis 落在 TOOLS 数组界内（不是掉在外面的孤儿）");
ok(/cmd: \["发生场", "genesis", "布场"\]/.test(F), "斜杠命令三别名（发生场/genesis/布场）");
ok(/tlGenesis: "发生场", tlGenesisS: "[^"]{10,}"/.test(F), "中文文案齐且副题非空");
ok(/tlGenesis: "Genesis field", tlGenesisS: "[^"]{10,}"/.test(F), "英文文案齐且副题非空");
ok(!/【本轮工序/.test(F), "前端仍不含任何工序正文（正文只在后端）");   /* 认块头，不认四个字：前端有一条报缺件的 UI 文案带「本轮工序」 */

console.log("【十二】护栏的护栏：sim_wds_sde_tools 的 KEYS 已带上第 15 道");
try {
  const g = fs.readFileSync(path.join(ROOT, "tools/sim_wds_sde_tools.js"), "utf8");
  const gk = g.match(/const KEYS = \[([^\]]+)\]/);
  ok(!!gk && gk[1].indexOf('"genesis"') >= 0, "sim_wds_sde_tools 的 KEYS 含 genesis（否则它按 14 道数「本轮工序」当场红）");
} catch (e) { ok(false, "sim_wds_sde_tools 读得到", e.message); }

console.log("【十三】平台名录对账（模型自己得知道手上有这道）");
ok(/你手上有十五件\*\*单轮工序\*\*/.test(W), "名录件数改十五（forge 护栏按这句与键数对账）");
ok(/\*\*\/发生场\*\* 不答题/.test(W), "名录枚举里列了 /发生场");
ok(/（十五件工序＋十八道产线/.test(W), "行 890 注释件数同步");

console.log("\n结果：PASS " + pass + " · FAIL " + fail);
process.exit(fail ? 1 : 0);
