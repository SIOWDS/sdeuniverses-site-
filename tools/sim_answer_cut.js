/* 只测一件事：**一轮答案没写完就断了，页面说不说得出来。**

   病史（2026-08-21 用户截图报的「第五轮就停止了」）：
   一轮深度问答的正文断在「它」字上——120 字，停在半句。而屏幕上**什么提示都没有**：
   没有 error 帧、没有掉线提示、没有秒数。流干净结束、字数够长（>60），
   于是照常入档、照常渲染、照常往下走，读者看到的只是一段断掉的答案和一片安静。

   根因是一处漏网：08-18 加过一帧 `fin`（正文几字·思考几字·**停因**·上游有没有发过 [DONE]），
   它是分辨「基底自己停笔」与「整条流被掐断」的唯一依据——
   但那一刀只给 streamPaper（提炼／成文）装了消费端，**doAsk 这条路把这一帧静默丢掉了**。
   服务端一直知道上游没发 [DONE]（doneMark=false），只是没人接。

   ⚠ 这一刀做的是**把证据接住并说出来**，不是治那个断——断在谁那儿，要读到那句话才知道。
   与 08-18 那次同一个口径。 */
"use strict";
const fs = require("fs");
const H = fs.readFileSync("/home/claude/site/public/search/index.html", "utf8");
const W = fs.readFileSync("/home/claude/site/src/worker.js", "utf8");

let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };

console.log("— 一、断句判据真跑 —");
const iA = H.indexOf("function looksCut(txt){");
const iB = H.indexOf("function finishAsk(");
const SRC = iA >= 0 && iB > iA ? H.slice(iA, iB) : "";
ok(!!SRC, "抠得出 looksCut");
const looksCut = new Function(SRC + "\nreturn looksCut;")();

/* 用户截图里那一段的结尾，逐字照抄 */
ok(looksCut("AI 没有先改“做”，因为“做”还在人手里；它也没有先改“被看见”，因为“看见”本来就要等返照。它") === true,
   "用户截图那段的结尾判为「断了」（停在「它」字上）");
ok(looksCut("……最后一句写完了。") === false, "句号收尾＝写完了");
ok(looksCut("那么，它到底是什么？") === false, "问号收尾＝写完了");
ok(looksCut("他说：“事情就是这样。”") === false, "右引号收尾＝写完了（引文收尾也算数）");
ok(looksCut("……写完了。\n\n  ") === false, "尾部空白不影响判定");
ok(looksCut("") === false && looksCut(null) === false, "空输入不算断（空是另一种病，由零产出那一支管）");
ok(looksCut("末句用了逗号，") === true, "逗号收尾＝断了");
ok(looksCut("停在一个只写了标题的空章上") === true, "没有任何收尾符号＝断了");

console.log("— 二、doAsk 接住 fin／beat 两帧（08-18 漏装的就是这里）—");
const iD = H.indexOf("function doAsk(");
const DBLK = iD >= 0 ? H.slice(iD, H.indexOf("function finishAsk(", iD)) : "";
ok(!!DBLK, "抠得出 doAsk");
ok(/else if\(j\.t==='fin'\)\{/.test(DBLK), "doAsk 接住了收笔读数帧（此前只有成文那条路接）");
ok(/finRead\.done=!!_fv\.done;/.test(DBLK), "接住 done（上游有没有发过 [DONE]——被掐断与写完的唯一分界线）");
ok(/finRead\.fin=_fv\.fin\|\|'';/.test(DBLK), "接住停因（length 还是 stop）");
ok(/else if\(j\.t==='beat'\)\{/.test(DBLK), "顺带接住心跳（否则「死在第几秒」这个时间证据一直没人看见）");
ok(/if\(!acc\.length\) thinkEl\.textContent='⏳ '/.test(DBLK),
   "心跳只在还没出正文时接管状态行——已经在写字了就别抢（字数本身就是心跳）");
ok(/_bump\(75000\); finRead\.frames\+\+;/.test(DBLK), "数帧数（一帧都没收到 vs 收了帧才断，是两种病）");
ok((DBLK.match(/finishAsk\(ansEl, gotErr, lastStat, finRead\)/g) || []).length >= 2,
   "两条收尾路径（流正常结束／我们自己掉线）都把读数传下去");

console.log("— 三、写出了字但没收完 ⇒ 必须说出来 —");
const iF = H.indexOf("function finishAsk(");
const FBLK = iF >= 0 ? H.slice(iF, H.indexOf("function qNorm(", iF)) : "";
ok(!!FBLK, "抠得出 finishAsk");
ok(/finRead=finRead\|\|\{fin:'',done:false/.test(FBLK), "读数缺省不炸（老调用点传不传都行）");
/* 两条判据任一成立即算没收完：上游没发 [DONE]（铁证），或末尾不是收尾符号。 */
ok(/looksCut\(lastAns\) \|\| \(finRead\.frames && !finRead\.done\)/.test(FBLK),
   "两条判据：上游没发 [DONE]（铁证）或末尾停在半句——任一成立就是没收完");
ok(/lastAns\.length>60 && !gotErr &&/.test(FBLK),
   "服务端已经报过一句人话时不再叠一句（不许拿猜测盖住真错误）");
ok(/上游没发 \[DONE\]（是被掐断的，不是写完的）/.test(FBLK), "说清是被掐断还是上游正常收笔");
ok(/流停在第 '\+finRead\.sec\+' 秒/.test(FBLK), "把秒数报出来（死在第几秒是唯一的时间证据）");
ok(/停因 '\+finRead\.fin\+/.test(FBLK), "把停因报出来");
ok(/把这一问原样再问一次即可/.test(FBLK), "给出路：断了的那一轮可以原样重问补一轮完整的");
/* ⚠ 这一条是变异检验补出来的：删掉那行 appendChild，判据算得再对也只是算给自己看——
   下面那条「先后顺序」断言在两个 indexOf 都是 -1 时照样为真，蒙混过关。 */
const iCut = FBLK.indexOf("ansEl.appendChild(_cut);");
ok(iCut > 0, "判出来的那句话真的贴进了答案框（只判不显示等于没做）");
/* 断了照样入档：已经写出来的字是真交付物，不许因为断了就丢掉。 */
ok(iCut > 0 && FBLK.indexOf("turns.push({q:lastQ, a:lastAns});") > iCut,
   "断稿照常入档（已写出的字是真交付物），提示只是提示，不是把它作废");

console.log("— 四、上游确实发得出这一帧（消费端的前提）—");
ok(/controller\.enqueue\(_sseBytes\(\{ t: "fin", v: \{/.test(W), "服务端仍在发收笔读数帧");
ok(/done: !!_fin\.doneMark/.test(W), "帧里带着 doneMark（前端那条铁证判据靠它）");

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
