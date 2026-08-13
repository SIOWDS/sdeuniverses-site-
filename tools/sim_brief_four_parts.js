/* 只测一件事：站内搜索页「提炼精华」的**先思考 ＋ 两段一万字入口资料**。
   口径变过两次：一段三千字 → 四段两万字（线上真跑：最后一段写不完）→ 现在的规划段＋两段。

   为什么单独立一个脚本：入口资料是整条产线的枢纽——论文水平主要由它决定。
   它一旦短了或缺了栏，坏处不会当场显形，而是在两万字论文里以「基底自己现编」的形式出现。
   这里盯四种静默死法：
   ① 后端 part 被钳成 1|2 —— 第三、四段被当成第一段重写一遍（旧版真有这个 bug，四段成文那一轮没测到）；
   ② 九栏的栏名/栏号被改 —— 下游成文按栏名发指令、思想库存按栏名取料，改名即全线取空；
   ③ 某一段没写出来却照打「✓ 已就绪」—— 论文照着一份缺栏的清单去写，缺口原样继承；
   ④ 段收尾标记没剥净 —— 原样印进入口资料，再被成文当正文吃进去。
   前端部分把 paperHalf/runParts 从页面里抠出来真跑，后端部分对 worker.js 的提示语构造做断言。 */
"use strict";
const fs = require("fs");
const SRC = "/home/claude/site/public/search/index.html";
const WRK = "/home/claude/site/src/worker.js";
const h = fs.readFileSync(SRC, "utf8");
const w = fs.readFileSync(WRK, "utf8");

let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };

/* ===== 抠出 paperHalf + 四段流水，打桩真跑 ===== */
const a = h.indexOf("function paperHalf(");
const b = h.indexOf("function doPaper(");
if (a < 0 || b <= a) { console.log("FAIL 抠不出 paperHalf/runParts（锚点变了，先改本脚本）"); process.exit(1); }
const seg = h.slice(a, b);

let calls = [], plan = [], seeds = [];
function makeRunner() {
  calls = []; seeds = [];
  const stub = { getElementById: () => ({ set textContent(v) { }, classList: { add() { }, remove() { } }, style: {} }) };
  const streamPaper = function (part, extra) {
    const step = plan[calls.length] || { text: "" };
    calls.push(part); seeds.push(extra);
    return step.err ? Promise.reject(new Error(step.err)) : Promise.resolve(step.text);
  };
  const fn = new Function("document", "streamPaper", "GEN_STAT", "setProg",
    "var GEN_PREV='', GEN_BOX='';\n" + seg +
    "\nreturn { runParts: runParts, runFourParts: runFourParts, missText: missText, paperHalf: paperHalf, BRIEF_PARTS: BRIEF_PARTS, PAPER_PARTS: PAPER_PARTS, getPrev: function(){ return GEN_PREV; } };");
  return fn(stub, streamPaper, "briefStat", function () { });
}
const seedFor = (i, head, tail) => ({ gmode: "distill", head: i > 0 ? head : undefined, tail: i > 0 ? tail : undefined });
const stat = { set textContent(v) { } };
const LONG = (n) => "字".repeat(n);
const reset = (p) => { plan = p; calls = []; seeds = []; };

