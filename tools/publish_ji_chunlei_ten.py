# -*- coding: utf-8 -*-
"""季春雷（SDE 预备学员）十篇 · 改姓 + 深化增补 + 三种读法 + 上站。

用法：
    python3 tools/publish_ji_chunlei_ten.py --src /home/claude/jcl

流程：读源 txt → 改姓与清理（带 assert 锚定）→ 解析段落 →
      长文页 index.html / 印刷版 → wkhtmltopdf 出 PDF → read.html →
      works 索引 → 学员主页 → publications.json。
roster.json 与搜索索引由 build_roster.py / build_search_index.py 派生，本脚本不碰。
"""
import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jcl_meta import AUTHOR, STUDENT, PUBDATE_CN, PUBDATE_ISO, THEME, PAPERS, SRC_MAP
from jcl_supp import SUPPLEMENTS, REFERENCES

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "public" / "students" / STUDENT

# ── 改姓：SDE 招牌词 → 目标学科本地说法（顺序敏感，长词先行）────────────
RENAME = [
    # “发现学”是 SDE 内部“发生 vs 发现”的对置，学科读者不解其意，逐处换成本地说法
    ("发现学的路径", "定义先行的路径"),
    ("发现学的防御姿态", "定义先行的防御姿态"),
    ("拿给发现学看", "拿给通常的自我实现叙事看"),
    ("典型的发现学叙事", "典型的成果回溯叙事"),
    ("发生学分析", "生成机制分析"),
    ("发生学重构", "生成论重构"),
    ("发生学前提", "生成前提"),
    ("发生学理论", "生成论"),
    ("发生学概念", "生成论概念"),
    ("发生学的", "生成论的"),
    ("发生学", "生成论"),
    ("本体论级", "根本层面"),
    ("社会本体论", "社会存在论"),
    ("本体论", "存在论"),
    ("特征纠缠", "特征耦合"),
    ("纠缠", "交织"),
    ("显露", "显现"),
    ("裂缝", "缝隙"),
]

# ── 逐句清理：删水印 / 删自指与布道 / 删自我表彰 / 拆草稿痕迹 ──────────
# ("篇号", 类型, 锚, 替换)   类型: drop=整段删, sub=段内替换
CLEANUP = [
    ("01", "drop", "中华智问知识发生器 · sdeuniverses.com", None),
    ("02", "drop", "在此之前，我将继续相信", None),
    ("03", "drop", "这个检验设计，是本文理论最硬的一块学术分量", None),
    ("06", "sub", "在那一天到来之前，亲体冷凝这面旗可以继续插在这里。",
     "在那一天到来之前，本文的判断保持有效，并继续等待上述三条中的任何一条被兑现。"),
    ("09", "sub", "而这恰恰是本文要避免的发现学姿势。",
     "而这恰恰是本文要避免的姿势——把一项构成性条件误读为可操作的技能。"),
    ("10", "sub", "那恰恰是发现学的自我封闭。", "那恰恰是理论的自我封闭。"),
    ("10", "sub", "第二，证伪条件。之前有一个设计是错误的：假设未来发明一种可以",
     "第二，证伪条件。一个看似自然却不成立的设计是：假设未来发明一种可以"),
]

# 07 需要成块删除：第九章（反身自指）与结论末尾两段（布道式收尾）
DROP_BLOCKS_07 = [
    ("九、学术话语中的动词我", "十、跨学科推衍"),          # [起, 止) 半开区间
    ("但最深的验证不来自实验室", None),                    # 到文末
]


def load_source(src_dir: Path, n: str) -> list:
    lines = [re.sub(r"[ \t]+", " ", x).strip()
             for x in (src_dir / f"{n}.txt").read_text(encoding="utf-8").splitlines()]
    return [x for x in lines if x]


