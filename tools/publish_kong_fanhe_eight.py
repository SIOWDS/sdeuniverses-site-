# -*- coding: utf-8 -*-
"""孔凡鹤八篇 · 改姓 + 深化增补 + 三种读法 + 上站。

与季春雷那批的两处不同：
  1. 作者八篇都自带参考文献与注释，必须原样保留（只把编辑新增的对勘文献另列一节）；
  2. 孔凡鹤站上已有 32 篇，本批编号 40→33，需前插到既有 works 索引与主页。
页面 <head>（含 CSS）从他自己的既有论文页复制，主题因此天然一致。

用法： python3 tools/publish_kong_fanhe_eight.py --src /home/claude/kfh
"""
import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kfh_meta import AUTHOR, STUDENT, ROLE, PUBDATE_CN, PAPERS, SKELETON
from kfh_supp import SUPPLEMENTS, REFERENCES

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "public" / "students" / STUDENT

RENAME = [
    ("发现学的自我封闭", "理论的自我封闭"),
    ("发现学", "既成事实论"),
    ("发生学分析", "生成机制分析"),
    ("发生学重构", "生成机制重构"),
    ("发生学重解", "生成机制重解"),
    ("发生学后果", "生成层面的后果"),
    ("发生学意义", "生成层面的意义"),
    ("发生学展示", "生成过程展示"),
    ("发生学内部反对者", "内部反对者"),
    ("发生学概念", "生成机制概念"),
    ("发生学的", "生成机制的"),
    ("灾害发生论", "灾害生成论"),
    ("灾害发生学", "灾害生成论"),
    ("发生论", "生成论"),
    ("发生学", "生成机制"),
    ("本体论级", "根本层面"),
    ("本体论上", "存在论上"),
    ("本体论", "存在论"),
    ("特征纠缠", "特征耦合"),
    ("纠缠", "交织"),
    ("显露", "显现"),
    ("裂缝", "缝隙"),
]

# ("篇号", 类型, 锚, 替换)
CLEANUP = [
    # B01：证伪条件后的抒情表态，软化了刚立好的标准
    ("B01", "drop", "本文作者希望自己有一天被这样证伪", None),
    # B02：把“幸存者反而证明理论”的免疫式反击降格，改为可独立证伪的经验命题
    ("B02", "sub",
     "因此，“幸存者”非但不是对理论的证伪，反而是理论需要解释的核心现象之一：一个生产体征主体的系统，何以同时保有一批“反例”？答案是：反例本身就是系统自我正当化的一个组成部分。",
     "需要说明的是，这一条只作为一个可被单独检验的经验命题提出——非标路径成功者的可见度是否被系统性放大，这是可以测量的。它不承担吸收反例的功能：符合结论所列条件的个案，仍然构成对本文的证伪。"),
]


def load_source(src: Path, n: str):
    lines = [re.sub(r"[ \t]+", " ", x).strip()
             for x in (src / f"{n}.txt").read_text(encoding="utf-8").splitlines()]
    return [x for x in lines if x]


def apply_cleanup(n: str, lines: list):
    hits, out = 0, []
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
    return out


def rename(text: str) -> str:
    for a, b in RENAME:
        text = text.replace(a, b)
    return text


