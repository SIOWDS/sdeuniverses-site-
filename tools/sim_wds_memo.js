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
const PAGE = fs.readFileSync(ROOT + "/public/taste/wds-dialogue/index.html", "utf8");
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
    const box = new Function(s2 + "\nreturn { wdsTopBody };")();
    const LC = { url: "u", model: "m", name: "n" };
    const body = box.wdsTopBody(LC, { model: "m" });
    ok(!body.reasoning_effort && !body.thinking, "行为实测：这个档位发出去的请求体里确实没有 thinking / reasoning_effort");
  }
  ok(/llmText\(VC, KEY, sys, usr, mode === "profile" \? 1800 : 1600, MEMO_MS, _stat\)/.test(seg), "预算按'它本来该写多长'给（1600/1800），并把短截止与状态回执传进 llmText");
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
  const a = PAGE.indexOf("  function umOn()"), z = PAGE.indexOf("  /* —— 更新：逐场调");
  ok(a > 0 && z > a, "从页面里取到检索这一段源码");
  const seg = PAGE.slice(a, z);
  const mk = (sw, k, prof, sessId) => {
    const LS = { getItem: (x) => (x === "sde_wds_umem_on" ? (sw ? "1" : "0") : x === "sde_wds_umem_k" ? String(k) : null), setItem() {} };
    const UM = { memos: [], metas: [], profile: prof || "", pkeys: [], ready: true, running: false, stop: false };
    const stApi = { stamp: () => "今天 10:00" };
    const stSess = { id: () => sessId || "" };
    const box = new Function("localStorage", "UM", "stApi", "stSess", "UMEM_CAP",
      seg + "\nreturn { umOn, umTopK, umNorm, umGrams, umScore, umPick, umRecall, umFp, umPending };")(LS, UM, stApi, stSess, 6000);
    return { box, UM };
  };
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
    const { box, UM } = mk(true, 5, "画".repeat(2000));
    UM.memos = [{ id: "x", title: "长", gist: "创新智商", keys: ["创新智商"], points: "点".repeat(9000), updatedAt: 9 }];
    const t = box.umRecall("创新智商");
    ok(t.length <= 6000 + 8, "总量超上限时硬截断（实测 " + t.length + " 字符，正文部分不超过 6000）");
    ok(/（余下略）$/.test(t), "截断处明标'余下略'，不假装是完整的");
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
  const cIn = num(/var MEMO_IN = (\d+)/, PAGE), sIn = num(/const MEMO_IN_MAX = (\d+)/);
  ok(cIn === sIn, "客户端截断口径 " + cIn + " 与服务端上限 " + sIn + " 对齐（客户端不许比服务端还宽，否则白发一趟被截）");
  const cCap = num(/var UMEM_CAP = (\d+)/, PAGE), sCap = num(/const UMEM_MAX = (\d+)/);
  ok(cCap === sCap, "注入上限两端对齐（" + cCap + "）");
  ok(/id="bmem"[^>]*hidden/.test(PAGE), "按钮默认隐藏——本机存不了记录时（隐私模式）不该出现一个点了没反应的按钮");
  ok(/stMakeSession\(\); stShowBtn\(\); umShowBtn\(\);/.test(PAGE), "存储就绪后才亮出「记忆更新」按钮");
  ok(/umem: umRecall\(q\)/.test(PAGE), "答题请求确实带上了本机挑出的记忆");
  ok(/mode: "one"/.test(PAGE) && /mode: "profile"/.test(PAGE), "客户端两种更新都接了：逐场摘要 + 重炼画像");
  ok(/r\.code === "rate" \|\| r\.code === "bad_key"/.test(PAGE), "撞上限流、或 Key 用不了时**停下并说明**，不拿同一把坏 Key 连撞几十场");
  ok(/UM\.stop/.test(PAGE) && /剩下的下次接着做/.test(PAGE), "批量更新可中断，且已做好的不丢、下次接着做");
  ok(/摘要与画像只存在你这台设备的浏览器里/.test(PAGE), "面板里把'存在哪、发给谁'讲清楚了");
  ok(/记忆更新/.test(PAGE) && /⌾ 记忆更新/.test(PAGE), "顶栏按钮文案在");
}

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
