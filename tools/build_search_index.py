#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDE Universes 站内搜索索引构建器
- 抽取 public/ 下所有 HTML 可见正文 + 所有 PDF 正文
- 每个页面 URL 一个 doc；同目录的 PDF 归到该 URL（chunk 级去重：HTML 优先，PDF 补空缺）
- 按栏目分片输出到 public/search/
一份索引同时服务：Tier1 前端关键词搜 + Tier2 Worker 问答检索
用法：python3 tools/build_search_index.py
快速同源模式：python3 tools/build_search_index.py --html-only
保留旧独立PDF：python3 tools/build_search_index.py --reuse-pdf
每次内容更新后重跑本脚本再提交（索引会随内容过期）。
"""
import os, re, json, hashlib, subprocess, html as htmllib, datetime, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, "public")
OUT = os.path.join(PUB, "search")

SECTION_LABELS = {
    "column": "长文专栏", "students": "学员专栏", "books": "专著导读",
    "philosophy": "思想宇宙", "hotspot": "今日热点", "taste": "智能体·工具",
    "plagiarism": "论文抄袭专栏", "creation": "学术创造专栏",
    "diag": "自诊断", "quotes": "金句", "check": "校验", "_root": "首页与其他",
}
# 这些目录/文件不进搜索索引（工具页、纯脚本、检索页自身）
SKIP_DIRS = {"search"}
SKIP_URL_SUBSTR = ("/taste/idea-generator/", "/taste/glm-test", "/check/", "/diag/", "/quotes/", "/fresh")

CJK = re.compile(r"[\u4e00-\u9fff]")
HTML_ONLY = "--html-only" in sys.argv
REUSE_PDF = "--reuse-pdf" in sys.argv


def _check_stale():
    """--check：只比对不重建。索引是派生数据，会随内容过期。

    用途：提交前自检，或在别人怀疑「搜不到刚发的东西」时一秒定位。
    判据：磁盘上该进索引的页面集合，与 manifest 记录的 URL 集合是否一致。
    退出码 1 = 已过期，需重跑本脚本。
    """
    mf = os.path.join(OUT, "manifest.json")
    if not os.path.exists(mf):
        print("manifest.json 不存在 —— 索引从未构建", file=sys.stderr)
        return 1
    m = json.load(open(mf, encoding="utf-8"))
    have = {d["u"] for d in m.get("docs", [])}

    # 判据必须与下方主循环的筛选规则完全一致，否则自检会报出一堆假警报：
    # read.html 是 PDF 阅读器空壳（无独立正文，生成器跳过）；PDF 不单独成文档，
    # 而是归到同目录的页面 URL。照抄规则，不要另写一套。
    want = set()
    for dirpath, dirnames, filenames in os.walk(PUB):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.endswith(".html") or fn == "read.html":
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), PUB)
            u = canon_url(rel)
            if any(k in u for k in SKIP_URL_SUBSTR):
                continue
            want.add(u)

    missing = sorted(want - have)   # 已发布但未进索引 —— 站内搜不到
    # 孤立 PDF（同目录无 index.html）由生成器以 PDF 自身 URL 建文档，是合法收录，
    # 不在 want 里但也不是死链。只报那些磁盘上真的已经没有对应文件的。
    def _exists(u):
        rel = u.strip("/")
        if not rel:
            return True
        cand = os.path.join(PUB, rel)
        return os.path.exists(cand) or os.path.isdir(cand) or os.path.exists(os.path.join(cand, "index.html"))
    stale = sorted(u for u in (have - want) if not _exists(u))

    print("manifest 构建于 %s · 收录 %d 篇 · 磁盘 %d 篇" % (m.get("built", "?"), len(have), len(want)))
    if not missing and not stale:
        print("[OK] 索引与磁盘一致")
        return 0
    if missing:
        print("\n❌ 已发布但搜不到（%d 篇）：" % len(missing), file=sys.stderr)
        for u in missing[:25]:
            print("   " + u, file=sys.stderr)
        if len(missing) > 25:
            print("   …另有 %d 篇" % (len(missing) - 25), file=sys.stderr)
    if stale:
        print("\n⚠ 索引里有、磁盘已无（%d 篇）：" % len(stale), file=sys.stderr)
        for u in stale[:10]:
            print("   " + u, file=sys.stderr)
    print("\n→ 请运行：python3 tools/build_search_index.py", file=sys.stderr)
    return 1


def canon_url(relpath):
    u = "/" + relpath.replace(os.sep, "/")
    if u.endswith("/index.html"):
        u = u[: -len("index.html")]
    return u

def section_of(relpath):
    top = relpath.replace(os.sep, "/").split("/")[0]
    return top if top in SECTION_LABELS else "_root"

# --check 在此拦截：canon_url / SKIP_* 已定义，且尚未开始构建
if "--check" in sys.argv:
    sys.exit(_check_stale())


def clean_text(t):
    t = htmllib.unescape(t)
    t = t.replace("\u3000", " ").replace("\xa0", " ")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{2,}", "\n", t)
    return t.strip()

def html_title_and_text(path):
    raw = open(path, encoding="utf-8", errors="ignore").read()
    # 标题：<title> 优先，退回首个 <h1>
    title = ""
    m = re.search(r"<title[^>]*>(.*?)</title>", raw, re.S | re.I)
    if m:
        title = htmllib.unescape(re.sub(r"\s+", " ", m.group(1))).strip()
    if not title:
        m = re.search(r"<h1[^>]*>(.*?)</h1>", raw, re.S | re.I)
        if m:
            title = htmllib.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()
    # 正文：去 script/style/head/nav/footer，再去标签
    body = raw
    for tag in ("script", "style", "head", "nav", "footer", "svg"):
        body = re.sub(r"<%s[^>]*>.*?</%s>" % (tag, tag), " ", body, flags=re.S | re.I)
    body = re.sub(r"<!--.*?-->", " ", body, flags=re.S)
    body = re.sub(r"<[^>]+>", " ", body)
    return (title or "(无标题)"), clean_text(body)

def pdf_text(path):
    try:
        r = subprocess.run(["pdftotext", "-nopgbrk", path, "-"], capture_output=True, timeout=180)
        return clean_text(r.stdout.decode("utf-8", "ignore"))
    except FileNotFoundError:
        # The desktop/runtime bundle does not always ship the Poppler CLI.
        # Keep PDF indexing complete by falling back to the bundled pypdf.
        try:
            from pypdf import PdfReader
            reader = PdfReader(path)
            return clean_text("\n".join(page.extract_text() or "" for page in reader.pages))
        except Exception as e:
            print("  ! pdf fail:", path, e, file=sys.stderr)
            return ""
    except Exception as e:
        print("  ! pdf fail:", path, e, file=sys.stderr)
        return ""

def norm_key(s):
    # 去重键：只留中文与字母数字，压掉噪声后取指纹
    core = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", s)
    return hashlib.md5(core.encode("utf-8")).hexdigest() if len(core) >= 12 else None

def chunk_text(t, size=420, overlap=40):
    """按句号/换行优先切 ~size 字的块，块间小重叠。"""
    if not t:
        return []
    # 先按硬边界切成句子
    parts = re.split(r"(?<=[。！？!?；;\n])", t)
    chunks, cur = [], ""
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if len(cur) + len(p) <= size:
            cur += p
        else:
            if cur:
                chunks.append(cur)
            if len(p) > size:  # 超长句硬切
                for i in range(0, len(p), size - overlap):
                    chunks.append(p[i : i + size])
                cur = ""
            else:
                cur = p
    if cur:
        chunks.append(cur)
    # 过滤：太短或几乎没中文/字母的块丢掉（页码、噪声）
    out = []
    for c in chunks:
        c = c.strip()
        if len(c) < 24:
            continue
        if len(CJK.findall(c)) < 6 and len(re.findall(r"[A-Za-z]", c)) < 20:
            continue
        out.append(c)
    return out

# ---- 收集 ----
old_pdf_text = {}
if REUSE_PDF:
    try:
        old_manifest = json.load(open(os.path.join(OUT, "manifest.json"), encoding="utf-8"))
        for record in old_manifest.get("docs", []):
            if not record.get("u", "").lower().endswith(".pdf"):
                continue
            doc_path = os.path.join(OUT, "doc", "%s.json" % record["i"])
            payload = json.load(open(doc_path, encoding="utf-8"))
            old_pdf_text[record["u"]] = "\n".join(payload.get("c", []))
        print("复用独立 PDF 索引文本：%d 篇" % len(old_pdf_text))
    except Exception as e:
        print("  ! 无法复用旧 PDF 索引：", e, file=sys.stderr)

docs = {}  # url -> {title, section, html_text, pdf_texts:[...]}
for dp, dns, fns in os.walk(PUB):
    dns[:] = [d for d in dns if d not in SKIP_DIRS]
    for fn in fns:
        full = os.path.join(dp, fn)
        rel = os.path.relpath(full, PUB)
        if fn.endswith(".html"):
            if fn == "read.html":
                continue  # PDF 阅读器空壳：无独立正文，PDF 内容已折叠进目录 URL 文档
            url = canon_url(rel)
            if any(s in url for s in SKIP_URL_SUBSTR):
                continue
            title, text = html_title_and_text(full)
            d = docs.setdefault(url, {"title": title, "section": section_of(rel), "html": "", "pdf": []})
            if title and title != "(无标题)":
                d["title"] = title  # HTML 标题权威，覆盖 PDF 先到时留下的文件名占位
            d["html"] = (d["html"] + "\n" + text).strip()
        elif fn.endswith(".pdf"):
            if HTML_ONLY:
                # 站内长文的 PDF 均由同目录 index.html 生成；发布终检时可跳过
                # 重复的 PDF 文本抽取。孤立 PDF 留给完整构建模式收录。
                continue
            # 归到同目录的页面 URL（该目录若有 index.html 则用目录 URL，否则直接指向 PDF）
            reldir = os.path.dirname(rel)
            host_index = os.path.join(dp, "index.html")
            if os.path.exists(host_index):
                if REUSE_PDF:
                    # 同目录网页是PDF的发布母本；网页全文已经收录，无需重复解析。
                    continue
                url = canon_url(os.path.join(reldir, "index.html"))
            else:
                url = "/" + rel.replace(os.sep, "/")  # 无壳页 → 直链 PDF
            if any(s in url for s in SKIP_URL_SUBSTR):
                continue
            d = docs.setdefault(url, {"title": os.path.splitext(fn)[0], "section": section_of(rel), "html": "", "pdf": []})
            if REUSE_PDF and url in old_pdf_text:
                d["pdf"].append(old_pdf_text[url])
            else:
                d["pdf"].append(pdf_text(full))

# ---- 切块 + 去重（HTML 优先，PDF 补空缺）----
manifest_docs = []
shards = {}  # section -> [ {d, t} ]
per_doc = {}  # LIGHT_INDEX：docIdx -> [块...]，用于写"每篇一个文件"的轻量索引
tot_chunks = 0
tot_chars = 0
sec_stat = {}

url_list = sorted(docs.keys())
for idx, url in enumerate(url_list):
    d = docs[url]
    seen = set()
    doc_chunks = []
    # HTML 先切、登记指纹
    for c in chunk_text(d["html"]):
        k = norm_key(c)
        if k and k in seen:
            continue
        if k:
            seen.add(k)
        doc_chunks.append(c)
    # PDF 补：指纹已见的丢掉（栏目 HTML=PDF 镜像会被这里清掉；专著薄壳会保留 PDF）
    for pt in d["pdf"]:
        for c in chunk_text(pt):
            k = norm_key(c)
            if k and k in seen:
                continue
            if k:
                seen.add(k)
            doc_chunks.append(c)
    if not doc_chunks:
        continue
    di = len(manifest_docs)
    manifest_docs.append({"i": di, "u": url, "t": d["title"][:120], "s": d["section"]})
    sh = shards.setdefault(d["section"], [])
    for c in doc_chunks:
        sh.append({"d": di, "t": c})
        tot_chunks += 1
        tot_chars += len(c)
    per_doc[di] = doc_chunks          # LIGHT_INDEX：留一份，稍后按篇写出
    st = sec_stat.setdefault(d["section"], {"docs": 0, "chunks": 0})
    st["docs"] += 1
    st["chunks"] += len(doc_chunks)

# ---- 写出 ----
os.makedirs(OUT, exist_ok=True)
# 清旧分片
for f in os.listdir(OUT):
    if f.startswith("shard-") or f == "manifest.json":
        os.remove(os.path.join(OUT, f))

# Cloudflare 静态资产单文件上限 25MiB。栏目分片超过 SHARD_MAX 即按序切成多个文件，
# 文件名 shard-<sec>-1.json / -2.json …，清单写进 manifest sections[].files；
# 消费方一律按 s.files（缺省退回 [s.key]）逐文件拉取——切分随每次重建自动进行，
# 文本再涨十倍也只是文件变多，永远不会撞单文件上限。
# （消费方包括 .github/workflows/search-index.yml 的完整性自检；它一度按 key 拼
#   shard-<key>.json，栏目一分片就整片报缺失——凡新增消费方，一律走 s.files。）
SHARD_MAX = 6 * 1024 * 1024

sections_meta = []
for sec, st in sorted(sec_stat.items(), key=lambda kv: -kv[1]["chunks"]):
    parts, cur, cur_bytes = [], [], 16  # 16 = {"chunks":[]} 外壳底噪
    for c in shards[sec]:
        b = len(json.dumps(c, ensure_ascii=False, separators=(",", ":")).encode("utf-8")) + 1
        if cur and cur_bytes + b > SHARD_MAX:
            parts.append(cur)
            cur, cur_bytes = [], 16
        cur.append(c)
        cur_bytes += b
    if cur:
        parts.append(cur)
    files = [sec] if len(parts) == 1 else ["%s-%d" % (sec, i + 1) for i in range(len(parts))]
    for fname, cl in zip(files, parts):
        with open(os.path.join(OUT, "shard-%s.json" % fname), "w", encoding="utf-8") as f:
            json.dump({"chunks": cl}, f, ensure_ascii=False, separators=(",", ":"))
    sections_meta.append({"key": sec, "label": SECTION_LABELS.get(sec, sec),
                          "docs": st["docs"], "chunks": st["chunks"], "files": files})

# ---- LIGHT_INDEX：轻量两段式检索用的两样东西 ----
# 背景：整份索引已 60MB／20 片。答题时把它整份装进 Worker 会撞平台资源上限（线上实测 error 1102，
# 撞坏的 isolate 还会连累随后的请求）。所以另出一套小索引：
#   keywords.json —— 每篇一行的高频词（约 200KB），先用它把 849 篇筛成十几篇；
#   doc/<i>.json  —— 每篇自己的块文件，第二段只取选中的那十几篇（合计一两百 KB）。
# 大分片仍旧写出，站内搜索与旧消费方不受影响。
DOC_DIR = os.path.join(OUT, "doc")
if os.path.isdir(DOC_DIR):
    for f in os.listdir(DOC_DIR):
        if f.endswith(".json"):
            os.remove(os.path.join(DOC_DIR, f))
os.makedirs(DOC_DIR, exist_ok=True)

def _doc_keywords(chunks, topn=64):
    """每篇取高频中文 bigram + 英文词，作为第一段筛选的依据。"""
    freq = {}
    txt = "".join(chunks)[:40000]
    zh = re.sub(r"[^\u4e00-\u9fff]", " ", txt)
    for seg in zh.split():
        for i in range(len(seg) - 1):
            g = seg[i : i + 2]
            freq[g] = freq.get(g, 0) + 1
    for w in re.findall(r"[a-zA-Z]{3,}", txt.lower()):
        freq[w] = freq.get(w, 0) + 2
    return [k for k, _ in sorted(freq.items(), key=lambda kv: -kv[1])[:topn]]

# TIERED_INDEX：三层索引。检索时按需下钻，每层只读"够用来选下一层"的那点数据：
#   L0 /search/sections.json —— 版块层（9 个版块各一朵关键词云，几十 KB），先定"往哪个版块找"；
#   L1 /search/kw/<sec>.json —— 篇层，按版块切开（最大的一份也只有百来 KB），只读选中版块的；
#   L2 /search/doc/<i>.json  —— 段层，只读最终选中的那十几篇。
# 旧的 keywords.json 仍然写出，作为"选不出版块"时的兜底与旧版 worker 的退路。
KW_DIR = os.path.join(OUT, "kw")
if os.path.isdir(KW_DIR):
    for f in os.listdir(KW_DIR):
        if f.endswith(".json"):
            os.remove(os.path.join(KW_DIR, f))
os.makedirs(KW_DIR, exist_ok=True)

doc_sec = {d["i"]: d["s"] for d in manifest_docs}
kw_rows = []
kw_by_sec = {}
sec_cloud = {}
for di, chunks in per_doc.items():
    with open(os.path.join(DOC_DIR, "%d.json" % di), "w", encoding="utf-8") as f:
        json.dump({"i": di, "c": chunks}, f, ensure_ascii=False, separators=(",", ":"))
    ks = _doc_keywords(chunks)
    row = {"i": di, "k": ks}
    kw_rows.append(row)
    sec = doc_sec.get(di, "_root")
    kw_by_sec.setdefault(sec, []).append(row)
    cloud = sec_cloud.setdefault(sec, {})
    for t in ks:
        cloud[t] = cloud.get(t, 0) + 1

with open(os.path.join(OUT, "keywords.json"), "w", encoding="utf-8") as f:
    json.dump({"rows": kw_rows}, f, ensure_ascii=False, separators=(",", ":"))
for sec, rows in kw_by_sec.items():
    with open(os.path.join(KW_DIR, "%s.json" % sec), "w", encoding="utf-8") as f:
        json.dump({"rows": rows}, f, ensure_ascii=False, separators=(",", ":"))
# 版块层：每个版块取最能代表它的 600 个词（按"多少篇文章用到"排序），外加篇数，用于第一层选向
sections_l0 = []
for sec, cloud in sec_cloud.items():
    top = sorted(cloud.items(), key=lambda kv: -kv[1])[:600]
    sections_l0.append({"s": sec, "n": len(kw_by_sec.get(sec, [])), "k": [t for t, _ in top]})
with open(os.path.join(OUT, "sections.json"), "w", encoding="utf-8") as f:
    json.dump({"sections": sections_l0}, f, ensure_ascii=False, separators=(",", ":"))

manifest = {
    "built": datetime.datetime.utcnow().isoformat() + "Z",
    "counts": {"docs": len(manifest_docs), "chunks": tot_chunks, "chars": tot_chars},
    "sections": sections_meta,
    "docs": manifest_docs,
}
with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, separators=(",", ":"))

print("=== 索引构建完成 ===")
print("文档 %d 篇 | 块 %d 个 | 索引正文 %d 字" % (len(manifest_docs), tot_chunks, tot_chars))
HARD_CAP = 25 * 1024 * 1024  # Cloudflare 静态资产单文件硬上限（MiB）
for s in sections_meta:
    for fname in s["files"]:
        p = os.path.join(OUT, "shard-%s.json" % fname)
        sz = os.path.getsize(p)
        assert sz < HARD_CAP, "分片超 25MiB 上限：%s（%.1fMB）—— 调小 SHARD_MAX" % (p, sz / 1048576)
        print("  %-14s doc%4d  块%5d  分片%7.1fKB  (%s)" % (fname, s["docs"], s["chunks"], sz / 1024, s["label"]))
mz = os.path.getsize(os.path.join(OUT, "manifest.json"))
print("  manifest.json  %.1fKB" % (mz / 1024))
