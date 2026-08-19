# -*- coding: utf-8 -*-
"""胡志英学员页全面更新（2026-07-27）。

三件事：
1. 给此前 18 篇未评分的旧作补上创新智商（原始分，未做深化增补），
   写进 works 卡片的 meta 行，并在各论文页顶部加一个分数条；
2. 在 works 索引顶部插入覆盖全部 44 篇的创新智商榜，
   同时把页头描述从"英语教育"改为能涵盖其实际研究范围的说法；
3. 重写学员主页的"学术思想与研究"区块——原文只覆盖前 18 篇，
   且误用"她"（胡志英即约翰 John Hu，页面其余部分均作"他"）。

分数口径必须在页面上说清：旧作为原始分，2026-07-27 发表的 26 篇
标注为"原始分 → 深化增补后"，两者不同基准，榜单按原始分排序。
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[1]
STU = ROOT / "public" / "students" / "hu-zhiying"
WORKS = STU / "works" / "index.html"
PROFILE = STU / "index.html"

# ── 18 篇旧作的创新智商（原始分；五维加权 S.20 D.25 E.20 I.20 F.15）
OLD_SCORES = [
    ("operational-parasitism", "解绑的悖论：身体工作中操作者续期的自指结构", 144, 142, 148, 145, 140, 142),
    ("operational-enclosure", "操作性收编：继承不可继承者的智识代价", 143, 145, 145, 140, 142, 142),
    ("reflexive-impasse", "自反性困境：制度变迁中共识信托的消耗与经济增长的停滞", 143, 142, 148, 142, 138, 142),
    ("boundary-contraction", "边界收缩即边疆永失", 142, 145, 145, 138, 138, 142),
    ("institutional-autoimmunity", "制度性自体免疫", 142, 142, 145, 140, 136, 145),
    ("default-mode-threshold", "默认模式的能耗阈值", 142, 142, 145, 140, 136, 145),
    ("subjectivation-metabolism", "算法时代的自由意志危机", 141, 142, 145, 138, 136, 145),
    ("algorithmic-entrenchment", "算法闭环与生物代价", 141, 140, 145, 142, 136, 140),
    ("borrowed-stability", "稳定性借据", 140, 142, 145, 136, 138, 140),
    ("encapsulated-maintenance", "维持的悖论", 140, 142, 142, 136, 136, 142),
    ("accountable-degeneration", "探究的会计化退化", 140, 142, 142, 138, 134, 142),
    ("metabolic-polarity", "代谢基态的极性翻转", 138, 140, 142, 134, 134, 140),
    ("custodial-backfire", "自我囚禁的传承", 137, 140, 142, 132, 134, 138),
    ("efficacy-attrition", "自我复制的悖论", 137, 138, 142, 134, 132, 138),
    ("invisible-upkeep", "看不见的维持", 136, 138, 140, 132, 132, 140),
    ("shelter-as-cage", "庇护所即牢笼", 136, 138, 140, 130, 130, 145),
    ("legitimacy-autophagy", "合法性的自噬", 136, 138, 142, 132, 130, 138),
    ("evaluation-dependent-depletion", "评价依附性耗竭", 136, 138, 140, 132, 132, 138),
]

SCOREBOX = ('<div style="border:1px solid rgba(201,168,76,0.42);border-left:3px solid #C9A84C;'
            'padding:16px 22px;margin:20px 0;font-size:14.5px;line-height:1.9">'
            '<b style="color:#D4B25E">SDE 创新智商：{score}</b>'
            '<span style="opacity:.8"> · 五维 S{S} D{D} E{E} I{I} F{F}</span>'
            '<p style="margin:6px 0 0;opacity:.82">本篇为<b>原始分</b>——发表时未做深化增补。'
            '2026 年 7 月 27 日发表的 26 篇另标"原始分 → 增补后"，两者不同基准。'
            '编辑自评，待独立复评。</p></div>\n')


def load_new():
    a = json.loads((ROOT / "tools" / "hzy_report.json").read_text(encoding="utf-8"))["papers"]
    b = json.loads((ROOT / "tools" / "hzy2_report.json").read_text(encoding="utf-8"))["papers"]
    return a + b


def stamp_old_pages():
    n = 0
    for slug, _t, score, S, D, E, I, F in OLD_SCORES:
        path = STU / slug / "index.html"
        text = path.read_text(encoding="utf-8")
        if "SDE 创新智商" in text:
            continue
        anchor = '<div class="wrap">'
        assert anchor in text, f"{slug} 缺 .wrap 容器"
        text = text.replace(
            anchor,
            anchor + "\n" + SCOREBOX.format(score=score, S=S, D=D, E=E, I=I, F=F), 1)
        path.write_text(text, encoding="utf-8")
        n += 1
    return n


def stamp_old_cards():
    text = WORKS.read_text(encoding="utf-8")
    n = 0
    for slug, _t, score, *_ in OLD_SCORES:
        # 定位该篇卡片：其 modes 区里含本篇链接，meta 行在它前面
        m = re.search(
            r'(<div class="meta">)((?:(?!</div>).)*?)(</div>\s*<div class="modes">\s*'
            r'<a class="m primary" href="/students/hu-zhiying/%s/")' % re.escape(slug),
            text, re.S)
        assert m, f"{slug} 未匹配到卡片 meta"
        meta = m.group(2)
        if "创新智商" in meta:
            continue
        new_meta = meta.replace(
            " · 三种读法",
            f" · SDE 创新智商 {score}（原始分，未做深化增补） · 三种读法", 1)
        assert new_meta != meta, f"{slug} meta 行无三种读法锚点"
        text = text[:m.start(2)] + new_meta + text[m.end(2):]
        n += 1
    WORKS.write_text(text, encoding="utf-8")
    return n


RANK_ID = "hzy-iq-board"


def build_board():
    text = WORKS.read_text(encoding="utf-8")
    if RANK_ID in text:
        text = re.sub(r'<div id="%s".*?</div>\n</div>\n\n' % RANK_ID, "", text, flags=re.S)

    rows = [(s, t, sc, None) for s, t, sc, *_ in OLD_SCORES]
    for p in load_new():
        rows.append((p["slug"], p["title"], p["old_score"], p["score"]))
    rows.sort(key=lambda r: (-r[2], -(r[3] or 0)))

    body = []
    for i, (slug, title, old, new) in enumerate(rows, 1):
        cur = f'{old} → <b style="color:#D4B25E">{new}</b>' if new else f'{old}'
        tag = "增补后" if new else "原始分"
        body.append(
            f'<tr><td style="padding:5px 10px 5px 0;opacity:.6">{i}</td>'
            f'<td style="padding:5px 10px 5px 0"><a href="/students/hu-zhiying/{slug}/" '
            f'style="color:var(--gold);text-decoration:none">{title}</a></td>'
            f'<td style="padding:5px 0 5px 10px;white-space:nowrap">{cur}'
            f'<span style="opacity:.5;font-size:12px"> {tag}</span></td></tr>')

    scored = [r[2] for r in rows]
    avg = sum(scored) / len(scored)
    top = max(r[3] or r[2] for r in rows)

    block = f"""<div id="{RANK_ID}" style="max-width:900px;margin:26px auto 8px;padding:0 24px">
