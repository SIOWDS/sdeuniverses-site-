#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给 worker 装上共用的「站内近邻」端点 /api/kb/neighbors。

为什么要单独一个端点，而不在 /api/kb/retrieve 上加 mode：
  retrieve 交付的是**可直接垫进 prompt 的语料块**——它的用途是让基底"知道得更多"。
  近邻交付的是**一张必须被逐条处理的清单**（篇目 + 该篇的一句话判断 + 链接）——
  它的用途是让基底"必须交代与谁重合、分离线在哪"。两者的产物形态与失败后果都不同：
  retrieve 拿不到块，答案只是浅一点；近邻拿不到清单，产出会重复站上已有概念而无人发现。
  retrieve 已被三个客户端在用，不动它，避免为新用途去改一个正在承重的东西。

一句话判断从哪来：`/students/publications.json` 每条 item 的 summary 就是一句话判断
  （发表时逐篇写的"那一刀"），这是站上现成、最干净的近邻材料，724 条、401KB，
  可整份装载并模块级缓存——不必去碰 2000 万字语料。
  非学员栏目（每日必读/学科通融/专著）不在 publications 里，用现成的分层检索 lightRetrieve
  兜一遍，取标题与命中片段首句当作那一行。两路按 url 去重后合并排序。
"""
import re, sys, io

P = "src/worker.js"
s = io.open(P, encoding="utf-8").read()
orig = s

# ── ① 加载器 + 纯打分函数（放在 loadPyramid 之后，与其他 loader 同族） ──
anchor = "// 三层下钻：给一段问题，从长期原则里挑最相关的几条 → 顺 mids 进中期条目 → 顺 docs 落到文章。"
assert anchor in s, "loadPyramid 之后的锚点没找到"

BLOCK = r'''
// ===== NEIGHBORS：站内近邻清单 =====
// 目的与 retrieveKB 不同：不为"多知道一点"，而为**逼出交代**——
// 新判断必须说清它与站上已有篇目的分离线，否则概念会在同一个专栏里重复发明。
// 材料取 /students/publications.json：每条 item 的 summary 是发表时逐篇写的一句话判断。
let PUBS = { at: 0, items: null };
async function loadPubs(env, url) {
  const now = Date.now();
  if (PUBS.at && now - PUBS.at < CORPUS_TTL && PUBS.items) return PUBS.items;
  const out = [];
  try {
    const r = await env.ASSETS.fetch(new Request(new URL("/students/publications.json", url)));
    if (r.ok) {
      const j = await r.json();
      for (const st of (j.students || [])) {
        for (const it of (st.items || [])) {
          if (!it || !it.url || !it.title) continue;
          out.push({ t: String(it.title), u: String(it.url), kind: String(it.kind || ""), line: String(it.summary || ""), au: String(st.name || ""), auSlug: String(st.slug || "") });
        }
      }
    }
  } catch (e) {}
  PUBS = { at: now, items: out };
  return out;
}
// nbTerms/nbRank 是纯函数：与 pyramidDrill 同一套中文二元切分，便于离线测试。
function nbTerms(q) {
  const raw = String(q || "").toLowerCase();
  const terms = [];
  for (const w of (raw.match(/[a-z]{3,}/g) || [])) terms.push(w);
  for (const run of (raw.match(/[\u4e00-\u9fff]{2,}/g) || [])) { for (let i = 0; i + 2 <= run.length; i++) terms.push(run.slice(i, i + 2)); }
  const uniq = [];
  const seen = Object.create(null);
  for (const t of terms) if (!seen[t]) { seen[t] = 1; uniq.push(t); }
  return uniq;
}
// 标题权重最高（概念名通常落在标题里），一句话判断次之，栏目名只作微弱加成。
// own=作者自己的篇目：**不排除、只标注**——自我重复正是最常见也最难自查的一种重合。
function nbRank(items, q, k, opts) {
  opts = opts || {};
  const terms = nbTerms(q);
  if (!terms.length) return [];
  const au = String(opts.author || "").trim();
  const out = [];
  for (const it of (items || [])) {
    const T = String(it.t || "").toLowerCase(), L = String(it.line || "").toLowerCase(), K = String(it.kind || "").toLowerCase();
    let sc = 0;
    for (const t of terms) { if (T.indexOf(t) >= 0) sc += 3; if (L.indexOf(t) >= 0) sc += 1; if (K.indexOf(t) >= 0) sc += 1; }
    if (sc <= 0) continue;
    const own = !!au && (it.auSlug === au || it.au === au);
    out.push({ t: it.t, u: it.u, kind: it.kind, line: it.line, au: it.au, own: own, score: sc + (own ? 2 : 0) });
  }
  out.sort((a, b) => b.score - a.score || String(a.u).localeCompare(String(b.u)));
  return out.slice(0, Math.max(1, k || 8));
}
// 渲染成可直接注入的一块。注意这里只交付**材料与交代义务**，不替调用方规定文风：
// 各智能体的提问自己决定近邻节写成什么样，这一块只负责"名单在此，逐条处理"。
function nbBlock(list) {
  if (!list || !list.length) return "";
  const lines = list.map((x, i) => (i + 1) + "、《" + x.t + "》（" + x.u + "）"
    + (x.au ? "｜作者 " + x.au : "") + (x.own ? "｜**本人已发**" : "")
    + (x.line ? "\n　　该篇的判断：" + x.line : ""));
  return "【站内近邻（sdeuniverses.com 已发表的相关篇目）——这一节是硬要求：\n"
    + "对下列每一篇，必须说清它已经说到哪一步，以及你这一次的判断与它的分离线在哪；\n"
    + "凡划不出分离线的，直接说明本次判断与该篇重复，不要另起新名。标注「本人已发」的尤其要查，\n"
    + "同一个作者在同一个栏目里重复发明概念，是最不容易被自己发现的一种重合。】\n"
    + lines.join("\n") + "\n";
}
'''

s = s.replace(anchor, BLOCK.strip("\n") + "\n" + anchor, 1)

# ── ② 端点（放在 /api/kb/retrieve 之前） ──
ep_anchor = '    if (url.pathname === "/api/kb/retrieve") {'
assert ep_anchor in s, "retrieve 端点锚点没找到"

EP = r'''    if (url.pathname === "/api/kb/neighbors") {
      // 站内近邻清单：给任意智能体一张"必须逐条交代分离线"的名单。无需 Key，只读静态资产。
      // 两路材料：publications.json（学员专栏，自带一句话判断）+ 分层检索（每日必读/学科通融/专著等
      // 不在 publications 里的栏目，用命中片段首句当那一行）。按 url 去重后合并排序。
      if (request.method === "OPTIONS") return new Response(null, { headers: _cors() });
      if (request.method !== "POST") return new Response("Method Not Allowed", { status: 405 });
      let b = {}; try { b = await request.json(); } catch (e) {}
      const q = String(b.q || "").trim().slice(0, 2000);
      if (q.length < 1) return Response.json({ neighbors: [], block: "", n: 0 }, { headers: _cors() });
      const k = Math.max(1, Math.min(20, parseInt(b.k, 10) || 8));
      const author = String(b.author || "").slice(0, 40);
      const wantSite = b.site !== false;   // 是否并入非学员栏目（默认并入）
      try {
        const pubs = await loadPubs(env, url);
        let list = nbRank(pubs, q, k + 6, { author: author });
        const seen = Object.create(null);
        for (const x of list) seen[x.u] = 1;
        if (wantSite) {
          // 只多取一小把，够补上 publications 覆盖不到的栏目即可，不为它加检索预算。
          try {
            const lr = await lightRetrieve(env, url, q, [], 8, 900, { pick: 8 });
            for (const ck of (lr.hits || [])) {
              const d = lr.corpus.docs[ck.d];
              if (!d || !d.u || seen[d.u]) continue;
              if (/^\/students\//.test(d.u)) continue;   // 学员篇目已由 publications 一路覆盖且带判断句
              seen[d.u] = 1;
              const first = String(ck.t || "").replace(/\s+/g, " ").trim().slice(0, 120);
              list.push({ t: d.t, u: d.u, kind: "", line: first, au: "", own: false, score: 1 });
            }
          } catch (e) {}
        }
        list = list.sort((a, c) => c.score - a.score).slice(0, k);
        return Response.json({ neighbors: list, block: nbBlock(list), n: list.length, terms: nbTerms(q).length }, { headers: _cors() });
      } catch (e) {
        return Response.json({ neighbors: [], block: "", n: 0, error: String(e && e.message) }, { headers: _cors() });
      }
    }
'''

s = s.replace(ep_anchor, EP + ep_anchor, 1)

if s == orig:
    print("没有任何改动，退出"); sys.exit(1)
io.open(P, "w", encoding="utf-8").write(s)
print("patched: loadPubs/nbTerms/nbRank/nbBlock + /api/kb/neighbors")
