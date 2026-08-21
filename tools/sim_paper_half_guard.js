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
/* paperHalf 现在会在「末次仍是零字」时抛出带读数的错误，读数来自源码里的 RUNLOG/runWhy。
   ⚠ 这一段必须从源码抠出来真跑，不许在本脚本里手抄一个假的——手抄的后果不是报错，
   是它安静地测一个已经不存在的版本。 */
const da = h.indexOf("var RUNLOG=");
const db = h.indexOf("function streamPaper(");
if (da < 0 || db <= da) { console.log("FAIL 抠不出读数块 RUNLOG/runWhy（锚点变了，先改本脚本）"); process.exit(1); }
const diag = h.slice(da, db);

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
  /* ⚠ 2026-08-21：paperHalf 的重写判据新增了两个外部依赖——RUNLOG（上游有没有正常收笔）
     与 looksCut（末尾是不是半句）。两者都定义在抠取范围之外，不喂进来就 ReferenceError。
     **抠取式护栏的通病：被抠的函数长出新依赖时，护栏是「崩」不是「红」**，而崩比红更容易
     被当成「环境坏了」放过去。所以桩要跟着契约一起长——looksCut 用页面里的真实现，不另写一份。 */
  const looksCutSrc = h.slice(h.indexOf("function looksCut(txt){"), h.indexOf("function finishAsk("));
  const runlog = { frames: 1, done: true, fin: "stop", sec: 0, think: 0 };
  const fn = new Function("document", "streamPaper", "GEN_STAT", "RUNLOG",
    looksCutSrc + "\n" + diag + "\n" + seg + "\nreturn paperHalf;");
  return fn(stub, streamPaper, "paperStat", runlog);
}

const LONG = "字".repeat(2000);
/* 【2026-08-18 契约新增：段末标记闸】paperHalf 现在先问「收尾标记在不在」再剥它。
   于是**「成功」的桩必须自己带上收尾标记**——不带的桩表达的是「断在半句上」，
   会照新契约触发一次重试。旧桩全是不带标记的，所以这一批 D 后缀是必须的，不是装饰。 */
const DONE = "\n〔全文完〕";
const LONGD = LONG + DONE;
const tests = [];
function t(name, setup, check, wantThrow) { tests.push({ name, setup, check, wantThrow }); }

t("一次就够长且正常收尾 → 只调一次，原样返回", () => { plan = [{ text: LONGD }]; },
  (r) => r.length === 2000 && calls === 1);

t("第一次空串 → 自动重试；第二次成功 → 返回第二次的稿子", () => { plan = [{ text: "" }, { text: LONGD }]; },
  (r) => r.length === 2000 && calls === 2);

/* ===== 段末标记闸（2026-08-18）=====
   线上真现场：提炼精华的第二段断在「第八章 ④ 最难的一处：结论必须」，
   而屏幕上打的是「✓ 论文入口资料已就绪」——因为旧版只把收尾标记**剥掉**、从不问它在不在，
   一段断在半句上的稿只要够长就被当成写完了。那份断掉的施工图会把缺口原样带进两万字论文。 */
t("够长但没有收尾标记（断在半句）→ 重试一次", () => { plan = [{ text: LONG }, { text: LONGD }]; },
  (r) => r.length === 2000 && calls === 2);

t("两次都断在半句 → 照收已写的，不再第三次（重试封顶仍然管用）",
  () => { plan = [{ text: LONG }, { text: LONG }, { text: LONGD }]; },
  (r) => r.length === 2000 && calls === 2);

/* 【2026-08-13 契约翻面】旧版：两次都空 → 返回空串。那一行把「整条链死在这里」
   悄悄变成了「成功返回了 0 字」，真因（前置吃掉几秒、思考烧了几字、是不是被平台
   无声掉线）全部丢光，上层只好拿一句写死的猜测顶上——线上那次提炼 0 字就是这么来的。
   已写部分仍然保得住：那件事由 runParts 的 `if(i===0) throw e; return '';` 负责，
   不该由 paperHalf 用「把失败伪装成成功」来实现（下面仍有源码契约在守）。 */
t("两次都空 → 抛错，且错误里带得出读数（不许把死当成 0 字的成功交回去）",
  () => { plan = [{ text: "" }, { text: "" }]; },
  (e) => calls === 2 && /正文 0 字/.test(e.message) && /下半篇/.test(e.message), true);

t("重试封顶两次（不许无限重试烧配额）", () => { plan = [{ text: "" }, { text: "" }, { text: LONGD }]; },
  (e) => calls === 2, true);

t("写出一部分但没到最短长度 → 照旧收下（半段稿仍是稿，那不是静默）",
  () => { plan = [{ text: "字".repeat(300) }, { text: "字".repeat(300) }]; },
  (r) => r.length === 300 && calls === 2);

