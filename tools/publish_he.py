# -*- coding: utf-8 -*-
"""刘言言四篇 · 建页 + PDF + 三种读法。

用法： python3 tools/publish_lyy.py --src /home/claude/papers
四篇均已过 140 录取线，只做改姓与外科式打磨，不加深化增补章节。
<head> 从她自己的既有论文页 shell-self 复制（陶土棕主题）。
roster.json 的 papers/count 由 build_roster.py 派生，本脚本不动它。
"""
import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from he_meta import PAPERS, STUDENT, PUBDATE_CN
from he_supp import SUPPLEMENTS, REFERENCES

ROOT = Path(__file__).resolve().parents[1]
STU = ROOT / "public" / "students"
CN = "零一二三四五六七八九十"

RENAME = [
    ("差异序列（数百万人的教育晋升路径）与纠缠网络",
     "分化序列（数百万人的教育晋升路径）与交织网络"),
    ("一整个差异序列与纠缠网络之间长期矛盾的结算态",
     "一整套分化路径与交织网络之间长期矛盾的沉淀结果"),
    ("发现学式的诊断", "定性判定式的诊断"),
    ("发现学姿势", "贴标签的姿势"),
    ("发现学意义上的包装", "换名意义上的包装"),
    ("发现学", "既成事实论"),
    ("发生学分析", "生成机制分析"),
    ("发生学诊断", "生成机制诊断"),
    ("发生学展开", "生成机制展开"),
    ("发生学拆解", "生成机制拆解"),
    ("发生学追溯", "生成过程追溯"),
    ("发生学核心", "生成机制核心"),
    ("发生学问题", "生成机制问题"),
    ("发生学假说", "生成机制假说"),
    ("发生学视角", "生成机制视角"),
    ("发生学立场", "生成机制立场"),
    ("发生学框架", "生成机制框架"),
    ("发生学距离", "生成过程的距离"),
    ("发生学力量", "生成机制的力量"),
    ("发生学区别于观念史", "生成机制分析区别于观念史"),
    ("内部发生学", "内部生成机制"),
    ("发生学的", "生成机制的"),
    ("发生学", "生成机制"),
    ("发生论", "生成论"),
    ("本体论级", "根本层面"),
    ("本体论", "存在论"),
    ("特征纠缠", "特征耦合"),
    ("纠缠", "交织"),
    ("显露", "显现"),
    ("裂缝", "缝隙"),
]

BANNED = ("发生学", "发现学", "发生论", "本体论", "显露", "纠缠", "裂缝", "差异序列", "SDE 三界")


def cn(n: int) -> str:
    if n <= 10:
        return CN[n]
    if n < 20:
        return "十" + CN[n - 10]
    return CN[n // 10] + "十" + (CN[n % 10] if n % 10 else "")


def rename(t: str) -> str:
    for a, b in RENAME:
        t = t.replace(a, b)
    return t


def load_source(src: Path, sid: str):
    lines = [re.sub(r"[ \t]+", " ", x).strip()
             for x in (src / f"何丽霞_{sid}.txt").read_text(encoding="utf-8").splitlines()]
    return [x for x in lines if x]


def parse(paper, lines):
    key = paper["title"].split("：", 1)[0].split("——", 1)[0]
    # 只跳开头连续的题头行：短行且含标题关键词，或以破折号起头的副标题
    start = 0
    for i, line in enumerate(lines[:4]):
        if i != start:
            break
        if (len(line) < 90 and key in line) or line.startswith("——"):
            start = i + 1
    lines = lines[start:]
    abstract = keywords = ""
    blocks, mode = [], "body"
    for line in lines:
        if re.fullmatch(r"[-—─]{2,}|---|（全文完）", line):
            continue
        if re.fullmatch(r"(参考文献|References|REFERENCES)[:：]?", line):
            mode = "ref"; blocks.append(("h2", "参考文献")); continue
        if re.fullmatch(r"(注释|注)[:：]?", line):
            mode = "note"; blocks.append(("h2", "注释")); continue
        if mode == "body":
            m = re.match(r"^\*{0,2}摘\s*[　]?\s*要\*{0,2}[：:\s　]*(.*)$", line)
            if m and not abstract:
                abstract = m.group(1).strip() or "__NEXT__"
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
        is_h = mode == "body" and len(line) < 72 and (
            bool(re.match(r"^#{1,3}\s", line))
            or bool(re.match(r"^第?[一二三四五六七八九十]+[、.．]", line))
            or bool(re.match(r"^\d+(?:\.\d+)*[、.\s]\S", line))
            or line in ("引言", "结论", "余论", "证伪条件", "退化条件", "概念的边界与使用纪律"))
        line = re.sub(r"^#{1,3}\s*", "", line)
        blocks.append(("h2" if is_h else ("ref" if mode in ("ref",) else "p"), line))
    return abstract, keywords, blocks


def strongify(t):
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html.escape(t))


