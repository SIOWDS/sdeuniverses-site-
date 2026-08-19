# -*- coding: utf-8 -*-
"""Top5 索引更新：高鹏 / 张琼 前插新卡并修正主页静态区；蔡彦建 profile + works。

遵循 tools/README.md：最新作品置顶、最新序号 = 总数、主页静态区直接显示本批新作。
roster 的 papers/count 由 build_roster.py 派生；本脚本只补蔡彦的身份字段。
"""
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from top5_meta import PAPERS, STUDENTS, PUBDATE_CN

ROOT = Path(__file__).resolve().parents[1]
STU = ROOT / "public" / "students"
SKEL, SKEL_NAME = "kong-fanhe", "孔凡鹤"      # 蔡彦借骨架
CN = "零一二三四五六七八九十"


def cn(n):
    if n <= 10:
        return CN[n]
    if n < 20:
        return "十" + CN[n - 10]
    return CN[n // 10] + "十" + (CN[n % 10] if n % 10 else "")


def numlabel(sl, num):
    return f"之{num}" if STUDENTS[sl]["numstyle"] == "arabic" else f"之{cn(num)}"


def load():
    d = json.loads((ROOT / "tools" / "top5_report.json").read_text(encoding="utf-8"))
    return d["papers"]


def card(p):
    sl = p["student"]
    base = f'/students/{sl}/{p["slug"]}'
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


def prepend_works(sl, papers):
    path = STU / sl / "works" / "index.html"
    text = path.read_text(encoding="utf-8")
    for p in papers:
        assert f'/{p["slug"]}/' not in text, f'{p["slug"]} 已在 {sl} works 索引中'
    marker = '<div class="works">'
    assert marker in text, f"{sl} works 索引缺 .works 容器"
    text = text.replace(marker, marker + "\n" + "".join(card(p) for p in papers), 1)
    path.write_text(text, encoding="utf-8")


def fix_gao_peng_profile(papers):
    path = STU / "gao-peng" / "index.html"
    text = path.read_text(encoding="utf-8")
    total = STUDENTS["gao-peng"]["existing"] + len(papers)
    old = re.search(r'<p>本批新作：.*?</p><span class="go">浏览全部\d+篇 →</span>', text, re.S)
    assert old, "高鹏主页的作品入口文案未找到"
    titles = "、".join(f'《{p["title"].split("：")[0]}》' for p in papers)
    new = (f'<p>本批新作（{PUBDATE_CN}，按创新智商排名发表）：{titles}。'
           f'另附三种读法：网页长文、在线 PDF 与下载 PDF。</p>'
           f'<span class="go">浏览全部{total}篇 →</span>')
    text = text[:old.start()] + new + text[old.end():]
    path.write_text(text, encoding="utf-8")
    return total


def fix_zhang_qiong_profile(papers):
    path = STU / "zhang-qiong" / "index.html"
    text = path.read_text(encoding="utf-8")
    total = STUDENTS["zhang-qiong"]["existing"] + len(papers)
    m = re.search(r'<a class="works-entry"[^>]*>', text)
    assert m, "张琼主页 works-entry 入口未找到"
    p = papers[0]
    block = f"""<div style="max-width:820px;margin:28px auto 0;padding:0 24px">
  <div style="border:1px solid rgba(62,125,80,0.45);border-radius:14px;padding:20px 24px;background:rgba(62,125,80,0.06)">
    <div style="font-size:12px;letter-spacing:.28em;color:var(--gold);margin-bottom:8px" class="zh-only">本 批 新 作 · {PUBDATE_CN}</div>
    <div style="font-size:12px;letter-spacing:.28em;color:var(--gold);margin-bottom:8px" class="en-only">LATEST · JULY 26, 2026</div>
    <h3 style="font-size:19px;color:#1E3323;margin:0 0 8px"><a href="/students/zhang-qiong/{p["slug"]}/" style="color:inherit;text-decoration:none">{html.escape(p["title"])}</a></h3>
    <p style="font-size:14px;color:var(--ink2);margin:0 0 10px;line-height:1.85">{html.escape(p["hook"])}</p>
    <p style="font-size:13px;color:var(--ink2);margin:0 0 12px">{numlabel("zhang-qiong", p["num"])} · 约 {p["wan"]} 万字 · {p["pages"]} 页 · 本批评分第 {p["rank"]}</p>
    <p style="margin:0"><a href="/students/zhang-qiong/{p["slug"]}/" style="color:var(--gold)">📖 长文阅读</a>　<a href="/students/zhang-qiong/{p["slug"]}/read.html" style="color:var(--gold)">📄 在线 PDF</a>　<a href="/students/zhang-qiong/{p["slug"]}/{p["slug"]}.pdf" download style="color:var(--gold)">⬇ 下载 PDF</a></p>
  </div>
</div>
"""
    text = text[:m.start()] + block + text[m.start():]
    path.write_text(text, encoding="utf-8")
    return total


BIO_ZH = ("蔡彦 · SDE 预备学员。研究城市为何存续、为何在最好的时候失去转向的能力。"
          "本批三篇构成生成、条件、失效三个环节：《漩涡的契约》追问有用如何结晶为值得，"
          "《余地之根》追问活力何以依赖规则的管辖不及，《审美惯性》追问成功如何"
          "沉淀为一套把另一种未来预先归入“不配”的感知结构。")
BIO_EN = ("Cai Yan · SDE preparatory trainee. Works on why cities endure, and why they lose "
          "the capacity to turn precisely when they are at their strongest.")


def swap(text, title, desc):
    text = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", text, count=1, flags=re.S)
    text = re.sub(r'(<meta name="description" content=")[^"]*(")',
                  lambda m: m.group(1) + desc + m.group(2), text, count=1)
    return text.replace(SKEL_NAME, "蔡彦").replace(SKEL, "cai-yan")


def build_cai_yan(papers):
    (STU / "cai-yan" / "works").mkdir(parents=True, exist_ok=True)
    n = len(papers)
    # works 索引
    src = (STU / SKEL / "works" / "index.html").read_text(encoding="utf-8")
    head = f"""<div class="head">
  <div class="eyebrow">作 品 发 表 · PUBLISHED WORKS</div>
  <h1>蔡彦 · 作品</h1>
  <div class="who">SDE 预备学员 · 城市研究与制度史 · {n} 篇文章 · 每篇三种阅读方式</div>
  <div class="rule"></div>
</div>
"""
    works = ('<div class="works">\n' + "".join(card(p) for p in papers)
             + '  <div class="back"><a href="/students/cai-yan/">← 返回蔡彦 Profile</a></div>\n</div>\n')
    hi, wi, fi = (src.find('<div class="head"'), src.find('<div class="works"'), src.find("<footer>"))
    assert 0 < hi < wi < fi, "骨架结构与预期不符"
    out = swap(src[:hi] + head + "\n" + works + "\n" + src[fi:],
               "蔡彦 · 作品 · SDE Universes",
               "蔡彦 · SDE 预备学员 · 城市研究：审美惯性 / 漩涡的契约 / 余地之根，每篇三种阅读方式")
    (STU / "cai-yan" / "works" / "index.html").write_text(out, encoding="utf-8")

    # profile
    src = (STU / SKEL / "index.html").read_text(encoding="utf-8")
    latest = "".join(
        f"""    <div class="work">
      <span class="chip">{numlabel("cai-yan", p["num"])} · {html.escape(p["kind"])}</span>
      <h2><a href="/students/cai-yan/{p["slug"]}/" style="color:inherit;text-decoration:none">{html.escape(p["title"])}</a></h2>
      <p class="hook">{html.escape(p["hook"])}</p>
      <div class="meta">约 {p["wan"]} 万字 · {p["pages"]} 页 · 本批评分第 {p["rank"]} · 发表于{PUBDATE_CN}</div>
      <div class="modes">
        <a class="m primary" href="/students/cai-yan/{p["slug"]}/">📖 长文阅读</a>
        <a class="m ghost" href="/students/cai-yan/{p["slug"]}/read.html">📄 在线 PDF</a>
        <a class="m ghost" href="/students/cai-yan/{p["slug"]}/{p["slug"]}.pdf" download>⬇ 下载 PDF</a>
      </div>
    </div>
""" for p in papers)
    body = f"""<div class="level-tag" style="padding-top:40px">
  <span class="n">01</span><span class="t zh-only">学 员 介 绍 · PROFILE</span><span class="t en-only">PROFILE</span><span class="line"></span>
</div>
<div class="profile">
  <div class="avatar">蔡</div>
  <div class="p-info">
    <h1>蔡彦</h1>
    <div class="role zh-only">SDE 预备学员</div>
    <div class="role en-only">SDE PREPARATORY TRAINEE</div>
    <p class="bio zh-only">{BIO_ZH}</p>
    <p class="bio en-only">{BIO_EN}</p>
  </div>
</div>

<div class="level-tag">
  <span class="n">02</span><span class="t zh-only">最 新 作 品 · LATEST WORKS</span><span class="t en-only">LATEST WORKS</span><span class="line"></span>
</div>
<div class="works">
{latest}  <div class="back"><a href="/students/cai-yan/works/">查看全部作品 →</a></div>
</div>
"""
    m = re.search(r'<div class="level-tag"', src)
    fi = src.find("<footer>")
    assert m and fi > m.start(), "骨架结构与预期不符"
    out = swap(src[:m.start()] + body + "\n" + src[fi:],
               "蔡彦 · 学员专栏 | SDE Universes",
               "蔡彦 · SDE 预备学员 · Students' Column, SDE Universes")
    out = re.sub(r'<div class="avatar"[^>]*>\s*<img[^>]*>\s*</div>',
                 '<div class="avatar">蔡</div>', out)
    (STU / "cai-yan" / "index.html").write_text(out, encoding="utf-8")


def update_publications(papers):
    path = STU / "publications.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    by = {x["slug"]: x for x in data["students"]}
    for sl in {p["student"] for p in papers}:
        mine = [p for p in papers if p["student"] == sl]
        if sl not in by:
            by[sl] = {"slug": sl, "name": STUDENTS[sl]["name"], "count": 0,
                      "promo": {"lead": BIO_ZH, "themes": ["城市研究", "制度史", "创新失效"]},
                      "items": []}
            data["students"].append(by[sl])
        e = by[sl]
        have = {x["url"] for x in e["items"]}
        new = [{"number": p["num"], "title": p["title"],
                "url": f'/students/{sl}/{p["slug"]}/', "kind": p["kind"],
                "summary": p["hook"]} for p in mine
               if f'/students/{sl}/{p["slug"]}/' not in have]
        e["items"] = new + e["items"]
        e["count"] = len(e["items"])
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def add_cai_yan_identity():
    path = STU / "roster.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if any(x["slug"] == "cai-yan" for x in data["students"]):
        return None
    order = max(x.get("enrolled_order", 0) for x in data["students"]) + 1
    data["students"].append({"slug": "cai-yan", "name": "蔡彦", "small": "预备",
                             "count": 0, "enrolled_order": order, "papers": []})
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return order


def main():
    papers = load()
    groups = {}
    for p in papers:
        groups.setdefault(p["student"], []).append(p)
    for sl, ps in groups.items():
        ps.sort(key=lambda x: -x["num"])
        if STUDENTS[sl]["new"]:
            build_cai_yan(ps)
            print(f"  蔡彦：新建 profile + works（{len(ps)} 篇，序号 {numlabel(sl, ps[0]['num'])}）")
        else:
            prepend_works(sl, ps)
            total = (fix_gao_peng_profile(ps) if sl == "gao-peng"
                     else fix_zhang_qiong_profile(ps))
            print(f'  {STUDENTS[sl]["name"]}：works 前插 {len(ps)} 张卡（'
                  f'{numlabel(sl, ps[0]["num"])} 起），主页静态区已更新，篇数 → {total}')
    update_publications(papers)
    order = add_cai_yan_identity()
    if order:
        print(f"  roster 新增身份：蔡彦 / cai-yan / enrolled_order={order}")


if __name__ == "__main__":
    main()
