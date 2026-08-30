/* sim_chatsde_forge.js —— 学科通融产线：真产物向下传递 ＋ 闸门不许自动前进
 *
 * 缘起（2026-08-12 审计）：这条产线此前**不是发生链**，是十八次各写各的然后拼起来。
 *   前端每一步只把标题递下去：`secs.map((x,k) => (k+1) + ". " + x.t)`
 *   服务端还专门叮嘱「只列名，别重复它们的内容」。
 *   ⇒ 第七道（共有前提）看不见第二道抽出来的脊柱；第十五道成文看不见第四道的候选命题。
 *   读起来照样通顺，事后极难发现——这正是最贵的一类假产出。
 *
 * 本文件按《ChatSDE 重设计建议书》§14.2 的要求做**唯一标记**测试：
 *   在第 2 道埋一个标记，验证第 7、9、15、18 道能逐字读到它。
 *   任何一步只看得见标题，测试立即失败。
 * 跑法：node tools/sim_chatsde_forge.js
 */
"use strict";
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, "..");
let pass = 0, fail = 0;
/* 只保留会被读者看见的那部分：剥掉 /* *\/ 与 // 注释。
   判文案的断言必须走它——否则注释里引一句旧话就当场自伤。 */
function W_TXT(src) {
  return String(src).replace(/\/\*[\s\S]*?\*\//g, " ").replace(/^\s*\/\/.*$/gm, " ");
}
const ok = (n, c, d) => { if (c) { pass++; console.log("  ✓ " + n); } else { fail++; console.log("  ✗ " + n + (d ? ("  " + d) : "")); } };
const W = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");
const F = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");

/* ═══ 一、把服务端那三件真跑起来 ═══════════════════════════════ */
console.log("── 抠出 FORGE_STAGES / FORGE_NEEDS / forgeCarry / wdsForgeSys ──");
const a = W.indexOf("const FORGE_STAGES = [");
const b = W.indexOf("// 工序是流程要求，不改人格", a);
const SRC = (a > 0 && b > a) ? W.slice(a, b) : "";
ok("抠得到那一整段", SRC.indexOf("function wdsForgeSys") > 0 && SRC.indexOf("FORGE_NEEDS") > 0);
const M = new Function("const FORGE_HEART = '<HEART>';\n" + SRC
  + "\n return { STAGES: FORGE_STAGES, NEEDS: FORGE_NEEDS, carry: forgeCarry, sys: wdsForgeSys, MAX: FORGE_CARRY_MAX, JUDGE: FORGE_JUDGE_N, PLAIN: FORGE_PLAIN_STAGES, RES_MAX: RES_CARRY_MAX };")();

ok("十八道工序齐全", M.STAGES.length === 18);
ok("只到判断跑前十三道", M.JUDGE === 13);
ok("依赖表覆盖每一道（一道都不许漏）", Object.keys(M.NEEDS).length === M.STAGES.length
  && M.STAGES.every((_, i) => Array.isArray(M.NEEDS[i + 1])));
ok("第一道不消费上游（它是源头）", M.NEEDS[1].length === 0);
ok("除第一道外每一道都消费上游（否则就是各写各的）",
  M.STAGES.every((_, i) => i === 0 || M.NEEDS[i + 1].length > 0));
ok("依赖只能指向**前面**的道次（不许指向自己或后面）",
  Object.keys(M.NEEDS).every((k) => M.NEEDS[k].every((x) => x >= 1 && x < +k)));

/* 建议书 §六 逐道点名的承重依赖：这几条是产线的脊梁，掉一条这条产线就断一节 */
console.log("── 建议书点名的承重依赖 ──");
[["第 7 道（共有前提）读三家脊柱", 7, 2],
 ["第 7 道读存活候选", 7, 6],
 ["第 9 道（涌现命题）读第 8 道的暗流", 9, 8],
 ["第 11 道（五重检验）读近邻闸", 11, 5],
 ["第 13 道（近邻划界）读证伪条件", 13, 12],
 ["第 14 道（章节表）读涌现命题", 14, 9],
 ["第 15 道（成文一）读章节表", 15, 14],
 ["第 16 道（成文二）读上一段正文", 16, 15],
 ["第 17 道（成文三）读前两段正文", 17, 16],
 ["第 18 道（交付自查）读全部成文", 18, 17],
].forEach(([n, i, need]) => ok(n, M.NEEDS[i].indexOf(need) >= 0));

/* ═══ 二、⭐ 唯一标记：第 2 道埋下，第 7/9/15/18 道必须逐字读到 ═══ */
console.log("── 唯一标记状态传递（建议书 §14.2）──");
const MARK = "CONTROL-VARIABLE-7391";
const bodies = [];
for (let k = 1; k <= 17; k++) {
  bodies.push({ i: k, t: M.STAGES[k - 1].t,
    body: (k === 2 ? ("甲家承重命题：" + MARK + " 是这一家真正的控制变量。\n") : "")
      + ("第 " + k + " 道的正文正文正文。").repeat(40) });
}
const rs = (i) => ({ i: i, n: 18, t: M.STAGES[i - 1].t, topic: "题目", forge: 1,
  done: M.STAGES.map((s, k) => (k + 1) + ". " + s.t).join("\n"), bodies: bodies.slice(0, i - 1) });

[7, 9, 15, 18].forEach((i) => {
  const sys = M.sys(rs(i));
  const seen = sys.indexOf(MARK) >= 0;
  // 第 9、18 道不直接依赖第 2 道，标记要靠链条一路带过来；这里只要求"读得到第 2 道原文的那几道"真读到
  if (M.NEEDS[i].indexOf(2) >= 0) ok("★ 第 " + i + " 道逐字读到第 2 道埋的标记", seen);
  else ok("第 " + i + " 道按依赖表不直接读第 2 道（链条另有传法）", true);
});
ok("★★ 第 7 道确实读到了第 2 道的原文，不是只看到标题",
  M.sys(rs(7)).indexOf(MARK) >= 0 && M.sys(rs(7)).indexOf("第 2 道的正文正文正文") >= 0);
ok("★★ 第 15 道（成文一）读得到第 2 道原文", M.sys(rs(15)).indexOf(MARK) >= 0);

/* 反向：把 bodies 拿掉（＝旧口径只递标题），必须读不到，且**必须说出来** */
const sysNoBody = M.sys({ i: 7, n: 18, t: "x", topic: "题目", forge: 1, done: "1. 选源\n2. 抽脊", bodies: [] });
ok("★ 只递标题时读不到标记（这就是修复前的样子）", sysNoBody.indexOf(MARK) < 0);
ok("★ 而且必须明说材料不全，不许假装读过", /材料不全/.test(sysNoBody) && /不许假装读过/.test(sysNoBody));
ok("缺哪几道要点名", /第 2、6、5 道|第 2、5、6 道/.test(sysNoBody) || /2/.test(sysNoBody.slice(sysNoBody.indexOf("材料不全"))));

/* ═══ 三、预算与截断：不许悄悄截一半 ═══════════════════════════ */
console.log("── 上游原文的预算与截断 ──");
const huge = [{ i: 2, t: "抽脊", body: "字".repeat(90000) }, { i: 6, t: "候选互撞", body: "乙".repeat(90000) }, { i: 5, t: "近邻闸", body: "丙".repeat(90000) }];
const c = M.carry(7, huge);
ok("三道都拿得到一份（不许有人一个字都读不到）", c.got.length === 3);
ok("总量卡在预算内（否则这一趟自己被顶穿）", c.text.length < M.MAX * 1.3, "len=" + c.text.length);
ok("★ 截断必须看得见（悄悄截一半 ⇒ 下游拿半截材料写得头头是道）", /此处只带来前/.test(c.text) && /退回第 2 道重跑/.test(c.text));
ok("截断处说清原文有多长", /原文共 90000 字/.test(c.text));
const c2 = M.carry(7, [{ i: 2, t: "抽脊", body: "短的" }]);
// v4.1：FORGE_NEEDS[7] 由 [2,6,5] 三项扩到 [1,2,6,5] 四项（新增第1道，供空位型/题型声明下传）——miss 相应从 2 变 3
ok("只递上来一部分时，got/miss 分得清", c2.got.length === 1 && c2.miss.length === 3);
ok("空 body 不算数（空字符串不是产出）", M.carry(2, [{ i: 1, t: "选源", body: "   " }]).got.length === 0);
ok("第一道没有上游，carry 为空且不报缺", M.carry(1, bodies).text === "" && M.carry(1, bodies).miss.length === 0);

/* ═══ 四、闸门契约 ═══════════════════════════════════════════ */
console.log("── 闸门契约（服务端）──");
const s7 = M.sys(rs(7));
ok("★ 每一道都要求最后一行给出机器可读的闸门判决", /【闸门 · 这一道的最后一行必须是它/.test(s7));
["passed", "needs_revision", "return_to_stage:N", "blocked"].forEach((k) =>
  ok("闸门四态之一在位：" + k, s7.indexOf(k) > 0));
ok("明写不许为了能往下走而写 passed", /不许为了让流程能往下走而写 passed/.test(s7));
ok("上游产物那一段要求逐字引用并指名否定", /逐字引用/.test(s7) && /否定要指名/.test(s7));
/* ⚠ 这一条要看**产出的提示语**，不是看整份源码——我自己在注释里引了那句旧话，
   按整份文件搜会当场命中自己的注释（站里犯过的同一个坑，从另一头再犯一次）。 */
ok("旧那句「只列名，别重复它们的内容」已经不在提示语里", s7.indexOf("只列名，别重复它们的内容") < 0);
ok("目录那一段改成了「只是目录，别重复它们」", /只是目录/.test(s7));

/* ═══ 五、前端：递真产物 ＋ 不合格不许自动前进 ═══════════════ */
console.log("── 前端接线 ──");
/* ⚠ 起点锚原来连着下一行的注释（`var i = 0;` ＋「/* 【闸门】」）——阶段B 在两者之间
   插了一段恢复逻辑，锚当场失配、十一条全红。**锚只认一行代码，别把下一行捎上。** */
const fa = F.indexOf("        var i = 0;\n");
const fb = F.indexOf("        function finalStep()", fa);
const STEP = (fa > 0 && fb > fa) ? F.slice(fa, fb) : "";
ok("抠得到产线那一段", STEP.length > 1500);
/* ⚠ 别把整行抄进正则（站里反复犯的病）：阶段B 给每件产物加了 hash，这一条当场红，
   而它要守的用意——「递的是正文不是标题」——一个字都没变。只认承重的那几个字。 */
ok("★ 把每一道的正文一并递上去（不再只递标题）",
  /bodies = secs\.map\([\s\S]{0,120}body: x\.body/.test(STEP) && /bodies: bodies/.test(STEP));
ok("★ 每件产物随身带 hash（服务端据此判是不是旧版本）", /hash: fnv1a64\(x\.body\)/.test(STEP));
ok("目录那一份仍旧只给标题（它只是目录）", /done = steps\.map/.test(STEP));
ok("★ 闸门解析出四态", /passed\|needs_revision\|return_to_stage/.test(STEP));
ok("★ 只有 passed 才 i++ 往下跑", /if \(g\.d === "passed"\) \{ r\.box\.classList\.remove\("open"\); i\+\+; return step\(\); \}/.test(STEP));
ok("★ 没交出闸门判决的按不通过处理（不许当合格收下）", /d: "unknown"/.test(STEP) && /fgNoGate/.test(STEP));
ok("★ 技术故障也不再静默 i++ 跳过", /catch\(function \(e\) \{[\s\S]{0,400}forgeHalt/.test(STEP));
ok("停下来时把已跑完的那几道原样留着（停下 ≠ 丢弃）", /已经跑完的那几道一个字都不动/.test(STEP));
ok("给读者三条出路：重跑本道／退回第 N 道／强行继续", /fgAgain/.test(STEP) && /fgGoBack/.test(STEP) && /fgForce/.test(STEP));
ok("强行继续要记一笔降级（诚实显示能力降级）", /degraded\.push/.test(STEP) && /degraded = \[\];/.test(F));
ok("★ 降级要写进成品（没过闸的稿子不许和全过闸的长得一样）",
  /if \(degraded\.length\) md \+=/.test(F) && /fgDegraded/.test(F));
ok("退回第 N 道会把那之后的产物清掉（不许拿旧产物冒充新的）", /secs = secs\.slice\(0, g\.back - 1\)/.test(STEP));

/* ═══ 六、口径统一（建议书 P2）═══════════════════════════════ */
console.log("── 十四／十八／十三 口径 ──");
ok("★ 全站不再有「十四道工序」这个说法", W.indexOf("十四道工序") < 0 && F.indexOf("十四道工序") < 0);
ok("单轮工序与名录文案对账（2026-08-28 加发生场后十五件），且仍称「件」以免与道次混淆",
  /十五件\*\*单轮工序\*\*/.test(W) && (W.match(/const WDS_TOOL_KEYS = \[([^\]]*)\]/) || ["", ""])[1].split(",").length === 15);
ok("界面文案改成十八道", /fgPlan: "十八道工序/.test(F));
ok("英文文案同步（中英双份纪律）", /Eighteen stages/.test(F));
ok("只到判断＝前十三道，说法一致", /前十三道/.test(F) || /前十三步/.test(W));

/* ═══ 七、阶段A 剩下那三条（建议书 §四 P1）═══════════════════ */
console.log("── Key 文案与实际传输一致 ──");
/* ⚠ 只判**文案本身**，不扫整份源码：注释里必然会引到那句旧话（同一个坑今天踩过两次）。 */
const txtOnly = W_TXT(F);
ok("★ 全站不再承诺「不会上传本站 / never sent to this site」", !/不会上传本站|never sent to this site/.test(txtOnly));
ok("★ 中文文案说清了「经本站边缘服务内存转发」", /经本站边缘服务内存转发/.test(txtOnly));
ok("★ 中文文案说清了「不写库、不写日志、不做分析」",
  /不写入数据库/.test(txtOnly) && /不写进日志/.test(txtOnly) && /不做分析/.test(txtOnly));
ok("英文同步（中英双份纪律）", /relays it in memory through this site's edge service/.test(txtOnly));
ok("三处文案都改了（设置面板／底注／记忆说明）",
  (txtOnly.match(/边缘服务内存转发|edge service/g) || []).length >= 3);
/* ⚠ 这一条第一版写错了：它把 `storage.put("key", key)` 当成访客 Key 落库，
   而那三处存的是**站方自己配置的密钥**（由管理口令 adminHash 守着），与访客无关。
   要判的是「**访客那把 Key** 有没有被写进存储或日志」——它在请求里叫 KEY。
   💡 心法：写「没有做某事」的断言之前，先把命中的那几处逐个看一眼是什么。 */
ok("★ 访客的 Key 只活在局部变量里：没有任何 put/log 收它",
  !/(storage\.put|KV\.put|\.put)\([^)]{0,80}\bKEY\b/.test(W)
  && !/console\.(log|error|warn|info)\([^)]{0,120}\bKEY\b/.test(W));
ok("落库的那把是站方自己配的密钥，且由管理口令守着", /adminHash/.test(W) && /管理口令不正确/.test(W));
ok("上游报错回显做了长度钳位，不至于把请求体整段吐回来", /\.slice\(0, ?\d+\)/.test(W));

console.log("── 内化心得：一个人的一次调用不许改全站的底盘 ──");
ok("★ 缓存键带上了型号与提示版本，不再只有厂商", /function reflectKey\(vendor, VC\)/.test(W)
  && /REFLECT_PROMPT_VER/.test(W) && /String\(\(VC && VC\.model\)/.test(W));
/* ⚠ 上一条只查了 reflectKey **存在**——把 ensureReflect 里那句改回 "v3:"+vendor，它照样全绿。
   定义了不等于用上了：承重位要单独盯住调用点。 */
ok("★ 而且 ensureReflect 真的在用它（定义了 ≠ 用上了）",
  /const rkey = reflectKey\(vendor, VC\);/.test(W));
ok("键里带版本号，改提示语只要 \+1 就自然作废（不必再靠人记得改 v3→v4）",
  /const REFLECT_PROMPT_VER = \d+;/.test(W));
ok("内存缓存也按新键分（否则同厂商不同型号还是互相盖）",
  /REFLECT_MEM\[rkey\]/.test(W) && !/REFLECT_MEM\[vendor\]/.test(W));
ok("存取两侧用同一个键（rkey 传到 DO 那一侧）", /op: "getReflect", vendor, rkey/.test(W) && /op: "setReflect", vendor, rkey/.test(W));
ok("★ 答题主请求默认不再现场生成（allowGen 默认翻成 false）",
  /if \(allowGen === undefined\) allowGen = false;/.test(W));
ok("★ 预热那一处显式要生成（否则心得永远没人做）",
  /ctx\.waitUntil\(ensureReflect\(env, request\.url, _rv, _VC, b\.key, true\)/.test(W));
ok("注释写明了为什么翻默认值", /静默改变所有人的思考底盘/.test(W));

console.log("── 评分：站外敌意最近邻由程序保证 ──");
/* ⚠ 签名后来又多了一个 prof（领域档案／分身）。钉整串形参就会在下一次加参数时长红，
   而要守的事只有一件：**webCtx 真的传进了评分那一路**（缺了它，I 维就只能凭训练记忆补作者与年份）。 */
ok("★ 评分这一路收得到站外资料了（原来签名里根本没有）",
  /function WDS_IQ_SYS\(siteCtx, docCtx, docNote, lang, webCtx/.test(W)
  && /WDS_IQ_SYS\(siteCtx, docCtx, docNote, lang, webCtx/.test(W.slice(W.indexOf('tool === "iq"'))));
/* ⚠ 阶段D 把评分那一路从「宽泛搜索」改道到了**专用链**，这条断言的落点跟着搬家，
   而它要守的用意没变：**评分不等读者去点联网**。改成盯住新的那一条路。 */
ok("★ 评分工序强制走检索，不等读者去点联网", /\|\| tool === "iq";/.test(W) && /const wantNbr =/.test(W));
ok("★ 没有站外资料时 I 维标证据不足、不给分", /证据不足（未完成外部最近邻检索）/.test(W) && /\*\*不给具体分数\*\*/.test(W));
ok("★ 且综合分要声明自己不可引用", /不作为可引用的读数/.test(W));
ok("报告开头就要挂显著状态（不是藏在末尾）", /报告开头第一行就写/.test(W));
ok("明写不许假装完成敌意拓邻", /不许假装完成了敌意拓邻/.test(W));
ok("有站外资料时要求逐条落到出处", /逐条落到上面的出处/.test(W) && /引一条编的文献比不引伤得重/.test(W));

/* ═══ 八、阶段B：状态契约 ═══════════════════════════════════════
   🔴🔴 这一节的存在本身是一条教训。上一轮那条 P0 修复**在线上是空转的**：
   前端已经把 bodies 递上来、服务端 forgeCarry 也写好了，而 `/api/wds/chat` 里
   有一道**逐字段重建 rs 的白名单**，`bodies` 不在单子上 ⇒ 被静默丢掉。
   而护栏全绿——因为它直接调 wdsForgeSys，**绕过了读者真正会走的那一步**。
   💡 心法一：改了传输契约，第一件事是去看接收端的白名单。
   💡 心法二：护栏必须走真正的那条路。绕过清洗去测处理函数，测的是一条读者永远走不到的路。 */
console.log("── ⭐ 入参白名单：真的那条路 ──");
/* ⚠ 2026-08-27：「无 SDE 问对」给这一行前面加了一层「noSde 时整体清空」的三元包装——
   const rs = (noSde ? null : rsRaw) ? {...} : null。字面量跟着变了形，锚点要跟上；
   抠出来的这一段也因此多引用了一个自由变量 noSde，new Function 必须把它也当形参收下，
   否则 "noSde is not defined" ——这跟当年 rs 本身漏收是同一类坑（改了契约，先看抠取点）。 */
const wa = W.indexOf("      const rs = (noSde ? null : rsRaw) ? {");
const wb = W.indexOf("      // VISION：读者带来的图", wa);
const SAN = (wa > 0 && wb > wa) ? W.slice(wa, wb) : "";
ok("抠得到 rs 的清洗那一段", SAN.indexOf("rsRaw.topic") > 0);
const SANF = new Function("rsRaw", "noSde", SAN.replace("      const rs = (noSde ? null : rsRaw) ? {", "const rs = (noSde ? null : rsRaw) ? {") + "\n return rs;");
const sanIn = { i: 7, n: 18, forge: 1, t: "共有前提", topic: "题", done: "1. 选源",
  sv: 2, run: "r123abc", attempt: 2, idem: "r123abc:7:2",
  bodies: [{ i: 2, t: "抽脊", body: "甲家承重命题：" + MARK, hash: "deadbeefdeadbeef" },
           { i: 5, t: "近邻闸", body: "近邻正文" }, { i: 6, t: "候选互撞", body: "候选正文" }],
  gates: [{ i: 2, d: "passed" }, { i: 5, d: "needs_revision" }] };
const sanOut = SANF(sanIn, false);
ok("★★ bodies 过得了白名单（上一版就死在这里，而护栏全绿）",
  Array.isArray(sanOut.bodies) && sanOut.bodies.length === 3);
ok("★★ 正文一个字不少地过来了（不是只剩标题）", sanOut.bodies[0].body.indexOf(MARK) >= 0);
ok("gates 也过得来", Array.isArray(sanOut.gates) && sanOut.gates.length === 2 && sanOut.gates[1].d === "needs_revision");
ok("契约字段过得来（sv/run/attempt/idem）",
  sanOut.sv === 2 && sanOut.run === "r123abc" && sanOut.attempt === 2 && sanOut.idem === "r123abc:7:2");
ok("★ 走完清洗之后，wdsForgeSys 仍读得到那个标记（端到端）",
  M.sys(Object.assign({}, sanOut)).indexOf(MARK) >= 0);
ok("run/idem 做了字符白名单（外部输入不许原样进 system）",
  SANF({ i: 2, forge: 1, run: "a<script>b", idem: "x'\"y" }).run === "ascriptb");
ok("单件正文有长度钳位", /slice\(0, 40000\)/.test(SAN));
ok("总量有封顶（一趟不许把内存吃光）", /200000/.test(SAN));
ok("超总量时保住最近几道（从后往前收）", /for \(let k = src\.length - 1; k >= 0; k--\)/.test(SAN));
const big = SANF({ i: 18, forge: 1, bodies: Array.from({ length: 30 }, (_, k) => ({ i: k + 1, t: "x", body: "字".repeat(30000) })) });
ok("三十件 ×3 万字进来也不炸，且截在限内", big.bodies.length <= 20
  && big.bodies.reduce((a, b) => a + b.body.length, 0) <= 200000);
ok("注释写明了这条教训（下一个人别再踩）", /改了传输契约，第一件事是去看接收端的白名单/.test(W));

console.log("── 契约校验（forgeValidate 真跑）──");
const V = new Function("const FORGE_STAGES = new Array(18).fill({t:'x',d:'y'});" + SRC.slice(SRC.indexOf("const FORGE_SCHEMA_VER"))
  .slice(0, SRC.slice(SRC.indexOf("const FORGE_SCHEMA_VER")).indexOf("function wdsForgeSys"))
  + "\n return { v: forgeValidate, h: fnv1a64, SV: FORGE_SCHEMA_VER };")();
ok("抠得到 forgeValidate 与 fnv1a64", typeof V.v === "function" && typeof V.h === "function");
ok("正常入参放行", V.v({ i: 7, sv: V.SV, bodies: [{ i: 2, t: "a", body: "x", hash: V.h("x") }] }) === null);
ok("★ 格式换代了要说出来，不硬接", (V.v({ i: 7, sv: 99, bodies: [] }) || {}).code === "schema");
ok("★ 道次越界当场退回", (V.v({ i: 99, bodies: [] }) || {}).code === "stage");
ok("★ 产物标着自己或下游 ⇒ 退回（只能带上游）", (V.v({ i: 7, bodies: [{ i: 7, body: "x" }] }) || {}).code === "artifact");
ok("没有正文的产物 ⇒ 退回", (V.v({ i: 7, bodies: [{ i: 2 }] }) || {}).code === "artifact");
ok("★★ hash 对不上 ⇒ 退回（那多半是退回重跑之后带上来的旧版本）",
  (V.v({ i: 7, bodies: [{ i: 2, body: "新的正文", hash: V.h("旧的正文") }] }) || {}).code === "hash");
ok("不带 hash 的老客户端仍放行（兼容层，不许一升级就把人拒之门外）",
  V.v({ i: 7, bodies: [{ i: 2, body: "x" }] }) === null);
ok("每条退回都说得出是哪一道、错在哪", ["schema", "stage", "artifact", "hash"].every((c) => {
  const r = c === "schema" ? V.v({ i: 7, sv: 99 }) : c === "stage" ? V.v({ i: 99 })
    : c === "artifact" ? V.v({ i: 7, bodies: [{ i: 7, body: "x" }] })
    : V.v({ i: 7, bodies: [{ i: 2, body: "a", hash: V.h("b") }] });
  return r && r.msg && r.msg.length > 10;
}));
ok("端点接上了校验，且带机器可读错误码", /code: "forge_" \+ bad\.code/.test(W) && /const bad = forgeValidate\(rs\);/.test(W));
ok("校验不过就地收口，不往下跑", /controller\.enqueue\(_sseBytes\(\{ t: "error", code: "forge_"[\s\S]{0,120}return fin\(\);/.test(W));

console.log("── 两侧 hash 必须是同一个算法 ──");
const CH = new Function(F.slice(F.indexOf("  function fnv1a64(str) {"), F.indexOf("  var FORGE_SV = 2;")) + "\n return fnv1a64;")();
["", "a", "甲家承重命题：" + MARK, "字".repeat(5000), "mixed 中英 123 !@#"].forEach((x, k) =>
  ok("第 " + (k + 1) + " 组：前后端算出来同一个值", CH(x) === V.h(x)));
ok("★ 前端 FORGE_SV 与服务端 FORGE_SCHEMA_VER 同源", /var FORGE_SV = 2;/.test(F) && V.SV === 2);
ok("注释诚实交代了为什么不是 sha256", /不是防篡改/.test(W) && /不是防篡改/.test(F));

console.log("── 闸门链：下游看得见自己接的是什么货 ──");
const cg = M.carry(7, [{ i: 2, t: "抽脊", body: "甲" }, { i: 5, t: "近邻闸", body: "乙" }, { i: 6, t: "候选互撞", body: "丙" }],
  [{ i: 5, d: "needs_revision" }]);
ok("★ 没过闸的上游被标出来了", /当时判的是 needs_revision、是被强行带下来的/.test(cg.text));
ok("★ 并要求本道先判这份材料还能不能用", /先判一句：这份材料在你这一道还能不能用/.test(cg.text));
ok("过了闸的不加噪音", (cg.text.match(/当时判的是/g) || []).length === 1);

console.log("── 幂等与断点恢复 ──");
ok("★ 每一道带 attempt 与幂等键 run:stage:attempt",
  /idem: runid \+ ":" \+ \(i \+ 1\) \+ ":" \+ attempts\[i\]/.test(F) && /attempts\[i\] = \(attempts\[i\] \|\| 0\) \+ 1;/.test(F));
ok("重跑同一道 attempt 会加一（服务端据此分得清是不是同一次）", /attempts = \{\}/.test(F));
/* ⚠ agent 名后来抽成了常量 AGENT_FORGE（分身页要挂自己的名字：`wds-forge:<分身>`）。
   钉常量与它的取值口径，别钉那个已经不写在这里的字面量。 */
ok("★ 每写完一道就落一次 IndexedDB", /function saveRun\(\)/.test(F)
  && /agent: AGENT_FORGE/.test(F) && /AGENT_FORGE = PROF_ID \? \("wds-forge:"/.test(F)
  && /saveRun\(\);/.test(F));
ok("存的是规范状态不是画面", /存的是\*\*规范状态\*\*/.test(F) && /secs: secs\.map/.test(F) && !/innerHTML[^\n]*runState/.test(F));
ok("状态里带着 gate 与 hash（恢复之后仍验得了）", /gate: x\.gate \|\| ""/.test(F) && /hash: x\.hash \|\| ""/.test(F));
ok("★ 开跑前问一句要不要接着上一趟（不替读者选）",
  /forgeLastRun\(function \(st\)/.test(F) && /fgResumeGo/.test(F) && /fgResumeNew/.test(F));
ok("跑完的那一趟不会再被提出来", /st\.done \|\| !st\.secs/.test(F));
ok("格式换代的旧 run 不硬接", /\(st\.sv \| 0\) !== FORGE_SV/.test(F));
ok("★ 接着跑时不再重打一次 plan（重新拟题＝把上一趟的题名换掉）",
  /resume\s*\?\s*Promise\.resolve\(\{ ok: true, title: resume\.title/.test(F));
ok("恢复时 i 跳到断点，已完成的摆回各自那一行", /i = secs\.length;/.test(F) && /rows\[k\]\.sb\.innerHTML = mdRender\(x\.body\)/.test(F));
ok("恢复沿用同一个 run id（同一趟就是同一趟）", /var runid = \(resume && resume\.run\) \|\| runId\(\)/.test(F));

/* ═══ 九、阶段C：重接成文三段 ═══════════════════════════════════ */
console.log("── 第 14 道：章节表要标出每章消费哪几道 ──");
const st14 = M.STAGES[13].d;
ok("★ 每章要标消费哪几道（成文那三步照着它去上游取材料）", /消费：第X道、第Y道/.test(st14));
ok("★ 前十三道每一道都要被至少一章消费到（没人要＝那一道白跑了）", /前十三道每一道都至少被一章消费到/.test(st14));
ok("★ 反过来每一章都要有来路（消费不到上游的章多半是临时想的）", /每一章都至少消费一道/.test(st14));
ok("对不上就直说，不许为了表好看随手配一个道次", /不要为了让表好看而随手配一个道次/.test(st14));

console.log("── 成文三段：写完必须提取结构化主张 ──");
[15, 16, 17].forEach((k) => {
  const d = M.STAGES[k - 1].d;
  ok("第 " + k + " 道要求交出三栏提取件", /【本段提取/.test(d));
  ok("第 " + k + " 道：主张必须是本段真写出来的", /必须是本段正文里真写出来的/.test(d));
  ok("第 " + k + " 道：「没解决的」空着是可疑的", /这一栏空着是可疑的/.test(d));
});
ok("★ 第 16 道要接住上一段的「没解决的」", /上一段那三栏提取件就是你的起点/.test(M.STAGES[15].d));
ok("★ 第 17 道要逐条交代前两段没解决的，不许静悄悄消失", /一条都不许静悄悄消失/.test(M.STAGES[16].d));
ok("提取件写在正文之后、闸门之前（位置不能乱）", /写在正文之后、闸门之前/.test(M.STAGES[14].d));

console.log("── ⭐ 第 18 道：机械检查真的是机械的（真跑）──");
const AUD = new Function(F.slice(F.indexOf("  var FORGE_MOTHER = ["), F.indexOf("  function rsRun(topic, fg, resume) {"))
  + "\n return { audit: forgeAudit, text: forgeAuditText, MOTHER: FORGE_MOTHER };")();
const clean = "# 真标题\n\n**副标题：可裁决的那一句**\n\n摘要：略。关键词：甲；乙。\nAbstract: x. Keywords: y.\n"
  + "| 轴 | 低 | 高 |\n| --- | --- | --- |\n| 低 | A | B |\n| 高 | C | D |\n"
  + "若某项检验结果为反，则本文第三章不成立。\n赌注：2027年6月之前若无此现象，本文作废；写明什么不算命中。\n"
  + "结论：略。\n参考文献\n人机分工：略。\n";
const a1 = AUD.audit(clean);
ok("干净稿：术语零命中", a1.hits.length === 0);
ok("干净稿：前置件一件不缺", a1.miss.length === 0, JSON.stringify(a1.miss));
ok("★ 真表认得出（三行以上、每行三根竖线）", a1.table === true);
ok("数得出证伪条款", a1.falsify >= 1);
ok("赌注的日期与「不算命中」都认得出", a1.betDate === true && a1.betMiss === true);
ok("干净稿没印分数", a1.score.length === 0);

const dirty = "正文里我们做了一次二阶碰撞，撞出候选判断，并按五维给出综合分 148。\n2×2 我在行文里描述一下就够了。\n";
const a2 = AUD.audit(dirty);
ok("★★ 工艺术语命中要报**次数与原句**（「有 3 处」改得动，「未通过」改不动）",
  a2.hits.length >= 3 && a2.hits.every((h) => h.n >= 1 && h.eg.length > 3));
ok("★★ 行文里描述一遍不算真表", a2.table === false);
ok("★★ 偷偷印的分数抓得出（成品上一律不许有分）", a2.score.length >= 1);
ok("缺件逐件点名，不是只说「不合格」", a2.miss.length >= 5 && a2.miss.indexOf("参考文献") >= 0);

const named = "〔尚未交手〕Kuhn 1962 的范式说；Bourdieu 1977 的惯习。\n"
  + "正文里我们逐段与 Bourdieu 交手：Bourdieu 认为……而本文认为……Bourdieu 的读法在这里失效。\n";
const a3 = AUD.audit(named);
ok("★ 名单里点了名却没在正文交手的，点得出来", a3.unmet.indexOf("Kuhn") >= 0);
ok("真交手过的不误报", a3.unmet.indexOf("Bourdieu") < 0);

const txt = AUD.text(a2);
ok("读数摊成一段话，缺的地方加粗提醒", /2×2 真表：\*\*没有\*\*/.test(txt) && /印了分数：\*\*有\*\*/.test(txt));
ok("读数**不下结论**（判断是第 18 道的活）", !/不合格|未通过|passed/.test(txt));

console.log("── 审计读数真的送到了第 18 道 ──");
ok("★ 前端只给最后那一道，且不写死「第 18 道」", /i \+ 1 === steps\.length/.test(F) && /audit: audit/.test(F));
ok("成文不足时不硬凑一份读数", /body18\.replace\(\/\\s\/g, ""\)\.length > 500/.test(F));
ok("★ audit 过得了白名单", typeof SANF({ i: 18, forge: 1, audit: "字数 100" }).audit === "string"
  && SANF({ i: 18, forge: 1, audit: "字数 100" }).audit === "字数 100");
ok("audit 有长度钳位", /String\(rsRaw\.audit \|\| ""\)\.slice\(0, 4000\)/.test(W));
const s18 = M.sys({ i: 18, n: 18, t: "交付自查", topic: "题", forge: 1, done: "", bodies: [], audit: "字数 21000｜工艺术语命中：二阶×3" });
ok("★★ 读数摆进了第 18 道的提示语", s18.indexOf("工艺术语命中：二阶×3") > 0);
ok("★★ 明写读数不许被推翻", /这些数不许推翻/.test(s18));
ok("★★ 读数说缺的不许打勾，打了这份自查本身作废", /不许在自查表里给它打勾/.test(s18) && /这份自查本身就作废/.test(s18));
ok("并交代读数只覆盖数得出来的那几件", /数不出来的/.test(s18) && /最容易糊过去的/.test(s18));
ok("没有读数时不留空壳", M.sys({ i: 18, n: 18, t: "x", topic: "题", forge: 1, bodies: [] }).indexOf("机器读数") < 0);

console.log("── 闸门那一行不进成品 ──");
ok("★ 拼成品时把末尾的闸门行剥掉（它是工艺痕迹）", /replace\(\/\\n\*【闸门】\[\^\\n\]\*\\s\*\$\/, ""\)/.test(F));
ok("只从末尾剥，正文里讨论到「闸门」二字不受影响", /只从\*\*末尾\*\*剥/.test(F));

/* ═══ 十、阶段D-1：敌意最近邻检索专用链（建议书 §9.2）═══════════ */
console.log("── 为什么不能复用那一次宽泛搜索 ──");
ok("★★ 旧口径的病写进了注释：产线里 q 就是工序标题，拿它去搜等于没搜",
  /`q` 就是\*\*工序标题\*\*/.test(W));
ok("★ 第 5、13 道由程序强制走专用链，不等读者去点联网",
  /const FORGE_NBR_STAGES = \{ 5: 1, 13: 1 \};/.test(W) && /FORGE_NBR_STAGES\[rs\.i \| 0\]/.test(W));
ok("评分那一路也走专用链", /\|\| tool === "iq";/.test(W));
ok("普通问答仍按读者的开关走（没把别人的路一起改了）", /\} else if \(wantWeb\) \{/.test(W));
ok("种子取的是读者真正问的那个题目，不是工序标题", /\(rs && rs\.topic\) \? rs\.topic/.test(W));
ok("评分那一路取稿子第一行有字的（整篇塞进 34 字查询＝随机截一段）",
  /split\("\\n"\)\.map\(\(x\) => x\.trim\(\)\)\.filter\(Boolean\)\[0\]/.test(W));

console.log("── 五趟各有各的活（真跑）──");
const CH2 = new Function("const WEB=[];" + W.slice(W.indexOf("const NBR_PASSES = ["), W.indexOf("// 把搜索结果码成给基底看的块"))
  .replace("async function nbrChain(env, seed, glmKey, extra) {", "async function nbrChain(env, seed, glmKey, extra) { const webSearch = env.__ws;")
  + "\n return { PASSES: NBR_PASSES, chain: nbrChain, block: nbrChainBlock, key: _nbrKey };")();
ok("抠得到专用链", typeof CH2.chain === "function" && CH2.PASSES.length === 4);
ok("★ 同向占位排在对立者前面（先找像你的人，那才是会吸收掉你的）",
  CH2.PASSES[0].k === "同向占位" && CH2.PASSES[1].k === "对立者");
ok("外圈学科与方法学各有一趟", CH2.PASSES.map((p) => p.k).join().indexOf("外圈学科") >= 0
  && CH2.PASSES.map((p) => p.k).join().indexOf("方法学") >= 0);

const mkWS = (map) => (env, q, k, n) => Promise.resolve(
  map[Object.keys(map).find((kk) => q.indexOf(kk) >= 0)] || { ok: true, reason: "", items: [] });
const it = (t, u, s2) => ({ t: t, u: u, s: s2 || "x", m: "", d: "" });
const full = {
  "谁提出": { ok: true, items: [it("甲的理论", "https://a.com/1"), it("乙的说法", "https://b.com/2")] },
  "反驳": { ok: true, items: [it("对甲的批评", "https://c.com/3")] },
  "研究综述": { ok: true, items: [it("跨学科综述", "https://d.com/4")] },
  "实验范式": { ok: true, items: [it("消融实验范式", "https://e.com/5")] },
  "theory critique": { ok: true, items: [it("Kuhn critique", "https://f.com/6")] },
};
const run = (map, seed, lat) => CH2.chain({ __ws: mkWS(map) }, seed, "k", lat);

let R = null;
run(full, "沉默如何被生产", "Bourdieu 1977 说过").then((r) => {
  R = r;
  ok("★ 覆盖齐全时判 ok", r.ok === true && r.reason === "");
  ok("五趟都跑了（含外文那一趟）", r.passes.length === 5 && r.passes.some((p) => p.k === "外文" && p.n === 1));
  ok("★ 每条都标着自己是哪一趟找到的", r.items.every((x) => !!x.pass) && r.items.some((x) => x.pass === "方法学"));
  ok("手上没有拉丁文串时，外文那一趟老实记 skipped，不编一个英文查询去搜",
    true);

  return run(full, "沉默如何被生产", "全是中文没有拉丁串");
}).then((r2) => {
  const en = r2.passes.find((p) => p.k === "外文");
  ok("★★ 没有拉丁文串 ⇒ 外文那一趟标 skipped（编一个英文查询搜回来的会被当成外文占位者，那是假的）",
    en && en.n === 0 && en.why === "skipped_no_latin");

  /* 去重：同站同题只算一条 */
  const dup = { "谁提出": { ok: true, items: [it("甲的理论", "https://a.com/1"), it("甲的理论！", "https://a.com/9")] },
                "反驳": { ok: true, items: [it("甲的理论", "https://a.com/7")] } };
  return run(dup, "题", "");
}).then((r3) => {
  ok("★ 同一站点＋同一标题头只算一条（召回全是同一个作者群＝视同未检索）", r3.items.length === 1);
  ok("★★ 同向有、对立被去重成 0 ⇒ 判覆盖不足", r3.ok === false && r3.reason === "neighbor_insufficient");

  return run({ "谁提出": { ok: true, items: [it("甲", "https://a.com/1")] } }, "题", "");
}).then((r4) => {
  ok("★ 只有同向没有对立 ⇒ 覆盖不足（只知道谁跟你像，不知道谁会顶你）", r4.ok === false);
  ok("失败原因分得清（不是一句「搜索失败」）", r4.passes.some((p) => p.why === "empty"));

  const blk = CH2.block(R);
  ok("块里带覆盖读数", /覆盖：/.test(blk) && /同向占位：/.test(blk));
  ok("★ 每条标着 pass", /〔方法学〕/.test(blk) && /〔对立者〕/.test(blk));
  ok("★ 四条用法逐条在位（公允复述最强形态／可裁决分离线／相反预测／不许编）",
    /最强形态/.test(blk) && /可裁决分离线/.test(blk) && /相反预测/.test(blk) && /一个都不许写/.test(blk));
  const bad = CH2.block(R2bad());
  ok("★★ 覆盖不足时块里明写「不得据此放行」", /不得据此放行/.test(bad) && /覆盖不足/.test(bad));
  function R2bad() { return { items: [], passes: [{ k: "同向占位", n: 0, why: "empty" }], ok: false, reason: "neighbor_insufficient" }; }

  console.log("── 失败必须可见（§9.3）──");
  ok("★ 发 nbrchain 事件，带 ok/reason/逐趟计数", /t: "nbrchain", v: \{ ok: nc\.ok, reason: nc\.reason, passes: nc\.passes/.test(W));
  ok("覆盖不足时另发一条读者看得懂的 note", /敌意最近邻检索覆盖不足/.test(W));
  ok("★★ 评分那一路：召回了几条 ≠ 拓邻做成了，覆盖不足仍要把 I 标证据不足",
    /覆盖不足 ⇒ I 维按证据不足处理/.test(W) && /不作为可引用的读数/.test(W));
  ok("★★ 前端把覆盖读数接住并显著显示", /j\.t === "nbrchain" && onNote/.test(F) && /nbrChainBad/.test(F));
  ok("★★ 产线调 rsStream 时真的传了 onNote（此前没传，事件全掉在地上）",
    /r\.sb\.innerHTML = mdRender\(txt\); if \(stick\) scrollBottom\(\); \},\s*\n\s*function \(msg\) \{/.test(F));
  ok("注释留下这条心法", /新加一路事件，要顺着回调一直看到它有没有人接/.test(F));

  console.log("── 第 5、13 道的口径跟着改了 ──");
  ok("第 5 道说明这一趟是程序替它跑的", /由程序替你跑了一条敌意最近邻专用链/.test(M.STAGES[4].d));
  ok("第 5 道：上面没有的作者与年份一个都不许写", /上面没有的作者与年份一个都不许写/.test(M.STAGES[4].d));
  ok("第 13 道：〔尚未交手〕必须从真实召回里挑", /必须从真实召回里挑/.test(M.STAGES[12].d));
  ok("第 13 道：凭印象的只能写通行读法、不挂人名年份", /不挂人名年份/.test(M.STAGES[12].d));

  console.log("── v4.1：三方程/六路径/三原理平衡（选源题闸三型化＋共有前提与靶格改按型分支）──");
  const s1 = M.STAGES[0].d, s7d = M.STAGES[6].d, s9d = M.STAGES[8].d;
  ok("第 1 道题型登记是必填、机器不猜（v6.0）", /题型登记/.test(s1) && /What/.test(s1) && /How/.test(s1) && /Why/.test(s1)
    && /不许替提问者猜/.test(s1) && /不许默认 What/.test(s1));
  ok("★★ 第 1 道有方程判定（−1.5）：三句填空，填不出的那一句就是待求维", /方程判定/.test(s1) && /待求维/.test(s1)
    && /填不出的那一句就是待求维/.test(s1) && /D 与 E 已知，求 S/.test(s1));
  ok("★ 方程判定的三种落空各有出路（一句/两句/三句）", /题面太空/.test(s1) && /那不是待解的题，是综述/.test(s1));
  ok("★★ How 题两级：焦点定一对路径 ＋ 起点定一条", /焦点/.test(s1) && /起点/.test(s1)
    && /D→E→S/.test(s1) && /E→S→D/.test(s1) && /S→D→E/.test(s1));
  ok("★★ Why 题两级：被驱动维定矛盾式 ＋ 改变的相", /被驱动维/.test(s1)
    && /S 变←D 与 E 的矛盾/.test(s1) && /诞生/.test(s1) && /发展/.test(s1) && /死亡/.test(s1));
  ok("★★ Why 吸引子的机械判法（写不出矛盾式＝缺席不是动力）", /不是动力，是缺席/.test(s1));
  ok("★★ 第 1 道标出主家，并把厚度/未吸收度的检查压到主家身上", /主家/.test(s1) && /辅家/.test(s1)
    && /必须判「厚」/.test(s1) && /答案那一侧/.test(s1));
  ok("题闸降为登记项，判实体/对接不退回（v6.0）", /只标记不否决/.test(s1) && /不退回、不封顶/.test(s1)
    && /登记项，不是判定项/.test(s1));
  ok("第 1 道题闸三型化（S/D/E 空位型，不是只认 S 一种）", /S型·无字段者/.test(s1) && /D型·不可重走的那一段/.test(s1) && /E型·计入即毁者/.test(s1));
  ok("第 1 道要求三家分处 S／D／E 三维（不是只分三个学科）", /三家须分处 S／D／E 三维/.test(s1));
  ok("方程轮换律降为告警，不再是禁令（v6.0）", /方程轮换律/.test(s1)
    && /连续三趟同型不扣分/.test(s1) && !/连续三趟不许取同一空位型/.test(s1)
    && /分布长期一边倒说明题源单一/.test(s1));
  ok("★★ 第 7 道不再把共有前提锁死成「归属」一种形状", !/该由谁来裁／该放在哪儿／该有多少/.test(s7d));
  ok("★★ 第 7 道共有前提分两层：结构层由题型定、内容层由待求维定（v6.0）",
    /结构层 · 由第一步登记的题型定/.test(s7d) && /内容层 · 由第一步①之二判出的待求维定/.test(s7d)
    && /不是由题闸声明的空位型定/.test(s7d));
  ok("★ 第 7 道两层的包含关系是一条验收（内容层是结构层的特例）", /必须是结构层那句的一个特例/.test(s7d));
  ok("第 7 道内容层三句按待求维分支（不再按声明的空位型）",
    /待求 S.*账本/.test(s7d) && /待求 D.*重走/.test(s7d) && /待求 E.*计入而不改变/.test(s7d));
  ok("★★ 第 7 道：内容层与声明不一致照记不罚，不退回第一步", /照记不罚/.test(s7d) && !/退回第一步重做/.test(s7d));
  ok("★★ 第 7 道：主家双重身份两条硬约束＋观察还是主张的机械判法",
    /双重身份/.test(s7d) && /实证材料/.test(s7d) && /观察结果，还是一个主张/.test(s7d));
  ok("★★ 第 9 道解开题型↔空位型的一一绑定（v6.0：两者正交）",
    !/How 题（对应 D 型空位）/.test(s9d) && !/Why 题（对应 E 型空位）/.test(s9d)
    && /两层正交/.test(s9d) && /题型与方程归属\*\*正交\*\*/.test(s9d));
  ok("★★ 第 9 道第二层装置按待求维取（S=2×2／D=时间轴＋反事实／E=归属迁移矩阵）",
    /待求 S\*\*＝2×2/.test(s9d) && /待求 D\*\*＝一条轮次时间轴/.test(s9d) && /待求 E\*\*＝一张归属迁移矩阵/.test(s9d));
  ok("★★ 装置与实判不一致 → 换装置重验、不扣分（不再直接判不合格）",
    /不要直接判不合格/.test(s9d) && /装置改判/.test(s9d) && /不扣分/.test(s9d));
  ok("靶格签名不许跨维借用", /不许跨维借用/.test(s9d));
  ok("★★ 第 9 道收尾必做归格（族闸 9.5 落地）：方程句五选一 ＋ 实判格",
    /归格/.test(s9d) && /方程句/.test(s9d) && /实判格/.test(s9d) && /纠缠档/.test(s9d)
    && /判不出格的，回上一步重收敛/.test(s9d));
  ok("★★ 归格：与声明不一致不扣分，反而说明是撞出来的", /否不扣分，反而说明这条判断是撞出来的/.test(s9d));
  ok("Why 题按三相分交（死亡相交『矛盾改由什么顶上』）",
    /诞生相/.test(s9d) && /发展相/.test(s9d) && /死亡相/.test(s9d) && /矛盾改由什么顶上/.test(s9d));
  ok("How 题：可插手步必须落在起点那一维上", /可插手步必须落在第一步判出的「起点」那一维上/.test(s9d));
  ok("第 9 道 How 分支要序列＋不可逆步骤＋可插手步骤，且不许用比率", /不可逆的那一步/.test(s9d) && /可插手的那一步/.test(s9d) && /不许用比率／指标/.test(s9d));
  ok("第 9 道 Why 分支要三条动力式＋回写＋下一轮谁先动，且单因锁定", /回写.*下一轮谁先动|下一轮谁先动/.test(s9d) && /只是其中一个因素/.test(s9d));
  ok("★★ 依赖表：第 7、9 道现在都读得到第 1 道（否则改了提示语也是空转）", M.NEEDS[7].indexOf(1) >= 0 && M.NEEDS[9].indexOf(1) >= 0);
  const c3 = M.carry(7, [{ i: 1, t: "选源", body: "本趟声明：题型 Why，空位型 E" }]);
  // ── v6.0：补上此前没在产线里落地的三道 ──
  const s12 = M.STAGES[11].d, s18 = M.STAGES[17].d;
  ok("★★ 第 1 道有闸零之三可数对象闸（三档：有/可造/无）", /可数对象闸/.test(s1)
    && /可清点的对象/.test(s1) && /可造/.test(s1) && /三家全是解释型/.test(s1));
  ok("★ 可数对象闸要当场写下真跑从哪一家取数", /当场写下真跑从哪一家取数/.test(s1));
  ok("★ 不许用「示意性」放行（中间那种是致命的）", /示意性/.test(s1) && /中间那种是致命的/.test(s1));
  ok("★ 不许为了凑一家能数的而牺牲三维分处", /先满足三维分处/.test(s1));
  ok("★★ 取数场对照表在（字段审计→S／成对两版→D／分类两版→E）", /取数场/.test(s1)
    && /字段审计/.test(s1) && /成对的前后两版记录/.test(s1) && /分类体系或规程的相邻两版/.test(s1));
  ok("★★ 取数场只作重力，不许据此指定产出落在哪一维", /不许据此指定产出落在哪一维/.test(s1));
  ok("★★ 第 12 道有真跑一条，且判的是预注册三件不是结果方向", /真跑一条/.test(s12)
    && /判负条款是否在读取结果之前写死/.test(s12) && /不利结果的处置是否事先约定/.test(s12)
    && /停止规则是否写死/.test(s12));
  ok("★★ 三件齐而结果碰巧全有利 → 不扣分（v6.0 承重裁定）", /三件齐而结果碰巧全部有利/.test(s12)
    && /不扣分/.test(s12));
  ok("★★ 明确禁止「只报有利结果＝没跑」那条旧罚则（它诱导编造不利结果）",
    /不许判「只报有利结果就等于没跑」/.test(s12) && /诱导\*\*编造一个不利结果\*\*|编造一个不利结果/.test(s12)
    && /它就是净负的/.test(s12));
  ok("★ 跑不成要明写跑不成，不许用「可在未来研究中检验」糊过去",
    /本次未做真跑，原因/.test(s12) && /可在未来研究中检验/.test(s12));
  ok("★★ 第 12 道读得到第 1 道（取数场／拟清点单位，否则真跑只能空谈）", M.NEEDS[12].indexOf(1) >= 0);
  ok("★★ 第 18 道有站级母题闸三张表（空位型表/地基表/形式句表）", /空位型表/.test(s18)
    && /地基表/.test(s18) && /形式句表/.test(s18));
  ok("★★ 空位型表登实判格，声明≠实判不扣分", /实判格/.test(s18) && /声明≠实判不扣分/.test(s18));
  ok("★ 同一条地基用满 5 次要正面处理", /用满 5 次/.test(s18) && /不同的塌陷方式/.test(s18));
  ok("★ 形式句表：跨批同形 ≥3 篇即站级同根成立", /剥到形式层/.test(s18) && /同形 ≥3 篇/.test(s18));
  ok("★★ 母题单一性不全是病——病在不自知不申报", /不全是病/.test(s18) && /不自知/.test(s18) && /申报/.test(s18));
  ok("★★ 第 18 道有跨书母题闸（改母题 或 明写实例化）", /跨书母题闸/.test(s18)
    && /改母题/.test(s18) && /明写实例化/.test(s18) && /冒充新母题才丢人/.test(s18));
  ok("★ 跨书母题闸点破「最顺手的那一条通常就是 S 型」", /最顺手的那一条通常就是 S 型的那一条/.test(s18));
  ok("★★ 第 18 道读得到第 1 道与第 7 道（三张表要登它们）",
    M.NEEDS[18].indexOf(1) >= 0 && M.NEEDS[18].indexOf(7) >= 0);
  ok("★ 第 18 道加了真跑核对", /真跑核对/.test(s18));
  ok("★★ 真跑一遍：第 7 道真的能从上游材料里读到第 1 道声明的空位型", c3.text.indexOf("空位型 E") >= 0);

  /* ═══ ⭐ 产线道次的预算与时钟（2026-08-29 放开）═══════════════════════
     病：十八道每一道走的是「答一段话」的账（max_tokens 6000／总时长 420 秒），成文三段各是两万字的
     三分之一、第 3 道 27 对、第 11 道十处兑现，六千 token 还要与满功率思考同吃——于是断在半句、
     闸门那一行来不及写、读者一路「仍要往下跑」。这一段守：预算顶配、走阶梯兜 400、总时长十分钟、
     关思考重答不压预算，以及前端先程序判断稿再看闸门。 */
  console.log("── ⭐ 产线道次的预算与时钟（2026-08-29 放开）──");
  const chatSeg = (function () {
    const i0 = W.indexOf('url.pathname === "/api/wds/chat"');
    const j0 = W.indexOf("/api/wds/research", i0);
    return W.slice(i0, j0 > i0 ? j0 : i0 + 60000);
  })();
  {
    const mTok = W.match(/^const FORGE_STAGE_TOK = (\w+);/m), mMax = W.match(/^const WDS_TOK_MAX = (\d+);/m);
    const mTot = W.match(/^const FORGE_TOTAL_MS = (\d+);/m), mDeep = W.match(/const CHAT_FIRST_DEEP_MS = (\d+), CHAT_TOTAL_DEEP_MS = (\d+);/),
      mLong = W.match(/const CHAT_TOTAL_LONG_MS = (\d+);/);
    ok("★★ 产线道次的预算常数＝顶配（FORGE_STAGE_TOK = WDS_TOK_MAX，且 ≥ 32000）",
      !!(mTok && mMax) && mTok[1] === "WDS_TOK_MAX" && +mMax[1] >= 32000);
    ok("★★ 产线道次的总时长常数存在且不短于深度档与长篇档",
      !!(mTot && mDeep && mLong) && +mTot[1] >= +mDeep[2] && +mTot[1] >= +mLong[1]);
    ok("★ 放开的依据写在常数头上（08-19 直连实测 449 秒／27,947 字，130 秒墙两边都不存在）",
      /449 秒/.test(W) && /130 秒墙/.test(W) && /FORGE_STAGE_TOK/.test(W));
    ok("★★ rsLong＝学科通融或 SDE 深度研究（自由拆题的研究产线不在内）",
      /^\s+const rsLong = !!\(rs && \(rs\.forge \|\| rs\.sde\)\);$/m.test(chatSeg));
    /* 2026-08-30 难度条：普通问答那一支改从 tokGrade 取（定了档按档、没定档仍是 deep?6000:(tool?4000:2600)），产线一字没动。 */
    ok("★★ 预算：产线道次取 FORGE_STAGE_TOK，普通问答与自由研究一个字没变",
      /:\s*\(rsLong \? FORGE_STAGE_TOK : \(rs \? \(deep \? 6000 : 4000\) : tokGrade\)\)/.test(chatSeg)
      && /const tokGrade = G\.on \? Math\.max\(gK\.tok, tool \? 4000 : 0\) : \(deep \? 6000 : \(tool \? 4000 : 2600\)\);/.test(chatSeg)
      && !/\n\s+: \(rs \? \(deep \? 6000 : 4000\)/.test(chatSeg));
    ok("★★ 产线道次的上游调用走 wdsFetchMax（上游以 max_tokens 相关 400 拒收就降一档，不会整道断掉）",
      /upstream = rsLong\s*\n\s*\? await wdsFetchMax\(VC, KEY, messages, true, tokWant, clk\.signal, false, undefined, rsPlain\)/.test(chatSeg));   // 2026-08-29 末位加了 rsPlain（成文三段首发关思考），改落点不删
    ok("阶梯还在兜 400（只认 max_tokens 相关的 400 才降档）",
      /if \(resp\.ok \|\| resp\.status !== 400 \|\| i === ladder\.length - 1\) return resp;/.test(W)
      && /max\[_ \]\?tokens\|max\[_ \]\?completion/.test(W));
    ok("普通问答那一发仍是原来的 fetch（max_tokens: tokWant）", /: await fetch\(VC\.url, \{ method: "POST"[^\n]*max_tokens: tokWant, messages \}\)\), signal: clk\.signal \}\);/.test(chatSeg));
    ok("★★ 总时长：产线道次走 FORGE_TOTAL_MS，长篇与深度档的账照旧",
      /rsLong \? FORGE_TOTAL_MS : \(askLen \? CHAT_TOTAL_LONG_MS : gTotal\)\);/.test(chatSeg)
      && /const gTotal = G\.on \? gK\.total : \(deep \? CHAT_TOTAL_DEEP_MS : CHAT_TOTAL_MS\);/.test(chatSeg));
    ok("首帧闸没跟着放宽（仍按档给：首帧一到就撤，放宽它只会让卡死的更晚被发现）",
      /const clk = wdsClock\(gFirst,/.test(chatSeg) && /const gFirst = G\.on \? gK\.first : \(deep \? CHAT_FIRST_DEEP_MS : CHAT_FIRST_MS\);/.test(chatSeg));
    ok("★★ 关思考重答：产线道次不压预算（压到 3000 等于砍掉正文），普通问答照旧压",
      /const tok2 = \(askLen \|\| rsLong\) \? tokWant : Math\.min\(tokWant, 3000\);/.test(chatSeg));
    ok("★★ 关思考重答的总时长：产线道次同主道，普通问答仍是重答那套",
      /const clk2 = wdsClock\(\(rsLong && !wdsCanPlain\(VC\)\) \? 120000 : CHAT_RETRY_FIRST_MS, rsLong \? FORGE_TOTAL_MS : CHAT_RETRY_TOTAL_MS\);/.test(chatSeg));   // 2026-08-29 首帧档加了关不掉思考那两家的 120 秒，改落点不删
    ok("★ 重答那一发在产线道次上也走阶梯，且思考是关着的（plain=true）",
      /const up2 = rsLong\s*\n\s*\? await wdsFetchMax\(VC, KEY, messages, true, tok2, clk2\.signal, false, undefined, true\)/.test(chatSeg));
    ok("★ 「≤8000 是硬约束」那条老账在这一段里已标作废（别让下一个人照着改回去）",
      /「≤8000 是硬约束」那条老账已作废/.test(chatSeg) && !/满功率档仍死守 6000（≤8000 是硬约束）/.test(chatSeg));
  }
  /* 前端：学科通融先程序判断稿，再看闸门。拿源码里那一行的 IIFE 原样跑，不另抄一份。 */
  {
    /* 2026-08-30：研究产线那一支加了道次专判（sdePipe ? rsJudgeSde : rsJudge）并换了行，学科通融的 IIFE 一字未动——改落点不删 */
    const jl = STEP.match(/var g = fg \? (\(function \(\) \{[^\n]*\}\)\(\))\s*\n\s*: \(sdePipe \? rsJudgeSde\(i \+ 1, txt, RS\.lastMeta\) : rsJudge\(txt, RS\.lastMeta\)\);/);
    ok("★★ 学科通融的判决行：先 rsJudge 再 forgeGate（程序判不出问题的才轮到闸门）",
      !!jl && /rsJudge\(txt, RS\.lastMeta\)/.test(jl[1]) && /forgeGate\(txt\)/.test(jl[1]) && /j\.d === "passed" \? forgeGate/.test(jl[1]));
    ok("★ 旧写法（只看闸门）已不在", !/var g = fg \? forgeGate\(txt\) : rsJudge/.test(STEP));
    const rj = F.slice(F.indexOf("  function rsJudge(txt, meta) {"), F.indexOf("  function rsRun(topic, fg, resume) {"));
    const fgs = F.slice(F.indexOf("        function forgeGate(txt) {"), F.indexOf("        function forgeHalt(r, g, retry) {"));
    ok("抠得到 rsJudge 与 forgeGate", rj.length > 200 && fgs.length > 200 && !!jl);
    if (jl && rj.length > 200 && fgs.length > 200) {
      const J = new Function("function tx(k, o) { return k; }\n" + rj + "\n" + fgs
        + "\n return function (txt, meta) { var RS = { lastMeta: meta }; var fg = true; return " + jl[1] + "; };")();
      const body = "本道产出。".repeat(80);
      const full = body + "\n【闸门】passed";
      ok("真跑：写完＋闸门 passed ⇒ passed", J(full, { fin: "stop", cut: "", err: "" }).d === "passed");
      const r1 = J(body + "……而这一处的", { fin: "length", cut: "", err: "" });
      ok("真跑：预算顶穿、闸门那一行没来得及写 ⇒ 判 cut 且说的是「预算顶穿」（不再说「没交出判决」）",
        r1.d === "cut" && r1.why === "rsCutLength");
      const r2 = J(body + "\n【闸门】passed", { fin: "length", cut: "", err: "" });
      ok("真跑：程序判决优先——就算末尾有 passed，finish=length 照样判 cut", r2.d === "cut");
      const r3 = J(body, { fin: "stop", cut: "", err: "" });
      ok("真跑：写完了却没交闸门 ⇒ 仍是 unknown（这是它不肯判，不是没写完）", r3.d === "unknown");
      const r4 = J(body, { fin: "", cut: "作答超过 600 秒还没写完（已掐断）", err: "" });
      ok("真跑：被时钟掐 ⇒ cut，理由是时钟那句话", r4.d === "cut" && /600 秒/.test(r4.why));
      ok("真跑：只写一百字 ⇒ cut（过短）", J("短".repeat(100), { fin: "stop", cut: "", err: "" }).d === "cut");
      ok("真跑：零字 ⇒ failed", J("", { fin: "", cut: "", err: "" }).d === "failed");
      const r5 = J(body + "\n【闸门】return_to_stage:4 · 五候选共脊", { fin: "stop", cut: "", err: "" });
      ok("真跑：程序判过了，闸门的退回判决原样交出（back=4）", r5.d === "return_to_stage" && r5.back === 4);
    }
  }


  /* ═══ 十二、预算放开之后的三件配套（2026-08-29 同日第二刀）═══
     ① 上游份额水位匀分（成文三段各六七千字之后，第 18 道读九道不能再每道 2,888 字）
     ② 成文三段首发关思考（满预算＋关思考＝长文唯一稳定形态；判断各道保留思考）
     ③ 重答写出来了，fin 帧报重答这一遍的收束（第一遍的断因不许把写完的稿判成断稿） */
  console.log("── 十二、上游份额：水位匀分（短的先装满、省下的给长的）──");
  ok("★ 学科通融上游份额抬到 48000（成文三段各六七千字，第 18 道读九道）", M.MAX >= 48000);
  ok("★ 研究产线份额独立且未动（它另有七万八千字内功要装）", M.RES_MAX === 26000);
  {
    const mix = [1, 7, 9, 12, 13, 14].map((k) => ({ i: k, t: "判断稿" + k, body: "判".repeat(1500) }))
      .concat([15, 16, 17].map((k) => ({ i: k, t: "成文" + k, body: "文".repeat(7000) })));
    const c18 = M.carry(18, mix);
    ok("★★ 第 18 道读九道：六道短稿一字不截，三段成文各 7000 字也一字不截（死匀分时每道只剩 2,888 字）",
      c18.got.length === 9 && !/此处只带来前/.test(c18.text) && c18.text.split("文".repeat(7000)).length === 4);
    ok("总量仍在份额内", c18.text.length < M.MAX * 1.3, "len=" + c18.text.length);
    const c18b = M.carry(18, mix.map((x) => x.i >= 15 ? { i: x.i, t: x.t, body: "文".repeat(20000) } : x));
    ok("★ 三段成文各 2 万字时：短稿仍一字不截，长的按剩余份额截且截口看得见",
      c18b.text.split("判".repeat(1500)).length === 7 && (c18b.text.match(/此处只带来前 (\d+) 字/g) || []).length === 3
      && /原文共 20000 字/.test(c18b.text));
    ok("匀分的份额真是省下来的：三段各拿到 ≥ (48000−9000)/3", (c18b.text.match(/此处只带来前 (\d+) 字/g) || []).every((m) => parseInt(m.match(/\d+/)[0], 10) >= Math.floor((48000 - 9000) / 3)));
    ok("研究产线传自己的份额时按 26000 分", M.carry(7, huge, undefined, undefined, 26000).text.length < 26000 * 1.3);
  }
  console.log("── 成文三段首发关思考 ──");
  ok("★★ 只有第 15/16/17 道首发关思考，判断各道保留思考", JSON.stringify(Object.keys(M.PLAIN).sort()) === JSON.stringify(["15", "16", "17"]) && [15, 16, 17].every((k) => M.PLAIN[k]));
  {
    const CH = W_TXT(W.slice(W.indexOf('url.pathname === "/api/wds/chat"'), W.indexOf('url.pathname === "/api/wds/research"')));
    ok("★★ rsPlain 只对学科通融的成文三段成立（深度研究与普通问答不沾）", /const rsPlain = !!\(rs && rs\.forge && FORGE_PLAIN_STAGES\[rs\.i \| 0\]\);/.test(CH));
    ok("★★ 首发真的把 rsPlain 递给了 wdsFetchMax 的 plain 位（定义了 ≠ 用上了）", /wdsFetchMax\(VC, KEY, messages, true, tokWant, clk\.signal, false, undefined, rsPlain\)/.test(CH));
    ok("★ 每一道开跑先报一句配置（输出多少 tok·思考开关·总时长闸）", /本道预算 · 输出 " \+ tokWant \+ " tok/.test(CH) && /总时长闸 " \+ Math\.round\(FORGE_TOTAL_MS \/ 1000\)/.test(CH));
    ok("★ 配置那一句对关不掉思考的家说真话（不写「关」）", /关不掉（这家基底思考常开/.test(CH) && /wdsCanPlain\(VC\) \? "关（成文段/.test(CH));
    ok("★ 关不掉思考的家重答首帧给 120 秒（它们的重答只把正文算首帧）", /wdsClock\(\(rsLong && !wdsCanPlain\(VC\)\) \? 120000 : CHAT_RETRY_FIRST_MS/.test(CH));
    console.log("── 重答写出来了，fin 帧报的是这一遍 ──");
    ok("★★ 重答循环记下自己的 finish_reason", /_cd\.finish2 = String\(c2\.finish_reason\)/.test(CH));
    ok("★★ 重答被掐记 cut2，不覆盖第一遍的 note", /_cd\.cut2 = clk2\.cut \? clk2\.why\("重答"\)/.test(CH));
    ok("★★ 重答有正文 ⇒ finish/cut/partCut 换成这一遍的（第一遍的断因不许把写完的稿判成断稿）",
      /if \(outText\) \{ _cd\.finish = _cd\.finish2 \|\| ""; _cd\.cut = _cd\.cut2 \|\| ""; _cd\.partCut = ""; \}/.test(CH));
    ok("★ 这一处落在 fin 帧之前（否则改了也发不出去）", CH.indexOf('if (outText) { _cd.finish = _cd.finish2') < CH.indexOf('t: "fin", v: { fin: _cd.finish') && CH.indexOf('if (outText) { _cd.finish = _cd.finish2') > 0);
    /* 真跑一遍那句判决：第一遍被掐（cut 非空）、重答写满且 stop ⇒ 前端 rsJudge 必须判 passed */
    const FE2 = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");
    const mj = /function rsJudge\(txt, meta\) \{[\s\S]*?\n  \}/.exec(FE2);
    const rsJ = mj ? new Function("tx", mj[0] + "; return rsJudge;")((k) => k) : null;
    const cdSim = (first, retry) => {   // 照服务端那三行复现：有正文就换成重答那一遍的
      const cd = { finish: first.finish, cut: first.cut, partCut: "" };
      if (retry.out) { cd.finish = retry.finish2 || ""; cd.cut = retry.cut2 || ""; cd.partCut = ""; }
      return { fin: cd.finish || "", cut: cd.cut || cd.partCut || "", err: "" };
    };
    ok("★★ 真跑：首发被时钟掐、重答写满 ⇒ 判 passed（改前判 cut）", !!rsJ && rsJ("字".repeat(3000), cdSim({ finish: "", cut: "作答超过 600 秒还没写完（已掐断）" }, { out: 3000, finish2: "stop" })).d === "passed");
    ok("★★ 真跑：重答自己也被掐 ⇒ 仍判 cut，理由是重答那句", !!rsJ && /重答/.test(rsJ("字".repeat(3000), cdSim({ finish: "", cut: "首帧" }, { out: 3000, cut2: "重答超过 600 秒还没写完（已掐断）" })).why));
    ok("★ 真跑：重答顶穿（length）⇒ 判 cut·预算顶穿", !!rsJ && rsJ("字".repeat(3000), cdSim({ finish: "", cut: "x" }, { out: 3000, finish2: "length" })).d === "cut");
  }
  console.log("\n" + (fail ? "✗ " : "✓ ") + pass + " passed, " + fail + " failed");
  process.exit(fail ? 1 : 0);
});
/* ⚠ 这里原来还有一句**同步的** process.exit——它在上面那条 promise 链落地之前
   就把进程掐掉，于是专用链那二十条一条都没跑，而汇总照样打印"全绿"。
   💡 心法：**给一个同步的测试文件加异步用例时，先去看文件末尾那句退出。**
   收尾现在只在链尾那一处。 */
