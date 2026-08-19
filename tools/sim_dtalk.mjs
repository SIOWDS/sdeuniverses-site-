// 讨论回流（dc:/dn:）DO 层模拟——装载 src/worker.js 的 CommentBox，用假存储跑真逻辑。
import { CommentBox } from "../src/worker.js";

function fakeStorage() {
  const m = new Map();
  return {
    _m: m,
    async get(k) { return m.has(k) ? JSON.parse(JSON.stringify(m.get(k))) : undefined; },
    async put(k, v) { m.set(k, JSON.parse(JSON.stringify(v))); },
    async delete(k) {
      if (Array.isArray(k)) { let n = 0; for (const x of k) if (m.delete(x)) n++; return n; }
      return m.delete(k);
    },
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
Date.now = () => clock;

async function dir(p) {
  const r = await box.fetch(new Request("https://do/_dir", {
    method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(p),
  }));
  return await r.json();
}
let pass = 0, fail = 0;
const ok = (n, c, x) => { if (c) { pass++; console.log("  ✓ " + n); } else { fail++; console.log("  ✗ " + n + (x !== undefined ? "  ← " + JSON.stringify(x) : "")); } };

const A = "aaaaaaaaaaaa", B = "bbbbbbbbbbbb", C = "cccccccccccc";

console.log("\n=== 1. 一条发言进全站流并定向提醒 ===");
clock += 1000;
let r = await dir({
  op: "dcpost", slug: "students/zhang-qiong/inner-pointing", title: "内指", name: "高鹏", uid: B,
  text: "这一节我不同意", targets: [{ uid: A, k: "mine" }],
});
ok("落库成功", r.ok && r.id, r);
ok("提醒发出去 1 条", r.notified === 1, r);
let f = await dir({ op: "dcfeed", uid: C });
ok("全站流看得到", f.posts.length === 1 && f.posts[0].name === "高鹏", f.posts);
ok("带着文章标题与 slug", f.posts[0].title === "内指" && f.posts[0].slug === "students/zhang-qiong/inner-pointing");
let n = await dir({ op: "dcnews", uid: A });
ok("作者收到「在你的文章下」", n.news.length === 1 && n.news[0].k === "mine", n.news);
n = await dir({ op: "dcnews", uid: A });
ok("取过一次就清零", n.news.length === 0);

console.log("\n=== 2. 自己不提醒自己、同一人只提醒一次 ===");
clock += 1000;
r = await dir({
  op: "dcpost", slug: "students/zhang-qiong/inner-pointing", title: "内指", name: "张琼", uid: A,
  text: "我来回一句", reply: 1,
  targets: [{ uid: A, k: "mine" }, { uid: B, k: "reply" }, { uid: B, k: "join" }],
});
ok("作者自己发言不提醒自己、B 只收一次", r.notified === 1, r);
n = await dir({ op: "dcnews", uid: B });
ok("B 收到的是「回复了你」而不是「也在这一帖里」", n.news.length === 1 && n.news[0].k === "reply", n.news);
n = await dir({ op: "dcnews", uid: A });
ok("A 没被自己吵到", n.news.length === 0);

console.log("\n=== 3. 脏 uid 与脏 slug 挡得住 ===");
clock += 1000;
r = await dir({ op: "dcpost", slug: "../etc/passwd", name: "x", uid: B, text: "t", targets: [] });
ok("脏 slug 被挡", !r.ok, r);
r = await dir({ op: "dcpost", slug: "column/x", name: "x", uid: B, text: "t", targets: [{ uid: "不是uid", k: "join" }, { uid: "zzzz", k: "join" }] });
ok("脏 uid 被过滤，不落提醒", r.ok && r.notified === 0, r);

console.log("\n=== 4. 倒序与翻页 ===");
for (let i = 0; i < 5; i++) { clock += 1000; await dir({ op: "dcpost", slug: "column/x" + i, title: "第" + i + "篇", name: "人" + i, uid: C, text: "话" + i, targets: [] }); }
const p1 = await dir({ op: "dcfeed", uid: A, limit: 3 });
ok("第一页 3 条 + more", p1.posts.length === 3 && p1.more === true);
ok("最新的在最前", p1.posts[0].text === "话4", p1.posts.map((x) => x.text));
const p2 = await dir({ op: "dcfeed", uid: A, limit: 3, after: p1.next });
ok("第二页接得上、不重复", p2.posts.length === 3 && !p2.posts.some((x) => p1.posts.find((y) => y.id === x.id)), p2.posts.map((x) => x.text));

console.log("\n=== 5. 小红点 ===");
let bd = await dir({ op: "dcbadge", uid: A });
ok("A 刚看过 feed，没有新的", bd.fresh === 0, bd);
ok("最后一条摘要带得回来", bd.last && bd.last.text === "话4", bd.last);
clock += 5000;
await dir({ op: "dcpost", slug: "column/zz", title: "新文", name: "新人", uid: B, text: "新话", targets: [{ uid: A, k: "join" }] });
bd = await dir({ op: "dcbadge", uid: A });
ok("有新讨论 → fresh=1", bd.fresh === 1, bd);
ok("未读提醒数 1", bd.n === 1, bd);
await dir({ op: "dcfeed", uid: A });
bd = await dir({ op: "dcbadge", uid: A });
ok("看过 feed 后 fresh 归零", bd.fresh === 0, bd);
ok("但提醒数不因看 feed 而清（要点开才清）", bd.n === 1, bd);
await dir({ op: "dcnews", uid: A });
bd = await dir({ op: "dcbadge", uid: A });
ok("点开提醒后才清零", bd.n === 0, bd);

console.log("\n=== 6. 只留最近 400 条 ===");
for (let i = 0; i < 410; i++) { clock += 10; await dir({ op: "dcpost", slug: "column/bulk", title: "批量", name: "批", uid: C, text: "第" + i, targets: [] }); }
const keys = [...st._m.keys()].filter((k) => k.startsWith("dc:"));
ok("总条数被压在 400", keys.length === 400, keys.length);
const top = await dir({ op: "dcfeed", uid: C, limit: 1 });
ok("留下的是最新的那批", top.posts[0].text === "第409", top.posts[0]);

console.log("\n=== 7. 提醒队列上限 60 ===");
for (let i = 0; i < 70; i++) { clock += 10; await dir({ op: "dcpost", slug: "column/spam", name: "刷", uid: C, text: "扰" + i, targets: [{ uid: A, k: "join" }] }); }
bd = await dir({ op: "dcbadge", uid: A });
ok("提醒最多留 60 条", bd.n === 60, bd);
n = await dir({ op: "dcnews", uid: A });
ok("取出来也是 60 条且最新在前", n.news.length === 60 && n.news[0].text === "扰69", n.news[0]);

console.log("\n=== 8. 朋友圈那套没被搅到 ===");
clock += 1000;
await dir({ op: "hello", uid: A, name: "张琼" });
const mp = await dir({ op: "mopost", uid: A, name: "张琼", text: "一条朋友圈" });
ok("朋友圈照常能发", mp.ok, mp);
const mf = await dir({ op: "mofeed", uid: B });
ok("朋友圈时间线没混进讨论", mf.posts.length === 1 && mf.posts[0].text === "一条朋友圈", mf.posts.length);
const mb = await dir({ op: "mobadge", uid: B });
ok("朋友圈红点与讨论红点互不干扰", mb.ok && typeof mb.fresh === "number", mb);

console.log("\n———— " + pass + " 过 / " + fail + " 败 ————\n");
process.exit(fail ? 1 : 0);
