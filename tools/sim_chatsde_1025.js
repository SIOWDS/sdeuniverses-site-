// sim_chatsde_1025.js — 2026-10-25「急」五场评估后的 ChatSDE 补丁防回归
// 跑法：node tools/sim_chatsde_1025.js
const fs = require("fs"), path = require("path");
const W = fs.readFileSync(path.join(__dirname, "..", "src", "worker.js"), "utf8");
const F = fs.readFileSync(path.join(__dirname, "..", "public", "wds-mode.js"), "utf8");
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) { pass++; console.log("  ✓ " + m); } else { fail++; console.log("  ✗ " + m); } };

// ① 四角块新增纪律
const B = Function("return (" + W.match(/const FOUR_TRI_BLOCK = ([\s\S]*?);\n/)[1] + ")")();
for (const k of ["三个下标互不相同", "自己的**三项", "不许标〔待核〕凑数", "代表作或论文名", "至少换上一位本场前几轮没出现过的近邻",
                 "只列名不交手的删掉", "不许先把它说窄再反驳", "承重判断要接力", "（深化）／（修正）／（推翻：理由）",
                 "守住原题", "两半都要照顾到", "史实纪律", "《留侯论》", "格式纪律", "六到八行，每行一句"]) ok(B.includes(k), "四角块含：" + k);
ok(!/六到八行，压短/.test(B), "去掉会被照抄的「压短」");
ok(B.indexOf("承重判断要接力") < B.indexOf("**六套轮换：**"), "新纪律排在六套轮换之前");

// ② 追问器：看得到原题与已问过
const fs2 = W.match(/function followSys\(prof\) \{[\s\S]*?\n\}\n/)[0];
ok(/本场原题/.test(fs2) && /本场已问过/.test(fs2), "followSys 规矩⑥⑦在");
const fu = W.match(/async function followUps\([^)]*\)/)[0];
ok(/ctx\)$/.test(fu), "followUps 收 ctx");
ok(/本场原题：/.test(W) && /本场已问过：/.test(W), "usr 拼入原题与已问过");
ok(/\{ orig: _us\[0\] \|\| "", asked:/.test(W), "调用处递 ctx");
ok(/r === "reader" \|\| r === "user"/.test(W), "历史按 reader 角色取（前端实际角色名）");
ok(/b\.orig/.test(W), "优先用前端递来的原题");
ok(/orig: origQ\(\)/.test(F) && /function origQ\(\)/.test(F), "前端 payload 带 orig");

// ③ 兜底追问去标签
const fbSrc = W.match(/function fallbackFollows[\s\S]*?\n}\n/)[0];
const fb = Function("FOLLOW_KINDS", "FOLLOW_KINDS_CN", "SDE_EQUATIONS", "SDE_PATHS", "SDE_PRINCIPLES", "FOLLOW_EQ_LANG", "FOLLOW_PATHS_LANG", "FOLLOW_PR_LANG",
  fbSrc + ";return fallbackFollows;")(["What", "How", "Why"], ["是什么", "怎么做", "为什么"], "a｜b", "c｜d", "e｜f", "", "", "");
ok(fb("急-H1\n缝隙", null, "zh")[0].q === "急是经什么差异长成现在这样的？", "「急-H1」→「急」");
ok(fb("急-H2-DEEPSEEK-新 缝隙", null, "zh")[1].q.indexOf("急该先改") >= 0, "「急-H2-DEEPSEEK-新」→「急」");
ok(fb("客气是什么？", null, "zh")[2].q === "是什么张力把客气逼成了现在这样？", "普通题照旧");

// ④ 空栏名与过程标记剥除
const PREG_RE = /\n*[〔【\[]\s*预注册\s*[〕】\]][^\n]*/;
const bare = F.match(/var PREG_BARE = (\/.*\/gm);/)[1];
const take = F.match(/function pregTake\(text\) \{[\s\S]*?\n  \}\n/)[0];
const pregTake = Function("PREG_RE", "PREG_BARE", "pregField", "pregEmpty", take + ";return pregTake;")(PREG_RE, eval(bare), () => "", () => true);
let r = pregTake("正文一段。\n\n预注册卡\n\n我\n");
ok(r && r.empty && !/预注册卡/.test(r.body), "只剩栏名的「预注册卡」被剥掉");
r = pregTake("（压短）\n异位四角卡\n正文");
ok(r && !/压短/.test(r.body) && /异位四角卡/.test(r.body), "「（压短）」被剥、正文留着");
ok(pregTake("普通正文，提到预注册卡这个词。") === null, "行内提到不误伤");

console.log("\n" + (fail ? "✗" : "✓") + " " + pass + " PASS / " + fail + " FAIL");
process.exit(fail ? 1 : 0);