(async () => {
  const R = makeRunner();

  console.log("— 一、四段规格 —");
  ok(R.BRIEF_PARTS.length === 2, "正文两段（另有一次不进正文的规划段）· 实得 " + R.BRIEF_PARTS.length);
  ok(R.BRIEF_PARTS.every((p) => p.min >= 1000 && p.name && p.desc),
    "每段都有最短长度（≥1000，五千字口径下的截断闸）、段名与职能说明");
  ok(new Set(R.BRIEF_PARTS.map((p) => p.desc)).size === 2, "两段职能互不重复");
  ok(/分离点/.test(R.BRIEF_PARTS[0].desc), "第一段职能点名分离点（可裁决判据的唯一原料）");
  ok(/最近邻/.test(R.BRIEF_PARTS[1].desc), "第二段职能点名敌意最近邻");
  ok(R.BRIEF_PARTS !== R.PAPER_PARTS && R.PAPER_PARTS.length === 4, "入口资料两段、论文四段，各有各的表");

  console.log("— 二、顺利跑完四段 —");
  reset([{ text: LONG(5000) }, { text: LONG(5000) }]);
  let r = await R.runParts(R.BRIEF_PARTS, seedFor, stat, "提炼中");
  ok(calls.join(",") === "1,2", "两段依次发出 part=1,2 · 实得 " + calls.join(","));
  ok(r.done === 2, "done=2");
  ok(r.text.length > 9000 && r.text.length < 13000, "合计约一万字（用户定的硬上限）· 实得 " + r.text.length);
  ok(R.missText(r.done, R.BRIEF_PARTS) === false, "两段齐全时不打缺段标记");

  console.log("— 三、后段要拿得到前面写的东西（接到空气上＝重写第一栏）—");
  ok(seeds[1] && seeds[1].tail && seeds[1].tail.length > 0, "第二段拿到了《已写部分·结尾》");
  ok(seeds[0] && seeds[0].tail === undefined, "第一段不带续写锚（它就是开头）");

  ok(seeds[1] && seeds[1].head && seeds[1].head.length > 0, "第二段拿到了《已写部分·开头》");
  ok(/runParts\(BRIEF_PARTS, seedFor, stat, '🧪 提炼中', function\(t\)/.test(fs.readFileSync(SRC,"utf8")),
    "入口资料自带取头函数（partHead 是按论文的题名＋摘要写的，对只有栏目的资料会切错）");

  console.log("— 四、中途某段写不出来：就地停住、不丢已写的 —");
  reset([{ text: LONG(5000) }, { text: "" }, { text: "" }, { text: LONG(5000) }]);
  r = await R.runParts(R.BRIEF_PARTS, seedFor, stat, "提炼中");
  ok(r.done === 1, "第二段没成 ⇒ done 停在 1 · 实得 " + r.done);
  ok(r.text.length > 4000, "第一段一个字没丢 · 实得 " + r.text.length);
  const miss = R.missText(r.done, R.BRIEF_PARTS);
  ok(typeof miss === "string" && /第二段/.test(miss), "缺段说明点名缺了第二段 · 实得：" + miss);

  console.log("— 五、第一段拿不到就没有资料，必须抛错 —");
  reset([{ err: "boom" }, { err: "boom" }, { text: LONG(5000) }]);
  let threw = false;
  try { await R.runParts(R.BRIEF_PARTS, seedFor, stat, "提炼中"); } catch (e) { threw = true; }
  ok(threw, "第一段两次都失败 ⇒ 抛错（不许静默交白卷）");
  ok(calls.length === 2, "重试封顶两次，不无限重试 · 实得 " + calls.length);

  console.log("— 六、段收尾标记必须剥净 —");
  const marks = ["〔第一段完·待续〕", "〔第二段完·待续〕", "〔第三段完·待续〕", "〔全文完〕", "〔上半篇完·待续〕", "〔规划完〕"];
  for (const m of marks) {
    reset([{ text: LONG(2000) + "。\n" + m }]);
    const t = await R.paperHalf(1, {}, 1200, "第一段");
    ok(t.indexOf(m) < 0, "剥净 " + m);
  }

  console.log("— 七、后端：part 钳位（旧版把第三、四段当成第一段重写）—");
  ok(/const part = \(body\.part >= 0 && body\.part <= 4\)/.test(w),
    "worker 收 part=0..4（0 是提炼的规划段），不再写死 `body.part === 2 ? 2 : 1`");
  ok(!/const part = body\.part === 2 \? 2 : 1;/.test(w), "旧的 1|2 钳位已经删掉");

  console.log("— 八、后端：distill 的四段提示语 —");
  const d0 = w.indexOf('else if (mode === "distill") {');
  const d1 = w.indexOf('else if (mode === "paper" || mode === "polish") {');
  ok(d0 > 0 && d1 > d0, "抠得到 distill 分支");
  const dseg = w.slice(d0, d1);
  ok(/BRIEF_SPEC\s*=\s*\{/.test(dseg) && /0:/.test(dseg) && /2:/.test(dseg), "规格写死在后端，不交给模型临场分配");
  for (const n of ["0", "1", "2"]) ok(new RegExp("^\\s*" + n + ":", "m").test(dseg), "BRIEF_SPEC 有第 " + n + " 档（0＝规划段）");
  ok(/〔规划完〕/.test(dseg) && /〔第一段完·待续〕/.test(dseg) && /〔全文完〕/.test(dseg), "三个收尾标记与前端剥标记的正则对得上");
  ok(/4700–5300 字/.test(dseg), "正文每段约五千字（两段合计一万）");
  ok(/合计不得超过一万/.test(dseg), "规划段明写一万字总额（用户定的硬口径：最多 1 万字）");
  ok(/写完比写长要紧/.test(dseg), "正文段明写「写完比写长要紧」——上一版正是最后一段写不完");
  ok(/body\.plan/.test(dseg), "正文段拿得到规划段的取舍清单");
  ok(/_briefPlan = \(mode === "distill" && part === 0\)/.test(w) && /_plainLong = _fullPower && !_briefPlan/.test(w),
    "规划段是全链唯一保留思考的长文档步骤（「总结要先思考」）");
  /* 【2026-08-13 契约翻面 —— 这一条是用血写的，翻它必须写清理由】
     旧判据：「开着思考就不得给满额预算」。它来自那条铁证——满预算＋开思考 ⇒
     思考 38,777 字、正文 0 字、第 128 秒被平台杀掉。这条规矩本身**没有作废**，
     正文两段仍然照它执行（满预算＋显式关思考，见 sim_ask_stream_first [九]）。
     翻的只是规划段这一格，理由是它与别处有一个结构性差别：
       **它是全链唯一一段失败不阻断的调用**——不进正文，前端 `.catch(→'')` 吞掉，
       拿不到清单就照旧直接写两段正文。烧光了只是没有规划，不是没有资料。
     用户口径「maxtoken 要能最大极限」于是落在这里，而不是到处发。
     三重保险必须同时在位，少一条这条翻面就不成立：早于平台的时钟、阶梯降档、关思考兜底重跑。 */
  ok(/_briefPlan \? _rungs\(\[WDS_TOK_HEAVY, 64000, 32000, 16000\]\)/.test(w),
    "规划段给到最大极限（它失败不阻断，是唯一赔得起的一段）");
  ok(/const _rungs = \(a\) => a\.filter\(/.test(w),
    "阶梯去重：没核实过上限的家 WDS_TOK_HEAVY 仍是 64000，不去重就白烧一次调用");
  /* 首档现在可能是 384K，一步退到 32000 跨度太大：基底若因第一个数太大而 400，
     第二档还该是个「大但常见」的数。 */
  ok(/const WDS_TOK_HEAVY = wdsTokCap\(VC\);/.test(w), "重档预算按家取真上限，不再写死一个拍出来的 64000");
  ok(/const WDS_TOK_CAP = \{ deepseek: 384000 \}/.test(w), "DeepSeek 的上限＝官方口径 384K（2026-08-13 核实）");
  ok(/const _clk = _heavy \?/.test(w), "保险一：早于平台的时钟仍在");
  ok(/_briefPlan \? _rungs\(\[WDS_TOK_HEAVY, 64000, 32000, 16000\]\)/.test(w), "保险二：阶梯降档仍在（首档不被接受时自动退格）");
  ok(/正在关掉思考重跑一次/.test(w), "保险三：零正文时关思考兜底重跑仍在");
  ok(/前端吞掉、照样往下走|失败也不阻断（前端吞掉/.test(w),
    "翻面成立的前提写在源码注释里：规划段失败不阻断（前提没了，这一格就该退回有界预算）");
  ok(/MAXTOK = P === 0 \? 12000 : 32000/.test(dseg), "规划段有界预算、正文段长文档预算");
  ok(/body\.head/.test(dseg) && /body\.tail/.test(dseg), "第二段收《已写部分》的开头与结尾");
  ok(/P === 1 \? "" :/.test(dseg), "第一段不发续写指令，第二段才发");

  console.log("— 九、后端：九栏的栏名与栏号一个字不许改 —");
  const cols = ["一、缘起之问与行进轨迹", "二、已经立住的核心判断", "三、候选承重命题 X",
    "四、反复被触到的分离点", "五、敌意最近邻清单", "六、尚未解决的张力与前后不一致",
    "七、可裁决判据的线索", "八、经验材料清单", "九、明确不写什么"];
  for (const c of cols) ok(dseg.indexOf(c) > 0, "第「" + c.slice(0, 2) + "」栏栏名原样在册");
  ok(/栏标题原样照抄/.test(dseg), "明写栏标题原样照抄（下游按栏名取料）");
  /* 成文那一步按栏名＋栏号发指令；栏名改了这里会指错地方 */
  const pseg = w.slice(d1, d1 + 40000);
  ok(/〔三、候选承重命题〕/.test(pseg) && /〔四、反复被触到的分离点〕/.test(pseg) && /〔五、敌意最近邻清单〕/.test(pseg),
    "成文（提炼档）仍按这几栏的栏名发指令，与上面的栏名一致");

  console.log("— 十、后端：distill 升为长文档配置 —");
  ok(/const _topPower = \(mode === "paper" \|\| mode === "polish" \|\| mode === "distill"\)/.test(w),
    "distill 进满功率档（满预算＋关思考）——五千字/段还开着思考必被时钟杀在思考阶段");
  ok(!/\(mode === "iq" \|\| mode === "distill"\) \? \[WDS_TOK_HEAVY, 12000, 8000\]/.test(w),
    "distill 从 iq 那条 12000 阶梯里摘出来了");

  console.log("— 十一、后端：两万字入口资料要能整份喂进成文 —");
  ok(/String\(body\.brief \|\| ""\)\.trim\(\)\.slice\(0, 30000\)/.test(w),
    "brief 上限抬到 30000（9000 会砍掉一多万字）");
  ok(!/\(P === 1 \? brief : brief\.slice\(0, 5000\)\)/.test(w), "后三段拿到的入口资料不再只有 5000 字");

  console.log("— 十二、前端：doDistill 走四段流水 —");
  const bd = h.slice(h.indexOf("function doDistill(){"), h.indexOf("var paperAll="));
  ok(/runParts\(BRIEF_PARTS/.test(bd), "doDistill 调 runParts(BRIEF_PARTS…)");
  ok(/return runParts\(/.test(bd), "返回 Promise 链（不返回，自动十轮会在提炼没跑完时开始成文）");
  ok(/gmode:'distill'/.test(bd), "透传 gmode=distill（共用续写机时靠它切后端分支）");
  ok(/missText\(r\.done, BRIEF_PARTS\)/.test(bd), "缺段说明按入口资料自己的四段表算");
  ok(/genTarget\('briefStat','bpFill','bpChars','briefBox'\)/.test(bd), "进度条与实时正文都指到 brief 那一组元素");
  ok(/brief\.length<1500/.test(bd), "过短闸 1500（旧的 300 是三千字那一版的数）");
  ok(/paperHalf\(0, \{gmode:'distill'/.test(bd), "先跑一次 part=0 的规划调用（「总结要先思考」）");
  ok(/\.catch\(function\(\)\{ return ''; \}\)/.test(bd), "规划失败不阻断：拿不到清单就照旧直接写");
  ok(/if\(plan\) e\.plan=plan;/.test(bd), "拿到的清单真的透给了两段正文");
  ok(/id="bpFill"/.test(h) && /id="bpChars"/.test(h) && /id="briefProg"/.test(h), "进度条三个元素都在页面上（缺一个就是 setProg 静默失效）");
  ok(/GEN_PREV\.length\+pacc\.length/.test(h), "字数计从已写部分接着走（旧版写死 paperAll.length，打磨时把论文长度算了进去）");
  ok(/约 <b>12<\/b> 次基底调用（开涌现档 16 次）/.test(h), "说明条里的调用次数跟着改了（提炼四段 → 规划＋两段＝3 次）");

  console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
  process.exit(F ? 1 : 0);
})();
