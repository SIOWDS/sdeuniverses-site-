#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配套读物生成器 —— 给 /column/<slug>/ 的理论母文各配两篇长文：
  · explain.html   白话解释文（日常类比，人人能读懂）
  · practice.html  方法实践文（步骤、判据、检查表、失败模式）
并在母文页「摘要」正下方插入两个入口按钮（不放文末）。

用法：
  python3 tools/publish_companion.py <slug>            # 生成两篇 + 插入入口
  python3 tools/publish_companion.py <slug> --dry      # 只看不写

内容源：content/<slug>.explain.txt / content/<slug>.practice.txt（仓库外，见 CONTENT_DIR）
格式：
  TITLE: 标题
  SUB: 副标题
  ABS: 摘要（一段）
  == 小标题
  正文段落（空行分段；行首 - 为要点列表；行首 > 为引述块）
"""
import os, re, sys, html, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, "public")
CONTENT_DIR = os.environ.get("COMPANION_CONTENT", "/home/claude/content")
VER = "20260802b"

KIND = {
    "explain": dict(
        label="白话解释文", icon="🌱",
        eyebrow="配套读物 · 白话解释文",
        accent="#A8813C", accent2="#8C6A3A", tint="#FBF6EA",
        hint="用日常生活的类比，把母文讲成人人能懂的话",
        who="这一篇写给：读母文时被术语挡在门外、但想真正弄懂它在说什么的人。全篇不假设你读过任何理论书。",
    ),
    "practice": dict(
        label="方法实践文", icon="🛠",
        eyebrow="配套读物 · 技术与方法实践",
        accent="#2F5470", accent2="#24425A", tint="#EFF3F7",
        hint="把母文的判断落成可上手的步骤、判据与检查表",
        who="这一篇写给：已经认同母文的判断、现在想把它用到自己手头工作上的人。全篇以可操作为准，不重复论证。",
    ),
}

CSS = """
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:#FBF8F1;color:#2B2620;
 font-family:"Noto Serif SC","Songti SC","Source Han Serif SC",Georgia,serif;
 font-size:17px;line-height:1.95;letter-spacing:.01em}
.wrap{max-width:760px;margin:0 auto;padding:0 22px}
nav.cnav{background:#2B2620;color:#EDE4CF;position:sticky;top:0;z-index:30;
 font-family:system-ui,-apple-system,"PingFang SC","Microsoft YaHei",sans-serif}