<div style="border:1px solid rgba(201,168,76,0.30);border-radius:12px;padding:24px 26px 18px">
  <div style="color:#D4B25E;letter-spacing:.18em;font-size:13px;margin-bottom:8px">创 新 智 商 榜 · INNOVATION IQ</div>
  <p style="font-size:14px;line-height:1.9;margin:0 0 4px;opacity:.86">全部 {len(rows)} 篇按<b>原始分</b>排序（同一基准）。原始分为发表前评分；2026 年 7 月 27 日发表的 26 篇另做了深化增补，箭头后为增补后分数。均值 {avg:.1f}，最高 {top}。五维口径：论证结构 S · 判断反直觉度 D · 跨域纠合 E · 不可还原性 I · 可证伪性 F，加权 20/25/20/20/15。分数为编辑自评，待独立复评。</p>
  <div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-size:14px;line-height:1.7">
{chr(10).join(body)}
  </table></div>
</div>
</div>

"""
    anchor = '<div class="works">'
    assert anchor in text, "works 索引缺 .works 容器"
    text = text.replace(anchor, block + anchor, 1)

    old_who = 'SDE 学员 · 英语教育 · '
    assert old_who in text, "未找到页头描述"
    text = text.replace(old_who, 'SDE 学员 · 英语教育与跨学科理论建构 · ', 1)

    WORKS.write_text(text, encoding="utf-8")
    return len(rows), avg, top


RESEARCH_ZH = [
    "胡志英的早期研究以一个反复出现的结构性追问贯穿多个学科：一套系统——福利制度、组织、知识生产、文化观念、精神传统——为什么会在最忠实地执行自身设计时走向崩塌？他擅长为这类内生性失效命名并建立可检验的机制模型：以代谢基态的极性翻转解释福利制度的反向效果，以制度性自体免疫刻画社会修复工程的结构性崩溃，以稳定性借据说明思想与制度何以在功能尚未过时之际骤然瓦解，以操作性收编分析继承皮尔斯遗产的智识代价，以边界收缩即边疆永失给出学术范式免疫获得与未来锁死的同一根源。",
    "2026 年 7 月发表的二十六篇把这条追问往前推了一层：不再只问一套系统为何瓦解，而问那个能做出判断的人、器官或形态最初是怎么发生的，又是怎么被悄悄取消的。这一层的代表作包括：主张消散比生成更原始的《蚀先于生》、阐明追问者在自造的不可能对象上烧掉自己的《刀与伤口同源》、撤销构成性语法而正面重建地基的《临在》、以科举千年史追踪判断力如何在成功中被自我吞噬的《成功者的茧》、把客观性重述为一个每天都在耗电的耗散结构的《因果的维持》，以及处理教育、组织评价、传统工艺与技术代偿的一组篇章。",
    "他的方法有一种诊断学家的冷静：先为一类失效精确命名，再逼自己写出能让这个命名失效的条件。四十四篇里几乎每一篇都带着可操作的证伪设计与排除最强竞争解释的方案——这也是他的作品在评分中最稳定的一维。贯穿始终的是同一个反直觉的洞见：维持一套系统的那些机制，往往正是让它从内部瓦解的根源；而近作把这句话推到了更深处——被瓦解的，往往首先是那个本来能看见瓦解正在发生的器官。",
]

RESEARCH_EN = ("Hu Zhiying's earlier work asks why systems collapse precisely when they execute their own "
               "design most faithfully, naming a series of endogenous failure mechanisms across welfare policy, "
               "organisations, knowledge production and cultural traditions. The twenty-six papers published in "
               "July 2026 push the question one layer back: not why a system falls apart, but how the organ "
               "capable of noticing that it is falling apart came into being in the first place — and how it is "
               "quietly removed.")


def rewrite_research():
    text = PROFILE.read_text(encoding="utf-8")
    i = text.find("学 术 思 想 与 研 究")
    j = text.find("作 品 与 专 栏")
    assert 0 < i < j, "未定位到研究区块"
    start = text.rfind('<div style="max-width:820px', i, j)
    end = text.rfind('<div class="level-tag"', i, j)
    assert 0 < start < end, "研究区块结构与预期不符"

    style = 'font-size:15px;line-height:2.05;text-align:justify;margin:0 0 14px;color:inherit'
    paras = "".join(f'\n    <p class="zh-only" style="{style}">{p}</p>' for p in RESEARCH_ZH)
    paras += f'\n    <p class="en-only" style="{style}">{RESEARCH_EN}</p>'
    block = ('<div style="max-width:820px;margin:0 auto;padding:6px 24px 10px">\n'
             '  <div style="background:var(--panel2,rgba(150,130,80,.06));'
             'border:1px solid var(--line,rgba(150,130,80,.25));border-radius:14px;'
             'padding:30px 30px 18px">'
             f'{paras}\n  </div>\n</div>\n')
    text = text[:start] + block + text[end:]
    PROFILE.write_text(text, encoding="utf-8")
    return text.count("她")


def main():
    a = stamp_old_pages()
    b = stamp_old_cards()
    n, avg, top = build_board()
    she = rewrite_research()
    print(f"  旧作分数条：{a} 篇论文页已加")
    print(f"  旧作卡片：{b} 张 meta 行已补分")
    print(f"  创新智商榜：{n} 篇，均值 {avg:.1f}，最高 {top}")
    print(f"  主页研究区块已重写；剩余“她”字 {she} 处")


if __name__ == "__main__":
    main()
