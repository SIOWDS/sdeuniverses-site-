// SDE对话 → 通用智能体 的「交接」护栏：真跑 sde-handoff.js，再验两端接线。
// 跑法：node tools/sim_handoff.mjs
import fs from "fs";

const R = (p) => fs.readFileSync(new URL("../" + p, import.meta.url), "utf8");
const MOD = R("public/taste/assets/sde-handoff.js");
const WDS = R("public/wds-mode.js");

let pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; console.log("  \u2713 " + name); }
  else { fail++; console.log("  \u2717 " + name + (extra !== undefined ? "  \u2190 " + JSON.stringify(extra).slice(0, 260) : "")); }
}

/* ── 假环境：localStorage / document / window.open ── */
const LS = new Map();
global.localStorage = {
  getItem: (k) => (LS.has(k) ? LS.get(k) : null),
  setItem: (k, v) => LS.set(k, String(v)),
  removeItem: (k) => LS.delete(k),
};
function mkNode(tag) {
  return {
    tag, id: "", value: "", children: [], _txt: "", _attr: {}, parentNode: null, onclick: null,
    get textContent() { return this._txt; },
    set textContent(v) { this._txt = v; },
    setAttribute(k, v) { this._attr[k] = v; },
    appendChild(c) { c.parentNode = this; this.children.push(c); return c; },
    insertBefore(c) { c.parentNode = this; this.children.unshift(c); return c; },
    removeChild(c) { this.children = this.children.filter((x) => x !== c); c.parentNode = null; },
    focus() { this.focused = true; },
    querySelector() { return null; },
    get deep() { return this._txt + this.children.map((c) => c.deep).join(""); },
  };
}
const BOXES = {};
global.document = {
  body: mkNode("body"),
  createElement: (t) => mkNode(t),
  createTextNode: (s) => ({ tag: "#text", _txt: s, children: [], get deep() { return this._txt; } }),
  getElementById: (id) => BOXES[id] || null,
};
let OPENED = [];
global.window = { open: (u, t) => { OPENED.push({ u, t }); return {}; } };
global.location = { href: "" };

/* 装载真模块 */
eval(MOD);
const H = global.window.SDEHandoff;
ok("\u6a21\u5757\u88c5\u8f7d\u5e76\u6302\u4e0a window", !!H && typeof H.send === "function");

console.log("\n=== 1. \u6ce8\u518c\u8868\uff1a\u4e94\u53f0\u901a\u7528\u667a\u80fd\u4f53\u90fd\u5728\uff0c\u4e14\u6bcf\u53f0\u90fd\u8bf4\u6e05\u4e86\u4ee3\u4ef7 ===");
const ids = H.AGENTS.map((a) => a.id);
ok("\u4e94\u53f0", H.AGENTS.length === 5, ids);
["idea", "zhiwen", "uplift", "forge", "search"].forEach((i) => ok("\u5728\u8868\u91cc\uff1a" + i, ids.indexOf(i) >= 0));
ok("\u91d1\u70b9\u5b50\u4e0e\u4e2d\u534e\u667a\u95ee\u662f\u7528\u6237\u70b9\u540d\u7684\u90a3\u4e24\u53f0",
  /\u91d1\u70b9\u5b50/.test(H.byId("idea").name) && /\u4e2d\u534e\u667a\u95ee/.test(H.byId("zhiwen").name));
ok("\u6bcf\u53f0\u90fd\u6709 url / \u5165\u53e3 id / \u5e72\u4ec0\u4e48 / \u591a\u5c11\u4ee3\u4ef7",
  H.AGENTS.every((a) => a.url && a.sel.length && a.what && a.cost), H.AGENTS.map((a) => a.id));
ok("\u5165\u53e3 id \u662f\u6570\u7ec4\uff08\u76ee\u6807\u9875\u6539\u7248\u6709\u9000\u8def\uff09", H.AGENTS.every((a) => Array.isArray(a.sel)));

