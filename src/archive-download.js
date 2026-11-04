/* 临时打包下载（tools/books_archive.py 生成）。
   网址 /__a/<64位十六进制>.zip，桶里的键是 archive/<该值的 SHA-256>.zip：
   仓库和工作流只见得到哈希，见不到网址。排在密码门之后，门外进不来。 */
async function sha256hex(s) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

export async function archiveDownload(request, env, url) {
  const m = /^\/__a\/([0-9a-f]{64})\.zip$/.exec(url.pathname);
  if (!m) return null;
  if (request.method !== "GET" && request.method !== "HEAD") return new Response("method not allowed", { status: 405 });
  if (!env || !env.PDFS) return new Response("not found", { status: 404 });
  const key = "archive/" + (await sha256hex(m[1])) + ".zip";
  const hasRange = !!request.headers.get("range");
  const obj = await env.PDFS.get(key, { range: hasRange ? request.headers : undefined, onlyIf: request.headers });
  if (!obj) return new Response("这个下载链接已失效。", { status: 404, headers: { "content-type": "text/plain; charset=utf-8", "cache-control": "no-store" } });
  const h = new Headers();
  h.set("etag", obj.httpEtag);
  h.set("accept-ranges", "bytes");
  h.set("content-type", "application/zip");
  h.set("content-disposition", 'attachment; filename="SDE-monograph-PDF.zip"');
  h.set("cache-control", "private, no-store");
  h.set("x-robots-tag", "noindex, nofollow");
  if (!("body" in obj)) return new Response(null, { status: 304, headers: h });
  if (hasRange && obj.range && obj.range.offset !== undefined) {
    const st = obj.range.offset;
    const ln = obj.range.length === undefined ? obj.size - st : obj.range.length;
    h.set("content-range", "bytes " + st + "-" + (st + ln - 1) + "/" + obj.size);
    h.set("content-length", String(ln));
    return new Response(request.method === "HEAD" ? null : obj.body, { status: 206, headers: h });
  }
  h.set("content-length", String(obj.size));
  return new Response(request.method === "HEAD" ? null : obj.body, { status: 200, headers: h });
}
