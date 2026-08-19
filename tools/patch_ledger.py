#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""命题账本第一件：给候选卡补 pid / kin / g / src 四个字段，把它升格成账本条目。

口径（用户 2026-07-31 定）：三个子系统＝S/D/E 三个维度，纠缠的最小充分条件是
**三处操作同一个对象**；那个对象只能是承重命题。**不造第五套键空间**——
候选卡本来就几乎是账本了，这里只补标识、血缘、文法与来处。

幂等；所有替换先 assert 锚点；写回一律先 encode 再 wb（io.open(...,"w") 会先截断）。
"""
import sys, io, os

P = os.path.join(os.path.dirname(__file__), "..", "src", "worker.js")
h = io.open(P, encoding="utf-8").read()
n = 0

def rep(old, new, label):
    global h, n
    assert old in h, "锚点没找到：" + label
    assert h.count(old) == 1, "锚点不唯一：" + label
    h = h.replace(old, new, 1)
    n += 1

if "ppGrams" in h:
    print("已经打过这个补丁，跳过。")
    sys.exit(0)

# ── 1. 账本工具（紧接 cdSettle 之后）──
LEDGER = r'''
      /* ═══ 命题账本（ledger）═══
         用户定的口径：三个子系统＝S/D/E 三个维度（浏览＝显露／ChatSDE＝发生／微信＝纠缠），
         而**纠缠的最小充分条件是三处操作同一个对象**。那个对象只能是承重命题——
         50 字级、可被反对的一句：它本来就是 I 维那把刀、近邻库的查询键、候选卡的第一段。

         **不造第五套键空间。** 站上已有四套互不认识的东西（库存 vt: ／候选卡 cd: ／
         近邻库 cards.json ／站内文章 slug），账本不是第五套，是把它们认成同一个对象的
         四个年龄段。候选卡本来就几乎是账本了（prop/face/crit/backs/seps/state/due 全有），
         这里只补四件：
           pid  跨三系统的稳定标识。cd:<inv>:<rnd> 是**存储键**不是标识——换存储、搬家、
                导出再导入，它就没了；而三个系统要指着同一条命题说话。
           kin  血缘：它从哪几条命题分叉/撞出来。**共同创造用分叉，不用共编**——
                一条命题只有一个作者，既免掉自由群体里最伤感情的所有权争议，
                又让"这个想法是怎么来的"自动长成一条可回溯的链。
           g    文法指纹（汉字二元组＋拉丁整词）：距离引擎与零调用粗筛的燃料。
           src  来处 {sys:"S|D|E", at:一句话}——账本要答得出"它是在哪个维度上冒出来的"。

         ⚠️ g 必须与 public/assets/sde-nbr.js 的 grams() **逐字同义**：一端算出的指纹另一端
            要能直接比。近邻库那条线已经栽过一次（Python 报告与 JS 运行时给出两个召回数字，
            根因是两端口径差了三处），所以 tools/sim_ledger.mjs 有一条断言拿同一批输入
            比两端产出的文法集合，改任一端不同步就当场红。

         **不存分数。** 没有赞、没有粉丝数、没有排名字段——自由群体里任何可排序成等级的
            数字都会让所有人朝分高的那个人的语汇靠拢，而语汇距离正是这套系统唯一的稀缺品。
            schema 里不给它位置，比事后约定"我们不做排行榜"可靠得多。 */
      const PP_PUNCT = /[\s，。、；：？！…—－·「」『』《》〈〉""''"'（）()\[\]【】,.;:?!/\\|+*=~`#$%^&_-]+/g;
      const ppGrams = (s) => {
        const low = String(s || "").toLowerCase();
        const out = Object.create(null);
        // 拉丁词必须在「标点换空格」之后、「压掉空白」之前抽：先压空白会把 ego depletion
        // 粘成 egodepletion，外文原题再也整词命中不了（近邻库那条线的护栏当场抓到过）。
        const lat = low.replace(PP_PUNCT, " ").match(/[a-z0-9]{3,}/g) || [];
        for (const w of lat) out[w] = 1;
        const t = low.replace(PP_PUNCT, "");
        const cjk = [];
        for (let i = 0; i < t.length; i++) {
          const c = t.charCodeAt(i);
          if (c >= 0x4e00 && c <= 0x9fff) cjk.push(t.charAt(i));
        }
        for (let i = 0; i < cjk.length - 1; i++) out[cjk[i] + cjk[i + 1]] = 1;
        return Object.keys(out);
      };
      const PP_ID_RE = /^p_[0-9a-z]{6,14}_[0-9a-f]{4}$/;
      const ppId = (t) => "p_" + Number(t || Date.now()).toString(36) + "_" + Math.random().toString(16).slice(2, 6);
      const ppSys = (x) => (["S", "D", "E"].indexOf(String(x || "").toUpperCase()) >= 0 ? String(x).toUpperCase() : "D");
      const ppKin = (x) => (Array.isArray(x) ? x : []).map((v) => String(v || "")).filter((v) => PP_ID_RE.test(v)).slice(0, 8);
      /* 惰性升格：老卡被读到时才补齐，改过才写回——与 cdSettle 同一路数。
         **不做批量迁移**：批量要对 DO 全表扫描、要挑一个没人在写的时刻，
         而惰性升格零风险、自然收敛，且天然幂等。 */
      const ppUp = (c) => {
        if (!c) return false;
        let dirty = false;
        if (!PP_ID_RE.test(String(c.pid || ""))) { c.pid = ppId(c.ts); dirty = true; }
        if (!Array.isArray(c.g) || !c.g.length) { c.g = ppGrams([c.prop, c.face].join(" ")); dirty = true; }
        if (!Array.isArray(c.kin)) { c.kin = []; dirty = true; }
        if (!c.src || typeof c.src !== "object") { c.src = { sys: "E", at: "" }; dirty = true; }
        return dirty;
      };
      /* pid → 存储键 的指针。写指针是幂等的，重复写一次比漏写一次便宜太多。 */
      const ppLink = async (st, c) => { if (c && c.pid && c.id) await st.put("pp:" + c.pid, c.id); };
'''
rep(
    "        c.settled = tnow;\n"
    "        return true;\n"
    "      };\n",
    "        c.settled = tnow;\n"
    "        return true;\n"
    "      };\n" + LEDGER,
    "账本工具",
)

# ── 2. 落卡时就带上四件 ──
rep(
    """        const card = {
          id, uid, name: cdClean(b.name || u0.name, 20), ts: now,""",
    """        const card = {
          id, uid, name: cdClean(b.name || u0.name, 20), ts: now,
          // ── 账本四件（见上面 ppUp 那段的口径）──
          pid: ppId(now),
          src: { sys: ppSys(b.sys), at: cdClean(b.src, 80) },
          kin: ppKin(b.kin),
          g: ppGrams(cdClean(b.prop, 120) + " " + cdClean(b.face, 200)),""",
    "落卡带账本字段",
)
rep(
    """        await this.ctx.storage.put("cd:" + id, card);
        await this.ctx.storage.put("cu:" + uid + ":" + id, 1);
        return Response.json({ ok: true, card });""",
    """        await this.ctx.storage.put("cd:" + id, card);
        await this.ctx.storage.put("cu:" + uid + ":" + id, 1);
        await ppLink(this.ctx.storage, card);
        return Response.json({ ok: true, card });""",
    "落卡写指针",
)

# ── 3. 读到就顺手升格（feed／back／sep 三处）──
rep(
    """          if (cdSettle(c, now)) await this.ctx.storage.put("cd:" + c.id, c);   // 惰性结算
          out.push(c);""",
    """          // 惰性结算 ＋ 惰性升格：两件事各自判，别用短路写在一行（|| 会吃掉第二件）
          let dirty = cdSettle(c, now);
          if (ppUp(c)) { dirty = true; await ppLink(this.ctx.storage, c); }
          if (dirty) await this.ctx.storage.put("cd:" + c.id, c);
          out.push(c);""",
    "feed 惰性升格",
)
rep(
    """        const bid = cdRnd();
        c.backs.push({ bid, uid, name: cdClean(b.name, 20), kind, text: txt, ts: now });
        await this.ctx.storage.put("cd:" + id, c);""",
    """        const bid = cdRnd();
        c.backs.push({ bid, uid, name: cdClean(b.name, 20), kind, text: txt, ts: now });
        if (ppUp(c)) await ppLink(this.ctx.storage, c);
        await this.ctx.storage.put("cd:" + id, c);""",
    "顶回时升格",
)
rep(
    """        c.seps = (c.seps || []).filter((s) => s.to !== to);
        c.seps.push({ to, text: txt, ts: now });
        await this.ctx.storage.put("cd:" + id, c);""",
    """        c.seps = (c.seps || []).filter((s) => s.to !== to);
        c.seps.push({ to, text: txt, ts: now });
        if (ppUp(c)) await ppLink(this.ctx.storage, c);
        await this.ctx.storage.put("cd:" + id, c);""",
    "分离线时升格",
)

# ── 4. 按 pid 取一条命题（三系统共用的那个"指着同一条说话"的动作）──
rep(
    """      if (op === "cddel") {""",
    """      if (op === "ppget") {
        /* 三个维度指着同一条命题说话的唯一入口。老卡没被读到过就还没有 pid——
           这时如实说"不在账本里"，不假装它不存在。 */
        const pid = String(b.pid || "");
        if (!PP_ID_RE.test(pid)) return Response.json({ ok: false, msg: "认不出这个命题号。" });
        const key = await this.ctx.storage.get("pp:" + pid);
        if (!key) return Response.json({ ok: false, msg: "这条命题还不在账本里（老卡要被读到一次才会补上命题号）。" });
        const c = await this.ctx.storage.get("cd:" + key);
        if (!c) return Response.json({ ok: false, msg: "这条命题已经不在了。" });
        let dirty = cdSettle(c, now);
        if (ppUp(c)) { dirty = true; await ppLink(this.ctx.storage, c); }
        if (dirty) await this.ctx.storage.put("cd:" + key, c);
        return Response.json({ ok: true, card: c });
      }
      if (op === "cddel") {""",
    "ppget",
)

# ── 5. 外层路由：cd 转发新字段 ＋ 新增 pp 族 ──
rep(
    """          text: b.text, prop: b.prop, face: b.face, crit: b.crit, nbr: b.nbr, picks: b.picks,
        });""",
    """          text: b.text, prop: b.prop, face: b.face, crit: b.crit, nbr: b.nbr, picks: b.picks,
          sys: b.sys, src: b.src, kin: b.kin,          // 账本：来处与血缘
        });""",
    "cd 路由转发",
)
rep(
    """      if (op === "mo") {
        const a = String(b.a || "");""",
    """      if (op === "pp") {   // 命题账本：三个维度指着同一条命题说话
        const a = String(b.a || "");
        const pass = ["get"];
        if (pass.indexOf(a) < 0) return Response.json({ ok: false, msg: "未知的账本动作。" }, { status: 400 });
        const d = await call({ op: "pp" + a, uid: who.uid, name: who.name, pid: String(b.pid || "") });
        return Response.json(Object.assign({ me }, d || { ok: false }), { headers: { "cache-control": "no-store" } });
      }
      if (op === "mo") {
        const a = String(b.a || "");""",
    "pp 路由",
)

io.open(P, "wb").write(h.encode("utf-8"))
print("已改 %d 处 → %s" % (n, os.path.relpath(P)))
