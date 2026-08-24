#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the paired 5,000-character essays for John Hu's WeChat archive.

Source files live in ``tools/data/john_wechat_upgrades/NNN.md``.  Each source
is a canonical article number.  Alternate versions automatically share the
canonical companion, so all 418 PDFs can be covered without writing the same
upgrade twice.
"""
from __future__ import annotations

import html
import json
import os
import re
from pathlib import Path

from lang_theme import CSS, PREFIX_FIX, esc, nav, page


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "tools" / "data" / "john_wechat.json"
SOURCE = ROOT / "tools" / "data" / "john_wechat_upgrades"
OUT = ROOT / "public" / "sites" / "lang" / "wechat" / "lift"
PUBLIC_BASE = "https://lang.sdeuniverses.com"

FOOTER = """<footer><div class="wrap">
  <p>约翰专栏提升工程 —— 原文一字未改；提升文从原文的问题继续向前，补出新判断、可操作读数、失效边界与家庭动作。</p>
  <p>语言发生学 · <a href="https://sdeuniverses.com/">SDE Universes</a> 的语言分站 —— 德麦国际 · Demai International Press</p>
</div></footer>"""

LIFT_CSS = """
.lift-progress{margin-top:28px;border:1px solid var(--edge);padding:18px 20px;background:var(--night2)}
.lift-progress .bar{height:5px;background:rgba(232,228,218,.13);margin-top:10px;overflow:hidden}
.lift-progress .bar i{display:block;height:100%;background:var(--vermilion-l)}
.lift-progress p{margin:0;color:var(--bone2);font:12px/1.7 var(--mono)}
.compare-shell{max-width:1380px;margin:0 auto;padding:38px 24px 0;display:grid;
  grid-template-columns:minmax(300px,38%) minmax(0,1fr);gap:38px;align-items:start}
