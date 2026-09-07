/* sim_wds_skin.js —— 「面板跟着换肤、里面的输入框不跟」这一类隐形的护栏
 *
 * 2026-09-07 王德生报的毛病：ChatSDE「成文 · PPT」里那个输入「写作主题」的框**看不见**。
 * 病根不在渲染、不在布局，而在**一半走变量、一半写死**：
 *   外层 .wdsm-tplb 的底色是 var(--wpanel)，浅色皮肤（html.wdsm-lt）下它是 #FFFDF8；
 *   而 scopeMenu 里那个 textarea 的内联样式写死着深色皮肤那一套——
 *   底 rgba(255,255,255,.06)、框 rgba(255,255,255,.15)、字 #F5EFE0。
 *   白底上铺一层白、描一道白框、写一行米白字 ⇒ 输入框连同提示语一起隐形。
 * **深色皮肤下一切正常，所以谁都没发现；只有换到浅色皮肤（或系统跟随浅色）的读者撞得上。**
 * 构建是绿的、node --check 是绿的、所有别的 sim 也是绿的——这条链上原来没有检查点，本文件就是。
 *
 * 查两件：
 *   ① 四个已知落点（成文的主题框／装书面板输入框／投稿面板抬头与外框）逐个走 var(--…)；
 *   ② 通扫：**内联样式**（cssText = / style=' / style="）里不许再出现写死的浅色字色
 *      与 rgba(255,255,255,…) 底/框——唯一豁免是 wdsKeyPanel（设置面板），
 *      它自带一整块写死的深底 #161B22，是自洽的一套，不受换肤影响。
 *      注意只扫内联样式那些行：CSS 变量表本身（:root{…} / html.wdsm-lt{…}）与
 *      各 CSS_ 字符串块里当然要写真颜色，那是**定义**不是**写死**。
 *   并对每条做变异测试：把病重新种回去，护栏必须当场变红。
 *
 * 跑法：node tools/sim_wds_skin.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");
const JS = path.join(ROOT, "public/wds-mode.js");
let pass = 0, fail = 0;
const ok = (n, c) => { if (c) { pass++; console.log("  ✓ " + n); } else { fail++; console.log("  ✗ " + n); } };

if (!fs.existsSync(JS)) { console.log("✗ 找不到 public/wds-mode.js"); process.exit(1); }
const src = fs.readFileSync(JS, "utf8");

/* ── 通扫器：给一份源码，回一张「内联样式里写死皮肤色」的清单 ── */
function hardcodedSkinColors(text) {
  /* 设置面板自带写死的深底，是自洽的一整套，整段豁免。
     边界取「下一个顶层 function」而不是花括号配平——这份文件里内联样式带花括号的字符串太多。 */
  const s = text.indexOf("function wdsKeyPanel(");
  let exFrom = -1, exTo = -1;
  if (s >= 0) {
    exFrom = s;
    const nxt = text.indexOf("\n  function ", s + 10);
    exTo = nxt < 0 ? text.length : nxt;
  }
  const LIGHT_TEXT = /color:\s*#(?:[EFef][0-9A-Fa-f]|[Dd][89A-Fa-f])[0-9A-Fa-f]{4}\b/;  // 浅到能在白底上隐形的字色
  const WHITE_WASH = /rgba\(\s*255\s*,\s*255\s*,\s*255\s*,/;                            // 白底/白框
  /* 抓的是**内联样式串本身**，不是「含 cssText 那一行」——写死值常常落在续行上
     （`x.style.cssText = "……" + "……"`），按行过滤会整片漏掉。三种写法都收：
       ① x.style.cssText = "…" + "…"    ② HTML 串里的 style='…'    ③ var IN = "…" 这个复用样式串的惯例 */
  const REGIONS = [
    /\.style\.cssText\s*=\s*(?:(?:"[^"]*"|'[^']*')\s*\+?\s*)+/g,
    /style\s*=\s*'[^']*'/g,
    /\bvar\s+IN\s*=\s*"[^"]*"/g,
  ];
  const lineAt = (i) => text.slice(0, i).split("\n").length;
  const hits = [];
  REGIONS.forEach(function (re) {
    re.lastIndex = 0;
    let m;
    while ((m = re.exec(text))) {
      const at = m.index;
      if (at >= exFrom && at < exTo) continue;              // 设置面板豁免
      if (LIGHT_TEXT.test(m[0]) || WHITE_WASH.test(m[0])) {
        hits.push({ line: lineAt(at), text: m[0].replace(/\s+/g, " ").trim().slice(0, 110) });
      }
    }
  });
  hits.sort((a, b) => a.line - b.line);
  return hits;
}

/* ── ① 四个已知落点 ── */
const spots = [
  ["成文·PPT 的「写作主题」输入框走变量（不再写死深色）",
    /ta\.style\.cssText[\s\S]{0,240}?background:var\(--wfill\);border:1px solid var\(--wline2\);color:var\(--wtx2\)/],
  ["装书面板的输入框底与框走变量",
    /var IN = "box-sizing:border-box;background:var\(--wfill\);border:1px solid var\(--wline2\)/],
  ["投稿面板抬头字色走变量",
    /font-weight:600;color:var\(--wtx\);margin-bottom:4px/],
  ["投稿面板外框与底走变量",
    /pan\.style\.cssText = "[^"]*border:1px solid var\(--wline\);[^"]*background:var\(--wfill\)"/],
];
spots.forEach(function (x) { ok(x[0], x[1].test(src)); });

/* 反面：这四处不许再留写死值 */
ok("「写作主题」那一行不再出现 #F5EFE0",
  !/ta\.style\.cssText[\s\S]{0,240}?#F5EFE0/.test(src));

/* ── ② 通扫 ── */
const hits = hardcodedSkinColors(src);
ok("内联样式里没有写死的皮肤色（设置面板豁免）—— 命中 " + hits.length + " 处"
  + (hits.length ? "：\n      " + hits.map(h => h.line + ": " + h.text).join("\n      ") : ""), hits.length === 0);

/* 豁免不是漏网：设置面板确实还写死着，扫描器认得出它、只是放它过去 */
ok("设置面板仍是自洽的一整套写死深色（豁免有实物，不是空豁免）",
  /background:#161B22/.test(src) && /color:#F5EFE0/.test(src));

/* ── 变异测试：病种回去，护栏必须红 ── */
const mutations = [
  ["主题框改回写死米白字",
    src.replace("background:var(--wfill);border:1px solid var(--wline2);color:var(--wtx2);font:14px/1.6 inherit",
      "background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.15);color:#F5EFE0;font:14px/1.6 inherit")],
  ["装书面板输入框改回写死白底白框",
    src.replace('var IN = "box-sizing:border-box;background:var(--wfill);border:1px solid var(--wline2)',
      'var IN = "box-sizing:border-box;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.15)')],
  ["投稿面板抬头改回 #E6EDF3",
    src.replace("font-weight:600;color:var(--wtx);margin-bottom:4px", "font-weight:600;color:#E6EDF3;margin-bottom:4px")],
  ["新面板里塞一行写死的浅色字",
    src.replace("  function tplMenu() {",
      "  function tplMenuX() { var z = document.createElement('div'); z.style.cssText = 'color:#EEE8DA'; return z; }\n  function tplMenu() {")],
];
mutations.forEach(function (m) {
  const changed = m[1] !== src;
  const caught = hardcodedSkinColors(m[1]).length > 0;
  ok("变异「" + m[0] + "」被抓住", changed && caught);
});

console.log("\n" + (fail ? "✗ " : "✓ ") + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
