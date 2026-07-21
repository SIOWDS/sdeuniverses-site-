#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把全站 RAG(/api/kb/retrieve)接进中华智问知识发生器:run 启动时按议题取一次结构化知识,
存 RUN.kbCtx,注入每一轮作答(第1轮裸议题路径 + 第2轮起 buildRoundUserMsg)。内功/评审阶段不注入。
复用金点子那次已上线的 /api/kb/retrieve 端点。assert 锚定;任一锚点缺失即报错拒改。"""

P = "public/taste/zhiwen/index.html"
p = open(P, encoding="utf-8").read()

# 1) helper（插在 streamChat 声明前）
sc = 'async function streamChat(apiKey, model, systemPrompt, userQ, bodyEl, statusEl, metaEl, colEl, maxTokens){'
assert p.count(sc) == 1, "zhiwen streamChat anchor not unique"
HELPER = '''// 全站 RAG：按议题取一段可注入的结构化知识（九库邻域子图 + 全站语料原文片段），供每一轮作答调用。无 Key、只读、失败即空串（安全退回原行为）。
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

# 2) run 启动时取一次 RAG，存 RUN.kbCtx（插在 RUN 对象字面量之后）
runlit = '          xinde:{}, xindeOk:{}, lanes:{}, papers:{}, histories:{}, papersText:{}, collisionSteps:{}, t0:Date.now() };'
assert p.count(runlit) == 1, "zhiwen RUN literal anchor not unique"
p = p.replace(runlit, runlit + "\n  // 全站 RAG：按议题取一次结构化知识作为作答底盘（内功/评审阶段不注入，仅注入每一轮回答）\n  try{ runHint.textContent = '正在检索全站相关知识作为作答底盘…'; RUN.kbCtx = await sdeKbContext(q); }catch(e){ RUN.kbCtx=''; }", 1)

# 3) buildRoundUserMsg：把 RUN.kbCtx 垫在【问题】之前（覆盖第 2 轮起）
parts = "  const parts = ['【问题】\\n' + question + '\\n'];"
assert p.count(parts) == 1, "zhiwen buildRoundUserMsg parts anchor not unique"
p = p.replace(parts, "  const kb = (RUN && RUN.kbCtx) ? (RUN.kbCtx + '\\n') : '';\n  const parts = [kb + '【问题】\\n' + question + '\\n'];", 1)

# 4) 第 1 轮裸议题路径也垫上 RUN.kbCtx
r1 = '    const usr = rnd===1 ? RUN.question : buildRoundUserMsg(RUN.question, history, pendingFb);'
assert p.count(r1) == 1, "zhiwen round1 anchor not unique"
p = p.replace(r1, "    const usr = rnd===1 ? ((RUN.kbCtx ? RUN.kbCtx + '\\n【问题】\\n' : '') + RUN.question) : buildRoundUserMsg(RUN.question, history, pendingFb);", 1)

open(P, "w", encoding="utf-8").write(p)
print("✅ 中华智问已接全站 RAG（第1轮 + 第2轮起 均注入 RUN.kbCtx）")
