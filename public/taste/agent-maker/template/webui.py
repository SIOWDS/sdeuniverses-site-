"""极简本地网页界面（只用 Python 标准库）。"""
import html
import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PAGE = """<!doctype html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{name}</title>
<style>
body{{margin:0;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:#f6f5f1;color:#222}}
header{{background:#1f2a44;color:#fff;padding:14px 20px}}header h1{{margin:0;font-size:18px}}header p{{margin:4px 0 0;font-size:13px;opacity:.8}}
#log{{max-width:820px;margin:0 auto;padding:16px 16px 140px}}
.m{{margin:12px 0;padding:12px 14px;border-radius:10px;white-space:pre-wrap;line-height:1.65}}
.u{{background:#dfe7f5;margin-left:15%}}.a{{background:#fff;border:1px solid #e3e0d6}}.t{{font-size:12px;color:#8a7a50}}
form{{position:fixed;bottom:0;left:0;right:0;background:#f6f5f1;border-top:1px solid #ddd;padding:12px}}
.row{{max-width:820px;margin:0 auto;display:flex;gap:8px}}textarea{{flex:1;height:60px;padding:8px;font:inherit;border-radius:8px;border:1px solid #ccc}}
button{{background:#1f2a44;color:#fff;border:0;border-radius:8px;padding:0 18px;font:inherit;cursor:pointer}}button.g{{background:#999}}
.ex{{font-size:13px;color:#555}}.ex a{{display:inline-block;margin:4px 6px 0 0;padding:3px 8px;background:#fff;border:1px solid #ddd;border-radius:12px;cursor:pointer}}
</style></head><body><header><h1>{name}</h1><p>{desc}</p></header>
<div id="log"><div class="ex">{examples}</div></div>
<form id="f"><div class="row"><textarea id="q" placeholder="输入你的需求，Ctrl+Enter 发送"></textarea>
<button>发送</button><button type="button" class="g" id="n">新对话</button></div></form>
<script>
const log=document.getElementById('log'),q=document.getElementById('q');
function add(c,t){{const d=document.createElement('div');d.className='m '+c;d.textContent=t;log.appendChild(d);scrollTo(0,1e9);return d}}
async function send(){{const t=q.value.trim();if(!t)return;q.value='';add('u',t);const w=add('a t','思考中……');
 try{{const r=await fetch('/ask',{{method:'POST',body:JSON.stringify({{q:t}})}});const j=await r.json();
 w.className='m a';w.textContent=(j.tools.length?'⚙ '+j.tools.join(' · ')+'\\n\\n':'')+j.answer}}catch(e){{w.textContent='出错：'+e}}}}
document.getElementById('f').onsubmit=e=>{{e.preventDefault();send()}};
q.onkeydown=e=>{{if(e.key==='Enter'&&(e.ctrlKey||e.metaKey))send()}};
document.getElementById('n').onclick=async()=>{{await fetch('/reset',{{method:'POST'}});log.innerHTML='';add('a t','—— 新对话 ——')}};
document.querySelectorAll('.ex a').forEach(a=>a.onclick=()=>{{q.value=a.textContent;q.focus()}});
</script></body></html>"""


def serve(agent, config, port=8765):
    lock = threading.Lock()
    examples = "".join(f"<a>{html.escape(x)}</a>" for x in config.get("example_questions", []))
    page = PAGE.format(name=html.escape(config["name"]), desc=html.escape(config.get("description", "")),
                       examples=("可以试试：" + examples) if examples else "").encode("utf-8")

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, body, ctype="application/json; charset=utf-8"):
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            self._send(page, "text/html; charset=utf-8")

        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(n) or b"{}")
            with lock:
                if self.path == "/reset":
                    agent.reset()
                    return self._send(b"{}")
                used = []
                try:
                    ans = agent.ask(data.get("q", ""), on_tool=lambda name, _a: used.append(name))
                except Exception as e:
                    ans = f"出错了：{e}"
            self._send(json.dumps({"answer": ans, "tools": used}, ensure_ascii=False).encode("utf-8"))

    url = f"http://127.0.0.1:{port}"
    print(f"网页界面已启动：{url}  （关闭本窗口即停止）")
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
