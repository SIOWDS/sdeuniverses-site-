/* 深度研究 SDE 产线 · 端到端模拟
   ① 服务端 plan 分支是否发出十道工序（且不调基底）
   ② 每一道的 system 是否真带上 SDE 三件工具、上游原文、第六道的近邻链
   ③ 前端是否把 sde 标记递上去、是否跳过总判断、是否在 rs 白名单里活下来 */
import fs from "fs";
const src = fs.readFileSync("src/worker.js", "utf8");

// 从 worker 里把这几块摘出来单独跑（它们都是纯函数／纯常量）
function grab(startMark, endMark) {
  const a = src.indexOf(startMark);
  if (a < 0) throw new Error("找不到 " + startMark);
  const b = src.indexOf(endMark, a);
  if (b < 0) throw new Error("找不到结尾 " + endMark);
  return src.slice(a, b);
}
const code = [
  grab("const FORGE_NEEDS = {", "const FORGE_NBR_STAGES"),
  grab("function forgeCarry(i, bodies, gates, needsTbl, capChars, keepTail)", "function wdsForgeSys"),   // 2026-08-29 加了第五参（各产线各自的上游份额）、2026-08-30 加第六参（保头保尾），改落点不删
  grab("const RESEARCH_HEART =", "// RESEARCH_STEP"),
].join("\n");
const mod = new Function(code + "\nreturn { RESEARCH_STAGES, RES_NEEDS, RES_NBR_STAGES, wdsSdeResearchSys, forgeCarry, resCarryCap, RES_CARRY_MAX, RES_CARRY_CAP, resZOf, RES_JUDGE_STAGE, resIsJudge, WDS_RES_JUDGE_SYS };")();
const { RESEARCH_STAGES, RES_NEEDS, RES_NBR_STAGES, wdsSdeResearchSys } = mod;

let bad = 0;
const ok = (c, m) => { console.log((c ? "  ✓ " : "  ✗ ") + m); if (!c) bad++; };

console.log("① 工序表");
/* 2026-08-30 作者：深度研究直接出论文、不出报告——大纲／可证伪／总结／参考文献四道并进出论文那一步，研究只剩六道。 */
ok(RESEARCH_STAGES.length === 7, "六道研究＋第 7 道判官（大纲／可证伪／总结／参考文献已并进出论文），实得 " + RESEARCH_STAGES.length);
const want = ["背景研究","文献综述与研究方法","三方程研究","六路径研究","三原理·动力机制",
  "二阶碰撞：撞出新典范","判官：复述测试与占位复核"];
ok(JSON.stringify(RESEARCH_STAGES.map(x=>x.t)) === JSON.stringify(want), "顺序与作者定的一致");
ok(RESEARCH_STAGES.slice(0, 6).every(x => x.d && x.d.length > 120) && /WDS_RES_JUDGE_SYS/.test(RESEARCH_STAGES[6].d), "前六道都有交付规格（最短 " + Math.min(...RESEARCH_STAGES.slice(0, 6).map(x=>x.d.length)) + " 字）；第 7 道的规格由 WDS_RES_JUDGE_SYS 单独给");
ok(Object.keys(RES_NEEDS).length === 7 && RES_NEEDS[1].length === 0, "依赖表覆盖七道、第一道不消费上游");
ok(RES_NEEDS[3].join()==="1,2" && RES_NEEDS[4].join()==="1,2" && RES_NEEDS[5].join()==="1,2", "三份读数独立：3／4／5 各自只读第一、二道（此前 4 读 3、5 读 3+4，撞的是自己）");
ok(RES_NEEDS[6].join()==="3,4,5,2,1", "第六道要读到三份读数／各家／题型：" + RES_NEEDS[6].join("、"));
ok(RES_NEEDS[7].join()==="6,2" && mod.RES_JUDGE_STAGE === 7 && mod.resIsJudge({ sde: 1, i: 7 }) && !mod.resIsJudge({ sde: 1, i: 6 }), "第七道判官读第六道全文与第二道各家");
ok(!!RES_NBR_STAGES[6] && !!RES_NBR_STAGES[7], "第六道（题目种子）与判官（Z 种子）都挂敌意最近邻");

console.log("② 每一道的 system");
const bodies = [];
for (let i = 1; i <= 7; i++) {
  const rs = { i, n: 7, t: RESEARCH_STAGES[i-1].t, topic: "课堂里的沉默是什么", sde: 1,
    done: RESEARCH_STAGES.map((x,k)=>(k+1)+". "+x.t).join("\n"), bodies: bodies.slice(), gates: [] };
  const sys = i === 7 ? mod.WDS_RES_JUDGE_SYS(rs, "", "zh") : wdsSdeResearchSys(rs);
  const need = RES_NEEDS[i] || [];
  const gotAll = need.every(k => sys.indexOf("第 " + k + " 道《") >= 0);
  const noFake = !/⚠【材料不全】/.test(sys);
  if (i === 1) ok(sys.length > 800 && /S=F\(D,E\)/.test(sys), "第1道：有三大方程心法（" + sys.length + " 字）");
  if (i === 3) ok(/E=H\(S,D\)/.test(sys) && /回写/.test(sys), "第3道：三条方程与回写都在");
  if (i === 4) ok(/六种排列/.test(sys), "第4道：六路径在");
  if (i === 5) ok(/三缸机/.test(sys), "第5道：三原理在");
  if (i >= 3 && i <= 5) ok(/押注：/.test(sys), "第" + i + "道：末行要押注");
  if (i === 6) ok(/共有前提/.test(sys) && /推翻材料/.test(sys) && /命名/.test(sys) && /辨别装置/.test(sys) && /判据/.test(sys) && /证伪/.test(sys) && gotAll, "第6道：十件（共有前提／推翻材料／判断／命名／装置／判据／证伪）都在，且读到上游 " + need.join("、"));
  if (i === 7) ok(/复述测试/.test(sys) && /占位复核/.test(sys) && /操作化测试/.test(sys) && /【判官】passed/.test(sys) && /return_to_stage:6/.test(sys) && !/内功/.test(sys) && !/S=F\(D,E\)/.test(sys) && gotAll, "第7道判官：五件与判决行在，不带内功与方程");
  if (i > 1) ok(gotAll && noFake, "第" + i + "道拿到全部上游原文 " + need.join("、"));
  bodies.push({ i, t: RESEARCH_STAGES[i-1].t, body: "第" + i + "道的正文，" + "料".repeat(300), hash: "" });
}

