#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""个人知识库（kb）—— 后端。幂等可复跑。

用户的话：「SDE 社区里面每人有个 SDE 个人网页，里面有个个人『知识库』，
画布可以直接存入自己的知识库，采用名字和密码。当然 SDE 个人网页是属于个人的。」

**先说三件已经在站上、不必重造的**（查过代码，不是凭印象）：
  · 名字＋密码登录：全站统一（"请先在「SDE 社区」用名字和密码登录"），uid 一套，
    账本那条线明令「不造第五套键空间」，所以这里**复用同一把身份**，一行新鉴权都不写。
  · 个人 SDE 网页：社区第二档已建（成员面 v-who）。
  · 三个已有的库：vt(一句话·200字·全站共用一池)／lb(只存站内篇目指针)／cd(三段命题·关系)。
    **它们都装不下画布的产出**——两万字报告、一张结构图、一页网页。缺口是真的。

⚠ **与「存储口径必须虚」的关系（这一步是口径的延伸，写清楚）**：
  微信/社区子系统定过「思想流必须虚，只存链接」，理由是 E = H(S, D) ⇒ E 不该自己囤 S。
  但那条口径同时有一个已裁定的例外：**朋友圈图片可以实，因为一张照片没有别处的规范源。**
  画布产出正是同一种东西——一份刚锻出来的稿子**在站上没有任何别的规范位置**，
  它不是站内 840 篇里的哪一篇，没有 slug 可指。⇒ 按同一条理由，它可以实。
  边界照旧：**站上已经有的篇目不许在这里再存一份**（那是文章库的活）。

设计：
  · 键 `ki:<uid>:<inv>:<rnd>` ＝元数据（题名/类型/字数/来处/pid），`kb:<uid>:<inv>:<rnd>` ＝正文。
    **分开存的理由**：列表不该把十件两万字的稿子一起拖回来。
  · 两个键都带 uid ⇒ 天然隔离，别人查不到也删不掉（与 lb: 同一路数）。
  · 配额写死在服务端：单件 30,000 字／每人 120 件／每人合计 1,200,000 字。
    超了**如实说**并指出去处（存到本机），不静默截断。
