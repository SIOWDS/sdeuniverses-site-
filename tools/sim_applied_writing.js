// 应用文五档：规范层（tools/skills/sde-applied-*.md）与机器层（worker.js 五档 SPEC）逐条对账
// 纪律来源：sde-applied-writing.md 第六节——「本组文件的档名、字数或硬律编号一改，机器层必须同 commit 改」。
// 站内每一次「改完源码模拟照样全绿、病却已上线」，根子都在同一件事有两份口径。
const fs = require("fs");
const R = (p) => fs.readFileSync(__dirname + "/../" + p, "utf8");
const W = R("src/worker.js"), F = R("public/wds-mode.js");
const SK = {
  writing: R("tools/skills/sde-applied-writing.md"),
  notice: R("tools/skills/sde-applied-notice.md"),
  plan: R("tools/skills/sde-applied-plan.md"),
  summary: R("tools/skills/sde-applied-summary.md"),
  speech: R("tools/skills/sde-applied-speech.md"),
  letter: R("tools/skills/sde-applied-letter.md"),
};
let PASS = 0, FAIL = 0;
const ok = (name, cond, extra) => {
  if (cond) { PASS++; console.log("  PASS " + name); }
  else { FAIL++; console.log("  FAIL " + name + (extra ? "　" + extra : "")); }
};
const han = (s) => (String(s).match(/[\u4e00-\u9fff]/g) || []).length;
// 各档 SPEC 段：起点是档名那一行，终点是下一个档的档名行（或 SPEC 表结束）
const SPECALL = W.slice(W.indexOf("      const SPEC = {"), W.indexOf("      }[kind];"));
function specOf(k) {
  const m = SPECALL.match(new RegExp("\\n        " + k + ": \\{ name: \"([^\"]+)\"[\\s\\S]*?(?=\\n        [a-z0-9]+: \\{ name: \"|$)"));
  return m ? m[0] : "";
}

// ══ 一、规范层本身 ══════════════════════════════════════════
console.log("【一、规范层：六份文件与字数下限】");
// ⭐ 用户定的下限：每类应用文的写作 Skill 至少 5000 汉字
for (const k of ["notice", "plan", "summary", "speech", "letter"]) {
  const n = han(SK[k]);
  ok("【" + k + "】分档规范 ≥5000 汉字（用户定的下限）", n >= 5000, "实得 " + n);
}
ok("总纲存在且成体量", han(SK.writing) >= 3000, "实得 " + han(SK.writing));

// 载重表：五档的 key / 目标字数 / 承重物 / 责任落点，从总纲附录 A 解析
console.log("\n【二、载重表：规范层 → 机器层】");
const rows = [];
for (const m of SK.writing.matchAll(/\n\| `(\w+)` \| ([^|]+?) \| (\d+) \| (\d+) \| (\d+) × (\d+) \| ([^|]+?) \| ([^|]+?) \| (\w) \|/g)) {
  rows.push({ key: m[1], name: m[2].trim(), words: +m[3], tok: +m[4], parts: +m[5], per: +m[6],
              form: m[7].trim(), owner: m[8].trim(), prefix: m[9] });
}
ok("总纲附录 A 解析出 5 行", rows.length === 5, "实得 " + rows.length);

