/* 近邻库护栏 tools/sim_nbr.js
 *
 * 不做源码检视式断言，而是**把 sde-nbr.js 真跑一遍**：
 * 造最小 window + fetch 桩喂真的 cards.json，再拿真实评测集量召回。
 * 跑法：node tools/sim_nbr.js
 */
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");

let PASS = 0, FAIL = 0;
function ok(name, cond, extra) {
  if (cond) { PASS++; }
  else { FAIL++; console.log("  ✗ " + name + (extra ? "  → " + extra : "")); }
}

// ── 载入真库 ──────────────────────────────────────────
const DBJSON = JSON.parse(fs.readFileSync(path.join(ROOT, "public/nbr/cards.json"), "utf8"));

// ── 造最小环境并真载 sde-nbr.js ─────────────────────────
const w = {};
global.fetch = (u) => Promise.resolve({
  ok: true, status: 200,
  json: () => Promise.resolve(JSON.parse(JSON.stringify(DBJSON)))
});
const src = fs.readFileSync(path.join(ROOT, "public/assets/sde-nbr.js"), "utf8");
new Function("window", src)(w);
const N = w.SDENbr;

// ── 评测集：从 tools/nbr/eval.py 里抠出来（单一真相，不另抄一份） ──
function readEval() {
  const t = fs.readFileSync(path.join(ROOT, "tools/nbr/eval.py"), "utf8");
  const body = t.slice(t.indexOf("EVAL = ["));
  const re = /\("([^"]+)",\s*\[([^\]]*)\]\)/g;
  const out = []; let m;
  while ((m = re.exec(body))) {
    const want = m[2].match(/"([^"]+)"/g).map(s => s.replace(/"/g, ""));
    out.push([m[1], want]);
  }
  return out;
}
const EVAL = readEval();

