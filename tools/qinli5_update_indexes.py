# -*- coding: utf-8 -*-
"""秦莉 works 索引：在「贰 · 艺术哲学四篇」之后插入新组「叁 · 爱的生成机制四篇」，
其余组序号顺延，并把总篇数、论文数与分组数三处口径一并改准。"""
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[1]
IDX = ROOT / "public" / "students" / "qin-li" / "works" / "index.html"
REPORT = json.loads((ROOT / "tools" / "qinli5_report.json").read_text(encoding="utf-8"))
BY = {p["slug"]: p for p in REPORT["papers"]}
ORDER = ["other-handedness", "residual-orientation", "decisive-touch", "beheld-flame"]
PUB_ISO = "2026-07-27"


def item(p):
    b = f'/students/qin-li/{p["slug"]}'
    return (f'<div class="it"><h3><a href="{b}/">{html.escape(p["title"])}</a>'
            f'<span class="sc">创新智商 {p["old_score"]}→{p["score"]}</span></h3>'
            f'<div class="m">约 {p["wan"]} 万字 · {p["pages"]} 页 · 发表于 {PUB_ISO}</div>'
            f'<div class="lk"><a href="{b}/">📖 长文阅读</a>'
            f'<a href="{b}/read.html">📄 在线 PDF</a>'
            f'<a href="{b}/{p["slug"]}.pdf" download>⬇ 下载 PDF</a></div></div>')


def main():
    t = IDX.read_text(encoding="utf-8")
    for s in ORDER:
        assert f"/{s}/" not in t, f"{s} 已在索引中"

    group = ('<div class="grp"><div class="n">叁</div><h2>爱的生成机制 · 金点子四篇</h2>\n'
             '<div class="d">同一个原初问题（爱是被滋养长出来的，不是想出来的）的四个切面：'
             '三个金点子分论「被朝见」「决触」与「剩余朝向」，第四篇由三者涌现出「他手性」。'
             '四篇都把最强的近邻逐一切开——列维纳斯的面容、布伯的「之间」、布朗的脆弱性展露、'
             '拉康的他者欲望、科胡特的转变性内化、比昂的涵容、戈特曼的修复尝试——'
             '并各自给出可操作的证伪条件。</div>\n'
             '<div class="cnt">4 篇</div><div class="r"></div></div>\n'
             '<div class="list">\n'
             + "\n".join(item(BY[s]) for s in ORDER) + "\n</div>\n")

    # 先倒序顺延原有组号，避免连锁
    for old, new in (("陆", "柒"), ("伍", "陆"), ("肆", "伍"), ("叁", "肆")):
        a = f'<div class="grp"><div class="n">{old}</div>'
        assert t.count(a) == 1, f"组号 {old} 不唯一"
        t = t.replace(a, f'<div class="grp"><div class="n">{new}</div>')

    anchor = '<div class="grp"><div class="n">肆</div><h2>创作理论 · 美学生成研究</h2>'
    assert t.count(anchor) == 1, "找不到创作理论组锚点"
    t = t.replace(anchor, group + anchor, 1)

    # 三处计数口径
    n = t.count("共 37 篇")
    assert n == 3, f"总篇数出现 {n} 次，预期 3"
    t = t.replace("共 37 篇", "共 41 篇")
    for a, b in (("论文 19 · 随笔 9", "论文 23 · 随笔 9"),
                 ("分六组：学术论文 19 篇", "分七组：学术论文 23 篇")):
        assert t.count(a) == 1, f"口径锚点不唯一: {a}"
        t = t.replace(a, b)

    m = re.search(r"约 ([\d.]+) 万字，分七组", t)
    assert m, "找不到总字数"
    total_wan = float(m.group(1)) + sum(float(BY[s]["wan"]) for s in ORDER)
    t = t.replace(f"约 {m.group(1)} 万字，分七组", f"约 {total_wan:.1f} 万字，分七组")

    assert t.count("<html") == 1 and t.count("</html>") == 1
    assert t.count('<div class="grp">') == 7, "组数应为 7"
    IDX.write_text(t, encoding="utf-8")
    print(f"works 索引：新增 4 篇（37 → 41），论文 19 → 23，组数 7，总字数 {total_wan:.1f} 万")


if __name__ == "__main__":
    main()
