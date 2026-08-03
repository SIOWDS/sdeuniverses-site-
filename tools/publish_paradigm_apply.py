#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日必读 · 应用文生成器
给 /paradigm/<slug>/ 的典范母文各配一篇约一万字的「应用文」：
  上篇＝日常类比的理论解释；下篇＝应用技术与方法流程（解决具体问题）
产出三种读法：
  apply.html            网页长文（复用母文自己的 CSS，视觉一致）
  apply-read.html       在线 PDF 翻页
  <slug>-apply.pdf      下载 PDF
并在母文「提要盒 / 导语」正下方插入入口条。

用法：
  python3 tools/publish_paradigm_apply.py <slug> [--dry] [--nopdf]

内容源：/home/claude/pa/<slug>.txt
  TITLE: 标题
  SUB:   副标题
  ABS:   提要（一段）
  == 章名
  正文段落（空行分段；行首 - 为条目行；行首 > 为引块；**粗体**）
"""
import os, re, sys, html, subprocess, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, "public")
CONTENT_DIR = os.environ.get("APPLY_CONTENT", "/home/claude/pa")
VER = "20260802b"
AUTHOR = "王德生 ＋ Claude"

EXTRA_CSS = """
.applybar{margin:26px 0 6px;padding:18px 20px;border-radius:12px;
 border:1px solid rgba(30,42,58,.18);background:rgba(255,255,255,.55)}
