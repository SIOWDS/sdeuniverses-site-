/* 讨论区解禁 · 前端真跑模拟
 * 用 jsdom 装载一张真实的文章页（已挂上 sde-talk-pw.js），跑完两段脚本，
 * 检查：登录框装没装上、Google 外链拦没拦住、凭证放进 sessionStorage 后
 * 内联脚本会不会进入已登录状态、发言时原样把凭证发给 /api/comments。
 */
const fs = require("fs");
const path = require("path");
const { JSDOM, VirtualConsole } = require("jsdom");

const SITE = "/home/claude/site";
const PAGE = process.argv[2] || "public/column/into-equation/index.html";

let pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; console.log("  ✓ " + name); }
  else { fail++; console.log("  ✗ " + name + (extra !== undefined ? "  ← " + JSON.stringify(extra) : "")); }
}

// 把外部脚本换成本地文件内容（jsdom 不去真取网络）
function inline(html) {
  return html.replace(/<script src="\/assets\/sde-talk-pw\.js[^"]*"><\/script>/,
    "<script>" + fs.readFileSync(path.join(SITE, "public/assets/sde-talk-pw.js"), "utf8") + "</script>");
}

function makeDom(html, store) {
  const calls = { comments: [], im: [], reloaded: 0, roster: 0 };
  const vc = new VirtualConsole();
  // jsdom 不允许改写 location.reload，但真的调了它会抛「navigation not implemented」——拿这个当探针
  vc.on("jsdomError", (e) => { if (/navigation/i.test(e && e.message || "")) calls.reloaded++; });
  const dom = new JSDOM(inline(html), {
    url: "https://sdeuniverses.com/column/into-equation/",
    runScripts: "dangerously",
    virtualConsole: vc,
    beforeParse(w) {
      // 预置存储
      for (const [k, v] of Object.entries(store.session || {})) w.sessionStorage.setItem(k, v);
      for (const [k, v] of Object.entries(store.local || {})) w.localStorage.setItem(k, v);
      // 假 fetch
      w.fetch = (u, o) => {
        const url = String(u);
        const body = o && o.body ? JSON.parse(o.body) : null;
        if (url.indexOf("/api/comments") === 0) {
          calls.comments.push({ method: (o && o.method) || "GET", body });
          return Promise.resolve({ status: 200, json: () => Promise.resolve({ ok: true, items: [] }) });
        }
        if (url.indexOf("/api/im") === 0) {
          calls.im.push(body);
          return Promise.resolve({ status: 200, json: () => Promise.resolve({ ok: true, me: { uid: "c2fd205b4c5b", name: "张琼" } }) });
        }
        if (url.indexOf("roster.json") >= 0) {
          calls.roster++;
          return Promise.resolve({ status: 200, json: () => Promise.resolve({ students: [{ name: "张琼" }, { name: "高鹏" }] }) });
        }
        return Promise.resolve({ status: 200, json: () => Promise.resolve({}) });
      };
      // reload 探针：直接在 location 上定义自己的 reload
      try {
        Object.defineProperty(w.location, "reload", { configurable: true, value: () => { calls.reloaded++; } });
      } catch (e) { calls.reloadHookFailed = true; }
    },
  });
  return { dom, w: dom.window, calls };
}

const html = fs.readFileSync(path.join(SITE, PAGE), "utf8");
if (html.indexOf("sde-talk-pw.js") < 0) {
  console.log("这张页面还没挂上脚本——先跑 rollout（不加 --apply 时本模拟先自行注入）");
}
const withTag = html.indexOf("sde-talk-pw.js") >= 0
  ? html
  : html.replace("</head>", '<script src="/assets/sde-talk-pw.js?v=t"></script>\n</head>');

