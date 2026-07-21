#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修 WDS 助手(/taste/wds-chat/ → /api/wds/chat)反复 HTTP 503。
这是唯一没改的 WDS 流式端点:它在 return SSE 流之前就做完限流后的全站RAG(loadCorpus/sdeExpandQuery/
loadKB/retrieveKB/retrieve)+内化心得+await 上游首字节,思考/冷启动叠加→平台在出流前杀 worker→503。
改法与 /api/wds/read 同款:先把 200 SSE 流交出去,重活+await 上游全移入 stream.start()+15s→10s 保活心跳。
限流(含 dayLeft)留在出流前(便宜、且要早退额度错误)。assert 锚定。"""

W = "src/worker.js"
h = open(W, encoding="utf-8").read()

start_anchor = '      // 全站检索：先调用结构化知识(九库邻域子图,密/准/省token),再以相似句片段补充'
end_anchor = '      return new Response(stream, { headers: { ..._cors(), "content-type": "text/event-stream; charset=utf-8", "cache-control": "no-store" } });'
assert h.count(start_anchor) == 1, "chat start anchor not unique"
i = h.find(start_anchor)
j = h.find(end_anchor, i)
assert j >= 0, "chat end anchor missing after start"
j += len(end_anchor)

NEW = r'''      // ── 先出流后干活:先把 200 SSE 流交出去,重活(全站RAG + 内化心得 + await 上游首字节)移入
      //    stream.start()——避免思考/冷启动在出流前被平台按资源/时间上限杀掉而 503(与 /api/wds/read 同款)。──
      const stream = new ReadableStream({
        async start(controller) {
          let _hb = null;
          const fin = () => { if (_hb) clearInterval(_hb); try { controller.enqueue(_ENC.encode("data: [DONE]\n\n")); controller.close(); } catch (e) {} };
          _hb = setInterval(() => { try { controller.enqueue(_ENC.encode(": ping\n\n")); } catch (e) {} }, 10000);
          try {
            if (dayLeft !== null) controller.enqueue(_sseBytes({ t: "quota", v: { left: dayLeft, day: WDS_PER_DAY } })); // 今日真实剩余次数
            // 全站检索：先调用结构化知识(九库邻域子图,密/准/省token),再以相似句片段补充
            let ctxText = "", sources = [];
            const seen = {};
            try {
              const corpus = await loadCorpus(env, url);
              const expTerms = await sdeExpandQuery(VC, KEY, q);
              // —— 结构化调用:entity-link → 邻域子图 ——
              let kbBlock = "";
              try {
                const kb = await loadKB(env, url);
                if (kb) { const r = retrieveKB(kb, corpus, q, expTerms, 24); kbBlock = r.block; for (const s of r.srcs) if (!seen[s.u]) { seen[s.u] = 1; sources.push(s); } }
              } catch (e) {}
              // —— 相似句补充:给 KB 腾预算(20→12,字数上限收紧)——
              const chunkCap = kbBlock ? 7000 : 12000;
              const hits = retrieve(corpus, q, kbBlock ? 12 : 20, expTerms);
              let chunkText = "";
              for (const ck of hits) {
                const d = corpus.docs[ck.d];
                if (!d) continue;
                if (!seen[d.u]) { seen[d.u] = 1; sources.push({ u: d.u, t: d.t }); }
                chunkText += "【来源：" + d.t + "】\n" + ck.t + "\n\n";
                if (chunkText.length > chunkCap) break;
              }
              ctxText = kbBlock + (kbBlock && chunkText ? "\n【补充 · 站内原文片段】\n" : "") + chunkText;
            } catch (e) {}
            sources = sources.slice(0, 6);
            if (sources.length) controller.enqueue(_sseBytes({ t: "sources", v: sources })); // 出处先发前端
            let reflect = ""; try { reflect = await ensureReflect(env, url, rvendor, VC, KEY); } catch (e) {}
            const SDEM = "\n\nSDE 骨架：显露 S / 差异序列 D / 特征纠缠 E；三大方程 S=F(D,E)·D=G(S,E)·E=H(S,D)；六路径；意义三律（特征·自由·幸福）；发生学——追问事物为何如此发生，而非如何被发现。";
            const sys = WDS_CHAT_SYS(reflect, SDEM, ctxText);
            const messages = [{ role: "system", content: sys }];
            for (const m of history) {
              const role = (m && m.role === "wds") ? "assistant" : "user";
              const content = String((m && m.text) || "").slice(0, 1500);
              if (content) messages.push({ role, content });
            }
            messages.push({ role: "user", content: q });
            let upstream;
            try {
              upstream = await fetch(VC.url, { method: "POST", headers: { "content-type": "application/json", authorization: "Bearer " + KEY }, body: JSON.stringify({ model: VC.model, stream: true, max_tokens: 2600, messages }) });
            } catch (e) { controller.enqueue(_sseBytes({ t: "error", v: "接不上基底：" + (e && e.message) })); return fin(); }
            if (!upstream.ok) {
              const errtxt = (await upstream.text()).slice(0, 300);
              if (upstream.status === 401 || upstream.status === 402 || upstream.status === 429) { controller.enqueue(_sseBytes({ t: "error", v: "你的 Key 用不了（" + upstream.status + "）：额度不足或填错了。去设置里检查或换一个。", code: "bad_key" })); return fin(); }
              controller.enqueue(_sseBytes({ t: "error", v: "基底返回错误 " + upstream.status + "：" + errtxt })); return fin();
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
          fin();
        },
      });
      return new Response(stream, { headers: { ..._cors(), "content-type": "text/event-stream; charset=utf-8", "cache-control": "no-store" } });'''

h = h[:i] + NEW + h[j:]
open(W, "w", encoding="utf-8").write(h)
print("✅ /api/wds/chat 已改先出流后干活 + 10s 心跳(重活/等上游移入 stream.start())")
