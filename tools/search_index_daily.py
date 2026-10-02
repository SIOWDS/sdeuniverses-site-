#!/usr/bin/env python3
"""Daily search publication gate and post-upload IndexMemory synchronization."""
import datetime as dt
import json
import os
import subprocess
import sys
import time
import urllib.request

ZONE = dt.timezone(dt.timedelta(hours=8))
ENDPOINT = "https://d3ea22f828ce19cf113a457ceba2c930.r2.cloudflarestorage.com"
MANIFEST = "s3://sdeuniverses-pdf/search/manifest.json"
STATUS = "https://sdeuniverses.com/api/idx/status"
HASH_KEY = "s3://sdeuniverses-pdf/search-meta/content-hash.txt"   # 放在 search/ 之外：sync --delete 不会误删它
SEARCH_DIR = "public/search"


def needs_build(manifest, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    built = dt.datetime.fromisoformat(manifest["built"].replace("Z", "+00:00"))
    if built.tzinfo is None:
        raise ValueError("manifest.built must include a timezone")
    return built.astimezone(ZONE).date() < now.astimezone(ZONE).date()


def check():
    result = subprocess.run(
        ["aws", "s3", "cp", MANIFEST, "-", "--endpoint-url", ENDPOINT, "--only-show-errors"],
        capture_output=True, text=True, timeout=90,
    )
    if result.returncode:
        if not any(marker in result.stderr for marker in ("NoSuchKey", "Not Found", "(404)")):
            raise RuntimeError("无法核验 R2 已发布索引；停止本趟，避免重复重建。")
        run, built = True, "首次构建"
    else:
        manifest = json.loads(result.stdout)
        run, built = needs_build(manifest), manifest["built"]
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as out:
        out.write("run=" + str(run).lower() + "\n")
    print("R2 索引构建时间：", built)
    print("本日尚未更新，继续。" if run else "北京时间今天已经更新，跳过本轮构建和同步。")


def content_fingerprint(root=SEARCH_DIR):
    """索引内容指纹：manifest 里唯一会自己变的 `built` 不参与，其余每个文件的路径与字节都参与。
    index.html 是搜索页本身，不在索引里，排除。"""
    import hashlib
    top = hashlib.sha256()
    for dirpath, _, names in sorted(os.walk(root)):
        for name in sorted(names):
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, root).replace(os.sep, "/")
            if rel == "index.html":
                continue
            with open(path, "rb") as fh:
                data = fh.read()
            if rel == "manifest.json":
                obj = json.loads(data.decode("utf-8"))
                obj.pop("built", None)
                data = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            top.update(rel.encode("utf-8") + b"\0" + hashlib.sha256(data).digest())
    return top.hexdigest()


def read_remote_hash():
    result = subprocess.run(
        ["aws", "s3", "cp", HASH_KEY, "-", "--endpoint-url", ENDPOINT, "--only-show-errors"],
        capture_output=True, text=True, timeout=90,
    )
    if result.returncode:
        if any(marker in result.stderr for marker in ("NoSuchKey", "Not Found", "(404)")):
            return None
        raise RuntimeError("无法读取已记录的内容指纹；停止本趟，避免误传：" + result.stderr[:200])
    return result.stdout.strip() or None


def content():
    """内容没变就不上传、不同步数据库（每天省一整轮 R2 写入与约百万行 DO 写入）。"""
    local = content_fingerprint()
    remote = read_remote_hash()
    changed = local != remote
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as out:
        out.write("changed=" + str(changed).lower() + "\n")
        out.write("hash=" + local + "\n")
    print("本地内容指纹：", local)
    print("已发布指纹：  ", remote or "（无）")
    print("内容有变化，继续上传并同步。" if changed else "内容与已发布索引完全一致：跳过上传与数据库同步。")


def record():
    """上传与数据库同步都成功之后才记录指纹——中途失败就不记，下一趟会重来。"""
    local = content_fingerprint()
    result = subprocess.run(
        ["aws", "s3", "cp", "-", HASH_KEY, "--endpoint-url", ENDPOINT, "--only-show-errors"],
        input=local, capture_output=True, text=True, timeout=90,
    )
    if result.returncode:
        raise RuntimeError("记录内容指纹失败：" + result.stderr[:200])
    print("已记录内容指纹：", local)


def read_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": "SDE-daily-index/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.load(response)


def sync():
    # 此处只请求一次 ensure；随后仅查询状态，不反复触发重建。
    first = read_json(STATUS + "?build=1")
    result = first.get("r", {})
    if not first.get("bound") or not result.get("ok"):
        raise RuntimeError("检索数据库未接受每日同步：" + json.dumps(first, ensure_ascii=False))
    if result.get("why") == "daily_limit":
        print("今日数据库已同步；每日限额生效，下一次更新在明晚。")
        return
    deadline = time.monotonic() + 360
    while time.monotonic() < deadline:
        status = read_json(STATUS).get("r", {})
        if status.get("err"):
            raise RuntimeError("数据库同步失败，旧索引保留：" + str(status["err"]))
        if status.get("ok") and not status.get("pending") and status.get("docs", 0) > 0:
            print("数据库同步完成：", json.dumps(status, ensure_ascii=False))
            return
        time.sleep(5)
    raise RuntimeError("数据库同步未在六分钟内完成；请检查 /api/idx/status。")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("check", "sync", "content", "record"):
        raise SystemExit("Usage: search_index_daily.py check|content|sync|record")
    {"check": check, "sync": sync, "content": content, "record": record}[sys.argv[1]]()