t("第一次报错 → 重试；第二次成功", () => { plan = [{ err: "网络中断" }, { text: LONGD }]; },
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
    if (x.wantThrow) ok(!!threw && x.check(threw), x.name + (threw ? "" : "（该抛错却没抛：静默又回来了）"));
    else ok(!threw && x.check(r), x.name + (threw ? "（意外抛错：" + threw.message + "）" : ""));
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
  /* ⚠ 2026-08-21 成文由四段改五段（第四段要装八项必交项，两次写到七八千字仍收不住笔）。
     断言从此钉**判据**——每一段都得有长度守卫、段数与段名一一对应——不再钉「4」这个数字。
     写死一个段数，下次改段数时红的是护栏而不是缺陷。 */
  const pnames = parts ? (parts[1].match(/name:'第[一二三四五]段'/g) || []) : [];
  ok(mins.length >= 4 && mins.length === pnames.length,
    "每一段都有长度守卫，且守卫数与段名数一一对应 · 实得 " + mins.length + " 段");
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
  /* 2026-08-18：收尾判据由「缺段」一件事扩成两件——缺段(miss) 与 断段(cut)。
     断段＝写出来了但没写到收尾标记；它此前完全不可见，屏幕照打「✓ 全文完成」。 */
  ok(/stat\.textContent = \(miss \|\| cut\)/.test(h), "状态栏：缺段与断段都有专属提示，不冒充完稿");
  ok(/var cut=CUTLOG\.length\?/.test(h), "状态栏：断段（CUTLOG）参与收尾判定");
  ok(h.indexOf("请再点一次「成文一篇」补齐") > 0, "状态栏：给出重来的动作");

  /* 投稿体例：四段合起来要凑齐的元素，前端文案与后端清单必须对得上 */
  ok(/[四五]段深度写作 · 两万字投稿体例/.test(h), "按钮下的说明条写明段数·两万字·投稿体例");
  ok(/成文一篇 · 两万字论文 → PDF/.test(h), "按钮文案已改成两万字");

  ok(/第\[一二三四五\]段完/.test(h), "回归：前端的段末标记正则认得到最后一段（漏一段＝末段永远被判「断在半句」）");
  ok(/function partHead\(t\)\{[\s\S]*?indexOf\('【一、'\)/.test(h), "回归：head 切分（题名+摘要）仍在");
  ok(h.indexOf("acc.slice(-1000)") > 0, "回归：tail 续写起点仍在");
  ok(/mdSkip|mdClean|isPaperHead/.test(h), "回归：排版 v3 的三个兜底函数仍在");

  /* ===== 三、零产出必须能说出自己是怎么死的（2026-08-13）=====
     线上真故障：提炼精华 0 字，屏幕上是一句写死的猜测。三种完全不同的死法
     （思考烧光额度 / 平台无声掉线 / 前置吃光窗口）从前被写成同一句话。 */
  ok(/var RUNLOG=\{[^}]*stat:''[^}]*think:0[^}]*out:0[^}]*sec:0/.test(h), "读数记录器 RUNLOG 在位（含 stat/think/out/sec）");
  ok(/function runWhy\(\)/.test(h), "runWhy：把读数拼成一句能读的话");
  ok(/else if\(j\.t==='beat'\)/.test(h), "前端接住服务端心跳帧 beat（否则「死在第几秒」永远看不见）");
  ok(/RUNLOG\.pre=j\.v/.test(h), "「开始作答·前置用掉 Xs」那条状态被单独留住（它是全链唯一的时间证据）");
  ok(/if\(!c\.length && attempt>=2\) throw new Error/.test(h), "paperHalf：末次零字抛错，不再伪装成功");
  ok(h.indexOf("'⚠ 这一轮一个字的正文都没写出来。读数：'+runWhy()") > 0, "提炼零产出：印读数，不印猜测");
  ok(/_bump\(170000\)/.test(h) && /_bump\(75000\)/.test(h), "成文/提炼这条流也有看门狗（首帧 170s·帧间 75s）");
  ok(/signal:_ac\?_ac\.signal:undefined/.test(h), "看门狗真的接到了 fetch 上（没接＝装饰品）");
  const _sse = h.indexOf("function sseCollect(");
  const _sseEnd = h.indexOf("function paradigmName(");
  const _sseSeg = _sse > 0 && _sseEnd > _sse ? h.slice(_sse, _sseEnd) : "";
  ok(/if\(!acc\.length\)\{ rej\(new Error/.test(_sseSeg), "sseCollect（碰撞/盲评/综合）：流干净结束却零字 → 报错，不再 res('')");

  console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
  process.exit(F ? 1 : 0);
})();
