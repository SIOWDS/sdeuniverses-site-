// 身份归一（amerge）DO 层模拟——直接装载 src/worker.js 里的 CommentBox，用假存储跑真逻辑。
// 照 tools/sim_moments.mjs 的套路（记忆里那条：这套比源码检视式 sim 强得多）。
// 跑法：node tools/sim_merge.mjs
//
// 为什么要有它：国内走口令、海外走 Google，是两拨真实的人，两个入口都得留；
// 但 uid 一个从名字派生、一个从 Google sub 派生 ⇒ 同一个人换通道进来就是另一个人。
// 合并要搬的东西横跨群籍／会话两向／朋友圈三张表／提醒队列，**漏一处就是数据丢失且不报错**，
// 所以每一处都要单独钉住，还要钉住"不该动的没被动"。
import { CommentBox } from "../src/worker.js";

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

let pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; console.log("  ✓ " + name); }
  else { fail++; console.log("  ✗ " + name + (extra !== undefined ? "  ← " + JSON.stringify(extra) : "")); }
}
function group(n) { console.log("\n【" + n + "】"); }

const OLD = "7cbeafe2e6ed";   // 海外 Google 身份（真实存在于线上通讯录）
const NEW = "111111111111";   // 名录名派生出的口令身份
const P1 = "222222222222";    // 一个旁人
const P2 = "333333333333";    // 另一个旁人

let st, box, clock = 1750000000000;
Date.now = () => clock;

async function dir(payload) {
  const r = await box.fetch(new Request("https://do/_dir", {
    method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(payload),
  }));
  return await r.json();
}

/* 造一份"合并前"的现场：旧身份在两个群、两个会话、发过动态、赞过别人、评过别人、有提醒 */
async function seed() {
  st = fakeStorage();
  box = new CommentBox({ storage: st, acceptWebSocket() {}, getWebSockets() { return []; } }, {});
  const s = st;
  await s.put("u:" + OLD, { name: "Desheng Wang", ts: 1000 });
  await s.put("u:" + NEW, { name: "王德生", ts: 2000 });
  await s.put("u:" + P1, { name: "张琼", ts: 1500 });
  await s.put("u:" + P2, { name: "高鹏", ts: 1500 });

  // 群：g1 旧身份是群主；g2 旧身份是成员，且新身份也已在里面（考验去重）
  await s.put("g:g1", { gid: "g1", name: "改姓训练", owner: OLD, members: [OLD, P1] });
  await s.put("gm:" + OLD + ":g1", 1); await s.put("gm:" + P1 + ":g1", 1);
  await s.put("g:g2", { gid: "g2", name: "医学组", owner: P1, members: [P1, OLD, NEW] });
  await s.put("gm:" + OLD + ":g2", 1); await s.put("gm:" + P1 + ":g2", 1); await s.put("gm:" + NEW + ":g2", 1);

  // 会话：一条群会话、一条私聊；另有旁人指向旧身份的私聊索引
  await s.put("ib:" + OLD + ":G_g1", { kind: "g", gid: "g1", last: "群里最后一句", lastTs: 900, unread: 0 });
  await s.put("ib:" + OLD + ":" + P1, { kind: "dm", peer: P1, last: "私聊最后一句", lastTs: 800, unread: 3 });
  await s.put("ib:" + P1 + ":" + OLD, { kind: "dm", peer: OLD, last: "张琼这边看到的最后一句", lastTs: 800, unread: 0 });

  // 朋友圈：旧身份发过一条；在别人那条底下点过赞、评过论
  await s.put("mo:inv1:aaa", { id: "inv1:aaa", uid: OLD, name: "Desheng Wang", text: "旧身份发的", imgs: [], ts: 700, likes: [], cmts: [] });
  await s.put("mu:" + OLD + ":inv1:aaa", 1);
  await s.put("mo:inv2:bbb", {
    id: "inv2:bbb", uid: P1, name: "张琼", text: "张琼发的", imgs: [], ts: 600,
    likes: [{ uid: OLD, name: "Desheng Wang", ts: 610 }, { uid: P2, name: "高鹏", ts: 620 }],
    cmts: [{ id: "c1", uid: OLD, name: "Desheng Wang", text: "旧身份的评论", ts: 630 }],
  });
  await s.put("mu:" + P1 + ":inv2:bbb", 1);

  // 提醒与限流
  await s.put("mn:" + OLD, { q: [{ k: "like", ts: 640 }, { k: "cmt", ts: 650 }], seen: 100 });
  await s.put("mn:" + NEW, { q: [{ k: "like", ts: 660 }], seen: 200 });
  await s.put("morl:" + OLD, [500, 600]);
}

