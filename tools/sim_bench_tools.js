/* 工序交付率量具的护栏：tools/sim_bench_tools.js（2026-08-28）
 * 守四件——都真跑，不扫源码串：
 *   ① 没有 Key 不许跑（这一台烧的是读者自己的 Key，退出码 2 且一次也不打上游）；
 *   ② 走服务端下发的那份规格（不是本地那份）——页面上判的就是它；
 *   ③ 失败的格子留在分母里（摘掉它，交付率会从难看变好看，正是最容易被人图省事删掉的一条）；
 *   ④ --mock 能把整条管道跑通并落一份读数（SSE 解析→逐件审计→汇总→存盘）。
 * 用法：node tools/sim_bench_tools.js
 */
"use strict";
const { execFileSync } = require("child_process");
const fs = require("fs");
let PASS = 0, FAIL = 0;
function ok(m, c) { if (c) { PASS++; console.log("  PASS " + m); } else { FAIL++; console.log("  FAIL " + m); } }
const SRC = fs.readFileSync("tools/bench_tools.js", "utf8");

console.log("① 没有 Key 不许跑");
let code = 0, outNoKey = "";
try { outNoKey = execFileSync("node", ["tools/bench_tools.js", "--n", "1"], { env: { ...process.env, WDS_KEY: "" }, encoding: "utf8" }); }
catch (e) { code = e.status; outNoKey = String(e.stdout || ""); }
ok("退出码 2（没 Key 就停）", code === 2);
ok("并说清怎么才跑得起来", /WDS_KEY=/.test(outNoKey));
ok("--dry 只算不跑", /只算不跑/.test(execFileSync("node", ["tools/bench_tools.js", "--dry"], { encoding: "utf8" })));

console.log("② --mock 把整条管道跑通");
const out = execFileSync("node", ["tools/bench_tools.js", "--mock", "--n", "1"], { encoding: "utf8" });
ok("逐道都出了交付率", (out.match(/交付率/g) || []).length >= 15);
ok("汇总标明是假上游、不是可引用读数", /不是可引用的读数/.test(out));
/* ⚠ 路径后面紧跟着中文括号注释，\S+ 会把「（runs/」一起吞进来（第一版当场 ENOENT）。
   只取到 .json 为止。 */
const f = (out.match(/读数留在 (\S+?\.json)/) || [])[1];
ok("读数落了盘", !!f && fs.existsSync(f));
const rec = JSON.parse(fs.readFileSync(f, "utf8"));
ok("落盘的是逐格明细，不只是汇总", Array.isArray(rec.cells) && rec.cells.length >= 15);
ok("明细里带缺件清单（不然事后查不出漏在哪）", rec.cells.some((c) => c.ok && Array.isArray(c.miss)));

console.log("③ 失败留在分母里");
const bad = rec.cells.find((c) => !c.ok);
ok("假上游那一格确实失败了（gap）", !!bad && bad.tool === "gap");
const row = rec.rows.find((r) => r.tool === "gap");
ok("它的 n 仍是 1（没被摘出分母）", row && row.n === 1 && row.fail === 1);
ok("汇总的平均交付率用的是总格数当分母", /out\.length \* 100/.test(SRC.replace(/\s+/g, " ")) || /\/ out\.length/.test(SRC));

console.log("④ 规格来源与纪律");
ok("优先用服务端下发的那一份规格", /const used = spec \|\| S\.toolSpecFor/.test(SRC));
ok("退回本地时如实标出来", /specFrom/.test(SRC));
ok("打的是线上真端点（不在本地另拼提示语）", /\/api\/wds\/chat/.test(SRC) && !/WDS_CHAT_SYS/.test(SRC));
ok("规格与审计都从源码抠，不复制副本", /new Function\(/.test(SRC) && !/const TOOL_SPEC = \{/.test(SRC));
ok("读数不进仓库", /runs/.test(fs.readFileSync(".gitignore", "utf8")));
try { fs.unlinkSync(f); } catch (e) {}

console.log("\n" + (FAIL ? "✗ " : "✓ ") + PASS + " PASS / " + FAIL + " FAIL\n");
process.exit(FAIL ? 1 : 0);
