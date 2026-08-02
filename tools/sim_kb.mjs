/* sim_kb.mjs —— 个人知识库（kb）的护栏
 *
 * 三层各测各的（记忆里那条教训：DO 层全绿不能替页面层作证）：
 *   ① DO 层：从 worker.js **抠真源码**进 vm 跑（不另写一份，改源码 sim 跟着变）
 *   ② 路由层：白名单、动作过滤
 *   ③ 页面层与模块层：接线、信封只拆一次、纪律
 *
 * 用法：node tools/sim_kb.mjs
 */
import fs from "fs";
import path from "path";
import vm from "vm";

const ROOT = path.join(path.dirname(new URL(import.meta.url).pathname), "..");
let PASS = 0, FAIL = 0;
const ok = (c, m) => { if (c) PASS++; else { FAIL++; console.log("  ✗ " + m); } };
const sec = t => console.log("\n── " + t + " ──");
const read = p => fs.readFileSync(path.join(ROOT, p), "utf8");

const W = read("src/worker.js");

/* ══ ① DO 层真跑 ═══════════════════════════════════ */
sec("① DO 层（抠真源码跑）");

/* 假存储：真 DO 的 list() 返回 Map，代码走 `for (const k of m.keys())`
   ⚠ 所以 keys 必须是**方法**不是属性（sim_lib 那次栽过） */
function fakeStore() {
  const m = new Map();
  return {
    _m: m,
    get: async k => (m.has(k) ? JSON.parse(JSON.stringify(m.get(k))) : undefined),
    put: async (k, v) => { m.set(k, v); },
    delete: async k => { m.delete(k); },
    list: async ({ prefix, limit }) => {
      const ks = [...m.keys()].filter(k => k.startsWith(prefix)).sort().slice(0, limit || 1000);
      return { keys: () => ks };
    }
  };
}

/* 抠出 kb 段：从注释起点到 cdpost 之前。锚点要够长，且从起点之后再找终点。 */
const A = W.indexOf("/* ===== 个人知识库 kb: =====");
ok(A > 0, "找不到 kb 段起点");
const B = W.indexOf('if (op === "cdpost")', A);
ok(B > A, "找不到 kb 段终点");
const SEG = W.slice(A, B);
ok(SEG.length > 2500, "抠出来的 kb 段太短：" + SEG.length);

let RND = 0;
async function runOp(store, op, b, uid = "u_abcdefghijkl") {
  const ctx = {
    Response: { json: (o) => ({ _json: o }) },
    Math, JSON, String, Number, parseInt, Date, console,
    _rnd: () => "r" + (++RND)
  };
  vm.createContext(ctx);
  const src = `
    (async function (op, b, uid, now) {
      const ok12 = (u) => typeof u === "string" && u.length >= 12;
      const moClean = (s, n) => String(s == null ? "" : s).replace(/[\\u0000-\\u001f]/g, "").trim().slice(0, n);
      const moInv = (t) => String(1e15 - t).padStart(16, "0");
      const moRnd = () => _rnd();     // ⚠ 每次 runOp 都新建 vm，桩里不能用局部计数器：
                                      //   会每次从 1 重来，同一毫秒内的两件撞成同一个键、
                                      //   互相覆盖，看起来就像"件数上限没生效"（第一版正是这样误报的）
      ${SEG}
      return { ok: false, msg: "未知 op" };
    })`;
  const fn = vm.runInContext(src, ctx);
  const r = await fn.call({ ctx: { storage: store } }, op, b, uid, Date.now());
  return r && r._json ? r._json : r;
}

