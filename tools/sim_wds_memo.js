/* 只测这一件事：与WDS对话新增的「用户RAG系统（全局记忆）」——
   把本机每一场历史对话各压成一条摘要，答题前在本机按当前问题挑出最相关的几条垫进当轮提问。

   五组断言：
   ① 存储层：DB 升到 v2、新建 memos/kv 两仓而不动既有对话；人工删一场连记忆一起删，自动淘汰只丢原文；
   ② 服务端 /api/wds/memo：**结构化短输出必须降档**（满功率是这条链路上反复吃过的亏）、自带短截止、
      独立配额桶（一次批量更新不许吃掉当天的对话额度）、宽松解析、字段有上限、一个字不落盘；
   ③ 注入纪律：umem 有硬上限、只挂当轮 user 消息（不进可缓存的 system）、并从历史预算里扣掉；
   ④ 本机检索的**行为实测**：相关的排前面、不相关的被阈值挡掉、排除当前这一场、topK 与开关生效、总量截断；
   ⑤ 两端常量对齐（客户端截断口径不许比服务端上限还宽）。
   全部对着真源码，不复制平行实现。 */
"use strict";
const fs = require("fs");
const ROOT = __dirname + "/..";
const W = fs.readFileSync(ROOT + "/src/worker.js", "utf8");
const S = fs.readFileSync(ROOT + "/public/assets/wds-store.js", "utf8");
const PAGE = fs.readFileSync(ROOT + "/public/taste/sde-dialogue/index.html", "utf8");
const CHAT = fs.readFileSync(ROOT + "/public/wds-mode.js", "utf8");
const MOD = fs.readFileSync(ROOT + "/public/assets/wds-memo.js", "utf8");   // 引擎只有这一份实现
const STORE = fs.readFileSync(ROOT + "/public/assets/wds-store.js", "utf8");
let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };
const num = (re, src) => Number((( src || W).match(re) || [])[1]);

