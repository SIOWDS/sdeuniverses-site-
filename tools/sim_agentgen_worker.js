/* 智能体生成器 Worker 端点护栏：node tools/sim_agentgen_worker.js
   抽出 worker.js 里 /api/wds/agentgen 端点与它依赖的真函数（厂商表、wdsFetchMax、wdsUp、wdsPlainBody…），
   mock 上游，逐家跑：路由、system 不可注入、预算阶梯、思考关闭、GPT/Claude 口径、缺 Key、空需求、超长。 */
const fs = require("fs");
const W = fs.readFileSync(__dirname + "/../src/worker.js", "utf8");
function grab(re) { const m = W.match(re); if (!m) throw new Error("grab fail " + re); return m[0]; }
function fnSrc(name) {   // 顶层函数：从 function name( 起，到下一个行首的 } 止（字符串里的花括号不干扰）
  const m = W.match(new RegExp("\\n(async )?function " + name + "\\([^\\n]*"));
  if (!m) throw new Error("no fn " + name);
  const a = m.index;
  if (/\}\s*$/.test(m[0]) && m[0].indexOf("{") > 0) return m[0];          // 一行写完的
  const e = W.indexOf("\n}", a + 1);
  return W.slice(a, e + 2);
}
function constObj(name) {   // 顶层常量表：到下一个行首的 }; 止（单行的取到行尾）
  const a = W.indexOf("\nconst " + name + " = {");
  if (a < 0) throw new Error("no const " + name);
  const line = W.slice(a + 1, W.indexOf("\n", a + 1));
  if (/\};?\s*(\/\/.*)?$/.test(line)) return line + "\n";
  const e = W.indexOf("\n}", a + 1);
  return W.slice(a, W.indexOf("\n", e + 1)) + "\n";
}
const parts = [
  grab(/const WDS_GPT_MODEL = .*\n/),
  constObj("WDS_TOP_MODEL"), constObj("WDS_VENDORS"), constObj("WDS_VMAP"),
  grab(/const WDS_EFFORT_CAP = .*\n/), grab(/const WDS_EFFORT_ORDER = .*\n/),
  grab(/const BYOK_NO_DAY = .*\n/),
  grab(/const AGENTGEN_PER_MIN = .*\n/),
  grab(/const AGENTGEN_SYS = `[\s\S]*?`;\n/),
  "function wdsTopBody(VC, body) { return body; }\n",
  ...["wdsVendorOf", "wdsUpFix", "wdsEffortPick", "wdsUp", "wdsFetchMax", "wdsPlainBody", "wdsMiniSplit", "glmAlwaysThinks", "limitRead", "_lhash", "wdsBucket", "_cors"].map(fnSrc),
].join("\n");
const a = W.indexOf('if (url.pathname === "/api/wds/agentgen") {');
const b = W.indexOf('if (url.pathname === "/api/wds/summarize") {', a);
if (a < 0 || b < 0) throw new Error("endpoint block not found");
const blk = W.slice(a, b);
const src = `${parts}
module.exports = async function run(body, upstream, limiterOk) {
  globalThis.fetch = upstream;
  const url = { pathname: "/api/wds/agentgen" };
  const env = {};
  const _do = () => ({ idFromName: () => 1, get: () => ({ fetch: async () => new Response(JSON.stringify({ ok: limiterOk !== false })) }) });
  const request = new Request("https://x/api/wds/agentgen", { method: "POST", body: JSON.stringify(body) });
  ${blk}
  return null;
};`;
const tmp = __dirname + "/_built_agentgen.js";
fs.writeFileSync(tmp, src);
const run = require(tmp);
fs.unlinkSync(tmp);

