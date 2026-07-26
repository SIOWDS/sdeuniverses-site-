# -*- coding: utf-8 -*-
"""秦莉 works 索引：在「壹 · 卫生政策四篇」之后插入新组「贰 · 艺术哲学四篇」，
其余组序号顺延，并更新总篇数。"""
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qinli4_meta import PUBDATE_CN

ROOT = Path(__file__).resolve().parents[1]
IDX = ROOT / "public" / "students" / "qin-li" / "works" / "index.html"
REPORT = json.loads((ROOT / "tools" / "qinli4_report.json").read_text(encoding="utf-8"))
BY = {p["slug"]: p for p in REPORT["papers"]}
ORDER = ["yielded-void", "existential-verdict", "guarding-drift", "completing-arc"]
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

    group = ('<div class="grp"><div class="n">贰</div><h2>艺术哲学 · 金点子四篇</h2>\n'
             '<div class="d">同一个原初问题（艺术是唯一的存在）的四个切面：三个金点子分论「缺余」、'
             '「存在的决断」与「存在论级差」，第四篇由三者涌现出「完成弧」。'
             '四篇均把最近邻逐一切开、为核心命题做跨域形式锚定，并给出可执行的证伪条件。</div>\n'
             '<div class="cnt">4 篇</div><div class="r"></div></div>\n'
             '<div class="list">\n'
             + "\n".join(item(BY[s]) for s in ORDER) + "\n</div>\n")

    anchor = '<div class="grp"><div class="n">贰</div><h2>创作理论 · 美学生成研究</h2>'
    assert t.count(anchor) == 1, "找不到原贰组锚点"

    # 先顺延原有组号（倒序替换，避免连锁）
    for old, new in (("伍", "陆"), ("肆", "伍"), ("叁", "肆"), ("贰", "叁")):
        a = f'<div class="grp"><div class="n">{old}</div>'
        assert t.count(a) == 1, f"组号 {old} 不唯一"
        t = t.replace(a, f'<div class="grp"><div class="n">{new}</div>')

    anchor2 = '<div class="grp"><div class="n">叁</div><h2>创作理论 · 美学生成研究</h2>'
    assert t.count(anchor2) == 1
    t = t.replace(anchor2, group + anchor2, 1)

    # 总篇数
    m = re.search(r"共\s*(\d+)\s*篇", t)
    assert m, "找不到总篇数"
    total = int(m.group(1))
    t = re.sub(r"共\s*\d+\s*篇", f"共 {total + 4} 篇", t)

    assert t.count("<html") == 1 and t.count("</html>") == 1
    assert t.count('<div class="grp">') == 6
    IDX.write_text(t, encoding="utf-8")
    print(f"works 索引：新增 4 篇（{total} → {total + 4}），组数 6")


if __name__ == "__main__":
    main()
