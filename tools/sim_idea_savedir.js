/* 「存到你选的文件夹」的针对性验证。
 * 为什么不用 sde-website-ops 里那个 sim_9grid.js：它已经跟不上这一页了——
 * 先是元素 mock 没有 getAttribute，补上后又在别处把内存跑爆。那个骨架需要重写，
 * 不能拿它当这次改动的闸门，所以这里只钉死这次真正改动的那一件事。
 *   node tools/sim_idea_savedir.js
 */
"use strict";
const fs = require("fs");
let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };

/* ---- 最小 DOM / IndexedDB / 目录选择器 mock ---- */
function mkIdb() {
  const mem = {};
  return {
    open() {
      const rq = {};
      setTimeout(() => {
        rq.result = {
          transaction(_s, mode) {
            return {
              objectStore() {
                return {
                  get(k) { const r = {}; setTimeout(() => { r.result = mem[k]; r.onsuccess && r.onsuccess(); }, 0); return r; },
                  put(v, k) { mem[k] = v; return {}; },
                  delete(k) { delete mem[k]; return {}; },
                };
              },
              set oncomplete(f) { setTimeout(f, 0); },
              set onerror(f) {},
            };
          },
          createObjectStore() {},
        };
        rq.onsuccess && rq.onsuccess();
      }, 0);
      return rq;
    },
    _mem: mem,
  };
}
let WRITTEN = [], DOWNLOADED = [], PICK_CALLS = 0, PICK_RESULT = "granted", CANCEL = false;
function mkDirHandle(nm) {
  return {
    name: nm,
    queryPermission() { return Promise.resolve(PICK_RESULT); },
    requestPermission() { return Promise.resolve(PICK_RESULT); },
    getFileHandle(fn) {
      return Promise.resolve({ createWritable: () => Promise.resolve({
        write(b) { WRITTEN.push({ dir: nm, name: fn, size: (b && b.size) || 1 }); return Promise.resolve(); },
        close() { return Promise.resolve(); },
      }) });
    },
  };
}
function boot(withPicker) {
  WRITTEN = []; DOWNLOADED = []; PICK_CALLS = 0; PICK_RESULT = "granted"; CANCEL = false;
  const anchors = [];
  const win = {};
  const doc = {
    createElement: () => { const a = { click() { DOWNLOADED.push(a.download); }, remove() {}, style: {} }; anchors.push(a); return a; },
    body: { appendChild() {} },
  };
  global.window = win; global.document = doc;
  global.indexedDB = mkIdb(); win.indexedDB = global.indexedDB;
  global.URL = { createObjectURL: () => "blob:x", revokeObjectURL() {} };
  if (withPicker) {
    win.showDirectoryPicker = () => { PICK_CALLS++; return CANCEL ? Promise.reject(new Error("abort")) : Promise.resolve(mkDirHandle("我的论文")); };
  } else { delete win.showDirectoryPicker; }
  delete win.WDSSaveDir;
  new Function("window", "document", "indexedDB", "URL", "setTimeout",
    fs.readFileSync("/home/claude/site/public/assets/wds-savedir.js", "utf8"))(win, doc, global.indexedDB, global.URL, setTimeout);
  return win.WDSSaveDir;
}
const wait = (ms) => new Promise((r) => setTimeout(r, ms || 30));

(async () => {
  console.log("① 支持目录的浏览器");
  let S = boot(true);
  ok(S.supported() === true, "识别为支持选文件夹");
  await wait();
  ok(S.name() === "", "初始没有选过任何文件夹");
  await S.ensure({ id: "t" });
  ok(PICK_CALLS === 1 && S.name() === "我的论文", "ensure 弹一次选择器并记住，实得 " + S.name());
  let r = await S.save("四篇学术论文.docx", { size: 9 });
  ok(r.where === "dir" && WRITTEN.length === 1, "文件写进了所选文件夹，不是下载目录");
  ok(WRITTEN[0].name === "四篇学术论文.docx" && WRITTEN[0].dir === "我的论文", "写入的文件名与目录都对");

  console.log("② 第二次保存不再打扰用户");
  const before = PICK_CALLS;
  await S.save("第二批_四篇.docx", { size: 9 });
  ok(PICK_CALLS === before, "复用已选目录，没有再弹选择器");
  ok(WRITTEN.length === 2 && DOWNLOADED.length === 0, "四批都写进同一个文件夹，一次都没落回下载目录");

  console.log("③ 用户撤销授权");
  PICK_RESULT = "denied"; CANCEL = true;      // 续权被拒 + 重选也取消
  r = await S.save("补规范_四篇.docx", { size: 9 });
  ok(r.where === "download" && DOWNLOADED.length === 1, "拿不到授权时回退成下载，产出不会丢");

  console.log("④ 不支持目录的浏览器（Firefox / Safari）");
  S = boot(false);
  await wait();
  ok(S.supported() === false, "如实识别为不支持");
  ok((await S.ensure({ id: "t" })) === null, "不去调用不存在的 API");
  r = await S.save("最后四篇_打磨版.docx", { size: 9 });
  ok(r.where === "download" && DOWNLOADED.length === 1, "直接走下载，不报错、不卡住");

  console.log("⑤ 改回下载目录");
  S = boot(true);
  await wait();
  await S.ensure({ id: "t" });
  ok(S.name() === "我的论文", "先选上");
  await S.forget();
  ok(S.name() === "", "清除后回到默认下载目录");

  console.log("⑥ 页面结构：四批「四篇」确实都走这条路");
  const html = fs.readFileSync("/home/claude/site/public/taste/idea-generator/index.html", "utf8");
  const ids = ["fourDlBtn", "upliftDlBtn", "normalizeDlBtn", "polishDlBtn"];
  ids.forEach((id) => {
    const i = html.indexOf("const " + id + " = ");
    const seg = html.slice(i, i + 2600);
    ok(i > 0 && seg.indexOf("saveWordDocx(") > 0, id + " 走统一的 saveWordDocx");
  });
  ok(/WDSSaveDir[\s\S]{0,200}ensure\(\{ id:'sde-idea-papers' \}\)/.test(html), "saveWordDocx 里先要目录再打包（手势没过期时）");
  ok(html.indexOf('<script src="/assets/wds-savedir.js"></script>') > 0, "页面引入了存储模块");
  ok(html.indexOf('id="saveDirPick"') > 0 && html.indexOf('id="saveDirClear"') > 0, "页面上有选择/清除文件夹的按钮");
  ok((html.match(/WDSSaveDir \? await window\.WDSSaveDir\.ensure/g) || []).length === 2, "两条自动流水线也复用同一个目录，不让用户选两次");

  console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
  process.exit(F ? 1 : 0);
})();
