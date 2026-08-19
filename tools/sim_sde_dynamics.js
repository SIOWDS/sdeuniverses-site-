/* SDE 动力智能体（三原理二阶碰撞）的护栏
 *
 * 守三件：
 *   ① 三条动力的配置不许走样——它们必须恰好是 D×E→S / S×E→D / S×D→E 三条，
 *      每一条都锁死"只承认自己是驱动"，否则这台就退回成又一台三视角机器。
 *   ② 五步链完整，且第四步（证伪报告）是终点——这台的产物是一组会让原主张翻车的
 *      观测，不是答案。链断一环，产物就变回综述。
 *   ③ 八家基底的管道与中华智问逐字一致——两边是复制关系，复制就会漂移，
 *      这条断言让漂移当场暴露。哪天在 zhiwen 修了基底 bug 而这边没同步，这里会红。
 *
 *   node tools/sim_sde_dynamics.js
 */
"use strict";
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const PAGE = process.env.DYN_HTML || path.join(ROOT, "public/taste/sde-dynamics/index.html");
const ZHIWEN = path.join(ROOT, "public/taste/zhiwen/index.html");

let P = 0, F = 0;
function ok(c, m) { if (c) { P++; console.log("  PASS " + m); } else { F++; console.log("  FAIL " + m); } }
function step(t, fn) { console.log(t); try { fn(); } catch (e) { F++; console.log("  FAIL 这一步自己抛了错：" + e.message); } }

const h = fs.readFileSync(PAGE, "utf8");
const z = fs.readFileSync(ZHIWEN, "utf8");

function grabFn(src, name) {
  for (const pre of ["async function ", "function "]) {
    const i = src.indexOf(pre + name + "(");
    if (i < 0) continue;
    let d = 0, started = false;
    for (let k = i; k < src.length; k++) {
      if (src[k] === "{") { d++; started = true; }
      else if (src[k] === "}") { d--; if (started && d === 0) return src.slice(i, k + 1); }
    }
  }
  return null;
}

step("① 页面骨架与元素", () => {
  ok(h.length > 30000, "页面不为空且不像被截断（" + h.length + " 字符）");
  ["question", "apiKey", "modelSel", "goBtn", "stopBtn", "steps", "hint", "errBox", "dlBtn", "copyBtn"]
    .forEach(id => ok(h.indexOf('id="' + id + '"') > 0, "元素在位：#" + id));
  ok(/<meta name="description" content="[^"]{60,}"/.test(h), "description 齐备");
});

