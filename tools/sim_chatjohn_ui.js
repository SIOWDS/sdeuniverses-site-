/* ChatJohn 前端全链路模拟：用 jsdom 加载真实页面，桩掉 fetch 喂各种 SSE 流，
 * 验「点了会怎样、流回来怎么渲染、出错怎么显示」——不需要任何 API Key。
 * 跑法：node sim_chatjohn_ui.js  （在 site 根目录）
 */
const fs = require("fs");
const { JSDOM } = require("jsdom");

const HTML = fs.readFileSync("public/sites/lang/chatjohn/index.html", "utf8");
let pass = 0, fail = 0;
const t = (n, c, extra) => { console.log((c ? "PASS" : "FAIL") + "  " + n + (c || !extra ? "" : "   ← " + extra)); c ? pass++ : fail++; };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// ── SSE 桩：把一串帧对象做成可读流 ─────────────────────────────
function sseBody(frames, opts) {
  opts = opts || {};
  const enc = new TextEncoder();
  let i = 0;
  return {
    getReader() {
      return {
        read() {
          if (opts.abortAt != null && i === opts.abortAt) { const e = new Error("aborted"); e.name = "AbortError"; return Promise.reject(e); }
          if (i >= frames.length) return Promise.resolve({ done: true, value: undefined });
          const f = frames[i++];
          const line = (f === "[DONE]") ? "data: [DONE]\n\n" : "data: " + JSON.stringify(f) + "\n\n";
          return Promise.resolve({ done: false, value: enc.encode(line) });
        },
      };
    },
  };
}
function okStream(frames, opts) { return Promise.resolve({ ok: true, body: sseBody(frames, opts), json: () => Promise.resolve({}) }); }
function jsonErr(obj, status) { return Promise.resolve({ ok: false, status: status || 400, body: null, json: () => Promise.resolve(obj) }); }

async function boot(store) {
  const dom = new JSDOM(HTML, { runScripts: "outside-only", url: "https://lang.sdeuniverses.com/chatjohn/", pretendToBeVisual: true });
  const w = dom.window;
  // localStorage 桩（jsdom 有，但要可控）
  const mem = Object.assign({}, store || {});
  Object.defineProperty(w, "localStorage", {
    value: {
      getItem: (k) => (k in mem ? mem[k] : null),
      setItem: (k, v) => { mem[k] = String(v); },
      removeItem: (k) => { delete mem[k]; },
    }, configurable: true,
  });
  w.confirm = () => true;
  w.TextDecoder = w.TextDecoder || require("util").TextDecoder;
  w.AbortController = w.AbortController || require("abort-controller");
  w.__calls = [];
  w.fetch = (u, o) => { w.__calls.push({ u: String(u), body: o && o.body ? JSON.parse(o.body) : null, signal: o && o.signal });
                        return w.__handler(String(u), o); };
  w.__handler = () => okStream(["[DONE]"]);
  // 页面脚本只在这里跑一次（JSDOM 用 outside-only 不自动执行页内 <script>，
  // 否则会跑两遍：两套事件监听 → 一次点击触发两次，测出来全是假故障）
  const code = HTML.match(/<script>([\s\S]*?)<\/script>\s*<\/body>/)[1];
  w.eval(code);
  await sleep(30);
  return { dom, w, mem };
}
const $ = (w, s) => w.document.querySelector(s);
const $$ = (w, s) => Array.from(w.document.querySelectorAll(s));

