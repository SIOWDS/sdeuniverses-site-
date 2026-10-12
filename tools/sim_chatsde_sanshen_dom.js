/* sim_chatsde_sanshen_dom.js —— 「SDE三审」真点一遍（jsdom 里跑整份 wds-mode.js ＋ sde-sanshen.js）
 * ?mode=sar 进门＝审＋改：机检 → 逐单元三审（每批 5 个，自动审完）→ 复审 → 终审 → 逐单元改稿（每批 3 个，自动改完）
 * → 两份 Word（三审意见书、修改稿）。另验：按钮三态循环、与其他多路模式互斥、结论底线从严、提问零 SDE 字样与不超上限。
 * 用法：node tools/sim_chatsde_sanshen_dom.js [输出目录]   （给了输出目录就把两份 docx 写出去，供 python-docx 复核）
 */
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");
const ROOT = path.join(__dirname, "..");
const SRC = fs.readFileSync(path.join(ROOT, "public/wds-mode.js"), "utf8");
const DOCX = fs.readFileSync(path.join(ROOT, "public/assets/sde-docx.js"), "utf8");
const ENG = fs.readFileSync(path.join(ROOT, "public/assets/sde-sanshen.js"), "utf8");
const OUT = process.argv[2] || "";
let pass = 0, fail = 0;
function ok(c, m) { if (c) { pass++; console.log("  PASS " + m); } else { fail++; console.log("  FAIL " + m); } }

const dom = new JSDOM("<!doctype html><html><head></head><body></body></html>",
  { runScripts: "outside-only", url: "https://sdeuniverses.com/taste/chatsde/?mode=sar", pretendToBeVisual: true });
const w = dom.window;
const mem = { sde_wds_key: "sk-abcdefghijklmnop", sde_wds_lang: "zh" };
Object.defineProperty(w, "localStorage", { value: { getItem: k => (k in mem ? mem[k] : null), setItem: (k, v) => { mem[k] = String(v); }, removeItem: k => { delete mem[k]; } }, configurable: true });
w.WDSM_PAGE = 1;
const U = require("util");
w.TextDecoder = w.TextDecoder || U.TextDecoder;
w.TextEncoder = w.TextEncoder || U.TextEncoder;
const calls = [];
function sse(tokens) {
  const lines = tokens.map(v => "data: " + JSON.stringify({ t: "token", v: v }) + "\n");
  lines.push("data: [DONE]\n");
  let i = 0; const enc = new U.TextEncoder();
  return Promise.resolve({ ok: true, status: 200, body: { getReader: () => ({ read: () => Promise.resolve(i < lines.length ? { done: false, value: enc.encode(lines[i++]) } : { done: true }), cancel: () => {} }) } });
}
// ── 样书：一部专著，目录＋六章；第三章混进一句修订残留、第五章有一段与第二章完全重复
const para = "城市更新不是把旧房子推倒重建，而是在原有的街巷与人情之中重新安排生活的秩序，这一点在老城区尤其明显。";
const DUP = "这一段文字是作者在修改时忘了删掉的旧稿，它与后文重复，读者会以为排版出了错，编辑必须把它清理干净才行。";
function body(n) { let s = ""; while (s.length < 1300) s += para + "第" + n + "章的材料。"; return s; }
const CH = ["街巷的记忆", "拆与留", "居民的声音", "规划者的难处", "重复的经验", "城市的明天"];
let BOOK = "老城新生\n目录\n";
CH.forEach((s, i) => { BOOK += "第" + "一二三四五六"[i] + "章 " + s + "\n"; });
BOOK += "参考文献\n致谢\n后记\n附录\n";
CH.forEach((s, i) => {
  BOOK += "\n第" + "一二三四五六"[i] + "章 " + s + "\n" + body(i + 1) + "\n";
  if (i === 1 || i === 4) BOOK += DUP + "\n";
  if (i === 2) BOOK += "此处需补充三个案例，请作者确认数据来源。\n";
});

