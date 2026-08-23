// 成文「超字数」三刀的护栏（2026-08-23）
//
// 起因：同一场对话连出三篇，PDF 页脚字数 5052/5000（散文·准）、4396/3000（论说·+47%）、
// 5193/2400（小说·+93%，其中约 570 字是复述上一节）。查下来是四处叠在一起：
//   ① distWordGate 只有下限没有上限——「不到 N 字就是没写完，回去补」，只在一个方向施压；
//   ② 选了字数档只改 SPEC.words / SPEC.fixed，**name 与 spec 里写死的数不动**，而两处都进提示语；
//   ③ story 的 spec 自己写着「可到 4000 字」，把上限放宽 1.67 倍；
//   ④ essay 无 fixed 且 tok 硬底 32000（≈一万汉字），预算是天花板，基底就往天花板写。
// 这份护栏钉住的就是这四处的修法，以及**减字的方向**（不许靠删例子减字——那是全篇最结实的部分）。
const fs = require("fs");
const R = (p) => fs.readFileSync(__dirname + "/../" + p, "utf8");
const W = R("src/worker.js");
let PASS = 0, FAIL = 0;
const ok = (name, cond, extra) => {
  if (cond) { PASS++; console.log("  PASS " + name); }
  else { FAIL++; console.log("  FAIL " + name + (extra ? "　" + extra : "")); }
};

// ── 一、字数闸的上限那一半 ───────────────────────────────────
console.log("【一、字数闸补上限】");
const mG = W.match(/function distWordGate\(want, part, N\) \{[\s\S]*?\n\}/);
ok("抠得到 distWordGate", !!mG);
const G = mG ? mG[0] : "";
ok("★ 上限是目标的 1.15 倍（与下限 0.9 对称）", /const cap = Math\.round\(w \* 1\.15\);/.test(G));
ok("★ 下限那一半没被这一刀弄丢", /w \* 0\.9/.test(G));
ok("★ 减字的方向写死了：先删解释与过渡", /先删你自己的解释与过渡/.test(G));
ok("★ 明令不许靠删例子/细节/具体的人来减字", /不许靠删例子、删细节、删具体的人来减字/.test(G));
ok("★ 复述上文被点名为超字的头号来源", /复述上文/.test(G));

let gate = null;
try {
  gate = new Function("want", "part", "N",
    G.replace(/^function distWordGate\([^)]*\)\s*\{/, "").replace(/\}$/, ""));
} catch (e) { gate = null; }
ok("闸能真跑", !!gate);
if (gate) {
  const g3000 = gate(3000, 1, 1);
  ok("★ 3000 字的档：闸上同时写着 2700 与 3450", /2700/.test(g3000) && /3450/.test(g3000), g3000.slice(0, 80));
  ok("★ 目标数本身仍在闸上", /3000/.test(g3000));
  ok("无目标的档仍交空串（报告/提纲/PPT 不逼字数）", gate(0, 1, 1) === "" && gate(undefined, 1, 1) === "");
  ok("非末趟仍明令不许收尾", /不许收尾/.test(gate(1700, 1, 3)));
  ok("★ 末趟仍不出现「不许收尾」（上限句不许把这条毁掉）", !/不许收尾/.test(gate(1700, 3, 3)));
  ok("★ 拆趟时上限按本趟算，不是按全篇算", /1955/.test(gate(1700, 3, 3)), "1700×1.15=1955");
  // 三篇真跑：现在各判什么
  const verdict = (want, got) => got < Math.round(want * 0.9) ? "短" : got > Math.round(want * 1.15) ? "超" : "合格";
  ok("★ 散文 5052/5000 判合格（这一档本来就是准的，别误伤）", verdict(5000, 5052) === "合格");
  ok("★ 论说 4396/3000 判超标（事故当时无人判它超）", verdict(3000, 4396) === "超");
  ok("★ 小说 4620/2400 判超标", verdict(2400, 4620) === "超");
  ok("★ 欠字那两次旧账仍判「短」（下限没被这一刀削掉）",
     verdict(2000, 1724) === "短" && verdict(5000, 2858) === "短");
}

