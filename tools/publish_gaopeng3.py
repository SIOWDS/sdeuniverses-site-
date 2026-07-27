# -*- coding: utf-8 -*-
"""高鹏四篇（以刑事手段干涉民事纠纷 · D 批打磨版） · 建页 + PDF + 三种读法。

用法： python3 tools/publish_gaopeng.py --src /home/claude/gp7
<head> 从高鹏自己的既有论文页复制，主题天然一致。
roster.json 的 papers/count 由 build_roster.py 派生，本脚本不碰。
"""
import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaopeng3_meta import PAPERS, STUDENTS, PUBDATE_CN
from gaopeng3_supp import NOTES, REFERENCES

ROOT = Path(__file__).resolve().parents[1]
STU = ROOT / "public" / "students"
CN = "零一二三四五六七八九十"

RENAME = [
    # 「发生学」在本批多为「~上／~的」的连读，先长后短
    ("发生学的收口", "生成分析的收口"),
    ("发生学的眼光", "生成分析的眼光"),
    ("发生学的意义", "生成层面的意义"),
    ("发生学分析最", "生成分析最"),
    ("发生学概念建", "生成概念建"),
    ("发生学案例", "生成机制案例"),
    ("发生学追踪", "生成追踪"),
    ("发生学之根", "生成之根"),
    ("发生学前提", "生成前提"),
    ("发生学过程", "生成过程"),
    ("发生学追问", "生成层面的追问"),
    ("发生学叙事", "生成叙事"),
    ("发生学链条", "生成链条"),
    ("发生学环节", "生成环节"),
    ("发生学结构", "生成结构"),
    ("发生学机制", "生成机制"),
    ("发生学节点", "生成节点"),
    ("发生学纪律", "生成分析的纪律"),
    ("发生学陷阱", "生成层面的陷阱"),
    ("发生学性质", "生成层面的性质"),
    ("发生学边界", "生成边界"),
    ("发生学功夫", "生成分析的功夫"),
    ("发生学工作", "生成分析的工作"),
    ("发生学问题", "生成问题"),
    ("发生学层面", "生成层面"),
    ("发生学位置", "生成层面的位置"),
    ("发生学从宏观", "生成分析从宏观"),
    ("发生学可以切", "生成分析可以切"),
    ("发生学就不再", "生成分析就不再"),
    ("发生学中的", "生成分析中的"),
    ("发生学中那个", "生成分析中那个"),
    ("发生学意义上", "生成层面上"),
    ("发生学上的", "生成层面的"),
    ("发生学上", "生成层面上"),
    ("发生学的", "生成层面的"),
    ("发生学", "生成分析"),
    ("发现学才会用", "把结论当起点的做法才会用"),
    ("发现学的“回归永恒本质”", "「回归永恒本质」那一路"),
    ("发现学的收口", "定义先行的收口"),
    ("发现学", "定义先行"),
    # 「本体论」是标准中译，改用同为 ontology 中译的「存在论」
    ("本体论偏向", "存在论偏向"),
    ("本体论", "存在论"),
    # 「回写」是内部工序名，本批指教义反过来定义认知
    ("回写：被缩水", "反向定型：被缩水"),
    ("回写步骤", "反向定型这一步"),
    ("回写进法学家", "反向写进法学家"),
    ("回写清晰得", "反向定型清晰得"),
    ("回写", "反向定型"),
    ("裂缝", "裂隙"),
    ("纠缠", "交织"),
    ("显露", "显现"),
]

# (源篇号, 类型, 锚, 替换)
CLEANUP = []


