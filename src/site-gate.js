/* ═══ 全站密码门（2026-11-03 起，封闭发展半年）═══
   王德生令：SDE 平台封闭半年（2026-11-03 → 2027-05-03），在原有登录之外再加一道全站密码。
   一个共用密码，由王德生本人手动发给要进来的人；进门后一切照旧（社区登录、个人站、ChatSDE 都不动）。

   · 只存密码的 SHA-256（加盐 "sde-gate-v1:"），代码里没有明文。
   · 换密码：改 GATE_PW_SHA（或在 Cloudflare 设环境变量 SITE_GATE_SHA 覆盖），旧 cookie 立刻全部作废。
   · 开门（封闭期结束）：把 GATE_ON 改成 false，或设环境变量 SITE_GATE=off。
   · cookie 种在 .sdeuniverses.com，主站与所有二级域名分站、个人站共用一次输入。
   · Worker 自绑定（SELF）发给自己的内部请求带 x-sde-internal，不被门拦。
   · /api/* 只放行来自本站页面的请求（Origin/Referer 是 sdeuniverses.com）或已过门的请求。 */

export const GATE_ON = true;
const GATE_PW_SHA = "1b11aabd82f8db3b2bc5210d7318ed4ccc8b999cffab71bee2d967a1da373bcb";
export const GATE_INTERNAL_KEY = "6c66e73b4629df1c5040389c5edfc0bb";
const COOKIE = "sde_gate";
const MAX_AGE = 200 * 24 * 3600; // 覆盖整个封闭期

async function sha256hex(s) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}
async function tokenFor(pwSha) { return sha256hex("sde-gate-cookie-v1:" + pwSha); }

function readCookie(request, name) {
  const c = request.headers.get("cookie") || "";
  for (const part of c.split(/;\s*/)) {
    const i = part.indexOf("=");
    if (i > 0 && part.slice(0, i) === name) return part.slice(i + 1);
  }
  return "";
}

function cookieDomain(host) {
  return /(^|\.)sdeuniverses\.com$/.test(host) ? "; Domain=.sdeuniverses.com" : "";
}

function fromOwnSite(request) {
  for (const h of ["origin", "referer"]) {
    const v = request.headers.get(h);
    if (!v) continue;
    try { if (/(^|\.)sdeuniverses\.com$/i.test(new URL(v).hostname)) return true; } catch (e) {}
  }
  return false;
}

function safeNext(n) {
  n = String(n || "/");
  return n.startsWith("/") && !n.startsWith("//") ? n : "/";
}

function gatePage(next, wrong) {
  const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  return `<!doctype html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>SDE 平台 · 封闭发展中</title>
<style>
:root{--bg:#0f1b2d;--card:#16263d;--ink:#e9eef5;--mute:#9fb0c4;--gold:#c9a45c;--err:#e07a6b}
*{box-sizing:border-box}html,body{margin:0;height:100%}
body{background:var(--bg);color:var(--ink);font-family:"Noto Serif SC","Source Han Serif SC","Songti SC",serif;display:flex;align-items:center;justify-content:center;padding:16px}
.c{width:100%;max-width:380px;background:var(--card);border:1px solid rgba(201,164,92,.35);border-radius:14px;padding:32px 26px;text-align:center}
h1{font-size:22px;margin:0 0 6px;letter-spacing:2px}h1 b{color:var(--gold)}
p{color:var(--mute);font-size:14px;line-height:1.7;margin:0 0 22px}
input{width:100%;font-size:16px;padding:12px 14px;border-radius:8px;border:1px solid rgba(255,255,255,.18);background:#0c1626;color:var(--ink);outline:none;text-align:center;letter-spacing:1px}
input:focus{border-color:var(--gold)}
button{margin-top:14px;width:100%;font-size:16px;padding:12px;border:0;border-radius:8px;background:var(--gold);color:#1a1408;font-weight:600;cursor:pointer;letter-spacing:4px}
.e{color:var(--err);font-size:13px;margin-top:12px;min-height:1em}
.f{margin-top:22px;font-size:12px;color:#6f8096}
</style></head><body>
<form class="c" method="post" action="/__gate">
<h1><b>SDE</b> 平台</h1>
<p>封闭发展中（2026.11 — 2027.05）<br>请输入访问密码</p>
<input type="hidden" name="next" value="${esc(next)}">
<input type="password" name="pw" autocomplete="current-password" autofocus required placeholder="访问密码">
<button type="submit">进入</button>
<div class="e">${wrong ? "密码不对，请再试一次。" : ""}</div>
<div class="f">德麦国际 · Demai International</div>
</form></body></html>`;
}

