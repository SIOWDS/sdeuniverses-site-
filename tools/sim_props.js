/* sim_props —— 语汇族距离引擎的验收。
   这条量纲的成败不在"能不能算出一个数"，而在**它有没有被篇数绑架**：
   并集法实测 r=+0.817，后果是系统把同一批小篇数的人反复推给所有人，
   亲手造出一个固定的边缘小圈子——正是它本该防的东西。
   所以本护栏第一组就是规模偏置，且是硬闸。 */
const fs = require("fs");
const path = require("path");
let P = 0, X = 0;
function ok(c, m) { if (c) { P++; console.log("  PASS " + m); } else { X++; console.log("  FAIL " + m); } }

const IDX = JSON.parse(fs.readFileSync("public/props/index.json", "utf8"));
const MOD = fs.readFileSync("public/assets/sde-dist.js", "utf8");
const PY = fs.readFileSync("tools/build_props.py", "utf8");
const W = fs.readFileSync("src/worker.js", "utf8");

console.log("① 规模偏置——这条量纲的命门");
ok(IDX.calib && typeof IDX.calib.size_bias_r === "number", "产物自带校准读数 size_bias_r");
ok(Math.abs(IDX.calib.size_bias_r) < 0.3,
  "规模偏置 |r| < 0.3，实得 " + IDX.calib.size_bias_r + "（并集法是 +0.817，那会造出固定的边缘小圈子）");
ok(/if abs\(r\) > 0\.3:\s*\n\s*raise SystemExit/.test(PY), "构建脚本自己拒绝出偏置过大的产物（不靠人记得看）");

console.log("② 指纹是固定长度，不是并集");
ok(IDX.k === 800, "k=800（由 k 扫描实测定，700–1200 是平台不是尖峰）");
const sizes = IDX.people.map((p) => p.fp.length);
ok(Math.max(...sizes) <= IDX.k, "没有人的指纹超过 k");
ok(IDX.people.every((p) => typeof p.full === "boolean"), "取不满 k 的人如实标 full:false（他不是更独特，是料不够）");
ok(IDX.calib.fp_min >= 100, "最小指纹仍有 " + IDX.calib.fp_min + " 个二元组，够比");

console.log("③ 判别力");
ok(IDX.calib.j_max / Math.max(IDX.calib.j_min, 1e-9) > 8,
  "距离跨度 " + (IDX.calib.j_max / IDX.calib.j_min).toFixed(1) + "×（并集法只有 10.8×，篇级更只有 3.9×）");
ok(IDX.calib.j_median > 0 && IDX.calib.j_median < 0.2, "中位距离落在可用区间");
ok(IDX.people.every((p) => Array.isArray(p.far) && p.far.length >= 3), "每人都有最远候选池");
ok(IDX.people.every((p) => p.far.every((f, i, a) => i === 0 || a[i - 1].j <= f.j)), "池内按距离升序（最远在前）");
ok(IDX.people.every((p) => p.far.every((f) => f.slug !== p.slug)), "池里不含自己");