/* ── ① 存储层 ── */
console.log("\n[一] 本机存储：新开两个仓，既有对话一条不动");
{
  ok(/var DB_NAME = "wds-store", DB_VER = 2, ST = "convos", MEMO = "memos", KV = "kv";/.test(S), "DB 升到 v2，并给记忆与画像各开一个仓");
  ok(/if \(!d\.objectStoreNames\.contains\(ST\)\)/.test(S), "升级时 convos 仓照旧只在缺失时才建——既有对话不会被重建覆盖");
  ok(/if \(!d\.objectStoreNames\.contains\(MEMO\)\)/.test(S) && /om\.createIndex\("agent_updated"/.test(S), "memos 仓与它的按时间索引都建了");
  ok(/if \(!d\.objectStoreNames\.contains\(KV\)\) d\.createObjectStore\(KV, \{ keyPath: "k" \}\)/.test(S), "kv 仓（画像与开关）建了");
  ok(/function tx\(mode, fn\) \{ return txs\(ST, mode, fn\); \}/.test(S), "老的 tx 原样保留，只是转调泛化后的 txs——老调用点零改动");
  const rm = S.slice(S.indexOf("function remove(id)"), S.indexOf("function list(agent, scope)"));
  ok(/memoDel\(id\)/.test(rm), "人工删除一场对话时，连它那条记忆一起删（读者说删就删干净）");
  const tr = S.slice(S.indexOf("function trim(agent)"), S.indexOf("/* ---------- 用户RAG"));
  ok(!/memoDel|memoClear/.test(tr), "但**自动淘汰（超 60 场）不动记忆**——摘要活得比原文长，这正是长期记忆的意义");
  const cl = S.slice(S.indexOf("function clear(agent, scope)"), S.indexOf("function trim(agent)"));
  ok(/memoClear\(agent\)/.test(cl) && /scope === undefined/.test(cl), "整体清空该智能体时连记忆一起清；限定 scope 时只清对应的几条");
  ["memoFp", "memoPut", "memoGet", "memoDel", "memoList", "memoClear", "kvGet", "kvSet"]
    .forEach((n) => ok(new RegExp("\\n\\s+" + n + ": " + n + "[,\\n]").test(S), "对外导出了 " + n));
}

/* ── ② 服务端 /api/wds/memo ── */
console.log("\n[二] 摘要端点：它是配菜，不许占正菜的档位与时钟");
{
  const seg = W.slice(W.indexOf('if (url.pathname === "/api/wds/memo")'), W.indexOf('// RAG_SUBREQUEST — /api/wds/rag'));
  ok(seg.length > 500, "路由 /api/wds/memo 在（" + seg.length + " 字符）");
  ok(/const VC = \{ url: WDS_VENDORS\[vd\]\.url, model: WDS_VENDORS\[vd\]\.model, name: WDS_VENDORS\[vd\]\.name \};/.test(seg) && !/wdsTopVC/.test(seg),
     "用不带 top 标记的 VC——**结构化短输出绝不跑满功率**（满功率会把预算烧在推演上、正文 0 字）");
  // 行为实测：同样的构造喂进 wdsTopBody，确认请求体里没有 thinking / reasoning_effort
  {
    const s2 = W.slice(W.indexOf("function wdsTopBody"), W.indexOf("// 五家基底"));
    // wdsMiniSplit 在切片之外（2026-08-29 MiniMax 那刀加的），给个空桩即可——这里要验的是档位，不是它
    const box = new Function("function wdsMiniSplit(){}\n" + s2 + "\nreturn { wdsTopBody };")();
    const LC = { url: "u", model: "m", name: "n" };
    const body = box.wdsTopBody(LC, { model: "m" });
    ok(!body.reasoning_effort && !body.thinking, "行为实测：这个档位发出去的请求体里确实没有 thinking / reasoning_effort");
  }
  ok(/llmText\(VC, KEY, sys, usr, mode === "profile" \? 1800 : \(mode === "proj" \? 2000 : 1600\), MEMO_MS, _stat\)/.test(seg), "预算按'它本来该写多长'给（摘要 1600 / 归并 2000 / 画像 1800），并把短截止与状态回执传进 llmText");
  const ms = num(/const MEMO_MS = (\d+)/);
  ok(ms > 0 && ms <= 50000, "MEMO_MS = " + ms + " 毫秒（远小于正菜的 55000：一场卡住不许拖死整批）");
  ok(/wdsBucket\("memo", ip, KEY\)/.test(seg), "走独立配额桶 memo");
  ok(!/wdsBucket\("dlg"/.test(seg), "**不吃对话桶**——一次全量更新几十场，不该让人当天不能再聊天");
  const pd = num(/const WDS_MEMO_PER_DAY = (\d+)/), pm = num(/WDS_MEMO_PER_DAY = \d+, WDS_MEMO_PER_MIN = (\d+)/);
  ok(pd >= 200 && pm >= 10, "记忆额度 " + pd + "/天 · " + pm + "/分钟（批活儿要够用）");
  ok(/looseJSON\(out\)/.test(seg), "用 looseJSON 宽松解析（思考模型偶发前后缀说明文字，硬 JSON.parse 会白丢一条）");
  ok(/gist \|\| ""\)\.slice\(0, 120\)/.test(seg) && /points \|\| ""\)\.slice\(0, 1200\)/.test(seg) && /\.slice\(0, 20\)\.map/.test(seg),
     "回给客户端的每个字段都有上限（主旨/要点/关键词），不放任基底写多长算多长");
  ok(/KEY\.length < 8/.test(seg) && /need_key/.test(seg), "纯 BYOK：没带 Key 直接回 need_key");
  ok(/_stat\.status === 401 \|\| _stat\.status === 402 \|\| _stat\.status === 429/.test(seg) && /code: "bad_key"/.test(seg),
     "Key 用不了是硬错、单独报出来——否则批量更新会拿同一把坏 Key 连撞几十场，每场只回一句没信息量的'再点一次'");
  ok(/async function llmText\(VC, KEY, sys, usr, maxTok, msTimeout, stat\)/.test(W) && /if \(stat\) stat\.status = resp\.status;/.test(W),
     "llmText 的状态回执是**可选参数**：不传就与从前完全一样，站内其余十几处调用点零改动");
  ok(!/env\.(COMMENTS|ASK_LIMITER)\.get\([^)]*\)\.fetch\(new Request\("https:\/\/do/.test(seg) && !/\.put\(/.test(seg),
     "整段里没有任何写库动作——**摘要只回客户端，本站一个字不落盘**");
  ok(/MEMO_IN_MAX/.test(seg), "喂进来的对话文本有硬上限 MEMO_IN_MAX");
  const inmax = num(/const MEMO_IN_MAX = (\d+)/);
  ok(inmax >= 8000 && inmax <= 40000, "MEMO_IN_MAX = " + inmax + "（一整场对话要装得下，又不能无边）");
  ok(/mode === "profile"/.test(seg), "两种模式：一条摘要 / 汇总成用户画像");
}

/* ── ③ 注入纪律 ── */
console.log("\n[三] 垫进去的记忆：有上限、挂当轮、扣预算");
{
  const cap = num(/const UMEM_MAX = (\d+)/);
  ok(cap > 0 && cap <= 12000, "UMEM_MAX = " + cap + "（记性不能以牺牲本场现场为代价）");
  ok(/const umem = b\.guide \? String\(b\.umem \|\| ""\)\.slice\(0, UMEM_MAX\) : "";/.test(W), "答题端点收 umem，截断到上限；非 guide 入口（陪读）一律不注入");
  ok(/content: \(focus \? [^\n]*\) \+ UMEM \+ LONGASK \}\)/.test(W), "UMEM 拼在**当轮 user 消息**上");
  const sysLine = W.slice(W.indexOf("const sys = b.guide ? WDS_DIALOGUE_SYS"), W.indexOf("const sys = b.guide ? WDS_DIALOGUE_SYS") + 240);
  ok(!/UMEM|umem/.test(sysLine), "**不进 system**——system 是可被基底前缀缓存的固定段，每轮换内容会把缓存打散");
  ok(/WDS_GUIDE_HIST_BUDGET - docText\.length - siteCtx\.length - UMEM\.length/.test(W), "历史预算把 UMEM 占用扣掉了（三者相加仍钳在总预算内）");
  ok(/不要复述它，也不要假装记得这里面没写的事/.test(W), "提示语讲明这是摘要不是原文：不许照着复述、不许假装记得没写的事");
}