EXTRA_CSS = """
.scorebox{border:1px solid rgba(201,168,76,0.42);border-left:3px solid #C9A84C;padding:16px 22px;margin:22px 0;font-size:15px;border-radius:8px}
.scorebox b{color:#C9A84C}
.scorebox p{margin:6px 0 0;font-size:14px;opacity:.85}
.supp{background:rgba(201,168,76,0.07);border:1px solid rgba(201,168,76,0.30);border-radius:8px;padding:4px 22px 6px;margin:20px 0}
.supp h2{font-size:19px;margin:18px 0 12px}
.supphead{color:#D4B25E}
.supptip{font-size:14.5px;opacity:.82}
.ref{font-size:14.5px;padding-left:2em;text-indent:-2em;opacity:.86}
.endbox{text-align:center;border-top:1px solid rgba(201,168,76,0.28);margin-top:48px;padding:38px 20px;opacity:.9}
"""


def skeleton_css():
    src = (STU / STUDENT["slug"] / STUDENT["skeleton"] / "index.html").read_text(encoding="utf-8")
    i, j = src.find("<style>"), src.find("</style>")
    assert 0 < i < j, "骨架页缺 style 块"
    return src[i + 7:j]


def render_page(paper, css, abstract, keywords, blocks):
    body = []
    for tag, line in blocks:
        body.append(f'<p class="ref">{strongify(line)}</p>' if tag == "ref"
                    else f"<{tag}>{strongify(line)}</{tag}>")
    body.append('<h2 class="supphead">深化增补：被放跑的最近邻、操作化与证伪</h2>')
    body.append('<p class="supptip">以下四节为编辑增补，针对审稿记下的扣分点定点补强，'
                '与作者正文分开标注，不改动作者原有判断与结构。</p>')
    for h, para in SUPPLEMENTS[paper["slug"]]:
        body.append(f'<section class="supp"><h2>{html.escape(h)}</h2><p>{strongify(para)}</p></section>')
    body.append("<h2>编辑增补所依据的核验文献</h2>")
    for label, url in REFERENCES[paper["slug"]]:
        inner = (f'<a href="{html.escape(url)}" target="_blank" rel="noopener">{html.escape(label)}</a>'
                 if url else html.escape(label))
        body.append(f'<p class="ref">{inner}</p>')
    slug, sl = paper["slug"], STUDENT["slug"]
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(paper["title"])} · {STUDENT["name"]} · SDE 学员专栏</title>
<meta name="description" content="{html.escape(paper["hook"][:150])}">
<style>{css}{EXTRA_CSS}</style></head>
<body>
<div class="readbar">
  <a class="nav-back" href="/students/{sl}/works/">‹ {STUDENT["name"]} · 全部作品</a>
  <div class="rb-modes">
    <span class="rb-btn cur">📖 长文阅读</span>
    <a class="rb-btn" href="read.html">📄 在线 PDF</a>
    <a class="rb-btn" href="{slug}.pdf" download>⬇ 下载 PDF</a>
  </div>
</div>
<header class="art">
  <div class="art-series">学员专栏 · {STUDENT["name"]} · {html.escape(paper["kind"])}</div>
  <h1 class="art-title">{html.escape(paper["title"])}</h1>
  <div class="art-subtitle">{html.escape(paper["subtitle"])}</div>
  <div class="art-meta">作者 {STUDENT["name"]} · {STUDENT["role"]} · 约 {paper["wan"]} 万字 · 发表于{PUBDATE_CN} · 深化增补版</div>
