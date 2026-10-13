"""启动入口。
  python run.py            对话模式（命令行）
  python run.py "问题"     一问一答，答完退出
  python run.py --web      打开本地网页界面 http://127.0.0.1:8765
"""
import importlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
sys.path.insert(0, HERE)
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8")
    except Exception:
        pass


def ensure_requirements():
    """缺什么依赖就自动 pip 安装什么。"""
    if sys.version_info < (3, 9):
        sys.exit("需要 Python 3.9 或更高版本。")
    req = os.path.join(HERE, "requirements.txt")
    if sys.platform == "emscripten" or not os.path.exists(req):   # 浏览器里自检时不装包
        return
    missing = []
    for line in open(req, encoding="utf-8"):
        pkg = line.split("#")[0].strip()
        if not pkg:
            continue
        mod = pkg.split("==")[0].split(">=")[0].split("[")[0].strip()
        mod = {"beautifulsoup4": "bs4", "python-docx": "docx", "pyyaml": "yaml",
               "pillow": "PIL", "scikit-learn": "sklearn"}.get(mod.lower(), mod).replace("-", "_")
        try:
            importlib.import_module(mod)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"正在安装依赖：{' '.join(missing)} ……")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", *missing])


def ensure_key():
    env_path = os.path.join(HERE, ".env")
    if os.path.exists(env_path):
        for line in open(env_path, encoding="utf-8"):
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"'))
    if not os.environ.get("AGENT_API_KEY"):
        cfg = json.load(open(os.path.join(HERE, "agent_config.json"), encoding="utf-8"))
        from core.agent import PROVIDERS
        vname = PROVIDERS.get(cfg.get("provider"), {}).get("name", cfg.get("provider", ""))
        key = input(f"请输入 {vname} 的 API Key（只需一次，会保存在本目录 .env）：").strip()
        if not key:
            sys.exit("没有 API Key，无法运行。")
        with open(env_path, "a", encoding="utf-8") as f:
            f.write(f"AGENT_API_KEY={key}\n")
        os.environ["AGENT_API_KEY"] = key


def load_agent():
    from core.agent import Agent
    import tools
    config = json.load(open("agent_config.json", encoding="utf-8"))
    prompt = open("system_prompt.md", encoding="utf-8").read()
    kdir = os.path.join(HERE, "knowledge")
    if os.path.isdir(kdir):  # 附带资料自动接在提示词后面
        for n in sorted(os.listdir(kdir)):
            if n.lower().endswith((".md", ".txt")):
                text = open(os.path.join(kdir, n), encoding="utf-8", errors="replace").read()
                prompt += f"\n\n<knowledge file=\"{n}\">\n{text}\n</knowledge>"
    return Agent(config, prompt, getattr(tools, "TOOLS", [])), config


def show_tool(name, args):
    s = json.dumps(args, ensure_ascii=False)
    print(f"  ⚙ {name} {s[:120]}{'…' if len(s) > 120 else ''}")


def chat(agent, config):
    print(f"\n=== {config['name']} ===\n{config.get('description', '')}")
    ex = config.get("example_questions") or []
    if ex:
        print("可以试试：\n" + "\n".join(f"  · {q}" for q in ex))
    print("（输入 /new 开始新对话，/exit 退出）\n")
    while True:
        try:
            q = input("你：").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q:
            continue
        if q in ("/exit", "/quit", "exit"):
            break
        if q == "/new":
            agent.reset()
            print("—— 已开始新对话 ——\n")
            continue
        try:
            print(f"\n{config['name']}：{agent.ask(q, on_tool=show_tool)}\n")
        except Exception as e:
            print(f"\n出错了：{e}\n")


def main():
    ensure_requirements()
    ensure_key()
    agent, config = load_agent()
    args = sys.argv[1:]
    if args and args[0] == "--web":
        import webui
        webui.serve(agent, config)
    elif args:
        print(agent.ask(" ".join(args), on_tool=show_tool))
    else:
        chat(agent, config)


if __name__ == "__main__":
    main()
