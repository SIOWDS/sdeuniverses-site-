/* sim_emerge_errors —— 涌现档「失败不再静默」的干跑（配合 /api/ask 的出流护栏）。

   缘起：读者截图报障，二阶碰撞栏只有一行
   「✗ HTTP 503 <!DOCTYPE html> <!--[if lt IE 7]> <html class="no-js ie6 oldie"…」。
   查下来两件事同时成立：① 平台把出流前的重活按资源上限掐了，回的是 Cloudflare 自己的 HTML
   错误页；② 前端把三路碰撞与三次盲评的失败**全吞掉**了（catch 是空的），所以屏幕上只剩
   最后一环的一个 ✗——读者以为是提炼坏了，其实前面已经死了好几次。

   本干跑只测第②件（第①件在 tools/sim_ask_stream_first.js）：
   ① errText 把平台错误页翻成人话，且不把 HTML 标签甩到页面上
   ② 单路 503：另两路照跑，失败逐条记名并显示在候选典范上方
   ③ 盲评 503：该卡记 0 分参与择优，但卡面上说得出「创新检查未完成」
   ④ 综合提炼 503 → 自动重试一次就成（此前它是整条链上唯一没有重试的一环）
   ⑤ 重试也失败：只打两次不无限重试，brief 不被污染，状态行是人话不是 HTML
   ⑥ 服务端出流后的进度提示（status）能被前端接住并显示
*/
"use strict";
const fs = require("fs");
const ROOT = "/home/claude/site";
const html = fs.readFileSync(ROOT + "/public/search/index.html", "utf8");
let P = 0, FA = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (FA++, console.log("  FAIL " + m)); };
const say = (s) => console.log(s);

/* ── 桩：DOM ── */
function mkEl() {
  return { textContent: "", innerHTML: "", value: "", disabled: false, style: {},
    _cls: {}, classList: { add(c) { this._cls = this._cls || {}; this._cls[c] = 1; },
      remove(c) { if (this._cls) delete this._cls[c]; }, has(c) { return !!(this._cls && this._cls[c]); } }, focus() {} };
}
const els = {};
const doc = { getElementById(id) { return els[id] || (els[id] = mkEl()); } };

/* ── 桩：基底（可编程剧本）。HTTP(503, html) ＝ 让这一次调用回一张平台错误页 ── */
const HTTP = (status, text) => ({ __http: { status: status, text: text } });
const CF503 = HTTP(503, '<!DOCTYPE html>\n<!--[if lt IE 7]> <html class="no-js ie6 oldie" lang="en-US"> <![endif]-->\n<head><title>steep-band-faf5.workers.dev | 503</title></head>');
const PARADIGM = (name) => name + "\n\n【承重命题】沉默不是知识缺口，也不是权力压制，而是" + name + "。\n"
  + "【它切开的辨别面】把「不敢说」与「无可说」第一次分得开。".repeat(6) + "\n"
  + "【可裁决判据】当匿名化提问时，脱耦论预测不变，本典范预测显著下降。\n" + "补白。".repeat(80);
const CARD = (S, D, E, I, F) => JSON.stringify({
  title: "典范", S: { score: S }, D: { score: D }, E: { score: E }, I: { score: I }, F: { score: F },
  neighbors: [], deductions: [], upgrades: [], verdict: "一句总评",
});
let SCRIPT = {};
const captured = [];
function fakeFetch(url, opt) {
  const body = JSON.parse(opt.body);
  captured.push(body);
  let out;
  if (body.mode === "collide") out = SCRIPT.collide.shift();
  else if (body.mode === "iq") out = SCRIPT.iq.shift();
  else if (body.mode === "synth") out = Array.isArray(SCRIPT.synth) ? SCRIPT.synth.shift() : SCRIPT.synth;
  else out = "";
  if (out && out.__http) return Promise.resolve({ ok: false, status: out.__http.status, text: () => Promise.resolve(out.__http.text) });
  const enc = new TextEncoder();
  const chunks = [];
  if (SCRIPT.withStatus) chunks.push('data: {"t":"status","v":"🔎 正在检索站内语料…"}\n');
  String(out || "空").match(/[\s\S]{1,180}/g).forEach(s => chunks.push("data: " + JSON.stringify({ t: "token", v: s }) + "\n"));
  chunks.push("data: [DONE]\n");
  let i = 0;
  return Promise.resolve({ ok: true, status: 200, body: { getReader() {
    return { read() { return i >= chunks.length ? Promise.resolve({ done: true })
      : Promise.resolve({ done: false, value: enc.encode(chunks[i++]) }); } }; } } });
}