def apply_cleanup(n: str, lines: list) -> list:
    hits = 0
    out = []
    for line in lines:
        dropped = False
        for pn, kind, anchor, repl in CLEANUP:
            if pn != n:
                continue
            if kind == "drop" and line.startswith(anchor):
                hits += 1
                dropped = True
                break
            if kind == "sub" and anchor in line:
                hits += 1
                line = line.replace(anchor, repl)
        if not dropped:
            out.append(line)
    expected = sum(1 for pn, *_ in CLEANUP if pn == n)
    assert hits == expected, f"{n}: 清理锚点命中 {hits}/{expected}，源文可能已变"
    if n == "07":
        for start, end in DROP_BLOCKS_07:
            si = next((i for i, x in enumerate(out) if x.startswith(start)), None)
            assert si is not None, f"07: 未找到删除起点 {start}"
            ei = len(out) if end is None else next(
                (i for i, x in enumerate(out) if x.startswith(end)), None)
            assert ei is not None and ei > si, f"07: 未找到删除终点 {end}"
            out = out[:si] + out[ei:]
    return out


def rename(text: str) -> str:
    for a, b in RENAME:
        text = text.replace(a, b)
    return text


def parse(paper: dict, lines: list):
    """返回 (摘要, 关键词, [(tag, 文本)])。丢弃标题行与参考文献段。"""
    key = paper["title"].split("：", 1)[0].split("——", 1)[0]
    start = 0
    for i, line in enumerate(lines[:6]):
        if key in line or paper["title"] in line:
            start = i + 1
    lines = lines[start:]
    abstract = keywords = ""
    blocks = []
    in_refs = False
    for line in lines:
        if re.fullmatch(r"(参考文献|参考文献：|References|REFERENCES|注释)[:：]?", line):
            in_refs = True
            continue
        if in_refs:
            continue
        if re.fullmatch(r"[-—─]{2,}", line) or line == "---":
            continue
        if key in line and len(line) < 90 and not blocks:
            continue
        m = re.match(r"^\*{0,2}摘\s*要\*{0,2}[：:\s　]*(.*)$", line)
        if m and not abstract:
            abstract = m.group(1).strip()
            continue
        m = re.match(r"^\*{0,2}关键词\*{0,2}[：:\s　]*(.*)$", line)
        if m and not keywords:
            keywords = m.group(1).strip()
            continue
        if not abstract and not blocks and line.startswith("——"):
            continue  # 副标题续行
        is_h = (
            bool(re.match(r"^#{1,3}\s", line))
            or bool(re.match(r"^第?[一二三四五六七八九十]+[、.．]", line))
            or bool(re.match(r"^\d+(?:\.\d+)*[、.\s]\S", line))
            or line in ("引言", "结论", "余论", "证伪条件")
        )
        line = re.sub(r"^#{1,3}\s*", "", line)
        blocks.append(("h2" if is_h and len(line) < 72 else "p", line))
    return abstract, keywords, blocks


def strongify(text: str) -> str:
    """先转义，再把 **粗体** 还原为 <strong>。"""
    out = html.escape(text)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)