/* ── ④ 本机检索：行为实测 ── */
console.log("\n[四] 检索在本机做：打分、阈值、排除本场、topK、截断");
{
  // 引擎已抽成共享模块 /assets/wds-memo.js —— 这里跑**模块本体**（页面只是薄委托，见 [五]）
  ok(/window\.WDSMemo = \{/.test(MOD) && /create: create/.test(MOD), "共享模块导出 WDSMemo.create 与纯函数");
  const mk = (sw, k, prof, sessId) => {
    const LS = { _d: {}, getItem(x) { return x === "sde_wds_umem_on" ? (sw ? "1" : "0") : x === "sde_wds_umem_k" ? String(k) : (this._d[x] || null); }, setItem(x, v) { this._d[x] = v; } };
    const win = {};
    new Function("window", "localStorage", "document", "fetch", MOD)(win, LS, { }, () => Promise.resolve({ json: () => Promise.resolve({}) }));
    const store = { stamp: () => "今天 10:00" };
    const eng = win.WDSMemo.create({ store: store, agent: "wds-dialogue", currentId: () => sessId || "" });
    const UM = eng.state; UM.ready = true; UM.profile = prof || "";
    // 老断言用的是 um* 名字，这里做一层名字映射，断言正文一个字不动
    const box = { umOn: eng.on, umTopK: eng.topK, umNorm: win.WDSMemo.norm, umGrams: win.WDSMemo.grams,
                  umScore: win.WDSMemo.score, umPick: win.WDSMemo.pick, umRecall: eng.recall,
                  umFp: win.WDSMemo.fp, umPending: eng.pending };
    return { box, UM, win };
  };
  let win0 = null;
  const R = [
    { id: "c1", title: "创新智商怎么打分", gist: "谈创新智商五维评分与两条硬阈值", keys: ["创新智商", "五维", "提智"], points: "谈了 S/D/E/I/F 五个维度与 150、160 两条线。", updatedAt: 3 },
    { id: "c2", title: "内卷与出路", gist: "谈内卷的发生学机制与突围条件", keys: ["内卷", "突围"], points: "内卷是差异序列被锁死后的空转。", updatedAt: 2 },
    { id: "c3", title: "今天天气", gist: "闲聊", keys: ["天气"], points: "没谈出什么。", updatedAt: 1 },
  ];

  {
    const { box, UM } = mk(true, 3, "");
    UM.memos = R;
    const picked = box.umPick("创新智商这套五维评分靠谱吗", UM.memos, 3, "");
    ok(picked.length >= 1 && picked[0].id === "c1", "问创新智商 → 《创新智商怎么打分》排第一（实测排序）");
    ok(!picked.some((r) => r.id === "c3"), "不相关的闲聊被阈值挡在外面");
    const p2 = box.umPick("内卷为什么突不出去", UM.memos, 3, "");
    ok(p2.length && p2[0].id === "c2", "换一个问题，命中随之改变（不是固定名次）");
    const p3 = box.umPick("创新智商五维", UM.memos, 3, "c1");
    ok(!p3.some((r) => r.id === "c1"), "**当前这一场被排除**——它的原文已逐字在上下文里，再塞摘要是浪费预算");
    const p4 = box.umPick("创新智商 内卷 五维 突围", UM.memos, 1, "");
    ok(p4.length === 1, "topK 生效（要 1 条就只给 1 条）");
    const none = box.umPick("量子色动力学的渐进自由", UM.memos, 3, "");
    ok(none.length === 0, "整场都不相关时宁可一条不给，也不硬凑");
  }
  {
    const { box, UM } = mk(false, 3, "你关心创新与评价制度");
    UM.memos = R;
    ok(box.umRecall("创新智商") === "", "开关关掉 → 一个字都不垫（与从前完全一样）");
  }
  {
    const { box, UM } = mk(true, 3, "你关心创新与评价制度");
    UM.memos = R;
    const t = box.umRecall("创新智商五维评分");
    ok(/关于我/.test(t) && /创新智商/.test(t), "开着时：画像 + 命中的条目一起垫进去");
    ok(t.indexOf("要点：") > 0, "条目里带上要点，不只有一句主旨");
  }
  {
    const { box, UM, win } = mk(true, 5, "画".repeat(2000)); win0 = win;
    UM.memos = [{ id: "x", title: "长", gist: "创新智商", keys: ["创新智商"], points: "点".repeat(9000), updatedAt: 9 }];
    const t = box.umRecall("创新智商");
    const CAPC = win0.WDSMemo ? win0.WDSMemo.CAP : 7000;
    const C0 = win0.WDSMemo.CAPS;
    ok(t.length <= CAPC + 8, "总量仍钳在上限内（实测 " + t.length + " 字符 ≤ " + CAPC + "）");
    // 三层之后，超量先被**各段自己的预算**挡住，全局那一刀是兜底而不是主力
    const seg3 = (t.split("【按这一问找出的旧事】")[1] || "");
    ok(seg3 && seg3.length <= C0.injPick + 40, "9000 字的要点被检索段自己的预算挡在 " + C0.injPick + " 字（实测该段 " + seg3.length + "）");
    const seg1 = t.split("\n【")[0];
    ok(seg1.length <= C0.injLong + 40, "2000 字的画像被长期段自己的预算挡在 " + C0.injLong + " 字（实测该段 " + seg1.length + "）");
    ok(/s\.length > UMEM_CAP \? s\.slice\(0, UMEM_CAP\) \+ "…（余下略）"/.test(MOD), "全局那一刀仍留着兜底，截断处仍明标'余下略'");
  }
  {
    const { box, UM } = mk(true, 3, "");
    UM.metas = [{ id: "a", n: 4, updatedAt: 100 }, { id: "b", n: 6, updatedAt: 200 }, { id: "c", n: 1, updatedAt: 300 }];
    UM.memos = [{ id: "a", fp: "4:100" }, { id: "b", fp: "2:50" }];
    const pend = box.umPending();
    ok(pend.length === 1 && pend[0].id === "b", "待更新只认'又聊长了的那些'：a 指纹未变不重做、c 太短不做、b 指纹变了要重做");
  }
}

/* ── ⑤ 两端对齐与接线 ── */
console.log("\n[五] 两端对齐与接线");
{
  const cIn = num(/var MEMO_IN = (\d+)/, MOD), sIn = num(/const MEMO_IN_MAX = (\d+)/);
  ok(cIn === sIn, "客户端截断口径 " + cIn + " 与服务端上限 " + sIn + " 对齐（客户端不许比服务端还宽，否则白发一趟被截）");
  const cCap = num(/var UMEM_CAP = (\d+)/, MOD), sCap = num(/const UMEM_MAX = (\d+)/);
  ok(cCap === sCap, "注入上限两端对齐（" + cCap + "）");
  ok(/id="bmem"[^>]*hidden/.test(PAGE), "按钮默认隐藏——本机存不了记录时（隐私模式）不该出现一个点了没反应的按钮");
  ok(/stMakeSession\(\); stShowBtn\(\); umShowBtn\(\);/.test(PAGE), "存储就绪后才亮出「记忆更新」按钮");
  ok(/umem: umRecall\(q\)/.test(PAGE), "答题请求确实带上了本机挑出的记忆");
  ok(/mode: "one"/.test(MOD) && /mode: "profile"/.test(MOD), "两种更新都在共享模块里：逐场摘要 + 重炼画像");
  ok(/umRefreshProfile\(kv, say\)/.test(PAGE) && /profileRefresh\(kv, say\)/.test(PAGE), "对话页的画像更新委托给模块");
  ok(/r\.code === "rate" \|\| r\.code === "bad_key"/.test(PAGE), "撞上限流、或 Key 用不了时**停下并说明**，不拿同一把坏 Key 连撞几十场");
  ok(/UM\.stop/.test(PAGE) && /剩下的下次接着做/.test(PAGE), "批量更新可中断，且已做好的不丢、下次接着做");
  ok(/摘要与画像只存在你这台设备的浏览器里/.test(PAGE), "面板里把'存在哪、发给谁'讲清楚了");
  ok(/记忆更新/.test(PAGE) && /⌾ 记忆更新/.test(PAGE), "顶栏按钮文案在");
}

/* ── ⑥ 只有一份实现：两个页面都委托给共享模块（2026-07-30 抽模块时立的） ── */
console.log("\n[六] 引擎只有一份：两个调用方都委托出去，谁也没有第二套");
{
  ok(!/function umScore\(q, rec\) \{\n    var qg/.test(PAGE), "对话页不再自带打分实现");
  ok(/window\.WDSMemo\.score\(q, rec\)/.test(PAGE) && /window\.WDSMemo\.pick\(/.test(PAGE), "对话页的 umScore/umPick 是薄委托");
  ok(/sc\.src = "\/assets\/wds-memo\.js(\?v=[a-z0-9]+)?"/.test(PAGE), "对话页加载共享模块（带不带 cachebust 都算）");
  ok(/WDSMemo\.create\(\{/.test(PAGE) && /agent: "wds-dialogue"/.test(PAGE), "对话页按自己的 agent 建实例");
  ok(/sc\.src = "\/assets\/wds-memo\.js(\?v=[a-z0-9]+)?"/.test(CHAT), "问WDS 也加载同一个模块（不是抄一份）");
  ok(/agent: AGENT_CHAT, agents: "all"/.test(CHAT) && /AGENT_CHAT = PROF_ID \? \("wds-chat:" \+ PROF_ID\) : "wds-chat"/.test(CHAT), "问WDS 的记忆池是**跨智能体**的（真·全局记忆）");
  ok(/profileKey: "profile:global"/.test(CHAT), "问WDS 用全局画像键");
  ok(/umem: memRecall\(q\)/.test(CHAT), "问WDS 每问都带上按这一问召回的记忆");
  ok(/function memListAll|memoListAll/.test(STORE) && /listAll: listAll/.test(STORE), "store 补了跨智能体的两个列表（纯新增，旧调用方零影响）");
  ok(/memoList: memoList,/.test(STORE), "memoList 原样保留");
  // 行为实测：跨智能体的池子确实两家都取
  const win = {}; const calls = [];
  new Function("window", "localStorage", "document", "fetch", MOD)(win, { getItem: () => null, setItem() {} }, {}, () => Promise.resolve({ json: () => Promise.resolve({}) }));
  const store = {
    stamp: () => "今天", memoList: (a) => { calls.push("memoList:" + a); return Promise.resolve([{ id: "d1", agent: "wds-dialogue", gist: "甲", updatedAt: 1 }]); },
    memoListAll: () => { calls.push("memoListAll"); return Promise.resolve([{ id: "d1", agent: "wds-dialogue", gist: "甲", updatedAt: 1 }, { id: "c1", agent: "wds-chat", gist: "乙", updatedAt: 2 }]); },
    list: (a) => { calls.push("list:" + a); return Promise.resolve([]); },
    listAll: () => { calls.push("listAll"); return Promise.resolve([{ id: "d1", n: 4, updatedAt: 1 }, { id: "c1", n: 4, updatedAt: 2 }]); },
    kvGet: () => Promise.resolve(null),
  };
  const g = win.WDSMemo.create({ store: store, agent: "wds-chat", agents: "all", currentId: () => "" });
  const one = win.WDSMemo.create({ store: store, agent: "wds-dialogue", currentId: () => "" });
  return_check: {
    g.refresh(function () {
      ok(calls.indexOf("memoListAll") >= 0 && calls.indexOf("listAll") >= 0, "agents:'all' → 取全部智能体的记忆与会话");
      ok(g.state.memos.length === 2, "两个智能体的记忆合成一个池子（实得 " + g.state.memos.length + " 条）");
      one.refresh(function () {
        ok(calls.indexOf("memoList:wds-dialogue") >= 0, "不传 agents 时仍只取本智能体（对话页行为一字未变）");
        ok(one.state.memos.length === 1, "单智能体池子还是 1 条");
        tiers();
      });
    });
  }
}



function tiers() {
/* ── ⑦ 三层记忆（2026-09-01）：分层、存量、折叠、注入 ── */
console.log("\n[七] 三层：长期常驻 · 中期按线索 · 短期不归它管；存 10 万，每轮带 7 千");
{
  const win = {};
  new Function("window", "localStorage", "document", "fetch", MOD)(
    win, { getItem: () => null, setItem() {} }, {}, () => Promise.resolve({ json: () => Promise.resolve({}) }));
  const M = win.WDSMemo, C = M.CAPS;

  // —— 存量与注入是两个数（分层的全部意义）——
  ok(C.total === 100000, "存量上限 10 万字（C.total = " + C.total + "）");
  ok(C.long + C.mid <= C.total, "长期 " + C.long + " ＋ 中期 " + C.mid + " 不超过总量，余下的是折叠周转余量");
  ok(M.CAP === 7000, "每答注入 " + M.CAP + " 字 —— 与 10 万存量差一个半数量级，绝不整份喂进上下文");
  ok(C.injLong + C.injProj + C.injPick <= M.CAP, "三段注入预算相加 " + (C.injLong + C.injProj + C.injPick) + " ≤ 总上限，不会互相挤爆");
  const sCap = Number((W.match(/const UMEM_MAX = (\d+)/) || [])[1]);
  ok(sCap === M.CAP, "客户端注入上限与服务端 UMEM_MAX 对齐（" + sCap + "）");

  // —— 分线索：关键词重叠 ≥2 并进去，否则另起 ——
  const mk = (id, title, keys, at, points) => ({ id, title, keys, at, updatedAt: at, gist: title + "的主旨", points: points || "要".repeat(400), stance: "" });
  const R = [
    mk("m1", "创新智商怎么打分", ["创新智商", "五维", "提智"], 10),
    mk("m2", "五维评分再谈", ["创新智商", "五维", "阈值"], 20),
    mk("m3", "内卷与出路", ["内卷", "突围"], 30),
  ];
  let pj = M.assign(R, []);
  ok(pj.length === 2, "三场归成两条线索（实得 " + pj.length + "）：前两场关键词重叠 2 个，第三场自成一条");
  const big = pj.filter((p) => p.ids.length === 2)[0];
  ok(big && big.ids.indexOf("m1") >= 0 && big.ids.indexOf("m2") >= 0, "并进同一条的确实是 m1 与 m2");
  ok(M.overlap(M.keyset(R[0]), M.keyset(R[2])) === 0, "m1 与 m3 一个关键词都不重叠 —— 所以不该被并到一起");
  // 反向验证：只重叠 1 个不许并（阈值真的在起作用，不是碰巧）
  const one = M.assign([mk("a", "甲", ["创新智商", "别的"], 1), mk("b", "乙", ["创新智商", "另一个"], 2)], []);
  ok(one.length === 2, "只重叠 1 个关键词时**不并**（JOIN_MIN=" + C.joinMin + "）—— 阈值是真的，实得 " + one.length + " 条线索");
  // 可复算：同一批记忆算两次结果一样（否则每次刷新线索都会重排，面板上永远在跳）
  const again = M.assign(R, []);
  ok(JSON.stringify(again.map((p) => p.ids)) === JSON.stringify(pj.map((p) => p.ids)), "同一批记忆算两次，线索划分完全一致（可复算）");
  // 条目被删之后，线索里那个 id 也该消失
  const shrunk = M.assign([R[0], R[2]], pj);
  const total = shrunk.reduce((a, p) => a + p.ids.length, 0);
  ok(total === 2, "删掉一条记忆后线索里的 id 跟着消失（实得 " + total + " 个成员，不再虚高）");

  // —— 存量量尺与折叠 ——
  const puts = [];
  const store = { stamp: () => "今天", memoPut: (r) => { puts.push(r.id); return Promise.resolve(r); },
                  kvSet: () => Promise.resolve(), kvGet: () => Promise.resolve(null) };
  const eng = M.create({ store, agent: "wds-chat", agents: "all", currentId: () => "" });
  eng.state.ready = true;
  eng.state.memos = R; eng.state.projs = pj; eng.state.profile = "画像"; eng.state.facts = ["甲", "乙"];
  let z = eng.sizes();
  ok(z.long === 4 && z.mid > 1000, "量尺分层计数：长期 " + z.long + " 字（画像＋常驻要点）· 中期 " + z.mid + " 字（场条目＋线索）");
  ok(z.total === z.long + z.mid, "总量＝长期＋中期；短期不计（本场原文另有它自己的历史预算）");

  // 撑破中期上限 → 折叠
  const fat = [];
  for (let i = 0; i < 200; i++) fat.push(mk("f" + i, "第" + i + "场", ["创新智商", "五维"], i, "点".repeat(600)));
  const eng2 = M.create({ store, agent: "wds-chat", currentId: () => "" });
  eng2.state.ready = true; eng2.state.memos = fat; eng2.state.projs = M.assign(fat, []);
  const before = eng2.sizes().mid;
  ok(before > C.mid, "先撑破：中期实得 " + before + " 字 > 上限 " + C.mid);
  return_fold: {
    eng2.fold(function (n) {
      const after = eng2.sizes().mid;
      ok(n > 0 && after <= C.mid, "折叠把中期压回上限内（折了 " + n + " 场，" + before + " → " + after + "）");
      ok(after <= C.mid * C.foldTo + 2000, "一次折到 " + Math.round(C.foldTo * 100) + "%，不是刚过线就折、折完又过线");
      ok(eng2.state.memos.length === fat.length, "**折叠不删条目**：仍是 " + eng2.state.memos.length + " 条");
      const cut = eng2.state.memos.filter((m) => m.folded);
      ok(cut.length === n && cut.every((m) => m.gist && (m.keys || []).length), "被折的每一条都还留着主旨与关键词——仍检索得到");
      ok(cut.every((m) => m.points.length <= C.stub + 10), "要点压成 " + C.stub + " 字存根，且明标「已折叠」");
      ok(cut[0].points.indexOf("已折叠") > 0, "存根末尾写明它被折过，不假装是完整要点");
      const ids = fat.slice(0, n).map((m) => m.id);
      ok(ids.every((i) => cut.some((m) => m.id === i)), "先折的是**最旧的**那些场");
      ok(puts.length === n, "折叠只写回被折的那 " + n + " 条（不是整库重写）");

      // —— 注入：三段各自封顶，并且长期是常驻、中期按线索 ——
      const LS = { getItem: (x) => (x === "sde_wds_umem_on" ? "1" : x === "sde_wds_umem_k" ? "3" : null), setItem() {} };
      const w3 = {};
      new Function("window", "localStorage", "document", "fetch", MOD)(w3, LS, {}, () => Promise.resolve({ json: () => Promise.resolve({}) }));
      const e3 = w3.WDSMemo.create({ store, agent: "wds-chat", currentId: () => "" });
      e3.state.ready = true;
      // 再加一场：它自成一条线索，但带"阈值"，所以能被这一问从**线索之外**捞回来
      const R2 = R.concat([{ id: "m9", title: "阈值那条线", keys: ["阈值", "定线"], updatedAt: 5,
                             gist: "谈阈值怎么定阈值", points: "谈了阈值怎么定。", stance: "" }]);
      e3.state.memos = R2; e3.state.projs = w3.WDSMemo.assign(R2, []);
      e3.state.profile = "你关心创新与评价制度"; e3.state.facts = ["你在做创新智商这套评分", "你忌讳空口无凭"];
      const txt = e3.recall("创新智商的五维评分怎么定阈值");
      ok(/【长期记忆】/.test(txt) && /【当前这条线索】/.test(txt) && /【按这一问找出的旧事】/.test(txt), "三段都在，且各自打了标——基底看得出哪一段是常驻、哪一段是这一问召回的");
      ok(txt.indexOf("你在做创新智商这套评分") > 0, "长期常驻要点每轮都带（不经检索）");
      const nomatch = e3.recall("量子色动力学的渐进自由");
      ok(/【长期记忆】/.test(nomatch), "问一件完全不相干的事，长期层照样在——它是常驻的");
      ok(!/【当前这条线索】/.test(nomatch) && !/【按这一问找出的旧事】/.test(nomatch), "但中期与检索两段都不给——宁可不给，也不硬套一条不相干的线索");
      ok(txt.length <= w3.WDSMemo.CAP + 8, "三段合计仍钳在注入上限内（实测 " + txt.length + "）");
      // 中期段不重复检索段已给过的那几条
      const picked = (txt.split("【按这一问找出的旧事】")[1] || "");
      const projSeg = (txt.split("【当前这条线索】")[1] || "").split("【按这一问找出的旧事】")[0];
      const dup = R2.filter((r) => picked.indexOf("《" + r.title + "》") >= 0 && projSeg.indexOf("《" + r.title + "》") >= 0);
      ok(dup.length === 0, "同一场不会在两段里各出现一次（省下的预算留给别的）");
      // 开关关掉 → 三层一起噤声
      const LS0 = { getItem: (x) => (x === "sde_wds_umem_on" ? "0" : null), setItem() {} };
      const w4 = {};
      new Function("window", "localStorage", "document", "fetch", MOD)(w4, LS0, {}, () => Promise.resolve({ json: () => Promise.resolve({}) }));
      const e4 = w4.WDSMemo.create({ store, agent: "wds-chat", currentId: () => "" });
      e4.state.ready = true; e4.state.memos = R; e4.state.projs = w4.WDSMemo.assign(R, []);
      e4.state.profile = "画像"; e4.state.facts = ["甲"];
      ok(e4.recall("创新智商") === "", "开关关掉 → 三层一个字都不垫（与从前完全一样）");

      /* —— 服务端：中期归并那一档 —— */
      console.log("\n[八] 服务端 mode=proj：中期的「归并」，与逐场摘要同一条纪律");
      const seg = W.slice(W.indexOf('if (url.pathname === "/api/wds/memo")'), W.indexOf("// NBR_JUDGE"));
      ok(/b\.mode === "proj" \? "proj" : "one"/.test(seg), "三种模式：逐场摘要 / 项目归并 / 用户画像");
      ok(/const SYS_PROJ =/.test(seg) && /要写出先后/.test(seg), "归并提示语要求写出**先后**——只把几场拼在一起是白归并");
      ok(/一度……后改为……/.test(seg), "改过口的地方要留痕，不许直接删掉（记忆最怕的是悄悄改口）");
      ok(/凡这几场里没谈过的，一个字都不要补/.test(seg), "与逐场摘要同一条：不许补没谈过的");
      ok(/mode === "proj" \? 2000 : 1600/.test(seg), "归并要写 500 字，预算给到 2000（仍是结构化短输出，不跑满功率）");
      ok(/const VC = \{ url: WDS_VENDORS\[vd\]\.url/.test(seg) && !/wdsTopVC/.test(seg), "归并也走降档 VC —— 三种模式一视同仁");
      ok(/if \(!sum\) return J\(\{ ok: false/.test(seg), "归并出空结果时明说没成，不写一段空的进去");
      ok(/facts: \(Array\.isArray\(j\.facts\)/.test(seg), "画像多回一组 facts（长期层的常驻要点），且有条数与长度上限");
      ok(/只收跨多场反复出现、已经稳定下来的/.test(seg), "facts 的收录标准写死在提示语里：跨多场、已稳定；一两场的、还在变的、猜的，一律不收");
      ok(!/\.put\(/.test(seg), "整段仍无任何写库动作 —— 三种模式都只回客户端，本站一个字不落盘");

      /* —— 前端面板 —— */
      console.log("\n[九] 面板：三层看得见、容量看得见、折叠看得见");
      ok(/function tierHd\(k, sub\)/.test(CHAT), "三层各有小标题（层名 + 它凭什么在这一层）");
      ok(/memTL:|memTM:|memTS:/.test(CHAT), "三层文案齐（长期 / 中期 / 短期）");
      ok(/wdsm-memcap/.test(CHAT) && /capL\.style\.width = Math\.min\(100, z\.long/.test(CHAT) && /capLg\.innerHTML = lg/.test(CHAT), "容量条画的是真读数（两段宽度与文字都由 sizes() 的 z 喂），不是写死的数字");
      ok(/memCapFull/.test(CHAT) && /memInj/.test(CHAT), "折叠了多少场、每轮带多少字，都摆在面板上");
      ok(/MEM\.projSum\(kv, pj\.id, say\)/.test(CHAT), "每条线索给一个「归并」钮 —— 花的是读者自己的 Key，所以由他按");
      ok(/facts: MEM\.state\.facts/.test(CHAT) && /projects: MEM\.state\.projs/.test(CHAT), "导出把三层一起带走（画像 + 常驻要点 + 线索 + 场条目）");
      ok(/kvSet\(MEM\.projKey \|\| "proj:index", null\)/.test(CHAT), "清空时线索索引一起清，不留一排空线索");
      ok(/分线索、折叠、检索这三件全在你这台机器上做，不发一次调用/.test(CHAT), "面板讲明：哪几件是免费的本机动作，哪几件要花调用");

      /* —— ⑩ 2026-09-01：这一答带哪几层，由难度档定 —— */
      console.log("\n[十] 按档配给：一般情况只带长期，深了才翻线索与旧事");
      ok(/function recall3\(q\)/.test(MOD) && /recall3: recall3/.test(MOD), "模块把三段分开交出去（L/P/K），不再只有拼好的一串");
      ok(/z\.L = "【长期记忆】/.test(MOD) && /z\.P = "【当前这条线索】/.test(MOD) && /z\.K = "【按这一问找出的旧事】/.test(MOD), "三段各自成段，服务端才切得开");
      ok(/var INJ_PICK5 = 4500/.test(MOD) && /z\.K\.slice\(0, INJ_PICK\)/.test(MOD), "第 5 档才放宽到 4500；老口径 recall() 仍按 3000 截 —— 放宽不许顺手漏给所有路");
      {
        const m = W.match(/const MEM_BY_LV = \{[\s\S]*?\};/);
        ok(!!m, "服务端有一张按档配给表");
        const tbl = m ? m[0] : "";
        ok(/1: \{ L: 200,\s+P: 0,\s+K: 0 \}/.test(tbl), "第 1 档只留称呼层 200 字：一句「你好」不去翻旧账");
        ok(/2: \{ L: 2000, P: 0,\s+K: 0 \}/.test(tbl), "第 2 档（也是标准档）只带长期 —— 一般情况下就是长期记忆");
        ok(/3: \{ L: 2000, P: 1500, K: 0 \}/.test(tbl), "第 3 档加当前线索，仍不检索");
        ok(/4: \{ L: 2000, P: 1500, K: 3000 \}/.test(tbl), "第 4 档三层齐");
        ok(/5: \{ L: 2000, P: 1500, K: 4500 \}/.test(tbl), "第 5 档把检索那段放宽");
      }
      ok(/function wdsMemByGrade\(m, G\)/.test(W), "配给函数在");
      ok(/G\.why === "std"\) \? 2 : 4/.test(W), "标准档按第 2 档；定不了档的几条路（产线/对撞/看图/老客户端）按第 4 档＝老行为");
      ok(/\.join\("\\n"\)\.slice\(0, UMEM_MAX\)/.test(W), "配给完还要再硬截在 UMEM_MAX —— 三段各自封顶之外的最后一道");
      ok(/if \(umem3\) \{ memPick = wdsMemByGrade\(umem3, G\); umem = memPick\.text; \}/.test(W), "配给发生在**定完档之后**（自动档要等检索跑完才知道深浅）");
      ok(/let umem = String\(b\.umem \|\| ""\)/.test(W), "umem 改成可重写，否则按档配给根本装不进去");
      ok(/const umem3 = \(b && b\.umem3/.test(W) && /老客户端只递 umem 字符串 ⇒ 这里不介入/.test(W), "老客户端只递 umem ⇒ 一字不改走老路");
      ok(/mem: memPick \? \{ lv: memPick\.lv, n: memPick\.n, has: memPick\.has \} : null/.test(W), "带了哪几层、共多少字，随难度读数发回前端");
      ok(/umem: _m3 \? "" : memRecall\(q\), umem3: _m3 \|\| undefined/.test(CHAT), "递 umem3 时 umem 留空 —— 两个都填等于把同一段记忆送两遍");
      ok(/if \(v\.mem\) parts\.push/.test(CHAT) && /gLineMem/.test(CHAT), "屏幕上看得见这一答读了哪几层记忆");

      console.log("\n[十一] 谈完自动更新：可开可关、开时问过、一次只做一场");
      ok(/var LS_MEMAUTO = "sde_wds_memauto"/.test(CHAT) && /localStorage\.getItem\(LS_MEMAUTO\) === "1"/.test(CHAT), "自动档有开关且**默认关**（没存过就是 false）");
      ok(/if \(cbA\.checked && !confirm\(t\("memAutoAsk"\)\)\)/.test(CHAT), "开的时候要问一句 —— 它花的是读者自己的 Key，默不作声地开等于替他花钱");
      ok(/if \(!memAuto \|\| memAutoBusy/.test(CHAT), "关着不跑；正在跑就不重入");
      ok(/if \(!kv\) return;/.test(CHAT) && /绝不为它弹一个窗打断人/.test(CHAT), "没 Key 就静静不做，不弹窗打断");
      ok(/todo = MEM\.pending\(\)\.filter\(function \(m\) \{ return m && m\.id !== cur; \}\)/.test(CHAT), "排除当前这一场 —— 还在谈的不该被当成谈完的");
      ok(/MEM\.one\(todo\[0\], kv\)/.test(CHAT), "一次只做一场，不趁人不注意跑一整批");
      ok(/try \{ memAutoRun\(\); \} catch \(e\) \{\}/.test(CHAT) && /开新的之前，先把刚谈完这一场/.test(CHAT), "点「＋新对话」时把刚谈完那一场交出去");
      ok(/MEM\.refresh\(function \(\) \{ memBadge\(\); memAutoRun\(\); \}\)/.test(CHAT), "进来时补做上次没炼完的那一场");
      ok(/memSwAuto:/.test(CHAT) && /一场一次调用，花你自己的 Key/.test(CHAT), "面板上把代价写明白");

      console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
      process.exit(F ? 1 : 0);
    });
  }
}
}
