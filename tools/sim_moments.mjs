// 朋友圈（moments）DO 层模拟——直接装载 src/worker.js 里的 CommentBox，用假存储跑真逻辑。
// 跑法：node tools/sim_moments.mjs
import { CommentBox } from "../src/worker.js";

/* ── 假的 DO 存储：Map + 按键排序的 list（含 prefix/limit/startAfter）── */
function fakeStorage() {
  const m = new Map();
  return {
    _m: m,
    async get(k) { return m.has(k) ? JSON.parse(JSON.stringify(m.get(k))) : undefined; },
    async put(k, v) { m.set(k, JSON.parse(JSON.stringify(v))); },
    async delete(k) { return m.delete(k); },
    async list(o = {}) {
      let ks = [...m.keys()].sort();
      if (o.prefix) ks = ks.filter((k) => k.startsWith(o.prefix));
      if (o.startAfter) ks = ks.filter((k) => k > o.startAfter);
      if (o.reverse) ks.reverse();
      if (o.limit) ks = ks.slice(0, o.limit);
      const out = new Map();
      for (const k of ks) out.set(k, JSON.parse(JSON.stringify(m.get(k))));
      return out;
    },
  };
}

const st = fakeStorage();
const box = new CommentBox({ storage: st, acceptWebSocket() {}, getWebSockets() { return []; } }, {});
let clock = 1750000000000;
const realNow = Date.now;
Date.now = () => clock;

async function dir(payload) {
  const r = await box.fetch(new Request("https://do/_dir", {
    method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(payload),
  }));
  return await r.json();
}

let pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; console.log("  ✓ " + name); }
  else { fail++; console.log("  ✗ " + name + (extra ? "  ← " + JSON.stringify(extra) : "")); }
}

const A = "aaaaaaaaaaaa", B = "bbbbbbbbbbbb", C = "cccccccccccc";

console.log("\n=== 1. 登记三个人，各发一条 ===");
for (const [u, n] of [[A, "张琼"], [B, "高鹏"], [C, "胡敏"]]) await dir({ op: "hello", uid: u, name: n });
clock += 1000; const p1 = await dir({ op: "mopost", uid: A, name: "张琼", text: "第一条", imgs: [] });
clock += 6000; const p2 = await dir({ op: "mopost", uid: B, name: "高鹏", text: "第二条", imgs: ["0123456789abcdef"] });
clock += 6000; const p3 = await dir({ op: "mopost", uid: A, name: "张琼", text: "第三条", imgs: [] });
ok("三条都发出去了", p1.ok && p2.ok && p3.ok, { p1, p2, p3 });
ok("图片键被收下了", (p2.post.imgs || []).length === 1);

console.log("\n=== 2. 时间线是倒序的 ===");
let f = await dir({ op: "mofeed", uid: C, limit: 20 });
ok("三条都在", f.posts.length === 3, f.posts.map((x) => x.text));
ok("最新的在最前", f.posts[0].text === "第三条" && f.posts[2].text === "第一条", f.posts.map((x) => x.text));
ok("别人的动态 mine=0", f.posts.every((x) => !x.mine));

console.log("\n=== 3. 翻页（startAfter 不重不漏）===");
const f1 = await dir({ op: "mofeed", uid: C, limit: 2 });
ok("第一页两条 + more", f1.posts.length === 2 && f1.more === true);
const f2 = await dir({ op: "mofeed", uid: C, limit: 2, after: f1.next });
ok("第二页一条 + 没有更多", f2.posts.length === 1 && f2.more === false, f2);
const ids = f1.posts.concat(f2.posts).map((x) => x.id);
ok("两页合起来正好是三条、无重复", new Set(ids).size === 3);

console.log("\n=== 4. 只看某人的 ===");
const fa = await dir({ op: "mofeed", uid: C, who: A });
ok("张琼名下两条", fa.posts.length === 2 && fa.posts.every((x) => x.uid === A), fa.posts.map((x) => x.name));
ok("个人页也是倒序", fa.posts[0].text === "第三条");

console.log("\n=== 5. 点赞：开关、去重、不误伤 ===");
let L = await dir({ op: "molike", uid: C, name: "胡敏", id: p1.post.id });
ok("赞上了", L.ok && L.on === 1 && L.likes.length === 1);
L = await dir({ op: "molike", uid: C, name: "胡敏", id: p1.post.id });
ok("再点一次＝取消", L.on === 0 && L.likes.length === 0);
await dir({ op: "molike", uid: C, name: "胡敏", id: p1.post.id });
await dir({ op: "molike", uid: B, name: "高鹏", id: p1.post.id });
L = await dir({ op: "molike", uid: B, name: "高鹏", id: p1.post.id });
ok("高鹏取消后只剩胡敏", L.likes.length === 1 && L.likes[0].uid === C, L.likes);
f = await dir({ op: "mofeed", uid: C, who: A });
ok("胡敏看自己赞过的 liked=1", f.posts.find((x) => x.id === p1.post.id).liked === 1);
f = await dir({ op: "mofeed", uid: B, who: A });
ok("高鹏看同一条 liked=0", f.posts.find((x) => x.id === p1.post.id).liked === 0);
ok("赞不存在的动态被挡", !(await dir({ op: "molike", uid: C, id: "0000000000000000:deadbeef" })).ok);
ok("乱格式的 id 被挡", !(await dir({ op: "molike", uid: C, id: "../mo:x" })).ok);

