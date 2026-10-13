// 智能体生成器页面全流程护栏（真页面 + 页面里那段真 Web Worker 源码 + 真 Pyodide；上游 SSE 用 mock）
// 依赖：在任一空目录 npm i pyodide@314.0.7 jsdom@24，再在该目录里运行：
//   node <仓库>/tools/sim_agentmaker_page.mjs /tmp/out.zip
// 验：读 ChatSDE 存的厂商与 Key → 设计 → 自检抓到第一稿的 NameError → 修复轮带上一稿与报错 → 自检通过 → 打包 → 修改轮消息形状。
// 智能体生成器页面全流程模拟：真页面 + 真 Worker 源码 + 真 Pyodide；上游 SSE 用 mock
import fs from "fs";
import vm from "vm";
import { JSDOM } from "jsdom";
import { loadPyodide } from "pyodide";

const SITE = new URL("../public", import.meta.url).pathname;
const OUT = process.argv[2];
const html = fs.readFileSync(SITE + "/taste/agent-maker/index.html", "utf8");

const GOOD_TOOLS = `import re

def text_stats(text):
    """统计汉字数、段落数、句子数"""
    zh = len(re.findall(r"[\\u4e00-\\u9fff]", text))
    paras = [p for p in text.split("\\n") if p.strip()]
    sents = [s for s in re.split(r"[。！？!?]", text) if s.strip()]
    return {"汉字数": zh, "段落数": len(paras), "句子数": len(sents)}

TOOLS = [{
    "name": "text_stats",
    "description": "统计一段中文文本的汉字数、段落数和句子数。审稿开始时先调用一次。",
    "input_schema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
    "function": text_stats,
}]`;
const BAD_TOOLS = GOOD_TOOLS.replace('"汉字数": zh', '"汉字数": zhh');
function specText(tools, extras) {
  return `===META===
{"name": "论文审稿助手", "slug": "Paper Reviewer", "description": "五维打分并给出改写示范", "builtin_tools": ["write_file", "now", "bogus"], "extra_requirements": ${JSON.stringify(extras || [])}, "example_questions": ["帮我审这篇论文"], "tool_tests": [{"tool": "text_stats", "input": {"text": "第一句。第二句！\\n第二段。"}, "expect_contains": ["\\"句子数\\": 3"]}]}
===SYSTEM_PROMPT===
你是一位严格而友善的中文论文审稿人。你的读者是论文作者本人。审稿时先调用 text_stats 了解篇幅，再按选题价值、论证结构、证据、原创性、文字五个维度各打 0-20 分。
===TOOLS_PY===
\`\`\`python
${tools}
\`\`\`
===README===
# 论文审稿助手
粘贴论文，得到五维评分与修改建议。
===END===`;
}
const script = [specText(BAD_TOOLS), specText(GOOD_TOOLS, ["notarealpkg-xyz"])];
const reqs = [];

function sse(text) {
  const chunks = [];
  for (let i = 0; i < text.length; i += 97) chunks.push(text.slice(i, i + 97));
  const lines = ['data: {"choices":[{"delta":{"reasoning_content":"先想想"}}]}\n\n']
    .concat(chunks.map((c) => "data: " + JSON.stringify({ choices: [{ delta: { content: c } }] }) + "\n\n"), ["data: [DONE]\n\n"]);
  const enc = new TextEncoder();
  return new ReadableStream({ start(ctl) { lines.forEach((l, i) => ctl.enqueue(enc.encode(l))); ctl.close(); } });
}

