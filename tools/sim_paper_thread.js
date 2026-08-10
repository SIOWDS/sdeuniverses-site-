/* 只测一件事：站内搜索页的「连续问对（≤10 轮）→ 提炼精华 → 论文入口资料 → 成文一篇」这条链
   （public/search/index.html 的 turns/buildHist/finishAsk/doDistill/doPaper + src/worker.js 的 hist/distill/brief）。

   为什么要有这个护栏：上下文这件事最容易坏在两头看不见的地方——
   ① 预算：十轮全量塞进去会把单轮 token 烧光，压缩策略一旦改错，最近两轮反而被砍；
   ② 接线：提炼出的《论文入口资料》如果没真接到成文那一步，页面上照样一切正常，
      只是论文悄悄退回单轮底稿——和「半篇冒充完稿」是同一类静默故障。 */
"use strict";
const fs = require("fs");
const H = fs.readFileSync("/home/claude/site/public/search/index.html", "utf8");
const W = fs.readFileSync("/home/claude/site/src/worker.js", "utf8");

let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };

/* ===== 一、把 buildHist 抠出来真跑（上下文预算是这条链最容易悄悄坏的地方）===== */
const a = H.indexOf("function buildHist(");
const b = H.indexOf("function updateTurnBar(");
if (a < 0 || b <= a) { console.log("FAIL 抠不出 buildHist（锚点变了，先改本脚本）"); process.exit(1); }
const mkHist = (turns) => new Function("turns", H.slice(a, b) + "\nreturn buildHist;")(turns);

const mk = (n) => Array.from({ length: n }, (_, i) => ({ q: "第" + (i + 1) + "问", a: "答".repeat(3000) }));

let turns = mk(10);
let hist = mkHist(turns)(false);
ok(hist.length === 10, "十轮全部进上下文（一轮都不丢）");
ok(hist[9].a.length === 1600 && hist[8].a.length === 1600, "最近两轮给足 1600 字（保真的永远是最近两轮）");
ok(hist[0].a.length === 500 && hist[7].a.length === 500, "更早的轮次压到 500 字（控预算）");
ok(hist[0].q === "第1问" && hist[9].q === "第10问", "问题一律不截断，顺序不乱");
const total = hist.reduce((s, t) => s + t.a.length + t.q.length, 0);
ok(total < 12000, "十轮压缩后总量 " + total + " 字 < 12000（单轮不会被上下文烧穿）");

const full = mkHist(turns)(true);
ok(full.every((t) => t.a.length === 2600), "提炼档 full=true：每轮都给 2600 字（提炼要看全场，不能只看尾巴）");
ok(full.length === 10, "提炼档拿到全部十轮");

turns = mk(1);
ok(mkHist(turns)(false)[0].a.length === 1600, "只有一轮时也按最近轮给足");

/* ===== 二、前端接线契约 ===== */
ok(H.indexOf("var MAXTURNS=10;") > 0, "轮次上限写死为 10");
ok(/turns\.length>=MAXTURNS/.test(H), "doAsk：满 10 轮拦住，不许无声继续");
ok(H.indexOf("请先「提炼精华」成论文入口资料，或「清空重来」") > 0, "满轮提示给出下一步动作");
ok(/turns\.length\?\{hist:buildHist\(false\)\}:\{\}/.test(H), "doAsk：有历史才带 hist（首轮仍走老路）");
ok(/turns\.push\(\{q:lastQ, a:lastAns\}\)/.test(H), "finishAsk：本轮入档");
ok(H.indexOf("if(lastAns && lastAns.length>60){") > 0, "只有真答出来的才算一轮（报错/空答不占轮次）");
ok(/function originQ\(\)\{ return turns\.length \? turns\[0\]\.q : lastQ; \}/.test(H), "缘起之问 = 整场问对的第一问");
ok(H.indexOf("q:originQ()") > 0, "成文用缘起之问定向，而不是最后一轮的追问");
ok(H.indexOf("esc(originQ().slice(0,64))") > 0, "PDF 页眉的缘起之问也走同一个口径");

