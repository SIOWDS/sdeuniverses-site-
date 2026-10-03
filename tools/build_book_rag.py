#!/usr/bin/env python3
"""为每一本有全文的专著，提前打造它自己的碰撞库（RAG）——public/books/m/N/rag.json。

2026-10-03 王德生令：每本书的智能体要有自己独特的 RAG 系统，能检索到其他的书、甚至网站上的文章，
来「碰撞这本书」；这些 RAG 要提前打造，给每本书。

做法（纯离线，可复跑）：
  1. 语料＝全站专著正文（按章、约 600 字一段）＋全站文章页正文（同样切段）；
  2. 字符 2 元 TF-IDF（中文无需分词也稳），每本书按章求「章向量」；
  3. 每一章去全语料里找最像的段落，排除这本书自己；按来源去重、限每章入选数，
     保证碰撞点散布在全书各章，而不是全挤在第一章；
  4. 其他专著与站上文章分开配额（默认各 12），相似度过高的标「同源」（多半是这本书的前身稿或姊妹篇），
     其余标「近邻」；每条记下它撞的是本书哪一章、两边共有的高权重字串（提示「为什么撞」）。
产物只是检索出来的候选碰撞点，不是结论；真正的碰撞由这本书的智能体在对话里做。

用法：python3 tools/build_book_rag.py            # 全部书
      python3 tools/build_book_rag.py 3 216      # 只建这几本
"""
import glob, html, io, json, os, re, sys, time
from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, "public")
CJK = re.compile(r"[一-鿿]")
CHUNK = 600
BOOK_QUOTA, ART_QUOTA, PER_CHAPTER = 12, 12, 3
SAME_SRC = 0.62   # 高于此值多半是同一段文字的另一个版本
CROSS_MIN = 5     # 专著配额里至少这么多本来自别的书类（跨界撞，不只在同一个书架里撞）
MIN_SIM = 0.11    # 低于此值的「近邻」多半只是共用了几个虚词，宁缺毋滥
PER_GROUP = 2     # 同一组文章（同一目录下的连载，如某书的各编）最多入选几篇
# 各书都有的套话章节：既不拿来查，也不让别人撞上
BOILER = re.compile(r"作者(介绍|简介)|出版信息|版权|参考(书目|文献)|推荐语|致谢|译名对照|索引|书名页|目\s*录")


def clean(h):
    h = re.sub(r"(?is)<(script|style|noscript|nav|header|footer|svg)\b.*?</\1>", " ", h)
    h = re.sub(r'(?is)<section id="sde-talk".*?</section>', " ", h)
    return h


def text_of(fragment):
    t = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def paras(h):
    """按块级元素取段；同一段只取一次。"""
    out = []
    for m in re.finditer(r"(?is)<(h[1-4]|p|li|blockquote|dd|td)\b[^>]*>(.*?)</\1>", h):
        t = text_of(m.group(2))
        if t:
            out.append((m.group(1).lower(), t))
    return out


def chunks_of(ps):
    buf, out = "", []
    for _, t in ps:
        if len(buf) + len(t) > CHUNK and buf:
            out.append(buf)
            buf = ""
        buf += (" " if buf else "") + t
        while len(buf) > CHUNK * 1.6:
            out.append(buf[:CHUNK])
            buf = buf[CHUNK:]
    if len(CJK.findall(buf)) > 60:
        out.append(buf)
    return out


def title_of(h):
    m = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", h) or re.search(r"(?is)<title>(.*?)</title>", h)
    return text_of(m.group(1))[:80] if m else ""


# ---------- 专著：按章 ----------
# 全文不在 /books/m/N/text/ 下的几本：直接给出它们的章节文件
ALT = {14: "books/logic/*/index.html", 34: "column/gadamer-for-everyone/index.html", 134: "books/m/134/web.html", 299: "books/religion-genesis/chapters/*.html"}


def alt_chapters(n):
    out = []
    for f in sorted(glob.glob(os.path.join(PUB, ALT[n]))):
        h = clean(io.open(f, encoding="utf-8", errors="replace").read())
        u = "/" + os.path.relpath(f, PUB).replace(os.sep, "/").replace("index.html", "")
        marks = [(m.start(), text_of(m.group(2))[:60]) for m in re.finditer(r"(?is)<(h1|h2)\b[^>]*>(.*?)</\1>", h)] or [(0, title_of(h))]
        for i, (pos, t) in enumerate(marks):
            end = marks[i + 1][0] if i + 1 < len(marks) else len(h)
            ps = paras(h[pos:end])
            if sum(len(x) for _, x in ps) > 200:
                out.append({"t": t, "u": u, "ps": ps})
    return out


