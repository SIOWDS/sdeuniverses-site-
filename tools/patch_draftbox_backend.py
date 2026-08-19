#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""草稿箱（画布 → SDE 浏览的管理系统）后端。幂等可复跑。

用户口径：「可以做成『草稿箱投稿』，放在 SDE 浏览的『管理系统』里面，
**不对外开放，只给我和你**。」

⇒ 两道门，各自配它的用户，**共用同一个箱子**：
  · 门一（给王德生）：社区身份（名字＋密码，全站唯一那一套）＋ `isAdminName` 服务端名单。
    不另设口令——社区登录本来就已经要名字和密码了，再加一道只会让"投一稿"变得麻烦。
  · 门二（给 Claude）：`DRAFT_KEY` 常量，**只在 src/worker.js 里，永不进 public/**。
    与 SDE2013 的区别要认清：那是**前端级**口令（公开页面里就有），
    所以它的能力被刻意收窄到"只能加不能删"；这一把不在前端，才敢给读和删。

存储照抄 kbadd 那一套（同一个 DO、同样的键分家）：
  `dri:<id>` ＝元数据、`drf:<id>` ＝正文。分开存的理由同 kb：
  列表不该把几十件两万字的稿子一起拖回来。
  **但键上不带 uid** —— 草稿箱是"我和你"共用的一个箱子，不是每人一个。
"""
import io, re

P = "src/worker.js"
h = io.open(P, encoding="utf-8").read()
orig = h
done = []


def rep(old, new, tag, probe, cnt=1):
    global h
    if probe in h:
        print("  · %s 已在，跳过" % tag); return
    assert old in h, "锚点找不到：" + tag
    assert h.count(old) == cnt, "锚点不唯一（%d 处）：%s" % (h.count(old), tag)
    h = h.replace(old, new, 1); done.append(tag); print("  ✔ %s" % tag)


# ── 1. 常量与扫描助手（放在 kb 的常量旁边）──────────────────
KBC = re.search(r'const KB_CHARS = \d+[^\n]*\n', h)
assert KBC, "找不到 KB_CHARS"
rep(
    KBC.group(0),
    KBC.group(0) + '''/* ── 草稿箱：画布 → 管理系统。不对外开放。 ──────────────────
   `DRAFT_KEY` 只在本文件里，**绝不写进 public/**（写进去它就退化成前端级口令，
   那时就只能像 SDE2013 那样把能力收窄到"只能加不能删"了）。 */
