/* 只测一件事：三家对撞的「继续对撞」（2026-09-01）。

   一轮撞完（判断→攻击→结算）不等于撞到底：结算出的那句话自己又是一条可攻的判断。
   继续＝拿上一轮的结算当这一轮的靶子，**并且座位左轮一格**。
   两处最容易做错、也最难在成品上看出来的：
     ① 不轮座 —— 出判断这一席永远是同一家，后面几轮撞的还是它第一轮划下的那条线；
     ② 同义重述 —— 把上一轮的结论换个说法再说一遍，三栏照样填满、读起来还挺像样，一层没往下走。
   所以这两条各有一组断言，且座位轮转是**真跑**出来的。 */
"use strict";
const fs = require("fs");
const W = fs.readFileSync(__dirname + "/../src/worker.js", "utf8");
const C = fs.readFileSync(__dirname + "/../public/wds-mode.js", "utf8");
let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };

console.log("\n[一] 轮次真的传到服务端，并且只在第二轮起才传");
ok(/duel: \{ role: ROLES\[i\], prior: prior, rd: rd > 1 \? rd : 0 \}/.test(C), "第一轮递 rd=0 —— 首轮三席的提示语一个字都不该变");
ok(/rd: Math\.max\(0, Math\.min\(9, parseInt\(duelRaw\.rd, 10\) \|\| 0\)\)/.test(W), "服务端把 rd 钳在 0–9（它来自客户端，不钳就是一个能塞任意值的口子）");
ok(/WDS_DUEL_SYS\(duel\.role, duel\.prior \|\| "", siteCtx, lang, duel\.rd \|\| 0\)/.test(W), "rd 一路传进角色提示语");

console.log("\n[二] 反空转：这一轮不许是上一轮的同义重述");
ok(/if \(role === "a" && RD\) \{/.test(W), "第一席在续轮有一份**不同的**提示语（不是把首轮那份再用一遍）");
ok(/同义重述是这一轮唯一不许出现的产物/.test(W), "第一席写死了反空转条款");
ok(/差别，落在哪一个词上/.test(W), "要求明说与上一轮那句话的差别落在哪个词 —— 这是同义重述唯一查得住的抓手");
ok(/就直说到底了、这一轮不该跑/.test(W), "撞到底了要如实停 —— 凑一轮比停下更坏");
ok(/反空转\】/.test(W) && /能不能由上一轮那句结算直接推出/.test(W), "第三席在续轮多一道判据：这一轮能否由上一轮直接推出");

console.log("\n[三] 座位轮转 —— 真跑一遍，不看字面");
{
  /* 把前端那行轮转原样取出来跑：三轮之后，出判断这一席必须换过人。 */
  const m = C.match(/var nx = seats\.slice\(1\)\.concat\(seats\.slice\(0, 1\)\);/);
  ok(!!m, "取得到轮转那一行");
  let seats = [{ v: "A" }, { v: "B" }, { v: "C" }];
  const first = [];
  for (let rd = 1; rd <= 4; rd++) {
    first.push(seats[0].v);
    seats = seats.slice(1).concat(seats.slice(0, 1));   // 与源码同一行的动作
  }
  ok(first.join("") === "ABCA", "四轮里出判断的依次是 A→B→C→A，题的定法每轮换手（实得 " + first.join("→") + "）");
  ok(new Set(first.slice(0, 3)).size === 3, "头三轮三家各坐过一次第一席 —— 没有哪一家垄断定题权");
}
ok(/nx\.degraded = seats\.degraded;/.test(C), "只有两家 Key 时的降级标记要跟着轮转走，否则第二轮起就不再如实标注");

console.log("\n[四] 半截的一轮不给「继续」");
ok(/if \(res && res\.ok && res\.verdict\)/.test(C), "三席都有产出、且结算非空，才给继续钮（半截的一轮没有可当靶子的结算）");
ok(/startRound\(nx, rd \+ 1, res\.verdict\)/.test(C), "上一轮的结算原样当下一轮第一家的靶子");
ok(/if \(streaming\) return;/.test(C), "正在跑的时候点不动");

console.log("\n[五] 多轮的产物要收得住");
/* ⚠ 第一版只查「文件里有没有 ROUNDS.join」——把保存那一处换成 all 也照样绿（反向验证抓到的）。
   要查的是**保存到画布那一句自己**用的是不是全部轮次。 */
ok(/ROUNDS\.push\(all\)/.test(C), "每一轮的全文都进 ROUNDS");
ok(/sv\.onclick = function \(\) \{ cvAdd\("md", q\.slice\(0, 24\), "# " \+ q \+ "\\n\\n" \+ ROUNDS\.join\("\\n\\n"\)\); \};/.test(C), "保存到画布带走的是**全部轮次**，不是最后一轮");
ok(/if \(cell\.acts && cell\.acts\.parentNode\)/.test(C), "开新一轮先摘掉上一轮的按钮行，页面上不会留下两排「继续对撞」");

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
