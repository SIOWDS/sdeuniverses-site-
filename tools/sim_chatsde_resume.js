/* sim_chatsde_resume.js —— 续写：只补没写够的那几节
 * 两次真跑同一形状：稳定写完六节，第 7 节起撞墙。既然一口气十六节写不完，
 * 就把"接着写"做成按钮：扫描已有稿、只重跑缺的那几节、**插回原位**。
 * 顺带查：固定骨架档的提纲解不出 JSON 时不许让整篇失败（真跑读数：交回 2375 字，不是 JSON）。
 * 跑法：node tools/sim_chatsde_resume.js
 */
"use strict";
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, "..");
let pass = 0, fail = 0;
const ok = (n, c) => { if (c) { pass++; console.log("  ✓ " + n); } else { fail++; console.log("  ✗ " + n); } };
const F = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");
const W = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");

/* ═══ 一、扫描函数真跑 ═══ */
console.log("── 哪几节没写够（真跑）──");
const a = F.indexOf("    function headAt(txt, h) {");
const b = F.indexOf("    /* ══ 关掉这个面板", a);
const SRC = (a > 0 && b > a) ? F.slice(a, b) : "";
ok("抠得到 secBlocks / missingSecs", SRC.indexOf("missingSecs") > 0);
const M = new Function(SRC + "\n return { secBlocks: secBlocks, missingSecs: missingSecs, headAt: headAt, tailCut: tailCut, secPass: secPass, betterOf: betterOf };")();

const SECS = [{ h: "一、引言", words: 1000 }, { h: "二、述评", words: 1000 },
              { h: "三、判据", words: 1000 }, { h: "四、结论", words: 1000 }];
/* ⚠ 收尾那个句号不是装饰：这一版起「够长但断在半句」也算没写成，
   一个不收口的 fixture 会被新闸整片判缺，测的就不再是长度那件事了。 */
const full = (h, n) => "## " + h + "\n\n" + "字".repeat(n) + "。\n\n";
const cut = (h, n) => "## " + h + "\n\n" + "字".repeat(n) + "而它才被\n\n";
const draft = full("一、引言", 900) + full("二、述评", 900) + full("三、判据", 30) + full("四、结论", 20);

const miss = M.missingSecs(draft, SECS);
ok("认得出缺的是第 3、4 节", miss.length === 2 && miss[0].i === 2 && miss[1].i === 3);
ok("写够的两节不被误判", miss.every((x) => x.i >= 2));
ok("每一节都量得到起止（插回原位要用）", M.secBlocks(draft, SECS).every((x) => x.from >= 0 && x.to > x.from));
const full4 = full("一、引言", 900) + full("二、述评", 900) + full("三、判据", 900) + full("四、结论", 900);
ok("完整稿扫出来一节不缺", M.missingSecs(full4, SECS).length === 0);
const noHead = full("一、引言", 900) + full("二、述评", 900);
ok("整节连标题都没有 → 也算缺（from = -1）", M.missingSecs(noHead, SECS).length === 2);
/* 小标题被基底改过字：退一步只认标题本身 */
const renamed = "## 一、引言（修订）\n\n" + "字".repeat(900) + "。\n\n" + full("二、述评", 900) + full("三、判据", 900) + full("四、结论", 900);
ok("小标题被改过字仍认得出（退一步只认标题本身）", M.missingSecs(renamed, SECS).length === 0);
const thr = SRC.match(/Math\.max\(260, Math\.round\(w \* ([\d.]+)\)\)/);
ok("门槛与正文那一处同源（本节目标 × 比例，比例从源码取）", !!thr && +thr[1] > 0 && +thr[1] < 1);