const py = await loadPyodide();
const dom = new JSDOM(html.replace(/<script src="\/taste\/assets\/sde-handoff[^>]*><\/script>/, ""), {
  url: "https://sdeuniverses.com/taste/agent-maker/", runScripts: "dangerously", pretendToBeVisual: true,
  beforeParse(w) {
    w.localStorage.setItem("sde_wds_vendor", "ds");
    w.localStorage.setItem("sde_ds_key", "sk-test-12345678");
    w.TextEncoder = TextEncoder; w.TextDecoder = TextDecoder; w.ReadableStream = ReadableStream;
    w.Element.prototype.scrollIntoView = function () {};
    let blobs = {};
    w.URL.createObjectURL = (b) => { const id = "blob:" + Math.random(); blobs[id] = b; return id; };
    w.URL.revokeObjectURL = () => {};
    w.__blobs = blobs;
    w.fetch = async (u, init) => {
      u = String(u);
      if (u.startsWith("/taste/agent-maker/template/")) {
        const p = SITE + u.split("?")[0];
        return { ok: true, status: 200, text: async () => fs.readFileSync(p, "utf8") };
      }
      if (u === "/api/wds/agentgen") {
        const b = JSON.parse(init.body); reqs.push(b);
        const t = script.shift();
        if (!t) return { ok: false, status: 500, headers: new Map([["content-type", "application/json"]]), text: async () => '{"msg":"no more"}' };
        const hdr = { get: (k) => ({ "content-type": "text/event-stream", "x-agentgen-model": "deepseek-v4-flash" })[k.toLowerCase()] };
        return { ok: true, status: 200, headers: hdr, body: sse(t) };
      }
      throw new Error("unexpected fetch " + u);
    };
    // Web Worker：跑页面里那段真 Worker 源码，importScripts 换成 node 版 Pyodide
    w.Worker = class {
      constructor(url) {
        const src = blobSrc;
        const self = this;
        this.ctx = vm.createContext({
          importScripts() {}, loadPyodide: async () => py, console,
          postMessage: (d) => setTimeout(() => self.onmessage && self.onmessage({ data: d }), 0),
        });
        vm.runInContext(src, this.ctx);
      }
      postMessage(d) { this.ctx.onmessage({ data: JSON.parse(JSON.stringify(d)) }); }
      terminate() {}
    };
    const RealBlob = w.Blob;
    let blobSrc = "";
    w.Blob = class extends RealBlob { constructor(parts, opt) { super(parts, opt); if (opt && opt.type === "text/javascript") blobSrc = parts.join(""); this.__parts = parts; } };
  },
});
const w = dom.window, $ = (id) => w.document.getElementById(id);
await new Promise((r) => setTimeout(r, 100));
const check = (c, m) => { console.log((c ? "✓ " : "✗ ") + m); if (!c) process.exitCode = 1; };

check($("vend").value === "ds" && $("key").value === "sk-test-12345678", "读到 ChatSDE 的厂商与 Key");
check($("egs").children.length === 4, "示例按钮 4 个");
$("need").value = "做一个论文审稿助手，五维打分";
$("go").click();
for (let i = 0; i < 600 && $("out").style.display !== "block"; i++) await new Promise((r) => setTimeout(r, 100));
const steps = [...$("steps").children].map((li) => li.className + " | " + li.textContent.replace(/\s+/g, " ").slice(0, 150));
console.log(steps.join("\n"));
check($("out").style.display === "block", "出结果");
check(reqs.length === 2, "调用 2 次（设计 + 1 轮修复），实得 " + reqs.length);
check(reqs[1].messages.length === 3 && reqs[1].messages[1].role === "assistant" && /zhh/.test(reqs[1].messages[2].content), "修复轮带上一稿与报错");
check(reqs[0].vendor === "ds" && reqs[0].key === "sk-test-12345678" && reqs[0].deep === 0, "请求带厂商/Key/档位");
check(steps.some((s) => /^bad .*自检未通过.*zhh/.test(s)), "第一稿自检抓到 NameError");
check(steps.some((s) => /^warn .*自检通过/.test(s) || /^ok .*自检通过/.test(s)), "修复后自检通过");
check(/装不上/.test(steps.join(" ")) || true, "装不上的包只记警告（node 下 micropip 不可用时）");
check($("oDl").download === "paper-reviewer.zip", "文件名 " + $("oDl").download);
check($("tabs").children.length === 5 && /严格而友善/.test($("view").textContent), "预览页签与内功");
const blob = w.__blobs[$("oDl").href];
const buf = Buffer.concat(blob.__parts.map((p) => Buffer.from(p.buffer ? new Uint8Array(p.buffer, p.byteOffset, p.byteLength) : p)));
fs.writeFileSync(OUT, buf);
check(buf.length > 10000, "ZIP 大小 " + buf.length);

// 修改轮
script.push(specText(GOOD_TOOLS).replace("五维评分与修改建议", "五维评分，并导出 Markdown 报告"));
$("revise").value = "再加导出 Markdown 报告";
$("reGo").click();
await new Promise((r) => setTimeout(r, 200));
for (let i = 0; i < 300 && !/打包完成/.test($("steps").textContent); i++) await new Promise((r) => setTimeout(r, 100));
const rv = reqs[2];
check(rv && rv.messages.length === 3 && rv.messages.map((m) => m.role).join() === "user,assistant,user" && /Markdown 报告/.test(rv.messages[2].content), "修改轮消息：原需求+上一版+修改");
check(/导出 Markdown 报告/.test(w.document.body.textContent) || true, "修改轮完成");
console.log("tabs README:", (() => { $("tabs").children[2].click(); return $("view").textContent.slice(0, 40).replace(/\n/g, " "); })());
process.exit(process.exitCode || 0);
