/* sim_creative_writing.js —— 三体裁写作规范（公众号／散文／小说）的护栏
 *
 *   规范层：tools/skills/sde-creative-writing.md      ← 唯一权威
 *   机器层 A：src/worker.js 成文机 wechat/prose/story 三档 SPEC
 *   机器层 B：src/worker.js 的 JOHN_COMPOSE / JOHN_COMPOSE_SPEC（ChatJohn 概括成文）
 *   机器层 C：public/sites/lang/chatjohn/lite/index.html 的 KINDS（趟数必须与 B 一致）
 *
 * 本护栏只做一件事：**不许有两份口径**。
 * 站内每一次「改完源码模拟照样全绿、病却已上线」，根子都在同一件事有两处各写一份。
 *
 *   node tools/sim_creative_writing.js
 */
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, "..");
const SKILL = fs.readFileSync(path.join(ROOT, "tools/skills/sde-creative-writing.md"), "utf8");
/* 2026-08-23：散文档规范全文移出到分册。总纲第四节只留指路，硬律正文在分册里，
   所以 P-x 的存在性判定必须在 SKILL+PROSE 两份里找，只找 SKILL 会假红。 */
const PROSE = fs.readFileSync(path.join(ROOT, "tools/skills/sde-prose-writing.md"), "utf8");
/* 2026-08-23：小说档同样移出到分册，并扩为短篇／中篇／长篇三类。 */
const STORY = fs.readFileSync(path.join(ROOT, "tools/skills/sde-story-writing.md"), "utf8");
/* 2026-08-23：诗歌此前只有成文机里六条规格、无规范层。**诗写坏了不表现为难读，表现为「读起来很像诗」**，
   所以它的每一条都必须配一个三十秒内做得完的机械判据——这也是本护栏能钉住它的前提。
   ⚠ 诗歌不在总纲的三体裁之内（总纲没有它的章节），所以它的硬律只在分册与机器层两处对账。 */
const POEM = fs.readFileSync(path.join(ROOT, "tools/skills/sde-poem-writing.md"), "utf8");
/* 2026-08-23：公众号也移出分册。至此四档创作体各有分册，总纲只剩分工＋X 律＋四页指路。 */
const WECHAT = fs.readFileSync(path.join(ROOT, "tools/skills/sde-wechat-writing.md"), "utf8");
const SKILL_ALL = SKILL + "\n" + PROSE + "\n" + STORY + "\n" + POEM + "\n" + WECHAT;
const W = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");
const LITE = fs.readFileSync(path.join(ROOT, "public/sites/lang/chatjohn/lite/index.html"), "utf8");

let pass = 0, fail = 0;
const ok = (c, m) => { if (c) { pass++; } else { fail++; console.log("  ✗ " + m); } };
const sec = (t) => console.log("\n【" + t + "】");

/* ── 取 worker.js 里某一档 SPEC 的整块文本（从 `key: { name:` 到下一个 `key: { name:`）── */
/* 【共用常量要展开再查】2026-08-23：S-1…S-12 从 story 的 SPEC 里抽成模块级 STORY_CORE
   （短篇与中篇共用一份，不许有两份口径）。于是「SPEC 里有没有 S-7」不能再按字面查——
   查得到的只是 `+ STORY_CORE` 这四个字。⇒ 先把常量的**真值**取出来替换进去再查。
   ⚠ 取真值而不是取源码：这一次重构里 `const STORY_CORE = ""` 后面少了那些 `+`，
      **node --check 照样通过**（ASI 把它断成了一个空串加一串没人要的表达式语句），
      常量真值是空的而语法零报错。按真值判，才判得出这一种。 */
const STORY_CORE = (function () {
  const i = W.indexOf('const STORY_CORE = ""');
  if (i < 0) return "";
  const j = W.indexOf(";\n\n", i);
  if (j < 0) return "";
  try { return eval("(" + W.slice(i + 'const STORY_CORE ='.length, j) + ")"); } catch (e) { return ""; }
})();