const H_NOSTORE = { "cache-control": "no-store", "x-robots-tag": "noindex, nofollow" };

/** 过门返回 null（继续往下走）；没过门返回一个 Response。 */
export async function siteGate(request, env) {
  const off = env && String(env.SITE_GATE || "").toLowerCase() === "off";
  if (!GATE_ON || off) return null;
  const url = new URL(request.url);
  const host = url.hostname.toLowerCase();
  const pwSha = (env && env.SITE_GATE_SHA) ? String(env.SITE_GATE_SHA) : GATE_PW_SHA;

  // 内部自绑定请求
  if (request.headers.get("x-sde-internal") === GATE_INTERNAL_KEY) return null;

  // 搜索引擎：封闭期一律不收录
  if (url.pathname === "/robots.txt") {
    return new Response("User-agent: *\nDisallow: /\n", { headers: { "content-type": "text/plain; charset=utf-8", ...H_NOSTORE } });
  }

  // 提交密码
  if (url.pathname === "/__gate") {
    if (request.method !== "POST") return Response.redirect(new URL("/", url).toString(), 303);
    let pw = "", next = "/";
    try { const f = await request.formData(); pw = String(f.get("pw") || ""); next = safeNext(f.get("next")); } catch (e) {}
    const ok = pw && (await sha256hex("sde-gate-v1:" + pw.trim())) === pwSha;
    if (!ok) {
      return new Response(gatePage(next, true), { status: 401, headers: { "content-type": "text/html; charset=utf-8", ...H_NOSTORE } });
    }
    const tok = await tokenFor(pwSha);
    return new Response(null, {
      status: 303,
      headers: {
        location: next,
        "set-cookie": `${COOKIE}=${tok}; Path=/; Max-Age=${MAX_AGE}; HttpOnly; Secure; SameSite=Lax${cookieDomain(host)}`,
        ...H_NOSTORE,
      },
    });
  }

  // 退出：清掉过门凭证，回到关卡（测试用，也可发给要换设备的人）
  if (url.pathname === "/__logout") {
    const hs = new Headers({ location: "/", ...H_NOSTORE, "clear-site-data": "\"cache\"" });
    hs.append("set-cookie", `${COOKIE}=; Path=/; Max-Age=0; Secure; SameSite=Lax${cookieDomain(host)}`);
    hs.append("set-cookie", `${COOKIE}=; Path=/; Max-Age=0; Secure; SameSite=Lax`);
    return new Response(null, { status: 303, headers: hs });
  }

  // 已过门
  if (readCookie(request, COOKIE) === (await tokenFor(pwSha))) return null;

  // 本站页面里发出的 API 调用（含二级域名分站跨源调用主站）
  if (url.pathname.startsWith("/api/") && fromOwnSite(request)) return null;

  if (request.method === "OPTIONS") return null;

  // 浏览器里关卡上线前缓存下来的旧页面：它再去要脚本时，回一段跳转脚本把整页送回关卡。
  if (request.headers.get("sec-fetch-dest") === "script" && !url.pathname.startsWith("/api/")) {
    return new Response('try{top.location.replace("/")}catch(e){location.replace("/")}', {
      status: 200, headers: { "content-type": "text/javascript; charset=utf-8", ...H_NOSTORE },
    });
  }

  const accept = request.headers.get("accept") || "";
  const isPage = !url.pathname.startsWith("/api/") && (request.method === "GET" || request.method === "HEAD") && (accept.includes("text/html") || accept === "" || accept === "*/*" && !url.pathname.includes("."));
  if (isPage) {
    return new Response(request.method === "HEAD" ? null : gatePage(url.pathname + url.search, false), {
      status: 401, headers: { "content-type": "text/html; charset=utf-8", ...H_NOSTORE, "clear-site-data": "\"cache\"" },
    });
  }
  return new Response(JSON.stringify({ ok: false, msg: "SDE 平台封闭发展中，需要访问密码。" }), {
    status: 401, headers: { "content-type": "application/json; charset=utf-8", ...H_NOSTORE },
  });
}
