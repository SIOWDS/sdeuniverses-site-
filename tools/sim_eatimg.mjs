// 朋友圈第二台智能体「吃图出金句」的模拟——把页面里那段真代码抠出来，用假 DOM、假 fetch、假 localStorage 跑。
// 跑法：node tools/sim_eatimg.mjs
import fs from "fs";

const HTML = fs.readFileSync(new URL("../public/sde-wechat/index.html", import.meta.url), "utf8");
let pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; console.log("  \u2713 " + name); }
  else { fail++; console.log("  \u2717 " + name + (extra !== undefined ? "  \u2190 " + JSON.stringify(extra).slice(0, 300) : "")); }
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/* ── 0. 静态校验 ── */
const a = HTML.indexOf("/* \u5403\u56fe\u51fa\u91d1\u53e5\uff1a");
const z = HTML.indexOf("/* \u65b0\u6d88\u606f\uff08\u8c01\u8d5e\u4e86\u6211", a);
ok("\u80fd\u627e\u5230\u5403\u56fe\u5757", a > 0 && z > a, { a, z });
const BLOCK = HTML.slice(a, z);
const ids = [...new Set([...BLOCK.matchAll(/el\("([^"]+)"\)/g)].map((m) => m[1]))];
for (const id of ids) ok("id \u5b58\u5728\uff1a" + id, HTML.indexOf('id="' + id + '"') >= 0);
ok("\u4e24\u53f0\u673a\u5668\u5404\u81ea\u6709\u62ac\u5934", /\u2460 <b>SDE\u91d1\u53e5\u751f\u4ea7\u673a<\/b>/.test(HTML) && /\u2461 <b>\u5403\u56fe\u51fa\u91d1\u53e5<\/b>/.test(HTML));
ok("\u8f93\u51fa\u533a\u4e24\u5757\u4e0d\u5171\u7528", HTML.indexOf('id="mu-out"') >= 0 && HTML.indexOf('id="ic-out"') >= 0);
ok("\u8fdb\u53d1\u8868\u9875\u4e5f\u6e05\u7a7a\u5403\u56fe\u7684\u8f93\u51fa", /moOpenPost\(\)\{[\s\S]{0,260}el\("ic-out"\)\.textContent=""/.test(HTML));
ok("\u9875\u9762\u4e0a\u5199\u660e Key \u53ea\u5b58\u672c\u673a", /Key \u53ea\u5b58\u5728\u4f60\u672c\u673a[\s\S]{0,40}\u672c\u7ad9\u670d\u52a1\u5668\u4e0d\u7ecf\u624b/.test(HTML));

/* ── 1. 假环境 ── */
function mkNode(tag) {
  return {
    tag, className: "", _txt: "", style: {}, children: [], disabled: false, value: "", placeholder: "",
    onclick: null, onchange: null, _listeners: {},
    get textContent() { return this._txt; },
    set textContent(v) { this._txt = v; this.children = []; },
    appendChild(c) { this.children.push(c); return c; },
    addEventListener(k, fn) { (this._listeners[k] = this._listeners[k] || []).push(fn); },
    emit(k) { (this._listeners[k] || []).forEach((fn) => fn.call(this)); },
    focus() { this.focused = true; },
    click() { if (this.onclick) this.onclick(); },
    // 渲染出来的整段文字（含子节点），用来断言
    get deep() { return this._txt + this.children.map((c) => c.deep !== undefined ? c.deep : (c.textContent || "")).join(""); },
  };
}
const NODES = {};
for (const id of ["ic-vd", "ic-kind", "ic-key", "ic-model", "ic-go", "ic-out", "mp-text", "mp-msg"]) NODES[id] = mkNode("div");
NODES["ic-vd"].value = "glm";
NODES["ic-kind"].value = "asis";
NODES["ic-go"].textContent = "\u5403\u56fe\u51fa\u91d1\u53e5";
global.el = (id) => NODES[id] || (NODES[id] = mkNode("div"));
global.mkEl = (t, c, x) => { const n = mkNode(t); n.className = c || ""; if (x != null) n.textContent = x; return n; };

const LS = new Map();
global.localStorage = { getItem: (k) => (LS.has(k) ? LS.get(k) : null), setItem: (k, v) => LS.set(k, String(v)), removeItem: (k) => LS.delete(k) };
global.document = {
  createTextNode: (s) => ({ tag: "#text", textContent: s, children: [], deep: s }),
  createElement: (t) => (t === "canvas"
    ? { width: 0, height: 0, getContext: () => ({ fillRect() {}, drawImage() {} }), toDataURL: () => "data:image/jpeg;base64,SMALL" }
    : mkNode(t)),
};
global.Image = class { set src(v) { this.width = 2000; this.height = 1000; setTimeout(() => this.onload && this.onload(), 0); } };

let REQ = null, RESP = null;
global.fetch = (url, init) => {
  REQ = { url, init };
  if (RESP && RESP.throw) return Promise.reject(RESP.throw);
  if (RESP && RESP.hang) {
    return new Promise((_, rej) => {
      init.signal.addEventListener("abort", () => { const e = new Error("aborted"); e.name = "AbortError"; rej(e); });
    });
  }
  return Promise.resolve({ status: RESP.status, text: () => Promise.resolve(RESP.body) });
};

let moPick = [];
global.__pick = (v) => { moPick = v; };
Object.defineProperty(global, "moPick", { get: () => moPick });

/* ── 2. 装载真代码 ── */
eval(BLOCK + ";globalThis.__unlock=function(){icBusy=false;};");   // 拿一个把手去解锁，不改真代码
const go = NODES["ic-go"];
ok("\u6309\u94ae\u5df2\u63a5\u7ebf", typeof go.onclick === "function");
ok("\u5f00\u673a\u5c31\u628a\u578b\u53f7\u9ed8\u8ba4\u5199\u8fdb placeholder", /glm-5v/.test(NODES["ic-model"].placeholder), NODES["ic-model"].placeholder);

const env1 = (c) => JSON.stringify({ choices: [{ message: { content: c } }] });
const GOOD = JSON.stringify({
  see: ["\u684c\u4e0a\u4e00\u676f\u51c9\u6389\u7684\u8336", "\u5c4f\u5e55\u4eae\u7740", "\u7a97\u5916\u5929\u9ed1\u4e86"],
  s: "\u663e\u51fa\u4e86\u684c\u9762\uff0c\u906e\u4f4f\u4e86\u684c\u5b50\u4ee5\u5916\u7684\u4e00\u6574\u5929",
  d: "\u4eae\u7740\u7684\u5c4f\u5e55\u4e0e\u9ed1\u4e0b\u53bb\u7684\u7a97\u4e4b\u95f4",
  e: "\u8336\u51c9\u4e0e\u5750\u4e45\u4e92\u4e3a\u6761\u4ef6",
  lines: [
    { g: "S\u663e", t: "\u8336\u51c9\u4e86\u624d\u770b\u89c1\u81ea\u5df1\u5750\u4e86\u591a\u4e45" },
    { g: "S\u906e", t: "\u753b\u6846\u5916\u90a3\u4e00\u6574\u5929\u6ca1\u4eba\u62cd" },
    { g: "D", t: "\u5c4f\u5e55\u8fd8\u4eae\u7740\uff0c\u7a97\u5df2\u7ecf\u9ed1\u4e86" },
    { g: "D\u53cd", t: "\u4e0d\u662f\u5929\u9ed1\u5f97\u5feb\uff0c\u662f\u6ca1\u4eba\u53eb\u505c" },
    { g: "E", t: "\u8fd9\u676f\u8336\u6bcf\u51c9\u4e00\u6b21\uff0c\u5c31\u591a\u4e00\u6bb5\u5750\u7740\u7684\u65f6\u95f4" },
  ],
});

console.log("\n=== 1. \u6ca1\u56fe\u4e0e\u6ca1 Key\uff1a\u4e0d\u53d1\u8bf7\u6c42\uff0c\u76f4\u63a5\u8bf4\u4eba\u8bdd ===");
REQ = null; RESP = { status: 200, body: env1(GOOD) };
go.click();
ok("\u6ca1\u56fe\u4e0d\u53d1", REQ === null && /\u5148\u5728\u4e0b\u9762\u653e\u4e00\u5f20\u56fe/.test(NODES["ic-out"].children[0].textContent), NODES["ic-out"].children[0] && NODES["ic-out"].children[0].textContent);
global.__pick(["AAA", "BBB", "CCC"]);
go.click();
ok("\u6ca1 Key \u4e0d\u53d1\uff0c\u5e76\u544a\u8bc9\u53bb\u54ea\u7533", REQ === null && /open\.bigmodel\.cn/.test(NODES["ic-out"].children[0].textContent), NODES["ic-out"].children[0].textContent);

console.log("\n=== 2. \u6b63\u5e38\u4e00\u8dd1\uff1a\u76f4\u8fde\u5382\u5546\u3001\u56fe\u53e6\u7f29\u3001\u6700\u591a\u4e24\u5f20 ===");
NODES["ic-key"].value = "sk-glm-1234567890";
NODES["ic-key"].emit("input");
ok("Key \u8f93\u5165\u5373\u5b58\u672c\u673a", LS.get("sde_glm_key") === "sk-glm-1234567890", [...LS]);
go.click();
await sleep(20);
ok("\u53d1\u5230\u667a\u8c31\u5b98\u65b9\u7aef\u70b9", REQ.url === "https://open.bigmodel.cn/api/paas/v4/chat/completions", REQ.url);
ok("\u5e26\u4e86 Authorization", REQ.init.headers.authorization === "Bearer sk-glm-1234567890");
ok("\u6ca1\u7ecf\u672c\u7ad9\u4e2d\u8f6c", !/llm-proxy/.test(REQ.url) && !REQ.init.headers["x-target-url"]);
const body = JSON.parse(REQ.init.body);
ok("\u9ed8\u8ba4\u578b\u53f7 glm-5v", body.model === "glm-5v", body.model);
ok("system \u662f\u5403\u56fe\u89c4\u7a0b", /\u4e09\u683c\u89e3\u6784/.test(body.messages[0].content));
ok("\u4e09\u6b65\u4e0e\u4e94\u673a\u4f4d\u90fd\u5199\u8fdb\u4e86 system", /S\u663e/.test(body.messages[0].content) && /\u4e0d\u8bb8\u4e24\u53e5\u540c\u4f4d/.test(body.messages[0].content));
ok("\u4e0d\u8bb8\u7f16\u56fe\u91cc\u6ca1\u6709\u7684\u4e1c\u897f", /\u4e0d\u8bb8\u5199\u56fe\u91cc\u6ca1\u6709\u7684\u4e1c\u897f/.test(body.messages[0].content));
ok("user \u662f\u6570\u7ec4\u3001\u6587\u5b57\u5728\u524d", Array.isArray(body.messages[1].content) && body.messages[1].content[0].type === "text");
ok("\u53ea\u9001\u4e24\u5f20\u56fe", body.messages[1].content.filter((c) => c.type === "image_url").length === 2);
ok("\u9001\u7684\u662f\u53e6\u7f29\u8fc7\u7684", body.messages[1].content.filter((c) => c.type === "image_url").every((c) => c.image_url.url === "data:image/jpeg;base64,SMALL"));
ok("\u53e3\u5473\u8fdb\u4e86\u63d0\u793a", /\u5c31\u56fe\u8bf4\u56fe/.test(body.messages[1].content[0].text));

console.log("\n=== 3. \u6e32\u67d3\uff1a\u5148\u7ed9\u89e3\u6784\uff0c\u518d\u7ed9\u4e94\u53e5\uff0c\u70b9\u4e00\u53e5\u53ea\u586b\u53e5\u5b50 ===");
const out = NODES["ic-out"];
ok("\u89e3\u6784\u5757\u5728\u6700\u4e0a\u9762", out.children[0].className === "ic-see", out.children.map((c) => c.className));
ok("\u770b\u89c1/\u663e\u9732/\u5dee\u5f02/\u7ea0\u7f20\u56db\u884c\u90fd\u5728", out.children[0].children.length === 4, out.children[0].children.length);
ok("\u770b\u89c1\u90a3\u884c\u771f\u5199\u4e86\u4e1c\u897f", /\u51c9\u6389\u7684\u8336/.test(out.children[0].deep), out.children[0].deep);
const items = out.children.filter((c) => c.className === "mu-item");
ok("\u4e94\u6761\u5019\u9009", items.length === 5, items.length);
ok("\u6bcf\u6761\u5e26\u673a\u4f4d\u89d2\u6807", items[0].children[0].children[0].className === "mu-tag", items[0].children[0].children.map((c) => c.className));
items[3].click();
ok("\u70b9\u4e00\u6761\u53ea\u586b\u53e5\u5b50\u3001\u4e0d\u5e26\u89d2\u6807", NODES["mp-text"].value === "\u4e0d\u662f\u5929\u9ed1\u5f97\u5feb\uff0c\u662f\u6ca1\u4eba\u53eb\u505c", NODES["mp-text"].value);
ok("\u672b\u5c3e\u6709\u518d\u5403\u4e00\u904d", out.children[out.children.length - 1].className === "mu-again");

console.log("\n=== 4. \u578b\u53f7\u8986\u76d6\u4e0e\u6362\u5bb6\uff1aKey \u5206\u5b58\u4e0d\u4e92\u8986 ===");
NODES["ic-model"].value = "glm-4.6v";
go.click(); await sleep(20);
ok("\u578b\u53f7\u8986\u76d6\u751f\u6548", JSON.parse(REQ.init.body).model === "glm-4.6v");
NODES["ic-model"].value = "";
NODES["ic-vd"].value = "qwen"; NODES["ic-vd"].onchange();
ok("\u6362\u5bb6\u540e Key \u6846\u6e05\u7a7a\uff08\u5343\u95ee\u8fd8\u6ca1\u5b58\u8fc7\uff09", NODES["ic-key"].value === "", NODES["ic-key"].value);
ok("\u578b\u53f7\u5360\u4f4d\u4e5f\u8ddf\u7740\u6362", /qwen-vl-max/.test(NODES["ic-model"].placeholder));
NODES["ic-key"].value = "sk-qwen-abcdefgh"; NODES["ic-key"].emit("input");
go.click(); await sleep(20);
ok("\u53d1\u5230\u767e\u70bc\u7aef\u70b9", /dashscope\.aliyuncs\.com/.test(REQ.url), REQ.url);
ok("\u7528\u7684\u662f\u5343\u95ee\u7684 Key", REQ.init.headers.authorization === "Bearer sk-qwen-abcdefgh");
ok("\u667a\u8c31\u7684 Key \u6ca1\u88ab\u8986\u6389", LS.get("sde_glm_key") === "sk-glm-1234567890", [...LS]);
NODES["ic-vd"].value = "glm"; NODES["ic-vd"].onchange();
ok("\u6362\u56de\u667a\u8c31\u81ea\u52a8\u5e26\u51fa\u65e7 Key", NODES["ic-key"].value === "sk-glm-1234567890");
ok("\u8bb0\u4f4f\u4e0a\u6b21\u9009\u7684\u5bb6", LS.get("sde_ic_vd") === "glm", LS.get("sde_ic_vd"));
NODES["ic-key"].value = ""; NODES["ic-key"].emit("input");
ok("\u6e05\u7a7a\u8f93\u5165\u6846\u4e0d\u4f1a\u8bef\u5220\u5b58\u6863", LS.get("sde_glm_key") === "sk-glm-1234567890");
NODES["ic-key"].value = "sk-glm-1234567890";

console.log("\n=== 5. GPT \u8d70\u672c\u7ad9\u4e2d\u8f6c\uff08\u5b83\u6ca1\u6709 CORS\uff09===");
NODES["ic-vd"].value = "gpt"; NODES["ic-vd"].onchange();
NODES["ic-key"].value = "sk-openai-zzzzzzzz"; NODES["ic-key"].emit("input");
go.click(); await sleep(20);
ok("\u53d1\u5230 /api/llm-proxy", REQ.url === "/api/llm-proxy", REQ.url);
ok("\u5e26 x-target-url \u6307\u5411\u5b98\u65b9\u7aef\u70b9", REQ.init.headers["x-target-url"] === "https://api.openai.com/v1/chat/completions", REQ.init.headers);
NODES["ic-vd"].value = "glm"; NODES["ic-vd"].onchange();

console.log("\n=== 6. \u5404\u79cd\u574f\u60c5\u51b5\u5404\u8bf4\u5404\u7684\u8bdd ===");
async function bad(resp) { RESP = resp; go.click(); await sleep(20); return NODES["ic-out"].children[0].textContent; }
ok("401 \u8bf4 Key \u7528\u4e0d\u4e86", /Key \u7528\u4e0d\u4e86\uff08401\uff09/.test(await bad({ status: 401, body: "{}" })));
ok("429 \u8bf4\u4f59\u989d\u6216\u592a\u5feb", /\uff08429\uff09/.test(await bad({ status: 429, body: "{}" })));
ok("500 \u628a\u5382\u5546\u7684\u8bdd\u900f\u51fa\u6765", /500[\s\S]*boom/.test(await bad({ status: 500, body: JSON.stringify({ error: { message: "boom" } }) })));
ok("\u4e0d\u662f JSON \u65f6\u8bf4\u5f97\u6e05\u695a", /\u6ca1\u6309\u683c\u5f0f\u56de/.test(await bad({ status: 200, body: env1("\u597d\u7684\uff0c\u6211\u770b\u5230\u4e86\u4e00\u5f20\u56fe") })));
ok("\u7f51\u7edc/\u8de8\u57df\u5f02\u5e38\u7ed9\u51fa\u8def", /CORS|\u6362\u4e00\u5bb6/.test(await bad({ throw: new TypeError("Failed to fetch") })));

console.log("\n=== 7. \u6302\u6b7b\u65f6\u81ea\u5df1\u6389\u95f8\uff08\u4e0d\u80fd\u6c38\u8fdc\u8f6c\u5708\uff09===");
RESP = { hang: 1 };
go.click();
await sleep(5);
ok("\u6b63\u5728\u770b\u56fe\u65f6\u518d\u70b9\u4e0d\u91cd\u53d1", (function () { const u = REQ.url; go.click(); return REQ.url === u; })());
ok("\u6309\u94ae\u5df2\u9501", go.disabled === true);

console.log("\n=== 8. \u56de\u5f97\u4e71\u4e5f\u80fd\u6d17\uff1a\u56f4\u680f\u3001\u53bb\u91cd\u3001\u957f\u77ed\u3001\u5c01\u9876\u4e94\u6761 ===");
// 先把上一发挂着的请求放掉（abort 由 90 秒兜底，这里直接换个响应重来）
RESP = { status: 200, body: env1("```json\n" + JSON.stringify({
  see: ["\u4e00\u53ea\u732b"], s: "", d: "", e: "",
  lines: ["\u597d", "\u91cd\u590d\u7684\u90a3\u4e00\u53e5\u8bdd\u5199\u5f97\u5177\u4f53", "\u91cd\u590d\u7684\u90a3\u4e00\u53e5\u8bdd\u5199\u5f97\u5177\u4f53", "\u5341".repeat(70),
    { g: "D", t: "\u732b\u5750\u5728\u952e\u76d8\u4e0a\u65f6\uff0c\u5b83\u624d\u662f\u4e3b\u4eba" }, { g: "E", t: "\u4f60\u63a8\u5f00\u5b83\u7684\u90a3\u4e00\u4e0b\uff0c\u5b83\u624d\u771f\u5750\u4e0b" },
    { g: "S", t: "\u7b2c\u4e09\u53e5\u5199\u5f97\u5177\u4f53\u4e00\u70b9\u513f" }, { g: "S", t: "\u7b2c\u56db\u53e5\u5199\u5f97\u5177\u4f53\u4e00\u70b9\u513f" }, { g: "S", t: "\u7b2c\u4e94\u53e5\u5199\u5f97\u5177\u4f53\u4e00\u70b9\u513f" }] }) + "\n```") };
global.__unlock(); go.disabled = false;         // 放掉上一发的锁（真实里由 90 秒 abort 解）
go.click(); await sleep(20);
const it2 = NODES["ic-out"].children.filter((c) => c.className === "mu-item");
ok("\u5c01\u9876\u4e94\u6761", it2.length === 5, it2.length);
ok("\u8fc7\u77ed\u7684\u4e22\u4e86", !it2.some((c) => c.deep.indexOf("\u597d") === 0));
ok("\u91cd\u590d\u7684\u53ea\u7559\u4e00\u6761", it2.filter((c) => /\u91cd\u590d\u7684\u90a3\u4e00\u53e5/.test(c.deep)).length === 1);
ok("\u8fc7\u957f\u7684\u4e22\u4e86", !it2.some((c) => c.deep.length > 70));
ok("\u6ca1\u7ed9\u89e3\u6784\u65f6\u53ea\u6e32\u770b\u89c1\u4e00\u884c", NODES["ic-out"].children[0].children.length === 1);

console.log("\n" + (fail ? "\u2717 " : "\u2713 ") + pass + " \u9879\u901a\u8fc7\uff0c" + fail + " \u9879\u5931\u8d25\n");
process.exit(fail ? 1 : 0);
