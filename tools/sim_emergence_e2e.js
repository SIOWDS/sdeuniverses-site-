/* 端到端干跑：把涌现流水线整条逻辑真跑一遍（基底打桩，不花一次真调用）。
   测的不是提示写得好不好——那要真跑才知道；测的是**接线与状态机**：
   前端发出的字段名，worker 是不是真的读得到；三路碰撞的结果怎么变成三张评分卡；
   择优取的是不是同一把尺子下的最高分；胜出典范与落选零件是不是都进了综合提炼；
   综合提炼是不是真的成了论文入口 brief；以及任一环挂掉时，整条线会不会静默交出半成品。 */
"use strict";
const fs = require("fs");
const ROOT = "/home/claude/site";
const html = fs.readFileSync(ROOT + "/public/search/index.html", "utf8");
const wk = fs.readFileSync(ROOT + "/src/worker.js", "utf8");
let P = 0, FA = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (FA++, console.log("  FAIL " + m)); };
const say = (s) => console.log(s);

/* ══════════ 桩：DOM ══════════ */
function mkEl() {
  return { textContent: "", innerHTML: "", value: "", disabled: false, style: {}, className: "",
    _cls: {}, classList: { add(c) { this._cls = this._cls || {}; this._cls[c] = 1; },
      remove(c) { if (this._cls) delete this._cls[c]; }, toggle(c, v) { v ? this.add(c) : this.remove(c); },
      has(c) { return !!(this._cls && this._cls[c]); } }, focus() {} };
}
const els = {};
const doc = { getElementById(id) { return els[id] || (els[id] = mkEl()); } };
["emergeStat", "emergeBox", "emergeWrap", "emergeActs", "briefStat", "briefBox", "briefWrap", "btnEmerge", "userKey", "iqSrc"].forEach(id => doc.getElementById(id));
els.emergeActs.classList.has = function (c) { return !!(this._cls && this._cls[c]); };

/* ══════════ 桩：基底（可编程剧本） ══════════ */
const PARADIGM = (name, extra) => name + "\n\n【承重命题】课堂沉默不是知识缺口，也不是权力压制，而是" + name + "。\n"
  + "【它切开的辨别面】" + "把「不敢说」与「无可说」第一次分得开。".repeat(6) + "\n"
  + "【第二轴与二维辨别格】第一象限（高X×高Y）：…；第二象限：…；第三象限：…；第四象限：…\n"
  + "【可裁决判据】当匿名化提问时，Meyer & Rowan 的脱耦论预测沉默不变，本典范预测沉默显著下降。\n"
  + "【可观测代理】匿名前后发言率之差，三个班级中至少两个复现。\n"
  + "【两条证伪条件】一、若匿名化后仍不变即证伪；二、若在无评价场景中同样出现即证伪。\n"
  + "【它从哪里撞出来】由观点一与观点三在「谁在评价」这一点上的相反判断撞出。\n"
  + "【它最容易在哪里被推翻】" + (extra || "第二轴与 Z 可能并不独立。") + "\n" + "补白。".repeat(80);
const CARD = (S, D, E, I, F, verdict, unhandled) => JSON.stringify({
  title: "典范", corpus: "教育社会学＋组织理论＋临床心理学",
  S: { score: S, evidence: "原文一句", why: "论证链可追溯" }, D: { score: D, evidence: "原文一句", why: "切了新辨别面" },
  E: { score: E, evidence: "原文一句", why: "跨域是类比" }, I: { score: I, evidence: "原文一句", why: "半数可还原" },
  F: { score: F, evidence: "原文一句", why: "有可跑的证伪条款" },
  narrow: { S: S + 4, D: D + 6, E: E + 5, I: I + 8, F: F + 2 },
  neighbors: [{ name: "Merton 仪式主义 1938", overlap: "占了强迫性遵从这一块", handled: false },
              { name: "Meyer & Rowan 脱耦 1977", overlap: "占了形式与功能脱钩", handled: true }].slice(0, unhandled ? 2 : 1),
  deductions: [{ dim: "I", quote: "原文某句", from: 130, to: I, why: "可被现成概念一比一替换" }],
  upgrades: [{ dim: "I", action: "请 Merton 进正文正面交手", gain: I + "→132" }], verdict: verdict
});
let SCRIPT = {};   // {collide:[...], iq:[...], synth:"..."} ；元素为字符串＝正常产出，Error＝该次调用失败
const captured = [];
function fakeFetch(url, opt) {
  const body = JSON.parse(opt.body);
  captured.push(body);
  let out;
  if (body.mode === "collide") out = SCRIPT.collide.shift();
  else if (body.mode === "iq") out = SCRIPT.iq.shift();
  else if (body.mode === "synth") out = SCRIPT.synth;
  else out = "";
  if (out instanceof Error) return Promise.resolve({ ok: false, status: 500, text: () => Promise.resolve(out.message) });
  const enc = new TextEncoder();
  const chunks = [];
  chunks.push('data: {"t":"think","v":"…"}\n');
  String(out).match(/[\s\S]{1,180}/g).forEach(s => chunks.push("data: " + JSON.stringify({ t: "token", v: s }) + "\n"));
  chunks.push("data: [DONE]\n");
  let i = 0;
  return Promise.resolve({ ok: true, status: 200, body: { getReader() {
    return { read() { return i >= chunks.length ? Promise.resolve({ done: true })
      : Promise.resolve({ done: false, value: enc.encode(chunks[i++]) }); } }; } } });
}

