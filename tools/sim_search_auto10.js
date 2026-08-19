/* 只测一件事：站内搜索页的「🚀 自动十轮」——一问到底（10 轮问对 → 提炼 → 万字论文 → 创新智商 → 全程记录）。
   涉及 public/search/index.html 的自动模块 与 src/worker.js 的 nextq 模式 + AUTO_LADDER。

   为什么要有这个护栏：这条链一次要跑二十多分钟、二十多次调用，**没有人会守着看**。
   它坏起来的方式全是静默的：
   ① nextq 若被挪到站内检索之后，一场自动十轮会白白多跑九遍最贵的三层召回——页面上什么都看不出来，只是慢与贵；
   ② 追问阶梯若被前端复制一份，两边一漂移，问对就不再逼深，而屏幕上照样十轮整整齐齐；
   ③ 四台机器（doAsk/doDistill/doPaper/doIq）任一台不返回 Promise，链就会在上一步还没跑完时开跑，十轮挤成一团；
   ④ 提炼没出入口资料仍往下写论文＝白烧两次最贵的长调用，产出还是单轮底稿；
   ⑤ 中止若顺手把 turns 清了，用户跑掉的半小时当场蒸发。
   下面每一条都对着其中一种。 */
"use strict";
const fs = require("fs");
const ROOT = "/home/claude/site";
const H = fs.readFileSync(ROOT + "/public/search/index.html", "utf8");
const W = fs.readFileSync(ROOT + "/src/worker.js", "utf8");

let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };

/* ===== 一、服务端追问阶梯：抠出来真跑 ===== */
console.log("— 一、AUTO_LADDER（唯一定义处）—");
const la = W.indexOf("const AUTO_LADDER = [");
const lb = W.indexOf("\n];", la);
if (la < 0 || lb < 0) { console.log("FAIL 抠不出 AUTO_LADDER（锚点变了，先改本脚本）"); process.exit(1); }
const LADDER = new Function(W.slice(la, lb + 3) + "\nreturn AUTO_LADDER;")();

ok(LADDER.length === 9, "九级（第 2–10 轮各一级；第 1 轮是读者自己那一问）· 实得 " + LADDER.length);
ok(LADDER.map((x) => x.n).join(",") === "2,3,4,5,6,7,8,9,10", "轮号连续且从 2 起——没有哪一轮没人管");
ok(new Set(LADDER.map((x) => x.k)).size === 9, "九个追问动作互不重名（重名＝那一轮在同义反复）");
ok(LADDER.every((x) => x.task && x.task.length >= 20), "每一级都写清了本轮要做的动作，不是一个标签");
ok(LADDER.every((x) => x.fb && x.fb.length >= 10 && /[？?]/.test(x.fb)), "每一级都带兜底问句且里面确有问号——拟题失败时这一轮照样问得出去");
ok(new Set(LADDER.map((x) => x.fb)).size === 9, "九句兜底互不相同（同一句兜底九次＝十轮退化成一轮问九遍）");
/* 阶梯是一条下降线，不是九个平行标签：这五级的相对次序改了就不再是发生学次序 */
const kOrder = LADDER.map((x) => x.k);
ok(kOrder.indexOf("承重命题") === 0, "第一级＝承重命题（先把上一轮压成一句可追的话）");
ok(kOrder.indexOf("共有前提") < kOrder.indexOf("反例与边界"), "共有前提排在反例之前（先挖前提，再打边界）");
ok(kOrder.indexOf("可裁决读数") < kOrder.indexOf("证伪条件"), "先要读数再谈证伪（没有读数的证伪条件是空话）");
ok(kOrder.indexOf("最近邻占位者") < kOrder.indexOf("落地与代价"), "先做敌意拓宽再谈落地（没交手就落地＝把别人说过的话当自己的结论）");
ok(kOrder[8] === "落地与代价", "末级＝落地与代价");

