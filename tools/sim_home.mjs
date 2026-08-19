/* 社区首页（v-home）的护栏 —— 抠页面真代码跑，不另写一份。
 *
 * 为什么必须有这一份：sde-wechat-3 记着一次真事故——候选/库存/文章库三个 tab
 * 全部「加载失败」，而 sim_candidate/sim_vault/sim_lib/sim_vaultjs 全绿，
 * 因为它们测的是 DO 层与模块层，**页面这一侧没有任何护栏**。
 * 社区首页正是又一族页面层聚合，所以先补护栏再推。
 *
 * 测九组：
 *   ① 页面接线四处一次改齐（show 白名单／标签分派／登录落点／视图存在）
 *   ② 纪律①：这一面上不许出现任何可排序成等级的字眼
 *   ③ 四个状态计数按 state 真算
 *   ④ 命题编号 pid 渲得出；老卡如实标「未编号」而不是假装有
 *   ⑤ 两处空态都写明出路（不是「暂无内容」）
 *   ⑥ 三个 feed 任一失败不拦路（公共物少一样，另几样照摆）
 *   ⑦ 正在交手按截止近的在前；活下来的按结算新的在前
 *   ⑧ 四格入口各自去对的地方
 *   ⑨ 页面里 el("…") 引到的 id 必须真的存在（打字错误探针）
 */
import fs from "node:fs";
import vm from "node:vm";

const P = new URL("../public/sde-wechat/index.html", import.meta.url).pathname;
const H = fs.readFileSync(P, "utf8");

let pass = 0, fail = 0;
const ok = (name, cond) => { if (cond) { pass++; } else { fail++; console.log("  ✗ " + name); } };

/* ── ① 接线四处 ────────────────────────────────────────── */
console.log("① 接线四处一次改齐");
/* ⚠️ 不钉顺序：白名单是会被后续功能插队的（成员面 who 就插在了 home 前面）。
   只断言「home 在这个数组里」，否则每加一个视图就假红一次。 */
ok('show() 白名单含 home', /\[("[a-z]+",)*"home"(,"[a-z]+")*\]\.forEach/.test(H));
ok('视图 v-home 存在，且带滚动容器 hm-body', /id="v-home"[\s\S]{0,120}id="hm-body"/.test(H));
ok('标签条第一颗是 data-go="home"', /<div class="tabs"[\s\S]{0,200}data-go="home"/.test(H));
ok('标签分派把 home 接到 homeGo（且排在 moments 之前）',
   H.indexOf('if(g==="home"){homeGo();return;}') > 0 &&
   H.indexOf('if(g==="home"){homeGo();return;}') < H.indexOf('if(g==="moments"){moGo'));
ok('登录后的落点是社区首页，不再是聊天列表',
   /show\("home"\);homeLoad\(\);loadInbox\(\)/.test(H) && !/show\("chats"\);loadInbox\(\);loadGroups/.test(H));
ok('「动态」标签仍指向 moments 视图（只改了字，没改 data-go）', /data-go="moments"><i>\u{1F33F}<\/i>\u52a8\u6001/u.test(H));

/* ── 抠出社区首页那一段真代码 ───────────────────────────── */
const A = H.indexOf("/* \u2500\u2500 \u793e\u533a\u9996\u9875\uff1a\u516c\u5171\u7269\u6446\u5230\u95e8\u53e3");
const B = H.indexOf("/* \u2500\u2500 \u5168\u6743\u7ba1\u7406 \u2500\u2500 */");
if (A < 0 || B < 0 || B < A) { console.log("✗ 抠不出社区首页代码段"); process.exit(1); }
const SRC = H.slice(A, B);

