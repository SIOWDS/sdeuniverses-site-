/* sim_chatsde_sentry.js —— ChatSDE「三刀·主动接地」重建（2026-08-31；撤 08-23「不去站外」）
 *
 * 三刀：① 占位哨 nbrSentry（真查站外占位者、事前摆进 system）② 远域结构 FAR_STRUCTS（24 门带判据的表）
 *       ③ 预注册卡 PREREG_BLOCK（带真日期的卡→判断账）。只在 _plain（普通 SDE 对话）挂，每轮跑。
 * 五节：一 抠真函数跑（不复制平行实现）；二 WDS_CHAT_SYS 装配（桩真跑：extras/sentryCtx 落进普通路、
 *       早返回路一个都不落）；三 端点接线；四 前端摘卡真跑；五 反向验证（删承重内容，逐条见红）。
 * 跑法：node tools/sim_chatsde_sentry.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");
const SRC = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");
const FE = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");
let pass = 0, fail = 0;
const ok = (n, c, d) => { if (c) { pass++; console.log("  \u2713 " + n); } else { fail++; console.log("  \u2717 " + n + (d ? ("  " + d) : "")); } };

function fnOf(src, name) { const i = src.indexOf("function " + name + "("); if (i < 0) return ""; const j = src.indexOf("\n}", i); return j < 0 ? "" : src.slice(i, j + 2); }

/* 抠三刀那一整块（FAR_STRUCTS…sentrySeedOf 连着一段）+ 依赖 _lhash，一起真跑——走真正的那条路 */
function buildBox(src) {
  const iS = src.indexOf("const FAR_STRUCTS = [");
  const iSeed = src.indexOf("function sentrySeedOf(");
  const iE = src.indexOf("\n}", iSeed);
  if (iS < 0 || iSeed < 0 || iE < 0) return null;
  const CHUNK = src.slice(iS, iE + 2);
  const lh = fnOf(src, "_lhash");
  try {
    return new Function(lh + "\n" + CHUNK + "\nreturn { FAR_STRUCTS, farPick, farBlock, PREREG_BLOCK, nbrSentryBlock, sentrySeedOf };")();
  } catch (e) { return { _err: String(e && e.message) }; }
}

