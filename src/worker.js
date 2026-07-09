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
    if (url.pathname === "/api/visits") {
      const id = env.COUNTER.idFromName("site-total");
      return env.COUNTER.get(id).fetch(request);
    }
    // Everything else: serve static assets (with configured html/404 handling)
    return env.ASSETS.fetch(request);
  },
};
