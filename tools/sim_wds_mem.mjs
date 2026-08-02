// @WDS 群聊记忆（_wdsHistory）模拟——装载 src/worker.js 的 CommentBox，用假存储跑真逻辑。
// 跑法：node tools/sim_wds_mem.mjs
//
// 守的是 2026-08-02 这次修复：旧版 _wdsChatContext 取 log.slice(-30) 拼成纯文本，
// 并且 filter((s)=>s.length<400) —— WDS 自己 deep 档的回答几乎条条超 400 字符，
// 于是被整条丢掉，它永远看不见自己上一句。本文件第 3 组就是那条回归的证明。
import { CommentBox } from "../src/worker.js";
import fs from "fs";

function fakeStorage() {
  const m = new Map();
  return {
    _m: m,
    async get(k) { return m.has(k) ? JSON.parse(JSON.stringify(m.get(k))) : undefined; },
    async put(k, v) { m.set(k, JSON.parse(JSON.stringify(v))); },
    async delete(k) { return m.delete(k); },
    async list() { return new Map(); },
  };
}

let pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; console.log("  ✓ " + name); }
  else { fail++; console.log("  ✗ " + name + (extra ? "  ← " + JSON.stringify(extra) : "")); }
}

const st = fakeStorage();
const box = new CommentBox({ storage: st, acceptWebSocket() {}, getWebSockets() { return []; } }, {});

// 造一场群聊：id 从 1 起，bot 消息穿插
async function seed(items) {
  let seq = 0;
  const log = items.map((it) => {
    seq += 1;
    return { id: seq, name: it.bot ? "WDS智能体" : (it.name || "张琼"), text: it.text, ts: 1750000000000 + seq * 1000, ...(it.bot ? { bot: 1 } : {}), ...(it.recalled ? { recalled: 1 } : {}), ...(it.img ? { img: 1 } : {}) };
  });
  await st.put("clog", log);
  await st.put("cseq", seq);
  return seq;
}

const LONG = "这是一条很长的回答。".repeat(80);   // 800 字符，远超旧版 400 的门槛

console.log("\n【一】基本形状：装进 messages 多轮，而不是一段纯文本");
{
  await seed([
    { name: "张琼", text: "@WDS 什么是显露？" },
    { bot: true, text: "显露是三维之一。" },
    { name: "高鹏", text: "那差异序列呢？" },
  ]);
  const h = await box._wdsHistory("deep", 999);
  ok("返回的是数组", Array.isArray(h));
  ok("三条都在", h.length === 3, h.length);
  ok("bot 的落 assistant", h[1].role === "assistant", h[1]);
  ok("人的落 user", h[0].role === "user" && h[2].role === "user");
  ok("人的消息带发言人名字（群里多人，名字承重）", h[0].content.startsWith("张琼："), h[0].content);
  ok("bot 的消息不加名字前缀", !/^WDS智能体：/.test(h[1].content), h[1].content);
}

console.log("\n【二】beforeId：当前提问不重复出现");
{
  const last = await seed([
    { name: "张琼", text: "第一问" },
    { bot: true, text: "第一答" },
    { name: "张琼", text: "@WDS 第二问" },
  ]);
  const h = await box._wdsHistory("deep", last);
  ok("最后一条（当前提问）被排除", h.length === 2, h.map((x) => x.content));
  ok("排除的正是它", !h.some((x) => x.content.includes("第二问")));
  const h2 = await box._wdsHistory("deep", 0);
  ok("不传 beforeId 时不排除（向后兼容）", h2.length === 3);
}

console.log("\n【三】回归证明：长消息必须被截断，不能整条丢弃");
{
  await seed([
    { name: "张琼", text: "问一句短的" },
    { bot: true, text: LONG },
    { name: "张琼", text: "接着问" },
  ]);
  const h = await box._wdsHistory("deep", 999);
  ok("长的 bot 回答仍在场（旧版在这里会整条丢掉）", h.length === 3, h.length);
  const botMsg = h.find((x) => x.role === "assistant");
  ok("它确实是那条长回答", !!botMsg && botMsg.content.includes("这是一条很长的回答"));
  ok("deep 档 800 字符未被截（per=3000）", botMsg && !botMsg.content.includes("（略）"), botMsg && botMsg.content.length);
  // quick 档 per=1200，用一条 2000 字符的验截断
  await seed([{ bot: true, text: "甲".repeat(2000) }]);
  const hq = await box._wdsHistory("quick", 999);
  ok("quick 档超 per 的被截断而非丢弃", hq.length === 1 && !!hq[0] && hq[0].content.includes("（略）"), hq.length);
  ok("截断后长度受控", !!hq[0] && hq[0].content.length <= 1200 + 10, hq[0] ? hq[0].content.length : "无内容");
}