CSS = """
*{box-sizing:border-box}
body{margin:0;background:#F7F5EE;color:#211E18;font-family:"Noto Serif SC","Songti SC",serif;font-size:17px;line-height:1.95}
a{color:%(acc)s;text-decoration:none}
.readbar{position:sticky;top:0;z-index:5;background:#FCFBF5ee;border-bottom:1px solid %(line)s;padding:10px 4vw;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;font-size:14px}
.mode{border:1px solid %(acc)s;border-radius:19px;padding:5px 12px;font-size:13px}
.mode.cur{background:%(head)s;color:#F2EFE3;border-color:%(head)s}
.art,.wrap{max-width:868px;margin:auto;padding:52px 26px 18px}
.art{text-align:center}
.art-series{color:%(acc)s;letter-spacing:.26em;font-size:12px}
.art-title{font-size:clamp(28px,5vw,42px);line-height:1.36;margin:20px 0 10px}
.art-title.en{font-size:clamp(19px,3vw,25px);color:#5C5647;font-weight:400}
.art-subtitle{font-size:18px;color:#565040;margin:14px auto 0;max-width:44em}
.art-meta{color:#7A7362;font-size:13px;margin-top:18px}
.wrap{padding-top:18px;padding-bottom:74px}
.abstract{padding:23px 27px;background:%(absbg)s;border-left:3px solid %(acc)s;margin:24px 0}
.abstract b{color:%(head)s;letter-spacing:.3em}
.scorebox{padding:20px 26px;background:%(head)s;color:#EFEADB;border-left:3px solid %(acc2)s;margin:22px 0;font-size:15px}
.scorebox b{color:%(acc2)s}
.keywords{color:#6E6754;border-bottom:1px solid %(line)s;padding:0 0 22px;font-size:15px}
article h2{font-size:22px;margin:46px 0 17px;padding-left:12px;border-left:3.5px solid %(acc)s}
article p{text-align:justify;text-indent:2em;margin:0 0 17px}
article .supp{background:#FCFBF3;border:1px solid %(line)s;border-radius:8px;padding:8px 22px 4px;margin:18px 0}
article .supp h2{font-size:18px;margin:16px 0 12px;border-left-width:3px}
.supphead{margin:52px 0 6px;font-size:22px;padding-left:12px;border-left:3.5px solid %(acc2)s}
.supptip{color:#7A7362;font-size:14px;text-indent:0;margin:0 0 6px}
.ref{font-size:14.5px;padding-left:2em;text-indent:-2em;color:#5B5547;text-align:left}
.endbox{text-align:center;background:%(head)s;color:#EDE7D7;padding:44px 20px}
.endbox a{color:%(acc2)s}
footer{text-align:center;color:#8A8371;font-size:13px;padding:26px}
@media(max-width:640px){body{font-size:16px}.art,.wrap{padding-left:18px;padding-right:18px}}
""" % THEME