console.log("\n\u4e00\u3001\u4e09\u5200\u7684\u7eaf\u4ef6\uff08\u62a0\u771f\u51fd\u6570\u8dd1\uff09");
const B = buildBox(SRC);
ok("FAR_STRUCTS/farPick/farBlock/PREREG_BLOCK/nbrSentryBlock/sentrySeedOf 抠得出并装起来", !!(B && !B._err && B.farPick), B && B._err);
if (B && !B._err) {
  // 刀② 远域
  ok("FAR_STRUCTS 恰 24 门，每门都有 d/s/j/k", B.FAR_STRUCTS.length === 24 && B.FAR_STRUCTS.every((f) => f.d && f.s && f.j && Array.isArray(f.k) && f.k.length), "n=" + B.FAR_STRUCTS.length);
  const p1 = B.farPick("语言习得的本质", 0, "语言习得的本质");
  const p1b = B.farPick("语言习得的本质", 0, "语言习得的本质");
  ok("farPick 确定性（同 seed/rot/topic 同结果）", p1 && p1b && p1.d === p1b.d, p1 && p1.d);
  const rots = [0, 1, 2, 3, 4].map((r) => B.farPick("同一个题", r, "同一个题").d);
  ok("farPick 随轮转会换门（5 轮里至少 3 门不同）", new Set(rots).size >= 3, rots.join("/"));
  // 跳过同域：题目里带某门关键词，那门不许被选中
  let skipHit = 0;
  ["免疫系统怎么工作", "金属腐蚀防护", "晶体材料结构", "会计记账原则"].forEach((tp) => {
    for (let r = 0; r < 24; r++) { const f = B.farPick(tp, r, tp); if (f.k.some((w) => tp.indexOf(w) >= 0)) skipHit++; }
  });
  ok("farPick 跳过同域（题目落在哪门就永不选它）", skipHit === 0, "命中 " + skipHit + " 次");
  const fb = B.farBlock(p1);
  ok("farBlock 含所选门的 学科/结构/判据", fb.indexOf(p1.d) >= 0 && fb.indexOf(p1.s) >= 0 && fb.indexOf(p1.j) >= 0);
  ok("farBlock 含四条硬规矩（搬结构不搬词/说不通比硬说通/名词当形容词/不留正文）",
    fb.indexOf("搬结构不搬词") >= 0 && fb.indexOf("说不通比硬说通有用") >= 0 && fb.indexOf("当形容词用") >= 0 && fb.indexOf("不留在正文") >= 0);
  ok("farBlock(null) 返回空串（没挑到就不挂）", B.farBlock(null) === "");
  // 刀③ 预注册
  ok("PREREG_BLOCK 含五栏（假设/数据源/判据/算输/截止）与真日期格式", ["假设", "数据源", "判据", "算输", "截止", "YYYY-MM-DD"].every((w) => B.PREREG_BLOCK.indexOf(w) >= 0));
  ok("PREREG_BLOCK 含『一轮最多一张』与『空心卡比不出更坏』", B.PREREG_BLOCK.indexOf("一轮最多一张") >= 0 && B.PREREG_BLOCK.indexOf("比不出更坏") >= 0);
  ok("PREREG_BLOCK 要求自定阈值标『本卡自定，待校准』", B.PREREG_BLOCK.indexOf("本卡自定，待校准") >= 0);
  // 刀① 占位哨 事前块
  const ncGood = { ok: true, reason: "", passes: [{ k: "同向占位", n: 2 }, { k: "对立者", n: 1 }, { k: "外圈学科", n: 1 }], items: [
    { t: "Some Prior Work on X", u: "https://a.org/1", s: "摘要一", m: "2019", d: "", pass: "同向占位" },
    { t: "A Rival Account", u: "https://b.org/2", s: "摘要二", m: "2021", d: "", pass: "对立者" } ] };
  const sbG = B.nbrSentryBlock(ncGood, false);
  ok("nbrSentryBlock 含标题『已经有人占过这块地』与两条占位者标题", sbG.indexOf("已经有人占过这块地") >= 0 && sbG.indexOf("Some Prior Work on X") >= 0 && sbG.indexOf("A Rival Account") >= 0);
  ok("nbrSentryBlock 要求『优先用这些真实占位者，别只凭记忆』", sbG.indexOf("优先用这些真实占位者") >= 0 && sbG.indexOf("别只凭记忆") >= 0);
  ok("nbrSentryBlock 明写『本轮已替你联网查过·不必联网那条不再适用』（撤 08-23）", sbG.indexOf("本轮已替你联网查过") >= 0 && sbG.indexOf("对这一答不再适用") >= 0);
  ok("nbrSentryBlock 缓存命中标『缓存』", B.nbrSentryBlock(ncGood, true).indexOf("缓存") >= 0);
  const ncBad = { ok: false, reason: "neighbor_insufficient", passes: [{ k: "同向占位", n: 1 }, { k: "对立者", n: 0 }], items: [{ t: "Only One Side", u: "https://c.org/3", s: "s", m: "", d: "", pass: "同向占位" }] };
  const sbB = B.nbrSentryBlock(ncBad, false);
  ok("覆盖不足时块里写『覆盖不足』且『不许拿它当全站无人提出的证据』", sbB.indexOf("覆盖不足") >= 0 && sbB.indexOf("不许拿它当") >= 0 && sbB.indexOf("全站无人提出") >= 0);
  // 种子回退
  ok("sentrySeedOf：正常实问原样用", B.sentrySeedOf("康德二律背反怎么解", []) === "康德二律背反怎么解");
  ok("sentrySeedOf：『继续』退到本场第一句实问", B.sentrySeedOf("继续", [{ role: "reader", text: "什么是幸福律" }, { role: "wds", text: "..." }]) === "什么是幸福律");
  ok("sentrySeedOf：『嗯嗯』也算填充词、会回退", B.sentrySeedOf("嗯嗯", [{ role: "reader", text: "语言是如何发生的" }]) === "语言是如何发生的");
  ok("sentrySeedOf：全是填充、历史里也没实问 → 返回短串（外面会因 <6 跳过）", B.sentrySeedOf("嗯", []).length < 6);
  ok("sentrySeedOf：认 user/content 两种字段名", B.sentrySeedOf("继续", [{ role: "user", content: "艺术为何需要边界" }]) === "艺术为何需要边界");
}

