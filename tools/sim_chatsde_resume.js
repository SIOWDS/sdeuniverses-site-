/* sim_chatsde_resume.js —— 续写：只补没写够的那几节
 * 两次真跑同一形状：稳定写完六节，第 7 节起撞墙。既然一口气十六节写不完，
 * 就把"接着写"做成按钮：扫描已有稿、只重跑缺的那几节、**插回原位**。
 * 顺带查：固定骨架档的提纲解不出 JSON 时不许让整篇失败（真跑读数：交回 2375 字，不是 JSON）。
 * 跑法：node tools/sim_chatsde_resume.js
 */
"use strict";
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, "..");
let pass = 0, fail = 0;
const ok = (n, c) => { if (c) { pass++; console.log("  ✓ " + n); } else { fail++; console.log("  ✗ " + n); } };
const F = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");
const W = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");

/* ═══ 一、扫描函数真跑 ═══ */
console.log("── 哪几节没写够（真跑）──");
const a = F.indexOf("    function secBlocks(txt, secs) {");
const b = F.indexOf("    /* ══ 关掉这个面板", a);
const SRC = (a > 0 && b > a) ? F.slice(a, b) : "";
ok("抠得到 secBlocks / missingSecs", SRC.indexOf("missingSecs") > 0);
const M = new Function(SRC + "\n return { secBlocks: secBlocks, missingSecs: missingSecs };")();

const SECS = [{ h: "一、引言", words: 1000 }, { h: "二、述评", words: 1000 },
              { h: "三、判据", words: 1000 }, { h: "四、结论", words: 1000 }];
const full = (h, n) => "## " + h + "\n\n" + "字".repeat(n) + "\n\n";
const draft = full("一、引言", 900) + full("二、述评", 900) + full("三、判据", 30) + full("四、结论", 20);

const miss = M.missingSecs(draft, SECS);
ok("认得出缺的是第 3、4 节", miss.length === 2 && miss[0].i === 2 && miss[1].i === 3);
ok("写够的两节不被误判", miss.every((x) => x.i >= 2));
ok("每一节都量得到起止（插回原位要用）", M.secBlocks(draft, SECS).every((x) => x.from >= 0 && x.to > x.from));
const full4 = full("一、引言", 900) + full("二、述评", 900) + full("三、判据", 900) + full("四、结论", 900);
ok("完整稿扫出来一节不缺", M.missingSecs(full4, SECS).length === 0);
const noHead = full("一、引言", 900) + full("二、述评", 900);
ok("整节连标题都没有 → 也算缺（from = -1）", M.missingSecs(noHead, SECS).length === 2);
/* 小标题被基底改过字：退一步只认标题本身 */
const renamed = "## 一、引言（修订）\n\n" + "字".repeat(900) + "\n\n" + full("二、述评", 900) + full("三、判据", 900) + full("四、结论", 900);
ok("小标题被改过字仍认得出（退一步只认标题本身）", M.missingSecs(renamed, SECS).length === 0);
const thr = SRC.match(/Math\.max\(260, Math\.round\(w \* ([\d.]+)\)\)/);
ok("门槛与正文那一处同源（本节目标 × 比例，比例从源码取）", !!thr && +thr[1] > 0 && +thr[1] < 1);

/* ═══ 二、续写钮的源码级要求 ═══ */
console.log("── 续写钮 ──");
const btn = F.slice(F.indexOf('var goOn = el("button", "wdsm-tbtn dgoon"'), F.indexOf('var pdfB = el("button"'));
ok("抠得到续写钮", btn.length > 600);
ok("默认不亮（没缺节时不摆没用的按钮）", /goOn\.style\.display = "none";/.test(btn));
ok("★ 补出来的内容插回原位，不是追加在末尾", /var head = blk\.from >= 0 \? text\.slice\(0, blk\.from\)/.test(btn) && /text = head \+/.test(btn));
ok("只跑缺的那几节，不重跑全篇", /missingSecs\(text, secs\)/.test(btn) && /miss\[k\]/.test(btn));
ok("补完后再扫一遍，全齐了就把钮收起来", /if \(!missingSecs\(text, secs\)\.length\) goOn\.style\.display = "none";/.test(btn));
ok("仍没写够的按节号报出来", /stillShort\.push\(i \+ 1\)/.test(btn) && /mGoOnEnd3/.test(btn));
ok("补的过程也存进度（中途关掉不白干）", /saveProgress\(/.test(btn));
ok("节间留白与正文那一处同量级（别一口气连打）", /setTimeout\(nextOne, \d{3,4}\)/.test(btn));
ok("没有分节表时明说，不静默失败", /mGoOnNo/.test(btn));
ok("收尾处会把续写钮亮出来", /goOnBtn\.style\.display = ""/.test(F));
ok("续写要用的 plan 在面板作用域留住了", /var dPlanObj = null;/.test(F) && /dPlanObj = plan;/.test(F));

/* ═══ 三、骨架档的提纲不许让整篇失败 ═══ */
console.log("── 提纲解不出 JSON 时 ──");
const syn = W.slice(W.indexOf("if (!plan && FIXED) {"), W.indexOf("if (!plan && FIXED) {") + 900);
ok("骨架档有合成分支", syn.length > 200);
ok("只对固定骨架档合成（自由分节档没有表可依，仍该失败）", /if \(!plan && FIXED\) \{/.test(W));
ok("题名从基底那一趟的原文里捞", /String\(raw \|\| ""\)/.test(syn) && syn.indexOf(".split(") > 0 && syn.indexOf("filter(") > 0);
ok("捞不到题名就退回档名，不留空", /_t \|\| SPEC\.name/.test(syn));
ok("sections 交空数组，由骨架合并那一步补齐十六节", /sections: \[\]/.test(syn));
ok("如实告诉读者提纲没解析出来、已按体例直接开写", /不是 JSON/.test(syn) && /已按体例直接开写/.test(syn));
ok("原来那条 noplan 失败路径仍保留（自由分节档要用）", /code: "noplan"/.test(W));

console.log("\n" + (fail ? "✗ " : "✓ ") + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
