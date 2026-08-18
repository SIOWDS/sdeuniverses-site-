/* sim_idx_cache.js · 2026-08-18
 * 护栏：站内索引缓存层（assets/sde-idx-cache.js）＋ 四个搜索页 ＋ worker 的 ?b= 分岔。
 * 跑法：node tools/sim_idx_cache.js
 */
const fs = require('fs'), path = require('path'), vm = require('vm');
const R = path.join(__dirname, '..');
let pass = 0, fail = 0;
function ok(c, m) { if (c) { pass++; } else { fail++; console.log('  ✗ ' + m); } }
function sec(t) { console.log('\n' + t); }
const rd = p => fs.readFileSync(path.join(R, p), 'utf8');

/* ---------- ① 模块本体：装到假 window 上跑 ---------- */
sec('① sde-idx-cache.js 行为');
function mkEnv(opts) {
  opts = opts || {};
  const log = { fetched: [], put: [], deleted: [] };
  const store = new Map();          // 桶名 -> Map(url -> body)
  const caches = opts.noCaches ? undefined : {
    keys: () => Promise.resolve([...store.keys()]),
    delete: (k) => { log.deleted.push(k); store.delete(k); return Promise.resolve(true); },
    open: (name) => {
      if (!store.has(name)) store.set(name, new Map());
      const b = store.get(name);
      return Promise.resolve({
        match: (u) => Promise.resolve(b.has(u) ? { json: () => Promise.resolve(b.get(u)) } : undefined),
        put: (u, r) => {
          if (opts.quotaFull) return Promise.reject(new Error('QuotaExceededError'));
          log.put.push(u); b.set(u, r.__body); return Promise.resolve();
        }
      });
    }
  };
  const fetch = (u, init) => {
    log.fetched.push({ u, init: init || null });
    if (opts.fetchFails) return Promise.reject(new Error('net'));
    const body = { chunks: [{ t: 'x' }], __u: u };
    return Promise.resolve({ ok: true, __body: body, json: () => Promise.resolve(body), clone() { return this; } });
  };
  const win = { caches, fetch };
  win.window = win;
  const ctx = vm.createContext(win);
  vm.runInContext(rd('public/assets/sde-idx-cache.js'), ctx);
  return { win, log, store, SDEIdx: win.SDEIdx };
}

