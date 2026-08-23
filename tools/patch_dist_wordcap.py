#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""成文超字数三刀（2026-08-23）· 幂等

病灶（三篇真跑坐实）：散文 5052/5000 准；论说 4396/3000 超 47%；小说 4620/2400 超 93%。
  ① distWordGate 只有下限没有上限——「不到 N 字就是没写完，回去补」，一个方向施压。
  ② 选了字数档只改了 SPEC.words / SPEC.fixed，**SPEC.name 与 SPEC.spec 里写死的数一个字没动**，
     而这两处都进提示语（name 进 user 的「现在开始产出「…」」，spec 进 system 的【本次任务】）。
  ③ story 的 spec 自己写着「约 2400 字，可到 4000 字」，把上限放宽 1.67 倍。
  ④ essay 无 fixed、tok 硬底 32000（≈一万汉字），而目标只有 3000——预算是天花板，基底往天花板写。

⚠ 幂等判据一律选**独一无二**的串（2026-08-23 zhiwen 那次栽在同形文本上）。
"""
import io, re, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "src", "worker.js")
h = io.open(P, encoding="utf-8").read()
orig = h
done = []

# ── 刀一：字数闸补上限 ────────────────────────────────────────
OLD_GATE = '''  let s = "\\n\\n【字数闸 · 这是合同不是建议】" + (N > 1 ? "本趟" : "全篇") + "至少写满 " + floor + " 字才允许收尾（目标 " + w + " 字）。";'''
NEW_GATE = '''  const cap = Math.round(w * 1.15);
  let s = "\\n\\n【字数闸 · 这是合同不是建议】" + (N > 1 ? "本趟" : "全篇") + "的合格区间是 " + floor + "\\u2013" + cap
    + " 字（目标 " + w + " 字）：至少写满 " + floor + " 字才允许收尾，写过 " + cap + " 字就是超标。";'''
if NEW_GATE.split("\n")[0] in h:
    done.append("刀一 已在")
else:
    assert OLD_GATE in h, "刀一锚点没找到"
    h = h.replace(OLD_GATE, NEW_GATE, 1)
    done.append("刀一 上限句已加")

OLD_TAIL = '''  s += "字数不够时回去补一个例子、一段余波、一次冲突、一个具体的人——"
    + "⛔ 不许把说过的话换个说法再说一遍来凑，也不许靠拉长句子与堆形容词凑。"
    + "**交稿前自己数一遍：不到 " + floor + " 字就是没写完，回去补，不要交。**";'''
NEW_TAIL = '''  s += "字数不够时回去补一个例子、一段余波、一次冲突、一个具体的人——"
    + "\\u26d4 不许把说过的话换个说法再说一遍来凑，也不许靠拉长句子与堆形容词凑。";
  /* 【超了和欠了一样是没写好】上限这一半是 2026-08-23 补的：三篇真跑 4396/3000、4620/2400，
     而闸从头到尾只说「不到就回去补」。⚠ 减字的方向必须写死——不写清就会去删例子与细节
     （那正是全篇最结实的部分），超出的那一截几乎总是解释、过渡与复述上文。 */
  s += "**超了和不够一样是没写好**：多出来的那一截一定是铺陈、复述上文、可删的形容与排比，"
    + "回去删到 " + cap + " 字以内——\\u26d4 不许靠删例子、删细节、删具体的人来减字，先删你自己的解释与过渡。";
  s += "**交稿前自己数一遍：不到 " + floor + " 字是没写完，超过 " + cap + " 字是没写紧，两头都要回去改，不要交。**";'''
if "超了和不够一样是没写好" in h:
    done.append("刀一尾 已在")
else:
    assert OLD_TAIL in h, "刀一尾锚点没找到"
    h = h.replace(OLD_TAIL, NEW_TAIL, 1)
    done.append("刀一尾 减字方向已写死")

# ── 刀二之一：新增 distFitCopy ────────────────────────────────
ANCHOR_FN = '''/* 字数闸：与 ChatJohn 的 X2 闸同源（见 johnComposeSys）。'''
FIT_FN = '''/* 【选了体量，规格文案也得跟着改口】(2026-08-23)
   档次表上线那一刀只改了 SPEC.words 与 SPEC.fixed，而 **SPEC.name 与 SPEC.spec 里写死的字数一个字没动**——
   这两处都进提示语：name 进 user 那句「现在开始产出「…」」，spec 进 system 的【本次任务】。
   于是读者选 1500 字的公众号，提示语里仍写着「公众号文章（3000字）」：两个数打架，基底一律按大的写。
   ⚠ 不对 spec 正文做正则改写——那里的数字含义各异（比例、节数、年份），**误伤比漏改贵得多**。
   只做两件确定的事：① name 括号里的字数按选中的体量改写；② 追加一条覆盖句，宣告以哪个数为准。 */
function distFitCopy(SPEC, w) {
  if (!SPEC || !w) return;
  if (typeof SPEC.name === "string") SPEC.name = SPEC.name.replace(/\\uff08\\s*[\\d,]+\\s*\\u5b57\\s*\\uff09/g, "\\uff08" + w + "\\u5b57\\uff09");
  SPEC.spec = String(SPEC.spec || "")
    + "\\n\\n【本次体量以这一条为准】读者这一次选的是 **" + w + " 字**。"
    + "上面规格里出现过的任何别的字数（含「约 X 字」「可到 X 字」，以及标题括号里的那个数）**一律作废**。"
    + "按 " + w + " 字配比例与详略：短了就砍掉一条线索，长了就多一个人、多一段余波——"
    + "**不是同一份内容拉长或压缩**。";
}
'''
if "function distFitCopy" in h:
    done.append("刀二·函数 已在")
else:
    assert ANCHOR_FN in h, "distFitCopy 插入锚点没找到"
    h = h.replace(ANCHOR_FN, FIT_FN + ANCHOR_FN, 1)
    done.append("刀二·函数 已插入")

# ── 刀二之二：接线 + 刀三：预算上下都夹 ────────────────────────
OLD_WIRE = '''      if (SPEC) {
        SPEC.words = _wPick;
        if (Array.isArray(SPEC.fixed) && SPEC.fixed.length) {
          SPEC.fixed = distScaleFixed(SPEC.fixed, _wPick);
          SPEC.parts = SPEC.fixed.length;
        } else if (_wPick) {
          /* 一趟出全篇的档：输出预算要跟着体量走，不然选了长档也写不出来
             （预算是天花板不是目标，按每汉字约 3.2 token 估，仍受平台上限压住）。 */
          SPEC.tok = Math.min(WDS_TOK_MAX, Math.max(SPEC.tok, Math.round(_wPick * 3.2)));
        }
      }'''
NEW_WIRE = '''      if (SPEC) {
        SPEC.words = _wPick;
        distFitCopy(SPEC, _wPick);   // 规格文案（name 与 spec）跟着选中的体量改口
        if (Array.isArray(SPEC.fixed) && SPEC.fixed.length) {
          SPEC.fixed = distScaleFixed(SPEC.fixed, _wPick);
          SPEC.parts = SPEC.fixed.length;
        } else if (_wPick) {
          /* 一趟出全篇的档：输出预算跟着体量走，**上下都夹**（按每汉字约 3.2 token 估）。
             ⚠ 原来这里是 max(SPEC.tok, …)——只升不降，于是 essay 目标 3000 字却拿着 32000 的硬底
             （≈ 一万汉字的位置）。预算是天花板不是目标，可留了十倍的天花板，基底就往天花板写：
             真跑 4396/3000。地板 8000 保住短档不被顶穿（诗 500 字、函件 600 字那几档）。 */
          SPEC.tok = Math.min(WDS_TOK_MAX, Math.max(8000, Math.round(_wPick * 3.2)));
        }
      }'''
if "distFitCopy(SPEC, _wPick)" in h:
    done.append("刀二·接线＋刀三 已在")
else:
    assert OLD_WIRE in h, "接线锚点没找到"
    h = h.replace(OLD_WIRE, NEW_WIRE, 1)
    done.append("刀二·接线＋刀三 已改")

# ── 刀二之三：story 那句自己放宽 1.67 倍的文案 ──────────────────
OLD_STORY = '''"把这场对话里那个判断，写成一篇【短篇小说，约 2400 字，可到 4000 字】。\\n"'''
NEW_STORY = '''"把这场对话里那个判断，写成一篇【短篇小说】。\\n"'''
if NEW_STORY in h:
    done.append("刀二·story 已在")
else:
    assert OLD_STORY in h, "story 文案锚点没找到"
    h = h.replace(OLD_STORY, NEW_STORY, 1)
    done.append("刀二·story 写死的「可到 4000 字」已去掉")

if h == orig:
    print("无改动（全部已在）")
else:
    io.open(P, "w", encoding="utf-8").write(h)
for d in done:
    print("  ·", d)
