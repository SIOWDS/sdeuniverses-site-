/* 「存到用户自选目录」的行为模拟。实现只有一份——/assets/wds-savedir.js（window.WDSSaveDir），
   金点子发生器、WDS 助手成文、与WDS对话的成文弹窗都用它。这里把那份真源码跑起来，
   配假的目录句柄与假 IndexedDB，验四件容易出事的事：
   ① 撞名不覆盖（opt-in，不打扰已有调用方）；② 不支持/取消/写失败一律回退下载，读者不空手；
   ③ 权限被撤销时当没选过处理，不静默失败；④ 文件名清洗与时间戳。
   另加静态断言：两个调用方（wds-mode.js / wds-dialogue）都尽早加载它、都没有再自写一套。 */
"use strict";
const fs = require("fs");
const SRC = "/home/claude/site/public/assets/wds-savedir.js";
const src = fs.readFileSync(SRC, "utf8");
let P = 0, F = 0;
const ok = (c, m) => { c ? (P++, console.log("  PASS " + m)) : (F++, console.log("  FAIL " + m)); };

function makeDir(name, existing) {
  const files = new Map((existing || []).map((n) => [n, ""]));
  const mkFile = (nm) => ({ createWritable: () => Promise.resolve({ write(t) { files.set(nm, t); return Promise.resolve(); }, close: () => Promise.resolve() }) });
  return {
    name, _files: files, _perm: "granted", _denyWrite: false,
    queryPermission() { return Promise.resolve(this._perm); },
    requestPermission() { return Promise.resolve(this._perm === "prompt" ? "granted" : this._perm); },
    getFileHandle(nm, opt) {
      if (this._denyWrite && opt && opt.create) return Promise.reject(new Error("no write"));
      if (files.has(nm)) return Promise.resolve(mkFile(nm));
      if (opt && opt.create) { files.set(nm, ""); return Promise.resolve(mkFile(nm)); }
      return Promise.reject(new Error("NotFound"));
    },
  };
}
// 每次要一个全新的 WDSSaveDir 实例：源码是 IIFE，用 new Function 换一套 window 即可
function load(win, stored) {
  const dls = [];
  const idbStore = new Map(stored ? [["dir", stored]] : []);
  const indexedDB = {
    open() {
      const rq = {};
      setTimeout(() => {
        rq.result = {
          transaction(_s, mode) {
            const tx = {};
            setTimeout(() => tx.oncomplete && tx.oncomplete(), 0);
            tx.objectStore = () => ({
              get(k) { const r = {}; setTimeout(() => { r.result = idbStore.get(k); r.onsuccess && r.onsuccess(); }, 0); return r; },
              put(v, k) { idbStore.set(k, v); return {}; },
              delete(k) { idbStore.delete(k); return {}; },
            });
            return tx;
          },
          objectStoreNames: { contains: () => true },
          createObjectStore() {},
        };
        rq.onsuccess && rq.onsuccess();
      }, 0);
      return rq;
    },
  };
  const W = Object.assign({ indexedDB }, win);
  const doc = { createElement: () => ({ click() { dls.push({ n: this.download }); }, remove() {}, style: {} }), body: { appendChild() {} } };
  new Function("window", "indexedDB", "document", "URL", "setTimeout", src)(
    W, indexedDB, doc, { createObjectURL: () => "blob:x", revokeObjectURL() {} }, setTimeout);
  return { api: W.WDSSaveDir, dls, idbStore };
}
const wait = (ms) => new Promise((r) => setTimeout(r, ms || 25));