const DRAFT_KEY = "sde-draft-2026-wds-claude";
const DR_CHARS = 60000;        // 单件上限
const DR_COUNT = 300;          // 件数上限
const DR_TOTAL = 4000000;      // 合计上限
async function drScan(ctx) {
  const m = await ctx.storage.list({ prefix: "dri:" });
  const items = []; let chars = 0;
  m.forEach((v) => { if (v && v.id) { items.push(v); chars += (v.chars || 0); } });
  return { items, n: items.length, chars };
}
''',
    "① 草稿箱常量与扫描助手", "const DRAFT_KEY =",
)

# ── 2. DO 四个 op（插在 kbadd 之前）──────────────────────────
rep(
    '''      if (op === "kbadd") {''',
    '''      /* ── 草稿箱 ──────────────────────────────────────────
         与知识库的分别：知识库是**每人私有**（键带 uid），草稿箱是**我和你共用一个箱子**
         （键不带 uid，但元数据记下是谁投的）。门在路由层，这里不再判身份。 */
      if (op === "drfadd") {
        const text = String(b.text == null ? "" : b.text);
        const title = moClean(b.title, 120) || "未命名草稿";
        if (text.trim().length < 20) return Response.json({ ok: false, msg: "太短了——草稿箱装的是要发出去的稿子。" });
        if (text.length > DR_CHARS) return Response.json({ ok: false, msg: "这一件 " + text.length + " 字，超过单件上限 " + DR_CHARS + " 字。请先拆开。" });
        const st = await drScan(this.ctx);
        if (st.n >= DR_COUNT) return Response.json({ ok: false, msg: "草稿箱已有 " + st.n + " 件，到上限了。先清掉几件。" });
        if (st.chars + text.length > DR_TOTAL) return Response.json({ ok: false, msg: "草稿箱合计已 " + st.chars + " 字，再投这一件会超上限。" });
        // 同题同文不再多存一件（画布上重复点是常事，与 kbadd 同口径）
        for (const it0 of st.items) {
          if (it0.title === title && it0.chars === text.length) {
            const old = await this.ctx.storage.get("drf:" + it0.id);
            if (old === text) return Response.json({ ok: true, dup: 1, item: it0 });
          }
        }
        const id = moInv(now) + ":" + moRnd();
        const meta = {
          id, title, kind: moClean(b.kind, 20) || "md", chars: text.length, ts: now,
          by: moClean(b.name, 40), from: moClean(b.from, 60), ver: parseInt(b.ver || 0, 10) || 0,
          note: moClean(b.note, 400), state: "new"
        };
        await this.ctx.storage.put("drf:" + id, text);
        await this.ctx.storage.put("dri:" + id, meta);
        return Response.json({ ok: true, item: meta, left: DR_COUNT - st.n - 1 });
      }
      if (op === "drflist") {
        const st = await drScan(this.ctx);
        st.items.sort((x, y) => (y.ts || 0) - (x.ts || 0));
        return Response.json({ ok: true, items: st.items.slice(0, 300), n: st.n, chars: st.chars,
          cap: { count: DR_COUNT, chars: DR_TOTAL, one: DR_CHARS } });
      }
      if (op === "drfget") {
        const id = String(b.id || "");
        const meta = await this.ctx.storage.get("dri:" + id);
        if (!meta) return Response.json({ ok: false, msg: "这一件不在草稿箱里。" });
        const text = await this.ctx.storage.get("drf:" + id);
        if (typeof text !== "string") return Response.json({ ok: false, msg: "正文取不到了（元数据还在）。" });
        return Response.json({ ok: true, item: meta, text });
      }
      if (op === "drfdel") {
        const id = String(b.id || "");
        const meta = await this.ctx.storage.get("dri:" + id);
        if (!meta) return Response.json({ ok: false, msg: "这一件不在草稿箱里。" });
        await this.ctx.storage.delete("drf:" + id);
        await this.ctx.storage.delete("dri:" + id);
        return Response.json({ ok: true, id });
      }
      if (op === "drfmark") {          // 改状态：new / doing / done
        const id = String(b.id || "");
        const meta = await this.ctx.storage.get("dri:" + id);
        if (!meta) return Response.json({ ok: false, msg: "这一件不在草稿箱里。" });
        const s = String(b.state || "");
        if (["new", "doing", "done"].indexOf(s) < 0) return Response.json({ ok: false, msg: "未知状态。" });
        meta.state = s;
        await this.ctx.storage.put("dri:" + id, meta);
        return Response.json({ ok: true, item: meta });
      }
      if (op === "kbadd") {''',
    "② DO 五个 op（增删查列改状态）", 'if (op === "drfadd")',
)

# ── 3. 门一：/api/im op:"dr"，管理员名单把门 ───────────────
rep(
    '''      if (op === "kb") {   // 个人知识库：只有本人能看、能改、能删''',
    '''      /* 草稿箱：**不对外开放**。门＝服务端管理员名单（`isAdminName`），
         不另设口令——社区登录本来就要名字＋密码了，再加一道只会让"投一稿"变麻烦。
         不在名单里的人拿到的是一句人话，不是 404（假装不存在只会让人反复试）。 */
      if (op === "dr") {
        if (!isAdminName(who.name)) {
          return Response.json({ ok: false, msg: "草稿箱不对外开放。要投稿请走「学员投稿」。" }, { status: 403 });
        }
        const a = String(b.a || "");
        const pass = ["add", "list", "get", "del", "mark"];
        if (pass.indexOf(a) < 0) return Response.json({ ok: false, msg: "未知的草稿箱动作。" }, { status: 400 });
        const d = await call({
          op: "drf" + a, uid: who.uid, name: who.name,
          id: String(b.id || ""), title: b.title, kind: b.kind, text: b.text,
          from: b.from, ver: b.ver, note: b.note, state: b.state,
        });
        return Response.json(Object.assign({ me }, d || { ok: false }), { headers: { "cache-control": "no-store" } });
      }
      if (op === "kb") {   // 个人知识库：只有本人能看、能改、能删''',
    "③ 门一：/api/im op:dr（管理员名单把门）", 'if (op === "dr") {',
)

# ── 4. 门二：/api/admin/draft，服务端钥匙 ─────────────────────
rep(
    '''    if (url.pathname === "/api/admin/r2-migrate" && request.method === "POST") {''',
    '''    /* 门二：给 Claude 的。钥匙只在本文件里、不在 public/ ——
       所以它敢给读和删（SDE2013 那三个口子不敢，因为那是前端级口令）。 */
    if (url.pathname === "/api/admin/draft" && request.method === "POST") {
      /* ⚠ `J` 在这份文件里是**每个路由块各自定义的局部函数**，不是全局的。
         直接用会是运行时 ReferenceError，而 `node --check` 抓不到这类错。
         凡在 worker.js 里新开路由，先确认用到的助手是不是本块自己的。 */
      const J = (o, st) => Response.json(o, { status: st || 200, headers: _cors() });
      const b = await request.json().catch(() => null);
      if (!b) return J({ ok: false, msg: "请求格式不对。" }, 400);
      if (String(b.key || "") !== DRAFT_KEY) return J({ ok: false, msg: "钥匙不对。" }, 401);
      const a = String(b.a || "");
      if (["add", "list", "get", "del", "mark"].indexOf(a) < 0) return J({ ok: false, msg: "未知动作。" }, 400);
      const dir2 = env.COMMENTS.get(env.COMMENTS.idFromName("im-dir-global"));
      const r = await dir2.fetch(new Request("https://do/_dir", {
        method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({
          op: "drf" + a, name: "Claude",
          id: String(b.id || ""), title: b.title, kind: b.kind, text: b.text,
          from: b.from || "Claude", ver: b.ver, note: b.note, state: b.state,
        })
      }));
      const d = await r.json().catch(() => ({ ok: false }));
      return J(d || { ok: false });
    }
    if (url.pathname === "/api/admin/r2-migrate" && request.method === "POST") {''',
    "④ 门二：/api/admin/draft（服务端钥匙）", '/api/admin/draft',
)

assert h != orig, "一处都没改"
io.open(P, "w", encoding="utf-8").write(h)
print("\n共 %d 处改动，%d → %d 字符" % (len(done), len(orig), len(h)))
