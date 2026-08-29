/* sim_chatsde_grade.js —— ChatSDE「难度条」（2026-08-30）
 *
 * [stated] 作者：深度思考要做成一个难度条选择，档位按站内检索的「高级度」定——与提问核心词相关的
 * 站内材料有多少、有多准（例：问「身在福中不知福」，检索该一路走到「幸福律」）。
 *
 * 四节：
 *   一、真跑：gradeAnchors / gradeCoreLanding / ragGrade / wdsGradeKnobs / wdsGradeReq / wdsGradePick
 *       全部从 worker.js 抠出来跑（不复制一份平行实现）。
 *   二、/api/wds/rag：九库先种、核心名并入检索词、返回 grade。
 *   三、/api/wds/chat：收 grade → 定档 → 基底/功率/预算/工序/时钟/资料量按档给；不适用的路不改；发 grade 帧。
 *   四、前端：难度条只在深度档露面、请求带 grade、grade 帧落成一行读数、双基底也带。
 *
 * 跑法：node tools/sim_chatsde_grade.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");
const SRC = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");
const FE = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");
let pass = 0, fail = 0;
const ok = (n, c, d) => { if (c) { pass++; console.log("  ✓ " + n); } else { fail++; console.log("  ✗ " + n + (d ? ("  " + d) : "")); } };

/* 抠函数：从 `function NAME(` 起到下一个顶格 `\n}` 止。 */
function fnOf(name) {
  const i = SRC.indexOf("function " + name + "(");
  if (i < 0) return "";
  const j = SRC.indexOf("\n}", i);
  return SRC.slice(i, j + 2);
}
function constOf(name) {
  const m = SRC.match(new RegExp("const " + name + " = ([^\\n]+?);(?=\\s*(?://|/\\*|\\n))"));
  return m ? ("const " + name + " = " + m[1] + ";") : "";
}