/* 假 DOM：只做这一段真的会用到的那几件事 */
function mkEl(id) {
  return {
    id, innerHTML: "", _attr: {},
    setAttribute(k, v) { this._attr[k] = v; },
    getAttribute(k) { return this._attr[k] || null; },
    textContent: "",
  };
}
function makeCtx(apis) {
  const nodes = { "hm-body": mkEl("hm-body") };
  const clicks = [];
  const ctx = {
    el: (id) => nodes[id] || (nodes[id] = mkEl(id)),
    esc: (s) => String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"),
    cdLeft: (c) => (c.state !== "open" ? "" : "\u8fd8\u5269 1 \u5c0f\u65f6"),
    show: (v) => { clicks.push(["show", v]); },
    cdOne: (id) => clicks.push(["cdOne", id]),
    cdGo: (a, b) => clicks.push(["cdGo", a, b]),
    vtGo: (a, b) => clicks.push(["vtGo", a]),
    lbGo: (a, b) => clicks.push(["lbGo", a]),
    cdApi: apis.cd, vtApi: apis.vt, lbApi: apis.lb,
    navigator: { clipboard: { writeText() {} } },
    setTimeout: () => {},
    window: { open: (u) => clicks.push(["open", u]) },
    document: { querySelectorAll: () => [] },
    Promise, console,
    _nodes: nodes, _clicks: clicks,
  };
  vm.createContext(ctx);
  vm.runInContext(SRC, ctx);
  return ctx;
}
const CARDS = [
  { id: "a", state: "open", due: 3000, prop: "\u547d\u98981", name: "\u7532", pid: "p_x1_aaaa", backs: [{ bid: "1" }] },
  { id: "b", state: "open", due: 1000, prop: "\u547d\u98982", name: "\u4e59", pid: "p_x2_bbbb", backs: [] },
  { id: "c", state: "alive", settled: 10, prop: "\u547d\u98983", name: "\u4e19", pid: "p_x3_cccc", seps: [{ text: "\u5206\u79bb\u7ebfA" }] },
  { id: "d", state: "alive", settled: 99, prop: "\u547d\u98984", name: "\u4e01", seps: [{ text: "\u5206\u79bb\u7ebfB" }] },   // 老卡：无 pid
  { id: "e", state: "dead", prop: "\u547d\u98985", name: "\u620a" },
  { id: "f", state: "untouched", prop: "\u547d\u98986", name: "\u5df1" },
];
const okRes = {
  cd: () => Promise.resolve({ ok: true, cards: CARDS }),
  vt: () => Promise.resolve({ ok: true, items: [1, 2, 3] }),
  lb: () => Promise.resolve({ ok: true, items: [1, 2] }),
};

const ctx = makeCtx(okRes);
await ctx.homeLoad();
await new Promise((r) => setTimeout(r, 30));
const OUT = ctx._nodes["hm-body"].innerHTML;

/* ── ② 纪律①：不许有可排序成等级的字眼 ─────────────────── */
console.log("\u2461 \u7eaa\u5f8b\uff1a\u6ca1\u6709\u4efb\u4f55\u53ef\u6392\u5e8f\u6210\u7b49\u7ea7\u7684\u4e1c\u897f");
/* ⚠️ 第四次栽在同一件事上：「全局查某词不许出现」会被**声明这几个词不存在的那一句**骗到。
   查之前先把 hm-note 那段剥掉（它正写着「没有赞、没有热度、没有排行」）。 */
const BODY = OUT.replace(/<p class="hm-note">[\s\S]*?<\/p>/g, "");
for (const w of ["\u70b9\u8d5e", "\u70ed\u5ea6", "\u6392\u884c", "\u6392\u540d", "\u7c89\u4e1d", "\u5f97\u5206", "\u699c"]) {
  ok("\u6e32\u51fa\u6765\u7684\u9875\u9762\u4e0d\u51fa\u73b0\u300c" + w + "\u300d\uff08\u5df2\u5265\u6389\u58f0\u660e\u53e5\uff09", BODY.indexOf(w) < 0);
}
ok("\u58f0\u660e\u53e5\u672c\u8eab\u786e\u5b9e\u5728\u9875\u4e0a\uff08\u5265\u6389\u7684\u662f\u5b83\u4e0d\u662f\u5220\u4e86\u5b83\uff09", OUT.indexOf("\u6ca1\u6709\u70ed\u5ea6") > 0);
ok("\u6e90\u7801\u91cc\u628a\u8fd9\u6761\u7eaa\u5f8b\u5199\u6210\u4e86\u6ce8\u91ca\uff08\u6539\u7684\u4eba\u770b\u5f97\u5230\uff09",
   /\u4e0d\u51fa\u73b0\u4efb\u4f55\u53ef\u6392\u5e8f\u6210\u7b49\u7ea7\u7684\u6570\u5b57/.test(SRC));