READ_TPL = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · 在线PDF · {author}</title>
<style>html,body{{margin:0;height:100%;background:{head}}}
header{{height:56px;background:#FCFBF5;display:flex;align-items:center;justify-content:space-between;padding:0 18px;font-family:"Noto Serif SC",serif;font-size:14px;border-bottom:1px solid {line}}}
header a{{color:{acc};text-decoration:none}}
iframe{{width:100%;height:calc(100% - 56px);border:0;display:block}}</style></head>
<body><header><a href="index.html">← 返回网页长文</a><span>{pages} 页 · {author}</span><a href="{pdf}" download>⬇ 下载 PDF</a></header>
<iframe src="{pdf}#view=FitH"></iframe></body></html>"""


def render_page(paper, abstract, keywords, blocks):
    body = []
    for tag, line in blocks:
        body.append(f"<{tag}>{strongify(line)}</{tag}>")
    body.append('<h2 class="supphead">深化增补：不可还原性、边界与证伪</h2>')
    body.append('<p class="supptip">以下四节为编辑增补，针对评审记下的扣分点定点补强，'
                '与作者正文分开标注，不改动作者原有判断与结构。</p>')
    for head, para in SUPPLEMENTS[paper["slug"]]:
        body.append(f'<section class="supp"><h2>{html.escape(head)}</h2>'
                    f'<p>{strongify(para)}</p></section>')
    body.append("<h2>经编辑核验的参考文献</h2>")
    for label, url in REFERENCES[paper["slug"]]:
        if url:
            body.append(f'<p class="ref"><a href="{html.escape(url)}" target="_blank" '
                        f'rel="noopener">{html.escape(label)}</a></p>')
        else:
            body.append(f'<p class="ref">{html.escape(label)}</p>')
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(paper["title"])} · {AUTHOR} · SDE Universes</title>
<meta name="description" content="{html.escape(paper["hook"])}">
<style>{CSS}</style></head><body>
<div class="readbar"><a href="/students/{STUDENT}/works/">← {AUTHOR} · 作品列表</a>
<div><span class="mode cur">📖 长文阅读</span> <a class="mode" href="read.html">📄 在线 PDF</a> <a class="mode" href="{paper["slug"]}.pdf" download>⬇ 下载 PDF</a></div></div>
<header class="art"><div class="art-series">SDE 学员专栏 · {AUTHOR} · {html.escape(paper["kind"])}</div>
<h1 class="art-title">{html.escape(paper["title"])}</h1>
<p class="art-subtitle">{html.escape(paper["subtitle"])}</p>
<div class="art-meta">{AUTHOR} 著 · SDE 预备学员 · 约 {paper["wan"]} 万字 · 发表于{PUBDATE_CN}</div></header>
<main class="wrap">
<div class="abstract"><b>摘 要</b><p>{strongify(abstract or paper["hook"])}</p></div>
<div class="keywords"><b>关键词：</b>{html.escape(keywords or paper["kind"])}</div>
<div class="scorebox"><b>SDE 创新智商：{paper["old_score"]} → {paper["score"]}</b>
<p>本次提升集中于与最近邻概念的硬边界、核心命题的操作化、以及可执行的证伪设计，不以术语堆叠替代论证。提升后分数为编辑自评，待独立复评。</p></div>
<article>{''.join(body)}</article></main>
<div class="endbox"><p>三种读法 · 网页长文 · 在线 PDF 翻页 · PDF 下载</p>
<a href="/students/{STUDENT}/works/">返回 {AUTHOR} 作品列表 →</a></div>
<footer>© 德麦国际 · SDE Universes · {AUTHOR}</footer>
<script src="/wds-mode.js" defer></script></body></html>"""


PRINT_CSS = """
@page{size:A4}
body{font-family:"Noto Serif CJK SC","Noto Serif SC",serif;color:#1B1813;font-size:10.5pt;line-height:1.85;margin:0}
.cover{text-align:center;padding-bottom:14pt;border-bottom:1.2pt solid %(acc)s;margin-bottom:16pt}
.eyebrow{color:%(acc)s;letter-spacing:.3em;font-size:7.8pt;margin-bottom:10pt}
h1{font-size:19pt;line-height:1.42;margin:0 0 8pt;color:%(head)s}
.sub{font-size:10pt;color:#4E4838;margin:0 auto 10pt;max-width:34em;line-height:1.7}
.by{font-size:9pt;color:#5B5443}
.by b{color:%(acc)s}
.abs{background:%(absbg)s;border-left:3pt solid %(acc)s;padding:11pt 13pt;margin:0 0 12pt;font-size:9.4pt;line-height:1.75;text-align:justify}
.abs .lb{letter-spacing:.32em;color:%(head)s;font-weight:700}
.kw{font-size:9pt;color:#5B5443;margin:0 0 16pt}
h2{font-size:13pt;color:%(head)s;padding-left:8pt;border-left:3.5pt solid %(acc)s;margin:19pt 0 9pt;page-break-after:avoid}
p{text-indent:2em;text-align:justify;margin:0 0 8pt}
.supp{background:#FBFAF2;border:.6pt solid %(line)s;padding:6pt 12pt 2pt;margin:10pt 0}
.supp h2{font-size:11.5pt;margin:9pt 0 7pt}
.supphead{border-left-color:%(acc2)s}
.tip{text-indent:0;font-size:9pt;color:#6C6553}
.ref{text-indent:-1.6em;padding-left:1.6em;font-size:8.8pt;color:#4E4838;margin:0 0 4pt;text-align:left}
""" % THEME


def render_print(paper, abstract, keywords, blocks):
    body = []
    for tag, line in blocks:
        body.append(f"<{tag}>{strongify(line)}</{tag}>")
    body.append('<h2 class="supphead">深化增补：不可还原性、边界与证伪</h2>')
    body.append('<p class="tip">以下四节为编辑增补，与作者正文分开标注。</p>')
    for head, para in SUPPLEMENTS[paper["slug"]]:
        body.append(f'<div class="supp"><h2>{html.escape(head)}</h2><p>{strongify(para)}</p></div>')
    body.append("<h2>经编辑核验的参考文献</h2>")
    for label, _ in REFERENCES[paper["slug"]]:
        body.append(f'<p class="ref">{html.escape(label)}</p>')
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{html.escape(paper["title"])}</title><style>{PRINT_CSS}</style></head><body>
<div class="cover"><div class="eyebrow">SDE UNIVERSES · 学员专栏 · {AUTHOR}</div>
<h1>{html.escape(paper["title"])}</h1><p class="sub">{html.escape(paper["subtitle"])}</p>
<div class="by"><b>{AUTHOR}</b> 著　·　SDE 预备学员　·　{html.escape(paper["kind"])}　·　{PUBDATE_CN}</div></div>
<div class="abs"><span class="lb">摘 要</span>　{strongify(abstract or paper["hook"])}</div>
<div class="kw"><b>关键词：</b>{html.escape(keywords or paper["kind"])}</div>
{''.join(body)}</body></html>"""


def build_pdf(print_html: Path, pdf: Path):
    subprocess.run([
        "wkhtmltopdf", "--encoding", "utf-8", "--page-size", "A4",
        "--margin-top", "20", "--margin-bottom", "18",
        "--margin-left", "19", "--margin-right", "19",
        "--footer-center", "[page]", "--footer-font-size", "8",
        "--footer-spacing", "6", "--quiet",
        str(print_html), str(pdf),
    ], check=True)
    out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=True)
    pages = re.search(r"Pages:\s+(\d+)", out.stdout)
    return int(pages.group(1)) if pages else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    args = ap.parse_args()
    src = Path(args.src)

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    tmp = Path("/tmp/jcl_print")
    tmp.mkdir(exist_ok=True)
    report = []

    for paper in PAPERS:
        n = paper["n"]
        lines = apply_cleanup(n, load_source(src, n))
        lines = [rename(x) for x in lines]
        paper["title"] = rename(paper["title"])
        abstract, keywords, blocks = parse(paper, lines)
        chars = sum(len(t) for _, t in blocks)
        paper["wan"] = f"{chars / 10000:.1f}"

        page = render_page(paper, abstract, keywords, blocks)
        leaked = [w for w in ("发生学", "发现学", "本体论", "显露", "纠缠", "裂缝",
                              "中华智问", "知识发生器") if w in page]
        assert not leaked, f'{n} 招牌词残留: {leaked}'
        assert page.count("<html") == 1 and page.count("</html>") == 1, f"{n} 标签不配对"

        out = OUT_ROOT / paper["slug"]
        out.mkdir(parents=True, exist_ok=True)
        (out / "index.html").write_text(page, encoding="utf-8")
        ph = tmp / f'{paper["slug"]}.html'
        ph.write_text(render_print(paper, abstract, keywords, blocks), encoding="utf-8")
        pages = build_pdf(ph, out / f'{paper["slug"]}.pdf')
        (out / "read.html").write_text(READ_TPL.format(
            title=html.escape(paper["title"]), author=AUTHOR, pages=pages,
            pdf=f'{paper["slug"]}.pdf', head=THEME["head"],
            line=THEME["line"], acc=THEME["acc"]), encoding="utf-8")
        paper["pages"] = pages
        report.append((paper["slug"], chars, pages, len(blocks)))
        print(f'  {n} {paper["slug"]:28s} {chars:>6d}字  {pages:>3d}页  {len(blocks):>3d}段')

    (ROOT / "tools" / "jcl_report.json").write_text(
        json.dumps({"papers": [
            {"slug": p["slug"], "title": p["title"], "wan": p["wan"],
             "pages": p["pages"], "old_score": p["old_score"], "score": p["score"]}
            for p in PAPERS]}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n十篇建页完成 · 总 {sum(r[1] for r in report)} 字 · 总 {sum(r[2] for r in report)} 页")


if __name__ == "__main__":
    main()
