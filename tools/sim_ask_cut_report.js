/* 只测一件事：**「写出了正文、却断在半句上」这一种死法，能不能被看见**
   （src/worker.js 的 askCore 收笔读数 ＋ public/search/index.html 的段末标记闸）。

   2026-08-18 线上真现场：用户点「🧪 提炼精华」，第二段（第十栏·论文观点与分章大纲）
   断在「第八章 ④ 最难的一处：结论必须」，后面的 ⑤⑥ 与〔供料自查〕整块没有；
   而状态栏打的是「✓ 论文入口资料已就绪」。三道口子叠在一起才造出这个静默：

     ① 服务端 _drain 早就拿到了 finish_reason、也知道上游有没有发过 [DONE]，
        但只有「零正文」那一支会说话 ⇒ 断稿与完稿在流里长得一模一样；
     ② 前端 paperHalf 只把收尾标记（〔全文完〕之类）**剥掉**，从不问它在不在
        ⇒ 断稿只要够长就过 min 闸，missText 返回 false，屏幕照打「✓」；
     ③ streamPaper 收到 error 帧就 reject，把已经流下来的几千字整个丢掉——
        而服务端**恰恰只在「写到一半才断」时才发这一帧** ⇒ 被掐 ⇒ 整段消失 ⇒
        上层重跑一次 ⇒ 再被掐 ⇒ 这一段彻底没有。

   本脚本对着这三条，外加一条独立的旧债（入口资料按段截断，把最末的施工图整块切掉）。
   ⚠ 判「完没完」由两边互为佐证，缺一不可：
       有收尾标记 ＋ doneMark ⇒ 正常收笔；
       无收尾标记 ＋ doneMark ⇒ 基底自己提前停笔（fin 说是 length 还是 stop）；
       无收尾标记 ＋ 无 doneMark ⇒ 整条流被掐（我们的时钟，或平台那道 128–133 秒的墙）。
     所以本脚本既守前端那道闸，也守服务端那三个数——只留一边等于只知道「断了」，
     不知道「被谁断的」，而那正是这一整轮返工要买的东西。 */
"use strict";
const fs = require("fs");
const W = fs.readFileSync("/home/claude/site/src/worker.js", "utf8");
const H = fs.readFileSync("/home/claude/site/public/search/index.html", "utf8");

let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };
const one = (s, re) => (s.match(re) || []).length === 1;

/* ===== 一、服务端：收笔读数 ===== */
console.log("— 一、服务端 askCore：收笔读数 —");

ok(/let buf = "", out = 0, think = 0, fin = "", errs = 0, doneMark = false;/.test(W),
  "_drain 声明了 doneMark（上游有没有正常收尾，是分辨死法的唯一硬证据）");
ok(/if \(p === "\[DONE\]"\) \{ doneMark = true; continue; \}/.test(W),
  "_drain 真的把 [DONE] 记下来了（只 continue 不记＝这个数永远是 false）");
ok(/return \{ out: out, think: think, fin: fin, errs: errs, doneMark: doneMark \};/.test(W),
  "_drain 把 doneMark 一并返回（不返回＝记了也拿不到）");