def cn(n: int) -> str:
    if n <= 10:
        return CN[n]
    if n < 20:
        return "十" + CN[n - 10]
    return CN[n // 10] + "十" + (CN[n % 10] if n % 10 else "")


def numlabel(student: str, num: int) -> str:
    return f"之{num}" if STUDENTS[student]["numstyle"] == "arabic" else f"之{cn(num)}"


def load_source(src: Path, sid: str):
    lines = [re.sub(r"[ \t]+", " ", x).strip()
             for x in (src / f"{sid}.txt").read_text(encoding="utf-8").splitlines()]
    return [x for x in lines if x]


def apply_cleanup(sid: str, lines: list):
    hits, out = 0, []
    for line in lines:
        drop = False
        for pn, kind, anchor, repl in CLEANUP:
            if pn != sid:
                continue
            if kind == "drop" and line.startswith(anchor):
                hits += 1
                drop = True
                break
            if kind == "sub" and anchor in line:
                hits += 1
                line = line.replace(anchor, repl)
        if not drop:
            out.append(line)
    expected = sum(1 for pn, *_ in CLEANUP if pn == sid)
    assert hits == expected, f"{sid}: 清理锚点命中 {hits}/{expected}"
    return out


def rename(t: str) -> str:
    for a, b in RENAME:
        t = t.replace(a, b)
    return t


SKIP_LEAD = {}   # 本批四篇首行均为题目


def parse(paper, lines):
    for lead in SKIP_LEAD.get(paper["src"], ()):
        if lines and lines[0].startswith(lead):
            lines = lines[1:]
    key = paper["title"].split("：", 1)[0].split("——", 1)[0]
    start = 0
    for i, line in enumerate(lines[:8]):
        # 摘要标记一出现就停：题名中的词常在摘要正文里复现（如"本文将这一残存命名为剩余朝向"），
        # 继续往下扫会把 start 推过摘要行，导致摘要被整段吞掉。
        # 摘要／关键词行一出现就停（无论其后是否紧跟正文），题名中的词常在摘要或关键词里复现，
        # 继续往下扫会把 start 推过它们，导致摘要与关键词被整段吞掉。
        if re.match(r"^#{0,3}\s*\*{0,2}(摘\s*要|关键词)\*{0,2}\s*[：:　]?", line):
            break
        if key in line or line.startswith("作者："):
            start = i + 1
    lines = lines[start:]
    abstract = keywords = ""
    blocks, mode = [], "body"
    for line in lines:
        bare = re.sub(r"^#{1,3}\s*", "", line)
        if re.fullmatch(r"[-—─]{2,}|---|（全文完）", bare):
            continue
        if re.fullmatch(r"(参考文献|References|REFERENCES)[:：]?", bare):
            mode = "ref"; blocks.append(("h2", "参考文献")); continue
        if re.fullmatch(r"(注释|注)[:：]?", bare):
            mode = "note"; blocks.append(("h2", "注释")); continue
        if re.fullmatch(r"材料说明[:：]?", bare):
            mode = "note"; blocks.append(("h2", "材料说明")); continue
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
            if key in line and len(line) < 90 and not blocks:
                continue
        is_h = mode == "body" and len(line) < 72 and (
            bool(re.match(r"^#{1,2}\s(?!#)", line))
            or bool(re.match(r"^第?[一二三四五六七八九十]+[、.．]", line))
            or bool(re.match(r"^\d+(?:\.\d+)*[、.\s]\S", line))
            or line in ("引言", "结论", "余论", "证伪条件", "证伪与边界"))
        is_h3 = mode == "body" and len(line) < 72 and not is_h and (
            bool(re.match(r"^#{3}\s", line))
            or bool(re.match(r"^（[一二三四五六七八九十]+）", line)))
        line = re.sub(r"^#{1,3}\s*", "", line)
        blocks.append(("h2" if is_h else ("h3" if is_h3 else ("ref" if mode == "ref" else "p")), line))
    return abstract, keywords, blocks


def strongify(t):
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html.escape(t))


EXTRA_CSS = """
.supp{background:rgba(201,168,76,0.07);border:1px solid rgba(201,168,76,0.30);border-radius:8px;padding:4px 22px 6px;margin:20px 0}
.supp h2{font-size:19px;margin:18px 0 12px}\n.wrap h3{font-size:17px;margin:22px 0 8px;color:#D4B25E;font-weight:700}
.supphead{color:#D4B25E}
.supptip{font-size:14.5px;opacity:.82}
.scorebox{border:1px solid rgba(201,168,76,0.42);border-left:3px solid #C9A84C;padding:18px 24px;margin:22px 0;font-size:15px}
.scorebox b{color:#D4B25E}
.kw{font-size:14.5px;margin:0 0 18px;opacity:.9}\n.ref{font-size:14.5px;padding-left:2em;text-indent:-2em;opacity:.86}
.endbox{text-align:center;border-top:1px solid rgba(201,168,76,0.28);margin-top:48px;padding:38px 20px;opacity:.9}
"""


