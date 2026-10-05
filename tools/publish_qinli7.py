# -*- coding: utf-8 -*-
"""秦莉《主体间性的发生》单篇 · 建页 + 打印版 PDF + read.html。

用法： python3 tools/publish_qinli7.py --docx /home/claude/shijing/paper/论文_主体间性的发生_修订版.docx
<head>/尾部脚本从秦莉最新既有论文页 beheld-vanishing 复制；read.html 同样复制其模板。
roster.json / publications.json 由 build_roster.py / align_publications.py 处理，本脚本不碰。
PDF 在 .gitignore 里（学员 PDF 走 R2），本脚本只写到本地 public/ 下供上传。
"""
import argparse, html, re, subprocess, sys
from pathlib import Path
import docx
from docx.table import Table
from docx.text.paragraph import Paragraph

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qinli7_meta import *

ROOT = Path(__file__).resolve().parents[1]
SKEL = ROOT / "public/students/qin-li/beheld-vanishing"
OUT = ROOT / "public/students" / STUDENT / SLUG

H2 = re.compile(r"^[一二三四五六七八九十]+、")
H3 = re.compile(r"^\d+\.\d+ ")
EXTRA_H3 = {"第一组：证伪条款", "第二组：可执行设计说明"}
H2_EXACT = {"注释与声明", "参考文献"}
TABLE_AFTER = "下表汇总十九条记录的编码"


def esc(t): return html.escape(t, quote=False)


def load(path):
    d = docx.Document(path)
    items = []
    for el in d.element.body.iterchildren():
        if el.tag.endswith("}p"):
            items.append(("p", Paragraph(el, d).text.replace("\xa0", " ").strip()))
        elif el.tag.endswith("}tbl"):
            items.append(("t", [[c.text.replace("\xa0", " ").strip() for c in r.cells] for r in Table(el, d).rows]))
    return items


def parse(items):
    meta = {}
    blocks = []
    mode = "body"
    for kind, v in items:
        if kind == "t":
            blocks.append(("table", v)); continue
        if not v:
            continue
        if v.startswith("▸ 写作说明"):
            break                       # 编辑残留，丢弃
        if v == TITLE:
            continue
        if v.startswith("Title:"):
            meta["entitle"] = v[len("Title:"):].strip(); continue
        if v.startswith("【摘要】"):
            meta["abs"] = v[4:].strip(); continue
        if v.startswith("【关键词】"):
            meta["kw"] = v[5:].strip(); continue
        if v.startswith("【Abstract】"):
            meta["eabs"] = v[len("【Abstract】"):].strip(); continue
        if v.startswith("【Keywords】"):
            meta["ekw"] = v[len("【Keywords】"):].strip(); continue
        if len(v) < 40 and (H2.match(v) or v in H2_EXACT):
            mode = "ref" if v == "参考文献" else "body"
            blocks.append(("h2", v)); continue
        if len(v) < 40 and (H3.match(v) or v in EXTRA_H3):
            blocks.append(("h3", v)); continue
        blocks.append(("ref" if mode == "ref" else "p", v))
    return meta, blocks


def table_html(rows, cls):
    head, body = rows[0], rows[1:]
    th = "".join(f"<th>{esc(c)}</th>" for c in head)
    tr = "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>" for r in body)
    t = f'<table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>'
    return f'<div class="tblwrap">{t}</div>' if cls == "tbl" else t


def render_body(blocks, cls):
    out = []
    for tag, v in blocks:
        if tag == "table":
            out.append(table_html(v, cls))
        elif tag == "ref":
            out.append(f'<p class="ref">{esc(v)}</p>')
        else:
            out.append(f"<{tag}>{esc(v)}</{tag}>")
    return "\n".join(out)


EXTRA_CSS = """<style>
.wrap .tblwrap{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:22px 0}
.wrap .tblwrap table.tbl{margin:0;min-width:760px;font-size:13.5px;line-height:1.6}
.wrap .tblwrap table.tbl th,.wrap .tblwrap table.tbl td{padding:8px 9px}
.wrap .abstract.en,.wrap .keywords.en{font-size:.93em;opacity:.92}
.wrap .abstract.en p{text-indent:0}
.wrap .entitle{font-style:italic;opacity:.8;margin:0 0 14px;font-size:.95em}
</style>
"""