/* 提炼 */
ok(H.indexOf("function doDistill()") > 0, "提炼精华函数在位");
ok(/if\(turns\.length<2\)\{ flashAsk\('至少完成两轮问对，再提炼。'\)/.test(H), "提炼门槛：至少两轮");
ok(/mode:'distill'/.test(H), "提炼走 distill 模式");
ok(/hist:buildHist\(true\)/.test(H), "提炼把全场问对（full）送上去");
ok(H.indexOf("if(brief.length<300){") > 0, "提炼产出过短则作废，不许拿半截当入口资料");
ok(H.indexOf("brief=''; return;") > 0, "作废时 brief 清空（成文会自动退回老路，而不是吃到半截清单）");
ok(/btnDistill.*style\.display = \(turns\.length>=2\)/.test(H.replace(/\n/g, " ")), "满两轮才露出提炼按钮");

/* 成文接线 —— 这条断了就是静默退化 */
ok(/brief\.slice\(0, i===0\?9000:5000\), qlist:qlist, briefKind:briefKind/.test(H), "成文·首段：有入口资料就以它为起点（并带上它的来源 briefKind）");
ok(/\{seed:lastAns\.slice\(0, i===0\?3500:1500\)\}/.test(H), "成文·首段：没有入口资料时退回单轮底稿（老路径不变）");
ok(/brief\.slice\(0, i===0\?9000:5000\)/.test(H), "成文·续写段：仍拿着同一份清单（缩到 5000 字）");
ok(/var qlist=turns\.map/.test(H), "问题清单（走过的路）一并送上去");

/* 清空 */
ok(H.indexOf("function resetThread(") > 0, "清空重来在位");
ok(/function resetThread\(quiet\)\{\s*\n\s*if\(!quiet && turns\.length && !confirm/.test(H),
   "resetThread(quiet)：只有人工点才弹确认，自动十轮清场不弹（弹了就卡住整场无人值守）");
ok(/turns=\[\]; brief=''/.test(H), "清空同时清掉入口资料（不许残留上一场的清单）");
ok(H.indexOf("confirm('清空这场问对") > 0, "清空前确认（十轮问对是贵的）");

/* ===== 三、worker 端契约 ===== */
ok(/_MODES = \{[^}]*distill: 1/.test(W), "worker：distill 进模式白名单");
ok(W.indexOf("const hist = (Array.isArray(body.hist) ? body.hist : []).slice(-10)") > 0, "worker：hist 钳到 10 轮");
ok(/\.slice\(0, 2600\) \}\)\)/.test(W) || W.indexOf('a: String((t && t.a) || "").trim().slice(0, 2600)') > 0, "worker：单轮答案钳到 2600 字");
ok(W.indexOf("const roundNo = hist.length + 1;") > 0, "worker：算得出这是第几轮");
ok(W.indexOf("const originQ = hist.length ? hist[0].q : q;") > 0, "worker：缘起之问 = 第一轮的问题");
ok(W.indexOf('const rq = _lightDeep') > 0, "worker：检索用问句按模式分流（distill 与碰撞/提炼同走 _lightDeep）");
ok(W.indexOf('(hist.length ? (q + " " + originQ.slice(0, 40)) : q)') > 0, "worker：连续问对时把缘起之问并进召回（治指代式短问漂走）");
ok(W.indexOf("lightRetrieve(env, url, rq, expTerms, K,") > 0, "worker：召回真的用了 rq，而不是裸 q");
ok(W.indexOf("sdeExpandQuery(VC, KEY, rq)") > 0, "worker：词义扩展也用 rq");
ok(W.indexOf('《此前的问对（同一场连续问对，共 "') > 0, "worker：单次调用的 user 消息带上此前问对");
ok(W.indexOf('《此前的问对（同一场连续问对）》') > 0, "worker：四步法的三次单维调用也带上此前问对");

