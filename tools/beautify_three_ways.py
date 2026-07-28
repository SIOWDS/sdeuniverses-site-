# -*- coding: utf-8 -*-
"""《能改的看不见，看得见的改不了》修改与完善。

内容上补一处真缺口：全篇的核心是「三关在六个维度上系统性地反着来」，
而这六个维度原本散在四章的散文里，读者得自己拼。补一张对照表，
把三关放在同一个视野里——**表里那两行（看得见吗／改得动吗）方向相反，就是全文的判断本身**。

排版沿用本栏之十二已用过的语汇（.li / .pull / .tbl / .rule），不另造：
  ① 六十余处编号条目升为可扫读的引导行
  ② 三关对照表（新增内容）
  ③ 三句最承重的判断做成引文块
  ④ 章间分隔线

正文一个字不改，只增结构与那张表。
"""
import re
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "public" / "paradigm" / "three-ways-to-die" / "index.html"

CSS_ADD = """
/* —— 排版补强（沿用本栏之十二的语汇）—— */
.li{margin-top:26px}
.li>b:first-child{display:block;color:var(--clay,#B5714A);font-size:17.5px;line-height:1.7;
 margin-bottom:7px;letter-spacing:.01em}
.pull{background:rgba(181,113,74,.08);border-left:4px solid var(--clay,#B5714A);
 border-radius:0 7px 7px 0;padding:18px 24px;margin:30px 0;font-size:19px;line-height:1.95;
 color:var(--indigo,#243447);font-weight:600;text-align:justify}
.pull.small{font-size:17px;font-weight:500}
.rule{border:0;height:1px;margin:46px 0;
 background:linear-gradient(90deg,transparent,rgba(181,113,74,.42),transparent)}
.tbl{width:100%;border-collapse:collapse;margin:26px 0;font-size:14.5px;background:var(--card,#FFFDF7)}
.tbl th{background:rgba(181,113,74,.13);color:#7A4A2C;font-weight:700;padding:10px 11px;
 border:1px solid var(--line,rgba(36,52,71,.16));text-align:left;line-height:1.6}
.tbl td{padding:10px 11px;border:1px solid var(--line,rgba(36,52,71,.16));line-height:1.75;vertical-align:top}
.tbl td:first-child{font-weight:700;color:#7A4A2C;white-space:nowrap;background:rgba(181,113,74,.05)}
.tbl tr.key td{background:rgba(181,113,74,.11)}
.tbl tr.key td:first-child{background:rgba(181,113,74,.18)}
.tbl .no{color:#9A3B2E;font-weight:700}
.tbl .yes{color:#2F6B4F;font-weight:700}
.tblnote{font-size:14px;color:var(--ink2,#5A6472);margin:-14px 0 26px;line-height:1.85;text-align:justify}
@media(max-width:640px){.tbl{font-size:12.5px}.tbl th,.tbl td{padding:7px 6px}
 .pull{font-size:16.5px;padding:14px 16px}.li>b:first-child{font-size:16px}}
"""

TABLE = """<table class="tbl">
<tr><th style="width:15%"></th><th style="width:28%">第一关 · 没成形</th><th style="width:28%">第二关 · 没位置</th><th style="width:29%">第三关 · 没掌权</th></tr>
<tr><td>死于</td><td>快</td><td>更好</td><td>熟</td></tr>
<tr><td>失败长什么样</td><td>什么也没有</td><td>说不清自己想要什么</td><td>明明知道却做不到</td></tr>
<tr><td>疼不疼</td><td>不疼——不知道丢了什么</td><td>不疼——没有痛的参照点</td><td>疼，当事人第一个知道</td></tr>
<tr><td>他的自述</td><td>说到一半卡住、找词</td><td>流畅地给出别人的答案</td><td>具体清楚，带着遗憾</td></tr>
<tr><td>时间尺度</td><td>毫秒到秒</td><td>年</td><td>秒</td></tr>
<tr class="key"><td>看得见吗</td><td class="no">原则上不可</td><td class="no">极难</td><td class="yes">一眼可见</td></tr>
<tr class="key"><td>改得动吗</td><td class="yes">可，只需克制</td><td class="yes">可，但有窗口</td><td class="no">几乎不可</td></tr>
<tr><td>误诊后果</td><td>被当成没追求</td><td>被送去做更多训练</td><td>被惩罚「反复」</td></tr>
</table>
<p class="tblnote">这张表里真正要紧的只有中间那两行。它们的颜色是反着的——而全文的判断就是这两行反着这件事本身：<b>唯一看得见的那一关，恰好是唯一改不动的；两关能改的，恰好都看不见。</b>其余各行都是为了让这两行站得住。</p>
"""

