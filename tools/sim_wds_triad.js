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
// ⚠ 只查字符串在不在会被下文的对照例蒙混过去（E→D→S 在例子里也出现一次）——
// 必须按「· **X→Y→Z**：」这个条目格式数，六条各要有自己的一行。
["S→D→E", "S→E→D", "D→S→E", "D→E→S", "E→S→D", "E→D→S"].forEach(p =>
  ok(seg.indexOf("· **" + p + "**：") > 0, "六条各有自己的条目行：" + p));
ok((seg.match(/· \*\*[SDE]→[SDE]→[SDE]\*\*：/g) || []).length === 6,
   "条目行恰好六条，实得 " + (seg.match(/· \*\*[SDE]→[SDE]→[SDE]\*\*：/g) || []).length);
// 一条路径＝「从哪儿开始 → 经过什么 → 实现什么」的一整条次序；分组只是查找方式，不是路径本身
ok(seg.indexOf("从哪儿开始 → 经过什么 → 实现什么") > 0, "路径的定义写成完整次序，不是「从哪下手」这一件事");
ok((seg.match(/例：/g) || []).length >= 14, "六条各带例子（全块举例 ≥14 处，实得 " + (seg.match(/例：/g) || []).length + "）");
ok(seg.indexOf("别把分组当成路径") > 0, "写明按起点/按落点归组只是查找方式，路径本身是那条完整次序");
ok(seg.indexOf("你现在动得了哪一样") > 0, "给了挑路径的实际判据：三样里你动得了哪一样");
ok(seg.indexOf("从一样你动不了的东西起手") > 0, "挡住从动不了的那一头起手");
ok(seg.indexOf("几条接起来的序列") > 0, "要求写序列");
ok(seg.indexOf("同一件事，次序换一下，一条能走通、一条走不通") > 0, "给了次序决定成败的对照例（D→S→E 走不通 / E→D→S 走得通）");
ok(seg.indexOf("写成 X→Y→Z") > 0, "答法要求把这一次走的那条写成 X→Y→Z");
ok(seg.indexOf("加强／重视／完善／优化") > 0, "挡住「加强/重视/完善/优化」这类假办法");

console.log("⑥ 为什么：三条原理 + 回写 + 时序读数");
ok(/S 与 D 相争 → 逼动 E/.test(seg), "原理：S×D → E");
ok(/S 与 E 相争 → 逼动 D/.test(seg), "原理：S×E → D");
ok(/D 与 E 相争 → 逼动 S/.test(seg), "原理：D×E → S");
ok(seg.indexOf("回写前两个") > 0, "**回写**在场（没有它就只是一次驱动，不是一条链）");
ok(seg.indexOf("驱动方向翻了") > 0, "写明驱动方向会翻");
ok(seg.indexOf("时序读数") > 0 && seg.indexOf("多久跟上") > 0, "要求给时序读数");
ok(seg.indexOf("三者相互影响") > 0 && seg.indexOf("永远没用") > 0, "挡住「三者相互影响、共同作用」这句万能废话");

console.log("⑥之二 起手根据（对标 SDE 对谈：每答说得出从哪条起手、凭什么）");
ok(seg.indexOf("起手根据") > 0, "有「起手根据」一节");
ok(seg.indexOf("说不出根据就是没起手") > 0, "说不出根据＝没起手");
ok(seg.indexOf("别写「本轮采用三大方程」") > 0, "禁止报工序名（要在行文里自然说清）");
ok(seg.indexOf("转要说，别悄悄转") > 0, "中途换入口要明说（呼应「公开改切≠静默替换」）");

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
ok(th.indexOf("先说清这一次走的是六条路径里的哪一条") > 0, "how 先说清走六条里的哪一条，写成 X→Y→Z");
ok(th.indexOf("你现在动得了哪一样") > 0, "how 给了挑路径的实际判据");
ok(th.indexOf("并且要把序列写出来") > 0, "how 要求写序列");
ok(ty.indexOf("回写") > 0, "why 补上了回写");
ok(ty.indexOf("下一轮先动的换成了谁") > 0, "why 要求写出下一轮换谁先动");

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
