# -*- coding: utf-8 -*-
"""把并蒂文的旧格式 source.md（TITLE:/SUB:/ABS:/== 小标题）转成构建器认的
YAML frontmatter + Markdown。

为什么要它：`tools/student-companions/build.sh` 用 pandoc 的
`gfm+yaml_metadata_block` 读元数据。旧格式没有 YAML 块，于是所有模板变量
（title/subtitle/theory_author/三联路径…）全部解析为空——生成的页面标题是
「 ·  | 学员专栏」、三联导航 href="" 是死链。**页面看起来存在，实际是空壳。**

母文那边的信息（篇名、作者、日期、字数）从上一级 index.html 里取，不臆造。

用法：
    python3 tools/student-companions/convert_legacy_source.py --check
    python3 tools/student-companions/convert_legacy_source.py --write
"""
import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STU = ROOT / "public" / "students"


def parent_meta(paper_dir: Path):
    idx = paper_dir / "index.html"
    assert idx.exists(), f"{paper_dir}: 母文不存在"
    t = idx.read_text(encoding="utf-8")
    m = re.search(r"<h1[^>]*>(.*?)</h1>", t, re.S)
    title = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""
    d = re.search(r"发表于\s*([0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日)", t)
    
    author = ""
    a = re.search(r"<title>[^<]*·\s*([^·<]+?)\s*·\s*SDE Universes", t)
    if a:
        author = a.group(1).strip()
    return {
        "original_title": title,
        "date": f"发表于{d.group(1)}" if d else "",
        "theory_author": author,
    }


def parse_legacy(text: str):
    head = {}
    for key in ("TITLE", "SUB", "ABS"):
        m = re.search(rf"^{key}:\s*(.*)$", text, re.M)
        head[key] = m.group(1).strip() if m else ""
    body = text[text.index("\n== "):] if "\n== " in text else ""
    body = re.sub(r"(?m)^==\s+(.*)$", r"## \1", body).strip()
    return head, body


def yaml_esc(s: str) -> str:
    return s.replace('"', "'")


def convert(src: Path, write: bool):
    raw = src.read_text(encoding="utf-8")
    if raw.lstrip().startswith("---"):
        return None                      # 已经是 YAML，跳过
    head, body = parse_legacy(raw)
    kind = src.parent.name               # interpretation / practice
    paper = src.parent.parent
    student = paper.parent.name
    pm = parent_meta(paper)
    base = f"/students/{student}/{paper.name}/"
    is_practice = kind == "practice"
    sib = "interpretation" if is_practice else "practice"

    fm = [
        "---",
        f'title: "{yaml_esc(head["TITLE"])}"',
        f'subtitle: "{yaml_esc(head["SUB"])}"',
        f'page_type: "{"实用文" if is_practice else "诠释文"}"',
        f'theory_author: "{yaml_esc(pm["theory_author"])}"',
        f'author_path: "/students/{student}/works/"',
        f'date: "{pm["date"]}"',
        f'wordlabel: "全文约{round(len(re.findall(r"[\u4e00-\u9fff]", body)) / 500) * 500 or 500}字"',
        f'original_title: "{yaml_esc(pm["original_title"])}"',
        f'original_path: "{base}"',
        f'interpretation_path: "{base}interpretation/"',
        f'practice_path: "{base}practice/"',
        f'sibling_path: "{base}{sib}/"',
        f'sibling_label: "{"诠释文" if sib == "interpretation" else "实用文"}"',
    ]
    if is_practice:
        fm.append("is_practice: true")
    fm.append("---")

    lead = f"> {head['ABS']}\n\n" if head["ABS"] else ""
    out = "\n".join(fm) + "\n\n" + lead + body + "\n"

    missing = [k for k, v in pm.items() if not v] + \
              [k for k in ("TITLE", "SUB") if not head[k]]
    if write:
        src.write_text(out, encoding="utf-8")
    return {"path": str(src.relative_to(ROOT)), "missing": missing,
            "sections": body.count("\n## ") + body.startswith("## ")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    done, bad = 0, []
    for src in sorted(STU.glob("*/*/*/source.md")):
        if src.parent.name not in ("interpretation", "practice"):
            continue
        r = convert(src, a.write)
        if r is None:
            continue
        done += 1
        if r["missing"] or r["sections"] < 2:
            bad.append(r)
    print(f"{'已改写' if a.write else '待改写'} {done} 份旧格式 source.md")
    for r in bad:
        print("  ⚠", r["path"], "缺", r["missing"], "节数", r["sections"])
    if not bad:
        print("  元数据全部从母文取到，无缺项")


if __name__ == "__main__":
    main()
