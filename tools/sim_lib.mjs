/* tools/sim_lib.mjs —— SDE 微信「文章库」护栏
   假存储真逻辑：把 worker.js 里 lb* 六个 op 的真源码抠出来跑（不另写一份，改源码 sim 跟着变）。
   另有对页面/模块的静态断言。 */
import fs from "node:fs";

let P = 0, F = 0;
const ok = (c, m) => { if (c) { P++; } else { F++; console.log("  FAIL:", m); } };

const src = fs.readFileSync("src/worker.js", "utf8");
const page = fs.readFileSync("public/sde-wechat/index.html", "utf8");
const vault = fs.readFileSync("public/taste/assets/sde-vault.js", "utf8");
const read = fs.readFileSync("public/taste/wds-companion/wds-read.js", "utf8");

/* ── 假存储：只实现 get/put/delete/list(prefix,limit) ── */
function mkStore() {
  const m = new Map();
  return {
    m,
    async get(k) { return m.get(k); },
    async put(k, v) { m.set(k, v); },
    async delete(k) { m.delete(k); },
    async list({ prefix = "", limit = 1000 } = {}) {
      const ks = [...m.keys()].filter((k) => k.startsWith(prefix)).sort().slice(0, limit);
      return { keys: () => ks };   // 真 DO 的 list().keys() 是方法，不是属性
    },
  };
}
/* 从真源码里抠出 lb 段，包成可调用的 handler */
const a = src.indexOf('if (op === "lbadd")');
const b = src.indexOf('if (op === "cdpost")');
ok(a > 0 && b > a, "源码里能定位 lb 段");
const body = src.slice(a, b);

const moClean = (s, n) => String(s == null ? "" : s).replace(/\s+/g, " ").trim().slice(0, n);
const moInv = (t) => String(1e15 - t).padStart(16, "0");
let rnd = 0;
const moRnd = () => "r" + (++rnd);
const ok12 = () => true;

const handler = new Function("op", "b", "uid", "now", "ctx", "Response", "moClean", "moInv", "moRnd", "ok12",
  "return (async function(){" + body + "return {ok:false,unhandled:1};}).call({ctx:ctx});");
const R = { json: (o) => o };
const store = mkStore();
const ctx = { storage: store };
const call = (op, bb, uid = "u1", now = 1000) => handler(op, bb, uid, now, ctx, R, moClean, moInv, moRnd, ok12);

console.log("── 1. 收藏（私人）");
let r = await call("lbadd", { slug: "hu-min/deafened-organ", title: "失听的器官" });
ok(r.ok && r.item.slug === "hu-min/deafened-organ", "收藏成功");
r = await call("lbadd", { slug: "hu-min/deafened-organ", title: "失听的器官" });
ok(r.ok && r.dup === 1, "同一人重复收同一篇不新增，标 dup");
r = await call("lbadd", { slug: "nosuchslug", title: "x" });
ok(!r.ok && /认不出/.test(r.msg), "认不出站内篇目要拒绝");
r = await call("lbadd", { slug: "a/b", title: "" });
ok(!r.ok && /篇名/.test(r.msg), "没篇名要拒绝");
r = await call("lbadd", { slug: "a/b<script>", title: "注入" });
ok(r.ok && r.item.slug === "a/bscript", "slug 里的非法字符被剥掉");

console.log("── 2. 我收的 / 删");
r = await call("lbmine", {});
ok(r.ok && r.items.length === 2, "我收的能列出（2 篇）");
const id0 = r.items[0].id;
let r2 = await call("lbdel", { id: id0 }, "u2");
ok(!r2.ok, "别人的收藏删不掉（键里带 uid，查不到）");
r2 = await call("lbdel", { id: id0 }, "u1");
ok(r2.ok, "能删自己的");
r = await call("lbmine", {});
ok(r.items.length === 1, "删后剩 1 篇");
r = await call("lbmine", {}, "u2");
ok(r.ok && r.items.length === 0, "别人看不到我的收藏（私人书签）");

console.log("── 3. 推给大家：门槛在分离线上");
r = await call("lbpush", { slug: "x/y", title: "某篇", sep: "好文推荐" });
ok(!r.ok && /切开了什么/.test(r.msg), "分离线太短要拒绝，且说明理由");
r = await call("lbpush", { slug: "x/y", title: "某篇", sep: "" });
ok(!r.ok, "空分离线拒绝");
r = await call("lbpush", { slug: "x/y", title: "某篇", sep: "它把「读不懂」从能力问题改判成供给条件问题" }, "u1", 100000);
ok(r.ok && r.item.sep.length >= 12, "带分离线能推成");
r = await call("lbpush", { slug: "x/y", title: "某篇", sep: "另一句同样够长的分离线在这里" }, "u1", 100000 + 25000);
ok(!r.ok && /已经推过/.test(r.msg), "同一人同一篇不能推两次");
r = await call("lbpush", { slug: "x/z", title: "另一篇", sep: "这一句也够长可以用来测限流" }, "u1", 100000 + 5000);
ok(!r.ok && /缓一下/.test(r.msg), "20 秒内不能连推");

console.log("── 4. 公共库");
r = await call("lbpub", {});
ok(r.ok && r.items.length === 1 && r.items[0].sep, "公共库能列出，且每条带分离线");
r = await call("lbpub", {}, "u2");
ok(r.ok && r.items.length === 1, "公共库人人可见（与私人收藏相反）");
const pid = r.items[0].id;
r = await call("lbunpush", { id: pid }, "u2");
ok(!r.ok && /只能撤回自己/.test(r.msg), "只能撤回自己推的");
r = await call("lbunpush", { id: pid }, "u1");
ok(r.ok, "作者能撤回");
r = await call("lbpub", {});
ok(r.items.length === 0, "撤回后公共库空");