/* ═══ 二、续写钮的源码级要求 ═══ */
console.log("── 续写钮 ──");
const btn = F.slice(F.indexOf('var goOn = el("button", "wdsm-tbtn dgoon"'), F.indexOf('var pdfB = el("button"'));
ok("抠得到续写钮", btn.length > 600);
ok("默认不亮（没缺节时不摆没用的按钮）", /goOn\.style\.display = "none";/.test(btn));
ok("★ 补出来的内容插回原位，不是追加在末尾", /blk\.from >= 0\) \{ head = text\.slice\(0, blk\.from\); tail = text\.slice\(blk\.to\); \}/.test(btn) && /text = head \+/.test(btn));
ok("只跑缺的那几节，不重跑全篇", /missingSecs\(text, secs\)/.test(btn) && /miss\[k\]/.test(btn));
ok("补完后再扫一遍，全齐了就把钮收起来", /if \(!missingSecs\(text, secs\)\.length\) goOn\.style\.display = "none";/.test(btn));
ok("仍没写够的按节号报出来", /stillShort\.push\(i \+ 1\)/.test(btn) && /mGoOnEnd3/.test(btn));
ok("补的过程也存进度（中途关掉不白干）", /saveProgress\(/.test(btn));
ok("节间留白与正文那一处同量级（别一口气连打）", /setTimeout\(nextOne, \d{3,4}\)/.test(btn));
ok("没有分节表时明说，不静默失败", /mGoOnNo/.test(btn));
ok("收尾处会把续写钮亮出来", /goOnBtn\.style\.display = ""/.test(F));
ok("续写要用的 plan 在面板作用域留住了", /var dPlanObj = null;/.test(F) && /dPlanObj = plan;/.test(F));

/* ═══ 二之二、这一轮补的闸（2026-08-12 稳健性复查）═══════════════════ */
console.log("── 尾部完整性判据（真跑）──");
/* ⚠ 断稿的判据是「**长散文行**停在字上」——短行、列表、标题、标签行都不算，
   因为有几种收尾本来就不带句号（真跑：第 1 节按体例必须以 `Keywords: …` 收尾）。 */
const PROSE = "这一处的分离线落在两边的判断之间而不是侧重不同上，因此它是可裁决的";
ok("长散文行末字是汉字 ⇒ 判为断在半句", M.tailCut(PROSE + "而它才被"));
ok("停在逗号上 ⇒ 断在半句", M.tailCut("其一，其二，"));
ok("停在顿号/冒号上 ⇒ 断在半句", M.tailCut("包括：") && M.tailCut("甲、"));
ok("句号收口 ⇒ 不算断", !M.tailCut("这一节到此为止。"));
ok("问号叹号省略号收口 ⇒ 不算断", !M.tailCut("是这样吗？") && !M.tailCut("就是它！") && !M.tailCut("大约如此……"));
ok("英文句点收口 ⇒ 不算断", !M.tailCut("That is the point."));
ok("右括号/引号收口 ⇒ 不算断", !M.tailCut("（见前文）") && !M.tailCut("他说「不是」"));
ok("行尾空白与 markdown 装饰不影响判读", !M.tailCut("收口了。**  \n\n") && M.tailCut(PROSE + "没收口 *"));

console.log("── 本来就不带句号的收尾：不许误判 ──");
ok("★ 关键词行（第 1 节按体例必须这么收尾）不算断",
  !M.tailCut(PROSE + "。\n\n**Keywords:** genesis; freezing; indexicality"));
/* ⚠ 体例表写死的是**方括号**形式 `【关键词】…` / `【Keywords】…`，它不带冒号——
   而我第一版的豁免只认「关键词：」这种带冒号的，于是每一篇的第 1 节都被误判成断稿
   （真跑里连着两份稿子都点了第 1 节）。
   💡 **补豁免要照着体例表抄它规定的那个形状，别照着自己脑子里的形状抄。** */
ok("★★ 中文方括号关键词行不算断（体例规定的就是这个形状）",
  !M.tailCut(PROSE + "。\n\n【关键词】发生学；冻结；索引性"));
ok("★★ 英文方括号关键词行同样不算断",
  !M.tailCut(PROSE + "。\n\n【Keywords】discovery paradigm; genesis-logy; cryonic state"));
ok("方括号里太长的就不当标签了（那多半是正文，不是一行标签）",
  M.tailCut(PROSE + "。\n\n【" + "字".repeat(30) + "】这一段还没写完就断在这里了呀真的断了"));
ok("★ 列表项收尾不算断", !M.tailCut(PROSE + "。\n\n- 甲：某某\n- 乙：某某"));
ok("★ 标题行收尾不算断", !M.tailCut(PROSE + "。\n\n### 3.4 小结"));
ok("★ 短行收尾不算断（多半是收束词，不是断稿）", !M.tailCut(PROSE + "。\n\n以上"));
ok("但停在半句标点上，短行也算断（那是铁证）", M.tailCut(PROSE + "。\n\n其一，"));
ok("空串归长度闸管，这里不重复判", !M.tailCut("") && !M.tailCut("   \n"));

console.log("── 够长但断在半句：也算缺节 ──");
const cutDraft = full("一、引言", 900) + full("二、述评", 900) + cut("三、判据", 900) + full("四、结论", 900);
const miss2 = M.missingSecs(cutDraft, SECS);
ok("★ 长度够却断在半句的那一节被认出来了", miss2.length === 1 && miss2[0].i === 2);
ok("认出来的原因标成 cut（不是 short）", miss2[0].why === "cut");
ok("写够又收了口的四节不被误判", M.missingSecs(full("一、引言", 900) + full("二、述评", 900) + full("三、判据", 900) + full("四、结论", 900), SECS).length === 0);

console.log("── 两遍取好的那一遍（真跑）──");
const NEED = 400;
ok("★ 第二遍是空的 ⇒ 留着第一遍", M.betterOf("甲".repeat(300), "", NEED).length === 300);
ok("★ 第二遍更短 ⇒ 留着第一遍", M.betterOf("甲".repeat(300), "乙".repeat(50), NEED).length === 300);
ok("两遍都不够 ⇒ 取长的那一遍", M.betterOf("甲".repeat(100), "乙".repeat(200), NEED).charAt(0) === "乙");
ok("★ 够长且收了口的胜过更长但断在半句的", M.betterOf("甲".repeat(500) + "。", "乙".repeat(900), NEED).indexOf("甲") === 0);
ok("都过闸时取长的", M.betterOf("甲".repeat(500) + "。", "乙".repeat(900) + "。", NEED).indexOf("乙") === 0);
ok("secPass 两道闸都要过", M.secPass("甲".repeat(500) + "。", NEED) && !M.secPass("甲".repeat(500), NEED) && !M.secPass("甲。", NEED));

console.log("── 切块锚点：标题只认行首 ──");
const trap = "## 一、引言\n\n" + "字".repeat(400) + "本文的四、结论并不在这里，只是提了一句。" + "字".repeat(400)
  + "\n\n## 四、结论\n\n" + "尾".repeat(600) + "。\n\n";
const bl = M.secBlocks(trap, [{ h: "一、引言", words: 1000 }, { h: "四、结论", words: 1000 }]);
ok("★ 正文里提到的同名串不会被当成标题（否则续写会切掉好文字）", bl[1].from === trap.indexOf("\n## 四、结论") + 1);
ok("找不到的节老实返回 -1", M.secBlocks("空稿", [{ h: "九、没有这一节", words: 900 }])[0].from === -1);
ok("稿子第一行就是标题时也认得出", M.secBlocks("## 一、引言\n\n字", [{ h: "一、引言", words: 900 }])[0].from === 0);

console.log("── 续写用的是同一套闸 ──");
ok("★ 续写也重试一次（不是打一趟就收下）", /return once\(\)\.then/.test(btn) && /once\(\)\.then\(function \(a2\)/.test(btn));
ok("★ 重试前退避（与主循环同量级）", /setTimeout\(r, 20000\)/.test(btn));
ok("★ 只在补出来的更好时才换上去", /betterOf\(old/.test(btn));
ok("★ 连着两节全败就停，不在墙上白打", /gFail >= 2\) gWall = true/.test(btn) && /gWall \|\|/.test(btn));
ok("★ 链上出岔子有兜底（按钮不会永远卡在 disabled）", /\.catch\(function \(e\)/.test(btn) && /goOn\.disabled = false;/.test(btn));
ok("★ 整节缺失时插到后面第一个找得到的节前面（不是全稿末尾）", /for \(q = i \+ 1; q < blocks\.length; q\+\+\)/.test(btn) && /blocks\[q\]\.from >= 0/.test(btn));
ok("死代码 _sink 已经拿掉", btn.indexOf("_sink") < 0);

/* ═══ 三、骨架档的提纲不许让整篇失败 ═══ */
console.log("── 提纲解不出 JSON 时 ──");
const syn = W.slice(W.indexOf("if (!plan && FIXED) {"), W.indexOf("if (!plan && FIXED) {") + 900);
ok("骨架档有合成分支", syn.length > 200);
ok("只对固定骨架档合成（自由分节档没有表可依，仍该失败）", /if \(!plan && FIXED\) \{/.test(W));
ok("题名从基底那一趟的原文里捞", /String\(raw \|\| ""\)/.test(syn) && syn.indexOf(".split(") > 0 && syn.indexOf("filter(") > 0);
ok("捞不到题名就退回档名，不留空", /_t \|\| SPEC\.name/.test(syn));
ok("sections 交空数组，由骨架合并那一步补齐十六节", /sections: \[\]/.test(syn));
ok("如实告诉读者提纲没解析出来、已按体例直接开写", /不是 JSON/.test(syn) && /已按体例直接开写/.test(syn));
ok("原来那条 noplan 失败路径仍保留（自由分节档要用）", /code: "noplan"/.test(W));

console.log("\n" + (fail ? "✗ " : "✓ ") + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
