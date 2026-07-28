/* 只测一件事：站内搜索页「成文一篇」的上/下半篇守卫（public/search/index.html · paperHalf + doPaper 链）。

   病根（2026-07-29 发现）：万字论文分两次调用写成，旧版只给上半篇做了长度守卫。
   下半篇若返回空串（基底空转、流被静默关闭、配额耗尽都会这样），空串会被原样拼进
   全文，状态栏照样打出「✓ 全文完成」，PDF 里却只有上半篇——缺第二轴、可裁决判据、
   证伪条件、结语与参考文献。一篇被这样交出去的稿子送去评创新智商，两道闸门直接破位。

   本脚本把 paperHalf 从页面里抠出来真跑（streamPaper 打桩），验证：失败要重试、
   重试仍失败不许抛掉上半篇、也不许冒充完稿。另对 doPaper/buildPdf 的源码做契约断言。 */
"use strict";
const fs = require("fs");
const SRC = "/home/claude/site/public/search/index.html";
const h = fs.readFileSync(SRC, "utf8");

let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };

/* ===== 一、抠出 paperHalf 真跑 ===== */
const a = h.indexOf("function paperHalf(");
const b = h.indexOf("function doPaper(");
if (a < 0 || b <= a) { console.log("FAIL 抠不出 paperHalf（锚点变了，先改本脚本）"); process.exit(1); }
const seg = h.slice(a, b);

let calls = 0, plan = [];
function makeHalf() {
  calls = 0;
  const stub = {
    getElementById: () => ({ set textContent(v) { } }),
  };
  const streamPaper = function () {
    const step = plan[calls] || { text: "" };
    calls++;
    return step.err ? Promise.reject(new Error(step.err)) : Promise.resolve(step.text);
  };
  /* 2026-07-29：状态行目标改成可切换的 GEN_STAT（成文一篇与打磨修改共用这台续写机），
     所以桩里要把它一并喂进去——真页面里它是顶层变量。 */
  const fn = new Function("document", "streamPaper", "GEN_STAT", seg + "\nreturn paperHalf;");
  return fn(stub, streamPaper, "paperStat");
}

const LONG = "字".repeat(2000);
const tests = [];
function t(name, setup, check) { tests.push({ name, setup, check }); }

t("一次就够长 → 只调一次，原样返回", () => { plan = [{ text: LONG }]; },
  (r) => r.length === 2000 && calls === 1);

t("第一次空串 → 自动重试；第二次成功 → 返回第二次的稿子", () => { plan = [{ text: "" }, { text: LONG }]; },
  (r) => r.length === 2000 && calls === 2);

t("两次都空 → 返回空串而不是抛错（上半篇必须被保住）", () => { plan = [{ text: "" }, { text: "" }]; },
  (r) => r === "" && calls === 2);

t("重试封顶两次（不许无限重试烧配额）", () => { plan = [{ text: "" }, { text: "" }, { text: LONG }]; },
  (r) => calls === 2);

t("第一次报错 → 重试；第二次成功", () => { plan = [{ err: "网络中断" }, { text: LONG }]; },
  (r) => r.length === 2000 && calls === 2);

t("上半篇收尾标记被剥掉", () => { plan = [{ text: LONG + "\n〔上半篇完·待续〕" }]; },
  (r) => r.indexOf("上半篇完") < 0 && r.length === 2000);

t("下半篇收尾标记被剥掉", () => { plan = [{ text: LONG + "\n〔全文完〕\n" }]; },
  (r) => r.indexOf("全文完") < 0 && r.length === 2000);

(async function () {
  for (const x of tests) {
    x.setup();
    const half = makeHalf();
    let r = null, threw = null;
    try { r = await half(2, {}, 1200, "下半篇"); } catch (e) { threw = e; }
    ok(!threw && x.check(r), x.name + (threw ? "（意外抛错：" + threw.message + "）" : ""));
  }

  /* 两次都报错才允许抛出去 —— 这是唯一该让整链失败的情形 */
  plan = [{ err: "e1" }, { err: "e2" }];
  const half = makeHalf();
  let threw2 = null;
  try { await half(1, {}, 600, "上半篇"); } catch (e) { threw2 = e; }
  ok(!!threw2 && calls === 2, "两次都报错 → 抛给调用方（上半篇彻底失败才终止）");

  /* ===== 二、doPaper / buildPdf 的源码契约 ===== */
  ok(/paperHalf\(1,\{seed:[^}]*\},600,'上半篇'\)/.test(h), "doPaper：上半篇走 paperHalf，最短 600 字");
  ok(/paperHalf\(2,\{[^}]*\},1200,'下半篇'\)/.test(h), "doPaper：下半篇走 paperHalf，最短 1200 字");
  ok(h.indexOf(".catch(function(){ return ''; })") > 0, "doPaper：下半篇彻底失败也不丢上半篇（吞成空串继续出稿）");
  ok(h.indexOf("halfOnly=(String(p2c||'').length<1200)") > 0, "doPaper：按下半篇实际长度判定 halfOnly");
  ok(h.indexOf("buildPdf(full, halfOnly)") > 0, "doPaper：halfOnly 一路传进 PDF 排版");
  ok(/function buildPdf\(text, halfOnly, opt\)/.test(h), "buildPdf：接收 halfOnly（并已参数化给打磨稿复用）");
  ok(h.indexOf("⚠ 未完成稿 · 下半篇生成中断") > 0, "buildPdf：未完成稿在 PDF 首页有红色警示带");
  ok(h.indexOf("缺：第二轴与二维辨别格、可裁决判据、证伪条件、结语与参考文献") > 0, "警示带写清缺了哪几项（读者据此不按完稿评阅）");
  ok(h.indexOf("请勿按完整论文评阅或引用") > 0, "警示带写明不得按完整论文评阅");

  /* 「✓ 全文完成」只许出现在非 halfOnly 的那一支 —— 静默半篇的病根就在这一句 */
  const done = h.indexOf("'✓ 全文完成 · '");
  const guard = h.indexOf("halfOnly");
  ok(done > 0 && guard > 0 && guard < done, "状态栏：✓ 全文完成 只在 halfOnly 判定之后给出");
  ok(h.indexOf("⚠ 仅上半篇完成 · ") > 0, "状态栏：半篇有专属提示，不冒充完稿");
  ok(h.indexOf("请再点一次「成文一篇」") > 0, "状态栏：给出重来的动作");

  /* 回归：旧的流程契约不许被这次改动碰掉 */
  ok(h.indexOf("〔上半篇完·待续〕") > 0, "回归：前端仍认上半篇收尾标记");
  ok(h.indexOf("var cut=p1c.indexOf('【一、');") > 0, "回归：head 切分（题目+摘要）仍在");
  ok(h.indexOf("var tail=p1c.slice(-1000);") > 0, "回归：tail 续写起点仍在");
  ok(/mdSkip|mdClean|isPaperHead/.test(h), "回归：排版 v3 的三个兜底函数仍在");

  console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
  process.exit(F ? 1 : 0);
})();