ITEM_HEADS = [
    "第一个人", "第二个人", "第三个人",
    "第一种：没成形。", "第二种：没位置。", "第三种：没掌权。",
    "第一关，成形。", "第二关，先占。", "第三关，掌权。",
    "第一关死于「快」。", "第二关死于「更好」。", "第三关死于「熟」。",
    "可见性：从第三关往回，急剧递减。", "可改性：方向正好相反。",
    "更及时的反馈", "更明确的标准", "更频繁的复盘", "更细的行为分解",
    "第二关伪装成第三关。", "第一关伪装成第二关。", "为什么伪装方向是单向的？",
    "第一，只有第三关的失败可以立案。",
    "第二，只有第三关的干预可以验收。",
    "第三，前两关的干预在短期内会让第三关的指标变差。",
    "第四，也是最难办的：做前两关的事需要的正是「不做」，而组织无法奖励不做。",
    "医学诊断。", "软件工程。", "司法。", "育儿。", "组织管理。", "语言学习。",
    "反驳一：第一关是个理论虚构。", "反驳二：第二关只是慢速的第三关。",
    "两个反驳共同揭示的一件事",
    "第一个邻居：冰山模型。", "第二个邻居：根因分析。", "第三个邻居：发展关键期。",
    "第四个邻居：习惯的顽固与旧习复发。", "第五个邻居：内隐偏见与自动化加工。",
    "第六个邻居：习得性无助。", "第七个邻居：正念与减速类实践。", "第八个邻居：刻意练习。",
    "共同点一：有过一段没有人看的时间。",
    "共同点二：那段时间里，他被允许做得很差。",
    "共同点三：他有一个不被评价的对照面。",
    "最要紧的一点：这三个共同点，没有一个是被设计出来的。",
    "第一条，最可靠：撤掉压力，看会不会出现。",
    "第二条：问「你想要什么」，听回答的形状。",
    "第三条：看他压力下会变成什么。",
    "第四条，用来兜底：看时间尺度。",
    "第一关：减慢覆盖。", "第二关：在窗口期腾地。",
    "第三关：管理切换，而不是承诺消除。",
    "第一条，关于三关是不是真的可分。",
    "第二条，关于撤除压力的分辨力。",
    "第三条，关于可改性的方向。",
    "第四条，关于致病因子那一笔。",
    "第五条，关于第二关的窗口。",
    "第六条，关于第一关是否存在。",
    "第七条，关于第三关的人是否真的更有能力。",
    "第八条，一个写死的赌注。",
    "第九条，关于卡顿是不是正向信号。",
]

PULLS = [
    ("能改的看不见，看得见的改不了；而修那看得见的，正在毁那看不见的。", ""),
    ("我们用来补救第三关的每一样工具，恰好都是前两关的致病因子。", " small"),
    ("最有效的剥夺，不是让人痛到不敢动，是让人舒服到从不痛。", " small"),
]

UNBOLD = [
    "他有本事，只是没有那个本事。",
    "这个循环里没有一个人做错了事。",
    "关键在语气而不在内容",
    "这也是为什么这个问题很难在集体讨论中被识别出来。",
]


def main():
    t = P.read_text(encoding="utf-8")
    tags0 = len(re.findall(r"<[a-zA-Z/][^>]*>", t))
    chars0 = len(re.sub(r"<[^>]+>", "", t))

    i = t.rfind("</style>")
    assert i > 0
    t = t[:i] + CSS_ADD + t[i:]

    n_item = 0
    for h in ITEM_HEADS:
        old = f"<p><b>{h}</b>"
        c = t.count(old)
        # 「第一个人」等在开篇与末章回访处各出现一次，两处都该结构化
        assert 1 <= c <= 2, f"条目锚点命中 {c} 次：{h[:22]}"
        t = t.replace(old, f'<p class="li"><b>{h}</b>')
        n_item += c

    # 对照表插在「可改性：方向正好相反」那一段之后、结论句之前
    a = ('<p class="li"><b>可见的那一关，恰好是唯一改不动的那一关；'
         '而两关可改的，恰好都不可见。</b></p>')
    if t.count(a) != 1:
        a = "<p><b>可见的那一关，恰好是唯一改不动的那一关；而两关可改的，恰好都不可见。</b></p>"
    assert t.count(a) == 1, "结论句锚点没找到"
    t = t.replace(a, TABLE + '<p class="pull">可见的那一关，恰好是唯一改不动的那一关；'
                            '而两关可改的，恰好都不可见。</p>', 1)

    for s, extra in PULLS:
        old = f"<p><b>{s}</b></p>"
        if t.count(old) == 1:
            t = t.replace(old, f'<p class="pull{extra}">{s}</p>', 1)

    n_ub = 0
    for s in UNBOLD:
        old = f"<b>{s}</b>"
        if t.count(old) == 1:
            t = t.replace(old, s, 1)
            n_ub += 1

    for h in ["一句话的规律", "与八个最像的说法划界", "这篇文章自己是第三关的产物"]:
        m = re.search(r'<h2 id="s\d+">' + re.escape(h) + r"</h2>", t)
        if m:
            t = t[:m.start()] + '<hr class="rule">' + t[m.start():]

    chars1 = len(re.sub(r"<[^>]+>", "", t))
    assert chars1 > chars0, "文字变少了"
    assert t.count("<html") == 1 and t.count("<table") == t.count("</table>")
    assert t.count("<p") == t.count("</p>"), "p 不配对"
    P.write_text(t, encoding="utf-8")
    print(f"  条目引导行 {n_item} 处 · 对照表 1 张（新增内容）· "
          f"引文块 {len(PULLS) + 1} 处 · 粗体瘦身 {n_ub} 处 · 分隔线 3 条")
    print(f"  标签 {tags0} → {len(re.findall(r'<[a-zA-Z/][^>]*>', t))} · 正文字数 {chars0} → {chars1}")


if __name__ == "__main__":
    main()