step("② 三条动力：恰好三条，且各锁一个被驱动项", () => {
  const cfg = h.slice(h.indexOf("const DYN_CFG"), h.indexOf("function dynLaneSys"));
  ok(cfg.indexOf("P1") > 0 && cfg.indexOf("P2") > 0 && cfg.indexOf("P3") > 0, "三条动力泳道齐");
  ok(/drive:'路径 × 土壤'[\s\S]{0,40}target:'显露'/.test(cfg), "动力一：路径×土壤 → 显露");
  ok(/drive:'显露 × 土壤'[\s\S]{0,40}target:'路径'/.test(cfg), "动力二：显露×土壤 → 路径");
  ok(/drive:'显露 × 路径'[\s\S]{0,60}target:'土壤'/.test(cfg), "动力三：显露×路径 → 土壤");
  ok((cfg.match(/target:/g) || []).length === 3, "恰好三个被驱动项，不多不少");
  const tg = (cfg.match(/target:'(.)/g) || []);
  ok(new Set(tg).size === 3, "三个被驱动项互不相同");
});

step("③ 单因主张锁死（这一条一松，本台就退回三视角机器）", () => {
  const sys = grabFn(h, "dynLaneSys");
  ok(!!sys, "dynLaneSys 存在");
  if (sys) {
    ok(sys.indexOf("只承认一条动力") > 0, "只承认自己那一条是驱动");
    ok(sys.indexOf("决定性") > 0, "必须主张自己是决定性的");
    ok(sys.indexOf("被驱动的结果") > 0, "另两条只是被驱动的结果");
    ok(sys.indexOf("其中一个因素") > 0 && sys.indexOf("严禁") > 0, "严禁写成「只是其中一个因素」");
    ok(sys.indexOf("时序读数") > 0, "每段必须带时序读数");
    ok(sys.indexOf("本台自己撑不住的地方") > 0, "必须留自曝一节（后面碰撞要用它当推翻材料）");
    ok(sys.indexOf("写\"暂无\"就是没做") > 0 || sys.indexOf("写“暂无”就是没做") > 0, "自曝不许写暂无");
  }
});

step("④ 五步链完整，且证伪报告是终点", () => {
  ["dynClaimPrompt", "dynLaneUser", "dynPremisePrompt", "dynCollidePrompt", "dynFalsifyPrompt"]
    .forEach(n => ok(!!grabFn(h, n), "提示词函数在位：" + n));
  const run = grabFn(h, "run");
  ok(!!run, "run 存在");
  if (run) {
    const order = ["dynClaimPrompt", "dynLaneUser", "dynPremisePrompt", "dynCollidePrompt", "dynFalsifyPrompt"]
      .map(n => run.indexOf(n));
    ok(order.every(x => x > 0), "五步都被 run 调用");
    ok(order.every((x, i) => i === 0 || x > order[i - 1]), "五步调用顺序正确（不可换序）");
    ok(run.indexOf("classList.add('final')") > 0, "证伪报告那一步被标为终点");
    ok(run.indexOf("okN < 2") > 0, "三条动力里少于两条成功就中止（撞不起来就别硬撞）");
  }
});

step("⑤ 共有前提与推翻材料的两条硬纪律", () => {
  const pre = grabFn(h, "dynPremisePrompt");
  ok(!!pre, "dynPremisePrompt 存在");
  if (pre) {
    ok(pre.indexOf("驱动的方向是固定的") > 0, "本型的共有前提形状（驱动方向固定）已写死");
    ok(pre.indexOf("这还用说吗") > 0, "共有前提的验收句");
    ok(pre.indexOf("跳起来反对") > 0, "有人反对＝第四种立场，重写");
    ok(pre.indexOf("必须来自 A/B/C 之一自己") > 0, "推翻材料必须来自三台之一自己");
    ok(pre.indexOf("一律不算数") > 0, "外搬理由不算数");
    ok(pre.indexOf("原样引出") > 0, "要求原样引出，不许转述");
    ok(pre.indexOf("未找到") > 0, "找不到就如实写，不许编");
  }
});

step("⑥ 证伪报告的六节与它的硬要求", () => {
  const f = grabFn(h, "dynFalsifyPrompt");
  ok(!!f, "dynFalsifyPrompt 存在");
  if (f) {
    ok(f.indexOf("不是答案") > 0, "明写产物不是答案");
    ok(f.indexOf("明天该去看什么") > 0, "读者标准：明天去看什么");
    ok(f.indexOf("它成立的条件") > 0, "第二节：原主张成立的条件（永远对的主张没用）");
    ok(f.indexOf("至少四条") > 0, "第三节：至少四条会让它翻车的观测");
    ok(f.indexOf("今天就能查") > 0, "至少一条今天就能查");
    ok(f.indexOf("应当") > 0 && f.indexOf("不许用") > 0, "读数里不许用情态词");
    ok(f.indexOf("早于") > 0, "第四节：顺序预测（A 的变化早于 B）");
    ok(f.indexOf("翻转条件") > 0, "第五节：翻转条件");
    ok(f.indexOf("反噬") > 0, "第六节：反噬");
    ok(f.indexOf("只能被议论") > 0, "四条观测全做不到时如实说这议题还不能被证伪");
  }
});

step("⑦ 去母体化：对读者的页面与提示词都不许露内部术语", () => {
  const bad = ["三视角", "显露态", "差异序列", "特征纠缠", "三大方程", "123原理", "二阶碰撞", "提智"];
  // 只查会被送进基底或显示给读者的地方：DYN_DISCIPLINE 是拦截清单本身，允许出现
  const disc = h.slice(h.indexOf("const DYN_DISCIPLINE"), h.indexOf("const DYN_CFG"));
  ok(disc.indexOf("不得出现任何内部术语") > 0, "纪律串在位");
  bad.forEach(w => ok(disc.indexOf(w) > 0, "拦截清单里列了：" + w));
  // 页面可见文案（去掉 script）里不许出现
  const visible = h.replace(/<script[\s\S]*?<\/script>/g, " ");
  const leak = bad.filter(w => visible.indexOf(w) >= 0);
  ok(leak.length === 0, "读者可见文案零内部术语" + (leak.length ? "，残留：" + leak.join("、") : ""));
});

step("⑧ 八家基底管道与中华智问逐字一致（复制就会漂移，这条让漂移当场暴露）", () => {
  const FNS = ["parseModel", "apiUrl", "isOverseas", "chatHeaders", "buildPayload",
               "parseResponse", "extractFull", "streamChat", "loadAsset", "vendorName", "keyStoreName"];
  let same = 0, diff = [];
  FNS.forEach(n => {
    const a = grabFn(h, n), b = grabFn(z, n);
    if (a && b && a === b) same++;
    else diff.push(n + (a ? (b ? "(内容不同)" : "(zhiwen 里没有)") : "(本页没有)"));
  });
  ok(diff.length === 0, "管道 " + same + "/" + FNS.length + " 条与 zhiwen 完全一致"
     + (diff.length ? "；不一致：" + diff.join(" / ") + " —— 两边要一起改" : ""));
  ok(h.indexOf("逐字复制") > 0, "页面里写明了这一段是逐字复制及其理由");
});

step("⑨ Key 检测与真跑共用同一套函数", () => {
  ok(h.indexOf("SDEKeyProbe.attach") > 0, "接了共享 Key 检测模块");
  ok(/buildPayload: buildPayload/.test(h) && /chatHeaders: chatHeaders/.test(h), "探测与真跑共用 buildPayload/chatHeaders");
  ok(h.indexOf("装不上也绝不能影响") > 0, "检测装不上不影响正常跑");
  ok((h.match(/x-target-url/g) || []).length === 4, "x-target-url 恰好 4 处且都在 chatHeaders 里");
});

step("⑩ 已挂到首页", () => {
  const idx = fs.readFileSync(path.join(ROOT, "public/index.html"), "utf8");
  ok(idx.indexOf("/taste/sde-dynamics/") > 0, "首页智能体条里有本台");
  ok(idx.indexOf("SDE动力智能体") > 0, "中文名在位");
});

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
