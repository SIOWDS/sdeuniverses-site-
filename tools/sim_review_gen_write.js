/* review-gen write 分支单元测试（2026-09-05）：从 src/worker.js 现场抽出 REVIEW_* 常量、packCards/refsList/cardDim 与 write 分支，
   对三型×12 节各跑一遍——验：每节输入 ≤62000 字；第 3–5 节只喂本维的卡（≤25 张）；residue 带进；OpenRouter 免费型号 ≤30000 字。
   用法：node tools/sim_review_gen_write.js */
const fs = require("fs"), path = require("path");
const s = fs.readFileSync(path.join(__dirname, "../src/worker.js"), "utf8");
const cut = (a, b, fromEnd) => { const i = s.indexOf(a); const j = s.indexOf(b, i); if (i < 0 || j < 0) throw new Error("anchor missing: " + a.slice(0, 30)); return s.slice(fromEnd ? i + a.length : i, j); };
const consts = cut("const REVIEW_CARD_FIELDS = {", "function reviewFieldTable(type)");
const helpers = cut("      const packCards = (cards, n) => {", '      let sys = "", usr = "", tok = 0;');
const wr = cut('      } else if (rmode === "write") {', '      } else {\n        return J({ ok: false, msg: "bad mode" }, 400);', true);
const src = consts + '\nconst REVIEW_SDEM="", REVIEW_STYLE="";\nfunction reviewFieldTable(){return "";}\n' +
  'function run(b,type,VC){ const clean=(x,n)=>String(x||"").slice(0,n); const J=(o)=>({err:o}); const HEAD="H\\n"; const deep=true;\n' + helpers + '\n let sys="",usr="",tok=0; {\n' + wr + '\n } return {sys,usr,tok}; }\n module.exports=run;';
const run = eval("(function(){" + src + " return run; })()");
function mk(type) { const c = []; for (let i = 1; i <= 70; i++) { const d = i % 3; const f = type === "how" ? "起手维：" + "SDE"[d] : type === "what" ? "所站方程：" + ["S=F(D,E)", "D=G(S,E)", "E=H(S,D)"][d] : "所站原理：" + ["原理一", "原理二", "原理三"][d]; c.push({ i, title: "P" + i, card: "承重命题：x\n" + f + "\n落点维：D\n所走路径：S→E→D\n" + "y".repeat(900) }); } return c; }
const art = { frame: "f".repeat(3000), map: "m".repeat(12000), verdict: "v".repeat(8000), surface: "s".repeat(4000), challenges: "c".repeat(12000), gaps: "g".repeat(8000), collide: "k".repeat(9000), collideRun: "r".repeat(5000), conjectures: "j".repeat(12000), occupants: "o".repeat(6000), territory: "t".repeat(10000), territoryCheck: "q".repeat(5000) };
const refs = []; for (let i = 1; i <= 70; i++) refs.push("Author. 2000. Title " + i + ". Venue. doi:10.1/" + i);
let fail = 0, maxLen = 0;
for (const type of ["how", "what", "why"]) for (let sec = 0; sec < 12; sec++) {
  const r = run({ sec, art, cards: mk(type), refs, prev: "p".repeat(5000), rename: { terms: [{ sde: "显露", disc: "显示" }], sections: {} }, residue: "显露×4" }, type, { url: "https://api.deepseek.com/v1", model: "deepseek-v4-pro", name: "DS" });
  if (r.err) { console.log("  ✗ ERR", type, sec, JSON.stringify(r.err)); fail++; continue; }
  const len = r.usr.length; maxLen = Math.max(maxLen, len);
  const nCards = (r.usr.match(/］《P/g) || []).length;
  if (len > 62000) { console.log("  ✗ 超预算", type, sec, len); fail++; }
  if (sec >= 2 && sec <= 4 && !(/本节涉及的解构卡/.test(r.usr) && nCards > 0 && nCards <= 25)) { console.log("  ✗ 筛卡", type, sec, nCards); fail++; }
  if (sec >= 6 && nCards) { console.log("  ✗ 第 7 节起不该喂卡", type, sec); fail++; }
  if (!/上一稿残留/.test(r.usr)) { console.log("  ✗ residue 未带", type, sec); fail++; }
}
const r2 = run({ sec: 11, art, cards: mk("how"), refs, prev: "p".repeat(5000) }, "how", { url: "https://openrouter.ai/api/v1", model: "nvidia/nemotron:free", name: "OR" });
if (r2.usr.length > 30000) { console.log("  ✗ OpenRouter 预算", r2.usr.length); fail++; }
console.log("  最长一节输入 " + maxLen + " 字；OpenRouter 总纲 " + r2.usr.length + " 字");
console.log(fail ? fail + " FAILED" : "WRITE BRANCH OK (36 sections × 4 checks)");
process.exit(fail ? 1 : 0);