/* ═══ 二、WDS_CHAT_SYS 装配（桩真跑：只验 extras/sentryCtx 落点，块内容用桩） ═══ */
console.log("\n\u4e8c\u3001WDS_CHAT_SYS \u88c5\u914d\uff08\u6869\u771f\u8dd1\uff09");
function buildSys(src) {
  const fn = fnOf(src, "WDS_CHAT_SYS");
  if (!fn) return null;
  const stubs = [
    'const DUEL_ROLES = { A: 1 };',
    'function WDS_DUEL_SYS(){ return "DUEL_STUB"; }',
    'function WDS_IQ_SYS(){ return "IQ_STUB"; }',
    'function resIsJudge(rs){ return !!(rs && rs.judgeTest); }',
    'function WDS_RES_JUDGE_SYS(){ return "JUDGE_STUB"; }',
    'function WDS_PLAIN_SYS(){ return "PLAIN_STUB"; }',
    'const LANG_TRIAD_BLOCK = "LTRIAD", SDE_TRIAD_BLOCK = "STRIAD";',
    'const LANG_PLATFORM_BLOCK = "LPLAT", SDE_PLATFORM_BLOCK = "SPLAT";',
    'const SDE_METHOD_BLOCK = "MBLOCK", SDE_METHOD_LITE = "MLITE";',
    'function wdsToolSys(){ return "TOOL_STUB"; }',
    'function wdsForgeSys(){ return "FORGE_STUB"; }',
    'function wdsResearchSys(){ return "RESEARCH_STUB"; }',
  ];
  try { return new Function(stubs.join("\n") + "\n" + fn + "\nreturn WDS_CHAT_SYS;")(); } catch (e) { return { _err: String(e && e.message) }; }
}
const W = buildSys(SRC);
ok("WDS_CHAT_SYS 抠得出并（带桩）装起来", typeof W === "function", W && W._err);
if (typeof W === "function") {
  const plain = W("R", "M", "SITE", "", false, "", "", "zh", "", "", null, null, null, false, "EXTRAS_MARK", "SENTRY_MARK");
  ok("普通对话：extras 落进 system", plain.indexOf("EXTRAS_MARK") >= 0);
  ok("普通对话：sentryCtx 落进 system", plain.indexOf("SENTRY_MARK") >= 0);
  ok("sentryCtx 在来料区（在 docCtx／about 之前）", plain.indexOf("SENTRY_MARK") < (plain.indexOf("EXTRAS_MARK")));
  ok("extras 在这一轮的活区（在产线 stub 之后）", plain.indexOf("EXTRAS_MARK") > plain.indexOf("RESEARCH_STUB"));
  // 早返回路：三刀一个都不许落
  const iq = W("R", "M", "", "", false, "", "", "zh", "", "iq", null, null, null, false, "EXTRAS_MARK", "SENTRY_MARK");
  ok("tool=iq（评分）早返回：extras/sentryCtx 都不落", iq === "IQ_STUB" || (iq.indexOf("EXTRAS_MARK") < 0 && iq.indexOf("SENTRY_MARK") < 0));
  const duel = W("R", "M", "", "", false, "", "", "zh", "", "", null, { role: "A" }, null, false, "EXTRAS_MARK", "SENTRY_MARK");
  ok("三家对撞早返回：不落", duel.indexOf("EXTRAS_MARK") < 0 && duel.indexOf("SENTRY_MARK") < 0);
  const nosde = W("R", "M", "", "", false, "", "", "zh", "", "", null, null, null, true, "EXTRAS_MARK", "SENTRY_MARK");
  ok("无 SDE 早返回：不落", nosde.indexOf("EXTRAS_MARK") < 0 && nosde.indexOf("SENTRY_MARK") < 0);
  const judge = W("R", "M", "", "", false, "", "", "zh", "", "", { judgeTest: 1 }, null, null, false, "EXTRAS_MARK", "SENTRY_MARK");
  ok("研究判官早返回：不落", judge.indexOf("EXTRAS_MARK") < 0 && judge.indexOf("SENTRY_MARK") < 0);
}

