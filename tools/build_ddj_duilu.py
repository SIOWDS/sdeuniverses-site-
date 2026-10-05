#!/usr/bin/env python3
"""三本《道德经》专著互为 RAG：第 290 号《普通人都能懂的老子》、第 297 号《道德经SDE解构导论》、第 311 号《道德经的缝隙与填补》。

2026-10-05 王德生令：三本书的智能体要能「碰撞和对读」，互相为对方的 RAG。
做法（纯离线，可复跑，读各书 text/index.html）：
  1. 每本书按章切成段（约 380–650 个汉字一段），记下它在哪一章、哪一节、网页锚点；
  2. 字符 2 元 TF-IDF；每本书的每一章去另外两本书里找最相撞的段落；
  3. 297 与 311 都按《道德经》章序编章，同一章（第 N 章）的最相撞段无论相似度多少都入选（对读同一章）；
     290 的段落若提到「第 N 章」，对 N 章加分；
  4. 每个段落最多被同一本书的 3 章借用，避免一段撞全书；
  5. 产物 public/books/m/N/duilu.json：items 的格式与 rag.json 一致（rel 固定为「对读」，n 为所撞本书章序，无则为 null），
     另带 sibs（兄弟书的名字、一句话取径）。智能体页 app.js 读它并并入碰撞库，每一问保证有对读段落带上。
用法：python3 tools/build_ddj_duilu.py
"""
import html, json, os, re, sys
from collections import Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, "public")
BOOKS = {
    290: {"t": "普通人都能懂的老子", "lens": "从老子这个人和五千字讲起，用家常故事把「无为、自然、反」讲给普通人；章是按话题排的，不按《道德经》章序", "aligned": False},
    297: {"t": "道德经SDE解构导论", "lens": "按《道德经》八十一章逐章问「这件事如何发生」：完整经文、逐句释义、传统比较、SDE 解构，核心判断是无中心、道即发生律", "aligned": True},
    311: {"t": "道德经的缝隙与填补", "lens": "按《道德经》八十一章逐章盘点「具体怎么做」的留白，再按六种路径补上一条今天能做的做法", "aligned": True},
}
CN = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}


def cn2int(s):
    s = s.strip()
    if s.isdigit():
        return int(s)
    if "百" in s:
        a, b = s.split("百", 1)
        return CN.get(a, 1) * 100 + (cn2int(b) if b else 0)
    if "十" in s:
        a, b = s.split("十", 1)
        return (CN.get(a, 1) if a else 1) * 10 + (CN.get(b, 0) if b else 0)
    return CN.get(s, 0)


def txt(h):
    return html.unescape(re.sub(r"<[^>]+>", "", h)).strip()


HAN = re.compile(r"[一-鿿]")


def chunks_of(no):
    s = open(f"{PUB}/books/m/{no}/text/index.html", encoding="utf-8").read()
    out = []
    for m in re.finditer(r'<section[^>]*class="chapter"[^>]*>.*?</section>', s, re.S):
        sec = m.group(0)
        sid = re.search(r'id="(s\d+)"', sec).group(1)
        lab = txt(re.search(r'class="chap-label">(.*?)</div>', sec, re.S).group(1))
        title = txt(re.search(r'<h2 class="chap-title">(.*?)</h2>', sec, re.S).group(1))
        n = None
        mm = re.match(r"第\s*([0-9一二三四五六七八九十百]+)\s*章", lab)
        if mm:
            n = cn2int(mm.group(1))
        sub = ""
        buf, cnt = [], 0
        def flush():
            nonlocal buf, cnt
            t = "".join(buf).strip()
            if len(HAN.findall(t)) >= 120:
                out.append(dict(no=no, sid=sid, n=n if BOOKS[no]["aligned"] else None, nlab=lab, title=title, sub=sub, x=t))
            buf, cnt = [], 0
        for k in re.finditer(r'<h3[^>]*>(.*?)</h3>|<p[^>]*>(.*?)</p>', sec, re.S):
            if k.group(1) is not None:
                flush(); sub = txt(k.group(1)).lstrip("◆ ").strip(); continue
            p = txt(k.group(2))
            if not p:
                continue
            buf.append(p + " "); cnt += len(HAN.findall(p))
            if cnt >= 380:
                flush()
        flush()
    return out