console.log("── 5. 源码级纪律");
ok(!/lp:.*count|hot|热度/.test(body), "后端不记热度/计数");
ok(/lb:" \+ uid/.test(body), "私人收藏的键带 uid（天然隔离）");
ok(/sep\.length < 12/.test(body), "分离线下限 12 字写死在服务端");
ok(!/R2|PDFS|uploaded/.test(body), "文章库不碰 R2（存指针不存副本）");
ok(/hits\.length >= 10/.test(body), "推荐位每日封顶");

console.log("── 6. 路由");
const route = src.slice(src.indexOf('if (op === "lb") {'), src.indexOf('if (op === "cd") {'));
ok(/\["add", "mine", "del", "push", "pub", "unpush"\]/.test(route), "路由白名单六个动作");
ok(/未知的文章库动作/.test(route), "非白名单动作被挡");

console.log("── 7. 页面接线");
ok(page.includes('id="v-lib"') && page.includes('id="lb-body"'), "新视图与容器存在");
/* ⚠ 不许钉数组尾巴：show() 的白名单**会被后续功能插队**（知识库 kb 加在 lib 之后，
   当场把这条钉死尾巴的断言弄红）。同一个教训 sim_home 那边已经栽过一次（钉了顺序）。
   判据改成「lib 在这个数组里」，顺序与相邻元素一概不管。 */
const wlArr = (page.match(/\[\s*"gate"[^\]]*\]\.forEach/) || [""])[0];
ok(/"lib"/.test(wlArr), "show() 白名单里没有 lib：" + wlArr.slice(0, 120));
ok(/"gate"/.test(wlArr) && /"me"/.test(wlArr), "取到的不是那个视图白名单数组");
ok(page.includes('v==="lib"'), "顶栏返回键条件已加 lib");
ok(page.includes('el("t-ttl").textContent="📚 文章库"'), "标题已接");
ok(page.includes('el("v-lib").classList.contains("on")'), "返回键回退路径已接");
ok(page.includes('id="b-lib"') && page.includes('lbWire();'), "我页入口与接线");
ok(page.includes('id="mu-article"'), "朋友圈「插一篇」按钮存在");
ok(/lbFar\s*\(/.test(page) && page.includes("publications.json"), "发现这一路从站上目录现算");
ok(!/按收藏数|最多人收藏|热门/.test(page), "页面上没有热度榜");
ok(page.includes("不计数、不公开、不排热度"), "私人书签的口径写在页面上（可见性铁律）");
ok(page.includes("你还没收过文章"), "空态写明出路");
const ids = new Set([...page.matchAll(/id="([^"]+)"/g)].map((m) => m[1]));
const refs = [...page.matchAll(/el\("([^"]+)"\)/g)].map((m) => m[1]);
ok(refs.every((x) => ids.has(x)), "页面无悬空 el() 引用");

console.log("── 8. 模块与浮层");
ok(/function fav\s*\(/.test(vault) && /fav: fav/.test(vault), "SDEVault.fav 已导出");
ok(/op: "lb", a: "add"/.test(vault), "fav 走 lb/add");
ok(/noAuth: 1/.test(vault) && /登录一次/.test(vault), "未登录不偷偷存，给可点去处");
ok(!/请登录/.test(vault.replace(/\/\*[\s\S]*?\*\//g, "")), "话术不是一句「请登录」（剥注释后查）");
ok(read.includes("wdsr-fav") && /SDEVault\.fav/.test(read), "陪读浮层按钮已接 fav");
ok(!/fetch\("\/api\/im"/.test(read.slice(read.indexOf("wdsr-fav"))), "浮层不自拼 /api/im，纪律只在模块里");


console.log("── 9. E 维度：S 的两个库进聊天现场，且 @WDS 看得见");
const wsrc = src;
ok(/_wdsLibContext/.test(wsrc), "后端有 _wdsLibContext");
const lc = wsrc.slice(wsrc.indexOf("async _wdsLibContext"), wsrc.indexOf("async answerWDS"));
ok(/op: "lbpub"/.test(lc) && /op: "vtfeed"/.test(lc), "两个库都取（文章推荐位＋思想库存）");
ok(/_dirCall/.test(lc), "走目录 DO（库不在聊天室这个 DO 里）");
ok(/catch \(e\) \{ return ""; \}/.test(lc), "取不到静默返空——上下文是加分项不是门禁");
ok(/x\.sep/.test(lc), "推荐位带上推荐人写的分离线（那才是有信息的部分）");
ok(/libCtx/.test(wsrc) && /\+ \(libCtx \|\| ""\)/.test(wsrc), "已注入 @WDS 的 user 消息");
ok(page.includes('id="b-ins"'), "聊天输入区有 📎");
ok(page.includes('id="inspanel"'), "用的是自建面板");
const insSeg = page.slice(page.indexOf("function insWire"), page.indexOf("function lbWire"));
ok(!/el\("epanel"\)\.innerHTML/.test(insSeg), "★ 不覆盖表情面板的内容（曾写错，会永久毁掉表情格子）");
ok(/classList\.toggle\("on"\)/.test(insSeg), "按既有机制用 .on 类开关，不是 style.display");
ok(/lbGo\("talk"/.test(insSeg) && /vtGo\("talk"/.test(insSeg), "两个库都接进聊天，且 from=talk 好让返回键回会话");
ok(/it&&it\.text/.test(insSeg) || /it\.text/.test(insSeg), "★ vtPick 回调收到的是整条记录，取 it.text（不是字符串）");
ok(/replace\(\/\\s\+\$\/,""\)/.test(insSeg), "插入是追加不是覆盖");

console.log(`\n${P} PASS / ${F} FAIL`);
process.exit(F ? 1 : 0);
