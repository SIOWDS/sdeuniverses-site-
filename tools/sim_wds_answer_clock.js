/* 只测这一次修的那件事：与WDS对话「没收到回答」的根因——出流之后、答题之前的准备阶段
   把整个请求的时钟烧光，而答题那一次调用本身一个超时都没有，于是被平台无声掐死，
   流里既无 error 也无 end，客户端只能干说"没收到回答"。

   四组断言：
   ① 词表扩展（配菜）不许再跑满功率档，且必须自带短截止；
   ② wdsFetchMax 能收上层的 AbortSignal（答题那一次终于有了时钟）；
   ③ 答题路径确有首帧/总时长两级护栏，且半截正文不丢；
   ④ 站内检索 5xx 会再打一次（SELF 子请求偶发 5xx 是常态，不是我方逻辑错）。
   全部对着 worker.js 的真源码，不复制一份平行实现。 */
"use strict";
const fs = require("fs");
const SRC = "/home/claude/site/src/worker.js";
const src = fs.readFileSync(SRC, "utf8");
let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };

/* ── ① 词表扩展：卸满功率 + 短截止（行为实测，不是 grep） ── */
console.log("\n[一] 词表扩展是配菜，不许占答题的时钟");
{
  const seg = src.slice(src.indexOf("function wdsTopBody"), src.indexOf("// 五家基底"));
  const box = new Function(seg + "\nreturn { wdsTopBody };")();
  const top = { url: "https://api.deepseek.com/v1/chat/completions", model: "m", name: "n", top: 1 };
  const asTop = box.wdsTopBody(top, { model: "m" });
  ok(asTop.reasoning_effort === "max", "带 top 标记时确实是满功率档（对照组）");
  // sdeExpandQuery 里的降档写法：只保留 url/model/name，不带 top
  const LC = { url: top.url, model: top.model, name: top.name };
  const asLight = box.wdsTopBody(LC, { model: "m" });
  ok(!asLight.reasoning_effort && !asLight.thinking, "卸掉 top 后请求体里没有 thinking / reasoning_effort——它不会再慢慢推演");

  const fnSrc = src.slice(src.indexOf("async function sdeExpandQuery"), src.indexOf("async function handleAsk"));
  ok(/const LC = \(VC && VC\.top\) \? \{/.test(fnSrc), "sdeExpandQuery 源码里确有降档那一步");
  ok(/ms \|\| SDE_EXPAND_MS/.test(fnSrc), "sdeExpandQuery 把截止时间传进了 llmText");
  const ms = Number((src.match(/const SDE_EXPAND_MS = (\d+)/) || [])[1]);
  ok(ms > 0 && ms <= 10000, "SDE_EXPAND_MS = " + ms + " 毫秒（必须远小于原来的 55000）");
  ok(/async function llmText\(VC, KEY, sys, usr, maxTok, msTimeout\)/.test(src), "llmText 收得下自定义超时");
  ok(/msTimeout \|\| 55000/.test(src), "llmText 不传就仍是 55 秒，别的调用点不受影响");
  const calls = src.match(/sdeExpandQuery\(VC, (?:KEY|key), q[^)]*\)/g) || [];
  ok(calls.length >= 2, "站内共 " + calls.length + " 处调用词表扩展");
  ok(calls.some((c) => /SDE_EXPAND_MS/.test(c)), "答题路径显式带上了短截止");
  ok(/const SDE_EXPAND_MS = \d+;\nasync function sdeExpandQuery/.test(src), "其余调用点即便不传，缺省也是这个短截止（降档与限时都写在函数内部，堵不漏）");
}