/* ── 抠出前端整块，真跑 ── */
const a = html.indexOf("var iqCard=null");
const b = html.indexOf("function renderSources(");
if (a < 0 || b <= a) { console.log("FAIL 抠不出前端块（锚点变了）"); process.exit(1); }
const clientSrc = html.slice(a, b);
function mkClient(turns) {
  const flashed = [];
  const fn = new Function("document", "fetch", "keyMode", "vendor", "turns", "originQ", "buildHist",
    "flashAsk", "esc", "asking", "papering", "distilling", "brief", "setTimeout",
    clientSrc + "\nreturn {doEmerge:doEmerge, errText:errText, getFails:function(){return emergeFails;},"
    + "getParadigms:function(){return paradigms;}, getBrief:function(){return brief;}};");
  const api = fn(doc, fakeFetch, "sys", "ds", turns,
    () => (turns[0] || {}).q || "", (full) => turns.map(t => ({ q: t.q, a: t.a })),
    (m) => flashed.push(m), (s) => String(s), false, false, false, "",
    (f) => f());   // 重试的等待在干跑里直接放行，别真等四秒
  api.flashed = flashed;
  return api;
}
const TURNS = [
  { q: "课堂沉默是怎么回事", a: "观点一：…\n观点二：…\n观点三：…" },
  { q: "匿名提问能解决吗", a: "观点一：…\n观点二：…\n观点三：…" },
];

/* ══════════ 一、errText：平台错误页要翻成人话 ══════════ */
say("\n━━━ 一、errText：读者不该看见 <!DOCTYPE html> ━━━");
{
  const C = mkClient(TURNS);
  const t503 = C.errText(new Error("HTTP 503 " + CF503.__http.text));
  ok(/503/.test(t503) && /资源上限/.test(t503), "503 翻成「平台资源上限，等十几秒再点一次」：" + t503.slice(0, 34) + "…");
  ok(t503.indexOf("<") < 0 && t503.indexOf("DOCTYPE") < 0, "一个 HTML 标签都不许漏到页面上");
  ok(/502/.test(C.errText(new Error("HTTP 502 Bad Gateway"))), "别的 5xx 也报得出码");
  ok(C.errText(new Error("基底返回错误")) === "基底返回错误", "本来就是人话的消息原样保留");
  ok(C.errText(new Error("x".repeat(400))).length <= 180, "超长消息截断，不撑爆状态行");
}

/* ══════════ 二、单路 503：另两路照跑，失败留名 ══════════ */
say("\n━━━ 二、三路碰撞：死一路也要说清死在哪 ━━━");
const C2 = mkClient(TURNS);
SCRIPT = { collide: [CF503, PARADIGM("评价在场性"), PARADIGM("可归因风险")],
  iq: [CARD(130, 136, 128, 126, 132), CARD(128, 130, 124, 120, 126)],
  synth: "一、最终承重命题：……" + "……".repeat(200) };
