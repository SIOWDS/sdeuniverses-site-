"""自检（不需要 API Key）：检查配置、提示词、工具定义，并逐个试跑工具。
  python selftest.py          打印结果
  python selftest.py --json   输出机器可读结果（生成器用）
"""
import json
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
sys.path.insert(0, HERE)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

errors, passed = [], []

try:  # 先补装依赖（与 run.py 同一套逻辑）
    import run
    run.ensure_requirements()
except Exception as e:
    errors.append({"check": "安装依赖", "error": f"{type(e).__name__}: {e}", "trace": ""})


def check(name, fn):
    try:
        fn()
        passed.append(name)
    except Exception as e:
        errors.append({"check": name, "error": f"{type(e).__name__}: {e}",
                       "trace": traceback.format_exc()[-1500:]})


def t_config():
    c = json.load(open("agent_config.json", encoding="utf-8"))
    for k in ("name", "model"):
        assert c.get(k), f"agent_config.json 缺少 {k}"


def t_prompt():
    p = open("system_prompt.md", encoding="utf-8").read()
    assert len(p.strip()) > 50, "system_prompt.md 太短"


TOOLS = []


def t_tools():
    global TOOLS
    import tools
    TOOLS = getattr(tools, "TOOLS", None)
    assert isinstance(TOOLS, list), "tools.py 必须定义列表 TOOLS"
    seen = set()
    for t in TOOLS:
        for k in ("name", "description", "input_schema", "function"):
            assert k in t, f"工具 {t.get('name')} 缺少字段 {k}"
        assert callable(t["function"]), f"{t['name']} 的 function 不可调用"
        assert t["input_schema"].get("type") == "object", f"{t['name']} 的 input_schema.type 必须是 object"
        assert t["name"] not in seen, f"工具重名 {t['name']}"
        seen.add(t["name"])
    import re
    for t in TOOLS:
        assert re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", t["name"]), f"工具名 {t['name']} 只能用英文字母数字下划线"


def t_core():
    from core import builtins  # noqa
    import core.agent  # noqa


check("配置文件", t_config)
check("系统提示词", t_prompt)
check("工具定义", t_tools)
check("运行内核", t_core)

if os.path.exists("tests.json") and TOOLS:
    fns = {t["name"]: t["function"] for t in TOOLS}
    for i, case in enumerate(json.load(open("tests.json", encoding="utf-8"))):
        def run(case=case):
            name = case["tool"]
            assert name in fns, f"测试引用了不存在的工具 {name}"
            out = fns[name](**case.get("input", {}))
            text = out if isinstance(out, str) else json.dumps(out, ensure_ascii=False, default=str)
            for s in case.get("expect_contains", []):
                assert s in text, f"输出中未找到「{s}」。实际输出：{text[:300]}"
        check(f"工具测试 #{i + 1} {case.get('tool')}", run)

if "--json" in sys.argv:
    print(json.dumps({"ok": not errors, "passed": passed, "errors": errors}, ensure_ascii=False))
else:
    for p in passed:
        print(f"✓ {p}")
    for e in errors:
        print(f"✗ {e['check']}：{e['error']}")
    print("\n自检通过，可以运行：python run.py" if not errors else "\n自检未通过。")
sys.exit(0 if not errors else 1)