(async function main() {

  /* ═════ 一、顺跑：一切都改挂过去 ═════ */
  group("一、顺跑");
  await seed();
  const d = await dir({ op: "amerge", from: OLD, to: NEW, toName: "王德生" });
  ok("返回 ok", d.ok === true, d);
  ok("报出两边的名字", d.fromName === "Desheng Wang" && d.toName === "王德生", d);

  group("二、群籍");
  ok("gm 索引改挂到新身份", (await st.get("gm:" + NEW + ":g1")) === 1);
  ok("旧 gm 索引已删", (await st.get("gm:" + OLD + ":g1")) === undefined);
  const g1 = await st.get("g:g1");
  ok("群成员数组里换成新身份", g1.members.includes(NEW) && !g1.members.includes(OLD), g1.members);
  ok("旧身份是群主时，群主也跟着改（不留无主群）", g1.owner === NEW, g1.owner);
  const g2 = await st.get("g:g2");
  ok("两个身份本来都在同一个群时，成员去重不重复计", g2.members.filter((x) => x === NEW).length === 1, g2.members);
  ok("群里的旁人一个都没动", g2.members.includes(P1) && g1.members.includes(P1));
  ok("报出的群数对得上", d.groups === 2, d.groups);

  group("三、会话（两向）");
  ok("群会话改挂到新身份", !!(await st.get("ib:" + NEW + ":G_g1")));
  const gConv = await st.get("ib:" + NEW + ":G_g1");
  ok("★ 群会话的 last 原样保留（群房号是 g/<gid>，与 uid 无关，历史不受影响）",
    gConv.last === "群里最后一句", gConv.last);
  const dm = await st.get("ib:" + NEW + ":" + P1);
  ok("私聊会话也改挂过去（会话在，人找得到）", !!dm);
  ok("★ 但私聊的 last 被如实改写，不假装历史搬走了",
    /合并前的私聊记录不在此处/.test(dm.last || ""), dm.last);
  ok("私聊未读清零（旧未读对新身份没有意义）", dm.unread === 0);
  ok("旁人指向旧身份的索引也改成指向新身份", !!(await st.get("ib:" + P1 + ":" + NEW)));
  ok("旁人那条旧索引已删（不留悬空指向）", (await st.get("ib:" + P1 + ":" + OLD)) === undefined);
  ok("旧身份自己的会话索引全删", (await st.get("ib:" + OLD + ":" + P1)) === undefined);
  ok("报出的会话数与私聊丢失数分开算", d.convs === 2 && d.dmLost === 1, { convs: d.convs, dmLost: d.dmLost });

  group("四、朋友圈");
  const post = await st.get("mo:inv1:aaa");
  ok("自己发的动态改作者", post.uid === NEW, post.uid);
  ok("动态上的署名也换成新名字", post.name === "王德生", post.name);
  ok("个人索引改挂", (await st.get("mu:" + NEW + ":inv1:aaa")) === 1
    && (await st.get("mu:" + OLD + ":inv1:aaa")) === undefined);
  const other = await st.get("mo:inv2:bbb");
  ok("★ 在别人动态下点的赞也改（否则那个赞就成了幽灵）",
    other.likes.some((l) => l.uid === NEW) && !other.likes.some((l) => l.uid === OLD), other.likes);
  ok("★ 在别人动态下写的评论也改", other.cmts.every((c) => c.uid !== OLD) && other.cmts.some((c) => c.uid === NEW));
  ok("别人的赞一个没动", other.likes.some((l) => l.uid === P2 && l.name === "高鹏"));
  ok("别人的动态作者没被误改", other.uid === P1);
  ok("报数对得上", d.posts === 1 && d.likes === 1 && d.cmts === 1, { p: d.posts, l: d.likes, c: d.cmts });

  group("五、提醒与收尾");
  const mn = await st.get("mn:" + NEW);
  ok("提醒队列并进新身份，两边都在", mn.q.length === 3, mn.q.length);
  ok("seen 取两者较大（不把已看过的又标成未读）", mn.seen === 200, mn.seen);
  ok("旧提醒队列已删", (await st.get("mn:" + OLD)) === undefined);
  ok("发帖限流是临时量，不搬且清掉", (await st.get("morl:" + OLD)) === undefined);
  ok("旧通讯录条目已删", (await st.get("u:" + OLD)) === undefined);
  const uNew = await st.get("u:" + NEW);
  ok("新身份在通讯录里且用名录名", uNew && uNew.name === "王德生", uNew);
  const al = await st.get("alias:" + OLD);
  ok("留一条改绑痕迹便于日后追查", al && al.to === NEW && al.fromName === "Desheng Wang", al);

  group("六、留痕可列");
  const la = await dir({ op: "aaliases" });
  ok("aaliases 列得出来", la.ok && la.aliases.length === 1, la);
  ok("留痕里两边的名字都在", la.aliases[0].fromName === "Desheng Wang" && la.aliases[0].toName === "王德生");

  /* ═════ 七、拒绝该拒绝的 ═════ */
  group("七、参数与边界");
  await seed();
  ok("uid 格式不对 → 拒", !(await dir({ op: "amerge", from: "xx", to: NEW })).ok);
  ok("两个 uid 相同 → 拒，并说明不用合并",
    /不用合并/.test(((await dir({ op: "amerge", from: NEW, to: NEW })).msg) || ""));
  ok("旧身份根本不在通讯录里 → 拒",
    /不在通讯录/.test(((await dir({ op: "amerge", from: "999999999999", to: NEW })).msg) || ""));

  /* ═════ 八、目标身份此前完全不存在（海外的人第一次用口令进来之前） ═════ */
  group("八、目标身份此前不存在");
  await seed();
  await st.delete("u:" + NEW);
  await st.delete("gm:" + NEW + ":g2");
  const g2b = await st.get("g:g2"); g2b.members = [P1, OLD]; await st.put("g:g2", g2b);
  const d2 = await dir({ op: "amerge", from: OLD, to: NEW, toName: "王德生" });
  ok("目标不存在也能合并（顺手把他建进通讯录）", d2.ok === true, d2);
  const u2 = await st.get("u:" + NEW);
  ok("新条目用的是传进来的名录名", u2 && u2.name === "王德生", u2);
  ok("群籍照样搬到位", (await st.get("gm:" + NEW + ":g1")) === 1);

  /* ═════ 九、幂等：同一次合并跑两遍不该出乱子 ═════ */
  group("九、跑两遍");
  await seed();
  await dir({ op: "amerge", from: OLD, to: NEW, toName: "王德生" });
  const again = await dir({ op: "amerge", from: OLD, to: NEW, toName: "王德生" });
  ok("第二遍找不到旧身份，直接拒（不会把新身份的数据搅坏）",
    !again.ok && /不在通讯录/.test(again.msg || ""), again);
  const g1b = await st.get("g:g1");
  ok("跑两遍之后群成员仍然只有一份新身份", g1b.members.filter((x) => x === NEW).length === 1, g1b.members);
  ok("跑两遍之后动态作者仍是新身份", (await st.get("mo:inv1:aaa")).uid === NEW);

  console.log("\n" + "═".repeat(52));
  console.log("  通过 " + pass + " / " + (pass + fail) + (fail ? "   ✗ 失败 " + fail : "   全绿"));
  console.log("═".repeat(52));
  process.exit(fail ? 1 : 0);
})().catch((e) => { console.error("\n模拟自身崩了：", e); process.exit(1); });
