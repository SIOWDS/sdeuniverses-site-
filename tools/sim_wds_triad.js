/* ChatSDE 常驻块「三类问题」的护栏：tools/sim_wds_triad.js
 *
 * 守的是三件一旦漂掉就静默降级的事：
 *   ① 这一块必须**每一轮都注入**——它跟 SDE_METHOD_BLOCK 不同，后者只在深度档进。
 *      判题型发生在开口之前；判错了类，答得再好也是答非所问。
 *   ② 九格、六路径、三原理的具体内容必须在，且**六步/九步（想的次序）与六路径（做的走法）
 *      不许被写成一回事**——两者都叫路径，这是最容易混掉的一处。
 *   ③ Why 那一条必须带**回写**：被逼动的那一个改完会回写前两个，下一轮换人先动。
 *      没有回写，它就只是一次驱动，不是一条链。
 *
 *   node tools/sim_wds_triad.js
 */
"use strict";
const fs = require("fs");

let P = 0, F = 0;
function ok(c, m) { if (c) { P++; console.log("  PASS " + m); } else { F++; console.log("  FAIL " + m); } }

const W = fs.readFileSync(process.env.WORKER_JS || "src/worker.js", "utf8");
const i = W.indexOf("const SDE_TRIAD_BLOCK");
const seg = i < 0 ? "" : W.slice(i, W.indexOf("\n/* ═══════════ SDE 工序", i));

console.log("① 常驻注入（不是只在深度档）");
ok(i > 0, "SDE_TRIAD_BLOCK 存在");
ok(/\+ SDEM\s*\n\s*\+ SDE_TRIAD_BLOCK/.test(W), "在 WDS_CHAT_SYS 里无条件拼进去（紧跟 SDEM，不带 deep 三元）");
ok(!/deep \? SDE_TRIAD_BLOCK/.test(W), "没有被写成只在深度档注入");
ok(W.indexOf("if (tool === \"iq\") return WDS_IQ_SYS") < W.indexOf("+ SDE_TRIAD_BLOCK"),
   "iq 改道仍排在它前面（评分者不装这块，防通胀）");

console.log("② 判题型的判据是「答案的形状」，不是疑问词");
ok(seg.indexOf("判据不是疑问词") > 0, "明写判据不是疑问词");
ok(/要一个\*\*东西\*\*[\s\S]{0,120}要一条\*\*路\*\*[\s\S]{0,120}要一个\*\*驱动\*\*/.test(seg), "三种形状：东西／路／驱动");
ok(seg.indexOf("S=F(D,E)") > 0 && seg.indexOf("D=G(S,E)") > 0 && seg.indexOf("E=H(S,D)") > 0, "三大方程作为共同底盘在场");

console.log("③ 是什么：九格齐备且各有例子");
[["S1", "对比"], ["S1", "分布"], ["S2", "粒子"], ["S2", "场"], ["S3", "真"],
 ["D1", "创造"], ["D1", "幸福"], ["D2", "六步"], ["D3", "最小误差"],
 ["E1", "三界"], ["E2", "符号"], ["E3", "势能"]].forEach(([g, w]) =>
  ok(seg.indexOf(g) > 0 && seg.indexOf(w) > 0, g + " 那一格含「" + w + "」"));
ok((seg.match(/例：/g) || []).length >= 8, "举例至少八处，实得 " + (seg.match(/例：/g) || []).length);
ok(seg.indexOf("中产阶级") > 0 && seg.indexOf("舆情") > 0, "S1/S2 有具体例子（不是抽象说明）");

console.log("④ 六步/九步 ≠ 六路径（最容易混掉的一处）");
ok(seg.indexOf("完全不是一回事") > 0, "明写两者不是一回事");
ok(seg.indexOf("六步是想的次序，六路径是做的走法") > 0, "给了一句能记住的分法");

console.log("⑤ 怎么办：六条路径写全，两种切法都在，且要求写序列");
["S→D→E", "S→E→D", "D→S→E", "D→E→S", "E→S→D", "E→D→S"].forEach(p =>
  ok(seg.indexOf(p) > 0, "路径在场：" + p));
ok(seg.indexOf("按**起点**分") > 0 || seg.indexOf("从 S 出发") > 0, "按起点分的三组在");
ok(seg.indexOf("落到哪儿") > 0, "按落点分的第二种切法也在");
ok(seg.indexOf("两种切法不冲突") > 0, "写明两种切法并存、各有用处");
ok(seg.indexOf("序列组合") > 0 && seg.indexOf("E→S→D→E") > 0, "要求写序列组合并给了一个真实序列的例子");
ok(seg.indexOf("加强／重视／完善／优化") > 0, "挡住「加强/重视/完善/优化」这类假办法");

console.log("⑥ 为什么：三条原理 + 回写 + 时序读数");
ok(/S 与 D 相争 → 逼动 E/.test(seg), "原理：S×D → E");
ok(/S 与 E 相争 → 逼动 D/.test(seg), "原理：S×E → D");
ok(/D 与 E 相争 → 逼动 S/.test(seg), "原理：D×E → S");
ok(seg.indexOf("回写前两个") > 0, "**回写**在场（没有它就只是一次驱动，不是一条链）");
ok(seg.indexOf("驱动方向翻了") > 0, "写明驱动方向会翻");
ok(seg.indexOf("时序读数") > 0 && seg.indexOf("多久跟上") > 0, "要求给时序读数");
ok(seg.indexOf("三者相互影响") > 0 && seg.indexOf("永远没用") > 0, "挡住「三者相互影响、共同作用」这句万能废话");

console.log("⑦ 问对反思：三档裁定 + 公开改切≠静默替换");
["承接", "改切", "驳回"].forEach(k => ok(seg.indexOf(k) > 0, "裁定档：" + k));
ok(seg.indexOf("公开改切 ≠ 静默替换") > 0, "硬纪律：公开改切不等于静默替换");
ok(seg.indexOf("年轻人都不想上进") > 0, "改切给了具体例子");
ok(seg.indexOf("不要每次都写成") > 0, "写明它是判断纪律、不是回答格式（防每轮都摆一张裁定表）");

console.log("⑧ 三件轻松版跟着更新了");
const tw = W.slice(W.indexOf("\n  what:"), W.indexOf("\n  how:"));
const th = W.slice(W.indexOf("\n  how:"), W.indexOf("\n  why:"));
const ty = W.slice(W.indexOf("\n  why:"), W.indexOf("\n  grid:"));
ok(tw.indexOf("先定位到格") > 0, "what 先定位到九格里的哪一格");
ok(tw.indexOf("先把那一格的具体内容答出来") > 0, "what 先答那一格的内容，再往下撞");
ok(th.indexOf("先说清这一次按哪一种切法在讲") > 0, "how 先说清按起点还是按落点");
ok(th.indexOf("并且要把序列写出来") > 0, "how 要求写序列");
ok(ty.indexOf("回写") > 0, "why 补上了回写");
ok(ty.indexOf("下一轮先动的换成了谁") > 0, "why 要求写出下一轮换谁先动");

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
