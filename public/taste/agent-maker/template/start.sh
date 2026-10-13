#!/usr/bin/env bash
# Mac / Linux 一键启动：首次运行自动建虚拟环境、装依赖
cd "$(dirname "$0")"
PY=$(command -v python3 || command -v python)
[ -z "$PY" ] && { echo "未找到 Python，请先安装 Python 3.9+"; exit 1; }
[ -d .venv ] || "$PY" -m venv .venv
. .venv/bin/activate
python run.py "$@"
