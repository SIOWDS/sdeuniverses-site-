/* SDE 站内索引缓存层 v1 · 2026-08-18
 *
 * 解决的问题：搜索类页面此前每次打开都要重下全部分片
 * （57 片 × 6.29MB = 359MB 原始 / zstd 后约 132MB），因为前端写死了
 * `?v=Date.now()` + {cache:'no-store'}，任何缓存都命不中。
 *
 * 做法：不按时间猜新鲜度，按 manifest.built 对账。
 *   · 分片 URL 带 `?b=<built>`——索引没重建则 URL 一字不变，命中缓存；
 *     索引一重建，57 个 URL 同时换新，**不可能吃到旧索引**。
 *   · worker 对带 `?b=` 的请求回 immutable（见 src/worker.js 的 /search/ 段）。
 *   · 再压一层 Cache Storage（桶名 sde-idx-<built>），防止上百 MB 被
 *     浏览器的 HTTP 缓存整体驱逐；开局顺手删掉旧 built 的桶。
 *
 * 用法：
 *   var V = SDEIdx.ver(manifest);
 *   SDEIdx.shard(fileName, V).then(function(d){ ... });
 *   manifest 本身用 SDEIdx.manifest() 取（走 ETag revalidate，未变则 304）。
 */
(function () {
  var PFX = 'sde-idx-';
  var swept = {};

  function ver(m) { return encodeURIComponent(String((m && m.built) || '0')); }

  function shardURL(fn, v) { return '/search/shard-' + fn + '.json?b=' + v; }

  /* manifest 是唯一的真相源，必须每次核对；但用 no-cache 而非 no-store：
     浏览器带 If-None-Match，没变时 worker 回 304，717KB 不必重下。 */
  function manifest() {
    return fetch('/search/manifest.json', { cache: 'no-cache' })
      .then(function (r) { return r.json(); })
      .catch(function () {
        return fetch('/search/manifest.json?v=' + Date.now(), { cache: 'no-store' })
          .then(function (r) { return r.json(); });
      });
  }

  function sweep(v) {
    if (swept[v]) return;
    swept[v] = 1;
    if (!window.caches || !caches.keys) return;
    try {
      caches.keys().then(function (ks) {
        ks.forEach(function (k) {
          if (k.indexOf(PFX) === 0 && k !== PFX + v) { try { caches.delete(k); } catch (e) {} }
        });
      }).catch(function () {});
    } catch (e) {}
  }

  function plain(u) { return fetch(u).then(function (r) { return r.json(); }); }

  function shard(fn, v) {
    var u = shardURL(fn, v);
    sweep(v);
    if (!window.caches || !caches.open) return plain(u);
    return caches.open(PFX + v).then(function (c) {
      return c.match(u).then(function (hit) {
        if (hit) return hit.json();
        return fetch(u).then(function (r) {
          /* put 可能因配额被拒——异步 reject，try/catch 接不住，必须 .catch */
          if (r && r.ok) { try { c.put(u, r.clone()).catch(function () {}); } catch (e) {} }
          return r.json();
        });
      });
    }).catch(function () { return plain(u); });
  }

  window.SDEIdx = { ver: ver, shardURL: shardURL, shard: shard, manifest: manifest };
})();