let pass = 0, fail = 0;
function ok(c, msg) { if (c) { pass++; } else { fail++; console.log("✗ " + msg); } }
const SSE = 'data: {"choices":[{"delta":{"content":"===META==="}}]}\n\ndata: [DONE]\n\n';
function upstream(calls, rejectFirst) {
  return async (u, init) => {
    const body = JSON.parse(init.body);
    calls.push({ u, body, auth: init.headers.authorization });
    if (rejectFirst && calls.length === 1) return new Response('{"error":{"message":"max_tokens out of range"}}', { status: 400 });
    return new Response(SSE, { status: 200, headers: { "content-type": "text/event-stream" } });
  };
}
(async () => {
  const K = "sk-1234567890";
  // ① DeepSeek 标准档：system 不可注入、只收 user/assistant、思考关、预算阶梯
  let calls = [];
  let r = await run({ vendor: "ds", key: K, messages: [{ role: "system", content: "HACK" }, { role: "user", content: "做个审稿助手" }, { role: "tool", content: "x" }] }, upstream(calls, true));
  const txt = await r.text();
  ok(r.status === 200 && /event-stream/.test(r.headers.get("content-type")), "ds 应流式 200");
  ok(txt.indexOf("===META===") >= 0, "流应原样回传");
  ok(calls.length === 2 && calls[0].body.max_tokens === 24000 && calls[1].body.max_tokens === 16000, "预算阶梯 24000→16000，实得 " + calls.map((c) => c.body.max_tokens));
  const m = calls[1].body.messages;
  ok(m.length === 2 && m[0].role === "system" && m[0].content.indexOf("你是「智能体设计师」") === 0 && m[1].role === "user", "system 只能是服务端那份：" + m.map((x) => x.role));
  ok(JSON.stringify(m).indexOf("HACK") < 0, "读者传的 system 不得进上游");
  ok(calls[1].body.thinking && calls[1].body.thinking.type === "disabled", "DeepSeek 应关思考");
  ok(calls[1].body.stream === true && calls[1].body.model === "deepseek-v4-flash", "标准档型号/流：" + calls[1].body.model);
  ok(calls[1].auth === "Bearer " + K, "Key 走 Bearer");
  ok(r.headers.get("x-agentgen-model") === "deepseek-v4-flash", "回报所用型号");
  // ② GPT 深度档：max_completion_tokens、reasoning_effort none
  calls = [];
  r = await run({ vendor: "gpt", key: K, deep: 1, messages: [{ role: "user", content: "x" }] }, upstream(calls)); await r.text();
  ok(calls[0].u.indexOf("api.openai.com") >= 0 && calls[0].body.model === "gpt-6-astra", "GPT 深度档型号：" + calls[0].body.model);
  ok(calls[0].body.max_completion_tokens === 24000 && calls[0].body.max_tokens == null, "GPT 用 max_completion_tokens");
  ok(calls[0].body.reasoning_effort === "none", "GPT 关思考＝none");
  // ③ Claude 标准档 / 读者自定型号 / 非法型号名
  calls = [];
  r = await run({ vendor: "cl", key: K, messages: [{ role: "user", content: "x" }] }, upstream(calls)); await r.text();
  ok(calls[0].body.model === "claude-sonnet-5-5", "Claude 标准档：" + calls[0].body.model);
  calls = [];
  r = await run({ vendor: "glm", key: K, model: "glm-5", messages: [{ role: "user", content: "x" }] }, upstream(calls)); await r.text();
  ok(calls[0].body.model === "glm-5" && calls[0].u.indexOf("bigmodel.cn") >= 0, "自定型号应生效");
  calls = [];
  r = await run({ vendor: "glm", key: K, model: "bad model;drop", messages: [{ role: "user", content: "x" }] }, upstream(calls)); await r.text();
  ok(calls[0].body.model === "glm-5.3-flash", "非法型号名应退回默认");
  // ④ 各家都能路由
  for (const v of ["ds", "glm", "kimi", "qwen", "mm", "mmcn", "cl", "gpt", "or", "nv"]) {
    calls = [];
    r = await run({ vendor: v, key: K, messages: [{ role: "user", content: "x" }] }, upstream(calls)); await r.text();
    ok(r.status === 200 && calls.length === 1, "厂商 " + v + " 应可路由");
  }
  // ⑤ 拒绝路径
  r = await run({ vendor: "ds", key: "short", messages: [{ role: "user", content: "x" }] }, upstream([]));
  ok(r.status === 400 && (await r.json()).code === "need_key", "缺 Key 应 400 need_key");
  r = await run({ vendor: "ds", key: K, messages: [] }, upstream([]));
  ok(r.status === 400, "空需求应 400");
  r = await run({ vendor: "ds", key: K, messages: [{ role: "assistant", content: "x" }] }, upstream([]));
  ok(r.status === 400, "首条非 user 应 400");
  r = await run({ vendor: "ds", key: K, messages: [{ role: "user", content: "x".repeat(150000) }, { role: "assistant", content: "y".repeat(150000) }] }, upstream([]));
  ok(r.status === 400, "超长应 400");
  r = await run({ vendor: "ds", key: K, messages: [{ role: "user", content: "x" }] }, upstream([]), false);
  ok(r.status === 429, "限流应 429");
  r = await run({ vendor: "ds", key: K, messages: [{ role: "user", content: "x" }] }, async () => new Response("bad key", { status: 401 }));
  const j = await r.json();
  ok(r.status === 502 && /Key 无效/.test(j.msg), "上游 401 应说清 Key 无效：" + j.msg);
  // ⑥ 提示词与模板一致：内置工具名
  for (const n of ["read_file", "write_file", "list_files", "fetch_url", "now"]) ok(W.indexOf(n) > 0, "设计师提示词应列内置工具 " + n);
  const builtins = fs.readFileSync(__dirname + "/../public/taste/agent-maker/template/core/builtins.py", "utf8");
  for (const n of ["read_file", "write_file", "list_files", "fetch_url", "now"]) ok(builtins.indexOf('"' + n + '"') > 0, "模板应提供内置工具 " + n);
  console.log((fail ? "✗ " : "✓ ") + pass + " 过 / " + fail + " 败");
  process.exit(fail ? 1 : 0);
})();