.source-rail{position:sticky;top:78px;border:1px solid var(--line);background:var(--card);padding:18px}
.source-rail .tag,.lift-meta{font:11px/1.5 var(--mono);letter-spacing:.14em;color:var(--vermilion)}
.source-rail h2{font:600 21px/1.5 var(--serif);letter-spacing:.03em;margin:9px 0 8px}
.source-rail p{font-size:13.5px;line-height:1.75;color:var(--ink2);margin:0 0 14px}
.source-rail iframe{width:100%;height:68vh;min-height:520px;border:1px solid var(--line);background:#fff}
.source-actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px}
.source-actions a{font:12px/1.4 var(--mono);color:var(--indigo);border:1px solid var(--line);padding:7px 10px}
.source-actions a:hover{border-color:var(--indigo);background:#fff}
.lift-essay{min-width:0;padding:2px 0 20px}
.lift-essay .lift-meta{margin-bottom:12px}
.lift-essay .thesis{font:600 20px/1.75 var(--serif);color:var(--ink);padding:18px 20px;
  border-left:3px solid var(--vermilion);background:var(--card);margin:0 0 34px}
.lift-essay section{padding:0 0 20px}
.lift-essay h2{font:600 23px/1.5 var(--serif);letter-spacing:.04em;margin:28px 0 12px;
  padding-bottom:8px;border-bottom:1px solid var(--line)}
.lift-essay p{font-size:17px;line-height:2;margin:15px 0;color:#23262F;max-width:44em}
.lift-essay strong{font-weight:600;color:var(--ink);background:linear-gradient(transparent 62%,rgba(166,58,43,.15) 62%)}
.lift-essay code{font:14px/1.6 var(--mono);background:#E7E6E1;padding:1px 5px;color:var(--indigo)}
.lift-essay a{color:var(--indigo);border-bottom:1px solid var(--line)}
.lift-index{padding-top:18px}
.lift-card{display:grid;grid-template-columns:64px 1fr auto;gap:18px;align-items:baseline;
  padding:18px 4px;border-bottom:1px dashed var(--line)}
.lift-card .num{font:12px/1.5 var(--mono);color:var(--vermilion)}
.lift-card h3{font:600 18px/1.55 var(--serif);margin:0 0 5px}
.lift-card p{margin:0;color:var(--ink2);font-size:13.5px}
.lift-card .count{font:11px/1.5 var(--mono);color:var(--ink3);white-space:nowrap}
@media(max-width:900px){
  .compare-shell{grid-template-columns:1fr;gap:26px;padding:28px 20px 0}
  .source-rail{position:relative;top:auto}
  .source-rail iframe{height:56vh;min-height:430px}
}
@media(max-width:600px){
  .compare-shell{padding-left:16px;padding-right:16px}
  .source-rail iframe{display:none}
  .lift-essay p{font-size:16.5px;line-height:1.95}
  .lift-card{grid-template-columns:46px 1fr}.lift-card .count{display:none}
}
"""


def split_front_matter(raw: str) -> tuple[dict[str, str], str]:
    if not raw.startswith("---\n"):
        raise ValueError("提升文缺少 YAML 风格头部")
    _, head, body = raw.split("---\n", 2)
    meta: dict[str, str] = {}
    for line in head.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            raise ValueError("无法解析头部行：%s" % line)
        meta[key.strip()] = value.strip().strip('"')
    return meta, body.strip()


def inline(text: str) -> str:
    safe = html.escape(text, quote=False)
    safe = re.sub(r"\[([^]]+)\]\((https?://[^)]+)\)",
                  lambda m: '<a href="%s" rel="noopener">%s</a>' %
                            (html.escape(m.group(2), quote=True), m.group(1)), safe)
    safe = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", safe)
    safe = re.sub(r"`([^`]+)`", r"<code>\1</code>", safe)
    return safe


def markdown_body(raw: str) -> str:
    out: list[str] = []
    paragraphs: list[str] = []

    def flush() -> None:
        if paragraphs:
            out.append("<p>%s</p>" % inline("".join(paragraphs).strip()))
            paragraphs.clear()

    section_open = False
    for line in raw.splitlines():
        line = line.rstrip()
        if line.startswith("## "):
            flush()
            if section_open:
                out.append("</section>")
            out.append("<section><h2>%s</h2>" % inline(line[3:].strip()))
            section_open = True
        elif not line.strip():
            flush()
        else:
            paragraphs.append(line.strip())
    flush()
    if section_open:
        out.append("</section>")
    return "\n".join(out)


def cjk_count(text: str) -> int:
    return len(re.findall(r"[\u3400-\u9fff]", text))


def load_upgrades() -> list[dict[str, object]]:
    arts = json.loads(DATA.read_text(encoding="utf-8"))
    by_num = {a["num"]: a for a in arts}
    upgrades: list[dict[str, object]] = []
    if not SOURCE.exists():
        return upgrades
    for path in sorted(SOURCE.glob("[0-9][0-9][0-9].md")):
        meta, body = split_front_matter(path.read_text(encoding="utf-8"))
        num = path.stem
        if num not in by_num:
            raise ValueError("提升文 %s 找不到原文" % num)
        if by_num[num].get("alt"):
            raise ValueError("%s 是同题另稿，提升文必须挂在正稿 %s" %
                             (num, by_num[num].get("alt_of")))
        n = cjk_count(body)
        if not 4500 <= n <= 6500:
            raise ValueError("提升文 %s 为 %d 个汉字，必须在 4500–6500 之间" % (num, n))
        for key in ("title", "thesis", "version"):
            if not meta.get(key):
                raise ValueError("提升文 %s 缺少 %s" % (num, key))
        upgrades.append({"num": num, "meta": meta, "body": body,
                         "cjk": n, "article": by_num[num]})
    return upgrades


def coverage(upgrades: list[dict[str, object]], arts: list[dict[str, object]]) -> int:
    nums = {u["num"] for u in upgrades}
    return sum(1 for a in arts if (a["alt_of"] if a.get("alt") else a["num"]) in nums)


def build() -> None:
    arts = json.loads(DATA.read_text(encoding="utf-8"))
    canonical = [a for a in arts if not a.get("alt")]
    upgrades = load_upgrades()
    covered = coverage(upgrades, arts)
    OUT.mkdir(parents=True, exist_ok=True)

    for upgrade in upgrades:
        num = str(upgrade["num"])
        meta = upgrade["meta"]
        article = upgrade["article"]
        assert isinstance(meta, dict) and isinstance(article, dict)
        original_url = "/wechat/pdf/%s.pdf" % num
        body_html = markdown_body(str(upgrade["body"]))
        body = """<div class="dark">
%s
<div class="wrap"><div class="hero tight">
  <div class="crumb"><a href="/wechat/">约翰专栏</a> · <a href="/wechat/lift/">提升工程</a> · 存档号 %s</div>
  <div class="eyebrow">原文 × 提升文 · PAIRED READING</div>
  <h1>%s</h1>
  <p class="lede">原文提出问题，提升文不复述答案，而把认识单位从“单个句子”推进到“整次互动”，并补出可观察读数、失效条件与家庭动作。</p>
</div></div></div>

<div class="light"><div class="compare-shell">
  <aside class="source-rail">
    <div class="tag">原文 · ORIGINAL · %s</div>
    <h2>%s</h2>
    <p>%s</p>
    <iframe title="原文 PDF" loading="lazy" src="%s#view=FitH"></iframe>
    <div class="source-actions"><a href="%s">单独打开原文 PDF</a><a href="/wechat/genesis/">返回所属频道</a></div>
  </aside>
  <article class="lift-essay">
    <div class="lift-meta">提升文 · %s · %s 汉字</div>
    <p class="thesis">%s</p>
%s
    <div class="note"><h3>两篇怎样并读</h3><p>先读左侧原文，抓住“语用能力”与人物、关系、负担、边界四个变量；再读右侧提升文，看评价单位怎样从“这句话礼不礼貌”改为“这句话给对方留下了哪些可继续的路”。提升文不替代原文，原文提供现场与证据，提升文负责把机制再向前推一步。</p></div>
    <div class="nearby"><a href="/wechat/lift/"><small>提升工程</small><b>查看总进度</b>418 篇原文逐篇并读</a><a href="%s"><small>原文</small><b>回到胡志英原稿</b>%s</a></div>
  </article>
</div></div>""" % (
            nav("wechat"), num, esc(str(meta["title"])),
            esc(str(article.get("date") or "未标日期")), esc(str(article["title"])),
            esc(str(article["sum"])), original_url, original_url,
            esc(str(meta["version"])), format(int(upgrade["cjk"]), ","),
            esc(str(meta["thesis"])), body_html, original_url, esc(str(article["title"]))
        )
        target = OUT / num
        target.mkdir(parents=True, exist_ok=True)
        (target / "index.html").write_text(
            page("%s · 提升文 · 约翰专栏" % str(meta["title"]),
                 "%s 与胡志英公众号原文并列阅读。" % str(meta["thesis"]),
                 "%s/wechat/lift/%s/" % (PUBLIC_BASE, num),
                 body, FOOTER, "#A63A2B", "<style>%s</style>" % LIFT_CSS),
            encoding="utf-8")

    cards = ""
    for upgrade in upgrades:
        meta = upgrade["meta"]
        article = upgrade["article"]
        assert isinstance(meta, dict) and isinstance(article, dict)
        cards += """<a class="lift-card" href="/wechat/lift/%s/">
  <span class="num">%s</span><span><h3>%s</h3><p>原文：%s</p></span><span class="count">%s 汉字</span>
</a>""" % (upgrade["num"], upgrade["num"], esc(str(meta["title"])),
            esc(str(article["title"])), format(int(upgrade["cjk"]), ","))
    pct = 100 * covered / len(arts) if arts else 0
    index_body = """<div class="dark">
%s
<div class="wrap"><div class="hero">
  <div class="eyebrow">约翰专栏 · 提升工程</div>
  <h1>原文不动，<em>思想继续向前</em></h1>
  <p class="lede">胡志英公众号共 <b>%d 篇原文</b>，其中 %d 篇是正稿、%d 篇是同题另稿。每个正稿配一篇约 5000 字提升文；同题另稿共享同一篇提升文，因此不制造重复文字，却让每一份原文都有可抵达的提升入口。</p>
  <div class="lift-progress"><p>当前覆盖 %d / %d 篇原文 · 已完成 %d / %d 篇独立提升文</p><div class="bar"><i style="width:%.4f%%"></i></div></div>
</div></div></div>
<div class="light"><div class="wrap"><section>
  <div class="col-h"><span class="no">已　完　成</span><h2>逐篇并读</h2><span class="ct">每篇 4500–6500 汉字</span></div>
  <p class="col-d">提升文必须补出四件原稿里尚未完成的工作：认识单位的改变、一个可复述的新读数、能推翻它的条件、读者明天可以执行的动作。</p>
  <div class="lift-index">%s</div>
</section></div></div>""" % (
        nav("wechat"), len(arts), len(canonical), len(arts) - len(canonical),
        covered, len(arts), len(upgrades), len(canonical), pct, cards)
    (OUT / "index.html").write_text(
        page("约翰专栏提升工程 · 语言发生学",
             "胡志英公众号 418 篇原文逐篇配写约 5000 字提升文，原文与提升文并列阅读。",
             "%s/wechat/lift/" % PUBLIC_BASE,
             index_body, FOOTER, "#A63A2B", "<style>%s</style>" % LIFT_CSS),
        encoding="utf-8")
    print("提升工程：%d 篇独立提升文，覆盖 %d / %d 篇原文" %
          (len(upgrades), covered, len(arts)))


if __name__ == "__main__":
    build()