console.log("\n=== 6. 评论与回复 ===");
let Cm = await dir({ op: "mocmt", uid: B, name: "高鹏", id: p1.post.id, text: "说得好" });
ok("评论进去了", Cm.ok && Cm.cmts.length === 1);
const cid1 = Cm.cmts[0].cid;
Cm = await dir({ op: "mocmt", uid: C, name: "胡敏", id: p1.post.id, text: "同意", rid: cid1 });
ok("回复带上了被回复人", Cm.cmts[1].rname === "高鹏" && Cm.cmts[1].rid === cid1, Cm.cmts[1]);
ok("空评论被挡", !(await dir({ op: "mocmt", uid: B, name: "高鹏", id: p1.post.id, text: "   " })).ok);

console.log("\n=== 7. 删评论的权限 ===");
let D = await dir({ op: "mocdel", uid: C, id: p1.post.id, cid: cid1 });
ok("胡敏删不了高鹏的评论", !D.ok && D.code === 403, D);
D = await dir({ op: "mocdel", uid: A, id: p1.post.id, cid: cid1 });
ok("楼主可以删自己楼里的评论", D.ok && D.cmts.length === 1, D);
const cid2 = D.cmts[0].cid;
D = await dir({ op: "mocdel", uid: C, id: p1.post.id, cid: cid2 });
ok("本人可以删自己的评论", D.ok && D.cmts.length === 0);

console.log("\n=== 8. 提醒：谁赞了我、谁评了我 ===");
let N = await dir({ op: "monews", uid: A });
ok("张琼收到了赞与评论的提醒", N.news.length >= 3, N.news.map((x) => x.k));
ok("提醒里有 like 也有 cmt", N.news.some((x) => x.k === "like") && N.news.some((x) => x.k === "cmt"));
N = await dir({ op: "monews", uid: A });
ok("取过一次就清空", N.news.length === 0);
await dir({ op: "molike", uid: A, name: "张琼", id: p1.post.id });
N = await dir({ op: "monews", uid: A });
ok("自己赞自己不提醒自己", N.news.length === 0, N.news);
await dir({ op: "mocmt", uid: A, name: "张琼", id: p1.post.id, text: "自评" });
N = await dir({ op: "monews", uid: A });
ok("自己评自己也不提醒", N.news.length === 0);

console.log("\n=== 9. 小红点 ===");
let Bd = await dir({ op: "mobadge", uid: C });
ok("胡敏看过时间线后没有新动态", Bd.fresh === 0, Bd);
clock += 60000; await dir({ op: "mopost", uid: B, name: "高鹏", text: "新的一条" });
Bd = await dir({ op: "mobadge", uid: C });
ok("有人发新动态 → fresh=1", Bd.fresh === 1, Bd);
await dir({ op: "mofeed", uid: C, limit: 20 });
Bd = await dir({ op: "mobadge", uid: C });
ok("看过之后 fresh 归零", Bd.fresh === 0, Bd);
await dir({ op: "mocmt", uid: B, name: "高鹏", id: p3.post.id, text: "顶" });
Bd = await dir({ op: "mobadge", uid: A });
ok("有人评我 → 未读数 1", Bd.n === 1, Bd);

console.log("\n=== 10. 删动态：权限、图片键回传、索引同删 ===");
D = await dir({ op: "model", uid: C, id: p2.post.id });
ok("别人删不掉", !D.ok && D.code === 403, D);
D = await dir({ op: "model", uid: C, id: p2.post.id, force: 1 });
ok("管理员 force 删得掉", D.ok);
ok("图片键回传给路由层去清 R2", (D.imgs || [])[0] === "0123456789abcdef", D.imgs);
ok("主键没了", st._m.get("mo:" + p2.post.id) === undefined);
ok("个人索引也没了", ![...st._m.keys()].some((k) => k.startsWith("mu:" + B + ":") && k.endsWith(p2.post.id)));
f = await dir({ op: "mofeed", uid: C, limit: 20 });
ok("时间线里也没了", !f.posts.some((x) => x.id === p2.post.id));
D = await dir({ op: "model", uid: A, id: p1.post.id });
ok("本人删自己的", D.ok);
f = await dir({ op: "mofeed", uid: C, who: A });
ok("个人页跟着少一条", f.posts.length === 1);

console.log("\n=== 11. 发帖限流与空帖 ===");
ok("空文字空图被挡", !(await dir({ op: "mopost", uid: A, name: "张琼", text: "   ", imgs: [] })).ok);
clock += 10000; await dir({ op: "mopost", uid: A, name: "张琼", text: "间隔够" });
const fast = await dir({ op: "mopost", uid: A, name: "张琼", text: "紧接着又发" });
ok("5 秒内连发被挡", !fast.ok && /太快/.test(fast.msg || ""), fast);
clock += 6000;
ok("等一会儿就能发", (await dir({ op: "mopost", uid: A, name: "张琼", text: "过一会儿" })).ok);

console.log("\n=== 12. 图片键必须是 16 位十六进制 ===");
clock += 10000;
const bad = await dir({ op: "mopost", uid: B, name: "高鹏", text: "带脏键", imgs: ["../../etc/passwd", "ZZZZ", "0123456789abcdef"] });
ok("脏键被过滤、只留合法的", bad.ok && bad.post.imgs.length === 1 && bad.post.imgs[0] === "0123456789abcdef", bad.post.imgs);
clock += 10000;
const many = await dir({ op: "mopost", uid: B, name: "高鹏", text: "十张图", imgs: Array(12).fill("0123456789abcdef") });
ok("最多 9 张", many.post.imgs.length === 9);

console.log("\n=== 13. 管理面板列全部 ===");
const all = await dir({ op: "moall" });
ok("列得出来且不含图片字节", all.ok && Array.isArray(all.posts) && all.posts.every((x) => typeof x.imgs === "number"), all.posts && all.posts.length);

Date.now = realNow;
console.log("\n———— " + pass + " 过 / " + fail + " 败 ————\n");
process.exit(fail ? 1 : 0);