const DW = {};
{
  const m = W.match(/const DIST_WORDS = \{([\s\S]*?)\};/);
  if (m) for (const x of m[1].matchAll(/(\w+):\s*(\d+)/g)) DW[x[1]] = +x[2];
}
for (const r of rows) {
  const seg = specOf(r.key);
  ok("【" + r.key + "】worker.js 里有这一档 SPEC", !!seg);
  if (!seg) continue;
  ok("【" + r.key + "】档名与规范层一致", seg.indexOf('name: "' + r.name + '"') > 0, "规范层写的是 " + r.name);
  ok("【" + r.key + "】目标字数与规范层一致", DW[r.key] === r.words, "DIST_WORDS " + DW[r.key] + " ／ 规范层 " + r.words);
  ok("【" + r.key + "】输出预算与规范层一致", new RegExp("tok: " + r.tok + "\\b").test(seg), "规范层 " + r.tok);
  ok("【" + r.key + "】前端档位表目标字数一致",
     new RegExp('k: "' + r.key + '"[^}]*\\bw: ' + r.words + '\\b').test(F));
  // ⭐ 五档全部要出 Word 与 PDF：应用文的成品是要发出去、要存档、要签字的
  ok("★【" + r.key + "】出得了 Word 与 PDF（doc:1）", new RegExp('k: "' + r.key + '"[^}]*doc: 1').test(F));
  // ⭐ 五档一律不挂笔法面板：学谁的腔调都不改责任落点
  ok("★【" + r.key + "】不挂笔法旗标", !new RegExp('k: "' + r.key + '"[^}]*\\bsty: 1').test(F));
  // 拆趟：规范层写 1 × N 的就不许拆，写 N × M 的必须拆且配比对得上
  const isChunk = r.parts > 1;
  ok("【" + r.key + "】拆趟与否与规范层一致（规范层 " + r.parts + " 趟）",
     isChunk === /parts: \d+/.test(seg) && isChunk === new RegExp('k: "' + r.key + '"[^}]*\\bc: 1').test(F));
  if (isChunk) {
    ok("【" + r.key + "】parts 与规范层一致", new RegExp("parts: " + r.parts + "\\b").test(seg));
    const ws = [...seg.matchAll(/words: (\d+)/g)].map((x) => +x[1]);
    ok("【" + r.key + "】fixed 条数 = parts", ws.length === r.parts, "实得 " + ws.length);
    // ⭐ 各趟之和低于目标 ＝ 闸自己先认输了
    ok("★【" + r.key + "】各趟之和不低于目标字数", ws.reduce((a, b) => a + b, 0) >= r.words,
       "和 " + ws.reduce((a, b) => a + b, 0) + " ／ 目标 " + r.words);
    ok("【" + r.key + "】单趟 ≤2200 字（越长越容易提前收尾）", Math.max(...ws) <= 2200);
    // 应用文各档都有自己的小标题体例，趟名只是内部分工
    ok("★【" + r.key + "】标了 noHead（趟名不许写进正文）", /noHead: 1/.test(seg));
  }
  // 服务端白名单：只改 SPEC 不改白名单＝菜单点得到、后端认不出，默默按「对话报告」写一篇
  ok("★【" + r.key + "】在服务端白名单里", new RegExp("\\b" + r.key + ": 1").test(W.slice(W.indexOf("const kind = ({ report: 1"), W.indexOf("const kind = ({ report: 1") + 400)));
}

// ══ 三、承重物与责任落点写进了提示语 ══════════════════════
console.log("\n【三、承重物与责任落点】");
for (const r of rows) {
  const seg = specOf(r.key);
  if (!seg) continue;
  // ⭐ 这一组的地基判断：五类不是五种长度，是责任落点的五种位置。
  //    落点不写进提示语，基底就会把五档写成同一种公文腔。
  /* ⚠ 只搜那两个词会被邻居喂饱：notice 的正文里另有「收件人先要知道…」「收件人的三个问题」，
     于是把承重那一句整句删掉，断言照样绿（变异第九发当场抓到）。
     💡 通则：**承重的是那一句话，不是那个词**——断言要钉整句形状。 */
  ok("★【" + r.key + "】提示语里写明了承重物形态（" + r.form + "）",
     new RegExp("承重物在这一档是\\*\\*" + r.form + "\\*\\*").test(seg));
  ok("★【" + r.key + "】提示语里写明了责任落在谁身上（" + r.owner + "）",
     new RegExp("责任落在\\*\\*" + r.owner + "\\*\\*身上").test(seg));
}