/* ═══ 一、真跑 ═══ */
console.log("\n一、难度读数与定档（真跑）");
const PARTS = [
  constOf("GRADE_STOP"), constOf("GRADE_STOP2"), constOf("GRADE_LV"), constOf("GRADE_NAME"),
  "const CHAT_FIRST_MS = 90000, CHAT_TOTAL_MS = 240000, CHAT_FIRST_DEEP_MS = 240000, CHAT_TOTAL_DEEP_MS = 420000, CHAT_FIRST_MID_MS = 150000, CHAT_TOTAL_MID_MS = 300000;",
  constOf("_kbNorm"), fnOf("kbLink"), fnOf("gradeAnchors"), fnOf("gradeCoreLanding"), fnOf("ragGrade"),
  fnOf("wdsGradeKnobs"), fnOf("wdsGradeReq"), fnOf("wdsGradePick"),
];
ok("六个函数与四个常量都抠得到", PARTS.every((p) => p && p.length > 20), PARTS.map((p, i) => (p ? "" : ("#" + i))).join(""));
let box = null;
try {
  box = new Function(PARTS.join("\n") + "\nreturn { gradeAnchors, gradeCoreLanding, ragGrade, wdsGradeKnobs, wdsGradeReq, wdsGradePick, GRADE_LV };")();
} catch (e) { ok("抠出来的代码能装起来", false, String(e && e.message)); }
if (box) {
  ok("抠出来的代码能装起来", true);
  // 锚：只取题面实词二元组
  const a1 = box.gradeAnchors("身在福中不知福");
  ok("「身在福中不知福」的锚含「知福」「福中」「身在」", a1.indexOf("知福") >= 0 && a1.indexOf("福中") >= 0 && a1.indexOf("身在") >= 0, a1.join("/"));
  ok("弱停用字打头的二元组（不知／在福）不当锚", a1.indexOf("不知") < 0 && a1.indexOf("在福") < 0, a1.join("/"));
  ok("弱停用字只杀打头：「存在」「中心」留得住，「什么」「在福」进不来", box.gradeAnchors("存在与中心位").indexOf("存在") >= 0 && box.gradeAnchors("存在与中心位").indexOf("中心") >= 0 && box.gradeAnchors("什么是在福").length === 0, box.gradeAnchors("存在与中心位").join("/"));
  const a2 = box.gradeAnchors("什么是三大方程 S=F(D,E)");
  ok("实词二元组与英文词都进锚", a2.indexOf("方程") >= 0 && a2.indexOf("三大") >= 0 && a2.indexOf("什么") < 0, a2.join("/"));
  ok("寒暄几乎没有锚", box.gradeAnchors("下午好").length <= 1 && box.gradeAnchors("你好啊").length === 0, box.gradeAnchors("下午好").join("/"));

  // 落点：用一份小九库（形状照真 kb-index / concepts.json）
  const kb = {
    idx: { "幸福律": ["concept", "c1"], "创造自由幸福": ["theory", "t1"], "显露": ["concept", "c2"], "三大方程": ["theory", "t2"] },
    byId: { c1: { id: "c1", type: "concept", name: "意义三律", def: "…" }, t1: { id: "t1", type: "theory", name: "三大意义律", def: "…" },
            c2: { id: "c2", type: "concept", name: "显露", def: "…" }, t2: { id: "t2", type: "theory", name: "三大方程", def: "…" } },
  };
  const c1 = box.gradeCoreLanding(kb, "身在福中不知福", ["幸福", "显露", "特征纠缠"]);
  ok("「福」→「幸福律」：落点名是读者认得的索引词，不是九库登记名", c1.length > 0 && c1[0].n === "幸福律" && c1[0].e === "意义三律", JSON.stringify(c1));
  ok("弱锚定记的是共字「福」", c1[0] && c1[0].by === "福" && c1[0].via === "共字" && c1[0].w === 6);
  ok("扩展词「显露」种到了却与题面无锚定 ⇒ 不算落点", c1.every((c) => c.n !== "显露"), JSON.stringify(c1));
  const c2 = box.gradeCoreLanding(kb, "什么是幸福律？", []);
  ok("题面直接含索引词 ⇒ 强锚定 w=10", c2.length > 0 && c2[0].n === "幸福律" && c2[0].via === "题面" && c2[0].w === 10, JSON.stringify(c2));
  const c3 = box.gradeCoreLanding(kb, "下午好", ["显露", "幸福"]);
  ok("寒暄：扩展词种到的实体一个都不算落点", c3.length === 0, JSON.stringify(c3));
  ok("坏 kb 不炸", box.gradeCoreLanding(null, "x", []).length === 0 && box.gradeCoreLanding({}, "x", []).length === 0);

  // 读数与档位
  const mk = (n, txt, sc) => { const a = []; for (let i = 0; i < n; i++) a.push({ sc: sc, d: i, t: txt + "…" + i }); return a; };
  const g0 = box.ragGrade("下午好", [], 0, 0, 0, []);
  ok("空检索 ⇒ 第 1 档、分 0", g0.lv === 1 && g0.score === 0, JSON.stringify(g0));
  const gHi = box.ragGrade("身在福中不知福", mk(18, "幸福律说的是收敛于主体可承受……知福者", 12), 18, 8, 15000, c1);
  ok("材料厚＋落点准 ⇒ 第 5 档（分 ≥72）", gHi.lv === 5 && gHi.score >= 72, JSON.stringify({ lv: gHi.lv, s: gHi.score, a: gHi.amount, p: gHi.acc, l: gHi.landing }));
  ok("读数带落点名、锚定段数、核心段数、锚定篇数", !!(gHi.core[0] && gHi.core[0].n === "幸福律") && gHi.ahits === 18 && gHi.chits === 18 && gHi.docs === 8 && gHi.adocs === 18, JSON.stringify(gHi.core));
  const gMid = box.ragGrade("身在福中不知福", mk(3, "幸福律……", 6).concat(mk(12, "无关的段落", 2)), 15, 5, 8000, c1);
  ok("材料薄但落到了核心律 ⇒ 中档（3）", gMid.lv === 3, JSON.stringify({ lv: gMid.lv, s: gMid.score, a: gMid.amount, p: gMid.acc, l: gMid.landing }));
  const gNoise = box.ragGrade("下午好", mk(12, "显露 差异 纠缠 显露 差异 纠缠", 4), 12, 6, 6000, []);
  ok("寒暄召回一堆 SDE 术语段 ⇒ 仍是第 1 档、分 0（扩展词召回的段不计分）", gNoise.lv === 1 && gNoise.score === 0, JSON.stringify({ lv: gNoise.lv, s: gNoise.score, a: gNoise.amount, p: gNoise.acc }));
  const gMix = box.ragGrade("什么是内卷", mk(2, "内卷是……", 9).concat(mk(20, "显露 差异 纠缠", 9)), 22, 9, 9000, []);
  ok("锚定段只有两段时，量按两段算、准按那两段算，不被二十段噪音抬高", gMix.ahits === 2 && gMix.amount <= 12 && gMix.lv <= 2, JSON.stringify({ lv: gMix.lv, s: gMix.score, a: gMix.amount, p: gMix.acc }));
  const gGhost = box.ragGrade("量子力学的测量问题", mk(6, "量子 测量 力学 观测……", 9), 6, 4, 3500, [{ n: "数学场", e: "数学场", by: "学", via: "共字", w: 6 }]);
  ok("共字种到的落点若在召回段里一次都没出现 ⇒ 不算落点（量子力学≠数学场）", gGhost.core.length === 0 && gGhost.landing === 0 && gGhost.chits === 0, JSON.stringify(gGhost.core));
  const gKeep = box.ragGrade("量子力学的测量问题", mk(6, "量子 测量 数学场 观测……", 9), 6, 4, 3500, [{ n: "数学场", e: "数学场", by: "学", via: "共字", w: 6 }]);
  ok("共字落点在段里真出现过 ⇒ 保留", gKeep.core.length === 1 && gKeep.landing > 0);
  const gStrong = box.ragGrade("什么是幸福律", mk(6, "别的东西……", 9), 6, 4, 3500, [{ n: "幸福律", e: "意义三律", by: "幸福律", via: "题面", w: 10 }]);
  ok("题面锚定不必验段：段里没出现也算落点（题目本身就点了名）", gStrong.core.length === 1 && gStrong.landing === 10);
  const gEx = box.ragGrade("三大方程是什么", mk(10, "三大方程是什么？S=F(D,E)……", 14), 10, 6, 9000, [{ n: "三大方程", e: "三大方程", by: "三大方程", via: "题面", w: 10 }]);
  ok("题面原句在站 ⇒ exact 为真且加分", gEx.exact === true && gEx.acc >= 25, JSON.stringify({ lv: gEx.lv, s: gEx.score, p: gEx.acc }));
  ok("档位切分是单调的（分越高档越高）", (function () {
    let last = 0;
    for (let sc = 0; sc <= 100; sc++) {
      let lv = 5; for (let i = 0; i < box.GRADE_LV.length; i++) if (sc < box.GRADE_LV[i]) { lv = i + 1; break; }
      if (lv < last) return false; last = lv;
    }
    return true;
  })());

  // 配方
  const k4 = box.wdsGradeKnobs(4);
  ok("第 4 档 ＝ 原深度档配方（顶配/满功率/6000/完整工序/240s·420s/10 篇/不装内功）",
    k4.top === 1 && k4.effort === "max" && k4.tok === 6000 && k4.method === 1 && k4.first === 240000 && k4.total === 420000 && k4.src === 10 && !k4.ng && !k4.plain, JSON.stringify(k4));
  const k5 = box.wdsGradeKnobs(5);
  ok("第 5 档在 4 之上：预算更大、装完整内功、其余同 4", k5.ng === 1 && k5.tok > k4.tok && k5.top === 1 && k5.effort === "max" && k5.method === 1 && k5.first === k4.first);
  const k3 = box.wdsGradeKnobs(3);
  ok("第 3 档：顶配基底、思考 high 不 max、完整工序、时钟在两档之间", k3.top === 1 && k3.effort === "high" && k3.method === 1 && k3.first > 90000 && k3.first < 240000 && k3.total > 240000 && k3.total < 420000);
  const k1 = box.wdsGradeKnobs(1), k2 = box.wdsGradeKnobs(2);
  ok("第 1 档：标准基底＋关思考＋标准时钟＋精简工序（寒暄快车道）", k1.top === 0 && k1.plain === 1 && k1.first === 90000 && k1.method === 0 && k1.tok <= 2600);
  ok("第 2 档：标准基底、思考随默认、不关", k2.top === 0 && k2.plain === 0 && k2.method === 0);
  ok("五档预算与资料量单调不减", [1, 2, 3, 4, 5].every((n, i, arr) => i === 0 || (box.wdsGradeKnobs(n).tok >= box.wdsGradeKnobs(arr[i - 1]).tok && box.wdsGradeKnobs(n).src >= box.wdsGradeKnobs(arr[i - 1]).src && box.wdsGradeKnobs(n).ctx >= box.wdsGradeKnobs(arr[i - 1]).ctx)));
  ok("认不出的档退到标准配方（lv 0）", box.wdsGradeKnobs(9).lv === 0 && box.wdsGradeKnobs("x").lv === 0);

  // 请求解析
  ok("grade 解析：auto／数字／垃圾", box.wdsGradeReq("auto") === "auto" && box.wdsGradeReq(3) === 3 && box.wdsGradeReq("5") === 5 && box.wdsGradeReq(0) === 0 && box.wdsGradeReq("9") === 0 && box.wdsGradeReq(undefined) === 0 && box.wdsGradeReq("x") === 0);

  // 定档
  const pStd = box.wdsGradePick(false, "auto", { lv: 5 }, {});
  ok("标准档：不定档（on=false, lv 0）——难度条与标准档无关", pStd.on === false && pStd.lv === 0 && pStd.why === "std");
  const pLegacy = box.wdsGradePick(true, 0, { lv: 2 }, {});
  ok("老客户端（没递 grade）：深度档照旧＝第 4 档配方", pLegacy.on === false && pLegacy.lv === 4 && pLegacy.k.tok === 6000 && pLegacy.why === "legacy");
  const pAuto = box.wdsGradePick(true, "auto", { lv: 2 }, {});
  ok("自动：按检索读数定档", pAuto.on === true && pAuto.lv === 2 && pAuto.auto === true && pAuto.pin === 0);
  const pNoRag = box.wdsGradePick(true, "auto", null, {});
  ok("自动但检索没接上：不知深浅 ⇒ 第 4 档并记 norag", pNoRag.on === true && pNoRag.lv === 4 && pNoRag.why === "norag");
  const pPin = box.wdsGradePick(true, 3, { lv: 5 }, {});
  ok("钉死：读者的档压过检索的档", pPin.on === true && pPin.lv === 3 && pPin.pin === 3 && pPin.auto === false);
  ok("产线道次／三家对撞／看图：一律不改（老深度档）", ["rsLong", "duel", "canSee"].every((k) => { const o = {}; o[k] = true; const p = box.wdsGradePick(true, "auto", { lv: 1 }, o); return p.on === false && p.lv === 4; }));
}