function unitRep(n) {
  return "【初审意见】\n- 第二段｜「居国内第一」｜比较性断言无来源｜补出处或删去｜A\n- 第三段｜「1万5千户」｜数字写法不规范｜改为「1.5万户」｜B\n"
    + "【洪流体检】\n起手：" + (n % 2 ? "有，开头用一位老住户的搬家开场" : "缺，直接给定义") + "\n接力：弱，第二节与第一节并列\n结算：缺，没有得出新判断\n出口：弱\n判：" + (n % 3 === 0 ? "洪流" : (n % 2 ? "半流" : "库存")) + "\n"
    + "库存｜第三节｜「城市更新包括以下五个方面」｜五个方面并排罗列不交锋｜开头补一个问题：为什么同一条街有人要拆有人要留，再让五个方面依次回答它\n"
    + "【终审线索】读者：最卷入——老住户搬家｜最劝退——第三节的分类罗列\n"
    + (n === 4 ? "风险｜第四节｜点名批评某区政府｜提请人工\n" : "风险：无\n")
    + "【台账】术语：城市更新（第" + n + "单元定义）；人物：老周";
}
const REV2 = "一、复审总判\n这部稿子前半是书，后半成了库存。\n二、全书洪流图\n| 单元 | 起手 | 接力 | 结算 | 出口 | 判 |\n|---|---|---|---|---|---|\n| 2 | 有 | 弱 | 缺 | 弱 | 半流 |\n三、库存段落与改法\n- 第三节：五个方面并排。主线：起手在第一章，结算放第六章。\n四、对初审的复核\nA 级确属必改。\n五、复审结论\n【复审结论】通过复审，理由：总体可读。";
const REV3 = "一、这是一部什么书、写给谁\n写给城市规划从业者。\n二、读者能不能被卷进去\n老住户的故事最能抓人。\n三、它在领域里的位置\n把已有说法用到新场景，适合国内出版。\n四、导向与合规\n- 第四单元点名批评某区政府，提请人工。\n五、出版形态与市场建议\n〔供参考〕\n六、终审决定\n【终审结论】同意出版\n七、必须完成的修改\n1. 删去重复段落 ｜ 第二、五章 ｜ 作者\n2. 补出处 ｜ 全书 ｜ 作者\n致作者：请按主线改。";
w.fetch = function (url, o) {
  if (String(url).indexOf("/api/wds/chat") < 0) return new Promise(() => {});
  const b = JSON.parse(o.body);
  calls.push(b);
  if (b.fc === 1) return sse(["[]"]);
  if (/【任务 · 复审报告/.test(b.q)) return sse([REV2.slice(0, 40), REV2.slice(40)]);
  if (/【任务 · 终审报告/.test(b.q)) return sse([REV3]);
  if (/【任务 · 按三审意见修改本单元】/.test(b.q)) {
    const m = /第 (\d+)\/\d+ 单元 · ([^\n]*)/.exec(b.q);
    return sse(["第" + (m ? m[1] : "?") + "单元 改后正文\n为什么同一条街有人要拆、有人要留？老周的搬家给出了第一个答案。〔待核〕\n【本单元修改说明】\n- 复审｜开头补了问题｜「城市更新包括以下五个方面」→「为什么同一条街有人要拆、有人要留？」"]);
  }
  if (/【本单元输出格式/.test(b.q)) {
    const m = /第 (\d+)\/\d+ 单元/.exec(b.q);
    return sse([unitRep(m ? +m[1] : 0)]);
  }
  return sse(["?"]);
};
try { w.eval(SRC); } catch (e) { console.log("eval err:", e.message); }
w.eval(DOCX);
w.eval(ENG);
const d = w.document;
const sa = d.querySelector(".wdsm-sabtn"), cs = d.querySelector(".wdsm-csbtn"), rv = d.querySelector(".wdsm-rvbtn"), ms = d.querySelector(".wdsm-msbtn");
ok(!!sa && sa.textContent.length > 0, "模式条上有三审按钮且初始就有字：「" + (sa && sa.textContent) + "」");
ok(sa.classList.contains("on") && /审＋改/.test(sa.textContent), "?mode=sar 进门就挂上「审＋改」");
sa.click();
ok(!sa.classList.contains("on") && /^⚖ SDE三审$/.test(sa.textContent), "再点一次＝关");
sa.click();
ok(sa.classList.contains("on") && /只审/.test(sa.textContent), "再点＝只审");
cs.click();
ok(cs.classList.contains("on") && !sa.classList.contains("on"), "开来稿初审会关掉三审（互斥）");
ms.click();
ok(ms.classList.contains("on") && !sa.classList.contains("on") && !cs.classList.contains("on"), "开稿件提升，三审仍关着");
sa.click(); sa.click();
ok(sa.classList.contains("on") && /审＋改/.test(sa.textContent) && !ms.classList.contains("on") && !rv.classList.contains("on") && !cs.classList.contains("on"), "开三审会关掉其余模式，停在审＋改");

const inEl = d.querySelector(".wdsm-in");
inEl.value = BOOK;
(d.querySelector(".wdsm-send") || d.querySelector(".wdsm-go")).click();