{
  const S = fakeStore();
  let r = await runOp(S, "kbadd", { title: "报告", kind: "md", text: "太短" });
  ok(!r.ok && /思想库存/.test(r.msg || ""), "过短的没有被挡住、也没指出该去哪：" + JSON.stringify(r));

  const body = "这是一份成品稿。".repeat(40);
  r = await runOp(S, "kbadd", { title: "报告", kind: "md", text: body, from: "ChatSDE · 画布", ver: 2 });
  ok(r.ok && r.item && r.item.id, "正常入库失败：" + JSON.stringify(r));
  ok(r.item.chars === body.length, "字数没记对");
  ok(r.item.ver === 2, "版本号没记下");

  /* 键必须带 uid —— 私人库的隔离全靠这个 */
  const keys = [...S._m.keys()];
  ok(keys.some(k => k.startsWith("kb:u_abcdefghijkl:")), "正文键没带 uid");
  ok(keys.some(k => k.startsWith("ki:u_abcdefghijkl:")), "元数据键没带 uid");
  ok(keys.every(k => !/^kb:[0-9]/.test(k)), "出现了不带 uid 的正文键（别人就能查到了）");

  /* 元数据与正文分开存 —— 列表不该把十件两万字一起拖回来 */
  const metaKey = keys.filter(k => k.startsWith("ki:"))[0];
  ok(typeof S._m.get(metaKey) === "object", "元数据不是对象");
  ok(!("text" in S._m.get(metaKey)), "元数据里混进了正文（列表就会很重）");

  /* 列表只回元数据 */
  const mine = await runOp(S, "kbmine", {});
  ok(mine.ok && mine.items.length === 1, "列表取不回");
  ok(!("text" in mine.items[0]), "kbmine 把正文也回了（那就白分开存了）");
  ok(mine.cap && mine.cap.count > 0 && mine.cap.one > 0, "没有回配额");

  /* 取全文 */
  const g = await runOp(S, "kbget", { id: mine.items[0].id });
  ok(g.ok && g.text === body, "取全文对不上");

  /* 同题同文不重复存 */
  const dup = await runOp(S, "kbadd", { title: "报告", kind: "md", text: body });
  ok(dup.ok && dup.dup === 1, "同题同文竟又存了一件");
  ok((await runOp(S, "kbmine", {})).items.length === 1, "去重没生效");

  /* 改名 */
  const rn = await runOp(S, "kbren", { id: mine.items[0].id, title: "新名字" });
  ok(rn.ok && rn.item.title === "新名字", "改名失败");
  ok((await runOp(S, "kbren", { id: mine.items[0].id, title: "  " })).ok === false, "空名字竟被接受");

  /* 别人的 uid 取不到、删不掉 */
  const other = await runOp(S, "kbget", { id: mine.items[0].id }, "u_zzzzzzzzzzzz");
  ok(!other.ok, "换个 uid 竟能读到别人的知识库");
  const odel = await runOp(S, "kbdel", { id: mine.items[0].id }, "u_zzzzzzzzzzzz");
  ok(!odel.ok, "换个 uid 竟能删掉别人的东西");
  ok((await runOp(S, "kbmine", {}, "u_zzzzzzzzzzzz")).items.length === 0, "换个 uid 竟看得见别人的列表");

  /* 删 */
  const del = await runOp(S, "kbdel", { id: mine.items[0].id });
  ok(del.ok, "删除失败");
  ok([...S._m.keys()].length === 0, "删了元数据却漏了正文（或反过来）：" + JSON.stringify([...S._m.keys()]));

  /* 未登录（uid 不合法）一律拒 */
  ok((await runOp(fakeStore(), "kbadd", { title: "x", text: body }, "短")).ok === false, "非法 uid 竟能入库");
}

sec("② 配额：超了要如实说，不许静默截断");
{
  const S = fakeStore();
  const huge = "字".repeat(30001);
  const r = await runOp(S, "kbadd", { title: "巨稿", text: huge });
  ok(!r.ok, "超过单件上限竟然存进去了");
  ok(/上限/.test(r.msg || "") && /存到本机/.test(r.msg || ""), "超限时没说清上限、也没给去处：" + r.msg);
  ok([...S._m.keys()].length === 0, "拒了却还是写进了存储");

  /* 件数上限 */
  const S2 = fakeStore();
  const body = "内容".repeat(30);
  for (let i = 0; i < 120; i++) await runOp(S2, "kbadd", { title: "件" + i, text: body + i });
  const over = await runOp(S2, "kbadd", { title: "第121", text: body + "x" });
  ok(!over.ok && /上限/.test(over.msg || ""), "件数上限没生效：" + JSON.stringify(over));
  ok((await runOp(S2, "kbmine", {})).items.length === 120, "件数竟超过上限");
}

