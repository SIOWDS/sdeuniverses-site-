/* 只钉一件事：**授权过期时不许把用户选好的文件夹忘掉**。
 *
 * 这个 bug 的形状（2026-07-30 实修）：
 *   save() 内部走 ensure({silent:true})，而 ensure 对已存句柄一律调 requestPermission()。
 *   可 requestPermission 必须在用户手势内，save() 却是在 Packer.toBlob() 打包完之后才被调到的——
 *   一篇上万字的 Word 打包要好几秒，那时手势早过期，Chrome **不弹框、直接回 'prompt'**。
 *   旧代码把这个 'prompt' 当成"用户撤销了授权"，执行 handle=null + idbDel()：
 *   用户选好的文件夹在一次下载之后凭空消失，"存储位置"变回默认下载目录，
 *   看起来就是"存储点不动了"。
 *
 * 为什么要单独一个 sim：这一层全是**真浏览器才有的行为**（手势有效期、queryPermission/
 * requestPermission 的区别），jsdom 跑整页复现不出来；只能把权限模型打桩，直测模块。
 *
 *   node tools/sim_savedir_perm.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const SRC = fs.readFileSync(path.join(__dirname, "..", "public", "assets", "wds-savedir.js"), "utf8");

let P = 0, F = 0;
const ok = (c, m, extra) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m + (extra ? "  ← " + extra : ""))); };

/* ---- 打桩：一个可编程的目录句柄 + IndexedDB + showDirectoryPicker ---- */
function mkEnv(opts) {
  opts = opts || {};
  const mem = {};                       // 冒充 IndexedDB 的那一格
  const log = { requested: 0, queried: 0, downloads: [], writes: [] };

  // 桩必须跟真浏览器一样有状态：requestPermission 一旦成功，
  // 后续 queryPermission 就该回 'granted'。桩不带状态的话，
  // 「续权之后这一趟能写进去」这条根本测不出来（第一版就栽在这）。
  let state = opts.state || "prompt";
  const handle = {
    name: "我的论文文件夹",
    queryPermission() { log.queried++; return Promise.resolve(state); },
    requestPermission() {
      log.requested++;
      // 真浏览器：手势外调用不弹框，直接回 'prompt'
      if (opts.gestureAlive) state = "granted";
      return Promise.resolve(state);
    },
    getFileHandle() {
      return Promise.resolve({ createWritable: () => Promise.resolve({ write(b) { log.writes.push(b); return Promise.resolve(); }, close: () => Promise.resolve() }) });
    },
  };

  const win = {
    showDirectoryPicker: () => (opts.pickerPicks === false ? Promise.reject(new Error("cancel")) : Promise.resolve(handle)),
    indexedDB: {
      open() {
        const rq = {};
        setTimeout(() => {
          rq.result = {
            createObjectStore() {},
            transaction() {
              const t = {};
              const store = {
                get() { const r = {}; setTimeout(() => { r.result = mem.dir; r.onsuccess && r.onsuccess(); }, 0); return r; },
                put(v) { mem.dir = v; return {}; },
                delete() { delete mem.dir; return {}; },
              };
              t.objectStore = () => store;
              Object.defineProperty(t, "oncomplete", { set(f) { setTimeout(f, 0); } });
              Object.defineProperty(t, "onerror", { set(f) {} });
              return t;
            },
          };
          rq.onsuccess && rq.onsuccess();
        }, 0);
        return rq;
      },
    },
    URL: { createObjectURL: () => "blob:x", revokeObjectURL() {} },
  };
  const doc = {
    createElement: () => ({ set href(v) {}, set download(v) { log.downloads.push(v); }, click() {}, remove() {} }),
    body: { appendChild() {}, removeChild() {} },
  };
  if (opts.preloaded) mem.dir = handle;

  // 模块是 IIFE 挂 window，用 Function 注入桩环境跑它
  const fn = new Function("window", "document", "indexedDB", "URL", "setTimeout", "Promise", SRC);
  fn(win, doc, win.indexedDB, win.URL, setTimeout, Promise);
  return { S: win.WDSSaveDir, log, mem, handle };
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  console.log("\n[一] 手势过期（requestPermission 回 'prompt'）—— 这是 bug 的现场");
  {
    const e = mkEnv({ preloaded: true, state: "prompt", gestureAlive: false });
    await e.S.load(); await sleep(20);
    ok(e.S.name() === "我的论文文件夹", "开局：上次选的文件夹已经取回来了", e.S.name());
    const r = await e.S.save("四篇.docx", { size: 9 });
    ok(r.where === "download", "这一趟回退成下载（写不进去就绝不丢产出）", r.where);
    ok(!!e.mem.dir, "**文件夹没有被删掉**（旧代码就是在这里把它 idbDel 掉的）");
    ok(e.S.name() === "我的论文文件夹", "存储位置照旧显示用户选的那个，不会变回默认下载目录", e.S.name());
    ok(r.reason === "perm", "回退原因带出来了，界面才能说实话而不是只说'已下载'", String(r.reason));
    ok(e.log.requested === 0, "**silent 模式一次都没调 requestPermission**（手势外调它本就无效）", "调了 " + e.log.requested + " 次");
    ok(e.log.queried >= 1, "只 queryPermission 查一下");
  }

  console.log("\n[二] 用户明确拒绝（denied）—— 这时才该忘掉");
  {
    const e = mkEnv({ preloaded: true, state: "denied", gestureAlive: false });
    await e.S.load(); await sleep(20);
    const r = await e.S.save("四篇.docx", { size: 9 });
    ok(r.where === "download", "回退下载");
    await sleep(30);   // idbDel 是 fire-and-forget，等它落地再看盘
    ok(!e.mem.dir, "明确 denied 才把文件夹忘掉（这一条是有意保留的）");
    ok(e.S.name() === "", "存储位置回到未选状态");
  }

  console.log("\n[三] 授权仍在（granted）—— 正常写进文件夹");
  {
    const e = mkEnv({ preloaded: true, state: "granted", gestureAlive: false });
    await e.S.load(); await sleep(20);
    const r = await e.S.save("四篇.docx", { size: 9 });
    ok(r.where === "dir", "直接写进文件夹", r.where);
    ok(e.log.writes.length === 1, "确实写了一次");
    ok(!r.reason, "正常写入不带 reason");
  }

  console.log("\n[四] 手势内的 ensure()（非 silent）—— 能把过期的权限续回来");
  {
    const e = mkEnv({ preloaded: true, state: "prompt", gestureAlive: true });
    await e.S.load(); await sleep(20);
    const h = await e.S.ensure({ id: "x" });
    ok(!!h, "续权成功，拿回句柄");
    ok(e.log.requested === 1, "非 silent 模式才请求权限，且只请求一次", "调了 " + e.log.requested + " 次");
    ok(!!e.mem.dir, "文件夹还在");
    const r = await e.S.save("四篇.docx", { size: 9 });
    ok(r.where === "dir", "续权之后这一趟就写进文件夹了（＝页面里那句『再点一次即可』当真）", r.where);
  }

  console.log("\n[五] 从没选过文件夹 —— 静默回退下载，不打扰");
  {
    const e = mkEnv({ preloaded: false });
    await e.S.load(); await sleep(20);
    const r = await e.S.save("四篇.docx", { size: 9 });
    ok(r.where === "download", "回退下载");
    ok(!r.reason, "没选过就不该报 perm 原因（那会把用户搞糊涂）", String(r.reason));
  }

  console.log("\n[六] 源码层面钉死，防以后改回去");
  {
    ok(/perm\(handle, !opts\.silent\)/.test(SRC), "**silent 模式不许请求权限**：perm(handle, !opts.silent)");
    ok(/if \(s === "denied"\) \{ handle = null; idbDel\(\); fire\(\); \}/.test(SRC),
       "**只有 denied 才 idbDel**（旧代码是无条件删，那正是 bug）");
    ok(!/if \(s === "granted"\) return handle;\s*\n\s*handle = null; idbDel\(\)/.test(SRC),
       "旧的无条件删除写法确已不在");
    ok(/reason = "perm"/.test(SRC), "回退原因有带出来");
  }

  console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
  process.exit(F ? 1 : 0);
})();
