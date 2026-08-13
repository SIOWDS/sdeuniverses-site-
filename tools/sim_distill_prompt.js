/* 只测一件事：站内搜索页「提炼精华」(/api/ask mode=distill) 的 system prompt。
   把 worker 里 mode==="distill" 那整块抠出来真跑，拿到规划段与两段正文实际发出去的 sys，
   再逐条断言。

   为什么要这份脚本（2026-08-13）：这一步是整条产线的枢纽——论文水平主要由这份入口资料决定。
   而此前它**只装了内功与心得、没装方法论**：关于方法论的全部内容只有一句称呼
   「你是一位以 SDE 方法论为隐性引擎的资深学者」。那是身份不是工序。
   于是九栏里〔三〕承重命题、〔四〕分离点、〔五〕敌意最近邻、〔七〕可裁决判据——
   逐条都是二阶碰撞的产出物——却没有任何一处告诉它二阶碰撞怎么走。
   这类缺失不会报错，只会安静地退回一阶（产出一个漂亮新名字），所以必须由断言守住。 */
"use strict";
const fs = require("fs");
const src = fs.readFileSync("/home/claude/site/src/worker.js", "utf8");

let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };

const a = src.indexOf('else if (mode === "distill") {');
const b = src.indexOf('else if (mode === "paper" || mode === "polish") {');
if (a < 0 || b <= a) { console.log("FAIL 抠不出 distill 块（锚点变了，先改本脚本）"); process.exit(1); }
const seg = "if (true) " + src.slice(a + "else ".length, b);

/* ⚠ 方法论指引必须从源码里取真的那一份传进去，不许在本脚本里手抄一段假的——
   手抄的后果不是报错，是它安静地测一个已经不存在的版本。 */
const gm = /const WDS_METHOD_GUIDE = "([\s\S]*?)";\n/.exec(src);
if (!gm) { console.log("FAIL 抠不出 WDS_METHOD_GUIDE"); process.exit(1); }
const GUIDE = JSON.parse('"' + gm[1] + '"');

function build(part, body) {
  const fn = new Function("part", "body", "q", "ctxText", "neigong", "reflect", "originQ", "hist", "histTxt", "WDS_METHOD_GUIDE",
    'const mode = "distill"; let MAXTOK = 0, sys = "", usrOverride = "";\n' + seg + "\nreturn { MAXTOK, sys, usrOverride };");
  return fn(part, body || {}, "问题", "站内资料正文", "内功正文", "心得正文", "缘起之问", [{ q: "一问" }], "〔第1轮〕问：一问\n答", GUIDE);
}
const B0 = build(0), B1 = build(1), B2 = build(2);

console.log("— 一、全套装载：内功 ＋ 心得 ＋ 完整方法论（用户 2026-08-13 定的口径）—");
for (const [n, X] of [["规划段", B0], ["第一段", B1], ["第二段", B2]]) {
  ok(X.sys.includes("内功正文"), n + "：装了完整内功");
  ok(X.sys.includes("心得正文"), n + "：装了心得");
  ok(X.sys.includes(GUIDE), n + "：装了**完整**方法论指引（逐字，不是节选、不是复述）");
}
/* 只有一句「以 SDE 方法论为隐性引擎」是身份不是工序——这条断言就是为了不让它再退回那个状态 */
ok(B1.sys.indexOf("二阶碰撞") > 0 && B1.sys.indexOf("敌意最近邻定位") > 0,
  "方法论第五节（二阶碰撞六步）真的在里面——九栏要的产物全靠它");
ok(B1.sys.includes("三大方程") && B1.sys.includes("六路径") && B1.sys.includes("123"),
  "三件工具齐全（三方程／六路径／123原理）");

console.log("— 二、这一步专属的工序：找金点子 → 挑脊梁骨 —");
for (const [n, X] of [["规划段", B0], ["第一段", B1], ["第二段", B2]]) {
  ok(X.sys.includes("一阶产物"), n + "：明令先把一场问对里的一阶产物（候选金点子）全捞出来");
  ok(X.sys.includes("敌意最近邻定位 → 代理坍缩"), n + "：明令逐个走二阶碰撞前三步");
  ok(X.sys.includes("X 不是 Y₁、也不是 Y₂，而是 Z"), n + "：脊梁骨要写成控制变量形态");
  ok(X.sys.includes("挑不出唯一一条"), n + "：立不住时准许写「还没长出脊梁骨」，不许硬立一个");
}
ok(B1.sys.includes("提炼不是做摘要"), "开宗明义：这一步不是摘要");
ok(/站外最近邻引了几个/.test(B1.sys) && /名字还是一条分离线/.test(B1.sys),
  "收口自检四问在位（0 个最近邻＝一阶／名字＝一阶／无判据＝不可证伪／自封要删）");
