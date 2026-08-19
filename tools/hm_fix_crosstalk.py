# -*- coding: utf-8 -*-
"""修复胡敏专栏的交叉串稿（2026-07-27）。

背景：7-26 的提交 7be73a4 把三类页头展示块在批内串了位——
  · 摘要块：14 页共用《经验的两种生成》的摘要（该文自己那页是对的）
  · 思想创新块：11 页共用《论好奇心的不可还原结构》的创新语（该文自己对）
  · 导读块：25 页共用《发生性空洞》的导读、11 页共用《好奇底子》的导读
正文完好，错的只是页头展示块。合计 39 页受影响。

处置原则：只删不造。别人的文字冒充本篇，比缺这个块更糟；能恢复的才恢复。
  · 4 篇（好奇底子/漩涡之困/自我景观化/静默的复刻）的 PDF 里保有正确摘要 → 回填
  · 其余错误摘要块 → 删除（这些页的 art-subtitle 前半段本就是自己摘要的开头）
  · 串稿的思想创新块与导读块 → 删除（无任何可恢复来源，不代写）
  · art-subtitle 尾部被拼进的他篇高亮句 → 截断到最后一个完整句号

若日后拿到原稿，回填位置即各页 <div class="wrap"> 之后的第一个块。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STU = ROOT / "public" / "students" / "hu-min"

# 各污染源的指纹（用于精确识别，绝不误伤自己那一页）
FP_ABS = "中医在AI时代面临的真正挑战"          # 源：experience-bifurcation
FP_INNOV = "好奇心衰退的关键不在动机的量"        # 源：curiosity-substrate
FP_DAODU_A = "它指出主流好奇心模型"              # 源：curiosity-substrate
FP_DAODU_B = "不是“应对失败”（压力-易感）"      # 源：generative-void
OWNER = {FP_ABS: "experience-bifurcation", FP_INNOV: "curiosity-substrate",
         FP_DAODU_A: "curiosity-substrate", FP_DAODU_B: "generative-void"}

# 从 PDF 提取回的正确摘要（见 tools/hm_abstracts.py）
sys.path.insert(0, str(ROOT / "tools"))
from hm_abstracts import RECOVERED


def cut_subtitle(s, slug=None):
    """砍掉 art-subtitle 里被拼进来的他篇高亮句，并回退到最后一个完整句末。"""
    if slug == OWNER[FP_INNOV]:          # 高亮句是本篇自己的，不动
        return s, False
    m = re.search(r'(<div class="art-subtitle">)(.*?)(</div>)', s, re.S)
    if not m:
        return s, False
    body = m.group(2)
    i = body.find('<span class="hl2">')
    if i < 0:
        return s, False
    head = body[:i]
    if FP_INNOV.split("，")[0] not in body and "而在察觉" not in body:
        return s, False          # 高亮句是自己的，不动
    cut = max(head.rfind("。"), head.rfind("；"))
    head = head[:cut + 1] if cut > 40 else head.rstrip("—- ，、") + "……"
    return s[:m.start(2)] + head + s[m.end(2):], True


def drop_block(s, opener, fingerprint):
    """删除以 opener 开头、内部含 fingerprint 的那个 div（按嵌套配平找结束）。"""
    i = s.find(opener)
    while i >= 0:
        depth, j = 0, i
        while j < len(s):
            if s.startswith("<div", j):
                depth += 1
            elif s.startswith("</div>", j):
                depth -= 1
                if depth == 0:
                    j += 6
                    break
            j += 1
        blk = s[i:j]
        if fingerprint in blk:
            k = j
            while k < len(s) and s[k] in "\n\r\t ":
                k += 1
            return s[:i] + s[k:], True
        i = s.find(opener, i + 1)
    return s, False


def restore_abstract(s, text):
    m = re.search(r'(<div class="abstract">.*?<p>)(.*?)(</p>)', s, re.S)
    if not m or FP_ABS not in m.group(2):
        return s, False
    return s[:m.start(2)] + text + s[m.end(2):], True


def drop_empty_lead(s):
    """innov 与 daodu 都被删掉后，留下的空 lead 壳一并清掉。"""
    m = re.search(r'<div class="lead">\s*</div>\s*', s)
    return (s[:m.start()] + s[m.end():], True) if m else (s, False)


def main():
    dry = "--dry" in sys.argv
    stat = {k: 0 for k in ("摘要删", "摘要复原", "创新删", "导读删", "副标题截", "空壳清")}
    rows = []
    for d in sorted(p.name for p in STU.iterdir() if (p / "index.html").exists()):
        path = STU / d / "index.html"
        s0 = s = path.read_text(encoding="utf-8")
        acts = []

        if FP_ABS in s and d != OWNER[FP_ABS]:
            if d in RECOVERED:
                s, ok = restore_abstract(s, RECOVERED[d])
                if ok: acts.append("摘要复原"); stat["摘要复原"] += 1
            else:
                s, ok = drop_block(s, '<div class="abstract">', FP_ABS)
                if ok: acts.append("摘要删"); stat["摘要删"] += 1

        if FP_INNOV in s and d != OWNER[FP_INNOV]:
            s, ok = drop_block(s, '<div class="innov">', FP_INNOV)
            if ok: acts.append("创新删"); stat["创新删"] += 1

        for fp in (FP_DAODU_A, FP_DAODU_B):
            if fp in s and d != OWNER[fp]:
                s, ok = drop_block(s, '<div class="daodu">', fp)
                if ok: acts.append("导读删"); stat["导读删"] += 1

        s, ok = cut_subtitle(s, d)
        if ok: acts.append("副标题截"); stat["副标题截"] += 1

        s, ok = drop_empty_lead(s)
        if ok: acts.append("空壳清"); stat["空壳清"] += 1

        if s != s0:
            assert s.count("<html") == 1 and s.count("</html>") == 1, d
            if not dry:
                path.write_text(s, encoding="utf-8")
            rows.append((d, "+".join(acts)))

    for d, a in rows:
        print("  %-30s %s" % (d, a))
    print("\n受影响页面 %d 项统计：%s%s" % (len(rows), stat, "（--dry 未落盘）" if dry else ""))


if __name__ == "__main__":
    main()
