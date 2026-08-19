/* 中华智问 · 三篇聚焦文碰撞链的护栏
 *
 * 这台是三路径二阶碰撞：A/B/C 三条泳道各锁一个落点（形态 S / 条件 E / 演化 D），
 * 各出一篇聚焦文，阶段三把三篇撞成第四篇典范文。
 *
 * 守两件此前没有守住的事：
 *   ① 第〇步「结构定位与共有前提」必须在，且必须要求推翻材料来自三篇之一自己；
 *      它与第⑥步（从五个既有概念的盲区交集取学术界那块地）是两层，不可互相顶替。
 *   ② 评分锚点必须与站内实测一致（真二阶 139-142，至今无一篇跨 150），
 *      不许回到「142 是略有瑕疵 / 150 是起点 / 触发计数直接给分」那套设计目标。
 *
 *   node tools/sim_zhiwen_collide.js
 */
"use strict";
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const PAGE = process.env.ZW_HTML || path.join(ROOT, "public/taste/zhiwen/index.html");

let P = 0, F = 0;
function ok(c, m) { if (c) { P++; console.log("  PASS " + m); } else { F++; console.log("  FAIL " + m); } }
function step(t, fn) { console.log(t); try { fn(); } catch (e) { F++; console.log("  FAIL 这一步自己抛了错：" + e.message); } }

const h = fs.readFileSync(PAGE, "utf8");

// 从页面里抠函数原文来跑（不复制一份代码——复制的那份对了不算数）
function grab(name) {
  const i = h.indexOf("function " + name + "(");
  if (i < 0) return null;
  // 找到与之配对的收尾大括号
  let d = 0, started = false;
  for (let k = i; k < h.length; k++) {
    if (h[k] === "{") { d++; started = true; }
    else if (h[k] === "}") { d--; if (started && d === 0) return h.slice(i, k + 1); }
  }
  return null;
}
const SRC = ["collideP0", "collideP1", "collideP3"].map(grab);
let FN = {};
try {
  FN = new Function("COLLISION_DISCIPLINE",
    SRC.join("\n") + "\nreturn {collideP0, collideP1, collideP3};")("〔纪律桩〕");
} catch (e) { console.log("  （抠函数失败：" + e.message + "）"); }

step("① 三路径的架子还在（三台各锁一个落点，且落点互不相同）", () => {
  ok(/A:\{Z:'E→D→S',\s*L:'D→E→S',\s*T:'S'\}/.test(h), "A 台锁落点 S（形态）");
  ok(/B:\{Z:'S→D→E',\s*L:'D→S→E',\s*T:'E'\}/.test(h), "B 台锁落点 E（条件）");
  ok(/C:\{Z:'E→S→D',\s*L:'S→E→D',\s*T:'D'\}/.test(h), "C 台锁落点 D（演化）");
  ok(h.indexOf("落点不是 S 的路径都不属于本智能体") > 0, "路径锁定的硬约束还在");
  ok(h.indexOf("撞车判定") > 0, "原料体检（位置三分闸）还在");
});

step("② 第〇步 · 结构定位与共有前提（本轮新加，最要紧）", () => {
  ok(!!SRC[0], "collideP0 存在");
  ok(h.indexOf("第〇步 · 结构定位与共有前提") > 0, "runCollision 里挂了第〇步");
  if (FN.collideP0) {
    const s = FN.collideP0("测试议题", "甲".repeat(80), "乙".repeat(80), "丙".repeat(80));
    ok(s.indexOf("各自把什么当成了单独够用的那一样") > 0, "第一段：三家各把什么当成单独够用");
    ok(s.indexOf("可以由其中一个落点单独结算") > 0, "第二段：三路径型的共有前提形状");
    ok(s.indexOf("这还用说吗") > 0, "共有前提的验收句（三家都会说这还用说吗）");
    ok(s.indexOf("跳起来反对") > 0, "验收的反面：有人反对就是第四种立场");
    ok(s.indexOf("必须来自 A/B/C 之一自己") > 0, "第三段：推翻材料必须来自三篇之一自己");
    ok(s.indexOf("一律不算数") > 0, "外搬理由不算数");
    ok(s.indexOf("原样引出") > 0, "要求原样引出那一句，不许转述");
    ok(s.indexOf("〔纪律桩〕") > 0, "末尾接了 COLLISION_DISCIPLINE");
  }
});

