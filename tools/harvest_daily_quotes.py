#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每日三句 · 库存自动扩充器 (harvest_daily_quotes)

从 public/column/*/index.html 抽取"承重金句",去重后追加进
public/assets/daily-quotes.js 的 DQ 数组。

为什么这样做而不是让模型每天现写:
  金句不是凭空造的,是从已发表的专栏正文里"显影"出来的承重句。
  正文本身已是打磨过的 SDE 文章,句子密度高;抽取器只做筛选,不做创作,
  所以无需大模型在环即可跑无人值守 —— 这正是"派生数据、预先生成"的第二铁律。

选句偏好(与首页抽取器 DQ_pickForDate 对齐):
  DQ_pickForDate 每天先抽 3 个"不同来源文章"再各取一句 —— 所以来源越多、
  每日三句越不重样。因此本器优先广度:从"尚未入池 / 少入池"的文章各取少量,
  尽量多铺来源,而不是往同一篇上堆。

用法:
  python3 tools/harvest_daily_quotes.py --dry-run          # 只看会选哪些,不写
  python3 tools/harvest_daily_quotes.py --count 30         # 追加 30 条并写回
  python3 tools/harvest_daily_quotes.py --count 30 --dry-run
"""
import re, sys, argparse, unicodedata, html
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
QUOTES_JS = ROOT / "public" / "assets" / "daily-quotes.js"
COLUMN_DIR = ROOT / "public" / "column"

MIN_SCORE = 4          # 质量地板:低于此分不进池
MIN_LEN, MAX_LEN = 18, 96
PER_ARTICLE_CAP = 2    # 单篇最多取几句(保广度)

# ── 元导航 / 设问脚手架:出现即弃 ──────────────────────────────
META = re.compile(
    r"(这篇文章|这一篇|本文|本书|本节|本章|这一章|这一节|下面|接下来|接着|"
    r"上篇|下篇|中篇|我们将|我们会|我们先|先讲|首先|如前|如上|后文|前文|"
    r"第一步|第二步|第三步|第一部分|第二部分|文章会|文章要|读者|请看|如下|"
    r"例如|比如说|譬如|举个例子|图\d|表\d|见下|见上|后面会|前面说)"
)
# ── 加分标记 ─────────────────────────────────────────────────
REVERSAL = re.compile(r"(不是.{0,22}?而是|从来不是|并非.{0,22}?而是|不.{1,16}?[,，]是|不是.{0,22}?[,，]是|不[是在].{0,14}?[,，]?是)")
DEFN     = re.compile(r"(的本质|的量度|就是.{0,14}本身|不过是|无非是|恰恰是|正是那|才是|本质上都是|从来就是)")
SDE      = re.compile(r"(发生|显露|纠缠|差异|表征|底盘|意义|路径|约束|自由|缠绕|中心位|退化|成熟态|锚定|张力|势能|回写)")
METAPHOR = re.compile(r"(像[一那这]?|如同|仿佛|好比|犹如)")
LEAD_CONJ = re.compile(r"^(可是|但是|然而|而且|所以|因此|因为|由此|可见|于是|然后|不过|其实|当然|况且|再者|另外|总之|换句话说|换言之|也就是说|这样一来|在这个意义上|正因如此)")
LEAD_PRON = re.compile(r"^(这|那|它|他|她|我们|你|你们|他们|这些|那些|此|其)")
# 续接式开头(缺主语/缺前提,离开段落就不自足)
CONT_OPEN = re.compile(r"^(意味着|这意味着|如果不能|如果能|如果不|理解这|这一步|之所以|正因为|也正因)")

# ── 硬弃(不适合上首页金句卡)──────────────────────────────────
CITATION = re.compile(r"[（(][^（()]*\d{4}[；;,，][^（()]*[）)]|[A-Za-z]{3,}\s*[,，]\s*\d{4}")  # (Mehan,1979;Cazden,2001) / Mehan,1979
ARG_LABEL = re.compile(r"^(推断|前提|命题|定理|推论|论点|论据|反驳|假设|定义|证明|引理|推证|小结)[一二三四五]?[:：]")
BOOK_REF  = re.compile(r"第[一二三四五六七八九十\d]{1,3}(编|卷)")  # "第四编里" 之类书内互指


DUP_THRESH = 0.72      # 3-gram Jaccard ≥ 此值即判为近重(文章常有换词复述)


def norm(s: str) -> str:
    """去标点空白后的规范形,用于去重。"""
    s = unicodedata.normalize("NFKC", s)
    return re.sub(r"[^\w\u4e00-\u9fff]", "", s).lower()


def grams(n: str):
    return {n[i:i + 3] for i in range(len(n) - 2)} or {n}


def jac(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def is_dup(g: set, gram_sets) -> bool:
    return any(jac(g, gs) >= DUP_THRESH for gs in gram_sets)


def load_pool():
    txt = QUOTES_JS.read_text(encoding="utf-8")
    entries = re.findall(r'\{t:"((?:[^"\\]|\\.)*)",u:"([^"]*)"\}', txt)
    seen = {norm(t) for t, _ in entries}
    per_src = defaultdict(int)
    for _, u in entries:
        per_src[u] += 1
    return txt, entries, seen, per_src


def article_text(path: Path) -> str:
    h = path.read_text(encoding="utf-8", errors="ignore")
    # 只取正文块:<p> / <blockquote> / <li>,天然排除 nav/footer/script/svg
    blocks = re.findall(r"<(?:p|blockquote|li)\b[^>]*>(.*?)</(?:p|blockquote|li)>", h, re.S | re.I)
    out = []
    for b in blocks:
        b = re.sub(r"<[^>]+>", "", b)            # 去内联标签
        b = html.unescape(b)
        b = re.sub(r"\s+", "", b)                # 中文正文无需空白
        if b:
            out.append(b)
    return "\n".join(out)


_LEAD_JUNK = "」』】》）)”\"、，,；;：: 　"


def clean(s: str) -> str:
    """去掉切句留下的悬尾闭合标点(上一句的收尾引号/括号漂到了本句开头)。"""
    return s.lstrip(_LEAD_JUNK).strip()


def split_sentences(text: str):
    for line in text.split("\n"):
        for p in re.split(r"(?<=[。！!？?])", line):
            p = clean(p)
            if p:
                yield p


def score(s: str) -> int:
    L = len(s)
    if L < MIN_LEN or L > MAX_LEN:
        return -99
    if META.search(s):
        return -99
    # 以 ？ 结尾的设问:只有带 —— 抛出判断的"为什么X——Y"式才留
    if s[-1] in "?？" and "——" not in s:
        return -99
    if (s.count("「") != s.count("」") or s.count("（") != s.count("）")
            or s.count("\u201c") != s.count("\u201d")):
        return -99                                # 半截引文
    if CITATION.search(s) or ARG_LABEL.match(s) or BOOK_REF.search(s):
        return -99                                # 学术引注 / 论证标号 / 书内互指:不上首页
    sc = 0
    if REVERSAL.search(s): sc += 3
    if DEFN.search(s):     sc += 2
    if "——" in s:          sc += 2
    if "；" in s or ";" in s: sc += 1
    if METAPHOR.search(s): sc += 1
    if SDE.search(s):      sc += 1
    if LEAD_CONJ.search(s): sc -= 2               # 承接连词开头 = 段中残句
    if CONT_OPEN.search(s): sc -= 2               # 续接式开头 = 缺主语/缺前提
    if LEAD_PRON.search(s): sc -= 1               # 代词回指 = 不自足
    return sc


def harvest(count: int):
    _, entries, seen, per_src = load_pool()
    pool_grams = [grams(norm(t)) for t, _ in entries]   # 与线上库对比
    batch_grams = []                                     # 批次内互查
    picks = []                                           # [(text, url, score)]

    arts = []
    for d in sorted(COLUMN_DIR.iterdir()):
        idx = d / "index.html"
        if d.is_dir() and idx.exists():
            slug = d.name
            arts.append((per_src.get(f"/column/{slug}/", 0), slug, idx))
    # 少入池 / 未入池的排前面 → 优先铺新来源
    arts.sort(key=lambda x: (x[0], x[1]))

    for _, slug, idx in arts:
        if len(picks) >= count:
            break
        url = f"/column/{slug}/"
        cands = []
        for s in split_sentences(article_text(idx)):
            n = norm(s)
            if n in seen:
                continue
            sc = score(s)
            if sc >= MIN_SCORE:
                cands.append((sc, len(s), s, n))
        cands.sort(key=lambda x: (-x[0], x[1]))
        taken = 0
        for sc, _, s, n in cands:
            if taken >= PER_ARTICLE_CAP or len(picks) >= count:
                break
            g = grams(n)
            if is_dup(g, pool_grams) or is_dup(g, batch_grams):
                continue
            picks.append((s, url, sc))
            batch_grams.append(g)
            taken += 1

    return picks


def write_back(picks):
    txt = QUOTES_JS.read_text(encoding="utf-8")
    marker = "\n];\nwindow.DQ=DQ;"
    assert marker in txt, "找不到 DQ 数组结束标记,拒绝写入(格式已变?)"
    lines = "".join(
        '\n {t:"%s",u:"%s"},' % (t.replace("\\", "\\\\").replace('"', '\\"'), u)
        for t, u, _ in picks
    )
    new = txt.replace(marker, lines + marker, 1)
    QUOTES_JS.write_text(new, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=30)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    picks = harvest(a.count)
    srcs = sorted({u for _, u, _ in picks})
    print(f"抽到 {len(picks)} 条,来自 {len(srcs)} 篇文章(目标 {a.count})")
    for i, (t, u, sc) in enumerate(picks, 1):
        print(f"[{sc}] {u[9:-1]:<34.34} {t}")

    if len(picks) < a.count:
        print(f"\n⚠ 只抽到 {len(picks)} 条(< {a.count})。可用新料在减少 —— "
              f"降低 MIN_SCORE 或等新文章发表。")

    if a.dry_run:
        print("\n[dry-run] 未写入。")
        return 0
    if not picks:
        print("无新句可加,跳过写入。")
        return 0
    write_back(picks)
    print(f"\n✅ 已追加 {len(picks)} 条到 {QUOTES_JS.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