"""
import io

P = "src/worker.js"
h = io.open(P, encoding="utf-8").read()
orig = h

PROBE = 'op === "kbadd"'
if PROBE in h:
    print("· 后端已有 kb 段，跳过")
else:
    ANCHOR = '''      if (op === "cdpost") {'''
    assert ANCHOR in h, "找不到 cdpost 锚点"
    assert h.count(ANCHOR) == 1, "锚点不唯一"

    KB = '''      /* ===== 个人知识库 kb: =====
         用户的话：「SDE 社区里面每人有个 SDE 个人网页，里面有个个人『知识库』，
         画布可以直接存入自己的知识库……当然 SDE 个人网页是属于个人的。」

         **它与已有三个库的分工，别混**：
           vt(思想库存)＝一句话、200 字上限、全站共用一池；
           lb(文章库)＝站上已有篇目的**指针**（slug＋题名），不存内容；
           cd(候选卡)＝三段命题，是关系不是文档。
         ⇒ 知识库装的是**本人产出的成品文档**（画布上的报告/结构图/网页/长稿）——
           这类东西此前只活在读者自己的浏览器 localStorage 里，换台机器就没了。

         **为什么这里可以存实的**：子系统的存储口径是「思想流必须虚」，
         理由是 E = H(S, D)、E 不该自己囤 S。但既有例外已裁定：朋友圈图片可以实，
         因为**一张照片没有别处的规范源**。画布稿同理——它不是站内 840 篇里的哪一篇，
         没有 slug 可指，站上没有第二个位置放它。边界照旧：
         **站上已经有的篇目不许在这里再存一份**（那是文章库的活，页面上已写明）。

         键：ki:<uid>:<inv>:<rnd> ＝元数据；kb:<uid>:<inv>:<rnd> ＝正文。
         分开存是因为**列表不该把十件两万字的稿子一起拖回来**。
         两个键都带 uid ⇒ 天然隔离：别人查不到，也删不掉（与 lb: 同一路数）。 */
      const KB_CHARS = 30000;      // 单件上限（两万字中文约 20000 字符，留冗余）
      const KB_COUNT = 120;        // 每人件数上限
      const KB_TOTAL = 1200000;    // 每人合计字数上限
      const kbKinds = { md: "文稿", html: "网页", svg: "图", mermaid: "结构图", csv: "表", json: "数据", code: "代码", note: "笔记" };
      async function kbScan(ctx, uid) {
        // 数一遍：件数与合计字数。元数据键很小，扫 200 条不贵。
        const m = await ctx.storage.list({ prefix: "ki:" + uid + ":", limit: 400 });
        let n = 0, chars = 0;
        const items = [];
        for (const k of m.keys()) {
          const it = await ctx.storage.get(k);
          if (!it) continue;
          n++; chars += (it.chars || 0); items.push(it);
        }
        return { n, chars, items };
      }
      if (op === "kbadd") {
        if (!ok12(uid)) return Response.json({ ok: false });
        const text = String(b.text == null ? "" : b.text);
        const title = moClean(b.title, 80) || "未命名";
        const kind = kbKinds[String(b.kind || "")] ? String(b.kind) : "note";
        if (text.trim().length < 20) return Response.json({ ok: false, msg: "太短了——知识库装的是成品，一两句话请存进「💡 思想库存」。" });
        if (text.length > KB_CHARS) {
          return Response.json({ ok: false, msg: "这一件 " + text.length + " 字，超过单件上限 " + KB_CHARS + " 字。请在画布上用「存到本机」保存，或先拆成几件。" });
        }
        const st = await kbScan(this.ctx, uid);
        if (st.n >= KB_COUNT) return Response.json({ ok: false, msg: "知识库已有 " + st.n + " 件，到上限了。先删掉几件，或把要长期留的「存到本机」。" });
        if (st.chars + text.length > KB_TOTAL) return Response.json({ ok: false, msg: "知识库合计已 " + st.chars + " 字，再存这一件会超过 " + KB_TOTAL + " 字上限。" });
        // 同一个人存同题同文不再多存一件（画布重复点「存进知识库」是常事）
        for (const it0 of st.items) {
          if (it0.title === title && it0.chars === text.length) {
            const old = await this.ctx.storage.get("kb:" + uid + ":" + it0.id);
            if (old === text) return Response.json({ ok: true, dup: 1, item: it0 });
          }
        }
        const id = moInv(now) + ":" + moRnd();
        const meta = {
          id, uid, title, kind, chars: text.length, ts: now,
          from: moClean(b.from, 60), pid: moClean(b.pid, 40), ver: parseInt(b.ver || 0, 10) || 0
        };
        await this.ctx.storage.put("kb:" + uid + ":" + id, text);
        await this.ctx.storage.put("ki:" + uid + ":" + id, meta);
        return Response.json({ ok: true, item: meta, left: KB_COUNT - st.n - 1 });
      }
      if (op === "kbmine") {
        // 只回元数据。正文按需一件一件取（kbget）。
        if (!ok12(uid)) return Response.json({ ok: false });
        const st = await kbScan(this.ctx, uid);
        st.items.sort((x, y) => (y.ts || 0) - (x.ts || 0));
        return Response.json({ ok: true, items: st.items.slice(0, 200), n: st.n, chars: st.chars, cap: { count: KB_COUNT, chars: KB_TOTAL, one: KB_CHARS } });
      }
      if (op === "kbget") {
        if (!ok12(uid)) return Response.json({ ok: false });
        const id = String(b.id || "");
        const meta = await this.ctx.storage.get("ki:" + uid + ":" + id);
        if (!meta) return Response.json({ ok: false, msg: "这一件不在你的知识库里。" });
        const text = await this.ctx.storage.get("kb:" + uid + ":" + id);
        if (typeof text !== "string") return Response.json({ ok: false, msg: "正文取不到了（元数据还在）。" });
        return Response.json({ ok: true, item: meta, text });
      }
      if (op === "kbren") {
        if (!ok12(uid)) return Response.json({ ok: false });
        const id = String(b.id || "");
        const meta = await this.ctx.storage.get("ki:" + uid + ":" + id);
        if (!meta) return Response.json({ ok: false, msg: "这一件不在你的知识库里。" });
        const t2 = moClean(b.title, 80);
        if (!t2) return Response.json({ ok: false, msg: "名字不能空。" });
        meta.title = t2;
        await this.ctx.storage.put("ki:" + uid + ":" + id, meta);
        return Response.json({ ok: true, item: meta });
      }
      if (op === "kbdel") {
        if (!ok12(uid)) return Response.json({ ok: false });
        const id = String(b.id || "");
        const meta = await this.ctx.storage.get("ki:" + uid + ":" + id);
        if (!meta) return Response.json({ ok: false, msg: "已经不在了。" });
        await this.ctx.storage.delete("kb:" + uid + ":" + id);
        await this.ctx.storage.delete("ki:" + uid + ":" + id);
        return Response.json({ ok: true });
      }
      if (op === "cdpost") {'''
    h = h.replace(ANCHOR, KB, 1)
    print("✔ 后端 kb 五个 op 已插入")

# 路由白名单：/api/im 的 op 分发（照 lb 那一块写一块 kb）
ROUTE_ANCHOR = '''      if (op === "cd") {   // 候选卡与顶回'''
if 'op === "kb"' in h:
    print("· 路由已有 kb，跳过")
else:
    assert ROUTE_ANCHOR in h, "找不到 cd 路由锚点"
    assert h.count(ROUTE_ANCHOR) == 1, "cd 路由锚点不唯一"
    ROUTE = '''      if (op === "kb") {   // 个人知识库：只有本人能看、能改、能删
        const a = String(b.a || "");
        const pass = ["add", "mine", "get", "ren", "del"];
        if (pass.indexOf(a) < 0) return Response.json({ ok: false, msg: "未知的知识库动作。" }, { status: 400 });
        await call({ op: "hello", uid: who.uid, name: who.name });
        const d = await call({
          op: "kb" + a, uid: who.uid, name: who.name,
          id: String(b.id || ""), title: b.title, kind: b.kind, text: b.text,
          from: b.from, pid: b.pid, ver: b.ver,
        });
        return Response.json(Object.assign({ me }, d || { ok: false }), { headers: { "cache-control": "no-store" } });
      }
      if (op === "cd") {   // 候选卡与顶回'''
    h = h.replace(ROUTE_ANCHOR, ROUTE, 1)
    print("✔ 路由 kb 已插入")

if h == orig:
    print("无改动（已是最新）")
else:
    io.open(P, "w", encoding="utf-8").write(h)
    print("%d → %d 字符" % (len(orig), len(h)))
