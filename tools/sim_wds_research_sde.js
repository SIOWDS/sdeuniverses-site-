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
  grab("function forgeCarry(i, bodies, gates, needsTbl, capChars)", "function wdsForgeSys"),   // 2026-08-29 加了第五参（各产线各自的上游份额），改落点不删
  grab("const RESEARCH_HEART =", "// RESEARCH_STEP"),
].join("\n");
const mod = new Function(code + "\nreturn { RESEARCH_STAGES, RES_NEEDS, RES_NBR_STAGES, wdsSdeResearchSys, forgeCarry };")();
const { RESEARCH_STAGES, RES_NEEDS, RES_NBR_STAGES, wdsSdeResearchSys } = mod;

let bad = 0;
const ok = (c, m) => { console.log((c ? "  ✓ " : "  ✗ ") + m); if (!c) bad++; };

console.log("① 工序表");
ok(RESEARCH_STAGES.length === 10, "十道工序，实得 " + RESEARCH_STAGES.length);
const want = ["背景研究","文献综述与研究方法","三方程研究","六路径研究","三原理·动力机制",
  "二阶碰撞：撞出新典范","论文大纲","自我反思与可证伪性","研究总结","参考文献"];
ok(JSON.stringify(RESEARCH_STAGES.map(x=>x.t)) === JSON.stringify(want), "顺序与作者定的一致");
ok(RESEARCH_STAGES.every(x => x.d && x.d.length > 120), "每道都有交付规格（最短 " + Math.min(...RESEARCH_STAGES.map(x=>x.d.length)) + " 字）");
ok(Object.keys(RES_NEEDS).length === 10 && RES_NEEDS[1].length === 0, "依赖表覆盖十道、第一道不消费上游");
ok(RES_NEEDS[6].join()==="3,4,5,2", "第六道要读到三方程/六路径/三原理/文献：" + RES_NEEDS[6].join("、"));
ok(!!RES_NBR_STAGES[6], "第六道挂敌意最近邻");

console.log("② 每一道的 system");
const bodies = [];
for (let i = 1; i <= 10; i++) {
  const rs = { i, n: 10, t: RESEARCH_STAGES[i-1].t, topic: "课堂里的沉默是什么", sde: 1,
    done: RESEARCH_STAGES.map((x,k)=>(k+1)+". "+x.t).join("\n"), bodies: bodies.slice(), gates: [] };
  const sys = wdsSdeResearchSys(rs);
  const need = RES_NEEDS[i] || [];
  const gotAll = need.every(k => sys.indexOf("第 " + k + " 道《") >= 0);
  const noFake = !/⚠【材料不全】/.test(sys);
  if (i === 1) ok(sys.length > 800 && /S=F\(D,E\)/.test(sys), "第1道：有三大方程心法（" + sys.length + " 字）");
  if (i === 3) ok(/E=H\(S,D\)/.test(sys) && /回写/.test(sys), "第3道：三条方程与回写都在");
  if (i === 4) ok(/六种排列/.test(sys), "第4道：六路径在");
  if (i === 5) ok(/三缸机/.test(sys), "第5道：三原理在");
  if (i === 6) ok(/占位者/.test(sys) && gotAll, "第6道：占位者判据在，且读到上游 " + need.join("、"));
  if (i === 10) ok(/只列前面各道真正引用过的/.test(sys) && gotAll, "第10道：参考文献口径在，且读到上游 " + need.join("、"));
  if (i > 1) ok(gotAll && noFake, "第" + i + "道拿到全部上游原文 " + need.join("、"));
  bodies.push({ i, t: RESEARCH_STAGES[i-1].t, body: "第" + i + "道的正文，" + "料".repeat(300), hash: "" });
}

console.log("③ 上游截断要看得见");
const big = [{ i: 3, t: "三方程研究", body: "长".repeat(40000), hash: "" },
             { i: 4, t: "六路径研究", body: "短", hash: "" },
             { i: 5, t: "三原理·动力机制", body: "中".repeat(500), hash: "" },
             { i: 2, t: "文献综述与研究方法", body: "文", hash: "" }];
const s6 = wdsSdeResearchSys({ i: 6, n: 10, t: "二阶碰撞：撞出新典范", topic: "T", sde: 1, done: "", bodies: big, gates: [] });
ok(/此处只带来前/.test(s6), "超长上游被截断且当场说明");
const s7 = wdsSdeResearchSys({ i: 7, n: 10, t: "论文大纲", topic: "T", sde: 1, done: "", bodies: [{ i: 6, t: "x", body: "y", hash: "" }], gates: [] });
ok(/⚠【材料不全】/.test(s7) && /第 3、4、5 道/.test(s7), "缺上游时点名说缺哪几道，不许假装读过");

console.log("④ 老路仍在（plan=free 的自由拆题）");
ok(/if \(b\.plan !== "free"\)/.test(src), "plan 默认发工序表，free 才走基底拆题");
ok(/sde: rsRaw\.sde \? 1 : 0/.test(src), "rs 白名单认 sde 字段（不认就静默丢掉，整条产线空转）");
ok(/rs\.sde && RES_NBR_STAGES/.test(src), "近邻链接线在");