ok("\u9875\u9762\u4e0a\u660e\u5199\u4e86\u8fd9\u56db\u4e2a\u6570\u4e0d\u662f\u5206\u6570", /\u4e0d\u662f\u5206\u6570[\s\S]{0,40}\u8d26\u672c\u72b6\u6001/.test(OUT));

/* ── ③ 四个状态计数 ───────────────────────────────────── */
console.log("\u2462 \u56db\u4e2a\u72b6\u6001\u8ba1\u6570\u6309 state \u771f\u7b97");
const num = (label) => {
  const m = OUT.match(new RegExp(">(\\d+)</b><span>" + label + "<"));
  return m ? Number(m[1]) : -1;
};
ok("\u9876\u56de\u671f = 2", num("\u9876\u56de\u671f") === 2);
ok("\u5df2\u4ea4\u624b = 2", num("\u5df2\u4ea4\u624b") === 2);
ok("\u6b7b\u683c = 1", num("\u6b7b\u683c") === 1);
ok("\u672a\u4ea4\u624b = 1", num("\u672a\u4ea4\u624b") === 1);

/* ── ④ 命题编号 ───────────────────────────────────────── */
console.log("\u2463 \u547d\u9898\u7f16\u53f7 pid");
ok("\u6709\u53f7\u7684\u5361\u628a pid \u6e32\u51fa\u6765\u4e86", OUT.indexOf("p_x1_aaaa") > 0 && OUT.indexOf("p_x3_cccc") > 0);
ok("\u6ca1\u53f7\u7684\u8001\u5361\u5982\u5b9e\u8bf4\u300c\u672a\u7f16\u53f7\u300d\uff0c\u4e0d\u5047\u88c5\u6709", OUT.indexOf("\u672a\u7f16\u53f7") > 0);
ok("pid \u5e26\u7740\u300c\u4e09\u5904\u6307\u7684\u662f\u540c\u4e00\u6761\u547d\u9898\u300d\u7684\u89e3\u91ca", /\u4e09\u5904\u6307\u7684\u662f\u540c\u4e00\u6761\u547d\u9898/.test(OUT));

/* ── ⑤ 空态写明出路 ───────────────────────────────────── */
console.log("\u2464 \u7a7a\u6001\u5199\u660e\u51fa\u8def");
const empty = makeCtx({ cd: () => Promise.resolve({ ok: true, cards: [] }), vt: okRes.vt, lb: okRes.lb });
await empty.homeLoad();
await new Promise((r) => setTimeout(r, 30));
const E = empty._nodes["hm-body"].innerHTML;
ok("\u4e0d\u662f\u4e00\u53e5\u300c\u6682\u65e0\u5185\u5bb9\u300d", E.indexOf("\u6682\u65e0\u5185\u5bb9") < 0);
ok("\u6ca1\u5361\u65f6\u544a\u8bc9\u4ed6\u53bb\u54ea\u7acb\u4e00\u5f20", /\u53bb\u300c\u{1F3AF} \u5019\u9009\u300d\u7acb\u4e00\u5f20|\u7acb\u6210\u5019\u9009\u5361/u.test(E));
ok("\u6ca1\u6d3b\u4e0b\u6765\u7684\u5361\u65f6\u8bf4\u6e05\u695a\u600e\u6837\u624d\u7b97\u6d3b\u4e0b\u6765", /\u88ab\u4eba\u9876\u56de\u3001\u800c\u4f5c\u8005\u8bf4\u5f97\u51fa\u4e00\u6761\u5206\u79bb\u7ebf/.test(E));