// ══ 四、七条共用 X 律 ═══════════════════════════════════════
console.log("\n【四、七条共用 X 律】");
const xs = [...SK.writing.matchAll(/### X(\d) · ([^\n—]+?) ——/g)].map((m) => ({ n: +m[1], name: m[2].trim() }));
ok("总纲解析出 7 条 X 律", xs.length === 7, "实得 " + xs.length);
const AX = (W.match(/const APPLIED_X = "[\s\S]*?";\n/) || [""])[0];
ok("抠得到 APPLIED_X", AX.length > 500);
for (const x of xs) ok("APPLIED_X 里有 X" + x.n, new RegExp("X" + x.n + " ").test(AX));
// ⚠ 与创作类那组的 X 律编号互不相干，不许交叉引用
ok("★ APPLIED_X 与 CW_X 是两个常量（编号互不相干）",
   /const APPLIED_X = /.test(W) && /const CW_X = /.test(W));
ok("★ 五档挂的是 APPLIED_X 不是 CW_X",
   rows.every((r) => specOf(r.key).indexOf("APPLIED_X") > 0)
   && rows.every((r) => specOf(r.key).indexOf("CW_X") < 0));
ok("五档都挂了交稿自检 APPLIED_CHECK", rows.every((r) => specOf(r.key).indexOf("APPLIED_CHECK") > 0));
// 落点律与截止律是这一组的命根子：禁用词必须真的写进块里
for (const bad of ["相关部门", "尽快", "望周知", "特此通知", "盼复"])
  ok("APPLIED_X 点名禁用「" + bad + "」", AX.indexOf(bad) > 0);
for (const must of ["谁来宣布", "谁签字", "9 月 3 日 17:00"])
  ok("APPLIED_X 给了正例「" + must + "」", AX.indexOf(must) > 0);

// ══ 五、各档硬律编号逐条落到提示语 ═════════════════════════
console.log("\n【五、各档硬律编号】");
for (const r of rows) {
  const seg = specOf(r.key);
  if (!seg) continue;
  const laws = [...SK[r.key].matchAll(new RegExp("### " + r.prefix + "-(\\d+) · ([^\\n（(]+)", "g"))]
    .map((m) => r.prefix + "-" + m[1]);
  ok("【" + r.key + "】规范层解析出硬律（前缀 " + r.prefix + "）", laws.length >= 8, "实得 " + laws.length);
  // 不要求每一条都进提示语（提示语有长度预算），但**命根子那几条必须进**
  const hit = laws.filter((L) => seg.indexOf(L) > 0);
  ok("★【" + r.key + "】过半硬律编号进了提示语", hit.length * 2 >= laws.length,
     hit.length + "/" + laws.length + " 命中：" + hit.join("、"));
}
// 各档评分卡里点名的「直接封顶」那几条，一条都不许漏进提示语
const cap = { notice: ["N-2", "N-6"], plan: ["F-5", "F-8"], summary: ["Z-4", "Z-9"], speech: ["J-2", "J-5"], letter: ["H-2", "H-4"] };
for (const k of Object.keys(cap)) {
  for (const L of cap[k]) {
    ok("★【" + k + "】封顶条 " + L + " 在规范层评分卡里点了名", new RegExp("封顶[\\s\\S]{0,120}" + L + "|" + L + "[\\s\\S]{0,120}封顶").test(SK[k]));
    ok("★【" + k + "】封顶条 " + L + " 进了提示语", specOf(k).indexOf(L) > 0);
  }
}

// ══ 六、字数闸挂上了 ════════════════════════════════════════
console.log("\n【六、字数闸】");
for (const r of rows) {
  const seg = specOf(r.key);
  if (!seg) continue;
  if (r.parts > 1) ok("【" + r.key + "】拆趟档走 part 那条路的闸（每趟一道）", /\+ distWordGate\(want, partIdx \+ 1, secs\.length\)/.test(W));
  else ok("【" + r.key + "】一趟档走全篇那道闸", /\+ distWordGate\(SPEC\.words, 1, 1\)/.test(W));
}
ok("★ 五档目标字数全在 DIST_WORDS 里", rows.every((r) => DW[r.key] === r.words));

console.log("\n" + (FAIL ? "✗ " : "✓ ") + PASS + " 项通过，" + FAIL + " 项失败");
process.exit(FAIL ? 1 : 0);