def book_chapters(n):
    if n in ALT:
        return alt_chapters(n)
    tp = os.path.join(PUB, "books", "m", str(n), "text", "index.html")
    if not os.path.exists(tp):
        return []
    h = clean(io.open(tp, encoding="utf-8", errors="replace").read())
    base = "/books/m/%s/text/" % n
    subs = []
    for href in re.findall(r'href="([^"#?]+)"', h):
        if not href.startswith(base):
            if href.startswith("http") or href.startswith("/") or href.startswith(".."):
                continue
            href = base + href.lstrip("./")
        rest = href[len(base):].strip("/")
        if rest and "/" not in rest and rest not in subs and (os.path.exists(os.path.join(PUB, href.strip("/"), "index.html")) or os.path.exists(os.path.join(PUB, href.strip("/") + ".html")) or (rest.endswith(".html") and os.path.exists(os.path.join(PUB, href.strip("/"))))):
            subs.append(rest)
    if len(CJK.findall(text_of(h))) < 20000 and subs:
        chs = []
        for s in subs:
            d0 = os.path.join(PUB, "books", "m", str(n), "text")
            fp = next(x for x in (os.path.join(d0, s, "index.html"), os.path.join(d0, s + ".html"), os.path.join(d0, s)) if os.path.isfile(x))
            sh = clean(io.open(fp, encoding="utf-8", errors="replace").read())
            ps = [p for p in paras(sh)]
            t = title_of(sh) or s
            chs.append({"t": t, "u": base + (s if s.endswith(".html") else s + ("/" if os.path.isdir(os.path.join(d0, s)) else "")), "ps": ps})
        return [c for c in chs if sum(len(t) for _, t in c["ps"]) > 200]
    # 单页全文：h1.front-title / h2.chap-title 作章；没有这两种就用 h2
    has = re.search(r'class="(chap-title|front-title)"', h)
    pat = r'(?is)<(h1|h2)\b[^>]*class="[^"]*(chap-title|front-title|part-title)[^"]*"[^>]*>(.*?)</\1>' if has else r"(?is)<(h2)\b([^>]*)>(.*?)</h2>"
    marks = [(m.start(), text_of(m.group(3))[:60]) for m in re.finditer(pat, h)]
    if not marks:
        return [{"t": title_of(h), "u": base, "ps": paras(h)}]
    chs = []
    for i, (pos, t) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(h)
        chs.append({"t": t, "u": base, "ps": paras(h[pos:end])})
    return [c for c in chs if sum(len(x) for _, x in c["ps"]) > 200]


# ---------- 站上文章 ----------
SKIP_DIR = re.compile(r"^/(books/m/|books/agent|search/|kb/|admin/|taste/|assets/|data/|api/|sites/read/library/|monographs/|reader/)")