.applybar .al{font-size:11.5px;letter-spacing:.34em;color:#B5714A;margin-bottom:10px}
.applybar .at{font-size:16.5px;font-weight:700;margin:0 0 6px}
.applybar .ag{font-size:14.5px;line-height:1.85;opacity:.86;margin:0 0 12px}
.applybar .arow{display:flex;flex-wrap:wrap;gap:9px}
.applybar a.ab{display:inline-block;text-decoration:none;padding:9px 14px;border-radius:8px;
 border:1px solid rgba(30,42,58,.22);font-size:14px;color:inherit;background:rgba(255,255,255,.6)}
.applybar a.ab:hover{border-color:#B5714A;color:#B5714A}
.backm{margin:48px 0 8px;padding:22px 26px;border:1px solid rgba(30,42,58,.16);
 border-radius:12px;background:rgba(255,255,255,.5)}
.backm .sl{font-size:11.5px;letter-spacing:.4em;color:#B5714A;margin-bottom:10px}
.backm p{margin:0 0 10px;font-size:15px;line-height:1.9}
.part{margin:54px 0 6px;padding:14px 0 10px;border-top:2px solid rgba(181,113,74,.5);
 border-bottom:1px solid rgba(30,42,58,.12);font-size:13px;letter-spacing:.3em;color:#B5714A}

/* —— 应用文自带的一套，只作用于本页，保证任何母文主题下都能看 —— */
.abstract{margin:26px 0 18px;padding:22px 26px;border-radius:12px;
 border:1px solid rgba(30,42,58,.16);background:rgba(255,255,255,.5)}
.abstract .lb{display:block;font-size:11.5px;letter-spacing:.4em;color:#B5714A;margin-bottom:10px}
.abstract p{margin:0;font-size:15px;line-height:1.95}
.toc{margin:0 0 34px;padding:18px 22px;border:1px solid rgba(30,42,58,.14);border-radius:12px}
.toc .tl{font-size:11.5px;letter-spacing:.4em;color:#B5714A;margin-bottom:12px}
.toc a{display:block;text-decoration:none;color:inherit;font-size:14.5px;line-height:2.05;opacity:.86}
.toc a:hover{color:#B5714A}
p.li{margin:0 0 12px;padding-left:16px;border-left:3px solid rgba(181,113,74,.45)}
p.pull{margin:22px 0;padding:16px 20px;border-left:4px solid #B5714A;
 background:rgba(181,113,74,.07);font-size:16px;line-height:1.95}
h2{margin:44px 0 16px;font-size:21px;line-height:1.55}
"""


def esc(s):
    return html.escape(s, quote=True)


def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return t


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
                if mode != "li": flush(); mode = "li"
                buf.append(ln[2:].strip())
            elif ln.startswith("> "):
                if mode != "pull": flush(); mode = "pull"
                buf.append(ln[2:].strip())
            else:
                if mode != "p": flush(); mode = "p"
                buf.append(ln.strip())
        flush()
        out.append({"h": s["h"], "blocks": blocks})
    return meta, out


def render_body(secs):
    o = []
    for i, s in enumerate(secs, 1):
        head = s["h"]
        if head.startswith("//"):          # // 分卷标题
            o.append(f'<div class="part">{inline(head[2:].strip())}</div>')
            continue
        o.append(f'<h2 id="s{i}">{inline(head)}</h2>')
        for mode, buf in s["blocks"]:
            if mode == "p":
                o.append("<p>" + inline("".join(buf)) + "</p>")
            elif mode == "li":
                o.extend(f'<p class="li">{inline(x)}</p>' for x in buf)
            elif mode == "pull":
                o.append('<p class="pull">' + inline("".join(buf)) + "</p>")
    return "\n".join(o)


def count_cn(secs):
    return sum(len(re.findall(r"[\u4e00-\u9fff]", "".join("".join(b) for _, b in s["blocks"])))
               for s in secs)


def mother(slug):
    p = os.path.join(PUB, "paradigm", slug, "index.html")
    h = open(p, encoding="utf-8", errors="replace").read()
    m = re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S)
    title = re.sub(r"\s+", "", html.unescape(re.sub(r"<[^>]+>", "", m.group(1)))) if m else slug
    st = re.search(r"<style>(.*?)</style>", h, re.S)
    css = st.group(1) if st else ""
    ser = re.search(r'class="(?:art-series|hero-eyebrow)"[^>]*>(.*?)<', h, re.S)
    series = re.sub(r"\s+", "", ser.group(1)) if ser else ""
    return h, title, css, series


def find_anchor(h):
    """母文入口条落点：提要盒之后 → 导语之后 → 文章头之后。"""
    for cls in ("abstract", "deck"):
        m = re.search(r'<div[^>]*class="%s"' % cls, h)
        if m:
            depth = 0
            for mm in re.finditer(r"<div\b|</div>", h[m.start():]):
                if mm.group(0) == "</div>":
                    depth -= 1
                    if depth == 0:
                        end = m.start() + mm.end()
                        m2 = re.compile(r'\s*<p class="kw".*?</p>', re.S).match(h, end)
                        if m2:
                            end = m2.end()
                        return end, f"{cls} 之后"
                else:
                    depth += 1
    m = re.search(r"</header>|</div>\s*<div class=\"wrap\">", h)
    return (m.end(), "文章头之后") if m else (None, None)


BAR = """
<!-- APPLY-READ -->
<div class="applybar">
  <div class="al">配 套 应 用 文 · 约 一 万 字 · 三 种 读 法</div>
  <p class="at">{title}</p>
  <p class="ag">{sub}</p>
  <div class="arow">
    <a class="ab" href="/paradigm/{slug}/apply.html">📖 展开阅读（网页长文）</a>
    <a class="ab" href="/paradigm/{slug}/apply-read.html">📄 在线 PDF</a>
    <a class="ab" href="/paradigm/{slug}/{slug}-apply.pdf" download>⬇ 下载 PDF</a>
  </div>
</div>
<!-- /APPLY-READ -->
"""


def page(slug, meta, secs, mtitle, mseries, css, pages):
    toc = "".join(
        f'<a href="#s{i}">{esc(re.sub(r"<[^>]+>", "", s["h"]))}</a>'
        for i, s in enumerate(secs, 1) if not s["h"].startswith("//"))
    n = count_cn(secs)
    desc = re.sub(r"\s+", " ", re.sub(r"\*\*", "", meta["ABS"]))[:150]
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(meta['TITLE'])} · 应用文 · 每日必读</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:type" content="article">
<meta property="og:title" content="{esc(meta['TITLE'])}">
<meta property="og:description" content="{esc(desc)}">
<link rel="canonical" href="https://sdeuniverses.com/paradigm/{slug}/apply.html">
<style>{css}{EXTRA_CSS}</style></head>
<body>

<div class="readbar">
  <a class="nav-back" href="/paradigm/{slug}/">← 回母文《{esc(mtitle)}》</a>
  <div class="rb-modes"><a class="rb-btn cur" href="#">📖 网页长文</a><a class="rb-btn" href="apply-read.html">📄 在线 PDF</a><a class="rb-btn" href="{slug}-apply.pdf" download>⬇ 下载 PDF</a></div>
</div>

<div class="art">
  <div class="art-series">应 用 文 · 配 {esc(mseries) if mseries else '每 日 必 读'}</div>
  <h1 class="art-title">{esc(meta['TITLE'])}</h1>
  <p class="art-subtitle">{inline(meta['SUB'])}</p>
  <div class="art-meta">作者 {AUTHOR} · 约 {n} 字 · {pages} 页 · 三种读法 · 母文《{esc(mtitle)}》</div>
</div>

<div class="wrap">

<div class="abstract">
  <span class="lb">提 要</span>
  <p>{inline(meta['ABS'])}</p>
</div>

<div class="toc"><div class="tl">目 录</div>{toc}</div>

{render_body(secs)}

<div class="backm">
  <div class="sl">这 一 篇 的 母 文</div>
  <p>本文只做两件事：把母文的判断用日常场景讲透，再把它落成可以照着做的流程。完整的论证、来源与证伪条件在母文里：<a href="/paradigm/{slug}/">《{esc(mtitle)}》</a>。</p>
  <p>母文同样备有三种读法：<a href="/paradigm/{slug}/">网页长文</a> · <a href="/paradigm/{slug}/read.html">在线 PDF</a> · <a href="/paradigm/{slug}/{slug}.pdf" download>下载 PDF</a>。</p>
</div>

</div>
<script src="/taste/wds-companion/wds-read.js?v={VER}" defer></script>
<script src="/wds-mode.js?v={VER}" defer></script>
</body>
</html>
"""


READ = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · 应用文 · 在线PDF · 每日必读</title>
<style>html,body{{margin:0;height:100%;background:#1F1E1C}}
header{{height:56px;background:#26241F;display:flex;align-items:center;justify-content:space-between;padding:0 18px;font-family:"Songti SC","Noto Serif SC",serif;font-size:14px;border-bottom:1px solid rgba(196,99,90,.4);color:#E6E0D4}}
header a{{color:#C4635A;text-decoration:none}}
iframe{{width:100%;height:calc(100% - 56px);border:0;display:block}}</style></head>
<body><header><a href="apply.html">‹ 返回网页长文</a><span>{pages} 页 · {author}</span><a href="{slug}-apply.pdf" download>⬇ 下载 PDF</a></header>
<iframe src="{slug}-apply.pdf#view=FitH"></iframe><script src="/wds-mode.js?v={ver}" defer></script>
</body></html>
"""


def build_pdf(slug, pdf):
    src = os.path.join(PUB, "paradigm", slug, "apply.html")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build_pdf_paradigm.py"),
                        src, "-o", pdf], capture_output=True, text=True)
    if r.returncode != 0:
        print("  PDF 失败：", (r.stderr or r.stdout)[-500:])
        return 0
    try:
        from pypdf import PdfReader
        return len(PdfReader(pdf).pages)
    except Exception:
        return 0


def main():
    slug = sys.argv[1]
    dry = "--dry" in sys.argv
    nopdf = "--nopdf" in sys.argv
    mh, mtitle, css, mseries = mother(slug)
    meta, secs = parse(os.path.join(CONTENT_DIR, f"{slug}.txt"))
    n = count_cn(secs)
    d = os.path.join(PUB, "paradigm", slug)
    pdf = os.path.join(d, f"{slug}-apply.pdf")
    print(f"  {slug}: {n} 字 · {len([s for s in secs if not s['h'].startswith('//')])} 章")
    if dry:
        return
    pages = 0
    for rnd in (1, 2):                       # 页数循环依赖：先出一版读真页数再重出
        open(os.path.join(d, "apply.html"), "w", encoding="utf-8").write(
            page(slug, meta, secs, mtitle, mseries, css, pages or "—"))
        if nopdf:
            break
        p = build_pdf(slug, pdf)
        if not p:
            break
        if p == pages:
            break
        pages = p
    open(os.path.join(d, "apply-read.html"), "w", encoding="utf-8").write(
        READ.format(title=esc(meta["TITLE"]), pages=pages or "—",
                    author=AUTHOR, slug=slug, ver=VER))
    print(f"  → apply.html / apply-read.html / {slug}-apply.pdf（{pages} 页）")

    if "<!-- APPLY-READ -->" in mh:
        print("  母文已有入口条，跳过")
        return
    pos, why = find_anchor(mh)
    assert pos, f"{slug}: 找不到锚点"
    bar = BAR.format(slug=slug, title=esc(meta["TITLE"]), sub=inline(meta["SUB"]))
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(mh[:pos] + bar + mh[pos:])
    print(f"  入口条：{why}")


if __name__ == "__main__":
    main()
