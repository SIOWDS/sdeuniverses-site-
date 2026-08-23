#!/usr/bin/env node
/* 站内检索「摘录串篇」探针（2026-08-23）
   —— 这类错不报任何异常：清单里的篇名与网址都对，摘录却是别人的段落。
      唯一能证伪的办法是把每条摘录回溯到它自己那篇的索引正文里。

   判据（不看页面 HTML，看索引）：
     摘录首 24 个非空白字符，必须能在 `search/doc/<i>.json` 的 c[] 里找到，
     其中 i = manifest 里那条 url 对应的篇号。
     ⚠ 别拿文章页 HTML 去比对——专著/多页作品的索引正文来自全书，
       导读页上本来就没有那些字，会把好的判成错的（我第一版就这么误判过一次）。

   用法：
     node tools/probe_kb_excerpt.js                    # 默认五道题，打 retrieve + find
     node tools/probe_kb_excerpt.js "自己的问题" ...
     SITE=https://sdeuniverses.com node tools/probe_kb_excerpt.js
   退出码：有错配 = 1（可直接挂进培训前的开机自检）。 */

const SITE = process.env.SITE || 'https://sdeuniverses.com';
const UA = { 'user-agent': 'Mozilla/5.0 (sde-probe)', 'content-type': 'application/json' };
const QUERIES = process.argv.slice(2).length ? process.argv.slice(2) : [
  '权力是如何发生的',
  '语感的本质是什么',
  '内卷为什么停不下来',
  '音乐是如何发生的',
  '数学教学中的关系承载',
];

const norm = (s) => String(s || '').replace(/\s+/g, '');
const KEY = 24;   // 用多少个字符去回溯：太短会撞车，太长会被索引里的换行切断

let MAN = null;
async function manifest() {
  if (MAN) return MAN;
  const r = await fetch(SITE + '/search/manifest.json', { headers: UA });
  const j = await r.json();
  const byUrl = new Map();
  for (const d of (j.docs || [])) byUrl.set(String(d.u || '').replace(/^https?:\/\/[^/]+/, ''), d.i);
  MAN = { built: j.built, n: (j.docs || []).length, byUrl };
  return MAN;
}

const DOC = new Map();
async function docText(i) {
  if (DOC.has(i)) return DOC.get(i);
  const r = await fetch(SITE + '/search/doc/' + i + '.json', { headers: UA });
  if (!r.ok) { DOC.set(i, null); return null; }
  const j = await r.json();
  const t = norm((j.c || []).join(''));
  DOC.set(i, t);
  return t;
}

/* 一条摘录的裁定：✓ 出自本篇 / ✗ 串篇 / ? 无从判定（篇号查不到、doc 取不到、摘录太短） */
async function verify(u, excerpt) {
  const man = await manifest();
  const path = String(u || '').replace(/^https?:\/\/[^/]+/, '');
  const i = man.byUrl.get(path);
  if (i === undefined) return { v: '?', why: 'manifest 里没有这条 url' };
  const frag = norm(excerpt).slice(0, KEY);
  if (frag.length < 10) return { v: '?', why: '摘录太短' };
  const t = await docText(i);
  if (t === null) return { v: '?', why: 'doc/' + i + '.json 取不到' };
  return t.indexOf(frag) >= 0 ? { v: '✓', why: 'i=' + i } : { v: '✗', why: 'i=' + i + ' 的正文里没有这段' };
}

async function probeRetrieve(q) {
  const r = await fetch(SITE + '/api/kb/retrieve', {
    method: 'POST', headers: UA, body: JSON.stringify({ q, budget: 16, cap: 4000 }),
  });
  const j = await r.json();
  const parts = String(j.block || '').split('【来源：').slice(1);
  const srcs = j.srcs || [];
  const out = [];
  for (let k = 0; k < parts.length; k++) {
    const body = parts[k].slice(parts[k].indexOf('\n') + 1);
    const u = srcs[k] && srcs[k].u;
    out.push(Object.assign({ u, snip: body.slice(0, 30) }, await verify(u, body)));
  }
  return { n: j.n, rows: out };
}

async function probeFind(q) {
  const r = await fetch(SITE + '/api/kb/find', {
    method: 'POST', headers: UA, body: JSON.stringify({ q, k: 6 }),
  });
  const j = await r.json();
  const out = [];
  for (const d of (j.docs || [])) {
    out.push(Object.assign({ u: d.u, snip: String(d.snip || '').slice(0, 30) }, await verify(d.u, d.snip)));
  }
  return { n: (j.docs || []).length, rows: out };
}

(async () => {
  const man = await manifest();
  console.log('索引：' + man.n + ' 篇 · built ' + man.built + ' · 站点 ' + SITE + '\n');
  let bad = 0, unk = 0, good = 0;
  for (const q of QUERIES) {
    for (const [name, fn] of [['retrieve', probeRetrieve], ['find', probeFind]]) {
      let res;
      try { res = await fn(q); }
      catch (e) { console.log('【' + q + '】' + name + ' 调用失败：' + e.message); continue; }
      const b = res.rows.filter((x) => x.v === '✗').length;
      const u = res.rows.filter((x) => x.v === '?').length;
      bad += b; unk += u; good += res.rows.length - b - u;
      console.log('【' + q + '】' + name + '：' + res.rows.length + ' 条'
        + (b ? '  ← 串篇 ' + b + ' 条' : '') + (u ? '  · 无从判定 ' + u : ''));
      for (const x of res.rows) {
        if (x.v !== '✓') console.log('   ' + x.v + ' ' + x.u + '  [' + x.why + ']  「' + x.snip + '…」');
      }
    }
  }
  console.log('\n合计：出自本篇 ' + good + ' · 串篇 ' + bad + ' · 无从判定 ' + unk);
  console.log(bad ? '✗ 仍在串篇——不要在这个状态下开培训/跑碰撞' : '✓ 未见串篇');
  process.exit(bad ? 1 : 0);
})();
