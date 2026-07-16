#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDE Universes 站内搜索索引构建器
- 抽取 public/ 下所有 HTML 可见正文 + 所有 PDF 正文
- 每个页面 URL 一个 doc；同目录的 PDF 归到该 URL（chunk 级去重：HTML 优先，PDF 补空缺）
- 按栏目分片输出到 public/search/
一份索引同时服务：Tier1 前端关键词搜 + Tier2 Worker 问答检索
用法：python3 tools/build_search_index.py
每次内容更新后重跑本脚本再提交（索引会随内容过期）。
"""
import os, re, json, hashlib, subprocess, html as htmllib, datetime, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, "public")
OUT = os.path.join(PUB, "search")

SECTION_LABELS = {
    "column": "长文专栏", "students": "学员专栏", "books": "专著导读",
    "philosophy": "思想宇宙", "hotspot": "今日热点", "taste": "智能体·工具",
    "plagiarism": "论文抄袭专栏",
    "diag": "自诊断", "quotes": "金句", "check": "校验", "_root": "首页与其他",
}
# 这些目录/文件不进搜索索引（工具页、纯脚本、检索页自身）
SKIP_DIRS = {"search"}
SKIP_URL_SUBSTR = ("/taste/idea-generator/", "/taste/glm-test", "/check/", "/diag/", "/quotes/", "/fresh")

CJK = re.compile(r"[\u4e00-\u9fff]")

def canon_url(relpath):
    u = "/" + relpath.replace(os.sep, "/")
    if u.endswith("/index.html"):
        u = u[: -len("index.html")]
    return u

def section_of(relpath):
    top = relpath.replace(os.sep, "/").split("/")[0]
    return top if top in SECTION_LABELS else "_root"

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
            # 归到同目录的页面 URL（该目录若有 index.html 则用目录 URL，否则直接指向 PDF）
            reldir = os.path.dirname(rel)
            host_index = os.path.join(dp, "index.html")
            if os.path.exists(host_index):
                url = canon_url(os.path.join(reldir, "index.html"))
            else:
                url = "/" + rel.replace(os.sep, "/")  # 无壳页 → 直链 PDF
            if any(s in url for s in SKIP_URL_SUBSTR):
                continue
            d = docs.setdefault(url, {"title": os.path.splitext(fn)[0], "section": section_of(rel), "html": "", "pdf": []})
            d["pdf"].append(pdf_text(full))

# ---- 切块 + 去重（HTML 优先，PDF 补空缺）----
manifest_docs = []
shards = {}  # section -> [ {d, t} ]
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
    st = sec_stat.setdefault(d["section"], {"docs": 0, "chunks": 0})
    st["docs"] += 1
    st["chunks"] += len(doc_chunks)

# ---- 写出 ----
os.makedirs(OUT, exist_ok=True)
# 清旧分片
for f in os.listdir(OUT):
    if f.startswith("shard-") or f == "manifest.json":
        os.remove(os.path.join(OUT, f))

sections_meta = []
for sec, st in sorted(sec_stat.items(), key=lambda kv: -kv[1]["chunks"]):
    sections_meta.append({"key": sec, "label": SECTION_LABELS.get(sec, sec),
                          "docs": st["docs"], "chunks": st["chunks"]})
    with open(os.path.join(OUT, "shard-%s.json" % sec), "w", encoding="utf-8") as f:
        json.dump({"chunks": shards[sec]}, f, ensure_ascii=False, separators=(",", ":"))

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
for s in sections_meta:
    sz = os.path.getsize(os.path.join(OUT, "shard-%s.json" % s["key"]))
    print("  %-10s doc%4d  块%5d  分片%7.1fKB  (%s)" % (s["key"], s["docs"], s["chunks"], sz / 1024, s["label"]))
mz = os.path.getsize(os.path.join(OUT, "manifest.json"))
print("  manifest.json  %.1fKB" % (mz / 1024))