def main():
    allc = {no: chunks_of(no) for no in BOOKS}
    for no, c in allc.items():
        print(no, "chunks", len(c), "chapters", len({x["sid"] for x in c}))
    flat = [x for no in BOOKS for x in allc[no]]
    vec = TfidfVectorizer(analyzer="char", ngram_range=(2, 2), sublinear_tf=True, min_df=2, max_df=0.5,
                          token_pattern=None, preprocessor=lambda t: HAN.sub(lambda m: m.group(0), "".join(HAN.findall(t))))
    X = vec.fit_transform([x["x"] for x in flat]).tocsr()
    terms = np.array(vec.get_feature_names_out())
    idx = {}
    for i, x in enumerate(flat):
        idx.setdefault(x["no"], []).append(i)
    for tgt in BOOKS:
        # 本书各章向量
        chs = {}
        for i in idx[tgt]:
            chs.setdefault(flat[i]["sid"], []).append(i)
        items = []
        used = {}
        for sid, ids in chs.items():
            first = flat[ids[0]]
            u = X[ids].sum(axis=0)
            u = np.asarray(u).ravel()
            nrm = np.linalg.norm(u) or 1
            u = u / nrm
            for sib in BOOKS:
                if sib == tgt:
                    continue
                sids = idx[sib]
                sims = X[sids].dot(u)
                sims = np.asarray(sims).ravel()
                bonus = np.zeros(len(sids))
                for j, i in enumerate(sids):
                    c = flat[i]
                    if first["n"] and c["n"] == first["n"]:
                        bonus[j] += 0.30
                    if first["n"] and not BOOKS[sib]["aligned"]:
                        if re.search(r"第\s*%d\s*章" % first["n"], c["x"]):
                            bonus[j] += 0.10
                order = np.argsort(-(sims + bonus))
                picked = 0
                for j in order[:40]:
                    i = sids[j]
                    key = (sib, i)
                    if used.get(key, 0) >= 3:
                        continue
                    aligned_hit = bool(first["n"] and flat[i]["n"] == first["n"])
                    if sims[j] < 0.10 and not aligned_hit:
                        continue
                    # 同一章已选一条后，第二条只收明显相撞的
                    if picked >= 1 and sims[j] < 0.20:
                        break
                    used[key] = used.get(key, 0) + 1
                    c = flat[i]
                    prod = X[i].multiply(X[ids].mean(axis=0)).toarray().ravel() if False else None
                    # 共有字串：两边都有的高权重 2 元组
                    xi = X[i].toarray().ravel()
                    sh = xi * u[: len(xi)] if len(xi) == len(u) else xi * 0
                    kw = [t for t in terms[np.argsort(-sh)[:6]] if sh[np.where(terms == t)[0][0]] > 0][:5]
                    items.append({
                        "kind": "book", "no": sib, "t": BOOKS[sib]["t"],
                        "u": f"/books/m/{sib}/text/#{c['sid']}",
                        "sch": (c["nlab"] + "　" if c["nlab"] else "") + c["title"] + ("　· " + c["sub"] if c["sub"] else ""),
                        "ch": (first["nlab"] + "　" if first["nlab"] else "") + first["title"],
                        "n": first["n"], "rel": "对读", "s": round(float(sims[j]), 3), "kw": kw,
                        "x": c["x"][:330],
                    })
                    picked += 1
                    if picked >= 2:
                        break
        out = {"no": tgt, "title": BOOKS[tgt]["t"], "built": "2026-10-05",
               "method": "三本《道德经》互为 RAG · char 2gram TF-IDF · 按章对读 · 297/311 同章必选",
               "sibs": [{"no": n, "t": BOOKS[n]["t"], "lens": BOOKS[n]["lens"]} for n in BOOKS if n != tgt],
               "items": items}
        p = f"{PUB}/books/m/{tgt}/duilu.json"
        json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        print(tgt, "items", len(items), "bytes", os.path.getsize(p), Counter(i["no"] for i in items))


if __name__ == "__main__":
    main()
