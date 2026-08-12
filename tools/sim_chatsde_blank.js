/* sim_chatsde_blank.js —— 两万字稿收尾白屏的护栏
 *   ① scanForward：真跑。学术节号（3.1／11.3）必须是安全切点，有序列表项仍必须不是
 *   ② paintD(final)：真跑。长尾巴要按块 appendSeg，不许一口气 innerHTML 一大坨
 *   ③ 心跳自愈：正文被清空后，下一拍必须把稿子退回纯文本救回来，且只救一次
 *   ④ 源码级：收尾三段必须分帧（不许两个 setTimeout 0 背靠背）、autoLink 早退
 * 跑法：node tools/sim_chatsde_blank.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");
let pass = 0, fail = 0;
const ok = (n, c) => { if (c) { pass++; console.log("  ✓ " + n); } else { fail++; console.log("  ✗ " + n); } };
const FSRC = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");

/* 从源码里抠出这三个函数一起跑——不手抄形状、不写字面量。 */
function grab(startMark, endMark) {
  const a = FSRC.indexOf(startMark);
  const b = FSRC.indexOf(endMark, a);
  return (a > 0 && b > a) ? FSRC.slice(a, b) : "";
}
const scanSrc = grab("    function scanForward(final) {", "    function appendSeg(seg) {");
const segSrc = grab("    function appendSeg(seg) {", "    /* 留痕：");
const paintSrc = grab("    function paintD(final) {", "    /* 上一次成文若没有正常收尾");
const __seg = segSrc, __paint = paintSrc;
ok("抠得到 scanForward / appendSeg / paintD", !!scanSrc && !!segSrc && !!paintSrc);

/* ═══ ① scanForward ═══ */
console.log("── scanForward：节号 vs 列表项 ──");
function mkScan(txt) {
  const box = { text: txt, scanAt: 0, lastSafe: 0, rendUpto: 0, fenceOdd: false, mathOdd: false };
  const fn = new Function("__b", "final",
    "var text=__b.text, scanAt=__b.scanAt, lastSafe=__b.lastSafe, rendUpto=__b.rendUpto," +
    "    fenceOdd=__b.fenceOdd, mathOdd=__b.mathOdd;" +
    scanSrc.replace("    function scanForward(final) {", "(function(){").replace(/\}\s*$/, "})();") +
    "__b.scanAt=scanAt; __b.lastSafe=lastSafe; __b.fenceOdd=fenceOdd; __b.mathOdd=mathOdd;");
  fn(box, true);
  return box;
}
const secTxt = "开头一段。\n\n3.1 核心概念的名义定义\n\n正文若干。\n\n11.3 适用边界与反向约束\n\n再一段。";
ok("学术节号 3.1 / 11.3 是安全切点（否则尾巴永远顶到 8000 上限）", mkScan(secTxt).lastSafe > 0);
const listTxt = "开头一段。\n\n1. 第一条\n2. 第二条\n3. 第三条";
ok("有序列表项仍然不是安全切点（不许把一个列表拆成两个）", mkScan(listTxt).lastSafe === 0);
ok("无序列表项仍然不是安全切点", mkScan("开头一段。\n\n- 甲\n- 乙").lastSafe === 0);
ok("引用行仍然不是安全切点", mkScan("开头一段。\n\n> 引一句").lastSafe === 0);
ok("普通段落是安全切点", mkScan("开头一段。\n\n普通的下一段。").lastSafe > 0);
ok("章标题 ## 是安全切点", mkScan("开头一段。\n\n## 三、理论框架\n\n正文。").lastSafe > 0);