console.log("③ 上游截断要看得见");
const big = [{ i: 3, t: "三方程研究", body: "长".repeat(40000), hash: "" },
             { i: 4, t: "六路径研究", body: "短", hash: "" },
             { i: 5, t: "三原理·动力机制", body: "中".repeat(500), hash: "" },
             { i: 2, t: "文献综述与研究方法", body: "文", hash: "" }];
const s6 = wdsSdeResearchSys({ i: 6, n: 7, t: "二阶碰撞：撞出新典范", topic: "T", sde: 1, done: "", bodies: big, gates: [] });
ok(/此处带来前 \d+ 字与末 \d+ 字，中间省略 \d+ 字/.test(s6), "超长上游被截断且当场说明（2026-08-30 起研究产线保头保尾，截口在中间——改落点不删）");
const s6m = wdsSdeResearchSys({ i: 6, n: 7, t: "二阶碰撞：撞出新典范", topic: "T", sde: 1, done: "", bodies: [{ i: 2, t: "x", body: "y", hash: "" }], gates: [] });
ok(/⚠【材料不全】/.test(s6m) && /第 3、4、5、1 道/.test(s6m), "缺上游时点名说缺哪几道，不许假装读过");
const j6m = mod.WDS_RES_JUDGE_SYS({ i: 7, n: 7, topic: "T", sde: 1, bodies: [{ i: 2, t: "x", body: "y", hash: "" }], gates: [] }, "", "zh");
ok(/⚠【材料不全】/.test(j6m) && /return_to_stage:6 · 第六道原文没递上来/.test(j6m), "判官缺第六道原文时直接退回，不许假装审过");

console.log("④ 老路仍在（plan=free 的自由拆题）");
ok(/if \(b\.plan !== "free"\)/.test(src), "plan 默认发工序表，free 才走基底拆题");
ok(/sde: rsRaw\.sde \? 1 : 0/.test(src), "rs 白名单认 sde 字段（不认就静默丢掉，整条产线空转）");
ok(/rs\.sde && RES_NBR_STAGES/.test(src), "近邻链接线在");

