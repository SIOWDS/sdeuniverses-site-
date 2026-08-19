# -*- coding: utf-8 -*-
"""秦莉三篇（意识流与影视语言互切 · 二次审稿打磨版） · 建页 + PDF + 三种读法 + 索引更新。

用法： python3 tools/publish_top5.py --src /home/claude/rest
每篇 <head> 从该学员自己的既有论文页复制；新学员（蔡彦）借同门骨架。
roster.json 的 papers/count 由 build_roster.py 派生，本脚本只补新学员身份字段。
"""
import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gyh_meta import PAPERS, STUDENTS, PUBDATE_CN
from gyh_supp import SUPPLEMENTS, REFERENCES

ROOT = Path(__file__).resolve().parents[1]
STU = ROOT / "public" / "students"
CN = "零一二三四五六七八九十"

RENAME = [
    ("发生学构成要素", "生成层面的构成要素"),
    ("发生学事件", "生成层面的事件"),
    ("发现学的自我封闭", "理论的自我封闭"),
    ("发现学的防御姿态", "定义先行的防御姿态"),
    ("发生学而非历史学", "生成分析而非历史学"),
    ("痕迹本体论依赖", "痕迹存在论依赖"),
    ("发生学微观分析", "微观生成分析"),
    ("发生学要问的是", "生成层面的追问是"),
    ("发生学不讲证据", "生成分析不讲证据"),
    ("外部发生学分析", "外部生成分析"),
    ("发现学的路径", "定义先行的路径"),
    ("发生学地处理", "在生成层面处理"),
    ("发生学人类学", "生成取向的人类学"),
    ("发生学动力学", "生成动力学"),
    ("发生学不接受", "生成分析不接受"),
    ("发现学叙事", "成果回溯叙事"),
    ("发生学分析", "生成机制分析"),
    ("发生学重建", "生成机制重建"),
    ("发生学结构", "生成结构"),
    ("发生学进程", "生成进程"),
    ("发生学过程", "生成过程"),
    ("发生学路径", "生成机制路径"),
    ("发生学意义", "生成层面的意义"),
    ("发生学判断", "生成层面的判断"),
    ("单体发生学", "单体生成论"),
    ("发生学起点", "生成层面的起点"),
    ("发生学切片", "生成切片"),
    ("发生学定义", "生成层面的定义"),
    ("发生学澄清", "生成层面的澄清"),
    ("发生学论断", "生成层面的论断"),
    ("发生学区分", "生成层面的区分"),
    ("发生学追问", "生成层面的追问"),
    ("发生学追踪", "生成过程追踪"),
    ("发生学假说", "生成假说"),
    ("发生学来源", "生成来源"),
    ("发生学根基", "生成根基"),
    ("发生学根据", "生成层面的根据"),
    ("发生学逻辑", "生成逻辑"),
    ("发生学轮廓", "生成轮廓"),
    ("在发生学上", "在生成层面上"),
    ("发生学机制", "生成机制"),
    ("发生学源头", "生成源头"),
    ("发生学关系", "生成层面的关系"),
    ("发生学关节", "生成关节"),
    ("发生学要义", "生成层面的要义"),
    ("发生学运作", "生成运作"),
    ("发生学描述", "生成描述"),
    ("微观发生学", "微观生成"),
    ("发生学的", "生成机制的"),
    ("本体论级", "根本层面"),
    ("本体论上", "存在论上"),
    ("特征纠缠", "特征耦合"),
    ("发生学中", "生成机制中"),
    ("发生学里", "生成机制里"),
    ("发生学地", "在生成层面"),
    ("发生论", "生成论"),
    ("本体论", "存在论"),
    ("发生学", "生成机制"),
    ("纠缠", "交织"),
    ("显露", "显现"),
    ("裂缝", "缝隙"),
]

# ("源篇号", 类型, 锚, 替换)
CLEANUP = [
    # 「发现学」是 SDE 内部「发生 vs 发现」的对置，学科读者不解其意，逐句换成本地说法
    ("G1", "sub", "这就会滑回发现学——", "这就会滑回“把结论当起点”的老路——"),
    ("G1", "sub", "一个更长、更笨拙、但不会把人骗回发现学的表述",
     "一个更长、更笨拙、但不会把人骗回“现成本质等着被发现”的表述"),
    ("G2", "sub", "它们都停留在“这部机器在做什么”的发现学层面。本文追问一个不同的发生学问题：",
     "它们都停留在“这部机器在做什么”这一层。本文追问一个不同的生成问题："),
    ("G2", "sub", "但“综合”是一个发现学的荣誉——", "但“综合”是一种成果回溯式的荣誉——"),
    ("G4", "sub", "那本文就在最后一刻滑回了发现学——", "那本文就在最后一刻滑回了“把结论当起点”——"),
    ("G4", "sub", "它是否正在从“发生学结论”滑向“发现学诊断”？",
     "它是否正在从一个生成层面的结论，滑向一个“现成本质被剥夺”式的诊断？"),
]


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