/* ── ② wdsFetchMax 收 signal（行为实测：桩 fetch 检查它有没有把 signal 递下去） ── */
console.log("\n[二] 答题那一次调用终于有了时钟");
{
  // 从预算常量一路取到 wdsTopBody 之后（含 wdsFetchMax / wdsRag / wdsTopBody），不碰依赖 WDS_VENDORS 的部分
  const seg = src.slice(src.indexOf("const WDS_TOK_MAX"), src.indexOf("// 五家基底"));
  let seen = null;
  const box = new Function("fetch", seg + "\nreturn { wdsFetchMax };")(async (u, o) => { seen = o; return { ok: true, status: 200 }; });
  const ac = new AbortController();
  return box.wdsFetchMax({ url: "x", model: "m", top: 1 }, "k", [], true, 8000, ac.signal).then((r) => {
    ok(!!seen && seen.signal === ac.signal, "wdsFetchMax 把上层的 AbortSignal 原样交给了 fetch");
    return box.wdsFetchMax({ url: "x", model: "m", top: 1 }, "k", [], true, 8000);
  }).then(() => {
    ok(!!seen && seen.signal === undefined, "不传 signal 时不注入 undefined 以外的东西（老调用点不受影响）");
    tail();
  });
}

function tail() {
  /* ── ③ 答题路径的两级护栏与"半截正文不丢" ── */
  console.log("\n[三] 首帧 / 总时长两级护栏");
  const ans = src.slice(src.indexOf("// ANSWER_DEADLINE"), src.indexOf("const _diagLine ="));
  const first = Number((ans.match(/ANS_FIRST_MS = (\d+)/) || [])[1]);
  const total = Number((ans.match(/ANS_TOTAL_MS = (\d+)/) || [])[1]);
  ok(first > 0 && total > first, "两级护栏都在且总时长大于首帧：首帧 " + first / 1000 + "s / 总 " + total / 1000 + "s");
  ok(/_ac\.signal/.test(ans), "护栏的 signal 确实交给了 wdsFetchMax");
  ok(/clearTimeout\(_t1\);\s+\/\/ 首帧到了/.test(ans), "收到第一帧就撤掉首帧护栏——正常的长思考不会被误杀");
  ok(/if \(got\) \{ controller\.enqueue\(_sseBytes\(\{ t: "note"/.test(ans), "中途断线时已写出的正文一个字都不丢（发 note 而非丢弃）");
  ok(/return \{ soft: _cut \?/.test(ans), "被自己掐断时回的是 soft（可降档重答），不是静默");
  ok(!/wdsFetchMax\(VC, KEY, messages, true, tokWant\)\s*;/.test(src), "答题路径已不存在「无 signal」的老调用");

  /* ── ④ 站内检索 5xx 重打一次 ── */
  console.log("\n[四] 站内检索的偶发 5xx 再打一次");
  const pre = src.slice(src.indexOf("// ANSWER_CLOCK"), src.indexOf("_st.pre = Math.round"));
  ok(/for \(let _try = 0; _try < 2; _try\+\+\)/.test(pre), "检索最多打两次");
  ok(/if \(rr\.status < 500\) break;/.test(pre), "只对 5xx 重打，4xx 立刻认输（不做无谓重试）");
  ok(/_st\.stage = "扩展检索词"/.test(pre) && /_st\.stage = "站内检索"/.test(pre), "前置两段都打了标");
  ok(/_st\.pre = Math\.round/.test(src) && /_st\.stage = "基底作答"/.test(src), "准备耗时被记下来，进入答题阶段时改标");

  /* ── ⑤ 心跳与客户端把阶段显示出来（下次报障一眼可判） ── */
  console.log("\n[五] 阶段随心跳回传，读者截图即证据");
  ok(/stage: state\.stage \|\| ""/.test(src), "心跳事件带上了当前阶段");
  const page = fs.readFileSync("/home/claude/site/public/taste/wds-dialogue/index.html", "utf8");
  ok(/j\.v\.stage\) diag\.stage = j\.v\.stage/.test(page), "客户端记住最后一个阶段");
  ok(/已 " \+ \(j\.v\.sec \|\| 0\) \+ " 秒 · "/.test(page), "等待时显示的是「已 N 秒 · 某阶段」");
  ok(/流式收到 " \+ diag\.bytes \+ " 字节/.test(page), "诊断行如实报收到多少字节（不再一律写「流式 0 字节」）");
  ok(/被中途切断/.test(page) && /停在「/.test(page), "诊断行说得出是干净结束还是被切断、停在哪一段");

  console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
  process.exit(F ? 1 : 0);
}