/* 多轮纪律：上下文塞进去还不够，必须逼它往前走一步 */
ok(W.indexOf('if (histTxt && mode === "answer") {') > 0, "worker：多轮纪律只加在问答档");
ok(W.indexOf("这是同一场连续问对的第 ") > 0, "多轮纪律：告诉基底这是第几轮");
ok(W.indexOf("本轮必须比上一轮多走一步") > 0, "多轮纪律：硬性要求往前走一步");
ok(W.indexOf("补一个反例、切一条更细的差异、或把上一轮的结论逼到它开始失效的边界") > 0, "多轮纪律：写明三种前进方式");
ok(W.indexOf("前面几轮写过的段落一律不许重写") > 0, "多轮纪律：禁复读（十轮摊成十份同义答案是主要失败模式）");
ok(W.indexOf("或已经跑离最初那个缘起之问") > 0, "多轮纪律：跑题要当场说出来");
ok(W.indexOf("结尾那个升维追问要顺着这几轮的走向出") > 0, "多轮纪律：追问要能带动下一轮");

/* distill 的九栏 */
ok(W.indexOf('if (mode === "distill") {') > 0, "worker：distill 块在位");
["一、缘起之问与行进轨迹", "二、已经立住的核心判断", "三、候选承重命题 X",
 "四、反复被触到的分离点", "五、敌意最近邻清单", "六、尚未解决的张力与前后不一致",
 "七、可裁决判据的线索", "八、经验材料清单", "九、明确不写什么"].forEach(function (s) {
  ok(W.indexOf(s) > 0, "入口资料九栏：" + s);
});
ok(W.indexOf("只写这场问对里确实出现过的内容，一个字也不许编") > 0, "distill：禁编造（唯一例外是「应当交手而未交手」那一栏）");
ok(W.indexOf("〔一手来源〕〔站内自引〕〔未核验〕") > 0, "distill：经验材料必须标证据等级");
ok(W.indexOf("本场问对未产出") > 0, "distill：没长出来的栏目要如实留白，不许拿话填满");
ok(W.indexOf('_lightDeep ? 40 :') > 0, "distill/碰撞/提炼：检索档下调到 40 块（装内功但不广撒网，控成本）");
ok(W.indexOf('_lightDeep ? 14000 :') > 0, "distill/碰撞/提炼：《站内资料》钳到 14000 字");

/* ===== 六、手动连续问对也要层层逐深（2026-08-10 线上真故障）=====
   截图里第 1 轮与第 2 轮都是「语言是什么？」——九级追问阶梯（AUTO_LADDER）与拟题接口（nextq）
   都在服务端现成，却只有「自动十轮」用得上；手动路径靠用户自己想下一问，而输入框又留着上一句，
   点两下就把同一问问了两遍。登山靠的是阶梯，不是只告诉人「请往上走」。 */
console.log("— 六、手动问对的追问阶梯 —");
const bFin = H.slice(H.indexOf("function finishAsk("), H.indexOf("function doAutoRun("));
ok(/turns\.push\(\{q:lastQ, a:lastAns\}\);[\s\S]{0,120}suggestNextQ\(\);/.test(bFin),
  "每入档一轮就拟好下一问（不是等用户自己想）");
ok(/mode:'nextq'/.test(bFin) && /step:step/.test(bFin) && /hist:buildHist\(true\)/.test(bFin),
  "拟题真走服务端那条阶梯：只送 step，不在前端再拄一份阶梯（拄两份迟早漂移，而漂移后页面一切正常）");