// ── 二、选了体量，规格文案跟着改口 ───────────────────────────
console.log("\n【二、规格文案跟着体量改口】");
const mF = W.match(/function distFitCopy\(SPEC, w\) \{[\s\S]*?\n\}/);
ok("★ 有 distFitCopy", !!mF);
let fit = null;
try {
  fit = new Function("SPEC", "w",
    mF[0].replace(/^function distFitCopy\([^)]*\)\s*\{/, "").replace(/\}$/, ""));
} catch (e) { fit = null; }
ok("distFitCopy 能真跑", !!fit);
if (fit) {
  const S1 = { name: "散文（5000字）", spec: "写成一篇散文，约 5000 字。" };
  fit(S1, 3000);
  ok("★ name 括号里的字数改成了选中的体量", S1.name === "散文（3000字）", S1.name);
  ok("★ spec 追加了覆盖句，且写的是选中的那个数", /本次体量以这一条为准/.test(S1.spec) && /\*\*3000 字\*\*/.test(S1.spec));
  ok("★ 覆盖句明写「别的字数一律作废」", /一律作废/.test(S1.spec));
  ok("★ 覆盖句点名「可到 X 字」这种写死的放宽", /可到 X 字/.test(S1.spec));
  ok("★ 不是同一份内容拉长压缩（短了砍线索、长了加人）", /不是同一份内容拉长或压缩/.test(S1.spec));
  ok("★ spec 原文没被删（只追加，不重写）", /写成一篇散文，约 5000 字。/.test(S1.spec));
  const S2 = { name: "对话报告", spec: "报告" };
  fit(S2, 0);
  ok("★ 没有目标字数的档一个字都不动（报告/提纲/PPT）", S2.name === "对话报告" && S2.spec === "报告");
  const S3 = { name: "学术论文（两万字·投稿体例）", spec: "x" };
  fit(S3, 12000);
  ok("★ 只改括号里带「字」的那个数，不碰「两万字」这种汉字写法（改它会误伤体例名）",
     S3.name === "学术论文（两万字·投稿体例）", S3.name);
  ok("不抛：spec 缺失也能跑", (() => { const s = { name: "x（500字）" }; fit(s, 300); return typeof s.spec === "string"; })());
}
ok("★ 接线在 SPEC.words 之后、fixed 缩放之前",
   /SPEC\.words = _wPick;\s*\n\s*distFitCopy\(SPEC, _wPick\);/.test(W));

// ── 三、story 那句自己放宽 1.67 倍的文案 ─────────────────────
console.log("\n【三、写死在规格里的放宽】");
ok("★ story 的「可到 4000 字」已去掉", !/可到 4000 字/.test(W));
ok("★ 小说档的规格还在（别把整句删没了）", /写成一篇【短篇小说】/.test(W));
// 顺带扫一遍：还有没有别处在规格里写死「可到 N 字」
{
  const hits = [...W.matchAll(/可到 [\d,]+ 字/g)].map((m) => m[0]);
  ok("★ 全文再没有第二处「可到 N 字」式的放宽", hits.length === 0, hits.join("／"));
}

// ── 四、一趟出全篇那条路的预算 ───────────────────────────────
console.log("\n【四、输出预算上下都夹】");
ok("★ 预算不再只升不降（原来是 max(SPEC.tok, …)）",
   !/Math\.max\(SPEC\.tok, Math\.round\(_wPick \* 3\.2\)\)/.test(W));
ok("★ 改成按体量算、地板 8000",
   /SPEC\.tok = Math\.min\(WDS_TOK_MAX, Math\.max\(8000, Math\.round\(_wPick \* 3\.2\)\)\);/.test(W));
{
  const TOKMAX = 64000;
  const budget = (w) => Math.min(TOKMAX, Math.max(8000, Math.round(w * 3.2)));
  ok("★ essay 选 3000 字：预算 9600（旧口径是 32000 ＝ 十倍天花板）", budget(3000) === 9600);
  ok("★ 诗 500 字：地板 8000 兜住，不会被压到写不完", budget(500) === 8000);
  ok("★ 函件 600 字：同样吃地板", budget(600) === 8000);
  ok("★ paper1 选 30000 字：仍被平台上限压在 64000", budget(30000) === 64000);
  ok("★ paper1 选 12000 字：38400，与旧口径同值（不误伤长档）", budget(12000) === 38400);
  ok("★ 每一档预算都不低于目标汉字数本身（不可能写不完）",
     [500, 600, 1200, 2000, 3000, 5000, 12000].every((w) => budget(w) >= w));
}

// ── 五、三处口径没被这一刀带歪 ───────────────────────────────
console.log("\n【五、原有口径仍在】");
ok("目标字数仍从表里取，不从文案里正则抠", /SPEC\.words = _wPick;/.test(W) && !/SPEC\.words = .*match\(/.test(W));
ok("拆趟那条路仍逐趟挂闸", /\+ distWordGate\(want, partIdx \+ 1, secs\.length\)/.test(W));
ok("一趟出全篇那条路仍挂闸", /\+ distWordGate\(SPEC\.words, 1, 1\)/.test(W));
ok("拆趟的接缝仍写着「别复述它」", /只为接得上，别复述它/.test(W));

console.log("\n═══ sim_dist_wordcap: " + PASS + " PASS / " + FAIL + " FAIL ═══");
process.exit(FAIL ? 1 : 0);