PRINT_CSS = """
@page{size:A4}
body{font-family:"Noto Serif CJK SC","Noto Serif SC",serif;color:#1A1710;font-size:10.5pt;line-height:1.85;margin:0}
.cover{text-align:center;padding-bottom:13pt;border-bottom:1.2pt solid #9A7C22;margin-bottom:16pt}
.eyebrow{color:#9A7C22;letter-spacing:.3em;font-size:7.8pt;margin-bottom:10pt}
h1{font-size:18.5pt;line-height:1.44;margin:0 0 8pt;color:#2A2411}
.sub{font-size:10pt;color:#4A4636;margin:0 auto 10pt;max-width:34em;line-height:1.7;font-style:italic;text-indent:0}
.by{font-size:9pt;color:#57513F}.by b{color:#9A7C22}
.abs{background:#F5F2E6;border-left:3pt solid #9A7C22;padding:11pt 13pt;margin:0 0 12pt;font-size:9.4pt;line-height:1.75;text-align:justify}
.abs .lb{letter-spacing:.32em;color:#2A2411;font-weight:700}
.abs.en{font-size:8.6pt;line-height:1.6}.abs.en .lb{letter-spacing:.1em}
.kw{font-size:9pt;color:#57513F;margin:0 0 16pt}
h2{font-size:13pt;color:#2A2411;padding-left:8pt;border-left:3.5pt solid #9A7C22;margin:19pt 0 9pt;page-break-after:avoid}
h3{font-size:11pt;color:#3A3418;margin:13pt 0 6pt;page-break-after:avoid}
p{text-indent:2em;text-align:justify;margin:0 0 8pt}
.ref{text-indent:-2em;padding-left:2em;font-size:8.8pt;color:#4A4636;margin:0 0 4pt;text-align:left}
table.ptbl{width:100%;border-collapse:collapse;font-size:7.6pt;line-height:1.45;margin:8pt 0 12pt;table-layout:fixed;word-wrap:break-word}
table.ptbl th{background:#F5F2E6;border:.5pt solid #B9A66A;padding:3pt 3pt;text-align:left;color:#2A2411}
table.ptbl td{border:.5pt solid #CBBE93;padding:3pt 3pt;vertical-align:top;text-indent:0}
table.ptbl tr{page-break-inside:avoid}
thead{display:table-header-group}
"""


RAD = {"\u2eda": "页", "\u2ed3": "长", "\u2ee2": "马", "\u2ec9": "贝", "\u2ec5": "见", "\u2eec": "齐",
       "\u2edb": "风", "\u2ec6": "角", "\u2ed4": "门", "\u2ea0": "民", "\u2ee5": "鱼"}


