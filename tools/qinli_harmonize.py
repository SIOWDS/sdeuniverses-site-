# -*- coding: utf-8 -*-
"""秦莉专栏全面整理：把一批批长出来的各自口径收成一套。

这个专栏是分七八批发的，每批各用各的规矩，于是积下四类不一致：

  ① **眉题 24 种写法**——同一组四篇用了四个不同学科名；7 篇干脆只写「学员专栏 · 秦莉」
  ② **publications.json 的 kind 是脏的**——16 条写着「金点子四篇（二）」这类内部批次标签
     （「金点子」是不该出现在读者面的词，全站只有她这里有），另 7 条带「进 入 论 文 · 」
     这种逐字空格的批次前缀
  ③ **分数格式四种**——带冒号／不带冒号／单段／多段混用
  ④ **8 篇早期论文无分数**，看起来像遗漏而不是口径

整理原则：**页面上的具体学科名是好的，脏的是 publications**——所以真源取页面，
反向去洗 publications，而不是拿脏 kind 去覆盖好眉题。洗完之后三处同源：
页面眉题 ↔ publications.kind ↔ 作者页列表。
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STU = ROOT / "public" / "students" / "qin-li"
PUB = ROOT / "public" / "students" / "publications.json"

# 批次标签 → 该篇真正的学科名（取自各自页面眉题，逐篇核对过）
KIND_FIX = {
    "existential-stake": "艺术哲学与存在决断",
    "bearing-the-enough": "艺术哲学与创作生成",
    "generative-silence": "艺术哲学与体制诊断",
    "surplus-injection": "艺术哲学与体制夹缝",
    "other-handedness": "亲密关系理论与临床心理学",
    "residual-orientation": "创伤心理学与存在分析",
    "decisive-touch": "爱的哲学与关系精神分析",
    "beheld-flame": "爱的现象学与依恋研究",
    "institutional-funeral": "卫生政策与制度分析",
    "self-locking-loop": "卫生政策与制度分析",
    "six-gates": "卫生政策与制度分析",
    "reverse-production": "卫生政策与制度分析",
    "yielded-void": "美学与艺术接受研究",
    "existential-verdict": "艺术哲学与意义生成",
    "guarding-drift": "艺术生态与技术批判",
    "completing-arc": "接受理论与传递结构",
}

# 眉题只写了「学员专栏 · 秦莉」的 7 篇：学科名取自 publications（去掉批次前缀与逐字空格）
SERIES_FIX = {
    "law-as-negative-space": "哲学与美学",
    "negative-inheritance": "哲学与宗教",
    "offbeat-justice": "法哲学与公共舆论",
    "release-morphology": "艺术理论",
    "scale-not-penetration": "跨文化传播",
    "unwritten-law": "语言与美学",
}

BATCH_JARGON = ("金点子", "提升·", "进 入 论 文")


def clean_kind(k):
    """去掉批次前缀与逐字空格，只留学科名。"""
    k = re.sub(r"^进\s*入\s*论\s*文\s*·\s*", "", k)
    if re.fullmatch(r"(?:\S\s){2,}\S*", k):        # 逐字空格的整串
        k = k.replace(" ", "")
    return k.strip()


def fix_publications():
    d = json.loads(PUB.read_text(encoding="utf-8"))
    rec = next(s for s in d["students"] if s["slug"] == "qin-li")
    n_kind = n_clean = 0
    for it in rec["items"]:
        slug = it["url"].strip("/").split("/")[-1]
        if slug in KIND_FIX:
            it["kind"] = KIND_FIX[slug]
            n_kind += 1
        else:
            c = clean_kind(it.get("kind", ""))
            if c != it.get("kind"):
                it["kind"] = c
                n_clean += 1
    left = [it["kind"] for it in rec["items"] if any(b in it["kind"] for b in BATCH_JARGON)]
    assert not left, f"仍有批次术语：{left}"
    # 全站再扫一遍，确认别人那里没有
    other = [(s["name"], i["kind"]) for s in d["students"] for i in s["items"]
             if any(b in i.get("kind", "") for b in BATCH_JARGON)]
    PUB.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ① publications：换掉批次标签 {n_kind} 条、清逐字空格与前缀 {n_clean} 条；"
          f"全站残留 {len(other)} 条")
    return {it["url"].strip("/").split("/")[-1]: it["kind"] for it in rec["items"]}


def fix_series(kinds):
    """页面眉题统一为「学员专栏 · 秦莉 · <学科名>」，与 publications 同源。"""
    n = 0
    for d in sorted(STU.iterdir()):
        if not d.is_dir() or d.name in ("works", "essays", "poems"):
            continue
        f = d / "index.html"
        if not f.exists():
            continue
        t = f.read_text(encoding="utf-8")
        m = re.search(r'(<div class="art-series"[^>]*>)(.*?)(</div>)', t, re.S)
        if not m:
            continue                                # 小说页无眉题，按其版式，不强加
        cur = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        kind = SERIES_FIX.get(d.name) or kinds.get(d.name)
        if not kind or kind == "长篇小说":
            continue
        want = f"学员专栏 · 秦莉 · {kind}"
        if cur == want:
            continue
        t = t[:m.start(2)] + want + t[m.end(2):]
        assert t.count("<html") == 1
        f.write_text(t, encoding="utf-8")
        n += 1
    print(f"  ② 页面眉题：统一 {n} 篇为「学员专栏 · 秦莉 · <学科名>」")


def fix_score_format():
    """统一为「创新智商 N → M」（多轮打磨的保留 N → M → K，那是真实记录）。"""
    n = 0
    for d in sorted(STU.iterdir()):
        if not d.is_dir():
            continue
        f = d / "index.html"
        if not f.exists():
            continue
        t = f.read_text(encoding="utf-8")
        new = re.sub(r"创新智商\s*：\s*", "创新智商 ", t)
        new = re.sub(r"(创新智商 [\d\s→]*\d)\s*", lambda m: re.sub(r"\s*→\s*", " → ", m.group(1)) + " ", new)
        if new != t:
            f.write_text(new, encoding="utf-8")
            n += 1
    print(f"  ③ 分数格式：统一 {n} 页为「创新智商 N → M」")


def state_unscored():
    """8 篇早期论文没有分数——把它写成明写的口径，而不是让它看起来像遗漏。"""
    f = STU / "works" / "index.html"
    t = f.read_text(encoding="utf-8")
    a = "创作理论 · 美学生成研究</h2>"
    assert t.count(a) == 1, "找不到创作理论组标题"
    note = ("<div class=\"d\">本组为早期批次，其中八篇发表于创新智商评分制度建立之前，"
            "故条目上不带分数——这是口径，不是遗漏；其余各组的分数均为编辑自评，标注为"
            "「old → new」并待独立复评。</div>")
    i = t.index(a) + len(a)
    j = t.index('<div class="d">', i)
    k = t.index("</div>", j) + len("</div>")
    if "这是口径，不是遗漏" not in t:
        t = t[:k] + "\n" + note + t[k:]
        f.write_text(t, encoding="utf-8")
        print("  ④ 创作理论组：补一句明写的评分口径")
    else:
        print("  ④ 评分口径已在，跳过")


if __name__ == "__main__":
    kinds = fix_publications()
    fix_series(kinds)
    fix_score_format()
    state_unscored()