def skeleton_css(student):
    s, slug = student, STUDENTS[student]["skeleton"]
    src = (STU / s / slug / "index.html").read_text(encoding="utf-8")
    i, j = src.find("<style>"), src.find("</style>")
    assert 0 < i < j, f"{s}/{slug} 缺 style 块"
    return src[i + 7:j]


def render_page(paper, css, abstract, keywords, blocks):
    st = STUDENTS[paper["student"]]
    absbox = (f'<div class="abstract"><span class="lb"><b>摘 要</b></span>'
              f'<p>{strongify(abstract)}</p></div>\n') if abstract else ""
    kwbox = (f'<div class="kw"><b>关键词：</b>{html.escape(keywords)}</div>\n'
             ) if keywords else ""
    body = []
    for tag, line in blocks:
        body.append(f'<p class="ref">{strongify(line)}</p>' if tag == "ref"
                    else f"<{tag}>{strongify(line)}</{tag}>")
    body.append('<h2 class="supphead">本次打磨说明</h2>')
    body.append('<section class="supp"><p class="supptip">本批的打磨未另起附录，'
                '而是就地改在原文出问题的那一句、那一段上——事实错处直接更正，'
                '不可核的材料换成可被真正去测的预测，被放跑的最近邻补成新的一段。'
                '以下逐条说明改动落在哪里、为什么。</p>'
                f'<p>{strongify(NOTES[paper["slug"]])}</p></section>')
    body.append("<h2>本次打磨所核验的文献</h2>")
    for label, url in REFERENCES[paper["slug"]]:
        inner = (f'<a href="{html.escape(url)}" target="_blank" rel="noopener">{html.escape(label)}</a>'
                 if url else html.escape(label))
        body.append(f'<p class="ref">{inner}</p>')
    slug, sl = paper["slug"], paper["student"]
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(paper["title"])} · {st["name"]} · SDE 学员专栏</title>
<meta name="description" content="{html.escape(paper["hook"])}">
<style>{css}{EXTRA_CSS}</style></head>
<body>
<div class="readbar">
  <a class="nav-back" href="/students/{sl}/works/">‹ {st["name"]} · 全部作品</a>
  <div class="rb-modes">
    <span class="rb-btn cur">📖 长文阅读</span>
    <a class="rb-btn" href="read.html">📄 在线 PDF</a>
    <a class="rb-btn" href="{slug}.pdf" download>⬇ 下载 PDF</a>
  </div>
</div>
<header class="art">
  <div class="art-series">学员专栏 · {st["name"]} · {html.escape(paper["kind"])}</div>
  <h1 class="art-title">{html.escape(paper["title"])}</h1>
  <div class="art-subtitle">{html.escape(paper["subtitle"])}</div>
  <div class="art-meta">作者 {st["name"]} · {st["role"]} · 约 {paper["wan"]} 万字 · 发表于{PUBDATE_CN} · 打磨版</div>
</header>
<div class="wrap">
{absbox}{kwbox}<div class="scorebox"><b>SDE 创新智商：{paper["old_score"]} → {paper["score"]}</b>
<p>本批四篇评分排名第 {paper["rank"]}。本批打磨的重心是两件事：逐篇补齐与同日发表的《救济之光》《不知的守夜》《法秩序的沉默前提》三篇之间的互引与分工（把「我比它多出来的是什么」写成可检验的一段，而非一句客套），以及清除一处伪造的田野材料并把它换成明示的思想例证。另更正日本行政指导史的两处年代错误。作者的核心判断与章节结构一律不动。提升后分数为编辑自评，待独立复评。</p></div>
{''.join(body)}
<div class="endbox"><p>三种读法 · 网页长文 · 在线 PDF 翻页 · PDF 下载</p>
<p><a href="/students/{sl}/works/">返回 {st["name"]} 全部作品 →</a></p></div>
</div>
<script src="/wds-mode.js" defer></script>
</body></html>"""


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
.kw{font-size:9pt;color:#57513F;margin:0 0 16pt}
h2{font-size:13pt;color:#2A2411;padding-left:8pt;border-left:3.5pt solid #9A7C22;margin:19pt 0 9pt;page-break-after:avoid}\nh3{font-size:11pt;color:#3A3418;margin:13pt 0 6pt;page-break-after:avoid}
p{text-indent:2em;text-align:justify;margin:0 0 8pt}
.supp{background:#FBF9EF;border:.6pt solid #D8C89A;padding:6pt 12pt 2pt;margin:10pt 0}
.supp h2{font-size:11.5pt;margin:9pt 0 7pt}
.tip{text-indent:0;font-size:9pt;color:#6A6350}
.ref{text-indent:-1.6em;padding-left:1.6em;font-size:8.8pt;color:#4A4636;margin:0 0 4pt;text-align:left}
"""