def postprocess(pdf):
    """① 封面以外每页盖页码（沙盒 wkhtmltopdf 忽略 --footer）；② 修 ToUnicode：把康熙部首/部首补充区映射回常用汉字，PDF 才搜得到。"""
    import io, unicodedata
    from pypdf import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas
    r = PdfReader(str(pdf)); w = PdfWriter()
    for i, pg in enumerate(r.pages):
        if i > 0:
            W, H = float(pg.mediabox.width), float(pg.mediabox.height)
            buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=(W, H))
            c.setFont("Helvetica", 8.5); c.drawCentredString(W / 2, 28, str(i + 1)); c.showPage(); c.save(); buf.seek(0)
            pg.merge_page(PdfReader(buf).pages[0])
        w.add_page(pg)
    seen = set()

    def tok(m):
        ch = chr(int(m.group(1), 16))
        if "\u2e80" <= ch <= "\u2fdf":
            n = RAD.get(ch) or unicodedata.normalize("NFKC", ch)
            assert len(n) == 1 and not ("\u2e80" <= n <= "\u2fdf"), hex(ord(ch))
            return "<%04X>" % ord(n)
        return m.group(0)
    for pg in w.pages:
        for f in pg["/Resources"].get("/Font", {}).values():
            f = f.get_object(); tu = f.get("/ToUnicode")
            if tu is None: continue
            so = tu.get_object()
            if id(so) in seen: continue
            seen.add(id(so))
            txt = so.get_data().decode("latin1")
            new = re.sub(r"\[([^\]]*)\]", lambda m: "[" + re.sub(r"<([0-9A-Fa-f]{4})>", tok, m.group(1)) + "]", txt)
            so.set_data(new.encode("latin1"))
    with open(pdf, "wb") as fh:
        w.write(fh)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--docx", required=True); a = ap.parse_args()
    meta, blocks = parse(load(a.docx))
    assert all(k in meta for k in ("abs", "kw", "eabs", "ekw", "entitle")), meta.keys()
    body_text = "".join(v for t, v in blocks if t in ("p", "h2", "h3", "ref")) + meta["abs"] + meta["kw"]
    chars = len(re.findall(r"[一-鿿]", body_text))
    wan = f"{chars/10000:.1f}"
    print("汉字数", chars, "→", wan, "万字；块数", len(blocks))

    sk = (SKEL / "index.html").read_text(encoding="utf-8")
    head = sk[:sk.index('<div class="wrap">')]
    tail = sk[sk.index('<footer>'):]
    # <head> 替换标题与描述
    head = re.sub(r"<title>.*?</title>", f"<title>{esc(TITLE)} · {NAME} · SDE 学员专栏</title>", head, 1, flags=re.S)
    head = re.sub(r'<meta name="description" content=".*?">', f'<meta name="description" content="{html.escape(HOOK)}">', head, 1, flags=re.S)
    head = head.replace("</head>", EXTRA_CSS + "</head>", 1)
    head = re.sub(r'<div class="art-series">.*?</div>', f'<div class="art-series">学员专栏 · {NAME} · {SERIES}</div>', head, 1)
    head = re.sub(r'<h1 class="art-title">.*?</h1>', f'<h1 class="art-title">{esc(TITLE)}</h1>', head, 1)
    head = re.sub(r'<div class="art-subtitle">.*?</div>', f'<div class="art-subtitle">{esc(meta["entitle"])}</div>', head, 1)
    head = re.sub(r'<div class="art-meta">.*?</div>',
                  f'<div class="art-meta">作者 {NAME} · {ROLE} · 约 {wan} 万字 · 发表于{PUBDATE_CN}</div>', head, 1)
    head = head.replace("beheld-vanishing", SLUG)
    tail = tail.replace("beheld-vanishing", SLUG)
    tail = re.sub(r"秦莉", NAME, tail)
    assert "悲剧" not in head and "beheld" not in head

    # 页尾 endbox（照 beheld-vanishing 样式，不放评分/深化说明）
    endbox = (f'<div class="endbox">\n  <div class="lbl">三 种 读 法</div>\n  <div class="big">网页长文 · 在线 PDF 翻页 · PDF 下载</div>\n'
              f'  <p>本文声明：未执行任何经验检验，多条证伪条款标注为未执行；样本有限、单一编码者。</p>\n'
              f'  <a class="solid" href="{SLUG}.pdf" download>⬇ 下载 PDF</a>\n'
              f'  <a class="ghost" href="/students/{STUDENT}/works/">返回 {NAME} 全部作品</a>\n</div>\n</div>\n')
    page = (head + '<div class="wrap">\n'
            f'<div class="abstract"><span class="ab-lbl">摘 要</span><p>{esc(meta["abs"])}</p></div>\n'
            f'<div class="keywords"><strong>关键词：</strong>{esc(meta["kw"])}</div>\n'
            f'<div class="abstract en"><span class="ab-lbl">Abstract</span><p>{esc(meta["eabs"])}</p></div>\n'
            f'<div class="keywords en"><strong>Keywords:</strong> {esc(meta["ekw"])}</div>\n'
            + render_body(blocks, "tbl") + "\n" + endbox + tail)

    # 打印版
    pr = (f'<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><title>{esc(TITLE)}</title><style>{PRINT_CSS}</style></head><body>'
          f'<div class="cover"><div class="eyebrow">SDE UNIVERSES · 学员专栏 · {NAME}</div><h1>{esc(TITLE)}</h1>'
          f'<p class="sub">{esc(meta["entitle"])}</p>'
          f'<div class="by"><b>{NAME}</b> 著　·　{ROLE}　·　{esc(SERIES)}　·　{PUBDATE_CN}</div></div>'
          f'<div class="abs"><span class="lb">摘 要</span>　{esc(meta["abs"])}</div>'
          f'<div class="kw"><b>关键词：</b>{esc(meta["kw"])}</div>'
          f'<div class="abs en"><span class="lb">Abstract</span>　{esc(meta["eabs"])}</div>'
          f'<div class="kw"><b>Keywords:</b> {esc(meta["ekw"])}</div>'
          + render_body(blocks, "ptbl") + "</body></html>")

    # 完整性自检
    for t, k in ((page, "page"), (pr, "print")):
        for tag in ("div", "table", "html"):
            assert len(re.findall(rf"<{tag}[\s>]", t)) == len(re.findall(rf"</{tag}>", t)), (k, tag)
        assert "写作说明" not in t
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "index.html").write_text(page, encoding="utf-8")
    ph = Path("/tmp/claude-0/ql7_print.html"); ph.write_text(pr, encoding="utf-8")
    pdf = OUT / f"{SLUG}.pdf"
    subprocess.run(["wkhtmltopdf", "--encoding", "utf-8", "--page-size", "A4",
                    "--margin-top", "20", "--margin-bottom", "18", "--margin-left", "19", "--margin-right", "19",
                    "--footer-center", "[page]", "--footer-font-size", "8", "--footer-spacing", "6", "--quiet",
                    str(ph), str(pdf)], check=True)
    postprocess(pdf)
    pages = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout).group(1))
    rd = (SKEL / "read.html").read_text(encoding="utf-8")
    rd = rd.replace("悲剧美学的发生学重构：可回改窗口与「被看见的消失」", TITLE).replace("beheld-vanishing", SLUG)
    assert "悲剧" not in rd
    (OUT / "read.html").write_text(rd, encoding="utf-8")
    print("页数", pages, "wan", wan)


if __name__ == "__main__":
    main()
