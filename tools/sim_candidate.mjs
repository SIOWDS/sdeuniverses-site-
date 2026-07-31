// 候选卡与顶回（cd*）DO 层模拟——直接装载 src/worker.js 的 CommentBox，用假存储跑真逻辑。
// 跑法：node tools/sim_candidate.mjs
//
// 这一档的承重点不是"能发能看"，是**结算的三个出口**：
//   无人顶回 → 未交手；被占位者击中且作者说不出分离线 → 死格；活下来 → 已交手。
// 结算是惰性的（读 feed 时到点即算），所以时间要能拨——下面直接改 clock。
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

const A = "aaaaaaaaaaaa";   // 作者
const B = "bbbbbbbbbbbb";   // 顶回的人
const C = "cccccccccccc";   // 另一个顶回的人

let st, box, clock = 1750000000000;
Date.now = () => clock;
const H = 3600 * 1000;

function fresh() {
  st = fakeStorage();
  box = new CommentBox({ storage: st, acceptWebSocket() {}, getWebSockets() { return []; } }, {});
}
async function dir(payload) {
  const r = await box.fetch(new Request("https://do/_dir", {
    method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(payload),
  }));
  return await r.json();
}
const GOOD = {
  prop: "任何划界者都无法在自己划出的界内安置自己的划界动作",
  face: "把「规则适用于对象」与「规则适用于自身」分开",
  crit: "找一条能规定自身适用条件的规则；找到即本判断失效",
};
async function post(uid = A, extra = {}) {
  return dir(Object.assign({ op: "cdpost", uid, name: uid === A ? "张琼" : "高鹏" }, GOOD, extra));
}
async function feed(uid = A) { return dir({ op: "cdfeed", uid }); }

