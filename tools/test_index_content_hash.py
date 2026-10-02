#!/usr/bin/env python3
"""内容指纹护栏：built 变不算变；任何内容、路径、新增、删除都算变；index.html 不参与。"""
import json, os, sys, tempfile, shutil
sys.path.insert(0, os.path.dirname(__file__))
import search_index_daily as d

def make(root, built="2026-10-01T00:00:00Z", doc="正文一"):
    os.makedirs(os.path.join(root, "doc"), exist_ok=True)
    os.makedirs(os.path.join(root, "kw"), exist_ok=True)
    json.dump({"built": built, "counts": {"docs": 1}, "sections": [], "docs": [{"i": 0, "u": "/", "t": "t", "s": "_root"}]},
              open(os.path.join(root, "manifest.json"), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump({"i": 0, "c": [doc]}, open(os.path.join(root, "doc", "0.json"), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump({"rows": [{"i": 0, "k": ["词"]}]}, open(os.path.join(root, "kw", "_root.json"), "w", encoding="utf-8"), ensure_ascii=False)
    open(os.path.join(root, "index.html"), "w").write("<html>搜索页</html>")

def fp(**kw):
    root = tempfile.mkdtemp()
    try:
        make(root, **kw); return d.content_fingerprint(root)
    finally:
        shutil.rmtree(root)

ok = True
def check(name, cond):
    global ok
    print(("PASS " if cond else "FAIL ") + name); ok &= bool(cond)

base = fp()
check("同样内容、不同 built → 指纹相同", base == fp(built="2026-12-31T23:59:59Z"))
check("正文改一个字 → 指纹不同", base != fp(doc="正文二"))
root = tempfile.mkdtemp()
try:
    make(root); a = d.content_fingerprint(root)
    open(os.path.join(root, "index.html"), "w").write("changed"); b = d.content_fingerprint(root)
    check("index.html 变化不影响指纹", a == b)
    open(os.path.join(root, "doc", "1.json"), "w").write("{}"); c = d.content_fingerprint(root)
    check("新增一个文件 → 指纹不同", c != a)
    os.remove(os.path.join(root, "doc", "1.json")); check("删掉它 → 回到原指纹", d.content_fingerprint(root) == a)
    m = json.load(open(os.path.join(root, "manifest.json"))); m["docs"].append({"i": 1, "u": "/x", "t": "x", "s": "_root"})
    json.dump(m, open(os.path.join(root, "manifest.json"), "w")); check("manifest 增一篇文档 → 指纹不同", d.content_fingerprint(root) != a)
finally:
    shutil.rmtree(root)
sys.exit(0 if ok else 1)
