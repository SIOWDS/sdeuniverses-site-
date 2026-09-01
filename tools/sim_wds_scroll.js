/* 只测一件事：流式贴底不许把顶栏／工具条抖出来（2026-09-01 的「屏幕闪烁」）。

   病灶：paint() 每帧整篇重排，重排后的高度**不一定更高**（代码围栏闭合、表格补齐、
   列表重排、光标换行都会让 scrollHeight 当场缩一截），scrollTop 被浏览器夹小，
   于是发出一次「向上滚动」的假动作。顶栏与工具条按滚动方向决定收/现，
   便以帧率一开一合；两条横条都带 .2s 过渡且 .hid 真的不占位 ⇒ 正文上下跳 ⇒ 整屏在闪。
   DeepSeek 出字最快、帧间隔压在 110ms 下限，所以在它身上最明显。

   这条护栏**跑真源码**：把 topOnScroll / toolsOnScroll 两个函数体从 public/wds-mode.js
   里原样取出来 eval，喂一串滚动坐标看它怎么动——不复制平行实现，改坏了它就红。 */
"use strict";
const fs = require("fs");
const SRC = fs.readFileSync(__dirname + "/../public/wds-mode.js", "utf8");
let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };

function body(name) {
  const i = SRC.indexOf("function " + name + "() {");
  if (i < 0) return "";
  let d = 0, j = SRC.indexOf("{", i);
  for (let k = j; k < SRC.length; k++) {
    if (SRC[k] === "{") d++;
    else if (SRC[k] === "}") { d--; if (!d) return SRC.slice(i, k + 1); }
  }
  return "";
}

/* 用真源码建一个可跑的副本：只把它依赖的几个外部名字换成桩。 */
function harness(fnName, setName, lastName) {
  const src = body(fnName);
  if (!src) return null;
  const calls = [];
  const ctx = { y: 0, prog: false, lastY: 0, calls: calls };
  const stub = `
    var bodyEl = { get scrollTop() { return CTX.y; } };
    var ${lastName} = 0;
    function progScrolling() { return CTX.prog; }
    function ${setName}(a, b) { CTX.calls.push(a); }
    ${setName === "toolsSet" ? "var toolsPinned = null;" : ""}
    ${src}
    RUN = function (y, prog) { CTX.y = y; CTX.prog = prog; ${fnName}(); return CTX.calls; };
  `;
  let RUN;
  const CTX = ctx;
  eval(stub);
  return { run: RUN, calls: calls, ctx: ctx };
}

[["topOnScroll", "topSet", "topLastY", true], ["toolsOnScroll", "toolsSet", "toolsLastY", false]].forEach(function (T) {
  const H = harness(T[0], T[1], T[2]);
  console.log("\n[" + T[0] + "] 真跑：喂一串滚动坐标");
  if (!H) { ok(false, "取得到函数体"); return; }
  const SHOW = T[3] ? false : true;    // 顶栏 topSet(false)＝现；工具条 toolsSet(true)＝现
  const HIDE = T[3] ? true : false;

  // ① 正常读答案：一路往下 ⇒ 收（这一条不能被这次修复弄丢）
  H.calls.length = 0;
  H.run(500, false); H.run(560, false);
  ok(H.calls.indexOf(HIDE) >= 0, "往下读就收 —— 屏幕让给答案，老行为保住");

  // ② 病灶复现：程序贴底期间的假上滚 ⇒ **不许现**
  H.calls.length = 0;
  H.run(1000, true);          // 贴底
  H.run(960, true);           // 重排把 scrollTop 夹小：一次假上滚
  H.run(1010, true);          // 下一帧又贴回底
  H.run(965, true);           // 再来一次
  ok(H.calls.indexOf(SHOW) < 0, "⭐ 程序贴底期间的假上滚**一次都没把它抖出来**（这就是闪烁的根）");

  // ③ 读者真的往上翻（不在贴底窗口里）⇒ 照旧要现
  H.calls.length = 0;
  H.run(1000, false); H.run(900, false);
  ok(H.calls.indexOf(SHOW) >= 0, "读者自己往上翻时照旧现 —— 修复没有把出口一起堵死");

  // ④ 到顶必现：即使正在程序贴底
  H.calls.length = 0;
  H.run(600, true); H.run(10, true);
  ok(H.calls.indexOf(SHOW) >= 0, "到顶必现，贴底窗口也压不住它");
});

console.log("\n[三] 贴底那一下要留下时刻，否则上面全是空谈");
ok(/function scrollBottom\(smooth\) \{\s*progScrollAt = Date\.now\(\);/.test(SRC), "scrollBottom 记下程序贴底的时刻");
ok(/function progScrolling\(\) \{ return Date\.now\(\) - progScrollAt < 400; \}/.test(SRC), "窗口 400ms（够盖住平滑滚动，又短到不影响读者真的翻页）");

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
