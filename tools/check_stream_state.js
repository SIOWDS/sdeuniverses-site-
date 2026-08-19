// 流内状态变量体检：每个 `async start(controller)` 块里，凡是用到的 _st / _hb 这类每流私有变量，
// 必须在本块内 let/const 声明。file 级别的 grep 查不出这种错（别的块里声明过、名字就"存在"了），
// node --check 也查不出（语法合法），但 ESM 严格模式下运行时会当场抛 ReferenceError——
// 2026-07-21 就是这么把答题与首页问答两条路由同时打死的。
const fs = require("fs");
const src = fs.readFileSync(process.argv[2] || "src/worker.js", "utf8");
const marker = "async start(controller)";
const bad = [];
let i = -1;
while ((i = src.indexOf(marker, i + 1)) >= 0) {
  // 取到下一个 start( 之前，作为这一块的近似范围
  const next = src.indexOf(marker, i + 1);
  const chunk = src.slice(i, next < 0 ? src.length : next);
  const line = src.slice(0, i).split("\n").length;
  for (const v of ["_st", "_hb"]) {
    if (!new RegExp("\\b" + v + "\\b").test(chunk)) continue;
    const declared = new RegExp("(?:let|const|var)[^;\\n]*\\b" + v + "\\b").test(chunk);
    if (!declared) bad.push({ v, line });
  }
}
if (bad.length) {
  console.log("发现未在本流内声明的状态变量（严格模式会抛 ReferenceError）：");
  bad.forEach((b) => console.log("  第 " + b.line + " 行起的 start(controller) 块：" + b.v));
  process.exit(1);
}
console.log("PASS 每条流的状态变量都在本流内声明（共 " + (src.split(marker).length - 1) + " 条流）");