def articles(book_text_urls):
    out = []
    for f in glob.glob(os.path.join(PUB, "**", "index.html"), recursive=True):
        u = "/" + os.path.relpath(f, PUB).replace(os.sep, "/")[: -len("index.html")]
        if u.count("/") < 3 or SKIP_DIR.match(u) or u in book_text_urls:
            continue
        try:
            raw = io.open(f, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        if 'http-equiv="refresh"' in raw[:3000]:
            continue
        h = clean(raw)
        ps = paras(h)
        n = sum(len(CJK.findall(t)) for _, t in ps)
        if n < 1500:
            continue
        # 卡片多的是导航页
        if len(re.findall(r'class="[^"]*\b(card|art|ch-paper|work)\b', raw)) > 6 and n < 6000:
            continue
        t = re.split(r"\s*[|｜]\s*(?=SDE Universes|SDE UNIVERSES|专著栏目|教育专栏|解构大师|西方哲学|商业与经济|公众号选读)", title_of(h) or u)[0].strip()
        out.append({"t": t or u, "u": u, "ps": ps})
    return out


def main(only):
    t0 = time.time()
    cat = json.load(io.open(os.path.join(PUB, "books", "catalog.json"), encoding="utf-8"))["books"]
    books = {b["number"]: b for b in cat if b.get("number") and (b["number"] in ALT or os.path.exists(os.path.join(PUB, "books", "m", str(b["number"]), "text", "index.html")))}
    docs, meta = [], []   # 每一段：文本；meta：(kind, srcid, title, url, chapter)
    chapter_ix = defaultdict(list)   # book -> [(chapter title, [chunk idx])]
    book_urls = set()
    for n, b in books.items():
        chs = book_chapters(n)
        for c in chs:
            book_urls.add(c["u"])
            ids = []
            if BOILER.search(c["t"]):
                continue
            for x in chunks_of(c["ps"]):
                ids.append(len(docs)); docs.append(x)
                meta.append(("book", n, b["title"], c["u"], c["t"]))
            if ids and not BOILER.search(c["t"]):
                chapter_ix[n].append((c["t"], ids))
    nb = len(docs)
    arts = articles(book_urls)
    for a in arts:
        for x in chunks_of(a["ps"]):
            docs.append(x); meta.append(("article", a["u"], a["t"], a["u"], ""))
    print("语料：专著 %d 本 %d 段，文章 %d 篇 %d 段（%.0fs）" % (len(chapter_ix), nb, len(arts), len(docs) - nb, time.time() - t0))
    vec = TfidfVectorizer(analyzer="char", ngram_range=(2, 2), min_df=3, max_df=0.2, sublinear_tf=True, max_features=300000, dtype=np.float32)
    X = vec.fit_transform(docs)
    vocab = np.array(vec.get_feature_names_out())
    print("向量化完成 %s（%.0fs）" % (X.shape, time.time() - t0))
    todo = [n for n in chapter_ix if (not only or n in only)]
    kinds = np.array([m[0] == "book" for m in meta])
    srcs = [m[1] for m in meta]
    for n in sorted(todo):
        b = books[n]
        chs = chapter_ix[n]
        own = np.array([s == n and k for s, k in zip(srcs, kinds)])
        # 本书「同一书的文章精选页」也算自己
        own_urls = "/books/m/%s/" % n
        cand = []   # (score, chapter idx, chunk idx)
        for ci, (ct, ids) in enumerate(chs):
            q = X[ids].mean(axis=0)
            q = np.asarray(q).ravel()
            nq = np.linalg.norm(q)
            if nq == 0:
                continue
            sims = X.dot(q / nq)
            sims[own] = -1
            top = np.argpartition(-sims, 60)[:60]
            for j in top:
                if sims[j] > MIN_SIM and not meta[j][3].startswith(own_urls):
                    cand.append((float(sims[j]), ci, int(j)))
        cand.sort(reverse=True)
        picked, seen_src, per_ch, quota = [], set(), defaultdict(int), {"book": 0, "article": 0}
        same, cross, per_group = 0, 0, defaultdict(int)
        mycat = b.get("category")
        chtext = {ci: " ".join(docs[k] for k in chs[ci][1]) for ci in range(len(chs))}
        for s, ci, j in cand:
            kind, sid, st, su, sch = meta[j]
            key = (kind, sid)
            if key in seen_src or per_ch[ci] >= PER_CHAPTER:
                continue
            q_ = BOOK_QUOTA if kind == "book" else ART_QUOTA
            if quota[kind] >= q_:
                continue
            other_cat = kind == "book" and books[sid].get("category") != mycat
            # 专著：留够跨界名额——同书类的满了 BOOK_QUOTA-CROSS_MIN 本就只再收别的书类
            if kind == "book" and not other_cat and quota["book"] - cross >= BOOK_QUOTA - CROSS_MIN:
                continue
            grp = su.rstrip("/").rsplit("/", 1)[0] if kind == "article" else ""
            if kind == "article" and per_group[grp] >= PER_GROUP:
                continue
            rel = "同源" if s >= SAME_SRC else ("跨界" if (other_cat or kind == "article" and not su.startswith("/books/")) and s < 0.35 else "同向")
            if rel == "同源":
                if same >= 3:
                    continue
                same += 1
            # 两边共有、权重最高的字串：提示「为什么撞」
            qv = np.asarray(X[chs[ci][1]].mean(axis=0)).ravel()
            dv = X[j].toarray().ravel()
            prod = qv * dv
            idx = np.argsort(-prod)[:24]
            terms, A, B = [], chtext[ci], docs[j]
            for k in idx:
                w = vocab[k]
                if prod[k] <= 0 or len(CJK.findall(w)) < len(w):
                    continue
                # 把相邻的二字串接成两边都出现的更长的词（「显影」+「影机」→「显影机」……）
                grew = True
                while grew:
                    grew = False
                    for k2 in idx:
                        w2 = vocab[k2]
                        if prod[k2] > 0 and w2[0] == w[-1] and (w + w2[1:]) in A and (w + w2[1:]) in B and len(w) < 8:
                            w = w + w2[1:]; grew = True; break
                if any(w in x or x in w for x in terms):
                    continue
                terms.append(w)
                if len(terms) >= 5:
                    break
            picked.append({"kind": kind, "no": sid if kind == "book" else None, "t": st, "u": su, "sch": sch,
                           "ch": chs[ci][0], "rel": rel, "s": round(s, 3), "kw": terms, "x": docs[j][:680]})
            seen_src.add(key); per_ch[ci] += 1; quota[kind] += 1
            if other_cat: cross += 1
            if kind == "article": per_group[grp] += 1
            if quota["book"] >= BOOK_QUOTA and quota["article"] >= ART_QUOTA:
                break
        out = {"no": n, "title": b["title"], "built": time.strftime("%Y-%m-%d"), "method": "char 2gram TF-IDF · 按章检索 · 专著与文章分配额",
               "chapters": [c[0] for c in chs], "items": picked}
        io.open(os.path.join(PUB, "books", "m", str(n), "rag.json"), "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    print("已建 %d 本的碰撞库（%.0fs）" % (len(todo), time.time() - t0))


if __name__ == "__main__":
    main({int(x) for x in sys.argv[1:]})