def render_print(paper, abstract, keywords, blocks):
    st = STUDENTS[paper["student"]]
    body = []
    for tag, line in blocks:
        body.append(f'<p class="ref">{strongify(line)}</p>' if tag == "ref"
                    else f"<{tag}>{strongify(line)}</{tag}>")
    body.append('<h2>本次打磨说明</h2>')
    body.append(f'<div class="supp"><p class="tip">改动已就地落在正文，此处逐条说明落点与理由。</p>'
                f'<p>{strongify(NOTES[paper["slug"]])}</p></div>')
    body.append("<h2>本次打磨所核验的文献</h2>")
    for label, _ in REFERENCES[paper["slug"]]:
        body.append(f'<p class="ref">{html.escape(label)}</p>')
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{html.escape(paper["title"])}</title><style>{PRINT_CSS}</style></head><body>
<div class="cover"><div class="eyebrow">SDE UNIVERSES · 学员专栏 · {st["name"]}</div>
<h1>{html.escape(paper["title"])}</h1><p class="sub">{html.escape(paper["subtitle"])}</p>
<div class="by"><b>{st["name"]}</b> 著　·　{st["role"]}　·　{html.escape(paper["kind"])}　·　{PUBDATE_CN}</div></div>
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
    tmp = Path("/tmp/top5_print"); tmp.mkdir(exist_ok=True)
    css_cache = {}

    for paper in PAPERS:
        sid, sl = paper["src"], paper["student"]
        lines = [rename(x) for x in apply_cleanup(sid, load_source(src, sid))]
        paper["title"] = rename(paper["title"])
        abstract, keywords, blocks = parse(paper, lines)
        chars = sum(len(t) for _, t in blocks)
        paper["wan"] = f"{chars / 10000:.1f}"
        if sl not in css_cache:
            css_cache[sl] = skeleton_css(sl)
        page = render_page(paper, css_cache[sl], abstract, keywords, blocks)
        probe = page
        leaked = [w for w in ("发生学", "发现学", "发生论", "本体论", "显露",
                              "纠缠", "裂缝", "金点子", "回写", "差异序列") if w in probe]
        assert not leaked, f"{sid} 招牌词残留: {leaked}"
        assert page.count("<html") == 1 and page.count("</html>") == 1, f"{sid} 标签不配对"
        assert abstract and 'class="abstract"' in page, f"{sid} 摘要未进页面"
        assert keywords and 'class="kw"' in page, f"{sid} 关键词未进页面"

        out = STU / sl / paper["slug"]
        out.mkdir(parents=True, exist_ok=True)
        (out / "index.html").write_text(page, encoding="utf-8")
        ph = tmp / f'{paper["slug"]}.html'
        ph.write_text(render_print(paper, abstract, keywords, blocks), encoding="utf-8")
        pages = build_pdf(ph, out / f'{paper["slug"]}.pdf')
        (out / "read.html").write_text(READ_TPL.format(
            title=html.escape(paper["title"]), author=STUDENTS[sl]["name"],
            pages=pages, pdf=f'{paper["slug"]}.pdf'), encoding="utf-8")
        paper["pages"] = pages
        refs = sum(1 for t, _ in blocks if t == "ref")
        print(f'  第{paper["rank"]} {sid}→{sl}/{paper["slug"]:24s} '
              f'{chars:>6d}字 {pages:>3d}页 作者文献{refs:>3d}条 {numlabel(sl, paper["num"])}')

    (ROOT / "tools" / "gaopeng3_report.json").write_text(json.dumps(
        {"papers": [{k: p[k] for k in ("src", "rank", "student", "num", "slug", "title",
                                       "kind", "hook", "wan", "pages", "old_score", "score")}
                    for p in PAPERS]}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f'\n本批建页完成 · 总 {sum(p["pages"] for p in PAPERS)} 页')


if __name__ == "__main__":
    main()
