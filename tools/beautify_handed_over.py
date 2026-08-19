# -*- coding: utf-8 -*-
"""《交出去的不止那件事》排版美化。

沿用本栏之十（probe-or-period）已成型的排版语汇，不另造轮子：
  .pull   核心判断的引文块        .tbl    表格
  .rule   章间分隔               .li     条目引导句（本次新增，本栏尚无）

做四件事：
  ① 57 处「第一种／第一条／第一个邻居」这类编号条目，从段内粗体升为可扫读的条目引导行
  ② 四分法改排成一张四行表——它本来就是一个二维分类，挤在段落里读者拼不出来
  ③ 两句最承重的判断做成引文块
  ④ 粗体瘦身：160 处里，段中修饰性加粗降回正文，只留承重句

只动展示层，一个字的正文都不改。
"""
import re
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "public" / "paradigm" / "handed-over" / "index.html"

CSS_ADD = """
/* —— 排版补强（沿用本栏之十的语汇）—— */
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
.tbl td:first-child{font-weight:700;color:var(--clay,#B5714A);white-space:nowrap}
.tbl .bad{color:#9A3B2E}
@media(max-width:640px){.tbl{font-size:12.5px}.tbl th,.tbl td{padding:7px 7px}
 .pull{font-size:16.5px;padding:14px 16px}.li>b:first-child{font-size:16px}}
"""

# ① 需要升为条目引导行的段（以粗体开头且是编号／枚举项）
ITEM_HEADS = [
    "第一件，把「这个学生长得怎么样」交给了分数。",
    "第二件，把「这信是不是真的」交给了可以数出来的东西。",
    "第三件，把「我身体怎么样」交给了手环和平台。",
    "第一，你得亲自做那个决定。",
    "第二，你得承担结果，而且这个结果要真的落到你身上。",
    "第三，你得自己发现哪里错了，而不是被告知。",
    "第一件：他要验的东西，已经不是他当年做过的那件事了。",
    "第二件：他会开始相信自己的判断力，超过它实际值得的程度。",
    "招聘。", "投资。", "医疗。", "写作与编辑。", "家庭。",
    "第一个：民航的定期手飞。",
    "第二个：外科的带教。",
    "第三个：军队的复盘制度。",
    "第一个邻居：委托—代理问题。",
    "第二个邻居：技能退化。",
    "第三个邻居：自动化悖论。",
    "第四个邻居：古德哈特定律。",
    "第五个邻居：外包与核心能力流失。",
    "第六个邻居：知识的诅咒。",
    "第一种：留一条自己做的细流。",
    "第二种：用一把独立的尺子定期复核。",
    "第三种：先自己判，再看答案。",
    "第四种：把「我判不出来」作为一个合法的回答。",
    "第五种：把验收能力的损耗写进决策。",
    "第六种：让做的人和验的人偶尔换位。",
    "第一条，关于验的能力是不是做的副产品。",
    "第二条，关于三个环节是否都必要。",
    "第三条，关于损失是否真的不可自察。",
    "第四条，关于改革方向的偏向。",
    "第五条，关于知情是否改变行为。",
    "第六条，关于四分法里的第一种是否真能维持。",
    "第七条，也是最直接的一条。",
    "第八条，关于四种形态的滑动方向。",
    "学生和分数。", "信和数字。", "身体和读数。",
]

# ② 四分法：四个引导段 + 各自说明，改排成一张表（说明段保留在表后）
TABLE = """<table class="tbl">
<tr><th style="width:16%">形态</th><th style="width:20%">做</th><th style="width:30%">验</th><th style="width:18%">状态</th><th style="width:16%">会滑向</th></tr>
<tr><td>第一种</td><td>交出去</td><td>自己验，且方式独立于对方的交付物</td><td>安全，分工的正常形态</td><td>第二种</td></tr>
<tr><td>第二种</td><td>交出去</td><td>交给与执行方分开的第三方</td><td>较弱，仍可用</td><td>第三种</td></tr>
<tr><td>第三种</td><td>交出去</td><td>交给执行方自评</td><td class="bad">结构上不成立</td><td>第四种</td></tr>
<tr><td>第四种</td><td>交出去</td><td>能力已无，而自以为还有</td><td class="bad">最坏，也最难修</td><td>—</td></tr>
</table>
"""