ok(B1.sys.includes("四问的答案要落进第三、四、五、七栏"), "自检结果要落进栏目，不许另开一栏复述工序");

console.log("— 二之二、用户 2026-08-13 定的六条原则，逐条守住 —");
/* 这六条是口径，不是建议。它们不会因为掉了一条而报错，只会让产出安静地退回
   「一份平铺的会议纪要」——所以每条都要有一句断言钉住。 */
for (const [n, X] of [["规划段", B0], ["第一段", B1], ["第二段", B2]]) {
  ok(X.sys.includes("〔原则一·不许偏题〕") && X.sys.includes("如何服务于缘起之问"),
    n + "：原则一·不许离开《缘起之问》这个主题");
  ok(X.sys.includes("〔原则二·围绕这一个问题做三维展开〕") && X.sys.includes("不许把三支写成同一件事的三种说法"),
    n + "：原则二·围绕同一问题做三维展开（并拦住假三维）");
  ok(X.sys.includes("〔原则三·层级推演，不是平面罗列〕") && X.sys.includes("推不下去的"),
    n + "：原则三·层级推演（推不下去要写明卡在哪，不许含糊过去）");
  ok(X.sys.includes("〔原则四·全篇是一棵树，编号贯通〕") && X.sys.includes("M1.1.1"),
    n + "：原则四·树状系统＋三级编号贯通");
  ok(X.sys.includes("形态要求，不加字数"),
    n + "：层级是形态不是加料——各栏字数照旧（否则必写不完）");
}
ok(B0.sys.includes("【先画树】") && B0.sys.includes("一个节点一行，不展开内容"),
  "规划段的活已改成「先画树」：先列节点名与编号，不展开");
ok(B0.sys.includes("把《缘起之问》原样抄一遍"), "树根就是缘起之问原句");
ok(B1.sys.includes("【本段的形态】") && B1.sys.includes("挂 M2.3.1"),
  "第一段：分离点要挂到具体节点编号上");
ok(B2.sys.includes("沿用第一段已经立好的节点编号，不另起一套"),
  "第二段：编号贯通（另起一套＝下游按编号取料时取空）");
ok(B2.sys.includes("本场岔出、与《缘起之问》接不上的那些内容"),
  "第九栏专收岔题项——偏题的东西有地方放，才不会混进核心判断");

console.log("— 三、工序在后台走，栏目里只留结果（护住下游那篇论文的改姓）—");
ok(B1.sys.includes("目标学科的母语"), "承重命题与判据用学科母语写（已改姓）");
ok(/不写「S 维度／D 维度／三视角／逮先验」这类词/.test(B1.sys),
  "内部环节词不许进命题措辞（下游论文正文明令禁用它们）");
/* 原则二要三维展开、原则六要改姓——两者靠「标注 vs 措辞」分开：
   骨架用方括号标注，命题用学科母语。这条缝要是糊掉，不是维度丢了就是论文被污染。 */
ok(B1.sys.includes("〔显露面〕〔差异面〕〔纠缠面〕") && B1.sys.includes("这些方括号标注一律不进正文"),
  "三个着力面只作方括号骨架标注，成文时不进正文（三维展开与改姓两不误）");

console.log("— 四、回归：原有的九栏契约一个字没动 —");
ok(B1.sys.includes("栏标题原样照抄，一个字不许改、栏号不许重排"), "栏名与栏号仍然写死（改名即全线取空）");
ok(B0.sys.includes("本次**不写正文**"), "规划段仍是不进正文的取舍清单");
ok(B0.MAXTOK === 12000 && B1.MAXTOK === 32000 && B2.MAXTOK === 32000, "预算仍是 12000／32000／32000 · 实得 " + [B0.MAXTOK, B1.MAXTOK, B2.MAXTOK].join("/"));
ok(B1.sys.includes("〔第一段完·待续〕") && B2.sys.includes("〔全文完〕"), "两段各自的收尾标记仍在");
ok(B1.sys.includes("四、反复被触到的分离点") && B2.sys.includes("五、敌意最近邻清单"), "九栏分段仍是 1–4 ／ 5–9");
ok(B2.sys.includes("先从《已写部分·结尾》停笔处无缝续写"), "第二段仍带续写锚");
ok(B0.usrOverride.indexOf("《已写部分·开头》") < 0, "规划段不带续写锚（它在最前面）");

