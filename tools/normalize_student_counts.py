# -*- coding: utf-8 -*-
"""全站学员数目一致化：合并重复的“本批新作”区块 + 修正过期总数。

背景：2026-07-26 分四批发表 44 篇，每批都往学员主页插了一个“本批新作”静态区，
结果高鹏／阳涌／张琼 的主页各有 2-3 个同日区块。本脚本把每人的同日区块合并为一个，
按序号从高到低列出该学员当天全部新作。

另修正若干页面里写死的过期总篇数（真实数以 roster.json 为准，它由
build_roster.py 从磁盘派生）。descriptive 用法（“系列五篇”“十五篇合作论文”
“公众号 122 篇”）与卡片里的批次数一概不动。
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STU = ROOT / "public" / "students"
PUBDATE_CN = "2026年7月26日"
CN = "零一二三四五六七八九十"


def cn(n):
    if n <= 10: return CN[n]
    if n < 20:  return "十" + CN[n - 10]
    return CN[n // 10] + "十" + (CN[n % 10] if n % 10 else "")


NUMSTYLE = {"gao-peng": "arabic"}          # 其余学员用中文序号


def numlabel(sl, num):
    return f"之{num}" if NUMSTYLE.get(sl) == "arabic" else f"之{cn(num)}"


# ── 当天各批的产出（从各批 report 汇总）────────────────────────────────
def todays_papers():
    out = {}
    for name in ("top5_report.json", "batch2_report.json", "batch3_report.json"):
        p = ROOT / "tools" / name
        if not p.exists():
            continue
        for x in json.loads(p.read_text(encoding="utf-8"))["papers"]:
            out.setdefault(x["student"], []).append(x)
    for sl in list(out):
        # 已撤下的学员（如蔡彦）目录已不存在，不参与合并
        if not (STU / sl / "index.html").exists():
            del out[sl]
            continue
        out[sl].sort(key=lambda x: -x["num"])
    return out


BLOCK_OPEN = '<div style="max-width:820px;margin:28px auto 0;padding:0 24px">'


def strip_blocks(h):
    """删掉本脚本家族此前插入的全部同日区块，返回 (新文本, 删除个数, 首个位置)。"""
    first = None
    removed = 0
    while True:
        i = h.find(BLOCK_OPEN)
        if i < 0:
            break
        # 逐字符配平 div，找到区块结束
        depth, j = 0, i
        while j < len(h):
            m = re.compile(r'<div\b|</div>').search(h, j)
            if not m:
                raise RuntimeError("div 未配平")
            depth += 1 if m.group(0) == "<div" else -1
            j = m.end()
            if depth == 0:
                break
        seg = h[i:j]
        if "本 批 新 作" not in seg:      # 不是我们的区块，保留并跳过
            break
        if first is None:
            first = i
        h = h[:i] + h[j:]
        removed += 1
    return h, removed, first


def build_block(sl, papers):
    items = "".join(
        f'      <li style="margin-bottom:9px"><a href="/students/{sl}/{p["slug"]}/" style="color:var(--gold)">'
        f'《{p["title"]}》</a>'
        f'<span style="font-size:13px;opacity:.8"> — {p["kind"]} · {numlabel(sl, p["num"])} · '
        f'约 {p["wan"]} 万字 · {p["pages"]} 页 · '
        f'<a href="/students/{sl}/{p["slug"]}/read.html" style="color:var(--gold)">在线 PDF</a> · '
        f'<a href="/students/{sl}/{p["slug"]}/{p["slug"]}.pdf" download style="color:var(--gold)">下载 PDF</a>'
        f'</span></li>\n' for p in papers)
    return f"""{BLOCK_OPEN}
  <div style="border:1px solid rgba(201,168,76,0.42);border-radius:14px;padding:20px 24px;background:rgba(201,168,76,0.06)">
    <div style="font-size:12px;letter-spacing:.28em;color:var(--gold);margin-bottom:10px">本 批 新 作 · {PUBDATE_CN} · {len(papers)} 篇</div>
    <ul style="margin:0 0 0 1.1em;line-height:1.8;padding:0">
{items}    </ul>
    <p style="margin:12px 0 0"><a href="/students/{sl}/works/" style="color:var(--gold)">查看全部作品 →</a></p>
  </div>
