#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_chatsde_rag_subrequest.py —— ChatSDE「流刚开就断」的三处改动（幂等）

报障现场（2026-08-16 用户截图）：
  〔诊断〕第 5 秒 · 收到 1 帧 · 思考 0 字 · 最后停在「扩展检索词」 · 流被截断（没收到收尾标记）

三处：
  A. /api/wds/rag 加四个可选字段（加法式白名单：pick / abs / capkb / hits / hitskb），kbn 上限 30→40
  B. /api/wds/chat 的站内检索整段改走 wdsRag 子请求（RAG_SUBREQUEST 收口）
  C. 阶段帧：阶段一变就立刻发一帧，不再等 5 秒心跳
  D. sdeExpandQuery 对关不掉思考的家（Kimi/MiniMax）给够额度
"""
import io, re, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "src/worker.js")
h = io.open(P, encoding="utf-8").read()
orig = h

def rep(old, new, tag):
    global h
    if new in h:
        print("  · 已在（跳过）：" + tag)
        return
    assert h.count(old) == 1, "锚点不唯一/找不到：" + tag + " count=" + str(h.count(old))
    h = h.replace(old, new)
    print("  ✓ " + tag)

# ── D. 扩展检索词的额度：关不掉思考的家要给够 ────────────────────────────
rep(
"""const SDE_EXPAND_MS = 6000;
async function sdeExpandQuery(VC, KEY, q, ms) {
  const LC = (VC && VC.top) ? { url: VC.url, model: VC.model, name: VC.name } : VC;
  const out = await llmText(LC, KEY, SDE_LEXICON, "用户问题：" + q + "\\n\\n请只输出 SDE 检索术语（顿号分隔）：", 300, ms || SDE_EXPAND_MS);""",
"""const SDE_EXPAND_MS = 6000;
// 【关不掉思考的家要另给额度 —— 2026-08-16】Kimi／MiniMax 思考常开、无开关（见 wdsPlainBody），
// 300 的额度会被 reasoning 整份吃掉、content 回空串；llmText 的空正文重试翻三倍也才 900，
// 两趟都空，六秒截止到点空手而归。⇒ 对这两家而言，「扩展检索词」这一步是**必然白烧六秒**：
// 用户那张截图第 5 秒还停在这一步，正是这个。给它们一个够落二十个术语的额度（仍 ≤2000，
// llmText 的"短额度关思考"判据不变）；关得掉思考的家一个字不动——300 足够，且省时省钱。
function sdeExpandTok(VC) {
  const u = String((VC && VC.url) || "");
  return (u.indexOf("moonshot") >= 0 || u.indexOf("minimax") >= 0) ? 1500 : 300;
}
async function sdeExpandQuery(VC, KEY, q, ms) {
  const LC = (VC && VC.top) ? { url: VC.url, model: VC.model, name: VC.name } : VC;
  const out = await llmText(LC, KEY, SDE_LEXICON, "用户问题：" + q + "\\n\\n请只输出 SDE 检索术语（顿号分隔）：", sdeExpandTok(VC), ms || SDE_EXPAND_MS);""",
"D 扩展词额度按家分档")

# ── A. /api/wds/rag 白名单加四项 ──────────────────────────────────────
rep(
"""      const kbn = Math.max(0, Math.min(30, parseInt(b.kbn, 10) || 0));
      const prevQ = String(b.prevQ || "").slice(0, 240);
      const chunkLimit = Math.max(200, Math.min(4000, parseInt(b.chunk, 10) || 0));""",
"""      const kbn = Math.max(0, Math.min(40, parseInt(b.kbn, 10) || 0));
      const prevQ = String(b.prevQ || "").slice(0, 240);
      const chunkLimit = Math.max(200, Math.min(4000, parseInt(b.chunk, 10) || 0));
      /* 【加法式白名单 · 2026-08-16】ChatSDE 的站内检索搬进这条子请求时，要保住它原来那几个口径，
         于是多这五个可选字段：pick 候选篇数、abs 源头行带绝对网址、capkb 有 KB 块时的片段预算、
         hits/hitskb 片段条数上限。**一个都不传＝与从前逐字一样**（既有三个调用点行为不变）。
         💡 心法（本文件已写过一次、这里再钉一遍）：改了传输契约，第一件事是去看接收端的白名单
         ——2026-08-12 rs.bodies 那次就是前端递了、白名单没加，线上整个空转还全绿。 */
      const pick = Math.max(0, Math.min(64, parseInt(b.pick, 10) || 0));
      const abs = b.abs === 1 || b.abs === true;
      const capKb = Math.max(0, Math.min(30000, parseInt(b.capkb, 10) || 0));
      const hitMax = Math.max(0, Math.min(64, parseInt(b.hits, 10) || 0));
      const hitMaxKb = Math.max(0, Math.min(64, parseInt(b.hitskb, 10) || 0));""",
"A rag 白名单五字段 + kbn 上限 40")

rep(
"""        const scan = await ragScan(env, url, q, expTerms, prevQ, K, chunkLimit || 1600);""",
"""        const scan = await ragScan(env, url, q, expTerms, prevQ, K, chunkLimit || 1600, pick ? { pick: pick } : undefined);""",
"A pick 递进 ragScan")

rep(
"""        const chunkCap = Math.max(4000, cap - kbBlock.length);
        let chunkText = "";
        for (const ck of scan.picked) {
          const d = scan.docs[ck.d]; if (!d) continue;
          if (!seen[d.u]) { seen[d.u] = 1; srcs.push({ u: d.u, t: d.t }); }
          chunkText += "【来源：" + d.t + "】\\n" + ck.t + "\\n\\n";
          if (chunkText.length > chunkCap) break;
        }""",
"""        // capkb 传了就按"有没有 KB 块"分两档（ChatSDE 的老口径）；没传＝旧算法一字不变。
        const chunkCap = capKb ? (kbBlock ? capKb : cap) : Math.max(4000, cap - kbBlock.length);
        const hitCap = kbBlock ? (hitMaxKb || hitMax) : hitMax;   // 0 ＝ 不限条数（旧行为）
        let chunkText = "", nHit = 0;
        for (const ck of scan.picked) {
          if (hitCap && nHit >= hitCap) break;
          const d = scan.docs[ck.d]; if (!d) continue;
          if (!seen[d.u]) { seen[d.u] = 1; srcs.push({ u: d.u, t: d.t }); }
          // 网址跟着篇名一起进上下文：它看不见网址，就会当站里没有链接
          // （2026-07-30 实测：读者要链接，它答"站内文章没有链接"——纯属没见过网址的幻觉）。
          chunkText += "【来源：" + d.t + (abs ? ("｜" + new URL(d.u, url).toString()) : "") + "】\\n" + ck.t + "\\n\\n";
          nHit++;
          if (chunkText.length > chunkCap) break;
        }""",
"A 片段段：capkb / hits / abs")

# ── C. 阶段帧 ────────────────────────────────────────────────────────
rep(
"""          const _st = { t0: Date.now(), think: 0, out: 0 };   // 必须 const/let 声明：ESM 是严格模式，裸赋值当场抛 ReferenceError
          _hb = wdsBeat(controller, _st);
          try {
            if (dayLeft !== null) controller.enqueue(_sseBytes({ t: "quota", v: { left: dayLeft, day: WDS_PER_DAY } })); // 今日真实剩余次数""",
"""          const _st = { t0: Date.now(), think: 0, out: 0, stage: "准备" };   // 必须 const/let 声明：ESM 是严格模式，裸赋值当场抛 ReferenceError
          _hb = wdsBeat(controller, _st);
          /* STAGE_FRAME（2026-08-16）：阶段一变就**立刻**发一帧，不等下一次心跳。
             心跳是 5 秒一拍，于是诊断行报的"最后停在哪一步"最多要差 5 秒——用户那张截图写着
             停在「扩展检索词」，而那一步自带 6 秒截止、其后还有整段站内检索，光看截图分不出
             到底死在哪一步。阶段帧一加，死在哪一步就是逐字确定的（前端 lastBeat 照旧取用，不必改）。 */
          const _stg = (s) => {
            _st.stage = s;
            try { controller.enqueue(_sseBytes({ t: "beat", v: { sec: Math.round((Date.now() - _st.t0) / 1000), think: _st.think || 0, out: _st.out || 0, stage: s } })); } catch (e) {}
          };
          try {
            if (dayLeft !== null) controller.enqueue(_sseBytes({ t: "quota", v: { left: dayLeft, day: WDS_PER_DAY } })); // 今日真实剩余次数""",
"C 阶段帧 _stg")

# ── B. chat 的站内检索改走子请求 ──────────────────────────────────────
rep(
"""            let ctxText = "", sources = [];
            const seen = {};
""",
"""            let ctxText = "", sources = [];   // 站内资料与出处：现在整段由 /api/wds/rag 子请求交回来
""",
"B 去掉不再用的 seen")

rep(
"""            if (!noSite) try {
              _st.stage = "扩展检索词";
              const expTerms = await sdeExpandQuery(VC, KEY, q);
              _st.stage = "站内检索";
              const wide = deep || tool === "collide";   // 碰撞要在更宽的面上挑，才可能凑出互相矛盾的三篇
              const _lrC = await lightRetrieve(env, url, q, expTerms, wide ? 30 : 20, 1600, { pick: wide ? 28 : 18 });
              const corpus = _lrC.corpus;
              // —— 结构化调用:entity-link → 邻域子图 ——
              let kbBlock = "";
              try {
                const kb = await loadKB(env, url);
                if (kb) { const r = retrieveKB(kb, corpus, q, expTerms, deep ? 36 : 24); kbBlock = r.block; for (const s of r.srcs) if (!seen[s.u]) { seen[s.u] = 1; sources.push(s); } }
              } catch (e) {}
              // —— 相似句补充:给 KB 腾预算(20→12,字数上限收紧)；深度档整体放宽 ——
              const chunkCap = deep ? (kbBlock ? 12000 : 18000) : (kbBlock ? 7000 : 12000);
              const hits = _lrC.hits.slice(0, deep ? (kbBlock ? 20 : 28) : (kbBlock ? 12 : 20));
              let chunkText = "";
              for (const ck of hits) {
                const d = corpus.docs[ck.d];
                if (!d) continue;
                if (!seen[d.u]) { seen[d.u] = 1; sources.push({ u: d.u, t: d.t }); }
                // 网址必须跟着篇名一起进上下文：它看不见网址，就会当站里没有链接
                // （2026-07-30 实测：读者要链接，它答"站内文章没有链接"——纯属没见过网址的幻觉）
                chunkText += "【来源：" + d.t + "｜" + new URL(d.u, url).toString() + "】\\n" + ck.t + "\\n\\n";
                if (chunkText.length > chunkCap) break;
              }
              ctxText = kbBlock + (kbBlock && chunkText ? "\\n【补充 · 站内原文片段】\\n" : "") + chunkText;
            } catch (e) {}""",
"""            if (!noSite) try {
              _stg("扩展检索词");
              const expTerms = await sdeExpandQuery(VC, KEY, q);
              _stg("站内检索");
              const wide = deep || tool === "collide";   // 碰撞要在更宽的面上挑，才可能凑出互相矛盾的三篇
              /* 🔴🔴 RAG_SUBREQUEST 收口（2026-08-16）——**本次报障的病灶就在这里**。
                 这一段原来是在**本请求之内**装语料（lightRetrieve ＋ loadKB）：冷启动时它要把
                 上百个索引分片解成对象，CPU 与内存全记在这一次请求头上，而这次请求后面还得驮着
                 一篇几千字的答。顶到平台单请求上限时，请求被**无声掐死**——没有 error、没有 [DONE]、
                 连 sources 都没发出来，读者只收到一两个心跳。这正是 /api/wds/rag 那条注释
                 （"拆出来单独跑一次…它有自己的一份 CPU 预算"）当初要治的病：
                 /api/wds/read 与成文那一路早就改走子请求了，**ChatSDE 是最后一条漏网的**。
                 用户 2026-08-16 那张截图（第5秒·收到1帧·思考0字·停在「扩展检索词」·流被截断）
                 就是这个死法：一帧＝那一次心跳，零 sources ＝ 死在检索段里。
                 ⚠ 口径逐条搬过去了（k/pick/kbn/两档 chunkCap/两档条数/绝对网址），不是趁机改配方。 */
              let _ragWhy = "";
              const _ragBody = {
                q: q, exp: expTerms,
                k: wide ? 30 : 20, pick: wide ? 28 : 18, kbn: deep ? 36 : 24,
                cap: deep ? 18000 : 12000, capkb: deep ? 12000 : 7000,
                hits: deep ? 28 : 20, hitskb: deep ? 20 : 12,
                abs: 1,
              };
              // 子请求偶发 5xx（被平台拒收）是常态而非我方逻辑错——它很便宜，直接再打一次。
              for (let _try = 0; _try < 2; _try++) {
                try {
                  const rr = await wdsRag(env, url, _ragBody);
                  if (rr.ok) {
                    const jr = await rr.json();
                    if (jr && jr.ok) { ctxText = jr.ctx || ""; sources = jr.srcs || []; _ragWhy = ""; break; }
                    _ragWhy = (jr && jr.msg) || "返回不可用";
                    break;
                  }
                  _ragWhy = "HTTP " + rr.status;
                  if (rr.status < 500) break;
                } catch (e) { _ragWhy = "子请求异常：" + ((e && e.message) || ""); }
              }
              // 失败必须可见：静默降级＝把"这一答其实没查过站内"记成查过了。
              if (!sources.length) controller.enqueue(_sseBytes({ t: "note", v: "站内检索这一问没接上（" + (_ragWhy || "无命中") + "），这一答只据内功与你给的材料——问的若是站内文章，重问一次多半就有了。" }));
            } catch (e) {}""",
"B 站内检索改走 wdsRag 子请求")

rep("""            _st.pre = Math.round((Date.now() - _st.t0) / 1000);
            _st.stage = "基底作答";""",
"""            _st.pre = Math.round((Date.now() - _st.t0) / 1000);
            _stg("基底作答");""", "C 基底作答用阶段帧")

rep("""              _st.stage = "关思考重答";""",
"""              _stg("关思考重答");""", "C 关思考重答用阶段帧")

if h == orig:
    print("没有任何改动（全部已在）")
else:
    io.open(P, "w", encoding="utf-8").write(h)
    print("已写入 " + P)