console.log("\n=== 2. \u76ee\u6807\u9875\u4e0a\u90a3\u4e2a id \u5fc5\u987b\u771f\u5b58\u5728 ===");
for (const a of H.AGENTS) {
  const page = "public" + a.url + "index.html";
  let html = "";
  try { html = R(page); } catch (e) {}
  ok("\u9875\u5b58\u5728\uff1a" + a.url, !!html);
  ok("\u5165\u53e3\u6846\u5b58\u5728\uff1a" + a.id + " \u2192 #" + a.sel[0], html.indexOf('id="' + a.sel[0] + '"') >= 0);
  ok("\u5df2\u5f15\u6a21\u5757\uff1a" + a.id, html.indexOf("sde-handoff.js") >= 0);
  ok("\u5df2\u63a5 receive\uff1a" + a.id, new RegExp('SDEHandoff\\.receive\\("' + a.id + '"\\)').test(html));
}

console.log("\n=== 3. \u4ea4\u51fa\u53bb\uff1a\u5199\u4ef6 ＋ \u5f00\u65b0\u6807\u7b7e ===");
OPENED = [];
const sent = H.send("idea", "  \u4e3a\u4ec0\u4e48\u8d8a\u52aa\u529b\u8d8a\u7126\u8651\uff1f  ", "SDE \u5bf9\u8bdd");
ok("\u8fd4\u56de true", sent === true);
ok("\u5f00\u7684\u662f\u65b0\u6807\u7b7e\u4e14\u6307\u5411\u91d1\u70b9\u5b50", OPENED.length === 1 && OPENED[0].u === "/taste/idea-generator/" && OPENED[0].t === "_blank", OPENED);
const filed = JSON.parse(LS.get("sde_handoff"));
ok("\u9996\u5c3e\u7a7a\u767d\u88ab\u53bb\u6389", filed.q === "\u4e3a\u4ec0\u4e48\u8d8a\u52aa\u529b\u8d8a\u7126\u8651\uff1f", filed.q);
ok("\u8bb0\u4e86\u6536\u4ef6\u4eba\u4e0e\u6765\u5904", filed.to === "idea" && /SDE/.test(filed.from));
ok("\u7a7a\u53e5\u4e0d\u4ea4", H.send("idea", "   ") === false && OPENED.length === 1);
ok("\u672a\u77e5\u667a\u80fd\u4f53\u4e0d\u4ea4", H.send("\u4e0d\u5b58\u5728", "\u4e00\u53e5\u8bdd") === false);

console.log("\n=== 4. \u53d6\u56de\u6765\uff1a\u53ea\u8ba4\u5199\u7ed9\u81ea\u5df1\u7684\u3001\u4e00\u6b21\u6027\u3001\u4f1a\u8fc7\u671f ===");
ok("\u522b\u4eba\u7684\u4ef6\u4e0d\u52a8\u5b83", H.take("zhiwen") === null && LS.has("sde_handoff"));
const got = H.take("idea");
ok("\u53d6\u5230\u4e86", got && got.q === "\u4e3a\u4ec0\u4e48\u8d8a\u52aa\u529b\u8d8a\u7126\u8651\uff1f", got);
ok("\u53d6\u8d70\u5373\u5220\uff08\u5237\u65b0\u4e0d\u4f1a\u518d\u586b\u4e00\u904d\uff09", !LS.has("sde_handoff") && H.take("idea") === null);
LS.set("sde_handoff", JSON.stringify({ to: "idea", q: "\u9648\u5e74\u65e7\u4e8b", ts: Date.now() - 11 * 60 * 1000 }));
ok("\u8fc7\u671f\u4ef6\u4e0d\u7528", H.take("idea") === null);
ok("\u8fc7\u671f\u4ef6\u4e5f\u4e0d\u7559\u5728\u90a3\u91cc", !LS.has("sde_handoff"));
LS.set("sde_handoff", "\u4e0d\u662f JSON");
ok("\u574f\u4ef6\u4e0d\u5d29\u4e14\u6e05\u6389", H.take("idea") === null && !LS.has("sde_handoff"));

