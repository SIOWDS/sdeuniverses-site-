#!/usr/bin/env node
/* 论文档「祖宗账」四道闸的护栏 —— 2026-08-22
 *
 * 缘起（这份护栏的基准样本是一份真稿）：
 *   ChatJohn 用两万字论文档产出《形式正确之后：语言教学中的「未落定问题」与听者转位》，
 *   21,955 字、十六节体例齐整、盲评 121.8（站内录取线 140）。
 *   查下来病灶不在提示语——十六节骨架把配额写得极细（八位占位者、三档年代各要有人、
 *   参考文献一位不漏）——**病灶在没有一处数得出来**：
 *     · 盘点表八行里只有六位具名，另几行是「传统语法教学」这类没有出处的统称；
 *     · 参考文献六条，最新一条 1990，近十年与十到三十年两档一位也没有；
 *     · 而它的承重命题正落在 1962–1997 那一片已经写满的地上；
 *     · 站上早有一篇讲同一现象、分数更高的文章（且就在这一档的语料白名单里），零提及——
 *       因为**成文这条路从头到尾没有取过一次料**。
 *
 * 所以这份护栏钉住四件事，一件都不许再退回去：
 *   ①【清点】ancPick / ancEras 能把「作者＋年份」数出来，且对那份真稿给出的正是当时的读数；
 *   ②【永远下发】ANCESTORS 块在清单为空时也必须下发（从前空清单＝整块不发，最该报警时最安静）；
 *   ③【取料】标了 rag 的四节两条路都取料，**按档案分流取料源**（语言档 johnRag 白名单／其余档主站 wdsRag），
 *       别的节不取，且白名单绝不许被别的档继承；
 *   ④【收稿闸】写完当场数，不足只发 note、绝不在服务端重写这一节。
 */
const fs = require("fs");
const path = require("path");
const WSRC = fs.readFileSync(path.join(__dirname, "..", "src", "worker.js"), "utf8");

let pass = 0, fail = 0;
function ok(name, cond) {
  if (cond) { pass++; console.log("  \u2713 " + name); }
  else { fail++; console.log("  \u2717 " + name); }
}
function eq(name, got, want) {
  ok(name + "（得 " + JSON.stringify(got) + "）", JSON.stringify(got) === JSON.stringify(want));
}

/* ═══ 一、把三个清点函数从 worker 里抠出来真跑 ═══ */
console.log("\u2500\u2500 清点函数 \u2500\u2500");
function grab(startMark, endMark) {
  const a = WSRC.indexOf(startMark);
  if (a < 0) return "";
  const b = WSRC.indexOf(endMark, a);
  return b < 0 ? "" : WSRC.slice(a, b);
}
const fnSrc = grab("const ANC_RE_PAREN", "/* \u300c\u4e0e John \u5bf9\u8bdd\u300d\u7684\u4eba\u683c\u4e0e\u5e95\u672c");
ok("抠得到 ancPick / ancEras / ancBlock 三个函数", /function ancPick/.test(fnSrc) && /function ancEras/.test(fnSrc) && /function ancBlock/.test(fnSrc));
const M = new Function(fnSrc + "\nreturn { ancPick, ancEras, ancBlock };")();

/* 基准样本：那份 121.8 真稿正文里出现过的全部引证形状，逐字照抄 */
const REALPAPER = "Chomsky\uff081965\uff09\u610f\u4e49\u4e0a\u7684\u53ef\u63a5\u53d7\u6027 \u2026 Hymes\uff081972\uff09\u63d0\u51fa\u300c\u4ea4\u9645\u80fd\u529b\u300d\u4e00\u8bcd \u2026 "
  + "Canale \u548c Swain\uff081980\uff09\u63d0\u51fa\u56db\u5206\u6846\u67b6 \u2026 Halliday\uff081978\uff09\u7684\u7406\u8bba \u2026 Halliday \u4e0e Hasan 1985 \u2026 Gee\uff081990\uff09\u63d0\u51fa\u300cDiscourses\u300d\u3002";

const pk = M.ancPick(REALPAPER);
eq("那份真稿点得到的具名位数", pk.n, 6);
ok("六位都点到了", ["chomsky", "hymes", "swain", "halliday", "hasan", "gee"].every((x) => pk.names.indexOf(x) >= 0));
ok("「Canale 和 Swain」这种共同署名只算得到带年份的那一位（宁漏不枉）", pk.names.indexOf("canale") < 0);

const er = M.ancEras(pk.years);
eq("那份真稿缺的正是这两档", er.gap, ["\u8fd1\u5341\u5e74", "\u5341\u5230\u4e09\u5341\u5e74"]);
ok("三十到五十年那一档它是有人的", er.e.old >= 3);