step("③ 第〇步真的被下游用上（传进去了才算数）", () => {
  ok(/function collideP1\(q, A, B, C, step0\)/.test(h), "collideP1 收 step0");
  ok(/function collideP3\(q, step2, step0\)/.test(h), "collideP3 收 step0");
  ok(/collideP1\(q,A,B,C,step0\)/.test(h), "调用处把 step0 传给 collideP1");
  ok(/collideP3\(q,step2,step0\)/.test(h), "调用处把 step0 传给 collideP3");
  ok(/collisionSteps = \{checkup, step0,/.test(h), "step0 进了 collisionSteps（会随材料进第四篇论文）");
  if (FN.collideP1) {
    const withS = FN.collideP1("q", "A", "B", "C", "【一】…【二】…【三】…");
    const noS = FN.collideP1("q", "A", "B", "C", "");
    ok(withS.indexOf("方向盘") > 0, "有 step0 时把它作为方向盘写进撞击指令");
    ok(withS.indexOf("谁是要被解释的那一样") > 0, "点破三对争的其实是终点之争");
    ok(noS.indexOf("方向盘") < 0, "拿不到 step0 时不硬塞（退回原来的撞法，不阻断产线）");
  }
  if (FN.collideP3) {
    const s = FN.collideP3("q", "暗流", "共有前提正文");
    ok(s.indexOf("不是三家的综合") > 0, "收口：新典范不是三家的综合");
    ok(s.indexOf("Y₃") > 0, "命题形状是三重否定（三条路径就该三个 Y）");
    ok(s.indexOf("某一个落点说了算") > 0, "不可还原那一问接上了共有前提");
  }
});

step("④ 两层共有前提的分工写明了（第〇步 vs 第⑥步）", () => {
  ok(h.indexOf("与第〇步的分工") > 0, "盲区涌现那一步写明了与第〇步的分工");
  ok(h.indexOf("整个学术界") > 0, "第⑥步取的是学术界那块地");
  ok(h.indexOf("不可互相顶替") > 0, "明写两层不可互相顶替");
  ok(h.indexOf("盲区交集") > 0, "第⑥步本身还在（没被新工序挤掉）");
});

step("⑤ 评分锚点与站内实测一致（不许回到设计目标那套）", () => {
  ok(h.indexOf("没有任何一篇跨过 150") > 0, "写明站内至今无一篇跨过 150");
  ok(h.indexOf("139-142") > 0, "真二阶的实测区间 139-142 在");
  ok(h.indexOf("触发计数只定区间参考") > 0, "触发计数已降为参考，不是主要标尺");
  ok(h.indexOf("以五维为准") > 0, "触发与五维冲突时以五维为准");
  ok(h.indexOf("校准的方向是准,不是低") > 0, "同时防一律压低");
  // 旧的通胀口径必须清干净
  const stale = ["142 不再是默认锚点", "150 也不再是天花板", "大多数 SDE 充分激活的产出应该在 142-148",
                 "150 是\"顶尖学者级起点\"", "果断给对应分数", "不要因为防范心理退回",
                 "0 条 → 130-138", "7 条 → 165-170"];
  const hit = stale.filter(s => h.indexOf(s) >= 0);
  ok(hit.length === 0, "旧的通胀口径已清净" + (hit.length ? "，残留：" + hit.join(" / ") : ""));
  ok(h.indexOf("0 条 → 115-128") > 0, "触发 0 条的下沿已从 130 降到 115");
  ok(h.indexOf("E 封顶 132") > 0, "跨域全是同形例证 → E 封顶 132");
});

step("⑥ 原有的硬关卡一个都没被挤掉", () => {
  ok(h.indexOf("三篇删除测试") > 0, "三篇删除测试还在");
  ok(h.indexOf("上游母学科") > 0, "上游母学科的形式同名检索还在");
  ok(h.indexOf("反转模板专查") > 0, "反转模板专查还在");
  ok(h.indexOf("机制证伪") > 0, "机制证伪两步法还在");
  ok(h.indexOf("严禁拿两个国家") > 0, "样本纪律（不许拿两国充数）还在");
  ok(h.indexOf("不可替换的角色") > 0, "三涌现物全支撑的硬关卡还在");
});

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
