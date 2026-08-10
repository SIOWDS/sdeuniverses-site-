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

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