console.log("\n【四】轮数：deep 约百轮，quick 短");
{
  const many = [];
  for (let i = 0; i < 400; i++) many.push({ name: "人" + (i % 3), text: "第" + i + "句" });
  await seed(many);
  const hd = await box._wdsHistory("deep", 9999);
  const hq = await box._wdsHistory("quick", 9999);
  ok("deep 取到 200 条量级（≈百轮）", hd.filter((x) => !x.content.startsWith("（更早的")).length === 200, hd.length);
  ok("quick 取到 60 条量级", hq.filter((x) => !x.content.startsWith("（更早的")).length === 60, hq.length);
  ok("deep 比 quick 记得多", hd.length > hq.length);
  ok("取的是最近的，不是最早的", hd[hd.length - 1].content.includes("第399句"), hd[hd.length - 1]);
}

console.log("\n【五】预算：超了从最旧处裁，并明标省略");
{
  const many = [];
  for (let i = 0; i < 200; i++) many.push({ name: "张琼", text: "甲".repeat(1500) });  // 200×1500 = 30 万，远超 6 万
  await seed(many);
  const h = await box._wdsHistory("deep", 9999);
  ok("最前面有省略说明", h[0].content.startsWith("（更早的"), h[0].content.slice(0, 30));
  ok("省略说明里有条数", /更早的 \d+ 条已省略/.test(h[0].content), h[0].content);
  const total = h.reduce((n, x) => n + x.content.length, 0);
  ok("总量守住预算（60000 上下一条的余量）", total <= 60000 + 1600, total);
  ok("最近一轮永远在场", h[h.length - 1].content.includes("甲"));
  ok("裁的是最旧的（保尾不保头）", h.length < 200);
}

console.log("\n【六】脏数据不崩");
{
  await seed([
    { name: "张琼", text: "正常一句" },
    { name: "高鹏", text: "撤回的", recalled: true },
    { name: "秦莉", text: "", img: true },
    { name: "胡敏", text: "又一句" },
  ]);
  const h = await box._wdsHistory("deep", 999);
  ok("撤回的不进历史", !h.some((x) => x.content.includes("撤回的")));
  ok("图片消息占位成 [图片]", h.some((x) => x.content.includes("[图片]")), h.map((x) => x.content));
  ok("正常消息都在", h.filter((x) => /正常一句|又一句/.test(x.content)).length === 2);
  // 存储整个坏掉
  const bad = new CommentBox({ storage: { async get() { throw new Error("boom"); }, async put() {} }, acceptWebSocket() {}, getWebSockets() { return []; } }, {});
  const hb = await bad._wdsHistory("deep", 0);
  ok("读库爆炸时返回空数组而不是抛出（记忆是加分项不是门禁）", Array.isArray(hb) && hb.length === 0);
}