function waitFor(pred, cb, ms2) {
  let t = 0;
  (function p() { if (pred() || t > (ms2 || 30000)) return cb(); t += 100; setTimeout(p, 100); })();
}
const act = re => Array.from(d.querySelectorAll(".wdsm-acts .wdsm-act")).find(b => re.test(b.textContent));
waitFor(() => Array.from(d.querySelectorAll(".wdsm-acts")).some(a => /两份 Word 都可导出/.test(a.textContent)), function () {
  const un = calls.filter(c => /【本单元输出格式/.test(c.q));
  const r2 = calls.filter(c => /【任务 · 复审报告/.test(c.q));
  const r3 = calls.filter(c => /【任务 · 终审报告/.test(c.q));
  const rw = calls.filter(c => /【任务 · 按三审意见修改本单元】/.test(c.q));
  ok(un.length === 6, "逐单元三审 6 个正文单元（目录原样保留、不审）：" + un.length);
  ok(r2.length === 1 && r3.length === 1, "复审、终审各一次");
  ok(rw.length === 6, "审＋改：6 个单元逐一改稿：" + rw.length);
  const all = calls.filter(c => c.fc !== 1);
  ok(all.every(c => c.nosde === 1 && c.nosite === 1), "全程走无 SDE 一路、不查站内");
  ok(all.every(c => c.q.length <= 19800), "每次提问不超 19800 字：最长 " + Math.max.apply(null, all.map(c => c.q.length)));
  ok(all.every(c => !/SDE/.test(c.q)), "提问里没有「SDE」字样（对外零术语）");
  ok(un.every(c => /【本书是专著：洪流四问这样判】/.test(c.q)), "类型由正文推断为专著，并递专著的洪流标准");
  ok(un.every(c => /不说|不编出处/.test(c.q) && /提请人工/.test(c.q)), "规则块带「提请人工」与不编出处");
  ok(/【前面单元的台账】\n（无）/.test(un[0].q) && /\[\d+\] 术语：城市更新/.test(un[1].q), "台账随提问递给后面单元");
  ok(/底线：修改后终审/.test(r2[0].q), "复审提问写明统计底线：" + (/底线：[^；]*/.exec(r2[0].q) || [""])[0]);
  ok(/A 级 \d+ 条/.test(r3[0].q) && /底线：(修改后出版|退回修改)/.test(r3[0].q), "终审提问带统计与底线");
  ok(/删去重复段落/.test(rw[0].q) && /〔复审·库存〕/.test(rw[0].q) && /〔初审·A〕/.test(rw[0].q), "改稿提问带终审必改、复审库存与初审意见");
  ok(/〔机检·A〕[^\n]*修订残留/.test(rw[2].q), "第三单元的改稿提问带上机检发现的修订残留");
  const txt = d.querySelector(".wdsm-rlab").textContent.replace(/\s+/g, " ");
  ok(/初审结论：修改后复审/.test(txt), "初审结论由代码定：有 A 级＝修改后复审");
  ok(/复审结论：修改后终审/.test(txt) && /比统计底线宽，已从严/.test(txt), "复审：基底给「通过复审」被底线从严为「修改后终审」");
  ok(/终审结论：(修改后出版|退回修改)/.test(txt) && !/终审结论：同意出版/.test(txt), "终审：基底给「同意出版」被底线从严");
  ok(/机检发现/.test(txt) && /修订残留/.test(txt) && /重复/.test(txt), "机检抓到修订残留与重复段落");
  const acts = Array.from(d.querySelectorAll(".wdsm-acts .wdsm-act")).map(a => a.textContent);
  ok(/三审意见书 Word/.test(acts[0]) && /修改稿 Word/.test(acts[1]), "收尾按钮：" + acts.join(" ｜ "));
  const saved = [];
  w.URL.createObjectURL = function (blob) { saved.push(blob); return "blob:x"; };
  w.URL.revokeObjectURL = function () {};
  act(/三审意见书 Word/).click();
  setTimeout(function () {
    act(/修改稿 Word/).click();
    setTimeout(function () {
      ok(saved.length === 2, "两份 Word 都生成了：" + saved.length);
      let left = saved.length;
      const bufs = [];
      saved.forEach(function (bl, k) {
        const fr = new w.FileReader();
        fr.onload = function () {
          bufs[k] = Buffer.from(fr.result);
          if (--left) return;
          const x1 = bufs[0].toString("utf8"), x2 = bufs[1].toString("utf8");
          ok(bufs[0].slice(0, 2).toString() === "PK" && bufs[1].slice(0, 2).toString() === "PK", "两份都是 zip（docx）");
          ok(/三审意见书/.test(x1) && /初审报告/.test(x1) && /复审报告/.test(x1) && /终审报告/.test(x1) && /修改情况/.test(x1), "意见书：三份报告＋修改情况齐全");
          ok(/<w:tbl>/.test(x1) && /逐单元洪流体检表/.test(x1) && /三审结论/.test(x1), "意见书：真表格、洪流体检表、三审结论表");
          ok(/不构成/.test(x1) && /符合出版要求/.test(x1) && /提请人工/.test(x1), "意见书：声明与提请人工");
          ok(!/【复审结论】|【终审结论】/.test(x1), "意见书正文里不留结论标记行（结论已进结论表）");
          ok(/修改稿/.test(x2) && /改后正文/.test(x2) && /〔待核〕/.test(x2), "修改稿：改后正文与待核标记");
          if (OUT) { fs.writeFileSync(path.join(OUT, "sanshen_report.docx"), bufs[0]); fs.writeFileSync(path.join(OUT, "sanshen_revised.docx"), bufs[1]); console.log("  wrote docx to " + OUT); }
          console.log("\n===== " + pass + " PASS / " + fail + " FAIL =====");
          process.exit(fail ? 1 : 0);
        };
        fr.readAsArrayBuffer(bl);
      });
    }, 300);
  }, 300);
}, 60000);