/* ═══ 二、/api/wds/rag ═══ */
console.log("\n二、/api/wds/rag：先种九库、核心名并入检索词、返回读数");
const ri = SRC.indexOf('if (url.pathname === "/api/wds/rag")');
const rj = SRC.indexOf('if (url.pathname === "/api/wds/dialogue-reflect")', ri);
const RAG = SRC.slice(ri, rj > ri ? rj : ri + 20000);
ok("找得到 /api/wds/rag 那一段", RAG.length > 2000 && RAG.length < 20000);
const iLand = RAG.indexOf("gradeCoreLanding(kb, q, expTerms)"), iScan = RAG.indexOf("const scan = await ragScan(");
ok("九库落点在检索**之前**算", iLand > 0 && iScan > iLand);
ok("落点名并进检索词（这一趟检索才真走到那条律上）", /for \(const c of core\) if \(expTerms\.indexOf\(c\.n\) < 0\) expTerms\.push\(c\.n\);/.test(RAG));
ok("九库只装一次、档案模式仍跳过", /let kb = null, core = \[\];\s*if \(kbn && !prof\)/.test(RAG) && /if \(kbn && !prof && kb\)/.test(RAG) && (RAG.match(/await loadKB\(env, url\)/g) || []).length === 1);
ok("返回体带 grade（由 ragGrade 算，喂的是 scan.picked 与真实条数）", /grade: ragGrade\(q, scan\.picked, nHit, srcs\.length, kbBlock\.length \+ chunkText\.length, core\)/.test(RAG));
ok("兄弟 sim 抠片段循环的两个锚点还在（别把它抠崩）", RAG.indexOf("        // capkb 传了就按") > 0 && RAG.indexOf("        return J({ ok: true, ctx:") > 0);

