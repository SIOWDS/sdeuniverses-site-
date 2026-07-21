#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复『凝成一万字论文』运行一段时间后 HTTP 503。
根因同答题:read-paper 的 part 模式是非流式——worker 在 return JSON 前要做 loadCorpus/retrieveKB/retrieve
+ await 思考满档模型写完整部分(每部分约1700-1900字,可耗时很久);冷启动/慢首字节叠加时平台在 worker 交出
响应前按资源/时间上限杀掉它 → 出流前 503(六部分逐段,常在中途某部分挂)。
改法:part 模式改 SSE 流式——先把 200 流交出去,RAG 与 await 上游全移入 stream.start(),逐字转发;客户端
part 调用改为读 SSE 累积(顺带逐字实时显示);出流后慢只退化成流内温和提示,不再 503。plan/summary 维持
非流式(单次有界+客户端已重试)。三处(worker/客户端/e2e mock)同步改,保持一致。
assert 锚定;锚点缺失即报错拒改。"""

# ═══════════ 1) worker.js: part 模式 → SSE 流式 ═══════════
W = "src/worker.js"
h = open(W, encoding="utf-8").read()
w_start = '      if (b.mode === "part") {'
w_end = '        const text = await llmText(VC, KEY, sys, usr, 3600);\n        return text ? J({ ok: true, text }) : J({ ok: false, msg: "本部分生成失败，请重试。" }, 502);\n      }'
# 末尾锚点唯一(llmText 3600 + 本部分生成失败),据此定位;起手 if 有两处(另一处是别的处理器),回溯取末尾前最近的那个
assert h.count(w_end) == 1, "worker part end anchor not unique"
j0 = h.find(w_end)
i = h.rfind(w_start, 0, j0)
assert i >= 0, "worker part start anchor missing before end"
j = j0 + len(w_end)

W_NEW = r'''      if (b.mode === "part") {
        const title = String(b.title || "").slice(0, 200);
        const parts = Array.isArray(b.parts) ? b.parts : [];
        const idx = parseInt(b.idx, 10) || 0;
        if (!parts[idx]) return J({ ok: false, msg: "bad idx" }, 400);
        const points = (Array.isArray(b.points) ? b.points : []).slice(0, 8);
        const prevBrief = String(b.prevBrief || "").slice(0, 1400);
        const convoBrief = String(b.convo || convo).slice(0, 6000);
        // 分部写作走 SSE 流：先把 200 流交出去，再在流内做 RAG 与 await 上游写完——避免非流式在返回前被平台按
        // 资源/时间上限杀掉而 503（此前“一万字论文运行一段时间后 503”的根因）。出流后慢只退化成流内温和提示。
        const stream = new ReadableStream({
          async start(controller) {
            const fin = () => { try { controller.enqueue(_ENC.encode("data: [DONE]\n\n")); controller.close(); } catch (e) {} };
            try {
              let partCtx = "";
              if (GD) {
                try {
                  const corpus = await loadCorpus(env, url);
                  const pq = (title + " " + (parts[idx].h || "") + " " + points.join(" ")).slice(0, 300);
                  const pseen = {};
                  // —— 结构化知识：九库邻域子图（按本部分主旨定位），让成文引到成体系的判断而非仅相似句 ——
                  let kbBlock = "";
                  try { const kb = await loadKB(env, url); if (kb) { const r = retrieveKB(kb, corpus, pq, [], 18); kbBlock = r.block; } } catch (e) {}
                  // —— 相似句补充：K=12；KB 命中时收紧上限为其让预算 ——
                  const pcap = Math.max(3000, 8000 - kbBlock.length);
                  const phits = retrieve(corpus, pq, 12, []);
                  let chunkText = "";
                  for (const ck of phits) { const d = corpus.docs[ck.d]; if (!d || pseen[d.u]) continue; pseen[d.u] = 1; chunkText += "【来源：" + d.t + "】\n" + ck.t.slice(0, 900) + "\n\n"; if (chunkText.length > pcap) break; }
                  partCtx = kbBlock + (kbBlock && chunkText ? "\n【补充 · 站内原文片段】\n" : "") + chunkText;
                } catch (e) {}
              }
              const sys = "你是 SDE 学派的学者，正在写一篇严谨的学术论文。" + (GD ? "本文属《问对WDS》系列——由一场与 WDS 的百轮问答凝成、关于 SDE 思想的论文。" : "") + BASE
                + "\n用严谨学术汉语写作：论证扎实、有可被反驳的明确判断、不注水、不摆空模板；可用 SDE 概念但必须讲透、服务论证。用自然段和简短小标题分层，不要用 #、* 等 markdown 符号，不要写参考文献。";
              const usr = "论文标题：" + title + "\n金点子：" + points.join("；") + "\n"
                + (partCtx ? ("【站内资料·全站检索到的相关段落（可据以印证或对话，引用时标（来源：篇名），没有的别编）】\n" + partCtx + "\n") : "")
                + "【对话依据】" + convoBrief + "\n"
                + (prevBrief ? ("【前文已写·摘要】" + prevBrief + "\n") : "")
                + "\n现在写【" + parts[idx].h + "】这一部分（主旨：" + (parts[idx].gist || "") + "），约 1700-1900 字。直接从正文写起，不要开场白，不要复述论文标题，不要与前文重复。";
              let upstream;
              try {
                upstream = await fetch(VC.url, { method: "POST", headers: { "content-type": "application/json", authorization: "Bearer " + KEY }, body: JSON.stringify(wdsTopBody(VC, { model: VC.model, stream: true, max_tokens: 3600, messages: [{ role: "system", content: sys }, { role: "user", content: usr }] })) });
              } catch (e) { controller.enqueue(_sseBytes({ t: "error", v: "接不上基底：" + (e && e.message) })); return fin(); }
              if (!upstream.ok) {
                const errtxt = (await upstream.text()).slice(0, 200);
                if (upstream.status === 401 || upstream.status === 402 || upstream.status === 429) { controller.enqueue(_sseBytes({ t: "error", v: "你的 Key 用不了（" + upstream.status + "）：额度不足或填错了。", code: "bad_key" })); return fin(); }
                controller.enqueue(_sseBytes({ t: "error", v: "基底返回错误 " + upstream.status + "：" + errtxt })); return fin();
              }
              const reader = upstream.body.getReader();
              const dec = new TextDecoder();
              let buf = "";
              while (true) {
                const { done: rdone, value } = await reader.read();
                if (rdone) break;
                buf += dec.decode(value, { stream: true });
                let li;
                while ((li = buf.indexOf("\n")) >= 0) {
                  const line = buf.slice(0, li).trim();
                  buf = buf.slice(li + 1);
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
              controller.enqueue(_sseBytes({ t: "error", v: "本部分生成出错：" + (e && e.message) + "（可重试）" }));
            }
            fin();
          },
        });
        return new Response(stream, { headers: { ..._cors(), "content-type": "text/event-stream; charset=utf-8", "cache-control": "no-store" } });
      }'''
h = h[:i] + W_NEW + h[j:]
open(W, "w", encoding="utf-8").write(h)
print("✅ worker: read-paper part 模式已改 SSE 流式")

# ═══════════ 2) 客户端 wds-dialogue: 加 postStream + part 循环改流式 ═══════════
P = "public/taste/wds-dialogue/index.html"
p = open(P, encoding="utf-8").read()

# 2a. 插入 postStream（在 docModal 之前）
dm_anchor = '  function docModal(title, kind) {'
assert p.count(dm_anchor) == 1, "client docModal anchor not unique"
POSTSTREAM = r'''  // 分部写作走流式（SSE）：先建立连接再逐字收——避免“出流前”被平台上限杀掉而 503；出流前的偶发 5xx 仍退避重试。
  function postStream(body, onToken) {
    body.guide = 1; body.paperN = PN; body.docTitle = article.text ? article.title : TITLE; body.docText = article.text || ""; body.history = history; body.reflect = xinde;
    var delays = [1500, 4000];
    function attempt(n) {
      return fetch(PAPER, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) }).then(function (r) {
        if (!r.ok || !r.body) {
          if (n < delays.length) return new Promise(function (res) { setTimeout(res, delays[n]); }).then(function () { return attempt(n + 1); });
          throw new Error("HTTP " + r.status);
        }
        var reader = r.body.getReader(), dec = new TextDecoder(), buf = "", text = "", errMsg = "";
        function pump() {
          return reader.read().then(function (res) {
            if (res.done) { if (errMsg && !text) throw new Error(errMsg); return text; }
            buf += dec.decode(res.value, { stream: true });
            var idx2;
            while ((idx2 = buf.indexOf("\n")) >= 0) {
              var line = buf.slice(0, idx2).trim(); buf = buf.slice(idx2 + 1);
              if (line.indexOf("data:") !== 0) continue;
              var pp = line.slice(5).trim();
              if (pp === "[DONE]") continue;
              try { var j = JSON.parse(pp); if (j.t === "token") { text += j.v; if (onToken) onToken(text); } else if (j.t === "error") { errMsg = j.v; } } catch (e) {}
            }
            return pump();
          });
        }
        return pump();
      }, function (e) {
        if (n < delays.length) return new Promise(function (res) { setTimeout(res, delays[n]); }).then(function () { return attempt(n + 1); });
        throw e;
      });
    }
    return attempt(0);
  }
'''
p = p.replace(dm_anchor, POSTSTREAM + dm_anchor, 1)

# 2b. part 循环改用 postStream（逐字实时显示）
PART_OLD = r'''        return postR({ mode: "part", idx: i, title: pl.title, points: pl.points, parts: pl.parts, convo: pl.convo, prevBrief: prev.slice(-1400), key: kv.key, vendor: kv.vendor })
          .then(function (r) {
            if (!r.ok) throw new Error(r.msg || "\u5206\u8282\u751f\u6210\u5931\u8d25");
            out += (out ? "\n\n" : "") + pl.parts[i].h + "\n" + r.text;
            prev = r.text; i++;
            dm.setText(out);
            return step();
          });'''
assert p.count(PART_OLD) == 1, "client part-loop anchor not unique"
PART_NEW = r'''        var base = out ? (out + "\n\n") : "", head = pl.parts[i].h + "\n";
        return postStream({ mode: "part", idx: i, title: pl.title, points: pl.points, parts: pl.parts, convo: pl.convo, prevBrief: prev.slice(-1400), key: kv.key, vendor: kv.vendor }, function (partial) { dm.setText(base + head + partial); })
          .then(function (text) {
            out = base + head + text;
            prev = text; i++;
            dm.setText(out);
            return step();
          });'''
p = p.replace(PART_OLD, PART_NEW, 1)
open(P, "w", encoding="utf-8").write(p)
print("✅ 客户端: part 调用改流式 + 逐字实时显示")

# ═══════════ 3) e2e sim: part mock → SSE + 加大 flush ═══════════
S = "tools/sim_wds_dialogue_e2e.js"
s = open(S, encoding="utf-8").read()
SIM_OLD = r'''  if (b.mode === "part") return Promise.resolve({ json: () => Promise.resolve({ ok: true, text: "正文".repeat(900) }) });'''
assert s.count(SIM_OLD) == 1, "sim part mock anchor not unique"
SIM_NEW = r'''  if (b.mode === "part") return Promise.resolve({ ok: true, body: sse(['data: {"t":"token","v":"' + "正文".repeat(900) + '"}\n', "data: [DONE]\n"]) });'''
s = s.replace(SIM_OLD, SIM_NEW, 1)
FLUSH_OLD = '  papB.onclick(); await flush(60);'
assert s.count(FLUSH_OLD) == 1, "sim flush anchor not unique"
s = s.replace(FLUSH_OLD, '  papB.onclick(); await flush(120);', 1)
open(S, "w", encoding="utf-8").write(s)
print("✅ e2e: part mock 改 SSE + flush 加大")