def parse(paper: dict, lines: list):
    """保留作者的参考文献与注释；返回 (摘要, 关键词, [(tag,文本)])。"""
    key = paper["title"].split("：", 1)[0].split("——", 1)[0]
    start = 0
    for i, line in enumerate(lines[:8]):
        if key in line or line.startswith("作者：") or line.startswith(paper["title"][:8]):
            start = i + 1
    lines = lines[start:]
    abstract = keywords = ""
    blocks, mode = [], "body"
    for line in lines:
        if re.fullmatch(r"[-—─]{2,}|---", line):
            continue
        if re.fullmatch(r"(参考文献|References|REFERENCES)[:：]?", line):
            mode = "ref"
            blocks.append(("h2", "参考文献"))
            continue
        if re.fullmatch(r"(注释|注)[:：]?", line):
            mode = "note"
            blocks.append(("h2", "注释"))
            continue
        if re.fullmatch(r"材料说明[:：]?", line):
            mode = "note"
            blocks.append(("h2", "材料说明"))
            continue
        if mode == "body":
            if line.startswith("作者：") and len(line) < 20:
                continue
            m = re.match(r"^\*{0,2}摘\s*要\*{0,2}[：:\s　]*(.*)$", line)
            if m and not abstract:
                if m.group(1).strip():
                    abstract = m.group(1).strip()
                    continue
                abstract = "__NEXT__"
                continue
            if abstract == "__NEXT__":
                abstract = line
                continue
            m = re.match(r"^\*{0,2}关键词\*{0,2}[：:\s　]*(.*)$", line)
            if m and not keywords:
                keywords = m.group(1).strip() or "__NEXT__"
                continue
            if keywords == "__NEXT__":
                keywords = line
                continue
            if key in line and len(line) < 90 and not blocks:
                continue
        is_h = mode == "body" and (
            bool(re.match(r"^#{1,3}\s", line))
            or bool(re.match(r"^第?[一二三四五六七八九十]+[、.．]", line))
            or bool(re.match(r"^\d+(?:\.\d+)*[、.\s]\S", line))
            or line in ("引言", "结论", "余论", "证伪条件")
        ) and len(line) < 72
        line = re.sub(r"^#{1,3}\s*", "", line)
        blocks.append(("h2" if is_h else ("ref" if mode == "ref" else "p"), line))
    return abstract, keywords, blocks


def strongify(t: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html.escape(t))


SKEL_HEAD = None
EXTRA_CSS = """
.supp{background:rgba(201,168,76,0.07);border:1px solid rgba(201,168,76,0.30);border-radius:8px;padding:4px 22px 6px;margin:20px 0}
.supp h2{font-size:19px;margin:18px 0 12px}
.supphead{color:var(--gold2)}
.supptip{font-size:14.5px;color:#B0A484}
.scorebox{border:1px solid rgba(201,168,76,0.42);border-left:3px solid var(--gold);padding:18px 24px;margin:22px 0;font-size:15px;color:#DCD2B2}
.scorebox b{color:var(--gold2)}
.ref{font-size:14.5px;padding-left:2em;text-indent:-2em;color:#B8AE96}
.endbox{text-align:center;border-top:1px solid rgba(201,168,76,0.28);margin-top:48px;padding:38px 20px;color:#B8AE96}
"""


def load_skeleton():
    global SKEL_HEAD
    src = (OUT_ROOT / SKELETON / "index.html").read_text(encoding="utf-8")
    i, j = src.find("<style>"), src.find("</style>")
    assert 0 < i < j, "骨架页缺 style 块"
    SKEL_HEAD = src[i + 7:j]


def render_page(paper, abstract, keywords, blocks):
    body = []
    for tag, line in blocks:
        if tag == "ref":
            body.append(f'<p class="ref">{strongify(line)}</p>')
        else:
            body.append(f"<{tag}>{strongify(line)}</{tag}>")
    body.append('<h2 class="supphead">深化增补：被放跑的最近邻、操作化与证伪</h2>')
    body.append('<p class="supptip">以下四节为编辑增补，针对评审记下的扣分点定点补强，'
                '与作者正文分开标注，不改动作者原有判断与结构。</p>')
    for head, para in SUPPLEMENTS[paper["slug"]]:
        body.append(f'<section class="supp"><h2>{html.escape(head)}</h2>'
                    f'<p>{strongify(para)}</p></section>')
    body.append("<h2>编辑增补所依据的核验文献</h2>")
    for label, url in REFERENCES[paper["slug"]]:
        inner = (f'<a href="{html.escape(url)}" target="_blank" rel="noopener">{html.escape(label)}</a>'
                 if url else html.escape(label))
        body.append(f'<p class="ref">{inner}</p>')
    slug = paper["slug"]
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(paper["title"])} · {AUTHOR} · SDE 学员专栏</title>
<meta name="description" content="{html.escape(paper["hook"])}">
<style>{SKEL_HEAD}{EXTRA_CSS}</style></head>
<body>
<div class="readbar">
  <a class="nav-back" href="/students/{STUDENT}/works/">‹ {AUTHOR} · 全部作品</a>
  <div class="rb-modes">
    <span class="rb-btn cur">📖 长文阅读</span>
    <a class="rb-btn" href="read.html">📄 在线 PDF</a>
    <a class="rb-btn" href="{slug}.pdf" download>⬇ 下载 PDF</a>
  </div>