/* ══════════ 抠出前端整块（iq 助手 + 涌现编排器），真跑 ══════════ */
const a = html.indexOf("var iqCard=null");
const b = html.indexOf("function renderSources(");
if (a < 0 || b <= a) { console.log("FAIL 抠不出前端块（锚点变了）"); process.exit(1); }
const clientSrc = html.slice(a, b);
function mkClient(turns) {
  const fn = new Function("document", "fetch", "keyMode", "vendor", "turns", "originQ", "buildHist",
    "flashAsk", "esc", "asking", "papering", "distilling", "brief", "flashed",
    clientSrc + "\nreturn {doEmerge:doEmerge, pickWays:pickWays, viewsText:viewsText, paradigmName:paradigmName,"
    + "iqComposite:iqComposite, pyRound:pyRound, getBrief:function(){return brief;}, getParadigms:function(){return paradigms;}};");
  const flashed = [];
  const api = fn(doc, fakeFetch, "sys", "ds", turns,
    () => (turns[0] || {}).q || "", (full) => turns.map(t => ({ q: t.q, a: (t.a || "").slice(0, full ? 2600 : 1600) })),
    (m) => flashed.push(m), (s) => String(s), false, false, false, "", flashed);
  api.flashed = flashed;
  return api;
}
const TURNS = [
  { q: "AI 时代课堂里的沉默是怎么回事", a: "观点一：沉默是评价场的结构产物。……\n观点二：沉默是差异被反复抹平后的结果。……\n观点三：沉默只有在师生共处的关系场里才成立。……" },
  { q: "那匿名提问能解决吗", a: "观点一：能，评价一撤沉默就退。\n观点二：不能，抹平是长期沉积的。\n观点三：要看关系场还在不在。" },
  { q: "有没有反例", a: "观点一：有，翻转课堂。\n观点二：那不是反例。\n观点三：得看场。" },
];

