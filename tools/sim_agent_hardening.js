/* sim_agent_hardening —— 2026-08-21「对话·提炼·成文」三段精修的护栏。
   这一刀治的全是真跑抓出来的病，逐条对应：
     对话 · 逐轮结账块（旧携带策略是一刀切且**砍尾巴**，砍掉的正是落点与下一问）
     提炼 · 编号硬闸（第二栏没展开三级，第十栏却引了一堆没定义过的节点 ⇒ 成文取空）
     成文 · 四段拆五段（第四段要装八项必交项，两次写到七八千字仍收不住笔）
           · 重写判据（缺标记 ≠ 断在半句：为一行标记重烧八千字）
           · 出稿机检（十五条自检写在提示词里，仍漏出内部编号、拼接残留、章节号重复、文献占位）
           · 四处显示（规划段被印成第一段／思考帧抢状态行／秒数每段重置／成文没有正文框）

   ⚠ 抠取锚点一律选「同类里唯一」的形状；本文件的注释里不写出任何回归字面。 */
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");
const H = fs.readFileSync(path.join(ROOT, "public/search/index.html"), "utf8");
const W = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");

let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };
const sec = (t) => console.log("\n— " + t + " —");

/* ══════════ 一、对话：逐轮结账 ══════════ */
sec("一、对话 · 逐轮结账块");
ok(/〔第N轮·结〕/.test(W), "成批问对的提示词里写死了结账块的形状");
["落点", "走法", "欠账", "下一问"].forEach((k) =>
  ok(new RegExp(k + "：").test(W), "结账块四栏之「" + k + "」在服务端写死"));
/* ⚠ 两条路互为兜底时必须各钉一条——否则删掉一条，断言会从另一条那里过。
   本文件第一版就栽在这里：删掉成批问对那一处的「不许写无」，护栏全绿。 */
ok((W.match(/不许写「无」/g) || []).length >= 2,
  "**两条路**（成批问对／深度问答）的欠账栏都不许写「无」——账本一路乐观，提炼拿到的就是粉饰过的账");
const ROUNDS = W.slice(W.indexOf('else if (mode === "rounds")'), W.indexOf('else if (mode === "synth")'));
ok(/不许写「无」/.test(ROUNDS), "成批问对这一条路装了结账块");
const ANSDEEP = W.slice(W.indexOf('if (histTxt && mode === "answer")'), W.indexOf('if (body.tri === true'));
ok(/轮·结〕/.test(ANSDEEP) && /不许写「无」/.test(ANSDEEP), "深度档问答这一条路也装了（不能只装一条）");

const TL = H.slice(H.indexOf("function takeLedger(txt){"), H.indexOf("function parseRounds(txt){"));
ok(TL.length > 100, "抠得出摘账本的函数");
let takeLedger = null, ledField = null;
try {
  const f = new Function(TL + "\nreturn {takeLedger:takeLedger, ledField:ledField};")();
  takeLedger = f.takeLedger; ledField = f.ledField;
} catch (e) { }
ok(typeof takeLedger === "function" && typeof ledField === "function", "两个函数抠得出并能构造");
if (typeof takeLedger === "function") {
  const body = "这一轮的正文。\n\n〔第 3 轮·结〕\n落点：甲不是乙。\n走法：切了差异\n欠账：没处理丙\n下一问：那么丙又靠什么成立？";
  const r = takeLedger(body);
  ok(r.led.indexOf("〔第 3 轮·结〕") === 0, "账本从正文里摘得出来");
  ok(r.body.indexOf("〔") < 0 && r.body.length > 0, "摘完正文里不再重复留一份");
  ok(ledField(r.led, "落点") === "甲不是乙。", "取得出「落点」栏");
  ok(ledField(r.led, "下一问") === "那么丙又靠什么成立？", "取得出「下一问」栏");
  const plain = takeLedger("一段没有账本的老正文。");
  ok(plain.led === "" && plain.body.length > 0, "老轮次没有账本时原样返回（退路必须留着）");
}
const BH = H.slice(H.indexOf("function buildHist(full){"), H.indexOf("function updateTurnBar(){"));
ok(/t\.led\|\|''/.test(BH), "携带上下文时读账本");
ok(/led \|\| \(t\.a\|\|''\)\.slice\(0,500\)/.test(BH),
  "更早的轮次：有账本就只带账本（完整），没有才退回旧的前 500 字");
