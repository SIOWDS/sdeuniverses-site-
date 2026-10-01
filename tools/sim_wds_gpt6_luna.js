/* Exercise the bundled Worker model endpoint, probe routes and adapter without API keys.
   Requires esbuild (also used by Wrangler); set NODE_PATH to its installation if needed. */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const esbuild = require("esbuild");
const calls = [];
const sandbox = {
  console, URL, Request, Response, Headers, TextEncoder, TextDecoder,
  AbortController, ReadableStream, TransformStream, crypto: globalThis.crypto,
  setTimeout, clearTimeout, setInterval, clearInterval, atob, btoa,
  fetch: async (url, init) => {
    assert.equal(String(url), "https://api.openai.com/v1/chat/completions");
    calls.push({ url: String(url), body: JSON.parse(init.body), headers: init.headers });
    return Response.json({ choices: [{ message: { role: "assistant", content: "OK" }, finish_reason: "stop" }] });
  },
};
const source = fs.readFileSync(path.join(__dirname, "../src/worker.js"), "utf8")
  + "\nglobalThis.api = { wdsStdVC, wdsTopVC, wdsPickModel, wdsVisionLadder, wdsFetchMax };";
// Match Wrangler's bundled execution rather than evaluating its unbundled source as a script.
const built = esbuild.buildSync({
  stdin: { contents: source, resolveDir: path.join(__dirname, "../src"), sourcefile: "worker.js" },
  bundle: true, write: false, platform: "browser", format: "iife", globalName: "SDEWorker",
}).outputFiles[0].text;
vm.runInNewContext(built, sandbox);
sandbox.worker = sandbox.SDEWorker.default;
const api = sandbox.api;
const request = (route, body) => new Request("https://sdeuniverses.com" + route,
  body ? { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) } : undefined);
async function run() {
  const models = await (await sandbox.worker.fetch(request("/api/wds/models"), {}, {})).json();
  assert.equal(models.ok, true);
  for (const tier of ["lite", "std", "top", "vis"]) {
    assert.equal(models.v.gpt[tier], "gpt-6-luna", "published model tier: " + tier);
    const probe = await (await sandbox.worker.fetch(request("/api/wds/ping", {
      vendor: "gpt", tier, key: "local-test-key-only",
    }), {}, {})).json();
    assert.equal(probe.ok, true);
    assert.equal(probe.model, "gpt-6-luna");
    const sent = calls.at(-1).body;
    assert.equal(sent.model, "gpt-6-luna");
    assert.equal(sent.reasoning_effort, "none");
    assert.equal(sent.max_completion_tokens, 64);
    assert.equal("max_tokens" in sent, false);
    if (tier === "vis") assert.equal(sent.messages[0].content[1].type, "image_url");
  }
  assert.deepEqual(Array.from(api.wdsVisionLadder("openai", "")), ["gpt-6-luna"], "vision has no automatic costly fallback");
  for (const [mode, vc, plain, expectedEffort] of [
    ["standard", api.wdsStdVC("openai", ""), false, "low"],
    ["deep", api.wdsTopVC("openai", ""), false, "high"],
    ["maximum effort", { ...api.wdsTopVC("openai", ""), effort: "max" }, false, "max"],
    ["plain long-form", api.wdsTopVC("openai", ""), true, "none"],
  ]) {
    await api.wdsFetchMax(vc, "local-test-key-only", [{ role: "user", content: "Test" }], true,
      1024, new AbortController().signal, true, [1024], plain);
    const sent = calls.at(-1).body;
    assert.equal(sent.model, "gpt-6-luna", mode);
    assert.equal(sent.reasoning_effort, expectedEffort, mode);
    assert.equal(sent.stream, true);
    assert.equal(sent.max_completion_tokens, 1024);
    for (const field of ["max_tokens", "temperature", "top_p", "presence_penalty", "frequency_penalty"])
      assert.equal(field in sent, false, mode + ": " + field);
  }
  assert.equal(api.wdsTopVC("openai", "gpt-6-sol").model, "gpt-6-sol", "explicit model selection is preserved");
  assert.equal(api.wdsStdVC("openai", "bad model").model, "gpt-6-luna", "invalid overrides use the requested default");
  assert.equal(models.v.ds.std, "deepseek-v4-flash");
  assert.equal(models.v.ds.top, "deepseek-v4-pro");
  console.log("PASS: GPT-6 Luna model listing, all four probe routes, four streaming request modes, overrides and other providers (8 mocked upstream requests; no network).");
}
run().catch(error => { console.error(error); process.exitCode = 1; });
