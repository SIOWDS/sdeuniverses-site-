// 真·装载体检：用 jsdom 把 /sde-wechat/ 整页跑起来，看装载期有没有异常，
// 以及各功能的按钮是不是都接上了线（onclick / 事件）。
// 跑法：node /home/claude/loadcheck.mjs
import fs from "fs";
import { JSDOM, VirtualConsole } from "jsdom";   // 需要先装：npm i jsdom

const P = new URL("../public/sde-wechat/index.html", import.meta.url);
let html = fs.readFileSync(P, "utf8");

const errs = [];
const vc = new VirtualConsole();
vc.on("jsdomError", (e) => errs.push("jsdomError: " + (e.stack || e.message)));
vc.on("error", (...a) => errs.push("console.error: " + a.join(" ")));

const dom = new JSDOM(html, {
  runScripts: "dangerously",
  url: "https://sdeuniverses.com/sde-wechat/",
  virtualConsole: vc,
  pretendToBeVisual: true,
  beforeParse(w) {
    w.fetch = () => new Promise(() => {});          // 网络全挂住，只看装载
    w.matchMedia = () => ({ matches: false, addListener() {}, addEventListener() {} });
    w.HTMLCanvasElement.prototype.getContext = () => ({ fillRect() {}, drawImage() {}, fillStyle: "" });
    w.HTMLCanvasElement.prototype.toDataURL = () => "data:image/jpeg;base64,SMALL";
    w.scrollTo = () => {};
    // addEventListener 接的线 onclick 上看不见 —— 记一笔，否则会误报"没接线"
    const AE = w.EventTarget.prototype.addEventListener;
    w.__wired = new Map();
    w.EventTarget.prototype.addEventListener = function (t, fn, o) {
      if (this && this.id) w.__wired.set(this.id + ":" + t, 1);
      return AE.call(this, t, fn, o);
    };
  },
});

await new Promise((r) => setTimeout(r, 600));
const { window } = dom;
const d = window.document;

console.log("\n===== 装载期异常 =====");
if (!errs.length) console.log("  (\u65e0)");
errs.forEach((e) => console.log("  \u2717 " + e.split("\n").slice(0, 6).join("\n     ")));

console.log("\n===== \u5173\u952e\u6309\u94ae/\u8f93\u5165\u662f\u5426\u63a5\u7ebf\uff08\u672c\u5de5\u5177\u662f**\u672a\u767b\u5f55**\u72b6\u6001\uff09=====");
console.log("  \u6ce8\uff1a\u767b\u5f55\u540e\u624d\u63a5\u7ebf\u7684\uff08vtWire/cdWire \u91cc\u90a3\u4e9b\uff09\u5728\u8fd9\u91cc\u663e\u793a\u4e3a\u672a\u63a5\u7ebf\uff0c\u5c5e\u6b63\u5e38\uff1b\n  \u5bb9\u5668\u7c7b\uff08\u7f29\u7565\u533a\uff09\u7684\u70b9\u51fb\u5728\u5b50\u8282\u70b9\u4e0a\uff0c\u4e5f\u4e0d\u7b97\u95ee\u9898\u3002\u771f\u6b63\u8981\u76ef\u7684\u662f\u4e0a\u9762\u90a3\u6bb5\u201c\u88c5\u8f7d\u671f\u5f02\u5e38\u201d\u3002");
const WIRED = [
  ["mp-ok", "\u53d1\u8868\u670b\u53cb\u5708"],
  ["mp-thumbs", "\u56fe\u7247\u7f29\u7565\u533a"],
  ["mp-file", "\u9009\u56fe input"],
  ["mp-docpick", "\u9009\u6587\u7ae0\uff08\u5206\u4eab\u6587\u7ae0\uff09"],
  ["mp-doc", "\u6587\u7ae0 input"],
  ["mu-go", "\u2460 SDE\u91d1\u53e5\u751f\u4ea7\u673a"],
  ["mu-vault", "\u4ece\u5e93\u5b58\u91cc\u6311\uff08\u767b\u5f55\u540e\u624d\u63a5\uff09"],
  ["ic-go", "\u2461 \u5403\u56fe\u51fa\u91d1\u53e5"],
  ["ic-vd", "\u5403\u56fe\u57fa\u5e95\u9009\u62e9"],
  ["ic-key", "\u5403\u56fe Key"],
];
for (const [id, name] of WIRED) {
  const n = d.getElementById(id);
  if (!n) { console.log("  \u2717 " + name + "\uff1a\u9875\u9762\u4e0a\u6839\u672c\u6ca1\u6709 #" + id); continue; }
  const W = window.__wired || new Map();
  const on = typeof n.onclick === "function" || typeof n.onchange === "function" || typeof n.oninput === "function"
    || ["click", "change", "input"].some((t) => W.has(id + ":" + t));
  console.log((on ? "  \u2713 " : "  \u2717 ") + name + "\uff08#" + id + "\uff09" + (on ? "" : " \u2014\u2014 \u6ca1\u63a5\u7ebf"));
}

console.log("\n===== 函数是否都定义到了（装载被打断的话，后面的会缺）=====");
const FNS = ["moOpenPost", "moPaintThumbs", "muPaint", "icPaint", "icParse", "moPaintDoc", "vtWire"];
for (const f of FNS) console.log((new RegExp("function\\s+" + f + "\\s*\\(").test(html) ? "  \u2713 " : "  \u2717 ") + f + " \u5df2\u5b9a\u4e49");

console.log("\n===== 脚本块数量 =====");
console.log("  inline scripts: " + [...d.querySelectorAll("script:not([src])")].length);
process.exit(errs.length ? 1 : 0);