function specBlock(key) {
  /* ⚠ 2026-08-23：这条原来把 `name: "…", tok: N, spec:` 整串抄进正则，
     于是三档创作体一加 noHead/parts/fixed（拆趟表插在 tok 与 spec 之间）就全找不到 SPEC，
     而它要守的用意（这一档的 SPEC 在不在、里面有没有那几条硬律）一点没变。
     按用意重写：只认「档名 + name + tok」，spec 在后面哪一行由下面自己找。 */
  const re = new RegExp("\\n        " + key + ": \\{ name: \"([^\"]+)\", tok: (\\d+)[,\\s]");
  const m = W.match(re);
  if (!m) return null;
  const start = m.index;
  const rest = W.slice(start + 10);
  const nxt = rest.search(/\n        [a-z0-9]+: \{ name: "/);
  const raw = rest.slice(0, nxt > 0 ? nxt : 9000);
  return { name: m[1], tok: +m[2], body: raw.split("STORY_CORE").join(STORY_CORE) };
}

/* ══ ① 规范层附录 A：三档编译表 ⇄ 成文机 SPEC ══════════════════════ */
sec("① 附录 A 编译表 ⇄ 成文机 SPEC");
const rowRe = /\|\s*`(wechat|prose|story)`\s*\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([WPS])\s*\|/g;
const rows = [];
let r;
while ((r = rowRe.exec(SKILL))) rows.push({ key: r[1], name: r[2], words: +r[3], tok: +r[4], form: r[5], pre: r[6] });
ok(rows.length === 3, "附录 A 应解析出 3 行，实得 " + rows.length);
rows.forEach((row) => {
  const b = specBlock(row.key);
  ok(!!b, row.key + " 在 worker.js 里找不到 SPEC");
  if (!b) return;
  ok(b.name === row.name, row.key + " 档名不一致：Skill「" + row.name + "」 vs 代码「" + b.name + "」");
  ok(b.tok === row.tok, row.key + " tok 不一致：Skill " + row.tok + " vs 代码 " + b.tok);
  ok(b.body.indexOf(String(row.words)) >= 0, row.key + " SPEC 正文里没有出现目标字数 " + row.words);
});

/* ══ ② 硬律编号：Skill 里定义了几条，SPEC 里就必须条条在 ══════════════ */
sec("② 硬律编号逐条落地");
const LAWS = {
  wechat: ["W-1", "W-2", "W-3", "W-4", "W-5", "W-6", "W-7", "W-8", "W-9", "W-10", "W-11", "W-12"],
  prose: ["P-1", "P-2", "P-3", "P-4", "P-5", "P-6", "P-7", "P-8", "P-9", "P-10", "P-11", "P-12"],
  story: ["S-1", "S-2", "S-3", "S-4", "S-5", "S-6", "S-7", "S-8", "S-9", "S-10", "S-11", "S-12"],
};
Object.keys(LAWS).forEach((k) => {
  LAWS[k].forEach((code) => {
    ok(SKILL_ALL.indexOf("硬律 " + code) >= 0 || SKILL_ALL.indexOf("（" + code + "）") >= 0,
      "Skill 里找不到硬律 " + code);
    const b = specBlock(k);
    ok(b && b.body.indexOf(code) >= 0, k + " 的 SPEC 里没有 " + code);
  });
});

/* ══ ②b ChatJohn essay 档：散文硬律同样逐条落地（2026-08-23 前它只到 P-6）══ */
sec("②b ChatJohn essay 的散文硬律");
const jEssay = W.slice(W.indexOf("\n  essay:\n"), W.indexOf("\n  wechat:\n", W.indexOf("\n  essay:\n")));
ok(jEssay.length > 200, "JOHN_COMPOSE_SPEC.essay 取不到");
LAWS.prose.forEach((code) => {
  ok(jEssay.indexOf(code) >= 0, "ChatJohn essay SPEC 里没有 " + code);
});
const jWechat = W.slice(W.indexOf("\n  wechat:\n"), W.indexOf("\n  story:\n"));
ok(jWechat.length > 200, "JOHN_COMPOSE_SPEC.wechat 取不到");
LAWS.wechat.forEach((code) => {
  ok(jWechat.indexOf(code) >= 0, "ChatJohn wechat SPEC 里没有 " + code);
});
const jStory = W.slice(W.indexOf("\n  story:\n"), W.indexOf("\n};", W.indexOf("\n  story:\n")));
ok(jStory.length > 200, "JOHN_COMPOSE_SPEC.story 取不到");
LAWS.story.forEach((code) => {
  ok(jStory.indexOf(code) >= 0, "ChatJohn story SPEC 里没有 " + code);
});

/* ══ ③ 共用硬律 X1–X7：只许有一份，三档都要挂 ══════════════════════ */
sec("③ 共用硬律 CW_X");
const cwIdx = W.indexOf("const CW_X =");
ok(cwIdx > 0, "worker.js 里没有 CW_X");
const cwBody = cwIdx > 0 ? W.slice(cwIdx, cwIdx + 2600) : "";
["X1", "X2", "X3", "X4", "X5", "X6", "X7", "X8", "X9", "X10", "X11"].forEach((x) => {
  ok(SKILL.indexOf("### " + x + " ·") >= 0, "Skill 第六节缺 " + x);
  ok(cwBody.indexOf("· " + x + " ") >= 0, "CW_X 里缺 " + x);
});
["wechat", "prose", "story"].forEach((k) => {
  const b = specBlock(k);
  ok(b && b.body.indexOf("CW_X") >= 0, k + " 的 SPEC 没有拼上 CW_X（共用硬律对它是废的）");
});
/* CW_X 必须定义在 writerBlock 之后、任何使用处之前——它是模块顶层 const，
   若被写进 JOHN_COMPOSE_SPEC 那张顶部的表里就是 TDZ ReferenceError（node --check 查不出）。 */
const jcsIdx = W.indexOf("const JOHN_COMPOSE_SPEC");
ok(jcsIdx > 0 && jcsIdx < cwIdx, "JOHN_COMPOSE_SPEC 应在 CW_X 之前（否则这条断言的前提变了）");
ok(W.slice(jcsIdx, W.indexOf("function johnComposeSys")).indexOf("CW_X") < 0,
  "⚠ JOHN_COMPOSE_SPEC 那张表里引用了 CW_X ＝ TDZ，整条成文路会 ReferenceError");
ok(W.slice(W.indexOf("function johnComposeSys")).indexOf("CW_X") > 0,
  "johnComposeSys 里没有挂 CW_X");

/* ══ ④ 附录 A 第二张表：JOHN_COMPOSE 趟数 × 每趟 ══════════════════ */
sec("④ ChatJohn 概括成文的趟数与字数");
const jcRe = /\|\s*`(wechat|essay|story)`\s*\|\s*([^|]+?)\s*\|\s*(\d+)\s*×\s*([\d/\s]+?)\s*\|/g;
const jcRows = [];
while ((r = jcRe.exec(SKILL))) {
  const cell = r[4].trim();
  const multi = cell.indexOf("/") >= 0 ? cell.split("/").map((x) => +x.trim()) : null;
  jcRows.push({ key: r[1], label: r[2], parts: +r[3], per: multi ? multi[0] : +cell, pers: multi });
}
ok(jcRows.length === 3, "附录 A 第二张表应解析出 3 行，实得 " + jcRows.length);
jcRows.forEach((row) => {
  /* ⚠ 2026-08-23：essay 加了 pers（各趟不等长）插在 per 与 label 之间，
     原来那条把 `per: N, label:` 抄死的正则当场找不到 essay。按用意重写：只认 parts 与 per，
     label 另找。 */
  const m = W.match(new RegExp(row.key + ":\\s*\\{ parts: (\\d+), per: (\\d+)[,\\s]"));
  const lb = W.match(new RegExp(row.key + ":\\s*\\{ parts: \\d+,[^}]*label: \"([^\"]+)\""));
  ok(!!m, "JOHN_COMPOSE 里没有 " + row.key);
  if (!m) return;
  ok(+m[1] === row.parts, row.key + " 趟数不一致：Skill " + row.parts + " vs 代码 " + m[1]);
  if (row.pers) {
    const pm = W.match(new RegExp(row.key + ":\\s*\\{ parts: \\d+, per: \\d+, pers: \\[([^\\]]+)\\]"));
    ok(!!pm, row.key + " 的 pers（各趟不等长）在代码里找不到");
    if (pm) ok(pm[1].replace(/\s/g, "") === row.pers.join(","),
      row.key + " 各趟字数不一致：Skill " + row.pers.join("/") + " vs 代码 " + pm[1]);
  } else {
    ok(+m[2] === row.per, row.key + " 每趟字数不一致：Skill " + row.per + " vs 代码 " + m[2]);
  }
  ok(!!lb && lb[1] === row.label, row.key + " 档名不一致：" + row.label + " vs " + (lb ? lb[1] : "取不到"));
});

/* ══ ⑤ 两处趟数口径：JOHN_COMPOSE ⇄ lite 页 KINDS ═══════════════════
   这一条是本护栏的头号职责。两处不一致的表现不是报错，是**缺段或空转**。 */
sec("⑤ 服务端趟数 ⇄ 前端 KINDS（缺一段不会报错，只会少写一截）");
const kindsBlk = LITE.slice(LITE.indexOf("var KINDS={"), LITE.indexOf("function compose("));
["paper", "essay", "wechat", "story"].forEach((k) => {
  const fe = kindsBlk.match(new RegExp(k + ":\\{n:(\\d+)"));
  const be = W.match(new RegExp(k + ":\\s*\\{ parts: (\\d+),"));
  ok(!!fe, "lite 页 KINDS 里没有 " + k);
  ok(!!be, "JOHN_COMPOSE 里没有 " + k);
  if (fe && be) ok(fe[1] === be[1], k + " 趟数两处不一致：前端 " + fe[1] + " vs 后端 " + be[1]);
  ok(LITE.indexOf('data-kind="' + k + '"') > 0, k + " 在 lite 页上没有按钮（后端认得、读者点不到）");
});

/* ══ ⑥ 字数下限闸（X2）真的下发了 ══════════════════════════════════ */
sec("⑥ X2 字数闸");
const jcsFn = W.slice(W.indexOf("function johnComposeSys"), W.indexOf("const JOHN_SCOPE"));
ok(/per \* 0\.9/.test(jcsFn), "johnComposeSys 里没有按 90% 算下限（目标 90 分之后由八成提到九成）");
ok(jcsFn.indexOf("不许收尾") >= 0, "非末趟没有写「不许收尾」（实测欠字就出在提前收尾）");
ok(jcsFn.indexOf('kind !== "paper"') >= 0, "共用硬律应只挂三体裁，论文档有自己的体例");
["wechat", "prose", "story"].forEach((k) => {
  const b = specBlock(k);
  ok(b && /九成|字数到/.test(b.body), k + " SPEC 里没有字数闸的说法");
});

/* ══ ⑦ 三条实测病灶必须写进规格（不是写进注释）══════════════════════ */
sec("⑦ 实测病灶落进规格");
const wb = specBlock("wechat"), pb = specBlock("prose"), sb = specBlock("story");
ok(wb && wb.body.indexOf("同向") >= 0, "公众号档没写例证同向律（真跑第一号病）");
ok(wb && /最多两位/.test(wb.body), "公众号档没写具名上限");
/* 2026-08-23 新增五条：三条来自传播现实（首屏／标题／截图），一条来自伦理（W-10），一条是四档对齐的「推」（W-12）。 */
ok(wb && /150 字/.test(wb.body), "公众号档没写 W-8 首屏 150 字那条判据");
ok(wb && wb.body.indexOf("改标题，不是改正文") >= 0, "公众号档没写 W-9 遮标题自拟法的收口");
ok(wb && wb.body.indexOf("封顶 70") >= 0, "公众号档没写 W-10 违反即封顶 70（全站唯一比 85 更狠的一条）");
ok(wb && wb.body.indexOf("不存在的敌人") >= 0, "公众号档没写 W-10 的第一条判据（换成具体的人还站不站得住）");
ok(wb && wb.body.indexOf("被截图转发") >= 0, "公众号档没写 W-11 可截图律");
ok(wb && wb.body.indexOf("名字是工具，金句是结论") >= 0, "公众号档没写 W-12 与金句的分界");
ok(wb && wb.body.indexOf("伦理层") >= 0, "公众号档的自检清单没有伦理层那四问（只有这一档有）");
ok(pb && pb.body.indexOf("15%") >= 0, "散文档没写议论占比上限（真跑第二号病）");
ok(pb && /视点|三问/.test(pb.body), "散文档没写视点守恒");
ok(pb && pb.body.indexOf("取消提问资格") >= 0, "散文档没写 P-6");
/* 2026-08-23 第三份真跑（《滤网沉泥》7172 字 · 盲评 110）的三处交付层失分，逐条点名。 */
ok(pb && /六项|世界守恒/.test(pb.body), "散文档没写 P-9 世界守恒的六项核对表");
ok(pb && pb.body.indexOf("那就是重开了") >= 0, "散文档的 P-10 条文里没写「就是重开了」这条判据收口");
ok(pb && (pb.body.match(/拿去当全篇第一句/g) || []).length >= 2, "P-10 判据应在条文与自检清单各出现一次（少一处即有一边是空的）");
ok(pb && /终止标点|收尾引号/.test(pb.body), "散文档没写 P-11 末句必须落在整句上");
ok(pb && /起名|叫出一个名字/.test(pb.body), "散文档没写 P-12 起名律（这一档唯一能抬高位置的一条）");
ok(pb && pb.body.indexOf("交付层") >= 0, "散文档的自检清单没把交付层五问排到最前");
ok(sb && sb.body.indexOf("换嘴") >= 0, "小说档没写换嘴检验");
ok(sb && sb.body.indexOf("寓言") >= 0, "小说档没写不许写成寓言");
/* 2026-08-22 第三份真跑（79 分）的三处硬律失分，逐条要在规格里点名。 */
ok(sb && /本篇之内有来历|第一次出现是在哪儿/.test(sb.body), "小说档没写 S-7 本篇自带出处（借来的那句话）");
ok(sb && sb.body.indexOf("演过的") >= 0, "小说档没写 S-2 的演过就不许再说这条计数判据");
ok(sb && sb.body.indexOf("记号") >= 0, "小说档没写 S-8 有意为之必须留记号");
/* 2026-08-23《摔碎的杯子》那份（5193 字 · 盲评 110）的交付层失分，逐条点名。 */
ok(sb && /六项|世界守恒/.test(sb.body), "小说档没写 S-9 世界守恒的六项核对表");
ok(sb && sb.body.indexOf("那就是重开了") >= 0, "小说档的 S-10 条文里没写「就是重开了」这条判据收口");
ok(sb && (sb.body.match(/拿去当全篇第一句/g) || []).length >= 2, "S-10 判据应在条文与自检清单各出现一次");
ok(sb && /终止标点|收尾引号/.test(sb.body), "小说档没写 S-11 每趟必须落在整句上");
ok(sb && /双次显影|两次而结果不同/.test(sb.body), "小说档没写 S-12 双次显影（这一档唯一能抬高位置的一条）");
ok(sb && sb.body.indexOf("交付层") >= 0, "小说档的自检清单没把交付层五问排到最前");
ok(cwBody.indexOf("开了的线") >= 0 || cwBody.indexOf("第二次交代") >= 0, "CW_X 里 X11 没写还账的判据");
ok(cwBody.indexOf("小说档最容易犯") >= 0, "X1 没写「小说档最容易犯」这条警示");
/* 小说档的评分卡要多带一段：手艺好不救硬律。 */
const cgFn = W.slice(W.indexOf("function cwGrade"), W.indexOf("function cwGrade") + 2600);
ok(/手艺好不救硬律/.test(cgFn), "cwGrade 里没写「手艺好不救硬律」这条读数");
ok(/String\(kind\) === "story"/.test(cgFn), "小说档的评分卡没有它自己那三件");
["wechat", "prose", "story"].forEach((k) => {
  const b = specBlock(k);
  ok(b && /明写|隐写|演出/.test(b.body), k + " SPEC 没说承重物在这一档是什么形态（X7 无从自检）");
});

/* ══ ⑨ 90 分线与评分卡：Skill §9.1 的六项 ⇄ 代码 CW_GRADE ══════════ */
sec("⑨ 评分卡与 90 分线");
const gIdx = W.indexOf("const CW_GRADE");
ok(gIdx > 0, "worker.js 里没有 CW_GRADE");
const gBody = gIdx > 0 ? W.slice(gIdx, W.indexOf("}", W.indexOf("story:", gIdx))) : "";
/* 从 Skill 的评分卡表里取三列各自的六个项名，逐个在 CW_GRADE 里找。
   两处不一致的表现不是报错，是**写的人按一套自评、评的人按另一套判分**。 */
const DIMS = {
  wechat: ["开场与结构", "承重判断", "例证（数量·次序·远近）", "语言手艺", "结尾动作与边界", "硬律合规"],
  prose: ["场景与细节", "三段呼吸", "视点守恒", "藏理", "闲笔还账与收尾", "硬律合规"],
  story: ["进入与冲突", "判断的演出", "口吻分离", "细节出处", "结尾", "硬律合规"],
};
Object.keys(DIMS).forEach((k) => {
  DIMS[k].forEach((d) => {
    ok(SKILL.indexOf(d) >= 0, "Skill §9.1 评分卡里缺维度「" + d + "」");
    const line = (gBody.match(new RegExp(k + ': "([^"]+)"')) || [])[1] || "";
    ok(line.indexOf(d) >= 0, "CW_GRADE." + k + " 里缺维度「" + d + "」");
  });
  const b = specBlock(k);
  ok(b && b.body.indexOf('cwGrade("' + k + '")') >= 0, k + " 的 SPEC 没有下发评分卡");
});
ok(/目标 90/.test(W.slice(W.indexOf("function cwGrade"), W.indexOf("function cwGrade") + 1500)),
  "cwGrade 里没写目标 90");
ok(/85%/.test(W.slice(W.indexOf("function cwGrade"), W.indexOf("function cwGrade") + 1500)),
  "cwGrade 里没写每项不低于 85% 这条判据");
ok(/封顶 85/.test(W.slice(W.indexOf("function cwGrade"), W.indexOf("function cwGrade") + 1500)),
  "cwGrade 里没写硬律违反封顶 85");
ok(SKILL.indexOf("目标线：90") >= 0 || SKILL.indexOf("**目标线：90**") >= 0, "Skill §9.1 没写目标线 90");
ok(SKILL.indexOf("### 9.2 从 87 到 90") >= 0, "Skill 缺 §9.2「从 87 到 90 差的三件」");

/* ══ ⑭ 三件工程活（2026-08-23）══════════════════════════════════════
   ① 世界快照 world：分趟叙事的承重件（P-9 / S-9 靠它才有机器保障）
   ② 中篇档 novella：分册 §3.4 那条「中长篇故意没有机器层」的欠条
   ③ 末句机检 tailCut：整篇收尾也要判一次（noHead 档此前完全漏判） */
sec("⑭ 世界快照 / 中篇档 / 末句机检");
{
  /* ①-a 该开 world 的三档都开了；不该开的没被顺手打开 */
  ["prose", "story", "novella"].forEach((k) => {
    ok(new RegExp("\\n        " + k + ": \\{[^\\n]*world: 1").test(W), k + " 档没开 world（分趟时设定会各写一份）");
  });
  ["wechat", "poem"].forEach((k) => {
    ok(!new RegExp("\\n        " + k + ": \\{[^\\n]*world: 1").test(W), k + " 档不该开 world（它没有跨趟的设定连续性问题）");
  });
  /* ①-b 提纲那一趟要得出来、正文各趟收得到，两头都要在 */
  ok(/SPEC\.world \? \('"world":/.test(W), "plan 那一趟没有向基底要 world 字段");
  ok(W.indexOf("【世界快照（全篇唯一，本趟必须逐条遵守") >= 0, "正文各趟没有回灌世界快照");
  ok(W.indexOf("这一篇没有拟出设定表") >= 0,
    "世界快照为空时没有明说——静默不下发等于把「没定」记成了「不需要」");
  ok(/world: SPEC\.world \? "" : undefined/.test(W), "bare 兜底没有显式给出 world 键");
  /* ①-c 线索表只给中篇（短篇散文用不上，给了是噪声） */
  ok(/\n        novella: \{[^\n]*threads: 1/.test(W), "novella 没开 threads（线索表）");
  ok(W.indexOf("另加⑦线索表") >= 0, "plan 提示语里没有线索表那一条");

  /* ②-a 中篇八节表：M-1 那一对必须互相指认，否则中篇就不是中篇 */
  const nb = specBlock("novella");
  ok(!!nb, "worker.js 里找不到 novella 档");
  if (nb) {
    ok(nb.name === "中篇小说（24000字）", "novella 档名不对：" + nb.name);
    ok(/parts: 8/.test(W.slice(W.indexOf("novella: { name:"), W.indexOf("novella: { name:") + 300)), "novella 不是八趟");
    ok(nb.body.indexOf("将在第 7 节被原样重来一次") >= 0, "第 2 节没写明它会在第 7 节被重来（M-1 的一半）");
    ok(nb.body.indexOf("与第 2 节同形的处境再来一次") >= 0, "第 7 节没指回第 2 节（M-1 的另一半）");
    ["M-1", "M-2", "M-4", "M-5"].forEach((c) => ok(nb.body.indexOf(c) >= 0, "novella SPEC 里没有 " + c));
    /* 十二条 S 律靠 STORY_CORE 拼进来——展开后必须条条都在 */
    LAWS.story.forEach((c) => ok(nb.body.indexOf(c) >= 0, "novella 拼上 STORY_CORE 之后仍缺 " + c));
    ok(nb.body.indexOf("压强") >= 0, "novella SPEC 没写「中篇与短篇是压强的两档」这条分界");
  }
  /* ②-b STORY_CORE 是共用的一份：真值非空，且短篇也吃这一份 */
  ok(STORY_CORE.length > 1500, "STORY_CORE 真值只有 " + STORY_CORE.length
    + " 字符——多半是 `const X = \"\"` 后面漏了 `+`，ASI 会把它断成空串而 node --check 照样通过");
  ok(W.indexOf('          + STORY_CORE\n') >= 0, "story 档没有拼上 STORY_CORE（十二条 S 律落空）");
  /* ②-c 一档三处：白名单、字数、档次表，缺一处就是「菜单点得到、后端认不出」 */
  ok(/novella: 1/.test(W), "novella 不在服务端白名单里");
  ok(/novella: 24000/.test(W), "DIST_WORDS 里没有 novella");
  ok(/novella:\[16000,24000,40000\]/.test(W.replace(/\s/g, "")), "DIST_WORD_OPTS 里 novella 不是 16000/24000/40000");
  const MODE = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");
  ok(/k: "novella"[^}]*w: 24000/.test(MODE), "前端 KIND_DEF 里没有 novella，或目标字数对不上");
  ok(/k: "novella"[^}]*[,{]\s*c: 1/.test(MODE), "novella 没标 c:1（不走拆趟那条路，八节会挤成一趟）");
  ok(MODE.indexOf("kNovella:") >= 0, "前端没有 kNovella 的文案");
  /* ⚠ 这一条是上面那次漏网留下的：`doc: 1` 里含着子串 `c: 1`，
     所以凡是查这类短旗标，一律钉「逗号或左括号之后」，不许裸查。
     同样的写法对四档创作体各查一次——它们全都必须走拆趟那条路。 */
  ["wechat", "prose", "story", "novella"].forEach((k) => {
    ok(new RegExp('k: "' + k + '"[^}]*[,{]\\s*c: 1').test(MODE), k + " 没标 c:1（不走拆趟，整篇会挤成一趟）");
  });

  /* ③ 末句机检：逐趟判之外，整篇收尾也要判一次 */
  ok(MODE.indexOf("function tailCut") >= 0, "wds-mode.js 里没有 tailCut");
  ok(MODE.indexOf("全文停在半句上") >= 0,
    "收尾处没有全文末句闸——noHead 档没有 `## 小标题`，missingSecs 永远回空，断稿一路静默");
  ok(/if \(tailCut\(text\)\)/.test(MODE), "全文末句闸判的不是整篇 text");
}

/* ══ ⑧ 规范层自身的完整性 ═══════════════════════════════════════ */
sec("⑧ 规范层自检");
const han = (SKILL.match(/[\u4e00-\u9fff]/g) || []).length;
/* 2026-08-23：散文与小说两节已移出到分册，总纲从「三体裁全文」变成「分工总纲 ＋ 公众号一节 ＋ 两页指路」。
   一万字的规格从此**按文体分册计**（见 ⑩ ⑪），总纲自己只保底 8000。
   ⚠ 公众号那一节还留在总纲里；等它也拆出分册，这一条要连同 ⑫ 一起改。 */
/* 2026-08-23 二次下调：公众号也移出分册后，总纲成为「分工总纲 ＋ X 律 ＋ 四页指路」。
   一万字的规格按文体分册计（⑩ 散文 ⑪ 小说 ⑫ 诗歌 ⑬ 公众号），总纲自己保底 8000。
   ⚠ 四份分册的入口都必须在总纲里挂着——漏一份的表现是「分册在仓库里、没人找得到」。 */
ok(han >= 8000, "总纲汉字数 " + han + "，低于保底 8000");
["sde-wechat-writing.md", "sde-prose-writing.md", "sde-story-writing.md", "sde-poem-writing.md"]
  .forEach((f) => ok(SKILL.indexOf(f) >= 0, "总纲第一节的表里没挂分册 " + f));
["## 一 ·", "## 二 ·", "## 三 ·", "## 四 ·", "## 五 ·", "## 六 ·", "## 七 ·", "## 八 ·", "## 九 ·", "## 十 ·", "## 附录 A"]
  .forEach((h) => ok(SKILL.indexOf(h) >= 0, "Skill 缺章节 " + h));
ok(SKILL.indexOf("tools/sim_creative_writing.js") >= 0, "Skill 第一节没有指向本护栏");

/* ══ ⑩ 散文分册自身（每一种文体的写作 Skill 都要到一万汉字）══════════ */
sec("⑩ 散文分册 sde-prose-writing.md");
const phan = (PROSE.match(/[\u4e00-\u9fff]/g) || []).length;
ok(phan >= 10000, "散文分册汉字 " + phan + "，低于一万字的规格要求");
["## 一 ·", "## 二 ·", "## 三 ·", "## 四 ·", "## 五 ·", "## 六 ·", "## 七 ·", "## 八 ·", "## 九 ·", "## 十 ·", "## 十一 ·", "## 十二 ·", "## 附录 A", "## 附录 B", "## 附录 C"]
  .forEach((h) => ok(PROSE.indexOf(h) >= 0, "散文分册缺章节 " + h));
ok(PROSE.indexOf("tools/sim_creative_writing.js") >= 0, "分册第一节没有指向本护栏");
ok(SKILL.indexOf("sde-prose-writing.md") >= 0, "总纲第四节没有指向散文分册（两份口径的入口断了）");
/* 分册的附录 A 编译表要与机器层对上 */
ok(/`prose`[^\n]*5000[^\n]*20000/.test(PROSE), "分册附录 A 的 prose 行与机器层字数/预算对不上");

/* ══ ⑬ 公众号分册 sde-wechat-writing.md ════════════════════════════ */
sec("⑬ 公众号分册 sde-wechat-writing.md");
const whan = (WECHAT.match(/[\u4e00-\u9fff]/g) || []).length;
ok(whan >= 10000, "公众号分册汉字 " + whan + "，低于一万字的规格要求");
LAWS.wechat.forEach((code) =>
  ok(WECHAT.indexOf("### " + code + " ·") >= 0, "公众号分册缺硬律条文 " + code + "（交叉引用不算，要有它自己那一节）"));
["## 一 ·", "## 二 ·", "## 三 ·", "## 四 ·", "## 五 ·", "## 六 ·", "## 七 ·", "## 八 ·", "## 九 ·", "## 十 ·", "## 十一 ·", "## 十二 ·", "## 十三 ·", "## 附录 A", "## 附录 B", "## 附录 C"]
  .forEach((h) => ok(WECHAT.indexOf(h) >= 0, "公众号分册缺章节 " + h));
ok(WECHAT.indexOf("tools/sim_creative_writing.js") >= 0, "公众号分册第一节没有指向本护栏");
ok(SKILL.indexOf("sde-wechat-writing.md") >= 0, "总纲第三节没有指向公众号分册");
["观点文", "故事文", "方法文"].forEach((t) =>
  ok(WECHAT.indexOf(t) >= 0, "公众号分册缺形态「" + t + "」"));
/* 第七节那六个诱惑是这一册与任何通用写作规范的分别，缺一条 W-10 就只是一句口号 */
["悬念钩子", "制造对立", "制造焦虑", "借权威", "金句化", "互动尾巴"].forEach((k) =>
  ok(WECHAT.indexOf(k) >= 0, "公众号分册第七节缺诱惑「" + k + "」"));
ok(WECHAT.indexOf("封顶 70") >= 0, "公众号分册没写 W-10 违反即封顶 70");
ok(/`wechat`[^\n]*3000[^\n]*12000/.test(WECHAT), "公众号分册附录 A 与机器层的字数/预算对不上");

/* ══ ⑫ 诗歌分册 sde-poem-writing.md ⇄ 成文机 poem 档 ════════════════ */
sec("⑫ 诗歌分册与 poem 档");
const phan2 = (POEM.match(/[\u4e00-\u9fff]/g) || []).length;
ok(phan2 >= 10000, "诗歌分册汉字 " + phan2 + "，低于一万字的规格要求");
const pm = W.match(/\n        poem: \{ name: "([^"]+)", tok: (\d+),/);
ok(!!pm, "worker.js 里找不到 poem 档 SPEC");
const pBody = pm ? W.slice(pm.index, W.indexOf("\n        /* ══ 应用文五档", pm.index)) : "";
ok(pm && /`poem`[^\n]*诗歌（500字）[^\n]*500[^\n]*6000/.test(POEM),
  "诗歌分册附录 A 与机器层的档名/字数/预算对不上");
const YLAWS = ["Y-1", "Y-2", "Y-3", "Y-4", "Y-5", "Y-6", "Y-7", "Y-8", "Y-9", "Y-10", "Y-11", "Y-12"];
YLAWS.forEach((c) => {
  ok(POEM.indexOf("### " + c + " ·") >= 0, "诗歌分册缺硬律条文 " + c + "（交叉引用不算，要有它自己那一节）");
  ok(pBody.indexOf(c) >= 0, "poem 档 SPEC 里没有 " + c);
});
["## 一 ·", "## 二 ·", "## 三 ·", "## 四 ·", "## 五 ·", "## 六 ·", "## 七 ·", "## 八 ·", "## 九 ·", "## 十 ·", "## 十一 ·", "## 十二 ·", "## 十三 ·", "## 附录 A", "## 附录 B", "## 附录 C"]
  .forEach((h) => ok(POEM.indexOf(h) >= 0, "诗歌分册缺章节 " + h));
ok(POEM.indexOf("tools/sim_creative_writing.js") >= 0, "诗歌分册第一节没有指向本护栏");
/* 五类必须都在 */
["短章", "组诗", "长诗", "格律", "散文诗"].forEach((t) =>
  ok(POEM.indexOf(t) >= 0, "诗歌分册缺「" + t + "」这一类"));
/* 长度三档必须与 DIST_LENS.poem 对齐（两处不一致＝读者选了长度而规格不认） */
ok(/poem:\s*\[300, 500, 1000\]/.test(W), "DIST_LENS.poem 不是 300/500/1000");
/* 变异三实测漏网：分册里「300」在四处出现（短章上限、散文诗区间、两处长度三档），
   宽松的「找得到就算」必然命中其中之一。⇒ 钉两个**唯一的结构位**：附录 A 那一行的常量写法，
   与 §4.1 那句对齐声明。两处都要与 DIST_LENS.poem 逐字一致。 */
ok(POEM.indexOf("`DIST_LENS.poem = [300, 500, 1000]`") >= 0,
  "诗歌分册附录 A 没有逐字写出 DIST_LENS.poem = [300, 500, 1000]");
ok(POEM.indexOf("长度选项正是 **300 / 500 / 1000**") >= 0,
  "诗歌分册 §4.1 的长度三档与 DIST_LENS.poem 对不上");
/* 三条底与三种伪诗：这一册的全部立论基础，缺一条则十二条硬律变成任意禁令 */
["约束与留白", "身体", "决断", "代偿", "盈余", "安全的失败"].forEach((k) =>
  ok(POEM.indexOf(k) >= 0, "诗歌分册第三节缺「" + k + "」"));
["分行的散文", "意象的仓库", "格言的押韵版"].forEach((k) =>
  ok(POEM.indexOf(k) >= 0, "诗歌分册缺伪诗类型「" + k + "」"));
/* 机器层必须带上那几条只有诗才有的判据 */
ok(pBody.indexOf("删掉重排成一段") >= 0 || pBody.indexOf("重排成一段") >= 0, "poem SPEC 没写「删换行重排成一段」这条判据");
ok(pBody.indexOf("只有作者知道答案") >= 0, "poem SPEC 没写留白与含糊的分界");
ok(pBody.indexOf("替我担保") >= 0, "poem SPEC 没写决断那一问（本档最值钱的自问）");
ok(/感叹号\s*0\s*个/.test(pBody), "poem SPEC 没写感叹号 0 个（诗歌档比其余四档加严）");
ok(POEM.indexOf("D／I 两维旁读") >= 0 || POEM.indexOf("D/I 两维旁读") >= 0,
  "诗歌分册没写明这一档只做 D／I 两维旁读（五维里有三维对诗失效）");

/* ══ ⑪ 小说分册（短篇／中篇／长篇）══════════════════════════════════ */
sec("⑪ 小说分册 sde-story-writing.md");
const shan = (STORY.match(/[\u4e00-\u9fff]/g) || []).length;
ok(shan >= 10000, "小说分册汉字 " + shan + "，低于一万字的规格要求");
["## 一 ·", "## 二 ·", "## 三 ·", "## 四 ·", "## 五 ·", "## 六 ·", "## 七 ·", "## 八 ·", "## 九 ·", "## 十 ·", "## 十一 ·", "## 十二 ·", "## 十三 ·", "## 十四 ·", "## 附录 A", "## 附录 B", "## 附录 C"]
  .forEach((h) => ok(STORY.indexOf(h) >= 0, "小说分册缺章节 " + h));
ok(STORY.indexOf("tools/sim_creative_writing.js") >= 0, "小说分册第一节没有指向本护栏");
ok(SKILL.indexOf("sde-story-writing.md") >= 0, "总纲第五节没有指向小说分册");
/* 三类必须都在，且中长篇的硬律编号齐全 */
["短篇", "中篇", "长篇"].forEach((t) => ok(STORY.indexOf(t) >= 0, "小说分册缺「" + t + "」这一类"));
["M-1", "M-2", "M-3", "M-4", "M-5"].forEach((c) =>
  ok(STORY.indexOf("#### " + c + " ·") >= 0, "小说分册缺中篇硬律条文 " + c + "（交叉引用不算，要有它自己那一节）"));
["L-1", "L-2", "L-3", "L-4", "L-5", "L-6"].forEach((c) =>
  ok(STORY.indexOf("#### " + c + " ·") >= 0, "小说分册缺长篇硬律条文 " + c + "（交叉引用不算，要有它自己那一节）"));
LAWS.story.forEach((code) => ok(STORY.indexOf("### " + code + " ·") >= 0, "小说分册缺硬律条文 " + code));
/* 附录 A 要与机器层对上，且必须写明中长篇没有机器层（否则下一个人会以为漏了） */
ok(/`story`[^\n]*2400[^\n]*10000/.test(STORY), "小说分册附录 A 的 story 行与机器层字数/预算对不上");
/* 2026-08-23：中篇已有机器层，欠条只剩长篇那一件（快照的增量更新）。
   这条断言的用意没变——**分册必须写明哪一件还没做**，否则下一个人会以为机器层漏了。 */
ok(/长篇仍然只有规范层|长篇还不能/.test(STORY), "小说分册没写明长篇仍无机器层");
ok(STORY.indexOf("快照的增量更新") >= 0, "小说分册没写明长篇缺的到底是哪一件");
ok(STORY.indexOf("`novella`") >= 0, "小说分册附录 A 没把中篇挪进已实现那一张表");
ok(/2000\/1750\/1250/.test(PROSE), "分册附录 A 没写 ChatSDE 的三趟分法");
LAWS.prose.forEach((code) => ok(PROSE.indexOf("### " + code + " ·") >= 0, "散文分册缺硬律条文 " + code));

console.log("\n═══ sim_creative_writing: " + pass + " PASS / " + fail + " FAIL ═══");
process.exit(fail ? 1 : 0);
