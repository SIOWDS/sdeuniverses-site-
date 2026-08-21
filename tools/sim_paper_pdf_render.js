/* 只测一件事：站内搜索页「成文一篇」出 PDF 时的行级排版兜底（mdSkip / mdClean / isPaperHead）。
   病根（2026-07-28 SDE-paper11 实例）：下半篇整段吐 Markdown（# 标题、**加粗**、|竖线表格|、--- 分隔线），
   旧渲染器只认【】与「一、」两种标题，其余一律 esc 成正文，于是这些标记原样印进了 PDF。
   规程 v2 已在 system prompt 里禁用 Markdown；本脚本守的是那层「不信任模型输出」的兜底。
   用例全部取自那一篇的真实行。 */
"use strict";
const fs = require("fs");
const html = fs.readFileSync("/home/claude/site/public/search/index.html", "utf8");

/* 把三个具名函数原样抠出来真跑（不复制一份实现——复制的那份永远不会跟着改） */
const names = ["mdSkip", "mdClean", "isPaperHead", "canvasInk", "pdfScaleFor"];
const PDF_MAX_PX = parseInt((html.match(/var PDF_MAX_PX = (\d+);/) || [])[1], 10);
let src = "";
names.forEach(function (n) {
  const a = html.indexOf("function " + n + "(");
  if (a < 0) { console.log("FAIL 抠不出 " + n + "（渲染器改名了，先改本脚本）"); process.exit(1); }
  const b = html.indexOf("\nfunction ", a + 1);
  src += html.slice(a, b < 0 ? a + 900 : b) + "\n";
});
const F = new Function("PDF_MAX_PX", src + "return {mdSkip:mdSkip, mdClean:mdClean, isPaperHead:isPaperHead, canvasInk:canvasInk, pdfScaleFor:pdfScaleFor};")(PDF_MAX_PX);

let P = 0, FA = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (FA++, console.log("  FAIL " + m)); };
const line = (raw) => ({ skip: F.mdSkip(raw), text: F.mdClean(raw), head: F.isPaperHead(raw, F.mdClean(raw)) });

/* —— 标题：Markdown 井号与 4.1 式编号都要认出来 —— */
let r = line("# 四、第二轴强制：从制度感知闭合到辨别格");
ok(r.head && r.text === "四、第二轴强制：从制度感知闭合到辨别格", "# 一级标题 → 认作标题且井号被剥掉");
r = line("## 4.1 候选轴的排除");
ok(r.head && r.text === "4.1 候选轴的排除", "## 二级标题 → 认作标题且井号被剥掉");
r = line("### 5.3 裁决表");
ok(r.head && r.text === "5.3 裁决表", "### 三级标题同样处理");
ok(F.isPaperHead("4.2 锁定第二轴：功能的内化程度", "4.2 锁定第二轴：功能的内化程度"), "没带井号的 4.2 式节标题也认");

/* —— 回归：老的两种标题形态不许被这次改动弄丢 —— */
ok(F.isPaperHead("【摘要】", "【摘要】"), "回归：【摘要】仍是标题");
ok(F.isPaperHead("一、引言", "一、引言"), "回归：「一、引言」仍是标题");
ok(!F.isPaperHead("这一命题以一句核心陈述立骨。", "这一命题以一句核心陈述立骨。"), "普通正文不被误判为标题");
ok(!F.isPaperHead("2020 年以来，教育系统面对的冲击不再只是策略问题，而是功能根基的动摇。",
  "2020 年以来，教育系统面对的冲击不再只是策略问题，而是功能根基的动摇。"), "以数字开头的长正文不被误判为标题");

/* —— 加粗：成对与落单都要清干净 —— */
ok(F.mdClean("本文给出一个不同的承重命题：**教育系统当前的僵持，并非源自定义清晰的抵抗**。")
  === "本文给出一个不同的承重命题：教育系统当前的僵持，并非源自定义清晰的抵抗。", "**成对加粗**被剥成纯文本");
ok(F.mdClean("而是一种定义丧失后的「失认」——** 它不是在抗拒") === "而是一种定义丧失后的「失认」——它不是在抗拒", "落单的 ** 也被清掉");
ok(F.mdClean("__下划强调__照样处理") === "下划强调照样处理", "__下划__ 同样剥掉");