/* 不许把随便一个四位数当成年份 */
const noise = M.ancPick("\u5171 30 \u4ef6\u6750\u6599\uff0c\u7f16\u53f7 1234\uff1b\u4e00\u81f4\u7387 0.80\uff1b\u53d1\u8868\u4e8e 2026-08-22\uff1b\u7b2c 5 \u8282\u3002");
eq("纯数字与日期不算具名占位者", noise.n, 0);
const good = M.ancPick("Clark & Brennan 1991\uff1bSacks\uff081974\uff09\uff1bWiddowson\uff081978\uff09\uff1bLyster \u4e0e Ranta 1997\uff1bBell 1984\uff1bOchs 1979\uff1bAustin 1962\uff1bGoffman 1981");
ok("换成本该出现的那八位就能数到八位", good.n >= 8);
eq("换成那八位之后不再缺三十到五十年档", M.ancEras(good.years).gap.indexOf("\u4e09\u5341\u5230\u4e94\u5341\u5e74") < 0, true);

/* ═══ 二、ANCESTORS 块：空清单也必须下发 ═══ */
console.log("\u2500\u2500 ANCESTORS 块（永远下发）\u2500\u2500");
const b0 = M.ancBlock([]);
ok("清单为空时仍然下发（不是空串）", b0.length > 80);
ok("空清单会明说一位也没盘出来", /\u4e00\u4f4d\u4e5f\u6ca1\u76d8\u51fa\u6765/.test(b0));
ok("空清单会写明缺几位并要本节自己补", /\u7f3a 8 \u4f4d/.test(b0) && /\u5fc5\u987b\u81ea\u5df1\u8865\u9f50/.test(b0));
ok("空清单会点名三档年代全缺", /\u8fd1\u5341\u5e74/.test(b0) && /\u5341\u5230\u4e09\u5341\u5e74/.test(b0) && /\u4e09\u5341\u5230\u4e94\u5341\u5e74/.test(b0));
ok("统称不算一位这条写进了下发文字", /\u6ca1\u6709\u51fa\u5904\u7684\u7edf\u79f0\u4e00\u5f8b\u4e0d\u7b97\u4e00\u4f4d/.test(b0));
ok("补不到时的正当出路也写了（如实写检索边界）", /\u5982\u5b9e\u5199\u660e\u68c0\u7d22\u5230\u4ec0\u4e48\u8303\u56f4/.test(b0));
ok("绝不许编造那一条在（补位最容易诱发编造）", /\u7edd\u4e0d\u8bb8\u7f16\u9020\u4eba\u540d\u5e74\u4efd/.test(b0));

const b6 = M.ancBlock(["Chomsky 1965 \u2014\u2014 \u53ef\u63a5\u53d7\u6027", "Hymes 1972", "Swain 1980", "Halliday 1978", "Hasan 1985", "Gee 1990"]);
ok("六位时报「实到 6 位」", /\u5b9e\u5230 \\*\\*6 \u4f4d/.test(b6) || b6.indexOf("6 \u4f4d") > 0);
ok("六位时仍报缺 2 位", /\u7f3a 2 \u4f4d/.test(b6));
ok("六位时点名缺的两档", /\u8fd1\u5341\u5e74\u3001\u5341\u5230\u4e09\u5341\u5e74/.test(b6));

const b8 = M.ancBlock(["Austin 1962", "Sacks 1974", "Widdowson 1978", "Ochs 1979", "Bell 1984", "Clark 1991", "Lyster 1997", "Stivers 2009", "Enfield 2019"]);
ok("够八位且三档齐时不再喊缺", !/\u7f3a \\d+ \u4f4d/.test(b8) && !/\u8fd9\u4e00\u6863\u4e00\u4f4d\u4e5f\u6ca1\u6709/.test(b8));
ok("无论够不够，参考文献一位不漏那一条都在", /\u4e00\u4f4d\u4e0d\u6f0f\u5730\u5217\u8fdb\u6761\u76ee/.test(b8));

