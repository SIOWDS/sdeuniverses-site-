/* 共享讨论区组件 · 真跑模拟
 * 用 jsdom 装载真实页面（已铺开），检查讨论区渲染、登录、发言、阅读量计数、slug 推导。
 */
const fs = require("fs");
const path = require("path");
const { JSDOM, VirtualConsole } = require("jsdom");

const SITE = "/home/claude/site";
let pass = 0, fail = 0;
function ok(n, c, x) {
  if (c) { pass++; console.log("  ✓ " + n); }
  else { fail++; console.log("  ✗ " + n + (x !== undefined ? "  ← " + JSON.stringify(x) : "")); }
}

function run(page, store, extra) {
  const rel = page.replace(/^public/, "").replace(/index\.html$/, "");
  let html = fs.readFileSync(path.join(SITE, page), "utf8");
  html = html.replace(/<script src="\/assets\/sde-talk\.js[^"]*"((?: data-[a-z-]+="[^"]*")*) defer><\/script>/,
    (m, attrs) => '<script' + (attrs || "") + '>' + fs.readFileSync(path.join(SITE, "public/assets/sde-talk.js"), "utf8") + "</script>");
  // 其余外部脚本一律拆掉，免得 jsdom 去抓网络
  html = html.replace(/<script src="[^"]*"[^>]*><\/script>/g, "");
  const calls = { comments: [], im: [], pv: [], roster: 0, err: [] };
  const vc = new VirtualConsole();
  vc.on("jsdomError", (e) => calls.err.push(String(e && e.message).slice(0, 80)));
  const dom = new JSDOM(html, {
    url: "https://sdeuniverses.com" + rel,
    runScripts: "dangerously",
    virtualConsole: vc,
    beforeParse(w) {
      for (const [k, v] of Object.entries((store && store.session) || {})) w.sessionStorage.setItem(k, v);
      for (const [k, v] of Object.entries((store && store.local) || {})) w.localStorage.setItem(k, v);
      w.fetch = (u, o) => {
        const url = String(u), body = o && o.body ? JSON.parse(o.body) : null;
        if (url.startsWith("/api/comments")) {
          calls.comments.push({ url, method: (o && o.method) || "GET", body });
          return Promise.resolve({ status: 200, json: () => Promise.resolve({ ok: true, items: (extra && extra.items) || [] }) });
        }
        if (url.startsWith("/api/pv")) {
          calls.pv.push({ url, method: (o && o.method) || "GET" });
          return Promise.resolve({ status: 200, json: () => Promise.resolve({ total: 1234 }) });
        }
        if (url.startsWith("/api/im")) {
          calls.im.push(body);
          return Promise.resolve({ status: 200, json: () => Promise.resolve({ ok: true, me: { uid: "c2fd205b4c5b", name: "张琼" } }) });
        }
        if (url.includes("roster.json")) {
          calls.roster++;
          return Promise.resolve({ status: 200, json: () => Promise.resolve({ students: [{ name: "张琼" }, { name: "高鹏" }] }) });
        }
        return Promise.resolve({ status: 200, json: () => Promise.resolve({}) });
      };
    },
  });
  return { w: dom.window, d: dom.window.document, calls };
}
const wait = (ms) => new Promise((r) => setTimeout(r, ms || 70));
const ID = (n) => JSON.stringify({ cred: "sdepw1:SDE2026:" + n, name: n, exp: Date.now() + 3600000 });

