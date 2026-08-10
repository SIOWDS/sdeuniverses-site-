#!/usr/bin/env python3
import urllib.parse
# -*- coding: utf-8 -*-
"""第二语料：十二个语言/运行时/基础设施项目的判形滞后期。预注册见 PREREG3.md。"""
import json, os, re, sys, time, urllib.request

TOK = os.environ.get("GH_TOK", "")
PROJECTS = [  # (owner/repo, 首次公开发布年)
    ("python/cpython", 1991), ("golang/go", 2009), ("rust-lang/rust", 2010),
    ("nodejs/node", 2009), ("git/git", 2005), ("postgres/postgres", 1996),
    ("curl/curl", 1998), ("ruby/ruby", 1995), ("php/php-src", 1995),
    ("openssl/openssl", 1998), ("llvm/llvm-project", 2003), ("vim/vim", 1991),
]
PAT = re.compile(r"(compat|deprecat|stabilit|versioning|backward)", re.I)
EXT = re.compile(r"\.(md|rst|txt|html)$", re.I)

def api(url):
    r = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "prereg3",
        **({"Authorization": f"Bearer {TOK}"} if TOK else {})})
    with urllib.request.urlopen(r, timeout=60) as f:
        return json.load(f)

def oldest_commit(repo, path):
    """真正的最早一次提交：翻到最后一页再取末条（单页取末条在 >100 次提交时会取错）。"""
    q = f"https://api.github.com/repos/{repo}/commits?path={urllib.parse.quote(path)}&per_page=100"
    page, last = 1, None
    while page <= 40:
        cs = api(q + f"&page={page}")
        if not cs:
            break
        last = cs[-1]
        if len(cs) < 100:
            break
        page += 1
        time.sleep(0.1)
    return last


out = []
for repo, born in PROJECTS:
    try:
        tree = api(f"https://api.github.com/repos/{repo}/git/trees/HEAD?recursive=1")
        paths = [t["path"] for t in tree.get("tree", []) if t["type"] == "blob"
                 and PAT.search(t["path"]) and (EXT.search(t["path"]) or t["path"].lower().startswith("doc"))]
        paths = paths[:12]
        best = None
        for p in paths:
            try:
                cs = oldest_commit(repo, p)
            except Exception:
                continue
            if not cs:
                continue
            d = cs["commit"]["committer"]["date"][:4]
            if best is None or int(d) < best[0]:
                best = (int(d), p)
            time.sleep(0.15)
        out.append(dict(repo=repo, born=born, n_paths=len(paths),
                        policy_year=best[0] if best else None,
                        policy_path=best[1] if best else None,
                        lag=(best[0] - born) if best else None))
        print(f"  {repo:<22} 发布 {born}  文件 {len(paths):>2}  首次政策 {best[0] if best else '—'}  滞后 {best[0]-born if best else '—'}")
    except Exception as e:
        out.append(dict(repo=repo, born=born, error=str(e)[:80]))
        print(f"  {repo:<22} 失败 {e}")
json.dump(out, open("result3.json", "w"), ensure_ascii=False, indent=2)
lags = sorted(x["lag"] for x in out if x.get("lag") is not None)
none_n = sum(1 for x in out if x.get("policy_year") is None and "error" not in x)
print(f"\nn={len(lags)}  滞后期 {lags}")
if lags:
    m = lags[len(lags)//2] if len(lags) % 2 else (lags[len(lags)//2-1]+lags[len(lags)//2])/2
    print(f"Q1 中位数 = {m}  （阈值 ≥5）")
print(f"Q2 无政策文件的项目数 = {none_n}  （阈值 ≥2）")
if lags:
    import statistics
    ages = [2026 - x["born"] for x in out if x.get("lag") is not None]
    ls = [x["lag"] for x in out if x.get("lag") is not None]
    n = len(ls)
    ra = sorted(range(n), key=lambda i: ages[i]); rl = sorted(range(n), key=lambda i: ls[i])
    RA = [0]*n; RL = [0]*n
    for r, i in enumerate(ra): RA[i] = r
    for r, i in enumerate(rl): RL[i] = r
    d2 = sum((RA[i]-RL[i])**2 for i in range(n))
    rho = 1 - 6*d2/(n*(n*n-1))
    print(f"Q3 年龄与滞后的秩相关 rho = {rho:.3f}")
