# -*- coding: utf-8 -*-
"""高鹏：把 A 批四篇挂进 works 索引（置顶）与学员主页新作区，并改口径。

works 索引是扁平的 .work 卡片流，最新在最前、序号等于当前作品总数。
主页有两处需要同步：新作清单 <ul> 与页脚那句"浏览全部 N 篇"。
"""
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaopeng3_meta import PUBDATE_CN

ROOT = Path(__file__).resolve().parents[1]
STU = ROOT / "public" / "students" / "gao-peng"
IDX, PROF = STU / "works" / "index.html", STU / "index.html"
REPORT = json.loads((ROOT / "tools" / "gaopeng3_report.json").read_text(encoding="utf-8"))
BY = {p["slug"]: p for p in REPORT["papers"]}
ORDER = ["juris-sustaining", "ashes-of-rights",
         "second-genesis-of-will", "flesh-of-power"]
G = 'style="color:var(--gold)"'


def card(p):
    b = f'/students/gao-peng/{p["slug"]}'
    return (f'  <div class="work">\n'
            f'    <span class="chip">之{p["num"]} · 新作 · {html.escape(p["kind"])} · 打磨版</span>\n'
            f'    <h2>{html.escape(p["title"])}</h2>\n'
            f'    <p class="hook">{html.escape(p["hook"])}</p>\n'
            f'    <div class="meta">约 {p["wan"]} 万字 · {p["pages"]} 页 · '
            f'SDE 创新智商 {p["old_score"]} → {p["score"]}（编辑自评，待独立复评） · '
            f'本批评分第 {p["rank"]} · 三种读法 · 发表于{PUBDATE_CN}</div>\n'
            f'    <div class="modes">\n'
            f'      <a class="m primary" href="{b}/">📖 长文阅读</a>\n'
            f'      <a class="m ghost" href="{b}/read.html">📄 在线 PDF</a>\n'
            f'      <a class="m ghost" href="{b}/{p["slug"]}.pdf" download>⬇ 下载 PDF</a>\n'
            f'    </div>\n'
            f'  </div>\n')


def li(p):
    b = f'/students/gao-peng/{p["slug"]}'
    return (f'      <li style="margin-bottom:9px"><a href="{b}/" {G}>《{html.escape(p["title"])}》</a>'
            f'<span style="font-size:13px;opacity:.8"> — {html.escape(p["kind"])} · 之{p["num"]} · '
            f'约 {p["wan"]} 万字 · {p["pages"]} 页 · '
            f'<a href="{b}/read.html" {G}>在线 PDF</a> · '
            f'<a href="{b}/{p["slug"]}.pdf" download {G}>下载 PDF</a></span></li>')


def do_index():
    t = IDX.read_text(encoding="utf-8")
    for s in ORDER:
        assert f'/{s}/' not in t, f"{s} 已在索引中"
    # 上一批的"新作"标记退役，只让本批带
    n_old = t.count(" · 新作 · ")
    t = t.replace(" · 新作 · ", " · ")
    anchor = '<div class="works">\n'
    assert t.count(anchor) == 1, "works 容器锚点不唯一"
    t = t.replace(anchor, anchor + "".join(card(BY[s]) for s in ORDER), 1)
    assert t.count('<div class="work">') == 66, "卡片数应为 66"
    assert t.count("<html") == 1 and t.count("</html>") == 1
    IDX.write_text(t, encoding="utf-8")
    print(f"works 索引：新增 4 张卡片置顶（62 → 66），退役旧「新作」标记 {n_old} 处")


def do_profile():
    t = PROF.read_text(encoding="utf-8")
    m = re.search(r'(<ul[^>]*>\s*)(<li style="margin-bottom:9px">)', t)
    assert m, "找不到主页新作清单"
    t = t[:m.end(1)] + "\n" + "\n".join(li(BY[s]) for s in ORDER) + "\n" + t[m.start(2):]

    old_p = re.search(r'<p>本批新作（.*?</p>', t, re.S)
    assert old_p, "找不到页脚新作摘要"
    names = "、".join(f'《{BY[s]["title"].split("：")[0]}》' for s in ORDER[:3])
    t = t[:old_p.start()] + (
        f'<p>本批新作（{PUBDATE_CN}，按创新智商排名发表）：{names}等四篇，'
        f'与同日发表的《救济之光》《不知的守夜》《法秩序的沉默前提》互为接续，各篇均已写明分工。另附三种读法：网页长文、在线 PDF 与下载 PDF。</p>'
    ) + t[old_p.end():]

    old_n = re.search(r'浏览全部(\d+)篇', t)
    assert old_n, "找不到浏览全部 N 篇"
    t = t[:old_n.start()] + "浏览全部66篇" + t[old_n.end():]

    assert t.count("<html") == 1 and t.count("</html>") == 1
    PROF.write_text(t, encoding="utf-8")
    print(f"主页：新作清单置顶 4 条，页脚 {old_n.group(1)} → 66 篇")


if __name__ == "__main__":
    do_index()
    do_profile()