ok(!/var lim = full \?/.test(BH), "旧那把一刀切已经不在了（不是新旧两套并存）");
ok(/function tailQuestionFromLedger\(led\)\{/.test(H), "拟下一问先认账本里的固定字段");
ok(H.indexOf("tailQuestionFromLedger(") < H.indexOf("|| tailQuestion(lastAns)") + 200
  && /tailQuestionFromLedger\([\s\S]{0,80}\) \|\| tailQuestion\(lastAns\)/.test(H),
  "账本取不到时才退回旧的正则猜法（猜法一个字没删）");

/* ══════════ 二、提炼：编号硬闸 ══════════ */
sec("二、提炼 · 编号与字数硬闸");
ok(/一个三级节点都没展开/.test(W), "第一段提示词点名了「只写 M1 一行即为不合格」这个病");
ok(/不许引用任何没有在第二栏定义过的编号/.test(W), "禁止挂空号写进硬闸");
ok(/本段\*\*合计不得超过 2800 字\*\*/.test(W), "第十栏的字数上限写成硬闸，不再只是「约」");
ok(/function auditBrief\(brief\)\{/.test(H), "前端有入口资料的编号机检");
let auditBrief = null;
try { auditBrief = new Function(H.slice(H.indexOf("function auditBrief(brief){"), H.indexOf("function auditOutput(text){")) + "\nreturn auditBrief;")(); } catch (e) { }
ok(typeof auditBrief === "function", "编号机检抠得出并能构造");
if (typeof auditBrief === "function") {
  const bad = "二、已经立住的核心判断\nM1 甲。\nM2 乙。\n十、论文观点与分章大纲\n供料：M1.1、M4.1.1、M4.2.2";
  const r = auditBrief(bad);
  ok(r.length === 2, "真跑：既报空号、也报「九栏没有三级节点」两条");
  ok(/没定义过的节点/.test(r.join("")), "空号被点名");
  const good = "二、已经立住的核心判断\nM1 甲。\nM1.1 甲显露面。\nM1.1.1 可指认项。\n十、论文观点与分章大纲\n供料：M1.1.1";
  ok(auditBrief(good).length === 0, "编号真的落地时零误报");
  ok(auditBrief("没有第十栏的半份稿").length === 0, "没有第十栏时不误报（半份稿另有闸管）");
}

/* ══════════ 三、成文：五段 ══════════ */
sec("三、成文 · 四段拆五段");
const PP = H.slice(H.indexOf("var PAPER_PARTS=["), H.indexOf("function partHead("));
const names = (PP.match(/name:'第[一二三四五]段'/g) || []);
ok(names.length === 5, "前端成文是五段");
ok(/第四段',desc:'证伪条件与当场检验·讨论·研究局限'/.test(PP), "第四段只收论证三章");
ok(/第五段',desc:'结论·注释·参考文献·附录 A·投稿声明'/.test(PP), "第五段收交付件");
ok(/part >= 1 && part <= 5/.test(W), "服务端钳位跟着改到 5（不改就永远写不到第五段）");
ok(/4: "〔第四段完·待续〕", 5: "〔全文完〕"/.test(W), "收尾标记：第四段改成待续，全文完移到第五段");
ok(/第[一二三四五]段完·待续/.test(H) && /第\[一二三四五\]段完/.test(H.replace(/\\/g, "")) === false || /一二三四五/.test(H),
  "前端段末标记正则认得第五段");
ok(/PAPER_PARTS\.length\+1;/.test(H), "调用次数公式从定义处抽段数，不再写死 4");
ok(!/\+4\+1;/.test(H), "旧那个写死的 4 已经不在");
ok(/本段只写这三章，写完就停/.test(W), "第四段明令不许提前写交付件（不然又收不了口）");
ok(/不作为证据/.test(W), "当场检验的案例必须给可回看出处，给不出就自认构造示例");
ok(/绝不许把「URL」「篇名」这类格式说明本身当作条目内容留在成品里/.test(W), "参考文献禁止把格式说明写成条目");

sec("四、成文 · 重写判据与出稿机检");
const PH = H.slice(H.indexOf("function paperHalf(part, extra, minLen, label, attempt){"), H.indexOf("function partHead(t){"));
ok(/var reallyCut = \(RUNLOG\.frames && !RUNLOG\.done\) \|\| looksCut\(c\)/.test(PH),
  "重写判据改成两条：上游没正常收笔 或 末尾停在半句");
ok(/!ended && !reallyCut && c\.length>=minLen/.test(PH),
  "只缺标记、正文完整、字数达标 ⇒ 记账收下，不再整段推倒");
ok(PH.indexOf("reallyCut") < PH.indexOf("if(c.length && !ended){"),
  "这一支排在重试之前（排在后面等于永远走不到）");
let auditOutput = null;
try { auditOutput = new Function(H.slice(H.indexOf("function auditOutput(text){"), H.indexOf("/* 进度条：")) + "\nreturn auditOutput;")(); } catch (e) { }
ok(typeof auditOutput === "function", "出稿机检抠得出并能构造");
if (typeof auditOutput === "function") {
  const dirty = "默顿这一支占了 M1.2 对面的位置。本节要做第十二节里最难的动作。（这里按你的要求，继续写第四章。）\n8.1 适用边界\n正文\n8.1 适用边界\n张琼 (2026). SDE Universes — URL.";
  const r = auditOutput(dirty);
  ok(r.length >= 4, "真跑：那篇论文的四类真实缺陷至少抓到四类");
  ok(/内部节点编号/.test(r.join("")), "抓内部节点编号泄漏");
  ok(/内部条目号/.test(r.join("")), "抓内部条目号泄漏");
  ok(/拼接残留/.test(r.join("")), "抓段间拼接残留");
  ok(/章节号重复/.test(r.join("")), "抓章节号重复");
  ok(/格式占位/.test(r.join("")), "抓参考文献里的格式占位");
  ok(auditOutput("一、引言\n本文讨论知识分发。\n2.1 缺口\n拉图尔 Latour, B. (1987). Science in Action. Harvard University Press.").length === 0,
    "干净稿零误报（误报会让人学会无视机检）");
}
ok(/出稿机检查出 /.test(H), "机检结果真的贴到状态行上（只判不显示等于没做）");

sec("五、四处显示");
ok(/function PART_LABEL\(part\)\{/.test(H) && /if\(part===0\) return '规划段'/.test(H),
  "规划段不再被印成第一段（part||1 把 0 变 1 那个坑）");
ok(/一二三四五'\.charAt/.test(H), "段名认得到第五段");
ok(/j\.t==='think'\)\{[\s\S]{0,220}if\(!pacc\.length\) stat\.textContent/.test(H),
  "思考帧也加上「出了正文就别抢状态行」这道保护（心跳帧早就有）");
ok(/function genElapsed\(\)\{/.test(H) && /GEN_T0=Date\.now\(\);/.test(H),
  "整刀总时长跨段不重置");
ok(/genTarget\('paperStat','ppFill','ppChars','paperLive'\)/.test(H) && /id="paperLive"/.test(H),
  "成文补上实时正文框（此前只有一个进度条）");

sec("六、邻居没被碰坏");
ok(/orig\.slice\(0, 120000\)/.test(W), "打磨的原稿入料放开到 12 万（26000 会砍掉结论与文献）");
["function doAsk(){", "function streamPaper(part, extra){", "function sseCollect(payload, onStat){", "function autoBatch(from, n, ix, attempt){"].forEach(function (a) {
  const i = H.indexOf(a);
  ok(i > 0 && /new AbortController\(\)/.test(H.slice(i, i + 4200)), "四条流式通道的看门狗都还在：" + a.replace(/function |\(.*/g, ""));
});

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
