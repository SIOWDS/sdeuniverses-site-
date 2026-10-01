#!/usr/bin/env node
/* 语言分站取料白名单对账 —— node tools/sim_lang_scope.js
   src/worker.js 的 LANG_PRE 决定 ChatJohn（lang.sdeuniverses.com）能检索到哪些篇目。
   漏一条的表现是「站上读得到、John 引不到」，没人会当场发现：2026-10-01 查出
   第 105／108／183 号三部胡志英专著出版一个多月都不在表上。本脚本把四处逐条对账：
     ① LANG_PRE 每条都是带结尾斜杠的网址前缀，且 public/ 下真有这一页；
     ② /sites/lang/all/ 上列出的每一篇，都被 LANG_PRE 覆盖；
     ③ LANG_PRE 里的每一部专著（/books/m/<号>/），都列在 /sites/lang/all/ 上；
     ④ 书目 public/books/catalog.json 里署名胡志英的每一部专著，都在 LANG_PRE 上；
     ⑤ site-data.json 里归语言站的书号，都在 LANG_PRE 上。
   任一条不过即退出码 1。改 LANG_PRE、发胡志英新书、改 /all/ 页之后都要跑。 */
"use strict";
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const PUB = path.join(ROOT, "public");
const read = (p) => fs.readFileSync(path.join(ROOT, p), "utf8");

const worker = read("src/worker.js");
const m = worker.match(/const LANG_PRE = \[([\s\S]*?)\n\];/);
if (!m) { console.error("✗ 在 src/worker.js 里找不到 const LANG_PRE = [...]"); process.exit(1); }
const body = m[1].split("\n").map((l) => l.replace(/\/\/.*$/, "")).join("\n");
const PRE = [...body.matchAll(/"([^"]+)"/g)].map((x) => x[1]);

const errs = [];
const covered = (u) => PRE.some((p) => u.indexOf(p) === 0);

// ①
const seen = new Set();
for (const p of PRE) {
  if (seen.has(p)) errs.push("① 重复条目：" + p);
  seen.add(p);
  if (!p.startsWith("/") || !p.endsWith("/")) { errs.push("① 不是带结尾斜杠的前缀：" + p); continue; }
  if (!fs.existsSync(path.join(PUB, p, "index.html"))) errs.push("① public/ 下没有这一页：" + p);
}

// ②
const allHtml = read("public/sites/lang/all/index.html");
const CONTENT = /^\/(students|books\/m|column|confluence|paradigm)\//;
const listed = new Set();
for (const x of allHtml.matchAll(/href="([^"#?]+)/g)) {
  const u = x[1];
  if (!CONTENT.test(u)) continue;
  if (/^\/students\/[^/]+\/$/.test(u)) continue;   // 作者主页（页脚链接），不是篇目
  listed.add(u);
  if (!covered(u)) errs.push("② /all/ 上列着、John 取不到：" + u);
}

// ③
for (const p of PRE) {
  if (!/^\/books\/m\/\d+\/$/.test(p)) continue;
  if (![...listed].some((u) => u.indexOf(p) === 0)) errs.push("③ 白名单里的专著没列在 /all/ 上：" + p);
}

// ④
const cat = JSON.parse(read("public/books/catalog.json"));
const books = Array.isArray(cat) ? cat : (cat.books || []);
let huN = 0;
for (const b of books) {
  if (!(b.authors || []).some((a) => String(a).indexOf("胡志英") >= 0)) continue;
  if (b.number == null) continue;
  huN++;
  const p = "/books/m/" + b.number + "/";
  if (!PRE.includes(p)) errs.push("④ 胡志英专著不在白名单：" + p + "《" + b.title + "》");
}

// ⑤
const site = JSON.parse(read("public/sites/site-data.json"));
for (const id of ((site.subsites.lang || {}).ownership || {}).book_ids || []) {
  const p = "/books/m/" + id + "/";
  if (!PRE.includes(p)) errs.push("⑤ 归语言站的书号不在白名单：" + p);
}

console.log("LANG_PRE " + PRE.length + " 条 · /all/ 列出 " + listed.size + " 个篇目链接 · 书目中胡志英专著 " + huN + " 部");
if (errs.length) {
  console.error("\n✗ 对账不过（" + errs.length + " 处）：");
  for (const e of errs) console.error("   " + e);
  process.exit(1);
}
console.log("[OK] 白名单、/all/ 页、书目、站点数据四处一致");