/* 装了方法论就是往固定前缀里再加约四千字。它是预填不是新调用，但预填时间照样算在
   平台那道墙里——所以把它记成一条明账，别让下一个人以为这是免费的。 */
console.log("— 四之二、入料上限：读全场的那几刀要看得全（2026-08-13「可以更大」）—");
{
  const W = src;
  /* 病灶：每轮答案此前切 2600 字，而深度档一轮就写 1700–2100、自动十轮每轮 2000–2600，
     正好卡在边界上——长的那几轮是**被砍着尾巴**进提炼的。基底窗口有 1M，这刀砍得毫无必要。 */
  ok(/const _fullRead = \(mode === "distill" \|\| mode === "paper" \|\| mode === "polish" \|\| mode === "synth"\)/.test(W),
    "「读全场」的四档单独成一个集合（提炼／成文／打磨／综合）");
  const mSlice = /\.slice\(_fullRead \? -(\d+) : -(\d+)\)/.exec(W);
  ok(!!mSlice && Number(mSlice[1]) > Number(mSlice[2]), "读全场时取更多轮次 · 实得 " + (mSlice && mSlice[1]) + " vs " + (mSlice && mSlice[2]));
  const mAns = /a: String\(\(t && t\.a\) \|\| ""\)\.trim\(\)\.slice\(0, _fullRead \? (\d+) : (\d+)\)/.exec(W);
  /* 深度档一轮写 1700–2100 字、涌现档约 3000 字 —— 上限要高到任何一轮都摸不到，
     那才叫「不截断」；两万字只是把最长的那几轮放过，仍是个会咬人的数。 */
  ok(!!mAns && Number(mAns[1]) >= 30000,
    "每轮答案实质不再截断（上限高到任何一轮都摸不到）· 实得 " + (mAns && mAns[1]));
  ok(!!mAns && Number(mAns[2]) === 2600,
    "⚠ 每轮都要跑的那一档**一个字没动**：它的预填时间算在平台 130 秒的墙里，放宽＝把撞墙提前 · 实得 " + (mAns && mAns[2]));
  const mCtx = /const CTX_MAX = _lightDeep \? (\d+)/.exec(W);
  ok(!!mCtx && Number(mCtx[1]) >= 40000, "《站内资料》上限同步放开 · 实得 " + (mCtx && mCtx[1]));
  ok(/本刀入料 · 合计约/.test(W) && /问对全文 " \+ hist\.length \+ " 轮/.test(W),
    "入料字数印在屏幕上（放开了钳位，就必须能和「前置几秒」对着看，否则下次又只能猜）");
  /* 用户口径：十轮问对做成**一份文档**送进去。三刀共用同一份、逐字节相同 ⇒ 命中前缀缓存，
     所以它必须排在会变的东西（规划清单、已写部分）之前——前缀一变，缓存就从变动处断掉。 */
  ok(/《整场问对全文 · 共 " \+ hist\.length \+ " 轮 · 未做任何截断》/.test(W),
    "全场问对以「一份完整文档」的名义送进去，并写明未截断");
  ok(/这是唯一的原始材料，也是完整的/.test(W), "并告诉基底：只能从这份文档里提");
  for (const [n, X] of [["规划段", B0], ["第一段", B1], ["第二段", B2]]) {
    const iDoc = X.usrOverride.indexOf("《整场问对全文");
    const iPlan = X.usrOverride.indexOf("《本次的取舍清单》");
    const iWrit = X.usrOverride.indexOf("《已写部分");
    ok(iDoc > 0, n + "：文档在位");
    ok(iPlan < 0 || iDoc < iPlan, n + "：文档排在会变的规划清单之前（否则前缀缓存断在这里）");
    ok(iWrit < 0 || iDoc < iWrit, n + "：文档排在会变的已写部分之前");
  }
}

console.log("— 五、代价记明账 —");
const extra = GUIDE.length;
ok(extra > 1500 && extra < 6000, "方法论块在两千字量级（不是节选、也没膨胀）· 实得 " + extra + " 字");
console.log("  （一刀入料现为：内功≈3.3万字 ＋ 心得 ＋ 方法论 " + extra + " 字 ＋ 本步工序约 1.2 千字 ＋ 站内资料 0（检索已整段跳过）＋ 整场问对全文·未截断；十轮全文约两三万字，远小于 1M 窗口）");

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
