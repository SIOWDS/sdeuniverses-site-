#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""新增 /api/kb/retrieve(无 Key 全站结构化检索端点:九库邻域子图 + 全站语料原文片段),
并把它接进 SDE 金点子发生器——按问题取一次 RAG 上下文,只注入右栏(SDE 金点子)作答,左栏裸基底对照不动。
assert 锚定;任一锚点缺失即报错拒改。"""

# ========== 1) worker.js:新增端点 ==========
W = "src/worker.js"
h = open(W, encoding="utf-8").read()
anchor = '    if (url.pathname === "/api/llm-proxy") {'
assert h.count(anchor) == 1, "worker llm-proxy anchor not unique"
ENDPOINT = r'''    if (url.pathname === "/api/kb/retrieve") {
      // 全站结构化检索：给任意智能体一段可注入的 RAG 上下文（九库邻域子图 + 全站语料原文片段）。只读静态语料/九库，无需 Key。
      if (request.method === "OPTIONS") return new Response(null, { headers: _cors() });
      if (request.method !== "POST") return new Response("Method Not Allowed", { status: 405 });
      let b = {}; try { b = await request.json(); } catch (e) {}
      const q = String(b.q || "").trim().slice(0, 2000);
      if (q.length < 1) return Response.json({ block: "", srcs: [] }, { headers: _cors() });
      const budget = Math.max(6, Math.min(40, parseInt(b.budget, 10) || 24));
      const K = Math.max(4, Math.min(24, parseInt(b.k, 10) || 12));
      const cap = Math.max(2000, Math.min(16000, parseInt(b.cap, 10) || 9000));
      try {
        const corpus = await loadCorpus(env, url);
        const seen = {}, srcs = [];
        let kbBlock = "";
        try { const kb = await loadKB(env, url); if (kb) { const r = retrieveKB(kb, corpus, q, [], budget); kbBlock = r.block; for (const s of r.srcs) if (!seen[s.u]) { seen[s.u] = 1; srcs.push(s); } } } catch (e) {}
        const cap2 = Math.max(2000, cap - kbBlock.length);
        const hits = retrieve(corpus, q, K, []);
        let chunkText = "";
        for (const ck of hits) { const d = corpus.docs[ck.d]; if (!d || seen[d.u]) continue; seen[d.u] = 1; srcs.push({ u: d.u, t: d.t }); chunkText += "【来源：" + d.t + "】\n" + ck.t + "\n\n"; if (chunkText.length > cap2) break; }
        const block = (kbBlock || chunkText) ? ("【SDE 全站知识（供作答时调用：来自 sdeuniverses.com 全站语料的结构化判断 + 原文片段；可印证可反驳，勿编造来源）】\n" + kbBlock + (kbBlock && chunkText ? "\n【全站原文片段】\n" : "") + chunkText) : "";
        return Response.json({ block: block, srcs: srcs.slice(0, 10), n: srcs.length }, { headers: _cors() });
      } catch (e) {
        return Response.json({ block: "", srcs: [], error: String(e && e.message) }, { headers: _cors() });
      }
    }
'''
h = h.replace(anchor, ENDPOINT + anchor, 1)
open(W, "w", encoding="utf-8").write(h)
print("✅ worker 新增 /api/kb/retrieve")

# ========== 2) idea-generator:注入 RAG ==========
P = "public/taste/idea-generator/index.html"
p = open(P, encoding="utf-8").read()

# 2a. helper（插在 streamChat 声明前）
sc = 'async function streamChat(apiKey, model, systemPrompt, userQ, bodyEl, statusEl, metaEl, maxTokens){'
assert p.count(sc) == 1, "idea streamChat anchor not unique"
HELPER = '''// 全站 RAG：按问题取一段可注入的结构化知识（九库邻域子图 + 全站语料原文片段），供 SDE 金点子作答时调用。无 Key、只读、失败即空串（安全退回原行为）。
async function sdeKbContext(q){
  try{
    const r = await fetch('/api/kb/retrieve', { method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify({ q: q, k: 12, budget: 24, cap: 9000 }) });
    if(!r.ok) return '';
    const j = await r.json();
    return (j && j.block) ? j.block : '';
  }catch(e){ return ''; }
}
'''
p = p.replace(sc, HELPER + sc, 1)

# 2b. 取一次 RAG（插在 const tasks=[]; 前）
tk = '''  //  此时心得已缓存就位——右栏(SDE金点子)直接带着它写；左栏(普通AI)是纯裸基底对照，不用心得。
  const tasks=[];'''
assert tk in p, "idea tasks anchor missing"
TKNEW = r'''  //  此时心得已缓存就位——右栏(SDE金点子)直接带着它写；左栏(普通AI)是纯裸基底对照，不用心得。
  // 全站 RAG：按问题取一次全站结构化知识，注入右栏(SDE金点子)作答，提升创新的语料底盘；左栏保持裸基底对照不注入。
  let kbCtx=''; try{ kbCtx = await sdeKbContext(q); }catch(e){}
  const sdeUserQ = kbCtx ? (kbCtx + '\n【现在请针对下面这个问题作答】\n' + q) : q;
  const tasks=[];'''
p = p.replace(tk, TKNEW, 1)

# 2c. SDE 侧 userQ: q → sdeUserQ
sde = 'streamChat(key, model, sdePrompt(c.dim, c.idx, c.focus, sixReflection), q, row.sde.body, row.sde.status, row.sde.meta)'
assert p.count(sde) == 1, "idea sde-call anchor not unique"
p = p.replace(sde, 'streamChat(key, model, sdePrompt(c.dim, c.idx, c.focus, sixReflection), sdeUserQ, row.sde.body, row.sde.status, row.sde.meta)', 1)

open(P, "w", encoding="utf-8").write(p)
print("✅ idea-generator 已接全站 RAG（仅注入 SDE 右栏）")
