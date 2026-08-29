"use strict";
/* 心得现写退避（2026-08-29 第三刀）护栏。
 * 验三件事：
 *   ① 生成失败时，服务端确实发出 reflectgen:{ok:false}（不是只靠一句人话）。
 *   ② 带 rs.noRegen:1 的请求，服务端**不会**再打一次生成调用（上游调用总数应比①少一次）。
 *   ③ 跳过重试时，note 里要如实说清楚"早前试过、没写出来"，不能装作什么都没发生。
 * 复用诊断脚本三的隔离打桩模式：每个用例独立 import 一份 worker.js，互不污染。
 */
const fs = require("fs");
const os = require("os");
const path = require("path");
const ROOT = "/home/claude/site";

let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };

function sseOf(frames) {
  const enc = new TextEncoder();
  let i = 0;
  return new ReadableStream({
    pull(c) {
      if (i >= frames.length) { c.close(); return; }
      const f = frames[i++];
      c.enqueue(enc.encode(f === "[DONE]" ? "data: [DONE]\n\n" : "data: " + JSON.stringify(f) + "\n\n"));
    },
  });
}
const delta = (s) => ({ choices: [{ delta: { content: s } }] });
const VENDOR_HOSTS = ["api.deepseek.com", "open.bigmodel.cn", "api.moonshot.cn", "dashscope.aliyuncs.com", "api.minimax.io"];
const CTX = { waitUntil() {}, passThroughOnException() {} };

async function runOnce(vendor, noRegen, upstreamMode) {
  const UP = { seen: [] };
  let SELF_ENV = null, W = null;
  globalThis.fetch = async function (input, init) {
    const u = String((input && input.url) || input || "");
    let host = ""; try { host = new URL(u).host; } catch (e) {}
    if (VENDOR_HOSTS.some((h) => host.indexOf(h) >= 0)) {
      let body = {}; try { body = JSON.parse((init && init.body) || "{}"); } catch (e) {}
      UP.seen.push({ url: u, body: body });
      if (body.stream === false) {
        if (upstreamMode === "fail") {
          return new Response(JSON.stringify({ choices: [{ message: { content: "", reasoning_content: "MOCK_THINKING ".repeat(400) }, finish_reason: "length" }] }), { status: 200, headers: { "content-type": "application/json" } });
        }
        return new Response(JSON.stringify({ choices: [{ message: { content: "MOCK_REFLECT_TEXT ".repeat(60) } }] }), { status: 200, headers: { "content-type": "application/json" } });
      }
      return new Response(sseOf([delta("好的。"), "[DONE]"]), { status: 200, headers: { "content-type": "text/event-stream" } });
    }
    if (/^https:\/\/sdeuniverses\.com\/api\//.test(u) && SELF_ENV) {
      return W.default.fetch(input instanceof Request ? input : new Request(u, init), SELF_ENV, CTX);
    }
    throw new Error("UNSTUBBED_FETCH " + u);
  };
  const CONFIG_VAULT = {
    idFromName: (n) => ({ n: n }),
    get: () => ({
      fetch: async (req) => {
        let body = {}; try { body = JSON.parse(await req.text()); } catch (e) {}
        if (body.op === "getReflect") return new Response(JSON.stringify({ reflect: "", rkey: body.rkey, exact: false, from: "" }), { status: 200 });
        return new Response(JSON.stringify({ ok: true }), { status: 200 });
      },
    }),
  };
  const LIMITER = { idFromName: (n) => ({ n: n }), get: () => ({ fetch: async () => new Response(JSON.stringify({ ok: true }), { status: 200 }) }) };
  const ASSETS = { fetch: async (req) => { try { return new Response(fs.readFileSync(path.join(ROOT, "public", new URL(req.url).pathname.replace(/\/$/, "/index.html"))), { status: 200 }); } catch (e) { return new Response("nf", { status: 404 }); } } };
  const env = { ASSETS: ASSETS, ASK_LIMITER: LIMITER, CONFIG_VAULT: CONFIG_VAULT, PDFS: { head: async () => null, get: async () => null } };
  SELF_ENV = env;

  const TMP = path.join(os.tmpdir(), "guard_noregen_" + vendor + "_" + Date.now() + "_" + Math.random().toString(36).slice(2) + ".mjs");
  fs.copyFileSync(path.join(ROOT, "src/worker.js"), TMP);
  W = await import("file://" + TMP);

  const rsBody = { i: 2, n: 10, t: "文献综述", topic: "什么是SDE本体论？", done: "1. 背景研究", sde: 1 };
  if (noRegen) rsBody.noRegen = 1;
  const req = new Request("https://sdeuniverses.com/api/wds/chat", {
    method: "POST", headers: { "content-type": "application/json", "cf-connecting-ip": "9.9.9.9" },
    body: JSON.stringify({ q: "文献综述", history: [], key: "testtesttest12345678", vendor: vendor, model: "", mode: "std", nosite: 1, rs: rsBody }),
  });
  const res = await W.default.fetch(req, env, CTX);
  const text = await res.text();
  const events = [];
  for (const line of text.split("\n")) {
    const s = line.trim(); if (s.indexOf("data:") !== 0) continue;
    const p = s.slice(5).trim(); if (p === "[DONE]") continue;
    try { events.push(JSON.parse(p)); } catch (e) {}
  }
  return { upCalls: UP.seen.length, genCalls: UP.seen.filter((x) => x.body.stream === false).length, events: events };
}

