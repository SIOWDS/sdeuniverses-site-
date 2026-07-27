# -*- coding: utf-8 -*-
"""孔凡鹤第二批四篇上站后的五处口径更新：
  ① works 索引：四条新卡置顶 + 篇数 40→44 + 顺手清掉页头的招牌词
  ② 学员主页：新作区块换成本批四篇（旧批八篇的清单收进 works 索引即可）+ 篇数 40→44
  ③ publications.json：四条新条目置顶 + count 40→44
roster.json 由 build_roster.py 派生，本脚本不碰。
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STU = ROOT / "public" / "students" / "kong-fanhe"
REPORT = json.loads((ROOT / "tools" / "kfh2_report.json").read_text(encoding="utf-8"))
BY = {p["slug"]: p for p in REPORT["papers"]}
ORDER = ["co-constructive-field", "attribution-sensitivity",
         "ripened-intuition", "co-creative-disorientation"]
PUB_CN = "2026年7月27日"
CN = {44: "四十四", 43: "四十三", 42: "四十二", 41: "四十一"}


def work_card(p):
    b = f'/students/kong-fanhe/{p["slug"]}'
    return (
        '  <div class="work">\n'
        f'    <span class="chip">之{CN[p["num"]]} · 新作 · {html.escape(p["kind"])} · 深化增补版</span>\n'
        f'    <h2>{html.escape(p["title"])}</h2>\n'
        f'    <p class="hook">{html.escape(p["hook"])}</p>\n'
        f'    <div class="meta">约 {p["wan"]} 万字 · {p["pages"]} 页 · '
        f'SDE 创新智商 {p["old_score"]} → {p["score"]}（编辑自评，待独立复评） · '
        f'三种读法 · 发表于{PUB_CN}</div>\n'
        '    <div class="modes">\n'
        f'      <a class="m primary" href="{b}/">📖 长文阅读</a>\n'
        f'      <a class="m ghost" href="{b}/read.html">📄 在线 PDF</a>\n'
        f'      <a class="m ghost" href="{b}/{p["slug"]}.pdf" download>⬇ 下载 PDF</a>\n'
        '    </div>\n'
        '  </div>\n')


def li(p):
    b = f'/students/kong-fanhe/{p["slug"]}'
    return (f'      <li><a href="{b}/" style="color:var(--gold)">《{html.escape(p["title"])}》</a>'
            f'<span style="color:var(--ink2);font-size:13px"> — {html.escape(p["kind"])} · '
            f'约 {p["wan"]} 万字 · <a href="{b}/read.html" style="color:var(--gold)">在线 PDF</a> · '
            f'<a href="{b}/{p["slug"]}.pdf" download style="color:var(--gold)">下载 PDF</a></span></li>\n')


def sub1(t, old, new, label):
    assert t.count(old) == 1, f"{label}：锚点出现 {t.count(old)} 次（须为 1）"
    return t.replace(old, new, 1)


def works_index():
    f = STU / "works" / "index.html"
    t = f.read_text(encoding="utf-8")
    for s in ORDER:
        assert f"/{s}/" not in t, f"{s} 已在索引中"

    t = sub1(t, '<div class="works">\n  <div class="work">',
             '<div class="works">\n' + "".join(work_card(BY[s]) for s in ORDER) + '  <div class="work">',
             "works 列表开头")
    t = sub1(t, '<b data-publication-count>40</b> 篇', '<b data-publication-count>44</b> 篇', "徽标篇数")
    t = sub1(t, 'SDE 学员 · 家庭教育与身体发生学 · 40 篇文章',
             'SDE 学员 · 家庭教育与身体经验研究 · 44 篇文章', "页头口径（顺带清招牌词）")

    assert t.count("<html") == 1 and t.count("</html>") == 1
    assert t.count('<div class="work">') == 44, f'卡片数 {t.count(chr(60)+"div class=" + chr(34) + "work" + chr(34) + chr(62))}，预期 44'
    # 断言只管本批四张新卡与页头；旧批论文勾子里的招牌词属另一次改姓作业，不在本批擅动
    head_and_new = t[:t.index('  <div class="work">\n    <span class="chip">之四十 ·')]
    assert "发生学" not in head_and_new, "本批新卡或页头仍有招牌词"
    f.write_text(t, encoding="utf-8")
    print(f"  ① works 索引：新增 4 张卡（40 → 44），页头招牌词已清")


def profile():
    f = STU / "index.html"
    t = f.read_text(encoding="utf-8")

    # 新作清单整体换成本批四篇
    i = t.index('<p class="zh-only" style="margin-top:14px"><b style="color:var(--gold2)">本批新作')
    j = t.index("</ul>", i) + len("</ul>")
    block = ('<p class="zh-only" style="margin-top:14px"><b style="color:var(--gold2)">'
             f'本批新作 · {PUB_CN} · 四篇（每篇三种读法）</b></p>\n'
             '    <ul class="zh-only" style="margin:8px 0 0 1.1em;line-height:1.85">\n'
             + "".join(li(BY[s]) for s in ORDER) + '    </ul>')
    t = t[:i] + block + t[j:]

    t = sub1(t, '<b data-publication-count>40</b> 篇', '<b data-publication-count>44</b> 篇', "主页徽标")
    t = sub1(t, '<div class="tag zh-only">作 品 · 40 篇已发表</div>',
             '<div class="tag zh-only">作 品 · 44 篇已发表</div>', "中文作品标签")
    t = sub1(t, '<div class="tag en-only">40 PUBLISHED</div>',
             '<div class="tag en-only">44 PUBLISHED</div>', "英文作品标签")
    t = sub1(t, '孔凡鹤已有 40 篇作品署名发表，覆盖家庭教育、青少年主体生成、身体感受、锻炼机制、关系结构，'
                '以及本批新增的灾害生成论与存在感研究两簇。',
             '孔凡鹤已有 44 篇作品署名发表，覆盖家庭教育、青少年主体生成、身体感受、锻炼机制、关系结构、'
             '灾害生成论与存在感研究，以及本批新增的心理治疗改变机制一簇。', "中文简介")
    t = sub1(t, 'Kong Fanhe has published 40 works', 'Kong Fanhe has published 44 works', "英文简介")
    t = sub1(t, 'and — newly added in this batch — disaster genesis and the formation of the sense of existing.',
             'disaster genesis, the formation of the sense of existing, and — newly added in this batch — '
             'the mechanisms of change in psychotherapy.', "英文簇名")
    t = sub1(t, '<span class="zh-only">查看全部 40 篇作品 →</span>',
             '<span class="zh-only">查看全部 44 篇作品 →</span>', "中文全部作品链接")
    t = sub1(t, '<span class="en-only">See all 40 works →</span>',
             '<span class="en-only">See all 44 works →</span>', "英文全部作品链接")

    assert t.count("<html") == 1 and t.count("</html>") == 1
    assert t.count("<ul") == t.count("</ul>"), "ul 不配对"
    f.write_text(t, encoding="utf-8")
    print("  ② 学员主页：新作区块换为本批四篇，六处计数 40 → 44")


def publications():
    f = ROOT / "public" / "students" / "publications.json"
    d = json.loads(f.read_text(encoding="utf-8"))
    rec = next(s for s in d["students"] if s["slug"] == "kong-fanhe")
    have = {i["url"] for i in rec["items"]}
    new = []
    for s in ORDER:
        p = BY[s]
        url = f'/students/kong-fanhe/{s}/'
        assert url not in have, f"{s} 已在 publications"
        new.append({"number": p["num"], "title": p["title"], "url": url,
                    "kind": p["kind"], "summary": p["hook"]})
    rec["items"] = new + rec["items"]
    rec["count"] = len(rec["items"])
    assert rec["count"] == 44, f'publications 计 {rec["count"]} 条，预期 44'
    f.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    empty = sum(1 for s in d["students"] for i in s["items"] if not i.get("summary"))
    print(f"  ③ publications.json：kong-fanhe 40 → 44；全站空摘要 {empty} 条")


if __name__ == "__main__":
    works_index()
    profile()
    publications()
