# -*- coding: utf-8 -*-
"""把胡志英本批十五篇前插到 works 索引与学员主页，并更新 publications.json。

遵循 tools/README.md 的发布事故记忆：
  · 最新作品置于列表第一位；最新序号 = 发布后作品总数（33），同批依次递减；
  · 学员主页静态区域直接显示本批新作，不只依赖延迟加载的作品列单。
胡志英主页的作品区是"进入作品"入口卡（无 .panel 样式），因此静态新作区
用内联样式自带，插在入口卡之后、返回区之前，不改动既有卡片。
roster.json 的 papers/count 由 build_roster.py 从磁盘派生，本脚本不碰。
"""
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hzy_meta import PAPERS, STUDENTS, PUBDATE_CN

STUDENT = "hu-zhiying"
AUTHOR = STUDENTS[STUDENT]["name"]
EXISTING_COUNT = STUDENTS[STUDENT]["existing"]
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
    d = json.loads((ROOT / "tools" / "hzy_report.json").read_text(encoding="utf-8"))
    papers = d["papers"]
    assert [p["num"] for p in papers] == sorted((p["num"] for p in papers), reverse=True), \
        "报告未按序号降序，前插会导致序号乱序"
    return papers


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
    text = text.replace(old, f"{total} 篇文章")
    path.write_text(text, encoding="utf-8")
    return total


NEWBLOCK_ID = "hzy-batch3"


def update_profile(papers):
    path = STU / "index.html"
    text = path.read_text(encoding="utf-8")
    assert NEWBLOCK_ID not in text, "主页已插入过本批新作区，勿重复"
    total = EXISTING_COUNT + len(papers)
    anchor = '<div class="back">'
    assert text.count(anchor) == 1, "主页返回区结构与预期不符"

    items = "".join(
        f'      <li style="margin-bottom:9px"><a href="/students/{STUDENT}/{p["slug"]}/" '
        f'style="color:var(--gold)">《{html.escape(p["title"])}》</a>'
        f'<span style="color:var(--ink2);font-size:13px"> — {html.escape(p["kind"])} · '
        f'约 {p["wan"]} 万字 · 智商 {p["old_score"]}→{p["score"]} · '
        f'<a href="/students/{STUDENT}/{p["slug"]}/read.html" style="color:var(--gold)">在线 PDF</a> · '
        f'<a href="/students/{STUDENT}/{p["slug"]}/{p["slug"]}.pdf" download '
        f'style="color:var(--gold)">下载 PDF</a></span></li>\n'
        for p in papers)

    block = f"""<div id="{NEWBLOCK_ID}" style="border:1px solid rgba(201,168,76,0.30);border-radius:10px;padding:22px 26px;margin:26px 0">
  <div style="color:var(--gold2);letter-spacing:.18em;font-size:13px;margin-bottom:6px">作 品 · {total} 篇已发表</div>
  <p class="zh-only" style="margin:0 0 10px">{AUTHOR}已有 {total} 篇作品署名发表；本批新增十五篇，覆盖过程存在论、认识论与追问者位置、判断力的制度生成、时间性与传统工艺四簇。</p>
  <p class="en-only" style="margin:0 0 10px">Hu Zhiying has {total} published works; this batch adds fifteen, spanning process ontology, the epistemology of the questioner, the institutional formation of judgement, and temporality in traditional craft.</p>
  <p class="zh-only" style="margin-top:12px"><b style="color:var(--gold2)">本批新作 · {PUBDATE_CN} · 十五篇（每篇三种读法）</b></p>
  <ul class="zh-only" style="margin:8px 0 0 1.1em;line-height:1.75;padding:0">
{items}  </ul>
  <p style="margin-top:14px"><a href="/students/{STUDENT}/works/" style="color:var(--gold)"><span class="zh-only">查看全部 {total} 篇作品 →</span><span class="en-only">See all {total} works →</span></a></p>
</div>
"""
    text = text.replace(anchor, block + anchor, 1)
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
