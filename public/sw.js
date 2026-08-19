/* 爱思乐园 Service Worker —— 装到手机桌面（PWA）的那一半。
 *
 * 设计口径只有一条，别越界：**这台 SW 不缓存任何正文**。
 * 全站的纪律是「普通刷新即最新」——worker.js 给 HTML 下的是
 * no-store 且剥掉 ETag/Last-Modified，搜索索引与 wds-mode.js / sde-read.css
 * 也各自钉了 no-cache。SW 若插一层自己的缓存，等于把那条纪律从背后废掉：
 * 站上改了内容，装了 App 的人继续看旧的，而且他连"强刷"这个动作都没有。
 * 所以：
 *   · 导航请求（点开任一页）→ 直接走网络；只有网络真的断了，才回一张离线页。
 *   · 其余请求（图片/脚本/接口/PDF）→ 一律不接管，交回浏览器自己走。
 *   · 只预存离线页与图标这几个字节，别的什么都不存。
 * 这样既满足浏览器"可安装"的门槛（要有 fetch 处理器、断网时导航有回应），
 * 又不会让任何一个读者拿到过期正文。
 *
 * 换版本：改 V 即可（旧缓存在 activate 里清）。
 */
var V = "sde-shell-v1";
var SHELL = ["/offline.html", "/assets/app/icon-192.png"];

self.addEventListener("install", function (e) {
  e.waitUntil(
    caches.open(V).then(function (c) { return c.addAll(SHELL); })
      .catch(function () {})            // 预存失败不许拖垮安装
      .then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener("activate", function (e) {
  e.waitUntil(
    caches.keys().then(function (ks) {
      return Promise.all(ks.map(function (k) { return k === V ? null : caches.delete(k); }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener("fetch", function (e) {
  var req = e.request;
  if (req.method !== "GET") return;
  var url;
  try { url = new URL(req.url); } catch (err) { return; }
  if (url.origin !== self.location.origin) return;      // 外站不接管
  if (url.pathname.indexOf("/api/") === 0) return;      // 接口一律直通（含 SSE 流）

  // 只接管"整页导航"，而且只为了断网时有话可说。
  if (req.mode === "navigate") {
    e.respondWith(
      fetch(req).catch(function () {
        return caches.match("/offline.html").then(function (r) {
          return r || new Response("离线", { status: 503, headers: { "content-type": "text/plain; charset=utf-8" } });
        });
      })
    );
  }
  // 其余：不调用 respondWith ＝ 浏览器照原样走，缓存策略完全由响应头决定。
});

// 页面可以让新版 SW 立刻接管（/app/ 页上的"检查更新"用）
self.addEventListener("message", function (e) {
  if (e.data === "skip-waiting") self.skipWaiting();
});
