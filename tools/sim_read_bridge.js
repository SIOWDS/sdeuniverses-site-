/* 陪读浮层的跨系统出口（浏览 → 微信 / 浏览 → 产线）：tools/sim_read_bridge.js
 *
 * 为什么要有这一份：`wds-read.js` 铺在 **2000+ 个正文页**上，是全站最宽的入口。
 * 它此前是条死胡同——读者在文章页问出一个好问题，既落不成候选卡（送不到微信被顶回），
 * 也转不去任何一台产线。本轮接上了两条线，而正因为面积大，几件事一旦漂掉后果也最大：
 *   ① 两个模块必须**懒加载**——为一个多数人不点的按钮给两千页各加两个请求，是纯损耗；
 *   ② 落卡的 `sys` 必须是 **"S"**（浏览维度）。模块默认 "D"，照抄默认会让账本
 *      把浏览产的卡记成对话产的，而账本是三系统指着同一条命题说话的唯一凭据；
 *   ③ 三段硬门与占位闸门一律走 SDECand，这里一行都不许重写（抄第二遍必漂，且漂得静默）；
 *   ④ 动作条只在**答完**之后出现，流式期间摆出来等于请读者对半截话下判断；
 *   ⑤ 模块拉不到要如实说并给人工去处，不许拦路、不许假装。
 *
 *   node tools/sim_read_bridge.js
 */
"use strict";
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const SRC = process.env.READ_JS || path.join(ROOT, "public/taste/wds-companion/wds-read.js");

let P = 0, F = 0;
function ok(c, m) { if (c) { P++; console.log("  PASS " + m); } else { F++; console.log("  FAIL " + m); } }
function step(t, fn) { console.log(t); try { fn(); } catch (e) { F++; console.log("  FAIL 这一步自己抛了错：" + e.message); } }

const RAW = fs.readFileSync(SRC, "utf8");
// 面板里的中文有的直接写、有的写成 \uXXXX 转义（视当初怎么生成）。
// 断言若只认其中一种，就会在另一种写法下静默放过——所以先把转义解开再查。
const S = RAW.replace(/\\u([0-9a-fA-F]{4})/g, (m, h) => String.fromCharCode(parseInt(h, 16)));

step("① 语法与结构", () => {
  ok(S.length > 20000, "文件不为空且不像被截断（" + S.length + " 字符）");
  try { new Function(S); ok(true, "整份脚本可解析"); } catch (e) { ok(false, "整份脚本可解析：" + e.message.slice(0, 90)); }
  ["function candPanel", "function passPanel", "function wdsrActs", "function lazyJs"]
    .forEach(f => ok(S.indexOf(f) > 0, "函数在位：" + f.replace("function ", "")));
});