(async () => {
  console.log("\n=== 1. 原本有内联块、现已转成共享件的页 ===");
  {
    const { d, calls } = run("public/column/into-equation/index.html");
    await wait();
    ok("讨论区渲染出来了", !!d.getElementById("sde-talk"));
    ok("标题在", /读者讨论区/.test((d.querySelector("#sde-talk .tk-title") || {}).textContent || ""));
    ok("登录框在", !!d.getElementById("tk-pw-name") && !!d.getElementById("tk-pw-code"));
    ok("落位在 footer 之前", (() => {
      const s = d.getElementById("sde-talk"), f = d.querySelector("footer");
      return f && s && (s.compareDocumentPosition(f) & 4) !== 0;
    })());
    ok("拉了本篇的留言", calls.comments.some((c) => c.url === "/api/comments?slug=column/into-equation"), calls.comments.map((c) => c.url));
    ok("阅读量数了一次", calls.pv.length === 1 && /slug=column\/into-equation/.test(calls.pv[0].url), calls.pv);
    ok("阅读量数字写进页面", d.getElementById("sde-pv-n").textContent === "1,234", d.getElementById("sde-pv-n").textContent);
    ok("没有脚本报错", calls.err.length === 0, calls.err);
  }

  console.log("\n=== 2. 新增讨论区的学员论文页（无 footer）===");
  {
    const p = "public/students/hu-min/substrate-dissipation/index.html";
    const { d, calls } = run(p);
    await wait();
    ok("讨论区渲染出来了", !!d.getElementById("sde-talk"));
    ok("落位在正文之内、endbox 之后", (() => {
      const s = d.getElementById("sde-talk"), e = d.querySelectorAll(".endbox");
      if (!s || !e.length) return false;
      return (e[e.length - 1].compareDocumentPosition(s) & 4) !== 0;
    })());
    ok("slug 由路径推出", calls.comments[0] && calls.comments[0].url === "/api/comments?slug=students/hu-min/substrate-dissipation", calls.comments[0]);
    ok("这类页没有阅读量位，不乱数", calls.pv.length === 0, calls.pv);
    ok("没有脚本报错", calls.err.length === 0, calls.err);
  }

  console.log("\n=== 3. 那 13 张「只有脚本没有讨论区」的坏页 ===");
  {
    const { d, calls } = run("public/students/hu-zhiying/sterilisation/index.html");
    await wait();
    ok("现在讨论区出来了", !!d.getElementById("sde-talk"));
    ok("这 13 张本来就没有阅读量位，不乱数", calls.pv.length === 0, calls.pv);
    ok("讨论区能拉取本篇留言", (calls.comments[0] || {}).url === "/api/comments?slug=students/hu-zhiying/sterilisation", (calls.comments[0]||{}).url);
    ok("没有脚本报错", calls.err.length === 0, calls.err);
  }

  console.log("\n=== 4. data-slug 覆盖（extended 并到母篇）===");
  {
    const { calls } = run("public/education/ai-era/institutional-familialization/extended/index.html");
    await wait();
    ok("用的是母篇的 slug，不是自己的路径",
      calls.comments[0] && calls.comments[0].url === "/api/comments?slug=education/ai-era/institutional-familialization",
      calls.comments[0] && calls.comments[0].url);
  }

  console.log("\n=== 5. 原先 slug 抄错的页，现在指向自己 ===");
  {
    const { calls } = run("public/students/liu-yanyan/proximal-uptake/index.html");
    await wait();
    ok("不再指到张琼名下", calls.comments[0] && calls.comments[0].url === "/api/comments?slug=students/liu-yanyan/proximal-uptake",
      calls.comments[0] && calls.comments[0].url);
  }

  console.log("\n=== 6. 登录 → 发言 → 退出 ===");
  {
    const { w, d, calls } = run("public/column/into-equation/index.html");
    await wait();
    ok("初始是未登录", d.getElementById("tk-signed").style.display === "none");
    d.getElementById("tk-pw-name").value = "zhang-qiong";
    d.getElementById("tk-pw-code").value = "SDE2026";
    d.getElementById("tk-pw-go").dispatchEvent(new w.Event("click"));
    await wait();
    ok("验了身份", calls.im.length === 1 && calls.im[0].op === "hello");
    ok("不刷新页面就进入已登录（比旧版少一次刷新）", d.getElementById("tk-signed").style.display === "block");
    ok("显示名录规范名", d.getElementById("tk-gname").textContent === "张琼");
    ok("登录框收起", d.getElementById("tk-pwbox").style.display === "none");
    ok("发言框出现", d.getElementById("tk-text").style.display === "block");

    d.getElementById("tk-text").value = "一条测试发言";
    d.getElementById("tk-send").dispatchEvent(new w.Event("click"));
    await wait();
    const post = calls.comments.filter((c) => c.method === "POST");
    ok("发言 POST 出去了", post.length === 1);
    ok("带的是站内凭证", post[0] && post[0].body.credential === "sdepw1:SDE2026:zhang-qiong", post[0] && post[0].body);

    d.getElementById("tk-gout").dispatchEvent(new w.Event("click"));
    await wait(30);
    ok("退出后 sessionStorage 清了", !w.sessionStorage.getItem("sde_gauth"));
    ok("退出后跨标签副本也清了", !w.localStorage.getItem("sde_talk_id"));
    ok("退出后回到登录框", d.getElementById("tk-signed").style.display === "none");
  }

  console.log("\n=== 7. 身份跨页/跨标签沿用 ===");
  {
    const { d } = run("public/students/hu-min/substrate-dissipation/index.html", { session: { sde_gauth: ID("高鹏") } });
    await wait();
    ok("sessionStorage 里的身份直接生效", d.getElementById("tk-signed").style.display === "block");
    ok("名字对", d.getElementById("tk-gname").textContent === "高鹏");
  }
  {
    const { d, w } = run("public/students/hu-min/substrate-dissipation/index.html", { local: { sde_talk_id: ID("高鹏") } });
    await wait();
    ok("只有 localStorage 时也生效（新标签页）", d.getElementById("tk-signed").style.display === "block");
    ok("并回填进 sessionStorage", !!w.sessionStorage.getItem("sde_gauth"));
  }
  {
    const expired = JSON.stringify({ cred: "sdepw1:SDE2026:高鹏", name: "高鹏", exp: Date.now() - 1 });
    const { d } = run("public/students/hu-min/substrate-dissipation/index.html", { local: { sde_talk_id: expired } });
    await wait();
    ok("过期身份不放行", d.getElementById("tk-signed").style.display === "none");
  }

  console.log("\n=== 8. 阅读量不重复计数 ===");
  {
    // 要挑一张「由共享件负责计数」的页（自带 sde-pv-js 的那 25 页用的是它们自己的键）
    const p = "public/column/education-dilemma-2/index.html";
    const day = new Date(Date.now() + 8 * 3600 * 1000).toISOString().slice(0, 10);
    const first = run(p);
    await wait();
    ok("第一次来 → POST 计一次", first.calls.pv.length === 1 && first.calls.pv[0].method === "POST", first.calls.pv);
    ok("并把今天记进 localStorage", first.w.localStorage.getItem("sde_pv_column_education-dilemma-2") === day,
      Object.keys(first.w.localStorage).length ? first.w.localStorage.getItem("sde_pv_column_education-dilemma-2") : "(空)");
    const again = run(p, { local: { "sde_pv_column_education-dilemma-2": day } });
    await wait();
    ok("同一天再来 → 只 GET 不再 POST", again.calls.pv.length === 1 && again.calls.pv[0].method === "GET", again.calls.pv);
  }
  {
    // 那 25 张另有独立 pv 脚本的页：共享件必须让位，否则一次访问数两遍
    const list = require("child_process").execSync(
      "grep -rl 'id=\"sde-pv-js\"' " + SITE + "/public --include=index.html | head -1", { encoding: "utf8" }).trim();
    if (list) {
      const { calls } = run(list.replace(SITE + "/", ""));
      await wait();
      ok("页面自带 pv 脚本时，共享件不再数一遍", calls.pv.length <= 1, { page: list.replace(SITE + "/public", ""), pv: calls.pv.length });
    } else ok("（没有自带 pv 脚本的页面可测）", true);
  }

  console.log("\n=== 9. 已有留言的渲染与回复 ===");
  {
    const items = [
      { id: "a1", name: "张琼", text: "顶楼", parent: "", ts: Date.now() - 60000 },
      { id: "a2", name: "高鹏", text: "回一句", parent: "a1", ts: Date.now() - 30000 },
    ];
    const { d, w } = run("public/column/into-equation/index.html", { session: { sde_gauth: ID("胡敏") } }, { items });
    await wait();
    ok("顶楼渲染", d.querySelectorAll("#tk-list .tk-item").length === 1);
    ok("楼中楼渲染", d.querySelectorAll("#tk-list .tk-sub").length === 1);
    ok("条数显示", /2 条/.test(d.getElementById("tk-count").textContent));
    d.querySelector("#tk-list .tk-reply").dispatchEvent(new w.Event("click"));
    await wait(20);
    ok("点回复进入回复态", d.getElementById("tk-replying").style.display === "block");
    ok("提示回复的是谁", /张琼/.test(d.getElementById("tk-replying-to").textContent));
  }

  console.log("\n———— " + pass + " 过 / " + fail + " 败 ————\n");
  process.exit(fail ? 1 : 0);
})();
