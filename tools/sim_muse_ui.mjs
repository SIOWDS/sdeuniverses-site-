// 朋友圈「SDE金句生产机」前端块的模拟——把页面里那段真代码抠出来，用假 DOM 跑。
// 跑法：node tools/sim_muse_ui.mjs
import fs from "fs";

const HTML = fs.readFileSync(new URL("../public/sde-wechat/index.html", import.meta.url), "utf8");
let pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; console.log("  \u2713 " + name); }
  else { fail++; console.log("  \u2717 " + name + (extra !== undefined ? "  \u2190 " + JSON.stringify(extra).slice(0, 300) : "")); }
}

/* ── 0. 静态校验：新代码里 el("x") 引到的 id，HTML 里必须真有 ── */
const a = HTML.indexOf("/* SDE\u91d1\u53e5\u751f\u4ea7\u673a\uff1a");
const z = HTML.indexOf("/* \u65b0\u6d88\u606f\uff08\u8c01\u8d5e\u4e86\u6211", a);
ok("\u80fd\u5728\u9875\u9762\u91cc\u627e\u5230\u91d1\u53e5\u5757", a > 0 && z > a, { a, z });
const BLOCK = HTML.slice(a, z);
const ids = [...new Set([...BLOCK.matchAll(/el\("([^"]+)"\)/g)].map((m) => m[1]))];
for (const id of ids) ok("id \u5b58\u5728\uff1a" + id, HTML.indexOf('id="' + id + '"') >= 0);
ok("\u6309\u94ae\u3001\u4e0b\u62c9\u3001\u8f93\u51fa\u533a\u90fd\u5728\u53d1\u8868\u9875\u91cc",
  /<div class="mu-bar">[\s\S]*id="mu-go"[\s\S]*id="mu-kind"[\s\S]*<\/div>\s*<div class="mu-out" id="mu-out">/.test(HTML));
ok("\u8fdb\u53d1\u8868\u9875\u65f6\u4f1a\u6e05\u7a7a\u4e0a\u4e00\u6279\u5019\u9009", /moOpenPost\(\)\{[\s\S]{0,200}el\("mu-out"\)\.textContent=""/.test(HTML));

/* ── 1. 假 DOM ── */
function mkNode(tag) {
  return {
    tag, className: "", _txt: "", style: {}, children: [], disabled: false, value: "", onclick: null,
    get textContent() { return this._txt; },
    set textContent(v) { this._txt = v; this.children = []; },
    appendChild(c) { this.children.push(c); return c; },
    focus() { this.focused = true; },
    click() { if (this.onclick) this.onclick(); },
  };
}
const NODES = {};
for (const id of ["mu-go", "mu-kind", "mu-out", "mp-text", "mp-msg"]) NODES[id] = mkNode("div");
NODES["mu-go"].textContent = "\u2728 SDE\u91d1\u53e5\u751f\u4ea7\u673a";
NODES["mu-kind"].value = "auto";
global.el = (id) => NODES[id] || (NODES[id] = mkNode("div"));
global.mkEl = (t, c, x) => { const n = mkNode(t); n.className = c || ""; if (x != null) n.textContent = x; return n; };
let moPick = [];
global.__setPick = (v) => { moPick = v; };
Object.defineProperty(global, "moPick", { get: () => moPick });

let CALLS = [], NEXT = null;
global.api = (op, extra) => { CALLS.push({ op, extra }); return NEXT(); };
global.document = { createElement: (t) => (t === "canvas" ? { width: 0, height: 0, getContext: () => ({ fillRect() {}, drawImage() {} }), toDataURL: () => "data:image/jpeg;base64,SHRUNK" } : mkNode(t)) };
global.Image = class { set src(v) { this.width = 1600; this.height = 900; setTimeout(() => this.onload && this.onload(), 0); } };

/* ── 2. 装载真代码 ── */
eval(BLOCK.replace(/^var muBusy=false;/m, "globalThis.muBusy=false;var muBusy;"));
const muGo = NODES["mu-go"];
ok("\u6309\u94ae\u5df2\u63a5\u7ebf", typeof muGo.onclick === "function");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/* ── 3. \u65e0\u56fe\uff1a\u76f4\u63a5\u53d1 ── */
console.log("\n=== 1. \u65e0\u56fe\uff1a\u76f4\u63a5\u53d1\uff0c\u6309\u94ae\u8fdb\u5165\u201c\u6b63\u5728\u60f3\u201d ===");
CALLS = [];
let resolve1; NEXT = () => new Promise((r) => { resolve1 = r; });
NODES["mp-text"].value = "  \u4eca\u5929\u6539\u7a3f\u5b50  ";
NODES["mu-kind"].value = "flip";
muGo.click();
ok("\u6309\u94ae\u7981\u7528\u5e76\u6539\u6587\u6848", muGo.disabled && /\u6b63\u5728\u60f3/.test(muGo.textContent), muGo.textContent);
await sleep(5);
ok("\u53d1\u4e86\u4e00\u6b21", CALLS.length === 1, CALLS);
ok("op \u4e0e a \u5bf9", CALLS[0].op === "mo" && CALLS[0].extra.a === "muse", CALLS[0]);
ok("\u8349\u7a3f\u53bb\u4e86\u9996\u5c3e\u7a7a\u767d", CALLS[0].extra.seed === "\u4eca\u5929\u6539\u7a3f\u5b50", CALLS[0].extra.seed);
ok("\u53e3\u5473\u8ddf\u7740\u4e0b\u62c9\u8d70", CALLS[0].extra.kind === "flip");
ok("\u6ca1\u56fe\u65f6 imgs \u4e3a\u7a7a", CALLS[0].extra.imgs.length === 0);
muGo.click();
ok("\u6b63\u5728\u60f3\u7684\u65f6\u5019\u518d\u70b9\u4e0d\u4f1a\u91cd\u53d1", CALLS.length === 1, CALLS.length);

console.log("\n=== 2. \u56de\u6765\u4e86\uff1a\u5019\u9009\u53ef\u70b9\uff0c\u70b9\u4e00\u6761\u5c31\u586b\u8fdb\u8f93\u5165\u6846 ===");
resolve1({ s: 200, d: { ok: true, lines: ["\u7b2c\u4e00\u53e5", "\u7b2c\u4e8c\u53e5"], saw: 0, blind: 0, srcs: [{ t: "\u56de\u5199\u7f3a\u5931", u: "/x/" }] } });
await sleep(5);
ok("\u6309\u94ae\u6062\u590d", !muGo.disabled && /\u91d1\u53e5\u751f\u4ea7\u673a/.test(muGo.textContent), muGo.textContent);
const out = NODES["mu-out"];
const items = out.children.filter((c) => c.className === "mu-item");
ok("\u4e24\u6761\u5019\u9009\u90fd\u6e32\u4e0a\u4e86", items.length === 2, out.children.map((c) => c.className));
ok("\u7b2c\u4e00\u884c\u662f\u8bf4\u660e", out.children[0].className === "mu-note" && /\u53d6\u6750\u7ad9\u5185.*\u56de\u5199\u7f3a\u5931/.test(out.children[0].textContent), out.children[0].textContent);
ok("\u672b\u5c3e\u6709\u6362\u4e00\u6279", out.children[out.children.length - 1].className === "mu-again");
items[1].click();
ok("\u70b9\u4e00\u6761\u5c31\u586b\u8fdb\u53bb", NODES["mp-text"].value === "\u7b2c\u4e8c\u53e5", NODES["mp-text"].value);
ok("\u5149\u6807\u56de\u5230\u8f93\u5165\u6846", NODES["mp-text"].focused === true);
ok("\u4e0b\u65b9\u63d0\u793a\u544a\u8bc9\u4ed6\u53ef\u4ee5\u6539", /\u53ef\u4ee5\u76f4\u63a5\u6539/.test(NODES["mp-msg"].textContent));

console.log("\n=== 3. \u6709\u56fe\uff1a\u5148\u53e6\u7f29\u4e00\u9053\u3001\u6700\u591a\u4e24\u5f20 ===");
CALLS = [];
NEXT = () => Promise.resolve({ s: 200, d: { ok: true, lines: ["\u4e00\u53e5"], saw: 2, blind: 0, srcs: [] } });
global.__setPick(["AAA", "BBB", "CCC", "DDD"]);
muGo.click();
await sleep(20);
ok("\u53ea\u9001\u4e24\u5f20", CALLS[0].extra.imgs.length === 2, CALLS[0].extra.imgs);
ok("\u9001\u7684\u662f\u53e6\u7f29\u8fc7\u7684 dataURL", CALLS[0].extra.imgs.every((d) => d === "data:image/jpeg;base64,SHRUNK"));
ok("\u770b\u4e86\u56fe\u7684\u63d0\u793a\u5728", /\u770b\u4e86\u4f60\u7684 2 \u5f20\u56fe/.test(NODES["mu-out"].children[0].textContent), NODES["mu-out"].children[0].textContent);

console.log("\n=== 4. \u57fa\u5e95\u770b\u4e0d\u4e86\u56fe\uff1a\u5982\u5b9e\u544a\u8bc9\u7528\u6237 ===");
NEXT = () => Promise.resolve({ s: 200, d: { ok: true, lines: ["\u4e00\u53e5"], saw: 0, blind: 1, srcs: [] } });
muGo.click();
await sleep(20);
ok("\u8bf4\u4e86\u770b\u4e0d\u4e86\u56fe", /\u770b\u4e0d\u4e86\u56fe/.test(NODES["mu-out"].children[0].textContent), NODES["mu-out"].children[0].textContent);

console.log("\n=== 5. \u5931\u8d25\u4e0e\u7f51\u7edc\u5f02\u5e38\uff1a\u6309\u94ae\u5fc5\u987b\u80fd\u518d\u70b9 ===");
global.__setPick([]);
NEXT = () => Promise.resolve({ s: 429, d: { ok: false, msg: "\u751f\u5f97\u592a\u5feb\u4e86" } });
muGo.click();
await sleep(20);
ok("\u663e\u793a\u670d\u52a1\u7aef\u7684\u8bdd", /\u592a\u5feb/.test(NODES["mu-out"].children[0].textContent));
ok("\u6309\u94ae\u5df2\u89e3\u9501", !muGo.disabled);
NEXT = () => Promise.reject(new Error("net"));
muGo.click();
await sleep(20);
ok("\u7f51\u7edc\u5f02\u5e38\u4e5f\u89e3\u9501", !muGo.disabled && /\u7f51\u7edc\u5f02\u5e38/.test(NODES["mu-out"].children[0].textContent));

console.log("\n=== 6. \u6362\u4e00\u6279\uff1a\u518d\u8dd1\u4e00\u6b21 ===");
CALLS = [];
NEXT = () => Promise.resolve({ s: 200, d: { ok: true, lines: ["\u4e00", "\u4e8c"], saw: 0, blind: 0, srcs: [] } });
muGo.click();
await sleep(20);
const again = NODES["mu-out"].children[NODES["mu-out"].children.length - 1];
again.click();
await sleep(20);
ok("\u53c8\u53d1\u4e86\u4e00\u6b21", CALLS.length === 2, CALLS.length);

console.log("\n" + (fail ? "\u2717 " : "\u2713 ") + pass + " \u9879\u901a\u8fc7\uff0c" + fail + " \u9879\u5931\u8d25\n");
process.exit(fail ? 1 : 0);
