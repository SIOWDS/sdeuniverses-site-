/* sim_chatsde_compare_dom.js —— 同题对照的「真点一遍」（jsdom 里跑整份 wds-mode.js）
 * 静态检查抓不到的那类漏（按钮没字、点了没反应、两路请求实际递出去的东西、Word 按钮出没出来），
 * 这里把页面真跑起来：点按钮 → 打字 → 发送 → 截下两条 /api/wds/chat 请求 → 喂两段假的流 → 看收尾。
 */
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");
const SRC = fs.readFileSync(path.join(__dirname, "..", "public/wds-mode.js"), "utf8");
let pass = 0, fail = 0;
function ok(c, m) { if (c) { pass++; console.log("  PASS " + m); } else { fail++; console.log("  FAIL " + m); } }

const dom = new JSDOM("<!doctype html><html><head></head><body></body></html>",
  { runScripts: "outside-only", url: "https://sdeuniverses.com/taste/chatsde/", pretendToBeVisual: true });
const w = dom.window;
const mem = { sde_wds_key: "sk-abcdefghijklmnop", sde_wds_lang: "zh" };
Object.defineProperty(w, "localStorage", { value: { getItem: k => (k in mem ? mem[k] : null), setItem: (k, v) => { mem[k] = String(v); }, removeItem: k => { delete mem[k]; } }, configurable: true });
w.WDSM_PAGE = 1;
w.TextDecoder = w.TextDecoder || require("util").TextDecoder;
w.TextEncoder = w.TextEncoder || require("util").TextEncoder;
const calls = [];
w.fetch = function (url, o) {
  if (String(url).indexOf("/api/wds/chat") < 0) return new Promise(() => {});
  const body = JSON.parse(o.body);
  if (body.fc === 1) {                      // 事实核查道：对有 SDE 那份挑出「九百年」
    calls.push(body);
    const arr = /九百年/.test(body.q) ? '[{"orig":"九百年","fix":"约七百年","why":"奥卡姆是14世纪人","level":"错"}]' : "[]";
    const ls = ['data: ' + JSON.stringify({ t: "token", v: arr }) + "\n", 'data: [DONE]\n'];
    let k = 0; const en = new (require("util").TextEncoder)();
    return Promise.resolve({ ok: true, status: 200, body: { getReader: () => ({ read: () => Promise.resolve(k < ls.length ? { done: false, value: en.encode(ls[k++]) } : { done: true }), cancel: () => {} }) } });
  }
  const side = body.cmp;
  const txt = side === "sde" ? "## 一、判断\n\n有 SDE 这一路的正文，九百年的使用。" : "## 一、判断\n\n无 SDE 这一路的正文。";
  const lines = [
    side === "sde" ? 'data: {"t":"note","v":"难度第 5 档：已装完整内功先验（78159 字，含二阶碰撞）。"}\n' : 'data: {"t":"note","v":"同题对照 · 无 SDE 一路"}\n',
    'data: ' + JSON.stringify({ t: "token", v: txt }) + "\n",
    'data: [DONE]\n',
  ];
  calls.push(body);
  let i = 0;
  const enc = new (require("util").TextEncoder)();
  return Promise.resolve({
    ok: true, status: 200,
    body: { getReader: () => ({ read: () => Promise.resolve(i < lines.length ? { done: false, value: enc.encode(lines[i++]) } : { done: true }), cancel: () => {} }) },
  });
};
try { w.eval(SRC); } catch (e) { console.log("eval err:", e.message); }

setTimeout(function () {
  const d = w.document;
  const btn = d.querySelector(".wdsm-cmpbtn");
  ok(!!btn, "模式条上有「同题对照」按钮");
  ok(btn && btn.textContent.trim() === "⚖ 同题对照", "按钮初始就有字（不是零宽空框）：「" + (btn && btn.textContent) + "」");
  ok(btn && btn.style.display !== "none", "ChatSDE 本体页上可见");
  btn.click();
  ok(btn.classList.contains("on") && /：开/.test(btn.textContent), "点一下就开：「" + btn.textContent + "」");
  const tri = d.querySelector(".wdsm-tribtn"), mob = d.querySelector(".wdsm-mobbtn");
  ok(!tri.classList.contains("on") && !mob.classList.contains("on"), "开对照时对撞与群碰都是关的");
  const inEl = d.querySelector(".wdsm-in");
  inEl.value = "解构一万小时定律";
  const sendBtn = d.querySelector(".wdsm-send") || d.querySelector(".wdsm-go");
  if (sendBtn) sendBtn.click();
  else inEl.dispatchEvent(new w.KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
  setTimeout(function () {
    const main = calls.filter(c => c.fc !== 1);
    ok(main.length === 2, "一问发出两条正文请求（实际 " + main.length + " 条）");
    const S = calls.find(c => c.cmp === "sde"), P = calls.find(c => c.cmp === "plain");
    ok(!!S && !!P, "一条 cmp=sde，一条 cmp=plain");
    if (S && P) {
      ok(S.q === P.q && /2000 字/.test(S.q) && S.q.indexOf("解构一万小时定律") === 0, "两路题面逐字相同，且带同一句篇幅要求");
      ok(S.history.length === 0 && P.history.length === 0, "两路都不带历史");
      ok(!S.umem && !P.umem && !S.about && !P.about, "两路都不带记忆与「关于我」");
      ok(S.mode === "deep" && P.mode === "deep" && S.grade === 5 && P.grade === 5, "两路同档：deep＋第 5 档");
      ok(S.vendor === P.vendor && S.key === P.key, "两路同一家同一把 Key");
      ok(P.nosde === 1 && !S.nosde, "只有右路是 nosde");
    }
    setTimeout(function () {
      const cols = d.querySelectorAll(".wdsm-du .wdsm-duc");
      ok(cols.length === 2, "左右两栏都画出来了");
      const txt = d.querySelector(".wdsm-du").textContent;
      ok(/有 SDE 这一路的正文/.test(txt) && /无 SDE 这一路的正文/.test(txt), "两栏各写各的正文");
      ok(/已装完整内功先验/.test(cols[0].textContent) && !/已装完整内功/.test(cols[1].textContent), "左栏显示装了完整内功，右栏没有");
      const acts = Array.from(d.querySelectorAll(".wdsm-acts .wdsm-act")).map(b => b.textContent);
      ok(acts.some(a => /Word · 有 SDE/.test(a)) && acts.some(a => /Word · 无 SDE/.test(a)), "收尾出两颗 Word 按钮：" + acts.join(" ｜ "));
      ok(acts.some(a => /两份 Word 一起存/.test(a)) && acts.some(a => /创新智商/.test(a)), "另有「两份一起存」与「打创新智商」");
      const fcs = calls.filter(c => c.fc === 1);
      ok(fcs.length === 2 && fcs.every(c => c.nosde === 1 && c.history.length === 0), "两份各过一道事实核查（nosde、无历史）");
      ok(/约七百年的使用/.test(cols[0].textContent) && !/九百年/.test(cols[0].querySelector(".wdsm-a").textContent), "有 SDE 那份的「九百年」被改成「约七百年」");
      const fcBox = d.querySelectorAll(".wdsm-cmpfc");
      ok(fcBox.length === 2 && /改了 1 处/.test(fcBox[0].textContent) && /未发现/.test(fcBox[1].textContent), "两栏底下各挂核查记录：" + Array.from(fcBox).map(b => b.querySelector("summary").textContent).join(" ｜ "));
      console.log("\n===== " + pass + " PASS / " + fail + " FAIL =====");
      process.exit(fail ? 1 : 0);
    }, 900);
  }, 300);
}, 300);
