/* 只测一件事：站内搜索页「成文一篇」的上/下半篇守卫（public/search/index.html · paperHalf + doPaper 链）。

   病根（2026-07-29 发现）：论文分多次调用写成，旧版只给第一段做了长度守卫。
   （2026-08-10 起由两段改四段·两万字·投稿体例：单次调用有 ~120 秒平台时钟上限，
    5000 字/段是量出来的安全区，加长单段必被杀在思考阶段。所以字数靠加段数。）
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

t("第一段收尾标记被剥掉", () => { plan = [{ text: LONG + "\n〔第一段完·待续〕" }]; },
  (r) => r.indexOf("第一段完") < 0 && r.length === 2000);

t("第二/三段收尾标记同样被剥掉（新标记漏进正则＝标记原样印进 PDF）", () => { plan = [{ text: LONG + "\n〔第三段完·待续〕" }]; },
  (r) => r.indexOf("第三段完") < 0 && r.length === 2000);

t("回归：旧的上半篇标记仍被剥掉（基底偶尔沿用旧话术）", () => { plan = [{ text: LONG + "\n〔上半篇完·待续〕" }]; },
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
  /* 四段契约（2026-08-10 起）：两万字＝四段各约五千字，逐段有独立长度守卫。 */
  const parts = /var PAPER_PARTS=\[([\s\S]*?)\];/.exec(h);
  ok(!!parts, "doPaper：四段规格表 PAPER_PARTS 在位");
  const mins = parts ? (parts[1].match(/min:\s*(\d+)/g) || []) : [];
  ok(mins.length === 4, "四段整整四条规格（少一条＝有一段没有长度守卫）· 实得 " + mins.length);
  ok(/\{min:600\b/.test(h) && /\{min:1000\b/.test(h), "第一段 600 字守卫、末段 1000 字守卫都在");
  ok(/paperHalf\(i\s*\+\s*1,\s*seedFor\(i, head, acc\.slice\(-1000\)\), P\.min, P\.name\)/.test(h),
    "每一段都走 paperHalf 并带自己的最短长度（不是只守第一段）");
  ok(/if\(i===0\) throw e;/.test(h), "第一段彻底失败 → 抛给调用方（没有稿子就不该往下跑）");
  ok(/return '';\s*\/\* 后面某段失败不丢已写的部分/.test(h), "后续段失败 → 吞成空串，不丢已写的部分");
  ok(/if\(c\.length<P\.min\) return;/.test(h),
    "某段没写够就地停住，不再往后跑（后段要接前段结尾，硬跑会接到空气上）");
  ok(/function missText\(done, ?SPEC\)/.test(h) && /本稿只写完 '\+SPEC\.length\+' 段中的前 '\+done\+' 段，缺：/.test(h),
    "missText：按实际完成段数说清缺了哪几段");
  ok(h.indexOf("return buildPdf(paperAll, miss);") > 0, "doPaper：缺段说明一路传进 PDF 排版");
  ok(/function buildPdf\(text, incomplete, opt\)/.test(h), "buildPdf：接收缺段说明（并已参数化给打磨稿复用）");
  ok(h.indexOf("⚠ 未完成稿 · '+esc(String(incomplete))+'") > 0, "buildPdf：未完成稿在 PDF 首页有红色警示带");
  ok(h.indexOf("请勿按完整论文评阅或引用") > 0, "警示带写明不得按完整论文评阅");

  /* 「✓ 全文完成」只许出现在 miss 判定之后 —— 静默半篇的病根就在这一句 */
  const done = h.indexOf("✓ 全文完成 · ");
  const guard = h.indexOf("miss=missText(r.done)");
  ok(done > 0 && guard > 0 && guard < done, "状态栏：✓ 全文完成 只在缺段判定之后给出");
  ok(/stat\.textContent = miss/.test(h), "状态栏：缺段有专属提示，不冒充完稿");
  ok(h.indexOf("请再点一次「成文一篇」补齐") > 0, "状态栏：给出重来的动作");

  /* 投稿体例：四段合起来要凑齐的元素，前端文案与后端清单必须对得上 */
  ok(/四段深度写作 · 两万字投稿体例/.test(h), "按钮下的说明条已改成四段·两万字·投稿体例");
  ok(/成文一篇 · 两万字论文 → PDF/.test(h), "按钮文案已改成两万字");

  ok(/第\[一二三四\]段完/.test(h), "回归：前端认四段收尾标记");
  ok(/function partHead\(t\)\{[\s\S]*?indexOf\('【一、'\)/.test(h), "回归：head 切分（题名+摘要）仍在");
  ok(h.indexOf("acc.slice(-1000)") > 0, "回归：tail 续写起点仍在");
  ok(/mdSkip|mdClean|isPaperHead/.test(h), "回归：排版 v3 的三个兜底函数仍在");

  console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
  process.exit(F ? 1 : 0);
})();