/* ── ⑥ 任一 feed 失败不拦路 ───────────────────────────── */
console.log("\u2465 \u4e09\u4e2a feed \u4efb\u4e00\u5931\u8d25\u4e0d\u62e6\u8def");
for (const [k, name] of [["cd", "\u5019\u9009"], ["vt", "\u5e93\u5b58"], ["lb", "\u6587\u7ae0\u5e93"]]) {
  const apis = { ...okRes };
  apis[k] = () => Promise.reject(new Error("boom"));
  const c2 = makeCtx(apis);
  await c2.homeLoad();
  await new Promise((r) => setTimeout(r, 30));
  const O2 = c2._nodes["hm-body"].innerHTML;
  ok(name + " \u6302\u4e86\uff0c\u5176\u4f59\u516c\u5171\u7269\u7167\u6446", O2.indexOf("\u5171\u540c\u4f53\u653b\u4e0b\u7684") > 0 || O2.indexOf("\u516c\u5171\u7269") > 0 || O2.indexOf("hm-grid") > 0);
  ok(name + " \u6302\u4e86\u4e0d\u6ce8\u5165\u300c\u52a0\u8f7d\u5931\u8d25\u300d", O2.indexOf("\u52a0\u8f7d\u5931\u8d25") < 0);
}

/* ── ⑦ 排序 ───────────────────────────────────────────── */
console.log("\u2466 \u6392\u5e8f");
ok("\u6b63\u5728\u4ea4\u624b\uff1a\u622a\u6b62\u8fd1\u7684\u5728\u524d", OUT.indexOf("\u547d\u98982") < OUT.indexOf("\u547d\u98981"));
ok("\u6d3b\u4e0b\u6765\u7684\uff1a\u7ed3\u7b97\u65b0\u7684\u5728\u524d", OUT.indexOf("\u547d\u98984") < OUT.indexOf("\u547d\u98983"));

/* ── ⑧ 四格入口 ───────────────────────────────────────── */
console.log("\u2467 \u56db\u683c\u516c\u5171\u7269\u5165\u53e3");
for (const g of ["vault", "lib", "cand", "nbr"]) ok("\u6709 " + g + " \u90a3\u4e00\u683c", OUT.indexOf('data-go2="' + g + '"') > 0);
ok("\u8fd1\u90bb\u5e93\u90a3\u683c\u5199\u4e86\u300c\u5e93\u672a\u547d\u4e2d\u2260\u6ca1\u88ab\u5360\u300d", /\u5e93\u672a\u547d\u4e2d\u2260\u6ca1\u88ab\u5360/.test(OUT));
ok("\u56db\u683c\u7684\u53bb\u5904\u5199\u5728\u4ee3\u7801\u91cc\uff08vault\u2192vtGo\uff0flib\u2192lbGo\uff0fcand\u2192cdGo\uff0fnbr\u2192/nbr/\uff09",
   /"vault"\)[\s\S]{0,40}vtGo/.test(SRC) && /"lib"\)[\s\S]{0,40}lbGo/.test(SRC) &&
   /"cand"\)[\s\S]{0,40}cdGo/.test(SRC) && /"nbr"\)[\s\S]{0,60}\/nbr\//.test(SRC));

/* ── ⑨ el() 引用的 id 必须存在 ─────────────────────────── */
console.log("\u2468 el(\"\u2026\") \u5f15\u7528\u7684 id \u90fd\u5b58\u5728");
const ids = new Set([...H.matchAll(/id="([A-Za-z0-9_-]+)"/g)].map((m) => m[1]));
const refs = [...SRC.matchAll(/\bel\("([A-Za-z0-9_-]+)"\)/g)].map((m) => m[1]);
const missing = refs.filter((r) => !ids.has(r));
ok("\u65e0\u60ac\u7a7a\u5f15\u7528\uff08" + refs.length + " \u5904\uff09" + (missing.length ? "\uff1a" + missing.join(",") : ""), missing.length === 0);

console.log("\n===== " + pass + " PASS / " + fail + " FAIL =====");
process.exit(fail ? 1 : 0);
