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
    if len(sys.argv) != 2 or sys.argv[1] not in ("check", "sync"):
        raise SystemExit("Usage: search_index_daily.py check|sync")
    {"check": check, "sync": sync}[sys.argv[1]]()
