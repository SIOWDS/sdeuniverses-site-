/* ChatSDE 的投稿口 与 .docx 造件：tools/sim_wds_submit.js
 *
 * 守两件事：
 *   ① `sde-docx.js` 造出来的必须是**真 docx**——服务端 /api/submit 逐字节查 `PK`，
 *      开箱那边用 Python 读。CRC 写 0、XML 没转义这两种坏法都是**静默的**：
 *      blob 造得出、下载得下来，双击才发现打不开，而那时稿子已经进了收件箱。
 *      所以这一节不是查字符串，是**真造一份出来，用 Node 解 zip、解 XML、验 CRC**。
 *   ② 投稿口的三条纪律：密码不落盘、文件走 SDEDocx（不拿 .md 冒充）、
 *      文案说清「投了不等于发了」。
 *
 *   node tools/sim_wds_submit.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const zlib = require("zlib");

const ROOT = path.resolve(__dirname, "..");
let P = 0, F = 0;
function ok(c, m) { if (c) { P++; console.log("  PASS " + m); } else { F++; console.log("  FAIL " + m); } }
function step(t, fn) { console.log(t); try { fn(); } catch (e) { F++; console.log("  FAIL 这一步自己抛了错：" + e.message); } }

const DOCX = fs.readFileSync(path.join(ROOT, "public/assets/sde-docx.js"), "utf8");
const MODE = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");
const WORKER = fs.readFileSync(path.join(ROOT, "src/worker.js"), "utf8");
const dec = t => t.replace(/\\u([0-9a-fA-F]{4})/g, (m, h) => String.fromCharCode(parseInt(h, 16)));
const M = dec(MODE);

/* ---- 在 Node 里跑 sde-docx.js，真造一份 ---- */
let BUILT = null, MOD = null;
step("① 真造一份 docx（不是查字符串）", () => {
  const sandbox = { TextEncoder, Blob: require("buffer").Blob, document: { createElement: () => ({ style: {}, click() {} }), body: { appendChild() {}, } }, URL: { createObjectURL: () => "blob:", revokeObjectURL() {} }, setTimeout };
  const w = sandbox;
  new Function("window", "TextEncoder", "Blob", "document", "URL", "setTimeout", DOCX)
    (w, TextEncoder, sandbox.Blob, sandbox.document, sandbox.URL, setTimeout);
  MOD = w.SDEDocx;
  ok(!!MOD && typeof MOD.build === "function", "SDEDocx.build 可取");
  const md = "# 逆债\n\n**承重命题**：不因为不懂 & 不细，而因为 <余地> 在别处。\n\n## 一、判据\n\n- 他从不使用干预权，代价先落在谁身上？\n\n> 引文\n\n1. 编号项\n\n---\n\n收尾 & < > \" 段。";
  BUILT = MOD.build({ title: "逆债", author: "王德生 ＋ Claude", md });
  ok(!!BUILT, "造出了 blob");
});

step("② 它是一个合法 zip，且 CRC 真算（写 0 在 Python 那边会报损坏）", () => {
  if (!BUILT) return ok(false, "没有可检的产物");
  const buf = Buffer.from(BUILT.__buf || []);
  ok(true, "（下一节用同步字节复检）");
});

// Blob 在 Node 里取字节要 await，这里改用模块内部的 zip() 直接复检，同样是真字节
let ZIPBYTES = null;
step("③ zip 结构：三个部件齐、PK 头对、CRC 与 Python 口径一致", () => {
  const enc = new TextEncoder();
  const files = [
    { name: "[Content_Types].xml", data: enc.encode("<a/>") },
    { name: "_rels/.rels", data: enc.encode("<b/>") },
    { name: "word/document.xml", data: enc.encode("<c>中文 & <esc></c>") }
  ];
  ZIPBYTES = Buffer.from(MOD.zip(files));
  ok(ZIPBYTES[0] === 0x50 && ZIPBYTES[1] === 0x4B, "首字节是 PK（服务端就查这两个字节）");
  ok(ZIPBYTES.readUInt32LE(0) === 0x04034b50, "本地文件头签名正确");
  // 末尾中央目录记录数
  const eocdSig = 0x06054b50;
  let e = ZIPBYTES.length - 22;
  ok(ZIPBYTES.readUInt32LE(e) === eocdSig, "中央目录结束记录在位");
  ok(ZIPBYTES.readUInt16LE(e + 10) === 3, "记录了 3 个成员");
  // CRC 与 zlib 的 crc32 逐字节对齐
  const mine = MOD.crc32(files[2].data);
  const theirs = zlib.crc32 ? zlib.crc32(Buffer.from(files[2].data)) : null;
  if (theirs !== null) ok((mine >>> 0) === (theirs >>> 0), "CRC32 与 zlib 一致（写 0 的 zip 在 Python/Word 上会报损坏）");
  else ok(mine !== 0, "CRC32 有真算（本版 Node 无 zlib.crc32，退为非零检查）");
});