console.log("\n=== 5. \u843d\u5230\u9875\u9762\uff1a\u586b\u6846 ＋ \u6a2a\u5e45\uff0c\u4e14\u4e0d\u8986\u76d6\u8bfb\u8005\u5df2\u5199\u7684 ===");
document.body.children = [];
BOXES["question"] = mkNode("textarea");
H.send("idea", "\u628a\u8fd9\u4e00\u95ee\u505a\u6210\u56db\u7bc7\u8bba\u6587", "SDE \u5bf9\u8bdd");
let r = H.receive("idea");
ok("\u586b\u8fdb\u4e86\u7b2c\u4e00\u4e2a\u5b58\u5728\u7684\u6846", BOXES["question"].value === "\u628a\u8fd9\u4e00\u95ee\u505a\u6210\u56db\u7bc7\u8bba\u6587", BOXES["question"].value);
const bar = document.body.children[0];
ok("\u6a2a\u5e45\u63d2\u5728\u6700\u4e0a\u9762", bar && bar._attr.style && /position:relative/.test(bar._attr.style));
ok("\u6a2a\u5e45\u5199\u660e\u6765\u5904\u4e0e\u539f\u53e5", /SDE \u5bf9\u8bdd/.test(bar.deep) && /\u56db\u7bc7\u8bba\u6587/.test(bar.deep), bar.deep.slice(0, 120));
ok("\u6a2a\u5e45\u660e\u8bf4\u5b83\u4e0d\u4f1a\u66ff\u4f60\u6309\u5f00\u59cb", /\u4e0d\u4f1a\u66ff\u4f60\u6309\u5f00\u59cb/.test(bar.deep));
document.body.children = [];
BOXES["question"].value = "\u6211\u81ea\u5df1\u5df2\u7ecf\u5199\u4e86\u4e00\u4e2a\u95ee\u9898";
H.send("idea", "\u540e\u6765\u4ea4\u8fc7\u6765\u7684\u90a3\u4e00\u53e5", "SDE \u5bf9\u8bdd");
H.receive("idea");
ok("\u2605 \u4e0d\u8986\u76d6\u8bfb\u8005\u5df2\u5199\u7684", BOXES["question"].value === "\u6211\u81ea\u5df1\u5df2\u7ecf\u5199\u4e86\u4e00\u4e2a\u95ee\u9898", BOXES["question"].value);
ok("\u4f46\u544a\u8bc9\u4ed6\u6709\u4e00\u4ef6\u6ca1\u653e\u8fdb\u53bb", /\u6ca1\u52a8\u5b83/.test(document.body.children[0].deep));
document.body.children = [];
BOXES["question"].value = "";
H.send("idea", "\u6ca1\u6709\u6846\u7684\u60c5\u5f62", "SDE \u5bf9\u8bdd");
delete BOXES["question"];
r = H.receive("idea");
ok("\u76ee\u6807\u6846\u4e0d\u5728\u4e5f\u4e0d\u62a5\u9519\uff08\u7eaa\u5f8b\u2463\uff09", r && r.q === "\u6ca1\u6709\u6846\u7684\u60c5\u5f62");
BOXES["question"] = mkNode("textarea");