</div>
"""


# ── 过期总数：逐处带 assert 锚定 ────────────────────────────────────────
# 说明：[data-publication-count] 由 publication-count.js 在运行时用 roster 覆盖，
# 页面里写的是无 JS 时的回退值——仍须正确，否则首屏与禁用 JS 时显示旧数。
STALE_TEXT = [
    ("hu-zhiying/works/index.html", "英语教育 · 3 篇文章", "英语教育 · 18 篇文章"),
    ("huang-qianying/index.html", "作 品 · 25 篇已发表", "作 品 · 51 篇已发表"),
    ("huang-qianying/works/index.html", "理解发生学 · 20 篇文章", "理解发生学 · 51 篇文章"),
    ("lei-jianhua/works/index.html", "家庭教育系列 6 篇", "家庭教育系列 10 篇"),
    ("putao/works/index.html", "SDE 学员 · 39 篇文章", "SDE 学员 · 42 篇文章"),
    ("shao-min/works/index.html", "诗歌批评 · 6 篇文章", "诗歌批评 · 7 篇文章"),
    ("yang-yong/index.html", "作 品 发 表 · 9 篇", "作 品 发 表 · 39 篇"),
]


def fix_generic(slug, real, rel):
    """把回退计数与写死的 fact 磁贴同步到 roster 的真实数。"""
    f = STU / slug / rel
    if not f.exists():
        return []
    h = f.read_text(encoding="utf-8")
    log = []

    def rep_count(m):
        if int(m.group(2)) != real:
            log.append(f"回退值 {m.group(2)} → {real}")
        return f"{m.group(1)}{real}<"
    h2 = re.sub(r'(data-publication-count[^>]*>)(\d+)<', rep_count, h)

    def rep_fact(m):
        if int(m.group(1)) != real:
            log.append(f"fact 磁贴 {m.group(1)}篇 → {real}篇")
        return f"<b>{real}篇</b><span>{m.group(2)}</span>"
    h2 = re.sub(r'<b>(\d+)\s*篇</b>\s*<span>([^<]*已发表[^<]*)</span>', rep_fact, h2)

    if h2 != h:
        f.write_text(h2, encoding="utf-8")
    return log


def main():
    roster = {s["slug"]: s for s in json.loads((STU / "roster.json").read_text(encoding="utf-8"))["students"]}
    papers = todays_papers()

    print("— 合并重复的“本批新作”区块 —")
    for sl, ps in sorted(papers.items()):
        f = STU / sl / "index.html"
        h = f.read_text(encoding="utf-8")
        new, removed, pos = strip_blocks(h)
        if removed == 0:
            print(f"  {sl:<14}无本脚本家族区块，跳过")
            continue
        block = build_block(sl, ps)
        new = new[:pos] + block + new[pos:]
        f.write_text(new, encoding="utf-8")
        print(f"  {roster[sl]['name']:<6}{sl:<14}{removed} 个区块 → 1 个，列出当日 {len(ps)} 篇")

    print("\n— 同步回退计数与 fact 磁贴（全部 35 名学员）—")
    total = 0
    for slug in sorted(roster):
        for rel in ("index.html", "works/index.html"):
            for line in fix_generic(slug, roster[slug]["count"], rel):
                print(f"  {roster[slug]['name']:<6}{slug + '/' + rel:<32}{line}")
                total += 1
    print(f"  共修正 {total} 处")

    print("\n— 修正写死的过期总数 —")
    for rel, old, new in STALE_TEXT:
        f = STU / rel
        h = f.read_text(encoding="utf-8")
        assert old in h, f"锚点未找到：{rel} :: {old}"
        f.write_text(h.replace(old, new, 1), encoding="utf-8")
        print(f"  {roster[rel.split('/')[0]]['name']:<6}{rel:<32}{old}  →  {new}")


if __name__ == "__main__":
    main()