const finFrame = /controller\.enqueue\(_sseBytes\(\{ t: "fin", v: \{[\s\S]{0,240}?\}\s*\}\)\);/.exec(W);
ok(!!finFrame, "askCore 发出收笔读数帧 t:'fin'");
const fv = finFrame ? finFrame[0] : "";
ok(/out: _st\.out/.test(fv), "读数带正文字数");
ok(/think: _st\.think/.test(fv), "读数带思考字数");
ok(/fin: _fin\.fin/.test(fv), "读数带停因 finish_reason（length 还是 stop，是两种不同的病）");
ok(/done: !!_fin\.doneMark/.test(fv), "读数带 doneMark（没有它就分不出「基底停笔」与「流被掐」）");
ok(/sec: Math\.round\(/.test(fv), "读数带秒数（「死在第几秒」是唯一的时间证据）");

/* 只在真写出了正文时才发：零正文那一支自有它的兜底与诊断，不该在这里重复报账 */
ok(/if \(_fin && _fin\.out > 0\) controller\.enqueue\(_sseBytes\(\{ t: "fin"/.test(W),
  "收笔读数只在写出了正文时发（零正文走它自己那条兜底＋诊断）");

/* 位置：必须排在零正文兜底之后、清心跳与 [DONE] 之前 */
const iFallback = W.indexOf("// ===== 零正文兜底 =====");
const iFin = W.indexOf('t: "fin"');
const iBeatStop = W.indexOf("try { if (_hb) clearInterval(_hb); } catch (e) {}   // 外层心跳由 handleAsk 收");
ok(iFallback > 0 && iFin > iFallback, "收笔读数排在零正文兜底之后（兜底重跑写出来的字也要算进读数）");
ok(iBeatStop > 0 && iFin < iBeatStop, "收笔读数排在收心跳之前（收完心跳再发就赶不上这一帧）");

ok(/let _fin = r;/.test(W), "_fin 默认取首跑读数");
ok(/if \(up2\.ok\) \{ r2 = await _drain\(up2, controller, _st\); if \(r2\) _fin = r2; \}/.test(W),
  "兜底重跑真写出了字时，读数改以它为准（否则报的是那一遍失败的账）");

/* ===== 二、前端：段末标记闸 ===== */
console.log("— 二、前端 paperHalf：段末标记闸 —");

const a = H.indexOf("function paperHalf(");
const b = H.indexOf("function doPaper(");
const seg = a > 0 && b > a ? H.slice(a, b) : "";
ok(seg.length > 500, "抠得出 paperHalf 那一段源码 · 实得 " + seg.length + " 字符（太短＝注释里抢先出现了抠取锚点）");

/* ⚠ 2026-08-21 成文由四段改五段：断言只钉「认得到所有段的标记」这个判据，不钉段数字面。 */
ok(/var END_RE=\/〔\(\?:\(\?:上半篇完\|第\[一二三四五\]段完\)·待续\|规划完\|全文完\)〕/.test(seg),
  "END_RE 认全五种收尾标记（规划完／第N段完·待续／全文完／旧的上半篇完），且认得到末段");
ok(seg.indexOf("var END_RE=") > 0, "END_RE 写在 paperHalf 函数**里面**（写在外面，两台抠源码真跑的护栏当场 ReferenceError）");

const iEnded = seg.indexOf("var ended=END_RE.test(raw)");
const iStrip = seg.indexOf("raw.replace(END_RE,'')");
ok(iEnded > 0 && iStrip > iEnded,
  "先判标记在不在，再剥它——剥完就分不出「本来没有」和「已经剥掉」了");

ok(/if\(c\.length && !ended\)\{[\s\S]{0,400}?if\(attempt<2\)\{[\s\S]{0,300}?return paperHalf\(part, extra, minLen, label, attempt\+1\);/.test(seg),
  "断在半句 → 重试一次（与「写得太短」同一种处置）");
ok(/CUTLOG\.push\(label\+/.test(seg), "第二次仍断 → 照收，但记进 CUTLOG（半段稿仍是稿，只是不许冒充完稿）");
/* ⚠ 2026-08-21 新增了「只缺标记、正文完整 ⇒ 记账收下」那一支，它也 push CUTLOG 且不重试。
   原断言用「push 后 200 字内不许出现 attempt<2」来表达"记账只在末次"，新那一支落在重试分支之前，
   200 字窗口会扫到后面那个 attempt<2 ⇒ 误红。改成钉真正的判据：**重试那一支自己不许记账**。 */
ok(!/CUTLOG\.push\([\s\S]{0,120}\n\s*return paperHalf\(part, extra, minLen, label, attempt\+1\)/.test(seg),
  "记账只在不再重试的那几支（每重试一次记一笔＝同一段被数两遍）");

/* ===== 三、断段必须进收尾判定（这一条断了，整轮返工白做）===== */
console.log("— 三、收尾判定：断段不许冒充「✓ 已就绪」—");

ok((H.match(/var cut=CUTLOG\.length\?/g) || []).length === 2,
  "提炼与成文两处收尾都把断段算进判定 · 实得 " + (H.match(/var cut=CUTLOG\.length\?/g) || []).length + " 处");
ok(/stat\.textContent = \(miss \|\| cut\)/.test(H), "成文：缺段或断段，任一成立就不打「✓ 全文完成」");
ok(/stat\.textContent = \(miss \|\| cut\)\s*\n\s*\? cut\+/.test(H) || /\? cut\+\(miss/.test(H),
  "提炼：断段的说明排在最前（它比缺段更容易被忽略）");
/* ⚠ 2026-08-21：CUTLOG 现在装两类东西——真断稿，与「内容完整只缺标记」的那一类，
   后者不该再挂「连跑两次都没写到收尾标记」这句话。断言改成钉「读数仍随收尾一起报」。 */
ok(/CUTLOG\.join\('、'\)/.test(H) && /runWhy\(\)/.test(H) && /runWhy\(\)/.test(H.slice(H.indexOf("function runWhy"))),
  "断段提示仍与读数 runWhy 一起出现（否则又回到「猜」）");
ok(/function genTarget\([^)]*\)\{[^}]*CUTLOG=\[\];/.test(H),
  "每个任务开头清一次 CUTLOG（不清＝上一次的断段记到这一次头上）");

/* ===== 四、写到一半的字不许丢 ===== */
console.log("— 四、streamPaper：error 帧不再丢弃已写正文 —");

ok(/else if\(j\.t==='error'\)\{ RUNLOG\.err=j\.v\|\|''; if\(pacc\.length\)\{ resolve\(pacc\); return; \} reject\(/.test(H),
  "已经写出字的：带着错误照收；一个字都没有的：照旧 reject");
ok(/else if\(j\.t==='fin'\)\{/.test(H), "前端接住收笔读数帧 fin");
ok(/RUNLOG\.fin=_f\.fin\|\|''; RUNLOG\.done=!!_f\.done;/.test(H), "fin 与 done 都存进 RUNLOG");
ok(/if\(RUNLOG\.fin\) a\.push\('停因 '\+RUNLOG\.fin\)/.test(H), "runWhy 说得出停因");
ok(/if\(RUNLOG\.frames && !RUNLOG\.done\) a\.push\('上游没发 \[DONE\]/.test(H),
  "runWhy 分得出「被掐断」与「写完了」");
ok(/var RUNLOG=\{[^}]*fin:''[^}]*done:false\}/.test(H) && one(H, /function runReset\(\)/g),
  "RUNLOG 的两个新字段在声明与 runReset 里都在（只加一处＝第二次调用带着上一次的读数）");

/* ===== 五、入口资料不再按段截断（独立的旧债）===== */
console.log("— 五、入口资料整份送进成文 —");

ok(/brief\.slice\(0, 30000\)/.test(H),
  "成文四段拿到的是整份入口资料——第十栏〔分章大纲〕排在最末，按段截断正好把施工图切掉");
ok(!/brief\.slice\(0, i===0\?9000:5000\)/.test(H), "回归：按段截断那一行（含注释里的字面）已经不在");
ok(/const brief = String\(body\.brief \|\| ""\)\.trim\(\)\.slice\(0, 30000\);/.test(W),
  "服务端本来就收 30000（前端那一刀纯属自伤）");

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