/* ══════════ 一、正常路径 ══════════ */
say("\n━━━ 一、正常路径：三轮问对 → 三路碰撞 → 三次盲评 → 择优 → 综合提炼 ━━━");
SCRIPT = {
  collide: [PARADIGM("评价在场性"), PARADIGM("可归因风险"), PARADIGM("发言的可撤回性")],
  iq: [CARD(128, 132, 120, 118, 126, "停在一阶边缘", true),
       CARD(133, 141, 129, 131, 138, "分离设计成立", true),
       CARD(126, 130, 122, 116, 124, "只换了名字", true)],
  synth: "一、最终承重命题：课堂沉默不是知识缺口，而是可归因风险。" + "……".repeat(200),
};
captured.length = 0;
const C = mkClient(TURNS);
C.doEmerge().then(function () {
  const cs = captured;
  const col = cs.filter(x => x.mode === "collide"), iqs = cs.filter(x => x.mode === "iq"), sy = cs.filter(x => x.mode === "synth");

  say("\n  ▸ 调用序列：" + cs.map(x => x.mode).join(" → "));
  ok(cs.length === 7, "一次涌现＝3 碰撞 + 3 盲评 + 1 提炼 ＝ 7 次调用（十轮问对另算）");
  ok(col.length === 3 && iqs.length === 3 && sy.length === 1, "三环调用数正确");

  say("\n  ▸ 客户端→worker 的字段契约");
  ok(col.every(x => x.q && x.origin && x.views && x.way >= 1 && x.way <= 6), "collide 带齐 q/origin/views/way");
  ok(new Set(col.map(x => x.way)).size === 3, "三路用的是三种不同撞法");
  ok(col[0].views.indexOf("观点一") > 0 && col[0].views.indexOf("〔第3轮〕") > 0, "views 汇总了全部轮次的三观点");
  ok(iqs.every(x => x.text && x.text.length > 200 && !x.views), "盲评只送稿子本身，不送问对上下文（保持匿名来稿）");
  ok(sy[0].winner && sy[0].others && sy[0].cards && Array.isArray(sy[0].hist), "synth 带齐 winner/others/cards/hist");

  say("\n  ▸ 择优");
  const ps = C.getParadigms();
  say("    三个典范得分：" + ps.map(p => C.paradigmName(p.text) + "=" + p.total).join("　"));
  ok(ps.length === 3 && ps.every(p => p.total > 0), "三个典范都拿到了分");
  ok(ps[0].total === 125 && ps[1].total === 135 && ps[2].total === 124, "分数＝页面按权重算（125/135/124，与 score.py 逐字同值）");
  ok(sy[0].winner.indexOf("可归因风险") === 0, "胜出的是最高分那个，不是第一个撞出来的");
  ok(sy[0].others.indexOf("评价在场性") > 0 && sy[0].others.indexOf("发言的可撤回性") > 0, "两个落选典范都进了提炼（零件可回收）");
  ok(sy[0].others.indexOf("创新智商 125") > 0, "落选典范带着自己的分进去，提炼时知道差在哪");
  ok(/胜出/.test(sy[0].cards) && /未交手的最近邻：Merton/.test(sy[0].cards), "评分卡摘要标了胜出方并带出未交手最近邻");
  ok(/\[I\]/.test(sy[0].cards), "扣分记录逐条进了提炼（第九栏「评分卡开出的作业」的原料）");

  say("\n  ▸ 出口");
  ok(C.getBrief().length > 300, "综合提炼成为论文入口 brief（成文一篇直接吃它）");
  ok(els.briefWrap.classList.has("show") && els.emergeActs.classList.has("show"), "两块面板都亮了");
  ok(/胜出/.test(els.emergeStat.textContent), "状态行报出了胜出典范");

  /* ══════════ 二、不够创新 → 换方式重来 ══════════ */
  say("\n━━━ 二、创新检查不合格：换碰撞方式重来一次 ━━━");
  const usedFirst = col.map(x => x.way).sort().join();
  SCRIPT = { collide: [PARADIGM("甲"), PARADIGM("乙"), PARADIGM("丙")],
    iq: [CARD(120, 122, 118, 112, 118, "一阶", true), CARD(121, 123, 119, 113, 119, "一阶", true), CARD(122, 124, 120, 114, 120, "一阶", true)],
    synth: "一、最终承重命题：……" + "……".repeat(200) };
  captured.length = 0;
  return C.doEmerge(true).then(function () {
    const col2 = captured.filter(x => x.mode === "collide");
    const usedSecond = col2.map(x => x.way).sort().join();
    say("    第一次抽到：" + usedFirst + "　第二次抽到：" + usedSecond);
    ok(usedFirst !== usedSecond, "重来抽到的是另外三种撞法——真的换了方式");
    ok((usedFirst + "," + usedSecond).split(",").sort().join() === "1,2,3,4,5,6", "两轮合起来正好把六种撞法用完，无重复");
    ok(/未过 135/.test(els.emergeStat.textContent), "三个都没过 135 时，状态行明说并提示可再撞");
    ok(C.getBrief().length > 300, "即便没过 135，仍照常交出综合提炼（不拦路，由人决定）");

    /* ══════════ 三、故障路径 ══════════ */
    say("\n━━━ 三、故障路径：单路失败 / 全挂 / 评分卡坏了 / 提炼过短 ━━━");
    const C3 = mkClient(TURNS);
    SCRIPT = { collide: [new Error("配额耗尽"), PARADIGM("丁"), PARADIGM("戊")],
      iq: [CARD(130, 136, 128, 126, 132, "尚可", true), CARD(125, 128, 122, 118, 124, "偏弱", true)],
      synth: "一、最终承重命题：……" + "……".repeat(200) };
    captured.length = 0;
    return C3.doEmerge().then(function () {
      ok(C3.getParadigms().length === 2, "单路失败：另外两路照常跑完，不拖垮全局");
      ok(captured.filter(x => x.mode === "iq").length === 2, "只对真撞出来的典范做创新检查");
      ok(captured.filter(x => x.mode === "synth")[0].winner.indexOf("丁") === 0, "两个里仍能择优");

      const C4 = mkClient(TURNS);
      SCRIPT = { collide: [new Error("x"), new Error("y"), new Error("z")], iq: [], synth: "" };
      captured.length = 0;
      return C4.doEmerge().then(function () {
        ok(C4.getParadigms().length === 0 && /✗/.test(els.emergeStat.textContent), "三路全挂：报错收场，不进盲评也不进提炼");
        ok(captured.filter(x => x.mode === "synth").length === 0, "全挂时不会拿空典范去做综合提炼");
        ok(C4.getBrief() === "", "全挂时不会污染论文入口 brief");

        const C5 = mkClient(TURNS);
        SCRIPT = { collide: [PARADIGM("己"), PARADIGM("庚"), PARADIGM("辛")],
          iq: ["这不是 JSON，是一段寒暄。", CARD(131, 138, 127, 129, 134, "好", true), "```json\n{坏掉的\n```"],
          synth: "太短" };
        captured.length = 0;
        return C5.doEmerge().then(function () {
          const ps5 = C5.getParadigms();
          ok(ps5[0].total === 0 && ps5[2].total === 0 && ps5[1].total === 132, "评分卡解析失败的记 0 分，不打崩流程");
          ok(captured.filter(x => x.mode === "synth")[0].winner.indexOf("庚") === 0, "唯一评上分的那个胜出");
          ok(C5.getBrief() === "" && /过短/.test(els.briefStat.textContent), "提炼过短即作废，绝不让半成品当论文入口");

          const C6 = mkClient([TURNS[0]]);
          captured.length = 0;
          C6.doEmerge();
          ok(captured.length === 0 && /至少完成两轮/.test(C6.flashed.join("")), "少于两轮直接挡回，不空烧调用");

          /* ══════════ 四、worker 侧：用捕获到的真实 payload 跑 worker 分支 ══════════ */
          say("\n━━━ 四、worker 侧：拿客户端真发出的 payload 跑 worker 的分支 ━━━");
          const wa = wk.indexOf('if (mode === "collide") {'), wc = wk.indexOf('else if (mode === "distill")');
          const seg = wk.slice(wa, wc);
          const runW = (mode, body) => new Function("mode", "body", "q", "ctxText", "neigong", "reflect", "histTxt",
            'let MAXTOK=0,sys="",usrOverride="";\n' + seg + "\nreturn {MAXTOK,sys,usrOverride};")(
            mode, body, body.q, "《站内资料》若干", "内功正文", "心得正文", "〔第1轮〕…");
          const colBody = { mode: "collide", q: "问", origin: "缘起之问", views: "观点一：A\n观点二：B\n观点三：C", way: 5 };
          const W1 = runW("collide", colBody);
          ok(/【承重命题】/.test(W1.sys) && /【两条证伪条件】/.test(W1.sys) && /本次碰撞方式/.test(W1.sys) && W1.MAXTOK === 3200,
    "collide 分支跑通：典范骨架与撞法指令都在，MAXTOK=3200");
          ok(W1.sys.indexOf("内功正文") === 0 && W1.sys.indexOf("心得正文") > 0, "碰撞装了内功＋心得（高超智慧）");
          ok(/换母学科/.test(W1.sys) && !/两两对撞】/.test(W1.sys.split("【本次碰撞方式")[1] || ""), "way=5 只注入第五式，不串味");
          ok(W1.usrOverride.indexOf("观点一：A") > 0 && W1.usrOverride.indexOf("缘起之问") > 0, "三观点与缘起之问都进了用户消息");
          [1, 2, 3, 4, 6].forEach(w => {
            const W = runW("collide", Object.assign({}, colBody, { way: w }));
            ok(/【本次碰撞方式/.test(W.sys), "way=" + w + " 有对应指令段");
          });
          const Wbad = runW("collide", Object.assign({}, colBody, { way: 99 }));
          ok(/【本次碰撞方式/.test(Wbad.sys), "way 越界被钳回 1–6，不会拼出 undefined");

          const syBody = { mode: "synth", q: "问", origin: "缘起之问", winner: "胜出典范正文", others: "落选甲\n落选乙", cards: "评分卡摘要" };
          const W2 = runW("synth", syBody);
          ok(/一、最终承重命题/.test(W2.sys) && /十、明确不写什么/.test(W2.sys) && W2.MAXTOK === 5200,
    "synth 分支跑通：十栏首尾都在，MAXTOK=5200");
          ok(W2.sys.indexOf("内功正文") === 0, "综合提炼也装内功");
          ok(W2.usrOverride.indexOf("胜出典范正文") > 0 && W2.usrOverride.indexOf("落选甲") > 0
            && W2.usrOverride.indexOf("评分卡摘要") > 0 && W2.usrOverride.indexOf("〔第1轮〕") > 0,
            "胜出典范＋落选典范＋评分卡＋整场问对，四样都送到了");

          const ta = wk.indexOf('if (body.tri === true && mode === "answer")');
          const tseg = wk.slice(ta, wk.indexOf("\n  }", ta) + 4);
          const T = new Function("body", "mode", 'let sys="底座";\n' + tseg + "\nreturn sys;");
          ok(T({ tri: true }, "answer").indexOf("观点一：") > 0, "tri=true 时三观点纪律被追加到 sys");
          ok(T({}, "answer") === "底座" && T({ tri: true }, "paper") === "底座", "不开涌现档、或非问答模式，一字不加");

          /* ══════════ 五、下游：入口资料的两种来源不许指错栏 ══════════ */
          say("\n━━━ 五、下游：涌现档十栏 vs 提炼档九栏，成文一篇按来源发指令 ━━━");
          const pa = wk.indexOf('const brief = String(body.brief');
          /* base 是一条 + 串起来的长表达式；切到「硬性纪律」那个字符串的开引号前，
             再自己补一个 ""; 把表达式收尾——否则切出来的是半截字符串字面量。 */
          const pb = wk.indexOf('\n        + "硬性纪律：① 【用二阶碰撞法造一篇典范文', pa);
          const pseg = wk.slice(pa, pb) + '\n        + "";';
          const runP = (kind) => new Function("body", "neigong", "reflect",
            'const q="";\n' + pseg + '\nreturn base;')({ brief: "入口资料正文", briefKind: kind }, "内功", "心得");
          const Bs = runP("synth"), Bd = runP("distill");
          ok(/涌现档·十栏/.test(Bs) && /提炼档·九栏/.test(Bd), "两种来源各走各的指令段");
          ok(/〔九、评分卡开出的作业〕是硬账/.test(Bs), "十栏：评分卡的账要在论文里逐条清掉");
          ok(/〔三、两个落选典范的可回收零件〕/.test(Bs) && /至少要装上一件/.test(Bs), "十栏：落选零件至少装一件");
          ok(!/第三栏（候选承重命题）/.test(Bs), "十栏不会再被按九栏的栏号指挥（旧版这里五条指令有四条指错地方）");
          ok(/〔三、候选承重命题〕/.test(Bd) && /〔四、反复被触到的分离点〕/.test(Bd), "九栏的老指令一字不丢");
          ok(/〔一、最终承重命题〕/.test(Bs) && /盲评分不等于写成了论文/.test(Bs), "十栏：起跑线是最终承重命题，且点破分数不等于论文");
          const Bnone = new Function("body", "neigong", "reflect", 'const q="";\n' + pseg + '\nreturn base;')({}, "内功", "心得");
          ok(!/论文入口资料/.test(Bnone), "无入口资料时（单轮直接成文）一字不加，老路径不受影响");
          ok(/briefKind:briefKind/.test(html), "客户端把 briefKind 随成文请求带上");
          ok(/brief=String\(t\|\|''\)\.trim\(\); briefKind='synth'/.test(html), "综合提炼落地时标记为 synth");
          ok(/brief=acc\.trim\(\); briefKind='distill'/.test(html), "提炼档落地时标记为 distill");

          say("\n━━━ 六、现场清理与前置提醒 ━━━");
          ok(/briefKind='distill'; paradigms=\[\]; emergeUsed=\[\]/.test(html), "清空重来会一并清掉牌堆与典范（新题目不会抽到上一题的剩牌）");
          ok(/triRounds<2/.test(html) && /没有三观点可撞/.test(html), "轮次里没有三观点时会先警告再跑");

          say("\n" + (FA ? "✗ " : "✓ ") + P + " PASS / " + FA + " FAIL");
          process.exit(FA ? 1 : 0);
        });
      });
    });
  });
}).catch(function (e) { console.log("HARNESS ERROR: " + (e && e.stack || e)); process.exit(1); });