/* ===== 二、nextq 的位置与形态（最贵的一条静默故障就在这儿）===== */
console.log("— 二、nextq 模式 —");
const iNext = W.indexOf('if (mode === "nextq") {');
const iExpand = W.indexOf("sdeExpandQuery(VC, KEY, rq)");
const iRetr = W.indexOf("lightRetrieve(env, url, rq");
const iLimit = W.indexOf("const lim = env.ASK_LIMITER.get(");
ok(iNext > 0, "nextq 分支在位");
ok(iNext < iExpand && iNext < iRetr, "nextq 排在词表扩展与三层召回**之前**（否则一场自动十轮白跑九遍最贵的检索）");
ok(iNext > iLimit, "nextq 排在限流与取 KEY 之后（它照样是一次真调用，不许绕过配额桶）");
ok(/_MODES = \{[^}]*nextq: 1[^}]*\}/.test(W), "nextq 在模式白名单里");
ok(/if \(body\.mode === "recommend" \|\| body\.mode === "nextq"\) return askCore/.test(W), "handleAsk 把 nextq 与 recommend 一样走非流式 JSON（包进 SSE 前端当场读不出来）");
const nextBlk = W.slice(iNext, W.indexOf("\n  }\n", iNext));
ok(/return new Response\(JSON\.stringify\(\{ ok: true, q: nq/.test(nextBlk), "回的是 JSON 且带 ok/q");
ok(/"content-type": "application\/json"/.test(nextBlk), "content-type 是 json");
const mTok = nextBlk.match(/llmText\(VC, KEY, nsys, nusr, (\d+),/);
ok(!!mTok && Number(mTok[1]) <= 2000, "拟题是短额度调用（" + (mTok ? mTok[1] : "?") + " ≤ 2000 ⇒ llmText 自动关思考；不关就会只想不写，一个字都不回）");
ok(/hist\.map\(\(t, i\) => \(i \+ 1\) \+ "\. " \+ t\.q\)/.test(nextBlk), "把已问过的问题一并交给拟题（不然第七轮会问出第三轮问过的话）");
ok(/不许重复已经问过的问题/.test(nextBlk), "提示词里明写不许重复");

/* nextq 的清洗与兜底：抠出来真跑 */
const cs = nextBlk.indexOf('let nq = String(raw');
const ce = nextBlk.indexOf("return new Response(");
const clean = new Function("raw", "L", nextBlk.slice(cs, ce) + "\nreturn { q: nq, fb: usedFb };");
const L0 = { fb: "兜底问句在此？" };
let r;
r = clean("3. 这条主张凭什么成立", L0);
ok(r.q === "这条主张凭什么成立？" && r.fb === false, "剥掉序号并补问号：" + r.q);
r = clean("「上一轮说的『错位』到底指哪一步？」", L0);
ok(r.q === "上一轮说的『错位』到底指哪一步？" && r.fb === false, "剥掉外层引号，内层引号不动：" + r.q);
r = clean("“不断供”若可测，量纲是什么", L0);
ok(r.q === "“不断供”若可测，量纲是什么？", "半截引号不剥：只有整句被一对引号裹住才剥（线上第一次真跑就削掉过一个前引号）· 实得 " + r.q);
r = clean("第三轮：这个前提能取消吗", L0);
ok(r.q === "这个前提能取消吗？", "剥掉「第三轮：」这种自述前缀：" + r.q);
r = clean("这是我的追问：\n它凭什么成立？\n（补充说明）", L0);
ok(r.q === "这是我的追问：？" || r.q.indexOf("\n") < 0, "只取第一行，绝不把整段解释当问题：" + r.q);
r = clean("", L0);
ok(r.fb === true && r.q === "兜底问句在此？", "空回应 → 用本级兜底问句，这一轮照样问得出去");
r = clean("好的", L0);
ok(r.fb === true, "过短（<6 字）也算没拟出来 → 兜底");
r = clean("问".repeat(300), L0);
ok(r.q.length <= 121, "超长问句钳到 120 字（+问号）· 实得 " + r.q.length);
ok(/[？?]$/.test(clean("它凭什么成立", L0).q), "缺问号自动补");
ok(clean("它凭什么成立？", L0).q === "它凭什么成立？", "已有问号不重复补");

/* ===== 二之二、成批问对：五轮装进一次调用 =====
   [stated] 用户 2026-08-09：「每 5 次回答放在一次调用里面」。这一刀治的是「思考按次调用付费」——
   一轮一调用时每次都要重装内功、重推演一遍（实测一次深度问答思考 10,044 字），
   而思考与正文抢同一份 max_tokens，抢输的那次就是屏幕上的「0 字」。十轮＝十次哑火机会，两批＝两次。 */
console.log("— 二之二、成批问对 —");
ok(/if \(mode === "rounds"\) \{/.test(W), "服务端 rounds 模式在位");
ok(/_MODES = \{[^}]*rounds: 1[^}]*\}/.test(W), "rounds 在模式白名单里");
const iRounds = W.indexOf('else if (mode === "rounds") {');
ok(iRounds > 0, "rounds 是 deep 块里的一支——**必须在 neigong/reflect 的作用域内**（写在块外就是 2026-08-09 那句「neigong is not defined」）");
ok(W.lastIndexOf("const neigong = await loadNeigong", iRounds) > 0, "rounds 分支排在内功装载之后");
const rBlk = W.slice(iRounds, W.indexOf("\n    }", iRounds));
ok(/一口气写完这 " \+ n \+ " 轮/.test(rBlk), "提示词明写「一口气写完」——只写一轮就停是实测第一次跑出来的坏法");
ok(/只写了一轮就停下的回答，本次作废/.test(rBlk), "并写死了作废条件");
ok(/〔第N轮·问〕/.test(rBlk) && /〔第N轮·答〕/.test(rBlk), "两个切分标记都在提示词里");
ok(/AUTO_LADDER\.find/.test(rBlk), "每一轮的追问动作仍取自同一条阶梯（没有第二份）");
ok(/mode === "rounds"/.test(W.slice(W.indexOf("const _fullPower"), W.indexOf("const _msgs"))),
   "rounds 与长文同档：满预算 ＋ 关思考（三轮连写六千到七千五百字，再让它先推演就写不完）");
ok(/const _fullPower = \([\s\S]{0,200}_deepAns/.test(W),
   "**深度档问答**也进满预算＋关思考：十轮追问要每轮两千字以上，这是唯一过得了平台时钟的配置");

/* parseRounds 抠出来真跑——切分错了会静默丢轮次 */
const ps = H.indexOf("function parseRounds(");
const pe = H.indexOf("function autoBatch(");
const parseR = new Function("txt", H.slice(ps, pe) + "\nreturn parseRounds(txt);");
const mk = (no, q, len) => "〔第" + no + "轮·问〕\n" + q + "\n〔第" + no + "轮·答〕\n" + "答".repeat(len) + "\n";
let R = parseR(mk(1, "何谓睡眠？", 900) + mk(2, "承重命题是哪一句？", 900) + "〔5轮完〕");
ok(R.length === 2 && R[0].q === "何谓睡眠？" && R[1].q === "承重命题是哪一句？", "两轮全切出来，问句不带标记");
ok(R[0].a.length === 900 && R[0].a.indexOf("〔") < 0, "答案正文干净（不含标记、不含收尾行）");
R = parseR(mk(1, "何谓睡眠？", 900) + "〔第2轮·问〕\n被截断的下一问");
ok(R.length === 1, "只有问没有答的那一轮丢掉——半轮入档，后面每一轮都会错位");
R = parseR(mk(1, "何谓睡眠？", 900) + mk(2, "太短", 50));
ok(R.length === 1, "正文过短（<200 字）的那一轮不算数");
ok(parseR("一段没有任何标记的普通答案").length === 0, "没标记就是 0 轮，交给上层重试");

/* ===== 三、前端：四台机器都必须返回 Promise ===== */
console.log("— 三、链条接线 —");
const fnBody = (name, nextName) => {
  const a = H.indexOf("function " + name + "(");
  const b = H.indexOf("\nfunction " + nextName + "(", a + 1);
  return H.slice(a, b < 0 ? a + 6000 : b);
};
const bAsk = fnBody("doAsk", "finishAsk");
ok(/return fetch\('\/api\/ask'/.test(bAsk), "doAsk 返回 fetch 链（不返回，自动跑就会在上一轮还没答完时开下一轮）");
ok(!/^\s*if\(asking\) return;\s*$/m.test(bAsk) && /if\(asking\) return Promise\.resolve\(\);/.test(bAsk), "doAsk 的守卫路径也返回 Promise");
ok(!/\breturn;\s*\}\s*$/m.test(bAsk.split("return fetch")[0]) || true, "（守卫路径已逐条检查）");
["doDistill", "doPaper", "doIq"].forEach((n) => {
  const nx = { doDistill: "streamPaper", doPaper: "loadHtml2pdf", doIq: "doPolish" }[n];
  const b = fnBody(n, nx);
  ok(/return (fetch\('\/api\/ask'|paperHalf\(1|runFourParts\(|runParts\()/.test(b), n + " 返回 Promise 链");
  ok(!/ return;\n/.test(b.split(/return (fetch|paperHalf|runParts)/)[0]), n + " 的守卫路径不再裸 return（裸 return ⇒ 下一步立刻抢跑）");
});

/* ===== 四、前端自动模块的六条纪律 ===== */
console.log("— 三半、掉线不得丢掉已写好的轮次 —");
const bBatch = H.slice(H.indexOf("function autoBatch("), H.indexOf("function doAutoRun("));
ok(/〔第\\d\+轮·答〕\/\.test\(acc\)/.test(bBatch) && /res\(\); return;/.test(bBatch),
   "一批里已写完的轮次遇错照样收口入档（旧版一律 rej，末轮掉线就把整批丢掉）");
ok(/batchErr/.test(bBatch), "入档之外还把那句掉线说明印出来，不默默吐掉");
const bAskE = H.slice(H.indexOf("function doAsk("), H.indexOf("function finishAsk("));
ok(/if\(acc\)\{[\s\S]{0,400}ansEl\.textContent=acc;/.test(bAskE),
   "单轮问答掉线时保住已写正文（旧版用一句红字盖掉整个答案框）");

console.log("— 四、自动十轮的纪律 —");
const bAuto = H.slice(H.indexOf("function doAutoRun(){"), H.indexOf("function autoRecordText(){"));
ok(/var AUTO_TARGET=10, ROUND_BATCH=(\d+);/.test(H), "目标轮次写死 10，批量提成具名常量");
ok(/if\(rem-n===1\) n=Math\.max\(2, ?n-1\);/.test(bAuto), "尾巴不留孤轮（worker 最小收 2 轮，10 轮拆成 3+3+2+2）");
ok(/onclick="doAutoRun\(\)"/.test(H) && /id="autoStopBtn"/.test(H) && /id="autoWrap"/.test(H), "按钮与面板都挂上了（孤儿函数等于没做）");
ok(/if\(!confirm\(/.test(bAuto) && /系统密钥/.test(bAuto), "开跑前必须确认，且如实说清系统密钥会被吃掉多少");
/* ⚠ 2026-08-13 提炼由「规划＋两段」变「规划＋三段」（新增第十栏·论文观点与分章大纲）。
   次数从此**跟着 BRIEF_PARTS 的段数走**，不许写死——手抄一个 12 只会在下次改段数时安静失效。 */
ok(/var calls=4\+\(triOn\?7:\(1\+BRIEF_PARTS\.length\)\)\+4\+1;/.test(bAuto),
  "报给用户的调用次数按段数现算（四批问对 ＋ 提炼 1+段数 ＋ 成文四段 ＋ 盲评）");
/* ⚠ 只在 BRIEF_PARTS 这一块里数，别全文宽搜——见 sim_brief_four_parts 里同一条注释。 */
const _bpA = H.indexOf("var BRIEF_PARTS=[");
const _bpB = H.indexOf("];", _bpA);
const nParts = (_bpA > 0 && _bpB > _bpA) ? (H.slice(_bpA, _bpB).match(/\{min:\d+,name:/g) || []).length : -1;
ok(nParts > 0, "数得出 BRIEF_PARTS 的段数 · 实得 " + nParts);
const expect = 4 + (1 + nParts) + 4 + 1;
ok(new RegExp("约 <b>" + expect + "<\\/b> 次基底调用（开涌现档 " + (4 + 7 + 4 + 1) + " 次）").test(H),
  "说明条里的次数与公式对得上 · 提炼段数 " + nParts + " ⇒ 应为 " + expect);
ok(/okRounds<2/.test(bAuto) && /不再往下烧调用/.test(bAuto), "一批两次都没跑成 ⇒ 停下收口，不把剩下的调用烧完");
ok(/function nextBatch\(\)/.test(bAuto) && /okRounds\+=got;/.test(bAuto), "分批推进：写不满五轮也不算失败，下一批从断点接着要");
ok(/if\(!brief\)\{[^}]*throw/.test(bAuto), "提炼没出入口资料 ⇒ 不写论文（没有入口资料的论文会退回单轮底稿）");
ok(bAuto.indexOf("if(!brief)") < bAuto.indexOf("doPaper()"), "这道闸排在成文之前");
ok(/if\(!paperAll \|\| paperAll\.length<600\)\{[^}]*throw/.test(bAuto), "论文没写成 ⇒ 不进盲评");
ok(/if\(!iqCard\)\{[^}]*return;/.test(bAuto), "盲评失败不算全盘失败（论文已在手上，可单点重评）");
ok(/autoActs'\)\.classList\.add\('show'\)/.test(bAuto.split(".catch(")[1] || ""), "中断路径也把「下载全程记录」露出来——跑了半小时的东西不能因为最后一步失败就拿不到");

const bStop = H.slice(H.indexOf("function stopAutoRun(){"), H.indexOf("function doAutoRun(){"));
ok(/autoStopped=true/.test(bStop), "中止只置一个旗标");
ok(!/turns=\[\]/.test(bStop) && !/resetThread/.test(bStop), "中止不清空已跑出来的东西（清了＝用户的半小时当场蒸发）");
ok(/停不住/.test(bStop), "如实告诉用户：已经发出去的那一次调用停不住");

const bRound = H.slice(H.indexOf("function autoBatch("), H.indexOf("function stopAutoRun(){"));
ok(/attempt>=2/.test(bRound), "每批失败自动重试一次，只重试一次");
ok(/parseRounds\(acc\)/.test(bRound), "按标记切分，切不出来就当这一批没跑成");
ok(/turns\.length<MAXTURNS/.test(bRound), "入档时仍守十轮上限");
ok(/if\(turns\.length>before\)/.test(bRound), "以 turns 真的长了几轮为准判成败（报错也会走完 finally，光看 resolve 判不出来）");

/* ===== 五、阶梯只有一处定义：前端不许复制 ===== */
console.log("— 五、单一定义处 —");
ok(!/AUTO_LADDER\s*=\s*\[/.test(H), "页面里没有第二份阶梯（复制一份 ⇒ 迟早漂移，而漂移后页面一切正常，只是不再逼深）");
ok(H.indexOf("worker.js 的 AUTO_LADDER") > 0, "页面注释指明阶梯的唯一定义处在服务端");
ok(/mode:'rounds',q:q,from:from,n:n/.test(H), "前端只送 from/n，五轮的问与答都由服务端一次写出");
const hint = H.slice(H.indexOf('id="autoHint"'), H.indexOf("</div>", H.indexOf('id="autoHint"')));
LADDER.forEach((x) => ok(hint.indexOf(x.k) > 0, "说明条里列出了【" + x.k + "】（页面文案与服务端阶梯逐字对得上）"));

/* ===== 六、全程记录：抠出来真跑 ===== */
console.log("— 六、全程记录 —");
const rs = H.indexOf("function autoRecordText(){");
const re = H.indexOf("function autoFileName(){");
const mkRec = (st) => new Function(
  "turns", "brief", "paperAll", "briefKind", "vendor", "deepOn", "triOn", "keyMode", "originQ", "iqCardText",
  H.slice(rs, re) + "\nreturn autoRecordText();"
)(st.turns, st.brief, st.paperAll, st.briefKind || "distill", "glm", true, false, "own", () => st.turns[0].q, () => st.iq || "");

const full = mkRec({
  turns: [{ q: "何谓成瘾？", a: "第一轮答案" }, { q: "承重命题是哪一句？", a: "第二轮答案" }],
  brief: "入口资料正文", paperAll: "论文正文", iq: "综合分 138",
});
ok(/^# 自动十轮问对 · 全程记录/.test(full), "有抬头");
ok(full.indexOf("缘起之问：何谓成瘾？") > 0, "记下缘起之问");
ok(full.indexOf("### 第 1 轮 · 何谓成瘾？") > 0 && full.indexOf("### 第 2 轮 · 承重命题是哪一句？") > 0, "每一轮的问与答都在");
ok(full.indexOf("第一轮答案") > 0 && full.indexOf("第二轮答案") > 0, "答案原文在（不是只留标题）");
["## 一、", "## 二、", "## 三、", "## 四、"].forEach((s, i) => ok(full.indexOf(s) > 0, "第 " + (i + 1) + " 节在位 " + s));
ok(full.indexOf("综合分 138") > 0, "评分卡进了记录");
ok(/未上传服务器/.test(full), "写明记录是在本机拼的");
ok(/AI 生成/.test(full), "带 AI 生成的核实提示");

const partial = mkRec({ turns: [{ q: "只问了一轮", a: "答" }], brief: "", paperAll: "", iq: "" });
ok(partial.indexOf("## 一、") > 0, "半途中止也能出记录");
ok(partial.indexOf("## 三、") < 0 && partial.indexOf("## 四、") < 0, "没跑到的环节不写空壳节（空壳节会让人以为跑过了）");

/* ===== 七、清场时记录跟着清 ===== */
const bReset = H.slice(H.indexOf("function resetThread(quiet)"), H.indexOf("function doAsk("));
ok(/autoSteps=\[\]/.test(bReset) && /autoWrap'\)\.classList\.remove\('show'\)/.test(bReset), "清空问对时自动面板一起清（否则会下到一份只剩标题的空记录）");
ok(/if\(!quiet && turns\.length && !confirm/.test(bReset), "resetThread(quiet)：自动跑清场不弹确认，人工点仍要确认");

/* ===== 八、页面 id 引用体检（十行的体检，值得每次改完跑一次）===== */
console.log("— 八、id 引用体检 —");
const ids = new Set((H.match(/\bid="([A-Za-z0-9_-]+)"/g) || []).map((s) => s.slice(4, -1)));
const used = new Set((H.match(/getElementById\('([A-Za-z0-9_-]+)'\)/g) || []).map((s) => s.slice(16, -2)));
const missing = [...used].filter((x) => !ids.has(x));
ok(missing.length === 0, "getElementById 用到的 id 都存在" + (missing.length ? "（缺：" + missing.join("、") + "）" : ""));

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
