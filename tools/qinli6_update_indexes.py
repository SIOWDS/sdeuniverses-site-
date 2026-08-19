# -*- coding: utf-8 -*-
"""秦莉 works 索引：在「伍 · 创作理论」之后插入新组「陆 · 跨媒介与改编研究」，
随笔／诗选／长篇小说三组序号顺延，并把总篇数、论文数、分组数与总字数四处口径改准。
另更新 publications.json 与学员主页。
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STU = ROOT / "public" / "students" / "qin-li"
IDX = STU / "works" / "index.html"
REPORT = json.loads((ROOT / "tools" / "qinli6_report.json").read_text(encoding="utf-8"))
BY = {p["slug"]: p for p in REPORT["papers"]}
ORDER = ["line-of-separation", "negative-print",
         "two-time-sovereignties", "obligatory-perceptual-work"]
PUB_ISO = "2026-07-28"
PUB_CN = "2026年7月28日"


def item(p):
    b = f'/students/qin-li/{p["slug"]}'
    return (f'<div class="it"><h3><a href="{b}/">{html.escape(p["title"])}</a>'
            f'<span class="sc">创新智商 {p["old_score"]}→{p["score"]}</span></h3>'
            f'<div class="m">约 {p["wan"]} 万字 · {p["pages"]} 页 · 发表于 {PUB_ISO}</div>'
            f'<div class="lk"><a href="{b}/">📖 长文阅读</a>'
            f'<a href="{b}/read.html">📄 在线 PDF</a>'
            f'<a href="{b}/{p["slug"]}.pdf" download>⬇ 下载 PDF</a></div></div>')


def li(p):
    b = f'/students/qin-li/{p["slug"]}'
    return (f'      <li><a href="{b}/" style="color:var(--gold)">《{html.escape(p["title"])}》</a>'
            f'<span style="color:var(--ink2);font-size:13px"> — {html.escape(p["kind"])} · '
            f'约 {p["wan"]} 万字 · <a href="{b}/read.html" style="color:var(--gold)">在线 PDF</a> · '
            f'<a href="{b}/{p["slug"]}.pdf" download style="color:var(--gold)">下载 PDF</a></span></li>\n')


def works_index():
    t = IDX.read_text(encoding="utf-8")
    for s in ORDER:
        assert f"/{s}/" not in t, f"{s} 已在索引中"

    group = ('<div class="grp"><div class="n">陆</div><h2>跨媒介与改编研究 · 《追忆似水年华》四篇</h2>\n'
             '<div class="d">同一个原初问题（意识流与影视语言的切磋）的四个切面，'
             '以普鲁斯特原著与拉乌·鲁兹一九九九年的同名电影为分析现场。'
             '三篇分论「时间的两种主权」「衔接权的不可代偿」与「负片」，'
             '第四篇回过头来修正自己的立论词——真正的理论对象不是被命名的痕迹，'
             '而是那条切开失败内部差异的分离线。'
             '四篇各自与场域里最近的对手正面划界：查特曼的两条时序、巴特的可写文本、'
             '劳拉·马克斯的触感视觉、德勒兹的时间-影像、巴赞、伊瑟尔的空白与布莱希特的间离；'
             '其中《负片》给出一套眼动可测的证伪设计。</div>\n'
             '<div class="cnt">4 篇</div><div class="r"></div></div>\n'
             '<div class="list">\n'
             + "\n".join(item(BY[s]) for s in ORDER) + "\n</div>\n")

    # 先倒序顺延原有组号，避免连锁
    for old, new in (("捌", "玖"), ("柒", "捌"), ("陆", "柒")):
        a = f'<div class="grp"><div class="n">{old}</div>'
        assert t.count(a) == 1, f"组号 {old} 不唯一"
        t = t.replace(a, f'<div class="grp"><div class="n">{new}</div>')

    anchor = '<div class="grp"><div class="n">柒</div><h2>随 笔</h2>'
    assert t.count(anchor) == 1, "找不到随笔组锚点"
    t = t.replace(anchor, group + anchor, 1)

    fixes = [("共 45 篇 · 论文 27 · 随笔 9 · 诗 8 · 长篇小说 1",
              "共 49 篇 · 论文 31 · 随笔 9 · 诗 8 · 长篇小说 1"),
             ("分八组：学术论文 27 篇", "分九组：学术论文 31 篇"),
             ("文学作品 18 篇", "文学作品 18 篇")]
    for a, b in fixes:
        if a in t and a != b:
            t = t.replace(a, b)

    add = sum(float(BY[s]["wan"]) for s in ORDER)
    m = re.search(r"约 ([\d.]+) 万字，分九组", t)
    assert m, "找不到总字数锚点"
    t = t.replace(f"约 {m.group(1)} 万字，分九组",
                  f"约 {float(m.group(1)) + add:.1f} 万字，分九组")
    t = re.sub(r"(共 )45( 篇)", r"\g<1>49\g<2>", t)
    t = t.replace("<b data-publication-count>45</b>", "<b data-publication-count>49</b>")

    assert t.count('<div class="grp">') == 9, f'组数 {t.count(chr(60)+"div class=" + chr(34) + "grp" + chr(34) + chr(62))}，应为 9'
    assert t.count("<html") == 1 and t.count("</html>") == 1
    IDX.write_text(t, encoding="utf-8")
    print(f"  ① works 索引：新增一组 4 篇（45 → 49），论文 27 → 31，组数 9，本批 {add:.1f} 万字")


def publications():
    f = ROOT / "public" / "students" / "publications.json"
    d = json.loads(f.read_text(encoding="utf-8"))
    rec = next(s for s in d["students"] if s["slug"] == "qin-li")
    have = {i["url"] for i in rec["items"]}
    new = []
    for s in ORDER:
        p = BY[s]
        url = f"/students/qin-li/{s}/"
        assert url not in have, f"{s} 已在 publications"
        new.append({"number": p["num"], "title": p["title"], "url": url,
                    "kind": p["kind"], "summary": p["hook"]})
    rec["items"] = new + rec["items"]
    rec["count"] = len(rec["items"])
    assert rec["count"] == 49, f'publications 计 {rec["count"]} 条，应为 49'
    f.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    empty = sum(1 for s in d["students"] for i in s["items"] if not i.get("summary"))
    print(f"  ② publications.json：45 → 49；全站空摘要 {empty} 条")


def profile():
    f = STU / "index.html"
    t = f.read_text(encoding="utf-8")
    i = t.index('<p class="zh-only" style="margin-top:14px"><b style="color:var(--gold2)">本批新作')
    j = t.index("</ul>", i) + len("</ul>")
    block = ('<p class="zh-only" style="margin-top:14px"><b style="color:var(--gold2)">'
             f'本批新作 · {PUB_CN} · 四篇（每篇三种读法）</b></p>\n'
             '    <ul class="zh-only" style="margin:8px 0 0 1.1em;line-height:1.85">\n'
             + "".join(li(BY[s]) for s in ORDER) + '    </ul>')
    t = t[:i] + block + t[j:]
    t = t.replace("<b data-publication-count>45</b>", "<b data-publication-count>49</b>")
    t = re.sub(r"(查看全部作品（)45( 篇)", r"\g<1>49\g<2>", t)
    t = re.sub(r"(作 品 · )45( 篇已发表)", r"\g<1>49\g<2>", t)
    assert t.count("<html") == 1 and t.count("<ul") == t.count("</ul>")
    f.write_text(t, encoding="utf-8")
    print("  ③ 学员主页：新作区块换为本批四篇，计数 45 → 49")


if __name__ == "__main__":
    works_index()
    publications()
    profile()