(async () => {
  console.log("— ① 第一次遇到这家（无 noRegen），上游会真的打一次生成调用，失败要发 reflectgen:{ok:false} —");
  const r1 = await runOnce("kimi", false, "fail");
  ok(r1.genCalls === 1, "确实打了一次非流式生成调用（genCalls=" + r1.genCalls + "）");
  const rg1 = r1.events.find((e) => e.t === "reflectgen");
  ok(!!rg1, "发出了 reflectgen 事件");
  ok(!!rg1 && rg1.v && rg1.v.ok === false, "reflectgen.ok === false（生成确实失败了）");
  const note1 = r1.events.filter((e) => e.t === "note").map((e) => e.v).join(" | ");
  ok(/正在带着完整内功现写一份/.test(note1), "有「正在现写」这句人话（不是纯机器信号，读者也看得懂）");

  console.log("\n— ② 带 rs.noRegen:1 再问一次同一家，服务端不该再打生成调用 —");
  const r2 = await runOnce("kimi", true, "fail");
  ok(r2.genCalls === 0, "**没有**再打生成调用（genCalls=" + r2.genCalls + "，退避生效）");
  ok(r2.upCalls === 1, "上游调用总数只剩答题那一次（=" + r2.upCalls + "）");
  const rg2 = r2.events.find((e) => e.t === "reflectgen");
  ok(!rg2, "跳过时不发 reflectgen（没试就不该发「试过」的信号）");
  const note2 = r2.events.filter((e) => e.t === "note").map((e) => e.v).join(" | ");
  ok(/早前已经现写心得试过、没写出来/.test(note2), "跳过时如实说明「早前试过没写出来」，不是装作什么都没发生");
  ok(/不再重试/.test(note2), "明确说了不再重试");

  console.log("\n— ③ 反向：noRegen 为假、且生成这次能成功时，不应该被误判成失败/跳过 —");
  const r3 = await runOnce("kimi", false, "ok");
  ok(r3.genCalls === 1, "打了生成调用");
  const rg3 = r3.events.find((e) => e.t === "reflectgen");
  ok(!!rg3 && rg3.v && rg3.v.ok === true, "生成成功时 reflectgen.ok === true");

  console.log("\n— ④ 反向：老前端（不带 noRegen 字段）行为不变——不该被这一刀误伤 —");
  const r4 = await runOnce("mm", undefined, "fail"); // undefined = 不传该字段，模拟旧前端
  ok(r4.genCalls === 1, "旧前端（无 noRegen 字段）仍然照常尝试生成（向后兼容）");

  console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
  if (F) process.exit(1);
})().catch((e) => { console.error("FATAL", e && e.stack || e); process.exit(1); });