/* —— 表格：分隔行整行丢弃，数据行转成可读的分隔符 —— */
ok(F.mdSkip("| :--- | :--- | :--- | :--- | :--- |"), "表格分隔行被整行丢弃");
ok(F.mdSkip("|---|---|"), "紧凑写法的分隔行也丢弃");
ok(F.mdSkip("---"), "--- 水平分隔线被丢弃");
ok(!F.mdSkip("| 象限/理论 | 泰亚克＆库班的预测 | 本文的预测 |"), "表头数据行不许被误丢");
ok(F.mdClean("| 象限/理论 | 泰亚克＆库班的预测 | 本文（失认症）的预测 |")
  === "象限/理论 ｜ 泰亚克＆库班的预测 ｜ 本文（失认症）的预测", "表格数据行 → 全角竖线分隔的一行");
ok(F.mdClean("| **第二象限（判别格）**<br>（高内化, 高闭合） | 语法**会抵抗** |")
  === "第二象限（判别格） （高内化, 高闭合） ｜ 语法会抵抗", "表格行里的加粗与 <br> 一并归一");

/* —— 兜底不许吃掉正文 —— */
ok(F.mdClean("教育改革的真正阻碍不是「学校语法」的坚固。") === "教育改革的真正阻碍不是「学校语法」的坚固。", "普通正文原样通过");
ok(F.mdClean("") === "" && F.mdClean("   ") === "", "空行归一为空（调用方据此跳过）");

/* ================= PDF 空白自检（2026-08-21）=================
   线上真交出过一份 **33 页全白**的 PDF：jsPDF 2.3.1，每页 content stream 只有
   `q … cm /I0 Do Q`（只画一张图、零文字对象），那张图是纯白 JPEG（灰度 min=max=255）。
   页数是对的 ⇒ DOM 有内容、高度算得出，白掉的是 html2canvas 那一步。
   最坏的地方不是白，是**它静默地成功了**：进度条走完、状态行报「PDF 已就绪」，
   读者拿去当交付物才发现是白纸。这一组守那道墨量闸。
   ⚠ 阈值从源码抽出来比，不手抄——手抄的数只会在下次调阈值时安静失效。 */
console.log("— 空白画布自检 —");
const INK_MIN = parseFloat((html.match(/var INK_MIN=([\d.]+);/) || [])[1]);
ok(INK_MIN > 0 && INK_MIN < 0.05, "源码里取得到墨量下限 INK_MIN · 实得 " + INK_MIN);

/* 假画布：drawImage 把源画布的 _ink（暗像素占比）记下来，getImageData 按它铺数据。
   这样测的是 canvasInk 自己的算法（缩图→数非白→算占比），不必真起一个浏览器。 */
function fakeSrc(w_, h_, ink) { return { width: w_, height: h_, _ink: ink }; }
function mkFake(opt) {
  opt = opt || {};
  return function () {
    let W = 0, H = 0, ink = 0;
    return {
      set width(v) { W = v; }, get width() { return W; },
      set height(v) { H = v; }, get height() { return H; },
      getContext() {
        return {
          fillStyle: "", fillRect() { },
          drawImage(src) { ink = src._ink || 0; },
          getImageData(x, y, w_, h_) {
            if (opt.taint) throw new Error("SecurityError: tainted canvas");
            const n = w_ * h_, d = new Uint8ClampedArray(n * 4);
            const dark = Math.round(n * ink);
            for (let i = 0; i < n; i++) {
              const v = i < dark ? 20 : 255;
              d[i * 4] = v; d[i * 4 + 1] = v; d[i * 4 + 2] = v; d[i * 4 + 3] = 255;
            }
            return { data: d };
          }
        };
      }
    };
  };
}
const blank = F.canvasInk(fakeSrc(1588, 67000, 0), mkFake());
ok(blank < INK_MIN, "整份全白 ⇒ 墨量低于下限，出稿被拦下 · 实得 " + blank);
const good = F.canvasInk(fakeSrc(1588, 67000, 0.05), mkFake());
ok(good >= INK_MIN, "正常论文（5% 非白）⇒ 放行 · 实得 " + good.toFixed(4));
const thin = F.canvasInk(fakeSrc(1588, 67000, 0.004), mkFake());
ok(thin >= INK_MIN, "只有题名与金线的极稀页也放行（阈值留得松，宁可放过不可错杀）· 实得 " + thin.toFixed(4));
ok(F.canvasInk(fakeSrc(0, 0, 0), mkFake()) === 0, "零尺寸画布 ⇒ 0（确定是白的）");
ok(F.canvasInk(fakeSrc(1588, 2000, 0.05), mkFake({ taint: true })) === -1,
  "画布读不到（跨域污染）⇒ 返回 -1＝不判，绝不因为量不到就拦掉真稿");