</div>
<header class="art">
  <div class="art-series">学员专栏 · {AUTHOR} · {html.escape(paper["kind"])}</div>
  <h1 class="art-title">{html.escape(paper["title"])}</h1>
  <div class="art-subtitle">{html.escape(paper["subtitle"])}</div>
  <div class="art-meta">作者 {AUTHOR} · {ROLE} · 约 {paper["wan"]} 万字 · 发表于{PUBDATE_CN} · 深化增补版</div>
</header>
<div class="wrap">
<div class="scorebox"><b>SDE 创新智商：{paper["old_score"]} → {paper["score"]}</b>
<p>本次提升集中于补上被放跑的最近邻理论、核心命题的操作化与可执行的证伪设计。提升后分数为编辑自评，待独立复评。</p></div>
{''.join(body)}
<div class="endbox"><p>三种读法 · 网页长文 · 在线 PDF 翻页 · PDF 下载</p>
<p><a href="/students/{STUDENT}/works/">返回 {AUTHOR} 全部作品 →</a></p></div>
</div>
<script src="/wds-mode.js" defer></script>
</body></html>"""


PRINT_CSS = """
@page{size:A4}
body{font-family:"Noto Serif CJK SC","Noto Serif SC",serif;color:#1A1710;font-size:10.5pt;line-height:1.85;margin:0}
.cover{text-align:center;padding-bottom:13pt;border-bottom:1.2pt solid #9A7C22;margin-bottom:16pt}
.eyebrow{color:#9A7C22;letter-spacing:.3em;font-size:7.8pt;margin-bottom:10pt}
h1{font-size:18.5pt;line-height:1.44;margin:0 0 8pt;color:#1B3A26}
.sub{font-size:10pt;color:#4A4636;margin:0 auto 10pt;max-width:34em;line-height:1.7}
.by{font-size:9pt;color:#57513F}.by b{color:#9A7C22}
.abs{background:#F4F1E4;border-left:3pt solid #9A7C22;padding:11pt 13pt;margin:0 0 12pt;font-size:9.4pt;line-height:1.75;text-align:justify}
.abs .lb{letter-spacing:.32em;color:#1B3A26;font-weight:700}
.kw{font-size:9pt;color:#57513F;margin:0 0 16pt}
h2{font-size:13pt;color:#1B3A26;padding-left:8pt;border-left:3.5pt solid #9A7C22;margin:19pt 0 9pt;page-break-after:avoid}
p{text-indent:2em;text-align:justify;margin:0 0 8pt}
.supp{background:#FAF8EE;border:.6pt solid #D8C89A;padding:6pt 12pt 2pt;margin:10pt 0}
.supp h2{font-size:11.5pt;margin:9pt 0 7pt}
.tip{text-indent:0;font-size:9pt;color:#6A6350}
.ref{text-indent:-1.6em;padding-left:1.6em;font-size:8.8pt;color:#4A4636;margin:0 0 4pt;text-align:left}
"""


def render_print(paper, abstract, keywords, blocks):
    body = []
    for tag, line in blocks:
        if tag == "ref":
            body.append(f'<p class="ref">{strongify(line)}</p>')
        else:
            body.append(f"<{tag}>{strongify(line)}</{tag}>")
    body.append('<h2>深化增补：被放跑的最近邻、操作化与证伪</h2>')
    body.append('<p class="tip">以下四节为编辑增补，与作者正文分开标注。</p>')
    for head, para in SUPPLEMENTS[paper["slug"]]:
        body.append(f'<div class="supp"><h2>{html.escape(head)}</h2><p>{strongify(para)}</p></div>')
    body.append("<h2>编辑增补所依据的核验文献</h2>")
    for label, _ in REFERENCES[paper["slug"]]:
        body.append(f'<p class="ref">{html.escape(label)}</p>')
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{html.escape(paper["title"])}</title><style>{PRINT_CSS}</style></head><body>
<div class="cover"><div class="eyebrow">SDE UNIVERSES · 学员专栏 · {AUTHOR}</div>
<h1>{html.escape(paper["title"])}</h1><p class="sub">{html.escape(paper["subtitle"])}</p>
<div class="by"><b>{AUTHOR}</b> 著　·　{ROLE}　·　{html.escape(paper["kind"])}　·　{PUBDATE_CN}</div></div>
<div class="abs"><span class="lb">摘 要</span>　{strongify(abstract or paper["hook"])}</div>
<div class="kw"><b>关键词：</b>{html.escape(keywords or paper["kind"])}</div>
{''.join(body)}</body></html>"""


READ_TPL = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · 在线PDF · {author}</title>
<style>html,body{{margin:0;height:100%;background:#0E0B08}}
header{{height:56px;background:#171310;display:flex;align-items:center;justify-content:space-between;padding:0 18px;font-family:"Songti SC","Noto Serif SC",serif;font-size:14px;border-bottom:1px solid rgba(201,168,76,0.28);color:#B8AE96}}
header a{{color:#C9A84C;text-decoration:none}}
iframe{{width:100%;height:calc(100% - 56px);border:0;display:block}}</style></head>
<body><header><a href="index.html">‹ 返回网页长文</a><span>{pages} 页 · {author}</span><a href="{pdf}" download>⬇ 下载 PDF</a></header>
<iframe src="{pdf}#view=FitH"></iframe></body></html>"""


def build_pdf(ph: Path, pdf: Path) -> int:
    subprocess.run(["wkhtmltopdf", "--encoding", "utf-8", "--page-size", "A4",
                    "--margin-top", "20", "--margin-bottom", "18",
                    "--margin-left", "19", "--margin-right", "19", "--quiet",
                    str(ph), str(pdf)], check=True)
    out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=True)
    m = re.search(r"Pages:\s+(\d+)", out.stdout)
    return int(m.group(1)) if m else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    args = ap.parse_args()
    src = Path(args.src)
    load_skeleton()
    tmp = Path("/tmp/kfh_print")
    tmp.mkdir(exist_ok=True)

    for paper in PAPERS:
        n = paper["n"]
        lines = [rename(x) for x in apply_cleanup(n, load_source(src, n))]
        paper["title"] = rename(paper["title"])
        abstract, keywords, blocks = parse(paper, lines)
        chars = sum(len(t) for _, t in blocks)
        paper["wan"] = f"{chars / 10000:.1f}"

        page = render_page(paper, abstract, keywords, blocks)
        leaked = [w for w in ("发生学", "发现学", "发生论", "本体论", "显露", "纠缠", "裂缝") if w in page]
        assert not leaked, f"{n} 招牌词残留: {leaked}"
        assert page.count("<html") == 1 and page.count("</html>") == 1, f"{n} 标签不配对"

        out = OUT_ROOT / paper["slug"]
        out.mkdir(parents=True, exist_ok=True)
        (out / "index.html").write_text(page, encoding="utf-8")
        ph = tmp / f'{paper["slug"]}.html'
        ph.write_text(render_print(paper, abstract, keywords, blocks), encoding="utf-8")
        pages = build_pdf(ph, out / f'{paper["slug"]}.pdf')
        (out / "read.html").write_text(READ_TPL.format(
            title=html.escape(paper["title"]), author=AUTHOR, pages=pages,
            pdf=f'{paper["slug"]}.pdf'), encoding="utf-8")
        paper["pages"] = pages
        refs = sum(1 for t, _ in blocks if t == "ref")
        print(f'  {n} {paper["slug"]:24s} {chars:>6d}字 {pages:>3d}页 {len(blocks):>4d}段 作者文献{refs:>3d}条')

    (ROOT / "tools" / "kfh_report.json").write_text(json.dumps(
        {"papers": [{k: p[k] for k in ("n", "num", "slug", "title", "kind", "hook",
                                       "wan", "pages", "old_score", "score")} for p in PAPERS]},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f'\n八篇建页完成 · 总 {sum(int(float(p["wan"]) * 10000) for p in PAPERS)} 字 · '
          f'总 {sum(p["pages"] for p in PAPERS)} 页')


if __name__ == "__main__":
    main()