step("② 懒加载：不给两千页各加两个请求", () => {
  ok(S.indexOf("var LAZY = {}") > 0, "有懒加载缓存表");
  ok(/lazyJs\("\/taste\/assets\/sde-cand\.js/.test(S), "候选卡模块是点了才拉");
  ok(/lazyJs\("\/taste\/assets\/sde-handoff\.js/.test(S), "交接模块是点了才拉");
  // 这份脚本自己不许在顶层静态引这两个模块
  ok(!/<script[^>]*sde-cand/.test(S), "没有静态 script 标签引候选卡模块");
  ok(S.indexOf("LAZY[src]") > 0, "同一个模块只拉一次（有缓存）");
});

step("③ ⚠ 落卡的来处维度必须是 S（浏览），不能用模块默认的 D", () => {
  ok(/sys:\s*"S"/.test(S), "落卡带 sys:\"S\"");
  ok(!/sys:\s*"D"/.test(S), "没有把浏览侧的卡记成对话维度");
  ok(S.indexOf("照抄默认会让账本") > 0, "代码注释写明了为什么不能照抄默认");
  ok(/src:\s*"SDE \\u966a\\u8bfb|src: "SDE \u966a\u8bfb/.test(S) || S.indexOf("SDE \u966a\u8bfb \u00b7 ") > 0,
     "来处写成「SDE 陪读 · 篇名」，可回溯到哪一页");
});

step("④ 三段硬门与占位闸门一律走模块，这里不重写", () => {
  ok(S.indexOf("C.check(c)") > 0, "三段校验调 SDECand.check");
  ok(S.indexOf("C.gate(") > 0, "占位闸门调 SDECand.gate");
  ok(S.indexOf("C.post(c)") > 0, "落卡调 SDECand.post");
  ok(S.indexOf("C.draft(") > 0, "预填调 SDECand.draft");
  ok(S.indexOf("C.NA_LINE") > 0, "查库失败用模块给的口径（不自己编一句）");
  // 不许把闸门话术抄一份到这里
  ok(S.indexOf("\u5e93\u672a\u547d\u4e2d\u3015\u00b7 \u4e0d\u5f97\u636e\u4ee5\u653e\u884c") < 0,
     "没有把〔库未命中〕那句话术抄第二份（抄一份就会有一天两份不一样）");
});

step("⑤ 动作条只在答完之后出现", () => {
  ok(S.indexOf("body._wrap = wrap") > 0, "addMsg 只记外壳，不预造空动作条（开场白/报错永远用不上）");
  ok(/try \{ wdsrActs\(bubble, answer\); \} catch/.test(S), "在 finish 里挂，且挂失败不影响正常收尾");
  // ⚠ 不能拿 indexOf("wdsrActs(bubble, answer)") 直接比——它先命中的是**函数定义**那一行，
  //   而定义排在 finish 之前，于是这条断言会反过来误判。要在 finish 的函数体里找。
  const fin = S.indexOf("function finish()");
  ok(fin > 0, "finish 存在");
  const body = fin > 0 ? S.slice(fin, fin + 500) : "";
  ok(body.indexOf("wdsrActs(bubble, answer)") > 0, "调用点在 finish 的函数体里（不是流式期间）");
  ok(S.indexOf("function wdsrActs(") < fin, "定义排在 finish 之前（提升与否都可用，但顺序如此）");
  ok(S.indexOf("answer.length < 40") > 0, "太短的答案不摆按钮");
});

step("⑥ 交接：只填不跑，且预填用得上的那句", () => {
  ok(S.indexOf("\u4e0d\u66ff\u4f60\u6309\u5f00\u59cb") > 0, "面板上明写不替读者按开始");
  ok(S.indexOf("H.send(a.id") > 0, "走 SDEHandoff.send，不自己拼 localStorage");
  ok(S.indexOf("H.AGENTS.forEach") > 0, "台数从模块的权威表来（不在这里再抄一份名单）");
  ok(/focusSeg \|\| lastAsk/.test(S), "预填：选中段优先，没选中就用这一轮问的那句");
  ok(S.indexOf("var lastAsk") > 0, "lastAsk 有声明（引用未声明的变量会当场 ReferenceError）");
  ok(/lastAsk = String\(q/.test(S), "问出去时记下那一句");
});

step("⑦ 失败不拦路，且不假装", () => {
  ok(S.indexOf("\u5019\u9009\u5361\u6a21\u5757\u6ca1\u52a0\u8f7d\u4e0a") > 0, "候选卡模块拉不到时如实说");
  ok(S.indexOf("\u4ea4\u63a5\u6a21\u5757\u6ca1\u52a0\u8f7d\u4e0a") > 0, "交接模块拉不到时如实说");
  ok(S.indexOf("/sde-wechat/") > 0, "拉不到也给人工去处（微信）");
  ok(/idea-generator[\s\S]{0,400}zhiwen[\s\S]{0,400}sde-dynamics/.test(S), "拉不到也给三台的人工去处");
  ok((S.match(/\.catch\(function/g) || []).length >= 4, "各条异步路径都有兜底");
});

step("⑧ 样式是拼进 JS 字符串的，别再插裸换行", () => {
  ok(RAW.indexOf('".wdsr-acts{') > 0, "新样式以 JS 字符串形式拼入");
  ok(RAW.indexOf('".wdsr-pan a{color:#5FA8D3}"') > 0, "最后一条样式也闭合正确");
  const css = RAW.slice(RAW.indexOf('".wdsr-acts{'), S.indexOf('".wdsr-pan a{'));
  ok(css.indexOf("\n") < 0 || /"\s*\+\s*\n\s*"/.test(css), "样式段每行都是完整字符串加号相连（这里插裸换行会当场把脚本拆坏）");
});

step("⑨ 缓存戳：改了这份脚本，全站引用必须一起 bump", () => {
  const stamps = new Set();
  (function walk(d) {
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      const p = path.join(d, e.name);
      if (e.isDirectory()) { if (e.name !== ".git") walk(p); }
      else if (/\.(html|js)$/.test(e.name)) {
        const t = fs.readFileSync(p, "utf8");
        const re = /wds-read\.js\?v=([0-9a-z]+)/g; let m;
        while ((m = re.exec(t))) stamps.add(m[1]);
      }
    }
  })(path.join(ROOT, "public"));
  ok(stamps.size === 1, "全站 wds-read.js?v= 戳一致，实得：" + Array.from(stamps).join(" / "));
});

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