/* 闸装没装上、装在哪一步——只看代码形状 */
const bp = html.slice(html.indexOf("function buildPdf(text"), html.indexOf("var iqCard="));
ok(/\.toCanvas\(\)\.then\(/.test(bp), "出稿链里真的先 toCanvas 量一次，再 outputPdf");
ok(bp.indexOf(".toCanvas()") < bp.indexOf(".outputPdf('blob')"), "量墨排在出 blob 之前（出完再量就晚了）");
ok(/ink>=0 && ink<INK_MIN/.test(bp), "只在「量得到且低于下限」时拦（-1 那一支放行）");
ok(/throw new Error\('PDF 渲染出来是白纸/.test(bp), "拦下时抛错并报读数，不静默交白稿");
ok(/画布 '\+cv\.width\+'×'\+cv\.height/.test(bp), "读数里带画布尺寸（判「是没画还是画歪了」全靠它）");

/* ⚠⚠ 上面全是形状判据 —— 第一版就是这么全绿着上线的，而闸**根本没接上**：
   html2pdf 的 then 用 onFulfilled.bind(this) 把 this 绑到 worker，
   画布挂在 **this.prop.canvas**（0.10.1 源码 `this.prop.canvas=e`），不是 this.canvas。
   写成 this.canvas 不报错，只是永远 undefined，`cv?…:-1` 那一支于是一路放行。
   所以这里把闸的回调**原样抠出来真跑**，`this` 换成一个仿真 worker —— 形状对不对不算数，
   拿不拿得到画布才算数。 */
/* ================= 画布高度上限（2026-08-21 查实的白页根因）=================
   那份 33 页全白的 PDF 自己带着证据：每页 1588×2034 px，32 满页＋末页 1886
   ⇒ 整份画布高 66,974 px，而 **Chrome 单张 canvas 的高度硬上限是 65,535 px**。
   超限不抛错、不报警，只是静静给一张空白画布 —— 于是「页数对、内容没」。
   超出仅 2.2%，临界点 65535/2034 ≈ 32.2 页：成文四段改五段把稿子推过了线。
   ⇒ scale 必须跟着稿子长度走。下面用**那份真稿的高度**当夹具。 */
console.log("— 画布高度上限：长稿必须自动降倍率 —");
ok(PDF_MAX_PX > 0 && PDF_MAX_PX < 65535,
  "上限常量取自源码，且留了余量（<65535）· 实得 " + PDF_MAX_PX);
ok(F.pdfScaleFor(11230) === 2, "十页的稿子照旧 scale 2（不许为了防边界把所有稿子都弄糊）");
const realH = Math.round(66974 / 2);                    /* 那份真稿的 CSS 排版高度 */
const s33 = F.pdfScaleFor(realH);
ok(s33 < 2, "33 页那份真稿必须降倍率 · 实得 " + s33);
ok(realH * s33 <= 65535, "降完之后画布高度落在浏览器上限之内 · 实得 " + Math.round(realH * s33) + "px");
ok(realH * 2 > 65535, "夹具本身是对的：不降倍率的那一版确实越线（" + realH * 2 + "px）");
ok(F.pdfScaleFor(200000) >= 0.5, "再长也不低于 0.5（低于这个字不可读，交给墨量闸去拦）");
ok(F.pdfScaleFor(0) === 2 && F.pdfScaleFor(undefined) === 2, "量不到高度 ⇒ 退回 2，不因为读数缺失就把稿子弄糊");
let mono = true;
for (let h = 20000; h <= 120000; h += 1000) if (F.pdfScaleFor(h) > F.pdfScaleFor(h - 1000)) mono = false;
ok(mono, "倍率随稿子变长单调不升（不许中间反弹回去越线）");

/* 闸装没装在出稿链上 */
console.log("— 倍率真的传给了 html2canvas —");
const bpScale = html.slice(html.indexOf("function buildPdf(text"), html.indexOf("var iqCard="));
ok(/var _scale=pdfScaleFor\(_h\);/.test(bpScale), "出稿前按排版高度算一次倍率");
ok(/scrollHeight/.test(bpScale), "高度取自真实排版（元素已进文档，scrollHeight 才有值）");
ok(/html2canvas:\{scale:_scale,/.test(bpScale), "算出来的倍率真的传给了 html2canvas（不是算完丢掉）");
ok(!/html2canvas:\{scale:2,/.test(bpScale), "写死的 scale:2 已经不在");
ok(/PDFLOG\.push\(/.test(bpScale) && /采样倍率已由 2 降到/.test(bpScale),
  "降了倍率要说出来（不许静默改画质）");
/* ⚠ 只搜变量名是搜不出事的：`var pdfNote='';` 里照样有 pdfNote。要搜的是**它真的从
   PDFLOG 取了值、又真的进了状态行**——这一条第一版就是这么绿着被变异测试打脸的。 */
const dp = html.slice(html.indexOf("function doPaper(){"), html.indexOf("function loadHtml2pdf("));
ok(/PDFLOG\.length\s*\?/.test(dp) && /PDFLOG\.join\(/.test(dp), "状态行真的从 PDFLOG 取读数，不是一个空串");
ok(/stat\.textContent = \(miss \|\| cut \|\| auMsg \|\| pdfNote\)/.test(dp), "有读数时状态行会走「有话要说」那一支");
ok(/\?\s*pdfNote\+cut\+auMsg/.test(dp), "读数排在最前面（读者一眼看到画质降了）");

console.log("— 闸真的接在 worker 上（不是只有形状对）—");
const _gA = bp.indexOf(".toCanvas().then(function(){");
const _gB = bp.indexOf("}).outputPdf('blob')", _gA);
ok(_gA > 0 && _gB > _gA, "抠得到墨量闸的回调");
const guardBody = bp.slice(_gA + ".toCanvas().then(function(){".length, _gB);
ok(guardBody.trim().length > 0, "抠出来的回调非空（空串对 !/…/.test 全是 PASS，会安静失效）");
/* 闸的读数里要带采样倍率与排版高度（判「是没画还是超了上限」全靠这两个数），
   它们是 buildPdf 的闭包变量 —— 桩必须跟着契约一起长，否则真跑会炸在 ReferenceError 上
   而不是抛出那句该抛的话。 */
const guard = new Function("INK_MIN", "canvasInk", "text", "_scale", "_h",
  "return function(){" + guardBody + "};")(INK_MIN, (cv) => F.canvasInk(cv, mkFake()), "正文两万字", 1.75, 33487);
const fire = (self) => { try { guard.call(self); return null; } catch (e) { return e.message; } };
const msg = fire({ prop: { canvas: fakeSrc(1588, 67000, 0) } });
ok(msg && /白纸/.test(msg), "worker.prop.canvas 上的全白画布 ⇒ 真的抛错（写成 this.canvas 这条会红）");
ok(msg && /1588×67000/.test(msg), "错误里报出真实画布尺寸 · 实得：" + String(msg).slice(0, 60));
ok(msg && /采样倍率 1\.75/.test(msg) && /排版高 33487px/.test(msg),
  "读数里带采样倍率与排版高度（判「是没画还是超了浏览器上限」全靠这两个数）");
ok(msg && /65535/.test(msg), "读数里点名浏览器的画布上限，看的人不用再去查");
ok(fire({ prop: { canvas: fakeSrc(1588, 67000, 0.05) } }) === null, "正常画布 ⇒ 放行");
ok(fire({ canvas: fakeSrc(1588, 67000, 0) }) !== null, "兜底：画布挂在 this.canvas 上也量得到（上游改字段时还活着）");
ok(fire({}) === null, "拿不到画布 ⇒ 放行，绝不因为量不到就拦真稿");
ok(fire(undefined) === null, "this 丢了也不炸（不许把出稿链搞成一个新的静默死法）");


console.log("\n===== " + P + " PASS / " + FA + " FAIL =====");
process.exit(FA ? 1 : 0);
