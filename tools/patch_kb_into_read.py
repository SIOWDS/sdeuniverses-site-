#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把九库结构化检索接进 /api/wds/read 的 guide 块——首页中部『与WDS对话SDE』真正走的 RAG。
KB 邻域子图在前,K=36 相似句召回保留但收紧字数上限为其让预算;来源合并回传。同步更新 e2e 断言。
assert 锚定,任一锚点缺失即报错拒改。"""
import sys

W = "src/worker.js"
h = open(W, encoding="utf-8").read()

# ---- worker: 用起止锚点框住 guide 检索块,整段替换(避免逐字复述全块)----
start = '      let siteCtx = "", siteSrcs = [];\n      if (b.guide) {'
end   = '          siteSrcs = siteSrcs.slice(0, 10);\n        } catch (e) {}\n      }'
i = h.find(start)
assert i >= 0, "worker start anchor missing"
j = h.find(end, i)
assert j >= 0, "worker end anchor missing"
j += len(end)
assert h.count(start) == 1, "worker start anchor not unique"

NEW = '''      let siteCtx = "", siteSrcs = [];
      if (b.guide) {
        try {
          const corpus = await loadCorpus(env, url);
          let expTerms = []; try { expTerms = await sdeExpandQuery(VC, KEY, q); } catch (e) {}
          const seen = {};
          // —— 先调用结构化知识：九库 entity-link → 邻域子图（成体系的判断，而非相似句）——
          let kbBlock = "";
          try {
            const kb = await loadKB(env, url);
            if (kb) { const r = retrieveKB(kb, corpus, q, expTerms, docText ? 14 : 24); kbBlock = r.block; for (const s of r.srcs) if (!seen[s.u]) { seen[s.u] = 1; siteSrcs.push(s); } }
          } catch (e) {}
          // —— 相似句召回：K=36 广召回 + 上一轮接续；KB 命中时收紧字数上限，为结构化知识让出预算 ——
          const hits = retrieve(corpus, q, 36, expTerms);
          let prevQ = "";
          for (let i = history.length - 1; i >= 0; i--) { const m = history[i]; if (m && m.role !== "wds" && m.text) { prevQ = String(m.text).slice(0, 240); break; } }
          if (prevQ && prevQ !== q) {
            const more = retrieve(corpus, prevQ, 10, []);
            const have = new Set(hits.map((c) => c.d + "|" + c.t.slice(0, 40)));
            for (const ck of more) { const id = ck.d + "|" + ck.t.slice(0, 40); if (!have.has(id)) { have.add(id); hits.push(ck); } }
          }
          const chunkCap = Math.max(6000, (docText ? 12000 : 30000) - kbBlock.length);   // 读者提交文章时站内资料让位；KB 命中时为其留出预算
          let chunkText = "";
          for (const ck of hits) {
            const d = corpus.docs[ck.d]; if (!d) continue;
            if (!seen[d.u]) { seen[d.u] = 1; siteSrcs.push({ u: d.u, t: d.t }); }
            chunkText += "【来源：" + d.t + "】\\n" + ck.t + "\\n\\n";
            if (chunkText.length > chunkCap) break;
          }
          siteCtx = kbBlock + (kbBlock && chunkText ? "\\n【补充 · 站内原文片段】\\n" : "") + chunkText;
          siteSrcs = siteSrcs.slice(0, 10);
        } catch (e) {}
      }'''
h = h[:i] + NEW + h[j:]
open(W, "w", encoding="utf-8").write(h)
print("✅ worker /api/wds/read guide 块已接九库")

# ---- e2e sim: 更新旧断言 + 新增 KB 接线断言 ----
S = "tools/sim_wds_dialogue_e2e.js"
s = open(S, encoding="utf-8").read()
old = '''ok("全站 RAG 加强档（K=36 + 接续补捞 + 3 万上限 + 来源回传）",
  W.includes("retrieve(corpus, q, 36, expTerms)") && W.includes("siteCtx.length > (docText ? 12000 : 30000)") && W.includes('{ t: "sources", v: siteSrcs }'));'''
assert old in s, "sim assertion anchor missing"
new = '''ok("全站 RAG 加强档（K=36 + 接续补捞 + KB留预算的字数上限 + 来源回传）",
  W.includes("retrieve(corpus, q, 36, expTerms)") && W.includes("(docText ? 12000 : 30000) - kbBlock.length") && W.includes('{ t: "sources", v: siteSrcs }'));
ok("与WDS对话 RAG 已接九库（guide 块 retrieveKB 邻域子图优先，chunk 让预算）",
  W.includes("const kb = await loadKB(env, url)") && W.includes("retrieveKB(kb, corpus, q, expTerms, docText ? 14 : 24)") && W.includes("siteCtx = kbBlock +"));'''
s = s.replace(old, new, 1)
open(S, "w", encoding="utf-8").write(s)
print("✅ e2e 断言已同步(旧改新 + 增 KB 接线校验)")