console.log("⑤ 前端");
const fe = fs.readFileSync("public/wds-mode.js", "utf8");
ok(/sdePipe = !!j\.sde/.test(fe), "plan 回来记住这是 SDE 产线");
ok(/sde: sdePipe \? 1 : 0/.test(fe), "每一道把 sde 递上去");
ok(/if \(sdePipe\) return done\(""\);/.test(fe), "跳过总判断（第九道就是总结）");
ok(/i \+ 1 === steps\.length\)\)\) \? 1 : 0/.test(fe), "背景/文献/参考文献三道强制联网");
ok(/"\\u2913 \.docx"/.test(fe) && /SDEDocx\.build\(\{ title: title/.test(fe), "报告有 Word 导出");


/* ═══ 追加（2026-08-29）：满血 ＋ 完整内功 ═══════════════════════════ */
console.log("⑥ 全血加功力");
{
  const S = fs.readFileSync("src/worker.js", "utf8");
  const ok2 = (c, m) => { console.log((c ? "  ✓ " : "  ✗ ") + m); if (!c) process.exitCode = 1; };
  ok2(/const deep = b\.mode === "deep" \|\| !!\(b\.rs && typeof b\.rs === "object" && b\.rs\.sde && !noSde\);/.test(S),
    "深度研究一律满血档（最强基底＋完整方法论工序＋检索加倍＋6000 输出）");
  ok2(/if \(rs && rs\.sde && !prof\) \{/.test(S), "研究这一路装完整内功（分身档不叠，它自带底盘）");
  const FE2 = fs.readFileSync("public/wds-mode.js", "utf8");
  ok2(/if \(PROFILE\) _planBody\.plan = "free";/.test(FE2), "分身页不跑这条产线（工序名是母体术语，会把改姓档灌回去）");
  ok2(!/SDE/.test((FE2.match(/rsTip: "[^"]*"/g) || []).join(" ")), "按钮说明里没有学派术语（分身页读同一张表）");
  ok2(/loadNeigong\(env, url, "\/taste\/assets\/sde-neigong\.txt"\)/.test(S), "装的是全站共读那一份（与金点子发生器同源）");
  ok2(/const _carryLen = Math\.min\(RES_CARRY_MAX, /.test(S), "上游原文按 forgeCarry 的真实上限计（不是把二十万字原文全算进去）");   // 2026-08-29：研究产线自己的份额 RES_CARRY_MAX（数没变，仍 26000），改落点不删
  ok2(/forgeCarry\(i, rs\.bodies, rs\.gates, RES_NEEDS, RES_CARRY_MAX\)/.test(S), "研究产线的 forgeCarry 真传了自己的份额（学科通融抬到 48000 不许连带把它抬上去——它另有七万八千字内功要装）");
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
     上游原文按依赖表匀分到 FORGE_CARRY_MAX；站外资料 1/2/10 三道 8000、第 6 道近邻链 6000。 */
  const CTX = 25500, WEB = { 1: 8000, 2: 8000, 6: 6000, 10: 8000 };
  let allFull = true, cutStages = [];
  for (let i = 1; i <= 10; i++) {
    const need = mod.RES_NEEDS[i] || [];
    const carry = need.length ? Math.min(26000, need.length * 9000) : 0;   // 每道正文按 9000 字算，多了会被匀分截到 26000
    const f = m2.resPriorFit(_full, carry, CTX, WEB[i] || 0, 0, m2.RES_SYS_CAP_TOP);
    if (f.mode !== "full") allFull = false;
    if (f.ctxKeep < CTX || f.webKeep < (WEB[i] || 0)) cutStages.push(i);
  }
  ok2(allFull && !cutStages.length, "满血档：十道全部装完整内功且一样读物都不裁（内功 " + _full + " 字；第一刀在第 6/10 道会退精简版）");
  const f6old = m2.resPriorFit(_full, 26000, CTX, 6000, 0, m2.RES_SYS_CAP);
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
  ok2(/const _cap = \(VC\.top && !umodel\) \? RES_SYS_CAP_TOP : RES_SYS_CAP;/.test(S), "满血顶配走 15 万档，读者自选型号守 13 万");
}

console.log("⑦ 全套三件：内功 Skill ＋ 心得 ＋ 方法论");
{
  const S = fs.readFileSync("src/worker.js", "utf8");
  const ok2 = (c, m) => { console.log((c ? "  ✓ " : "  ✗ ") + m); if (!c) process.exitCode = 1; };
  /* 心得：缺就现写，而且只在研究这一路、且只在确实缺、有 Key 的时候进这个分支；
     存储没躺（!reflectStoreDown()）与本轮没被退避过（!rs.noRegen）两条**都**要拦得住生成——
     2026-08-29 第三刀把单条 if 拆成 if/else if，锚点跟着挪，断言落点也挪过来（不删）。 */
  ok2(/if \(rs && rs\.sde && !prof && !reflect && KEY\) \{[\s\S]{0,300}if \(rs\.noRegen\)/.test(S),
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
  ok2(/var g = fg \? \(function \(\) \{ var j = rsJudge\(txt, RS\.lastMeta\); return j\.d === "passed" \? forgeGate\(txt\) : j; \}\)\(\) : rsJudge\(txt, RS\.lastMeta\);/.test(FE), "step()：学科通融先程序判再走基底的【闸门】，研究产线走程序判决");
  ok2(!/if \(!fg\) \{ i\+\+; return step\(\); \}/.test(FE), "技术故障不再 i++ 静默跳过（研究产线也停下交给读者）");
  ok2(/g\.d === "cut" \? \(tx\("rsCut1"\)/.test(FE) && /g\.d === "failed" \? \(tx\("rsFailed1"\)/.test(FE), "闸门条对 cut／failed 各说各的原因，不再借「自己判了没做够」那句");
  for (const k of ["rsCut1", "rsCut2", "rsFailed1", "rsCutEmpty", "rsCutStopped", "rsCutLength", "rsCutShort"]) {
    ok2((FE.match(new RegExp("\\b" + k + ":", "g")) || []).length === 2, "中英两套文案都有 " + k);
  }
}

console.log(bad || process.exitCode ? ("\n✗ 有不过的项") : "\n✓ 全过");
process.exit((bad || process.exitCode) ? 1 : 0);