(async () => {
  console.log("\n=== 1. 没登录的读者 ===");
  {
    const { w, calls } = makeDom(withTag, {});
    await new Promise((r) => setTimeout(r, 60));
    const d = w.document;
    ok("登录框装上了", !!d.getElementById("tk-pwbox"));
    ok("名字与密码两个框都在", !!d.getElementById("tk-pw-name") && !!d.getElementById("tk-pw-code"));
    ok("Google 按钮容器被藏了", (d.getElementById("tk-gsi").offsetParent === null) ||
      !!d.querySelector("style") && [...d.querySelectorAll("style")].some((s) => /#tk-gsi\{display:none !important\}/.test(s.textContent)));
    ok("accounts.google.com 的脚本节点没进 head",
      d.head.querySelector('script[src*="accounts.google.com"]') === null,
      [...d.head.querySelectorAll("script[src]")].map((x) => x.src));
    ok("发言框仍然藏着", d.getElementById("tk-text").style.display === "none");
    ok("文案里已经没有 Google", !/Google/.test(d.querySelector("#sde-talk .tk-hint").textContent),
      d.querySelector("#sde-talk .tk-hint").textContent);
    ok("讨论内容照常拉取", calls.comments.some((c) => c.method === "GET"));
  }

  console.log("\n=== 2. 在登录框里登录 ===");
  {
    const { w, calls } = makeDom(withTag, {});
    await new Promise((r) => setTimeout(r, 60));
    const d = w.document;
    d.getElementById("tk-pw-name").value = "zhang-qiong";
    d.getElementById("tk-pw-code").value = "SDE2026";
    d.getElementById("tk-pw-go").dispatchEvent(new w.Event("click"));
    await new Promise((r) => setTimeout(r, 60));
    ok("拿 hello 验了一次身份", calls.im.length === 1 && calls.im[0].op === "hello", calls.im);
    ok("凭证格式对", /^sdepw1:SDE2026:zhang-qiong$/.test(calls.im[0].credential), calls.im[0] && calls.im[0].credential);
    const rec = JSON.parse(w.sessionStorage.getItem("sde_gauth") || "null");
    ok("凭证进了 sessionStorage", !!rec && rec.cred === "sdepw1:SDE2026:zhang-qiong");
    ok("名字换成了名录里的规范名「张琼」", rec && rec.name === "张琼", rec && rec.name);
    ok("跨标签页副本也写了", !!JSON.parse(w.localStorage.getItem("sde_talk_id") || "null"));
    ok("登录后刷新了页面", calls.reloaded === 1, calls.reloaded);
  }

  console.log("\n=== 3. 刷新之后（这是整个设计的承重点）===");
  {
    const rec = JSON.stringify({ cred: "sdepw1:SDE2026:张琼", name: "张琼", exp: Date.now() + 3600000 });
    const { w, calls } = makeDom(withTag, { session: { sde_gauth: rec } });
    await new Promise((r) => setTimeout(r, 60));
    const d = w.document;
    ok("内联脚本认了这张站内凭证、进入已登录", d.getElementById("tk-signed").style.display === "block");
    ok("发言人显示为张琼", d.getElementById("tk-gname").textContent === "张琼");
    ok("发言框出来了", d.getElementById("tk-text").style.display === "block");
    ok("发送栏出来了", d.getElementById("tk-sendbar").style.display === "flex");
    ok("登录框自动隐藏", d.getElementById("tk-pwbox").style.display === "none");

    // 真按发言键
    d.getElementById("tk-text").value = "这是一条测试发言";
    d.getElementById("tk-send").dispatchEvent(new w.Event("click"));
    await new Promise((r) => setTimeout(r, 60));
    const post = calls.comments.filter((c) => c.method === "POST");
    ok("发言真的 POST 出去了", post.length === 1, calls.comments.map((c) => c.method));
    ok("带着站内凭证、不是 Google 凭证", post[0] && post[0].body.credential === "sdepw1:SDE2026:张琼", post[0] && post[0].body);
    ok("正文对", post[0] && post[0].body.text === "这是一条测试发言");
  }

  console.log("\n=== 4. 跨标签页：只有 localStorage 有身份 ===");
  {
    const rec = JSON.stringify({ cred: "sdepw1:SDE2026:高鹏", name: "高鹏", exp: Date.now() + 3600000 });
    const { w } = makeDom(withTag, { local: { sde_talk_id: rec } });
    await new Promise((r) => setTimeout(r, 60));
    ok("新标签页也自动是登录态", w.document.getElementById("tk-signed").style.display === "block");
    ok("名字对", w.document.getElementById("tk-gname").textContent === "高鹏");
  }

  console.log("\n=== 5. 过期的身份不放行 ===");
  {
    const rec = JSON.stringify({ cred: "sdepw1:SDE2026:张琼", name: "张琼", exp: Date.now() - 1000 });
    const { w } = makeDom(withTag, { local: { sde_talk_id: rec }, session: {} });
    await new Promise((r) => setTimeout(r, 60));
    ok("过期就回到登录框", w.document.getElementById("tk-signed").style.display !== "block");
    ok("登录框可见", w.document.getElementById("tk-pwbox").style.display !== "none");
  }

  console.log("\n=== 6. 退出要退干净 ===");
  {
    const rec = JSON.stringify({ cred: "sdepw1:SDE2026:张琼", name: "张琼", exp: Date.now() + 3600000 });
    const { w } = makeDom(withTag, { session: { sde_gauth: rec }, local: { sde_talk_id: rec } });
    await new Promise((r) => setTimeout(r, 60));
    w.document.getElementById("tk-gout").dispatchEvent(new w.Event("click"));
    await new Promise((r) => setTimeout(r, 30));
    ok("sessionStorage 清了", !w.sessionStorage.getItem("sde_gauth"));
    ok("localStorage 副本也清了（否则一刷新又登回去）", !w.localStorage.getItem("sde_talk_id"));
    ok("登录框回来了", w.document.getElementById("tk-pwbox").style.display !== "none");
  }

  console.log("\n=== 7. 名录联想 ===");
  {
    const { w, calls } = makeDom(withTag, {});
    await new Promise((r) => setTimeout(r, 60));
    ok("首屏不拉 roster.json", calls.roster === 0);
    w.document.getElementById("tk-pw-name").dispatchEvent(new w.Event("focus"));
    await new Promise((r) => setTimeout(r, 40));
    ok("点了输入框才拉", calls.roster === 1);
    ok("名录填进 datalist", w.document.getElementById("tk-pw-roster").children.length === 2);
  }

  console.log("\n———— " + pass + " 过 / " + fail + " 败 ————\n");
  process.exit(fail ? 1 : 0);
})();