(async function main() {

  /* ═════ 一、落卡的三段都必填 ═════ */
  group("一、落卡");
  fresh();
  ok("承重命题太短 → 拒，并说明要压成一句能被反对的话",
    /能被反对/.test((await post(A, { prop: "短" })).msg || ""));
  ok("缺「切开的辨别面」→ 拒，理由是没法被顶回",
    /没法被顶回/.test((await post(A, { face: "" })).msg || ""));
  ok("缺「可裁决判据」→ 拒，理由是别人只能表态不能顶回",
    /只能表态/.test((await post(A, { crit: "" })).msg || ""));
  const p1 = await post();
  ok("三段齐 → 落卡成功", p1.ok === true, p1.msg);
  ok("默认状态 open", p1.card.state === "open");
  ok("顶回期是 72 小时", p1.card.due - p1.card.ts === 72 * H, (p1.card.due - p1.card.ts) / H);
  ok("个人索引也写了", (await st.get("cu:" + A + ":" + p1.card.id)) === 1);

  group("二、限流：候选贵在少而硬");
  clock += 1000;
  ok("20 秒内再发 → 拒，并明说候选卡不是发帖",
    /不是发帖/.test((await post()).msg || ""));
  clock += 30000;
  for (let i = 0; i < 9; i++) { await post(); clock += 30000; }
  ok("一天十张封顶", /十张够多/.test((await post()).msg || ""));

  /* ═════ 三、顶回只有三种 ═════ */
  group("三、顶回");
  fresh(); clock += H;
  const c1 = (await post()).card;
  ok("点赞式的动作不存在——kind 不在三种里就拒",
    /只有三种/.test((await dir({ op: "cdback", uid: B, id: c1.id, kind: "like", text: "顶" })).msg || ""));
  ok("自己顶自己不算交手",
    /不算交手/.test((await dir({ op: "cdback", uid: A, id: c1.id, kind: "rev", text: "我反对我自己" })).msg || ""));
  ok("顶回内容太短 → 拒（要能被作者回应）",
    /能被作者回应/.test((await dir({ op: "cdback", uid: B, id: c1.id, kind: "rev", text: "啊" })).msg || ""));
  const bk = await dir({ op: "cdback", uid: B, name: "高鹏", id: c1.id, kind: "occ", text: "卢曼《社会的社会》1997：观察者不能观察自己的盲点" });
  ok("给占位者 → 成功", bk.ok === true, bk.msg);
  ok("顶回带上 kind 与作者", bk.card.backs[0].kind === "occ" && bk.card.backs[0].uid === B);
  const news = await dir({ op: "cdnews", uid: A });
  ok("★ 顶回会通知卡的作者", news.items.length === 1 && news.items[0].k === "back", news.items);

  /* ═════ 四、结算的三个出口 ═════ */
  group("四、结算 · 出口一：无人顶回 → 未交手");
  fresh();
  const cA = (await post()).card;
  clock += 73 * H;
  let f = await feed();
  ok("到点自动结算，无需定时任务", f.cards[0].state !== "open", f.cards[0].state);
  ok("没人顶回 → 〔未交手〕", f.cards[0].state === "untouched", f.cards[0].state);
  ok("结算结果落库了（不是每次读都重算）", (await st.get("cd:" + cA.id)).state === "untouched");

  group("五、结算 · 出口二：被占位者击中且说不出分离线 → 死格");
  fresh();
  const cB = (await post()).card;
  clock += H;
  await dir({ op: "cdback", uid: B, name: "高鹏", id: cB.id, kind: "occ", text: "卢曼早就说过" });
  clock += 73 * H;
  f = await feed();
  ok("有 occ 顶回、作者没给分离线 → 〔死格〕", f.cards[0].state === "dead", f.cards[0].state);

  group("六、结算 · 出口三：带着分离线活下来");
  fresh();
  const cC = (await post()).card;
  clock += H;
  const r1 = await dir({ op: "cdback", uid: B, name: "高鹏", id: cC.id, kind: "occ", text: "卢曼早就说过" });
  const bid = r1.card.backs[0].bid;
  const sp = await dir({ op: "cdsep", uid: A, id: cC.id, to: bid, text: "卢曼在【观察者能否看见自己的盲点】上是不能；本条说的是【划界动作能否被安置在界内】，读法是看那条界本身有没有位置" });
  ok("作者给分离线 → 成功", sp.ok === true, sp.msg);
  clock += 73 * H;
  f = await feed();
  ok("occ 被分离线接住 → 〔活下来〕", f.cards[0].state === "alive", f.cards[0].state);

  group("七、只有反向预测/换层级，没有占位者 → 也算活下来");
  fresh();
  const cD = (await post()).card;
  clock += H;
  await dir({ op: "cdback", uid: B, name: "高鹏", id: cD.id, kind: "rev", text: "我预测在司法解释里恰恰相反" });
  await dir({ op: "cdback", uid: C, name: "胡敏", id: cD.id, kind: "lvl", text: "换到身体层级重述：疼痛不能给自己定位" });
  clock += 73 * H;
  f = await feed();
  ok("没有 occ 就没有死格的理由 → 〔活下来〕", f.cards[0].state === "alive", f.cards[0].state);
  ok("两条顶回都在", f.cards[0].backs.length === 2);

  /* ═════ 八、分离线的权限与边界 ═════ */
  group("八、分离线");
  fresh();
  const cE = (await post()).card;
  clock += H;
  const r2 = await dir({ op: "cdback", uid: B, name: "高鹏", id: cE.id, kind: "occ", text: "这条撞上了卢曼" });
  const bid2 = r2.card.backs[0].bid;
  ok("别人不能替作者给分离线",
    /只有作者/.test((await dir({ op: "cdsep", uid: B, id: cE.id, to: bid2, text: "我来替他说" })).msg || ""));
  // 注意：长度闸排在最前（还没读卡就先看字数），所以桩文本必须够长，否则测到的是长度闸不是这一条
  ok("对不存在的顶回给分离线 → 拒",
    /找不到这条顶回/.test((await dir({ op: "cdsep", uid: A, id: cE.id, to: "deadbeef", text: "凭空写一条足够长的分离线" })).msg || ""));
  ok("分离线太短 → 拒，并给出该写成什么形状",
    /是 A/.test((await dir({ op: "cdsep", uid: A, id: cE.id, to: bid2, text: "不" })).msg || ""));
  await dir({ op: "cdsep", uid: A, id: cE.id, to: bid2, text: "第一版分离线，写得不够狠" });
  const s2 = await dir({ op: "cdsep", uid: A, id: cE.id, to: bid2, text: "第二版分离线，改好了" });
  ok("同一条顶回重写分离线 → 覆盖不叠加", s2.card.seps.length === 1, s2.card.seps);
  ok("留的是最新那一版", /第二版/.test(s2.card.seps[0].text));
  const n2 = await dir({ op: "cdnews", uid: B });
  ok("★ 分离线会通知那位顶回的人（对撞是双向的）", n2.items.some((x) => x.k === "sep"), n2.items);

  /* ═════ 九、过期之后一律不许再动 ═════ */
  group("九、过期");
  fresh();
  const cF = (await post()).card;
  clock += 73 * H;
  ok("过期后不能再顶回",
    /已经结算/.test((await dir({ op: "cdback", uid: B, id: cF.id, kind: "rev", text: "迟到的顶回" })).msg || ""));
  ok("过期后作者也不能再补分离线（时限对双方一样硬）",
    /已经结算/.test((await dir({ op: "cdsep", uid: A, id: cF.id, to: "x", text: "迟到的分离线写得够长" })).msg || ""));
  ok("被拒的那一次也把状态落库了", (await st.get("cd:" + cF.id)).state === "untouched");
  // ★ 这一条是护栏抓出来的真 bug：门若写成 if(cdSettle(...))，只挡得住恰好触发结算的那一次，
  //   之后 cdSettle 返回 false，已结算的卡还能被继续顶回。第二次、第三次都要被挡住。
  ok("★ 已结算之后再顶回，第二次、第三次一样被挡",
    /已经结算/.test((await dir({ op: "cdback", uid: B, id: cF.id, kind: "rev", text: "又一次迟到的顶回" })).msg || "")
    && /已经结算/.test((await dir({ op: "cdback", uid: C, id: cF.id, kind: "lvl", text: "第三次迟到的顶回" })).msg || ""));
  ok("★ 已结算的卡上没有多出来的顶回", ((await st.get("cd:" + cF.id)).backs || []).length === 0);

  /* ═════ 十、近邻库读数随卡落库 ═════ */
  group("十、近邻读数");
  fresh();
  const cG = (await post(A, {
    nbr: { status: "hit", verdict: "占位：卢曼《社会的社会》1997　等 3 家",
           hits: [{ prop: "观察者无法观察自己的盲点", who: "卢曼" }, { prop: "x", who: "y" }] },
    picks: ["胡敏", "孔凡鹤"],
  })).card;
  ok("落卡时把近邻库读数一起存下来（不必每次重查）", cG.nbr && /卢曼/.test(cG.nbr.verdict), cG.nbr);
  ok("命中项被裁到 5 条以内", (cG.nbr.hits || []).length === 2);
  ok("点将名单也存下来", cG.picks.length === 2, cG.picks);
  clock += 30000;   // 20 秒限流是真的，桩也要守（否则测到的是限流不是这一条）
  const cH = (await post(A, { nbr: null })).card;
  ok("没给近邻读数也能落卡（库未命中不是拦路）", cH.ok !== false && cH.nbr === null);

  /* ═════ 十一、删除 ═════ */
  group("十一、删除");
  fresh();
  const cI = (await post()).card;
  ok("别人删不掉", /只能删自己/.test((await dir({ op: "cddel", uid: B, id: cI.id })).msg || ""));
  ok("自己能删", (await dir({ op: "cddel", uid: A, id: cI.id })).ok === true);
  ok("个人索引也一并删", (await st.get("cu:" + A + ":" + cI.id)) === undefined);

  /* ═════ 十二、时间序与"只看他的" ═════ */
  group("十二、时间序");
  fresh();
  const x1 = (await post(A)).card; clock += 60000;
  const x2 = (await post(B)).card; clock += 60000;
  const x3 = (await post(A)).card;
  f = await feed();
  ok("时间线倒序（最新在前）", f.cards[0].id === x3.id && f.cards[2].id === x1.id,
    f.cards.map((c) => c.name));
  const mine = await dir({ op: "cdfeed", uid: A, who: A });
  ok("只看某人 → 只出他的两张", mine.cards.length === 2 && mine.cards.every((c) => c.uid === A), mine.cards.length);
  ok("未读角标算得出", (await dir({ op: "cdbadge", uid: A })).ok === true);

  console.log("\n" + "═".repeat(52));
  console.log("  通过 " + pass + " / " + (pass + fail) + (fail ? "   ✗ 失败 " + fail : "   全绿"));
  console.log("═".repeat(52));
  process.exit(fail ? 1 : 0);
})().catch((e) => { console.error("\n模拟自身崩了：", e); process.exit(1); });