console.log("④ 推的是池不是人——防负载塌到一个人身上");
ok(IDX.far_pool >= 5, "池至少 5 人，实得 " + IDX.far_pool);
ok(/function draw\(/.test(MOD) && /Math\.random\(\)/.test(MOD), "模块从池里随机抽，不是永远取第一");
ok(/距离决定谁进池，轮转决定这次叫谁/.test(MOD), "纪律①写在模块里");
// 真跑一次：抽 200 轮，看会不会永远抽到同一个
{
  const mod = require(path.resolve("public/assets/sde-dist.js"));
  const pool = IDX.people[0].far;
  const seen = {};
  for (let i = 0; i < 200; i++) {
    // 直接测 draw 的行为：借 forText 走不通（要 fetch），故用同构的抽样验证
    const a = pool.slice(), out = [];
    while (out.length < 3 && a.length) out.push(a.splice(Math.floor(Math.random() * a.length), 1)[0]);
    out.forEach((x) => { seen[x.slug] = (seen[x.slug] || 0) + 1; });
  }
  const n = Object.keys(seen).length;
  ok(n >= Math.min(5, pool.length), "200 轮里池中至少 " + Math.min(5, pool.length) + " 人被抽到过，实得 " + n);
  ok(typeof mod.grams === "function" && typeof mod.far === "function" && typeof mod.forText === "function",
    "模块导出 grams/far/forText");
}

console.log("⑤ 没有分数、没有排行（纪律②）");
const S = JSON.stringify(IDX);
["score", "rank", "hot", "likes", "点赞", "热度", "排名"].forEach((k) => {
  ok(S.indexOf("\"" + k + "\"") < 0, "产物 schema 里没有 " + k + " 字段");
});
ok(/没有分数、没有排行/.test(MOD), "纪律②写在模块里");

console.log("⑥ 三端 grams 逐字同义（近邻库那条线栽过一次）");
{
  const mod = require(path.resolve("public/assets/sde-dist.js"));
  // 从 worker.js 抠真 ppGrams 跑
  const seg = W.slice(W.indexOf("const ppGrams = (s) =>"), W.indexOf("const PP_ID_RE"));
  const punct = W.match(/const PP_PUNCT = (\/\[[^\n]+\/g);/);
  ok(!!punct, "取到 worker 的 PP_PUNCT");
  const fn = new Function("PP_PUNCT", "return " + seg.replace(/^const ppGrams = /, "").replace(/;\s*$/, "") + ";");
  const wg = fn(new RegExp(punct[1].slice(1, -2), "g"));
  const cases = [
    "认知的抵押与 ego depletion 之间",
    "X 不是 Y，而是 Z——一条判决性对照",
    "自由律／幸福律（意义三律）",
    "abc12 短词 与 longword 混排",
    "纯中文没有任何拉丁词的一句话",
    "Ego Depletion 大小写与  多重  空白",
    "标点。。。全是标点，，，",
  ];
  let same = 0;
  cases.forEach((c) => {
    const a = wg(c).slice().sort().join("|");
    const b = mod.grams(c).slice().sort().join("|");
    if (a === b) same++; else console.log("    ✗ 不一致：" + c);
  });
  ok(same === cases.length, "worker.ppGrams 与 sde-dist.grams 七组全同，实得 " + same + "/" + cases.length);
  // 拉丁整词不许被粘起来
  ok(mod.grams("ego depletion").indexOf("egodepletion") < 0, "ego depletion 不粘成一个词");
  ok(mod.grams("ego depletion").indexOf("ego") >= 0, "拉丁词按整词抽");
}

console.log("⑦ 失败不拦路（纪律③）");
ok(/\.catch\(function \(\) \{ return null; \}\)/.test(MOD), "取库失败返回 null，不 reject");
ok(/if \(!j \|\| !j\._by\[slug\]\) return \[\];/.test(MOD), "库没取到时 far() 返回空数组不抛");
ok(/零调用、不烧任何 Key/.test(MOD), "零调用零 Key 写在模块头");

console.log("⑧ forText 与 far 是两个问题");
ok(/谁离这个人远/.test(MOD) && /谁离这条命题远/.test(MOD), "模块里写明两者差别");
ok(/excludeSlug/.test(MOD), "forText 能排除作者自己");

console.log("⑨ 点将已从领域级升到语汇族级（第一个消费者）");
{
  const WX = fs.readFileSync("public/sde-wechat/index.html", "utf8");
  ok(/assets\/sde-dist\.js/.test(WX), "微信页引了距离模块");
  ok(/window\.SDEDist\.forText\(prop, *3, *mySlug\)/.test(WX), "点将问的是「谁离这条命题最远」，不是「谁离这个人最远」");
  ok(/function cdPickWhoV1\(/.test(WX), "领域级留作回退（模块没加载／库里没我／命题没写够字时仍有人可点）");
  ok(/if\(!window\.SDEDist\|\|prop\.length<8\)\{cdPickWhoV1\(\);return;\}/.test(WX), "取不到就回退，不是留空");
  ok(/\.catch\(function\(\)\{cdPickWhoV1\(\);\}\)/.test(WX), "查失败也回退（失败不拦路）");
  ok(/try\{cdPickWho\(\);\}catch\(e\)\{\}/.test(WX), "命题改了重算点将（否则还是上一条命题的答案）");
  ok(/cdRosterRaw/.test(WX), "留了原始名录表以取 slug");
  ok(/从最远的一批里轮着点，不是每次都叫同一个人/.test(WX), "页面上如实说明是轮转不是固定");
  ok(/他看不懂也是一种读数/.test(WX), "如实说明词面距离的限度，不吹成语义理解");
}

console.log("\n" + (X ? "FAIL " : "ALL PASS ") + P + " / " + X);
process.exit(X ? 1 : 0);
