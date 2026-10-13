"""智能体运行内核：OpenAI 兼容的工具调用循环（所有生成的智能体共用，无需修改）。
只用 Python 标准库，十家厂商通用：DeepSeek / 智谱 / Kimi / 千问 / MiniMax / Claude / GPT / OpenRouter / NVIDIA。"""
import json
import os
import time
import urllib.error
import urllib.request

from core import builtins

PROVIDERS = {
    "deepseek":   {"name": "DeepSeek",        "url": "https://api.deepseek.com/v1/chat/completions"},
    "zhipu":      {"name": "智谱 GLM",         "url": "https://open.bigmodel.cn/api/paas/v4/chat/completions"},
    "kimi":       {"name": "Kimi",            "url": "https://api.moonshot.cn/v1/chat/completions"},
    "qwen":       {"name": "千问 Qwen",        "url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"},
    "minimax":    {"name": "MiniMax",         "url": "https://api.minimax.io/v1/chat/completions"},
    "minimax_cn": {"name": "MiniMax（国内）",  "url": "https://api.minimaxi.com/v1/chat/completions"},
    "anthropic":  {"name": "Claude",          "url": "https://api.anthropic.com/v1/chat/completions"},
    "openai":     {"name": "GPT",             "url": "https://api.openai.com/v1/chat/completions"},
    "openrouter": {"name": "OpenRouter",      "url": "https://openrouter.ai/api/v1/chat/completions"},
    "nvidia":     {"name": "NVIDIA",          "url": "https://integrate.api.nvidia.com/v1/chat/completions"},
}


class Agent:
    def __init__(self, config, system_prompt, tools):
        self.config = config
        self.system_prompt = system_prompt
        self.provider = os.environ.get("AGENT_PROVIDER") or config.get("provider", "deepseek")
        prov = PROVIDERS.get(self.provider, {})
        self.url = os.environ.get("AGENT_BASE_URL") or config.get("base_url") or prov.get("url")
        if not self.url:
            raise ValueError(f"未知厂商 {self.provider}，请在 agent_config.json 填 base_url")
        self.model = os.environ.get("AGENT_MODEL") or config.get("model")
        self.key = os.environ.get("AGENT_API_KEY", "")
        self.max_tokens = int(config.get("max_tokens", 8000))
        self.max_steps = int(config.get("max_steps", 20))
        self.tools = {}
        for t in builtins.select(config.get("builtin_tools", [])) + list(tools):
            self.tools[t["name"]] = t
        self.history = []

    # ---------- 与厂商通信 ----------
    def _body(self, messages):
        body = {"model": self.model, "messages": messages}
        if "api.openai.com" in self.url:
            body["max_completion_tokens"] = self.max_tokens   # GPT 不认 max_tokens
        else:
            body["max_tokens"] = max(self.max_tokens, 1024) if "anthropic.com" in self.url else self.max_tokens
        if self.tools:
            body["tools"] = [{"type": "function", "function": {
                "name": t["name"], "description": t["description"], "parameters": t["input_schema"]}}
                for t in self.tools.values()]
        return body

    def _post(self, body):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        last = None
        for attempt in range(4):
            req = urllib.request.Request(self.url, data=data, method="POST", headers={
                "Content-Type": "application/json", "Authorization": f"Bearer {self.key}"})
            try:
                with urllib.request.urlopen(req, timeout=600) as r:
                    return json.loads(r.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                detail = e.read().decode("utf-8", "replace")[:600]
                last = f"HTTP {e.code}：{detail}"
                if e.code in (401, 403):
                    raise RuntimeError(f"API Key 无效或无权限（{self.provider}）。{detail}")
                if e.code == 400 and "max_tokens" in detail and self.max_tokens > 4000:
                    self.max_tokens //= 2                      # 预算超过该型号上限：减半重试
                    body = self._body(body["messages"])
                    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
                    continue
                if e.code not in (429, 500, 502, 503, 504, 529):
                    raise RuntimeError(last)
            except urllib.error.URLError as e:
                last = f"网络错误：{e.reason}"
            time.sleep(2 * (attempt + 1))
        raise RuntimeError(f"多次重试仍失败。{last}")

    # ---------- 工具 ----------
    def _call_tool(self, name, raw_args):
        tool = self.tools.get(name)
        if tool is None:
            return f"错误：没有名为 {name} 的工具"
        try:
            args = json.loads(raw_args) if isinstance(raw_args, str) and raw_args.strip() else (raw_args or {})
            result = tool["function"](**args)
            if not isinstance(result, str):
                result = json.dumps(result, ensure_ascii=False, default=str)
            return result[:50000]
        except Exception as e:  # 工具出错时把错误交还给模型，由它自行调整
            return f"工具执行出错：{type(e).__name__}: {e}"

    # ---------- 对话 ----------
    def ask(self, user_text, on_tool=None):
        """发一条消息，自动跑完所有工具调用，返回最终文字回答。"""
        self.history.append({"role": "user", "content": user_text})
        for _ in range(self.max_steps):
            resp = self._post(self._body([{"role": "system", "content": self.system_prompt}] + self.history))
            choice = (resp.get("choices") or [{}])[0]
            msg = choice.get("message") or {}
            calls = msg.get("tool_calls") or []
            keep = {"role": "assistant", "content": msg.get("content") or ""}
            if msg.get("reasoning_content"):          # DeepSeek 思考档的多轮工具调用要求原样带回
                keep["reasoning_content"] = msg["reasoning_content"]
            if calls:
                keep["tool_calls"] = calls
            self.history.append(keep)
            if not calls:
                return (msg.get("content") or "").strip() or "（模型没有给出文字回答）"
            for c in calls:
                fn = c.get("function") or {}
                if on_tool:
                    try:
                        on_tool(fn.get("name"), json.loads(fn.get("arguments") or "{}"))
                    except Exception:
                        on_tool(fn.get("name"), {})
                self.history.append({"role": "tool", "tool_call_id": c.get("id"),
                                     "content": self._call_tool(fn.get("name"), fn.get("arguments"))})
        return "（已达到最大步数，任务未完成。可在 agent_config.json 调大 max_steps。）"

    def reset(self):
        self.history = []
