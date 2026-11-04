/* PDF 禁止下载（2026-11-04，封闭发展期）。所有 Worker 响应都经过这里。
   · 浏览器打开 / iframe 嵌入 .pdf → 302 到 /pdf-view/（站内阅读器，无下载按钮）。
     这样旧页面、外部链接、#page=N 的引证都还能读，只是拿不到浏览器自带的下载栏。
   · 站内阅读器（PDF.js）的同站 fetch → 放行，否则 2000 多个阅读页全部打不开。
   · 其余一律 403：<a download>、右键另存、跨站盗链、curl 之类没有 Sec-Fetch 头又不是站内来路的。
   · 所有 HTML 注入 /assets/pdf-lock.js，把下载入口灰掉（含 JS 后生成的）。
   边界：阅读器要把文件读进浏览器才能显示，本层挡的是"下载入口"，不是字节本身；
   这些文件若仍在公开 GitHub 仓库里，从那里还是拿得到。
   恢复下载：把 PDF_LOCK_ON 改成 false，或在 Cloudflare 设环境变量 PDF_LOCK=off。 */
import { GATE_INTERNAL_KEY } from "./site-gate.js";

export const PDF_LOCK_ON = true;
const LOCK_JS = "/assets/pdf-lock.js?v=1";
const VIEW_DESTS = new Set(["document", "iframe", "frame", "embed", "object"]);
const H_NOSTORE = { "cache-control": "no-store", "x-robots-tag": "noindex, nofollow" };

function isPdfPath(pathname) {
  let p = pathname;
  try { p = decodeURIComponent(pathname); } catch (e) {}
  return /\.pdf\/*$/i.test(p);
}

function fromOwnHost(request, url) {
  const v = request.headers.get("referer") || request.headers.get("origin");
  if (!v) return false;
  try {
    const h = new URL(v).hostname.toLowerCase();
    return h === url.hostname.toLowerCase() || /(^|\.)sdeuniverses\.com$/.test(h);
  } catch (e) { return false; }
}

function toViewer(url) {
  const path = url.pathname.replace(/\/+$/, "") + url.search;
  return new Response(null, {
    status: 302,
    headers: { location: "/pdf-view/?f=" + encodeURIComponent(path), ...H_NOSTORE },
  });
}

function refuse() {
  return new Response("PDF 下载已关闭。", {
    status: 403,
    headers: { "content-type": "text/plain; charset=utf-8", ...H_NOSTORE },
  });
}

// 返回 null＝放行；否则返回要回给浏览器的响应。
export function pdfDecision(request, url) {
  if (request.headers.get("x-sde-internal") === GATE_INTERNAL_KEY) return null;
  const mode = request.headers.get("sec-fetch-mode");
  const dest = request.headers.get("sec-fetch-dest") || "";
  const site = request.headers.get("sec-fetch-site") || "";
  if (mode) {
    if (mode === "navigate") return VIEW_DESTS.has(dest) ? toViewer(url) : refuse();
    if (dest === "empty" && (site === "same-origin" || site === "same-site")) return null;
    return refuse();
  }
  // 老版 iOS 等不发 Sec-Fetch-* 的浏览器：按 Accept 和来路判断。
  const accept = request.headers.get("accept") || "";
  if (accept.includes("text/html")) return toViewer(url);
  return fromOwnHost(request, url) ? null : refuse();
}

class HeadInject {
  element(el) {
    el.prepend('<script src="' + LOCK_JS + '"></script>', { html: true });
  }
}

export async function withPdfLock(request, env, handle) {
  const off = !PDF_LOCK_ON || (env && String(env.PDF_LOCK || "").toLowerCase() === "off");
  if (off) return handle();
  const readable = request.method === "GET" || request.method === "HEAD";
  const url = new URL(request.url);
  if (readable && isPdfPath(url.pathname)) {
    const d = pdfDecision(request, url);
    if (d) return d;
  }
  const res = await handle();
  if (!readable || res.webSocket) return res;
  const ct = (res.headers.get("content-type") || "").toLowerCase();
  // 路径不带 .pdf 却回了 PDF 的（如社区附件 /api/im/doc），同样处理。
  if (ct.includes("application/pdf") && !isPdfPath(url.pathname)) {
    const d = pdfDecision(request, url);
    if (d) { try { if (res.body) await res.body.cancel(); } catch (e) {} return d; }
    return res;
  }
  if (request.method === "GET" && res.status === 200 && ct.startsWith("text/html")) {
    return new HTMLRewriter().on("head", new HeadInject()).transform(res);
  }
  return res;
}