(async () => {
  console.log("── A. 无 Key 的入口保护 ────────────────────────");
  {
    const { w } = await boot({});
    await sleep(700);
    t("首次进页无 Key 自动弹设置", !!$(w, ".mask"));
    const panel = $(w, ".panel");
    t("面板有厂商下拉", !!panel && panel.querySelectorAll("#sv option").length === 5);
    t("面板有 Key 输入且是 password", !!$(w, "#sk") && $(w, "#sk").type === "password");
    t("面板有测试连接按钮", !!$(w, "#sp"));
    $(w, "#sc").click(); await sleep(20);
    t("取消能关掉面板", !$(w, ".mask"));
    // 无 Key 直接发送
    $(w, "#q").value = "语感是什么";
    $(w, "#go").click(); await sleep(40);
    t("无 Key 点发送 → 弹设置而不是发请求", !!$(w, ".mask") && w.__calls.length === 0);
  }

  console.log("\n── B. 设置面板：保存与测试连接 ──────────────────");
  {
    const { w, mem } = await boot({});
    await sleep(700);
    $(w, "#sv").value = "zhipu"; $(w, "#sk").value = "sk-abcdefghijklmnop";
    $(w, "#sm").value = "glm-5"; $(w, "#sd").checked = true;
    $(w, "#ss").click(); await sleep(30);
    t("保存写入 Key", mem["sde_wds_key"] === "sk-abcdefghijklmnop");
    t("保存写入厂商", mem["sde_wds_vendor"] === "zhipu");
    t("保存写入模型覆盖", mem["sde_john_model"] === "glm-5");
    t("保存写入深想档", mem["sde_john_deep"] === "1");
    t("保存后面板关闭", !$(w, ".mask"));
    t("Key 键名与 ChatSDE 通用", "sde_wds_key" in mem && "sde_wds_vendor" in mem);
  }
  {
    const { w } = await boot({ sde_wds_key: "sk-abcdefghijklmnop" });
    $(w, "#btnSet").click(); await sleep(30);
    w.__handler = () => Promise.resolve({ ok: true, json: () => Promise.resolve({ ok: true, name: "DeepSeek", model: "deepseek-v4-flash" }) });
    $(w, "#sp").click(); await sleep(60);
    t("测试连接：通了会报型号", /通了/.test($(w, "#pm").textContent), $(w, "#pm").textContent);
    w.__handler = () => Promise.resolve({ ok: true, json: () => Promise.resolve({ ok: false, code: "bad_key" }) });
    $(w, "#sp").click(); await sleep(60);
    t("测试连接：坏 Key 说人话", /没通过校验/.test($(w, "#pm").textContent), $(w, "#pm").textContent);
  }

  console.log("\n── C. 一轮完整问答 ─────────────────────────────");
  const KEYED = { sde_wds_key: "sk-abcdefghijklmnop", sde_wds_vendor: "deepseek" };
  {
    const { w } = await boot(KEYED);
    w.__handler = () => okStream([
      { t: "src", v: [{ t: "后手生位", u: "https://lang.sdeuniverses.com/students/hu-zhiying/post-hand-slot/" }] },
      { t: "think", v: "先看这句话的 D……" },
      { t: "d", v: "## 先看这一句\n\n它的问题**不在语法**，在 D。\n\n- 一是没有读者\n- 二是没有场合\n\n" },
      { t: "d", v: "详见 https://lang.sdeuniverses.com/students/hu-zhiying/post-hand-slot/ 。" },
      { t: "fin", v: { wrote: 60, sec: 3 } }, "[DONE]",
    ]);
    $(w, "#q").value = "这句话哪里不对？";
    $(w, "#go").click(); await sleep(300);
    const msgs = $$(w, ".msg");
    t("用户气泡已渲染", msgs.length >= 1 && msgs[0].className.indexOf("u") >= 0);
    t("John 气泡已渲染", msgs.length === 2 && msgs[1].className.indexOf("j") >= 0);
    const bd = msgs[1].querySelector(".bd");
    t("markdown 标题渲染", !!bd.querySelector("h2"));
    t("markdown 粗体渲染", !!bd.querySelector("strong"));
    t("markdown 列表渲染", bd.querySelectorAll("li").length === 2);
    t("裸链接成锚", !!bd.querySelector('a[href*="post-hand-slot"]'));
    t("思考过程折叠块出现", !!msgs[1].querySelector("details.think"));
    t("站内出处条出现", !!msgs[1].querySelector(".srcs a"));
    t("出处链接可点", (msgs[1].querySelector(".srcs a") || {}).href === "https://lang.sdeuniverses.com/students/hu-zhiying/post-hand-slot/");
    const tools = msgs[1].querySelectorAll(".tools button");
    t("工具条有复制与重答", tools.length === 2 && /复制/.test(tools[0].textContent) && /重答/.test(tools[1].textContent));
    t("发送键复位", $(w, "#go").textContent === "发送" && !$(w, "#go").disabled);
    t("光标已移除", !bd.querySelector(".cursor"));
    const req = w.__calls[0];
    t("请求打到 /api/john/chat", /\/api\/john\/chat$/.test(req.u), req.u);
    t("请求带上了 Key", req.body.key === "sk-abcdefghijklmnop");
    t("请求带上了厂商", req.body.vendor === "deepseek");
    t("历史里只有一条 user", req.body.messages.length === 1 && req.body.messages[0].role === "user");
  }

  console.log("\n── D. 出错与中断 ───────────────────────────────");
  {
    const { w } = await boot(KEYED);
    w.__handler = () => okStream([{ t: "error", v: "这把 Key 没通过校验。" }, "[DONE]"]);
    $(w, "#q").value = "x"; $(w, "#go").click(); await sleep(200);
    t("error 帧显示为 ⚠ 提示", /没通过校验/.test(($(w, ".err") || {}).textContent || ""));
    t("出错后给「重试」而不是「重答」", /重试/.test($$(w, ".tools button").map((b) => b.textContent).join()));
    t("出错后仍可继续输入", !$(w, "#go").disabled);
  }
  {
    const { w } = await boot(KEYED);
    w.__handler = () => jsonErr({ ok: false, msg: "太快啦，过十几秒再试。" }, 429);
    $(w, "#q").value = "x"; $(w, "#go").click(); await sleep(200);
    t("HTTP 429 的 msg 被显示出来", /太快啦/.test(($(w, ".err") || {}).textContent || ""));
  }
  {
    const { w } = await boot(KEYED);
    // 写两帧后中断
    w.__handler = () => okStream([{ t: "d", v: "写了一半" }, { t: "d", v: "又写一点" }, { t: "d", v: "不该出现" }], { abortAt: 2 });
    $(w, "#q").value = "x"; $(w, "#go").click(); await sleep(250);
    const j = $$(w, ".msg.j")[0];
    t("中断后保留已写内容", /写了一半又写一点/.test(j.querySelector(".bd").textContent));
    t("中断后不吐出后续内容", !/不该出现/.test(j.querySelector(".bd").textContent));
    t("中断后按钮复位", $(w, "#go").textContent === "发送");
  }

  console.log("\n── E. 多轮 · 成文条 · 新对话 ───────────────────");
  {
    const { w } = await boot(KEYED);
    w.__handler = () => okStream([{ t: "d", v: "答一" }, "[DONE]"]);
    $(w, "#q").value = "问一"; $(w, "#go").click(); await sleep(200);
    t("一轮之后成文条还藏着", $(w, "#bar").hidden === true);
    w.__handler = () => okStream([{ t: "d", v: "答二" }, "[DONE]"]);
    $(w, "#q").value = "问二"; $(w, "#go").click(); await sleep(200);
    t("两轮之后成文条出现", $(w, "#bar").hidden === false);
    t("成文条三个文体", $$(w, "#bar button").length === 3);
    const labels = $$(w, "#bar button").map((b) => b.textContent);
    t("三个文体标了字数", /1 万字/.test(labels[0]) && /4000/.test(labels[1]) && /2000/.test(labels[2]), labels.join(" | "));
    // 第二轮请求应带上完整历史
    const last = w.__calls[w.__calls.length - 1];
    t("第二轮带上整场历史", last.body.messages.length === 3);
    $(w, "#btnNew").click(); await sleep(30);
    t("新对话清空消息", $$(w, ".msg").length === 0);
    t("新对话收起成文条", $(w, "#bar").hidden === true);
  }

  console.log("\n── F. 概括成文（多段拼接）─────────────────────");
  {
    const { w } = await boot(KEYED);
    w.__handler = () => okStream([{ t: "d", v: "答" }, "[DONE]"]);
    $(w, "#q").value = "问一"; $(w, "#go").click(); await sleep(150);
    $(w, "#q").value = "问二"; $(w, "#go").click(); await sleep(150);
    let seq = 0;
    w.__handler = (u, o) => {
      const b = JSON.parse(o.body);
      seq++;
      return okStream([{ t: "meta", v: { part: b.part, parts: 2 } }, { t: "d", v: "第" + b.part + "段正文。" }, { t: "fin", v: {} }, "[DONE]"]);
    };
    $$(w, "#bar button")[1].click();   // 散文＝2 段
    await sleep(500);
    const box = $(w, ".compose");
    t("成文面板出现", !!box);
    t("散文调了两趟", seq === 2, "seq=" + seq);
    t("两段被拼在一起", /第1段正文。[\s\S]*第2段正文。/.test(box.querySelector(".bd2").textContent));
    const parts = w.__calls.filter((c) => /compose/.test(c.u));
    t("第二趟带上了上一段的尾巴", parts.length === 2 && /第1段正文/.test(parts[1].body.prev || ""));
    t("成文请求也带 Key", parts[0].body.key === "sk-abcdefghijklmnop");
    t("成文请求带上整场对话", parts[0].body.messages.length === 4);
    t("完成后出现复制与下载", box.querySelectorAll(".act button").length === 2);
    t("完成后标出字数", /\d+ 字/.test(box.querySelector(".hd span").textContent), box.querySelector(".hd span").textContent);
    t("成文完毕按钮复位", !$$(w, "#bar button")[0].disabled);
  }

  console.log("\n── G. 安全：注入不逃逸 ─────────────────────────");
  {
    const { w } = await boot(KEYED);
    w.__handler = () => okStream([
      { t: "d", v: '<img src=x onerror="window.__pwned=1">' },
      { t: "d", v: "<scr" + "ipt>window.__pwned2=1</scr" + "ipt>" },
      { t: "src", v: [{ t: '<img src=x onerror="window.__pwned3=1">', u: "https://a.com/" }] },
      "[DONE]",
    ]);
    $(w, "#q").value = "x"; $(w, "#go").click(); await sleep(250);
    t("回答里的 img 标签未被执行", !w.__pwned && !w.document.querySelector(".bd img"));
    t("回答里的 script 未被执行", !w.__pwned2 && !w.document.querySelector(".bd script"));
    t("出处标题里的注入未执行", !w.__pwned3 && !w.document.querySelector(".srcs img"));
    const { w: w2 } = await boot(KEYED);
    w2.__handler = () => okStream([{ t: "d", v: "正常" }, "[DONE]"]);
    $(w2, "#q").value = '<img src=x onerror="window.__pwned4=1">';
    $(w2, "#go").click(); await sleep(200);
    t("用户输入里的注入未执行", !w2.__pwned4 && !w2.document.querySelector(".msg.u img"));
    t("用户输入按纯文本显示", /<img/.test($$(w2, ".msg.u")[0].querySelector(".bd").textContent));
  }

  console.log("\n── H. 输入交互 ─────────────────────────────────");
  {
    const { w } = await boot(KEYED);
    w.__handler = () => okStream([{ t: "d", v: "好" }, "[DONE]"]);
    const q = $(w, "#q");
    q.value = "回车发送";
    const ev = new w.KeyboardEvent("keydown", { key: "Enter", shiftKey: false, bubbles: true });
    q.dispatchEvent(ev); await sleep(200);
    t("Enter 发送", $$(w, ".msg").length === 2 && q.value === "");
    q.value = "换行不发";
    q.dispatchEvent(new w.KeyboardEvent("keydown", { key: "Enter", shiftKey: true, bubbles: true }));
    await sleep(60);
    t("Shift+Enter 不发送", $$(w, ".msg").length === 2 && q.value === "换行不发");
    q.value = "   ";
    $(w, "#go").click(); await sleep(60);
    t("空白输入不发送", $$(w, ".msg").length === 2);
    t("种子问题按钮共四条", $$(w, ".seed").length === 4);
  }

  console.log("\n" + "═".repeat(48));
  console.log("总计  PASS " + pass + "   FAIL " + fail);
  if (fail) process.exit(1);
})().catch((e) => { console.error("测试脚本自身出错：", e); process.exit(2); });
