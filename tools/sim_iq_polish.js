/* 只测两件事：
   ① 搜索页新加的「创新智商评估」算分器与官方 scripts/score.py 是不是同一把尺子
      （综合分、层级、闸门告警、Python round 的银行家舍入），差一分就是两套标准；
   ② worker.js 里 iq / polish 两个新模式的 prompt 是不是把该有的硬条款都带上了
      （盲评三铁律、五维权重、两道闸门、135 的五维换算、评分卡逐条清账）。
   算分器函数从 index.html 里原样抠出来真跑——复制一份实现，那份永远不会跟着改。 */
"use strict";
const fs = require("fs");
const ROOT = "/home/claude/site";
const html = fs.readFileSync(ROOT + "/public/search/index.html", "utf8");
const wk = fs.readFileSync(ROOT + "/src/worker.js", "utf8");

let P = 0, FA = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (FA++, console.log("  FAIL " + m)); };

/* —— 抠出算分器 —— */
const names = ["iqComposite", "pyRound", "iqLevel", "iqNum", "parseIqJson"];
let src = "var IQ_W={S:0.20,D:0.25,E:0.20,I:0.20,F:0.15};\n";
const lv = html.match(/var IQ_LEVELS=\[[^\n]*\];/);
if (!lv) { console.log("FAIL 抠不出 IQ_LEVELS"); process.exit(1); }
src += lv[0] + "\n";
names.forEach(function (n) {
  const a = html.indexOf("function " + n + "(");
  if (a < 0) { console.log("FAIL 抠不出 " + n); process.exit(1); }
  const b = html.indexOf("\nfunction ", a + 1);
  src += html.slice(a, b < 0 ? a + 1200 : b) + "\n";
});
const F = new Function(src + "return {c:iqComposite,r:pyRound,l:iqLevel,n:iqNum,p:parseIqJson};")();
const total = (S, D, E, I, Iq, Fq) => F.r(F.c({ S: S, D: D, E: E, I: I, F: Iq }));
const T = (d) => F.r(F.c(d));

console.log("— 一、与 scripts/score.py 逐字对表 —");
/* 下面五组都是官方脚本跑出来的真实结果（含本次评的那一篇） */
ok(T({ S: 127, D: 134, E: 122, I: 114, F: 113 }) === 123, "SDE-paper33 五维 → 123（脚本同值）");
ok(T({ S: 129, D: 142, E: 128, I: 126, F: 115 }) === 129, "收窄口径 → 129（脚本同值）");
ok(T({ S: 135, D: 140, E: 130, I: 135, F: 145 }) === 137, "源本示范卡 → 137，不是手写的 138（勘误一）");
ok(T({ S: 133, D: 138, E: 124, I: 124, F: 142 }) === 132, "《分离线》五维 → 132");
ok(T({ S: 134, D: 136, E: 128, I: 122, F: 136 }) === 131, "《卸责之困》五维 → 131");
ok(Math.abs(F.c({ S: 127, D: 134, E: 122, I: 114, F: 113 }) - 123.05) < 1e-9, "未取整的综合分 = 123.05");

console.log("— 二、Python round 的银行家舍入（.5 进偶数） —");
ok(F.r(122.5) === 122, "122.5 → 122（进偶数，不是 123）");
ok(F.r(123.5) === 124, "123.5 → 124");
ok(F.r(123.05) === 123, "123.05 → 123");
ok(F.r(134.7) === 135, "134.7 → 135");
ok(T({ S: 130, D: 130, E: 130, I: 130, F: 130 }) === 130, "五维全 130 → 130（权重和恰为 1）");

console.log("— 三、层级标尺（数值单调，155/165 不许排在 160 前） —");
ok(/基底零提示语默认/.test(F.l(100)), "100 = 基底零提示语默认水平");
ok(/高级专家/.test(F.l(125)) && /高级专家/.test(F.l(134)), "125–134 = 高级专家");
ok(/资深学者/.test(F.l(135)), "135 = 资深学者（本次打磨的目标线）");
ok(/本体论级阈值/.test(F.l(150)), "150 = 本体论级阈值");
ok(/典范级阈值/.test(F.l(160)), "160 = 典范级阈值");
ok(/金点子/.test(F.l(157)) && !/典范级/.test(F.l(157)), "157 落在 155 档而不是 160 档");
ok(/大众水平/.test(F.l(70)), "低于 80 仍给最低档，不返回 undefined");

console.log("— 四、脏输入不许把卡片打崩 —");
ok(F.n("134") === 134 && F.n(null) === 0 && F.n(9999) === 200 && F.n(-5) === 0, "分数钳位 0–200");
ok(F.p('```json\n{"S":{"score":1}}\n```').S.score === 1, "剥掉 Markdown 围栏后仍能解析");
ok(F.p('好的，这是评分卡：{"a":1} 以上。').a === 1, "前后有寒暄也能取出 JSON");
try { F.p("完全没有大括号"); ok(false, "无 JSON 时应抛错"); } catch (e) { ok(true, "无 JSON 时抛错而不是静默出空卡"); }