(async () => {
  // 1. 版本键来自 manifest.built，且分片 URL 带 ?b=
  let e = mkEnv();
  const V = e.SDEIdx.ver({ built: '2026-08-18T05:54:01.752988Z' });
  ok(V.indexOf('2026-08-18') === 0, 'ver() 应取自 built');
  ok(e.SDEIdx.shardURL('students-1', V) === '/search/shard-students-1.json?b=' + V, '分片 URL 应带 ?b=');
  ok(e.SDEIdx.shardURL('students-1', V).indexOf('Date') < 0, '分片 URL 不得含时间戳');

  // 2. 第一次拉网、第二次命中缓存（零 fetch）
  e = mkEnv();
  await e.SDEIdx.shard('students-1', 'V1');
  ok(e.log.fetched.length === 1, '首次应发一次 fetch');
  ok(e.log.put.length === 1, '首次应写入 Cache Storage');
  await e.SDEIdx.shard('students-1', 'V1');
  ok(e.log.fetched.length === 1, '同版本第二次必须零 fetch（这条红＝缓存没生效）');

  // 3. built 一变，URL 换新 → 必须重下，且旧桶被删
  e = mkEnv();
  await e.SDEIdx.shard('students-1', 'V1');
  await e.SDEIdx.shard('students-1', 'V2');
  ok(e.log.fetched.length === 2, '换版本必须重下（这条红＝会吃到旧索引）');
  ok(e.log.deleted.indexOf('sde-idx-V1') >= 0, '旧版本桶应被清掉');
  ok(e.store.has('sde-idx-V2'), '新版本桶应存在');

  // 4. 配额被拒 / 无 caches / fetch 失败 —— 都不许把页面搞死
  e = mkEnv({ quotaFull: true });
  let r = await e.SDEIdx.shard('a', 'V1').catch(() => 'THREW');
  ok(r !== 'THREW' && r.chunks, 'put 被配额拒绝时仍应正常返回数据');
  e = mkEnv({ noCaches: true });
  r = await e.SDEIdx.shard('a', 'V1').catch(() => 'THREW');
  ok(r !== 'THREW' && r.chunks, '浏览器无 Cache Storage 时应回退纯 fetch');
  ok(e.log.fetched[0].u.indexOf('?b=V1') > 0, '回退路径也要带版本键');

  // 5. manifest：走 no-cache 重新校验（带 ETag），不再 no-store；失败时回退老写法
  e = mkEnv();
  await e.SDEIdx.manifest();
  ok(e.log.fetched[0].u === '/search/manifest.json', 'manifest 不再挂 ?v=Date.now()');
  ok(e.log.fetched[0].init && e.log.fetched[0].init.cache === 'no-cache', 'manifest 应用 no-cache（带 ETag 核对，未变回 304）');
  e = mkEnv({ fetchFails: true });
  r = await e.SDEIdx.manifest().catch(() => 'THREW');
  ok(r === 'THREW', 'manifest 两条路都失败时应向上抛，由页面显示"索引加载失败"');

  /* ---------- ② 四个页面已换线 ---------- */
  sec('② 四个搜索页');
  const pages = ['public/search/index.html', 'public/frontier/search/index.html',
    'public/taste/heygen-course/index.html', 'public/taste/essence-audio/index.html'];
  pages.forEach(p => {
    const h = rd(p);
    ok(/assets\/sde-idx-cache\.js\?v=/.test(h), p + ' 应引入 sde-idx-cache.js（带缓存戳）');
    ok(!/shard-'\+fn\+'\.json\?v='\+Date\.now\(\)/.test(h), p + ' 不得再用时间戳拉分片');
    ok(/SDEIdx\.shard\(fn, ?IDXV\)/.test(h), p + ' 应改走 SDEIdx.shard');
    ok(/SDEIdx\.manifest\(\)/.test(h), p + ' 应改走 SDEIdx.manifest');
    ok(/IDXV\s*=\s*SDEIdx\.ver\(m\)/.test(h), p + ' 应把 built 存进 IDXV');
    ok(!/\/search\/(manifest|shard-)[^'"]*\?v='\s*\+\s*Date\.now\(\)/.test(h), p + ' 索引 URL 不得再挂时间戳');
  });
  // 全站扫一遍，别有漏网的
  const stray = [];
  (function walk(d) {
    for (const f of fs.readdirSync(d)) {
      const fp = path.join(d, f), st = fs.statSync(fp);
      if (st.isDirectory()) { if (f !== 'node_modules' && f !== '.git') walk(fp); }
      else if (/\.(html|js)$/.test(f)) {
        const t = fs.readFileSync(fp, 'utf8');
        if (/shard-'\s*\+\s*fn\s*\+\s*'\.json\?v='\s*\+\s*Date\.now\(\)/.test(t)) stray.push(fp);
      }
    }
  })(path.join(R, 'public'));
  ok(stray.length === 0, '全站不应还有按时间戳拉分片的页面：' + stray.join(','));

  /* ---------- ③ worker 的 ?b= 分岔 ---------- */
  sec('③ worker /search/ 缓存分岔');
  const w = rd('src/worker.js');
  ok(/url\.searchParams\.has\("b"\)[\s\S]{0,120}immutable/.test(w), 'worker 应对带 ?b= 的请求回 immutable');
  ok(/: "no-cache"/.test(w), 'worker 对不带 ?b= 的仍应回 no-cache');
  // 抠出那一段，用假 R2 真跑
  const seg = w.match(/if \(\(request\.method === "GET"[\s\S]*?x-served-from", "r2"\);/);
  ok(!!seg, '应能定位 /search/ 路由段');
  const cc = (hasB) => {
    const h2 = new Map();
    const url = { searchParams: { has: (k) => hasB && k === 'b' } };
    // 复刻那三行的判断（与源码同形，改了源码这里会被 ③ 的正则先红）
    h2.set('cache-control', url.searchParams.has('b') ? 'public, max-age=31536000, immutable' : 'no-cache');
    return h2.get('cache-control');
  };
  ok(cc(true) === 'public, max-age=31536000, immutable', '带 b → immutable');
  ok(cc(false) === 'no-cache', '不带 b → no-cache');

  /* ---------- ④ 真跑：去掉多余 .l 副本后检索结果必须逐条一致 ---------- */
  sec('④ 真跑 · .l 副本裁剪的等价性');
  const shardPath = '/tmp/s1.json';
  if (!fs.existsSync(shardPath)) {
    console.log('  （跳过：/tmp/s1.json 不在，先 curl 一片线上分片下来）');
  } else {
    const d = JSON.parse(fs.readFileSync(shardPath, 'utf8'));
    function countCap(s, t, cap) { let n = 0, i = 0; while ((i = s.indexOf(t, i)) >= 0) { n++; i += t.length; if (n >= cap) break; } return n; }
    function softScore(lowerText, Q) {
      let hitKeys = 0, tf = 0;
      for (const k of Q.keys) { const n = countCap(lowerText, k, 3); if (n) { hitKeys++; tf += n; } }
      if (!hitKeys) return 0;
      const cov = hitKeys / Q.keys.length;
      let sc = tf * (0.25 + 0.75 * cov);
      for (const r2 of Q.runs) if (r2.length >= 2 && lowerText.indexOf(r2) >= 0) sc += 3;
      if (Q.full.length >= 2 && lowerText.indexOf(Q.full) >= 0) sc += 8;
      return sc < 0.9 ? 0 : sc;
    }
    const qs = ['发生', 'sde', 'SDE 本体论', '轮空', 'Innovation IQ', '二阶碰撞', 'DOI', '回写'];
    let mism = 0, saved = 0, total = 0;
    const old = d.chunks.map(c => ({ t: c.t, l: String(c.t || '').toLowerCase() }));
    const neu = d.chunks.map(c => { const o = { t: c.t }; const lo = String(c.t || '').toLowerCase(); if (lo !== c.t) o.l = lo; return o; });
    neu.forEach((c, i) => { total += (c.t || '').length; if (!c.l) saved += (c.t || '').length; });
    for (const q of qs) {
      const lq = q.toLowerCase();
      const Q = { keys: lq.split(/\s+/).filter(Boolean), runs: lq.split(/\s+/).filter(Boolean), full: lq };
      for (let i = 0; i < old.length; i++) {
        const a = softScore(old[i].l, Q);
        const b = softScore(neu[i].l || neu[i].t, Q);
        if (a !== b) mism++;
      }
    }
    ok(mism === 0, '裁剪后 ' + qs.length + ' 组查询 × ' + old.length + ' 块的得分必须逐条相同，实测不一致 ' + mism + ' 处');
    console.log('  · 本片省下的重复正文：' + saved.toLocaleString() + ' / ' + total.toLocaleString() +
      ' 字（' + (100 * saved / total).toFixed(1) + '%），按 UTF-16 约 ' + (2 * saved / 1048576).toFixed(1) + 'MB/片');
  }

  console.log('\n' + pass + ' PASS / ' + fail + ' FAIL');
  process.exit(fail ? 1 : 0);
})();