captured.length = 0;
C2.doEmerge().then(function () {
  ok(C2.getParadigms().length === 2, "另外两路照常跑完（单路失败不拖垮全局，老行为不变）");
  const fails = C2.getFails();
  ok(fails.length === 1 && /第 1 路/.test(fails[0]), "失败逐条记名：" + (fails[0] || "").slice(0, 30) + "…");
  ok(/资源上限/.test(fails[0]) && fails[0].indexOf("<") < 0, "记的是人话，不是那张 HTML 错误页");
  ok(/本次有 1 处未跑通/.test(els.emergeBox.innerHTML), "候选典范上方确实印出了「本次有 1 处未跑通」");
  ok(/✓ 三路已撞完/.test(els.emergeStat.textContent), "两个里照样择优、照样往下走");

  /* ══════════ 三、盲评 503 ══════════ */
  say("\n━━━ 三、创新检查挂掉：记 0 分，但卡面上说得出为什么 ━━━");
  const C3 = mkClient(TURNS);
  SCRIPT = { collide: [PARADIGM("甲"), PARADIGM("乙"), PARADIGM("丙")],
    iq: [CF503, CARD(133, 141, 129, 131, 138), CF503],
    synth: "一、最终承重命题：……" + "……".repeat(200) };
  captured.length = 0;
  return C3.doEmerge().then(function () {
    const ps = C3.getParadigms();
    ok(ps[0].total === 0 && ps[2].total === 0 && ps[1].total === 135, "两张挂掉的记 0 分，唯一评上分的胜出（135）");
    ok(/资源上限/.test(ps[0].err || ""), "挂掉的卡带上了失败原因");
    ok(/创新检查未完成/.test(els.emergeBox.innerHTML), "卡面上印出「创新检查未完成…按 0 分参与择优」");
    ok(captured.filter(x => x.mode === "synth").length === 1, "照样进综合提炼，不因为盲评挂了就断链");

    /* ══════════ 四、综合提炼：重试一次 ══════════ */
    say("\n━━━ 四、综合提炼 503 → 自动重试一次 ━━━");
    const C4 = mkClient(TURNS);
    SCRIPT = { collide: [PARADIGM("丁"), PARADIGM("戊"), PARADIGM("己")],
      iq: [CARD(130, 136, 128, 126, 132), CARD(129, 134, 126, 124, 130), CARD(128, 132, 125, 122, 128)],
      synth: [CF503, "一、最终承重命题：……" + "……".repeat(200)] };
    captured.length = 0;
    return C4.doEmerge().then(function () {
      ok(captured.filter(x => x.mode === "synth").length === 2, "第一次挂了会再打一次（此前这一环没有任何重试）");
      ok(C4.getBrief().length > 300 && /✓ 综合提炼完成/.test(els.briefStat.textContent), "第二次成了，入口资料照常立住");

      /* ══════════ 五、重试也挂：不无限重试、不污染 brief ══════════ */
      say("\n━━━ 五、两次都挂：收得住 ━━━");
      const C5 = mkClient(TURNS);
      SCRIPT = { collide: [PARADIGM("庚"), PARADIGM("辛"), PARADIGM("壬")],
        iq: [CARD(130, 136, 128, 126, 132), CARD(129, 134, 126, 124, 130), CARD(128, 132, 125, 122, 128)],
        synth: [CF503, CF503, "不该被用到"] };
      captured.length = 0;
      return C5.doEmerge().then(function () {
        ok(captured.filter(x => x.mode === "synth").length === 2, "只打两次，不无限重试（配额是真金白银）");
        ok(C5.getBrief() === "", "brief 不被污染，半成品不会被当成论文入口");
        ok(/✗/.test(els.emergeStat.textContent) && els.emergeStat.textContent.indexOf("<") < 0
          && /资源上限/.test(els.emergeStat.textContent), "收场那一行是人话：" + els.emergeStat.textContent.slice(0, 40) + "…");
        ok(/本次有/.test(els.emergeBox.innerHTML) === false && C5.getParadigms().length === 3, "三路都撞出来了，就不该有「未跑通」的横幅");

        /* ══════════ 六、服务端进度提示要接得住 ══════════ */
        say("\n━━━ 六、出流后的进度提示（status）能显示 ━━━");
        const C6 = mkClient(TURNS);
        SCRIPT = { withStatus: true, collide: [PARADIGM("癸"), PARADIGM("子"), PARADIGM("丑")],
          iq: [CARD(130, 136, 128, 126, 132), CARD(129, 134, 126, 124, 130), CARD(128, 132, 125, 122, 128)],
          synth: "一、最终承重命题：……" + "……".repeat(200) };
        captured.length = 0;
        return C6.doEmerge().then(function () {
          ok(/if\(j\.t==='status'\)\{ if\(onStat\) onStat\(acc\.length,false,j\.v\); \}/.test(html),
            "sseCollect 把服务端的 status 转给了 onStat 的第三个参数");
          ok(C6.getParadigms().length === 3 && C6.getBrief().length > 300, "带 status 的流照常跑完（多出来的事件不会打乱解析）");

          say("\n" + (FA ? "✗ " : "✓ ") + P + " PASS / " + FA + " FAIL");
          process.exit(FA ? 1 : 0);
        });
      });
    });
  });
}).catch(function (e) { console.log("HARNESS ERROR: " + (e && e.stack || e)); process.exit(1); });