/* ═══ 三、端点接线（/api/wds/chat） ═══ */
console.log("\n\u4e09\u3001\u7aef\u70b9\u63a5\u7ebf");
ok("端点定义 _plain（无 tool/产线/对撞/领域档案/无SDE）", /const _plain = !noSde && !tool && !duel && !prof && !\(rsRaw && \(rsRaw\.forge \|\| rsRaw\.sde\)\)/.test(SRC));
ok("端点定义 noSentry 关阀（默认开）", /const noSentry = b\.nosentry === 1 \|\| b\.nosentry === true;/.test(SRC));
ok("sentryOn = _plain && !noSite && !canSee && !noSentry", /const sentryOn = _plain && !noSite && !canSee && !noSentry;/.test(SRC));
ok("占位哨真查：sentryOn 且种子≥6 才 nbrChain（普通对话真走链）", /if \(sentryOn && _plainSeed\.length >= 6\)/.test(SRC) && /nbrChain\(env, _plainSeed,/.test(SRC));
ok("占位哨缓存：caches.default 30 分钟、空结果不入缓存", /caches\.default\.match\(_ck\)/.test(SRC) && /max-age=1800/.test(SRC) && SRC.indexOf("空结果不入缓存") >= 0);
ok("占位哨发 t:sentry 帧", /t: "sentry"/.test(SRC));
ok("远域/预注册只在 _plain 装配，发 t:far 帧", /if \(_plain\) \{\n\s*const _far = farPick\(_plainSeed \|\| q,/.test(SRC) && /t: "far"/.test(SRC));
ok("调用点把 extras, sentryCtx 传进 WDS_CHAT_SYS", /WDS_CHAT_SYS\(reflect, SDEM,[^\n]*noSde, extras, sentryCtx\)/.test(SRC));
ok("STOCK/FIVE/LEDGER 三块未删（每轮自报的底线仍在）", SRC.indexOf("const SDE_METHOD_STOCK") >= 0 && SRC.indexOf("const SDE_METHOD_LEDGER") >= 0 && SRC.indexOf("const SDE_METHOD_FIVE") >= 0);

/* ═══ 四、前端摘卡真跑（pregTake） ═══ */
console.log("\n\u56db\u3001\u524d\u7aef\u6458\u5361\u771f\u8dd1");
function buildPreg(fe) {
  const iRe = fe.indexOf("var PREG_RE =");
  const iFn = fe.indexOf("function pregRender(");
  const iEnd = fe.indexOf("\n  }", iFn);
  if (iRe < 0 || iFn < 0 || iEnd < 0) return null;
  const CH = fe.slice(iRe, iEnd + 4);
  // pregRender 里用了 el/LANG/localStorage —— 只需要 pregTake，给它一个不触发 pregRender 的壳
  try { return new Function(CH.replace(/function pregRender[\s\S]*$/, "") + "\nreturn { pregTake: pregTake, PREG_RE: PREG_RE };")(); } catch (e) { return { _err: String(e && e.message) }; }
}
const PB = buildPreg(FE);
ok("前端 pregTake 抠得出并装起来", !!(PB && !PB._err && PB.pregTake), PB && PB._err);
if (PB && !PB._err) {
  const ans = "正文一段。\n〔预注册〕假设：文凭溢价三年内收窄 ｜ 数据源：某劳动力调查 ｜ 判据：溢价率下降 ｜ 算输：若溢价不降则本判断错 ｜ 截止：2027-06-30";
  const c = PB.pregTake(ans);
  ok("真卡：假设/数据源/算输/截止 都抠得出", c && c.hypo.indexOf("文凭溢价") >= 0 && c.src.indexOf("劳动力调查") >= 0 && c.lose.indexOf("则本判断错") >= 0 && c.due === "2027-06-30", c && JSON.stringify(c));
  ok("真卡：正文里那一行被剥净（body 不含〔预注册〕）", c && c.body.indexOf("〔预注册〕") < 0 && c.body.indexOf("正文一段") >= 0);
  const empty = PB.pregTake("正文。\n〔预注册〕假设：视情况 ｜ 数据源：有待研究 ｜ 判据：无 ｜ 算输：视情况 ｜ 截止：未来某天");
  ok("空心卡：判定 empty（剥掉但不摆）", empty && empty.empty === true);
  ok("没卡：返回 null", PB.pregTake("就是一段普通回答，没有卡。") === null);
}
ok("前端有 renderSentry / renderFar 两个渲染函数", FE.indexOf("function renderSentry(") >= 0 && FE.indexOf("function renderFar(") >= 0);
ok("前端 SSE 分发接了 sentry / far", /else if \(j\.t === "sentry"\)/.test(FE) && /else if \(j\.t === "far"\)/.test(FE));
ok("前端 payload 带 nosentry；有占位哨关阀钮 data-k='nosentry'", /nosentry: \(sentryOnUI \? 0 : 1\)/.test(FE) && FE.indexOf("data-k='nosentry'") >= 0);
ok("finish() 里剥预注册卡并渲染判断账", FE.indexOf("var _preg = pregTake(answer);") >= 0 && FE.indexOf("pregRender(cell, _preg)") >= 0);

/* ═══ 五、反向验证：删承重内容，逐条必须见红（不是改标签） ═══ */
console.log("\n\u4e94\u3001\u53cd\u5411\u9a8c\u8bc1\uff08\u5220\u627f\u91cd\u5185\u5bb9\uff0c\u9010\u6761\u89c1\u7ea2\uff09");
function mustRed(name, mutSrc, probe) {
  let red = false;
  try { red = !probe(mutSrc); } catch (e) { red = true; }
  ok("删『" + name + "』后该测见红", red);
}
// M1 装配：删 WDS_CHAT_SYS 里 sentryCtx 那一行 → SENTRY 不落
mustRed("+ (sentryCtx || \"\")", SRC.replace('    + (sentryCtx || "")\n', ""), (ms) => {
  const w = buildSys(ms); return typeof w === "function" && w("R", "M", "S", "", false, "", "", "zh", "", "", null, null, null, false, "EX", "SEN").indexOf("SEN") >= 0;
});
// M2 装配：删 extras 那一行 → EXTRAS 不落
mustRed("+ (extras || \"\")", SRC.replace('    + (extras || "")\n', ""), (ms) => {
  const w = buildSys(ms); return typeof w === "function" && w("R", "M", "S", "", false, "", "", "zh", "", "", null, null, null, false, "EX", "SEN").indexOf("EX") >= 0;
});
// M3 远域：删 farPick 里跳过同域那一行 → 同域会被选中
mustRed("farPick 跳过同域", SRC.replace('  const pool = FAR_STRUCTS.filter((f) => !f.k.some((w) => t.indexOf(String(w).toLowerCase()) >= 0)); // 题目落在哪门就跳过哪门\n', '  const pool = [];\n'), (ms) => {
  const b = buildBox(ms); if (!b || b._err) return true; let hit = 0;
  for (let r = 0; r < 24; r++) { const f = b.farPick("免疫系统怎么工作", r, "免疫系统怎么工作"); if (f.k.some((w) => "免疫系统怎么工作".indexOf(w) >= 0)) hit++; }
  return hit === 0;   // 修复态：命中 0；改坏后必 >0 ⇒ 这里返回 false ⇒ 见红
});
// M4 种子：删回退循环 → 『继续』不再退到实问
mustRed("sentrySeedOf 回退循环", SRC.replace(/  for \(const m of hist\) \{[\s\S]*?\n  \}\n/, ""), (ms) => {
  const b = buildBox(ms); if (!b || b._err) return true;
  return b.sentrySeedOf("继续", [{ role: "reader", text: "什么是幸福律" }]) === "什么是幸福律";
});
// M5 门控：删 sentryOn 里的 !noSite → 共创台也会触发占位哨
mustRed("sentryOn 的 !noSite", SRC.replace("const sentryOn = _plain && !noSite && !canSee && !noSentry;", "const sentryOn = _plain && !canSee && !noSentry;"), (ms) => /const sentryOn = _plain && !noSite &&/.test(ms));
// M6 占位哨块：删『优先用这些真实占位者』承重句
mustRed("nbrSentryBlock『优先用这些真实占位者』", SRC.replace("**这一答的『已有说法』一栏，优先用这些真实占位者，别只凭记忆补人名年份。**", ""), (ms) => {
  const b = buildBox(ms); if (!b || b._err) return true;
  return b.nbrSentryBlock({ ok: true, passes: [], items: [{ t: "x", u: "u", s: "s", pass: "同向占位" }] }, false).indexOf("优先用这些真实占位者") >= 0;
});
// M7 预注册：删真日期格式 YYYY-MM-DD
mustRed("PREREG 真日期格式", SRC.replace(/YYYY-MM-DD/g, "\u67d0\u5929"), (ms) => {
  const b = buildBox(ms); if (!b || b._err) return true; return b.PREREG_BLOCK.indexOf("YYYY-MM-DD") >= 0;
});
// M8 端点：删 t:sentry 发帧
mustRed("端点 t:sentry 发帧", SRC.replace(/t: "sentry"/g, 't: "sentryX"'), (ms) => /t: "sentry"/.test(ms) && /nbrChain\(env, _plainSeed,/.test(ms));
// M9 调用点：把两个新参去掉 → 传输契约断
mustRed("调用点传 extras, sentryCtx", SRC.replace(", noSde, extras, sentryCtx);", ", noSde);"), (ms) => /noSde, extras, sentryCtx\);/.test(ms));

console.log("\n" + (fail ? ("\u2717 " + fail + " FAIL / " + pass + " PASS") : ("\u2713 ALL " + pass + " PASS")));
process.exit(fail ? 1 : 0);
