#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 tools/sim_wds_mode_v2.js 修回能响的状态（幂等）

现状（2026-08-15 排 ChatSDE 空答时顺手撞见）：这套护栏在 HEAD 上就红 14 条并在
第 1305 行崩溃 —— **一套读不出来的护栏比没有护栏更坏**，因为它把真红也一起淹了。
逐条查下来，红的没有一条是产品坏了，全是护栏没跟上 08-12 下午那三次真实改法：

  ① 成文菜单加了第十档「凝成两万字论文 · 一趟写完」(paper1)，且「一万字」已改名两万字；
  ② 关闭面板从「直接绑 onclick」改成**事件委托**（顶栏被心跳重建后 onclick 那版会失灵，
     这是对的改法）——而桩的 click() 只调 this.onclick、也没有 closest()，于是关不掉；
     面板关不掉 ⇒ 后面 ⑱⑲⑳㉑ 全部读到上一轮留下的那块面板 ⇒ 级联假红；
  ③ 一万字论文从「拟题一趟＋每节一趟」改成**默认单趟**（dc7dffa），护栏还钉着分节的结局。

所以这里改的是**桩的能力**与**过期的现实**，一条断言的严格程度都没有放松。
"""
import pathlib

P = pathlib.Path(__file__).resolve().parents[1] / "tools" / "sim_wds_mode_v2.js"
s = P.read_text(encoding="utf-8")
done = []


def rep(old, new, tag):
    global s
    if new in s:
        print("  · 已在位：" + tag); return
    assert s.count(old) == 1, "锚点 %s 命中 %d 次" % (tag, s.count(old))
    s = s.replace(old, new); done.append(tag); print("  ✎ " + tag)


# ── ① 桩补 closest()：事件委托靠它认按钮 ──────────────────────────────
rep("""  contains(n) { if (n === this) return true; return this.children.some((c) => c.contains(n)); }""",
    """  contains(n) { if (n === this) return true; return this.children.some((c) => c.contains(n)); }
  // 事件委托（tg.closest(".dx")）要它。产品从「直接绑 onclick」改成委托是对的
  // （顶栏被心跳重建后 onclick 那一版会失灵），桩得跟上，不能靠改断言绕过去。
  closest(sel) { let n = this; while (n) { if (n._match && n._match(sel)) return n; n = n.parentNode; } return null; }""",
    "桩：Node.closest()")

# ── ② 桩的 click 要冒泡：委托的监听器挂在祖先节点上 ────────────────────
rep("""  click() { if (this.onclick) this.onclick({ currentTarget: this, target: this }); }""",
    """  click() {
    // 真浏览器里点一颗按钮，事件会一路冒到祖先——委托就是靠这个。
    // 旧桩只调自己的 onclick，于是"挂在遮罩上的那颗逃生钮"永远点不动。
    if (this.onclick) this.onclick({ currentTarget: this, target: this });
    let n = this;
    while (n) {
      const ls = (n._listeners && n._listeners.click) || [];
      ls.slice().forEach((f) => f({ currentTarget: n, target: this }));
      n = n.parentNode;
    }
  }""",
    "桩：click 沿父链冒泡")

# ── ③ 菜单：第十档 ＋ 改名 ＋ PDF 判据收紧 ─────────────────────────────
rep("""  ok(menu.children.length === 9, "菜单九项（报告/成文/一万字/提纲/总结文章/对外PPT/导出/选目录/成文记录），实得 " + menu.children.length);
  ok(menu.textContent.indexOf("一万字") >= 0, "一万字论文那一档在菜单里");
  ok(menu.textContent.indexOf("总结载入的文章") >= 0, "总结全文那一档在菜单里");
  ok(menu.textContent.indexOf("PDF") < 0, "PDF 不在成文菜单里（它在顶栏）");""",
    """  // 2026-08-12 再加第七档「两万字论文 · 一趟写完」（paper1，默认该选的那一个，
  //   分十六趟那一档留着做对照）→ 十项；同时「一万字」全线改名「两万字」。
  ok(menu.children.length === 10, "菜单十项（报告/成文/两万字一趟/两万字十六趟/提纲/总结文章/对外PPT/导出/选目录/成文记录），实得 " + menu.children.length);
  ok(menu.textContent.indexOf("两万字") >= 0, "两万字论文那一档在菜单里");
  ok(/一趟写完|single pass/.test(menu.textContent) && /十六趟|sixteen passes/.test(menu.textContent),
    "一趟与十六趟两档并列（单趟是默认，十六趟作对照）");
  ok(menu.textContent.indexOf("总结载入的文章") >= 0, "总结全文那一档在菜单里");
  // ⚠ 判据只看**档名**：两万字那两档的副标题里本就写着「出 Word 与 PDF」，
  //   拿整段文本找 "PDF" 会把它们误判成"PDF 导出档回到菜单里了"。要挡的是那一档本身。
  ok(![].slice.call(menu.children).some((b) => /^[^\\n]*PDF/.test(String(b.textContent || "").split("·")[0])
      && /导出|Export/.test(String(b.textContent || ""))),
    "PDF 导出档不在成文菜单里（它在顶栏那颗独立按钮上）");""",
    "菜单：十项／两万字／PDF 判据只看档名")

P.write_text(s, encoding="utf-8")
print("\n改了 %d 处" % len(done))

# ── ④ 四条源码级正则过期（产品长出新条件，行为没变，正则却对不上了） ────────
s = P.read_text(encoding="utf-8")
done = []

rep("""  ok(/var _shown = String\\(out\\.textContent[\\s\\S]{0,140}if \\(text && !_shown\\) \\{\\s*out\\.textContent = text;/.test(_dn),""",
    """  // 白屏自检后来加到三种量法，中间那段长过 140 字 ⇒ 放宽到 320，但仍钉住
  // 「先算 _shown、再据它退回纯文本」这个次序（把自检删掉照样当场红）。
  ok(/var _shown = String\\(out\\.textContent[\\s\\S]{0,320}if \\(text && !_shown\\) \\{\\s*out\\.textContent = text;/.test(_dn),""",
    "㉑：白屏自检正则放宽到 320（次序仍钉死）")

rep("""  ok(/setTimeout\\(function \\(\\) \\{[\\s\\S]{0,220}try \\{ if \\(text && text\\.length <= 40000\\) autoLink/.test(_dn), "autoLink/deckPrep 挪出同一个任务，正文先上屏");""",
    """  // 后来又加了「正文里没有书名号就整段跳过」这个前置条件 ⇒ 条件段放开，
  //   但 autoLink 必须仍在 setTimeout 里（挪回同一个任务当场红）。
  ok(/setTimeout\\(function \\(\\) \\{[\\s\\S]{0,260}try \\{ if \\(text && text\\.length <= 40000[^)]*\\) autoLink/.test(_dn), "autoLink/deckPrep 挪出同一个任务，正文先上屏");""",
    "㉑：autoLink 正则容得下新增的前置条件")

rep("""  ok(/if \\(j\\.t === "token"\\) \\{ text \\+= j\\.v;[^\\n]*paintD\\(false\\)/.test(_ds), "改成调增量渲染器 paintD");""",
    """  // 单趟档（paper1）进来之后这一支拆成了多行、并多了 !oneShot 这道闸
  //   （一趟出全篇时中途一个字都不排）。判据改成跨行找，但 paintD(false) 必须还在。
  ok(/if \\(j\\.t === "token"\\) \\{[\\s\\S]{0,400}text \\+= j\\.v;[\\s\\S]{0,400}paintD\\(false\\)/.test(_ds), "改成调增量渲染器 paintD");
  ok(/!oneShot && Date\\.now\\(\\) - lastP > paintGap/.test(_ds), "一趟出全篇那一档中途不排版（排版全推到收尾那一次）");""",
    "㉑：paintD 正则跨行 ＋ 补钉单趟不排版")

rep("""  ok(/if \\(!fenceOdd && !mathOdd && next && !\\/\\^\\(\\[-\\*\\+>\\|\\]\\|\\\\d\\+\\[\\.\\)\\]\\)\\//.test(_ds),""",
    """  // 后来又允许「下一行是新的一节标题」也当安全切口（_isSec）⇒ 中间放开，
  //   围栏/公式成对与列表行不许切这两条仍钉死。
  ok(/if \\(!fenceOdd && !mathOdd && next && [\\s\\S]{0,40}\\/\\^\\(\\[-\\*\\+>\\|\\]\\|\\\\d\\+\\[\\.\\)\\]\\)\\//.test(_ds),""",
    "㉑：安全切口正则容得下 _isSec")

# ── ⑤ ㉒ 分节那一节：按档名点，别再按序号 ───────────────────────────────
rep("""  document.body.querySelector(".wdsm-menu").children[2].click();     // 第三档＝凝成一万字论文""",
    """  /* ⚠ 2026-08-12 菜单里多了「两万字 · 一趟写完」，它排在分十六趟那一档**前面**——
     再按 children[2] 点到的就是单趟档，于是这一节整段读成"只跑了一趟"。
     按档名点（这套护栏自己在⑨那里就写过这条规矩，这里当初没照做）。 */
  [].slice.call(document.body.querySelector(".wdsm-menu").children)
    .filter((b) => /十六趟|sixteen passes/.test(String(b.textContent || "")))[0].click();""",
    "㉒：分节档按档名点，不按序号")

# ── ⑥ 顺手还掉写死沙盒路径这笔旧债（换棵工作树就整套假红） ─────────────
n = s.count('"/home/claude/site/')
if n:
    s = s.replace('"/home/claude/site/', 'SITE + "/')
    if "const SITE = " not in s:
        s = s.replace('const fs = require("fs");',
                      'const fs = require("fs");\n// 不写死沙盒路径：换棵工作树跑就会整套假红（这套护栏历史上栽过一次）\nconst SITE = require("path").join(__dirname, "..");', 1)
    done.append("还债：%d 处写死路径改成 __dirname" % n)
    print("  ✎ 还债：%d 处写死沙盒路径" % n)

P.write_text(s, encoding="utf-8")
print("\n第二轮改了 %d 处" % len(done))

# ── ⑦ ㉒ 的桩：每节要写足到过得了「这一节算不算写出来了」那道下限 ──────────
s = P.read_text(encoding="utf-8"); done = []
_o = '''  ROUTE["/api/wds/distill"] = function (p) {
    LEGS.push({ stage: p.stage || "", idx: p.idx, hasPlan: !!(p.plan && p.plan.sections), tail: String(p.prevTail || "") });
    if (p.stage === "plan") return [{ t: "plan", v: PLAN }];
    if (p.stage === "part") return [{ t: "token", v: "## 第 " + (p.idx + 1) + " 节\\n\\n这一节的正文。" }];'''
_n = '''  ROUTE["/api/wds/distill"] = function (p) {
    LEGS.push({ stage: p.stage || "", idx: p.idx, hasPlan: !!(p.plan && p.plan.sections), tail: String(p.prevTail || "") });
    if (p.stage === "plan") return [{ t: "plan", v: PLAN }];
    /* ⚠ 每节必须写足：产品判「这一节写出来没有」的下限是 max(260, 目标字数×0.4)
       ＝这里的 480 字。桩里只回一句话 ⇒ 每节都判没写出来 ⇒ 退避二十秒重来一遍，
       四秒内只跑得完两趟，读起来像"产线跑一节就停了"。**假红就是这么来的。** */
    if (p.stage === "part") return [{ t: "token", v: "## 第 " + (p.idx + 1) + " 节\\n\\n" + "这一节的正文写足到过得了下限。".repeat(40) }];'''
rep(_o, _n, "㉒：桩里每节写足过下限")
P.write_text(s, encoding="utf-8")
print("\n第三轮改了 %d 处" % len(done))

# ── ⑧ 同样两处毛病还散在后面几节里：按序号点 ＋ 每节写不足 ──────────────
s = P.read_text(encoding="utf-8"); done = []
PICK = '''[].slice.call(document.body.querySelector(".wdsm-menu").children)
    .filter((b) => /十六趟|sixteen passes/.test(String(b.textContent || "")))[0].click();'''
n1 = s.count('document.body.querySelector(".wdsm-menu").children[2].click();')
if n1:
    s = s.replace('document.body.querySelector(".wdsm-menu").children[2].click();', PICK)
    print("  ✎ 余下 %d 处「按序号点第三档」改成按档名点" % n1); done.append("children[2]")
LONG = '"## 第 " + (p.idx + 1) + " 节\\\\n\\\\n" + "这一节的正文写足到过得了下限。".repeat(40)'
n2 = s.count('"## 第 " + (p.idx + 1) + " 节\\\\n\\\\n这一节的正文。"')
if n2:
    s = s.replace('"## 第 " + (p.idx + 1) + " 节\\\\n\\\\n这一节的正文。"', LONG)
    print("  ✎ 余下 %d 处「每节只回一句话」写足到过下限" % n2); done.append("short-part")
n3 = s.count('"这一节的正文。".repeat(20)')
if n3:
    s = s.replace('"这一节的正文。".repeat(20)', '"这一节的正文写足到过得了下限。".repeat(40)')
    print("  ✎ 余下 %d 处 repeat(20)（140 字，仍在 480 的下限之下）" % n3); done.append("repeat20")
P.write_text(s, encoding="utf-8")
print("\n第四轮改了 %d 类" % len(done))
