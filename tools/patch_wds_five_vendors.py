#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WDS 助手 · 扩到五家基底（后端，幂等，assert 锚定）
   ① WDS_VENDORS / WDS_TOP_MODEL 更新为五家的现行地址与型号
   ② 七处 `b.vendor === "ds" ? "deepseek" : "zhipu"` 统一换成 wdsVendorOf()
   ③ rvendor（内功心得按基底分缓存）改用 wdsShort()
   ④ 思考参数按厂商分派（各家开思考的参数名不一样）
   ⑤ 读者可覆盖 model（型号会过时，留一个自救口）
   ⑥ 新增 /api/wds/ping：不产内容、只验一次连通与鉴权，给前端「测试」按钮用
"""
import pathlib, re

P = pathlib.Path("/home/claude/site/src/worker.js")
h = P.read_text(encoding="utf-8"); o = h

# ───────── ① 基底表 ─────────
OLD_TBL = '''const WDS_VENDORS = {
  deepseek: { url: "https://api.deepseek.com/v1/chat/completions", model: "deepseek-v4-flash", name: "DeepSeek" },
  kimi: { url: "https://api.moonshot.cn/v1/chat/completions", model: "moonshot-v1-8k", name: "Kimi" },
  zhipu: { url: "https://open.bigmodel.cn/api/paas/v4/chat/completions", model: "glm-4-plus", name: "\\u667a\\u8c31 GLM" },
  qwen: { url: "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions", model: "qwen-plus", name: "\\u5343\\u95ee Qwen" },
  minimax: { url: "https://api.minimax.chat/v1/text/chatcompletion_v2", model: "abab6.5s-chat", name: "MiniMax" },
};'''
assert OLD_TBL in h, "基底表锚点"
NEW_TBL = '''// 五家基底。全部走各自的 OpenAI 兼容 chat/completions，由 Worker 服务端转发（不是浏览器直连，所以无 CORS 问题）。
// ⚠️ 型号会过时：各家改名/下线的节奏比本站快得多，所以读者可在设置里覆盖 model（见 wdsPickModel），
//    真过时了不必等改代码。默认值核对于 2026-07-28。
const WDS_VENDORS = {
  deepseek: { url: "https://api.deepseek.com/v1/chat/completions", model: "deepseek-v4-flash", name: "DeepSeek", apply: "platform.deepseek.com" },
  zhipu: { url: "https://open.bigmodel.cn/api/paas/v4/chat/completions", model: "glm-5-air", name: "\\u667a\\u8c31 GLM", apply: "open.bigmodel.cn" },
  kimi: { url: "https://api.moonshot.cn/v1/chat/completions", model: "kimi-k2.6", name: "Kimi", apply: "platform.moonshot.cn" },
  qwen: { url: "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions", model: "qwen-plus", name: "\\u5343\\u95ee Qwen", apply: "bailian.console.aliyun.com" },
  minimax: { url: "https://api.minimax.io/v1/chat/completions", model: "MiniMax-M2.7", name: "MiniMax", apply: "platform.minimax.io" },
};
// 前端短码 ↔ 基底键。未知一律落 zhipu（老前端只发 ds/其它两种值，这样不会断）。
const WDS_VMAP = { ds: "deepseek", glm: "zhipu", kimi: "kimi", qwen: "qwen", mm: "minimax" };
const WDS_VSHORT = { deepseek: "ds", zhipu: "glm", kimi: "kimi", qwen: "qwen", minimax: "mm" };
function wdsVendorOf(v) { return WDS_VMAP[String(v || "").toLowerCase()] || "zhipu"; }
function wdsShort(vd) { return WDS_VSHORT[vd] || "glm"; }
// 读者自填的型号覆盖默认值。只放行像模型名的字符串，别让它变成往上游注入别的东西的口子。
function wdsPickModel(vd, want, top) {
  const w = String(want || "").trim();
  if (w && w.length <= 60 && /^[A-Za-z0-9._:\\/-]+$/.test(w)) return w;
  return (top ? (WDS_TOP_MODEL[vd] || WDS_VENDORS[vd].model) : WDS_VENDORS[vd].model);
}'''
h = h.replace(OLD_TBL, NEW_TBL, 1)

OLD_TOP = 'const WDS_TOP_MODEL = { deepseek: "deepseek-v4-pro", zhipu: "glm-5" };'
assert OLD_TOP in h, "TOP 表锚点"
NEW_TOP = ('// 深度档型号（满血）。Kimi K3 与 MiniMax M2.x 的思考是常开的，没有单独的开关参数。\n'
           'const WDS_TOP_MODEL = { deepseek: "deepseek-v4-pro", zhipu: "glm-5", kimi: "kimi-k3", qwen: "qwen3.7-max", minimax: "MiniMax-M3" };')
h = h.replace(OLD_TOP, NEW_TOP, 1)

# ───────── ④ 思考参数按厂商分派 ─────────
OLD_BODY = '''function wdsTopBody(VC, body) {
  if (VC && VC.top && String(VC.url).indexOf("api.deepseek.com") >= 0) {
    body.thinking = { type: "enabled" };
    body.reasoning_effort = "max";
    delete body.temperature; delete body.top_p;
  }
  return body;
}'''
assert OLD_BODY in h, "wdsTopBody 锚点"
NEW_BODY = '''function wdsTopBody(VC, body) {
  if (!VC || !VC.top) return body;
  const u = String(VC.url);
  if (u.indexOf("api.deepseek.com") >= 0) {
    body.thinking = { type: "enabled" };
    body.reasoning_effort = "max";
    delete body.temperature; delete body.top_p;
  } else if (u.indexOf("open.bigmodel.cn") >= 0) {
    body.thinking = { type: "enabled" };
  } else if (u.indexOf("dashscope.aliyuncs.com") >= 0) {
    body.enable_thinking = true;               // 千问用的是这个名字，不是 thinking
  }
  // Kimi K3 与 MiniMax M2.x/M3：思考常开、无开关参数，塞了反而可能被判非法字段——什么都不加。
  return body;
}'''
h = h.replace(OLD_BODY, NEW_BODY, 1)

# ───────── ② 七处 vendor 映射 ─────────
OLD_V = 'const vd = b.vendor === "ds" ? "deepseek" : "zhipu";'
n = h.count(OLD_V)
assert n == 7, "vendor 映射处数变了：" + str(n)
h = h.replace(OLD_V, 'const vd = wdsVendorOf(b.vendor);')

# ───────── ③ rvendor ─────────
OLD_R = 'const KEY = userKey, rvendor = ({ zhipu: "glm", deepseek: "ds" })[vd] || vd;'
n = h.count(OLD_R)
assert n == 5, "rvendor 处数变了：" + str(n)
h = h.replace(OLD_R, 'const KEY = userKey, rvendor = wdsShort(vd);')

# ───────── ⑤ 读者可覆盖 model：chat 与 distill 两条主路 ─────────
OLD_M1 = '      const VC = deep ? wdsTopVC(vd) : { url: WDS_VENDORS[vd].url, model: WDS_VENDORS[vd].model, name: WDS_VENDORS[vd].name };'
assert OLD_M1 in h, "chat VC 锚点"
NEW_M1 = ('      const umodel = String(b.model || "").trim();                 // 读者在设置里填的型号覆盖（型号会过时，留个自救口）\n'
          '      const VC = deep\n'
          '        ? { url: WDS_VENDORS[vd].url, model: wdsPickModel(vd, umodel, 1), name: WDS_VENDORS[vd].name, top: 1 }\n'
          '        : { url: WDS_VENDORS[vd].url, model: wdsPickModel(vd, umodel, 0), name: WDS_VENDORS[vd].name };')
h = h.replace(OLD_M1, NEW_M1, 1)

OLD_M2 = '      const VC = wdsTopVC(vd);                 // 成文＝最费脑的一步，直接最强档'
assert OLD_M2 in h, "distill VC 锚点"
NEW_M2 = ('      const VC = { url: WDS_VENDORS[vd].url, model: wdsPickModel(vd, String(b.model || ""), 1), name: WDS_VENDORS[vd].name, top: 1 };  // 成文＝最费脑的一步，直接最强档')
h = h.replace(OLD_M2, NEW_M2, 1)

# ───────── ⑥ /api/wds/ping ─────────
ANCHOR = '    // /api/wds/websearch：独立的联网搜索端点'
assert ANCHOR in h, "ping 插入锚点"
PING = '''    // /api/wds/ping：只验一次「这把 Key + 这个型号 + 这家地址」通不通，不产内容、不进检索、不计对话额度。
    // 存在的理由很实在：各家型号改名下线的节奏比本站改代码快，读者得能自己当场验证，而不是对着一句"基底返回错误"猜。
    if (url.pathname === "/api/wds/ping") {
      if (request.method === "OPTIONS") return new Response(null, { headers: _cors() });
      if (request.method !== "POST") return new Response("Method Not Allowed", { status: 405 });
      let b = {}; try { b = await request.json(); } catch (e) {}
      const vd = wdsVendorOf(b.vendor);
      const key = String(b.key || "").trim();
      if (key.length < 8) return Response.json({ ok: false, code: "need_key", msg: "先填这家的 Key。" }, { headers: _cors() });
      const model = wdsPickModel(vd, String(b.model || ""), !!b.deep);
      const ctrl = new AbortController();
      const timer = setTimeout(() => { try { ctrl.abort(); } catch (e) {} }, 25000);
      try {
        const r = await fetch(WDS_VENDORS[vd].url, {
          method: "POST",
          headers: { "content-type": "application/json", authorization: "Bearer " + key },
          body: JSON.stringify({ model, stream: false, max_tokens: 16, messages: [{ role: "user", content: "ping" }] }),
          signal: ctrl.signal,
        });
        if (r.ok) return Response.json({ ok: true, vendor: vd, model, name: WDS_VENDORS[vd].name }, { headers: _cors() });
        const txt = (await r.text()).slice(0, 300);
        const code = (r.status === 401 || r.status === 403) ? "bad_key" : (r.status === 402 ? "no_credit" : (r.status === 404 || /model/i.test(txt) ? "bad_model" : "http"));
        return Response.json({ ok: false, code, status: r.status, model, msg: txt }, { headers: _cors() });
      } catch (e) {
        return Response.json({ ok: false, code: "net", model, msg: (e && e.message) || "connect failed" }, { headers: _cors() });
      } finally { clearTimeout(timer); }
    }

'''
h = h.replace(ANCHOR, PING + ANCHOR, 1)

assert h != o
P.write_text(h, encoding="utf-8")
print("worker 5-vendor patch OK; delta =", len(h) - len(o))
