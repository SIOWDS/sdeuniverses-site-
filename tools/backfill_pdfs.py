# -*- coding: utf-8 -*-
"""给学员专栏里缺 PDF 的作品页补上「在线 PDF + 下载 PDF」两种读法。

做三件事：
  ① 从已有的网页长文里抽出正文，排成 A4 版式，wkhtmltopdf 生成 <slug>.pdf
  ② 生成 read.html（PDF.js 翻页壳，与站上其余 460 余篇同一形制）
  ③ 修 readbar：补齐三读法按钮，并把指向错误 slug 的死链改对

纪律：
  · 只读页面已有内容，不新写、不改写任何正文
  · 页脚导流区（.endbox）、组内导航（.pnbar）、交互卡（.tk-*/.xp-*）不进 PDF
  · 生成后校验页数 > 0 且 PDF 首页能抽出中文，否则该页回滚不写入
"""
import argparse
import html as H
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STU = ROOT / "public" / "students"
TMP = Path("/tmp/pdfgen")
TMP.mkdir(exist_ok=True)
SKIP_DIRS = {"works", "poems", "essays"}

PRINT_CSS = """
@page{size:A4}
body{font-family:"Noto Serif CJK SC","Noto Serif SC",serif;color:#1A1710;font-size:10.5pt;line-height:1.85;margin:0}
.cover{text-align:center;padding-bottom:13pt;border-bottom:1.2pt solid #9A7C22;margin-bottom:16pt}
.eyebrow{color:#9A7C22;letter-spacing:.3em;font-size:7.8pt;margin-bottom:10pt}
h1{font-size:18.5pt;line-height:1.44;margin:0 0 8pt;color:#2A2411}
.sub{font-size:10pt;color:#4A4636;margin:0 auto 10pt;max-width:34em;line-height:1.7}
.by{font-size:9pt;color:#57513F}.by b{color:#9A7C22}
.abs{background:#F5F2E6;border-left:3pt solid #9A7C22;padding:11pt 13pt;margin:0 0 12pt;font-size:9.4pt;line-height:1.75;text-align:justify}
.abs .lb{letter-spacing:.32em;color:#2A2411;font-weight:700}
h2{font-size:13pt;color:#2A2411;padding-left:8pt;border-left:3.5pt solid #9A7C22;margin:19pt 0 9pt;page-break-after:avoid}
h3{font-size:11pt;color:#3A3418;margin:13pt 0 6pt;page-break-after:avoid}
p{text-indent:2em;text-align:justify;margin:0 0 8pt}
blockquote{margin:9pt 0 9pt 2em;padding-left:10pt;border-left:2pt solid #D8C89A;color:#4A4636}
blockquote p{text-indent:0}
li{margin:0 0 5pt;text-align:justify}
.ref{text-indent:-1.6em;padding-left:1.6em;font-size:8.8pt;color:#4A4636;margin:0 0 4pt;text-align:left}
"""

