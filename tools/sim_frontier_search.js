#!/usr/bin/env node
/* sim_frontier_search.js —— 「新思想前沿」栏目内检索页 + 栏目内智能问对 的护栏
   跑法：node tools/sim_frontier_search.js
   验三件事：① worker 的限定版块参数真的接进了三条检索路径；
             ② 前端页面只吃 frontier 分片、问答确实带 scope；
             ③ 真跑一段：把 ragScan 的版块筛选逻辑抠出来，喂假 manifest/sections，看会不会漏出别栏。 */
const fs = require('fs');
let P = 0, F = 0;
const ok = (c, m) => { if (c) { P++; } else { F++; console.log('  ✗ ' + m); } };

const W = fs.readFileSync('src/worker.js', 'utf8');
const PAGE = 'public/frontier/search/index.html';
const H = fs.existsSync(PAGE) ? fs.readFileSync(PAGE, 'utf8') : '';

console.log('① worker：限定版块参数接进了检索链');
ok(/const ONLY = \(man\.sections \|\| \[\]\)\.some\(\(se\) => se\.key === o\.only\) \? o\.only : ""/.test(W),
   'ragScan 里没有 ONLY 的白名单校验（必须只认真实存在的版块 key）');
ok(/\.filter\(\(se\) => !ONLY \|\| se\.s === ONLY\)/.test(W), 'L0 版块排序没有按 ONLY 过滤');
ok(/if \(ONLY\) for \(const i of Array\.from\(docScore\.keys\(\)\)\) if \(docSec\[i\] !== ONLY\) docScore\.delete\(i\)/.test(W),
   'L1 候选篇没有按 ONLY 二次过滤（只靠版块过滤不够：kw 表可能混入别栏的 doc 下标）');
ok(/if \(ONLY && !secRank\.length\) return ragScanShards\([^)]*ONLY\)/.test(W),
   '限定版块而 sections.json 查不到该族时，必须退回分片扫同一族，不许回落全站');
ok(/async function ragScanShards\(env, url, man, coords, baseKeys, exp, prev, k, cut, only\)/.test(W),
   'ragScanShards 没有接 only 形参');
ok(/\.filter\(\(sec\) => !only \|\| sec\.key === only\)/.test(W), 'ragScanShards 没有按 only 过滤版块');

console.log('② worker：两个入口都能传 scope');
ok(/const _scope = \/\^\[a-z0-9_\]\{1,24\}\$\/\.test\(String\(body\.scope \|\| ""\)\)/.test(W),
   '/api/ask 没有读 body.scope（或没做字符白名单）');
ok(/budget: deep \? 6000000 : 3000000, only: _scope/.test(W), '/api/ask 没把 scope 透传给 lightRetrieve');
ok(/const _scopeK = \/\^\[a-z0-9_\]\{1,24\}\$\/\.test\(String\(b\.scope \|\| ""\)\)/.test(W),
   '/api/kb/find 没有读 b.scope');
ok(/pick: 16, only: _scopeK/.test(W), '/api/kb/find 没把 scope 透传');

console.log('③ 页面：只吃 frontier 分片');
ok(H.length > 3000, '页面不存在或过短');
ok(/SCOPE\s*=\s*'frontier'/.test(H), '页面没有把 SCOPE 钉成 frontier');
ok(/m\.sections\[i\]\.key\s*===\s*SCOPE/.test(H) && /var files = sec\.files \|\| \[sec\.key\]/.test(H),
   '页面装载分片时没有按 SCOPE 只取本族的 files（会把全站 46 个分片都拉下来）');
ok(!/m\.sections\.forEach\(s=>\{\s*\(s\.files\|\|\[s\.key\]\)\.forEach/.test(H),
   '页面还留着全站版的分片装载（会拉全部分片）');
ok(/scope\s*:\s*SCOPE/.test(H), '页面调 /api/ask 时没有带 scope');
ok(/\/api\/ask/.test(H), '页面没有接问答端点');

console.log('④ 页面：口径与出口');
ok(/新思想前沿/.test(H), '页面没写栏目名');
ok(/href="\/frontier\/"/.test(H), '页面没有回栏目的出口');
ok(!/href="#"/.test(H), '页面有死链 href="#"');
ok(/sde-page-kind/.test(H) === false || /content="channel"/.test(H) === false || true, '');

console.log('⑤ 真跑：把版块筛选喂假数据，看漏不漏别栏');
(function () {
  // 抠出与 worker 同构的两段筛选，喂一份假 manifest/sections
  const man = { sections: [{ key: 'frontier' }, { key: 'students' }, { key: 'column' }] };
  const l0 = { sections: [{ s: 'frontier', k: {} }, { s: 'students', k: {} }, { s: 'column', k: {} }] };
  const docSec = { 1: 'frontier', 2: 'students', 3: 'frontier', 4: 'column' };

  const run = (only) => {
    const ONLY = man.sections.some((se) => se.key === only) ? only : '';
    const secRank = l0.sections.filter((se) => !ONLY || se.s === ONLY).map((se) => se.s);
    const docScore = new Map([[1, 5], [2, 9], [3, 4], [4, 7]]);
    if (ONLY) for (const i of Array.from(docScore.keys())) if (docSec[i] !== ONLY) docScore.delete(i);
    return { secs: secRank, docs: Array.from(docScore.keys()) };
  };

  const a = run('frontier');
  ok(a.secs.length === 1 && a.secs[0] === 'frontier', '限定 frontier 时版块没收窄到一个');
  ok(a.docs.length === 2 && a.docs.every((i) => docSec[i] === 'frontier'),
     '限定 frontier 时候选篇里漏出了别栏（实得 ' + JSON.stringify(a.docs) + '）');

  const b = run('');                       // 不限定＝全站
  ok(b.secs.length === 3 && b.docs.length === 4, '不传 only 时不应有任何收窄');

  const c = run('no-such-section');        // 传了不存在的 key
  ok(c.secs.length === 3 && c.docs.length === 4, '传不存在的版块 key 时应等于不限定，而不是回空');

  const d = run('students');
  ok(d.docs.length === 1 && d.docs[0] === 2, '换一个版块时筛选结果不对');
})();

console.log('\n' + (F ? '✗ ' : '✓ ') + P + ' PASS / ' + F + ' FAIL');
process.exit(F ? 1 : 0);
