// SDE Universes site worker: visit counter + static assets
export class VisitCounter {
  constructor(ctx, env) {
    this.ctx = ctx;
  }
  async fetch(request) {
    let total = (await this.ctx.storage.get("total")) || 0;
    if (request.method === "POST") {
      total += 1;
      await this.ctx.storage.put("total", total);
    }
    return new Response(JSON.stringify({ total }), {
      headers: {
        "content-type": "application/json",
        "cache-control": "no-store",
      },
    });
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    // /fresh：永不缓存的首页镜像，用于验证最新版本
    if (url.pathname === "/fresh") {
      const home = await env.ASSETS.fetch(new Request(new URL("/", url), request));
      const r = new Response(home.body, home);
      r.headers.set("cache-control", "no-store");
      r.headers.set("cdn-cache-control", "no-store");
      return r;
    }
    if (url.pathname === "/api/visits") {
      const id = env.COUNTER.idFromName("site-total");
      return env.COUNTER.get(id).fetch(request);
    }
    // /api/llm-proxy：境外基底(GPT/Claude/Gemini)纯转发代理。
    // 解决两件事：①浏览器 CORS 拦截 ②中国大陆无法直连境外 API。
    // 纪律：只转发、不存储、不记录任何 Key；只放行白名单里的官方 LLM 域名。
    if (url.pathname === "/api/llm-proxy") {
      // 预检
      if (request.method === "OPTIONS") {
        return new Response(null, {
          headers: {
            "access-control-allow-origin": "*",
            "access-control-allow-methods": "POST, OPTIONS",
            "access-control-allow-headers": "content-type, authorization, x-target-url",
            "access-control-max-age": "86400",
          },
        });
      }
      if (request.method !== "POST") {
        return new Response("Method Not Allowed", { status: 405 });
      }
      const target = request.headers.get("x-target-url") || "";
      // 白名单：只允许转发到这几家官方 LLM 端点，防止被当开放代理滥用
      const ALLOW = [
        "https://api.openai.com/",
        "https://api.anthropic.com/",
        "https://generativelanguage.googleapis.com/",
      ];
      const ok = ALLOW.some((p) => target.startsWith(p));
      if (!ok) {
        return new Response(
          JSON.stringify({ error: { message: "target url not allowed", type: "proxy_forbidden" } }),
          { status: 403, headers: { "content-type": "application/json", "access-control-allow-origin": "*" } }
        );
      }
      // 组装转发请求：原样带上 Authorization / Content-Type / anthropic 专用头，其余头一律不带
      const fwdHeaders = new Headers();
      const auth = request.headers.get("authorization");
      if (auth) fwdHeaders.set("authorization", auth);
      const ct = request.headers.get("content-type");
      if (ct) fwdHeaders.set("content-type", ct);
      // Anthropic 需要 x-api-key + anthropic-version；Gemini 用 URL 里的 key。这里透传常见必需头。
      const apiKey = request.headers.get("x-api-key");
      if (apiKey) fwdHeaders.set("x-api-key", apiKey);
      const av = request.headers.get("anthropic-version");
      if (av) fwdHeaders.set("anthropic-version", av);
      const adb = request.headers.get("anthropic-dangerous-direct-browser-access");
      if (adb) fwdHeaders.set("anthropic-dangerous-direct-browser-access", adb);

      let upstream;
      try {
        upstream = await fetch(target, {
          method: "POST",
          headers: fwdHeaders,
          body: request.body,
        });
      } catch (e) {
        return new Response(
          JSON.stringify({ error: { message: "upstream fetch failed: " + (e && e.message), type: "proxy_upstream_error" } }),
          { status: 502, headers: { "content-type": "application/json", "access-control-allow-origin": "*" } }
        );
      }
      // 原样回传响应体(含流式)，补上 CORS 头让浏览器可读
      const respHeaders = new Headers(upstream.headers);
      respHeaders.set("access-control-allow-origin", "*");
      respHeaders.delete("content-encoding"); // 避免二次压缩导致前端解码错乱
      return new Response(upstream.body, {
        status: upstream.status,
        statusText: upstream.statusText,
        headers: respHeaders,
      });
    }
    // Everything else: serve static assets (with configured html/404 handling)
    const resp = await env.ASSETS.fetch(request);
    const ct = resp.headers.get("content-type") || "";
    if (ct.includes("text/html")) {
      const r = new Response(resp.body, resp);
      r.headers.set("cache-control", "no-cache, must-revalidate");
      r.headers.set("cdn-cache-control", "no-store");
      return r;
    }
    return resp;
  },
};
