#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""往 src/worker.js 插入 /api/nbr/judge（近邻库二级细判）。

幂等：已插入则原样退出。锚点取自当前文件，不凭记忆。
"""
import os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
P = os.path.join(ROOT, "src/worker.js")
s = open(P, encoding="utf-8").read()

if "/api/nbr/judge" in s:
    print("已插入过，跳过")
    sys.exit(0)

# ── 常量：插在 MEMO_MS 那一族后面 ────────────────────────────
CONST_ANCHOR = 'const MEMO_MS = 45000;'
assert s.count(CONST_ANCHOR) == 1, "常量锚点不唯一"
CONSTS = CONST_ANCHOR + '''
// 近邻库二级细判（/api/nbr/judge）单独一个桶：它是**闸门**不是正菜，一个候选可能连判几次；
// 走对话桶会让人"过了闸就没额度写文章"。
const NBR_PER_DAY = 400, NBR_PER_MIN = 30;
// 细判也是结构化短输出——满功率会把预算烧在推演上、正文 0 字（十二/十三修同一族的病）。
// 所以：降档 VC（不带 top）＋ 短截止 ＋ 按"它本来该写多长"给预算。
const NBR_MS = 45000;
const NBR_TOK = 2200;
// 一次最多送几张卡去细判。粗筛 R@12=32/35，12 张已经够；再多只是烧钱。
const NBR_MAX_CARDS = 12;'''
s = s.replace(CONST_ANCHOR, CONSTS, 1)

# ── 端点：插在 /api/wds/rag 之前 ────────────────────────────
ROUTE_ANCHOR = '''    // RAG_SUBREQUEST — /api/wds/rag：把「全站检索」从答题请求里拆出来，单独跑一次。'''
assert s.count(ROUTE_ANCHOR) == 1, "路由锚点不唯一"

ENDPOINT = r'''    // NBR_JUDGE — /api/nbr/judge：近邻库的**二级细判**。
    //
    // 一级是 /assets/sde-nbr.js 的词面粗筛（零调用），它只负责把可能的正主送进 top-12。
    // 为什么必须有二级：拿当天产线上 35 条真候选实测，**有 3 条与它的正主一个词都不共享**
    // （「成功之死」对「自我损耗」词面为零）。词面永远够不着这一类，只能让基底来判。
    //
    // 四条纪律（前两条是吃过亏才写下的，后两条是这个闸门自己的命门）：
    // ① **不装内功**。理由同 mode=iq：装了内功的基底对 SDE 语言会过敏性加分，
    //    而这一步要判的恰恰是"这个说法是不是别人早就说过"——加分等于放水。
    // ② **降档 + 短截止**（结构化短输出，见 MEMO_MS 那一族的注释）。
    // ③ **闸门必须两边都能开**。既要能判"占死"，也要能判"活下来"——
    //    只会杀的闸门会复制五步操作法「三条件检验永不返回健康」那个坑；
    //    只会放的闸门就是橡皮图章，比没有更坏。所以 rel 三档写死，且 pass 由服务端按规则算，不由基底自称。
    // ④ **通过条件不是「没有近邻」，而是「带着一条可裁决的分离线活下来」**。
    //    凡判为 near 的，必须给出 sep；给不出 sep 的 near 一律降为 own（占死）。
    if (url.pathname === "/api/nbr/judge") {
      if (request.method === "OPTIONS") return new Response(null, { headers: _cors() });
      if (request.method !== "POST") return new Response("Method Not Allowed", { status: 405 });
      let b = {}; try { b = await request.json(); } catch (e) {}
      const J = (o, st) => Response.json(o, { status: st || 200, headers: _cors() });
      const KEY = String(b.key || "").trim();
      if (KEY.length < 8) return J({ ok: false, code: "need_key", msg: "细判用你自己的 API Key 运行（在 ⚙ 里填入，只存你的浏览器本地）。粗筛不用 Key。" }, 400);
      const q = String(b.q || "").trim().slice(0, 400);
      if (!q) return J({ ok: false, msg: "把候选压成一句 50 字级的承重命题再送来。" }, 400);
      const ids = (Array.isArray(b.ids) ? b.ids : []).slice(0, NBR_MAX_CARDS).map((x) => String(x));

      const vd = wdsVendorOf(b.vendor);
      const VC = { url: WDS_VENDORS[vd].url, model: WDS_VENDORS[vd].model, name: WDS_VENDORS[vd].name };   // 降档：纪律②
      const ip = request.headers.get("cf-connecting-ip") || "unknown";
      try {
        const lim = env.ASK_LIMITER.get(env.ASK_LIMITER.idFromName(wdsBucket("nbr", ip, KEY)));
        const lr = await (await lim.fetch(new Request("https://limiter.internal/?w=" + NBR_PER_MIN + "&d=" + NBR_PER_DAY))).json();
        if (!lr.ok) return J({ ok: false, code: "rate", msg: lr.reason === "day" ? ("这把 Key 今天已细判 " + (lr.inDay || 0) + "/" + NBR_PER_DAY + " 次，明天再续（闸门额度与对话额度分开计）。") : "判得太快了，过十几秒再来。" }, 429);
      } catch (e) {}

      // 卡面**以服务端的库为准**，客户端只递 id——否则谁都能塞一张自己编的卡进来骗过闸门。
      let DB = null;
      try {
        const r = await env.ASSETS.fetch(new Request(new URL("/nbr/cards.json", url)));
        if (r.ok) DB = await r.json();
      } catch (e) {}
      if (!DB || !Array.isArray(DB.cards)) return J({ ok: false, msg: "近邻库读不到，稍后再试。" }, 502);
      const byId = Object.create(null);
      for (const c of DB.cards) byId[c.id] = c;
      const picked = ids.map((i) => byId[i]).filter(Boolean);
      if (!picked.length) return J({ ok: false, msg: "没有可细判的卡——先跑一次粗筛，或直接按〔库未命中〕处理（不得据以放行）。" }, 400);

      const cardTxt = picked.map((c, i) =>
        "［" + (i + 1) + "］" + c.id + "　圈层：" + c.ring
        + "\n承重命题：" + c.prop
        + "\n出处：" + (c.src && c.src.author || "") + "《" + (c.src && (c.src.zh || c.src.title) || "") + "》" + (c.src && c.src.year || "")
        + "\n它占住什么：" + c.holds
        + "\n已知分离线：" + (Array.isArray(c.sep) ? c.sep.join("；") : "")
      ).join("\n\n");

      const sys = "你是一道**闸门**。有人提出了一个新命题，下面是若干可能早就占住了这块地的既有理论。"
        + "你要逐一判定：这个新命题是不是只是它的换词重述。\n\n"
        + "对每一张卡给出三档之一：\n"
        + "· own ＝ **占死**。把新命题压成一句话之后，可以用这张卡的承重命题 1:1 替换而不损失任何判断力。换了个词而已。\n"
        + "· near ＝ **近邻**。同一片地，但新命题确实多出了一点东西。**此时你必须写出那条分离线，而且它必须是可裁决的**——"
        + "形如「在 X 这种情形下，这张卡预测 A，新命题预测非 A，A 怎么读数」。写不出这样一条，就判 own，不要判 near。\n"
        + "· far ＝ **无关**。两者根本不在同一片地。\n\n"
        + "另外，请补出**库里没有、但同样占着这块地**的占位者（尤其是外文原题的、与新命题同向的那些）。"
        + "同向的比可以被推开的更要紧——一个只列举得出可被推开的对手的近邻表，是在自我保护。\n\n"
        + "只输出 JSON，不要任何其他文字：\n"
        + '{"v":[{"id":"卡号","rel":"own|near|far","why":"判据，不超过 60 字","sep":"rel=near 时必填的可裁决分离线，其余留空"}],'
        + '"miss":[{"who":"作者","title":"外文原题","why":"它凭什么也占着这块地，不超过 40 字"}],'
        + '"line":"一句话说清这块地的占用状况，不超过 50 字"}\n\n'
        + "纪律：不许恭维，不许为了让新命题活下来而放宽；也不许为了显得严格而把明显不同的东西判成占死。"
        + "你没读过的东西不要编——拿不准就不写进 miss。";
      const usr = "【新命题】\n" + q + "\n\n【可能的占位者】\n" + cardTxt;

      try {
        const _stat = {};
        const out = await llmText(VC, KEY, sys, usr, NBR_TOK, NBR_MS, _stat);
        if (_stat.status === 401 || _stat.status === 402 || _stat.status === 429)
          return J({ ok: false, code: "bad_key", msg: "你的 Key 用不了（" + _stat.status + "）：额度不足或填错了。" }, 400);
        const j = looseJSON(out);
        if (!j) return J({ ok: false, msg: "这一次没判出来（基底没给出可用结果），可以再点一次。" }, 502);

        const okIds = Object.create(null);
        for (const c of picked) okIds[c.id] = 1;
        const seen = Object.create(null);
        const v = (Array.isArray(j.v) ? j.v : []).filter((x) => x && okIds[String(x.id)] && !seen[String(x.id)] && (seen[String(x.id)] = 1))
          .map((x) => {
            let rel = String(x.rel || "").toLowerCase();
            if (rel !== "own" && rel !== "near" && rel !== "far") rel = "far";
            const sep = String(x.sep || "").trim().slice(0, 400);
            // 纪律④：near 而给不出分离线的，一律降为 own。闸门的通过条件是「带着一条分离线活下来」，
            // 不是「说一句它们不一样」。这一降级由服务端做，不能指望基底自觉。
            if (rel === "near" && sep.length < 12) rel = "own";
            return { id: String(x.id), rel: rel, why: String(x.why || "").slice(0, 200), sep: rel === "near" ? sep : "" };
          });
        // 没被基底提到的卡，按 far 补齐——免得前端把"漏判"显示成"无关"。
        for (const c of picked) if (!seen[c.id]) v.push({ id: c.id, rel: "unjudged", why: "基底没有给出这一张的判定", sep: "" });

        const owned = v.filter((x) => x.rel === "own");
        const near = v.filter((x) => x.rel === "near");
        // 纪律③：pass 由规则算，不由基底自称。
        // 占死一张即不通过；一张都没占死才算过闸，且过闸的形态是「带着 near 的分离线活下来」。
        const pass = owned.length === 0;
        const miss = (Array.isArray(j.miss) ? j.miss : []).slice(0, 6).map((m) => ({
          who: String(m && m.who || "").slice(0, 60),
          title: String(m && m.title || "").slice(0, 160),
          why: String(m && m.why || "").slice(0, 160)
        })).filter((m) => m.who || m.title);

        return J({
          ok: true, pass: pass, n: picked.length,
          owned: owned.length, near: near.length,
          v: v, miss: miss,
          line: String(j.line || "").slice(0, 200),
          verdict: pass
            ? ("过闸：没有一张把它占死；带着 " + near.length + " 条分离线活下来。"
               + (miss.length ? "但基底另点了 " + miss.length + " 位库里没有的占位者，先把它们请进来再说。" : "")
               + "注意：过闸只说明**这一批**没占死它，不等于没被占——库未命中与库外的空间都不在这一判之内。")
            : ("不过闸：有 " + owned.length + " 张把它占死了。要么换承重命题，要么对每一张补出可裁决的分离线再判一次。")
        });
      } catch (e) {
        return J({ ok: false, msg: "细判时出错：" + (e && e.message) }, 502);
      }
    }
'''

s = s.replace(ROUTE_ANCHOR, ENDPOINT + ROUTE_ANCHOR, 1)
open(P, "w", encoding="utf-8").write(s)
print("已插入 /api/nbr/judge，worker.js 现", len(s.splitlines()), "行")
