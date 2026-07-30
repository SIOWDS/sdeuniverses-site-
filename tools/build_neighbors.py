#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 public/kb/neighbors.json —— 站内近邻检索的专用索引。

为什么不能直接用 publications.json：
  近邻检索要抓的恰恰是**自造概念名**（自噬性稳态、拮抗负荷、品核、互裁……），
  而这些名字在很多篇里根本不在标题里，只在**副标题与关键词**里。
  拿 publications 的 title+summary 去匹配「自噬性稳态」，会漏掉张琼那篇
  《改不动的机器》——那正是最该被召回的一篇（概念同族、同一作者、同一专栏）。
  漏召回在这个端点上是静默失败：产出照样生成，只是概念被第二次发明。

所以索引必须把四类文本都收进来：标题、副标题、关键词、那一刀（一句话判断）。
一句话判断的取值顺序：.innov .txt（发表时逐篇写的"本文的那一刀"）→ publications 的 summary
→ meta description。三者都缺就留空，仍可参与匹配（靠标题与关键词）。

用法：python3 tools/build_neighbors.py   （幂等，直接覆盖输出文件）
"""
import json, re, os, io, glob, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, "public")
OUT = os.path.join(PUB, "kb", "neighbors.json")

# publications.json：拿栏目名(kind)、作者名与备用的一句话判断
pub_by_url, name_by_slug = {}, {}
try:
    d = json.load(io.open(os.path.join(PUB, "students", "publications.json"), encoding="utf-8"))
    for st in d.get("students", []):
        name_by_slug[st.get("slug", "")] = st.get("name", "")
        for it in st.get("items", []):
            if it.get("url"):
                pub_by_url[it["url"]] = it
except Exception as e:
    print("publications.json 读取失败（继续，只是少了栏目名与备用判断）：", e)


def txt(x):
    x = re.sub(r"<[^>]+>", " ", x or "")
    x = x.replace("&amp;", "&").replace("&nbsp;", " ").replace("&quot;", '"').replace("&#39;", "'")
    return re.sub(r"\s+", " ", x).strip()


def one(pat, h, g=1):
    m = re.search(pat, h, re.S)
    return txt(m.group(g)) if m else ""


rows, skipped = [], 0
for f in sorted(glob.glob(os.path.join(PUB, "**", "index.html"), recursive=True)):
    rel = "/" + os.path.relpath(f, PUB).replace(os.sep, "/")
    u = rel[:-len("index.html")]                      # /students/xx/yy/
    if u.count("/") < 3:                              # 只要篇目页，不要栏目首页
        continue
    if re.match(r"^/students/[^/]+/works/$", u):
        continue
    try:
        h = io.open(f, encoding="utf-8", errors="replace").read()
    except Exception:
        skipped += 1; continue
    t = one(r'<h1 class="art-title">(.*?)</h1>', h)
    if not t:
        continue                                      # 没有 art-title 的不是篇目页
    sub = one(r'<div class="art-subtitle">(.*?)</div>', h) or one(r'<div class="art-sub">(.*?)</div>', h)
    kw = one(r'<div class="keywords">(.*?)</div>', h) or one(r'<p class="kw">(.*?)</p>', h)
    kw = re.sub(r"^\s*(关键词|Keywords)\s*[：:]?\s*", "", kw)
    line = one(r'<div class="innov">.*?<div class="txt">(.*?)</div>', h)
    it = pub_by_url.get(u) or {}
    if not line:
        line = txt(it.get("summary", ""))
    if not line:
        line = one(r'<meta name="description" content="(.*?)">', h)
    seg = u.strip("/").split("/")
    au = name_by_slug.get(seg[1], "") if seg and seg[0] == "students" and len(seg) > 1 else ""
    au_slug = seg[1] if seg and seg[0] == "students" and len(seg) > 1 else ""
    rows.append(dict(t=t[:200], sub=sub[:220], kw=kw[:220], u=u,
                     kind=it.get("kind", "") or (seg[0] if seg else ""),
                     line=line[:400], au=au, auSlug=au_slug, sec=seg[0] if seg else ""))

rows.sort(key=lambda r: r["u"])
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump({"generated": __import__("datetime").date.today().isoformat(), "n": len(rows), "items": rows},
          io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

有副 = sum(1 for r in rows if r["sub"])
有键 = sum(1 for r in rows if r["kw"])
有刀 = sum(1 for r in rows if r["line"])
from collections import Counter
print("写出 %s：%d 篇 · %.0f KB" % (os.path.relpath(OUT, ROOT), len(rows), os.path.getsize(OUT) / 1024))
print("  带副标题 %d · 带关键词 %d · 带一句话判断 %d · 跳过读不出的 %d" % (有副, 有键, 有刀, skipped))
print("  分栏目：", Counter(r["sec"] for r in rows).most_common(8))