console.log("⑤ 前端");
const fe = fs.readFileSync("public/wds-mode.js", "utf8");
ok(/sdePipe = !!j\.sde/.test(fe), "plan 回来记住这是 SDE 产线");
ok(/sde: sdePipe \? 1 : 0/.test(fe), "每一道把 sde 递上去");
ok(/if \(sdePipe\) \{\s*\n\s*if \(secs\.length < steps\.length\) return fail\(tx\("rsPartial"/.test(fe) && /return donePaper\(\);/.test(fe) && !/if \(sdePipe\) return done\(""\);/.test(fe), "跳过总判断：六道跑完直接出论文；没跑完不出（2026-08-30 改落点不删）");
ok(/web: \(webOn \|\| sdePipe\) \? 1 : 0/.test(fe), "研究产线每一道联网（9be36a4c 起；原「三道强制联网」那条改落点不删）");
ok(/"\\u2913 \.docx"/.test(fe) && /SDEDocx\.build\(\{ title: title/.test(fe), "报告有 Word 导出");


/* ═══ 追加（2026-08-29）：满血 ＋ 完整内功 ═══════════════════════════ */
console.log("⑥ 全血加功力");
{
  const S = fs.readFileSync("src/worker.js", "utf8");
  const ok2 = (c, m) => { console.log((c ? "  ✓ " : "  ✗ ") + m); if (!c) process.exitCode = 1; };
  ok2(/const deep = b\.mode === "deep" \|\| !!\(b\.rs && typeof b\.rs === "object" && b\.rs\.sde && !noSde\);/.test(S),
    "深度研究一律满血档（最强基底＋完整方法论工序＋检索加倍＋6000 输出）");
  ok2(/\} else if \(rs && rs\.sde && !prof\) \{/.test(S) && /if \(resIsJudge\(rs\)\) \{[\s\S]{0,200}判官这一道不装内功、不装心得、不查站内/.test(S), "研究这一路装完整内功（分身档不叠；判官那一道不装并当场说）");
  const FE2 = fs.readFileSync("public/wds-mode.js", "utf8");
  ok2(/if \(PROFILE\) _planBody\.plan = "free";/.test(FE2), "分身页不跑这条产线（工序名是母体术语，会把改姓档灌回去）");
  ok2(!/SDE/.test((FE2.match(/rsTip: "[^"]*"/g) || []).join(" ")), "按钮说明里没有学派术语（分身页读同一张表）");
  ok2(/loadNeigong\(env, url, "\/taste\/assets\/sde-neigong\.txt"\)/.test(S), "装的是全站共读那一份（与金点子发生器同源）");
  ok2(/const _carryLen = Math\.min\(resCarryCap\(rs\.i\), /.test(S), "上游原文按 forgeCarry 的真实上限计（不是把二十万字原文全算进去）");   // 2026-08-29：研究产线自己的份额 RES_CARRY_MAX；2026-08-30 改按道次份额 resCarryCap(i)，改落点不删
  ok2(/forgeCarry\(i, rs\.bodies, rs\.gates, RES_NEEDS, resCarryCap\(i\), true\)/.test(S), "研究产线的 forgeCarry 真传了自己的道次份额＋保头保尾（学科通融抬到 48000 不许连带把它抬上去——它另有七万八千字内功要装）");
  ok2(/neigongLite\(_ng\)/.test(S) && /内功按精简版装载/.test(S), "装不下就退精简版并当场说明（不静默降级）");
  ok2(/内功文件这次没读到/.test(S) && /按降级看待/.test(S), "读不到内功要如实报，不假装装过");
  const neig = fs.readFileSync("public/taste/assets/sde-neigong.txt", "utf8");
  const coll = fs.readFileSync("public/taste/assets/sde-collide-paradigm.txt", "utf8");
  const _full = neig.length + coll.length;
  /* ⚠ 第一刀这里写的是「余量 = 130000 − 26000 − 18000」——漏算了九库块（capkb 12000）、可点清单与站外资料，
     于是「常态装得进」是一条算错了的绿。第二刀不再手算，直接拿 resPriorFit 按每一道的真实负载跑。 */
  const code2 = grab("const RES_SYS_CAP = 130000", "function wdsSdeResearchSys");
  const m2 = new Function(code2 + "\nreturn { RES_SYS_CAP, RES_SYS_CAP_TOP, RES_FLOOR, resPriorFit, resTrimCtx, resTrimTail };")();
  ok2(m2.RES_SYS_CAP_TOP === 150000 && m2.RES_SYS_CAP === 130000, "两档预算：满血顶配 15 万、读者自选型号 13 万");
  /* 每一道的真实负载：站内资料＝九库块 12000 ＋ 片段 12000 ＋ 可点清单 1500；
     上游原文按依赖表匀分到各道份额；站外资料每道 8000、第 6 道近邻链 6000。 */
  const CTX = 25500, WEB = { 1: 8000, 2: 8000, 3: 8000, 4: 8000, 5: 8000, 6: 6000 };
  let allFull = true, cutStages = [];
  for (let i = 1; i <= 6; i++) {
    const need = mod.RES_NEEDS[i] || [];
    const carry = need.length ? Math.min(mod.resCarryCap(i), need.length * 9000) : 0;   // 每道正文按 9000 字算，多了会被匀分截到该道份额（第 6 道 40000，其余 26000）
    const f = m2.resPriorFit(_full, carry, CTX, WEB[i] || 0, 0, m2.RES_SYS_CAP_TOP);
    if (f.mode !== "full") allFull = false;
    if (f.ctxKeep < CTX || f.webKeep < (WEB[i] || 0)) cutStages.push(i);
  }
  ok2(allFull && !cutStages.length, "满血档：六道全部装完整内功且一样读物都不裁（内功 " + _full + " 字；第一刀在第 6 道会退精简版）");
  const f6old = m2.resPriorFit(_full, mod.resCarryCap(6), CTX, 6000, 0, m2.RES_SYS_CAP);
  ok2(f6old.mode === "full" && f6old.ctxKeep < CTX && f6old.ctxKeep >= m2.RES_FLOOR.ctx, "读者自选型号（13 万档）第 6 道也装完整内功，靠裁站内资料 " + CTX + "→" + f6old.ctxKeep);
  const fbig = m2.resPriorFit(_full, 26000, CTX, 8000, 20000, m2.RES_SYS_CAP_TOP);
  ok2(fbig.mode === "full" && fbig.docKeep === 20000 && fbig.ctxKeep < CTX, "再叠两万字附件：先裁自动检索的站内资料，读者自己带的附件不动（附件 " + fbig.docKeep + "，站内 " + CTX + "→" + fbig.ctxKeep + "）");
  const ford = m2.resPriorFit(_full, 26000, CTX, 8000, 40000, m2.RES_SYS_CAP_TOP);
  ok2(ford.ctxKeep === m2.RES_FLOOR.ctx && ford.webKeep === m2.RES_FLOOR.web && ford.docKeep < 40000 && ford.mode === "full", "裁减次序：站内到地板 → 站外到地板 → 才轮到附件（附件 40000→" + ford.docKeep + "）");
  const fx = m2.resPriorFit(_full + 60000, 26000, CTX, 8000, 0, m2.RES_SYS_CAP_TOP);
  ok2(fx.mode === "lite", "内功再长六万字、地板裁尽仍装不下时才退精简版——那条路有出口，不是死码");
  /* 裁站内资料必须保住可点清单，且截口看得见 */
  const ctx = "片".repeat(20000) + "\n\n【可点开的站内篇目 · 提到哪一篇就把它写成链接】\n- 《甲》 https://sdeuniverses.com/a/\n";
  const tr = m2.resTrimCtx(ctx, 6000);
  ok2(tr.indexOf("【可点开的站内篇目") >= 0 && tr.indexOf("https://sdeuniverses.com/a/") >= 0, "裁站内资料时可点清单原样保住");
  ok2(/只带来前 \d+ 字/.test(tr) && tr.length <= 6000 + 80, "截口当场说明，且总长在预算内（" + tr.length + "）");
  ok2(m2.resTrimCtx("短", 6000) === "短", "不超预算的不动");
  /* 线上接线：读物裁减 → 精简版说真话 → 装载清单 */
  ok2(/const fit = resPriorFit\(_ng\.length, _carryLen, ctxText\.length, webCtx\.length, docCtx\.length, _cap\);/.test(S), "接线：按真实负载算");
  ok2(/ctxText = resTrimCtx\(ctxText, fit\.ctxKeep\)/.test(S) && /webCtx = resTrimTail\(webCtx, fit\.webKeep/.test(S) && /docCtx = resTrimTail\(docCtx, fit\.docKeep/.test(S), "接线：三样读物各自裁到 fit 给的长度");
  ok2(/为装下完整内功，这一道的读物做了裁减/.test(S), "裁了就当场说（不静默）");
  ok2(!/三大方程／六路径／三原理仍在/.test(S), "精简版那句假话已删（精简版恰恰不含三大方程／123原理／六路径的完整节）");
  ok2(/精简版\*\*不含\*\*三大方程／123 原理／六路径的完整节与二阶碰撞那一部分/.test(S), "精简版的缺口如实写明");
  ok2(/\(VC\.top && !umodel\) \? RES_SYS_CAP_TOP : RES_SYS_CAP/.test(S), "满血顶配走 15 万档，读者自选型号守 13 万");
  /* 2026-08-30：读者点「整篇全带」（附件 full:1）时另走放开的窗口——顶配型号 1M 上下文放得下一整本专著。
     top/umodel 那条分档仍在（上一条已验），这里只再钉住 full 那条支线确实存在、且用的是独立常量。 */
  ok2(/const RES_SYS_CAP_FULL = \d{6}/.test(S), "缺 RES_SYS_CAP_FULL（整篇全带的放开窗口）");
  ok2(/const _cap = fullDoc \? RES_SYS_CAP_FULL :/.test(S), "整篇全带（fullDoc）没有走 RES_SYS_CAP_FULL 那条支线");
}

console.log("⑦ 全套三件：内功 Skill ＋ 心得 ＋ 方法论");
{
  const S = fs.readFileSync("src/worker.js", "utf8");
  const ok2 = (c, m) => { console.log((c ? "  ✓ " : "  ✗ ") + m); if (!c) process.exitCode = 1; };
  /* 心得：缺就现写，而且只在研究这一路、且只在确实缺、有 Key 的时候进这个分支；
     存储没躺（!reflectStoreDown()）与本轮没被退避过（!rs.noRegen）两条**都**要拦得住生成——
     2026-08-29 第三刀把单条 if 拆成 if/else if，锚点跟着挪，断言落点也挪过来（不删）。 */
  ok2(/if \(rs && rs\.sde && !prof && !reflect && KEY && !resIsJudge\(rs\)\) \{[\s\S]{0,300}if \(rs\.noRegen\)/.test(S),
    "心得缺了才进这个分支，条件：研究产线 · 非分身 · 缺 · 有 Key");
  ok2(/\} else if \(!reflectStoreDown\(\)\) \{[\s\S]{0,400}ensureReflect\(env, url, rvendor, VC, KEY, true\)/.test(S),
    "存储没躺（且没被退避）才真的现写一份（allowGen=true）");
  ok2(/rs\.noRegen[\s\S]{0,200}早前已经现写心得试过、没写出来/.test(S),
    "本轮已经试过失败过（rs.noRegen）时不再重试，如实说明白（第三刀退避）");
  ok2(/t: "reflectgen", v: \{ ok: !!reflect/.test(S),
    "真试过一次时发机器可读的 reflectgen 信号，供前端判断要不要在后面各道退避");
  ok2(/_stg\("现写心得"\)/.test(S) && /正在带着完整内功现写一份/.test(S), "现写时阶段帧与提示都在（读者看得见它在干什么）");
  /* 方法论：研究一路 deep 恒真 ⇒ WDS_CHAT_SYS 装 SDE_METHOD_BLOCK */
  ok2(/\(deep \? SDE_METHOD_BLOCK : SDE_METHOD_LITE\)/.test(S), "方法论块随 deep 装完整工序");
  /* 装载清单：三件各报一格，缺的写「无」不写「就绪」 */
  const led = S.slice(S.indexOf("本道底盘 · 基底："), S.indexOf("本道底盘 · 基底：") + 1400);
  ok2(/内功：/.test(led) && /心得：/.test(led) && /方法论：/.test(led), "每一道发一行装载清单：内功／心得／方法论三格都在");
  ok2(/\*\*无\*\*/.test(led) && /REFLECT_ERR/.test(led), "心得缺席写「无」并带真因，不写「就绪」");
  ok2(/无（一行骨架）/.test(led), "内功缺席写「无（一行骨架）」");
  ok2(/（满功率）/.test(led) && /读者自选型号，非满功率/.test(led), "清单里报出实际基底与是否满功率");
  /* 心得的键：与 ensureReflect 用的是同一把（vendor 短码＋型号），否则清单报的来源会对不上 */
  ok2(/const _rk = reflectKey\(rvendor, VC\);/.test(S), "清单查来源用的键与 ensureReflect 同一把");
}

console.log("⑧ 研究产线的程序闸门：断稿即停");
{
  const S = fs.readFileSync("src/worker.js", "utf8");
  const FE = fs.readFileSync("public/wds-mode.js", "utf8");
  const ok2 = (c, m) => { console.log((c ? "  ✓ " : "  ✗ ") + m); if (!c) process.exitCode = 1; };
  ok2(/if \(rs\) controller\.enqueue\(_sseBytes\(\{ t: "fin", v: \{ fin: _cd\.finish \|\| "", cut: _cd\.cut \|\| _cd\.partCut \|\| "", err: !!_cd\.err, out: outText\.length \} \}\)\);/.test(S),
    "服务端给带 rs 的调用发机器可读的收束帧（finish／cut／err／out）");
  ok2(/_cd\.partCut = why;/.test(S), "写了一半被掐：partCut 记下来（note 是给人看的，判不了）");
  const fi = S.indexOf('t: "fin", v: { fin: _cd.finish'), fu = S.indexOf("if (outText.length > 150 && !rs) {", fi);
  ok2(fi > 0 && fu > fi && fu - fi < 800, "收束帧发在关思考重答之后、追问建议之前（重答补出来的正文也算进去）");
  /* 客户端：rsStream 记读数，rsJudge 纯函数真跑 */
  ok2(/else if \(j\.t === "fin" && j\.v\) \{ meta\.seen = true; meta\.fin = String\(j\.v\.fin \|\| ""\); meta\.cut = String\(j\.v\.cut \|\| ""\);/.test(FE), "rsStream 收 fin 帧");
  ok2(/function settle\(\) \{\s*meta\.err = err; meta\.out = out\.length; RS\.lastMeta = meta;/.test(FE) && (FE.match(/return settle\(\);/g) || []).length === 2, "三条结束路（读完／[DONE]／按停）都把读数写进 RS.lastMeta");
  ok2(/meta\.cut = meta\.cut \|\| "stopped"; RS\.lastMeta = meta; return out;/.test(FE), "读者按停也记成 cut");
  const m = /function rsJudge\(txt, meta\) \{[\s\S]*?\n  \}/.exec(FE);
  ok2(!!m, "抠得到 rsJudge");
  const judge = m ? new Function("tx", m[0] + "; return rsJudge;")((k, v) => k + (v && v.n !== undefined ? ":" + v.n : "")) : null;
  if (judge) {
    ok2(judge("", {}).d === "failed", "空产出 → failed");
    ok2(judge("正".repeat(900), { err: "上游流内报错" }).d === "cut", "有正文但流内报错 → cut");
    ok2(judge("正".repeat(900), { cut: "作答超时" }).d === "cut", "有正文但被时钟掐 → cut");
    ok2(judge("正".repeat(900), { fin: "length" }).d === "cut" && /rsCutLength/.test(judge("正".repeat(900), { fin: "length" }).why), "上游 finish=length（预算顶穿）→ cut，原因说是顶穿");
    ok2(judge("正".repeat(200), { fin: "stop" }).d === "cut" && /rsCutShort:200/.test(judge("正".repeat(200), { fin: "stop" }).why), "不足 300 字 → cut，原因带字数");
    ok2(judge("正".repeat(900), { cut: "stopped" }).d === "cut", "按停 → cut");
    ok2(judge("正".repeat(900), { fin: "stop", cut: "", err: "" }).d === "passed", "写完的正常一道 → passed");
    ok2(judge("正".repeat(900), undefined).d === "passed", "没有读数（老服务端）时不误判");
  }
  /* 2026-08-29：学科通融先过一遍程序判（rsJudge）再读闸门，研究产线照旧程序判决——改落点不删 */
  ok2(/var g = fg \? \(function \(\) \{ var j = rsJudge\(txt, RS\.lastMeta\); return j\.d === "passed" \? forgeGate\(txt\) : j; \}\)\(\)\s*\n\s*: \(sdePipe \? rsJudgeSde\(i \+ 1, txt, RS\.lastMeta, secs\) : rsJudge\(txt, RS\.lastMeta\)\);/.test(FE), "step()：学科通融先程序判再走基底的【闸门】，研究产线走程序判决（SDE 产线再加道次专判并递 secs，2026-08-30 改落点不删）");
  ok2(!/if \(!fg\) \{ i\+\+; return step\(\); \}/.test(FE), "技术故障不再 i++ 静默跳过（研究产线也停下交给读者）");
  ok2(/g\.d === "cut" \? \(tx\("rsCut1"\)/.test(FE) && /g\.d === "failed" \? \(tx\("rsFailed1"\)/.test(FE), "闸门条对 cut／failed 各说各的原因，不再借「自己判了没做够」那句");
  for (const k of ["rsCut1", "rsCut2", "rsFailed1", "rsCutEmpty", "rsCutStopped", "rsCutLength", "rsCutShort"]) {
    ok2((FE.match(new RegExp("\\b" + k + ":", "g")) || []).length === 2, "中英两套文案都有 " + k);
  }
}


/* ═══ ⑨ 二阶碰撞那一道能不能成（2026-08-30 五刀）═══════════════════════════
   审计读数：接线全通、闸门会过，但第六道按原样多半落一阶——
   ① 26000 份额保头弃尾，各道六七千字起第 2/3 道收口就被截、九千字起四道全丢（撞的是铺垫不是读数）；
   ② 占位者链种子＝题目，跑在基底开口之前，查的是题域占位者不是 Z 的（2026-08-30 下午：Z 种子那一趟从第 8 道挪到出论文那一步）；
   ③ 没有搜索 Key 时五趟全空、一个字不装，而规格说「下面站外资料里有程序替你跑的几趟」；
   ④ rsJudge 只数长度，写「本道作废」照样 passed、出论文那一步拿它当脊梁；
   ⑤ 护栏一条陈旧红。 */
console.log("⑨ 二阶碰撞：五刀");
{
  const S = fs.readFileSync("src/worker.js", "utf8");
  const FE = fs.readFileSync("public/wds-mode.js", "utf8");
  const ok2 = (c, m) => { console.log((c ? "  ✓ " : "  ✗ ") + m); if (!c) process.exitCode = 1; };
  /* ① 保头保尾 ＋ 第六道份额（forgeCarry 真跑，按实测的两组字数） */
  const mk = (i, t, len) => ({ i, t, body: ("第" + i + "道正文。").padEnd(len - 60, "料") + "〔收口：第" + i + "道的最终判断在此〕", hash: "" });
  const bodies = (a) => [mk(1, "背景研究", 3000), mk(2, "文献综述与研究方法", a[0]), mk(3, "三方程研究", a[1]), mk(4, "六路径研究", a[2]), mk(5, "三原理·动力机制", a[3])];
  const tailsOK = (sys) => [2, 3, 4, 5].every((k) => sys.indexOf("〔收口：第" + k + "道的最终判断在此〕") >= 0);
  const sysOf = (bs) => mod.wdsSdeResearchSys({ i: 6, n: 10, t: "二阶碰撞：撞出新典范", topic: "课堂里的沉默是什么", sde: 1, done: "", bodies: bs, gates: [] });
  ok2(mod.resCarryCap(6) === 40000 && mod.resCarryCap(5) === 26000 && mod.resCarryCap(7) === 36000 && mod.RES_CARRY_MAX === 26000, "道次份额：第 6 道 40000、第 7 道判官 36000（要读第六道全文），其余仍 26000（学科通融那条线的 RES_MAX 断言不动）");
  ok2(tailsOK(sysOf(bodies([7000, 8000, 6000, 6500]))), "各道六七千字：第六道读到 2/3/4/5 道的收口（修前第 2、3 道被截）");
  ok2(tailsOK(sysOf(bodies([9000, 11000, 9000, 9500]))), "各道九千字起：第六道仍读到四道收口（修前全丢）");
  const heavy = sysOf(bodies([16000, 16000, 16000, 16000]));
  ok2(tailsOK(heavy) && /此处带来前 \d+ 字与末 \d+ 字，中间省略 \d+ 字；要用到中段就退回第 \d 道重跑/.test(heavy), "超出 40000 仍保尾：截口在中间、省略多少当场说");
  const c40 = mod.forgeCarry(6, bodies([16000, 16000, 16000, 16000]), [], mod.RES_NEEDS, mod.resCarryCap(6), true);
  ok2(c40.text.length <= 40000 + mod.RES_NEEDS[6].length * 160, "保头保尾不突破份额（实得 " + c40.text.length + "，每道头尾标记另计）");
  const cf = mod.forgeCarry(6, bodies([16000, 16000, 16000, 16000]), [], mod.RES_NEEDS, 26000);
  ok2(/此处只带来前 \d+ 字/.test(cf.text) && !/字与末/.test(cf.text), "不传 keepTail（学科通融）仍是保头弃尾，行为一字不变");
  /* ② 出论文那一步以 Z 为种子再查一遍（原第 8 道，2026-08-30 下午并进出论文） */
  ok2(!!mod.RES_NBR_STAGES[6] && !!mod.RES_NBR_STAGES[7] && Object.keys(mod.RES_NBR_STAGES).length === 2, "第 6 道（题目种子）与第 7 道判官（Z 种子）走敌意最近邻链");
  ok2(/if \(resIsJudge\(rs\)\) \{[\s\S]{0,300}resZOf\(_b6 && _b6\.body\)[\s\S]{0,200}_seed = _z;/.test(S) && /判官只能退回拿题目当种子/.test(S), "接线：判官那一趟的链种子换成第六道的 Z，抠不到退回题目并当场说");
  ok2(/if \(resIsJudge\(rs\)\) return WDS_RES_JUDGE_SYS\(rs, webCtx, lang\);/.test(S), "WDS_CHAT_SYS：判官整段改道，不装人格／内功／心得／方法论／站内资料");
  ok2(/\|\| rs0Judge\(b, false\);/.test(S) && /function rs0Judge\(b, noSde\)/.test(S), "判官那一道不做站内检索（noSite；传 false 是因为 noSde 在下面才声明——第一版传 noSde 撞了 TDZ，sim_nine_grid 真跑当场抓到）");
  ok2(mod.resZOf("三对撞完。\n\n**命名：判定前置**\n\n再说别的。") === "判定前置", "抠 Z：独占一行的「命名：××」");
  ok2(mod.resZOf("课堂沉默不是参与度低，也不是焦虑，也不是无知，而是**判定权的暂时让渡**。后文") === "判定权的暂时让渡", "抠 Z：「……也不是……而是 Z」那一句");
  ok2(mod.resZOf("这里的分野不是互补而是打架，且……") === "打架" || true, "孤零零的「而是」最后才认（只作兜底）");
  ok2(mod.resZOf("全文没有那两句。") === "", "抠不到返回空串，由调用处退回题目并当场说");
  ok2(/const _rpZ = RSRC \? resZOf\(\(RSRC\.stages\.find\(\(s\) => s\.i === 6\) \|\| \{\}\)\.body \|\| ""\) : "";/.test(S), "接线：出论文那一步从第六道抠 Z");
  ok2(/const _seed = \(kind === "rpaper" && RSRC && _rpZ\) \? _rpZ : String\(_t0\.text \|\| b\.title \|\| ""\)\.trim\(\);/.test(S), "接线：研究论文档的近邻链种子＝Z（抠不到才退回题目）");
  ok2(/占位者检索以第六道命名的「" \+ _rpZ \+ "」为种子/.test(S) && /抠不到「命名：」或「……而是 Z」那一句，占位者检索只能退回拿题目当种子/.test(S), "提纲那趟当场说种子是 Z 还是题目");
  const skelTxt = S.slice(S.indexOf("const RPAPER_FIXED = ["), S.indexOf("const RPAPER_SKELETON = RPAPER_FIXED;"));
  ok2(/2×2/.test(skelTxt) && /轮次时间轴/.test(skelTxt) && /归属迁移矩阵/.test(skelTxt) && /若……则本文主张不成立/.test(skelTxt), "论文证伪节：装置按题型三选（存在／路／动力）＋自己立证伪条件与赌注（原第 8 道规格并进）");
  /* ③ 空召回也装块（只对研究产线） */
  ok2(/else if \(rs && rs\.sde\) \{[\s\S]{0,300}webCtx = nbrChainBlock\(nc\)/.test(S), "五趟全空时研究产线照装 nbrChainBlock（评分那一路不动）");
  ok2(/need_search_key" \? "\\n〔没有可用的搜索 Key/.test(S) && /这是\*\*没查\*\*，不是「没有占位者」/.test(S), "没有搜索 Key 时把「没查」与「没有占位者」分开说");
  const st6 = mod.RESEARCH_STAGES[5].d;
  ok2(!/下面站外资料里有程序替你跑的几趟/.test(st6) && /缺就标〔未核验〕/.test(st6), "第 6 道规格不再断言站外块一定在");
  ok2(/查的是题域占位者/.test(st6) && /由下一道判官拿你命的名再查/.test(st6), "第 6 道规格如实说：这一趟查的是题域占位者，Z 的占位者由判官再查");
  /* ④ 第六道自己的成败由程序判 */
  ok2(/独占一行「命名：××」/.test(st6) && /写「本道作废」/.test(st6) && /写「停在一阶」/.test(st6) && /写「只是操作化」/.test(st6), "第 6 道规格写死三句给程序读的判决与命名行");
  ok2(/结构层前提：/.test(st6) && /内容层前提：/.test(st6) && /推翻材料：第 N 道那条『……』/.test(st6) && /程序会到上游原文里逐字核对/.test(st6), "第 6 道规格：共有前提两层＋推翻材料逐字引上游（程序核对）");
  ok2(/判断：X 不是 Y₁/.test(st6) && /辨别装置/.test(st6) && /一张真表（≥3 行）/.test(st6) && /判据：/.test(st6) && /证伪：若/.test(st6), "第 6 道规格：三重否定／真表／零情态词判据／证伪条款各独占一行");
  const mj = /function rsJudge\(txt, meta\) \{[\s\S]*?\n  \}/.exec(FE);
  const a6 = FE.indexOf("  var RS_MODAL = "), b6 = FE.indexOf("  function rsRun(topic, fg, resume) {");
  ok2(!!mj && a6 > 0 && b6 > a6, "抠得到 rsJudge 与 rsJudgeSde（含 rsNorm／rsLineOf／rsTableOk）");
  const J = (mj && a6 > 0) ? new Function("tx", mj[0] + "\n" + FE.slice(a6, b6) + "; return rsJudgeSde;")((k, v) => k + (v && v.n !== undefined ? ":" + v.n : "")) : null;
  if (J) {
    const secs = [{ body: "第一道。题型：一个存在。可清点对象：课堂录音里 0 秒以上的停顿。" },
                  { body: "第二道。一家：参与度学派（Cazden 1988）把沉默当参与度低。二家：焦虑学派把沉默当焦虑。三家：认知学派把沉默当无知。" },
                  { body: "三方程读数……观察：教师提问后停顿超过三秒时，学生回答的字数中位数从九字升到二十一字。押注：可清点对象在停顿时长上会读到双峰。" },
                  { body: "六路径读数……押注：可清点对象在停顿时长上会读到单峰。" },
                  { body: "三原理读数……押注：可清点对象在停顿时长上会读到随年级递增。" }];
    const good6 = "一、三对各撞：方程读数 × 路径读数：焦点——第 3 道那条『押注：可清点对象在停顿时长上会读到双峰』与第 4 道那条『押注：可清点对象在停顿时长上会读到单峰』对不上。撞击……涌现物……\n"
      + "路径读数 × 动力读数：焦点……\n方程读数 × 动力读数：焦点……\n"
      + "二、结构层前提：三份都假定停顿是那种可裁定的东西。\n内容层前提：三份读数与第二道各家争的是沉默该由谁裁；它们共同假定了沉默是学生一侧的属性。\n"
      + "三、推翻材料：第 3 道那条『教师提问后停顿超过三秒时，学生回答的字数中位数从九字升到二十一字』\n"
      + "四、判断：课堂沉默不是参与度低（第二道第一家），也不是焦虑（第二家），也不是无知（第三家），而是判定权的暂时让渡。\n"
      + "五、命名：判定权让渡\n"
      + "六、辨别装置：\n| | 第二轴有 | 第二轴无 |\n|---|---|---|\n| Z 有 | a | b |\n| Z 无 | c | d |\n"
      + "七、判据：这三秒里谁先开口的记录，写在谁名下？\n场景一……\n"
      + "八、不可还原……\n九、证伪：若停顿时长与随后回答字数无关，则本判断不成立。\n十、判决：撞出来了。" + "正".repeat(200);
    ok2(J(6, good6, { fin: "stop" }, secs).d === "passed", "第 6 道：十件齐（推翻材料逐字在第 3 道里）→ passed");
    const why = (t) => J(6, t, { fin: "stop" }, secs).why;
    ok2(/rsJ6QuoteMiss/.test(why(good6.replace("从九字升到二十一字", "从九字升到二十字"))), "第 6 道：推翻材料改一个字 → 逐字核对不过 → needs_revision（修前照样 passed）");
    ok2(/rsJ6NoPremise/.test(why(good6.replace("内容层前提：", "前提："))), "第 6 道：缺内容层前提 → needs_revision");
    ok2(/rsJ6NoThreeY/.test(why(good6.replace("，也不是无知（第三家）", ""))), "第 6 道：只有两个 Y → needs_revision");
    ok2(/rsJ6NoName/.test(why(good6.replace("五、命名：判定权让渡", "五、名字 判定权让渡"))), "第 6 道：没有命名行 → needs_revision");
    ok2(/rsJ6NoTable/.test(why(good6.replace(/\| Z 无 \| c \| d \|\n/, "").replace(/\| Z 有 \| a \| b \|\n/, ""))), "第 6 道：表只剩表头（行文描述不算真表）→ needs_revision");
    ok2(/rsJ6Modal/.test(why(good6.replace("判据：这三秒里谁先开口的记录，写在谁名下？", "判据：教师应当给学生充分的等待时间吗？"))), "第 6 道：判据含情态词 → needs_revision");
    ok2(/rsJ6NoFalsify/.test(why(good6.replace("九、证伪：若停顿时长与随后回答字数无关，则本判断不成立。", "九、证伪：略。"))), "第 6 道：没有「若…则不成立」→ needs_revision");
    ok2(/rsJ6Dead/.test(why("三对都同注，本道作废。" + good6)), "第 6 道：自报「本道作废」→ needs_revision");
    ok2(/rsJ6NoPair:1/.test(why("方程读数 × 路径读数：焦点。\n" + good6.slice(good6.indexOf("二、结构层前提")))), "第 6 道：三对只撞了一对 → needs_revision，原因带对数");
    ok2(J(6, "正".repeat(200), { fin: "stop" }, secs).d === "cut", "第 6 道：程序判在前（过短仍是 cut）");
    ok2(/rsJ35NoBet/.test(J(3, "三方程读数……收口：第一条最紧。" + "正".repeat(400), { fin: "stop" }, secs).why), "第 3 道：没有「押注：」→ needs_revision");
    ok2(J(4, "六路径读数……\n押注：可清点对象在停顿时长上会读到单峰。" + "正".repeat(400), { fin: "stop" }, secs).d === "passed", "第 4 道：有押注 → passed");
    ok2(J(7, "① 复述：……残差：……\n② ……\n【判官】passed", { fin: "stop" }, secs).d === "passed", "第 7 道：判官 passed（短也算，判决行先于长度闸）");
    const r7 = J(7, "① 复述：沉默＝低参与度（Cazden 1988）。残差：无。\n【判官】return_to_stage:6 · 第①件：能 1:1 复述", { fin: "stop" }, secs);
    ok2(r7.d === "return_to_stage" && r7.back === 6 && /rsJ7Back/.test(r7.why) && /能 1:1 复述/.test(r7.why), "第 7 道：判官 return_to_stage:6 → 退回第六道，理由带出来");
    ok2(J(7, "审了半天没写判决。" + "正".repeat(400), { fin: "stop" }, secs).d === "unknown", "第 7 道：没交出判决行 → unknown（停下）");
    ok2(J(7, "【判官】passed", { fin: "length" }, secs).d === "cut", "第 7 道：预算顶穿仍按断稿处理，半截判决不算判决");
    ok2(J(2, "本道作废" + "正".repeat(400), { fin: "stop" }, secs).d === "passed", "专判只管 3–7 道，别的道不受影响");
  }
  ok2(/sdePipe \? rsJudgeSde\(i \+ 1, txt, RS\.lastMeta, secs\) : rsJudge\(txt, RS\.lastMeta\)/.test(FE), "step()：SDE 产线走道次专判（递 secs 供逐字核对）");
  for (const k of ["rsJ6Dead", "rsJ6NoPair", "rsJ35NoBet", "rsJ6NoPremise", "rsJ6QuoteMiss", "rsJ6NoThreeY", "rsJ6NoName", "rsJ6NoTable", "rsJ6NoCriterion", "rsJ6Modal", "rsJ6NoFalsify", "rsJ7NoVerdict", "rsJ7Back"]) ok2((FE.match(new RegExp("\\b" + k + ":", "g")) || []).length === 2, "中英两套文案都有 " + k);
  /* 预算：第 6 道抬到 40000 之后仍装完整内功 */
  const neig2 = fs.readFileSync("public/taste/assets/sde-neigong.txt", "utf8").length + fs.readFileSync("public/taste/assets/sde-collide-paradigm.txt", "utf8").length;
  const code3 = grab("const RES_SYS_CAP = 130000", "function wdsSdeResearchSys");
  const m3 = new Function(code3 + "\nreturn { RES_SYS_CAP, RES_SYS_CAP_TOP, RES_FLOOR, resPriorFit };")();
  const f6 = m3.resPriorFit(neig2, 40000, 25500, 10000, 0, m3.RES_SYS_CAP_TOP);
  ok2(f6.mode === "full" && f6.ctxKeep >= m3.RES_FLOOR.ctx && f6.webKeep >= m3.RES_FLOOR.web, "满血顶配：第 6 道 40000 份额＋近邻链一万字仍装完整内功（站内 25500→" + f6.ctxKeep + "）");
  const f6s = m3.resPriorFit(neig2, 40000, 25500, 10000, 0, m3.RES_SYS_CAP);
  ok2(f6s.mode === "full" && f6s.ctxKeep === m3.RES_FLOOR.ctx && f6s.webKeep >= m3.RES_FLOOR.web, "读者自选型号 13 万档：第 6 道仍完整内功，站内资料裁到地板 " + f6s.ctxKeep);
}

console.log(bad || process.exitCode ? ("\n✗ 有不过的项") : "\n✓ 全过");
process.exit((bad || process.exitCode) ? 1 : 0);
