/* 只测中华智问这一侧的三件事：每轮重取底盘、成文注入近邻名单、成文后过三关。
   外加一件更要紧的：**两页共用的那份判据是不是真的只有一份**——
   判据被复制两份的失败是静默的（某一关实际不再把关，论文照样产出，无人收到报错），
   所以这里同时对共用模块跑一遍判据，并检查两个页面都优先走它。 */
"use strict";
const fs = require("fs");
const ROOT = __dirname + "/..";
const Z = fs.readFileSync(ROOT + "/public/taste/zhiwen/index.html", "utf8");
const G = fs.readFileSync(ROOT + "/public/taste/idea-generator/index.html", "utf8");
const M = fs.readFileSync(ROOT + "/public/taste/assets/sde-nbr-gate.js", "utf8");
let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };

/* 装载共用模块：给它一个假 window */
const w = {};
new Function("window", M)(w);
const N = w.SDENbr;

console.log("\n[一] 共用模块本身（判据的唯一来源）");
{
  ok(!!N && typeof N.sectionOK === "function" && typeof N.crossOK === "function" && typeof N.verdict === "function",
     "window.SDENbr 暴露 sectionOK / crossOK / verdict / coinedName / postNameGap");
  ok(N.sectionOK("五、近邻检测\n《规训与惩罚》 (Foucault, 1975) 《持久的不平等》 若观察到 X 则本文错") === true,
     "三个点名 + 判决性预测 → 通过");
  ok(N.sectionOK("五、近邻检测\n本文不可被替代。") === false, "空头承诺 → 不通过");
  ok(N.sectionOK("一、引论") === false, "没有那一节 → 不通过");
  ok(N.crossOK("近邻检测\n本文所属学科：社会学\n（学科：社会学）（学科：社会学）（学科：社会学）") === false,
     "三个标注全是本文学科 → 不通过");
  ok(N.crossOK("近邻检测\n（学科：社会学）（学科：心理学）") === true, "标注含两个学科 → 通过");
  ok(N.crossOK("近邻检测\n与福柯、与布迪厄、与拉图尔") === null, "看不出学科 → null 放行");
  ok(N.coinedName("本文将其命名为“互裁”") === "互裁", "抽得出新命名");
  ok(N.sectionOK("四、最近邻判别\n《社会系统》(Luhmann, 1984)《冲突》《持久的不平等》 可判定差异：……") === true,
     "认中华智问那边的措辞（最近邻判别 / 可判定差异）——两页术语不同，判据要都吃下");

  /* verdict 三关合一 */
  (async () => {
    const v1 = await N.verdict("一、引论");
    ok(v1.need === true && /未达标/.test(v1.why), "verdict：没做检测 → need + 说明哪一关");
    const v2 = await N.verdict("近邻检测\n本文所属学科：社会学\n《社会系统》(A,1990)（学科：社会学）《冲突》(B,1991)（学科：社会学）《持久的不平等》(C,1992)（学科：社会学） 若 X 则本文错");
    ok(v2.need === true && /同一学科/.test(v2.why), "verdict：三个近邻同一学科 → need，且 why 指明是这一关");
    const v3 = await N.verdict("");
    ok(v3.need === false, "verdict：空文不判 need（没稿子就没有闸）");
  })();
}

console.log("\n[二] 两页都优先走共用模块（判据不许有第二份在跑）");
{
  ok(/sde-nbr-gate\.js/.test(Z), "中华智问引入了共用模块");
  ok(/sde-nbr-gate\.js/.test(G), "金点子也引入了共用模块");
  for (const [n, fn, call] of [["nbrSectionOK", "function nbrSectionOK(text){", "sectionOK"],
                               ["coinedName", "function coinedName(text){", "coinedName"],
                               ["nbrCrossOK", "function nbrCrossOK(text){", "crossOK"]]) {
    const i = G.indexOf(fn);
    const head = G.slice(i, i + 320);
    ok(new RegExp("window\\.SDENbr[\\s\\S]{0,60}return window\\.SDENbr\\." + call).test(head),
       "金点子的 " + n + " 先问共用模块，本地实现只作兜底");
  }
  ok(/window\.SDENbr/.test(Z), "中华智问那边直接用共用模块（没有第二份本地实现）");
  ok(!/function nbrCrossOK/.test(Z), "中华智问没有复制一份判据进页面");
}

console.log("\n[三] 每轮按当轮主题重取底盘");
{
  const seg = Z.slice(Z.indexOf("每轮按**当轮主题**重取站内底盘"), Z.indexOf("const usr = rnd===1"));
  ok(/rnd > 1/.test(seg), "第 2 轮起才重取（第 1 轮已有启动时那一份，不重复取）");
  ok(/history\[history\.length-1\]/.test(seg), "种子含上一轮摘要——螺旋每轮换焦点，底盘要跟着走");
  ok(/if\(_c\) RUN\.kbCtx = _c;/.test(seg), "取不到就沿用上一份，不把已有底盘清空");
  ok(/catch\(_\)/.test(seg), "取失败不影响这一轮作答");
}

console.log("\n[四] 成文：注入名单 + 过三关");
{
  ok(/function paperMaterials\(question, summaries, finalAnswer, nbrBlock\)/.test(Z), "paperMaterials 接受近邻名单");
  const pm = Z.slice(Z.indexOf("function paperMaterials"), Z.indexOf("function paperMaterials") + 700);
  ok(/if\(nbrBlock\) parts\.push\(nbrBlock/.test(pm), "名单**前置**——两万字材料容易把它埋掉");
  const sysSeg = Z.slice(Z.indexOf("任务说明 ═"), Z.indexOf("任务说明 ═") + 3000);
  ok(/NBR_CHECK_MARK/.test(sysSeg) && /NBR_DISC_MARK/.test(sysSeg), "paperSystem 里近邻检测与学科标注都是硬要求");
  ok(/判决性对照预测/.test(sysSeg) && /领域\*\*之外\*\*的学科/.test(sysSeg), "四件套与跨学科都要求了");

  ok((Z.match(/await nbrGateFix\(/g) || []).length === 2, "两处成文（每台一篇 + 典范第四篇）都过闸");
  const gf = Z.slice(Z.indexOf("async function nbrGateFix"), Z.indexOf("function paperSystem"));
  ok(/window\.SDENbr\.verdict/.test(gf), "闸门判据来自共用模块，不在这里另写一套");
  ok(/if\(!text \|\| !window\.SDENbr\) return text;/.test(gf), "模块没加载成功就整关跳过——宁可不查，不可误伤出稿");
  ok(/, 4000\)/.test(gf), "补写用有界预算");
  ok(/catch\(_\)/.test(gf) && /return text/.test(gf), "补写失败照原样返回，不让一节拖垮两万字");
  ok(/一千五百字以内/.test(gf), "补节有字数上限");
  ok(/replace\(\/\\s\*\$\/, ''\)/.test(gf), "补出来的一节拼在原文尾部，原文一字不动");
  ok(Z.indexOf("await nbrGateFix") < Z.indexOf("ptext = dejargonOutput"), "先过闸再去术语——补进来的那一节也要被去术语扫一遍");
}

setTimeout(() => {
  console.log("\n结果：PASS " + P + " · FAIL " + F);
  process.exit(F ? 1 : 0);
}, 50);