/* ═══ ② paintD(final)：长尾必须分块 ═══ */
console.log("── paintD(final)：长尾分块 ──");
function mkPaint(tailLen) {
  const paras = [];
  for (let i = 0; paras.join("\n\n").length < tailLen; i++) paras.push("段落" + i + "。".repeat(120));
  const txt = paras.join("\n\n");
  const calls = { appendSeg: 0, innerHTMLLen: 0, mdRender: 0 };
  /* tailEl 用真 getter/setter：innerHTML 被写过多少字，是"有没有一口气塞一大坨"的直接读数 */
  const tailEl = { className: "wdsm-tail", _t: "", _h: "",
    set textContent(v) { this._t = v; }, get textContent() { return this._t; },
    set innerHTML(v) { this._h = v; calls.innerHTMLLen += String(v).length; }, get innerHTML() { return this._h; } };
  const out = { insertBefore: () => { calls.appendSeg++; }, innerHTML: "", appendChild: () => {} };
  /* scanForward 在这一测里不参与（它自己上面已经单独测过），置空即可；
     其余一律用源码原文，不做任何字符串改写——改写过一次，改出来的是语法错。 */
  const src =
    "var text=__b.text, rendUpto=0, lastSafe=0, paintedHtml=0, tailEl=__b.tailEl, out=__b.out," +
    "    paintGap=130, pTrace={ paints:0 };" +
    "function scanForward(){} function traceSave(){}\n" +
    __seg + "\n" + __paint + "\n paintD(true); __b.paintedHtml = paintedHtml;";
  const box = { text: txt, tailEl: tailEl, out: out };
  new Function("__b", "el", "mdRender", src)(
    box,
    () => ({ innerHTML: "", textContent: "", className: "" }),
    (s2) => { calls.mdRender++; return "<p>" + s2 + "</p>"; });
  return { calls, len: txt.length };
}
const big = mkPaint(9000);
ok("长尾（" + big.len + " 字）走分块：appendSeg 被调用多次", big.calls.appendSeg >= 3);
ok("长尾不再一口气把一大坨塞进 tailEl.innerHTML", big.calls.innerHTMLLen === 0);
ok("长尾的 mdRender 是逐块调用的", big.calls.mdRender >= 3);
const small = mkPaint(1200);
ok("短尾仍走一次性 innerHTML（别为了分块把简单路径也搞复杂）", small.calls.innerHTMLLen > 0 && small.calls.appendSeg === 0);
const mThr = paintSrc.match(/if \(tail\.length > (\d+)\)/);
const mChunk = paintSrc.match(/if \(_buf\.length >= (\d+)\)/);
ok("分块阈值与块长都是源码里取的，不是这里手抄的", !!mThr && !!mChunk);
ok("块长小于阈值（否则分块等于没分）", !!mThr && !!mChunk && +mChunk[1] < +mThr[1]);

/* ═══ ③ 心跳自愈正文 ═══ */
console.log("── 心跳自愈：白屏就地退回纯文本 ──");
const beatSrc = grab("    beatT = setInterval(function () {", "    }, 2000);");
ok("抠得到心跳", beatSrc.indexOf("bodyHealed") > 0);
function mkBeat(outHasText, textLen, painted, hasChild) {
  const notes = [];
  const box = { healed: 0 };
  /* firstChild 是"此刻 DOM 里还有没有东西"的结构量；painted 是历史累计量。
     两者分开传，才测得出「排过版但正文已经没了」这个唯一要救的场景。 */
  const out = { textContent: outHasText ? "有字" : "", innerHTML: outHasText ? "<p>有字</p>" : "",
                firstChild: hasChild ? {} : null };
  const src =
    "var bodyHealed=0, paintedHtml=" + painted + ", text=__b.text, out=__b.out, wrap=__b.wrap," +
    "    beatLast=Date.now(), pTrace={}, beatT=1;" +
    "function traceSave(){} function el(){return {};} function t(k){return k;}" +
    "function dNote(v){ __b.notes.push(String(v)); }" +
    "function clearInterval(){}\n" +
    /* beatSrc 是 setInterval 那个回调的**函数体**（起点锚在 `beatT = setInterval(function () {` 之后、
       终点锚在 `}, 2000);` 之前），所以直接包成一个函数体跑一拍即可，不做任何字符串裁剪——
       裁剪过一次，裁出来的是语法错。 */
    "(function(){" + beatSrc.slice(beatSrc.indexOf("{") + 1) + "})();" +
    "__b.healed = bodyHealed; __b.outText = out.textContent;";
  new Function("__b", src)(Object.assign(box, {
    text: "x".repeat(textLen), out: out, wrap: { parentNode: {}, querySelector: () => ({}) }, notes: notes,
  }));
  return { box, notes, out };
}
const b1 = mkBeat(false, 5000, 0, false);
ok("正文空 + 稿子有字 → 自愈成纯文本", b1.box.healed === 1 && b1.out.textContent.length === 5000);
ok("自愈时报了一句给读者（dBlankFix）", b1.notes.join("|").indexOf("dBlankFix") >= 0);
const b2 = mkBeat(true, 5000, 100, true);
ok("正文有字 → 不动它（不许把排好的版白白拆成纯文本）", b2.box.healed === 0);
const b3 = mkBeat(false, 5000, 500, true);
ok("正文框还有子节点 → 不动（可能是图/canvas 这类没文字的东西，别拆）", b3.box.healed === 0);
/* ⚠ 这一条是本文件存在的理由：判据原来用 paintedHtml（只增不减的累计量），
   于是"排过版之后正文又没了"——唯一需要兜底的场景——永远兜不到，自愈从写下那天起就是死的。 */