/* ═══ 三、/api/wds/chat ═══ */
console.log("\n三、/api/wds/chat：定档与按档给");
const ci = SRC.indexOf('if (url.pathname === "/api/wds/chat")');
const cj = SRC.indexOf('if (url.pathname === "/api/wds/research"', ci);
const CHAT = SRC.slice(ci, cj > ci ? cj : ci + 120000);
ok("找得到 /api/wds/chat 那一段", CHAT.length > 5000);
ok("收 grade 字段（走解析器，不原样用）", /const gradeReq = wdsGradeReq\(b\.grade\);/.test(CHAT));
ok("子请求成功时把 grade 收下（ragG）", /ragG = \(jr\.grade && typeof jr\.grade === "object"\) \? jr\.grade : null;/.test(CHAT));
ok("定档：deep／请求／读数／不适用三条路一起递进 wdsGradePick", /const G = wdsGradePick\(deep, gradeReq, ragG, \{ rsLong: !!\(rs && \(rs\.forge \|\| rs\.sde\)\), duel: !!duel, canSee: canSee \}\);/.test(CHAT));
ok("按档改 VC 时看图那条路不碰", /if \(G\.on && !canSee\) \{\s*VC\.top = gK\.top \? 1 : 0;\s*VC\.model = wdsPickModel\(vd, umodel, gK\.top\);/.test(CHAT));
ok("功率档随档给（3 档 high／4–5 档 max），非顶配时不留 effort", /if \(gK\.top && gK\.effort\) VC\.effort = gK\.effort; else delete VC\.effort;/.test(CHAT));
ok("方法论块按档给（mFull），不再直接看 deep", /WDS_CHAT_SYS\(reflect, SDEM, \(nbrCtx \? nbrCtx \+ "\\n" : ""\) \+ ctxText, webCtx, mFull,/.test(CHAT) && /const mFull = G\.on \? !!gK\.method : deep;/.test(CHAT));
ok("预算按档给，工序保底 4000；不适用时是老账（6000／4000／2600）", /const tokGrade = G\.on \? Math\.max\(gK\.tok, tool \? 4000 : 0\) : \(deep \? 6000 : \(tool \? 4000 : 2600\)\);/.test(CHAT) && /: \(rsLong \? FORGE_STAGE_TOK : \(rs \? \(deep \? 6000 : 4000\) : tokGrade\)\)/.test(CHAT));
ok("时钟按档给，产线与长篇的总时长照旧最长", /const gFirst = G\.on \? gK\.first : \(deep \? CHAT_FIRST_DEEP_MS : CHAT_FIRST_MS\);/.test(CHAT) && /const clk = wdsClock\(gFirst,\s*rsLong \? FORGE_TOTAL_MS : \(askLen \? CHAT_TOTAL_LONG_MS : gTotal\)\);/.test(CHAT));
ok("零帧提示报的是这一档真实的首帧闸", /const _lim = Math\.round\(gFirst \/ 1000\);/.test(CHAT));
ok("出处条数与站内资料量按档裁，裁了要说", /sources = sources\.slice\(0, G\.on \? gK\.src : \(deep \? 10 : 6\)\);/.test(CHAT) && /if \(G\.on && ctxText\.length > gK\.ctx\)/.test(CHAT) && /站内资料只带前/.test(CHAT));
ok("发 grade 帧，且标准档也发（读者看得见这一问的高级度）", /if \(ragG \|\| G\.on \|\| deep\) controller\.enqueue\(_sseBytes\(\{ t: "grade", v: \{/.test(CHAT));
ok("grade 帧里带落点、量、准、配方", /core: ragG \? \(ragG\.core \|\| \[\]\) : \[\]/.test(CHAT) && /method: mFull \? "完整工序" : "精简工序", tok: tokGrade, ng: !!\(G\.on && gK\.ng && !prof\)/.test(CHAT));
ok("第 1 档主答走关思考的请求体（普通问答那一发）", /body: JSON\.stringify\(gPlain \? wdsPlainBody\(VC, \{ model: VC\.model, stream: true, max_tokens: tokWant, messages \}\) : wdsTopBody\(VC, \{ model: VC\.model, stream: true, max_tokens: tokWant, messages \}\)\)/.test(CHAT));
ok("关思考只对关得掉的家（gPlain 带 wdsCanPlain）", /const gPlain = !!\(G\.on && gK\.plain && wdsCanPlain\(VC\)\);/.test(CHAT));
const i5 = CHAT.indexOf("if (G.on && gK.ng && !prof && !(rs && rs.sde)) {");
ok("第 5 档装完整内功：只在普通问答上、走 resPriorFit 预算闸、装不下退精简并说明", i5 > 0
  && CHAT.slice(i5, i5 + 2600).indexOf("resPriorFit(_ng5.length, 0, ctxText.length, webCtx.length, docCtx.length,") > 0
  && CHAT.slice(i5, i5 + 2600).indexOf("neigongLite(_ng5)") > 0
  && CHAT.slice(i5, i5 + 2600).indexOf("内功文件没读到") > 0);
ok("第 5 档内功装在 system 拼装之前", i5 > 0 && i5 < CHAT.indexOf("const sys = WDS_CHAT_SYS("));
ok("定档发生在检索之后、心得之前（读数从检索里来；心得键随型号变）", CHAT.indexOf("const G = wdsGradePick(") > CHAT.indexOf("const rr = await wdsRag(env, url, _ragBody);") && CHAT.indexOf("const G = wdsGradePick(") < CHAT.indexOf("reflect = await ensureReflect(env, url, rvendor, VC, KEY)"));
ok("研究产线（rs.sde）自己的内功装载没被动", /if \(rs && rs\.sde && !prof\) \{\s*let _ng = "";/.test(CHAT));

/* ═══ 四、前端 ═══ */
console.log("\n四、前端：难度条");
ok("难度条的存储键与状态", /var LS_GRADE = "sde_wds_grade";/.test(FE) && /var gradePin = 0, gradeLast = null;/.test(FE));
ok("难度条挂在深度思考那颗钮旁边（自动＋1–5）", /data-k='deep'><\/button>" \+\s*"<span class='wdsm-grade' style='display:none'><i><\/i>" \+\s*"<button data-g='0'><\/button><button data-g='1'>1<\/button>/.test(FE) && /<button data-g='5'>5<\/button>/.test(FE));
ok("标准档整条不显示", /function paintGrade\(\) \{\s*if \(!gradeEl\) return;\s*if \(thinkMode !== "deep"\) \{ gradeEl\.style\.display = "none"; return; \}/.test(FE));
ok("档位一变就重画难度条", /paintGrade\(\);\s*\/\/ 难度条只在深度档露面\s*toolsPaint\(\);/.test(FE));
ok("点数字钉死、点自动回 0，都落 localStorage", /gradePin = \(g >= 1 && g <= 5\) \? g : 0;\s*try \{ localStorage\.setItem\(LS_GRADE, String\(gradePin\)\); \} catch \(e\) \{\}/.test(FE));
ok("主对话请求只在深度档带 grade（auto 或钉死的档）", /if \(thinkMode === "deep"\) payload\.grade = gradePin \? gradePin : "auto";/.test(FE));
ok("双基底也带 grade", /if \(thinkMode === "deep"\) pl\.grade = gradePin \? gradePin : "auto";/.test(FE));
ok("grade 帧落成一行读数", /else if \(j\.t === "grade"\) \{ gradeLine\(cell, j\.v\); \}/.test(FE));
ok("读数摆在答案外面（插在正文之前），且只有实际定过档的才更新条上的 lit", /cell\.turn\.insertBefore\(d, cell\.a\);\s*if \(v\.on\) \{ gradeLast = v; paintGrade\(\); \}/.test(FE));
ok("读数行写落点、命中量、配方", /gFmt\("gLineLand"/.test(FE) && /gFmt\("gLineHits"/.test(FE) && /gFmt\("gLineThink"/.test(FE));
ok("中英两套文案都齐（gLab/gAuto/gNames/gLineLv）", ["gLab", "gAuto", "gNames", "gLineLv", "gLineNoRag"].every((k) => (FE.match(new RegExp(k + ": ", "g")) || []).length >= 2));
ok("tipDeep 已改成难度条说明（中英）", /tipDeep: "难度条：按这一问在站内检索到的核心词材料/.test(FE) && /tipDeep: "Difficulty bar: the level is set automatically/.test(FE));
ok("难度条样式在", /\.wdsm-grade\{display:inline-flex/.test(FE) && /\.wdsm-grade button\.lit\{/.test(FE) && /\.wdsm-gline\{/.test(FE));

/* ═══ 五、前端真跑：paintGrade / gradeLine 在一个小 DOM 上跑一遍 ═══
   （node --check 查不出运行时错——2026-07 那行 plainMeta.textContent 的血案就是这么漏的） */
console.log("\n五、前端真跑（小 DOM）");
{
  function N(tag) { this.tagName = tag; this.children = []; this.attrs = {}; this.className = ""; this.textContent = ""; this.style = {}; this.title = ""; }
  N.prototype.appendChild = function (c) { this.children.push(c); c.parentNode = this; return c; };
  N.prototype.insertBefore = function (c, ref) { const i = this.children.indexOf(ref); if (i < 0) this.children.push(c); else this.children.splice(i, 0, c); c.parentNode = this; return c; };
  N.prototype.setAttribute = function (k, v) { this.attrs[k] = String(v); };
  N.prototype.getAttribute = function (k) { return k in this.attrs ? this.attrs[k] : null; };
  N.prototype._all = function (o) { o.push(this); this.children.forEach((c) => c._all(o)); return o; };
  N.prototype._m = function (sel) { if (sel[0] === ".") return this.className.split(/\s+/).indexOf(sel.slice(1)) >= 0; return this.tagName === sel; };
  N.prototype.querySelector = function (sel) { return this._all([]).slice(1).find((n) => n._m(sel)) || null; };
  N.prototype.querySelectorAll = function (sel) { return this._all([]).slice(1).filter((n) => n._m(sel)); };
  const layer = new N("div");
  const grade = new N("span"); grade.className = "wdsm-grade"; layer.appendChild(grade);
  grade.appendChild(new N("i"));
  for (let g = 0; g <= 5; g++) { const b = new N("button"); b.setAttribute("data-g", String(g)); grade.appendChild(b); }
  grade.appendChild(new N("em"));
  const store = {};
  const localStorage = { setItem: (k, v) => { store[k] = v; }, getItem: (k) => (k in store ? store[k] : null) };
  const document = { createElement: (t) => new N(t), createTextNode: (t) => { const n = new N("#text"); n.textContent = t; return n; } };
  const i0 = FE.indexOf("  var gradeEl = layer.querySelector(\".wdsm-grade\");");
  const i1 = FE.indexOf("  function gradeLine(cell, v) {", i0);
  const i2 = FE.indexOf("\n  }\n", i1 > 0 ? i1 : i0) + 4;
  const seg = FE.slice(i0, i2);
  ok("抠得到难度条那一段前端代码", i0 > 0 && i1 > i0 && seg.indexOf("function gradeLine(") > 0 && seg.indexOf("function paintGrade(") > 0, "i0=" + i0 + " i1=" + i1 + " len=" + seg.length);
  const zh = { gLab: "难度", gAuto: "自动", gNames: ["轻", "常", "深", "满", "极"], gAutoT: "A", gPinT: "钉死第 {n} 档（{name}）", gNow: "上一答 {n}·{name}", gPinNow: "钉 {n}·{name}",
    gLineLv: "难度 {n}/5·{name}", gLineAuto: "自动", gLineNoRag: "自动·检索没接上，按 4 档", gLinePin: "钉死", gLineStd: "标准档（未按此加深）",
    gLineLand: "落点：{list}", gLineBy: "由「{by}」", gLineHits: "站内 {docs} 篇·锚定 {a}/{h} 段", gLineCore: "核心 {c} 段", gLineExact: "题面原句在站", gLineNone: "站内无锚定命中", gLineThink: "思考{think}", gLineNg: "＋完整内功" };
  let fx = null;
  try {
    fx = new Function("layer", "localStorage", "document", "LS_GRADE", "t", "el",
      "var thinkMode = 'deep', gradePin = 0, gradeLast = null;\n" + seg +
      "\nreturn { paint: paintGrade, line: gradeLine, pin: function (v) { gradePin = v; }, mode: function (m) { thinkMode = m; }, last: function () { return gradeLast; } };")(
      layer, localStorage, document, "sde_wds_grade", (k) => zh[k], (t, c, x) => { const e = new N(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; });
    ok("难度条那一段装得起来", true);
  } catch (e) { ok("难度条那一段装得起来", false, String(e && e.message)); }
  if (fx) {
    fx.paint();
    const bs = grade.querySelectorAll("button");
    ok("深度档：条露面、「自动」钮点亮、还没读数时没有 lit", grade.style.display === "" && bs[0].className.indexOf("on") >= 0 && bs[0].textContent === "自动" && bs.every((b) => b.className.indexOf("lit") < 0));
    const cell = { turn: new N("div"), a: new N("div") }; cell.turn.appendChild(cell.a);
    fx.line(cell, { lv: 4, name: "满", on: true, auto: true, pin: 0, why: "auto", deep: true, score: 66, amount: 30, acc: 15, landing: 21, hits: 18, ahits: 7, chits: 3, docs: 7, chars: 12000, exact: false,
      core: [{ n: "幸福律", by: "福", via: "共字" }], anchors: ["身在", "福中", "知福"], model: "deepseek-v4-pro", top: 1, think: "满功率", method: "完整工序", tok: 6000, ng: false });
    const line = cell.turn.children[0];
    ok("读数行插在正文之前", line !== cell.a && line.className === "wdsm-gline" && cell.turn.children[1] === cell.a);
    const txt = line._all([]).map((n) => n.textContent).join("");
    ok("读数行写着档／自动／落点（由「福」）／命中量／配方", /难度 4\/5·满/.test(txt) && /（自动）/.test(txt) && /落点：幸福律（由「福」）/.test(txt) && /站内 7 篇·锚定 7\/18 段·核心 3 段/.test(txt) && /deepseek-v4-pro · 思考满功率 · 完整工序/.test(txt), txt);
    ok("读数行的悬停提示带分项", /score 66 = 量 30 \+ 准 15 \+ 落点 21/.test(line.title) && /锚：身在\/福中\/知福/.test(line.title), line.title);
    fx.paint();
    const bs2 = grade.querySelectorAll("button");
    ok("自动定到 4 档后：4 号钮 lit、「自动」仍 on、右侧写「上一答 4·满」", bs2[4].className.indexOf("lit") >= 0 && bs2[0].className.indexOf("on") >= 0 && grade.querySelector("em").textContent === "上一答 4·满", bs2.map((b) => b.className).join(","));
    // 钉死 2 档
    bs2[2].onclick();
    ok("点 2 号钮 ⇒ 钉死 2 档、落 localStorage、2 号钮 on 且 lit", store.sde_wds_grade === "2" && bs2[2].className.indexOf("on") >= 0 && bs2[2].className.indexOf("lit") >= 0 && bs2[4].className.indexOf("lit") < 0 && grade.querySelector("em").textContent === "钉 2·常");
    bs2[0].onclick();
    ok("点「自动」⇒ 回 0、localStorage 记 0、lit 回到上一答的 4", store.sde_wds_grade === "0" && bs2[0].className.indexOf("on") >= 0 && bs2[4].className.indexOf("lit") >= 0);
    // 标准档的读数：不更新条
    const cell2 = { turn: new N("div"), a: new N("div") }; cell2.turn.appendChild(cell2.a);
    fx.line(cell2, { lv: 0, name: "标准", on: false, auto: false, pin: 0, why: "std", deep: false, hits: 5, ahits: 1, docs: 3, core: [], anchors: [], rlv: 2, score: 20 });
    const txt2 = cell2.turn.children[0]._all([]).map((n) => n.textContent).join("");
    ok("标准档的读数行报的是检索自己算的档（rlv 2）、注明未按此加深，不更新条", /难度 2\/5·常/.test(txt2) && /标准档（未按此加深）/.test(txt2) && fx.last().lv === 4, txt2);
    const cell3 = { turn: new N("div"), a: new N("div") }; cell3.turn.appendChild(cell3.a);
    fx.line(cell3, { lv: 0, on: false, deep: false, rlv: 0, hits: 0 });
    ok("一档都算不出（检索空）的标准档不出读数行", cell3.turn.children.length === 1);
    fx.mode("std"); fx.paint();
    ok("切回标准档：整条隐藏", grade.style.display === "none");
  }
}

console.log("\n" + (fail ? "✗ " : "✓ ") + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
