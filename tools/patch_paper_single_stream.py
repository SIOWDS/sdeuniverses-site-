#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把"凝成一万字论文"从"拟题(JSON)→六次分部→总结"的多趟编排,改成单趟流式:
read-paper 新增 mode="full"——先出流后干活+心跳,把整篇论文(标题+六部分)当一篇长文一次写完、逐字 token 吐出;
客户端 papB 改成只调这一个流式请求(逐字实时显示);e2e mock+断言同步。
一趟请求=一次 503 机会(而非七次),且无 JSON 提纲要解析、无分部接缝。assert 锚定。"""

# ═══════════ 1) worker.js:read-paper 新增 mode="full"(插在 summary 之前,summary 锚点唯一)═══════════
W = "src/worker.js"
h = open(W, encoding="utf-8").read()
anchor = '      if (b.mode === "summary") {'
assert h.count(anchor) == 1, "read-paper summary anchor not unique"
FULL = r'''      if (b.mode === "full") {
        // 单趟流式成文:先把 200 SSE 流交出去,再在流内做 RAG + await 上游把整篇论文一次写完、逐字转发。
        // 一趟请求=一次 503 机会(而非拟题+六分部+总结七趟),且无 JSON 提纲要解析、无分部接缝。
        const stream = new ReadableStream({
          async start(controller) {
            let _hb = null;
            const fin = () => { if (_hb) clearInterval(_hb); try { controller.enqueue(_ENC.encode("data: [DONE]\n\n")); controller.close(); } catch (e) {} };
            _hb = setInterval(() => { try { controller.enqueue(_ENC.encode(": ping\n\n")); } catch (e) {} }, 10000);
            try {
              // 全站 RAG:按议题线索取一段结构化知识,整篇一次注入
              let ragCtx = "";
              if (GD) {
                try {
                  const corpus = await loadCorpus(env, url);
                  const q = ((docTitle ? docTitle + " " : "") + convo.slice(0, 600)).slice(0, 300);
                  const seen = {};
                  let kbBlock = "";
                  try { const kb = await loadKB(env, url); if (kb) { const r = retrieveKB(kb, corpus, q, [], 24); kbBlock = r.block; } } catch (e) {}
                  const cap = Math.max(4000, 12000 - kbBlock.length);
                  const hits = retrieve(corpus, q, 16, []);
                  let chunkText = "";
                  for (const ck of hits) { const d = corpus.docs[ck.d]; if (!d || seen[d.u]) continue; seen[d.u] = 1; chunkText += "【来源：" + d.t + "】\n" + ck.t.slice(0, 900) + "\n\n"; if (chunkText.length > cap) break; }
                  ragCtx = kbBlock + (kbBlock && chunkText ? "\n【补充 · 站内原文片段】\n" : "") + chunkText;
                } catch (e) {}
              }
              const PW = PN >= 6 ? "一万" : "5000";
              const sys = "你是 SDE 学派的学者，正在写一篇严谨的学术论文。" + (GD ? "本文属《问对WDS》系列——由一场与 WDS 的百轮问答凝成、关于 SDE 思想的论文。" : "") + BASE
                + "\n用严谨学术汉语写作：论证扎实、有可被反驳的明确判断、不注水、不摆空模板；可用 SDE 概念但必须讲透、服务论证。用自然段和简短小标题分层，不要用 #、* 等 markdown 符号，不要写参考文献。";
              const usr = CTX + (ragCtx ? ("\n【站内资料·全站检索到的相关段落（可据以印证，引用时标（来源：篇名），没有的别编）】\n" + ragCtx + "\n") : "")
                + "\n\n现在，请把上面这场对话凝成一篇约 " + PW + " 字的完整学术论文，一气呵成、从头写到尾：\n"
                + "① 开篇先给一个准确、有锋刃的标题（单独成行）；\n"
                + "② 正文分 " + (PN >= 6 ? "六" : "三") + " 个部分，每部分一个简短小标题 + 充分展开的论证，各部分构成完整论证链（问题的提出 → 逐个核心判断 → 对最强反驳的回应 → 结论与限度），部分之间不重复、层层递进；\n"
                + "③ 直接从标题写起，不要开场白、不要目录、不要“以下是”之类的话。";
              let upstream;
              try { upstream = await fetch(VC.url, { method: "POST", headers: { "content-type": "application/json", authorization: "Bearer " + KEY }, body: JSON.stringify(wdsTopBody(VC, { model: VC.model, stream: true, max_tokens: (GD && vd === "deepseek") ? 32000 : 8000, messages: [{ role: "system", content: sys }, { role: "user", content: usr }] })) }); }
              catch (e) { controller.enqueue(_sseBytes({ t: "error", v: "接不上基底：" + (e && e.message) })); return fin(); }
              if (!upstream.ok) {
                const errtxt = (await upstream.text()).slice(0, 200);
                if (upstream.status === 401 || upstream.status === 402 || upstream.status === 429) { controller.enqueue(_sseBytes({ t: "error", v: "你的 Key 用不了（" + upstream.status + "）：额度不足或填错了。", code: "bad_key" })); return fin(); }
                controller.enqueue(_sseBytes({ t: "error", v: "基底返回错误 " + upstream.status + "：" + errtxt })); return fin();
              }
              const reader = upstream.body.getReader(); const dec = new TextDecoder(); let buf = "";
              while (true) {
                const { done: rdone, value } = await reader.read(); if (rdone) break;
                buf += dec.decode(value, { stream: true }); let li;
                while ((li = buf.indexOf("\n")) >= 0) {
                  const line = buf.slice(0, li).trim(); buf = buf.slice(li + 1);
                  if (!line.startsWith("data:")) continue; const p = line.slice(5).trim(); if (p === "[DONE]") continue;
                  let j; try { j = JSON.parse(p); } catch (e) { continue; }
                  if (j.error) { controller.enqueue(_sseBytes({ t: "error", v: j.error.message || "基底流内错误" })); continue; }
                  const d = (j.choices && j.choices[0] && j.choices[0].delta) || {};
                  if (d.reasoning_content) controller.enqueue(_sseBytes({ t: "think", v: d.reasoning_content }));
                  if (d.content) controller.enqueue(_sseBytes({ t: "token", v: d.content }));
                }
              }
            } catch (e) { controller.enqueue(_sseBytes({ t: "error", v: "成文出错：" + (e && e.message) + "（可重试）" })); }
            fin();
          },
        });
        return new Response(stream, { headers: { ..._cors(), "content-type": "text/event-stream; charset=utf-8", "cache-control": "no-store" } });
      }
'''
h = h.replace(anchor, FULL + anchor, 1)
open(W, "w", encoding="utf-8").write(h)
print("✅ worker: read-paper 新增 mode='full' 单趟流式成文")

# ═══════════ 2) 客户端 papB.onclick → 单趟流式 ═══════════
P = "public/taste/wds-dialogue/index.html"
p = open(P, encoding="utf-8").read()
PAPB_OLD = r'''  papB.onclick = function () {
    var kv = needKey(function (ok) { if (ok) papB.onclick(); }); if (!kv) return;
    busy = true; paint();
    var dm = docModal("\u6b63\u5728\u51dd\u6210\u300a\u95ee\u5bf9WDS\u300b\u2026", "paper");
    dm.setProg("\u7b2c 1 \u6b65\uff1a\u62df\u9898\u4e0e\u63d0\u7eb2\u2026");
    var out = "", prev = "", i = 0;
    postPlanStream({ mode: "plan", key: kv.key, vendor: kv.vendor }).then(function (pl) {
      if (!pl.ok) throw new Error(pl.msg || "\u63d0\u7eb2\u5931\u8d25");
      dm.setTitle(pl.title);
      function step() {
        if (i >= pl.parts.length) {
          busy = false; paint(); dm.setProg("\u5171 " + out.replace(/\s/g, "").length + " \u5b57 \u00b7 \u53ef\u590d\u5236\u6216\u5bfc\u51fa PDF");
          return;
        }
        dm.setProg("\u7b2c " + (i + 2) + " \u6b65 / \u5171 " + (pl.parts.length + 1) + " \u6b65\uff1a\u6b63\u5728\u5199\u3010" + pl.parts[i].h + "\u3011\u2026");
        var base = out ? (out + "\n\n") : "", head = pl.parts[i].h + "\n";
        return postStream({ mode: "part", idx: i, title: pl.title, points: pl.points, parts: pl.parts, convo: pl.convo, prevBrief: prev.slice(-1400), key: kv.key, vendor: kv.vendor }, function (partial) { dm.setText(base + head + partial); })
          .then(function (text) {
            out = base + head + text;
            prev = text; i++;
            dm.setText(out);
            return step();
          });
      }
      return step();
    }).catch(function (e) {
      busy = false; paint(); dm.setProg("");
      dm.setText(out + (out ? "\n\n" : "") + "\u3010\u751f\u6210\u4e2d\u65ad\uff1a" + (e && e.message) + "\u3002\u5df2\u5199\u597d\u7684\u90e8\u5206\u4ecd\u53ef\u590d\u5236\u6216\u5bfc\u51fa\uff0c\u4e5f\u53ef\u5173\u6389\u91cd\u8bd5\u3002\u3011");
    });
  };'''
assert p.count(PAPB_OLD) == 1, "client papB anchor not unique"
PAPB_NEW = r'''  papB.onclick = function () {
    var kv = needKey(function (ok) { if (ok) papB.onclick(); }); if (!kv) return;
    busy = true; paint();
    var dm = docModal("正在凝成《问对WDS》…", "paper");
    dm.setProg("一气呵成撰写中（约一万字）· 逐字实时显示…");
    // 单趟流式:整篇论文一次写完、逐字往外吐（onToken 实时刷进弹窗）
    postStream({ mode: "full", key: kv.key, vendor: kv.vendor }, function (partial) { dm.setText(partial); })
      .then(function (text) {
        busy = false; paint();
        var nl = text.indexOf("\n");
        if (nl > 0 && nl < 60) dm.setTitle(text.slice(0, nl).trim());
        dm.setProg("共 " + text.replace(/\s/g, "").length + " 字 · 可复制或导出 PDF");
      })
      .catch(function (e) {
        busy = false; paint(); dm.setProg("");
        dm.setText("【生成中断：" + (e && e.message) + "。已写好的部分仍可复制或导出，也可关掉重试。】");
        if (e && e.code === "need_key") keyPanel(null);
      });
  };'''
p = p.replace(PAPB_OLD, PAPB_NEW, 1)
open(P, "w", encoding="utf-8").write(p)
print("✅ 客户端: papB 改为单趟流式成文(逐字实时显示)")

# ═══════════ 3) e2e sim:加 full mock + 更新 papB 断言 ═══════════
S = "tools/sim_wds_dialogue_e2e.js"
s = open(S, encoding="utf-8").read()
# 3a. full mock —— 插在 plan mock 之前
plan_mock_anchor = '  if (b.mode === "plan") {'
assert s.count(plan_mock_anchor) == 1, "sim plan mock anchor not unique"
FULL_MOCK = r'''  if (b.mode === "full") {
    rec.convoSeen = readConvoText(b.history || [], b.guide ? 300000 : 24000);
    let paper = "先修门框：论X的节律优先性\n";
    for (let k = 1; k <= 6; k++) paper += "第" + k + "部分 · 小标题\n" + "正文".repeat(800) + "\n\n";
    return Promise.resolve({ ok: true, body: sse(['data: {"t":"token","v":' + JSON.stringify(paper) + '}\n', "data: [DONE]\n"]) });
  }
'''
s = s.replace(plan_mock_anchor, FULL_MOCK + plan_mock_anchor, 1)

# 3b. papB 断言块更新(拟题+分部 → 单趟 full)
ASRT_OLD = r'''  const plan = calls.filter((c) => c.body.mode === "plan");
  const parts = calls.filter((c) => c.body.mode === "part");
  ok("拟题一次 + 六部分逐段（共七步）", plan.length === 1 && parts.length === 6, "plan " + plan.length + " / part " + parts.length);
  ok("拟题亦吃全场原文", plan[0].convoSeen.length > 180000 && plan[0].convoSeen.indexOf("第一问：什么是发生学") >= 0);
  ok("每部分带 idx / 上一节摘要防重复 / 心得", parts.every((c, i) => c.body.idx === i && (c.body.reflect || "").length >= 4000) && parts.slice(1).every((c) => (c.body.prevBrief || "").length > 0));'''
assert s.count(ASRT_OLD) == 1, "sim papB assertion block anchor not unique"
ASRT_NEW = r'''  const fullCalls = calls.filter((c) => c.body.mode === "full");
  const plan = calls.filter((c) => c.body.mode === "plan");
  const parts = calls.filter((c) => c.body.mode === "part");
  ok("成文走单趟流式（mode full，不再拆多趟）", fullCalls.length === 1 && plan.length === 0 && parts.length === 0, "full " + fullCalls.length + " / plan " + plan.length + " / part " + parts.length);
  ok("成文吃全场原文（非末段摘要）", fullCalls[0].convoSeen.length > 180000 && fullCalls[0].convoSeen.indexOf("第一问：什么是发生学") >= 0);
  ok("成文带 guide 与本场心得", fullCalls[0].body.guide === 1 && (fullCalls[0].body.reflect || "").length >= 4000);'''
s = s.replace(ASRT_OLD, ASRT_NEW, 1)
open(S, "w", encoding="utf-8").write(s)
print("✅ e2e: 加 full mock + papB 断言改为单趟流式")
