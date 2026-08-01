/* tools/sim_nbr_web.mjs —— 候选近邻闸接入 web 检索 · 护栏
   钉三件事：① worker 的 /api/nbr/web 端点契约；② 两个模块的撞名已拆开；
   ③ 碰撞机里那一格真的插在「扩候选」与「候选互撞」之间、且钩子用的是 s.id。
   全部对真文件做静态断言——这一层的失败是静默的（闸门照样显示"已过闸"），
   没有护栏就只能等下一次真跑失手才发现。 */
import fs from "node:fs";

let P = 0, F = 0;
const ok = (c, m) => { if (c) P++; else { F++; console.log("  FAIL:", m); } };
const R = (p) => fs.readFileSync(p, "utf8");

console.log("── 1. 联网腿：不重复造轮子");
const w = R("src/worker.js");
ok(!w.includes('"/api/nbr/web"'), "★ 没有另起一个重复端点（并发线的闸走已有的 /api/wds/websearch）");
ok(w.includes('"/api/wds/websearch"'), "已有的联网端点还在");
const tplW = R("tools/forge/forge.template.html");
ok(tplW.includes("/api/wds/websearch"), "候选闸的联网腿打的是那个端点");
ok(tplW.includes("转成 2 条**英文**学术检索词") || tplW.includes("英文"),
   "★ 联网前先把候选转成英文学术检索词（找国际占位者，中文模板找不到）");

console.log("── 2. 两个模块的撞名已拆开（这是最容易静默出错的一处）");
const lib = R("public/assets/sde-nbr.js");
const gate = R("public/taste/assets/sde-nbr-gate.js");
ok(/w\.SDENbrLib = w\.SDENbr;/.test(lib), "库模块导出 SDENbrLib");
ok(/w\.SDENbrGate = w\.SDENbr;/.test(gate), "判据模块导出 SDENbrGate");
ok(lib.includes("function web(q, key)"), "库模块有 web() 三级");
ok(lib.includes('"/api/nbr/web"'), "web() 打的是新端点");
ok(lib.includes("function gateLine3"), "有三级合一的结论行");
ok(/gateLine3[\s\S]{0,600}不得据以放行/.test(lib), "★ 三个 miss 叠在一起仍然只说「未命中」，不说「未被占位」");
ok(lib.includes("web: web"), "web 已进导出表");
// 两个模块都定义 window.SDENbr —— 撞名本身还在（保留向后兼容），但必须各留一条警告
ok(/撞名|盖掉/.test(lib) && /撞名|盖掉/.test(gate), "两处都留了撞名警告");

console.log("── 3. 候选闸插对了位置（工序6：闸门不是终点报告）");
const tpl = R("tools/forge/forge.template.html");
const page = R("public/taste/paradigm-forge/index.html");
for (const [nm, src] of [["模板", tpl], ["生成物", page]]) {
  ok(src.includes("id:'nbrgate'"), `${nm}：步骤表有 nbrgate`);
  const iE = src.indexOf("id:'expand'"), iN = src.indexOf("id:'nbrgate'"), iC = src.indexOf("id:'collide2'");
  ok(iE > 0 && iN > iE && iC > iN, `★ ${nm}：顺序是 扩候选 → 候选闸 → 候选互撞`);
  ok(src.includes("SDEPlaceholder"), `${nm}：占位者库已接`);
  ok(/未命中不等于未被占位|不得据此放行|不得据以放行/.test(src), `★ ${nm}：未命中不得据以放行写死在代码里`);
  ok(!/if\(id===['"]nbrgate/.test(src.slice(src.indexOf("async function runStage(i){"),
      src.indexOf("async function runStage(i){") + 600)), `${nm}：runStage 内没有裸用 id`);
}

console.log("── 4. 近邻库种子卡");
const db = JSON.parse(R("public/nbr/cards.json"));
ok(Array.isArray(db.cards) && db.cards.length >= 99, `卡数 ${db.cards.length} ≥ 99`);
const ids = new Set(db.cards.map((c) => c.id));
ok(ids.size === db.cards.length, "无重复 id");
ok(db.n === db.cards.length, "n 与实际条数一致");
// 本批必到的三张：两次真跑失手的占位者
// Lorde 与 Marcuse 库内已有（nbr-0205/0206，引擎室漏掉的那两位）——不重复造。
// 本批必到的三张是当天评估里真正切出来、而库里此前没有的。
for (const [id, who] of [["nbr-0303", "Yankelovich"], ["nbr-0304", "John"], ["nbr-0309", "Harrison"]]) {
  const c = db.cards.find((x) => x.id === id);
  ok(c && c.src.author.includes(who), `★ ${id} 是 ${who}（真跑失手条目已入库）`);
}
let bad = [];
for (const c of db.cards) {
  if (!c.prop || !c.alias || !c.src || !c.holds || !c.sep || !c.ring) bad.push(c.id + ":缺字段");
  else if (c.alias.length < 3) bad.push(c.id + ":alias<3");
  else if (c.sep.length < 1) bad.push(c.id + ":sep<1");
}
ok(bad.length === 0, `全部卡过形状校验（${bad.slice(0, 5).join(" ")}）`);
// 分离线必须是可裁决的形状，不能是"侧重不同"
const vague = db.cards.filter((c) => c.sep.some((s) => /^侧重|^更强调|^角度不同$/.test(s)));
ok(vague.length === 0, "没有「侧重不同」这类不算划界的分离线");
// ⚠ 卡号不连续（库里原本就有 0073 以上的号），不能用 id >= 判本批——按确切号认。
const BATCH2 = Array.from({ length: 27 }, (_, i) => "nbr-" + String(301 + i).padStart(4, "0"));
const newCards = db.cards.filter((c) => BATCH2.includes(c.id));
ok(newCards.length === 27, `C 批 27 张（实测 ${newCards.length}）`);
ok(newCards.every((c) => c.sep.some((s) => /可实测|判决性对照|预测/.test(s))),
   "★ C 批**每一张**都带可裁决的对照预测（侧重不同不算划界，这是硬规矩）");

console.log("── 5. 卡源，不是生成物");
const bn = R("tools/build_nbr.py");
ok(bn.includes("from cards_c import CARDS_C"), "★ C 批在卡源里（只改生成物会被下一次构建抹掉——这坑今天踩过一次）");
ok(bn.includes("CARDS_A + CARDS_B + CARDS_C"), "三批都进 CARDS");
const cc = R("tools/nbr/cards_c.py");
ok(/frm=/.test(cc), "每张卡记着从哪一篇回写来的");
ok(db.cards.every((c) => (c.g || []).length > 3), "★ 全部卡都有预算词元 g（缺了就永远召不回来）");

console.log(`\n${P} PASS / ${F} FAIL`);
process.exit(F ? 1 : 0);
