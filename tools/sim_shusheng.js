// 书生（/books/agent/）服务端提示语与分支的模拟（2026-10-03）。用法：node tools/sim_shusheng.js
const fs = require("fs");
const src = fs.readFileSync(__dirname + "/../src/worker.js", "utf8");
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) pass++; else { fail++; console.log("FAIL:", m); } };
const grab = (start, endMark) => { const i = src.indexOf(start); if (i < 0) throw new Error("missing " + start); const j = src.indexOf(endMark, i); return src.slice(i, j); };
const code = grab("const SHUSHENG_ACTS = {", "\n// ===== SDE 助教模式·全站对话入口 system");
const ctx = new Function("WDS_METHOD_GUIDE", code + "\nreturn {SHUSHENG_ACTS, WDS_SHUSHENG_SYS, SHUSHENG_PAPER_RULE, SHUSHENG_PAPER_SYS, SHUSHENG_PAPER_USR};")("〈方法论指引〉");
const acts = ["read", "apply", "cut", "clash", "write"];
ok(acts.every(a => ctx.SHUSHENG_ACTS[a] && ctx.SHUSHENG_ACTS[a].length > 120), "五道门工序齐全");
for (const a of acts) {
  const s = ctx.WDS_SHUSHENG_SYS("心得", "\n骨架", "内功", "旁证", "SIO三大公理", "德麦国际专著第3号", a, "三归", "三条公理的归位者", "〔跨界·专著〕《内卷与突围》……", "1. 三表征同源于一个误判……");
  ok(s.includes("《SIO三大公理》") && s.endsWith(ctx.SHUSHENG_ACTS[a]), a + "：书名在、本门工序压在最末");
  ok(s.includes("核心要点（你对这本书全书的常驻记忆）") && s.indexOf("核心要点") < s.indexOf("专属碰撞库"), a + "：核心要点常驻、排在碰撞库之前");
  ok(s.startsWith("你是「三归」（三条公理的归位者）") && s.includes("专属碰撞库") && s.indexOf("专属碰撞库") < s.indexOf("站内相关篇目"), a + "：以书自己的名字自称，专属碰撞库在旁证之前");
  ok(!s.includes("【读者正在读的文本】"), a + "：全书不进 system（走第一轮消息，利于前缀缓存）");
}
const s0 = ctx.WDS_SHUSHENG_SYS("", "", "", "", "X", "", "bogus");
ok(!/【本轮这道门/.test(s0), "认不出的门不注入工序");
ok(/书写于哪个阶段，就先用它自己的话讲/.test(s0) && /三方来源账/.test(s0) && /引书必须真在书里/.test(s0), "四条铁规在");
ok(/拆一处必须建一处/.test(ctx.SHUSHENG_ACTS.cut) && /必须同时给出补法/.test(ctx.SHUSHENG_ACTS.cut), "拆开必带建构");
ok(/共有的那个前提/.test(ctx.SHUSHENG_ACTS.clash) && /不是 A，也不是 B，而是 Z/.test(ctx.SHUSHENG_ACTS.clash), "对撞走二阶碰撞");
const pu = ctx.SHUSHENG_PAPER_USR(false, "CTX", "", "一万"), mu = ctx.SHUSHENG_PAPER_USR(true, "CTX", "", "一万");
ok(/来源账/.test(pu) && /六个部分/.test(pu), "论文：六部分＋来源账");
ok(/立项书与全书提纲/.test(mu) && /可错预言/.test(mu) && /导论初稿/.test(mu), "专著：立项书＋提纲＋导论初稿");
ok(/三方来源账/.test(ctx.SHUSHENG_PAPER_SYS(true, "")), "成文 system 带三方来源账");
// /api/wds/read 分支
const rd = grab('if (url.pathname === "/api/wds/read") {', 'if (url.pathname === "/api/wds/chat") {');
ok(/const BA = !!b\.bookagent;/.test(rd) && /const GDX = !!b\.guide \|\| BA;/.test(rd), "read：BA/GDX 定义");
ok(/let sys = BA \? WDS_SHUSHENG_SYS\(/.test(rd), "read：书生 system 优先");
ok(/const VC = GDX \? wdsTopVC/.test(rd), "read：书生走最强档");
ok(/if \(b\.guide \|\| b\.book \|\| \(BA && !BRAG\)\) \{/.test(rd), "read：有专属碰撞库就不现场检索");
ok(/const BPTS = BA \? String\(b\.bookPoints/.test(rd) && /ANAME, AEPI, BRAG, BPTS\)/.test(rd), "read：核心要点递进 system");
ok(/const BRAG = BA \? String\(b\.bookRag \|\| ""\)\.slice\(0, 16000\)/.test(rd) && /ANAME, AEPI, BRAG, BPTS\)/.test(rd), "read：名字与专属库递进 system");
ok(/slice\(0, BA \? 120000 : 100000\)/.test(rd), "read：书生全书上限 12 万字符");
ok(/if \(GDX && docText\) \{/.test(rd) && /packReadHistory\(history, histBudget, GDX \? 12000 : 0\)/.test(rd), "read：全书作首轮消息＋长记忆");
ok(!/\bb\.guide \? wdsTopVC/.test(rd), "read：无残留 b.guide 选档");
const pp = grab('if (url.pathname === "/api/wds/read-paper") {', 'if (b.mode === "summary") {');
ok(/if \(BA\) \{ sys = SHUSHENG_PAPER_SYS\(_mono, BASE\); usr = SHUSHENG_PAPER_USR\(_mono, CTX, ragCtx, PW\); \}/.test(pp), "paper：书生成文分支");
ok(/max_tokens: BA \? 16000 : WDS_TOK_SAFE/.test(pp), "paper：书生成文预算 16000");
ok(/const CTX = BA \?/.test(pp) && /专属碰撞库/.test(pp) && /核心要点（全书骨架）/.test(pp), "paper：CTX 带书、专属库、对话");
console.log(pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
