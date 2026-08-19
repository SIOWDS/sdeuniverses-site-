# -*- coding: utf-8 -*-
"""第二批索引更新：高鹏 / 张琼 / 阳涌 前插新卡并修正主页静态区。"""
import html, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from batch3_meta import PAPERS, STUDENTS, PUBDATE_CN

ROOT = Path(__file__).resolve().parents[1]
STU = ROOT / "public" / "students"
CN = "零一二三四五六七八九十"

def cn(n):
    if n <= 10: return CN[n]
    if n < 20:  return "十" + CN[n - 10]
    return CN[n // 10] + "十" + (CN[n % 10] if n % 10 else "")

def numlabel(sl, num):
    return f"之{num}" if STUDENTS[sl]["numstyle"] == "arabic" else f"之{cn(num)}"

def card(p):
    sl, base = p["student"], f'/students/{p["student"]}/{p["slug"]}'
    return f"""  <div class="work">
    <span class="chip">{numlabel(sl, p["num"])} · 新作 · {html.escape(p["kind"])} · 深化增补版</span>
    <h2>{html.escape(p["title"])}</h2>
    <p class="hook">{html.escape(p["hook"])}</p>
    <div class="meta">约 {p["wan"]} 万字 · {p["pages"]} 页 · SDE 创新智商 {p["old_score"]} → {p["score"]}（编辑自评，待独立复评） · 本批评分第 {p["rank"]} · 三种读法 · 发表于{PUBDATE_CN}</div>
    <div class="modes">
      <a class="m primary" href="{base}/">📖 长文阅读</a>
      <a class="m ghost" href="{base}/read.html">📄 在线 PDF</a>
      <a class="m ghost" href="{base}/{p["slug"]}.pdf" download>⬇ 下载 PDF</a>
    </div>
  </div>
"""

def prepend_works(sl, ps):
    path = STU / sl / "works" / "index.html"
    t = path.read_text(encoding="utf-8")
    for p in ps:
        assert f'/{p["slug"]}/' not in t, f'{p["slug"]} 已在 {sl} works 中'
    m = f'<{"main" if STUDENTS[sl]["container"] == "wrap" else "div"} class="{STUDENTS[sl]["container"]}">'
    assert m in t, f"{sl} 缺 {m} 容器"
    path.write_text(t.replace(m, m + "\n" + "".join(card(p) for p in ps), 1), encoding="utf-8")

def static_block(sl, ps, accent="var(--gold)", head="#1E3323"):
    items = "".join(
        f'      <li style="margin-bottom:9px"><a href="/students/{sl}/{p["slug"]}/" style="color:{accent}">《{html.escape(p["title"])}》</a>'
        f'<span style="font-size:13px;opacity:.8"> — {html.escape(p["kind"])} · {numlabel(sl, p["num"])} · 约 {p["wan"]} 万字 · '
        f'<a href="/students/{sl}/{p["slug"]}/read.html" style="color:{accent}">在线 PDF</a> · '
        f'<a href="/students/{sl}/{p["slug"]}/{p["slug"]}.pdf" download style="color:{accent}">下载 PDF</a></span></li>\n'
        for p in ps)
    return f"""<div style="max-width:820px;margin:28px auto 0;padding:0 24px">
  <div style="border:1px solid rgba(201,168,76,0.42);border-radius:14px;padding:20px 24px;background:rgba(201,168,76,0.06)">
    <div style="font-size:12px;letter-spacing:.28em;color:{accent};margin-bottom:10px">本 批 新 作 · {PUBDATE_CN} · {len(ps)} 篇</div>
    <ul style="margin:0 0 0 1.1em;line-height:1.8;padding:0">
{items}    </ul>
    <p style="margin:12px 0 0"><a href="/students/{sl}/works/" style="color:{accent}">查看全部作品 →</a></p>
  </div>
</div>
"""

def insert_profile(sl, ps):
    """在主页第一个作品入口之前插入本批静态区。"""
    path = STU / sl / "index.html"
    t = path.read_text(encoding="utf-8")
    anchor = None
    for pat in (r'<a class="works-entry"[^>]*>', r'<a class="works"[^>]*>', r'<div class="works">', r'<footer[ >]'):
        m = re.search(pat, t)
        if m:
            anchor = m.start(); break
    assert anchor is not None, f"{sl} 主页未找到作品入口锚点"
    t = t[:anchor] + static_block(sl, ps) + t[anchor:]
    # 顺带修正过期的总篇数字样
    total = STUDENTS[sl]["existing"] + len(ps)
    t = re.sub(r'浏览全部\d+篇', f'浏览全部{total}篇', t)
    path.write_text(t, encoding="utf-8")
    return total

def update_publications(papers):
    path = STU / "publications.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    by = {x["slug"]: x for x in data["students"]}
    for sl in {p["student"] for p in papers}:
        e = by[sl]; have = {x["url"] for x in e["items"]}
        new = [{"number": p["num"], "title": p["title"], "url": f'/students/{sl}/{p["slug"]}/',
                "kind": p["kind"], "summary": p["hook"]}
               for p in papers if p["student"] == sl and f'/students/{sl}/{p["slug"]}/' not in have]
        e["items"] = new + e["items"]; e["count"] = len(e["items"])
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def main():
    papers = json.loads((ROOT / "tools" / "batch3_report.json").read_text(encoding="utf-8"))["papers"]
    groups = {}
    for p in papers:
        groups.setdefault(p["student"], []).append(p)
    for sl, ps in groups.items():
        ps.sort(key=lambda x: -x["num"])
        prepend_works(sl, ps)
        total = insert_profile(sl, ps)
        print(f'  {STUDENTS[sl]["name"]}：works 前插 {len(ps)} 张（{numlabel(sl, ps[0]["num"])} 起），'
              f'主页静态区已加，篇数 → {total}')
    update_publications(papers)

if __name__ == "__main__":
    main()
