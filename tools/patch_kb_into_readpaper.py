#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把九库结构化检索接进 /api/wds/read-paper 的 part 模式——《问对WDS》成文时每一部分的站内检索。
KB 邻域子图在前(按本部分标题+主旨+金点子定位),K=12 相似句召回保留但收紧上限为其让预算。同步 e2e 断言。
assert 锚定,任一锚点缺失即报错拒改。"""

W = "src/worker.js"
h = open(W, encoding="utf-8").read()

start = '        let partCtx = "";\n        if (GD) {'
end   = '              if (partCtx.length > 8000) break;\n            }\n          } catch (e) {}\n        }'
assert h.count(start) == 1, "worker start anchor not unique/found"
i = h.find(start); j = h.find(end, i)
assert j >= 0, "worker end anchor missing"
j += len(end)

NEW = '''        let partCtx = "";
        if (GD) {
          try {
            const corpus = await loadCorpus(env, url);
            const pq = (title + " " + (parts[idx].h || "") + " " + points.join(" ")).slice(0, 300);
            const pseen = {};
            // —— 结构化知识：九库邻域子图（按本部分主旨定位），让成文引到成体系的判断而非仅相似句 ——
            let kbBlock = "";
            try {
              const kb = await loadKB(env, url);
              if (kb) { const r = retrieveKB(kb, corpus, pq, [], 18); kbBlock = r.block; }
            } catch (e) {}
            // —— 相似句补充：K=12；KB 命中时收紧上限为其让预算 ——
            const pcap = Math.max(3000, 8000 - kbBlock.length);
            const phits = retrieve(corpus, pq, 12, []);
            let chunkText = "";
            for (const ck of phits) {
              const d = corpus.docs[ck.d]; if (!d || pseen[d.u]) continue; pseen[d.u] = 1;
              chunkText += "【来源：" + d.t + "】\\n" + ck.t.slice(0, 900) + "\\n\\n";
              if (chunkText.length > pcap) break;
            }
            partCtx = kbBlock + (kbBlock && chunkText ? "\\n【补充 · 站内原文片段】\\n" : "") + chunkText;
          } catch (e) {}
        }'''
h = h[:i] + NEW + h[j:]
open(W, "w", encoding="utf-8").write(h)
print("✅ worker /api/wds/read-paper part 模式已接九库")

# ---- e2e sim: 旧上限断言改新 + 增 part 模式 KB 接线断言 ----
S = "tools/sim_wds_dialogue_e2e.js"
s = open(S, encoding="utf-8").read()
old = 'ok("万字论文分部检索（K=12 / 8000 上限）", W.includes("retrieve(corpus, pq, 12, [])") && W.includes("partCtx.length > 8000"));'
assert old in s, "sim part assertion anchor missing"
new = ('ok("万字论文分部检索（K=12 + KB留预算上限）", W.includes("retrieve(corpus, pq, 12, [])") && W.includes("8000 - kbBlock.length"));\n'
       'ok("成文分部亦接九库（part 模式 retrieveKB 供结构化判断）", W.includes("retrieveKB(kb, corpus, pq, [], 18)") && W.includes("partCtx = kbBlock +"));')
s = s.replace(old, new, 1)
open(S, "w", encoding="utf-8").write(s)
print("✅ e2e 断言已同步(part 上限改新 + 增 KB 接线校验)")