READ_TPL = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · 在线PDF · {author}</title>
<style>html,body{{margin:0;height:100%;background:#0E0B08}}
header{{height:56px;background:#171310;display:flex;align-items:center;justify-content:space-between;padding:0 18px;font-family:"Songti SC","Noto Serif SC",serif;font-size:14px;border-bottom:1px solid rgba(201,168,76,0.28);color:#B8AE96}}
header a{{color:#C9A84C;text-decoration:none}}
iframe{{width:100%;height:calc(100% - 56px);border:0;display:block}}</style></head>
<body><header><a href="index.html">‹ 返回网页长文</a><span>{pages} 页 · {author}</span><a href="{pdf}" download>⬇ 下载 PDF</a></header>
<iframe src="{pdf}#view=FitH"></iframe></body></html>"""

DROP = re.compile(
    r'<div class="(?:endbox|pnbar|tk-[^"]*|xp-[^"]*|innov|sde-expert|sde-revnote)"[^>]*>.*?</div>\s*|'
    r'<nav class="pnbar".*?</nav>|<script\b.*?</script>|<style\b.*?</style>|'
    r'<form\b.*?</form>|<button\b.*?</button>', re.S | re.I)

BLOCK = re.compile(r"<(h2|h3|h4|p|li|blockquote)\b([^>]*)>(.*?)</\1>", re.S | re.I)


def txt(s):
    s = re.sub(r"<br\s*/?>", " ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    return H.unescape(s).strip()


def field(t, cls):
    m = re.search(r'class="%s"[^>]*>(.*?)</(?:div|span|h1)>' % cls, t, re.S)
    return txt(m.group(1)) if m else ""


def extract(t):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", t, re.S)
    title = txt(m.group(1)) if m else ""
    sub = field(t, "art-subtitle")
    series = field(t, "art-series")
    meta = field(t, "art-meta")

    # 正文区：从 .wrap（或 h1 之后）到 endbox / body 结束
    i = t.find('<div class="wrap"')
    if i < 0:
        i = t.find("</header>")
    if i < 0 and m:
        i = t.find("</h1>", t.find("<h1"))
    j = t.find('<div class="endbox"')
    if j < 0:
        j = t.rfind("</body>")
    region = t[i:j if j > i else len(t)]
    region = DROP.sub("", region)

    abstract = ""
    ma = re.search(r'class="abs"[^>]*>(.*?)</div>', region, re.S)
    if ma:
        abstract = txt(ma.group(1))
        region = region.replace(ma.group(0), "")

    blocks = []
    for b in BLOCK.finditer(region):
        tag, attrs, inner = b.group(1).lower(), b.group(2), txt(b.group(3))
        if not inner or len(inner) < 2:
            continue
        cls = (re.search(r'class="([^"]*)"', attrs) or [None, ""])[1] if 'class="' in attrs else ""
        if tag == "li":
            tag, cls = "p", cls
        if "ref" in cls:
            blocks.append(("ref", inner))
        else:
            blocks.append((tag, inner))
    return title, sub, series, meta, abstract, blocks


def render(title, sub, series, meta, abstract, blocks, author):
    body = []
    for tag, line in blocks:
        if tag == "ref":
            body.append('<p class="ref">%s</p>' % H.escape(line))
        elif tag == "blockquote":
            body.append("<blockquote><p>%s</p></blockquote>" % H.escape(line))
        else:
            body.append("<%s>%s</%s>" % (tag, H.escape(line), tag))
    abs_html = ('<div class="abs"><span class="lb">摘 要</span>　%s</div>' % H.escape(abstract)) if abstract else ""
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{H.escape(title)}</title><style>{PRINT_CSS}</style></head><body>
<div class="cover"><div class="eyebrow">SDE UNIVERSES · 学员专栏 · {H.escape(author)}</div>
<h1>{H.escape(title)}</h1>{'<p class="sub">%s</p>' % H.escape(sub) if sub else ''}
<div class="by">{H.escape(meta or series)}</div></div>
{abs_html}{''.join(body)}</body></html>"""


def build_pdf(ph, pdf):
    subprocess.run(["wkhtmltopdf", "--encoding", "utf-8", "--page-size", "A4",
                    "--margin-top", "20", "--margin-bottom", "18",
                    "--margin-left", "19", "--margin-right", "19", "--quiet",
                    str(ph), str(pdf)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    o = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=True)
    m = re.search(r"Pages:\s+(\d+)", o.stdout)
    return int(m.group(1)) if m else 0


def fix_readbar(t, slug, name):
    """补齐/修正三读法按钮；返回 (新文本, 说明)。"""
    modes = ('<div class="rb-modes">'
             '<span class="rb-btn cur">📖 长文阅读</span>'
             f'<a class="rb-btn" href="read.html">📄 在线 PDF</a>'
             f'<a class="rb-btn" href="{slug}.pdf" download>⬇ 下载 PDF</a>'
             "</div>")
    m = re.search(r'<div class="rb-modes">.*?</div>\s*(?=</div>)', t, re.S)
    if m:
        if f'href="{slug}.pdf"' in m.group(0) and 'href="read.html"' in m.group(0):
            return t, "读法条已正确"
        return t.replace(m.group(0), modes, 1), "修正读法条（原链接指向别的文件）"
    m = re.search(r'(<div class="readbar"[^>]*>\s*<a class="nav-back".*?</a>)', t, re.S)
    if m:
        return t.replace(m.group(1), m.group(1) + modes, 1), "补上读法条"
    nav = (f'<div class="readbar"><a class="nav-back" href="/students/{name}/works/">'
           f'‹ 全部作品</a>{modes}</div>')
    m = re.search(r"<body[^>]*>", t)
    if m:
        return t[:m.end()] + nav + t[m.end():], "新建读法条"
    return t, "找不到插入点"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="只处理某学员 slug")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    names = {}
    done = failed = 0
    for stu in sorted(p for p in STU.iterdir() if p.is_dir()):
        if a.only and stu.name != a.only:
            continue
        prof = stu / "index.html"
        nm = stu.name
        if prof.exists():
            mm = re.search(r"<h1[^>]*>(.*?)</h1>", prof.read_text(encoding="utf-8"), re.S)
            if mm:
                nm = txt(mm.group(1)).split("·")[0].strip() or stu.name
        names[stu.name] = nm

        for d in sorted(p for p in stu.iterdir() if p.is_dir()):
            if d.name in SKIP_DIRS:
                continue
            idx = d / "index.html"
            if not idx.exists():
                continue
            t = idx.read_text(encoding="utf-8")
            if "art-title" not in t and "readbar" not in t:
                continue
            if list(d.glob("*.pdf")):
                continue
            if a.limit and done >= a.limit:
                break

            title, sub, series, meta, abstract, blocks = extract(t)
            chars = sum(len(x) for _, x in blocks)
            if not title or chars < 400:
                print(f"  ✗ {stu.name}/{d.name}  抽正文失败（标题{'有' if title else '无'} · 正文 {chars} 字）")
                failed += 1
                continue

            ph = TMP / f"{stu.name}__{d.name}.html"
            ph.write_text(render(title, sub, series, meta, abstract, blocks, nm), encoding="utf-8")
            pdf = d / f"{d.name}.pdf"
            if a.dry:
                print(f"  · {stu.name}/{d.name}  {chars} 字 / {len(blocks)} 块  → 将生成")
                done += 1
                continue
            try:
                pages = build_pdf(ph, pdf)
            except Exception as e:
                print(f"  ✗ {stu.name}/{d.name}  wkhtmltopdf 失败 {e}")
                failed += 1
                continue
            probe = subprocess.run(["pdftotext", "-f", "1", "-l", "1", str(pdf), "-"],
                                   capture_output=True, text=True).stdout
            if pages < 1 or not re.search(r"[\u4e00-\u9fff]", probe):
                pdf.unlink(missing_ok=True)
                print(f"  ✗ {stu.name}/{d.name}  PDF 校验不过（{pages} 页），已回滚")
                failed += 1
                continue

            (d / "read.html").write_text(READ_TPL.format(
                title=H.escape(title), author=H.escape(nm), pages=pages,
                pdf=f"{d.name}.pdf"), encoding="utf-8")
            t2, note = fix_readbar(t, d.name, stu.name)
            if t2 != t:
                idx.write_text(t2, encoding="utf-8")
            print(f"  ✓ {stu.name}/{d.name:34s} {chars:>6d}字 {pages:>3d}页  {note}")
            done += 1

    print(f"\n  完成 {done} 页，失败 {failed} 页")


if __name__ == "__main__":
    main()