(async () => {
  console.log("\n[一] 撞名不覆盖（opt-in）");
  {
    const d = makeDir("论文", ["WDS-问对WDS-20260728-1930.md"]);
    const { api } = load({ showDirectoryPicker: () => Promise.resolve(d) }, d);
    await wait();
    const r = await api.save("WDS-问对WDS-20260728-1930.md", "第二稿", { noOverwrite: true });
    ok(r.where === "dir" && r.name === "WDS-问对WDS-20260728-1930-2.md", "撞名顺延到 -2：" + r.name);
    ok(d._files.get("WDS-问对WDS-20260728-1930.md") === "", "上一稿一个字没被动");
    ok(d._files.get(r.name) === "第二稿", "新稿确实落盘");
    const r3 = await api.save("WDS-问对WDS-20260728-1930.md", "第三稿", { noOverwrite: true });
    ok(r3.name.endsWith("-3.md"), "第三次顺延到 -3：" + r3.name);
    const r4 = await api.save("全新名字.md", "x", { noOverwrite: true });
    ok(r4.name === "全新名字.md", "不撞名就用原名，不多此一举");
  }
  {
    const d = makeDir("论文", ["a.md"]);
    const { api } = load({ showDirectoryPicker: () => Promise.resolve(d) }, d);
    await wait();
    const r = await api.save("a.md", "覆盖", {});
    ok(r.name === "a.md" && d._files.get("a.md") === "覆盖", "不传 noOverwrite 时行为不变（不打扰已有调用方）");
  }

  console.log("\n[二] 拿不到目录时不许把产出弄丢");
  {
    const { api, dls } = load({});   // 没有 showDirectoryPicker
    await wait();
    ok(api.supported() === false, "正确判定为不支持");
    const r = await api.save("b.md", "正文", { noOverwrite: true });
    ok(r.where === "download" && dls.length === 1, "回退成普通下载");
  }
  {
    const { api, dls } = load({ showDirectoryPicker: () => Promise.resolve(null) });
    await wait();
    const r = await api.save("c.md", "正文", { silent: false, noOverwrite: true });
    ok(r.where === "download" && dls.length === 1, "用户按取消也回退下载，不是错误");
  }
  {
    const d = makeDir("只读", []); d._denyWrite = true;
    const { api, dls } = load({ showDirectoryPicker: () => Promise.resolve(d) }, d);
    await wait();
    const r = await api.save("d.md", "正文", { noOverwrite: true });
    ok(r.where === "download" && dls.length === 1, "写失败也回退下载");
  }

  console.log("\n[三] 权限被撤销");
  {
    const d = makeDir("旧目录", []); d._perm = "denied";
    const picked = makeDir("新目录", []);
    const { api, idbStore } = load({ showDirectoryPicker: () => Promise.resolve(picked) }, d);
    await wait();
    const h = await api.ensure({});
    ok(h === picked, "旧句柄权限没了就当没选过，重新弹选择器");
    ok(idbStore.get("dir") === picked, "新目录被记住");
  }

  console.log("\n[四] 文件名与时间戳");
  {
    const { api } = load({});
    await wait();
    ok(api.safeName('报告/一:二*三?"四<五>六|七') === "报告一二三四五六七", "非法字符清掉：" + api.safeName('报告/一:二*三?"四<五>六|七'));
    ok(api.safeName("  多  空  格  ") === "多 空 格", "空白折叠并去首尾");
    ok(api.safeName("很长标题".repeat(30)).length <= 40, "过长截到 40 字以内");
    ok(/^\d{8}-\d{4}$/.test(api.stamp()), "时间戳形如 20260728-1930：" + api.stamp());
  }

  console.log("\n[五] 两个调用方都用这一份，没有第二套实现");
  {
    const wm = fs.readFileSync("/home/claude/site/public/wds-mode.js", "utf8");
    const dlg = fs.readFileSync("/home/claude/site/public/taste/wds-dialogue/index.html", "utf8");
    ok(wm.includes("/assets/wds-savedir.js") && dlg.includes("/assets/wds-savedir.js"), "两处都引用共享模块");
    ok(!/indexedDB\.open\(\s*DIRDB/.test(wm) && !wm.includes('DIRDB = "wds-fs"'), "wds-mode.js 里那套重复实现已删干净");
    ok(!/showDirectoryPicker\s*\(/.test(dlg), "对话页没有再自写一个目录选择器");
    ok(/SAVEDIR_SRC = "\/assets\/wds-savedir\.js/.test(wm) && /sc\.src = SAVEDIR_SRC/.test(wm) && /sc\.src = "\/assets\/wds-savedir\.js/.test(dlg), "两处都在脚本一开始就把它拉进来（点击那一刻句柄要已在内存里）");
    ok(dlg.includes("noOverwrite: true") && wm.includes("noOverwrite: true"), "两处都启用了撞名顺延");
    ok(dlg.includes("tbtn savedir") && dlg.includes("\\u5b58\\u5230\\u76ee\\u5f55") && dlg.includes("saveDoc("), "对话页的成文弹窗有「存到目录」按钮并接上写入");
    ok(wm.includes("function exportSession") && wm.includes("saveToDir(\"WDS-\" + safeName(t(\"convoTitle\"))"), "导出本场对话也走同一个目录");
  }

  console.log("\n===== " + P + " PASS / " + F + " FAIL =====");
  process.exit(F ? 1 : 0);
})();
