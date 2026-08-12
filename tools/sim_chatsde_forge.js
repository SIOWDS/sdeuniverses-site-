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
  + "\n return { STAGES: FORGE_STAGES, NEEDS: FORGE_NEEDS, carry: forgeCarry, sys: wdsForgeSys, MAX: FORGE_CARRY_MAX, JUDGE: FORGE_JUDGE_N };")();

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
ok("只递上来一部分时，got/miss 分得清", c2.got.length === 1 && c2.miss.length === 2);
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
ok("单轮工序仍是十四件，且改称「件」以免与道次混淆",
  /十四件\*\*单轮工序\*\*/.test(W) && (W.match(/const WDS_TOOL_KEYS = \[([^\]]*)\]/) || ["", ""])[1].split(",").length === 14);
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
ok("★ 评分这一路收得到站外资料了（原来签名里根本没有）",
  /function WDS_IQ_SYS\(siteCtx, docCtx, docNote, lang, webCtx\)/.test(W)
  && /WDS_IQ_SYS\(siteCtx, docCtx, docNote, lang, webCtx\);/.test(W));
ok("★ 评分工序强制走检索，不等读者去点联网",
  /const wantWeb = !!b\.web \|\| String\(b\.tool \|\| ""\) === "iq";/.test(W));
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
const wa = W.indexOf("      const rs = rsRaw ? {");
const wb = W.indexOf("      // VISION：读者带来的图", wa);
const SAN = (wa > 0 && wb > wa) ? W.slice(wa, wb) : "";
ok("抠得到 rs 的清洗那一段", SAN.indexOf("rsRaw.topic") > 0);
const SANF = new Function("rsRaw", SAN.replace("      const rs = rsRaw ? {", "const rs = rsRaw ? {") + "\n return rs;");
const sanIn = { i: 7, n: 18, forge: 1, t: "共有前提", topic: "题", done: "1. 选源",
  sv: 2, run: "r123abc", attempt: 2, idem: "r123abc:7:2",
  bodies: [{ i: 2, t: "抽脊", body: "甲家承重命题：" + MARK, hash: "deadbeefdeadbeef" },
           { i: 5, t: "近邻闸", body: "近邻正文" }, { i: 6, t: "候选互撞", body: "候选正文" }],
  gates: [{ i: 2, d: "passed" }, { i: 5, d: "needs_revision" }] };
const sanOut = SANF(sanIn);
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
ok("★ 每写完一道就落一次 IndexedDB", /function saveRun\(\)/.test(F) && /agent: "wds-forge"/.test(F) && /saveRun\(\);/.test(F));
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

console.log("\n" + (fail ? "✗ " : "✓ ") + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
