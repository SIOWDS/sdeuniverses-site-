# -*- coding: utf-8 -*-
"""把孔凡鹤本批八篇前插到 works 索引与学员主页，并更新 publications.json。

遵循 tools/README.md 的发布事故记忆：
  · 最新作品置于列表第一位；最新序号 = 发布后作品总数（40），同批依次递减；
  · 学员主页静态区域直接显示本批新作，不只依赖延迟加载的作品列单。
roster.json 的 papers/count 由 build_roster.py 从磁盘派生，本脚本不碰。
"""
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kfh_meta import AUTHOR, STUDENT, PUBDATE_CN, EXISTING_COUNT

ROOT = Path(__file__).resolve().parents[1]
STU = ROOT / "public" / "students" / STUDENT
CN = "零一二三四五六七八九十"


def cn(n: int) -> str:
    if n <= 10:
        return CN[n]
    if n < 20:
        return "十" + CN[n - 10]
    return CN[n // 10] + "十" + (CN[n % 10] if n % 10 else "")


def load():
    d = json.loads((ROOT / "tools" / "kfh_report.json").read_text(encoding="utf-8"))
    return d["papers"]          # 已按 num 降序（40→33）


def card(p):
    base = f'/students/{STUDENT}/{p["slug"]}'
    return f"""  <div class="work">
    <span class="chip">之{cn(p["num"])} · 新作 · {html.escape(p["kind"])} · 深化增补版</span>
    <h2>{html.escape(p["title"])}</h2>
    <p class="hook">{html.escape(p["hook"])}</p>
    <div class="meta">约 {p["wan"]} 万字 · {p["pages"]} 页 · SDE 创新智商 {p["old_score"]} → {p["score"]}（编辑自评，待独立复评） · 三种读法 · 发表于{PUBDATE_CN}</div>
    <div class="modes">
      <a class="m primary" href="{base}/">📖 长文阅读</a>
      <a class="m ghost" href="{base}/read.html">📄 在线 PDF</a>
      <a class="m ghost" href="{base}/{p["slug"]}.pdf" download>⬇ 下载 PDF</a>
    </div>
  </div>
"""


def update_works(papers):
    path = STU / "works" / "index.html"
    text = path.read_text(encoding="utf-8")
    for p in papers:
        assert f'/{p["slug"]}/' not in text, f'{p["slug"]} 已在 works 索引中，勿重复插入'
    total = EXISTING_COUNT + len(papers)
    marker = '<div class="works">'
    assert marker in text, "works 索引缺 .works 容器"
    text = text.replace(marker, marker + "\n" + "".join(card(p) for p in papers), 1)
    old = f"{EXISTING_COUNT} 篇文章"
    assert old in text, f"未找到篇数字样：{old}"
    text = text.replace(old, f"{total} 篇文章", 1)
    path.write_text(text, encoding="utf-8")
    return total


def update_profile(papers):
    path = STU / "index.html"
    text = path.read_text(encoding="utf-8")
    total = EXISTING_COUNT + len(papers)
    start = text.find('<div class="works">')
    end = text.find('<div class="back">', start)
    assert 0 < start < end, "主页 works 区结构与预期不符"

    items = "".join(
        f'      <li><a href="/students/{STUDENT}/{p["slug"]}/" style="color:var(--gold)">'
        f'《{html.escape(p["title"])}》</a>'
        f'<span style="color:var(--ink2);font-size:13px"> — {html.escape(p["kind"])} · '
        f'约 {p["wan"]} 万字 · <a href="/students/{STUDENT}/{p["slug"]}/read.html" '
        f'style="color:var(--gold)">在线 PDF</a> · '
        f'<a href="/students/{STUDENT}/{p["slug"]}/{p["slug"]}.pdf" download '
        f'style="color:var(--gold)">下载 PDF</a></span></li>\n'
        for p in papers)

    block = f"""<div class="works">
  <div class="panel">
    <div class="tag zh-only">作 品 · {total} 篇已发表</div>
    <div class="tag en-only">{total} PUBLISHED</div>
    <p class="zh-only">{AUTHOR}已有 {total} 篇作品署名发表，覆盖家庭教育、青少年主体生成、身体感受、锻炼机制、关系结构，以及本批新增的灾害生成论与存在感研究两簇。</p>
    <p class="en-only">Kong Fanhe has published {total} works on family education, adolescent agency, embodied feeling, exercise, relational structures, and — newly added in this batch — disaster genesis and the formation of the sense of existing.</p>
    <p class="zh-only" style="margin-top:14px"><b style="color:var(--gold2)">本批新作 · {PUBDATE_CN} · 八篇（每篇三种读法）</b></p>
    <ul class="zh-only" style="margin:8px 0 0 1.1em;line-height:1.85">
{items}    </ul>
    <p style="margin-top:14px"><a href="/students/{STUDENT}/works/" style="color:var(--gold)"><span class="zh-only">查看全部 {total} 篇作品 →</span><span class="en-only">See all {total} works →</span></a></p>
  </div>
  """
    text = text[:start] + block + text[end:]
    path.write_text(text, encoding="utf-8")
    return total


def update_publications(papers):
    path = ROOT / "public" / "students" / "publications.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    entry = next((x for x in data["students"] if x["slug"] == STUDENT), None)
    if entry is None:
        entry = {"slug": STUDENT, "name": AUTHOR, "count": 0, "items": []}
        data["students"].append(entry)
    have = {x["url"] for x in entry["items"]}
    new = []
    for p in papers:
        url = f'/students/{STUDENT}/{p["slug"]}/'
        if url in have:
            continue
        new.append({"number": p["num"], "title": p["title"], "url": url,
                    "kind": p["kind"], "summary": p["hook"]})
    entry["items"] = new + entry["items"]
    entry["count"] = len(entry["items"])
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(new), entry["count"]


def main():
    papers = load()
    t1 = update_works(papers)
    t2 = update_profile(papers)
    added, count = update_publications(papers)
    print(f"  works 索引：前插 {len(papers)} 张卡，篇数 {EXISTING_COUNT} → {t1}，"
          f"首卡序号 之{cn(papers[0]['num'])}")
    print(f"  学员主页：静态新作区 {len(papers)} 条，篇数标 {t2}")
    print(f"  publications.json：新增 {added} 条，条目合计 {count}")


if __name__ == "__main__":
    main()
