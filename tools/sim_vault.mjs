// 思想库存（vt*）DO 层模拟——装真 CommentBox＋假存储跑真逻辑。
// 跑法：node tools/sim_vault.mjs
//
// 库存是**全站共用的一池**：对话侧存进来、朋友圈「说点什么」从里面取、候选卡从里面升格。
// 它与候选卡是**两个门槛，一条通路**——库存低门槛（一句话就存）先接住，够硬的再升格。
// 最容易出错的三处：①同一句被反复存成许多条（库存要能翻，不能被刷屏）
// ②「随便翻翻／还没被用过／我存的」三种取法互相串味 ③别人的东西被删掉。
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

const A = "aaaaaaaaaaaa", B = "bbbbbbbbbbbb";
let st, box, clock = 1750000000000;
Date.now = () => clock;

function fresh() {
  st = fakeStorage();
  box = new CommentBox({ storage: st, acceptWebSocket() {}, getWebSockets() { return []; } }, {});
}
async function dir(p) {
  const r = await box.fetch(new Request("https://do/_dir", {
    method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(p),
  }));
  return await r.json();
}
const add = (uid, text, kind, src) => dir({ op: "vtadd", uid, name: uid === A ? "张琼" : "高鹏", text, kind, src });

(async function main() {

  group("一、存进去");
  fresh();
  ok("太短的不存，并说明要存一句能站住的话",
    /能站住的话/.test((await add(A, "嗯")).msg || ""));
  const r1 = await add(A, "划界者的拇指不在指纹里", "name", "涌现档 · 换母学科");
  ok("四个字以上就能存（门槛故意放低）", r1.ok === true, r1.msg);
  ok("类型与出处都留下来", r1.item.kind === "name" && /涌现档/.test(r1.item.src));
  ok("默认取用次数为 0", r1.item.used === 0);
  ok("个人索引也写了", (await st.get("vu:" + A + ":" + r1.item.id)) === 1);
  clock += 1000;
  const bad = await add(A, "随便一句", "不存在的类型");
  ok("类型不认识时落回「观察」，不报错", bad.ok === true && bad.item.kind === "note", bad.item && bad.item.kind);

  group("二、去重：库存要能翻，不能被刷屏");
  fresh();
  const d1 = await add(A, "同一句话被存了两遍");
  clock += 1000;
  const d2 = await add(A, "同一句话被存了两遍");
  ok("同一个人存同一句 → 返回原条，不新增", d2.ok === true && d2.dup === 1 && d2.item.id === d1.item.id, d2);
  const f0 = await dir({ op: "vtfeed", uid: A });
  ok("库里确实只有一条", f0.items.length === 1, f0.items.length);
  clock += 1000;
  await add(B, "同一句话被存了两遍");
  const f1 = await dir({ op: "vtfeed", uid: A });
  ok("★ 不同的人存同一句是两条（去重只在个人范围内，不替别人做主）", f1.items.length === 2, f1.items.length);

  group("三、三种取法互不串味");
  fresh();
  const ids = [];
  for (let i = 0; i < 6; i++) { const r = await add(i < 4 ? A : B, "第 " + i + " 条库存的话"); ids.push(r.item.id); clock += 1000; }
  await dir({ op: "vtuse", uid: A, id: ids[0] });
  await dir({ op: "vtuse", uid: A, id: ids[1] });
  const all = await dir({ op: "vtfeed", uid: A });
  ok("最新：六条都在", all.items.length === 6, all.items.length);
  ok("时间倒序（最新在最前）", /第 5 条/.test(all.items[0].text), all.items[0].text);
  const onlyFresh = await dir({ op: "vtfeed", uid: A, fresh: 1 });
  ok("「还没被用过」只剩四条", onlyFresh.items.length === 4, onlyFresh.items.length);
  ok("被用过的确实不在里面", !onlyFresh.items.some((x) => x.id === ids[0] || x.id === ids[1]));
  const mine = await dir({ op: "vtfeed", uid: A, who: A });
  ok("「我存的」只出自己的四条", mine.items.length === 4 && mine.items.every((x) => x.uid === A), mine.items.length);
  const pick = await dir({ op: "vtfeed", uid: A, pick: 1, limit: 6 });
  ok("「随便翻翻」条数不变，只是次序被洗过", pick.items.length === 6);
  ok("随机取法不会凭空造条目", pick.items.every((x) => ids.indexOf(x.id) >= 0));

  group("四、取用计数");
  fresh();
  const u = (await add(A, "被反复取用的一句话")).item;
  await dir({ op: "vtuse", uid: B, id: u.id });
  const u2 = await dir({ op: "vtuse", uid: B, id: u.id });
  ok("每取一次加一", u2.used === 2, u2.used);
  ok("★ 别人也能取用（库存是共用的一池，不是私人收藏）", u2.ok === true);
  ok("取用不存在的条目 → 明说已经不在了",
    /已经不在了/.test((await dir({ op: "vtuse", uid: A, id: "nope" })).msg || ""));

  group("五、删除");
  fresh();
  const v = (await add(A, "只有作者能删的一句话")).item;
  ok("别人删不掉，并说明只能删自己存的",
    /只能删自己存的/.test((await dir({ op: "vtdel", uid: B, id: v.id })).msg || ""));
  ok("自己能删", (await dir({ op: "vtdel", uid: A, id: v.id })).ok === true);
  ok("个人索引一并删", (await st.get("vu:" + A + ":" + v.id)) === undefined);
  ok("删完库里就空了", (await dir({ op: "vtfeed", uid: A })).items.length === 0);

  group("六、与候选卡是两个门槛、一条通路");
  fresh();
  const short = await add(A, "一个还没成型的命名");
  ok("★ 库存收得下候选卡收不下的东西（一句话就行，没有三段硬门）", short.ok === true);
  const card = await dir({
    op: "cdpost", uid: A, name: "张琼",
    prop: short.item.text, face: "", crit: "",
  });
  ok("★ 同一句话直接去立候选卡会被拦（三段硬门仍在，库存不是绕过它的后门）",
    card.ok === false && /辨别面/.test(card.msg || ""), card.msg);
  const card2 = await dir({
    op: "cdpost", uid: A, name: "张琼",
    prop: short.item.text,
    face: "把「已经成型的命名」与「还在成型中的命名」分开",
    crit: "找到一个一出生就完整的命名，本判断即失效",
  });
  ok("补齐另两段之后就能升格", card2.ok === true, card2.msg);

  console.log("\n" + "═".repeat(52));
  console.log("  通过 " + pass + " / " + (pass + fail) + (fail ? "   ✗ 失败 " + fail : "   全绿"));
  console.log("═".repeat(52));
  process.exit(fail ? 1 : 0);
})().catch((e) => { console.error("\n模拟自身崩了：", e); process.exit(1); });