console.log("\n=== 6. \u95eeWDS \u90a3\u4e00\u7aef\u7684\u63a5\u7ebf ===");
ok("\u6bcf\u4e2a\u56de\u7b54\u4e0b\u9762\u6709\u300c\u4ea4\u7ed9\u667a\u80fd\u4f53\u300d\u6309\u94ae", /aPass:\s*"[^"]*\u4ea4\u7ed9\u667a\u80fd\u4f53/.test(WDS));
ok("\u6309\u94ae\u63a5\u5230 passPanel", /ps\.onclick\s*=\s*function\s*\(\)\s*\{\s*passPanel\(cell, ps\);/.test(WDS));
ok("\u9762\u677f\u4ece\u5171\u7528\u6a21\u5757\u8bfb\u6ce8\u518c\u8868\uff08\u4e0d\u53e6\u62c4\u4e00\u4efd\uff09", /window\.SDEHandoff/.test(WDS) && /H\.AGENTS/.test(WDS));
ok("\u9012\u7684\u662f\u53ef\u6539\u7684\u4e00\u53e5\uff08textarea \u9884\u586b\u672c\u8f6e\u95ee\u9898\uff09", /ta\.value = String\(cell\.q \|\| ""\)/.test(WDS));
ok("\u9762\u677f\u91cc\u5199\u660e\u53ea\u586b\u4e0d\u8dd1", /\u53ea\u586b\u4e0d\u8dd1/.test(WDS));
ok("\u518d\u70b9\u4e00\u6b21\u5c31\u6536\u8d77\uff08\u4e0d\u4f1a\u53e0\u51fa\u4e00\u5806\uff09", /if \(cell\.pass && cell\.pass\.parentNode\)[\s\S]{0,120}return;/.test(WDS));
ok("\u6a21\u5757\u6ca1\u88c5\u8f7d\u65f6\u8bf4\u4eba\u8bdd\u800c\u4e0d\u662f\u62a5\u9519", /sde-handoff\.js[^"]*\u6ca1\u88c5\u8f7d\u4e0a/.test(WDS));
ok("\u7a7a\u6001\u4e5f\u6307\u4e86\u8def\uff08hero \u91cc\u63d0\u4e86\u4ea4\u7ed9\u667a\u80fd\u4f53\uff09", /heroAfter:[^\n]*\u4ea4\u7ed9\u667a\u80fd\u4f53/.test(WDS));
ok("\u4e2d\u82f1\u6587\u6848\u90fd\u914d\u9f50\uff08passH/passTip/passGo\uff09",
  (WDS.match(/passH:/g) || []).length === 2 && (WDS.match(/passTip:/g) || []).length === 2 && (WDS.match(/passGo:/g) || []).length === 2);
const shell = R("public/taste/chatsde/index.html");
ok("\u58f3\u9875\u5f15\u4e86\u6a21\u5757", /sde-handoff\.js\?v=/.test(shell));
// 别把版本戳钉成魔法数字——它每动一次 wds-mode.js 就要往前走一格。
// 只验"格式对且不早于上一次已知值"（这套戳是 YYYYMMDD+字母，按字典序比就是按时间比）。
const _st = (shell.match(/wds-mode\.js\?v=(20\d{6}[a-z]+)/) || [])[1] || "";
ok("\u58f3\u9875\u7248\u672c\u6233\u5f80\u524d\u8d70\u4e86\uff08\u5b9e\u5f97 " + _st + "\uff09", _st >= "20260731e");

console.log("\n=== 7. \u4e94\u6761\u7eaa\u5f8b\u5199\u5728\u6a21\u5757\u91cc\uff08\u5404\u9875\u4e0d\u8bb8\u5404\u5199\u4e00\u5957\uff09 ===");
["\u4e00\u6b21\u6027", "\u8bfb\u8005\u7684\u4e1c\u897f\u4f18\u5148", "\u53ea\u586b\u4e0d\u8dd1", "\u5931\u8d25\u4e0d\u62e6\u8def", "\u8bf4\u6e05\u6765\u5904"].forEach((k) =>
  ok("\u7eaa\u5f8b\u5728\u6a21\u5757\u6ce8\u91ca\u91cc\uff1a" + k, MOD.indexOf(k) >= 0));
ok("\u6a21\u5757\u4e0d\u9760\u4efb\u4f55\u5916\u90e8\u5e93", !/require\(|import /.test(MOD));

console.log("\n" + (fail ? "\u2717 " : "\u2713 ") + pass + " \u9879\u901a\u8fc7\uff0c" + fail + " \u9879\u5931\u8d25\n");
process.exit(fail ? 1 : 0);
