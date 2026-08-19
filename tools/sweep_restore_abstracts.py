# -*- coding: utf-8 -*-
"""补回今天各批被吞掉的摘要（网页 + PDF）。

背景：共用解析器跳标题时扫前 8 行取最后一个含关键词的行，而不少摘要会提到
论文自己的概念名，于是摘要本身命中、剪切点落到它后面。网页因此没有摘要块，
render_print 又以 `abstract or paper["hook"]` 静默回退，把编辑写的推介语印成了
作者摘要——这是署名错置，必须修。

做法刻意保守：不整页重渲（避免旧渲染器带来回归），只做两件事——
  · 网页：在 scorebox 之前插入摘要块，复用该学员骨架已有的 .abstract / .abs 样式，
          都没有就随块注入一小段兜底样式
  · PDF ：用修正后的摘要重出（这一份必须重出，因为错的内容已经印在里面）

用法：
    python3 tools/sweep_restore_abstracts.py --dry     # 只报告，不落盘
    python3 tools/sweep_restore_abstracts.py           # 实际修复
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
STU = ROOT / "public" / "students"

# 批次 → (发布模块, 元数据模块, 源目录)
BATCHES = [
    ("kfh_report.json",    "publish_kong_fanhe_eight", "kfh_meta",    "/home/claude/kfh"),
    ("top5_report.json",   "publish_top5",             "top5_meta",   "/home/claude/rest"),
    ("batch2_report.json", "publish_batch2",           "batch2_meta", "/home/claude/rest"),
    ("batch3_report.json", "publish_batch3",           "batch3_meta", "/home/claude/rest"),
]

FALLBACK_CSS = (
    "<style>.abs-restored{background:rgba(201,168,76,0.07);border-left:3px solid currentColor;"
    "opacity:.96;padding:20px 24px;margin:20px 0}"
    ".abs-restored .lb{display:block;font-size:11.5px;letter-spacing:.42em;opacity:.85;margin-bottom:10px}"
    ".abs-restored p{margin:0;text-indent:0;line-height:1.95;text-align:justify}"
    ".abs-restored .kw{margin-top:12px;font-size:13.5px;opacity:.8;text-indent:0}</style>"
)


def parse_fixed(P, paper, lines):
    """修正版：遇「摘要/关键词」即停止跳标题；摘要可跨段收集。"""
    key = paper["title"].split("：", 1)[0].split("——", 1)[0]
    start = 0
    for i, line in enumerate(lines[:6]):
        if re.match(r'^\*{0,2}摘\s*[　]?\s*要', line) or line.startswith("关键词"):
            break
        if (key in line or line.startswith("作者：")) and len(line) < 90:
            start = i + 1
    lines = lines[start:]

    abstract = keywords = ""
    collecting = False
    blocks, mode = [], "body"
    for line in lines:
        if re.fullmatch(r"[-—─]{2,}|---|（全文完）", line):
            if collecting:
                collecting = False
            continue
        if re.fullmatch(r"(参考文献|References|REFERENCES)[:：]?", line):
            mode = "ref"; collecting = False; blocks.append(("h2", "参考文献")); continue
        if re.fullmatch(r"(注释|注)[:：]?", line):
            mode = "note"; collecting = False; blocks.append(("h2", "注释")); continue
        if re.fullmatch(r"材料说明[:：]?", line):
            mode = "note"; collecting = False; blocks.append(("h2", "材料说明")); continue
        if mode == "body":
            m = re.match(r'^\*{0,2}摘\s*[　]?\s*要\*{0,2}[：:\s　]*(.*)$', line)
            if m and not abstract:
                abstract = m.group(1).strip() or "__NEXT__"; collecting = True; continue
            if collecting:
                if (line.startswith("关键词")
                        or re.match(r'^第?[一二三四五六七八九十]+[、.．]', line)
                        or re.match(r'^#{1,3}\s', line)):
                    collecting = False
                    if abstract == "__NEXT__":
                        abstract = ""
                else:
                    abstract = line if abstract == "__NEXT__" else abstract + line
                    continue
            m = re.match(r'^\*{0,2}关键词\*{0,2}[：:\s　]*(.*)$', line)
            if m and not keywords:
                keywords = m.group(1).strip() or "__NEXT__"; continue
            if keywords == "__NEXT__":
                keywords = line; continue
        is_h = mode == "body" and len(line) < 72 and (
            bool(re.match(r'^#{1,3}\s', line))
            or bool(re.match(r'^第?[一二三四五六七八九十]+[、.．]', line))
            or bool(re.match(r'^\d+(?:\.\d+)*[、.\s]\S', line))
            or line in ("引言", "结论", "余论", "证伪条件", "证伪条件与边界"))
        line = re.sub(r'^#{1,3}\s*', "", line)
        blocks.append(("h2" if is_h else ("ref" if mode == "ref" else "p"), line))
    return abstract, keywords, blocks


def abstract_block(page, P, abstract, keywords):
    """挑一个该页骨架已有的摘要类；都没有就用兜底类（随块带样式）。"""
    css = page[page.find("<style>"):page.find("</style>")]
    if re.search(r'\.abstract\{', css):
        cls, extra = "abstract", ""
    elif re.search(r'\.abs\{', css):
        cls, extra = "abs", ""
    else:
        cls, extra = "abs-restored", FALLBACK_CSS
    kw = (f'<p class="kw"><b>关键词：</b>{html.escape(keywords)}</p>' if keywords else "")
    return (f'{extra}<div class="{cls}"><span class="lb"><b>摘 要</b></span>'
            f'<p>{P.strongify(abstract)}</p>{kw}</div>\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    fixed = skipped = failed = 0
    for report, pubmod, metamod, srcdir in BATCHES:
        P = __import__(pubmod)
        M = __import__(metamod)
        # kfh 那批的源篇号字段叫 n，其余叫 src
        KEY = "src" if "src" in M.PAPERS[0] else "n"
        meta = {p[KEY]: p for p in M.PAPERS}
        src = Path(srcdir)
        rep = json.loads((ROOT / "tools" / report).read_text(encoding="utf-8"))["papers"]
        print(f"\n── {report}")
        for r in rep:
            sl = r.get("student") or "kong-fanhe"
            d = STU / sl / r["slug"]
            f = d / "index.html"
            if not f.exists():
                print(f"   ⚠ {sl}/{r['slug']} 页面不存在（可能已撤下），跳过"); skipped += 1; continue
            page = f.read_text(encoding="utf-8")
            if 'class="abstract"' in page or 'class="abs"' in page or 'class="abs-restored"' in page:
                skipped += 1; continue

            sid = r.get("src") or r.get("n")
            paper = dict(meta[sid]); paper.update(r)
            try:
                lines = [P.rename(x) for x in P.apply_cleanup(sid, P.load_source(src, sid))]
                paper["title"] = P.rename(paper["title"])
                abstract, keywords, blocks = parse_fixed(P, paper, lines)
            except Exception as e:
                print(f"   ✗ {sl}/{r['slug']} 解析失败：{e}"); failed += 1; continue
            if len(abstract) < 40:
                print(f"   ⚠ {sl}/{r['slug']} 源文未解析出摘要（{len(abstract)} 字），跳过"); skipped += 1; continue

            anchor = '<div class="scorebox">'
            if anchor not in page:
                print(f"   ✗ {sl}/{r['slug']} 未找到 scorebox 锚点"); failed += 1; continue

            if not args.dry:
                new = page.replace(anchor, abstract_block(page, P, abstract, keywords) + anchor, 1)
                f.write_text(new, encoding="utf-8")
                # PDF 里印的是错的内容，必须重出
                ph = Path("/tmp/sweep_print"); ph.mkdir(exist_ok=True)
                hp = ph / f'{r["slug"]}.html'
                hp.write_text(P.render_print(paper, abstract, keywords, blocks), encoding="utf-8")
                P.build_pdf(hp, d / f'{r["slug"]}.pdf')
                from jcl_stamp_pages import stamp
                stamp(d / f'{r["slug"]}.pdf')
            print(f"   ✓ {sl}/{r['slug']:<30} 摘要 {len(abstract):>4} 字"
                  f" · 关键词 {'有' if keywords else '无'}")
            fixed += 1

    print(f"\n补回 {fixed} 篇 · 跳过 {skipped} · 失败 {failed}"
          + ("（--dry 未落盘）" if args.dry else ""))


if __name__ == "__main__":
    main()
