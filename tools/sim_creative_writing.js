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
const W = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");
const LITE = fs.readFileSync(path.join(ROOT, "public/sites/lang/chatjohn/lite/index.html"), "utf8");

let pass = 0, fail = 0;
const ok = (c, m) => { if (c) { pass++; } else { fail++; console.log("  ✗ " + m); } };
const sec = (t) => console.log("\n【" + t + "】");

/* ── 取 worker.js 里某一档 SPEC 的整块文本（从 `key: { name:` 到下一个 `key: { name:`）── */
function specBlock(key) {
  const re = new RegExp("\\n        " + key + ": \\{ name: \"([^\"]+)\", tok: (\\d+), spec:");
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
  wechat: ["W-1", "W-2", "W-3", "W-4", "W-5", "W-6"],
  prose: ["P-1", "P-2", "P-3", "P-4", "P-5", "P-6"],
  story: ["S-1", "S-2", "S-3", "S-4", "S-5", "S-6"],
};
Object.keys(LAWS).forEach((k) => {
  LAWS[k].forEach((code) => {
    ok(SKILL.indexOf("硬律 " + code) >= 0 || SKILL.indexOf("（" + code + "）") >= 0,
      "Skill 里找不到硬律 " + code);
    const b = specBlock(k);
    ok(b && b.body.indexOf(code) >= 0, k + " 的 SPEC 里没有 " + code);
  });
});

/* ══ ③ 共用硬律 X1–X7：只许有一份，三档都要挂 ══════════════════════ */
sec("③ 共用硬律 CW_X");
const cwIdx = W.indexOf("const CW_X =");
ok(cwIdx > 0, "worker.js 里没有 CW_X");
const cwBody = cwIdx > 0 ? W.slice(cwIdx, cwIdx + 2600) : "";
["X1", "X2", "X3", "X4", "X5", "X6", "X7"].forEach((x) => {
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
ok(/per \* 0\.8/.test(jcsFn), "johnComposeSys 里没有按 80% 算下限");
ok(jcsFn.indexOf("不许收尾") >= 0, "非末趟没有写「不许收尾」（实测欠字就出在提前收尾）");
ok(jcsFn.indexOf('kind !== "paper"') >= 0, "共用硬律应只挂三体裁，论文档有自己的体例");
["wechat", "prose", "story"].forEach((k) => {
  const b = specBlock(k);
  ok(b && /八成|八成以上|字数到/.test(b.body), k + " SPEC 里没有字数闸的说法");
});

/* ══ ⑦ 三条实测病灶必须写进规格（不是写进注释）══════════════════════ */
sec("⑦ 实测病灶落进规格");
const wb = specBlock("wechat"), pb = specBlock("prose"), sb = specBlock("story");
ok(wb && wb.body.indexOf("同向") >= 0, "公众号档没写例证同向律（真跑第一号病）");
ok(wb && /最多两位/.test(wb.body), "公众号档没写具名上限");
ok(pb && pb.body.indexOf("15%") >= 0, "散文档没写议论占比上限（真跑第二号病）");
ok(pb && /视点|三问/.test(pb.body), "散文档没写视点守恒");
ok(pb && pb.body.indexOf("取消提问资格") >= 0, "散文档没写 P-6");
ok(sb && sb.body.indexOf("换嘴") >= 0, "小说档没写换嘴检验");
ok(sb && sb.body.indexOf("寓言") >= 0, "小说档没写不许写成寓言");
["wechat", "prose", "story"].forEach((k) => {
  const b = specBlock(k);
  ok(b && /明写|隐写|演出/.test(b.body), k + " SPEC 没说承重物在这一档是什么形态（X7 无从自检）");
});

/* ══ ⑧ 规范层自身的完整性 ═══════════════════════════════════════ */
sec("⑧ 规范层自检");
const han = (SKILL.match(/[\u4e00-\u9fff]/g) || []).length;
ok(han >= 10000, "Skill 汉字数 " + han + "，低于一万字的规格要求");
["## 一 ·", "## 二 ·", "## 三 ·", "## 四 ·", "## 五 ·", "## 六 ·", "## 七 ·", "## 八 ·", "## 九 ·", "## 十 ·", "## 附录 A"]
  .forEach((h) => ok(SKILL.indexOf(h) >= 0, "Skill 缺章节 " + h));
ok(SKILL.indexOf("tools/sim_creative_writing.js") >= 0, "Skill 第一节没有指向本护栏");

console.log("\n═══ sim_creative_writing: " + pass + " PASS / " + fail + " FAIL ═══");
process.exit(fail ? 1 : 0);
