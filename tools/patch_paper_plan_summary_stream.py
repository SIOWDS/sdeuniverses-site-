#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把论文链路彻底流式化:read-paper 的 plan(拟题) 与 summary(总结) 也改 SSE 流式(part 上一轮已改)。
plan 在流内跑 LLM、累积正文、looseJSON+重试,末尾发一个 {t:"plan"} 事件带回结构化提纲;summary 逐字转发。
客户端:plan 用新 postPlanStream 读结构化事件,summary 用 postStream 累积;postStream 透传 error code。
e2e:plan/summary mock 改 SSE。三处一致。assert 锚定,锚点缺失即报错拒改。"""

# ═════════════ 1) worker.js: summary + plan → SSE ═════════════
W = "src/worker.js"
h = open(W, encoding="utf-8").read()

# --- summary ---
s_start = '      if (b.mode === "summary") {'
s_end = '        const out = await llmText(VC, KEY, sys, usr, 3200);\n        return out ? J({ ok: true, text: out }) : J({ ok: false, msg: "总结生成失败，请重试。" }, 502);\n      }'
assert h.count(s_start) == 1 and h.count(s_end) == 1, "worker summary anchors not unique"
si = h.find(s_start); sj = h.find(s_end, si) + len(s_end)
SUMMARY_NEW = r'''      if (b.mode === "summary") {
        const stream = new ReadableStream({
          async start(controller) {
            const fin = () => { try { controller.enqueue(_ENC.encode("data: [DONE]\n\n")); controller.close(); } catch (e) {} };
            try {
              const sys = "你是 WDS，王德生的 AI 分身。你刚经历了一场" + SCENE + "。现在要为读者把这场对话总结下来。" + BASE
                + "\n用严谨而有锋刃的汉语；不摆空模板、不注水、不写开场白；不要用 #、* 等 markdown 符号，用短小标题与自然段分层。";
              const usr = CTX + "\n\n请写一份这场陪读的总结，约 1200-1600 字，分四节：\n一、我们谈了什么（脉络，不是流水账）\n二、真正推进了的几个判断（逐条列出，每条一句话说清它比常识多走了哪一步）\n三、用 SDE 看这场对话（显露/差异序列/特征纠缠或三大方程，照见读者原来卡在哪、现在站在哪）\n四、还没解决的问题（留给读者继续读、继续想的口子）\n直接从正文写起。";
              let upstream;
              try { upstream = await fetch(VC.url, { method: "POST", headers: { "content-type": "application/json", authorization: "Bearer " + KEY }, body: JSON.stringify(wdsTopBody(VC, { model: VC.model, stream: true, max_tokens: 3200, messages: [{ role: "system", content: sys }, { role: "user", content: usr }] })) }); }
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
            } catch (e) { controller.enqueue(_sseBytes({ t: "error", v: "总结生成出错：" + (e && e.message) + "（可重试）" })); }
            fin();
          },
        });
        return new Response(stream, { headers: { ..._cors(), "content-type": "text/event-stream; charset=utf-8", "cache-control": "no-store" } });
      }'''
h = h[:si] + SUMMARY_NEW + h[sj:]

# --- plan ---（plan 起手在两个处理器都有；用唯一末尾锚点定位，回溯取其前最近的起手，只命中 read-paper）
p_start = '      if (b.mode === "plan") {'
p_end = '        return J({ ok: true, title: j.title, points: j.points || [], parts: j.parts.slice(0, PN), convo: convo.slice(-6000) });\n      }'
assert h.count(p_end) == 1, "worker plan end anchor not unique"
pj0 = h.find(p_end)
pi = h.rfind(p_start, 0, pj0)
assert pi >= 0, "worker plan start anchor missing before end"
pj = pj0 + len(p_end)
PLAN_NEW = r'''      if (b.mode === "plan") {
        const stream = new ReadableStream({
          async start(controller) {
            const fin = () => { try { controller.enqueue(_ENC.encode("data: [DONE]\n\n")); controller.close(); } catch (e) {} };
            try {
              const sys = "你是 SDE 学派的学术编辑，要把一场" + (GD ? "百轮问答" : "陪读对话") + "提炼成一篇约 " + (PN >= 6 ? "一万" : "5000") + " 字学术论文的骨架。" + (GD ? "这篇论文属于《问对WDS》系列——从与 WDS 的对话中练就创新观点、凝成关于 SDE 思想的论文。" : "") + BASE;
              const usr = CTX + "\n\n请基于以上：① 拟一个准确、有锋刃的学术论文标题（不要副标题堆砌）；② 选出 " + (PN >= 6 ? "4-6" : "3-5") + " 个『金点子』——这场对话里真正反直觉、可被检验的新判断，各一句；③ 给 " + (PN >= 6 ? "六" : "三") + " 个部分的写作大纲，每部分一个标题和一句主旨，各部分合起来构成完整论证（问题的提出 → " + (PN >= 6 ? "逐个展开核心判断（可多个部分） → 对最强反驳的回应" : "核心论证") + " → 结论与限度），部分之间不重复。\n只输出 JSON、不要任何其他文字：{\"title\":\"标题\",\"points\":[\"金点子1\",\"金点子2\"],\"parts\":[{\"h\":\"部分标题\",\"gist\":\"主旨\"},{\"h\":\"部分标题\",\"gist\":\"主旨\"},{\"h\":\"部分标题\",\"gist\":\"主旨\"}]}";
              const planTok = GD ? 8000 : 2400;
              const genOnce = async () => {
                let upstream;
                try { upstream = await fetch(VC.url, { method: "POST", headers: { "content-type": "application/json", authorization: "Bearer " + KEY }, body: JSON.stringify(wdsTopBody(VC, { model: VC.model, stream: true, max_tokens: planTok, messages: [{ role: "system", content: sys }, { role: "user", content: usr }] })) }); }
                catch (e) { return { err: "接不上基底：" + (e && e.message) }; }
                if (!upstream.ok) {
                  const errtxt = (await upstream.text()).slice(0, 200);
                  if (upstream.status === 401 || upstream.status === 402 || upstream.status === 429) return { err: "你的 Key 用不了（" + upstream.status + "）：额度不足或填错了。", code: "bad_key" };
                  return { err: "基底返回错误 " + upstream.status + "：" + errtxt };
                }
                const reader = upstream.body.getReader(); const dec = new TextDecoder(); let buf = "", content = "";
                while (true) {
                  const { done: rdone, value } = await reader.read(); if (rdone) break;
                  buf += dec.decode(value, { stream: true }); let li;
                  while ((li = buf.indexOf("\n")) >= 0) {
                    const line = buf.slice(0, li).trim(); buf = buf.slice(li + 1);
                    if (!line.startsWith("data:")) continue; const p = line.slice(5).trim(); if (p === "[DONE]") continue;
                    let j; try { j = JSON.parse(p); } catch (e) { continue; }
                    if (j.error) return { err: j.error.message || "基底流内错误" };
                    const d = (j.choices && j.choices[0] && j.choices[0].delta) || {};
                    if (d.reasoning_content) controller.enqueue(_sseBytes({ t: "think", v: d.reasoning_content }));
                    if (d.content) content += d.content;
                  }
                }
                return { content };
              };
              let r = await genOnce();
              let jj = r.content ? looseJSON(r.content) : null;
              if (!(jj && jj.title && Array.isArray(jj.parts) && jj.parts.length)) {
                if (r.err) { controller.enqueue(_sseBytes({ t: "error", v: r.err, code: r.code })); return fin(); }
                r = await genOnce();   // 思考模式下 JSON 偶发不达标：服务端自动重试一次
                jj = r.content ? looseJSON(r.content) : null;
                if (!(jj && jj.title && Array.isArray(jj.parts) && jj.parts.length)) { controller.enqueue(_sseBytes({ t: "error", v: r.err || "提纲生成失败，请重试。", code: r.code })); return fin(); }
              }
              controller.enqueue(_sseBytes({ t: "plan", v: { title: jj.title, points: jj.points || [], parts: jj.parts.slice(0, PN), convo: convo.slice(-6000) } }));
            } catch (e) { controller.enqueue(_sseBytes({ t: "error", v: "提纲生成出错：" + (e && e.message) })); }
            fin();
          },
        });
        return new Response(stream, { headers: { ..._cors(), "content-type": "text/event-stream; charset=utf-8", "cache-control": "no-store" } });
      }'''
h = h[:pi] + PLAN_NEW + h[pj:]
open(W, "w", encoding="utf-8").write(h)
print("✅ worker: summary + plan 已改 SSE 流式")

# ═════════════ 2) 客户端 wds-dialogue ═════════════
P = "public/taste/wds-dialogue/index.html"
p = open(P, encoding="utf-8").read()

# 2a. postStream 透传 error code（三处 ASCII 锚点小改）
a1o = 'var reader = r.body.getReader(), dec = new TextDecoder(), buf = "", text = "", errMsg = "";'
a1n = 'var reader = r.body.getReader(), dec = new TextDecoder(), buf = "", text = "", errMsg = "", errCode = "";'
assert p.count(a1o) == 1, "postStream var-decl anchor not unique"
p = p.replace(a1o, a1n, 1)
a2o = 'if (res.done) { if (errMsg && !text) throw new Error(errMsg); return text; }'
a2n = 'if (res.done) { if (errMsg && !text) { var er = new Error(errMsg); er.code = errCode; throw er; } return text; }'
assert p.count(a2o) == 1, "postStream done anchor not unique"
p = p.replace(a2o, a2n, 1)
a3o = 'try { var j = JSON.parse(pp); if (j.t === "token") { text += j.v; if (onToken) onToken(text); } else if (j.t === "error") { errMsg = j.v; } } catch (e) {}'
a3n = 'try { var j = JSON.parse(pp); if (j.t === "token") { text += j.v; if (onToken) onToken(text); } else if (j.t === "error") { errMsg = j.v; errCode = j.code || ""; } } catch (e) {}'
assert p.count(a3o) == 1, "postStream error-capture anchor not unique"
p = p.replace(a3o, a3n, 1)

# 2b. 新增 postPlanStream（插在 docModal 之前，即 postStream 之后）
dm_anchor = '  function docModal(title, kind) {'
assert p.count(dm_anchor) == 1, "client docModal anchor not unique"
POSTPLAN = '''  // 拟题也走流式（SSE）：先建立连接，思考在流内进行，末尾一个 {t:"plan"} 事件带回结构化提纲——避免出流前 503。
  function postPlanStream(body) {
    body.guide = 1; body.paperN = PN; body.docTitle = article.text ? article.title : TITLE; body.docText = article.text || ""; body.history = history; body.reflect = xinde;
    var delays = [1500, 4000];
    function attempt(n) {
      return fetch(PAPER, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) }).then(function (r) {
        if (!r.ok || !r.body) {
          if (n < delays.length) return new Promise(function (res) { setTimeout(res, delays[n]); }).then(function () { return attempt(n + 1); });
          throw new Error("HTTP " + r.status);
        }
        var reader = r.body.getReader(), dec = new TextDecoder(), buf = "", plan = null, errMsg = "", errCode = "";
        function pump() {
          return reader.read().then(function (res) {
            if (res.done) { if (plan) return plan; return { ok: false, msg: errMsg || "\u63d0\u7eb2\u751f\u6210\u5931\u8d25\uff0c\u8bf7\u91cd\u8bd5\u3002", code: errCode }; }
            buf += dec.decode(res.value, { stream: true });
            var idx2;
            while ((idx2 = buf.indexOf("\\n")) >= 0) {
              var line = buf.slice(0, idx2).trim(); buf = buf.slice(idx2 + 1);
              if (line.indexOf("data:") !== 0) continue;
              var pp = line.slice(5).trim();
              if (pp === "[DONE]") continue;
              try { var j = JSON.parse(pp); if (j.t === "plan" && j.v) { plan = { ok: true, title: j.v.title, points: j.v.points || [], parts: j.v.parts || [], convo: j.v.convo || "" }; } else if (j.t === "error") { errMsg = j.v; errCode = j.code || ""; } } catch (e) {}
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
p = p.replace(dm_anchor, POSTPLAN + dm_anchor, 1)

# 2c. summary flow → postStream（逐字实时显示）
SUM_OLD = r'''    postR({ mode: "summary", key: kv.key, vendor: kv.vendor })
      .then(function (r) {
        busy = false; paint(); dm.setProg("");
        if (!r.ok) { dm.setTitle("\u6ca1\u80fd\u751f\u6210"); dm.setText(r.msg || "\u8bf7\u91cd\u8bd5\u3002"); if (r.code === "need_key") keyPanel(null); return; }
        dm.setTitle("\u4e0e WDS \u5bf9\u8bdd \u00b7 \u5168\u573a\u603b\u7ed3"); dm.setText(r.text);
      })
      .catch(function (e) { busy = false; paint(); dm.setTitle("\u6ca1\u80fd\u751f\u6210"); dm.setText("\u7f51\u7edc\u51fa\u9519\uff1a" + (e && e.message)); });'''
assert p.count(SUM_OLD) == 1, "client summary-flow anchor not unique"
SUM_NEW = r'''    postStream({ mode: "summary", key: kv.key, vendor: kv.vendor }, function (partial) { dm.setText(partial); })
      .then(function (text) {
        busy = false; paint(); dm.setProg("");
        dm.setTitle("\u4e0e WDS \u5bf9\u8bdd \u00b7 \u5168\u573a\u603b\u7ed3"); dm.setText(text);
      })
      .catch(function (e) { busy = false; paint(); dm.setProg(""); dm.setTitle("\u6ca1\u80fd\u751f\u6210"); dm.setText("\u751f\u6210\u51fa\u9519\uff1a" + (e && e.message)); if (e && e.code === "need_key") keyPanel(null); });'''
p = p.replace(SUM_OLD, SUM_NEW, 1)

# 2d. plan 调用 → postPlanStream
PLAN_CALL_OLD = 'postR({ mode: "plan", key: kv.key, vendor: kv.vendor }).then(function (pl) {'
assert p.count(PLAN_CALL_OLD) == 1, "client plan-call anchor not unique"
p = p.replace(PLAN_CALL_OLD, 'postPlanStream({ mode: "plan", key: kv.key, vendor: kv.vendor }).then(function (pl) {', 1)
open(P, "w", encoding="utf-8").write(p)
print("✅ 客户端: postPlanStream + summary/plan 流式 + postStream code 透传")

# ═════════════ 3) e2e sim: plan + summary mock → SSE ═════════════
S = "tools/sim_wds_dialogue_e2e.js"
s = open(S, encoding="utf-8").read()
SIM_PLAN_OLD = r'''    return Promise.resolve({ json: () => Promise.resolve({ ok: true, title: "问对WDS：一场百轮对话凝成的论文", points: ["金点子甲", "金点子乙", "金点子丙", "金点子丁"], parts, convo: rec.convoSeen.slice(0, 6000) }) });'''
assert s.count(SIM_PLAN_OLD) == 1, "sim plan mock anchor not unique"
SIM_PLAN_NEW = r'''    const planObj = { title: "问对WDS：一场百轮对话凝成的论文", points: ["金点子甲", "金点子乙", "金点子丙", "金点子丁"], parts, convo: rec.convoSeen.slice(0, 6000) };
    return Promise.resolve({ ok: true, body: sse(['data: {"t":"plan","v":' + JSON.stringify(planObj) + '}\n', "data: [DONE]\n"]) });'''
s = s.replace(SIM_PLAN_OLD, SIM_PLAN_NEW, 1)
SIM_SUM_OLD = r'''    return Promise.resolve({ json: () => Promise.resolve({ ok: true, text: "总结正文".repeat(350) }) });'''
assert s.count(SIM_SUM_OLD) == 1, "sim summary mock anchor not unique"
SIM_SUM_NEW = r'''    return Promise.resolve({ ok: true, body: sse(['data: {"t":"token","v":"' + "总结正文".repeat(350) + '"}\n', "data: [DONE]\n"]) });'''
s = s.replace(SIM_SUM_OLD, SIM_SUM_NEW, 1)
sf_o = '  sumB.onclick(); await flush(20);'
assert s.count(sf_o) == 1, "sim summary flush anchor not unique"
s = s.replace(sf_o, '  sumB.onclick(); await flush(40);', 1)
open(S, "w", encoding="utf-8").write(s)
print("✅ e2e: plan + summary mock 改 SSE + summary flush 加大")
