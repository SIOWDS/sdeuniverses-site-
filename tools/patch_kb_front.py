#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""个人知识库 —— 前端三处。幂等可复跑。

  ① `sde-vault.js` 加 `kb()`：入库纪律**只写在模块里**（与 auto/fav 同住），
     各页各写一遍等于把同一条纪律抄三份，改一处必漏两处。
  ② 画布工具条加「⇧ 存进知识库」：未登录**不偷偷存**，给可点的去处。
  ③ 社区页「我」→「📦 我的知识库」新视图 v-kb：列表 / 打开 / 改名 / 删除 / 下载。
"""
import io, re

done = []


def patch(path, edits):
    h = io.open(path, encoding="utf-8").read()
    orig = h
    for old, new, tag, probe in edits:
        if probe in h:
            print("  · %s 已在，跳过" % tag); continue
        assert old in h, "锚点找不到：%s（%s）" % (tag, path)
        assert h.count(old) == 1, "锚点不唯一（%d 处）：%s" % (h.count(old), tag)
        h = h.replace(old, new, 1); done.append(tag); print("  ✔ %s" % tag)
    if h != orig:
        io.open(path, "w", encoding="utf-8").write(h)
        print("    → %s  %d → %d" % (path, len(orig), len(h)))


# ══ ① 共享模块 ══════════════════════════════════════════════
patch("public/taste/assets/sde-vault.js", [(
    '''  w.SDEVault = { auto: auto, fav: fav, head: head, lead: lead, cred: cred, KINDS: KINDS };''',
    '''  /* ── 个人知识库入库 ──────────────────────────────────
     与 auto()/fav() 同住这一个模块，为的是**共用同一把身份与同四条纪律**。
     它和另外两个的分工别混：
       auto → 思想库存（一句话，200 字上限，全站共用一池）
       fav  → 文章库（站内篇目的指针，只存 slug＋题名）
       kb   → 知识库（**本人产出的成品文档**，画布上那些东西）
     ⚠ 纪律②在这里尤其要守：未登录**不偷偷存**——知识库是私人的，
       没有身份就没有"谁的"，存进去也取不回来。 */
  var KB_KINDS = { md: 1, html: 1, svg: 1, mermaid: 1, csv: 1, json: 1, code: 1, note: 1 };
  function kb(o, box) {
    o = o || {};
    var text = String(o.text == null ? "" : o.text);
    var title = String(o.title || "").trim().slice(0, 80) || "未命名";
    var kind = KB_KINDS[String(o.kind || "")] ? String(o.kind) : "note";
    if (text.trim().length < 20) {
      note(box, "太短了——知识库装的是成品，一两句话请存进「💡 思想库存」。");
      return Promise.resolve({ ok: false });
    }
    var c = cred();
    if (!c) {
      note(box, '还没存——知识库是你私人的，得先有身份。'
        + '先在 <a href="/sde-wechat/" target="_blank">SDE 社区</a> 用名字和密码登录一次（全站通用），'
        + '之后画布上的东西按一下就进「📦 我的知识库」，换台机器也还在。');
      return Promise.resolve({ ok: false, noAuth: 1 });
    }
    note(box, "正在存进知识库…");
    return fetch("/api/im", {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({
        credential: c, op: "kb", a: "add",
        title: title, kind: kind, text: text,
        from: String(o.from || "").slice(0, 60), pid: String(o.pid || "").slice(0, 40),
        ver: o.ver || 0
      })
    }).then(function (r) { return r.json(); }).then(function (d) {
      var x = (d && d.d) ? d.d : d;                 // 与 /api/im 的信封对齐（页面层那次栽过）
      if (x && x.ok) {
        note(box, (x.dup ? "这一件已经在知识库里了（同题同文）。" : "已存进知识库。")
          + ' <a href="/sde-wechat/" target="_blank">去看看 →</a>');
      } else {
        note(box, (x && x.msg) ? x.msg : "没存上——不拦路，你还可以用「存到本机」。");
      }
      return x || { ok: false };
    }, function () {
      /* 纪律④：失败不拦路，但要如实说，不许假装存过了 */
      note(box, "没存上（网络或登录过期）——不拦路，你还可以用「存到本机」。");
      return { ok: false };
    });
  }

  w.SDEVault = { auto: auto, fav: fav, kb: kb, head: head, lead: lead, cred: cred, KINDS: KINDS, KB_KINDS: KB_KINDS };''',
    "① sde-vault 加 kb()", "function kb(o, box)",
)])

# ══ ② 画布出口 ══════════════════════════════════════════════
patch("public/wds-mode.js", [
    (
        '''      cvEdit: "✎ 编辑",''',
        '''      cvKb: "⇧ 存进知识库", cvKbT: "存进你在 SDE 社区的私人知识库（要名字和密码），换台机器也还在",
      cvEdit: "✎ 编辑",''',
        "② 中文文案", 'cvKb: "⇧ 存进知识库"',
    ),
    (
        '''      cvEdit: "\\u270e Edit",''',
        '''      cvKb: "\\u21e7 To my library", cvKbT: "Save into your private library in the SDE Community (needs your name and password)",
      cvEdit: "\\u270e Edit",''',
        "③ 英文文案", 'cvKb: "\\u21e7 To my library"',
    ),
    (
        '''    mk(tx("cvEdit"), function () { cvEditOn(it); }, CV.edit).title = tx("cvEditT");''',
        '''    /* 存进个人知识库。**画布此前只有本机出口**（localStorage / 下载 / 存到本机目录），
       换台机器就没了；而画布装的正是成品。走 SDEVault.kb —— 身份与纪律都在模块里，
       这里一行都不重写（抄第二遍必漂，且漂得静默）。 */
    var kbb = mk(tx("cvKb"), function () {
      if (!window.SDEVault || typeof SDEVault.kb !== "function") { cvNote(tx("cvKbNo")); return; }
      cvGrab();
      SDEVault.kb({
        title: it.title, kind: it.kind, text: cvText(),
        from: "ChatSDE · 画布", ver: it.vi + 1
      }, cvNoteEl());        // ⚠ 必须传**真 DOM 元素**：模块的 note() 是 box.innerHTML=…，
                             //   传个带 _note 的假壳它会静默什么都不做（看着像存成功了）
    });
    kbb.title = tx("cvKbT");
    mk(tx("cvEdit"), function () { cvEditOn(it); }, CV.edit).title = tx("cvEditT");''',
        "④ 画布工具条加「存进知识库」", 'var kbb = mk(tx("cvKb")',
    ),
    (
        '''  function cvOrigin() {''',
        '''  /* 模块的 note(box, html) 做的就是 `box.innerHTML = html`，所以**必须给它真 DOM 元素**。
     这里在画布正文区顶上留一块常驻的回话位，重画时会被清掉、用时再造。 */
  function cvNoteEl() {
    var box = cvWrapEl && cvWrapEl.querySelector(".wdsm-cvnote2");
    if (box) return box;
    box = el("div", "wdsm-cvnote2");
    box.style.cssText = "color:var(--wgold);font-size:12px;padding:8px 0 10px;line-height:1.7";
    if (cvWrapEl) cvWrapEl.insertBefore(box, cvWrapEl.firstChild);
    return box;
  }
  function cvNote(html) { var b = cvNoteEl(); if (b) b.innerHTML = html; }
  function cvOrigin() {''',
        "⑤ 画布上的回话位", "function cvNoteEl()",
    ),
    (
        '''      cvKb: "⇧ 存进知识库", cvKbT:''',
        '''      cvKbNo: "知识库模块没装载上——不拦路，你还可以用「存到本机」。",
      cvKb: "⇧ 存进知识库", cvKbT:''',
        "⑥ 中文兜底文案", 'cvKbNo: "知识库模块没装载上',
    ),
    (
        '''      cvKb: "\\u21e7 To my library", cvKbT:''',
        '''      cvKbNo: "Library module did not load \\u2014 you can still use Save locally.",
      cvKb: "\\u21e7 To my library", cvKbT:''',
        "⑦ 英文兜底文案", "cvKbNo: \"Library module did not load",
    ),
])

print("\n共 %d 处" % len(done))