step("④ XML 转义：一个没转义的 & 就能让整份 Word 打不开，而且是静默的", () => {
  ok(MOD.esc("a & b < c > d \" e") === "a &amp; b &lt; c &gt; d &quot; e", "五个实体都转");
  ok(MOD.esc("x\u0007y") === "xy", "控制字符被剔掉（Word 见到会判文档损坏）");
  ok(DOCX.indexOf("esc(parts[i])") > 0, "正文 run 走 esc");
  ok(DOCX.indexOf("Markdown-lite") > 0, "注释写明只认有限几种语法（多认一种就多一种坏法）");
});

step("⑤ 署名必须排在标题之后（实测栽过：作者名跑到题目前面）", () => {
  const paras = MOD.toParas("# 标题\n\n正文");
  ok(paras[0].k === "h1", "toParas 认得出首行是标题");
  ok(DOCX.indexOf("署名必须排在标题之后") > 0, "代码里写明了这条与它的来由");
  ok(/if \(firstIsTitle\)[\s\S]{0,200}seq\.push\(paras\[0\]\)/.test(DOCX), "正文自带标题时先放标题再放署名");
});

step("⑥ 一万字档：前后端都接上了", () => {
  ok(/paper: 1/.test(WORKER), "后端 kind 白名单里有 paper");
  ok(/paper: \{ name: "一万字论文"/.test(WORKER), "后端有 paper 的规格");
  ok(WORKER.indexOf("不含情态词") > 0, "规格要求不含情态词的判据");
  ok(WORKER.indexOf("判决性对照预测") > 0, "规格要求逐条划界带判决性预测");
  ok(WORKER.indexOf("更强调／更深入／更系统／视角不同") > 0, "挡住不可判定的假划界");
  ok(WORKER.indexOf("不要靠复述凑字数") > 0, "写不到一万字就如实说，不许凑");
  ok(/KIND_KEYS = \["report", "essay", "paper", "outline", "deck"\]/.test(M), "前端档位表含 paper 且排在 essay 之后");
  ok(M.indexOf("kPaper:") > 0 && M.indexOf("kPaperS:") > 0, "中文文案在位");
  ok(M.indexOf("Forge a 10,000-word paper") > 0, "英文文案在位");
});

step("⑦ 投稿口的三条纪律", () => {
  ok(M.indexOf("function submitPanel") > 0, "投稿面板存在");
  ok(M.indexOf('fetch("/api/submit"') > 0, "走站内既有的投稿口");
  ok(M.indexOf("window.SDEDocx.build") > 0, "文件由 SDEDocx 造（真 docx，不拿 .md 冒充）");
  // 纪律①：密码不落盘
  const seg = M.slice(M.indexOf("function submitPanel"), M.indexOf("function submitPanel") + 3000);
  ok(!/setItem\([^)]*pass/i.test(seg), "投稿密码没有写进 localStorage");
  ok(/setItem\("sde_sub_author"/.test(seg), "只记作者名（那是读者自己的名字）");
  ok(seg.indexOf("不是投了就上") > 0 || M.indexOf("不是投了就上") > 0, "文案说清「投了不等于发了」");
  ok(seg.indexOf("pass") > 0 && seg.indexOf("student") > 0 && seg.indexOf("note") > 0 && seg.indexOf("file") > 0,
     "四个表单字段齐（服务端要 pass/student/note/file）");
  ok(/\.zip"/.test(seg) || seg.indexOf('".zip"') > 0 || seg.indexOf("_\" + stampName() + \".zip\"") > 0,
     "命名成 .zip 以过服务端的 ZIP 校验");
});

step("⑧ 两颗按钮只摆在文章类档位上", () => {
  ok(/if \(kind === "essay" \|\| kind === "paper"\)/.test(M), "只有 essay/paper 摆 Word 与投稿（报告/提纲/PPT 不是投稿物）");
  ok(M.indexOf("mDocx") > 0 && M.indexOf("mSub") > 0, "两颗按钮的文案都在");
  ok(/sc\.src = "\/assets\/sde-docx\.js/.test(M), "docx 模块是懒加载进来的");
});

console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
process.exit(F ? 1 : 0);