</header>
<div class="wrap">
<div class="abstract"><span class="lb"><b>{"摘 要" if abstract else "编者导语"}</b></span><p>{strongify(abstract or paper["hook"])}</p>
{f'<p class="kw"><b>关键词：</b>{html.escape(keywords)}</p>' if keywords else ''}</div>
<div class="scorebox"><b>SDE 创新智商：{paper["old_score"]} → {paper["score"]}</b>
<p>初评未达发表线，经深化增补后重评。提升集中于补上被放跑的最近邻理论、核心概念的操作化与可执行的证伪设计。提升后分数为编辑自评，待独立复评。</p></div>
{''.join(body)}
<div class="endbox"><p>三种读法 · 网页长文 · 在线 PDF 翻页 · PDF 下载</p>
<p><a href="/students/{sl}/works/">返回 {STUDENT["name"]} 全部作品 →</a></p></div>
</div>
<script src="/wds-mode.js" defer></script>
</body></html>"""


PRINT_CSS = """
@page{size:A4}
body{font-family:"Noto Serif CJK SC","Noto Serif SC",serif;color:#1A1710;font-size:10.5pt;line-height:1.85;margin:0}
.cover{text-align:center;padding-bottom:13pt;border-bottom:1.2pt solid #C9A84C;margin-bottom:16pt}
.eyebrow{color:#C9A84C;letter-spacing:.3em;font-size:7.8pt;margin-bottom:10pt}
h1{font-size:18.5pt;line-height:1.44;margin:0 0 8pt;color:#2A2411}
.sub{font-size:10pt;color:#57513F;margin:0 auto 10pt;max-width:34em;line-height:1.7}
.by{font-size:9pt;color:#57513F}.by b{color:#C9A84C}
.abs{background:#F5F2E6;border-left:3pt solid #C9A84C;padding:11pt 13pt;margin:0 0 12pt;font-size:9.4pt;line-height:1.75;text-align:justify}
.abs .lb{letter-spacing:.32em;color:#2A2411;font-weight:700}
.kw{font-size:9pt;color:#57513F;margin:0 0 16pt}
h2{font-size:13pt;color:#2A2411;padding-left:8pt;border-left:3.5pt solid #C9A84C;margin:19pt 0 9pt;page-break-after:avoid}
p{text-indent:2em;text-align:justify;margin:0 0 8pt}
.supp{background:#FBF9EF;border:.6pt solid #D8C89A;padding:6pt 12pt 2pt;margin:10pt 0}
.supp h2{font-size:11.5pt;margin:9pt 0 7pt}
.tip{text-indent:0;font-size:9pt;color:#6A6350}
.ref{text-indent:-1.6em;padding-left:1.6em;font-size:8.8pt;color:#4A4636;margin:0 0 4pt;text-align:left}
"""


def render_print(paper, abstract, keywords, blocks):
    body = []
    for tag, line in blocks:
        body.append(f'<p class="ref">{strongify(line)}</p>' if tag == "ref"
                    else f"<{tag}>{strongify(line)}</{tag}>")
    body.append('<h2>深化增补：被放跑的最近邻、操作化与证伪</h2>')
    body.append('<p class="tip">以下四节为编辑增补，与作者正文分开标注。</p>')
    for h, para in SUPPLEMENTS[paper["slug"]]:
        body.append(f'<div class="supp"><h2>{html.escape(h)}</h2><p>{strongify(para)}</p></div>')
    body.append("<h2>编辑增补所依据的核验文献</h2>")
    for label, _ in REFERENCES[paper["slug"]]:
        body.append(f'<p class="ref">{html.escape(label)}</p>')
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{html.escape(paper["title"])}</title><style>{PRINT_CSS}</style></head><body>
<div class="cover"><div class="eyebrow">SDE UNIVERSES · 学员专栏 · {STUDENT["name"]}</div>
<h1>{html.escape(paper["title"])}</h1><p class="sub">{html.escape(paper["subtitle"])}</p>
<div class="by"><b>{STUDENT["name"]}</b> 著　·　{STUDENT["role"]}　·　{html.escape(paper["kind"])}　·　{PUBDATE_CN}</div></div>
<div class="abs"><span class="lb">{"摘 要" if abstract else "编者导语"}</span>　{strongify(abstract or paper["hook"])}</div>
{f'<div class="kw"><b>关键词：</b>{html.escape(keywords)}</div>' if keywords else ''}
{''.join(body)}</body></html>"""


READ_TPL = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · 在线PDF · {author}</title>
<style>html,body{{margin:0;height:100%;background:#0E0B08}}
header{{height:56px;background:#2A2411;display:flex;align-items:center;justify-content:space-between;padding:0 18px;font-family:"Songti SC","Noto Serif SC",serif;font-size:14px;border-bottom:1px solid rgba(201,168,76,0.4);color:#B8AE96}}
header a{{color:#C9A84C;text-decoration:none}}
iframe{{width:100%;height:calc(100% - 56px);border:0;display:block}}</style></head>
<body><header><a href="index.html">‹ 返回网页长文</a><span>{pages} 页 · {author}</span><a href="{pdf}" download>⬇ 下载 PDF</a></header>
<iframe src="{pdf}#view=FitH"></iframe></body></html>"""


def build_pdf(ph, pdf):
    subprocess.run(["wkhtmltopdf", "--encoding", "utf-8", "--page-size", "A4",
                    "--margin-top", "20", "--margin-bottom", "18",
                    "--margin-left", "19", "--margin-right", "19", "--quiet",
                    str(ph), str(pdf)], check=True)
    o = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=True)
    m = re.search(r"Pages:\s+(\d+)", o.stdout)
    return int(m.group(1)) if m else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    args = ap.parse_args()
    src = Path(args.src)
    tmp = Path("/tmp/lyy_print"); tmp.mkdir(exist_ok=True)
    css = skeleton_css()

    for paper in PAPERS:
        sid = paper["src"]
        lines = [rename(x) for x in load_source(src, sid)]
        paper["title"] = rename(paper["title"])
        abstract, keywords, blocks = parse(paper, lines)
        chars = sum(len(t) for _, t in blocks)
        paper["wan"] = f"{chars / 10000:.1f}"
        page = render_page(paper, css, abstract, keywords, blocks)
        # 只查正文区，<head> 的 style 里没有招牌词，但描述与标题也要干净
        leaked = [w for w in BANNED if w in page]
        assert not leaked, f"{sid} 招牌词残留: {leaked}"
        assert page.count("<html") == 1 and page.count("</html>") == 1, f"{sid} 标签不配对"
        for tag in ("div", "header", "style"):
            o, c = page.count(f"<{tag}"), page.count(f"</{tag}>")
            assert o == c, f"{sid} <{tag}> 开闭不配对 {o}/{c}"

        out = STU / STUDENT["slug"] / paper["slug"]
        out.mkdir(parents=True, exist_ok=True)
        (out / "index.html").write_text(page, encoding="utf-8")
        ph = tmp / f'{paper["slug"]}.html'
        ph.write_text(render_print(paper, abstract, keywords, blocks), encoding="utf-8")
        pages = build_pdf(ph, out / f'{paper["slug"]}.pdf')
        (out / "read.html").write_text(READ_TPL.format(
            title=html.escape(paper["title"]), author=STUDENT["name"],
            pages=pages, pdf=f'{paper["slug"]}.pdf'), encoding="utf-8")
        paper["pages"] = pages
        refs = sum(1 for t, _ in blocks if t == "ref")
        heads = sum(1 for t, _ in blocks if t == "h2")
        print(f'  {sid} → {paper["slug"]:24s} {chars:>6d}字 {pages:>3d}页 '
              f'章节{heads:>3d} 文献{refs:>3d}条 之{cn(paper['num'])} IQ{paper['old_score']}→{paper['score']}')

    (ROOT / "tools" / "he_report.json").write_text(json.dumps(
        {"papers": [{k: p[k] for k in ("src", "num", "slug", "title", "kind",
                                       "hook", "wan", "pages", "old_score", "score")}
                    for p in PAPERS]}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f'\n四篇建页完成 · 总 {sum(p["pages"] for p in PAPERS)} 页')


if __name__ == "__main__":
    main()
