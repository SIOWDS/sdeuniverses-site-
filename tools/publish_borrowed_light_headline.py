from pathlib import Path
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
import html
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "tmp" / "borrowed-light-expanded.docx"
OUT = ROOT / "public" / "column" / "origin-claim-innovation" / "index.html"


def iter_blocks(doc):
    for child in doc.element.body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, doc)
        elif isinstance(child, CT_Tbl):
            yield Table(child, doc)


def table_html(table):
    rows = []
    for r_i, row in enumerate(table.rows):
        cells = []
        for cell in row.cells:
            text = " ".join(p.text.strip() for p in cell.paragraphs if p.text.strip())
            tag = "th" if r_i == 0 and len(table.rows) > 1 else "td"
            cells.append(f"<{tag}>{html.escape(text)}</{tag}>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return '<div class="table-wrap"><table>' + "".join(rows) + "</table></div>"


doc = Document(SOURCE)
parts = []
started = False
in_refs = False

for block in iter_blocks(doc):
    if isinstance(block, Paragraph):
        text = block.text.strip()
        if not started:
            if text.replace(" ", "") in {"摘要", "摘　要"}:
                started = True
                parts.append("<h2>摘要</h2>")
            continue
        if not text:
            continue
        style = block.style.name if block.style else ""
        if style == "Heading 1":
            in_refs = text == "参考文献"
            parts.append(f"<h2>{html.escape(text)}</h2>")
        elif style == "Heading 2":
            parts.append(f"<h3>{html.escape(text)}</h3>")
        elif style == "Heading 3":
            parts.append(f"<h4>{html.escape(text)}</h4>")
        elif style == "FigureCaption":
            parts.append(f"<div class='caption'>{html.escape(text)}</div>")
        elif style == "Reference" or in_refs:
            parts.append(f"<p class='reference'>{html.escape(text)}</p>")
        elif style in {"AbstractText", "EnglishAbstract"}:
            parts.append(f"<p class='abstract-text'>{html.escape(text)}</p>")
        elif style == "Keywords":
            parts.append(f"<p class='keywords'>{html.escape(text)}</p>")
        elif text == "文章结构":
            parts.append("<h2>文章结构</h2>")
        elif re.fullmatch(r"(GI|OOI|EVI)\s*=.*", text):
            parts.append(f"<div class='formula'>{html.escape(text)}</div>")
        else:
            parts.append(f"<p>{html.escape(text)}</p>")
    else:
        if started:
            parts.append(table_html(block))

body = "\n".join(parts)
html_doc = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>借来的光与站不住的土 | 王德生 | 今日头条 | SDE Universes</title>
<meta name="description" content="王德生：华语公共叙事中籍贯图腾对本土创新发生学的阻断机制。基于SDE本体论的概念模型、比较案例与制度命题。">
<style>
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}:root{{--bg:#f4eddd;--paper:#fffaf0;--ink:#211d17;--muted:#746653;--gold:#9a711c;--red:#87352f;--blue:#295b72;--line:#d9c9aa}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:"Noto Serif SC","Songti SC",Georgia,serif;line-height:1.95}}a{{color:var(--blue);text-decoration:none}}a:hover{{text-decoration:underline}}
nav{{height:66px;padding:0 5vw;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--line);background:rgba(244,237,221,.96);position:sticky;top:0;z-index:10}}.brand{{color:#71392f;letter-spacing:.1em}}.back{{color:var(--muted);font-size:14px}}
.hero{{max-width:1080px;margin:auto;padding:82px 26px 58px;text-align:center}}.kicker{{font-size:13px;color:var(--red);font-weight:700;letter-spacing:.26em}}
h1{{font-size:clamp(40px,5.7vw,70px);line-height:1.22;margin:18px 0 20px}}.deck{{max-width:900px;margin:0 auto 22px;color:#5f5140;font-size:21px}}.meta{{color:var(--muted);font-size:14px}}
.reading-modes{{display:flex;justify-content:center;flex-wrap:wrap;gap:12px;margin:28px auto 0}}.mode-link{{display:inline-flex;align-items:center;justify-content:center;min-width:150px;padding:10px 18px;border:1px solid #b99a5c;border-radius:999px;background:#fffaf0;color:#6f4b15;font-size:15px;box-shadow:0 5px 18px rgba(87,62,20,.08)}}.mode-link:hover{{background:#f3e5c3;text-decoration:none}}.mode-link.active{{background:#8d6718;color:#fff;border-color:#8d6718}}
.editor-note{{max-width:940px;margin:0 auto 42px;padding:24px 30px;background:#edf4f5;border:1px solid #bfd2d6;border-left:4px solid var(--blue);border-radius:10px;line-height:1.8}}
article{{max-width:940px;margin:auto;padding:0 28px 84px;font-size:18px}}h2{{font-size:30px;line-height:1.45;color:#294e5e;margin:58px 0 20px;padding-bottom:10px;border-bottom:1px solid var(--line)}}h3{{font-size:23px;color:#7b4b24;margin:38px 0 13px}}h4{{font-size:20px;color:#6a4427;margin:30px 0 10px}}p{{margin:0 0 1.3em;text-align:justify}}
.abstract-text{{background:rgba(255,250,240,.72);margin-bottom:0;padding:0 26px 1.15em}}h2+ .abstract-text{{padding-top:24px;border-radius:12px 12px 0 0}}.keywords{{background:#fffaf0;padding:14px 26px;border:1px solid var(--line);border-radius:0 0 12px 12px;color:#6b5639}}
.table-wrap{{overflow-x:auto;margin:28px 0 38px;border:1px solid var(--line);border-radius:10px;background:var(--paper)}}table{{border-collapse:collapse;width:100%;min-width:680px}}th,td{{border-bottom:1px solid #e4d8bf;border-right:1px solid #e4d8bf;padding:13px 15px;text-align:left;vertical-align:top}}th{{background:#e9dfc9;color:#654918}}tr:last-child td{{border-bottom:0}}td:last-child,th:last-child{{border-right:0}}
.caption{{font-size:15px;color:var(--gold);font-weight:700;margin:24px 0 8px}}.formula{{margin:18px 0;padding:18px 22px;background:#2b2924;color:#f6ecd6;border-left:4px solid #d2aa4d;font-family:Georgia,"Noto Serif SC",serif}}
.reference{{font-size:16px;padding-left:2em;text-indent:-2em;margin-bottom:.72em}}.note{{font-size:14px;color:var(--muted)}}.footnav{{display:flex;justify-content:space-between;gap:18px;margin-top:58px;padding-top:24px;border-top:1px solid var(--line)}}
footer{{text-align:center;border-top:1px solid var(--line);padding:30px;color:var(--muted);font-size:13px}}
@media(max-width:720px){{.hero{{padding-top:52px}}.deck{{font-size:18px}}article{{font-size:17px;padding-left:19px;padding-right:19px}}h2{{font-size:26px}}.back{{display:none}}}}
</style></head><body>
<nav><a class="brand" href="/">SDE Universes</a><a class="back" href="/headline/">← 每日头条</a></nav>
<header class="hero"><div class="kicker">今日头条 · 理论研究论文 · 2万字扩充精排版</div>
<h1>借来的光与站不住的土</h1>
<p class="deck">华语公共叙事中“籍贯图腾”对本土创新发生学的阻断机制——基于SDE本体论的概念模型、比较案例与制度命题</p>
<div class="meta">王德生 · 2026年7月24日 · 中文正文约20,266汉字 · 三种阅读模式</div>
<div class="reading-modes" aria-label="阅读方式">
<a class="mode-link active" href="./" aria-current="page">网页精读</a>
<a class="mode-link" href="read.html">在线 PDF 翻页</a>
<a class="mode-link" href="borrowed-light.pdf" download>下载 PDF</a>
</div></header>
<aside class="editor-note"><strong>本版说明：</strong>采用《借来的光与站不住的土_2万字扩充精排版》作为唯一正式底稿。全文已纳入2026年菲尔兹奖最新事实，区分真实成果Sᵣ与叙事结算Sₙ，加入比较案例、可证伪命题、治理指标与经验研究纲领。原稿中关于June Huh与马克龙祝贺的错误案例已经删除。</aside>
<article>{body}<div class="footnav"><a href="/headline/">← 每日头条存档</a><a href="/">返回首页 →</a></div></article>
<footer>© 德麦国际 Demai International · 王德生 · SDE Universes</footer>
</body></html>"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(html_doc, encoding="utf-8")
print(OUT)
print("characters", len(re.sub(r"<[^>]+>", "", body)))
print("tables", body.count("<table>"), "h2", body.count("<h2>"))