nav.cnav .wrap{display:flex;align-items:center;justify-content:space-between;gap:14px;height:50px}
nav.cnav a{color:#EDE4CF;text-decoration:none;font-size:14px}
nav.cnav .cnav-logo{font-weight:700;letter-spacing:.06em}
nav.cnav .cnav-back{opacity:.82}
nav.cnav .cnav-back:hover{opacity:1}
header.art{background:linear-gradient(180deg,#FFFDF8 0%,#F5EFE2 100%);
 border-bottom:1px solid rgba(43,38,32,.10);padding:44px 0 34px}
.art-eyebrow{font-size:12.5px;letter-spacing:.16em;color:__ACC__;font-weight:700;
 font-family:system-ui,-apple-system,"PingFang SC",sans-serif;margin-bottom:16px}
h1.art-title{font-size:33px;line-height:1.4;margin:0 0 14px;font-weight:800}
.art-subtitle{font-size:17px;color:#5C5346;line-height:1.7;margin-bottom:16px}
.art-meta{font-size:13px;color:#8A8071;
 font-family:system-ui,-apple-system,"PingFang SC",sans-serif}
.swap{display:flex;flex-wrap:wrap;gap:10px;margin:22px auto 0}
.swap a{flex:1 1 240px;display:block;text-decoration:none;padding:12px 15px;border-radius:9px;
 border:1px solid rgba(43,38,32,.16);background:#fff;color:#2B2620;
 font-family:system-ui,-apple-system,"PingFang SC",sans-serif;font-size:14px;line-height:1.6}
.swap a b{display:block;font-size:14.5px;margin-bottom:2px}
.swap a span{color:#8A8071;font-size:12.5px}
.swap a:hover{border-color:__ACC__;box-shadow:0 2px 10px rgba(43,38,32,.07)}
article{padding:30px 0 10px}
.abs{background:__TINT__;border-left:4px solid __ACC__;border-radius:0 8px 8px 0;
 padding:18px 20px;margin:0 0 26px;font-size:15.5px;line-height:1.85;color:#4A4238}
.abs b{color:__ACC2__}
.toc{border:1px solid rgba(43,38,32,.13);border-radius:9px;padding:16px 20px;margin:0 0 34px;
 font-family:system-ui,-apple-system,"PingFang SC",sans-serif;font-size:14.5px;background:#FFFDF8}
.toc .tl{font-size:12.5px;letter-spacing:.14em;color:__ACC__;font-weight:700;margin-bottom:10px}
.toc ol{margin:0;padding-left:20px;color:#5C5346}
.toc li{margin:5px 0}
.toc a{color:#4A4238;text-decoration:none}
.toc a:hover{color:__ACC__;text-decoration:underline}
h2{font-size:22px;line-height:1.5;margin:44px 0 16px;padding-top:8px;font-weight:800;
 border-top:1px solid rgba(43,38,32,.10)}
h2 .no{display:inline-block;min-width:1.9em;color:__ACC__;font-size:16px;font-weight:700;
 font-family:system-ui,-apple-system,"PingFang SC",sans-serif}
p{margin:0 0 17px;text-align:justify}
p b,li b{color:__ACC2__}
ul.pts{margin:0 0 18px;padding-left:0;list-style:none}
ul.pts li{position:relative;padding-left:20px;margin:0 0 10px;text-align:justify}
ul.pts li:before{content:"—";position:absolute;left:0;color:__ACC__}
blockquote{margin:0 0 20px;padding:14px 18px;background:#FFFDF8;
 border-left:3px solid rgba(43,38,32,.22);color:#4A4238;font-size:16px}
.endbox{margin:48px 0 10px;padding:22px;border-radius:10px;background:__TINT__;
 border:1px solid rgba(43,38,32,.12)}
.endbox .et{font-size:12.5px;letter-spacing:.14em;color:__ACC__;font-weight:700;
 font-family:system-ui,-apple-system,"PingFang SC",sans-serif;margin-bottom:12px}
.endbox a{color:__ACC2__}
footer{margin-top:46px;padding:26px 0 40px;border-top:1px solid rgba(43,38,32,.12);
 font-family:system-ui,-apple-system,"PingFang SC",sans-serif;font-size:13px;color:#8A8071}
footer a{color:#8A8071}
@media(max-width:640px){body{font-size:16px}h1.art-title{font-size:26px}h2{font-size:19.5px}}
"""

# ---------- 母文页入口条 ----------
BAR_STYLE = """<style>
.cmpn-bar{max-width:760px;margin:26px auto;padding:16px 18px;border-radius:10px;
 border:1px solid rgba(127,127,127,.32);background:rgba(127,127,127,.06);
 font-family:system-ui,-apple-system,"PingFang SC","Microsoft YaHei",sans-serif}
.cmpn-bar .cmpn-t{font-size:12.5px;letter-spacing:.14em;font-weight:700;opacity:.72;margin-bottom:12px}
.cmpn-bar .cmpn-g{display:flex;flex-wrap:wrap;gap:10px}
.cmpn-bar a{flex:1 1 250px;display:block;text-decoration:none;color:inherit;
 padding:12px 14px;border-radius:8px;border:1px solid rgba(127,127,127,.34);
 background:rgba(255,255,255,.06);line-height:1.6}
.cmpn-bar a b{display:block;font-size:14.5px;margin-bottom:3px}
.cmpn-bar a span{display:block;font-size:12.5px;opacity:.66}
.cmpn-bar a:hover{border-color:currentColor;background:rgba(127,127,127,.12)}
</style>"""

BAR_TPL = """
<!-- COMPANION-READS -->
{style}
<div class="cmpn-bar">
  <div class="cmpn-t">配套读物 · 两条更好走的路</div>
  <div class="cmpn-g">
    <a href="/column/{slug}/explain.html"><b>🌱 白话解释文 · {ex_title}</b><span>不用术语，用日常生活的类比把本文讲一遍 · 约5000字</span></a>
    <a href="/column/{slug}/practice.html"><b>🛠 方法实践文 · {pr_title}</b><span>把本文的判断落成步骤、判据与检查表 · 约5000字</span></a>
  </div>
</div>
<!-- /COMPANION-READS -->
"""


def cq(s):
    """直引号成对转中文弯引号，避免正文出现 &quot; 与半角引号。"""
    return re.sub(r'"([^"\n]*)"', "\u201c\\1\u201d", s)


def esc(s):
    return html.escape(cq(s), quote=True)


def tesc(s):
    return html.escape(cq(s), quote=False)


# ---------- 内容解析 ----------
def parse(path):
    raw = open(path, encoding="utf-8").read().replace("\r\n", "\n")
    meta, secs, cur = {}, [], None
    for line in raw.split("\n"):
        m = re.match(r"^(TITLE|SUB|ABS):\s*(.*)$", line)
        if m and not secs:
            meta[m.group(1)] = m.group(2).strip()
            continue
        if line.startswith("== "):
            cur = {"h": line[3:].strip(), "blocks": []}
            secs.append(cur)
            continue
        if cur is None:
            continue
        cur["blocks"].append(line.rstrip())
    for k in ("TITLE", "SUB", "ABS"):
        assert meta.get(k), f"{path} 缺 {k}"
    assert secs, f"{path} 没有小节"
    out = []
    for s in secs:
        blocks, buf, mode = [], [], None
        def flush():
            nonlocal buf, mode
            if buf:
                blocks.append((mode, buf))
            buf, mode = [], None
        for ln in s["blocks"]:
            if not ln.strip():
                flush(); continue
            if ln.startswith("- "):
                if mode != "ul": flush(); mode = "ul"
                buf.append(ln[2:].strip())
            elif ln.startswith("> "):
                if mode != "bq": flush(); mode = "bq"
                buf.append(ln[2:].strip())
            else:
                if mode != "p": flush(); mode = "p"
                buf.append(ln.strip())
        flush()
        out.append({"h": s["h"], "blocks": blocks})
    return meta, out


def inline(t):
    t = tesc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"《([^》]+)》", r"《\1》", t)
    return t


def render_body(secs):
    o = []
    for i, s in enumerate(secs, 1):
        o.append(f'<h2 id="s{i}"><span class="no">{i:02d}</span>{inline(s["h"])}</h2>')
        for mode, buf in s["blocks"]:
            if mode == "p":
                o.append("<p>" + inline("".join(buf)) + "</p>")
            elif mode == "ul":
                o.append('<ul class="pts">' + "".join(f"<li>{inline(x)}</li>" for x in buf) + "</ul>")
            elif mode == "bq":
                o.append("<blockquote>" + inline("".join(buf)) + "</blockquote>")
    return "\n".join(o)


def render_page(slug, kind, meta, secs, mother_title, mother_short, sib_title):
    k = KIND[kind]
    other = "practice" if kind == "explain" else "explain"
    ok = KIND[other]
    css = CSS.replace("__ACC__", k["accent"]).replace("__ACC2__", k["accent2"]).replace("__TINT__", k["tint"])
    toc = "".join(f'<li><a href="#s{i}">{tesc(s["h"])}</a></li>' for i, s in enumerate(secs, 1))
    nchar = sum(len(re.findall(r"[\u4e00-\u9fff]", "".join("".join(b) for _, b in s["blocks"]))) for s in secs)
    desc = re.sub(r"\s+", " ", meta["ABS"])[:150]
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(meta['TITLE'])} · {k['label']} | SDE Universes</title>
<meta name="description" content="{esc(desc)}">
<meta name="author" content="王德生 · SDE Universes">
<meta property="og:type" content="article">
<meta property="og:title" content="{esc(meta['TITLE'])} · {k['label']}">
<meta property="og:description" content="{esc(desc)}">
<link rel="canonical" href="https://sdeuniverses.com/column/{slug}/{kind}.html">
<style>{css}</style>
</head>
<body>
<nav class="cnav"><div class="wrap">
  <a class="cnav-logo" href="/browse/">SDE Universes</a>
  <a class="cnav-back" href="/column/{slug}/">← 回母文《{esc(mother_short)}》</a>
</div></nav>

<header class="art"><div class="wrap">
  <div class="art-eyebrow">{k['eyebrow']} · 母文《{esc(mother_short)}》</div>
  <h1 class="art-title">{esc(meta['TITLE'])}</h1>
  <div class="art-subtitle">{inline(meta['SUB'])}</div>
  <div class="art-meta">王德生 原著 · Claude 撰写 · SDE Universes · 2026年8月 · 约 {nchar} 字</div>
  <div class="swap">
    <a href="/column/{slug}/"><b>← 母文 · {esc(mother_short)}</b><span>完整论证在这里</span></a>
    <a href="/column/{slug}/{other}.html"><b>{ok['icon']} {ok['label']} · {esc(sib_title)}</b><span>{ok['hint']}</span></a>
  </div>
</div></header>

<article class="wrap">
<div class="abs"><b>这一篇是什么</b>　{inline(meta['ABS'])}<br><br><b>读法</b>　{k['who']}</div>
<div class="toc"><div class="tl">目 录</div><ol>{toc}</ol></div>
{render_body(secs)}
<div class="endbox">
  <div class="et">接下来读什么</div>
  <p style="margin-bottom:10px">这一篇只是入口。真正的论证、边界与反驳，都在母文里：<a href="/column/{slug}/">《{esc(mother_title)}》</a>。</p>
  <p style="margin:0">另一条路：<a href="/column/{slug}/{other}.html">{ok['icon']} {ok['label']}《{esc(sib_title)}》</a>——{ok['hint']}。</p>
</div>
</article>

<footer><div class="wrap">
  © 2026 SDE Universes · 德麦国际 ·
  <a href="/column/{slug}/">回母文</a> ·
  <a href="/browse/">首页</a>
</div></footer>
<script src="/taste/wds-companion/wds-read.js?v={VER}" defer></script>
<script src="/wds-mode.js?v={VER}" defer></script>
</body>
</html>
"""


# ---------- 母文页插入点 ----------
def close_div(h, start):
    depth = 0
    for m in re.finditer(r"<div\b|</div>", h[start:]):
        if m.group(0) == "</div>":
            depth -= 1
            if depth == 0:
                return start + m.end()
        else:
            depth += 1
    return None


def find_anchor(h):
    """返回插入位置(索引)与说明。优先：摘要盒之后 → 摘要段之后 → header 之后。"""
    m = re.search(r'<div[^>]*class="(?:abs|abstract|abstract-box|absbox|deck)\b[^"]*"', h)
    if m:
        end = close_div(h, m.start())
        if end:
            m2 = re.compile(r"\s*<(div|p)\b[^>]*>(?:(?!</\1>).){0,400}?关键词.*?</\1>", re.S).match(h, end)
            if m2:
                end = m2.end()
            return end, "摘要盒之后"
    m = re.search(r"<p>\s*(?:<strong>|<b>)\s*摘要", h)
    if m:
        end = h.index("</p>", m.start()) + 4
        m2 = re.compile(r"\s*<p>\s*(?:<strong>|<b>)\s*关键词.*?</p>", re.S).match(h, end)
        if m2:
            end = m2.end()
        m3 = re.compile(r"\s*<hr\s*/?>", re.S).match(h, end)
        if m3:
            end = m3.end()
        return end, "摘要段之后"
    m = re.search(r"</header>", h)
    if m:
        end = m.end()
        m2 = re.compile(r"\s*(?:<div[^>]*>\s*)?<article\b[^>]*>", re.S).match(h, end)
        if m2:
            end = m2.end()
        return end, "文章头之后"
    m = re.search(r'<div[^>]*class="meta"[^>]*>.*?</div>', h, re.S)
    if m:
        return m.end(), "作者行之后"
    return None, None


def mother_meta(slug):
    p = os.path.join(PUB, "column", slug, "index.html")
    h = open(p, encoding="utf-8", errors="replace").read()
    m = re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S)
    t = html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else slug
    t = re.sub(r"\s+", "", t)
    return h, t


def main():
    slug = sys.argv[1]
    dry = "--dry" in sys.argv
    h, mtitle = mother_meta(slug)
    short = mtitle.split("：")[0].split("——")[0].strip()
    pages = {}
    for kind in ("explain", "practice"):
        meta, secs = parse(os.path.join(CONTENT_DIR, f"{slug}.{kind}.txt"))
        pages[kind] = (meta, secs)
    for kind in ("explain", "practice"):
        meta, secs = pages[kind]
        sib = pages["practice" if kind == "explain" else "explain"][0]["TITLE"]
        out = render_page(slug, kind, meta, secs, mtitle, short, sib)
        n = sum(len(re.findall(r"[\u4e00-\u9fff]", "".join("".join(b) for _, b in s["blocks"]))) for s in secs)
        dst = os.path.join(PUB, "column", slug, f"{kind}.html")
        print(f"  {kind:8s} {n:5d}字  {len(secs)}节  → {dst}")
        if not dry:
            open(dst, "w", encoding="utf-8").write(out)

    if "<!-- COMPANION-READS -->" in h:
        print("  母文已有入口条，跳过插入")
        return
    pos, why = find_anchor(h)
    assert pos, f"{slug}: 找不到插入锚点"
    bar = BAR_TPL.format(style=BAR_STYLE, slug=slug,
                         ex_title=esc(pages["explain"][0]["TITLE"]),
                         pr_title=esc(pages["practice"][0]["TITLE"]))
    new = h[:pos] + bar + h[pos:]
    print(f"  入口条插入位置：{why}（第 {h[:pos].count(chr(10))+1} 行后）")
    if not dry:
        open(os.path.join(PUB, "column", slug, "index.html"), "w", encoding="utf-8").write(new)


if __name__ == "__main__":
    main()