/* ═══ 三、下发点：判据必须落在常量上，不许是字面量 ═══ */
console.log("\u2500\u2500 part 那一趟怎么挂 \u2500\u2500");
ok("part 的 sys 用的是 ancBlock（不是原来那个三元条件）", /\+ ancBlock\(planIn\.ancestors/.test(WSRC));
ok("原来那句「清单为空就整块不发」已经不在了",
  WSRC.indexOf('(Array.isArray(planIn.ancestors) && planIn.ancestors.length') < 0);
ok("plan 那一趟会把实到位数记进 plan（ancN）", /plan\.ancN = _ancF\.n/.test(WSRC));
ok("盘不够会补问一次，且是关思考的窄调用", /ancPick\(plan\.ancestors\.join\(" ; "\)\)\.n < 8/.test(WSRC) && /llmText\(\{ url: VC\.url/.test(WSRC));
ok("补问只给 1800 tok / 25 秒（配菜额度，不许占正文预算）", /_asys, _ausr, 1800, 25000/.test(WSRC));
ok("补问失败不拖住整篇（整段 try/catch）",
  /if \(ancPick\(plan\.ancestors[\s\S]{0,3200}?\} catch \(e\) \{\}/.test(WSRC));
ok("补不到也如实报给读者（note 里写实到几位）", /\u5360\u4f4d\u76d8\u70b9\u53ea\u76d8\u5230 " \+ _ancF\.n \+ " \u4f4d\u5177\u540d/.test(WSRC));
ok("补问块留在合并块之外（合并块被别的护栏 new Function 求值，不能有 await）",
  WSRC.indexOf("\u76d8\u4e0d\u591f\u5c31\u8865\u95ee\u4e00\u6b21") < WSRC.indexOf("\n                if (FIXED) {"));

/* ═══ 四、站内同题取料 ═══ */
console.log("\u2500\u2500 站内同题取料 \u2500\u2500");
const SKEL = grab("const PAPER_SKELETON = [", "\n      /* ═══ 一万字研究论文版骨架");   // 只数十六节表：后面紧跟着研究论文档的兜底表，rag／chk 会被算进去
ok("抠得到骨架表", SKEL.length > 2000);
const ragged = (SKEL.match(/rag: 1/g) || []).length;
eq("正好四节标了要取料", ragged, 4);
["\u4e00\u3001\u5f15\u8a00", "\u4e8c\u3001\u6587\u732e\u8ff0\u8bc4", "\u4e94\u3001\u6700\u8fd1\u90bb\u76d8\u70b9", "\u53c2\u8003\u6587\u732e\u4e0e\u9644\u5f55"].forEach((h) => {
  const i = SKEL.indexOf(h);
  ok("「" + h + "」这一节标了 rag", i > 0 && SKEL.slice(i, i + 120).indexOf("rag: 1") > 0);
});
/* 2026-08-22：这道闸原来只对语言档开，于是**主站 ChatSDE 的两万字论文一趟也没取过站内料**。
   现在两条路都取，但取料源按档案分流——白名单被别的档继承＝检索范围张冠李戴。 */
const RAGBLK = (() => { const a = WSRC.indexOf("if (_fixSec && _fixSec.rag)"); return a < 0 ? "" : WSRC.slice(a, a + 1400); })();
ok("标了 rag 的节两条路都取料（不再只对语言档开）", /if \(_fixSec && _fixSec\.rag\) \{/.test(WSRC));
ok("语言档走 johnRag（白名单）", /prof && prof\.id === "lang"[\s\S]{0,200}johnRag\(env, url, _rq\)/.test(RAGBLK));
ok("其余档走主站 wdsRag（全站检索）", /\} else \{[\s\S]{0,300}wdsRag\(env, url, \{ q: _rq/.test(RAGBLK));
ok("语言白名单没有被别的档继承", RAGBLK.indexOf("johnRag") < RAGBLK.indexOf("} else {"));
ok("两条路的检索词是同一个（题名＋承重命题＋本节标题）", (RAGBLK.match(/_rq/g) || []).length >= 3);
ok("主站那一路按 /api/wds/rag 的口径拿 ctx", /_jr && _jr\.ok\) siteCtx = _jr\.ctx/.test(RAGBLK));
ok("两条路各自 try/catch，取料失败都退化成不取", (RAGBLK.match(/catch \(e\) \{ siteCtx = ""; \}/g) || []).length === 2);
ok("取料读的是服务端的 SPEC.fixed，不是客户端递上来的 secs",
  /_fixSec = \(Array\.isArray\(SPEC\.fixed\) && SPEC\.fixed\[partIdx\]\)/.test(WSRC));
ok("查询词是题名＋承重命题＋本节标题（不是对话尾巴）",
  /planIn\.title[\s\S]{0,120}planIn\.thesis[\s\S]{0,60}sec\.h/.test(RAGBLK));
ok("取料失败退化成不取，不抛错", /catch \(e\) \{ siteCtx = ""; \}/.test(WSRC));
ok("取到料就要求指名划界", /\u5fc5\u987b\u6307\u540d\u5212\u754c/.test(WSRC));
ok("站内自己人比外面的对手更该划界，这句在", /\u7ad9\u5185\u81ea\u5df1\u4eba\u6bd4\u5916\u9762\u7684\u5bf9\u624b\u66f4\u8be5\u5212\u754c/.test(WSRC));
ok("材料块仍守着「只有这几篇是真的」那条反编造纪律", /\u53ea\u6709\u8fd9\u51e0\u7bc7\u662f\u771f\u7684/.test(WSRC));
ok("站内材料挂在接缝之前（接缝必须是 sys 的最后一段）",
  WSRC.indexOf("siteCtx ? (\"\\n\\n\u3010\u7ad9\u5185\u5df2\u7ecf\u53d1\u8868\u8fc7\u7684\u540c\u9898\u7bc7\u76ee") < WSRC.indexOf("prevTail ? (\"\\n\\n\u3010\u4e0a\u4e00\u8282\u7684\u7ed3\u5c3e"));

/* ═══ 五、收稿闸 ═══ */
console.log("\u2500\u2500 收稿闸 \u2500\u2500");
const chks = (SKEL.match(/chk: \d/g) || []).length;
eq("三节挂了收稿闸（述评／盘点／参考文献）", chks, 3);
ok("盘点表那一节的门槛是八位", SKEL.slice(SKEL.indexOf("\u4e94\u3001\u6700\u8fd1\u90bb\u76d8\u70b9"), SKEL.indexOf("\u4e94\u3001\u6700\u8fd1\u90bb\u76d8\u70b9") + 120).indexOf("chk: 8") > 0);
ok("正文被累积下来才数得了（且封顶，不许无界增长）", /secTxt\.length < 60000/.test(WSRC));
ok("闸只发 note，不在服务端重写这一节", /_fixSec\.chk && wrote/.test(WSRC) && /t: "note"[\s\S]{0,300}\u53ea\u70b9\u5230 " \+ _pk\.n/.test(WSRC));
ok("note 里说清差多少、缺哪一档、以及建议退改", /\u4f53\u4f8b\u8981 " \+ _fixSec\.chk \+ " \u4f4d/.test(WSRC) && /\u5efa\u8bae\u5c31\u8fd9\u4e00\u8282\u9000\u6539/.test(WSRC));
ok("一个字都没写出来时不发这个 note（别在断稿上再骂一句）", /_fixSec\.chk && wrote\)/.test(WSRC));

/* ═══ 六、真跑一遍收稿闸的判定 ═══ */
console.log("\u2500\u2500 收稿闸真跑 \u2500\u2500");
[["那份 121.8 的盘点表", REALPAPER, 8, true],
 ["补齐到八位之后", "Austin\uff081962\uff09\uff1bSacks 1974\uff1bWiddowson 1978\uff1bOchs 1979\uff1bBell 1984\uff1bClark 1991\uff1bLyster 1997\uff1bStivers 2009", 8, false],
 ["述评节只点到三位", "Hymes\uff081972\uff09\uff1bHalliday 1978\uff1bGee\uff081990\uff09", 5, true],
].forEach(([name, txt, need, shouldFire]) => {
  const fired = M.ancPick(txt).n < need;
  ok(name + "：闸" + (shouldFire ? "该响" : "该不响"), fired === shouldFire);
});

/* ═══ 七、v3.0 祖宗闸的第二道：从「数得出来」到「数对了人」 ═══
   缘起第二份真稿：《论语言之美的发生》26,425 字，盲评 132.7（前一版同题 130.9，只涨 1.8）。
   v2.3 那四道闸结构上全部生效——文献从零到十二条、六条脉络各有判决性反例、三条自我否决条款——
   可补进来的十二位全是这个题目下**最容易想到的名字**，真正占着承重命题的四位一个没有：
   雅各布森的诗性功能、鲍曼的表演、鲍曼与布里格斯的再语境化、戈夫曼的参与框架。
   四位都不在「语言之美」这个词底下——**它们在别的行里，用别的名字，说的是同一件事**。
   ⇒ 本节钉住 A1 别名法与随之而来的六条纪律，规范层在 tools/skills/sde-academic-paper.md §3.8。 */
console.log("\u2500\u2500 v3.0 别名法与四条纪律 \u2500\u2500");
const SKILL = fs.readFileSync(path.join(__dirname, "skills", "sde-academic-paper.md"), "utf8");
const ANCB = (() => { const a = WSRC.indexOf("function ancBlock("); return a < 0 ? "" : WSRC.slice(a, WSRC.indexOf("\n}", a)); })();
const ASYS = (() => { const a = WSRC.indexOf("【只做一件事"); return a < 0 ? "" : WSRC.slice(a, a + 3000); })();

ok("ancBlock 收 aliases 这个入参", /function ancBlock\(list, aliases\)/.test(WSRC));
ok("调用点把 planIn.aliases 传进去了", WSRC.indexOf("ancBlock(planIn.ancestors, planIn.aliases)") > 0);
/* ⚠ 与「永远下发」同理：**没盘出叫法**才是最该报警的情况，那一支绝不许静默。 */
ok("有叫法时下发 ALIASES 块", ANCB.indexOf("ALIASES（这个现象在别的行里还叫这些名字") > 0);
ok("没盘出叫法时也下发（且改成让本节自己先补一步）", ANCB.indexOf("这一趟没盘出别的叫法") > 0);
ok("ALIASES 要求每个叫法底下都有人被点到名", /每一个叫法底下都得有人被点到名/.test(ANCB));
[["A2 承重命题逐条配祖宗", "每条至少两位"], ["A3 年代验实交", "近十年至少两条"],
 ["Q1 伪引文禁令", "加引号的伪引文比不引更伤"], ["Q2 列而不引禁令", "要么从表里删掉"]].forEach(([n, mark]) => {
  ok(n + " 随每一节下发", ANCB.indexOf(mark) > 0);
});
/* A1 的要害是**顺序**：叫法必须是补问那一趟的第一个必填字段，
   不是提示语末尾一句叮嘱（v2.3 那句「先想三个不同叫法」就是被当成叮嘱忽略掉的）。 */
ok("补问改成两步、只输出一个 JSON 对象", /只做一件事，分两步/.test(ASYS) && /aliases/.test(ASYS));
ok("aliases 排在 list 之前（先列名再列人）", ASYS.indexOf("第一步 aliases") > 0
  && ASYS.indexOf("第一步 aliases") < ASYS.indexOf("第二步 list"));
ok("每个叫法要对得上一个学科", /对得上一个具体的学科或传统/.test(ASYS));
ok("第二步要求按每个叫法各找一位", /按每一个叫法各去找至少一位/.test(ASYS));
ok("补问里加了「每条承重命题各要有人」", ASYS.indexOf("每一条承重命题上至少两位") > 0);
ok("旧那句「三个不同叫法」的叮嘱已被顶掉", WSRC.indexOf("三个不同叫法**各想一遍") < 0);
/* 形状兼容：模型偷懒直接给裸数组时不许整趟白跑。 */
ok("两种形状都收（对象与裸数组）", /Array\.isArray\(_aj0\) \? _aj0 :/.test(WSRC));
ok("盘出来的叫法也报一条 note", WSRC.indexOf("这个现象在别的行里还叫：") > 0);

/* Q1 的可数版真跑一遍 */
console.log("\u2500\u2500 Q1 引文闸真跑 \u2500\u2500");
const QA = (() => {
  const a = WSRC.indexOf("function quoteAudit(");
  return new Function(WSRC.slice(a, WSRC.indexOf("\n}", a) + 2) + "; return quoteAudit;")();
})();
eq("那句伪引文数得出来", QA("亚里士多德提出隐喻是「对偏离日常语言的一种令人愉快的手段」的早期表述").n, 1);
eq("两处引文数两处", QA("他说「甲乙丙丁戊己」，又说「庚辛壬癸子丑」").n, 2);
eq("短引号不算（术语标记不是引文）", QA("所谓「场合」不是「环境」的同义语").n, 0);
eq("没有引文时不响", QA("语域三变项共同选择语义结构。").n, 0);

/* 规范层自身 */
console.log("\u2500\u2500 规范层 v3.0 \u2500\u2500");
ok("Skill 有 §3.8 v3.0 那一章", SKILL.indexOf("### 3.8　v3.0") > 0);
["A1", "A2", "A3", "A4", "Q1", "Q2", "C1"].forEach((c) => {
  ok("Skill 里有 " + c + " 这一条", SKILL.indexOf("#### " + c + " ·") > 0);
  ok("出稿自检清单里有 " + c, new RegExp("\\*\\*" + c + "[ab]?\\*\\*").test(SKILL));
});
ok("Skill 记下了漏掉的那四位", ["雅各布森", "鲍曼", "布里格斯", "戈夫曼"].every((n) => SKILL.indexOf(n) > 0));
ok("Skill 头部写明 v3.0 管的是「找的是不是对的人」", SKILL.indexOf("找的是不是对的人") > 0);
ok("A4 把自我否决条款接到盘点表上", SKILL.indexOf("接到 I 维的盘点表上") > 0);

console.log("\n" + (fail ? "\u2717 " : "\u2713 ") + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
