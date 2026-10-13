"""内置工具：生成器可按需为智能体开启（agent_config.json 的 builtin_tools）。
文件读写只限于智能体目录下的 workspace/ 文件夹。"""
import datetime
import html
import os
import re
import urllib.request

WORKSPACE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workspace")


def _safe(path):
    os.makedirs(WORKSPACE, exist_ok=True)
    full = os.path.abspath(os.path.join(WORKSPACE, path))
    if not full.startswith(os.path.abspath(WORKSPACE)):
        raise ValueError("只能访问 workspace/ 目录内的文件")
    return full


def read_file(path):
    with open(_safe(path), encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    full = _safe(path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    return f"已保存到 workspace/{path}（{len(content)} 字符）"


def list_files():
    os.makedirs(WORKSPACE, exist_ok=True)
    out = []
    for root, _, files in os.walk(WORKSPACE):
        for n in files:
            out.append(os.path.relpath(os.path.join(root, n), WORKSPACE))
    return "\n".join(sorted(out)) or "（workspace 为空）"


def fetch_url(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (agent)"})
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read().decode(r.headers.get_content_charset() or "utf-8", errors="replace")
    raw = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    text = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    return re.sub(r"\s+", " ", text).strip()[:20000]


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S %A")


_ALL = {
    "read_file": {
        "name": "read_file", "function": read_file,
        "description": "读取 workspace/ 目录下的文本文件内容。",
        "input_schema": {"type": "object", "properties": {"path": {"type": "string", "description": "相对 workspace/ 的路径"}}, "required": ["path"]},
    },
    "write_file": {
        "name": "write_file", "function": write_file,
        "description": "把文本内容保存为 workspace/ 下的文件（会覆盖同名文件）。",
        "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]},
    },
    "list_files": {
        "name": "list_files", "function": list_files,
        "description": "列出 workspace/ 目录下的全部文件。",
        "input_schema": {"type": "object", "properties": {}},
    },
    "fetch_url": {
        "name": "fetch_url", "function": fetch_url,
        "description": "抓取一个网页，返回去掉标签后的正文文字（最多 2 万字符）。",
        "input_schema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},
    },
    "now": {
        "name": "now", "function": now,
        "description": "返回当前本地日期与时间。",
        "input_schema": {"type": "object", "properties": {}},
    },
}

NAMES = list(_ALL)


def select(names):
    return [_ALL[n] for n in names if n in _ALL]
