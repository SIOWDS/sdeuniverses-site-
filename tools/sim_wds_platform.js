/* 平台自述块 SDE_PLATFORM_BLOCK 的护栏：tools/sim_wds_platform.js
 *
 * 这一块是 ChatSDE 作为「平台总机」的名录。它唯一会真正伤到读者的方式是**编一个不存在的路径**——
 * 编出来的地址读者一点就落空，比不给还糟。所以本护栏最核心的一节是：
 *   **把块里出现的每一个站内路径抠出来，逐条反查磁盘上真有那个页面。**
 * 建站是活的：某天一个栏目被改名或下线而这块没跟，这条断言会当场红。
 *
 *   node tools/sim_wds_platform.js
 */
"use strict";
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
let P = 0, F = 0;
function ok(c, m) { if (c) { P++; console.log("  PASS " + m); } else { F++; console.log("  FAIL " + m); } }

const W = fs.readFileSync(process.env.WORKER_JS || path.join(ROOT, "src/worker.js"), "utf8");
const i = W.indexOf("const SDE_PLATFORM_BLOCK");
const seg = i < 0 ? "" : W.slice(i, W.indexOf("\n/* ═══════════ SDE 工序", i));

console.log("① 常驻注入，且排在 iq 改道之后");
ok(i > 0, "SDE_PLATFORM_BLOCK 存在");
ok(/\+ SDE_TRIAD_BLOCK\s*\n\s*\+ SDE_PLATFORM_BLOCK/.test(W), "紧跟三类问题块无条件拼进去");
ok(!/deep \? SDE_PLATFORM_BLOCK/.test(W), "没有被写成只在深度档注入");
const iq = W.indexOf("if (tool === \"iq\") return WDS_IQ_SYS");
const cs = W.indexOf("function WDS_CHAT_SYS");
const inj = W.indexOf("+ SDE_PLATFORM_BLOCK");
ok(cs > 0 && cs < iq && iq < inj, "注入点在 WDS_CHAT_SYS 内且在 iq 改道之后（评分者不装名录）");

console.log("② ⚠ 名录里的每一个站内路径都必须真的存在（编路径是这块唯一会伤到读者的地方）");
const paths = Array.from(new Set((seg.match(/\/[a-z0-9][a-z0-9\-\/]*\//g) || [])));
ok(paths.length >= 20, "抠出 " + paths.length + " 个站内路径");
// 一条路径出现在块里有两种正当理由：①它真的存在，可以送人去；
// ②它**不存在，而块里正是在警告"别送到这个地址"**（/books/ 就是这种）。
// 断言要能分开这两种，否则要么放过编造，要么逼着把有用的警告删掉。
const WARN = /没有总目录页|不要把读者送到|不存在|已经下线/;
const missing = [], warned = [];
paths.forEach(p => {
  if (fs.existsSync(path.join(ROOT, "public", p, "index.html"))) return;
  // 看这个路径附近有没有明确的"别去"警告
  let isWarned = false, at = -1;
  while ((at = seg.indexOf(p, at + 1)) >= 0) {
    if (WARN.test(seg.slice(Math.max(0, at - 160), at + 160))) { isWarned = true; break; }
  }
  (isWarned ? warned : missing).push(p);
});
ok(missing.length === 0, "逐条反查磁盘：所有用来送人的路径都真实存在"
   + (missing.length ? "；**编造/失效的：" + missing.join(" ") + "** —— 编路径比不给还糟，立刻改" : ""));
ok(warned.every(p => !fs.existsSync(path.join(ROOT, "public", p, "index.html"))),
   "被明示「别送到这里」的路径（" + (warned.join(" ") || "无") + "）确实不存在——若它后来建起来了，这条警告就该撤掉");

console.log("③ 三部分齐备，且认成三个维度不是三个入口");
["SDE浏览", "ChatSDE", "SDE社区"].forEach(k => ok(seg.indexOf(k) > 0, "三部分之一：" + k));
ok(seg.indexOf("不是三个入口") > 0, "明写不是三个入口");
ok(/SDE浏览＝显露[\s\S]{0,60}ChatSDE＝发生[\s\S]{0,60}SDE社区＝纠缠/.test(seg), "三维对应：浏览=显露／ChatSDE=发生／社区=纠缠");
ok(seg.indexOf("新思想的发生") > 0, "写明平台目标只有一句");
ok(seg.indexOf("你就是中间那一维") > 0, "写明 ChatSDE 自己的位置");
ok(seg.indexOf("把他推到下一维去") > 0, "写明它的活是往下一维推，不是把人留住");

console.log("④ 三台完整产线按题型分派（这是总机的分派表）");
ok(/这到底是什么[\s\S]{0,80}idea-generator/.test(seg), "What → 金点子");
ok(/具体怎么办[\s\S]{0,80}zhiwen/.test(seg), "How → 中华智问");
ok(/为什么会这样[\s\S]{0,80}sde-dynamics/.test(seg), "Why → 动力智能体");
ok(seg.indexOf("烧的是他自己的 Key") > 0, "送人过去要说清烧谁的 Key");
ok(seg.indexOf("不要替他按开始") > 0, "不许替读者按开始（越权）");
ok(seg.indexOf("要一段经典原文，不是一个问题") > 0, "经典解构器的入口差别写明了");

console.log("⑤ 社区那一维：说清它凭什么值得去");
ok(seg.indexOf("顶回") > 0 && seg.indexOf("三选一") > 0, "结构化顶回三选一");
ok(seg.indexOf("不共享同一套语汇") > 0, "写明它的价值在于异质他者");
ok(seg.indexOf("这是你这一维的天花板") > 0, "诚实交代 ChatSDE 自己的天花板");
ok(seg.indexOf("承重命题") > 0, "候选卡的粒度说清了");

console.log("⑥ 占位库那条硬纪律不许被说软");
ok(seg.indexOf("零调用不烧 Key") > 0, "/nbr/ 零调用");
ok(seg.indexOf("库里没查到 ≠ 没被占") > 0, "库未命中 ≠ 未被占位");
ok(seg.indexOf("不能据此说他是原创") > 0, "不许据库未命中说原创");

console.log("⑦ 防编造与防报菜名");
ok(seg.indexOf("一律不许编") > 0 || seg.indexOf("不许编") > 0, "不许编不存在的路径");
ok(seg.indexOf("不确定就说") > 0, "不确定就说不确定");
ok(seg.indexOf("不要报菜名") > 0, "不许每次都罗列一堆去处");
ok(seg.indexOf("一次最多推一处") > 0, "一次最多推一处");
ok(seg.indexOf("先答再送") > 0, "先把这一问答到位再说下一步");
ok(seg.indexOf("代替回答，是偷懒") > 0, "不许用「你可以去 X」代替回答");
ok(seg.indexOf("送错了比不送更糟") > 0, "拿不准就问，别硬送");
ok(seg.indexOf("名录会随建站变动") > 0, "注释里提醒名录会过时");

console.log("⑧ 斜杠命令与工序表对得上");
["/是什么", "/怎么办", "/为什么", "/评分", "/近邻", "/母题", "/缝隙", "/碰撞", "/通融", "/改姓", "/坐标", "/九宫", "/结构图"]
  .forEach(c => ok(seg.indexOf(c) > 0, "命令在名录里：" + c));
const F2 = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");
["是什么", "怎么办", "为什么", "评分", "近邻", "母题", "缝隙", "碰撞", "通融", "改姓", "坐标", "九宫", "结构图"]
  .forEach(c => ok(F2.indexOf('"' + c + '"') > 0, "前端真认这个命令：/" + c));

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