console.log("— 五、worker.js：iq 模式的硬条款 —");
const iqBlk = wk.slice(wk.indexOf('if (mode === "iq") {'), wk.indexOf('// ===== 单次调用发流'));
ok(iqBlk.length > 3000, "iq 分支存在且不是空壳");
ok(/匿名来稿/.test(iqBlk), "铁律一：来稿以匿名呈现（盖住出处）");
ok(/不加分.*不减分|「名家写的」不加分/.test(iqBlk), "出处不影响分数");
ok(/综合分由系统按固定权重计算[^。]*你不许自己算/.test(iqBlk), "铁律二：禁止基底手算综合分");
ok(/逐字存在的句子/.test(iqBlk), "铁律三：证据句必须逐字取自原文");
ok(/0\.20/.test(iqBlk) && /0\.25/.test(iqBlk) && /0\.15/.test(iqBlk), "五维权重写进了提示");
ok(/闸门/.test(iqBlk) && /120 以下/.test(iqBlk), "两道闸门（I/F <120 一票否决）");
ok(/伪发生/.test(iqBlk) && /推不翻/.test(iqBlk), "头号靶子伪发生");
ok(/评分者五偏差|过度通胀/.test(iqBlk), "评分者五偏差防线");
ok(/敌意拓宽/.test(iqBlk) && /之外找/.test(iqBlk), "敌意拓宽：必须往本行之外找占位者");
ok(/校准锚点/.test(iqBlk) && /100–105/.test(iqBlk), "校准锚点防分数漂移");
ok(/handled/.test(iqBlk) && /narrow/.test(iqBlk), "输出含最近邻 handled 与收窄口径 narrow");
ok(/50 字/.test(iqBlk), "I 维的 50 字压缩测试");
ok(!/内功/.test(iqBlk), "评分者不装内功（装了会对 SDE 语言过敏性加分）");

console.log("— 六、worker.js：polish 模式的硬条款 —");
const poBlk = wk.slice(wk.indexOf('if (mode === "polish") {'), wk.indexOf('else if (part === 1)'));
ok(poBlk.length > 2000, "polish 分支存在且不是空壳");
ok(/S≥135、D≥142、E≥130、I≥132、F≥135/.test(poBlk), "135 目标已换算成五维硬指标");
ok(/I ＞ F ＞ E ＞ S ＞ D/.test(poBlk), "力气按 I>F>E>S>D 分配（天花板一直在 I 与 F）");
ok(/这是打磨，不是另写一篇/.test(poBlk), "纪律一：保留原稿已挣到的分");
ok(/每一条扣分记录都必须在改稿中被正面处理/.test(poBlk), "纪律二：评分卡逐条清账");
ok(/只增不注水/.test(poBlk), "纪律三：新增段落必须承担具体职能");
ok(/可裁决差异/.test(poBlk), "未交手的占位者必须写出可裁决差异");
ok(/当场交出执行结果|真跑的结果/.test(poBlk), "F：承诺的检验必须当场执行");
ok(/〔上半篇完·待续〕/.test(poBlk) && /〔全文完〕/.test(poBlk), "上下半篇的收尾标记齐备");

console.log("— 七、路由与守卫 —");
ok(/_MODES = \{ recommend: 1, paper: 1, iq: 1, polish: 1 \}/.test(wk), "四个模式都在白名单里");
ok(/mode === "paper" \|\| mode === "polish"/.test(wk), "polish 复用成文分支（内功+心得+自检规程 v3 零重复）");
ok(/mode !== "paper" && mode !== "polish"/.test(wk), "四步法分支不会劫持 polish");
ok(/deep = body\.deep === true \|\| mode === "paper" \|\| mode === "polish"/.test(wk), "polish 走深度档，iq 不走");
ok(/gmode/.test(html), "页面把 gmode 透传给两段续写机");
ok(/genTarget\('polishStat','ppFill2','ppChars2'\)/.test(html), "打磨时进度打在打磨稿自己的状态行上");
ok(/genTarget\('paperStat','ppFill','ppChars'\)/.test(html), "跑完切回成文一篇的状态行");
ok(/id="btnIq"/.test(html) && /id="btnPolish"/.test(html), "两个按钮已挂在答后动作条上");
ok(/同基底自评 · 非独立认证/.test(html), "同基底既写又评时卡片自报非认证");

console.log("\n" + (FA ? "✗ " : "✓ ") + P + " PASS / " + FA + " FAIL");
process.exit(FA ? 1 : 0);