(async function main() {
  console.log("近邻库护栏");

  // ①  库本身的形状
  console.log("\n[一] 库的形状");
  ok("cards.json 有卡", DBJSON.n > 0 && DBJSON.cards.length === DBJSON.n);
  ok("卡数 ≥ 60（第一版种子的下限）", DBJSON.n >= 60, "n=" + DBJSON.n);
  ok("id 唯一", new Set(DBJSON.cards.map(c => c.id)).size === DBJSON.n);
  ok("每张卡别名 ≥3（别名表是成败关键）",
    DBJSON.cards.every(c => (c.alias || []).length >= 3),
    DBJSON.cards.filter(c => (c.alias || []).length < 3).map(c => c.id).join(","));
  ok("每张卡至少一条分离线", DBJSON.cards.every(c => (c.sep || []).length >= 1));
  ok("每张卡都有 holds（它占住什么）", DBJSON.cards.every(c => !!c.holds));
  ok("每张卡都有出处 author+title",
    DBJSON.cards.every(c => c.src && c.src.author && c.src.title));
  ok("承重命题都在 80 字以内（50 字级压缩）",
    DBJSON.cards.every(c => c.prop.replace(/\s/g, "").length <= 80));
  ok("核验状态取值合法",
    DBJSON.cards.every(c => ["verified", "cited-in-context", "unverified"].indexOf(c.verify) >= 0));
  ok("预算的文法 g 非空", DBJSON.cards.every(c => (c.g || []).length > 3));

  // ②  纪律
  console.log("\n[二] 三条纪律");
  const miss = await N.ask("量子色动力学的渐近自由与夸克禁闭的格点计算", 12);
  ok("查不到时 status=miss", miss.status === "miss");
  ok("miss 的 verdict 明写〔库未命中〕",
    /库未命中/.test(miss.verdict), miss.verdict);
  ok("miss 的 verdict 明写「不得据以放行」",
    /不得据以放行/.test(miss.verdict));
  ok("miss 不返回任何 hit", miss.hits.length === 0);
  ok("verdictLine 在 miss 时也说不得放行", /库未命中/.test(N.verdictLine(miss)));
  ok("纪律②：库的路径与站内索引分开（/nbr/ 不是 /search/）",
    N.SRC.indexOf("/nbr/") === 0 && N.SRC.indexOf("search") < 0, N.SRC);
  ok("纪律③：write 形状校验存在", typeof N.shape === "function");
  ok("形状校验挡住缺分离线的卡",
    N.shape({ prop: "x", alias: ["a", "b", "c"], src: {}, holds: "h", ring: "r", sep: [] }).ok === false);
  ok("形状校验挡住别名不足 3 条的卡",
    N.shape({ prop: "x", alias: ["a"], src: { author: "x" }, holds: "h", ring: "r", sep: ["s"] }).ok === false);
  ok("形状齐备的卡放行",
    N.shape({ prop: "x", alias: ["a", "b", "c"], src: { author: "x" }, holds: "h", ring: "r", sep: ["s"] }).ok === true);

  // ③  打分口径
  console.log("\n[三] 打分口径");
  const g1 = N._grams("认知偿付力被成功结算消耗");
  ok("文法出的是汉字二元组", !!g1["认知"] && !!g1["偿付"]);
  ok("拉丁词按整词进文法", !!N._grams("ego depletion 自我损耗")["depletion"]);
  ok("归一化吃掉标点与书名号",
    N._norm("《成功之死》，一个判断。") === N._norm("成功之死一个判断"));
  ok("只撞上 1 个二元组不算命中（绝对下限 2）",
    N._score(N._grams("甲乙"), N._grams("甲乙丙丁戊己庚辛")) === 0
    || N._score({ 甲乙: 1 }, { 甲乙: 1, 丙丁: 1 }) === 0);
  ok("分母取查询侧而非 min（短卡面串不许因为短而拿高分）",
    (function () {
      const q = N._grams("一二三四五六七八九十甲乙丙丁");
      const shortC = { 一二: 1, 二三: 1 };
      return N._score(q, shortC) < 0.35;
    })());

  // ④  真实召回（唯一算数的质量指标）
  console.log("\n[四] 粗筛召回（评测集＝当天产线真实候选）");
  ok("评测集抠得出来且够大", EVAL.length >= 30, "n=" + EVAL.length);
  const R = { 1: 0, 3: 0, 5: 0, 10: 0, 12: 0, 20: 0 };
  const dead = [];
  for (const [q, want] of EVAL) {
    const res = await N.ask(q, 40);
    let pos = 999;
    res.hits.forEach((h, i) => { if (want.indexOf(h.id) >= 0 && i < pos) pos = i; });
    for (const k of Object.keys(R)) if (pos < +k) R[k]++;
    if (pos >= 12) dead.push([q.slice(0, 26), want]);
  }
  const n = EVAL.length;
  console.log("  R@1=%d/%d  R@3=%d/%d  R@5=%d/%d  R@10=%d/%d  R@12=%d/%d  R@20=%d/%d",
    R[1], n, R[3], n, R[5], n, R[10], n, R[12], n, R[20], n);
  ok("R@12 ≥ 28/35（粗筛只需把正主送进 top12，不必 top1）", R[12] >= 28, `R@12=${R[12]}`);
  ok("R@20 ≥ 32/35", R[20] >= 32, `R@20=${R[20]}`);
  ok("R@1 ≥ 20/35", R[1] >= 20, `R@1=${R[1]}`);
  ok("确实存在词面死角（若为 0 说明评测集被做软了）", dead.length > 0);
  ok("词面死角不超过 6 条", dead.length <= 6, "dead=" + dead.length);
  console.log("  词面死角 %d 条（这些只能交二级细判——纪律①的实测依据）：", dead.length);
  dead.forEach(([q, wnt]) => console.log("    · 「" + q + "…」应中 " + wnt.join(",")));

  // ⑤  那个真实的历史案例：卢曼必须被检出来
  console.log("\n[五] 历史案例复检");
  const lu = await N.ask("任何划界者都无法在自己划出的界内安置自己的划界动作，这个盲点是构成性的", 12);
  ok("《操作自盲》的承重命题能把卢曼检出来（当年 I=115 的直接病因）",
    lu.hits.some(h => h.id === "nbr-0001"),
    lu.hits.slice(0, 3).map(h => h.id).join(","));
  const forge = await N.ask("收编不发生在反抗之后，它借着反抗工具的身体先行在场", 12);
  ok("引擎室那次漏掉的洛德/马尔库塞在库里且能被检出",
    forge.hits.some(h => ["nbr-0205", "nbr-0206", "nbr-0201"].indexOf(h.id) >= 0),
    forge.hits.slice(0, 3).map(h => h.id).join(","));
  ok("洛德那张卡明写它是同向占位者、不可被推开",
    /同向/.test(DBJSON.cards.find(c => c.id === "nbr-0205").sep.join("")));

  // ⑥  页面接线
  console.log("\n[六] 页面接线");
  const page = fs.readFileSync(path.join(ROOT, "public/nbr/index.html"), "utf8");
  ok("页面引了共用模块", page.indexOf("/assets/sde-nbr.js") > 0);
  ok("页面把三条纪律写在明处",
    /库未命中/.test(page) && /不同命名空间/.test(page) && /每轮回写/.test(page));
  ok("页面提醒别贴标题要贴承重命题", /不要贴文章标题/.test(page));
  ok("页面标了 channel（否则 build_roster 会把它当一篇作品）",
    /sde-page-kind"\s+content="channel"/.test(page));
  ok("没有残留的 CSS 变量笔误", page.indexOf("#7C7costs") < 0);

  console.log("\n%d PASS / %d FAIL", PASS, FAIL);
  process.exit(FAIL ? 1 : 0);
})();