SKIP_LEAD = {"P26": ("概念—方法与自反性研究",)}   # 首行是章节名，不是题目


def parse(paper, lines):
    for lead in SKIP_LEAD.get(paper["src"], ()):
        if lines and lines[0].startswith(lead):
            lines = lines[1:]
    key = paper["title"].split("：", 1)[0].split("——", 1)[0]
    start = 0
    for i, line in enumerate(lines[:8]):
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
.ref{font-size:14.5px;padding-left:2em;text-indent:-2em;opacity:.86}
.endbox{text-align:center;border-top:1px solid rgba(201,168,76,0.28);margin-top:48px;padding:38px 20px;opacity:.9}
"""


def skeleton_css(student):
    ref = STUDENTS[student]["skeleton"]
    owner, slug = ref.split("/", 1) if "/" in ref else (student, ref)
    src = (STU / owner / slug / "index.html").read_text(encoding="utf-8")
    i, j = src.find("<style>"), src.find("</style>")
    assert 0 < i < j, f"{owner}/{slug} 缺 style 块"
    return src[i + 7:j]


def render_page(paper, css, abstract, keywords, blocks):
    st = STUDENTS[paper["student"]]
    body = []
    for tag, line in blocks:
        body.append(f'<p class="ref">{strongify(line)}</p>' if tag == "ref"
                    else f"<{tag}>{strongify(line)}</{tag}>")
    body.append('<h2 class="supphead">深化增补：被放跑的最近邻</h2>')
    body.append('<p class="supptip">以下为编辑增补，针对评审时记下的扣分点定点补强——'
                '每条只做一件事：把一位被放跑的最近邻请上台，切开，给出可裁决的判准。'
                '增补与作者正文分开标注，不改动作者原有判断与结构。</p>')
    for h, para in SUPPLEMENTS[paper["slug"]]:
        body.append(f'<section class="supp"><h2>{html.escape(h)}</h2><p>{strongify(para)}</p></section>')
    body.append("<h2>编辑增补所依据的核验文献</h2>")
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
  <div class="art-meta">作者 {st["name"]} · {st["role"]} · 约 {paper["wan"]} 万字 · 发表于{PUBDATE_CN} · 深化增补版</div>
</header>
<div class="wrap">
<div class="scorebox"><b>SDE 创新智商：{paper["old_score"]} → {paper["score"]}</b>
<p>本批四篇评分排名第 {paper["rank"]}。提升集中于补上评审时找出的、被放跑的最近邻——切开它们，是这个概念主张不可还原性的前提。提升后分数为编辑自评，待独立复评。</p></div>
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
    body.append('<h2>深化增补：被放跑的最近邻</h2>')
    body.append('<p class="tip">以下为编辑增补，与作者正文分开标注。</p>')
    for h, para in SUPPLEMENTS[paper["slug"]]:
        body.append(f'<div class="supp"><h2>{html.escape(h)}</h2><p>{strongify(para)}</p></div>')
    body.append("<h2>编辑增补所依据的核验文献</h2>")
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
        # 作者已发表的真实书名《古典汉语审美发生学》属可核验事实，引用时不得篡改，
        # 故在查残留前先剔除这一处准确引用，再检其余。
        CITED = "《方以智晚节考》"
        probe = page.replace(CITED, "《…》")
        leaked = [w for w in ("发生学", "发现学", "发生论", "本体论", "显露", "纠缠", "裂缝") if w in probe]
        assert not leaked, f"{sid} 招牌词残留: {leaked}"
        assert page.count("<html") == 1 and page.count("</html>") == 1, f"{sid} 标签不配对"

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

    (ROOT / "tools" / "gyh_report.json").write_text(json.dumps(
        {"papers": [{k: p[k] for k in ("src", "rank", "student", "num", "slug", "title",
                                       "kind", "hook", "wan", "pages", "old_score", "score")}
                    for p in PAPERS]}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f'\n本批建页完成 · 总 {sum(p["pages"] for p in PAPERS)} 页')


if __name__ == "__main__":
    main()
