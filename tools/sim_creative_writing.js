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
const SKILL_ALL = SKILL + "\n" + PROSE + "\n" + STORY + "\n" + POEM;
const W = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");
const LITE = fs.readFileSync(path.join(ROOT, "public/sites/lang/chatjohn/lite/index.html"), "utf8");

let pass = 0, fail = 0;
const ok = (c, m) => { if (c) { pass++; } else { fail++; console.log("  ✗ " + m); } };
const sec = (t) => console.log("\n【" + t + "】");

/* ── 取 worker.js 里某一档 SPEC 的整块文本（从 `key: { name:` 到下一个 `key: { name:`）── */
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
  return { name: m[1], tok: +m[2], body: rest.slice(0, nxt > 0 ? nxt : 6000) };
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
  wechat: ["W-1", "W-2", "W-3", "W-4", "W-5", "W-6", "W-7"],
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
const jcRe = /\|\s*`(wechat|essay|story)`\s*\|\s*([^|]+?)\s*\|\s*(\d+)\s*×\s*(\d+)\s*\|/g;
const jcRows = [];
while ((r = jcRe.exec(SKILL))) jcRows.push({ key: r[1], label: r[2], parts: +r[3], per: +r[4] });
ok(jcRows.length === 3, "附录 A 第二张表应解析出 3 行，实得 " + jcRows.length);
jcRows.forEach((row) => {
  const m = W.match(new RegExp(row.key + ":\\s*\\{ parts: (\\d+), per: (\\d+), label: \"([^\"]+)\""));
  ok(!!m, "JOHN_COMPOSE 里没有 " + row.key);
  if (!m) return;
  ok(+m[1] === row.parts, row.key + " 趟数不一致：Skill " + row.parts + " vs 代码 " + m[1]);
  ok(+m[2] === row.per, row.key + " 每趟字数不一致：Skill " + row.per + " vs 代码 " + m[2]);
  ok(m[3] === row.label, row.key + " 档名不一致：" + row.label + " vs " + m[3]);
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

/* ══ ⑧ 规范层自身的完整性 ═══════════════════════════════════════ */
sec("⑧ 规范层自检");
const han = (SKILL.match(/[\u4e00-\u9fff]/g) || []).length;
/* 2026-08-23：散文与小说两节已移出到分册，总纲从「三体裁全文」变成「分工总纲 ＋ 公众号一节 ＋ 两页指路」。
   一万字的规格从此**按文体分册计**（见 ⑩ ⑪），总纲自己只保底 8000。
   ⚠ 公众号那一节还留在总纲里；等它也拆出分册，这一条要连同 ⑫ 一起改。 */
ok(han >= 8000, "总纲汉字数 " + han + "，低于保底 8000");
ok(SKILL.indexOf("## 三 · 公众号文章规范") >= 0, "公众号一节仍应留在总纲（尚未拆分册）");
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
ok(/未实现|没有机器层/.test(STORY), "小说分册没写明中篇与长篇只有规范层——下一个改这里的人会以为机器层漏了");
ok(/2000\/1750\/1250/.test(PROSE), "分册附录 A 没写 ChatSDE 的三趟分法");
LAWS.prose.forEach((code) => ok(PROSE.indexOf("### " + code + " ·") >= 0, "散文分册缺硬律条文 " + code));

console.log("\n═══ sim_creative_writing: " + pass + " PASS / " + fail + " FAIL ═══");
process.exit(fail ? 1 : 0);
