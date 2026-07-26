# -*- coding: utf-8 -*-
"""生成季春雷的 works 作品索引与学员主页。

做法遵循站内纪律：复制既有学员页面的 <head>（含 style）与 nav/footer 骨架，
只换标题、描述与正文，主题因此天然一致；不手写新 CSS。
最新作品置顶，序号 = 当前作品总数并依次递减（见 tools/README.md 的发布事故记忆）。
"""
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jcl_meta import AUTHOR, STUDENT, PUBDATE_CN, PAPERS

ROOT = Path(__file__).resolve().parents[1]
STU = ROOT / "public" / "students"
SKEL = "kong-fanhe"          # 借骨架的学员（暗金主题，站内多数）
SKEL_NAME = "孔凡鹤"
CN_NUM = "零一二三四五六七八九十"


def cn(n: int) -> str:
    if n <= 10:
        return CN_NUM[n]
    if n < 20:
        return "十" + CN_NUM[n - 10]
    return CN_NUM[n // 10] + "十" + (CN_NUM[n % 10] if n % 10 else "")


def swap_shell(text: str, title: str, desc: str) -> str:
    """换掉借来骨架里的标题、描述与人名。"""
    text = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", text, count=1, flags=re.S)
    text = re.sub(r'(<meta name="description" content=")[^"]*(")',
                  lambda m: m.group(1) + desc + m.group(2), text, count=1)
    text = text.replace(SKEL_NAME, AUTHOR).replace(SKEL, STUDENT)
    return text


def card(paper: dict, index: int) -> str:
    slug, base = paper["slug"], f'/students/{STUDENT}/{paper["slug"]}'
    return f"""  <div class="work">
    <span class="chip">之{cn(index)} · {html.escape(paper["kind"])} · 深化增补版</span>
    <h2>{html.escape(paper["title"])}</h2>
    <p class="hook">{html.escape(paper["hook"])}</p>
    <div class="meta">约 {paper["wan"]} 万字 · {paper["pages"]} 页 · SDE 创新智商 {paper["old_score"]} → {paper["score"]}（编辑自评，待独立复评） · 三种读法 · 发表于{PUBDATE_CN}</div>
    <div class="modes">
      <a class="m primary" href="{base}/">📖 长文阅读</a>
      <a class="m ghost" href="{base}/read.html">📄 在线 PDF</a>
      <a class="m ghost" href="{base}/{slug}.pdf" download>⬇ 下载 PDF</a>
    </div>
  </div>
"""


def build_works(papers):
    src = (STU / SKEL / "works" / "index.html").read_text(encoding="utf-8")
    total = len(papers)
    head_block = f"""<div class="head">
  <div class="eyebrow">作 品 发 表 · PUBLISHED WORKS</div>
  <h1>{AUTHOR} · 作品</h1>
  <div class="who">SDE 预备学员 · 教育发生与意义生成 · {total} 篇文章 · 每篇三种阅读方式</div>
  <div class="rule"></div>
</div>
"""
    cards = "".join(card(p, total - i) for i, p in enumerate(papers))
    works_block = f"""<div class="works">
{cards}  <div class="back"><a href="/students/{STUDENT}/">← 返回{AUTHOR} Profile</a></div>
</div>
"""
    hi, wi = src.find('<div class="head"'), src.find('<div class="works"')
    fi = src.find("<footer>")
    assert 0 < hi < wi < fi, "骨架结构与预期不符"
    out = src[:hi] + head_block + "\n" + works_block + "\n" + src[fi:]
    return swap_shell(out, f"{AUTHOR} · 作品 · SDE Universes",
                      f"{AUTHOR} · SDE 预备学员 · 十篇：静息窗口 / 三股绳 / 藏息 / 在场范式 / 亲体冷凝 / 动词我 / 不可预制的空缺 / 主体性代偿 / 无痕生长，每篇三种阅读方式")


BIO_ZH = ("季春雷 · SDE 预备学员。十篇论文分两簇：一簇追问教育里那些不可被看见的过程"
          "如何被时间结构与评价体系挤出（静息窗口、三股绳、藏息、认知冗余、无痕生长）；"
          "一簇追问意义为何不在未来的回报里（在场范式、亲体冷凝、动词我、不可预制的空缺、"
          "主体性代偿）。十篇共用同一个撤销动作：把“那个东西还在、只是缺量”换成"
          "“它的发生条件从未成立，或已被取消”。")
BIO_EN = ("Ji Chunlei · SDE preparatory trainee. Ten papers in two clusters: how education's "
          "unobservable processes are squeezed out by time structure and evaluation, and why "
          "meaning is not located in future returns. All ten perform the same reversal — from "
          "\"it is still there, only diminished\" to \"its conditions of occurrence never held.\"")


def build_profile(papers):
    src = (STU / SKEL / "index.html").read_text(encoding="utf-8")
    total = len(papers)
    # 主页静态最新作品区（不依赖延迟加载的作品列单）
    latest = "".join(
        f"""    <div class="work">
      <span class="chip">之{cn(total - i)} · {html.escape(p["kind"])}</span>
      <h2><a href="/students/{STUDENT}/{p["slug"]}/" style="color:inherit;text-decoration:none">{html.escape(p["title"])}</a></h2>
      <p class="hook">{html.escape(p["hook"])}</p>
      <div class="meta">约 {p["wan"]} 万字 · {p["pages"]} 页 · 发表于{PUBDATE_CN}</div>
      <div class="modes">
        <a class="m primary" href="/students/{STUDENT}/{p["slug"]}/">📖 长文阅读</a>
        <a class="m ghost" href="/students/{STUDENT}/{p["slug"]}/read.html">📄 在线 PDF</a>
        <a class="m ghost" href="/students/{STUDENT}/{p["slug"]}/{p["slug"]}.pdf" download>⬇ 下载 PDF</a>
      </div>
    </div>
""" for i, p in enumerate(papers))

    body = f"""<div class="level-tag" style="padding-top:40px">
  <span class="n">01</span><span class="t zh-only">学 员 介 绍 · PROFILE</span><span class="t en-only">PROFILE</span><span class="line"></span>
</div>
<div class="profile">
  <div class="avatar">季</div>
  <div class="p-info">
    <h1>{AUTHOR}</h1>
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
{latest}  <div class="back"><a href="/students/{STUDENT}/works/">查看全部 {total} 篇作品 →</a></div>
</div>
"""
    m = re.search(r'<div class="level-tag"', src)
    fi = src.find("<footer>")
    assert m and fi > m.start(), "骨架结构与预期不符"
    out = src[:m.start()] + body + "\n" + src[fi:]
    out = swap_shell(out, f"{AUTHOR} · 学员专栏 | SDE Universes",
                     f"{AUTHOR} · SDE 预备学员 · Students' Column, SDE Universes")
    # 借来的骨架里可能残留原学员头像 <img>；本页用文字头像，清掉
    out = re.sub(r'<div class="avatar"[^>]*>\s*<img[^>]*>\s*</div>',
                 '<div class="avatar">季</div>', out)
    return out


def update_publications(papers):
    path = STU / "publications.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["students"] = [x for x in data["students"] if x["slug"] != STUDENT]
    total = len(papers)
    data["students"].append({
        "slug": STUDENT, "name": AUTHOR, "count": total,
        "promo": {
            "lead": "十篇分两簇——教育里不可被看见的过程如何被挤出，以及意义为何不在未来的回报里。"
                    "共用同一个撤销动作：不是“它还在、只是缺量”，而是“它的发生条件从未成立”。",
            "themes": ["教育发生", "深度阅读", "意义生成", "代际传递", "主体性"],
        },
        "items": [{
            "number": total - i, "title": p["title"],
            "url": f'/students/{STUDENT}/{p["slug"]}/',
            "kind": p["kind"], "summary": p["hook"],
        } for i, p in enumerate(papers)],
    })
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_roster_identity(papers):
    """只补 roster 的身份字段；papers/count 由 build_roster.py 从磁盘派生。"""
    path = STU / "roster.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if any(x["slug"] == STUDENT for x in data["students"]):
        return
    order = max(x.get("enrolled_order", 0) for x in data["students"]) + 1
    data["students"].append({
        "slug": STUDENT, "name": AUTHOR, "small": "预备",
        "count": 0, "enrolled_order": order, "papers": [],
    })
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  roster 新增身份：{AUTHOR} / {STUDENT} / enrolled_order={order}")


def main():
    report = json.loads((ROOT / "tools" / "jcl_report.json").read_text(encoding="utf-8"))
    by_slug = {x["slug"]: x for x in report["papers"]}
    papers = []
    for p in PAPERS:
        q = dict(p)
        q.update(by_slug[p["slug"]])
        papers.append(q)
    # 站上顺序：本批同日发表，按篇号倒序（10 在最前）以便最新序号=总数
    papers = list(reversed(papers))

    (STU / STUDENT / "works").mkdir(parents=True, exist_ok=True)
    (STU / STUDENT / "works" / "index.html").write_text(build_works(papers), encoding="utf-8")
    (STU / STUDENT / "index.html").write_text(build_profile(papers), encoding="utf-8")
    update_publications(papers)
    update_roster_identity(papers)
    print(f"  works 索引 + 学员主页已生成（{len(papers)} 篇，最新序号 {len(papers)}）")


if __name__ == "__main__":
    main()