sec("③ 路由");
{
  ok(/if \(op === "kb"\) \{/.test(W), "没有 kb 的路由分发");
  const seg = W.slice(W.indexOf('if (op === "kb") {'), W.indexOf('if (op === "kb") {') + 900);
  ok(/\["add", "mine", "get", "ren", "del"\]/.test(seg), "路由动作白名单不对");
  ok(/未知的知识库动作/.test(seg), "非法动作没有被挡住");
  ok(/uid: who\.uid/.test(seg), "路由没有把登录者的 uid 传下去（那就没有私人可言了）");
  ok(!/uid: b\.uid/.test(seg), "路由竟从请求体里取 uid —— 谁都能冒充别人");
  /* 鉴权：kb 必须落在需要登录的那一段里 */
  ok(W.indexOf('if (op === "kb") {') > W.indexOf("请先在「SDE 社区」用名字和密码登录"), "kb 路由排在鉴权之前？");
}

sec("④ 模块层 sde-vault.kb");
{
  const V = read("public/taste/assets/sde-vault.js");
  ok(/function kb\(o, box\)/.test(V), "模块里没有 kb()");
  ok(/kb: kb/.test(V), "kb 没被导出");
  /* 纪律②：未登录不偷偷存，且要给可点的去处 */
  const seg = V.slice(V.indexOf("function kb(o, box)"), V.indexOf("w.SDEVault = {"));
  ok(/var c = cred\(\);/.test(seg), "kb 没走全站单点登录的身份");
  ok(/noAuth/.test(seg) && /sde-wechat/.test(seg), "未登录时没给可点的去处");
  ok(seg.indexOf("fetch") > seg.indexOf("if (!c)"), "身份判断排在请求之后（那就先发出去了）");
  /* 信封只拆一次 */
  ok(/\(d && d\.d\) \? d\.d : d/.test(seg), "没有对齐 /api/im 的 {s,d} 信封");
  /* 纪律④：失败不拦路，但不许假装存过 */
  ok(/没存上/.test(seg), "失败时没有如实说");
  ok(!/reject/.test(seg), "kb 会 reject —— 入库不该拖垮主产线");
}

sec("⑤ 画布出口");
{
  const M = read("public/wds-mode.js");
  ok(/cvKb: "⇧ 存进知识库"/.test(M), "画布没有存进知识库的文案");
  ok(/mk\(tx\("cvKb"\)/.test(M), "画布工具条没有那颗按钮");
  ok(/SDEVault\.kb\(\{/.test(M), "按钮没调 SDEVault.kb");
  ok(/typeof SDEVault\.kb !== "function"/.test(M), "没判模块在不在（模块是按需装的）");
  /* 必须传真 DOM 元素：模块的 note() 是 box.innerHTML=… */
  ok(/\}, cvNoteEl\(\)\)/.test(M), "没给 note() 传真 DOM 元素（传假壳会静默什么都不做）");
  ok(/function cvNoteEl\(\)/.test(M), "缺回话位");
  /* 存的是当前这一版，并把版号带过去 */
  ok(/text: cvText\(\)/.test(M), "存的不是当前版的正文");
  ok(/ver: it\.vi \+ 1/.test(M), "没带版本号过去");
  ok(/cvGrab\(\);\n\s*SDEVault\.kb/.test(M), "存之前没先收编辑框里的字（正在手改的内容会存成旧的）");
  /* 缓存串 */
  ok(!/sde-vault\.js\?v=1\b/.test(M), "wds-mode 还引着 v=1 的旧模块");
}

sec("⑥ 社区页");
{
  const H = read("public/sde-wechat/index.html");
  ok(/id="v-kb"/.test(H), "缺视图容器");
  ok(/id="b-kb"/.test(H), "「我」页没有入口");
  ok(/function kbLoad\(\)/.test(H) && /function kbShow\(/.test(H), "缺列表/打开");
  /* 白名单四处一次改齐 —— 漏一处就"进得去出不来" */
  ok(/"lib","kb"\]\.forEach/.test(H), "白名单·视图切换 漏了");
  ok(/v==="kb"\|\|v==="who"/.test(H), "白名单·返回键 漏了");
  ok(/v==="kb"\)el\("t-ttl"\)/.test(H), "白名单·标题 漏了");
  ok(/el\("v-kb"\)\.classList\.contains\("on"\)/.test(H), "白名单·返回目标 漏了");
  /* 信封只拆一次 */
  /* ⚠ 别用 [^)]* 去匹配参数：里面有 Object.assign(…) 自带右括号，第一版就是这么误报的 */
  const kbApiLine = (H.match(/function kbApi\([^\n]*/) || [""])[0];
  ok(/\.then\(unwrap\);/.test(kbApiLine), "kbApi 没拆信封：" + kbApiLine.slice(0, 90));
  ok(/api\("kb",/.test(kbApiLine), "kbApi 走的不是 kb 这条 op");
  const seg = H.slice(H.indexOf("function kbLoad()"), H.indexOf("function lbApi("));
  ok(!/\.d\.ok|\.s ===/.test(seg), "调用点又拆了一次信封（形状会打架）");
  /* 私人库：页面必须说清只有本人看得见，且不与文章库抢活 */
  ok(/只有你看得见/.test(H), "没写明这是私人的");
  ok(/已经有的篇目不必存进来/.test(H), "没划清与文章库的边界（会变成把站内文章存第二份）");
  /* 不许出现可排序成等级的数字 */
  const noteOff = seg.replace(/已用 [^']*/g, "");
  ok(!/热度|排行|点赞|粉丝/.test(noteOff), "知识库页面出现了排行/热度一类的东西");
  /* 空态写明出路 */
  ok(/还是空的/.test(seg) && /落到画布/.test(seg), "空态没写明出路");
  /* 用的是页面真有的时间函数 */
  ok(/fmtT\(it\.ts\)/.test(H), "没用页面里真有的 fmtT");
  ok(!/fmtTime\(/.test(H), "用了页面里并不存在的 fmtTime");
}

console.log("\n" + PASS + " PASS / " + FAIL + " FAIL");
process.exit(FAIL ? 1 : 0);