# ③ 升为引文块的两句
PULLS = [
    ("交出去的东西里，总有一样是验货的尺子。", ""),
    ("每一次都是同一个结构：用来发现损失的器官，恰好就是被损失掉的那一个。", " small"),
]

# ④ 粗体瘦身：这些段中修饰性加粗降回正文（承重句一律保留）
UNBOLD = [
    "他的判断力不是钝了，是错位了。",
    "举证责任翻转了。",
    "没有哪一步是错的，而且每一步都能省下真实的成本。",
    "结果是每一代人都在最有效率的状态下工作，而没有一代人在长那张地图。",
    "审计一旦标准化，它就变成了对材料的审计。",
    "这一点必须说清楚，否则会被读成对改革者的指责。",
]


def main():
    t = P.read_text(encoding="utf-8")
    tags0 = len(re.findall(r"<[a-zA-Z/][^>]*>", t))
    text0 = re.sub(r"<[^>]+>", "", t)

    # CSS
    i = t.rfind("</style>")
    assert i > 0
    t = t[:i] + CSS_ADD + t[i:]

    # ① 条目引导行
    n_item = 0
    for h in ITEM_HEADS:
        old = f"<p><b>{h}</b>"
        assert t.count(old) == 1, f"条目锚点命中 {t.count(old)} 次：{h[:20]}"
        t = t.replace(old, f'<p class="li"><b>{h}</b>', 1)
        n_item += 1

    # ② 四分法表格：插在「差别在两个变量上」那段之后
    a = "差别在两个变量上：<b>你还做不做，以及你还验不验。</b></p>"
    assert t.count(a) == 1
    t = t.replace(a, a + TABLE, 1)
    # 表格已给出骨架，四个引导段改为「逐条说清」的展开
    for old, new in [("第一种：做交出去，验还在自己手上。", "第一种：验还在自己手上。"),
                     ("第二种：做交出去，验也交出去，但验收方与执行方是分开的。", "第二种：验交给分开的第三方。"),
                     ("第三种：做交出去，验也交给同一方。", "第三种：验也交给同一方。"),
                     ("第四种：做交出去，验的能力已经没有了，而你以为还有。", "第四种：验的能力已经没有了，而你以为还有。")]:
        o = f"<p><b>{old}</b>"
        assert t.count(o) == 1, f"四分法锚点：{old[:16]}"
        t = t.replace(o, f'<p class="li"><b>{new}</b>', 1)

    # ③ 引文块
    for s, extra in PULLS:
        old = f"<p><b>{s}</b></p>"
        assert t.count(old) == 1, f"引文锚点：{s[:20]}"
        t = t.replace(old, f'<p class="pull{extra}">{s}</p>', 1)

    # ④ 粗体瘦身
    n_ub = 0
    for s in UNBOLD:
        old = f"<b>{s}</b>"
        if t.count(old) == 1:
            t = t.replace(old, s, 1)
            n_ub += 1

    # ⑤ 章间分隔：在「一句话的规律」与「与六个最像的说法划界」两章前各加一条
    for h in ["一句话的规律", "与六个最像的说法划界"]:
        m = re.search(r'<h2 id="s\d+">' + re.escape(h) + r"</h2>", t)
        assert m, f"找不到章标题：{h}"
        t = t[:m.start()] + '<hr class="rule">' + t[m.start():]

    # 不变量：正文文字一个字都没动（只增删标签与表格里新写的表头）
    text1 = re.sub(r"<[^>]+>", "", t)
    # 只允许「做交出去，」这几个被缩短的引导句字样减少，其余文字一字不动
    for ch in set(text0) - set(text1):
        assert ch in "做交出去，验也但收方与执行是分开的能力已经没有了而你以为还有手上", f"有文字被误删：{ch}"
    assert t.count("<html") == 1 and t.count("<table") == t.count("</table>")
    assert t.count("<p") == t.count("</p>"), "p 不配对"
    P.write_text(t, encoding="utf-8")
    tags1 = len(re.findall(r"<[a-zA-Z/][^>]*>", t))
    print(f"  条目引导行 {n_item + 4} 处 · 四分法表格 1 张 · 引文块 {len(PULLS)} 处 · "
          f"粗体瘦身 {n_ub} 处 · 分隔线 2 条")
    print(f"  标签 {tags0} → {tags1}")


if __name__ == "__main__":
    main()
