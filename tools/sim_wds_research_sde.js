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
  grab("function forgeCarry(i, bodies, gates, needsTbl)", "function wdsForgeSys"),
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
  ok2(/const _room = 130000 - Math\.min\(_carryLen, FORGE_CARRY_MAX\)/.test(S), "预算按 system 实际占用算，不是拍脑袋");
  ok2(/neigongLite\(_ng\)/.test(S) && /内功按精简版装载/.test(S), "装不下就退精简版并当场说明（不静默降级）");
  ok2(/内功文件这次没读到/.test(S) && /按降级看待/.test(S), "读不到内功要如实报，不假装装过");
  const neig = fs.readFileSync("public/taste/assets/sde-neigong.txt", "utf8");
  const coll = fs.readFileSync("public/taste/assets/sde-collide-paradigm.txt", "utf8");
  /* 常态（上游满载 2.6 万 ＋ 站内资料满载 1.8 万、无附件）必须装得下完整内功；
     只有再叠上一份大附件才会退到精简版，而那时会当场说明。 */
  const _full = neig.length + coll.length;
  ok2(_full < 130000 - 26000 - 18000, "常态满载下完整内功装得进（内功 " + _full + " 字 vs 余量 " + (130000 - 26000 - 18000) + "）");
  ok2(_full > 130000 - 26000 - 18000 - 12000, "再叠一份大附件就会退精简版——那一条路是有出口的，不是死码");
}

console.log(bad || process.exitCode ? ("\n✗ 有不过的项") : "\n✓ 全过");
process.exit((bad || process.exitCode) ? 1 : 0);