console.log("\n【七】接线：answerWDS 真的把历史装进 messages");
{
  const src = fs.readFileSync(new URL("../src/worker.js", import.meta.url), "utf8");
  ok("旧的 _wdsChatContext 已彻底移除", !/_wdsChatContext/.test(src));
  ok("answerWDS 收 beforeId", /async answerWDS\(question, beforeId\)/.test(src));
  ok("调用点递了当前消息 id", /answerWDS\(_wq, msg\.id\)/.test(src));
  const seg = src.slice(src.indexOf("async answerWDS"), src.indexOf("async answerWDS") + 9000);
  ok("取历史时带上 tier、beforeId 与现算的预算", /_wdsHistory\(tier, beforeId, Math\.max\(WDS_HIST_FLOOR/.test(seg));
  ok("历史铺进 messages 数组（system 之后、当前问题之前）",
    /messages: \[\{ role: "system", content: sys \}, \.\.\.hist, \{ role: "user", content: usr \+ _modeInstr \}\]/.test(seg));
  ok("usr 里不再拼群聊上下文（避免同一份历史进两遍）", !/群里最近的讨论/.test(seg));
  ok("两档预算都在代码里", /deep:\s*\{ msgs: 200, budget: 60000, per: 3000 \}/.test(src) && /quick:\s*\{ msgs: 60,\s*budget: 12000, per: 1200 \}/.test(src));
  ok("站内检索与两个库仍在（这次没碰它们）", /_wdsLibContext/.test(seg) && /siteCtx/.test(seg));
}

console.log("\n【八】装全能：内功＋心得＋完整方法论＋记忆＋网站 RAG 五件齐");
{
  const src = fs.readFileSync(new URL("../src/worker.js", import.meta.url), "utf8");
  const seg = src.slice(src.indexOf("async answerWDS"), src.indexOf("async answerWDS") + 11000);
  ok("① 内功两档都装（不再只有 deep）", /await loadNeigong\(this\.env, base\)/.test(seg) && !/tier === "deep"\) \{ try \{ neigong/.test(seg));
  ok("② 心得仍在（按基底复用 reflect:<vendor>）", /ensureReflect\(this\.env, base, rvendor, VC, key\)/.test(seg));
  ok("③ 装的是全站唯一那份完整方法论指引", /WDS_METHOD_GUIDE/.test(seg));
  // 「猜想→执行→评估→反馈→修正→迭代」本身没错——那是**六步法**（D2 路径组织层），
  // WDS_SYS 里就是这么标的。错的是旧摘要把它标成了「六路径/六步法」，
  // 把 D2 的六步法与 S/D/E 六种排列的六路径混为一谈。守的是这个混淆不许回来。
  ok("③b 六路径与六步法不再被混为一谈", !/六路径\/六步法/.test(src), "仍有「六路径/六步法」的写法");
  ok("③b2 六步法在 WDS_SYS 里仍标在 D2 路径组织层（没被误删）", /D2 意义?路径组织\(六步法：猜想/.test(src) || /六步法：猜想→执行/.test(src));
  ok("③c 完整指引里确有真六路径", /S→D→E 学科本体论分析/.test(src) && /E→D→S 综述与建制/.test(src));
  ok("④ 记忆装进 messages（见第七组）", /\.\.\.hist/.test(seg));
  ok("⑤ 网站 RAG 仍是全站检索且 deep 档加宽到 K=24 / 18000",
    /lightRetrieve\(this\.env, base, q, expTerms, tier === "deep" \? 24 : 12/.test(seg) && /tier === "deep" \? 18000 : 6500/.test(seg));
  ok("固定部分现算进 _fixed（内功＋心得＋方法论＋站内资料＋两个库）",
    /const _fixed = \(neigong \? neigong\.length : 0\)/.test(seg) && /WDS_METHOD_GUIDE\.length \+ siteCtx\.length/.test(seg));
  ok("总预算两档都定义了", /WDS_TOTAL_CHARS = \{ deep: 100000, quick: 60000 \}/.test(src) && /WDS_HIST_FLOOR = 8000/.test(src));
}

console.log("\n【九】动态预算的行为：只许更小，且有地板");
{
  const many = [];
  for (let i = 0; i < 100; i++) many.push({ name: "张琼", text: "乙".repeat(1200) });
  await seed(many);
  const wide = await box._wdsHistory("deep", 9999);
  const tight = await box._wdsHistory("deep", 9999, 9000);
  const tot = (a) => a.reduce((n, x) => n + x.content.length, 0);
  ok("传了更小的预算就真的记得少", tot(tight) < tot(wide), { wide: tot(wide), tight: tot(tight) });
  ok("小预算守得住", tot(tight) <= 9000 + 1600, tot(tight));
  const huge = await box._wdsHistory("deep", 9999, 999999);
  ok("传超大预算也不许超过本档上限（上限仍由常量把关）", tot(huge) <= 60000 + 1600, tot(huge));
  ok("即使预算很紧，最近一轮仍在场", tight.length >= 1 && tight[tight.length - 1].content.includes("乙"));
  ok("预算为 0/未传时走本档默认", tot(await box._wdsHistory("deep", 9999, 0)) === tot(wide));
}

console.log("\n【十】可缓存前缀：变动的东西一律不许进 system");
{
  const src = fs.readFileSync(new URL("../src/worker.js", import.meta.url), "utf8");
  const seg = src.slice(src.indexOf("async answerWDS"), src.indexOf("async answerWDS") + 12000);
  ok("system 里只有 sys，不带模式指令（否则同一份前缀被劈成两版，缓存命中减半）",
    /role: "system", content: sys \}/.test(seg) && !/content: sys \+ _modeInstr/.test(seg));
  ok("模式指令挂在当轮 user 末尾（顺带占高注意力位）", /content: usr \+ _modeInstr/.test(seg));
  // sys 的组成必须全是逐字稳定的东西——变动项（站内资料/两个库/提问）都在 usr 里
  const sysBlock = seg.slice(seg.indexOf("const sys = WDS_SYS"), seg.indexOf("const _mode = wdsMode"));
  ok("sys 只由内功/心得/方法论这些稳定件拼成", /neigong/.test(sysBlock) && /reflect/.test(sysBlock) && /WDS_METHOD_GUIDE/.test(sysBlock));
  ok("站内资料不进 sys（它每问都不同，进去就废掉整个前缀）", !/siteCtx/.test(sysBlock));
  ok("两个库不进 sys（同理，它们随共同体动态变）", !/libCtx/.test(sysBlock));
  ok("提问本身不进 sys", !/【提问者的问题】/.test(sysBlock));
  // 心得的缓存链条要完好
  const er = src.slice(src.indexOf("async function ensureReflect"), src.indexOf("async function ensureReflect") + 2600);
  ok("心得三级缓存仍在：内存 → CONFIG_VAULT → 才生成",
    /REFLECT_MEM\[vendor\]/.test(er) && /op: "getReflect"/.test(er) && /op: "setReflect"/.test(er));
  ok("心得有失败负缓存（坏 Key 不连撞）", /REFLECT_FAIL_TTL/.test(er));
  ok("内功有模块级缓存（不重复取文件）", /NEIGONG_CACHE|let NEIGONG|NEIGONG =/.test(src));
}

console.log("\n" + (fail === 0 ? "✅" : "❌") + "  " + pass + " PASS / " + fail + " FAIL\n");
process.exit(fail === 0 ? 0 : 1);
