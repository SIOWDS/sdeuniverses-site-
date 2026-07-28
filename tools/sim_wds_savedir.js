/* 「成文 → 存到用户自选目录」的行为模拟：不复制一份平行实现，直接把 wds-mode.js 里
   那一整块抽出来，配一个假的目录句柄跑真逻辑。要验的是三件容易出事的事：
   ① 同名不覆盖（成文常常反复重写，把上一稿悄悄盖掉是最容易被骂的"贴心"）；
   ② 浏览器不支持时必须回退成普通下载，读者不能空手；
   ③ 权限被拒时说人话，且不把文件默默丢掉。 */
"use strict";
const fs = require("fs");
const SRC = "/home/claude/site/public/wds-mode.js";
const src = fs.readFileSync(SRC, "utf8");
let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };

const seg = src.slice(src.indexOf("var DIRH = null"), src.indexOf("function download(name, text) {"));
ok(seg.length > 1500, "抽到目录模块（" + seg.length + " 字符）");

// —— 假环境：假目录句柄 + 假 IndexedDB + 记账用的 download/t ——
function makeDir(name, existing) {
  const files = new Map((existing || []).map((n) => [n, ""]));
  return {
    name: name,
    _files: files,
    _perm: "granted",
    queryPermission() { return Promise.resolve(this._perm); },
    requestPermission() { this._perm = "granted"; return Promise.resolve("granted"); },
    getFileHandle(nm, opt) {
      if (files.has(nm)) return Promise.resolve(mkFile(nm));
      if (opt && opt.create) { files.set(nm, ""); return Promise.resolve(mkFile(nm)); }
      return Promise.reject(new Error("NotFound"));
    },
  };
  function mkFile(nm) {
    return { createWritable() { return Promise.resolve({ write(txt) { files.set(nm, txt); return Promise.resolve(); }, close() { return Promise.resolve(); } }); } };
  }
}
function box(win) {
  const dls = [];
  const idb = { open() { const r = {}; setTimeout(() => { r.result = null; r.onerror && r.onerror(); }, 0); return r; } };
  const fn = new Function("window", "indexedDB", "t", "download", "setTimeout",
    seg + "\nreturn { dirWrite, saveToDir, safeName, stampName, dirSupported, dirPick, setH: function (h) { DIRH = h; }, getName: dirName, dls: null };");
  const api = fn(win, idb, (k) => "[" + k + "]", (n, x) => dls.push({ n, x }), setTimeout);
  api.dls = dls;
  return api;
}

(async () => {
  /* ① 同名不覆盖 */
  console.log("\n[一] 反复成文不许盖掉上一稿");
  {
    const api = box({});
    const d = makeDir("论文", ["WDS-提炼成文-20260728-1930.md"]);
    const got = await new Promise((res) => api.dirWrite(d, "WDS-提炼成文-20260728-1930.md", "第二稿", (o, i) => res({ o, i })));
    ok(got.o === true && got.i === "WDS-提炼成文-20260728-1930-2.md", "撞名自动写成 -2：" + got.i);
    ok(d._files.get("WDS-提炼成文-20260728-1930.md") === "", "上一稿原封不动没被覆盖");
    ok(d._files.get(got.i) === "第二稿", "新稿确实落盘了");
    const got3 = await new Promise((res) => api.dirWrite(d, "WDS-提炼成文-20260728-1930.md", "第三稿", (o, i) => res({ o, i })));
    ok(got3.i === "WDS-提炼成文-20260728-1930-3.md", "第三次顺延到 -3：" + got3.i);
    const plain = await new Promise((res) => api.dirWrite(d, "全新的名字.md", "x", (o, i) => res({ o, i })));
    ok(plain.o === true && plain.i === "全新的名字.md", "不撞名时用原名，不多此一举加序号");
  }

  /* ② 不支持的浏览器：回退下载 */
  console.log("\n[二] Firefox / Safari 这类没有这个 API 的浏览器");
  {
    const api = box({});   // window 上没有 showDirectoryPicker
    ok(api.dirSupported() === false, "正确判定为不支持");
    const msgs = [];
    api.saveToDir("a.md", "正文", (m) => msgs.push(m));
    await new Promise((r) => setTimeout(r, 10));
    ok(api.dls.length === 1 && api.dls[0].n === "a.md" && api.dls[0].x === "正文", "自动回退成普通下载，读者照样拿到文件");
    ok(msgs.some((m) => m === "[dDirNoApi]"), "同时说清为什么走了下载这条路");
  }

  /* ③ 支持时：正常写入 / 权限被拒 */
  console.log("\n[三] 支持的浏览器");
  {
    const d = makeDir("我的文稿", []);
    const api = box({ showDirectoryPicker: () => Promise.resolve(d) });
    ok(api.dirSupported() === true, "判定为支持");
    const msgs = [];
    api.saveToDir("b.md", "正文二", (m) => msgs.push(m));
    await new Promise((r) => setTimeout(r, 20));
    ok(d._files.get("b.md") === "正文二", "第一次会弹目录选择器，选完就写进去");
    ok(api.dls.length === 0, "写成功就不再多下载一份");
    ok(msgs[0] === "[dDirWait]" && msgs[msgs.length - 1].indexOf("[dDirSaved]") === 0, "状态从「正在写入」走到「已存到」");
    ok(msgs[msgs.length - 1].indexOf("我的文稿/b.md") > 0, "存完把目录名和文件名都报出来：" + msgs[msgs.length - 1]);
  }
  {
    const d = makeDir("只读目录", []);
    d._perm = "denied";
    d.requestPermission = () => Promise.resolve("denied");
    const api = box({ showDirectoryPicker: () => Promise.resolve(d) });
    api.setH(d);   // 模拟"上次选过、这次权限没了"
    const msgs = [];
    api.saveToDir("c.md", "正文三", (m) => msgs.push(m));
    await new Promise((r) => setTimeout(r, 20));
    ok(msgs[msgs.length - 1] === "[dDirDenied]", "权限被拒时说人话，让读者重选一次");
    ok(d._files.size === 0, "没有权限就一个字都不写");
  }

  /* ④ 文件名 */
  console.log("\n[四] 文件名");
  {
    const api = box({});
    ok(api.safeName('报告/一:二*三?"四<五>六|七') === "报告一二三四五六七", "非法字符全清掉：" + api.safeName('报告/一:二*三?"四<五>六|七'));
    ok(api.safeName("  多  空  格  ") === "多 空 格", "空白折叠并去掉首尾");
    ok(api.safeName("很长的标题".repeat(20)).length <= 40, "过长标题截到 40 字以内");
    ok(/^\d{8}-\d{4}$/.test(api.stampName()), "时间戳形如 20260728-1930：" + api.stampName());
  }

  console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
  process.exit(F ? 1 : 0);
})();
