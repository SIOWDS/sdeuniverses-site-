#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复『与WDS对话』答题偶发 HTTP 503。
根因:worker 在返回 SSE 流之前就把重活全做完——限流、内化心得、全站 RAG(loadCorpus/sdeExpandQuery/
loadKB/retrieveKB/retrieve)、以及 await 思考满档模型的首字节(可达数十秒)。冷启动叠加时,平台在 worker
尚未交出响应前就按资源/时间上限杀掉它 → 503(出流前,客户端显示"接不上 WDS")。
改法:先把 200 SSE 流交出去,再在流内做 RAG 与等待上游;出流后即便冷启动慢/首字节慢也只会退化成流内
一条温和提示,不再 503。逻辑与产出字符串一字不改(保 e2e 断言),仅把执行位置移进 stream.start()。
assert 锚定;起止锚点缺失即报错拒改。"""

W = "src/worker.js"
h = open(W, encoding="utf-8").read()

start_anchor = '      // 内核底盘（完整内功→内化心得，按基底缓存复用；失败则降级为无底盘）\n      let reflect = String(b.reflect || "").slice(0, 14000);   // 与WDS对话：本场开工亲写的心得（客户端随每条消息带上）'
end_anchor = '      return new Response(stream, { headers: { ..._cors(), "content-type": "text/event-stream; charset=utf-8", "cache-control": "no-store" } });'

i = h.find(start_anchor)
assert i >= 0, "read start anchor missing"
j = h.find(end_anchor, i)
assert j >= 0, "read end anchor missing"
j += len(end_anchor)
# 唯一性:该起止对在 /api/wds/read 内只应出现一次(chat 用不同变量名)
assert h.count(start_anchor) == 1, "read start anchor not unique"

NEW = r'''      // ── 出流前只做“廉价且必须早退”的事:上面已完成 method/参数/Key/限流校验。──
      // 重活(内化心得、全站 RAG、以及 await 思考满档模型首字节)一律移入 stream.start():
      // 先把 200 SSE 流交出去,再在流内干活——冷启动慢/首字节慢只会退化成流内一条温和提示,
      // 不会在“出流前”被平台按资源/时间上限杀掉而返回 503(此前 503 的根因)。
      const stream = new ReadableStream({
        async start(controller) {
          const done = () => { try { controller.enqueue(_ENC.encode("data: [DONE]\n\n")); controller.close(); } catch (e) {} };
          try {
            // 内核底盘（完整内功→内化心得，按基底缓存复用；失败则降级为无底盘）
            let reflect = String(b.reflect || "").slice(0, 14000);   // 与WDS对话：本场开工亲写的心得（客户端随每条消息带上）
            if (!reflect) { try { reflect = await ensureReflect(env, url.origin + "/", rvendor, VC, KEY); } catch (e) {} }
            const SDEM = "\n\nSDE 骨架：显露 S / 差异序列 D / 特征纠缠 E；三大方程 S=F(D,E)·D=G(S,E)·E=H(S,D)；六路径；意义三律（特征·自由·幸福）；发生学——追问事物为何如此发生，而非如何被发现。";
            // 与WDS对话（guide）：全站 RAG 加强档——K=36 广召回 + 上一轮接续检索，上下文上限 3 万字符，来源随流回传
            let siteCtx = "", siteSrcs = [];
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
                  chunkText += "【来源：" + d.t + "】\n" + ck.t + "\n\n";
                  if (chunkText.length > chunkCap) break;
                }
                siteCtx = kbBlock + (kbBlock && chunkText ? "\n【补充 · 站内原文片段】\n" : "") + chunkText;
                siteSrcs = siteSrcs.slice(0, 10);
              } catch (e) {}
            }
            if (siteSrcs.length) controller.enqueue(_sseBytes({ t: "sources", v: siteSrcs })); // 先把站内出处发给前端
            const sys = b.guide ? WDS_DIALOGUE_SYS(reflect, SDEM, siteCtx, docTitle, docText) : WDS_READ_SYS(reflect, SDEM, docTitle, docText);
            // 历史预算随正文/站内资料篇幅收缩：合计钳在 ~12万字符内，防超长文+百轮对话挤爆基底上下文
            // 陪读：正文+历史 ~12万字符收缩；与WDS对话（guide）：全面记忆——30万字符预算+单条1.2万，正常百轮全量不裁（RAG 的 siteCtx 已计入物理护栏）
            const histBudget = b.guide ? Math.max(60000, WDS_GUIDE_HIST_BUDGET - docText.length - siteCtx.length) : Math.min(WDS_HIST_BUDGET, Math.max(20000, 120000 - docText.length - siteCtx.length));
            const messages = [{ role: "system", content: sys }];
            if (b.guide && docText) {
              // 读者提交的文章：作为对话最前面的一轮独立消息注入——比塞在 system 末尾（排在3万字站内资料之后）可靠得多
              messages.push({ role: "user", content: "这是我提交给你的文章全文，本场对话就围绕它。\n\n《" + (docTitle || "未命名") + "》\n\n" + docText });
              messages.push({ role: "assistant", content: "《" + (docTitle || "未命名") + "》全文我已通读完毕（" + docText.length + " 字符）。接下来你每问一句，我都扣着这篇文章本身答——引它的原话、拆它的显露与差异序列、指出它的创新与缝隙。你问吧。" });
            }
            messages.push(...packReadHistory(history, histBudget, b.guide ? 12000 : 0));
            messages.push({ role: "user", content: focus ? ("我正读到这一句：「" + focus + "」\n\n我的问题：" + q) : q });
            let upstream;
            try {
              upstream = await fetch(VC.url, { method: "POST", headers: { "content-type": "application/json", authorization: "Bearer " + KEY }, body: JSON.stringify(wdsTopBody(VC, { model: VC.model, stream: true, max_tokens: b.guide ? 8000 : 2200, messages })) });
            } catch (e) {
              controller.enqueue(_sseBytes({ t: "error", v: "接不上基底：" + (e && e.message) })); return done();
            }
            if (!upstream.ok) {
              const errtxt = (await upstream.text()).slice(0, 300);
              if (upstream.status === 401 || upstream.status === 402 || upstream.status === 429) { controller.enqueue(_sseBytes({ t: "error", v: "你的 Key 用不了（" + upstream.status + "）：额度不足或填错了。去设置里检查或换一个。", code: "bad_key" })); return done(); }
              controller.enqueue(_sseBytes({ t: "error", v: "基底返回错误 " + upstream.status + "：" + errtxt })); return done();
            }
            const reader = upstream.body.getReader();
            const dec = new TextDecoder();
            let buf = "";
            while (true) {
              const { done: rdone, value } = await reader.read();
              if (rdone) break;
              buf += dec.decode(value, { stream: true });
              let idx;
              while ((idx = buf.indexOf("\n")) >= 0) {
                const line = buf.slice(0, idx).trim();
                buf = buf.slice(idx + 1);
                if (!line.startsWith("data:")) continue;
                const p = line.slice(5).trim();
                if (p === "[DONE]") continue;
                let j; try { j = JSON.parse(p); } catch (e) { continue; }
                if (j.error) { controller.enqueue(_sseBytes({ t: "error", v: j.error.message || "基底流内错误" })); continue; }
                const d = (j.choices && j.choices[0] && j.choices[0].delta) || {};
                if (d.reasoning_content) controller.enqueue(_sseBytes({ t: "think", v: d.reasoning_content }));
                if (d.content) controller.enqueue(_sseBytes({ t: "token", v: d.content }));
              }
            }
          } catch (e) {
            controller.enqueue(_sseBytes({ t: "error", v: "生成出错：" + (e && e.message) + "（可再问一次）" }));
          }
          done();
        },
      });
      return new Response(stream, { headers: { ..._cors(), "content-type": "text/event-stream; charset=utf-8", "cache-control": "no-store" } });'''

h = h[:i] + NEW + h[j:]
open(W, "w", encoding="utf-8").write(h)
print("✅ /api/wds/read 已改为『先出流后干活』(stream-first),消除出流前 503 窗口")