ok(/turns\.length>=MAXTURNS/.test(bFin), "满十轮不再拟题");
ok(/\.catch\(function\(\)\{[\s\S]{0,200}style\.display='none'/.test(bFin),
  "拟题失败只收起提示，不报错也不动输入框——一次拟题失败不该有权力中断整场问对");
ok(/qNorm\(qa\.value\)===qNorm\(lastQ\)/.test(bFin),
  "只在输入框仍是上一句（或空）时才替换：用户已在自己敲下一问时不许抢他的字");
/* qNorm 抠出来真跑：去空白与句读后相等就算同一问 */
const qNorm = new Function("s", H.slice(H.indexOf("function qNorm("), H.indexOf("/* ===== 每答完一轮")) + "\nreturn qNorm(s);");
ok(qNorm("语言是什么？") === qNorm("语言是什么"), "qNorm：带不带问号算同一句");
ok(qNorm(" 语言 是什么 ") === qNorm("语言是什么"), "qNorm：空白不算数");
ok(qNorm("语言是什么") !== qNorm("语言不是什么"), "qNorm：真不同的两句不能被归成一句");
const bAsk2 = H.slice(H.indexOf("function doAsk("), H.indexOf("function finishAsk("));
ok(/turns\.some\(function\(t\)\{ return qNorm\(t\.q\)===qNorm\(q\); \}\)/.test(bAsk2),
  "同一问题重复问直接拦下（白烧一次百多秒的深度调用，还会把入口资料与论文一起带偏）");
ok(bAsk2.indexOf("turns.some(function(t){ return qNorm(t.q)===qNorm(q); })") < bAsk2.indexOf("asking=true;"),
  "拦截排在 asking=true 之前（拦完要能再问，不能把页面锁死）");
ok(/const AUTO_LADDER = \[/.test(W) && /if \(mode === "nextq"\)/.test(W),
  "服务端仍是阶梯的唯一定义处");
ok(/拟不出来|fb: "/.test(W), "每一级都配兵底问句（拟题失败也能把这一轮问出去）");

/* ===== 七、“不动了”不得再发生（2026-08-10 第二起线上故障）=====
   第 4 轮：空白框、无报错、等八十分钟仍是空。两处都要堵：
   ① 流完了却一个字都没有时，finishAsk 必须说话；② 流根本不结束时，前端得有自己的看门狗。 */
console.log("— 七、静默挂死 —");
const bFin2 = H.slice(H.indexOf("function finishAsk("), H.indexOf("function qNorm("));
ok(/if\(!lastAns \|\| !lastAns\.length\)\{[\s\S]{0,400}class="err"/.test(bFin2),
  "流完了却零产出时给一句能读的话（旧版完全沉默，空白框停在那儿）");
ok(/本轮没有入档/.test(bFin2), "并告诉用户本轮没入档、直接再问一次就行");
const bAsk3 = H.slice(H.indexOf("function doAsk("), H.indexOf("function finishAsk("));
ok(/new AbortController\(\)/.test(bAsk3) && /signal:_ac\?_ac\.signal:undefined/.test(bAsk3),
  "doAsk 自带 AbortController 且真接到 fetch 上（服务端的闸管不住整个 Worker 被杀）");
ok(/function _bump\(ms\)/.test(bAsk3) && (bAsk3.match(/_bump\(/g) || []).length >= 3,
  "看门狗每收一帧就续一次（只设一次等于把正常的长回答也掉了）");
ok(/_bump\(deepOn\?150000:70000\)/.test(bAsk3),
  "首帧闸给得宽：深度档出流前要跑词表扩展＋全站检索＋装内功");
ok(/if\(_stalled\)\{/.test(bAsk3) && /finishAsk\(ansEl, gotErr, lastStat\);/.test(bAsk3),
  "自己掉线时：已写出的字保住并入档，不当成「请求失败」一抄了事");
ok(/if\(_wd\) clearTimeout\(_wd\);/.test(bAsk3), "收尾清掉看门狗（不清就会在下一轮里乱开枪）");

/* ===== 八、零产出的那句话不得盖掉真因（2026-08-10）=====
   上一版刚加的「零产出提示」把服务端已经报出的真错误（额度用完、Key 不能用、
   上游 4xx、被闸掉线）一并盖成了「被平台无声掉线了」这句猜测——真因当场消失。 */
console.log("— 八、零产出提示不得抹掉真因 —");
const bFin3 = H.slice(H.indexOf("function finishAsk("), H.indexOf("function qNorm("));
ok(/function finishAsk\(ansEl, gotErr, lastStat\)/.test(bFin3), "finishAsk 收得到 gotErr 与 lastStat");
ok(/if\(gotErr\) return;/.test(bFin3), "服务端已报过真因时直接返回，不拿通用文案盖它");
ok(bFin3.indexOf("if(gotErr) return;") < bFin3.indexOf("本轮一个字都没回来"), "返回排在写通用文案之前");
ok(/lastStat\?'停住时的最后一步是：'/.test(bFin3), "真的没有真因时，至少把最后一条状态印出来（死在检索还是死在基底，是两回事）");
const bAsk4 = H.slice(H.indexOf("function doAsk("), H.indexOf("function finishAsk("));
ok(/var gotErr=false, lastStat='';/.test(bAsk4), "doAsk 里有这两个变量");
ok(/gotErr=true;/.test(bAsk4), "收到 error 帧就立旗");
ok(/lastStat=j\.v;/.test(bAsk4), "每条 status 都记下来");
ok((bAsk4.match(/finishAsk\(ansEl, gotErr, lastStat\)/g) || []).length >= 2, "两个调用点都把旗传下去（漏一个就又盖一次）");

/* ===== 九、深度档连续问对：轮次越往后站内资料越少 =====
   检索时间与预填时间都算在平台那道 130 秒的墙里，而历轮上下文本身还在变长。 */
console.log("— 九、轮次越后、资料越少 —");
ok(/const _thr = \(mode === "answer" && hist\.length\)/.test(W), "阶梯只对深度档连续问对生效（不影响成文／提炼／盲评）");
const mK = W.match(/const K = mode === "recommend" \? 48 : \(_lightDeep \? 40 : \(deep \? ([^:]*) : 20\)\);/);
const mC = W.match(/const CTX_MAX = _lightDeep \? 14000 : \(deep \? ([^:]*) : 12000\);/);
ok(!!mK && !!mC, "K 与 CTX_MAX 都改成了随轮次递减");
const kFn = new Function("_thr", "return " + (mK ? mK[1] : "120") + ";");
const cFn = new Function("_thr", "return " + (mC ? mC[1] : "50000") + ";");
ok(kFn(0) === 120 && cFn(0) === 50000, "第一轮一字不减（它本来就不撞墙）");
ok(kFn(3) < kFn(0) && cFn(3) < cFn(0), "第四轮确实降下来了· K=" + kFn(3) + " CTX=" + cFn(3));
ok(kFn(5) >= 36 && cFn(5) >= 12000, "降到底也保底（K≥36、CTX≥12000）· 实得 " + kFn(5) + " / " + cFn(5));
ok(kFn(9) === kFn(5) && cFn(9) === cFn(5), "_thr 已封顶，不会越减越没");

/* ===== 十、写得完才算数（2026-08-10 第三起线上故障）=====
   截图：「DeepSeek 超过 107 秒还没写完（已掉线）」，答案断在半句。
   107 = 120 减去出流前花的 8 秒（闸本身已经对了）——真正的问题是字数目标本身就写不下。
   另：答案框是纯文本，基底写的 ## 与 ** 与 --- 全部原样印在了屏幕上。 */
console.log("— 十、写得完才算数 —");
const mAnsLen = W.match(/\*\*(\d+)–(\d+) 字\*\*，结尾留一个/);
ok(!!mAnsLen && Number(mAnsLen[2]) <= 2200,
  "深度档问答字数上限 ≤ 2200（107 秒写不完 2800）· 实得 " + (mAnsLen ? mAnsLen[2] : "?"));
ok(/宁可少展开一节，也必须把最后一句写完/.test(W),
  "明写「写完比写长要紧」：断在半句的答案不如一个短而完整的");
ok((W.match(/不写 #、不写 \*\*、不画表格、不写 --- 分隔线/g) || []).length >= 2,
  "深度档与普通档两处都禁了 Markdown（答案框是 textContent，## 会原样印出来）");
ok(/ansEl\.textContent=acc;/.test(H), "答案框确实是纯文本渲染（所以上一条才是必须的）");
ok(/Math\.max\(25000, 120000 - _spent\)/.test(W),
  "总闸由 115 秒抬到 120 秒（平台墙 128–133，仍留 8–13 秒把掉线那句话发出去）");

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