const b5 = mkBeat(false, 5000, 999999, false);
ok("★ 排过很多版但此刻正文空了 → 必须自愈（判据不许用累计量）", b5.box.healed === 1);
const b4 = mkBeat(false, 50, 0, false);
ok("稿子太短（没写出东西）→ 不当白屏处理", b4.box.healed === 0);

/* ═══ ④ 源码级：收尾分帧与早退 ═══ */
console.log("── 收尾分帧与早退 ──");
/* ⚠ 终点锚原来是 `wrap.querySelector(".dx").onclick` —— 那一行在「面板关不掉」那一修里被
   事件委托取代了，锚失效后 indexOf 返回 -1，slice 一路切到文件末尾，
   于是别处的 setTimeout(..., 0) 被算进"收尾的延时"，这条就红了。
   改锚到 done() 之后紧跟的那段注释（它属于 done 这一块，不会被别的改动带走）。 */
const _d0 = FSRC.indexOf("    function done() {\n      clearTimeout(dWd);");
/* ⚠ 终点锚第二次被改动带走了（上一轮锚 .dx onclick，这一轮锚那段注释，注释又被挪过）。
   改用**不会被下一次改动带走**的东西：done() 之后紧跟的下一个顶层 function 声明。 */
const _d1 = FSRC.indexOf("\n    function ", _d0 + 40);
const doneSrc = FSRC.slice(_d0, _d1 > _d0 ? _d1 : _d0 + 9000);
ok("抠得到 done()", doneSrc.length > 800);
/* ⚠ 别用裸的 /\}, (\d+)\);/ 去捞延时——它会把 `.reduce(function(a,s){…}, 0)` 的**初值 0**
   当成一个 0 毫秒的 setTimeout（本文件真被这条误报红过一次）。
   只认「换行 ＋ 六个空格 ＋ }, N);」这一种收尾形态，那是这两块 setTimeout 独有的。 */
const gaps = (doneSrc.match(/setTimeout\(function[\s\S]*?\n      \}, (\d+)\);/g) || [])
  .map((x) => +x.match(/\n      \}, (\d+)\);$/)[1]);
ok("收尾的延时都不是 0（两个 0ms 任务会紧挨着排，浏览器插不进一帧）", gaps.length >= 2 && gaps.every((g) => g > 0));
ok("两段重活的延时不相同、且递增（先上屏，再锦上添花）", gaps.length >= 2 && gaps[1] > gaps[0]);
ok("稿子仍然先落地再谈显示（distSave 排在 paintD 之前）",
  doneSrc.indexOf("distSave(") > 0 && doneSrc.indexOf("distSave(") < doneSrc.indexOf("paintD(true)"));
ok("autoLink 早退：没有书名号就不扫整篇", /text\.indexOf\("\\u300a"\) >= 0/.test(doneSrc));
ok("autoLink 的长度闸还在", /text\.length <= 40000/.test(doneSrc));
ok("白屏兜底（done 里那一条）没被删", doneSrc.indexOf("dBlankFix") > 0);
/* 只查那个三元判据的形状；解释这条病的注释里也写着 paintedHtml，别把注释算成病 */
ok("★ 两处白屏判据都不再用 paintedHtml 这个累计量",
  (FSRC.match(/\(paintedHtml > 0 \? /g) || []).length === 0);
ok("两处白屏判据都改用 out.firstChild 这个此刻的结构量",
  (FSRC.match(/out\.firstChild \? "1" : ""/g) || []).length === 2);

/* ═══ 五、成文记录还原：kind 不能丢，否则 Word/PDF/投稿三颗按钮全没有 ═══ */
console.log("── 成文记录还原 ──");
const rst = FSRC.slice(FSRC.indexOf("onRestore: function (rec)"), FSRC.indexOf("onRestore: function (rec)") + 1200);
ok("还原不再写死 report", !/distill\("report", body, head\)/.test(rst));
ok("还原按 scopeLabel 反查 kind（用 KIND_KEYS 派生，不手抄档名）", /KIND_KEYS\.forEach/.test(rst) && /kindT\(x\) === head/.test(rst));
ok("老记录对不上时按正文形状兜底认成 paper", /\? "paper" : "report"/.test(rst));
ok("导出按钮仍只挂在 essay/paper 两档（还原回 paper 才拿得到）",
  /if \(kind === "essay" \|\| kind === "paper"\)/.test(FSRC));
ok("痕迹逐步打标仍在（收尾·存稿／排版／挂链接／库存）",
  ["收尾·存稿", "收尾·排版", "收尾·挂链接", "收尾·库存", "已收尾"].every((k) => doneSrc.indexOf(k) > 0));

console.log("\n" + (fail ? "✗ " : "✓ ") + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
